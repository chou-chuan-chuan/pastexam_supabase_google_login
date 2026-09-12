import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY } from "../config.js";
import { SUPABASE_CLIENT_OPTIONS } from "./auth.js";
import { isUuid, loadPlaylistContext, playlistSchemaUnavailable, playlistSongUrl } from "./playlists.js";
import { youtubeThumbnailUrl } from "./youtube.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS) : null;
const $ = (selector) => document.querySelector(selector);
const el = { message: $("#playlistDetailMessage"), loading: $("#playlistDetailLoading"), detail: $("#playlistDetail"), name: $("#playlistDetailName"), description: $("#playlistDetailDescription"), count: $("#playlistDetailCount"), play: $("#playPlaylistButton"), list: $("#playlistItemList"), empty: $("#playlistDetailEmpty") };
let playlist = null;
let items = [];
let moving = false;

function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function showMessage(text, kind = "error") {
  el.message.textContent = text;
  el.message.className = `notice ${kind}`;
  el.loading.classList.add("hidden");
}

function songFor(item) {
  return Array.isArray(item.songs) ? item.songs[0] : item.songs;
}

function playlistItem(item, index) {
  const song = songFor(item);
  const row = node("article", "playlist-item");
  const thumbnail = document.createElement("img");
  thumbnail.className = "playlist-item-thumbnail";
  thumbnail.src = youtubeThumbnailUrl(song.youtube_video_id);
  thumbnail.alt = `${song.title} 的 YouTube 縮圖`;
  thumbnail.loading = "lazy";
  const content = node("div", "playlist-item-content");
  content.append(node("h2", "", song.title), node("p", "song-artist", song.artist));
  const details = [song.language, song.genre].filter(Boolean).join(" · ");
  if (details) content.append(node("p", "card-meta", details));
  const actions = node("div", "playlist-item-actions");
  const play = node("a", "button primary", "播放");
  play.href = playlistSongUrl(item.song_id, playlist.id);
  play.setAttribute("aria-label", `播放「${song.title}」`);
  const order = node("div", "playlist-order-controls");
  const up = node("button", "button secondary", "↑");
  up.type = "button"; up.disabled = moving || index === 0; up.setAttribute("aria-label", `將「${song.title}」往前移`); up.addEventListener("click", () => moveItem(item.song_id, -1));
  const down = node("button", "button secondary", "↓");
  down.type = "button"; down.disabled = moving || index === items.length - 1; down.setAttribute("aria-label", `將「${song.title}」往後移`); down.addEventListener("click", () => moveItem(item.song_id, 1));
  order.append(up, down);
  const remove = node("button", "button danger", "移除");
  remove.type = "button"; remove.setAttribute("aria-label", `從播放清單移除「${song.title}」`); remove.addEventListener("click", () => removeItem(item, song));
  actions.append(play, order, remove);
  row.append(thumbnail, content, actions);
  return row;
}

function render() {
  document.title = `${playlist.name}｜播放清單｜歌曲歌詞 PDF 資料庫`;
  el.name.textContent = playlist.name;
  el.description.textContent = playlist.description || "尚無描述";
  el.count.textContent = `${items.length} 首歌曲`;
  el.play.disabled = items.length === 0;
  el.play.onclick = () => { if (items[0]) window.location.href = playlistSongUrl(items[0].song_id, playlist.id); };
  el.list.replaceChildren(...items.map(playlistItem));
  el.list.classList.toggle("hidden", items.length === 0);
  el.empty.classList.toggle("hidden", items.length !== 0);
  el.loading.classList.add("hidden");
  el.detail.classList.remove("hidden");
}

async function reload() {
  const result = await loadPlaylistContext(supabase, playlist.id);
  if (result.error || !result.playlist) return showMessage(result.error?.message || "無法載入播放清單。這個清單可能不存在或不屬於你。");
  playlist = result.playlist;
  items = result.items;
  render();
}

async function moveItem(songId, direction) {
  if (moving) return;
  moving = true; render();
  const { error } = await supabase.rpc("move_playlist_item", { p_playlist_id: playlist.id, p_song_id: songId, p_direction: direction });
  moving = false;
  if (error) { showMessage(error.message || "無法調整歌曲順序。"); render(); return; }
  await reload();
}

async function removeItem(item, song) {
  if (!confirm(`確定從播放清單移除「${song.title}」？`)) return;
  const { error } = await supabase.from("playlist_items").delete().eq("playlist_id", playlist.id).eq("song_id", item.song_id);
  if (error) return showMessage(error.message || "無法從播放清單移除歌曲。");
  showMessage("歌曲已從播放清單移除；歌曲資料不受影響。", "success");
  await reload();
}

async function init() {
  const playlistId = new URL(window.location.href).searchParams.get("id");
  if (!configured) return showMessage("請先完成 Supabase 設定。", "warning");
  if (!isUuid(playlistId)) return showMessage("播放清單網址缺少有效的 id。");
  const { data } = await supabase.auth.getSession();
  if (!data?.session?.user) return showMessage("登入後即可查看自己的播放清單。", "info");
  const result = await loadPlaylistContext(supabase, playlistId);
  if (result.error || !result.playlist) {
    return showMessage(playlistSchemaUnavailable(result.error) ? "播放清單功能尚未完成資料庫部署。" : "無法載入播放清單。這個清單可能不存在或不屬於你。");
  }
  playlist = result.playlist;
  items = result.items;
  render();
}

init();
