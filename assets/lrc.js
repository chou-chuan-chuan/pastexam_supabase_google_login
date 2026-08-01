const TIMESTAMP_PATTERN = /\[(\d{1,3}):([0-5]\d)(?:[.:](\d{1,3}))?\]/g;
const METADATA_PATTERN = /^\[([a-zA-Z]+):([^\]]*)\]$/;

function fractionToMs(fraction = "") {
  if (!fraction) return 0;
  if (fraction.length === 1) return Number(fraction) * 100;
  if (fraction.length === 2) return Number(fraction) * 10;
  return Number(fraction.slice(0, 3));
}

function timestampToMs(minutes, seconds, fraction) {
  return Number(minutes) * 60_000 + Number(seconds) * 1_000 + fractionToMs(fraction);
}

export function parseLrc(source) {
  const metadata = {};
  const errors = [];
  const parsed = [];
  let offsetMs = 0;
  let sequence = 0;

  if (typeof source !== "string" || !source.trim()) {
    return { cues: [], metadata, offsetMs, errors: ["LRC 內容是空的。"] };
  }

  const lines = source.replace(/^\uFEFF/, "").split(/\r?\n/);

  // LRC offset is global, even when a producer places the metadata after cues.
  for (const [lineNumber, rawLine] of lines.entries()) {
    const match = rawLine.trim().match(METADATA_PATTERN);
    if (!match || match[1].toLowerCase() !== "offset") continue;
    const parsedOffset = Number(match[2].trim());
    if (Number.isInteger(parsedOffset)) offsetMs = parsedOffset;
    else errors.push(`第 ${lineNumber + 1} 行的 offset 不是整數。`);
  }

  lines.forEach((rawLine, lineNumber) => {
    const line = rawLine.trim();
    if (!line) return;

    const metadataMatch = line.match(METADATA_PATTERN);
    if (metadataMatch && !/^\[\d/.test(line)) {
      const key = metadataMatch[1].toLowerCase();
      const value = metadataMatch[2].trim();
      if (["ar", "ti", "al", "by"].includes(key)) {
        metadata[key] = value;
      }
      return;
    }

    const matches = [...line.matchAll(TIMESTAMP_PATTERN)];
    if (!matches.length) {
      errors.push(`第 ${lineNumber + 1} 行沒有有效時間標記。`);
      return;
    }

    const text = line.replace(TIMESTAMP_PATTERN, "").trim();
    if (!text) {
      errors.push(`第 ${lineNumber + 1} 行沒有歌詞文字。`);
      return;
    }

    for (const match of matches) {
      const startMs = timestampToMs(match[1], match[2], match[3]) + offsetMs;
      if (startMs < 0) {
        errors.push(`第 ${lineNumber + 1} 行套用 offset 後時間小於 0。`);
        continue;
      }
      parsed.push({ start_ms: startMs, text, sequence: sequence++ });
    }
  });

  parsed.sort((a, b) => a.start_ms - b.start_ms || a.sequence - b.sequence);

  const nextGreaterStart = new Array(parsed.length).fill(null);
  for (let index = parsed.length - 2; index >= 0; index -= 1) {
    nextGreaterStart[index] = parsed[index + 1].start_ms > parsed[index].start_ms
      ? parsed[index + 1].start_ms
      : nextGreaterStart[index + 1];
  }

  const cues = parsed.map((cue, index) => {
    return {
      line_index: index,
      start_ms: cue.start_ms,
      end_ms: nextGreaterStart[index],
      text: cue.text
    };
  });

  return { cues, metadata, offsetMs, errors };
}
