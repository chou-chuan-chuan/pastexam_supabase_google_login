import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, STORAGE_BUCKET, MAX_FILE_SIZE_BYTES } from "../config.js";
import { SUPABASE_CLIENT_OPTIONS, cleanOAuthCallbackFromBrowser, oauthRedirectUrl, parseOAuthResponse, verifyGoogleAuthConfiguration } from "./auth.js";
import { filterSongs, pendingSongPayload, songTagObjects, sortSongsForDisplay, uploaderDisplayName } from "./catalog.js";
import { PdfReplacementError, updateSongWithOptionalPdf } from "./pdf-replacement.js";
import { PdfViewer } from "./pdf-viewer.js";
import { loadUserPlaylists, normalizePlaylistMembership, playlistSchemaUnavailable } from "./playlists.js";
import { extractYouTubeVideoId, normalizeYouTubeUrl, youtubeThumbnailUrl } from "./youtube.js";
import { approvedMetadataValues, hasMeaningfulUploadMetadata, songReferenceSearch } from "./song-reference.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS) : null;
const $ = (selector) => document.querySelector(selector);

const el = {
  setupNotice: $("#setupNotice"), messageBox: $("#messageBox"), userLabel: $("#userLabel"),
  signIn: $("#googleSignInButton"), signOut: $("#signOutButton"), playlistsLink: $("#playlistsPageLink"), adminLink: $("#adminPageLink"), openUpload: $("#openUploadButton"),
  search: $("#searchInput"), language: $("#languageFilter"), genre: $("#genreFilter"), year: $("#yearFilter"),
  tagFilters: $("#tagFilterList"), clearFilters: $("#clearFiltersButton"), refresh: $("#refreshButton"), total: $("#totalCount"), description: $("#listDescription"),
  loading: $("#loadingState"), grid: $("#songGrid"), empty: $("#emptyState"),
  previewDialog: $("#previewDialog"), previewTitle: $("#previewTitle"), previewViewer: $("#pdfPreviewViewer"), closePreview: $("#closePreviewButton"), closePreviewFooter: $("#closePreviewFooterButton"), openPdf: $("#openPdfButton"), downloadPdf: $("#downloadPdfButton"),
  uploadDialog: $("#uploadDialog"), uploadForm: $("#uploadForm"), uploadTitle: $("#uploadTitle"), uploadArtist: $("#uploadArtist"), uploadAlbum: $("#uploadAlbum"), uploadYear: $("#uploadYear"), uploadLanguage: $("#uploadLanguage"), uploadGenre: $("#uploadGenre"), uploadYoutube: $("#uploadYoutube"), uploadYoutubeStatus: $("#uploadYoutubeStatus"), uploadYoutubePreview: $("#uploadYoutubePreview"), uploadYoutubeThumbnail: $("#uploadYoutubeThumbnail"), uploadYoutubeVideoId: $("#uploadYoutubeVideoId"), uploadTags: $("#uploadTagChoices"), uploadNotes: $("#uploadNotes"), uploadPdf: $("#uploadPdf"), maxFileSize: $("#maxFileSizeLabel"), uploadProgress: $("#uploadProgress"), submitUpload: $("#submitUploadButton"),
  uploadReference: $("#uploadReference"), uploadReferenceInput: $("#uploadReferenceInput"), uploadReferenceOptions: $("#uploadReferenceOptions"), uploadReferenceStatus: $("#uploadReferenceStatus"), clearUploadReference: $("#clearUploadReference"),
  editDialog: $("#editDialog"), editForm: $("#editForm"), editSongId: $("#editSongId"), editTitle: $("#editTitle"), editArtist: $("#editArtist"), editAlbum: $("#editAlbum"), editYear: $("#editYear"), editLanguage: $("#editLanguage"), editGenre: $("#editGenre"), editYoutube: $("#editYoutube"), editTags: $("#editTagChoices"), editNotes: $("#editNotes"), editPdf: $("#editPdf"), editCurrentPdf: $("#editCurrentPdf"), editProgress: $("#editProgress"), saveEdit: $("#saveEditButton"),
  addPlaylistDialog: $("#addPlaylistDialog"), addPlaylistSong: $("#addPlaylistSong"), playlistChoices: $("#playlistChoiceList"), closeAddPlaylist: $("#closeAddPlaylistButton"), inlinePlaylistForm: $("#inlinePlaylistForm"), inlinePlaylistName: $("#inlinePlaylistName"), inlinePlaylistDescription: $("#inlinePlaylistDescription"), createAndAddPlaylist: $("#createAndAddPlaylistButton")
};

const VIEWER_SIGNED_URL_TTL_SECONDS = 1800;
const pdfPreview = new PdfViewer(el.previewViewer, { label: "歌詞 PDF 預覽" });

let currentUser = null;
let isAdmin = false;
let songs = [];
let tags = [];
let displayOrderAvailable = false;
let orderMoveBusy = false;
let authQueue = Promise.resolve();
let appliedAuthUserId;
let messageTimer;
let initialTagSlug = new URL(window.location.href).searchParams.get("tag");
let addPlaylistSong = null;
let approvedReferenceSongs = [];
let uploadReferenceMatches = [];
let activeReferenceIndex = -1;

const uploadMetadataInputs = {
  title: el.uploadTitle, artist: el.uploadArtist, album: el.uploadAlbum,
  release_year: el.uploadYear, language: el.uploadLanguage, genre: el.uploadGenre,
  youtube_url: el.uploadYoutube
};

function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function showMessage(text, kind = "info", timeout = 7000) {
  clearTimeout(messageTimer);
  el.messageBox.textContent = text;
  el.messageBox.className = `notice ${kind}`;
  if (timeout) messageTimer = setTimeout(() => el.messageBox.classList.add("hidden"), timeout);
}

function errorMessage(error, fallback) {
  console.error(error);
  return error?.message || fallback;
}

function safeFilename(name) {
  return name.normalize("NFKD").replace(/[^\w.\-]+/g, "_").replace(/_+/g, "_") || "lyrics.pdf";
}

function maximumFileSizeText() {
  const mb = MAX_FILE_SIZE_BYTES / (1024 * 1024);
  return `${Number.isInteger(mb) ? mb : mb.toFixed(1)} MB`;
}

function selectedTagIds(container) {
  return [...container.querySelectorAll('input[type="checkbox"]:checked')].map((input) => input.value);
}

function renderTagChoices(container, selected = []) {
  const selectedSet = new Set(selected);
  const content = tags.map((tag) => {
    const label = node("label", "tag-choice");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = tag.id;
    input.checked = selectedSet.has(tag.id);
    label.append(input, node("span", "", tag.name));
    return label;
  });
  container.replaceChildren(...(content.length ? content : [node("span", "muted", "尚無可用標籤。") ]));
}

function renderTagFilters() {
  const selected = new Set(selectedTagIds(el.tagFilters));
  const choices = tags.map((tag) => {
    const label = node("label", "tag-choice");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = tag.slug;
    input.checked = selected.has(tag.slug) || initialTagSlug === tag.slug;
    input.addEventListener("change", render);
    label.append(input, node("span", "", tag.name));
    return label;
  });
  el.tagFilters.replaceChildren(...(choices.length ? choices : [node("span", "muted", "尚無可用標籤。") ]));
  initialTagSlug = null;
}

function closeUploadReferenceOptions() {
  el.uploadReferenceOptions.classList.add("hidden");
  el.uploadReferenceInput.setAttribute("aria-expanded", "false");
  el.uploadReferenceInput.removeAttribute("aria-activedescendant");
  activeReferenceIndex = -1;
}

function resetUploadReference() {
  el.uploadReferenceInput.value = "";
  el.clearUploadReference.classList.add("hidden");
  closeUploadReferenceOptions();
  el.uploadReferenceStatus.textContent = approvedReferenceSongs.length
    ? "選取後可套用歌曲資料，套用後仍可自由修改。"
    : "目前尚無已通過歌曲可供參考。";
}

function rebuildUploadReferences() {
  // The page also loads the user's pending/rejected rows. Never suggest those.
  const approvedSongs = songs.filter((song) => song.status === "approved");
  approvedReferenceSongs = approvedSongs;
  for (const [field, input] of Object.entries(uploadMetadataInputs)) {
    if (!input.list) continue;
    const options = approvedMetadataValues(approvedSongs, field).map((value) => {
      const option = document.createElement("option");
      option.value = value;
      return option;
    });
    input.list.replaceChildren(...options);
  }
  // A refreshed catalog invalidates previous choices, never the copied form values.
  uploadReferenceMatches = [];
  el.uploadReferenceOptions.replaceChildren();
  resetUploadReference();
}

function applyUploadReference(values) {
  const currentValues = Object.fromEntries(Object.entries(uploadMetadataInputs).map(([field, input]) => [field, input.value]));
  currentValues.tag_ids = selectedTagIds(el.uploadTags);
  if (hasMeaningfulUploadMetadata(currentValues)
    && !window.confirm("套用這首已通過歌曲的資料？目前已輸入的歌曲資料會被取代。")) return;
  for (const [field, input] of Object.entries(uploadMetadataInputs)) input.value = values[field];
  renderTagChoices(el.uploadTags, values.tag_ids);
  updateYoutubePreview();
  el.uploadReferenceInput.value = values.title;
  el.clearUploadReference.classList.remove("hidden");
  el.uploadReferenceInput.focus();
  closeUploadReferenceOptions();
  el.uploadReferenceStatus.textContent = `已套用「${values.title}」的歌曲資料，可繼續修改；請另選 PDF。`;
}

function renderUploadReferenceOptions() {
  uploadReferenceMatches = songReferenceSearch(approvedReferenceSongs, el.uploadReferenceInput.value, tags);
  activeReferenceIndex = -1;
  el.uploadReferenceInput.removeAttribute("aria-activedescendant");
  el.clearUploadReference.classList.toggle("hidden", !el.uploadReferenceInput.value);
  const options = uploadReferenceMatches.map((song, index) => {
    const option = node("div", "song-reference-option");
    option.id = `uploadReferenceOption-${index}`;
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", "false");
    option.append(node("span", "song-reference-title", song.title), node("span", "song-reference-artist", song.artist));
    const detail = [song.album, song.release_year].filter(Boolean).join(" · ");
    if (detail) option.append(node("span", "song-reference-meta", detail));
    // Keep input focus for mouse selection; touch scrolling remains native.
    option.addEventListener("mousedown", (event) => event.preventDefault());
    option.addEventListener("click", () => applyUploadReference(song));
    return option;
  });
  el.uploadReferenceOptions.replaceChildren(...options);
  el.uploadReferenceOptions.classList.toggle("hidden", !options.length);
  el.uploadReferenceInput.setAttribute("aria-expanded", String(Boolean(options.length)));
  el.uploadReferenceStatus.textContent = !approvedReferenceSongs.length
    ? "目前尚無已通過歌曲可供參考。"
    : options.length ? `顯示 ${options.length} 首已通過歌曲（最多 8 首），可用上下鍵選擇、Enter 套用。` : "找不到符合的已通過歌曲。";
}

function uploadReferenceKeydown(event) {
  if (event.isComposing || event.keyCode === 229) return;
  const open = el.uploadReferenceInput.getAttribute("aria-expanded") === "true";
  if (event.key === "Escape" && open) {
    event.preventDefault(); event.stopPropagation(); closeUploadReferenceOptions();
  } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (!open) renderUploadReferenceOptions();
    if (!uploadReferenceMatches.length) return;
    const count = uploadReferenceMatches.length;
    activeReferenceIndex = activeReferenceIndex < 0
      ? (event.key === "ArrowDown" ? 0 : count - 1)
      : (activeReferenceIndex + (event.key === "ArrowDown" ? 1 : -1) + count) % count;
    const options = [...el.uploadReferenceOptions.children];
    options.forEach((option, index) => option.setAttribute("aria-selected", String(index === activeReferenceIndex)));
    const active = options[activeReferenceIndex];
    el.uploadReferenceInput.setAttribute("aria-activedescendant", active.id);
    active.scrollIntoView({ block: "nearest" });
  } else if (event.key === "Enter") {
    // Searching must never accidentally submit the PDF form.
    event.preventDefault();
    if (open && activeReferenceIndex >= 0) applyUploadReference(uploadReferenceMatches[activeReferenceIndex]);
  } else if (event.key === "Tab") {
    closeUploadReferenceOptions();
  }
}

function accountUI() {
  const signedIn = Boolean(currentUser);
  el.userLabel.textContent = signedIn ? (currentUser.user_metadata?.full_name || currentUser.email || "已登入") : "訪客模式";
  el.signIn.classList.toggle("hidden", signedIn);
  el.signOut.classList.toggle("hidden", !signedIn);
  el.playlistsLink.classList.toggle("hidden", !signedIn);
  el.adminLink.classList.toggle("hidden", !signedIn || !isAdmin);
  el.openUpload.disabled = !signedIn || !configured;
  el.description.textContent = signedIn ? "顯示已通過審核，以及你自己的待審核／退回歌曲。" : "顯示已通過審核的歌曲。";
}

function setLoading(value) {
  el.loading.classList.toggle("hidden", !value);
  if (value) { el.grid.classList.add("hidden"); el.empty.classList.add("hidden"); }
}

function rebuildSelect(select, values, emptyLabel) {
  const old = select.value;
  const first = document.createElement("option");
  first.value = "";
  first.textContent = emptyLabel;
  const options = [...new Set(values.filter((value) => value !== null && value !== undefined && value !== ""))]
    .sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true }))
    .map((value) => {
      const option = document.createElement("option"); option.value = String(value); option.textContent = String(value); return option;
    });
  select.replaceChildren(first, ...options);
  if (options.some((option) => option.value === old)) select.value = old;
}

function filters() {
  return { query: el.search.value, language: el.language.value, genre: el.genre.value, year: el.year.value, tags: selectedTagIds(el.tagFilters) };
}

function statusLabel(status) {
  return status === "approved" ? "已通過" : status === "rejected" ? "已退回" : "待審核";
}

function canEdit(song) {
  return Boolean(currentUser && song.uploader_id === currentUser.id && song.status === "pending");
}

async function signedPdfUrl(path, downloadName = null, expiresIn = 300) {
  const options = downloadName ? { download: downloadName } : undefined;
  const { data, error } = await supabase.storage.from(STORAGE_BUCKET).createSignedUrl(path, expiresIn, options);
  if (error) throw error;
  return data.signedUrl;
}

async function openPdf(song) {
  try {
    const [url, downloadUrl] = await Promise.all([
      signedPdfUrl(song.pdf_path, null, VIEWER_SIGNED_URL_TTL_SECONDS),
      signedPdfUrl(song.pdf_path, song.original_filename)
    ]);
    el.previewTitle.textContent = `${song.title} — ${song.artist}`;
    el.openPdf.href = url;
    el.downloadPdf.href = downloadUrl;
    el.previewDialog.showModal();
    await pdfPreview.load(url);
  } catch (error) {
    showMessage(errorMessage(error, "無法建立 PDF 預覽連結。"), "error", 0);
  }
}

function closePdf() {
  if (el.previewDialog.open) el.previewDialog.close();
}

function songCard(song) {
  const card = node("article", "song-card");
  const thumbnail = document.createElement("img");
  thumbnail.className = "song-thumbnail";
  thumbnail.src = youtubeThumbnailUrl(song.youtube_video_id);
  thumbnail.alt = `${song.title} 的 YouTube 縮圖`;
  thumbnail.loading = "lazy";

  const body = node("div", "song-card-body");
  const badges = node("div", "card-top");
  if (song.language) badges.append(node("span", "badge type", song.language));
  if (song.genre) badges.append(node("span", "badge genre", song.genre));
  if (song.status !== "approved") badges.append(node("span", `badge status-${song.status}`, statusLabel(song.status)));
  for (const tag of songTagObjects(song)) {
    const chip = node("button", "tag-chip", `#${tag.name}`);
    chip.type = "button";
    chip.addEventListener("click", () => {
      const input = [...el.tagFilters.querySelectorAll('input[type="checkbox"]')].find((item) => item.value === tag.slug);
      if (input) {
        input.checked = true;
        render();
        const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        window.scrollTo({ top: el.search.offsetTop, behavior: reducedMotion ? "auto" : "smooth" });
      }
    });
    badges.append(chip);
  }
  const top = node("div", "card-top-row");
  top.append(badges);
  if (isAdmin && displayOrderAvailable && song.status === "approved") {
    const approvedSongs = songs.filter((item) => item.status === "approved");
    const index = approvedSongs.findIndex((item) => item.id === song.id);
    const controls = node("div", "song-order-controls");
    const orderButton = (label, symbol, direction, boundaryDisabled) => {
      const button = node("button", "song-order-button", symbol);
      button.type = "button";
      button.setAttribute("aria-label", label);
      button.title = label;
      button.disabled = orderMoveBusy || boundaryDisabled;
      button.addEventListener("click", () => moveSongInPublicOrder(song.id, direction));
      return button;
    };
    controls.append(
      orderButton("將歌曲往前移", "↑", -1, index <= 0),
      orderButton("將歌曲往後移", "↓", 1, index === approvedSongs.length - 1)
    );
    top.append(controls);
  }
  body.append(top, node("h3", "", song.title), node("p", "song-artist", song.artist));
  body.append(node("p", "card-meta", [song.album, song.release_year].filter(Boolean).join(" · ") || "未提供專輯／年份"));
  body.append(node("p", "card-notes", song.notes || "尚無備註"), node("p", "card-meta", `上傳者：${uploaderDisplayName(song)}`), node("p", "filename", song.original_filename));

  const actions = node("div", "card-actions");
  const read = node("a", "button primary", "播放與閱讀");
  read.href = `./song.html?id=${encodeURIComponent(song.id)}`;
  const preview = node("button", "button secondary", "預覽 / 下載 PDF"); preview.type = "button"; preview.addEventListener("click", () => openPdf(song));
  actions.append(read, preview);
  if (song.status === "approved") {
    const addToPlaylist = node("button", "button secondary playlist-add-button", "加入播放清單");
    addToPlaylist.type = "button";
    addToPlaylist.setAttribute("aria-label", `將「${song.title}」加入播放清單`);
    addToPlaylist.addEventListener("click", () => openAddPlaylist(song));
    actions.append(addToPlaylist);
  }
  if (canEdit(song)) {
    const edit = node("button", "button secondary", "編輯"); edit.type = "button"; edit.addEventListener("click", () => openEdit(song));
    const remove = node("button", "button danger pending-song-delete-button", "刪除"); remove.type = "button"; remove.addEventListener("click", () => deletePendingSong(song));
    actions.append(edit, remove);
  }
  card.append(thumbnail, body, actions);
  return card;
}

function playlistChoice(playlist, selected) {
  const label = node("label", "playlist-choice");
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = selected;
  input.dataset.playlistId = playlist.id;
  input.addEventListener("change", async () => {
    input.disabled = true;
    const result = input.checked
      ? await supabase.rpc("add_song_to_playlist", { p_playlist_id: playlist.id, p_song_id: addPlaylistSong.id })
      : await supabase.from("playlist_items").delete().eq("playlist_id", playlist.id).eq("song_id", addPlaylistSong.id);
    input.disabled = false;
    if (result.error) {
      input.checked = !input.checked;
      showMessage(playlistSchemaUnavailable(result.error) ? "播放清單功能尚未完成資料庫部署。" : (result.error.message || "無法更新播放清單。"), "error", 0);
      return;
    }
    const state = input.checked ? "已加入" : "已移除";
    label.querySelector(".playlist-choice-state").textContent = state;
    showMessage(`${state}「${playlist.name}」。`, "success");
  });
  label.append(input, node("span", "playlist-choice-name", playlist.name), node("span", "playlist-choice-state", selected ? "已加入" : ""));
  return label;
}

async function openAddPlaylist(song) {
  if (!currentUser) return showMessage("請先登入以使用播放清單。", "info");
  addPlaylistSong = song;
  el.addPlaylistSong.textContent = `${song.title} — ${song.artist}`;
  el.playlistChoices.replaceChildren(node("div", "spinner"));
  if (!el.addPlaylistDialog.open) el.addPlaylistDialog.showModal();
  const [playlistResult, membershipResult] = await Promise.all([
    loadUserPlaylists(supabase),
    supabase.from("playlist_items").select("playlist_id").eq("song_id", song.id)
  ]);
  const error = playlistResult.error || membershipResult.error;
  if (error) {
    el.playlistChoices.replaceChildren(node("p", "muted", playlistSchemaUnavailable(error) ? "播放清單功能尚未完成資料庫部署。" : "無法載入播放清單。"));
    return;
  }
  const selected = new Set(normalizePlaylistMembership(membershipResult.data || []));
  const choices = (playlistResult.data || []).map((playlist) => playlistChoice(playlist, selected.has(playlist.id)));
  el.playlistChoices.replaceChildren(...(choices.length ? choices : [node("p", "muted", "尚未建立播放清單。請在下方建立第一個清單。")]));
}

async function createPlaylistAndAdd(event) {
  event.preventDefault();
  if (!currentUser || !addPlaylistSong) return;
  const name = el.inlinePlaylistName.value.trim();
  const description = el.inlinePlaylistDescription.value.trim() || null;
  if (!name) return showMessage("播放清單名稱不可為空。", "error");
  el.createAndAddPlaylist.disabled = true;
  const { data: playlist, error: createError } = await supabase.from("playlists").insert({ owner_id: currentUser.id, name, description }).select("id,name,description").single();
  if (createError) {
    el.createAndAddPlaylist.disabled = false;
    return showMessage(playlistSchemaUnavailable(createError) ? "播放清單功能尚未完成資料庫部署。" : (createError.message || "無法建立播放清單。"), "error", 0);
  }
  const { error: addError } = await supabase.rpc("add_song_to_playlist", { p_playlist_id: playlist.id, p_song_id: addPlaylistSong.id });
  el.createAndAddPlaylist.disabled = false;
  if (addError) return showMessage(addError.message || "播放清單已建立，但歌曲加入失敗。", "error", 0);
  el.inlinePlaylistForm.reset();
  showMessage(`已建立「${playlist.name}」並加入歌曲。`, "success");
  await openAddPlaylist(addPlaylistSong);
}

async function moveSongInPublicOrder(songId, direction) {
  if (orderMoveBusy || !isAdmin || !displayOrderAvailable) return;
  orderMoveBusy = true;
  render();
  try {
    const { error } = await supabase.rpc("move_song_in_public_order", { p_song_id: songId, p_direction: direction });
    if (error) throw error;
    await loadSongs();
  } catch (error) {
    showMessage(errorMessage(error, "無法調整公開歌曲順序。"), "error", 0);
  } finally {
    orderMoveBusy = false;
    render();
  }
}

function render() {
  const visible = filterSongs(songs, filters());
  el.total.textContent = String(visible.length);
  el.grid.replaceChildren(...visible.map(songCard));
  el.grid.classList.toggle("hidden", visible.length === 0);
  el.empty.classList.toggle("hidden", visible.length !== 0);
}

async function loadSongs() {
  if (!configured) { songs = []; tags = []; rebuildUploadReferences(); setLoading(false); render(); return; }
  setLoading(true);
  const [songsResult, tagsResult, orderResult] = await Promise.all([
    supabase.from("songs").select("id,title,artist,album,release_year,language,genre,notes,youtube_video_id,pdf_path,original_filename,uploader_id,uploader_display_name,status,created_at,updated_at,song_tags(tags(id,name,slug))").order("created_at", { ascending: false }),
    supabase.from("tags").select("id,name,slug").order("name"),
    supabase.from("song_display_order").select("song_id,position")
  ]);
  setLoading(false);
  if (songsResult.error || tagsResult.error) {
    showMessage(errorMessage(songsResult.error || tagsResult.error, "無法載入歌曲資料。"), "error", 0);
    songs = []; tags = []; rebuildUploadReferences(); render(); return;
  }
  displayOrderAvailable = !orderResult.error;
  if (orderResult.error) console.warn("Public song ordering is unavailable; using created_at order.", orderResult.error);
  songs = sortSongsForDisplay(songsResult.data || [], displayOrderAvailable ? orderResult.data : []);
  tags = tagsResult.data || [];
  rebuildSelect(el.language, songs.map((song) => song.language), "所有語言");
  rebuildSelect(el.genre, songs.map((song) => song.genre), "所有曲風");
  rebuildSelect(el.year, songs.map((song) => song.release_year).sort((a, b) => b - a), "所有年份");
  renderTagFilters();
  renderTagChoices(el.uploadTags, selectedTagIds(el.uploadTags));
  rebuildUploadReferences();
  render();
}

function updateYoutubePreview() {
  const id = extractYouTubeVideoId(el.uploadYoutube.value);
  el.uploadYoutubePreview.classList.toggle("hidden", !id);
  el.uploadYoutubeStatus.textContent = id ? `已辨識影片 ID：${id}` : "請輸入有效的 YouTube watch、youtu.be、embed 或 shorts URL。";
  el.uploadYoutubeStatus.className = id ? "field-success" : "field-error";
  if (id) { el.uploadYoutubeThumbnail.src = youtubeThumbnailUrl(id); el.uploadYoutubeVideoId.textContent = id; }
  return id;
}

function validateSongFields(values) {
  if (!values.title || !values.artist) return "歌曲名稱與歌手為必填。";
  if (!values.youtube_video_id) return "請輸入有效的 YouTube URL。";
  if (values.release_year && (values.release_year < 1800 || values.release_year > 2100)) return "發行年份必須介於 1800 到 2100。";
  return null;
}

function uploadBusy(busy) {
  el.submitUpload.disabled = busy;
  el.uploadProgress.classList.toggle("hidden", !busy);
}

async function uploadSong(event) {
  event.preventDefault();
  if (!currentUser) return showMessage("請先登入。", "error");
  const file = el.uploadPdf.files[0];
  const youtubeId = updateYoutubePreview();
  const values = { title: el.uploadTitle.value.trim(), artist: el.uploadArtist.value.trim(), album: el.uploadAlbum.value.trim(), release_year: el.uploadYear.value ? Number(el.uploadYear.value) : null, language: el.uploadLanguage.value.trim(), genre: el.uploadGenre.value.trim(), notes: el.uploadNotes.value.trim(), youtube_video_id: youtubeId };
  const validation = validateSongFields(values);
  if (validation) return showMessage(validation, "error", 0);
  if (!file || (file.type && file.type !== "application/pdf") || !file.name.toLowerCase().endsWith(".pdf")) return showMessage("請選擇 PDF 檔案。", "error", 0);
  if (file.size > MAX_FILE_SIZE_BYTES) return showMessage(`PDF 不可超過 ${maximumFileSizeText()}。`, "error", 0);

  uploadBusy(true);
  const path = `${currentUser.id}/${crypto.randomUUID()}-${safeFilename(file.name)}`;
  const { error: storageError } = await supabase.storage.from(STORAGE_BUCKET).upload(path, file, { contentType: "application/pdf", upsert: false });
  if (storageError) { uploadBusy(false); return showMessage(errorMessage(storageError, "PDF 上傳失敗。"), "error", 0); }

  const payload = pendingSongPayload({ ...values, pdf_path: path, original_filename: file.name }, currentUser.id);
  const { data: song, error: songError } = await supabase.from("songs").insert(payload).select("id").single();
  if (songError) {
    await supabase.storage.from(STORAGE_BUCKET).remove([path]); uploadBusy(false);
    return showMessage(errorMessage(songError, "歌曲資料建立失敗，已嘗試清理 PDF。"), "error", 0);
  }

  const { error: tagError } = await supabase.rpc("set_song_tags", { p_song_id: song.id, p_tag_ids: selectedTagIds(el.uploadTags) });
  if (tagError) {
    await supabase.from("songs").delete().eq("id", song.id);
    await supabase.storage.from(STORAGE_BUCKET).remove([path]); uploadBusy(false);
    return showMessage(errorMessage(tagError, "標籤儲存失敗，已回復此次上傳。"), "error", 0);
  }

  uploadBusy(false); el.uploadDialog.close(); el.uploadForm.reset(); updateYoutubePreview();
  showMessage("歌曲已送出，等待管理員審核。", "success");
  await loadSongs();
}

function openEdit(song) {
  if (!canEdit(song)) return showMessage("你目前沒有權限編輯這筆歌曲。", "error", 0);
  el.editSongId.value = song.id; el.editTitle.value = song.title; el.editArtist.value = song.artist; el.editAlbum.value = song.album || ""; el.editYear.value = song.release_year || ""; el.editLanguage.value = song.language || ""; el.editGenre.value = song.genre || ""; el.editYoutube.value = normalizeYouTubeUrl(song.youtube_video_id); el.editNotes.value = song.notes || "";
  el.editPdf.value = ""; el.editCurrentPdf.textContent = song.original_filename;
  renderTagChoices(el.editTags, songTagObjects(song).map((tag) => tag.id));
  el.editDialog.showModal();
}

async function saveEdit(event) {
  event.preventDefault();
  const youtubeId = extractYouTubeVideoId(el.editYoutube.value);
  const values = { title: el.editTitle.value.trim(), artist: el.editArtist.value.trim(), album: el.editAlbum.value.trim() || null, release_year: el.editYear.value ? Number(el.editYear.value) : null, language: el.editLanguage.value.trim() || null, genre: el.editGenre.value.trim() || null, notes: el.editNotes.value.trim() || null, youtube_video_id: youtubeId };
  const validation = validateSongFields(values);
  if (validation) return showMessage(validation, "error", 0);
  const songId = el.editSongId.value;
  const song = songs.find((item) => item.id === songId);
  if (!song || !canEdit(song)) return showMessage("你目前沒有權限編輯這筆歌曲。", "error", 0);
  el.saveEdit.disabled = true; el.editProgress.classList.remove("hidden");
  let updateResult;
  let updateError;
  let tagWarning;
  try {
    updateResult = await updateSongWithOptionalPdf({ supabase, bucket: STORAGE_BUCKET, song, values, file: el.editPdf.files[0] || null, currentUserId: currentUser.id, maxFileSizeBytes: MAX_FILE_SIZE_BYTES, requirePendingOwner: true });
    const { error: tagError } = await supabase.rpc("set_song_tags", { p_song_id: songId, p_tag_ids: selectedTagIds(el.editTags) });
    tagWarning = tagError || null;
  } catch (error) {
    updateError = error;
  }
  el.saveEdit.disabled = false; el.editProgress.classList.add("hidden");
  if (updateError) {
    const rollbackNote = updateError instanceof PdfReplacementError && updateError.rollbackWarning ? " 新 PDF 回滾失敗，可能留下 orphan object，請通知管理員。" : "";
    return showMessage(`${errorMessage(updateError, "無法更新待審核歌曲。")}${rollbackNote}`, "error", 0);
  }
  el.editDialog.close();
  if (updateResult.cleanupWarning || tagWarning) {
    if (updateResult.cleanupWarning) console.warn("Old PDF cleanup failed after successful replacement", updateResult.cleanupWarning);
    if (tagWarning) console.warn("Song updated but tags were not updated", tagWarning);
    const notices = [];
    if (updateResult.replaced) notices.push("PDF 已更換。");
    else notices.push("待審核歌曲已更新。");
    if (tagWarning) notices.push("標籤未能更新。");
    if (updateResult.cleanupWarning) notices.push("舊 PDF 清理失敗，新的 PDF 仍可正常使用；請通知管理員清理 orphan object。");
    showMessage(notices.join(" "), "info", 0);
  } else {
    showMessage(updateResult.replaced ? "PDF 已更換。" : "待審核歌曲已更新。", "success");
  }
  await loadSongs();
}

async function deletePendingSong(song) {
  if (!confirm(`確定刪除「${song.title}」？資料列與同步歌詞會先刪除，再清理 PDF。`)) return;
  const { error: databaseError } = await supabase.from("songs").delete().eq("id", song.id).eq("status", "pending");
  if (databaseError) return showMessage(errorMessage(databaseError, "無法刪除歌曲資料。"), "error", 0);
  const { error: storageError } = await supabase.storage.from(STORAGE_BUCKET).remove([song.pdf_path]);
  if (storageError) showMessage(errorMessage(storageError, "歌曲資料已刪除，但 PDF 成為 orphan；請由管理員清理。"), "error", 0);
  else showMessage("待審核歌曲與 PDF 已刪除。", "success");
  await loadSongs();
}

async function refreshAdminAccess() {
  isAdmin = false;
  if (!currentUser || !configured) return;
  const { data, error } = await supabase.rpc("is_admin");
  if (!error) isAdmin = data === true;
}

async function signInWithGoogle() {
  if (!configured) return showMessage("請先設定有效的 Supabase project。", "error", 0);
  el.signIn.disabled = true;
  try {
    await verifyGoogleAuthConfiguration(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: oauthRedirectUrl(window.location.href, "home") } });
    if (error) throw error;
  } catch (error) { showMessage(errorMessage(error, "無法開始 Google 登入。"), "error", 0); }
  finally { el.signIn.disabled = false; }
}

async function signOut() {
  const { error } = await supabase.auth.signOut({ scope: "local" });
  if (error) return showMessage(errorMessage(error, "無法登出。"), "error");
  await queueAuthSession(null, "SIGNED_OUT"); showMessage("已登出。", "success");
}

async function applyAuthSession(session) {
  currentUser = session?.user || null; isAdmin = false; await refreshAdminAccess(); accountUI(); await loadSongs();
}

function queueAuthSession(session, event) {
  authQueue = authQueue.catch(console.error).then(async () => {
    const userId = session?.user?.id || null;
    if (userId === appliedAuthUserId && event !== "USER_UPDATED") { currentUser = session?.user || null; accountUI(); return; }
    await applyAuthSession(session); appliedAuthUserId = userId;
  });
  return authQueue;
}

function bind() {
  el.signIn.addEventListener("click", signInWithGoogle); el.signOut.addEventListener("click", signOut);
  el.openUpload.addEventListener("click", () => { renderTagChoices(el.uploadTags, selectedTagIds(el.uploadTags)); el.uploadDialog.showModal(); });
  el.uploadReferenceInput.addEventListener("input", renderUploadReferenceOptions);
  el.uploadReferenceInput.addEventListener("focus", renderUploadReferenceOptions);
  el.uploadReferenceInput.addEventListener("keydown", uploadReferenceKeydown);
  el.uploadReference.addEventListener("focusout", (event) => {
    if (!el.uploadReference.contains(event.relatedTarget)) closeUploadReferenceOptions();
  });
  el.clearUploadReference.addEventListener("click", () => { resetUploadReference(); el.uploadReferenceInput.focus(); });
  el.uploadDialog.addEventListener("close", closeUploadReferenceOptions);
  el.uploadForm.addEventListener("reset", resetUploadReference);
  el.uploadYoutube.addEventListener("input", updateYoutubePreview); el.uploadForm.addEventListener("submit", uploadSong); el.editForm.addEventListener("submit", saveEdit);
  el.refresh.addEventListener("click", loadSongs);
  [el.search, el.language, el.genre, el.year].forEach((control) => { control.addEventListener("input", render); control.addEventListener("change", render); });
  el.clearFilters.addEventListener("click", () => { el.search.value = ""; el.language.value = ""; el.genre.value = ""; el.year.value = ""; el.tagFilters.querySelectorAll('input[type="checkbox"]').forEach((input) => { input.checked = false; }); render(); });
  el.closePreview.addEventListener("click", closePdf); el.closePreviewFooter.addEventListener("click", closePdf); el.previewDialog.addEventListener("close", () => { void pdfPreview.destroy(); el.openPdf.href = "#"; el.downloadPdf.href = "#"; });
  el.closeAddPlaylist.addEventListener("click", () => el.addPlaylistDialog.close()); el.inlinePlaylistForm.addEventListener("submit", createPlaylistAndAdd);
  document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => document.getElementById(button.dataset.close)?.close()));
}

window.addEventListener("beforeunload", () => { void pdfPreview.dispose(); });

async function init() {
  bind(); el.maxFileSize.textContent = maximumFileSizeText(); updateYoutubePreview();
  if (!configured) { el.setupNotice.classList.remove("hidden"); accountUI(); setLoading(false); render(); return; }
  const oauth = parseOAuthResponse(window.location.href);
  supabase.auth.onAuthStateChange((event, session) => setTimeout(() => void queueAuthSession(session, event), 0));
  const { data, error } = await supabase.auth.getSession();
  await queueAuthSession(data?.session || null, "GET_SESSION"); cleanOAuthCallbackFromBrowser();
  if (oauth.error) showMessage(oauth.error, "error", 0); else if (error) showMessage(errorMessage(error, "無法讀取登入 session。"), "error", 0);
}

init();
