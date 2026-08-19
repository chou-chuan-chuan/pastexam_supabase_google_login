#!/usr/bin/env python3
"""Verify Version 1.011 user-handwriting references and refined font output."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import median

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from japanese.svg_template_loader import (
    MODERN_HIRAGANA_ORDER,
    SVG_TEMPLATE_SOURCE_CHARACTERS,
    build_svg_reference_glyph,
)
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = TOOLS_DIR / "references"
SOURCE_COMPLETE = REFERENCE_DIR / "user-hiragana-template-source-complete.png"
MANIFEST_PATH = REFERENCE_DIR / "user-hiragana-template-manifest.json"
SVG_DIR = REFERENCE_DIR / "user-hiragana-svg"
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
EXPECTED_COMPLETE_SHA256 = "ed588c5e8c062a5053467a446e348570ec933b0afcd82dace0298798ea81afe9"
EXPECTED_VERSION = "1.011"
KANA_ADVANCE = 960


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def glyph_signature(glyph, glyf_table) -> tuple:
    coordinates, end_points, flags = glyph.getCoordinates(glyf_table)
    return (
        glyph.numberOfContours,
        tuple((round(x), round(y)) for x, y in coordinates),
        tuple(end_points),
        tuple(int(flag) for flag in flags),
    )


def stroke_length(stroke) -> float:
    return sum(math.dist(a, b) for a, b in zip(stroke.points, stroke.points[1:]))


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for path in (SOURCE_COMPLETE, MANIFEST_PATH, FONT_PATH):
        require(path.is_file(), f"Missing required file: {path}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    require(sha256(SOURCE_COMPLETE) == EXPECTED_COMPLETE_SHA256,
            "The complete maintainer handwriting source image hash changed")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    require(manifest.get("font_version") == EXPECTED_VERSION,
            f"Template manifest version is not {EXPECTED_VERSION}")
    require(manifest.get("coverage", {}).get("basic_modern_hiragana") == 46,
            "Template manifest does not declare all 46 modern basic Hiragana")
    expected = set(MODERN_HIRAGANA_ORDER)
    require(set(SVG_TEMPLATE_SOURCE_CHARACTERS) == expected,
            "SVG reference loader does not cover all 46 modern Hiragana")
    require(set(USER_HANDWRITING_REFINED) == expected,
            "Refined center-line source does not cover all 46 modern Hiragana")

    records = {item["character"]: item for item in manifest.get("glyphs", [])}
    require(set(records) == expected, "SVG manifest character set is incomplete")
    for character in sorted(expected, key=ord):
        record = records.get(character)
        if not record:
            continue
        path = SVG_DIR / record["file"]
        require(path.is_file(), f"Missing SVG for {character}: {path}")
        if path.is_file():
            require(sha256(path) == record["sha256"], f"SVG hash mismatch for {character}")
        strokes = USER_HANDWRITING_REFINED[character]
        require(bool(strokes), f"No refined strokes for {character}")
        for stroke in strokes:
            require(38 <= stroke.width <= 54, f"{character} has out-of-style width {stroke.width}")
            require(len(stroke.points) >= 2, f"{character} contains an empty stroke")

    # Structural gates for the glyphs that motivated this refinement.
    require(any(stroke_length(stroke) < 190 for stroke in USER_HANDWRITING_REFINED["む"]),
            "む no longer preserves a short independent handwritten mark")
    require(repr(USER_HANDWRITING_REFINED["ぬ"]) != repr(USER_HANDWRITING_REFINED["め"]),
            "ぬ and め refined sources unexpectedly became identical")
    require(repr(USER_HANDWRITING_REFINED["き"]) != repr(USER_HANDWRITING_REFINED["さ"]),
            "き and さ refined sources unexpectedly became identical")
    require(all(character in USER_HANDWRITING_REFINED for character in "わをん"),
            "Version 1.011 is missing the newly supplied わ/を/ん sources")

    font = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        cmap = font.getBestCmap()
        version_names = {record.toUnicode() for record in font["name"].names if record.nameID == 5}
        require(any(EXPECTED_VERSION in value for value in version_names),
                f"Built font name table does not report Version {EXPECTED_VERSION}")

        hira_centers = []
        for character in MODERN_HIRAGANA_ORDER:
            glyph_name = cmap.get(ord(character))
            require(glyph_name is not None, f"Built font is missing {character} U+{ord(character):04X}")
            if glyph_name is None:
                continue
            glyph = font["glyf"][glyph_name]
            require(not glyph.isComposite(), f"Basic Hiragana {character} unexpectedly became composite")
            glyph_bounds = bounds(font, glyph_name)
            require(glyph_bounds is not None, f"Built glyph {character} has no bounds")
            if glyph_bounds:
                require(-80 <= glyph_bounds[0] < glyph_bounds[2] <= 1040,
                        f"Unsafe horizontal bounds for {character}: {glyph_bounds}")
                require(font["hhea"].descent < glyph_bounds[1] < glyph_bounds[3] < font["hhea"].ascent,
                        f"Unsafe vertical bounds for {character}: {glyph_bounds}")
                hira_centers.append((glyph_bounds[1] + glyph_bounds[3]) / 2)
            require(font["hmtx"].metrics[glyph_name][0] == KANA_ADVANCE,
                    f"Unexpected advance for {character}: {font['hmtx'].metrics[glyph_name][0]}")

        # Mixed CJK/Kana optical alignment is a first-class 1.011 gate.
        han_sample = "平仮名片君愛声夢春心明日夜空"
        han_centers = []
        for character in han_sample:
            glyph_name = cmap.get(ord(character))
            if glyph_name:
                b = bounds(font, glyph_name)
                if b:
                    han_centers.append((b[1] + b[3]) / 2)
        if hira_centers and han_centers:
            hira_center = median(hira_centers)
            han_center = median(han_centers)
            require(abs(hira_center - han_center) <= 30,
                    f"Refined Hiragana optical center does not align with source CJK: hira={hira_center}, han={han_center}")

        # Ensure the build is no longer installing the filled SVG outlines directly.
        for character in "きぬむめわをん":
            glyph_name = cmap.get(ord(character))
            if not glyph_name:
                continue
            actual = font["glyf"][glyph_name]
            reference = build_svg_reference_glyph(character, -145)
            if not actual.isComposite():
                require(glyph_signature(actual, font["glyf"]) != glyph_signature(reference, {}),
                        f"{character} still exactly matches the old direct-SVG outline instead of refined strokes")

        # Small wa must now derive from the newly supplied わ source and remain optically smaller.
        for small, base in (("ゎ", "わ"), ("っ", "つ"), ("ゃ", "や")):
            sb = bounds(font, cmap[ord(small)])
            bb = bounds(font, cmap[ord(base)])
            if sb and bb:
                require((sb[2]-sb[0]) < (bb[2]-bb[0]) and (sb[3]-sb[1]) < (bb[3]-bb[1]),
                        f"Small-kana scale is not smaller for {small} <- {base}")
    finally:
        font.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"Refined Hiragana verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("PASS: 46 maintainer-authored Hiragana SVG references and hashes are complete")
    print("PASS: filled SVG outlines are references only; final glyphs use refined center-line strokes")
    print("PASS: む short mark, ぬ/め distinction, き/さ distinction, and わ/を/ん coverage are preserved")
    print("PASS: final TTF advances, bounds, Version 1.011 metadata, and CJK optical alignment are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
