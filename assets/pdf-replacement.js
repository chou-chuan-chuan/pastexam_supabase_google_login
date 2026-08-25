export class PdfReplacementError extends Error {
  constructor(message, { cause, rollbackWarning } = {}) {
    super(message, { cause });
    this.name = "PdfReplacementError";
    this.rollbackWarning = rollbackWarning || null;
  }
}

export function validateReplacementPdf(file, maxFileSizeBytes) {
  if (!file || file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
    throw new PdfReplacementError("請選擇 PDF 檔案。");
  }
  if (file.size > maxFileSizeBytes) {
    const megabytes = maxFileSizeBytes / (1024 * 1024);
    const label = Number.isInteger(megabytes) ? megabytes : megabytes.toFixed(1);
    throw new PdfReplacementError(`PDF 不可超過 ${label} MB。`);
  }
}

function safeFilename(name) {
  return name.normalize("NFKD").replace(/[^\w.\-]+/g, "_").replace(/_+/g, "_") || "lyrics.pdf";
}

export function replacementObjectPath(userId, filename, randomUUID = () => crypto.randomUUID()) {
  return `${userId}/${randomUUID()}-${safeFilename(filename)}`;
}

export async function updateSongWithOptionalPdf({
  supabase,
  bucket,
  song,
  values,
  file = null,
  currentUserId,
  maxFileSizeBytes,
  requirePendingOwner = false,
  randomUUID
}) {
  if (!song?.id || !currentUserId) {
    throw new PdfReplacementError("無法確認歌曲或登入身分。");
  }
  if (requirePendingOwner && (song.uploader_id !== currentUserId || song.status !== "pending")) {
    throw new PdfReplacementError("你目前沒有權限編輯這筆歌曲。");
  }

  let newPath = null;
  if (file) {
    validateReplacementPdf(file, maxFileSizeBytes);
    newPath = replacementObjectPath(currentUserId, file.name, randomUUID);
    const { error: uploadError } = await supabase.storage
      .from(bucket)
      .upload(newPath, file, { contentType: "application/pdf", upsert: false });
    if (uploadError) {
      throw new PdfReplacementError(uploadError.message || "PDF 上傳失敗。", { cause: uploadError });
    }
  }

  const updateValues = newPath
    ? { ...values, pdf_path: newPath, original_filename: file.name }
    : { ...values };
  let query = supabase.from("songs").update(updateValues).eq("id", song.id);
  if (requirePendingOwner) {
    query = query.eq("uploader_id", currentUserId).eq("status", "pending");
  }
  const { error: updateError } = await query.select("id").single();
  if (updateError) {
    let rollbackWarning = null;
    if (newPath) {
      const { error: rollbackError } = await supabase.storage.from(bucket).remove([newPath]);
      rollbackWarning = rollbackError || null;
    }
    throw new PdfReplacementError(updateError.message || "歌曲資料更新失敗。", {
      cause: updateError,
      rollbackWarning
    });
  }

  let cleanupWarning = null;
  if (newPath) {
    const { error: cleanupError } = await supabase.storage.from(bucket).remove([song.pdf_path]);
    cleanupWarning = cleanupError || null;
  }

  return {
    replaced: Boolean(newPath),
    pdfPath: newPath || song.pdf_path,
    originalFilename: newPath ? file.name : song.original_filename,
    cleanupWarning
  };
}
