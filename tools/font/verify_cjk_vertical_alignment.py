#!/usr/bin/env python3
"""Verify Version 1.023 placement-only alignment for 壁 and 堅."""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from japanese.user_japanese_overrides import SHARED_HAN_OPTICAL_TRANSFORMS


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
TARGETS = "壁堅"
EXPECTED_DY = {"壁": 45, "堅": 35}
EXPECTED_CENTER_Y = {"壁": 365.0, "堅": 354.5}
CONTROLS = "鉄強中紙持"


def bounds(font: TTFont, name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {name} has no bounds")
    return tuple(round(value) for value in pen.bounds)


def signature(font: TTFont, name: str) -> tuple:
    glyph = font["glyf"][name]
    coordinates, end_points, flags = glyph.getCoordinates(font["glyf"])
    return (glyph.numberOfContours, tuple((round(x), round(y)) for x, y in coordinates),
            tuple(end_points), tuple(int(flag) for flag in flags))


def drawing(font: TTFont, name: str, dy: int = 0) -> tuple:
    pen = DecomposingRecordingPen(font.getGlyphSet())
    output_pen = TransformPen(pen, Transform(1, 0, 0, 1, 0, dy)) if dy else pen
    font.getGlyphSet()[name].draw(output_pen)
    normalized = []
    for operation, operands in pen.value:
        normalized_operands = tuple(
            tuple(round(value) for value in point) if isinstance(point, tuple) else point
            for point in operands
        )
        normalized.append((operation, normalized_operands))
    return tuple(normalized)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    source = TTFont(SOURCE_PATH, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        scmap, tcmap, wcmap = source.getBestCmap(), ttf.getBestCmap(), woff2.getBestCmap()
        for character in TARGETS:
            optical = SHARED_HAN_OPTICAL_TRANSFORMS[character]
            expected_dy = EXPECTED_DY[character]
            require((optical.scale_x, optical.scale_y, optical.dx, optical.dy, optical.embolden) ==
                    (1.0, 1.0, 0.0, float(expected_dy), 0.0),
                    f"{character} is not the reviewed placement-only dy +{expected_dy} transform")
            source_name = scmap[ord(character)]
            target_name = tcmap[ord(character)]
            require(target_name == f"{source_name}.qfwJaOptical",
                    f"{character} does not map to its scoped optical copy")
            source_bounds = bounds(source, source_name)
            rendered_bounds = bounds(ttf, target_name)
            require(rendered_bounds == (source_bounds[0], source_bounds[1] + expected_dy,
                                        source_bounds[2], source_bounds[3] + expected_dy),
                    f"{character} bounds are not a pure +{expected_dy} y translation")
            require(drawing(ttf, target_name) == drawing(source, source_name, expected_dy),
                    f"{character} topology or outline changed beyond y translation")
            require(ttf["hmtx"].metrics[target_name] == source["hmtx"].metrics[source_name],
                    f"{character} horizontal metrics changed")
            center_y = (rendered_bounds[1] + rendered_bounds[3]) / 2
            require(center_y == EXPECTED_CENTER_Y[character],
                    f"{character} optical center is not reviewed: {center_y}")
            require(ttf["hhea"].descent < rendered_bounds[1] < rendered_bounds[3] < ttf["hhea"].ascent,
                    f"{character} clips vertical font metrics: {rendered_bounds}")
            require(tcmap[ord(character)] == wcmap[ord(character)], f"TTF/WOFF2 cmap differs for {character}")
            require(bounds(ttf, target_name) == bounds(woff2, target_name),
                    f"TTF/WOFF2 bounds differ for {character}")
            require(drawing(ttf, target_name) == drawing(woff2, target_name),
                    f"TTF/WOFF2 outline differs for {character}")
            require(ttf["hmtx"].metrics[target_name] == woff2["hmtx"].metrics[target_name],
                    f"TTF/WOFF2 metrics differ for {character}")

        for character in CONTROLS:
            source_name = scmap[ord(character)]
            require(tcmap[ord(character)] == source_name, f"Control Han {character} was remapped")
            require(signature(ttf, source_name) == signature(source, source_name),
                    f"Control Han {character} topology changed")
            require(ttf["hmtx"].metrics[source_name] == source["hmtx"].metrics[source_name],
                    f"Control Han {character} metrics changed")
    finally:
        source.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: 壁 and 堅 are source-identical outlines translated only +45 y / +35 y")
    print("PASS: advances/horizontal metrics, global line metrics, and control Han are unchanged")
    print("PASS: 壁/堅 optical centers match reviewed 365/354.5 positions with no clipping and TTF/WOFF2 parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
