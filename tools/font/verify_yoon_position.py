#!/usr/bin/env python3
"""Verify Version 1.023 yōon small-kana in-cell optical positioning."""

from __future__ import annotations

import sys
import subprocess
from io import BytesIO
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from kana_sources.full_data import YOON_SMALL_KANA_OFFSETS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[2]
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
EXPECTED_VERSION = "1.024"
TARGET_SOURCES = {
    "ゃ": "や", "ゅ": "ゆ", "ょ": "よ",
    "ャ": "ヤ", "ュ": "ユ", "ョ": "ヨ",
}
# U+3049 ぉ is intentionally regenerated from the separately authorized new
# U+304A お in this same revision and is verified by verify_hiragana_o.py.
NON_YOON_SMALL = "ぁぃぇっゎゕゖァィゥェォッヮヵヶ"
BASE_SHIFTS = {"ゃ": (0, -12), "ゅ": (0, -12), "ょ": (0, -12),
               "ャ": (0, -15), "ュ": (0, -15), "ョ": (0, -15)}


def bounds(font: TTFont, name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {name} has no outline")
    return tuple(round(value) for value in pen.bounds)


def signature(font: TTFont, name: str) -> tuple:
    glyph = font["glyf"][name]
    coordinates, end_points, flags = glyph.getCoordinates(font["glyf"])
    return (
        glyph.numberOfContours,
        tuple((round(x), round(y)) for x, y in coordinates),
        tuple(end_points),
        tuple(int(flag) for flag in flags),
    )


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH],
        cwd=REPO_ROOT,
    )
    before = TTFont(BytesIO(before_bytes), recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        version_names = {record.toUnicode() for record in ttf["name"].names if record.nameID == 5}
        require(any(EXPECTED_VERSION in value for value in version_names),
                f"TTF does not report Version {EXPECTED_VERSION}")

        for character, source in TARGET_SOURCES.items():
            name = f"uni{ord(character):04X}"
            source_name = f"uni{ord(source):04X}"
            before_sig = signature(before, name)
            after_sig = signature(ttf, name)
            require(after_sig == before_sig,
                    f"Accepted yōon glyph {character} changed in the repair revision")
            require(signature(ttf, source_name) == signature(before, source_name),
                    f"Large source {source} changed")
            require(ttf["hmtx"].metrics[source_name] == before["hmtx"].metrics[source_name],
                    f"Large source {source} metrics changed")
            old_bounds = bounds(before, name)
            new_bounds = bounds(ttf, name)
            require(new_bounds == old_bounds,
                    f"Accepted yōon bounds changed: {old_bounds} -> {new_bounds}")
            advance, lsb = ttf["hmtx"].metrics[name]
            require(advance == before["hmtx"].metrics[name][0] == 960,
                    f"{character} full-width advance changed")
            require(170 <= new_bounds[0] <= 190 and 16 <= new_bounds[1] <= 32,
                    f"{character} is outside reviewed lower-left optical bounds: {new_bounds}")
            require(new_bounds[0] >= 0 and new_bounds[2] <= advance and new_bounds[1] >= 0,
                    f"{character} clips or crosses its own advance box: {new_bounds}, advance={advance}")
            require(lsb == new_bounds[0] and advance - new_bounds[2] > 0,
                    f"{character} sidebearings are inconsistent")

        for character in NON_YOON_SMALL:
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(before, name),
                    f"Non-yōon small kana {character} outline changed")
            require(ttf["hmtx"].metrics[name] == before["hmtx"].metrics[name],
                    f"Non-yōon small kana {character} metrics changed")

        for character in TARGET_SOURCES:
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(woff2, name),
                    f"TTF/WOFF2 outlines differ for {character}")
            require(bounds(ttf, name) == bounds(woff2, name),
                    f"TTF/WOFF2 bounds differ for {character}")
            require(ttf["hmtx"].metrics[name] == woff2["hmtx"].metrics[name],
                    f"TTF/WOFF2 metrics differ for {character}")

        if errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 1

        print("PASS: all six accepted yōon glyph outlines/positions are unchanged from origin/main")
        print("PASS: large sources and non-target small-kana controls are unchanged; authorized ぉ/ぅ are gated separately")
        print("PASS: full-width 960-unit advances, safe sidebearings, and TTF/WOFF2 parity are preserved")
        print("character source scale old_dx/dy new_dx/dy bounds advance lsb rsb")
        for character, source in TARGET_SOURCES.items():
            name = f"uni{ord(character):04X}"
            base_dx, base_dy = BASE_SHIFTS[character]
            dx, dy = YOON_SMALL_KANA_OFFSETS[character]
            glyph_bounds = bounds(ttf, name)
            advance, lsb = ttf["hmtx"].metrics[name]
            print(f"{character} {source} 0.72 ({base_dx:+d},{base_dy:+d}) "
                  f"({base_dx + dx:+d},{base_dy + dy:+d}) {glyph_bounds} "
                  f"{advance} {lsb} {advance - glyph_bounds[2]}")
        return 0
    finally:
        before.close()
        ttf.close()
        woff2.close()


if __name__ == "__main__":
    raise SystemExit(main())
