import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const sourceFiles = ["assets/app.js", "assets/admin.js", "assets/song.js"];

test("user-controlled content is rendered without innerHTML", async () => {
  for (const file of sourceFiles) {
    const source = await readFile(new URL(`../${file}`, import.meta.url), "utf8");
    assert.doesNotMatch(source, /\.innerHTML\s*=/, file);
    assert.match(source, /textContent/, file);
  }
});

test("public submission code forces pending and never accepts status from the form", async () => {
  const app = await readFile(new URL("../assets/app.js", import.meta.url), "utf8");
  const catalog = await readFile(new URL("../assets/catalog.js", import.meta.url), "utf8");
  assert.doesNotMatch(app, /status\s*:\s*["']approved["']/);
  assert.match(catalog, /status:\s*["']pending["']/);
});

test("YouTube integration uses the official iframe API without autoplay or downloads", async () => {
  const player = await readFile(new URL("../assets/youtube-player.js", import.meta.url), "utf8");
  assert.match(player, /https:\/\/www\.youtube\.com\/iframe_api/);
  assert.match(player, /autoplay:\s*0/);
  assert.doesNotMatch(player, /fetch\([^)]*youtube|download.*youtube|captions/i);
});
