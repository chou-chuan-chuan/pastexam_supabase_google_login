import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

async function source(path) {
  return readFile(new URL(`../${path}`, import.meta.url), "utf8");
}

test("playlist pages and their expected modules exist", async () => {
  const [listPage, detailPage, listScript, fixture] = await Promise.all([source("playlists.html"), source("playlist.html"), source("assets/playlists-page.js"), source("tools/playlist-fixture.html")]);
  assert.match(listPage, /assets\/playlists-page\.js/);
  assert.match(detailPage, /assets\/playlist-page\.js/);
  assert.match(detailPage, /playlistDetailEmpty/);
  assert.match(listScript, /node\("button", "button secondary", "編輯"\)/);
  assert.doesNotMatch(`${listScript}\n${fixture}`, /重新命名 \/ 編輯/);
});

test("public song cards expose the add-to-playlist action without eager membership loading", async () => {
  const app = await source("assets/app.js");
  const songCard = app.slice(app.indexOf("function songCard"), app.indexOf("function playlistChoice"));
  assert.match(app, /加入播放清單/);
  assert.match(songCard, /預覽 \/ 下載 PDF/);
  assert.doesNotMatch(songCard, /node\("button", "button secondary", "下載 PDF"\)/);
  assert.doesNotMatch(app, /function downloadSongPdf/);
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
  assert.match(song, /\{ autoplay: Boolean\(playlist\) \}/);
  assert.match(song, /if \(playlist\)[\s\S]*player\.play\(\)/);
  assert.match(song, /onAutoplayBlocked:[\s\S]*playlistMutedAutoplayFallbackAttempted[\s\S]*player\.mute\(\)[\s\S]*player\.play\(\)/);
  assert.match(song, /if \(playlistMutedAutoplayFallbackAttempted\)[\s\S]*自動播放受瀏覽器限制，請按播放/);
});

test("current playlist styling uses a soft symmetric highlight without an inset left rail", async () => {
  const style = await source("assets/style.css");
  const rule = style.match(/\.playlist-panel-item\.is-current\s*\{[^}]+\}/)?.[0] || "";
  assert.match(rule, /background:\s*#f0e8fb/);
  assert.match(rule, /border-color:/);
  assert.doesNotMatch(rule, /inset|border-left|::before/);
});

test("playlist clients contain no service role or YouTube Data API integration", async () => {
  const combined = (await Promise.all([
    source("assets/playlists.js"), source("assets/playlists-page.js"), source("assets/playlist-page.js"), source("assets/song.js")
  ])).join("\n");
  assert.doesNotMatch(combined, /service_role/i);
  assert.doesNotMatch(combined, /youtubeapis\.com|youtube data api/i);
  assert.doesNotMatch(combined, /\.innerHTML\s*=/);
});
