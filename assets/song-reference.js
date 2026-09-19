import { songTagObjects } from "./catalog.js";
import { youtubeWatchUrl } from "./youtube.js";

export const REFERENCE_METADATA_FIELDS = Object.freeze([
  "title", "artist", "album", "release_year", "language", "genre"
]);

const text = (value) => typeof value === "string" || typeof value === "number" ? String(value).trim() : "";
const normalized = (value) => text(value).normalize("NFC").toLowerCase();

// Explicit allowlist: references never carry song IDs, notes, uploader or file data.
// Every entry point accepting songs enforces approval here, including direct mapping.
export function referenceFormValues(song, tagCatalog = []) {
  if (song?.status !== "approved") return null;
  const values = Object.fromEntries(REFERENCE_METADATA_FIELDS.map((field) => [field, text(song[field])]));
  const availableTagIds = new Set(tagCatalog.map((tag) => tag.id));
  return {
    ...values,
    youtube_url: youtubeWatchUrl(song.youtube_video_id) || "",
    tag_ids: [...new Set(songTagObjects(song).map((tag) => tag.id)
      .filter((id) => typeof id === "string" && id.trim() && availableTagIds.has(id)))]
  };
}

export function approvedSongReferences(songs, tagCatalog = []) {
  return (Array.isArray(songs) ? songs : [])
    .filter((song) => song?.status === "approved")
    .map((song) => referenceFormValues(song, tagCatalog));
}

export function approvedMetadataValues(songs, field) {
  if (!REFERENCE_METADATA_FIELDS.includes(field)) return [];
  return [...new Set(approvedSongReferences(songs).map((song) => song[field]).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, "zh-Hant", { numeric: true }));
}

function matchRank(song, query) {
  if (!query) return 0;
  const title = normalized(song.title);
  const artist = normalized(song.artist);
  if (title === query) return 0;
  if (title.startsWith(query)) return 1;
  if (title.includes(query)) return 2;
  if (artist === query) return 3;
  if (artist.startsWith(query)) return 4;
  if (artist.includes(query)) return 5;
  return ["album", "release_year", "language", "genre"]
    .some((field) => normalized(song[field]).includes(query)) ? 6 : Infinity;
}

export function songReferenceSearch(songs, query, tagCatalog = []) {
  const search = normalized(query);
  return approvedSongReferences(songs, tagCatalog)
    .map((song, index) => ({ song, index, rank: matchRank(song, search) }))
    .filter(({ rank }) => Number.isFinite(rank))
    .sort((left, right) => left.rank - right.rank || left.index - right.index)
    .slice(0, 8)
    .map(({ song }) => song);
}

export function hasMeaningfulUploadMetadata(values = {}) {
  return [...REFERENCE_METADATA_FIELDS, "youtube_url"].some((field) => Boolean(text(values[field])))
    || (Array.isArray(values.tag_ids) && values.tag_ids.some((id) => Boolean(text(id))));
}
