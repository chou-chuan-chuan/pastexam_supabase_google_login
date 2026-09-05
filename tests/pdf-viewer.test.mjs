import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import { clampedRenderPixelRatio, fitPageDimensions, fitPageScale } from "../assets/pdf-viewer-utils.js";

const portraitPage = { width: 612, height: 792 };
const landscapePage = { width: 792, height: 612 };

function assertFits(containerWidth, containerHeight, page) {
  const fitted = fitPageDimensions(containerWidth, containerHeight, page.width, page.height);
  assert.ok(fitted.scale > 0);
  assert.ok(fitted.width <= containerWidth + Number.EPSILON);
  assert.ok(fitted.height <= containerHeight + Number.EPSILON);
  assert.ok(Math.abs(fitted.width / fitted.height - page.width / page.height) < 1e-12);
  return fitted;
}

test("fits a complete portrait page in a phone portrait viewport", () => {
  const fitted = assertFits(358, 620, portraitPage);
  assert.equal(fitted.width, 358);
  assert.ok(fitted.height < 620);
});

test("fits a complete portrait page in a tablet viewport", () => {
  const fitted = assertFits(720, 650, portraitPage);
  assert.equal(fitted.height, 650);
  assert.ok(fitted.width < 720);
});

test("fits a complete landscape page in a phone landscape viewport", () => {
  const fitted = assertFits(740, 280, landscapePage);
  assert.equal(fitted.height, 280);
  assert.ok(fitted.width < 740);
});

test("fits a complete landscape page in a desktop viewport", () => {
  const fitted = assertFits(1000, 700, landscapePage);
  assert.equal(fitted.height, 700);
  assert.ok(fitted.width < 1000);
});

test("fit sizing never exceeds either available dimension", () => {
  for (const [width, height, page] of [
    [320, 480, portraitPage],
    [768, 900, portraitPage],
    [844, 320, landscapePage],
    [1440, 780, landscapePage]
  ]) assertFits(width, height, page);
});

test("invalid or zero fit dimensions return a safe empty result", () => {
  for (const values of [[0, 100, 50, 50], [100, -1, 50, 50], [100, 100, NaN, 50], [100, 100, 50, Infinity]]) {
    assert.equal(fitPageScale(...values), 0);
    assert.deepEqual(fitPageDimensions(...values), { scale: 0, width: 0, height: 0 });
  }
});

test("render pixel ratio respects device density and memory cap", () => {
  assert.equal(clampedRenderPixelRatio(400, 600, 3), 2);
  assert.equal(clampedRenderPixelRatio(2000, 2000, 2), 1);
  assert.equal(clampedRenderPixelRatio(0, 600, 2), 1);
});

test("shared viewer pins matching PDF.js main and worker versions and owns lifecycle", async () => {
  const viewer = await readFile(new URL("../assets/pdf-viewer.js", import.meta.url), "utf8");
  assert.match(viewer, /PDFJS_VERSION = "4\.10\.38"/);
  assert.match(viewer, /pdfjs-dist@\$\{PDFJS_VERSION\}\/build\/pdf\.min\.mjs/);
  assert.match(viewer, /pdfjs-dist@\$\{PDFJS_VERSION\}\/build\/pdf\.worker\.min\.mjs/);
  assert.match(viewer, /new Uint8Array\(await response\.arrayBuffer\(\)\)/);
  assert.match(viewer, /new IntersectionObserver/);
  assert.match(viewer, /new ResizeObserver/);
  assert.match(viewer, /PDF 第 \$\{pageNumber\} 頁，共 \$\{this\.pdfDocument\.numPages\} 頁/);
  assert.match(viewer, /page\.renderTask\?\.cancel\(\)/);
  assert.match(viewer, /await pdfDocument\.destroy\(\)/);
});

test("public, admin, and song surfaces share the viewer and contain no native PDF iframe", async () => {
  const files = await Promise.all([
    "index.html", "admin.html", "song.html", "assets/app.js", "assets/admin.js", "assets/song.js"
  ].map((path) => readFile(new URL(`../${path}`, import.meta.url), "utf8")));
  const [index, adminHtml, songHtml, app, admin, song] = files;
  for (const html of [index, adminHtml, songHtml]) {
    assert.doesNotMatch(html, /<iframe[^>]+(?:pdf|Pdf)/i);
    assert.match(html, /class="pdf-viewer"/);
  }
  for (const source of [app, admin, song]) {
    assert.match(source, /import \{ PdfViewer \} from "\.\/pdf-viewer\.js"/);
    assert.match(source, /new PdfViewer\(/);
  }
});
