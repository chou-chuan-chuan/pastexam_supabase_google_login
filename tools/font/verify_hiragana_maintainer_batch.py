#!/usr/bin/env python3
"""Verify Version 1.024 maintainer sources for あ/い/さ/き/と/り and derivatives."""

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
from kana_sources.user_handwriting_refined import MODERN_HIRAGANA_ORDER, USER_HANDWRITING_REFINED

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
REFERENCE_PATHS = {
    TOOLS_DIR / "references/U+3042-U+3044-U+3055-U+304D-maintainer-handwritten.png":
        "fddcbc948566f1b6f153932477aed5dc21a466d9608be94019692594c90e18c0",
    TOOLS_DIR / "references/U+3068-U+308A-maintainer-handwritten.png":
        "ebfbc29d18c44bef9523236e0f4997d239c0442579918f312440e8e225558063",
}
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
TARGETS = "あいさきとり"
EXPECTED_TOPOLOGY = {
    "あ": [3, 4, 17], "い": [7, 5], "さ": [3, 5, 6],
    "き": [3, 3, 5, 6], "と": [2, 9], "り": [5, 7],
}
EXPECTED_SOURCE_BOUNDS = {
    "あ": (230.0, 180.0, 730.0, 835.0),
    "い": (305.0, 250.0, 695.0, 760.0),
    "さ": (235.0, 175.0, 635.0, 820.0),
    "き": (240.0, 175.0, 675.0, 830.0),
    "と": (250.0, 305.0, 705.0, 820.0),
    "り": (300.0, 170.0, 615.0, 820.0),
}
AUTHORIZED_SOURCES = set("おすうあいさきとり")
UNCHANGED_SOURCE_SHA256 = "358de68e2b5f01fbd559b363de6058ae6edc72a7a5fa07babe016e78d7cb21e1"


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
    return tuple(component.getComponentInfo() for component in font["glyf"][name].components)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for path, expected_hash in REFERENCE_PATHS.items():
        require(path.is_file(), f"Maintainer reference is missing: {path.name}")
        if path.is_file():
            require(hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash,
                    f"Maintainer reference hash changed: {path.name}")

    for character in TARGETS:
        source = USER_HANDWRITING_REFINED[character]
        require([len(stroke.points) for stroke in source] == EXPECTED_TOPOLOGY[character],
                f"Unexpected {character} stroke topology")
        require(source_bounds(source) == EXPECTED_SOURCE_BOUNDS[character],
                f"Unexpected {character} source bounds: {source_bounds(source)}")
        transform = HIRAGANA_OPTICAL_TRANSFORMS[character]
        require((transform.scale_x or transform.scale, transform.scale_y or transform.scale,
                 transform.dx, transform.dy) == (1.0, 1.0, 0.0, 0.0),
                f"{character} must use its reviewed identity optical transform")

    unchanged = tuple((character, USER_HANDWRITING_REFINED[character])
                      for character in MODERN_HIRAGANA_ORDER if character not in AUTHORIZED_SOURCES)
    require(hashlib.sha256(repr(unchanged).encode("utf-8")).hexdigest() == UNCHANGED_SOURCE_SHA256,
            "A non-authorized large Hiragana source changed")

    for small, large in (("ぁ", "あ"), ("ぃ", "い")):
        require(small not in YOON_SMALL_KANA_OFFSETS, f"{small} was incorrectly assigned a yōon offset")
        for large_stroke, small_stroke in zip(KANA_STROKES[large], KANA_STROKES[small]):
            require(len(large_stroke.points) == len(small_stroke.points), f"{small} topology differs from {large}")
            for (large_x, large_y), (small_x, small_y) in zip(large_stroke.points, small_stroke.points):
                expected = (480 + (large_x - 480) * 0.72, 500 + (large_y - 500) * 0.72 - 12)
                require(abs(small_x - expected[0]) < 1e-8 and abs(small_y - expected[1]) < 1e-8,
                        f"{small} does not follow the normal 0.72-scale/-12-y path")

    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = TTFont(BytesIO(before_bytes), recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        changed = TARGETS + "ぁぃざぎど"
        for character in changed:
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) != signature(before, name), f"Compiled {character} did not change")
            require(signature(ttf, name) == signature(woff2, name), f"TTF/WOFF2 differ for {character}")
            glyph_bounds = bounds(ttf, name)
            advance, lsb = ttf["hmtx"].metrics[name]
            require(advance == 960 and lsb == glyph_bounds[0], f"{character} metrics are invalid")
            require(0 <= glyph_bounds[0] < glyph_bounds[2] <= advance and
                    ttf["hhea"].descent < glyph_bounds[1] < glyph_bounds[3] < ttf["hhea"].ascent,
                    f"{character} clips or escapes its cell: {glyph_bounds}")
        for voiced, base in (("ざ", "さ"), ("ぎ", "き"), ("ど", "と")):
            voiced_components = components(ttf, f"uni{ord(voiced):04X}")
            require(voiced_components[0] == (f"uni{ord(base):04X}", (1, 0, 0, 1, 0, 0)) and
                    voiced_components[1][0] == "uni3099" and voiced_components[1][1][5] == -125,
                    f"{voiced} does not inherit revised {base} with the shared dakuten")
        for character in "ゃゅょャュョ":
            name = f"uni{ord(character):04X}"
            require(signature(ttf, name) == signature(before, name), f"Accepted yōon glyph {character} drifted")
            require(ttf["hmtx"].metrics[name][0] == 960, f"Yōon glyph {character} lost full-width advance")
        for character in "えかくけこしせそたちつてらるれろやゆよ":
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
    print("PASS: あ/い/さ/き/と/り use the newly authorized maintainer center-line sources")
    print("PASS: ぁ/ぃ remain normal small-kana; ざ/ぎ/ど inherit the revised bases")
    print("PASS: yōon glyphs remain unchanged/full-width and composition bases き/り are current")
    print("PASS: unrelated large Hiragana are unchanged; TTF/WOFF2 agree without clipping")
    report_font = TTFont(TTF_PATH, recalcTimestamp=False)
    try:
        for character in TARGETS:
            print(f"{character} source_bounds={source_bounds(USER_HANDWRITING_REFINED[character])} "
                  f"rendered_bounds={bounds(report_font, f'uni{ord(character):04X}')} advance=960")
    finally:
        report_font.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
