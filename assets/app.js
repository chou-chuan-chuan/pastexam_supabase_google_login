import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, STORAGE_BUCKET, MAX_FILE_SIZE_BYTES } from "../config.js";
import { SUPABASE_CLIENT_OPTIONS, cleanOAuthCallbackFromBrowser, oauthRedirectUrl, parseOAuthResponse, verifyGoogleAuthConfiguration } from "./auth.js";
import { filterSongs, pendingSongPayload, songTagObjects, sortSongsForDisplay, uploaderDisplayName } from "./catalog.js";
import { PdfReplacementError, updateSongWithOptionalPdf } from "./pdf-replacement.js";
import { PdfViewer } from "./pdf-viewer.js";
import { extractYouTubeVideoId, normalizeYouTubeUrl, youtubeThumbnailUrl } from "./youtube.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS) : null;
const $ = (selector) => document.querySelector(selector);

const el = {
  setupNotice: $("#setupNotice"), messageBox: $("#messageBox"), userLabel: $("#userLabel"),
  signIn: $("#googleSignInButton"), signOut: $("#signOutButton"), adminLink: $("#adminPageLink"), openUpload: $("#openUploadButton"),
  search: $("#searchInput"), language: $("#languageFilter"), genre: $("#genreFilter"), year: $("#yearFilter"),
  tagFilters: $("#tagFilterList"), clearFilters: $("#clearFiltersButton"), refresh: $("#refreshButton"), total: $("#totalCount"), description: $("#listDescription"),
  loading: $("#loadingState"), grid: $("#songGrid"), empty: $("#emptyState"),
  previewDialog: $("#previewDialog"), previewTitle: $("#previewTitle"), previewViewer: $("#pdfPreviewViewer"), closePreview: $("#closePreviewButton"), closePreviewFooter: $("#closePreviewFooterButton"), openPdf: $("#openPdfButton"), downloadPdf: $("#downloadPdfButton"),
  uploadDialog: $("#uploadDialog"), uploadForm: $("#uploadForm"), uploadTitle: $("#uploadTitle"), uploadArtist: $("#uploadArtist"), uploadAlbum: $("#uploadAlbum"), uploadYear: $("#uploadYear"), uploadLanguage: $("#uploadLanguage"), uploadGenre: $("#uploadGenre"), uploadYoutube: $("#uploadYoutube"), uploadYoutubeStatus: $("#uploadYoutubeStatus"), uploadYoutubePreview: $("#uploadYoutubePreview"), uploadYoutubeThumbnail: $("#uploadYoutubeThumbnail"), uploadYoutubeVideoId: $("#uploadYoutubeVideoId"), uploadTags: $("#uploadTagChoices"), uploadNotes: $("#uploadNotes"), uploadPdf: $("#uploadPdf"), maxFileSize: $("#maxFileSizeLabel"), uploadProgress: $("#uploadProgress"), submitUpload: $("#submitUploadButton"),
  editDialog: $("#editDialog"), editForm: $("#editForm"), editSongId: $("#editSongId"), editTitle: $("#editTitle"), editArtist: $("#editArtist"), editAlbum: $("#editAlbum"), editYear: $("#editYear"), editLanguage: $("#editLanguage"), editGenre: $("#editGenre"), editYoutube: $("#editYoutube"), editTags: $("#editTagChoices"), editNotes: $("#editNotes"), editPdf: $("#editPdf"), editCurrentPdf: $("#editCurrentPdf"), editProgress: $("#editProgress"), saveEdit: $("#saveEditButton")
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

function accountUI() {
  const signedIn = Boolean(currentUser);
  el.userLabel.textContent = signedIn ? (currentUser.user_metadata?.full_name || currentUser.email || "已登入") : "訪客模式";
  el.signIn.classList.toggle("hidden", signedIn);
  el.signOut.classList.toggle("hidden", !signedIn);
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
  const preview = node("button", "button secondary", "預覽 PDF"); preview.type = "button"; preview.addEventListener("click", () => openPdf(song));
  const download = node("button", "button secondary", "下載 PDF"); download.type = "button"; download.addEventListener("click", () => downloadSongPdf(song));
  actions.append(read, preview, download);
  if (canEdit(song)) {
    const edit = node("button", "button secondary", "編輯"); edit.type = "button"; edit.addEventListener("click", () => openEdit(song));
    const remove = node("button", "button danger", "刪除"); remove.type = "button"; remove.addEventListener("click", () => deletePendingSong(song));
    actions.append(edit, remove);
  }
  card.append(thumbnail, body, actions);
  return card;
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

async function downloadSongPdf(song) {
  try {
    const anchor = document.createElement("a");
    anchor.href = await signedPdfUrl(song.pdf_path, song.original_filename);
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    anchor.click();
  } catch (error) {
    showMessage(errorMessage(error, "無法建立 PDF 下載連結。"), "error", 0);
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
  if (!configured) { songs = []; tags = []; setLoading(false); render(); return; }
  setLoading(true);
  const [songsResult, tagsResult, orderResult] = await Promise.all([
    supabase.from("songs").select("id,title,artist,album,release_year,language,genre,notes,youtube_video_id,pdf_path,original_filename,uploader_id,uploader_display_name,status,created_at,updated_at,song_tags(tags(id,name,slug))").order("created_at", { ascending: false }),
    supabase.from("tags").select("id,name,slug").order("name"),
    supabase.from("song_display_order").select("song_id,position")
  ]);
  setLoading(false);
  if (songsResult.error || tagsResult.error) {
    showMessage(errorMessage(songsResult.error || tagsResult.error, "無法載入歌曲資料。"), "error", 0);
    songs = []; tags = []; render(); return;
  }
  displayOrderAvailable = !orderResult.error;
  if (orderResult.error) console.warn("Public song ordering is unavailable; using created_at order.", orderResult.error);
  songs = sortSongsForDisplay(songsResult.data || [], displayOrderAvailable ? orderResult.data : []);
  tags = tagsResult.data || [];
  rebuildSelect(el.language, songs.map((song) => song.language), "所有語言");
  rebuildSelect(el.genre, songs.map((song) => song.genre), "所有曲風");
  rebuildSelect(el.year, songs.map((song) => song.release_year).sort((a, b) => b - a), "所有年份");
  renderTagFilters();
  renderTagChoices(el.uploadTags);
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
  el.openUpload.addEventListener("click", () => { renderTagChoices(el.uploadTags); el.uploadDialog.showModal(); });
  el.uploadYoutube.addEventListener("input", updateYoutubePreview); el.uploadForm.addEventListener("submit", uploadSong); el.editForm.addEventListener("submit", saveEdit);
  el.refresh.addEventListener("click", loadSongs);
  [el.search, el.language, el.genre, el.year].forEach((control) => { control.addEventListener("input", render); control.addEventListener("change", render); });
  el.clearFilters.addEventListener("click", () => { el.search.value = ""; el.language.value = ""; el.genre.value = ""; el.year.value = ""; el.tagFilters.querySelectorAll('input[type="checkbox"]').forEach((input) => { input.checked = false; }); render(); });
  el.closePreview.addEventListener("click", closePdf); el.closePreviewFooter.addEventListener("click", closePdf); el.previewDialog.addEventListener("close", () => { void pdfPreview.destroy(); el.openPdf.href = "#"; el.downloadPdf.href = "#"; });
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
