import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  compareDefaultSongOrder,
  filterSongs,
  matchesSong,
  pendingSongPayload,
  sortSongsForDisplay,
  uploaderDisplayName
} from "../assets/catalog.js";

const songs = [
  {
    title: "Moon River",
    artist: "Audrey Hepburn",
    album: "Breakfast at Tiffany's",
    release_year: 1961,
    language: "English",
    genre: "Soundtrack",
    notes: "Classic ballad",
    song_tags: [{ tags: { id: "tag-1", name: "電影", slug: "movie" } }]
  },
  {
    title: "島嶼天光",
    artist: "滅火器",
    album: "島嶼天光",
    release_year: 2014,
    language: "中文",
    genre: "Rock",
    notes: "Taiwan",
    song_tags: [{ tags: { id: "tag-2", name: "現場", slug: "live" } }]
  }
];

test("searches title, artist, album, language, genre, tag, and year", () => {
  for (const query of ["Moon", "Audrey", "Breakfast", "English", "Soundtrack", "電影", "1961"]) {
    assert.equal(matchesSong(songs[0], { query }), true, query);
  }
});

test("combines language, genre, year, and multiple tag filters", () => {
  assert.deepEqual(filterSongs(songs, {
    language: "中文",
    genre: "Rock",
    year: "2014",
    tags: ["live"]
  }).map((song) => song.title), ["島嶼天光"]);
  assert.equal(matchesSong(songs[1], { tags: ["live", "movie"] }), false);
});

test("sorts approved songs by persistent public display position", () => {
  const orderedSongs = [
    { id: "newer", status: "approved", created_at: "2026-03-01T00:00:00Z" },
    { id: "older", status: "approved", created_at: "2025-03-01T00:00:00Z" },
    { id: "middle", status: "approved", created_at: "2026-02-01T00:00:00Z" }
  ];
  const displayOrder = [
    { song_id: "older", position: 1024 },
    { song_id: "middle", position: 2048 },
    { song_id: "newer", position: 3072 }
  ];
  assert.deepEqual(sortSongsForDisplay(orderedSongs, displayOrder).map((song) => song.id), ["older", "middle", "newer"]);
});

test("groups fallback songs by language with blank and null languages last", () => {
  const unorderedSongs = [
    { id: "blank", status: "approved", language: "  ", created_at: "2026-05-01T00:00:00Z" },
    { id: "spanish", status: "approved", language: "Spanish", created_at: "2026-01-01T00:00:00Z" },
    { id: "french-old", status: "approved", language: "French", created_at: "2025-01-01T00:00:00Z" },
    { id: "null", status: "approved", language: null, created_at: "2026-04-01T00:00:00Z" },
    { id: "japanese", status: "approved", language: "Japanese", created_at: "2026-02-01T00:00:00Z" },
    { id: "french-new", status: "approved", language: "French", created_at: "2026-03-01T00:00:00Z" }
  ];
  assert.deepEqual(sortSongsForDisplay(unorderedSongs).map((song) => song.id), [
    "french-new",
    "french-old",
    "japanese",
    "spanish",
    "blank",
    "null"
  ]);
});

test("compares language case-insensitively, then newest first", () => {
  const sameLanguage = [
    { id: "older", language: "French", created_at: "2025-01-01T00:00:00Z" },
    { id: "newer", language: " french ", created_at: "2026-01-01T00:00:00Z" }
  ];
  assert.deepEqual(sameLanguage.sort(compareDefaultSongOrder).map((song) => song.id), ["newer", "older"]);
});

test("uses song id as the final deterministic default tie-break", () => {
  const tiedSongs = [
    { id: "song-b", language: "French", created_at: "2026-01-01T00:00:00Z" },
    { id: "song-a", language: "french", created_at: "2026-01-01T00:00:00Z" }
  ];
  assert.deepEqual(tiedSongs.sort(compareDefaultSongOrder).map((song) => song.id), ["song-a", "song-b"]);
});

test("uses created_at descending as the deterministic tie-breaker for equal positions", () => {
  const tiedSongs = [
    { id: "older", status: "approved", created_at: "2025-01-01T00:00:00Z" },
    { id: "newer", status: "approved", created_at: "2026-01-01T00:00:00Z" }
  ];
  const tiedOrder = tiedSongs.map((song) => ({ song_id: song.id, position: 1024 }));
  assert.deepEqual(sortSongsForDisplay(tiedSongs, tiedOrder).map((song) => song.id), ["newer", "older"]);
});

test("persistent admin positions override the language default", () => {
  const orderedSongs = [
    { id: "french", status: "approved", language: "French", created_at: "2026-01-01T00:00:00Z" },
    { id: "japanese", status: "approved", language: "Japanese", created_at: "2026-01-01T00:00:00Z" }
  ];
  const displayOrder = [
    { song_id: "japanese", position: 1024 },
    { song_id: "french", position: 2048 }
  ];
  assert.deepEqual(sortSongsForDisplay(orderedSongs, displayOrder).map((song) => song.id), ["japanese", "french"]);
});

test("songs missing order rows use the language default without disturbing persisted rows", () => {
  const partiallyOrderedSongs = [
    { id: "missing-japanese", status: "approved", language: "Japanese", created_at: "2026-02-01T00:00:00Z" },
    { id: "persisted-spanish", status: "approved", language: "Spanish", created_at: "2026-01-01T00:00:00Z" },
    { id: "missing-french", status: "approved", language: "French", created_at: "2026-03-01T00:00:00Z" }
  ];
  const displayOrder = [{ song_id: "persisted-spanish", position: 1024 }];
  assert.deepEqual(sortSongsForDisplay(partiallyOrderedSongs, displayOrder).map((song) => song.id), [
    "persisted-spanish",
    "missing-french",
    "missing-japanese"
  ]);
});

test("filtering preserves the configured public display order and tag behavior", () => {
  const displaySongs = sortSongsForDisplay([
    { ...songs[0], id: "moon", status: "approved", created_at: "2026-02-01T00:00:00Z" },
    { ...songs[1], id: "island", status: "approved", created_at: "2026-01-01T00:00:00Z" }
  ], [
    { song_id: "island", position: 1024 },
    { song_id: "moon", position: 2048 }
  ]);
  assert.deepEqual(filterSongs(displaySongs, { tags: ["live"] }).map((song) => song.id), ["island"]);
  assert.deepEqual(filterSongs(displaySongs, { query: "i" }).map((song) => song.id), ["island", "moon"]);
});

test("admin management list uses the shared language comparator without public positions", async () => {
  const adminSource = await readFile(new URL("../assets/admin.js", import.meta.url), "utf8");
  assert.match(adminSource, /import \{[^}]*compareDefaultSongOrder[^}]*\} from "\.\/catalog\.js"/);
  assert.match(adminSource, /songs\.filter\(matches\)\.sort\(compareDefaultSongOrder\)/);
  assert.doesNotMatch(adminSource, /song_display_order/);
  assert.doesNotMatch(adminSource, /\.order\("created_at", \{ ascending: false \}\)/);
});

test("submission payload always forces pending status", () => {
  const payload = pendingSongPayload({
    title: "Song",
    artist: "Artist",
    status: "approved",
    youtube_video_id: "dQw4w9WgXcQ",
    pdf_path: "user/file.pdf",
    original_filename: "lyrics.pdf"
  }, "user-id");
  assert.equal(payload.status, "pending");
  assert.equal(payload.uploader_id, "user-id");
});

test("uploader display prefers the stored OAuth name and falls back to UUID", () => {
  assert.equal(uploaderDisplayName({ uploader_display_name: " Google User ", uploader_id: "uuid" }), "Google User");
  assert.equal(uploaderDisplayName({ uploader_id: "uuid" }), "uuid");
  assert.equal(uploaderDisplayName({}), "—");
});
