#!/usr/bin/env python3
"""Verify the source-preserving U+5BB9 容 optical transform."""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from japanese.user_japanese_overrides import OPTICAL_ALIGNMENT_SUFFIX, SHARED_HAN_OPTICAL_TRANSFORMS


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
CHARACTER = "容"
EXPECTED_TRANSFORM = (1.00, 1.00, 19.45, 35.0, 0.0)
EXPECTED_SOURCE_BOUNDS = (87.1, -110, 746, 750.13)
EXPECTED_TARGET_BOUNDS = (106.1, -75, 765, 785.1333333333333)
EXPECTED_ADVANCE = 872
EXPECTED_TARGET_LSB = 104
EXPECTED_TARGET_RSB = 107


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def drawing(font: TTFont, glyph_name: str) -> tuple:
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return tuple(pen.value)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    transform = SHARED_HAN_OPTICAL_TRANSFORMS.get(CHARACTER)
    require(transform is not None, "U+5BB9 is missing from the shared-Han optical transform map")
    if transform:
        actual = (transform.scale_x, transform.scale_y, transform.dx, transform.dy, transform.embolden)
        require(actual == EXPECTED_TRANSFORM, f"Unexpected U+5BB9 transform: {actual}")

    source = TTFont(SOURCE_PATH, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        source_name = source.getBestCmap()[ord(CHARACTER)]
        target_name = ttf.getBestCmap()[ord(CHARACTER)]
        require(target_name == f"{source_name}{OPTICAL_ALIGNMENT_SUFFIX}", "U+5BB9 does not map to its derived optical copy")
        require(source_name in ttf.getGlyphOrder(), "The original U+5BB9 source glyph was removed")
        require(drawing(source, source_name) == drawing(ttf, source_name), "The official U+5BB9 source drawing changed")
        source_bounds = bounds(source, source_name)
        target_bounds = bounds(ttf, target_name)
        require(all(abs(a - b) <= 0.05 for a, b in zip(source_bounds, EXPECTED_SOURCE_BOUNDS)), f"Unexpected source bounds: {source_bounds}")
        require(all(abs(a - b) <= 0.05 for a, b in zip(target_bounds, EXPECTED_TARGET_BOUNDS)), f"Unexpected derived bounds: {target_bounds}")
        require(bounds(woff2, target_name) == target_bounds, "TTF/WOFF2 U+5BB9 bounds differ")
        source_advance, source_lsb = source["hmtx"].metrics[source_name]
        target_advance, target_lsb = ttf["hmtx"].metrics[target_name]
        require(source_advance == target_advance == EXPECTED_ADVANCE, f"U+5BB9 advance changed: {source_advance} -> {target_advance}")
        require(target_lsb == EXPECTED_TARGET_LSB, f"Unexpected derived LSB: {target_lsb}")
        require(source_lsb == 85, f"Unexpected source LSB: {source_lsb}")
        target_glyph = ttf["glyf"][target_name]
        target_rsb = EXPECTED_ADVANCE - target_lsb - (target_glyph.xMax - target_glyph.xMin)
        require(target_rsb == EXPECTED_TARGET_RSB, f"Unexpected derived RSB: {target_rsb}")
        require(abs(target_lsb - target_rsb) <= 3, "Derived U+5BB9 side bearings are not optically balanced")
        require(ttf["hmtx"].metrics[target_name] == woff2["hmtx"].metrics[target_name], "TTF/WOFF2 U+5BB9 metrics differ")
        center_x = (target_bounds[0] + target_bounds[2]) / 2
        center_y = (target_bounds[1] + target_bounds[3]) / 2
        require(abs(center_x - EXPECTED_ADVANCE / 2) <= 0.5, f"U+5BB9 is not centered in its advance: {center_x}")
        require(abs(center_y - 355) <= 0.1, f"U+5BB9 optical bounds center is not approximately 355: {center_y}")
    finally:
        source.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("PASS: U+5BB9 keeps the official drawing and source advance")
    print("PASS: scale_x=1.00 scale_y=1.00 dx=19.45 dy=35.0; derived LSB/RSB=104/107")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
