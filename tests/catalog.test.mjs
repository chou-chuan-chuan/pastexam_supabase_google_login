import test from "node:test";
import assert from "node:assert/strict";

import { filterSongs, matchesSong, pendingSongPayload, uploaderDisplayName } from "../assets/catalog.js";

const songs = [
  {
    title: "Moon River",
    artist: "Audrey Hepburn",
    album: "Breakfast at Tiffany's",
    release_year: 1961,
    language: "English",
    genre: "Soundtrack",
    notes: "Classic ballad",
    song_tags: [{ tags: { id: "tag-1", name: "電影", slug: "movie" } }]
  },
  {
    title: "島嶼天光",
    artist: "滅火器",
    album: "島嶼天光",
    release_year: 2014,
    language: "中文",
    genre: "Rock",
    notes: "Taiwan",
    song_tags: [{ tags: { id: "tag-2", name: "現場", slug: "live" } }]
  }
];

test("searches title, artist, album, language, genre, tag, and year", () => {
  for (const query of ["Moon", "Audrey", "Breakfast", "English", "Soundtrack", "電影", "1961"]) {
    assert.equal(matchesSong(songs[0], { query }), true, query);
  }
});

test("combines language, genre, year, and multiple tag filters", () => {
  assert.deepEqual(filterSongs(songs, {
    language: "中文",
    genre: "Rock",
    year: "2014",
    tags: ["live"]
  }).map((song) => song.title), ["島嶼天光"]);
  assert.equal(matchesSong(songs[1], { tags: ["live", "movie"] }), false);
});

test("submission payload always forces pending status", () => {
  const payload = pendingSongPayload({
    title: "Song",
    artist: "Artist",
    status: "approved",
    youtube_video_id: "dQw4w9WgXcQ",
    pdf_path: "user/file.pdf",
    original_filename: "lyrics.pdf"
  }, "user-id");
  assert.equal(payload.status, "pending");
  assert.equal(payload.uploader_id, "user-id");
});

test("uploader display prefers the stored OAuth name and falls back to UUID", () => {
  assert.equal(uploaderDisplayName({ uploader_display_name: " Google User ", uploader_id: "uuid" }), "Google User");
  assert.equal(uploaderDisplayName({ uploader_id: "uuid" }), "uuid");
  assert.equal(uploaderDisplayName({}), "—");
});
