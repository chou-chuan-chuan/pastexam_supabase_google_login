import test from "node:test";
import assert from "node:assert/strict";

import {
  isUuid,
  isSmartPlaylistContext,
  loadPlaylistContext,
  normalizePlaylistMembership,
  playlistContextFromUrl,
  playlistNeighbors,
  playlistSongCount,
  playlistSongUrl,
  smartPlaylistCards,
  smartPlaylistContextFromUrl,
  smartPlaylistItems,
  smartPlaylistUrl,
  sortPlaylistItems
} from "../assets/playlists.js";

const PLAYLIST_ID = "123e4567-e89b-42d3-a456-426614174000";
const SONG_A = "123e4567-e89b-42d3-a456-426614174001";
const SONG_B = "123e4567-e89b-42d3-a456-426614174002";
const SONG_C = "123e4567-e89b-42d3-a456-426614174003";
// Existing production Favorite tag id, confirmed by the maintainer.
const FAVORITE_TAG_ID = "92f53132-743b-4032-8d9a-df893f5a4f8c";
const FAVORITE_TAG = { id: FAVORITE_TAG_ID, name: "Favorite", slug: "favorite" };

test("parses only valid playlist UUID context and builds playlist song URLs", () => {
  assert.equal(playlistContextFromUrl(`https://example.test/song.html?id=${SONG_A}&playlist=${PLAYLIST_ID}`), PLAYLIST_ID);
  assert.equal(playlistContextFromUrl("https://example.test/song.html?playlist=not-a-uuid"), null);
  assert.equal(playlistContextFromUrl("https://example.test/song.html"), null);
  assert.equal(playlistSongUrl(SONG_A, PLAYLIST_ID), `./song.html?id=${SONG_A}&playlist=${PLAYLIST_ID}`);
  assert.equal(playlistSongUrl(SONG_A, "invalid"), `./song.html?id=${SONG_A}`);
  assert.equal(isUuid(PLAYLIST_ID), true);
});

test("parses and preserves language and favorite smart playlist URLs", () => {
  const language = { type: "language", value: "French" };
  const favorite = { type: "smart", value: "my-favorite" };
  assert.deepEqual(playlistContextFromUrl("https://example.test/song.html?language=French"), language);
  assert.deepEqual(smartPlaylistContextFromUrl("https://example.test/playlist.html?language=%20French%20"), language);
  assert.deepEqual(playlistContextFromUrl("https://example.test/song.html?smart=my-favorite"), favorite);
  assert.equal(isSmartPlaylistContext(language), true);
  assert.equal(playlistSongUrl(SONG_A, language), `./song.html?id=${SONG_A}&language=French`);
  assert.equal(playlistSongUrl(SONG_A, favorite), `./song.html?id=${SONG_A}&smart=my-favorite`);
  assert.equal(smartPlaylistUrl(language), "./playlist.html?language=French");
  assert.equal(smartPlaylistUrl(favorite), "./playlist.html?smart=my-favorite");
});

test("smart playlist cards include only approved, nonblank language groups and put Favorite first", () => {
  const songs = [
    { id: SONG_A, status: "approved", language: " French ", created_at: "2024-01-01", song_tags: [{ tag_id: FAVORITE_TAG_ID }] },
    { id: SONG_B, status: "approved", language: "", created_at: "2024-01-02", song_tags: [] },
    { id: SONG_C, status: "pending", language: "French", created_at: "2024-01-03", song_tags: [{ tag_id: FAVORITE_TAG_ID }] },
    { id: PLAYLIST_ID, status: "approved", language: null, created_at: "2024-01-04", song_tags: [{ tags: { slug: "other", name: "My favorite" } }] }
  ];
  const cards = smartPlaylistCards(songs, [], [FAVORITE_TAG]);
  assert.deepEqual(cards.map((card) => [card.name, card.song_count]), [["Favorite", 1], ["French", 1]]);
});

test("language and My favorite smart playlists filter approved songs and retain catalog order", () => {
  const songs = [
    { id: SONG_A, status: "approved", language: "French", created_at: "2024-01-01", song_tags: [] },
    { id: SONG_B, status: "approved", language: "French", created_at: "2024-01-02", song_tags: [{ tag_id: FAVORITE_TAG_ID }] },
    { id: SONG_C, status: "rejected", language: "French", created_at: "2024-01-03", song_tags: [{ tag_id: FAVORITE_TAG_ID }] }
  ];
  const order = [{ song_id: SONG_A, position: 2048 }, { song_id: SONG_B, position: 1024 }, { song_id: SONG_C, position: 1 }];
  const languageItems = smartPlaylistItems(songs, order, { type: "language", value: "French" });
  const favoriteItems = smartPlaylistItems(songs, order, { type: "smart", value: "my-favorite" });
  assert.deepEqual(languageItems.map((item) => item.song_id), [SONG_B, SONG_A]);
  assert.deepEqual(favoriteItems.map((item) => item.song_id), [SONG_B]);
  assert.deepEqual(playlistNeighbors(languageItems, SONG_A), { index: 1, total: 2, previous: languageItems[0], next: null });
});

test("Favorite uses the existing tag id, including when tag metadata is not public", () => {
  const context = { type: "smart", value: "my-favorite" };
  const songs = [
    { id: SONG_A, status: "approved", song_tags: [{ tag_id: FAVORITE_TAG_ID, tags: null }] },
    { id: SONG_B, status: "approved", song_tags: [{ tag_id: SONG_B, tags: { name: "Favorite", slug: "my-favorite" } }] },
    { id: SONG_C, status: "pending", song_tags: [{ tag_id: FAVORITE_TAG_ID }] },
    { id: PLAYLIST_ID, status: "rejected", song_tags: [{ tag_id: FAVORITE_TAG_ID }] }
  ];
  assert.deepEqual(smartPlaylistItems(songs, [], context).map((item) => item.song_id), [SONG_A]);
  assert.equal(smartPlaylistCards(songs, [], [FAVORITE_TAG])[0].song_count, 1);
});

test("Favorite reload reflects tag addition/removal and approval changes without playlist writes", async () => {
  const context = { type: "smart", value: "my-favorite" };
  const song = { id: SONG_A, status: "approved", song_tags: [] };
  const client = {
    from(table) {
      if (table === "song_display_order") return { select: () => ({ data: [], error: null }) };
      if (table === "tags") return { select: () => ({ data: [FAVORITE_TAG], error: null }) };
      assert.equal(table, "songs");
      return { select(fields) {
        assert.match(fields, /song_tags\(tag_id\)/);
        return { eq(column, value) {
          assert.deepEqual([column, value], ["status", "approved"]);
          return { data: [song], error: null };
        } };
      } };
    }
  };
  const memberIds = async () => (await loadPlaylistContext(client, context)).items.map((item) => item.song_id);
  assert.deepEqual(await memberIds(), []);
  song.song_tags = [{ tag_id: FAVORITE_TAG_ID }];
  assert.deepEqual(await memberIds(), [SONG_A]);
  song.song_tags = [];
  assert.deepEqual(await memberIds(), []);
  song.song_tags = [{ tag_id: FAVORITE_TAG_ID }];
  for (const status of ["pending", "rejected"]) {
    song.status = status;
    assert.deepEqual(await memberIds(), []);
  }
  song.status = "approved";
  assert.deepEqual(await memberIds(), [SONG_A]);
});

test("orders items by persistent position with a deterministic tie break", () => {
  const ordered = sortPlaylistItems([
    { song_id: SONG_C, position: 3072 },
    { song_id: SONG_B, position: 1024 },
    { song_id: SONG_A, position: 1024 }
  ]);
  assert.deepEqual(ordered.map((item) => item.song_id), [SONG_A, SONG_B, SONG_C]);
});

test("every readable tag gets one card, including newly created empty tags, using its current name", () => {
  const custom = { id: PLAYLIST_ID, name: "練習 & 合唱", slug: "practice" };
  const songs = [{ id: SONG_A, status: "pending", song_tags: [{ tag_id: custom.id }] }];
  const cards = smartPlaylistCards(songs, [], [custom, FAVORITE_TAG]);
  assert.deepEqual(cards.map((card) => [card.name, card.song_count]), [["Favorite", 0], ["練習 & 合唱", 0]]);
  assert.deepEqual(cards[1].context, { type: "tag", value: custom.id });
  assert.equal(cards.filter((card) => card.context.value === FAVORITE_TAG_ID).length, 1);
  assert.deepEqual(smartPlaylistCards([], [], []), []);
});

test("tag URLs round trip and reject malformed ids while retaining private and language routes", () => {
  const context = { type: "tag", value: PLAYLIST_ID };
  assert.equal(isSmartPlaylistContext(context), true);
  assert.equal(smartPlaylistUrl(context), `./playlist.html?tag=${PLAYLIST_ID}`);
  assert.equal(playlistSongUrl(SONG_A, context), `./song.html?id=${SONG_A}&tag=${PLAYLIST_ID}`);
  assert.deepEqual(playlistContextFromUrl(new URL(playlistSongUrl(SONG_A, context), "https://example.test").href), context);
  assert.deepEqual(smartPlaylistContextFromUrl(`https://example.test/playlist.html?tag=${PLAYLIST_ID}`), context);
  assert.equal(smartPlaylistContextFromUrl("https://example.test/playlist.html?tag=not-a-uuid"), null);
  assert.equal(isSmartPlaylistContext({ type: "tag", value: "not-a-uuid" }), false);
});

test("custom tag membership changes dynamically, keeps catalog order and provides accurate neighbors", () => {
  const context = { type: "tag", value: PLAYLIST_ID };
  const songs = [SONG_A, SONG_B, SONG_C].map((id) => ({ id, status: "approved", song_tags: [{ tag_id: PLAYLIST_ID }] }));
  const order = [{ song_id: SONG_A, position: 3 }, { song_id: SONG_B, position: 1 }, { song_id: SONG_C, position: 2 }];
  const items = smartPlaylistItems(songs, order, context);
  assert.deepEqual(items.map((item) => item.song_id), [SONG_B, SONG_C, SONG_A]);
  assert.deepEqual(playlistNeighbors(items, SONG_C), { index: 1, total: 3, previous: items[0], next: items[2] });
  songs[0].song_tags = [];
  songs[1].status = "pending";
  songs[2].status = "rejected";
  assert.deepEqual(smartPlaylistItems(songs, order, context), []);
  songs[1].status = "approved";
  assert.deepEqual(smartPlaylistItems(songs, order, context).map((item) => item.song_id), [SONG_B]);
});

test("tag detail and legacy Favorite context use live tag names and handle deletion or read errors", async () => {
  const custom = { id: PLAYLIST_ID, name: "練習", slug: "practice" };
  let tags = [custom, { ...FAVORITE_TAG }];
  let error = null;
  const client = { from(table) {
    if (table === "tags") return { select: () => ({ data: tags, error }) };
    if (table === "song_display_order") return { select: () => ({ data: [], error: null }) };
    assert.equal(table, "songs");
    return { select: () => ({ eq: () => ({ data: [], error: null }) }) };
  } };
  const context = { type: "tag", value: custom.id };
  assert.equal((await loadPlaylistContext(client, context)).playlist.name, "練習");
  custom.name = "演唱會";
  custom.slug = "concert";
  const renamed = await loadPlaylistContext(client, context);
  assert.equal(renamed.playlist.name, "演唱會");
  assert.deepEqual(renamed.playlist.context, context);
  assert.equal(smartPlaylistCards([], [], tags).find((card) => card.context.value === custom.id).name, "演唱會");
  tags[1].name = "最愛";
  assert.equal((await loadPlaylistContext(client, { type: "smart", value: "my-favorite" })).playlist.name, "最愛");
  tags = [];
  assert.equal((await loadPlaylistContext(client, context)).playlist, null);
  error = { message: "network error" };
  assert.equal((await loadPlaylistContext(client, context)).error, error);
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
