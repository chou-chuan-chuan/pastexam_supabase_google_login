import test from "node:test";
import assert from "node:assert/strict";

import { parseLrc } from "../assets/lrc.js";

test("parses second, centisecond, and millisecond timestamps", () => {
  const result = parseLrc("[01:23]A\n[01:23.45]B\n[01:23.456]C");
  assert.deepEqual(result.cues.map((cue) => cue.start_ms), [83_000, 83_450, 83_456]);
  assert.equal(result.errors.length, 0);
});

test("expands multiple timestamps and sorts stably", () => {
  const result = parseLrc("[00:10.000]Later\n[00:02][00:05.50]Repeat");
  assert.deepEqual(result.cues.map((cue) => [cue.start_ms, cue.text]), [
    [2_000, "Repeat"],
    [5_500, "Repeat"],
    [10_000, "Later"]
  ]);
});

test("reads metadata and applies offset", () => {
  const result = parseLrc("[ar:Artist]\n[ti:Title]\n[al:Album]\n[offset:500]\n[00:01]Line");
  assert.deepEqual(result.metadata, { ar: "Artist", ti: "Title", al: "Album" });
  assert.equal(result.offsetMs, 500);
  assert.equal(result.cues[0].start_ms, 1_500);
});

test("treats offset as global even when metadata follows a cue", () => {
  const result = parseLrc("[00:01]Line\n[offset:250]");
  assert.equal(result.offsetMs, 250);
  assert.equal(result.cues[0].start_ms, 1_250);
});

test("reports invalid lines, negative adjusted time, and empty input without throwing", () => {
  const result = parseLrc("[offset:-2000]\n[00:01]Too early\n[01:99]Bad\nplain lyric\n[00:03]");
  assert.equal(result.cues.length, 0);
  assert.equal(result.errors.length, 4);
  assert.deepEqual(parseLrc(" ").errors, ["LRC 內容是空的。"]);
});
