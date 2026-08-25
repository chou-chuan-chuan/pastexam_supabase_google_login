import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  PdfReplacementError,
  updateSongWithOptionalPdf,
  validateReplacementPdf
} from "../assets/pdf-replacement.js";


const bucket = "lyrics-pdfs";
const maxFileSizeBytes = 50 * 1024 * 1024;
const song = {
  id: "song-1",
  uploader_id: "user-1",
  status: "pending",
  pdf_path: "user-1/old.pdf",
  original_filename: "old.pdf"
};

function pdf(name = "new.pdf", size = 1024) {
  return { name, size, type: "application/pdf" };
}

function mockSupabase({ uploadError = null, updateError = null, removeErrors = [] } = {}) {
  const calls = { uploads: [], updates: [], filters: [], removals: [] };
  const query = {
    eq(column, value) { calls.filters.push([column, value]); return this; },
    select() { return this; },
    async single() { return { data: updateError ? null : { id: song.id }, error: updateError }; }
  };
  const client = {
    storage: {
      from(name) {
        assert.equal(name, bucket);
        return {
          async upload(path, file, options) {
            calls.uploads.push({ path, file, options });
            return { error: uploadError };
          },
          async remove(paths) {
            calls.removals.push(paths);
            return { error: removeErrors.shift() || null };
          }
        };
      }
    },
    from(table) {
      assert.equal(table, "songs");
      return {
        update(values) { calls.updates.push(values); return query; }
      };
    }
  };
  return { client, calls };
}

test("metadata-only edit keeps the existing PDF path and original filename", async () => {
  const { client, calls } = mockSupabase();
  const result = await updateSongWithOptionalPdf({
    supabase: client, bucket, song, values: { title: "Edited" }, currentUserId: "user-1",
    maxFileSizeBytes, requirePendingOwner: true
  });
  assert.deepEqual(calls.uploads, []);
  assert.deepEqual(calls.removals, []);
  assert.deepEqual(calls.updates, [{ title: "Edited" }]);
  assert.equal(result.pdfPath, song.pdf_path);
  assert.equal(result.originalFilename, song.original_filename);
});

test("replacement uploads a unique object, updates the row, then removes the old object", async () => {
  const { client, calls } = mockSupabase();
  const file = pdf("replacement.pdf");
  const result = await updateSongWithOptionalPdf({
    supabase: client, bucket, song, values: { title: "Edited" }, file, currentUserId: "user-1",
    maxFileSizeBytes, requirePendingOwner: true, randomUUID: () => "uuid-1"
  });
  assert.equal(calls.uploads[0].path, "user-1/uuid-1-replacement.pdf");
  assert.deepEqual(calls.updates[0], {
    title: "Edited",
    pdf_path: "user-1/uuid-1-replacement.pdf",
    original_filename: "replacement.pdf"
  });
  assert.deepEqual(calls.removals, [[song.pdf_path]]);
  assert.deepEqual(calls.filters, [["id", song.id], ["uploader_id", "user-1"], ["status", "pending"]]);
  assert.equal(result.replaced, true);
  assert.equal(result.originalFilename, "replacement.pdf");
});

test("upload failure does not update the database or remove the old PDF", async () => {
  const { client, calls } = mockSupabase({ uploadError: new Error("upload failed") });
  await assert.rejects(() => updateSongWithOptionalPdf({
    supabase: client, bucket, song, values: { title: "Edited" }, file: pdf(), currentUserId: "user-1",
    maxFileSizeBytes, requirePendingOwner: true, randomUUID: () => "uuid-2"
  }), /upload failed/);
  assert.deepEqual(calls.updates, []);
  assert.deepEqual(calls.removals, []);
});

test("database failure rolls back the new object and retains the old PDF", async () => {
  const { client, calls } = mockSupabase({ updateError: new Error("update failed") });
  await assert.rejects(() => updateSongWithOptionalPdf({
    supabase: client, bucket, song, values: { title: "Edited" }, file: pdf(), currentUserId: "user-1",
    maxFileSizeBytes, requirePendingOwner: true, randomUUID: () => "uuid-3"
  }), /update failed/);
  assert.deepEqual(calls.removals, [["user-1/uuid-3-new.pdf"]]);
  assert.ok(!calls.removals.flat().includes(song.pdf_path));
});

test("non-PDF and oversized files are blocked before any request", () => {
  assert.throws(() => validateReplacementPdf({ name: "lyrics.txt", type: "text/plain", size: 10 }, maxFileSizeBytes), PdfReplacementError);
  assert.throws(() => validateReplacementPdf(pdf("large.pdf", maxFileSizeBytes + 1), maxFileSizeBytes), /不可超過 50 MB/);
});

test("owner replacement cannot bypass the existing pending-owner permission", async () => {
  const { client, calls } = mockSupabase();
  await assert.rejects(() => updateSongWithOptionalPdf({
    supabase: client, bucket, song: { ...song, status: "approved" }, values: {}, file: pdf(), currentUserId: "user-1",
    maxFileSizeBytes, requirePendingOwner: true
  }), /沒有權限/);
  assert.deepEqual(calls.uploads, []);
  assert.deepEqual(calls.updates, []);
});

test("cleanup failure keeps the successful replacement and returns a warning", async () => {
  const cleanupError = new Error("cleanup failed");
  const { client, calls } = mockSupabase({ removeErrors: [cleanupError] });
  const result = await updateSongWithOptionalPdf({
    supabase: client, bucket, song, values: {}, file: pdf(), currentUserId: "user-1",
    maxFileSizeBytes, requirePendingOwner: true, randomUUID: () => "uuid-4"
  });
  assert.equal(result.cleanupWarning, cleanupError);
  assert.deepEqual(calls.removals, [[song.pdf_path]]);
});

test("preview and download flows use the current row path and filename", async () => {
  const [app, admin, detail] = await Promise.all([
    readFile(new URL("../assets/app.js", import.meta.url), "utf8"),
    readFile(new URL("../assets/admin.js", import.meta.url), "utf8"),
    readFile(new URL("../assets/song.js", import.meta.url), "utf8")
  ]);
  assert.match(app, /signedPdfUrl\(song\.pdf_path, song\.original_filename\)/);
  assert.match(admin, /createSignedUrl\(song\.pdf_path, 300, options\)/);
  assert.match(detail, /createSignedUrl\(song\.pdf_path, 600, options\)/);
  assert.match(detail, /download \? \{ download: song\.original_filename \}/);
});
