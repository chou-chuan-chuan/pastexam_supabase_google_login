#!/usr/bin/env python3
"""Verify the scoped Version 1.022 や topology replacement and derived ゃ."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from kana_sources.full_data import KANA_STROKES, YOON_SMALL_KANA_OFFSETS
from kana_sources.user_handwriting_optical import (
    HIRAGANA_OPTICAL_TRANSFORMS,
    USER_HANDWRITING_OPTICALLY_NORMALIZED,
)
from kana_sources.user_handwriting_refined import MODERN_HIRAGANA_ORDER, USER_HANDWRITING_REFINED

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[2]
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+3084-ya-maintainer-handwritten.png"
REFERENCE_SHA256 = "c6697e96ecead227017aed09e008f20daa00d8e0266567e99607674d83755d06"
OTHER_42_SOURCE_SHA256 = "7e23c800ccb7fe7092dce9949fd3bc07a71f5c869df38162028dcc9a9950fbe3"
YA_SOURCE_SHA256 = "a997191110bda0fae60eb313f3d247e5eb65a020a44281d7dcbd263d2919b0b4"
EXPECTED_VERSION = "1.024"


def bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int] | None:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return None if pen.bounds is None else tuple(round(value) for value in pen.bounds)


def glyph_signature(font: TTFont, glyph_name: str) -> tuple:
    glyph = font["glyf"][glyph_name]
    coordinates, end_points, flags = glyph.getCoordinates(font["glyf"])
    return (
        glyph.numberOfContours,
        tuple((round(x), round(y)) for x, y in coordinates),
        tuple(end_points),
        tuple(int(flag) for flag in flags),
    )


def source_bounds(strokes) -> tuple[float, float, float, float]:
    points = [point for stroke in strokes for point in stroke.points]
    return (
        min(point[0] for point in points), min(point[1] for point in points),
        max(point[0] for point in points), max(point[1] for point in points),
    )


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(REFERENCE_PATH.is_file(), "Maintainer や reference image is missing")
    if REFERENCE_PATH.is_file():
        require(hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest() == REFERENCE_SHA256,
                "Maintainer や reference image hash changed")

    other_sources = tuple(
        (character, USER_HANDWRITING_REFINED[character])
        for character in MODERN_HIRAGANA_ORDER if character not in {"や", "お", "す", "う"}
    )
    require(hashlib.sha256(repr(other_sources).encode("utf-8")).hexdigest() == OTHER_42_SOURCE_SHA256,
            "A Hiragana source outside authorized お/す/う and accepted や changed")
    ya_source = USER_HANDWRITING_REFINED["や"]
    require(hashlib.sha256(repr(ya_source).encode("utf-8")).hexdigest() == YA_SOURCE_SHA256,
            "The reviewed Version 1.022 や source changed")
    require(len(ya_source) == 3 and [len(stroke.points) for stroke in ya_source] == [12, 3, 8],
            "や must retain its reviewed three-stroke [12, 3, 8] point topology")
    require(source_bounds(ya_source) == (230.0, 180.0, 744.0, 820.0),
            f"Unexpected や source bounds: {source_bounds(ya_source)}")
    require(HIRAGANA_OPTICAL_TRANSFORMS["や"].scale == 1.0 and
            HIRAGANA_OPTICAL_TRANSFORMS["や"].dx == 0.0 and
            HIRAGANA_OPTICAL_TRANSFORMS["や"].dy == 0.0,
            f"Unexpected や optical transform: {HIRAGANA_OPTICAL_TRANSFORMS['や']}")
    require(USER_HANDWRITING_OPTICALLY_NORMALIZED["や"] == ya_source,
            "や identity optical transform changed source geometry")

    large, small = KANA_STROKES["や"], KANA_STROKES["ゃ"]
    require(len(large) == len(small) == 3, "ゃ does not preserve the three-stroke や topology")
    require([len(stroke.points) for stroke in small] == [12, 3, 8],
            "ゃ does not preserve や point topology")
    for large_stroke, small_stroke in zip(large, small):
        for (large_x, large_y), (small_x, small_y) in zip(large_stroke.points, small_stroke.points):
            dx, dy = YOON_SMALL_KANA_OFFSETS["ゃ"]
            expected = (480 + (large_x - 480) * 0.72 + dx, 500 + (large_y - 500) * 0.72 - 12 + dy)
            require(abs(small_x - expected[0]) < 1e-8 and abs(small_y - expected[1]) < 1e-8,
                    "ゃ is not the shared 0.72-scale/-12-y derivation of や")

    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        for font, label in ((ttf, "TTF"), (woff2, "WOFF2")):
            cmap = font.getBestCmap()
            version_names = {record.toUnicode() for record in font["name"].names if record.nameID == 5}
            require(any(EXPECTED_VERSION in value for value in version_names),
                    f"{label} does not report Version {EXPECTED_VERSION}")
            for character in ("や", "ゃ"):
                glyph_name = cmap.get(ord(character))
                require(glyph_name == f"uni{ord(character):04X}",
                        f"{label} cmap is wrong for U+{ord(character):04X}")
                if glyph_name:
                    glyph_bounds = bounds(font, glyph_name)
                    require(glyph_bounds is not None and glyph_bounds[0] < glyph_bounds[2] and glyph_bounds[1] < glyph_bounds[3],
                            f"{label} {character} has empty/invalid bounds: {glyph_bounds}")
                    require(font["hmtx"].metrics[glyph_name][0] == 960,
                            f"{label} {character} advance is not 960")
        for character in ("や", "ゃ"):
            glyph_name = f"uni{ord(character):04X}"
            require(bounds(ttf, glyph_name) == bounds(woff2, glyph_name),
                    f"TTF/WOFF2 bounds disagree for {character}")
            require(glyph_signature(ttf, glyph_name) == glyph_signature(woff2, glyph_name),
                    f"TTF/WOFF2 outlines disagree for {character}")
        large_bounds, small_bounds = bounds(ttf, "uni3084"), bounds(ttf, "uni3083")
        if large_bounds and small_bounds:
            require(small_bounds[2] - small_bounds[0] < large_bounds[2] - large_bounds[0] and
                    small_bounds[3] - small_bounds[1] < large_bounds[3] - large_bounds[1],
                    "ゃ is not optically smaller than や")
    finally:
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: all non-target Hiragana sources match their snapshots; accepted や remains unchanged")
    print("PASS: U+3083 derives from normalized U+3084 at scale 0.72, then receives only its scoped yōon offset")
    print("PASS: TTF/WOFF2 U+3084 and U+3083 cmap, outlines, bounds, advances, and metadata agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
