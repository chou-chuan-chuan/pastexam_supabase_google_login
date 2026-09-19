// Optional real-browser QA: node tests/upload-reference.browser.mjs
// Requires Playwright; PLAYWRIGHT_MODULE may point to an existing installation.
// All backend calls are mocked, and non-local network requests are blocked.
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile, mkdir, mkdtemp } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE || "playwright");
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = process.env.QA_OUTPUT_DIR || await mkdtemp(join(tmpdir(), "upload-reference-qa-"));
await mkdir(output, { recursive: true });
const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".woff2": "font/woff2", ".ttf": "font/ttf", ".png": "image/png" };
const server = createServer(async (req, res) => {
  const path = resolve(root, `.${new URL(req.url, "http://localhost").pathname === "/" ? "/index.html" : decodeURIComponent(new URL(req.url, "http://localhost").pathname)}`);
  if (!path.startsWith(root + sep)) { res.writeHead(403); res.end(); return; }
  try { res.writeHead(200, { "Content-Type": mime[extname(path)] || "application/octet-stream" }); res.end(await readFile(path)); }
  catch { res.writeHead(404); res.end(); }
});
await new Promise((done) => server.listen(0, "127.0.0.1", done));
const origin = `http://127.0.0.1:${server.address().port}`;

const tags = [{ id: "live", name: "現場", slug: "live" }, { id: "movie", name: "電影", slug: "movie" }, { id: "other", name: "其他", slug: "other" }];
const base = {
  id: "approved-private-id", status: "approved", title: "Lemon", artist: "米津玄師", album: "STRAY SHEEP", release_year: 2018,
  language: "日本語", genre: "Pop", youtube_video_id: "SX_ViT4Ra7k", notes: "private-notes",
  uploader_id: "private-uploader", uploader_display_name: "private-name", pdf_path: "private-path", original_filename: "private-filename.pdf",
  song_tags: [{ tags: tags[0] }, { tags: tags[1] }, { tags: { id: "deleted", name: "private-deleted-tag" } }]
};
const songs = [base, { ...base, id: "approved-two", title: "Flamingo", album: "Flamingo / TEENAGE RIOT", youtube_video_id: "Uh6dkL1M9DM" },
  { ...base, id: "long", title: "Wrap — 一首很長的歌曲名稱，確認在手機上也可以自然換行閱讀", artist: "A very long artist name for wrapping", album: "A".repeat(90) },
  ...Array.from({ length: 8 }, (_, i) => ({ ...base, id: `approved-${i}`, title: `Other ${i}`, language: "English", genre: "Rock" })),
  { ...base, id: "pending-private", status: "pending", title: "Secret pending", artist: "Secret artist", uploader_id: "another-user" },
  { ...base, id: "rejected-private", status: "rejected", title: "Secret rejected", artist: "Secret rejected artist" }];

const mockModule = `export function createClient() {
  const qa = window.__uploadQA;
  return {
    auth: { onAuthStateChange() {}, getSession: async () => ({ data: { session: { user: { id: "qa-uploader", email: "qa@example.test" } } } }) },
    rpc: async (name, args) => {
      if (name === "is_admin") return { data: false, error: null };
      if (name === "set_song_tags") { qa.tagWrites.push(args); return { error: null }; }
      throw new Error("Unexpected RPC: " + name);
    },
    storage: { from: () => ({ upload: async (path, file, options) => { qa.uploads.push({ path, name: file.name, options }); return { error: null }; } }) },
    from(table) {
      return {
        select() { return this; }, order() { return this; },
        insert(payload) { qa.inserts.push(payload); this.inserted = { id: "fresh-" + qa.inserts.length }; qa.songs.push({ ...payload, ...this.inserted, song_tags: [] }); return this; },
        single() { return Promise.resolve({ data: this.inserted, error: null }); },
        then(ok, fail) {
          const data = table === "songs" ? qa.songs : table === "tags" ? qa.tags : [];
          return Promise.resolve({ data, error: qa.failLoad ? { message: "Fixture load failure" } : null }).then(ok, fail);
        }
      };
    }
  };
}`;

const browser = await chromium.launch({ headless: true, args: [`--log-file=${join(output, "chromium.log")}`] });
const errors = [];
async function newPage(width, height, fixtureSongs = songs) {
  const context = await browser.newContext({ viewport: { width, height }, hasTouch: width === 390 });
  await context.addInitScript((fixture) => {
    window.__uploadQA = { ...fixture, inserts: [], uploads: [], tagWrites: [], failLoad: false };
  }, { songs: fixtureSongs, tags });
  await context.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin === origin && url.pathname === "/config.js") {
      await route.fulfill({ contentType: "text/javascript", body: 'export const SUPABASE_URL="https://fixture.invalid", SUPABASE_PUBLISHABLE_KEY="fixture-key", STORAGE_BUCKET="fixture", MAX_FILE_SIZE_BYTES=52428800;' });
    } else if (url.hostname === "cdn.jsdelivr.net" && url.pathname.includes("@supabase/supabase-js")) {
      await route.fulfill({ contentType: "text/javascript", body: mockModule });
    } else if (url.origin === origin) await route.continue();
    else if (url.hostname === "i.ytimg.com") await route.fulfill({ contentType: "image/png", body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZ9kAAAAASUVORK5CYII=", "base64") });
    else await route.abort();
  });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  page.setDefaultTimeout(10000);
  await page.goto(origin);
  await page.locator("#songGrid article").first().waitFor({ state: fixtureSongs.length ? "visible" : "hidden" });
  await page.locator("#openUploadButton").click();
  return page;
}
async function formValues(page) {
  return page.locator("#uploadForm").evaluate((form) => ({
    values: Object.fromEntries([...form.querySelectorAll("input:not([type=checkbox]), textarea")].filter((input) => input.id !== "uploadReferenceInput").map((input) => [input.id, input.value])),
    tags: [...form.querySelectorAll('#uploadTagChoices input:checked')].map((input) => input.value)
  }));
}
async function assertFits(page) {
  const measurements = await page.evaluate(() => {
    const form = document.querySelector("#uploadForm");
    const box = document.querySelector("#uploadReferenceOptions").getBoundingClientRect();
    const dialog = document.querySelector("#uploadDialog").getBoundingClientRect();
    return { page: document.documentElement.scrollWidth <= innerWidth, form: form.scrollWidth <= form.clientWidth,
      list: box.left >= dialog.left && box.right <= dialog.right };
  });
  assert.deepEqual(measurements, { page: true, form: true, list: true });
}

try {
  const page = await newPage(1440, 1080);
  const input = page.locator("#uploadReferenceInput");
  await input.fill("lem");
  assert.deepEqual(await page.locator('[role="option"] .song-reference-title').allTextContents(), ["Lemon"]);
  const referenceMarkup = await page.locator("#uploadReference").innerHTML()
    + await page.locator("#uploadForm datalist option").evaluateAll((options) => options.map((option) => option.value).join(" "));
  assert.doesNotMatch(referenceMarkup, /private-|Secret|uploader|pdf_path|original_filename/);
  await input.press("ArrowDown");
  const active = await input.getAttribute("aria-activedescendant");
  assert.equal(await page.locator(`#${active}`).getAttribute("aria-selected"), "true");
  await input.press("Escape");
  assert.equal(await input.getAttribute("aria-expanded"), "false");
  assert.equal(await page.locator("#uploadDialog").evaluate((dialog) => dialog.open), true);
  await input.press("ArrowUp");
  await assertFits(page);
  await page.screenshot({ path: join(output, "desktop-picker.png") });
  await input.press("Enter");
  const expected = { uploadTitle: "Lemon", uploadArtist: "米津玄師", uploadAlbum: "STRAY SHEEP", uploadYear: "2018", uploadLanguage: "日本語", uploadGenre: "Pop", uploadYoutube: "https://www.youtube.com/watch?v=SX_ViT4Ra7k" };
  for (const [id, value] of Object.entries(expected)) assert.equal(await page.locator(`#${id}`).inputValue(), value);
  assert.deepEqual((await formValues(page)).tags, ["live", "movie"]);
  assert.equal(await page.locator("#uploadNotes").inputValue(), "");
  assert.equal(await page.locator("#uploadPdf").evaluate((input) => input.files.length), 0);
  assert.equal(await page.locator("#uploadYoutubePreview").isVisible(), true);
  assert.match(await page.locator("#uploadYoutubeThumbnail").getAttribute("src"), /SX_ViT4Ra7k/);
  assert.equal(await page.locator("#uploadYoutubeStatus").getAttribute("class"), "field-success");
  await page.locator("#submitUploadButton").click();
  assert.equal(await page.evaluate(() => window.__uploadQA.inserts.length), 0);

  await page.locator("#uploadNotes").fill("My independent notes");
  await page.locator("#uploadPdf").setInputFiles({ name: "new-lyrics.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4\n%%EOF") });
  await page.locator("#uploadTitle").fill("My edited Lemon");
  const before = await formValues(page);
  await input.fill("Flamingo");
  let confirmations = 0;
  page.once("dialog", async (dialog) => { confirmations++; assert.match(dialog.message(), /目前已輸入的歌曲資料會被取代/); await dialog.dismiss(); });
  await page.locator('#uploadReferenceOptions [role="option"]').click();
  assert.deepEqual(await formValues(page), before);
  page.once("dialog", async (dialog) => { confirmations++; await dialog.accept(); });
  await page.locator('#uploadReferenceOptions [role="option"]').click();
  assert.equal(confirmations, 2);
  assert.equal(await page.locator("#uploadTitle").inputValue(), "Flamingo");
  assert.equal(await page.locator("#uploadNotes").inputValue(), "My independent notes");
  assert.equal(await page.locator("#uploadPdf").evaluate((input) => input.files[0].name), "new-lyrics.pdf");
  assert.match(await page.locator("#uploadYoutubeThumbnail").getAttribute("src"), /Uh6dkL1M9DM/);
  await page.locator('#uploadTagChoices input[value="live"]').uncheck();
  await page.locator('#uploadTagChoices input[value="other"]').check();
  const copied = await formValues(page);
  await page.locator("#clearUploadReference").click();
  assert.deepEqual(await formValues(page), copied);
  await input.fill("Secret");
  assert.equal(await page.locator('#uploadReferenceOptions [role="option"]').count(), 0);
  await input.press("Enter");
  assert.equal(await page.evaluate(() => window.__uploadQA.inserts.length), 0);
  await input.fill("");
  assert.equal(await page.locator('#uploadReferenceOptions [role="option"]').count(), 8);
  await input.press("Tab");
  assert.equal(await input.getAttribute("aria-expanded"), "false");
  await page.locator('#uploadDialog [data-close="uploadDialog"]').first().click();
  await page.locator("#openUploadButton").click();
  assert.deepEqual(await formValues(page), copied);
  await page.locator("#submitUploadButton").click();
  await page.locator("#uploadDialog").waitFor({ state: "hidden" });
  const submitted = await page.evaluate(() => ({ inserts: window.__uploadQA.inserts, uploads: window.__uploadQA.uploads, tags: window.__uploadQA.tagWrites }));
  assert.equal(submitted.inserts.length, 1);
  assert.equal(submitted.inserts[0].status, "pending");
  assert.equal(submitted.inserts[0].uploader_id, "qa-uploader");
  assert.match(submitted.inserts[0].pdf_path, /^qa-uploader\/[\da-f-]+-new-lyrics.pdf$/);
  assert.equal(submitted.inserts[0].pdf_path, submitted.uploads[0].path);
  assert.equal(submitted.inserts[0].notes, "My independent notes");
  assert.equal(submitted.inserts[0].title, "Flamingo"); // Existing title/artist did not block a fresh row.
  assert.equal("id" in submitted.inserts[0], false);
  assert.doesNotMatch(JSON.stringify(submitted.inserts), /private-|approved_song_id|source_song_id|parent_song_id|lifecycle_id/);
  assert.deepEqual(submitted.tags[0], { p_song_id: "fresh-1", p_tag_ids: ["movie", "other"] });
  await page.locator("#openUploadButton").click();
  assert.equal(await input.inputValue(), "");
  assert.equal(await page.locator("#uploadTitle").inputValue(), "");
  assert.deepEqual((await formValues(page)).tags, []);
  await page.locator('#uploadDialog [data-close="uploadDialog"]').first().click();

  await page.evaluate(() => {
    window.__uploadQA.songs.find((song) => song.title === "Lemon").status = "rejected";
    window.__uploadQA.songs.find((song) => song.title === "Secret pending").status = "approved";
  });
  await page.locator("#refreshButton").click();
  await page.waitForFunction(() => [...document.querySelectorAll("#uploadTitleSuggestions option")].some((option) => option.value === "Secret pending"));
  await page.locator("#openUploadButton").click();
  await input.fill("Lemon");
  assert.equal(await page.locator('#uploadReferenceOptions [role="option"]').count(), 0);
  await input.fill("Secret pending");
  assert.equal(await page.locator('#uploadReferenceOptions [role="option"]').count(), 1);
  await page.locator("#uploadTitle").fill("Keep across refresh");
  await page.locator('#uploadDialog [data-close="uploadDialog"]').first().click();
  await page.evaluate(() => { window.__uploadQA.failLoad = true; });
  await page.locator("#refreshButton").click();
  await page.waitForFunction(() => document.querySelector("#uploadTitleSuggestions").children.length === 0);
  await page.locator("#openUploadButton").click();
  assert.match(await page.locator("#uploadReferenceStatus").textContent(), /目前尚無已通過歌曲可供參考/);
  assert.equal(await page.locator("#uploadTitle").inputValue(), "Keep across refresh");
  await page.context().close();
  console.log("PASS desktop: keyboard, privacy, copy/confirm/clear, PDF preservation, fresh pending submission, reload/failure lifecycle");

  for (const [name, width, height] of [["tablet", 768, 1024], ["mobile", 390, 844]]) {
    const responsive = await newPage(width, height);
    await responsive.locator("#uploadReferenceInput").fill("Wrap");
    await assertFits(responsive);
    await responsive.screenshot({ path: join(output, `${name}-picker.png`) });
    await responsive.locator("#uploadReferenceInput").fill("lemon");
    if (name === "mobile") await responsive.locator('#uploadReferenceOptions [role="option"]').tap();
    else await responsive.locator('#uploadReferenceOptions [role="option"]').click();
    assert.equal(await responsive.locator("#uploadTitle").inputValue(), "Lemon");
    assert.equal(await responsive.locator("#uploadNotes").inputValue(), "");
    assert.equal(await responsive.locator("#uploadPdf").evaluate((input) => input.files.length), 0);
    await responsive.screenshot({ path: join(output, `${name}-filled.png`) });
    await responsive.context().close();
    console.log(`PASS ${name} ${width}px: contextual wrapping, no horizontal overflow, pointer/touch selection`);
  }
  const empty = await newPage(390, 844, songs.filter((song) => song.status !== "approved"));
  assert.match(await empty.locator("#uploadReferenceStatus").textContent(), /目前尚無已通過歌曲可供參考/);
  assert.equal(await empty.locator("#submitUploadButton").isEnabled(), true);
  assert.equal(await empty.locator("#uploadForm datalist option").count(), 0);
  await empty.locator("#uploadReferenceInput").fill("Secret");
  assert.equal(await empty.locator('#uploadReferenceOptions [role="option"]').count(), 0);
  await empty.screenshot({ path: join(output, "mobile-empty.png") });
  await empty.locator("#uploadTitle").fill("My new song");
  await empty.locator("#uploadArtist").fill("My artist");
  await empty.locator("#uploadYoutube").fill("https://www.youtube.com/watch?v=SX_ViT4Ra7k");
  await empty.locator("#uploadPdf").setInputFiles({ name: "first.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4\n%%EOF") });
  await empty.locator("#submitUploadButton").click();
  await empty.locator("#uploadDialog").waitFor({ state: "hidden" });
  assert.equal(await empty.evaluate(() => window.__uploadQA.inserts[0].status), "pending");
  await empty.context().close();
  assert.deepEqual(errors, []);
  console.log("PASS zero approved: no private suggestions, manual upload creates a pending row");
  console.log(`Screenshots: ${output}`);
} finally {
  await browser.close();
  await new Promise((done) => server.close(done));
}
