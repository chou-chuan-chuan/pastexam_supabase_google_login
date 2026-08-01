export function findActiveCue(cues, currentTimeMs) {
  if (!Array.isArray(cues) || !cues.length || !Number.isFinite(currentTimeMs)) return null;
  let low = 0;
  let high = cues.length - 1;
  let match = -1;

  while (low <= high) {
    const middle = Math.floor((low + high) / 2);
    if (cues[middle].start_ms <= currentTimeMs) {
      match = middle;
      low = middle + 1;
    } else {
      high = middle - 1;
    }
  }

  if (match < 0) return null;
  const cue = cues[match];
  if (cue.end_ms != null && currentTimeMs >= cue.end_ms) return null;
  return cue;
}

export function prepareCuesForSave(rows) {
  if (!Array.isArray(rows)) return [];
  const normalized = rows
    .map((row, sequence) => ({
      start_ms: Math.round(Number(row.start_ms)),
      text: String(row.text ?? "").trim(),
      sequence
    }))
    .filter((row) => row.text && Number.isFinite(row.start_ms) && row.start_ms >= 0)
    .sort((a, b) => a.start_ms - b.start_ms || a.sequence - b.sequence);

  const nextGreaterStart = new Array(normalized.length).fill(null);
  for (let index = normalized.length - 2; index >= 0; index -= 1) {
    nextGreaterStart[index] = normalized[index + 1].start_ms > normalized[index].start_ms
      ? normalized[index + 1].start_ms
      : nextGreaterStart[index + 1];
  }

  return normalized.map((row, index) => {
    return {
      line_index: index,
      start_ms: row.start_ms,
      end_ms: nextGreaterStart[index],
      text: row.text
    };
  });
}

export function validateCueRows(rows) {
  const errors = [];
  const warnings = [];
  if (!Array.isArray(rows) || !rows.length) return { errors: ["至少需要一行歌詞。"], warnings };

  let previous = -1;
  rows.forEach((row, index) => {
    const label = `第 ${index + 1} 行`;
    if (!String(row.text ?? "").trim()) errors.push(`${label}沒有文字。`);
    const start = Number(row.start_ms);
    if (!Number.isFinite(start) || start < 0) errors.push(`${label}的時間必須大於或等於 0。`);
    if (Number.isFinite(start)) {
      if (start < previous) warnings.push(`${label}的時間早於上一行，儲存時會重新排序。`);
      if (start === previous) warnings.push(`${label}與上一行時間相同，將以目前順序穩定排序。`);
      previous = start;
    }
  });
  return { errors, warnings };
}

export function formatCueTime(milliseconds) {
  const value = Math.max(0, Math.round(Number(milliseconds) || 0));
  const minutes = Math.floor(value / 60_000);
  const seconds = Math.floor((value % 60_000) / 1_000);
  const millis = value % 1_000;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}
