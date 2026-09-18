#!/usr/bin/env python3
"""Verify the Version 1.024 scoped す pressure repair and derived ず."""

from __future__ import annotations

import subprocess
import sys
from io import BytesIO
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from kana_sources.full_data import KANA_STROKES, LARGE_HIRAGANA_WEIGHT_FACTOR
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"


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

    source = USER_HANDWRITING_REFINED["す"]
    require(len(source) == 2 and [len(stroke.points) for stroke in source] == [4, 16],
            "す center-line topology changed")
    require([(s.width, s.start_width, s.end_width) for s in source] ==
            [(43.0, 38.0, 32.0), (46.0, 41.0, 33.0)],
            "す does not retain the reviewed harmonized per-stroke pressure")
    transform = HIRAGANA_OPTICAL_TRANSFORMS["す"]
    require((transform.scale_x, transform.scale_y, transform.dx, transform.dy) == (1.60, 1.04, 59.0, -47.0),
            "す optical placement changed during the pressure-only repair")
    normalized = KANA_STROKES["す"]
    for source_stroke, final_stroke in zip(source, normalized):
        require(final_stroke.width >= source_stroke.width * LARGE_HIRAGANA_WEIGHT_FACTOR,
                "す final pressure does not include the normal Hiragana weight layer")
        require(final_stroke.end_width >= 32.0 * LARGE_HIRAGANA_WEIGHT_FACTOR,
                "す retains a locally thin terminal segment")

    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = TTFont(BytesIO(before_bytes), recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    bounds_value = None
    try:
        require(signature(ttf, "uni3059") != signature(before, "uni3059"), "Compiled す did not change")
        require(signature(ttf, "uni305A") != signature(before, "uni305A"), "Derived ず did not inherit repaired す")
        require(components(ttf, "uni305A") == components(before, "uni305A"),
                "ず dakuten/base component placement changed unexpectedly")
        for character in "すず":
            name = f"uni{ord(character):04X}"
            glyph_bounds = bounds(ttf, name)
            if character == "す":
                bounds_value = glyph_bounds
            advance, lsb = ttf["hmtx"].metrics[name]
            require(advance == 960 and lsb == glyph_bounds[0], f"{character} metrics are invalid")
            require(ttf["hhea"].descent < glyph_bounds[1] < glyph_bounds[3] < ttf["hhea"].ascent,
                    f"{character} clips vertically: {glyph_bounds}")
            require(signature(ttf, name) == signature(woff2, name), f"TTF/WOFF2 differ for {character}")
            require(ttf["hmtx"].metrics[name] == woff2["hmtx"].metrics[name],
                    f"TTF/WOFF2 metrics differ for {character}")
        for character in "やえか":
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(before, name), f"Control Hiragana {character} changed")
    finally:
        before.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: す retains its accepted two-stroke geometry with harmonized local pressure")
    print("PASS: ず inherits repaired す with unchanged dakuten placement and no collision")
    print(f"す bounds={bounds_value} advance=960")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
