import test from "node:test";
import assert from "node:assert/strict";

import {
  findActiveCue,
  prepareCuesForSave,
  validateCueRows
} from "../assets/lyrics-sync.js";

const cues = [
  { line_index: 0, start_ms: 1_000, end_ms: 2_000, text: "A" },
  { line_index: 1, start_ms: 2_000, end_ms: 4_000, text: "B" },
  { line_index: 2, start_ms: 4_000, end_ms: null, text: "C" }
];

test("finds active cues at boundaries, between lines, and after the last line", () => {
  assert.equal(findActiveCue(cues, 999), null);
  assert.equal(findActiveCue(cues, 1_000)?.text, "A");
  assert.equal(findActiveCue(cues, 2_500)?.text, "B");
  assert.equal(findActiveCue(cues, 20_000)?.text, "C");
});

test("handles empty cues, duplicate timestamps, offset, and seek recalculation", () => {
  assert.equal(findActiveCue([], 2_000), null);
  const duplicates = [
    { start_ms: 1_000, end_ms: null, text: "first" },
    { start_ms: 1_000, end_ms: null, text: "second" }
  ];
  assert.equal(findActiveCue(duplicates, 1_000)?.text, "second");
  assert.equal(findActiveCue(cues, 500, 500)?.text, "A");
  assert.equal(findActiveCue(cues, 3_900)?.text, "B");
  assert.equal(findActiveCue(cues, 4_000)?.text, "C");
});

test("prepares stable, sorted cue payloads and derives end times", () => {
  assert.deepEqual(prepareCuesForSave([
    { start_ms: 2_000, text: "C" },
    { start_ms: 1_000, text: "A" },
    { start_ms: 1_000, text: "B" }
  ]), [
    { line_index: 0, start_ms: 1_000, end_ms: 2_000, text: "A" },
    { line_index: 1, start_ms: 1_000, end_ms: 2_000, text: "B" },
    { line_index: 2, start_ms: 2_000, end_ms: null, text: "C" }
  ]);
});

test("validates missing text, negative time, reverse order, and duplicates", () => {
  const result = validateCueRows([
    { start_ms: 2_000, text: "A" },
    { start_ms: 2_000, text: "B" },
    { start_ms: -1, text: "" }
  ]);
  assert.equal(result.errors.length, 2);
  assert.equal(result.warnings.length, 2);
});
