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

test("loads the versioned supplemental webfont first and manifests Latin, German, and Japanese coverage", async () => {
  const [css, manifestText] = await Promise.all([
    readFile(new URL("../assets/style.css", import.meta.url), "utf8"),
    readFile(new URL("../tools/font/glyph_manifest.json", import.meta.url), "utf8")
  ]);
  const manifest = JSON.parse(manifestText);
  assert.match(css, /font-family:\s*"QuanFangwei Supplement Web"/);
  assert.equal(manifest.derived_font.version, "1.015");
  assert.match(css, /QuanFangweiSupplementScript-Regular\.woff2\?v=1\.015/);
  assert.match(css, /QuanFangweiSupplementScript-Regular\.ttf\?v=1\.015/);
  assert.ok(css.indexOf("QuanFangweiSupplementScript-Regular.woff2") < css.indexOf("QuanFangweiSupplementScript-Regular.ttf"));
  assert.doesNotMatch(css, /font-family:\s*"ChenYuluoyan Web"/);
  assert.deepEqual(manifest.glyphs.map(({ character, codepoint, glyph_name }) => ({ character, codepoint, glyph_name })), [
    { character: "¿", codepoint: "U+00BF", glyph_name: "questiondown" },
    { character: "Ç", codepoint: "U+00C7", glyph_name: "Ccedilla" },
    { character: "ç", codepoint: "U+00E7", glyph_name: "ccedilla" },
    { character: "̧", codepoint: "U+0327", glyph_name: "uni0327" },
    { character: "¨", codepoint: "U+00A8", glyph_name: "dieresis" },
    { character: "̈", codepoint: "U+0308", glyph_name: "uni0308" },
    { character: "Ä", codepoint: "U+00C4", glyph_name: "Adieresis" },
    { character: "Ö", codepoint: "U+00D6", glyph_name: "Odieresis" },
    { character: "Ü", codepoint: "U+00DC", glyph_name: "Udieresis" },
    { character: "ä", codepoint: "U+00E4", glyph_name: "adieresis" },
    { character: "ö", codepoint: "U+00F6", glyph_name: "odieresis" },
    { character: "ü", codepoint: "U+00FC", glyph_name: "udieresis" },
    { character: "ß", codepoint: "U+00DF", glyph_name: "germandbls" },
    { character: "ẞ", codepoint: "U+1E9E", glyph_name: "uni1E9E" }
  ]);
  assert.match(manifest.groups.hiragana.characters, /あ.*ん.*ゔ/);
  assert.match(manifest.groups.katakana.characters, /ア.*ン.*ヴ/);
  assert.match(manifest.groups.japanese_marks.characters, /゙.*゚.*゛.*゜.*ー/);
  assert.equal(manifest.groups.hiragana.status, "verified");
  assert.equal(manifest.groups.katakana.status, "verified");
  assert.equal(manifest.groups.japanese_marks.status, "verified");
});
