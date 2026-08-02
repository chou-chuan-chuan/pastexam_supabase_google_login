import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const sourcePath = new URL("../assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf", import.meta.url);
const ttfPath = new URL("../assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf", import.meta.url);
const woff2Path = new URL("../assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2", import.meta.url);

test("keeps the official source font unchanged and ships valid font signatures", async () => {
  const [source, ttf, woff2] = await Promise.all([
    readFile(sourcePath),
    readFile(ttfPath),
    readFile(woff2Path)
  ]);
  assert.equal(createHash("sha256").update(source).digest("hex"), "1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db");
  assert.deepEqual([...ttf.subarray(0, 4)], [0, 1, 0, 0]);
  assert.equal(woff2.subarray(0, 4).toString("ascii"), "wOF2");
});

test("loads the supplemental webfont first and manifests the two requested characters", async () => {
  const [css, manifestText] = await Promise.all([
    readFile(new URL("../assets/style.css", import.meta.url), "utf8"),
    readFile(new URL("../tools/font/glyph_manifest.json", import.meta.url), "utf8")
  ]);
  const manifest = JSON.parse(manifestText);
  assert.match(css, /font-family:\s*"QuanFangwei Supplement Web"/);
  assert.ok(css.indexOf("QuanFangweiSupplementScript-Regular.woff2") < css.indexOf("QuanFangweiSupplementScript-Regular.ttf"));
  assert.doesNotMatch(css, /font-family:\s*"ChenYuluoyan Web"/);
  assert.deepEqual(manifest.glyphs.map(({ character, codepoint, glyph_name }) => ({ character, codepoint, glyph_name })), [
    { character: "¿", codepoint: "U+00BF", glyph_name: "questiondown" },
    { character: "Ç", codepoint: "U+00C7", glyph_name: "Ccedilla" }
  ]);
});
