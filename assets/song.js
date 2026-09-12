import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, STORAGE_BUCKET } from "../config.js";
import { SUPABASE_CLIENT_OPTIONS } from "./auth.js";
import { songTagObjects, uploaderDisplayName } from "./catalog.js";
import { findActiveCue, formatCueTime } from "./lyrics-sync.js";
import { PdfViewer } from "./pdf-viewer.js";
import { loadPlaylistContext, playlistContextFromUrl, playlistNeighbors, playlistSchemaUnavailable, playlistSongUrl } from "./playlists.js";
import { YouTubePlayer } from "./youtube-player.js";
import { youtubeThumbnailUrl, youtubeWatchUrl } from "./youtube.js";

const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS);
const $ = (selector) => document.querySelector(selector);
const el = {
  message: $("#songMessage"), loading: $("#songLoading"), content: $("#songContent"), title: $("#songTitle"), artist: $("#songArtist"), meta: $("#songMeta"), uploader: $("#songUploader"), tags: $("#songTags"),
  fallback: $("#youtubeFallbackLink"), playerHost: $("#youtubePlayer"), playerStatus: $("#playerStatus"), playerError: $("#playerError"), time: $("#currentTimeLabel"),
  autoScroll: $("#autoScrollToggle"), lyricsEmpty: $("#lyricsEmpty"), lyrics: $("#lyricsList"),
  filename: $("#pdfFilename"), pdfViewer: $("#songPdfViewer"), openPdf: $("#openSongPdf"), downloadPdf: $("#downloadSongPdf"),
  playlistPanel: $("#playlistPlayerPanel"), playlistName: $("#playlistPanelName"), playlistPosition: $("#playlistPosition"), playlistItems: $("#playlistPanelItems"), previous: $("#previousSongButton"), next: $("#nextSongButton")
};

const VIEWER_SIGNED_URL_TTL_SECONDS = 1800;
const pdfViewer = new PdfViewer(el.pdfViewer, { label: "歌詞 PDF" });

let song;
let cues = [];
let player;
let syncTimer;
let activeCueId = null;
let playlist = null;
let playlistItems = [];
let playlistNavigation = { index: -1, total: 0, previous: null, next: null };

function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function showError(message) {
  el.message.textContent = message;
  el.message.className = "notice error";
  el.loading.classList.add("hidden");
}

function songIdFromUrl() {
  const id = new URL(window.location.href).searchParams.get("id") || "";
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id) ? id : null;
}

async function signedPdfUrl(download = false, expiresIn = 600) {
  const options = download ? { download: song.original_filename } : undefined;
  const { data, error } = await supabase.storage.from(STORAGE_BUCKET).createSignedUrl(song.pdf_path, expiresIn, options);
  if (error) throw error;
  return data.signedUrl;
}

function renderSong() {
  document.title = `${song.title}｜歌曲歌詞 PDF 資料庫`;
  el.title.textContent = song.title;
  el.artist.textContent = song.artist;
  el.meta.textContent = [song.album, song.release_year, song.language, song.genre].filter(Boolean).join(" · ") || "尚無其他歌曲資訊";
  el.uploader.textContent = `上傳者：${uploaderDisplayName(song)}`;
  el.filename.textContent = song.original_filename;
  el.fallback.href = youtubeWatchUrl(song.youtube_video_id);
  el.tags.replaceChildren(...songTagObjects(song).map((tag) => {
    const link = node("a", "tag-chip", `#${tag.name}`);
    link.href = `./?tag=${encodeURIComponent(tag.slug)}`;
    return link;
  }));
}

function renderLyrics() {
  el.lyricsEmpty.classList.toggle("hidden", cues.length !== 0);
  el.lyrics.replaceChildren(...cues.map((cue) => {
    const item = document.createElement("li");
    item.dataset.cueId = String(cue.id);
    const button = node("button", "lyric-line");
    button.type = "button";
    button.append(node("span", "lyric-time", formatCueTime(cue.start_ms)), node("span", "lyric-text", cue.text));
    button.addEventListener("click", () => { player?.seekTo(cue.start_ms); updateSync(cue.start_ms); });
    item.append(button);
    return item;
  }));
}

function playlistSong(item) {
  return Array.isArray(item.songs) ? item.songs[0] : item.songs;
}

function navigatePlaylistItem(item) {
  if (item) window.location.href = playlistSongUrl(item.song_id, playlist.id);
}

function renderPlaylistContext() {
  if (!playlist || playlistNavigation.index < 0) return;
  el.playlistName.textContent = playlist.name;
  el.playlistPosition.textContent = `${playlistNavigation.index + 1} / ${playlistNavigation.total}`;
  el.previous.disabled = !playlistNavigation.previous;
  el.next.disabled = !playlistNavigation.next;
  el.previous.onclick = () => navigatePlaylistItem(playlistNavigation.previous);
  el.next.onclick = () => navigatePlaylistItem(playlistNavigation.next);
  el.playlistItems.replaceChildren(...playlistItems.map((item) => {
    const playlistItemSong = playlistSong(item);
    const current = item.song_id === song.id;
    const row = node("li", `playlist-panel-item${current ? " is-current" : ""}`);
    if (current) row.setAttribute("aria-current", "true");
    const link = node("a", "playlist-panel-link");
    link.href = playlistSongUrl(item.song_id, playlist.id);
    const thumbnail = document.createElement("img");
    thumbnail.src = youtubeThumbnailUrl(playlistItemSong.youtube_video_id);
    thumbnail.alt = "";
    thumbnail.loading = "lazy";
    const label = node("span", "playlist-panel-copy");
    label.append(node("strong", "", playlistItemSong.title), node("small", "", playlistItemSong.artist));
    link.append(thumbnail, label);
    row.append(link);
    return row;
  }));
  el.playlistPanel.classList.remove("hidden");
}

function updateSync(forcedTime = null) {
  const current = forcedTime ?? player?.getCurrentTimeMs() ?? 0;
  el.time.textContent = formatCueTime(current);
  const active = findActiveCue(cues, current);
  const nextId = active?.id ?? null;
  if (nextId === activeCueId) return;
  activeCueId = nextId;
  for (const item of el.lyrics.children) {
    const isActive = item.dataset.cueId === String(nextId);
    item.classList.toggle("active", isActive);
    const button = item.querySelector("button");
    if (isActive) button.setAttribute("aria-current", "true"); else button.removeAttribute("aria-current");
    if (isActive && el.autoScroll.checked) item.scrollIntoView({ block: "center", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }
}

function startSync() {
  clearInterval(syncTimer);
  syncTimer = setInterval(() => updateSync(), 250);
}

async function setupPlayer() {
  player = new YouTubePlayer(el.playerHost, song.youtube_video_id, {
    onReady: () => { el.playerStatus.textContent = "播放器已就緒，請按播放。"; startSync(); },
    onStateChange: (state) => {
      if (state === 1) el.playerStatus.textContent = "播放中";
      else if (state === 2) el.playerStatus.textContent = "已暫停";
      else if (state === 0) {
        updateSync();
        if (playlistNavigation.next) {
          el.playerStatus.textContent = "即將播放下一首…";
          navigatePlaylistItem(playlistNavigation.next);
        } else if (playlist) {
          el.playerStatus.textContent = "播放清單已播放完畢";
        } else {
          el.playerStatus.textContent = "播放完畢";
        }
      }
      else if (state === 3) el.playerStatus.textContent = "緩衝中…";
    },
    onError: () => { el.playerError.classList.remove("hidden"); el.playerStatus.textContent = "影片無法嵌入"; }
  });
  try { await player.create(); }
  catch (error) { el.playerError.classList.remove("hidden"); el.playerStatus.textContent = error.message; }
}

async function load() {
  const id = songIdFromUrl();
  if (!id) return showError("歌曲網址缺少有效的 id。");
  const playlistId = playlistContextFromUrl(window.location.href);
  const [songResult, cueResult, sessionResult] = await Promise.all([
    supabase.from("songs").select("id,title,artist,album,release_year,language,genre,notes,youtube_video_id,pdf_path,original_filename,uploader_id,uploader_display_name,status,song_tags(tags(id,name,slug))").eq("id", id).single(),
    supabase.from("lyric_cues").select("id,line_index,start_ms,end_ms,text").eq("song_id", id).order("line_index"),
    supabase.auth.getSession()
  ]);
  if (songResult.error) return showError(songResult.error.message || "無法載入歌曲；歌曲可能尚未通過審核。");
  if (cueResult.error) return showError(cueResult.error.message || "無法載入同步歌詞。");
  song = songResult.data;
  cues = cueResult.data || [];
  if (playlistId && sessionResult.data?.session?.user) {
    const context = await loadPlaylistContext(supabase, playlistId);
    if (!context.error && context.playlist) {
      const navigation = playlistNeighbors(context.items, id);
      if (navigation.index >= 0) {
        playlist = context.playlist;
        playlistItems = context.items;
        playlistNavigation = navigation;
      }
    } else if (playlistSchemaUnavailable(context.error)) {
      console.warn("Playlist database migration is not deployed; continuing in single-song mode.");
    }
  }
  renderSong(); renderLyrics();
  renderPlaylistContext();
  try {
    [el.openPdf.href, el.downloadPdf.href] = await Promise.all([signedPdfUrl(false, VIEWER_SIGNED_URL_TTL_SECONDS), signedPdfUrl(true)]);
  } catch (error) { showError(error.message || "無法建立 PDF 連結。"); return; }
  el.loading.classList.add("hidden"); el.content.classList.remove("hidden");
  try { await pdfViewer.load(el.openPdf.href); }
  catch (error) { showError(error.message || "無法載入 PDF，請使用另開或下載。"); }
  await setupPlayer();
}

window.addEventListener("beforeunload", () => { clearInterval(syncTimer); player?.destroy(); void pdfViewer.dispose(); });

load();
