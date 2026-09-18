#!/usr/bin/env python3
"""Verify the Version 1.024 repaired maintainer-handwritten お and derived ぉ."""

from __future__ import annotations

import hashlib
import sys
import subprocess
from io import BytesIO
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
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+304A-o-maintainer-handwritten.png"
REFERENCE_SHA256 = "ce49873d3a6f49382ad54f356ed370781db9df0e0c6c9640552bad9a015f4b2c"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
EXPECTED_VERSION = "1.024"
UNCHANGED_SOURCE_SHA256 = "032231e2ce4615fd6ce6045cf11103f1b9efb811812e7fbfc04b4e0e5ec74bd5"


def source_bounds(strokes) -> tuple[float, float, float, float]:
    points = [point for stroke in strokes for point in stroke.points]
    return (min(x for x, _ in points), min(y for _, y in points),
            max(x for x, _ in points), max(y for _, y in points))


def bounds(font: TTFont, name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {name} has no outline")
    return tuple(round(value) for value in pen.bounds)


def signature(font: TTFont, name: str) -> tuple:
    glyph = font["glyf"][name]
    coordinates, end_points, flags = glyph.getCoordinates(font["glyf"])
    return (glyph.numberOfContours, tuple((round(x), round(y)) for x, y in coordinates),
            tuple(end_points), tuple(int(flag) for flag in flags))


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(REFERENCE_PATH.is_file(), "Maintainer お reference image is missing")
    if REFERENCE_PATH.is_file():
        require(hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest() == REFERENCE_SHA256,
                "Maintainer お reference image hash changed")

    source = USER_HANDWRITING_REFINED["お"]
    require(len(source) == 3 and [len(stroke.points) for stroke in source] == [3, 16, 3],
            "お must retain the outline-derived three-stroke [3, 16, 3] topology")
    require(source_bounds(source) == (209.0, 190.0, 746.0, 835.0),
            f"Unexpected お source bounds: {source_bounds(source)}")
    transform = HIRAGANA_OPTICAL_TRANSFORMS["お"]
    require(transform.scale == 1.0 and transform.dx == 0.0 and transform.dy == 0.0,
            f"お optical transform is not identity: {transform}")
    require(USER_HANDWRITING_OPTICALLY_NORMALIZED["お"] == source,
            "お identity optical transform changed source geometry")
    unchanged_sources = tuple((character, USER_HANDWRITING_REFINED[character])
                              for character in MODERN_HIRAGANA_ORDER if character not in "おすう")
    require(hashlib.sha256(repr(unchanged_sources).encode("utf-8")).hexdigest() == UNCHANGED_SOURCE_SHA256,
            "A large Hiragana source outside the authorized お/す/う repair changed")

    large, small = KANA_STROKES["お"], KANA_STROKES["ぉ"]
    require(len(large) == len(small) == 3, "ぉ does not preserve the new お stroke topology")
    require("ぉ" not in YOON_SMALL_KANA_OFFSETS, "ぉ was incorrectly included in yōon offsets")
    for large_stroke, small_stroke in zip(large, small):
        require(len(large_stroke.points) == len(small_stroke.points), "ぉ point topology differs from お")
        for (large_x, large_y), (small_x, small_y) in zip(large_stroke.points, small_stroke.points):
            expected = (480 + (large_x - 480) * 0.72, 500 + (large_y - 500) * 0.72 - 12)
            require(abs(small_x - expected[0]) < 1e-8 and abs(small_y - expected[1]) < 1e-8,
                    "ぉ is not the normal 0.72-scale/-12-y derivation of お")

    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = TTFont(BytesIO(before_bytes), recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        version_names = {record.toUnicode() for record in ttf["name"].names if record.nameID == 5}
        require(any(EXPECTED_VERSION in value for value in version_names),
                f"TTF does not report Version {EXPECTED_VERSION}")
        require(signature(ttf, "uni304A") != signature(before, "uni304A"), "Compiled お did not change")
        require(signature(ttf, "uni3049") != signature(before, "uni3049"), "Derived ぉ did not change")
        for character in "ぁぃぇ":
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(before, name), f"Control small vowel {character} changed")
            require(ttf["hmtx"].metrics[name] == before["hmtx"].metrics[name],
                    f"Control small vowel {character} metrics changed")
        for character in "きや":
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(before, name), f"Accepted {character} topology changed")
        for character in "おぉ":
            name = f"uni{ord(character):04X}"
            glyph_bounds = bounds(ttf, name)
            advance, lsb = ttf["hmtx"].metrics[name]
            require(advance == 960 and lsb == glyph_bounds[0], f"{character} metrics are invalid")
            require(glyph_bounds[0] >= 0 and glyph_bounds[2] <= advance and glyph_bounds[1] >= 0,
                    f"{character} clips its glyph box: {glyph_bounds}")
            require(signature(ttf, name) == signature(woff2, name), f"TTF/WOFF2 outlines differ for {character}")
            require(bounds(ttf, name) == bounds(woff2, name), f"TTF/WOFF2 bounds differ for {character}")
            require(ttf["hmtx"].metrics[name] == woff2["hmtx"].metrics[name],
                    f"TTF/WOFF2 metrics differ for {character}")
        large_bounds, small_bounds = bounds(ttf, "uni304A"), bounds(ttf, "uni3049")
        require(small_bounds[2] - small_bounds[0] < large_bounds[2] - large_bounds[0] and
                small_bounds[3] - small_bounds[1] < large_bounds[3] - large_bounds[1],
                "ぉ is not visibly smaller than お")
    finally:
        before.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: U+304A uses the repaired three-stroke maintainer-handwritten source")
    print("PASS: U+3049 derives normally at scale 0.72 with shared shift (0,-12), not a yōon offset")
    print("PASS: non-target small vowels/Hiragana, accepted き/や, and full-width metrics are unchanged")
    print(f"お source_bounds={source_bounds(source)} rendered_bounds={large_bounds} advance=960 transform=identity")
    print(f"ぉ rendered_bounds={small_bounds} advance=960 scale=0.72 position=normal-small-kana")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
