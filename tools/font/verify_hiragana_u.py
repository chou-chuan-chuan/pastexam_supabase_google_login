#!/usr/bin/env python3
"""Verify Version 1.024 maintainer-handwritten う, derived ぅ, and composite ゔ."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from kana_sources.full_data import KANA_STROKES, YOON_SMALL_KANA_OFFSETS
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+3046-u-maintainer-handwritten.png"
REFERENCE_SHA256 = "9bc3e27070da6d14fb23473edf11f6fec4e2eef537ae7b0e77c9d299cc31ad0d"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"


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


def components(font: TTFont, name: str) -> tuple:
    glyph = font["glyf"][name]
    return tuple((component.glyphName, component.getComponentInfo()[1]) for component in glyph.components)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(REFERENCE_PATH.is_file(), "Maintainer う reference image is missing")
    if REFERENCE_PATH.is_file():
        require(hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest() == REFERENCE_SHA256,
                "Maintainer う reference image hash changed")
    source = USER_HANDWRITING_REFINED["う"]
    require(len(source) == 2 and [len(stroke.points) for stroke in source] == [4, 15],
            "う must retain the photo-coordinate two-stroke [4,15] topology")
    require(tuple(round(v, 3) for v in source_bounds(source)) == (339.091, 195.0, 620.909, 815.0),
            f"Unexpected う source bounds: {source_bounds(source)}")
    transform = HIRAGANA_OPTICAL_TRANSFORMS["う"]
    require((transform.scale_x or transform.scale, transform.scale_y or transform.scale,
             transform.dx, transform.dy) == (1.0, 1.0, 0.0, 0.0),
            f"Unexpected う optical transform: {transform}")
    require("ぅ" not in YOON_SMALL_KANA_OFFSETS, "ぅ was incorrectly assigned a yōon offset")
    large, small = KANA_STROKES["う"], KANA_STROKES["ぅ"]
    require([len(stroke.points) for stroke in large] == [4, 15] and
            [len(stroke.points) for stroke in small] == [4, 15],
            "ぅ does not preserve the revised う topology")
    for large_stroke, small_stroke in zip(large, small):
        for (large_x, large_y), (small_x, small_y) in zip(large_stroke.points, small_stroke.points):
            expected = (480 + (large_x - 480) * 0.72, 500 + (large_y - 500) * 0.72 - 12)
            require(abs(small_x - expected[0]) < 1e-8 and abs(small_y - expected[1]) < 1e-8,
                    "ぅ is not the normal 0.72-scale/-12-y derivation of revised う")

    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = TTFont(BytesIO(before_bytes), recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        for character in "うぅゔ":
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) != signature(before, name), f"Compiled {character} did not change")
            glyph_bounds = bounds(ttf, name)
            advance, lsb = ttf["hmtx"].metrics[name]
            require(advance == 960 and lsb == glyph_bounds[0], f"{character} metrics are invalid")
            require(ttf["hhea"].descent < glyph_bounds[1] < glyph_bounds[3] < ttf["hhea"].ascent,
                    f"{character} clips vertically: {glyph_bounds}")
            require(signature(ttf, name) == signature(woff2, name), f"TTF/WOFF2 differ for {character}")
            require(ttf["hmtx"].metrics[name] == woff2["hmtx"].metrics[name],
                    f"TTF/WOFF2 metrics differ for {character}")
        before_components = components(before, "uni3094")
        after_components = components(ttf, "uni3094")
        require(after_components[0] == ("uni3046", (1, 0, 0, 1, 0, 0)),
                "ゔ no longer uses revised う as an identity base component")
        require(before_components[1][0] == after_components[1][0] == "uni3099" and
                before_components[1][1][5] == after_components[1][1][5] == -125 and
                after_components[1][1][4] == 618,
                f"ゔ dakuten anchor is not the reviewed bounds-derived placement: {after_components[1]}")
        for character in "えや":
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(before, name), f"Control Hiragana {character} changed")
        u_bounds, small_bounds, vu_bounds = (bounds(ttf, f"uni{ord(c):04X}") for c in "うぅゔ")
        require(small_bounds[2] - small_bounds[0] < u_bounds[2] - u_bounds[0] and
                small_bounds[3] - small_bounds[1] < u_bounds[3] - u_bounds[1],
                "ぅ is not visibly smaller than revised う")
        require(vu_bounds[3] > u_bounds[3] and vu_bounds[1] == u_bounds[1],
                "ゔ dakuten relationship to revised う is invalid")
    finally:
        before.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: U+3046 uses the authorized two-stroke maintainer-handwritten source")
    print("PASS: U+3045 derives through the normal small-kana path without yōon positioning")
    print("PASS: U+3094 inherits revised う with reviewed bounds-derived dakuten placement and TTF/WOFF2 parity")
    print(f"う source_bounds={source_bounds(source)} rendered_bounds={u_bounds} advance=960")
    print(f"ぅ rendered_bounds={small_bounds} scale=0.72 position=normal-small-kana; ゔ bounds={vu_bounds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
