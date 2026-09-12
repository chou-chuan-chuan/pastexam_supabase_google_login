import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

async function source(path) {
  return readFile(new URL(`../${path}`, import.meta.url), "utf8");
}

test("playlist pages and their expected modules exist", async () => {
  const [listPage, detailPage] = await Promise.all([source("playlists.html"), source("playlist.html")]);
  assert.match(listPage, /assets\/playlists-page\.js/);
  assert.match(detailPage, /assets\/playlist-page\.js/);
  assert.match(detailPage, /playlistDetailEmpty/);
});

test("public song cards expose the add-to-playlist action without eager membership loading", async () => {
  const app = await source("assets/app.js");
  assert.match(app, /加入播放清單/);
  assert.match(app, /openAddPlaylist\(song\)/);
  assert.match(app, /from\("playlist_items"\)\.select\("playlist_id"\)\.eq\("song_id", song\.id\)/);
  assert.doesNotMatch(app.slice(0, app.indexOf("async function openAddPlaylist")), /from\("playlist_items"\)\.select\("playlist_id"\)/);
});

test("song page recognizes playlist context and advances on YouTube ENDED", async () => {
  const [page, song] = await Promise.all([source("song.html"), source("assets/song.js")]);
  assert.match(page, /playlistPlayerPanel/);
  assert.match(song, /playlistContextFromUrl\(window\.location\.href\)/);
  assert.match(song, /state === 0[\s\S]*playlistNavigation\.next[\s\S]*navigatePlaylistItem\(playlistNavigation\.next\)/);
  assert.match(song, /播放清單已播放完畢/);
  assert.match(song, /aria-current/);
});

test("playlist clients contain no service role or YouTube Data API integration", async () => {
  const combined = (await Promise.all([
    source("assets/playlists.js"), source("assets/playlists-page.js"), source("assets/playlist-page.js"), source("assets/song.js")
  ])).join("\n");
  assert.doesNotMatch(combined, /service_role/i);
  assert.doesNotMatch(combined, /youtubeapis\.com|youtube data api/i);
  assert.doesNotMatch(combined, /\.innerHTML\s*=/);
});
