#!/usr/bin/env python3
"""Verify Version 1.012 special kana/Han overrides and mixed alignment."""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from kana_sources.full_data import KANA_STROKES


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
HANDWRITTEN = {0x61D0: "uni61D0.qfwUser", 0x5915: "uni5915.qfwUser"}
ALIGNMENT = {0x6C17: ".qfwJaAlign", 0x4ED8: ".qfwJaAlign"}


def bounds(font: TTFont, name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    return pen.bounds


def drawing(font: TTFont, name: str):
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    return pen.value


def center_y(font: TTFont, name: str) -> float:
    b = bounds(font, name)
    return (b[1] + b[3]) / 2


def height(font: TTFont, name: str) -> float:
    b = bounds(font, name)
    return b[3] - b[1]


def verify() -> list[str]:
    errors: list[str] = []
    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for path in (SOURCE_PATH, TTF_PATH, WOFF2_PATH):
        require(path.is_file(), f"Missing {path}")
    if errors:
        return errors

    source = TTFont(SOURCE_PATH, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        source_cmap = source.getBestCmap()
        cmap = ttf.getBestCmap()
        wcmap = woff2.getBestCmap()
        require(cmap == wcmap, "TTF/WOFF2 cmap mismatch")

        for cp, expected in HANDWRITTEN.items():
            require(cmap.get(cp) == expected, f"U+{cp:04X} does not map to {expected}: {cmap.get(cp)}")
            require(expected in ttf.getGlyphOrder(), f"Missing handwritten glyph {expected}")
            require(bounds(ttf, expected) == bounds(woff2, expected), f"WOFF2 bounds differ for {expected}")
            require(ttf["hmtx"].metrics[expected] == woff2["hmtx"].metrics[expected], f"WOFF2 metrics differ for {expected}")
            original = source_cmap.get(cp)
            require(original is not None, f"Source lacks U+{cp:04X}")
            if original:
                require(drawing(source, original) == drawing(ttf, original), f"Original source glyph {original} changed")

        for cp, suffix in ALIGNMENT.items():
            name = cmap.get(cp, "")
            require(name.endswith(suffix), f"U+{cp:04X} alignment mapping missing: {name}")
            source_name = source_cmap.get(cp)
            require(source_name is not None, f"Source lacks alignment U+{cp:04X}")
            if source_name:
                require(drawing(source, source_name) == drawing(ttf, source_name), f"Original source glyph {source_name} changed")

        ke = cmap.get(ord("け"))
        ki = cmap.get(ord("気"))
        tsuke = cmap.get(ord("付"))
        if ke and ki and tsuke:
            centers = [center_y(ttf, name) for name in (ki, tsuke, ke)]
            heights = [height(ttf, name) for name in (ki, tsuke, ke)]
            require(max(centers) - min(centers) <= 32, f"気付け optical centers still diverge: {centers}")
            require(max(heights) - min(heights) <= 90, f"気付け ink heights still diverge: {heights}")

        su = KANA_STROKES["す"]
        require(len(su) >= 4 and len(su[2].points) >= 10, "す central loop source is not explicit enough")
        loop_x = [p[0] for p in su[2].points]
        loop_y = [p[1] for p in su[2].points]
        require(max(loop_x) - min(loop_x) >= 150 and max(loop_y) - min(loop_y) >= 170,
                f"す central loop is too small: x={min(loop_x)}..{max(loop_x)}, y={min(loop_y)}..{max(loop_y)}")

        ri = KANA_STROKES["り"]
        tail = ri[-1].points
        require(tail[0][1] >= 800 and tail[-1][1] <= 150,
                f"り tail is not long enough: {tail[0]} -> {tail[-1]}")
        require(tail[-1][0] <= tail[0][0] - 100,
                f"り tail needs a clearer lower-left finish: {tail[0]} -> {tail[-1]}")
    finally:
        source.close(); ttf.close(); woff2.close()
    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"Special Japanese verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("PASS: す has an explicit enlarged central counter")
    print("PASS: り has a longer, clearer tail")
    print("PASS: 懐 and 夕 use maintainer-handwriting derived glyphs")
    print("PASS: 気 and 付 retain original source drawings under optical alignment copies")
    print("PASS: 気付け optical centers/heights are aligned within the review gate")
    print("PASS: TTF/WOFF2 special override mappings, bounds, and metrics agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
