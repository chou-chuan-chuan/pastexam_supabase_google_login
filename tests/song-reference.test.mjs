import test from "node:test";
import assert from "node:assert/strict";
import { approvedSongReferences, approvedMetadataValues, songReferenceSearch, referenceFormValues, hasMeaningfulUploadMetadata } from "../assets/song-reference.js";
import { pendingSongPayload } from "../assets/catalog.js";
import { extractYouTubeVideoId } from "../assets/youtube.js";

const tags = [{ id: "live" }, { id: "movie" }, { id: "other" }];
const approved = {
  id: "private-song-id", status: "approved", title: "Lemon", artist: "米津玄師",
  album: "STRAY SHEEP", release_year: 2018, language: "日本語", genre: "Pop",
  youtube_video_id: "SX_ViT4Ra7k",
  song_tags: [{ tags: { id: "live", internal: "private-tag-data" } }, { tags: { id: "deleted" } }, { tags: { id: "live" } }, { tags: null }],
  notes: "private-notes", uploader_id: "private-user", uploader_display_name: "private-name",
  pdf_path: "private-file-path", original_filename: "private-filename", created_at: "private-time", reviewed_at: "private-review"
};
const pending = { ...approved, status: "pending", title: "Secret pending", artist: "Private artist", uploader_id: "another-user" };
const rejected = { ...approved, status: "rejected", title: "Secret rejected", album: "Private album" };
const mixed = [pending, approved, rejected];

test("all song entry points exclude pending/rejected, other users' submissions and missing approval", () => {
  const input = [...mixed, { ...approved, status: "Approved" }, { ...approved, status: undefined }, null];
  assert.deepEqual(approvedSongReferences(input, tags).map((song) => song.title), ["Lemon"]);
  assert.deepEqual(songReferenceSearch(input, "", tags).map((song) => song.title), ["Lemon"]);
  for (const song of [pending, rejected, {}, null]) assert.equal(referenceFormValues(song, tags), null);
  assert.deepEqual(songReferenceSearch(input, "Secret"), []);
  assert.deepEqual(approvedMetadataValues(input, "artist"), ["米津玄師"]);
});

test("deduplicates trimmed artist, album, language, genre and year values; ignores blanks/nulls", () => {
  const input = [approved, { ...approved, artist: " 米津玄師 ", release_year: "2018" },
    { status: "approved", artist: null, album: "", language: " \t ", genre: undefined, release_year: null }, pending, rejected];
  for (const field of ["artist", "album", "language", "genre", "release_year"]) {
    assert.deepEqual(approvedMetadataValues(input, field), [String(approved[field])]);
  }
  assert.deepEqual(approvedMetadataValues(input, "uploader_id"), []);
  assert.deepEqual(approvedMetadataValues(input, "notes"), []);
});

test("ranks exact title, title prefix/substring, artist exact/prefix/substring, then other metadata", () => {
  const rows = [
    { title: "Album match", artist: "Other", album: "LEMON" },
    { title: "Artist contains", artist: "The Lemon band" },
    { title: "Artist prefix", artist: "Lemon band" },
    { title: "Artist exact", artist: "Lemon" },
    { title: "Sweet Lemon", artist: "Other" },
    { title: "Lemon Tree", artist: "Other" },
    { title: "Lemon", artist: "Other" }
  ].map((song) => ({ ...song, status: "approved" }));
  assert.deepEqual(songReferenceSearch(rows, "  lEmOn ").map((song) => song.title), [
    "Lemon", "Lemon Tree", "Sweet Lemon", "Artist exact", "Artist prefix", "Artist contains", "Album match"
  ]);
});

test("searches artist, album, year, language and genre with partial case-insensitive queries", () => {
  for (const query of ["米津", "stray", "201", "日本", "POP"]) {
    assert.deepEqual(songReferenceSearch(mixed, query).map((song) => song.title), ["Lemon"], query);
  }
  const accented = { ...approved, title: "CAFÉ" };
  assert.equal(songReferenceSearch([accented], " cafe\u0301 ")[0].title, "CAFÉ");
});

test("limits to eight results with stable ties and never mutates the catalog", () => {
  const input = Array.from({ length: 12 }, (_, index) => ({ ...approved, title: `Song ${index}` }));
  const original = structuredClone(input);
  assert.deepEqual(songReferenceSearch(input, "song").map((song) => song.title), input.slice(0, 8).map((song) => song.title));
  assert.deepEqual(input, original);
  assert.equal(songReferenceSearch(input, "").length, 8);
  assert.deepEqual(songReferenceSearch(input, "absent"), []);
});

test("maps exactly reusable fields, canonical YouTube URL, and existing approved/catalog tag intersection", () => {
  const values = referenceFormValues(approved, tags);
  assert.deepEqual(values, {
    title: "Lemon", artist: "米津玄師", album: "STRAY SHEEP", release_year: "2018", language: "日本語", genre: "Pop",
    youtube_url: "https://www.youtube.com/watch?v=SX_ViT4Ra7k", tag_ids: ["live"]
  });
  assert.deepEqual(referenceFormValues(approved).tag_ids, []);
  const blank = referenceFormValues({ status: "approved", youtube_video_id: "invalid", album: null });
  assert.equal(blank.youtube_url, "");
  assert.equal(blank.album, "");
  assert.deepEqual(blank.tag_ids, []);
});

test("reference results cannot leak or search IDs, notes, files, timestamps or internal tag metadata", () => {
  const serialized = JSON.stringify(approvedSongReferences(mixed, tags));
  assert.doesNotMatch(serialized, /private-|Secret|uploader|pdf_path|original_filename|created_at|reviewed_at|song_tags|youtube_video_id/);
  for (const query of ["private", "another-user", "SX_ViT4Ra7k"]) assert.deepEqual(songReferenceSearch(mixed, query, tags), []);
});

test("empty/unavailable approved catalog works and refreshed statuses immediately affect suggestions", () => {
  assert.deepEqual(approvedSongReferences(null), []);
  assert.deepEqual(approvedMetadataValues([pending, rejected], "title"), []);
  assert.deepEqual(songReferenceSearch([pending, rejected], ""), []);
  assert.equal(songReferenceSearch([{ ...pending, status: "approved" }], "Secret").length, 1);
  assert.deepEqual(songReferenceSearch([{ ...approved, status: "rejected" }], "Lemon"), []);
});

test("overwrite protection detects each reusable field and tags but ignores PDF and notes", () => {
  for (const field of ["title", "artist", "album", "release_year", "language", "genre", "youtube_url"]) {
    assert.equal(hasMeaningfulUploadMetadata({ [field]: "entered" }), true, field);
  }
  assert.equal(hasMeaningfulUploadMetadata({ tag_ids: ["live"] }), true);
  assert.equal(hasMeaningfulUploadMetadata({ title: "  ", album: null, tag_ids: [], notes: "Keep", pdf_path: "new.pdf" }), false);
});

test("copied metadata still produces an independent pending submission for the current uploader", () => {
  const values = referenceFormValues(approved, tags);
  const payload = pendingSongPayload({ ...values, youtube_video_id: extractYouTubeVideoId(values.youtube_url),
    notes: "My notes", pdf_path: "current-user/fresh.pdf", original_filename: "fresh.pdf" }, "current-user");
  assert.equal(payload.status, "pending");
  assert.equal(payload.uploader_id, "current-user");
  assert.equal(payload.pdf_path, "current-user/fresh.pdf");
  assert.equal(payload.notes, "My notes");
  assert.doesNotMatch(JSON.stringify(payload), /private-|source_song_id|approved_song_id|parent_song_id|lifecycle_id/);
  assert.equal("id" in payload, false);
});
