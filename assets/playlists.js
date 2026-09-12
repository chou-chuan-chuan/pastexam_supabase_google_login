export const PLAYLIST_POSITION_STEP = 1024;

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value) {
  return UUID_PATTERN.test(String(value || ""));
}

export function playlistContextFromUrl(currentUrl) {
  const value = new URL(currentUrl).searchParams.get("playlist");
  return isUuid(value) ? value : null;
}

export function playlistSongUrl(songId, playlistId) {
  const params = new URLSearchParams({ id: songId });
  if (isUuid(playlistId)) params.set("playlist", playlistId);
  return `./song.html?${params.toString()}`;
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

export async function loadPlaylistContext(client, playlistId) {
  if (!isUuid(playlistId)) return { playlist: null, items: [], error: null };
  const [playlistResult, itemResult] = await Promise.all([
    loadPlaylist(client, playlistId),
    loadPlaylistItems(client, playlistId)
  ]);
  const error = playlistResult.error || itemResult.error;
  if (error || !playlistResult.data) return { playlist: null, items: [], error };
  return {
    playlist: playlistResult.data,
    items: sortPlaylistItems(itemResult.data || []),
    error: null
  };
}
