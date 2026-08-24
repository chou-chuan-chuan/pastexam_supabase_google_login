import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const setup = await readFile(new URL("../supabase/setup.sql", import.meta.url), "utf8");
const migration = await readFile(new URL("../supabase/lyrics_library_migration.sql", import.meta.url), "utf8");

test("setup defines the lyrics tables, constraints, indexes, RLS, and private bucket", () => {
  for (const table of ["songs", "lyric_cues", "tags", "song_tags"]) {
    assert.match(setup, new RegExp(`create table if not exists public\\.${table}`));
    assert.match(setup, new RegExp(`alter table public\\.${table} enable row level security`));
  }
  assert.match(setup, /youtube_video_id ~ '\^\[A-Za-z0-9_-\]\{11\}\$'/);
  assert.match(setup, /status in \('pending', 'approved', 'rejected'\)/);
  assert.match(setup, /unique \(song_id, line_index\)/);
  assert.match(setup, /create index if not exists lyric_cues_song_start_idx/);
  assert.match(setup, /values \('lyrics-pdfs', 'lyrics-pdfs', false, 52428800/);
  assert.match(setup, /uploader_display_name text/);
  assert.match(setup, /function public\.set_song_uploader_display_name/);
  assert.match(setup, /raw_user_meta_data/);
});

test("database RPCs atomically replace cues and tags and confirm used-tag deletion", () => {
  assert.match(setup, /function public\.replace_song_lyric_cues/);
  assert.match(setup, /delete from public\.lyric_cues[\s\S]*insert into public\.lyric_cues/);
  assert.match(setup, /function public\.set_song_tags/);
  assert.match(setup, /function public\.delete_tag/);
  assert.match(setup, /p_confirm_used/);
});

test("migration is self-contained and does not drop legacy exams or past-exams", () => {
  assert.match(migration, /create table if not exists public\.songs/);
  assert.doesNotMatch(migration, /drop table[^;]*exams/i);
  assert.doesNotMatch(migration, /delete from storage\.buckets[^;]*past-exams/i);
});
