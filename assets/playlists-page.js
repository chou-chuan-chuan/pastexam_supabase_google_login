import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY } from "../config.js";
import { SUPABASE_CLIENT_OPTIONS, cleanOAuthCallbackFromBrowser, oauthRedirectUrl, parseOAuthResponse, verifyGoogleAuthConfiguration } from "./auth.js";
import { loadUserPlaylists, playlistSchemaUnavailable, playlistSongCount } from "./playlists.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS) : null;
const $ = (selector) => document.querySelector(selector);
const el = {
  message: $("#playlistMessage"), userLabel: $("#userLabel"), signIn: $("#googleSignInButton"), stateSignIn: $("#stateSignInButton"), signOut: $("#signOutButton"),
  create: $("#createPlaylistButton"), createFirst: $("#createFirstPlaylistButton"), signedOut: $("#signedOutState"), loading: $("#playlistLoading"), grid: $("#playlistGrid"), empty: $("#playlistEmpty"),
  dialog: $("#playlistEditorDialog"), form: $("#playlistEditorForm"), editorTitle: $("#playlistEditorTitle"), editorId: $("#playlistEditorId"), name: $("#playlistName"), description: $("#playlistDescription"), save: $("#savePlaylistButton"), close: $("#closePlaylistEditorButton"), cancel: $("#cancelPlaylistEditorButton")
};

let currentUser = null;
let playlists = [];
let messageTimer;

function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function showMessage(text, kind = "info", timeout = 7000) {
  clearTimeout(messageTimer);
  el.message.textContent = text;
  el.message.className = `notice ${kind}`;
  if (timeout) messageTimer = setTimeout(() => el.message.classList.add("hidden"), timeout);
}

function displayDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("zh-TW", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function setView(state) {
  el.signedOut.classList.toggle("hidden", state !== "signed-out");
  el.loading.classList.toggle("hidden", state !== "loading");
  el.grid.classList.toggle("hidden", state !== "ready");
  el.empty.classList.toggle("hidden", state !== "empty");
}

function renderAccount() {
  const signedIn = Boolean(currentUser);
  el.userLabel.textContent = signedIn ? (currentUser.user_metadata?.full_name || currentUser.email || "已登入") : "訪客模式";
  el.signIn.classList.toggle("hidden", signedIn);
  el.signOut.classList.toggle("hidden", !signedIn);
  el.create.classList.toggle("hidden", !signedIn);
}

function playlistCard(playlist) {
  const card = node("article", "playlist-card");
  const content = node("div", "playlist-card-content");
  content.append(node("h2", "", playlist.name));
  content.append(node("p", "playlist-card-description", playlist.description || "尚無描述"));
  content.append(node("p", "card-meta", `${playlistSongCount(playlist)} 首歌曲 · 更新於 ${displayDate(playlist.updated_at)}`));
  const actions = node("div", "playlist-card-actions");
  const open = node("a", "button primary", "開啟");
  open.href = `./playlist.html?id=${encodeURIComponent(playlist.id)}`;
  const edit = node("button", "button secondary", "重新命名 / 編輯");
  edit.type = "button";
  edit.addEventListener("click", () => openEditor(playlist));
  const remove = node("button", "button danger", "刪除");
  remove.type = "button";
  remove.addEventListener("click", () => deletePlaylist(playlist));
  actions.append(open, edit, remove);
  card.append(content, actions);
  return card;
}

function renderPlaylists() {
  el.grid.replaceChildren(...playlists.map(playlistCard));
  setView(playlists.length ? "ready" : "empty");
}

async function loadPlaylists() {
  if (!currentUser) { playlists = []; setView("signed-out"); return; }
  setView("loading");
  const { data, error } = await loadUserPlaylists(supabase);
  if (error) {
    playlists = [];
    setView("empty");
    showMessage(playlistSchemaUnavailable(error) ? "播放清單功能尚未完成資料庫部署。" : (error.message || "無法載入播放清單。"), "error", 0);
    return;
  }
  playlists = data || [];
  renderPlaylists();
}

function openEditor(playlist = null) {
  el.editorTitle.textContent = playlist ? "編輯播放清單" : "建立播放清單";
  el.editorId.value = playlist?.id || "";
  el.name.value = playlist?.name || "";
  el.description.value = playlist?.description || "";
  el.dialog.showModal();
  el.name.focus();
}

async function savePlaylist(event) {
  event.preventDefault();
  const name = el.name.value.trim();
  const description = el.description.value.trim() || null;
  if (!name) return showMessage("播放清單名稱不可為空。", "error");
  el.save.disabled = true;
  const id = el.editorId.value;
  const result = id
    ? await supabase.from("playlists").update({ name, description }).eq("id", id)
    : await supabase.from("playlists").insert({ owner_id: currentUser.id, name, description });
  el.save.disabled = false;
  if (result.error) return showMessage(playlistSchemaUnavailable(result.error) ? "播放清單功能尚未完成資料庫部署。" : (result.error.message || "無法儲存播放清單。"), "error", 0);
  el.dialog.close();
  showMessage(id ? "播放清單已更新。" : "播放清單已建立。", "success");
  await loadPlaylists();
}

async function deletePlaylist(playlist) {
  if (!confirm(`確定刪除播放清單「${playlist.name}」？`)) return;
  const { error } = await supabase.from("playlists").delete().eq("id", playlist.id);
  if (error) return showMessage(error.message || "無法刪除播放清單。", "error", 0);
  showMessage("播放清單已刪除；歌曲資料不受影響。", "success");
  await loadPlaylists();
}

async function signIn() {
  if (!configured) return showMessage("請先設定有效的 Supabase project。", "error", 0);
  try {
    await verifyGoogleAuthConfiguration(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: oauthRedirectUrl(window.location.href, "playlists") } });
    if (error) throw error;
  } catch (error) { showMessage(error.message || "無法開始 Google 登入。", "error", 0); }
}

async function signOut() {
  const { error } = await supabase.auth.signOut({ scope: "local" });
  if (error) return showMessage(error.message || "無法登出。", "error");
}

async function applySession(session) {
  currentUser = session?.user || null;
  renderAccount();
  await loadPlaylists();
}

function bind() {
  el.signIn.addEventListener("click", signIn);
  el.stateSignIn.addEventListener("click", signIn);
  el.signOut.addEventListener("click", signOut);
  el.create.addEventListener("click", () => openEditor());
  el.createFirst.addEventListener("click", () => openEditor());
  el.form.addEventListener("submit", savePlaylist);
  el.close.addEventListener("click", () => el.dialog.close());
  el.cancel.addEventListener("click", () => el.dialog.close());
}

async function init() {
  bind();
  if (!configured) { renderAccount(); setView("signed-out"); showMessage("請先完成 Supabase 設定。", "warning", 0); return; }
  const oauth = parseOAuthResponse(window.location.href);
  supabase.auth.onAuthStateChange((_event, session) => setTimeout(() => void applySession(session), 0));
  const { data, error } = await supabase.auth.getSession();
  await applySession(data?.session || null);
  cleanOAuthCallbackFromBrowser();
  if (oauth.error || error) showMessage(oauth.error || error.message || "無法讀取登入 session。", "error", 0);
}

init();
