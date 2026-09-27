import { sortSongsForDisplay } from "./catalog.js";

export const PLAYLIST_POSITION_STEP = 1024;
// Route key only; membership uses the existing Favorite tag's stable id.
export const SMART_FAVORITE_KEY = "my-favorite";
export const FAVORITE_TAG_ID = "92f53132-743b-4032-8d9a-df893f5a4f8c";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value) {
  return UUID_PATTERN.test(String(value || ""));
}

export function playlistContextFromUrl(currentUrl) {
  const params = new URL(currentUrl).searchParams;
  const playlistId = params.get("playlist");
  if (isUuid(playlistId)) return playlistId;
  return smartPlaylistContextFromUrl(currentUrl);
}

export function smartPlaylistContextFromUrl(currentUrl) {
  const params = new URL(currentUrl).searchParams;
  const language = String(params.get("language") || "").trim();
  if (language) return { type: "language", value: language };
  return params.get("smart") === SMART_FAVORITE_KEY
    ? { type: "smart", value: SMART_FAVORITE_KEY }
    : null;
}

export function isSmartPlaylistContext(context) {
  return Boolean(
    context
    && (context.type === "language" && String(context.value || "").trim()
      || context.type === "smart" && context.value === SMART_FAVORITE_KEY)
  );
}

function appendPlaylistContext(params, context) {
  if (isUuid(context)) params.set("playlist", context);
  else if (context?.type === "language") params.set("language", String(context.value).trim());
  else if (context?.type === "smart" && context.value === SMART_FAVORITE_KEY) params.set("smart", context.value);
}

export function playlistSongUrl(songId, context) {
  const params = new URLSearchParams({ id: songId });
  appendPlaylistContext(params, context);
  return `./song.html?${params.toString()}`;
}

export function smartPlaylistUrl(context) {
  const params = new URLSearchParams();
  appendPlaylistContext(params, context);
  return isSmartPlaylistContext(context) ? `./playlist.html?${params.toString()}` : "./playlist.html";
}

export function sortPlaylistItems(items = []) {
  return [...items].sort((left, right) => {
    const positionDifference = Number(left.position) - Number(right.position);
    if (positionDifference) return positionDifference;
    return String(left.song_id).localeCompare(String(right.song_id));
  });
}

export function normalizePlaylistMembership(rows = []) {
  return [...new Set(rows.map((row) => row?.playlist_id).filter(isUuid))];
}

export function playlistNeighbors(items = [], currentSongId) {
  const ordered = sortPlaylistItems(items);
  const index = ordered.findIndex((item) => item.song_id === currentSongId);
  if (index < 0) return { index: -1, total: ordered.length, previous: null, next: null };
  return {
    index,
    total: ordered.length,
    previous: ordered[index - 1] || null,
    next: ordered[index + 1] || null
  };
}

export function playlistSongCount(playlist) {
  const value = playlist?.playlist_items?.[0]?.count ?? playlist?.song_count ?? 0;
  const count = Number(value);
  return Number.isFinite(count) && count >= 0 ? count : 0;
}

export function playlistSchemaUnavailable(error) {
  const text = `${error?.code || ""} ${error?.message || ""}`.toLowerCase();
  return text.includes("42p01") || text.includes("pgrst205") || text.includes("playlists") && text.includes("schema cache") || text.includes("move_playlist_item") && text.includes("not find") || text.includes("add_song_to_playlist") && text.includes("not find");
}

export async function loadUserPlaylists(client) {
  return client
    .from("playlists")
    .select("id,owner_id,name,description,created_at,updated_at,playlist_items(count)")
    .order("updated_at", { ascending: false });
}

export async function loadPlaylist(client, playlistId) {
  return client
    .from("playlists")
    .select("id,owner_id,name,description,created_at,updated_at")
    .eq("id", playlistId)
    .maybeSingle();
}

export async function loadPlaylistItems(client, playlistId) {
  return client
    .from("playlist_items")
    .select("playlist_id,song_id,position,added_at,songs!inner(id,title,artist,language,genre,youtube_video_id,status)")
    .eq("playlist_id", playlistId)
    .eq("songs.status", "approved")
    .order("position", { ascending: true });
}

function approvedSongs(songs = []) {
  return songs.filter((song) => song?.status === "approved");
}

function hasFavoriteTag(song) {
  // Public song_tags remain readable even when tags metadata is hidden by RLS.
  return (song?.song_tags || []).some((relation) => relation?.tag_id === FAVORITE_TAG_ID);
}

export function smartPlaylistItems(songs = [], displayOrder = [], context) {
  if (!isSmartPlaylistContext(context)) return [];
  const ordered = sortSongsForDisplay(approvedSongs(songs), displayOrder);
  const matching = context.type === "language"
    ? ordered.filter((song) => String(song.language || "").trim() === String(context.value).trim())
    : ordered.filter(hasFavoriteTag);
  return matching.map((song, index) => ({
    song_id: song.id,
    position: (index + 1) * PLAYLIST_POSITION_STEP,
    songs: song
  }));
}

export function smartPlaylistCards(songs = [], displayOrder = []) {
  const ordered = sortSongsForDisplay(approvedSongs(songs), displayOrder);
  const languages = new Map();
  for (const song of ordered) {
    const language = String(song.language || "").trim();
    if (!language) continue;
    languages.set(language, (languages.get(language) || 0) + 1);
  }
  return [
    {
      name: "My favorite",
      description: "具有 Favorite 標籤的歌曲。",
      song_count: ordered.filter(hasFavoriteTag).length,
      context: { type: "smart", value: SMART_FAVORITE_KEY }
    },
    ...[...languages.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([language, count]) => ({
        name: language,
        description: `語言：${language}`,
        song_count: count,
        context: { type: "language", value: language }
      }))
  ];
}

export async function loadSmartPlaylistCatalog(client) {
  const [songsResult, orderResult] = await Promise.all([
    client
      .from("songs")
      .select("id,title,artist,language,genre,youtube_video_id,status,created_at,song_tags(tag_id)")
      .eq("status", "approved"),
    client.from("song_display_order").select("song_id,position")
  ]);
  return {
    songs: songsResult.data || [],
    displayOrder: orderResult.error ? [] : (orderResult.data || []),
    error: songsResult.error || null
  };
}

export async function loadSmartPlaylistContext(client, context) {
  if (!isSmartPlaylistContext(context)) return { playlist: null, items: [], error: null };
  const catalog = await loadSmartPlaylistCatalog(client);
  if (catalog.error) return { playlist: null, items: [], error: catalog.error };
  const name = context.type === "language" ? String(context.value).trim() : "My favorite";
  return {
    playlist: {
      kind: "smart",
      name,
      description: context.type === "language"
        ? "自動歌單 · 根據歌曲語言更新"
        : "自動歌單 · 根據 Favorite 標籤更新",
      context
    },
    items: smartPlaylistItems(catalog.songs, catalog.displayOrder, context),
    error: null
  };
}

export async function loadPlaylistContext(client, context) {
  if (isSmartPlaylistContext(context)) return loadSmartPlaylistContext(client, context);
  if (!isUuid(context)) return { playlist: null, items: [], error: null };
  const [playlistResult, itemResult] = await Promise.all([
    loadPlaylist(client, context),
    loadPlaylistItems(client, context)
  ]);
  const error = playlistResult.error || itemResult.error;
  if (error || !playlistResult.data) return { playlist: null, items: [], error };
  return {
    playlist: { ...playlistResult.data, kind: "private", context },
    items: sortPlaylistItems(itemResult.data || []),
    error: null
  };
}
