import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, STORAGE_BUCKET, MAX_FILE_SIZE_BYTES } from "../config.js";
import { SUPABASE_CLIENT_OPTIONS, cleanOAuthCallbackFromBrowser, oauthRedirectUrl, parseOAuthResponse, verifyGoogleAuthConfiguration } from "./auth.js";
import { songTagObjects, uploaderDisplayName } from "./catalog.js";
import { PdfReplacementError, updateSongWithOptionalPdf } from "./pdf-replacement.js";
import { parseLrc } from "./lrc.js";
import { formatCueTime, prepareCuesForSave, validateCueRows } from "./lyrics-sync.js";
import { extractYouTubeVideoId, normalizeYouTubeUrl, youtubeWatchUrl } from "./youtube.js";
import { YouTubePlayer } from "./youtube-player.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS) : null;
const $ = (selector) => document.querySelector(selector);

const el = {
  setup: $("#adminSetupNotice"), message: $("#adminMessageBox"), user: $("#adminUserLabel"), headerSignIn: $("#adminGoogleSignInButton"), panelSignIn: $("#adminPanelSignInButton"), signOut: $("#adminSignOutButton"), deniedSignOut: $("#adminDeniedSignOutButton"), signedOut: $("#adminSignedOutState"), denied: $("#adminDeniedState"), deniedText: $("#adminDeniedDescription"), dashboard: $("#adminDashboard"),
  search: $("#adminSearchInput"), status: $("#adminStatusFilter"), refresh: $("#adminRefreshButton"), description: $("#adminListDescription"), loading: $("#adminLoadingState"), grid: $("#adminSongGrid"), empty: $("#adminEmptyState"), pending: $("#pendingCount"), approved: $("#approvedCount"), rejected: $("#rejectedCount"),
  preview: $("#adminPreviewDialog"), previewTitle: $("#adminPreviewTitle"), previewFrame: $("#adminPdfPreviewFrame"), closePreview: $("#adminClosePreviewButton"), closePreviewFooter: $("#adminClosePreviewFooterButton"), openPdf: $("#adminOpenPdfButton"), downloadPdf: $("#adminDownloadPdfButton"),
  tagSearch: $("#tagSearchInput"), tagForm: $("#createTagForm"), newTagName: $("#newTagName"), newTagSlug: $("#newTagSlug"), createTag: $("#createTagButton"), tagList: $("#tagAdminList"),
  editor: $("#songEditorDialog"), closeEditor: $("#closeSongEditorButton"), editorTitleHeading: $("#songEditorTitle"), metadataForm: $("#songMetadataForm"), title: $("#editorTitle"), artist: $("#editorArtist"), album: $("#editorAlbum"), year: $("#editorYear"), language: $("#editorLanguage"), genre: $("#editorGenre"), youtube: $("#editorYoutube"), youtubeStatus: $("#editorYoutubeStatus"), tagChoices: $("#editorTagChoices"), notes: $("#editorNotes"), pdf: $("#editorPdf"), currentPdf: $("#editorCurrentPdf"), saveMetadata: $("#saveMetadataButton"), playerShell: $(".admin-player-shell"), currentTime: $("#editorCurrentTime"), playerStatus: $("#editorPlayerStatus"), fallback: $("#editorYoutubeFallback"),
  lrcFile: $("#lrcFileInput"), lrcText: $("#lrcTextInput"), previewLrc: $("#previewLrcButton"), lrcSummary: $("#lrcSummary"), lrcErrors: $("#lrcErrorList"), plainLyrics: $("#plainLyricsInput"), createLines: $("#createCueLinesButton"), addCue: $("#addCueButton"), markCue: $("#markCueButton"), moveUp: $("#moveCueUpButton"), moveDown: $("#moveCueDownButton"), deleteCue: $("#deleteCueButton"), cueRows: $("#cueRows"), cueValidation: $("#cueValidationList"), saveCues: $("#saveCuesButton")
};

let currentUser = null;
let isAdmin = false;
let songs = [];
let tags = [];
let currentSong = null;
let cueRows = [];
let selectedCueIndex = -1;
let editorPlayer = null;
let editorTimer = null;
let authQueue = Promise.resolve();
let appliedAuthUserId;
let messageTimer;

function node(tag, className, text) { const item = document.createElement(tag); if (className) item.className = className; if (text !== undefined) item.textContent = text; return item; }
function showMessage(text, kind = "info", timeout = 7000) { clearTimeout(messageTimer); el.message.textContent = text; el.message.className = `notice ${kind}`; if (timeout) messageTimer = setTimeout(() => el.message.classList.add("hidden"), timeout); }
function errorMessage(error, fallback) { console.error(error); return error?.message || fallback; }
function statusLabel(status) { return status === "approved" ? "已通過" : status === "rejected" ? "已退回" : "待審核"; }
function formatDate(value) { return value ? new Intl.DateTimeFormat("zh-TW", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—"; }

function updateAccessUI() {
  const signedIn = Boolean(currentUser);
  el.user.textContent = signedIn ? (currentUser.user_metadata?.full_name || currentUser.email || "已登入") : "尚未登入";
  el.headerSignIn.classList.toggle("hidden", signedIn); el.signOut.classList.toggle("hidden", !signedIn);
  el.signedOut.classList.toggle("hidden", signedIn); el.denied.classList.toggle("hidden", !signedIn || isAdmin); el.dashboard.classList.toggle("hidden", !signedIn || !isAdmin);
  if (signedIn && !isAdmin) el.deniedText.textContent = `${currentUser.email || "此帳號"} 已完成 Google 登入，但不在 public.admin_users。`;
}

function setLoading(value) { el.loading.classList.toggle("hidden", !value); if (value) { el.grid.classList.add("hidden"); el.empty.classList.add("hidden"); } }
function updateCounts() { const count = (status) => songs.filter((song) => song.status === status).length; el.pending.textContent = String(count("pending")); el.approved.textContent = String(count("approved")); el.rejected.textContent = String(count("rejected")); }

function matches(song) {
  const query = el.search.value.trim().toLocaleLowerCase();
  const haystack = [song.title, song.artist, song.album, song.language, song.genre, song.release_year, song.original_filename, uploaderDisplayName(song), song.uploader_id, ...songTagObjects(song).map((tag) => tag.name)].join(" ").toLocaleLowerCase();
  return (!query || haystack.includes(query)) && (!el.status.value || song.status === el.status.value);
}

async function signedPdfUrl(song, download = false) {
  const options = download ? { download: song.original_filename } : undefined;
  const { data, error } = await supabase.storage.from(STORAGE_BUCKET).createSignedUrl(song.pdf_path, 300, options);
  if (error) throw error;
  return data.signedUrl;
}

async function openPdf(song) {
  try {
    const url = await signedPdfUrl(song);
    el.previewTitle.textContent = `${song.title} — ${song.artist}`; el.previewFrame.src = `${url}#view=FitH&toolbar=1&navpanes=0`; el.openPdf.href = url; el.downloadPdf.href = await signedPdfUrl(song, true); el.preview.showModal();
  } catch (error) { showMessage(errorMessage(error, "無法建立 PDF 預覽連結。"), "error", 0); }
}

function adminSongCard(song) {
  const card = node("article", "admin-song-card");
  const content = node("div", "admin-card-content");
  const top = node("div", "card-top"); top.append(node("span", `badge status-${song.status}`, statusLabel(song.status))); if (song.language) top.append(node("span", "badge type", song.language)); if (song.genre) top.append(node("span", "badge genre", song.genre));
  const details = document.createElement("dl"); details.className = "admin-details";
  const detail = (term, value) => { details.append(node("dt", "", term), node("dd", "", value || "—")); };
  detail("歌手", song.artist); detail("專輯／年份", [song.album, song.release_year].filter(Boolean).join(" · ")); detail("YouTube ID", song.youtube_video_id); detail("上傳者", uploaderDisplayName(song)); detail("建立時間", formatDate(song.created_at));
  const tagRow = node("div", "tag-row"); songTagObjects(song).forEach((tag) => tagRow.append(node("span", "tag-chip", `#${tag.name}`)));
  content.append(top, node("h3", "", song.title), details, tagRow, node("p", "card-notes", song.notes || "尚無備註"), node("p", "filename", song.original_filename));
  const actions = node("div", "admin-card-actions");
  const button = (label, className, handler) => { const item = node("button", `button ${className}`, label); item.type = "button"; item.addEventListener("click", handler); return item; };
  const read = node("a", "button secondary", "播放與閱讀"); read.href = `./song.html?id=${encodeURIComponent(song.id)}`;
  actions.append(read, button("預覽 PDF", "secondary", () => openPdf(song)), button("編輯與同步", "primary", () => openEditor(song)));
  if (song.status !== "approved") actions.append(button("通過", "success", () => changeStatus(song, "approved")));
  if (song.status !== "rejected") actions.append(button("退回", "warning", () => changeStatus(song, "rejected")));
  if (song.status !== "pending") actions.append(button("改回待審", "secondary", () => changeStatus(song, "pending")));
  actions.append(button("永久刪除", "danger", () => deleteSong(song)));
  card.append(content, actions); return card;
}

function renderSongs() {
  const visible = songs.filter(matches);
  el.grid.replaceChildren(...visible.map(adminSongCard)); el.grid.classList.toggle("hidden", visible.length === 0); el.empty.classList.toggle("hidden", visible.length !== 0);
  el.description.textContent = `${el.status.value ? statusLabel(el.status.value) : "所有狀態"}：${visible.length} 首歌曲。`;
}

function tagUsageCount(tagId) { return songs.filter((song) => songTagObjects(song).some((tag) => tag.id === tagId)).length; }
function slugify(value) { return String(value || "").normalize("NFKC").toLocaleLowerCase().trim().replace(/[^\p{Letter}\p{Number}]+/gu, "-").replace(/^-+|-+$/g, "").slice(0, 80); }

function renderTags() {
  const query = el.tagSearch.value.trim().toLocaleLowerCase();
  const visible = tags.filter((tag) => !query || `${tag.name} ${tag.slug}`.toLocaleLowerCase().includes(query));
  el.tagList.replaceChildren(...visible.map((tag) => {
    const row = node("div", "tag-admin-row");
    const name = document.createElement("input"); name.value = tag.name; name.setAttribute("aria-label", `${tag.name} 名稱`);
    const slug = document.createElement("input"); slug.value = tag.slug; slug.setAttribute("aria-label", `${tag.name} slug`);
    const count = tagUsageCount(tag.id);
    const save = node("button", "button secondary", "儲存"); save.type = "button"; save.addEventListener("click", () => updateTag(tag, name.value, slug.value));
    const remove = node("button", "button danger", "刪除"); remove.type = "button"; remove.addEventListener("click", () => deleteTag(tag, count));
    row.append(name, slug, node("span", "tag-usage", `${count} 首歌曲`), save, remove); return row;
  }));
}

async function loadData() {
  if (!isAdmin) return;
  setLoading(true);
  const [songsResult, tagsResult] = await Promise.all([
    supabase.from("songs").select("id,title,artist,album,release_year,language,genre,notes,youtube_video_id,pdf_path,original_filename,uploader_id,uploader_display_name,status,created_at,updated_at,reviewed_at,reviewed_by,song_tags(tags(id,name,slug))").order("created_at", { ascending: false }),
    supabase.from("tags").select("id,name,slug,created_at").order("name")
  ]);
  setLoading(false);
  if (songsResult.error || tagsResult.error) { showMessage(errorMessage(songsResult.error || tagsResult.error, "無法載入管理資料。"), "error", 0); return; }
  songs = songsResult.data || []; tags = tagsResult.data || []; updateCounts(); renderSongs(); renderTags();
}

async function changeStatus(song, status) {
  if (!confirm(`將「${song.title}」改為${statusLabel(status)}？`)) return;
  const { error } = await supabase.from("songs").update({ status, reviewed_at: new Date().toISOString(), reviewed_by: currentUser.id }).eq("id", song.id);
  if (error) return showMessage(errorMessage(error, "無法更新審核狀態。"), "error", 0);
  showMessage(`歌曲已改為${statusLabel(status)}。`, "success"); await loadData();
}

async function deleteSong(song) {
  if (!confirm(`永久刪除「${song.title}」？\n\n資料庫會以 cascade 原子刪除 cues 與 song_tags，再清理 Storage PDF。此操作不可復原。`)) return;
  const { error: databaseError } = await supabase.from("songs").delete().eq("id", song.id);
  if (databaseError) return showMessage(errorMessage(databaseError, "資料庫刪除失敗，PDF 未動。"), "error", 0);
  const { error: storageError } = await supabase.storage.from(STORAGE_BUCKET).remove([song.pdf_path]);
  if (storageError) showMessage(errorMessage(storageError, "資料列、cues 與 tags 已刪除，但 PDF 成為 orphan，請在 Storage 手動清理。"), "error", 0);
  else showMessage("歌曲、同步歌詞、標籤關聯與 PDF 已永久刪除。", "success");
  closeEditor(); await loadData();
}

function renderEditorTagChoices(selectedIds) {
  const selected = new Set(selectedIds);
  el.tagChoices.replaceChildren(...tags.map((tag) => {
    const label = node("label", "tag-choice"); const input = document.createElement("input"); input.type = "checkbox"; input.value = tag.id; input.checked = selected.has(tag.id); label.append(input, node("span", "", tag.name)); return label;
  }));
}

function selectedEditorTagIds() { return [...el.tagChoices.querySelectorAll('input[type="checkbox"]:checked')].map((input) => input.value); }

async function setupEditorPlayer(videoId) {
  clearInterval(editorTimer); editorPlayer?.destroy(); editorPlayer = null;
  el.playerShell.replaceChildren(); const host = document.createElement("div"); host.id = "adminEditorPlayer"; el.playerShell.append(host);
  el.fallback.href = youtubeWatchUrl(videoId); el.playerStatus.textContent = "載入播放器…";
  editorPlayer = new YouTubePlayer(host, videoId, {
    onReady: () => { el.playerStatus.textContent = "播放器已就緒"; editorTimer = setInterval(() => { el.currentTime.textContent = formatCueTime(editorPlayer.getCurrentTimeMs()); }, 200); },
    onStateChange: (state) => { if (state === 1) el.playerStatus.textContent = "播放中"; else if (state === 2) el.playerStatus.textContent = "已暫停"; else if (state === 0) el.playerStatus.textContent = "播放完畢"; },
    onError: () => { el.playerStatus.textContent = "此影片無法嵌入，請使用 YouTube 外連。"; }
  });
  try { await editorPlayer.create(); } catch (error) { el.playerStatus.textContent = error.message; }
}

async function openEditor(song) {
  currentSong = song; selectedCueIndex = -1; el.editorTitleHeading.textContent = `${song.title} — 同步編輯`;
  el.title.value = song.title; el.artist.value = song.artist; el.album.value = song.album || ""; el.year.value = song.release_year || ""; el.language.value = song.language || ""; el.genre.value = song.genre || ""; el.youtube.value = normalizeYouTubeUrl(song.youtube_video_id); el.notes.value = song.notes || ""; renderEditorTagChoices(songTagObjects(song).map((tag) => tag.id)); validateEditorYoutube();
  el.pdf.value = ""; el.currentPdf.textContent = song.original_filename;
  const { data, error } = await supabase.from("lyric_cues").select("id,line_index,start_ms,end_ms,text").eq("song_id", song.id).order("line_index");
  if (error) { showMessage(errorMessage(error, "無法載入同步歌詞。"), "error", 0); return; }
  cueRows = (data || []).map((cue) => ({ start_ms: cue.start_ms, text: cue.text })); renderCueRows(); el.lrcText.value = ""; el.plainLyrics.value = ""; el.lrcErrors.replaceChildren(); el.cueValidation.replaceChildren();
  el.editor.showModal(); await setupEditorPlayer(song.youtube_video_id);
}

function closeEditor() { if (el.editor.open) el.editor.close(); clearInterval(editorTimer); editorPlayer?.destroy(); editorPlayer = null; currentSong = null; }

function validateEditorYoutube() {
  const id = extractYouTubeVideoId(el.youtube.value); el.youtubeStatus.textContent = id ? `影片 ID：${id}` : "YouTube URL 無效"; el.youtubeStatus.className = id ? "field-success" : "field-error"; return id;
}

async function saveMetadata(event) {
  event.preventDefault(); if (!currentSong) return;
  const videoId = validateEditorYoutube(); if (!videoId || !el.title.value.trim() || !el.artist.value.trim()) return showMessage("歌曲名稱、歌手與有效 YouTube URL 為必填。", "error", 0);
  el.saveMetadata.disabled = true;
  const values = { title: el.title.value.trim(), artist: el.artist.value.trim(), album: el.album.value.trim() || null, release_year: el.year.value ? Number(el.year.value) : null, language: el.language.value.trim() || null, genre: el.genre.value.trim() || null, notes: el.notes.value.trim() || null, youtube_video_id: videoId };
  let result;
  let error;
  try {
    result = await updateSongWithOptionalPdf({ supabase, bucket: STORAGE_BUCKET, song: currentSong, values, file: el.pdf.files[0] || null, currentUserId: currentUser.id, maxFileSizeBytes: MAX_FILE_SIZE_BYTES });
  } catch (updateError) {
    error = updateError;
  }
  const tagResult = error ? null : await supabase.rpc("set_song_tags", { p_song_id: currentSong.id, p_tag_ids: selectedEditorTagIds() });
  el.saveMetadata.disabled = false;
  if (error) {
    const rollbackNote = error instanceof PdfReplacementError && error.rollbackWarning ? " 新 PDF 回滾失敗，可能留下 orphan object，請手動清理。" : "";
    return showMessage(`${errorMessage(error, "無法更新歌曲資料。")}${rollbackNote}`, "error", 0);
  }
  if (tagResult?.error) return showMessage(errorMessage(tagResult.error, "歌曲已更新，但標籤未能更新。"), "error", 0);
  currentSong = { ...currentSong, ...values, pdf_path: result.pdfPath, original_filename: result.originalFilename };
  el.currentPdf.textContent = result.originalFilename; el.pdf.value = "";
  if (result.cleanupWarning) {
    console.warn("Old PDF cleanup failed after successful replacement", result.cleanupWarning);
    showMessage("PDF 已更換；但舊 PDF 清理失敗，新的 PDF 仍可正常使用，請清理 orphan object。", "info", 0);
  } else {
    showMessage(result.replaced ? "PDF 已更換。" : "歌曲資料與標籤已更新。", "success");
  }
  await setupEditorPlayer(videoId); await loadData();
}

function renderCueRows() {
  el.cueRows.replaceChildren(...cueRows.map((row, index) => {
    const container = node("div", `cue-row${index === selectedCueIndex ? " selected" : ""}`);
    const select = node("button", "cue-select", index === selectedCueIndex ? "▶" : String(index + 1)); select.type = "button"; select.setAttribute("aria-label", `選取第 ${index + 1} 行`); select.addEventListener("click", () => { selectedCueIndex = index; renderCueRows(); });
    const time = document.createElement("input"); time.type = "number"; time.min = "0"; time.step = "0.001"; time.placeholder = "秒"; time.value = Number.isFinite(row.start_ms) ? (row.start_ms / 1000).toFixed(3) : ""; time.setAttribute("aria-label", `第 ${index + 1} 行時間（秒）`); time.addEventListener("input", () => { row.start_ms = time.value === "" ? Number.NaN : Number(time.value) * 1000; });
    const text = document.createElement("textarea"); text.rows = 2; text.value = row.text || ""; text.setAttribute("aria-label", `第 ${index + 1} 行歌詞`); text.addEventListener("input", () => { row.text = text.value; });
    const seek = node("button", "button secondary", "試聽"); seek.type = "button"; seek.disabled = !Number.isFinite(row.start_ms); seek.addEventListener("click", () => editorPlayer?.seekTo(row.start_ms));
    container.append(select, time, text, seek); return container;
  }));
  const validation = validateCueRows(cueRows);
  el.cueValidation.replaceChildren(...[...validation.errors.map((item) => `錯誤：${item}`), ...validation.warnings.map((item) => `提醒：${item}`)].map((item) => node("li", "", item)));
}

function parseLrcIntoRows() {
  const result = parseLrc(el.lrcText.value); cueRows = result.cues.map((cue) => ({ start_ms: cue.start_ms, text: cue.text })); selectedCueIndex = cueRows.length ? 0 : -1; renderCueRows();
  el.lrcSummary.textContent = `解析 ${cueRows.length} 行；offset ${result.offsetMs} ms${result.metadata.ar ? `；歌手 ${result.metadata.ar}` : ""}`;
  el.lrcErrors.replaceChildren(...result.errors.map((error) => node("li", "", error)));
}

function createPlainCueRows() { const lines = el.plainLyrics.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean); cueRows = lines.map((text) => ({ start_ms: Number.NaN, text })); selectedCueIndex = cueRows.length ? 0 : -1; renderCueRows(); }
function addCue() { cueRows.push({ start_ms: editorPlayer?.getCurrentTimeMs() ?? 0, text: "" }); selectedCueIndex = cueRows.length - 1; renderCueRows(); }
function markCue() { if (selectedCueIndex < 0 || !cueRows[selectedCueIndex]) return showMessage("請先選取一行歌詞。", "error"); cueRows[selectedCueIndex].start_ms = editorPlayer?.getCurrentTimeMs() ?? 0; if (selectedCueIndex < cueRows.length - 1) selectedCueIndex += 1; renderCueRows(); }
function moveCue(delta) { if (selectedCueIndex < 0) return; const target = selectedCueIndex + delta; if (target < 0 || target >= cueRows.length) return; [cueRows[selectedCueIndex], cueRows[target]] = [cueRows[target], cueRows[selectedCueIndex]]; selectedCueIndex = target; renderCueRows(); }
function deleteCue() { if (selectedCueIndex < 0) return; cueRows.splice(selectedCueIndex, 1); selectedCueIndex = Math.min(selectedCueIndex, cueRows.length - 1); renderCueRows(); }

async function saveCues() {
  if (!currentSong) return;
  const validation = validateCueRows(cueRows); renderCueRows();
  if (validation.errors.length) return showMessage("請先修正同步歌詞錯誤。", "error", 0);
  const payload = prepareCuesForSave(cueRows); el.saveCues.disabled = true; el.saveCues.textContent = "儲存中…";
  const { data, error } = await supabase.rpc("replace_song_lyric_cues", { p_song_id: currentSong.id, p_cues: payload });
  el.saveCues.disabled = false; el.saveCues.textContent = "儲存";
  if (error) return showMessage(errorMessage(error, "同步歌詞儲存失敗；原 transaction 已回滾。"), "error", 0);
  cueRows = payload.map((cue) => ({ start_ms: cue.start_ms, text: cue.text })); renderCueRows(); showMessage(`已替換 ${data} 句同步歌詞。`, "success");
}

async function createTag(event) {
  event.preventDefault(); const name = el.newTagName.value.trim(); const slug = slugify(el.newTagSlug.value || name); if (!name || !slug) return showMessage("標籤名稱與 slug 為必填。", "error");
  el.createTag.disabled = true; const { error } = await supabase.from("tags").insert({ name, slug }); el.createTag.disabled = false;
  if (error) return showMessage(errorMessage(error, "無法建立標籤；名稱或 slug 可能重複。"), "error", 0);
  el.tagForm.reset(); showMessage("標籤已建立。", "success"); await loadData();
}

async function updateTag(tag, rawName, rawSlug) {
  const name = rawName.trim(); const slug = slugify(rawSlug); if (!name || !slug) return showMessage("標籤名稱與 slug 不可為空。", "error");
  const { error } = await supabase.from("tags").update({ name, slug }).eq("id", tag.id);
  if (error) return showMessage(errorMessage(error, "無法更新標籤；名稱或 slug 可能重複。"), "error", 0);
  showMessage("標籤已更新。", "success"); await loadData();
}

async function deleteTag(tag, count) {
  if (!confirm(count ? `「${tag.name}」正被 ${count} 首歌曲使用。確定移除所有關聯並刪除標籤？` : `確定刪除未使用的「${tag.name}」？`)) return;
  const { error } = await supabase.rpc("delete_tag", { p_tag_id: tag.id, p_confirm_used: count > 0 });
  if (error) return showMessage(errorMessage(error, "無法刪除標籤。"), "error", 0);
  showMessage("標籤及其歌曲關聯已刪除。", "success"); await loadData();
}

async function checkAdmin() { isAdmin = false; if (!currentUser) return; const { data, error } = await supabase.rpc("is_admin"); if (error) showMessage(errorMessage(error, "無法驗證管理員權限。"), "error", 0); else isAdmin = data === true; }
async function signIn() { if (!configured) return showMessage("請先設定有效的 Supabase project。", "error", 0); el.headerSignIn.disabled = true; el.panelSignIn.disabled = true; try { await verifyGoogleAuthConfiguration(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY); const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: oauthRedirectUrl(window.location.href, "admin") } }); if (error) throw error; } catch (error) { showMessage(errorMessage(error, "無法開始 Google 登入。"), "error", 0); } finally { el.headerSignIn.disabled = false; el.panelSignIn.disabled = false; } }
async function signOut() { const { error } = await supabase.auth.signOut({ scope: "local" }); if (error) return showMessage(errorMessage(error, "無法登出。"), "error"); await queueSession(null, "SIGNED_OUT"); showMessage("已登出。", "success"); }
async function applySession(session) { currentUser = session?.user || null; await checkAdmin(); updateAccessUI(); if (isAdmin) await loadData(); else { songs = []; tags = []; updateCounts(); renderSongs(); renderTags(); } }
function queueSession(session, event) { authQueue = authQueue.catch(console.error).then(async () => { const id = session?.user?.id || null; if (id === appliedAuthUserId && event !== "USER_UPDATED") { currentUser = session?.user || null; updateAccessUI(); return; } await applySession(session); appliedAuthUserId = id; }); return authQueue; }

function bind() {
  el.headerSignIn.addEventListener("click", signIn); el.panelSignIn.addEventListener("click", signIn); el.signOut.addEventListener("click", signOut); el.deniedSignOut.addEventListener("click", signOut); el.refresh.addEventListener("click", loadData); el.search.addEventListener("input", renderSongs); el.status.addEventListener("change", renderSongs);
  el.closePreview.addEventListener("click", () => el.preview.close()); el.closePreviewFooter.addEventListener("click", () => el.preview.close()); el.preview.addEventListener("close", () => { el.previewFrame.removeAttribute("src"); el.openPdf.href = "#"; el.downloadPdf.href = "#"; });
  el.tagSearch.addEventListener("input", renderTags); el.tagForm.addEventListener("submit", createTag); el.newTagName.addEventListener("input", () => { if (document.activeElement !== el.newTagSlug) el.newTagSlug.value = slugify(el.newTagName.value); });
  el.closeEditor.addEventListener("click", closeEditor); el.editor.addEventListener("close", () => { clearInterval(editorTimer); editorPlayer?.destroy(); editorPlayer = null; currentSong = null; }); el.metadataForm.addEventListener("submit", saveMetadata); el.youtube.addEventListener("input", validateEditorYoutube);
  el.lrcFile.addEventListener("change", async () => {
    const file = el.lrcFile.files[0];
    if (!file) return;
    if (file.size > 1_000_000) {
      showStatus("LRC 檔案不可超過 1 MB。", "error");
      el.lrcFile.value = "";
      return;
    }
    try {
      el.lrcText.value = await file.text();
    } catch (error) {
      showStatus(`無法讀取 LRC：${error.message}`, "error");
    }
  });
  el.previewLrc.addEventListener("click", parseLrcIntoRows); el.createLines.addEventListener("click", createPlainCueRows); el.addCue.addEventListener("click", addCue); el.markCue.addEventListener("click", markCue); el.moveUp.addEventListener("click", () => moveCue(-1)); el.moveDown.addEventListener("click", () => moveCue(1)); el.deleteCue.addEventListener("click", deleteCue); el.saveCues.addEventListener("click", saveCues);
  document.addEventListener("keydown", (event) => { if (!el.editor.open) return; const target = event.target; if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement || target instanceof HTMLButtonElement || target.isContentEditable) return; if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") { event.preventDefault(); saveCues(); } else if (event.key === "Enter") { event.preventDefault(); markCue(); } else if (event.key === "ArrowUp") { event.preventDefault(); selectedCueIndex = Math.max(0, selectedCueIndex - 1); renderCueRows(); } else if (event.key === "ArrowDown") { event.preventDefault(); selectedCueIndex = Math.min(cueRows.length - 1, selectedCueIndex + 1); renderCueRows(); } });
}

async function init() {
  bind(); if (!configured) { el.setup.classList.remove("hidden"); updateAccessUI(); return; }
  const oauth = parseOAuthResponse(window.location.href); supabase.auth.onAuthStateChange((event, session) => setTimeout(() => void queueSession(session, event), 0)); const { data, error } = await supabase.auth.getSession(); await queueSession(data?.session || null, "GET_SESSION"); cleanOAuthCallbackFromBrowser(); if (oauth.error) showMessage(oauth.error, "error", 0); else if (error) showMessage(errorMessage(error, "無法讀取登入 session。"), "error", 0);
}

init();
