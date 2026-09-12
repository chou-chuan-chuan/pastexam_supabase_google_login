import test from "node:test";
import assert from "node:assert/strict";

import {
  extractYouTubeVideoId,
  isValidYouTubeVideoId,
  normalizeYouTubeUrl,
  youtubeThumbnailUrl
} from "../assets/youtube.js";
import { YouTubePlayer } from "../assets/youtube-player.js";

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

test("YouTube player keeps normal playback manual and opts playlist playback into autoplay", async () => {
  const originalWindow = globalThis.window;
  const configurations = [];
  let playCalls = 0;
  let muted = false;
  let autoplayBlockedCalls = 0;
  globalThis.window = {
    location: { origin: "https://example.test" },
    YT: {
      Player: function (_container, configuration) {
        configurations.push(configuration);
        return {
          playVideo: () => { playCalls += 1; },
          mute: () => { muted = true; },
          unMute: () => { muted = false; },
          isMuted: () => muted
        };
      }
    }
  };

  try {
    const normalPlayer = new YouTubePlayer({}, ID);
    await normalPlayer.create();
    assert.equal(configurations[0].playerVars.autoplay, 0);

    let playlistPlayer;
    playlistPlayer = new YouTubePlayer({}, ID, {
      onReady: () => playlistPlayer.play(),
      onAutoplayBlocked: () => { autoplayBlockedCalls += 1; }
    }, { autoplay: true });
    await playlistPlayer.create();
    assert.equal(configurations[1].playerVars.autoplay, 1);
    configurations[1].events.onReady({});
    assert.equal(playCalls, 1);
    configurations[1].events.onAutoplayBlocked({});
    assert.equal(autoplayBlockedCalls, 1);
    playlistPlayer.mute();
    assert.equal(playlistPlayer.isMuted(), true);
    playlistPlayer.unMute();
    assert.equal(playlistPlayer.isMuted(), false);
  } finally {
    if (originalWindow === undefined) delete globalThis.window;
    else globalThis.window = originalWindow;
  }
});
