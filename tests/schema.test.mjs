import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const setup = await readFile(new URL("../supabase/setup.sql", import.meta.url), "utf8");
const migration = await readFile(new URL("../supabase/lyrics_library_migration.sql", import.meta.url), "utf8");
const displayOrderMigration = await readFile(new URL("../supabase/song_display_order_migration.sql", import.meta.url), "utf8");
const defaultLanguageOrderMigration = await readFile(new URL("../supabase/default_language_song_order_migration.sql", import.meta.url), "utf8");
const adminUserManagementMigration = await readFile(new URL("../supabase/admin_user_management_migration.sql", import.meta.url), "utf8");

function adminUserManagementDefinitions(sql) {
  const start = sql.indexOf("create or replace function public.admin_list_users(");
  const endMarker = "grant execute on function public.admin_set_user_role(uuid, boolean) to authenticated;";
  const end = sql.indexOf(endMarker, start);
  assert.notEqual(start, -1, "admin_list_users definition is present");
  assert.notEqual(end, -1, "admin_set_user_role grant is present");
  return sql.slice(start, end + endMarker.length);
}

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

test("fresh public song ordering migration seeds the language-based default and enables read-only RLS", () => {
  assert.match(displayOrderMigration, /create table if not exists public\.song_display_order/);
  assert.match(displayOrderMigration, /case when language is null or btrim\(language\) = '' then 1 else 0 end/);
  assert.match(displayOrderMigration, /lower\(btrim\(language\)\),\s*created_at desc,\s*id/);
  assert.match(displayOrderMigration, /row_number\(\) over \([\s\S]*?\) \* 1024/);
  assert.match(displayOrderMigration, /alter table public\.song_display_order enable row level security/);
  assert.match(displayOrderMigration, /revoke all on table public\.song_display_order from anon, authenticated/);
  assert.match(displayOrderMigration, /grant select on table public\.song_display_order to anon, authenticated/);
  assert.match(displayOrderMigration, /s\.status = 'approved'/);
  assert.match(displayOrderMigration, /on delete cascade/);
});

test("production migration re-seeds approved songs once by language without changing song data", () => {
  assert.match(defaultLanguageOrderMigration, /^begin;/);
  assert.match(defaultLanguageOrderMigration, /to_regclass\('public\.song_display_order'\)/);
  assert.match(defaultLanguageOrderMigration, /intentionally resets the existing public display positions/i);
  assert.match(defaultLanguageOrderMigration, /manual ordering performed[\s\S]*will therefore be replaced/i);
  assert.match(defaultLanguageOrderMigration, /case when language is null or btrim\(language\) = '' then 1 else 0 end/);
  assert.match(defaultLanguageOrderMigration, /lower\(btrim\(language\)\),\s*created_at desc,\s*id/);
  assert.match(defaultLanguageOrderMigration, /where status = 'approved'/);
  assert.match(defaultLanguageOrderMigration, /on conflict \(song_id\) do update/);
  assert.doesNotMatch(defaultLanguageOrderMigration, /delete\s+from\s+public\.songs/i);
  assert.doesNotMatch(defaultLanguageOrderMigration, /update\s+public\.songs/i);
  assert.match(defaultLanguageOrderMigration, /commit;\s*$/);
});

test("approval insertion targets its language boundary and only renumbers current display order when needed", () => {
  for (const sql of [displayOrderMigration, defaultLanguageOrderMigration]) {
    assert.match(sql, /pg_advisory_xact_lock/);
    assert.match(sql, /lower\(btrim\(coalesce\(new\.language, ''\)\)\)/);
    assert.match(sql, /after the last currently displayed song in[\s\S]*same normalized language/i);
    assert.match(sql, /where song\.status = 'approved'\s+and not new_language_is_blank\s+and \(/);
    assert.match(sql, /lead\(song_order\.song_id\) over/);
    assert.match(sql, /lag\(song_order\.song_id\) over/);
    assert.match(sql, /successor_position::numeric - predecessor_position::numeric <= 1/);
    assert.match(sql, /row_number\(\) over \([\s\S]*?order by song_order\.position, song\.created_at desc, song\.id[\s\S]*?\) \* 1024 as new_position/);
    assert.match(sql, /on conflict \(song_id\) do nothing/);
  }
});

test("public song ordering can only be moved through an admin-protected RPC", () => {
  assert.match(displayOrderMigration, /function public\.move_song_in_public_order/);
  assert.match(displayOrderMigration, /if not public\.is_admin\(\) then/);
  assert.match(displayOrderMigration, /security definer/);
  assert.match(displayOrderMigration, /p_direction not in \(-1, 1\)/);
  assert.match(displayOrderMigration, /lag\(song_order\.song_id\)/);
  assert.match(displayOrderMigration, /lead\(song_order\.song_id\)/);
  assert.match(displayOrderMigration, /grant execute on function public\.move_song_in_public_order\(uuid, integer\) to authenticated/);
  assert.match(displayOrderMigration, /after insert or update of status on public\.songs/);
  assert.match(displayOrderMigration, /on conflict \(song_id\) do nothing/);
});

test("admin user management RPC definitions stay identical across setup and migrations", () => {
  const canonical = adminUserManagementDefinitions(adminUserManagementMigration);
  assert.equal(adminUserManagementDefinitions(setup), canonical);
  assert.equal(adminUserManagementDefinitions(migration), canonical);
  assert.match(adminUserManagementMigration, /^--[\s\S]*?begin;/);
  assert.match(adminUserManagementMigration, /commit;\s*$/);
});

test("admin user listing exposes only safe fields and server-side aggregate pagination", () => {
  const sql = adminUserManagementDefinitions(adminUserManagementMigration);
  assert.match(sql, /returns table \([\s\S]*user_id uuid,[\s\S]*email text,[\s\S]*display_name text,[\s\S]*provider text,[\s\S]*total_count bigint/);
  assert.match(sql, /if not public\.is_admin\(\) then[\s\S]*Administrator access required/);
  assert.match(sql, /from auth\.users as u/);
  assert.match(sql, /with submission_stats as \([\s\S]*count\(\*\) filter \(where s\.status = 'pending'\)/);
  assert.match(sql, /count\(\*\) over\(\)::bigint as total_count/);
  assert.match(sql, /greatest\(1, least\(coalesce\(p_limit, 25\), 100\)\)/);
  assert.match(sql, /normalized_role not in \('', 'admin', 'user'\)/);
  assert.match(sql, /\(fu\.user_id = \(select auth\.uid\(\)\)\) desc,[\s\S]*fu\.is_admin desc,[\s\S]*fu\.last_sign_in_at desc nulls last/);
  assert.doesNotMatch(sql.slice(0, sql.indexOf("create or replace function public.admin_set_user_role")), /encrypted_password|confirmation_token|recovery_token|refresh_token/);
});

test("admin role mutation is guarded, validates targets, and protects the final administrator", () => {
  const sql = adminUserManagementDefinitions(adminUserManagementMigration);
  const mutation = sql.slice(sql.indexOf("create or replace function public.admin_set_user_role"));
  assert.match(mutation, /security definer\s+set search_path = ''/);
  assert.match(mutation, /if not public\.is_admin\(\) then/);
  assert.match(mutation, /not exists \(select 1 from auth\.users as u where u\.id = p_user_id\)/);
  assert.match(mutation, /p_user_id = \(select auth\.uid\(\)\)/);
  assert.match(mutation, /lock table public\.admin_users in share row exclusive mode/);
  assert.match(mutation, /if admin_count <= 1 then[\s\S]*Cannot remove the last administrator/);
  assert.match(mutation, /insert into public\.admin_users \(user_id\)[\s\S]*on conflict \(user_id\) do nothing/);
  assert.match(mutation, /delete from public\.admin_users as au where au\.user_id = p_user_id/);
});

test("admin user management RPCs are executable only by authenticated clients", () => {
  for (const signature of [
    "public.admin_list_users\\(text, text, integer, integer\\)",
    "public.admin_set_user_role\\(uuid, boolean\\)"
  ]) {
    assert.match(adminUserManagementMigration, new RegExp(`revoke all on function ${signature} from public;`));
    assert.match(adminUserManagementMigration, new RegExp(`grant execute on function ${signature} to authenticated;`));
  }
});
