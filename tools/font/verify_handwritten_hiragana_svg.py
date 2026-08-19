#!/usr/bin/env python3
"""Verify that the built font exactly uses the user-authored Hiragana SVGs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from statistics import median

from fontTools.ttLib import TTFont

from japanese.svg_template_loader import (
    SVG_TEMPLATE_CHARACTERS,
    SVG_TEMPLATE_SMALL_MAP,
    SVG_TEMPLATE_SOURCE_CHARACTERS,
    build_svg_template_glyph,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = TOOLS_DIR / "references"
SOURCE_IMAGE = REFERENCE_DIR / "user-hiragana-template-source.png"
MANIFEST_PATH = REFERENCE_DIR / "user-hiragana-template-manifest.json"
SVG_DIR = REFERENCE_DIR / "user-hiragana-svg"
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
EXPECTED_SOURCE_SHA256 = "dea3c4c8576744dd609161940aae594a92bb9864b174a54dfce53759c32f0a00"
EXPECTED_VERSION = "1.010"
KANA_VERTICAL_SHIFT = -145
KANA_ADVANCE = 960


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glyph_signature(glyph, glyf_table) -> tuple:
    coordinates, end_points, flags = glyph.getCoordinates(glyf_table)
    return (
        glyph.numberOfContours,
        tuple((round(x), round(y)) for x, y in coordinates),
        tuple(end_points),
        tuple(int(flag) for flag in flags),
    )


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (SOURCE_IMAGE, MANIFEST_PATH, FONT_PATH):
        if not path.is_file():
            fail(f"Missing required file: {path}", errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if sha256(SOURCE_IMAGE) != EXPECTED_SOURCE_SHA256:
        fail("The user handwriting source image hash changed", errors)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("font_version") != EXPECTED_VERSION:
        fail(f"Manifest version is not {EXPECTED_VERSION}", errors)
    if manifest.get("source", {}).get("sha256") != EXPECTED_SOURCE_SHA256:
        fail("Manifest source-image hash is incorrect", errors)
    records = {item["character"]: item for item in manifest.get("glyphs", [])}
    if set(records) != set(SVG_TEMPLATE_SOURCE_CHARACTERS):
        fail("Manifest source-character set differs from the SVG loader", errors)
    for character, record in records.items():
        path = SVG_DIR / record["file"]
        if not path.is_file():
            fail(f"Missing SVG for {character}: {path}", errors)
        elif sha256(path) != record["sha256"]:
            fail(f"SVG hash differs from manifest for {character}", errors)

    font = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        cmap = font.getBestCmap()
        version_names = {
            record.toUnicode()
            for record in font["name"].names
            if record.nameID == 5
        }
        if not any(EXPECTED_VERSION in value for value in version_names):
            fail(f"Built font name table does not report Version {EXPECTED_VERSION}", errors)

        centers: list[float] = []
        for character in sorted(SVG_TEMPLATE_CHARACTERS, key=ord):
            glyph_name = cmap.get(ord(character))
            if not glyph_name:
                fail(f"Built font is missing U+{ord(character):04X} {character}", errors)
                continue
            actual = font["glyf"][glyph_name]
            expected = build_svg_template_glyph(character, KANA_VERTICAL_SHIFT)
            if actual.isComposite():
                fail(f"SVG-template glyph {glyph_name} unexpectedly became composite", errors)
                continue
            if glyph_signature(actual, font["glyf"]) != glyph_signature(expected, {}):
                fail(f"Built outline differs from reviewed SVG template for {character} ({glyph_name})", errors)
            actual.recalcBounds(font["glyf"])
            bounds = (actual.xMin, actual.yMin, actual.xMax, actual.yMax)
            if not (-80 <= bounds[0] < bounds[2] <= 1040):
                fail(f"Unsafe horizontal bounds for {character}: {bounds}", errors)
            if not (font["hhea"].descent < bounds[1] < bounds[3] < font["hhea"].ascent):
                fail(f"Unsafe vertical bounds for {character}: {bounds}", errors)
            advance = font["hmtx"].metrics[glyph_name][0]
            if advance != KANA_ADVANCE:
                fail(f"Unexpected advance for {character}: {advance}", errors)
            if character in SVG_TEMPLATE_SOURCE_CHARACTERS:
                centers.append((bounds[1] + bounds[3]) / 2)

        if len(centers) == len(SVG_TEMPLATE_SOURCE_CHARACTERS):
            center = median(centers)
            if not 285 <= center <= 370:
                fail(f"SVG Hiragana median optical center is out of reviewed range: {center}", errors)

        # Ensure every declared small variant really derives from a present SVG base.
        for small, base in SVG_TEMPLATE_SMALL_MAP.items():
            if base not in SVG_TEMPLATE_SOURCE_CHARACTERS or ord(small) not in cmap:
                fail(f"Small-kana derivation is incomplete: {small} <- {base}", errors)
    finally:
        font.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"User-handwriting SVG verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("PASS: source image and all 43 SVG hashes match the reviewed manifest")
    print("PASS: 43 source Hiragana and 11 small forms exactly match deterministic SVG builds")
    print("PASS: advances, bounds, font version, and median optical center are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
