#!/usr/bin/env python3
"""Verify the source-preserving U+5965 奥 optical transform."""

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
CHARACTER = "奥"
EXPECTED_TRANSFORM = (0.895, 0.895, 10.5, 34.0, 8.0, 790)
EXPECTED_SOURCE_BOUNDS = (91.0, -153.0, 678.0, 793.0)
EXPECTED_REFERENCE_BOUNDS = (122.0, -53.0, 668.0, 761.0)
EXPECTED_TARGET_BOUNDS = (127.8, -73.0, 662.0, 781.692)
EXPECTED_ADVANCE = 790
EXPECTED_SOURCE_METRICS = (798, 91, 120)
EXPECTED_REFERENCE_METRICS = (790, 122, 122)
EXPECTED_TARGET_LSB = 127
EXPECTED_TARGET_RSB = 128
REFERENCE_CENTER = (395.0, 354.0)


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def drawing(font: TTFont, glyph_name: str) -> tuple:
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return tuple(pen.value)


def side_bearings(font: TTFont, glyph_name: str) -> tuple[int, int, int]:
    advance, lsb = font["hmtx"].metrics[glyph_name]
    glyph = font["glyf"][glyph_name]
    rsb = advance - lsb - (glyph.xMax - glyph.xMin)
    return advance, lsb, rsb


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    transform = SHARED_HAN_OPTICAL_TRANSFORMS.get(CHARACTER)
    require(transform is not None, "U+5965 is missing from the shared-Han optical transform map")
    if transform:
        actual = (transform.scale_x, transform.scale_y, transform.dx, transform.dy, transform.embolden, transform.advance)
        require(actual == EXPECTED_TRANSFORM, f"Unexpected U+5965 transform: {actual}")
        require(transform.scale_x == transform.scale_y, "U+5965 optical scale must remain uniform")

    source = TTFont(SOURCE_PATH, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        source_name = source.getBestCmap()[ord(CHARACTER)]
        target_name = ttf.getBestCmap()[ord(CHARACTER)]
        reference_name = ttf.getBestCmap()[ord("奧")]
        require(target_name == f"{source_name}{OPTICAL_ALIGNMENT_SUFFIX}", "U+5965 does not map to its derived optical copy")
        require(source_name in ttf.getGlyphOrder(), "The original U+5965 source glyph was removed")
        require(drawing(source, source_name) == drawing(ttf, source_name), "The official U+5965 source drawing changed")
        source_bounds = bounds(source, source_name)
        target_bounds = bounds(ttf, target_name)
        reference_bounds = bounds(ttf, reference_name)
        require(all(abs(a - b) <= 0.05 for a, b in zip(source_bounds, EXPECTED_SOURCE_BOUNDS)), f"Unexpected source bounds: {source_bounds}")
        require(all(abs(a - b) <= 0.05 for a, b in zip(target_bounds, EXPECTED_TARGET_BOUNDS)), f"Unexpected derived bounds: {target_bounds}")
        require(all(abs(a - b) <= 0.05 for a, b in zip(reference_bounds, EXPECTED_REFERENCE_BOUNDS)), f"Unexpected U+5967 reference bounds: {reference_bounds}")
        require(bounds(woff2, target_name) == target_bounds, "TTF/WOFF2 U+5965 bounds differ")
        require(side_bearings(source, source_name) == EXPECTED_SOURCE_METRICS, f"Unexpected source metrics: {side_bearings(source, source_name)}")
        require(side_bearings(ttf, reference_name) == EXPECTED_REFERENCE_METRICS, f"Unexpected U+5967 reference metrics: {side_bearings(ttf, reference_name)}")
        target_advance, target_lsb, target_rsb = side_bearings(ttf, target_name)
        require(target_advance == EXPECTED_ADVANCE, f"U+5965 advance changed: {target_advance}")
        require(target_lsb == EXPECTED_TARGET_LSB, f"Unexpected derived LSB: {target_lsb}")
        require(target_rsb == EXPECTED_TARGET_RSB, f"Unexpected derived RSB: {target_rsb}")
        require(side_bearings(woff2, target_name) == side_bearings(ttf, target_name), "TTF/WOFF2 U+5965 metrics differ")
        center_x = (target_bounds[0] + target_bounds[2]) / 2
        center_y = (target_bounds[1] + target_bounds[3]) / 2
        require(abs(center_x - EXPECTED_ADVANCE / 2) <= 0.5, f"U+5965 is not centered in its advance: {center_x}")
        require(abs(center_y - REFERENCE_CENTER[1]) <= 0.5, f"U+5965 optical y center does not match U+5967 奧: {center_y}")
    finally:
        source.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("PASS: U+5965 keeps the official source drawing and maps to a derived optical copy")
    print("PASS: scale_x=0.895 scale_y=0.895 dx=10.5 dy=34.0 embolden=8.0; advance=790")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
