import test from "node:test";
import assert from "node:assert/strict";

import {
  isUuid,
  normalizePlaylistMembership,
  playlistContextFromUrl,
  playlistNeighbors,
  playlistSongCount,
  playlistSongUrl,
  sortPlaylistItems
} from "../assets/playlists.js";

const PLAYLIST_ID = "123e4567-e89b-42d3-a456-426614174000";
const SONG_A = "123e4567-e89b-42d3-a456-426614174001";
const SONG_B = "123e4567-e89b-42d3-a456-426614174002";
const SONG_C = "123e4567-e89b-42d3-a456-426614174003";

test("parses only valid playlist UUID context and builds playlist song URLs", () => {
  assert.equal(playlistContextFromUrl(`https://example.test/song.html?id=${SONG_A}&playlist=${PLAYLIST_ID}`), PLAYLIST_ID);
  assert.equal(playlistContextFromUrl("https://example.test/song.html?playlist=not-a-uuid"), null);
  assert.equal(playlistContextFromUrl("https://example.test/song.html"), null);
  assert.equal(playlistSongUrl(SONG_A, PLAYLIST_ID), `./song.html?id=${SONG_A}&playlist=${PLAYLIST_ID}`);
  assert.equal(playlistSongUrl(SONG_A, "invalid"), `./song.html?id=${SONG_A}`);
  assert.equal(isUuid(PLAYLIST_ID), true);
});

test("orders items by persistent position with a deterministic tie break", () => {
  const ordered = sortPlaylistItems([
    { song_id: SONG_C, position: 3072 },
    { song_id: SONG_B, position: 1024 },
    { song_id: SONG_A, position: 1024 }
  ]);
  assert.deepEqual(ordered.map((item) => item.song_id), [SONG_A, SONG_B, SONG_C]);
});

test("resolves previous and next items and safe boundaries", () => {
  const items = [
    { song_id: SONG_A, position: 1024 },
    { song_id: SONG_B, position: 2048 },
    { song_id: SONG_C, position: 3072 }
  ];
  assert.deepEqual(playlistNeighbors(items, SONG_A), { index: 0, total: 3, previous: null, next: items[1] });
  assert.deepEqual(playlistNeighbors(items, SONG_B), { index: 1, total: 3, previous: items[0], next: items[2] });
  assert.deepEqual(playlistNeighbors(items, SONG_C), { index: 2, total: 3, previous: items[1], next: null });
  assert.deepEqual(playlistNeighbors(items, PLAYLIST_ID), { index: -1, total: 3, previous: null, next: null });
});

test("normalizes duplicate membership rows and playlist counts", () => {
  assert.deepEqual(normalizePlaylistMembership([
    { playlist_id: PLAYLIST_ID },
    { playlist_id: PLAYLIST_ID },
    { playlist_id: "invalid" },
    null
  ]), [PLAYLIST_ID]);
  assert.equal(playlistSongCount({ playlist_items: [{ count: 4 }] }), 4);
  assert.equal(playlistSongCount({ playlist_items: [] }), 0);
});
