import test from "node:test";
import assert from "node:assert/strict";

import {
  extractYouTubeVideoId,
  isValidYouTubeVideoId,
  normalizeYouTubeUrl,
  youtubeThumbnailUrl
} from "../assets/youtube.js";

const ID = "dQw4w9WgXcQ";

test("extracts supported YouTube URL formats", () => {
  assert.equal(extractYouTubeVideoId(`https://www.youtube.com/watch?v=${ID}`), ID);
  assert.equal(extractYouTubeVideoId(`https://youtu.be/${ID}`), ID);
  assert.equal(extractYouTubeVideoId(`https://www.youtube.com/embed/${ID}`), ID);
  assert.equal(extractYouTubeVideoId(`https://www.youtube.com/shorts/${ID}`), ID);
  assert.equal(extractYouTubeVideoId(`https://www.youtube.com/watch?list=test&v=${ID}&t=42`), ID);
});

test("normalizes a YouTube URL and builds a safe thumbnail", () => {
  assert.equal(normalizeYouTubeUrl(`https://youtu.be/${ID}?si=share`), `https://www.youtube.com/watch?v=${ID}`);
  assert.equal(youtubeThumbnailUrl(ID), `https://i.ytimg.com/vi/${ID}/hqdefault.jpg`);
});

test("rejects empty, invalid, non-YouTube, script, and HTML input", () => {
  for (const value of [
    "",
    "not-a-url",
    "https://example.com/watch?v=dQw4w9WgXcQ",
    "javascript:alert(1)",
    '<iframe src="https://youtube.com/embed/dQw4w9WgXcQ"></iframe>',
    "https://youtube.com/watch?v=short",
    "https://youtube.com.evil.example/watch?v=dQw4w9WgXcQ"
  ]) {
    assert.equal(extractYouTubeVideoId(value), null, value);
  }
  assert.equal(isValidYouTubeVideoId("bad!videoid"), false);
});
