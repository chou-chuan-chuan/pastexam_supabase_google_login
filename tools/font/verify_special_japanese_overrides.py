#!/usr/bin/env python3
"""Verify approved Version 1.014 Japanese overrides without weakening source gates."""

from __future__ import annotations

import math
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from kana_sources.user_japanese_mark_refined import USER_JAPANESE_MARK_REFINED
from kana_sources.user_kanji_refined import (
    HYBRID_REPLACEMENT_CHARACTER,
    HYBRID_REPLACEMENT_TRANSFORM,
    HYBRID_SOURCE_CHARACTER,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def drawing(font: TTFont, glyph_name: str) -> tuple:
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return tuple(pen.value)


def point_segment_distance(point, start, end) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.dist(point, start)
    ratio = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(point, (ax + ratio * dx, ay + ratio * dy))


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    source = TTFont(SOURCE, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        scmap = source.getBestCmap()
        tcmap = ttf.getBestCmap()
        wcmap = woff2.getBestCmap()

        require(HYBRID_SOURCE_CHARACTER == {"懐": "懷"}, "懐 must use native 懷 as its style source")
        require(HYBRID_REPLACEMENT_CHARACTER == {"懐": "衣"}, "懐 must use native 衣 as its lower source")
        require(HYBRID_REPLACEMENT_TRANSFORM[0] == 0.86,
                "Native 衣 must retain the approved uniform 0.86 scale")

        target_name = tcmap.get(ord("懐"))
        require(target_name is not None and target_name.endswith(".qfwUser"),
                "懐 U+61D0 is not mapped to the approved hybrid override")
        if target_name:
            target_bounds = bounds(ttf, target_name)
            require(target_bounds is not None, "Hybrid 懐 has no outline bounds")
            if target_bounds:
                x_min, y_min, x_max, y_max = target_bounds
                require(70 <= x_min <= 110 and 900 <= x_max <= 980,
                        f"Hybrid 懐 horizontal bounds changed unexpectedly: {target_bounds}")
                require(-90 <= y_min <= -30 and 740 <= y_max <= 790,
                        f"Hybrid 懐 vertical bounds changed unexpectedly: {target_bounds}")
                require(abs((y_min + y_max) / 2 - 350) <= 5,
                        f"Hybrid 懐 is not vertically aligned with mixed CJK: {target_bounds}")

        # Cmap remapping must never destroy or mutate any original source drawing.
        for character in "懐懷衣夕":
            codepoint = ord(character)
            source_name = scmap.get(codepoint)
            require(source_name is not None, f"Source font is missing {character} U+{codepoint:04X}")
            if source_name is None:
                continue
            require(source_name in ttf.getGlyphOrder(), f"Derived font removed source glyph {source_name}")
            require(drawing(source, source_name) == drawing(ttf, source_name),
                    f"Original source drawing changed for {character} ({source_name})")
            if character != "懐":
                require(tcmap.get(codepoint) == source_name,
                        f"{character} U+{codepoint:04X} must retain its source cmap mapping")

        repeat_name = tcmap.get(ord("々"))
        require(repeat_name is not None and repeat_name.endswith(".qfwUser"),
                "々 U+3005 is not mapped to the dedicated approved override")
        if repeat_name:
            require(ttf["hmtx"].metrics[repeat_name][0] == 960,
                    f"々 advance must be 960, got {ttf['hmtx'].metrics[repeat_name][0]}")
            repeat_bounds = bounds(ttf, repeat_name)
            require(repeat_bounds is not None and 40 <= repeat_bounds[1] < repeat_bounds[3] <= 730,
                    f"々 mixed-text vertical bounds are unsafe: {repeat_bounds}")

        repeat_strokes = USER_JAPANESE_MARK_REFINED["々"]
        join_point = repeat_strokes[2].points[-1]
        lower_points = repeat_strokes[3].points
        join_distance = min(
            point_segment_distance(join_point, start, end)
            for start, end in zip(lower_points, lower_points[1:])
        )
        require(join_distance <= 3.0,
                f"々 right/lower center-lines no longer intersect: distance={join_distance:.2f}")

        require(tcmap == wcmap, "TTF and WOFF2 cmap differ")
        for character in "懐々夕":
            name = tcmap.get(ord(character))
            if name:
                require(bounds(ttf, name) == bounds(woff2, name),
                        f"TTF/WOFF2 bounds differ for {character}")
    finally:
        source.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        print(f"Special Japanese verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("PASS: 懐 uses native 懷 + native 衣 while preserving all source drawings")
    print("PASS: 々 uses connected project-local center-lines and safe mixed-text metrics")
    print("PASS: 夕 remains source-identical and TTF/WOFF2 agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
