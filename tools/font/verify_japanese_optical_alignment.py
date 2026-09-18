#!/usr/bin/env python3
"""Verify the source-preserving Japanese optical-alignment refinements."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from japanese.user_japanese_overrides import (
    OPTICAL_ALIGNMENT_SUFFIX,
    SHARED_HAN_OPTICAL_TRANSFORMS,
)
from kana_sources.user_handwriting_optical import (
    HIRAGANA_OPTICAL_TRANSFORMS,
    OpticalTransform,
    USER_HANDWRITING_OPTICALLY_NORMALIZED,
    transform_strokes,
)
from kana_sources.user_handwriting_refined import (
    MODERN_HIRAGANA_ORDER,
    USER_HANDWRITING_REFINED,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
EXPECTED_HAN_TRANSFORMS = {
    "壁": (1.00, 1.00, 0.0, 97.0, 0.0),
    "堅": (1.00, 1.00, 0.0, 55.0, 0.0),
    "奥": (0.921976, 0.855348, 9.0, 34.5, 4.0),
    "容": (1.00, 1.00, 19.45, 35.0, 0.0),
    "変": (0.80, 0.80, 19.25, 35.0, 8.0),
    "恋": (0.98, 0.98, 17.5, 35.0, 0.0),
    "哀": (0.93, 0.93, 15.5, 36.0, 0.0),
    "奧": (0.94, 0.94, 19.0, 34.5, 0.0),
    "優": (0.90, 0.90, 19.5, 35.0, 0.0),
    "寄": (0.92, 0.92, 18.5, 36.0, 0.0),
}


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def drawing(font: TTFont, glyph_name: str) -> tuple:
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return tuple(pen.value)


def stroke_bounds(strokes) -> tuple[float, float, float, float]:
    points = [point for stroke in strokes for point in stroke.points]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def center(glyph_bounds) -> tuple[float, float]:
    x_min, y_min, x_max, y_max = glyph_bounds
    return (x_min + x_max) / 2, (y_min + y_max) / 2


def span(glyph_bounds) -> tuple[float, float]:
    x_min, y_min, x_max, y_max = glyph_bounds
    return x_max - x_min, y_max - y_min


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    expected_hiragana = set(MODERN_HIRAGANA_ORDER)
    require(set(USER_HANDWRITING_REFINED) == expected_hiragana,
            "USER_HANDWRITING_REFINED no longer contains exactly 46 authoritative Hiragana")
    require(set(USER_HANDWRITING_OPTICALLY_NORMALIZED) == expected_hiragana,
            "Optical layer no longer covers the same 46 authoritative Hiragana")
    for character in MODERN_HIRAGANA_ORDER:
        source = USER_HANDWRITING_REFINED[character]
        normalized = USER_HANDWRITING_OPTICALLY_NORMALIZED[character]
        require(len(source) == len(normalized),
                f"Optical normalization changed stroke count for {character}")
        require([len(stroke.points) for stroke in source] ==
                [len(stroke.points) for stroke in normalized],
                f"Optical normalization changed point topology for {character}")

    from verify_hiragana_master_v2 import verify_sources
    verify_sources("す")
    su_transform=HIRAGANA_OPTICAL_TRANSFORMS["す"]
    require(su_transform.scale_x is None and su_transform.scale_y is None,
            "Master-v2 su must preserve its handwritten proportions with uniform metric normalization")

    require(set(SHARED_HAN_OPTICAL_TRANSFORMS) == set(EXPECTED_HAN_TRANSFORMS),
            "Han optical transform set differs from the ten reviewed per-glyph records")
    for character, expected in EXPECTED_HAN_TRANSFORMS.items():
        transform = SHARED_HAN_OPTICAL_TRANSFORMS[character]
        require((transform.scale_x, transform.scale_y, transform.dx, transform.dy,
                 transform.embolden) == expected,
                f"Unexpected transform record for {character}: {transform}")
        if character == "奥":
            require(transform.scale_x != transform.scale_y,
                    "奥 must use the approved independent X/Y browser-optical fit")
        else:
            require(transform.scale_x == transform.scale_y,
                    f"{character} must retain proportional source geometry")
    source = TTFont(SOURCE_PATH, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        source_cmap = source.getBestCmap()
        ttf_cmap = ttf.getBestCmap()
        woff2_cmap = woff2.getBestCmap()
        require(ttf_cmap == woff2_cmap, "TTF and WOFF2 cmap differ")

        for character in EXPECTED_HAN_TRANSFORMS:
            codepoint = ord(character)
            source_name = source_cmap.get(codepoint)
            target_name = ttf_cmap.get(codepoint)
            require(source_name is not None, f"Source font is missing {character} U+{codepoint:04X}")
            require(target_name == f"{source_name}{OPTICAL_ALIGNMENT_SUFFIX}",
                    f"{character} is not mapped to its recorded derived optical glyph")
            if source_name is None or target_name is None:
                continue
            require(source_name in ttf.getGlyphOrder(),
                    f"Derived font removed source glyph {source_name}")
            require(drawing(source, source_name) == drawing(ttf, source_name),
                    f"Source drawing changed for {character} ({source_name})")
            ttf_bounds = bounds(ttf, target_name)
            woff2_bounds = bounds(woff2, target_name)
            require(ttf_bounds == woff2_bounds,
                    f"TTF/WOFF2 bounds differ for {character}: {ttf_bounds} vs {woff2_bounds}")
            require(ttf["hmtx"].metrics[target_name] == woff2["hmtx"].metrics[target_name],
                    f"TTF/WOFF2 horizontal metrics differ for {character}")
            source_advance = source["hmtx"].metrics[source_name][0]
            target_advance, target_lsb = ttf["hmtx"].metrics[target_name]
            recorded_advance = SHARED_HAN_OPTICAL_TRANSFORMS[character].advance
            expected_advance = recorded_advance if recorded_advance is not None else source_advance
            require(target_advance == expected_advance,
                    f"{character} advance changed unexpectedly: {source_advance} -> {target_advance}")
            if ttf_bounds:
                x_min, y_min, x_max, y_max = ttf_bounds
                glyf_x_min = ttf["glyf"][target_name].xMin
                require(target_lsb == glyf_x_min,
                        f"{character} lsb does not match glyf xMin: {target_lsb} vs {glyf_x_min}")
                require(abs(target_lsb - x_min) <= 3.0,
                        f"{character} lsb is too far from the quadratic ink bound: {target_lsb} vs {x_min}")
                require(0 <= x_min < x_max <= target_advance,
                        f"{character} clips or escapes its advance: {ttf_bounds}, advance={target_advance}")
                require(ttf["hhea"].descent < y_min < y_max < ttf["hhea"].ascent,
                        f"{character} vertical bounds are unsafe: {ttf_bounds}")
                target_center = center(ttf_bounds)
                if character in "壁堅":
                    source_bounds = bounds(source, source_name)
                    require((x_min, x_max) == (source_bounds[0], source_bounds[2]),
                            f"{character} vertical-only correction changed horizontal bounds")
                else:
                    require(abs(target_center[0] - target_advance / 2) <= 1.0,
                            f"{character} is not centered in its advance: center={target_center[0]}, advance={target_advance}")
                if character == "奥":
                    require(abs(target_center[1] - 354) <= 0.5,
                            f"奥 optical y center does not match U+5967 奧: {target_center[1]}")
                elif character == "壁":
                    require(target_center[1] == 417,
                            f"壁 optical y center does not match reviewed final placement: {target_center[1]}")
                elif character == "堅":
                    require(target_center[1] == 374.5,
                            f"堅 optical y center does not match reviewed final placement: {target_center[1]}")
                else:
                    require(352 <= target_center[1] <= 358,
                            f"{character} optical y center is outside the reviewed range: {target_center[1]}")

        # Regression gate for a codepoint explicitly outside this refinement.
        for character in "夕":
            source_name = source_cmap[ord(character)]
            require(ttf_cmap.get(ord(character)) == source_name,
                    f"{character} U+{ord(character):04X} cmap changed unexpectedly")
            require(drawing(source, source_name) == drawing(ttf, source_name),
                    f"{character} source drawing changed unexpectedly")
        legacy_expected = {
            "懐": (".qfwUser", (89, -63, 950, 763), 989),
            "々": (".qfwUser", (180, 70, 784, 704), 960),
        }
        for character, (suffix, expected_bounds, expected_advance) in legacy_expected.items():
            name = ttf_cmap.get(ord(character))
            require(name is not None and name.endswith(suffix),
                    f"Approved {character} mapping changed unexpectedly")
            if name:
                require(bounds(ttf, name) == expected_bounds,
                        f"Approved {character} bounds changed unexpectedly: {bounds(ttf, name)}")
                require(ttf["hmtx"].metrics[name][0] == expected_advance,
                        f"Approved {character} advance changed unexpectedly")
                require(bounds(ttf, name) == bounds(woff2, name),
                        f"TTF/WOFF2 bounds differ for approved {character}")
    finally:
        source.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        print(f"Japanese optical-alignment verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("PASS: す uses master-v2 source and reviewed uniform Japanese metric normalization")
    print("PASS: ten reviewed Han, including vertical-only 壁/堅, use recorded source-preserving transforms and safe metrics")
    print("PASS: TTF/WOFF2 agree; 夕 and approved 懐/々 remain unchanged")
    print("PASS: the optical layer preserves each current Hiragana source stroke/point topology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
