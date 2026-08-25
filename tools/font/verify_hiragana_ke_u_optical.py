#!/usr/bin/env python3
"""Verify the narrow Version 1.016 け/う/こ/わ/ゎ refinement."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from kana_sources.full_data import KANA_STROKES
from kana_sources.user_handwriting_optical import (
    HIRAGANA_OPTICAL_TRANSFORMS,
    USER_HANDWRITING_OPTICALLY_NORMALIZED,
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
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
ALL_SOURCE_SHA256 = "f915a53246260eceeb2e34ccf76279807bab5866fcefcabffca39f38d47e387e"
OTHER_45_SOURCE_SHA256 = "bd73f08a671c8ae117e7878d5eae7edfac9fec7c95c9d67502101b3eebaf64f9"
WA_SOURCE_SHA256 = "486652c5d5e62fbbb3b74623810907abf9a1c8bafe3a74616251cb6d1b685913"
OTHER_TRANSFORM_SHA256 = "1888c79a1a1f0502e3bfdbf161bb6d950a6ed5dc9a761f629185205369337b95"
SOURCE_GATES = {
    "け": ("f3410a8a866046bb7d047f1dec2c045e773d0f37d1cb380c0935bddac4c27969", 7, 25),
    "う": ("432fedfedcca516996088b46771cc8882364d1dc4e7d421523203e4394a71204", 2, 10),
    "こ": ("89ed94af8fb7665b4c24cc46b7da00ea50bf0db57eb62ff0ab259e4a00644d7b", 4, 19),
}
EXPECTED_TRANSFORMS = {
    "け": (1.06, 1.0, 28.0, -26.0),
    "う": (1.12, 1.08, 0.0, -20.0),
    "こ": (1.0, 1.0, 28.0, 0.0),
}


def stroke_bounds(strokes) -> tuple[float, float, float, float]:
    points = [point for stroke in strokes for point in stroke.points]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def center(bounds) -> tuple[float, float]:
    return (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2


def span(bounds) -> tuple[float, float]:
    return bounds[2] - bounds[0], bounds[3] - bounds[1]


def font_bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return tuple(round(value) for value in pen.bounds)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    expected = set(MODERN_HIRAGANA_ORDER)
    require(len(MODERN_HIRAGANA_ORDER) == 46 and set(USER_HANDWRITING_REFINED) == expected,
            "USER_HANDWRITING_REFINED is not the authoritative complete 46-Hiragana set")
    require(hashlib.sha256(repr(USER_HANDWRITING_REFINED).encode("utf-8")).hexdigest() == ALL_SOURCE_SHA256,
            "Authoritative 46-Hiragana source coordinates/topology changed")
    other_sources = tuple(
        (character, USER_HANDWRITING_REFINED[character])
        for character in MODERN_HIRAGANA_ORDER if character != "わ"
    )
    require(hashlib.sha256(repr(other_sources).encode("utf-8")).hexdigest() == OTHER_45_SOURCE_SHA256,
            "A source other than the explicitly rewritten わ changed")
    wa_source = USER_HANDWRITING_REFINED["わ"]
    require(hashlib.sha256(repr(wa_source).encode("utf-8")).hexdigest() == WA_SOURCE_SHA256,
            "The reviewed わ source changed")
    require(len(wa_source) == 2 and sum(len(stroke.points) for stroke in wa_source) == 26,
            "The reviewed わ must retain its two-stroke, 26-point topology")
    require(set(USER_HANDWRITING_OPTICALLY_NORMALIZED) == expected,
            "Optical layer does not cover the authoritative 46-Hiragana set")

    other_signature = tuple(
        (character, HIRAGANA_OPTICAL_TRANSFORMS[character])
        for character in MODERN_HIRAGANA_ORDER
        if character not in SOURCE_GATES
    )
    require(hashlib.sha256(repr(other_signature).encode("utf-8")).hexdigest() == OTHER_TRANSFORM_SHA256,
            "A Hiragana transform other than け/う/こ changed")

    for character in MODERN_HIRAGANA_ORDER:
        source = USER_HANDWRITING_REFINED[character]
        normalized = USER_HANDWRITING_OPTICALLY_NORMALIZED[character]
        require(len(source) == len(normalized), f"Stroke count changed for {character}")
        require([len(item.points) for item in source] == [len(item.points) for item in normalized],
                f"Point topology changed for {character}")

    for character, (expected_hash, expected_strokes, expected_points) in SOURCE_GATES.items():
        source = USER_HANDWRITING_REFINED[character]
        require(hashlib.sha256(repr(source).encode("utf-8")).hexdigest() == expected_hash,
                f"Authoritative source hash changed for {character}")
        require(len(source) == expected_strokes and sum(len(item.points) for item in source) == expected_points,
                f"Source stroke/point count changed for {character}")
        transform = HIRAGANA_OPTICAL_TRANSFORMS[character]
        require((transform.scale_x or transform.scale, transform.scale_y or transform.scale,
                 transform.dx, transform.dy) == EXPECTED_TRANSFORMS[character],
                f"Unexpected optical transform for {character}: {transform}")

    ke_before = stroke_bounds(USER_HANDWRITING_REFINED["け"])
    ke_after = stroke_bounds(USER_HANDWRITING_OPTICALLY_NORMALIZED["け"])
    ke_before_span = span(ke_before)
    ke_after_span = span(ke_after)
    require(abs((ke_after_span[0] / ke_before_span[0]) - 1.06) <= 0.000001,
            "け horizontal point span does not match scale_x 1.06")
    require(abs((ke_after_span[1] / ke_before_span[1]) - 1.0) <= 0.000001,
            "け vertical point span changed")
    require(tuple(round(a - b, 6) for a, b in zip(center(ke_after), center(ke_before))) == (28.0, -26.0),
            "け center did not move exactly +28 x/-26 y")

    u_before = stroke_bounds(USER_HANDWRITING_REFINED["う"])
    u_after = stroke_bounds(USER_HANDWRITING_OPTICALLY_NORMALIZED["う"])
    u_before_span = span(u_before)
    u_after_span = span(u_after)
    require(abs((u_after_span[0] / u_before_span[0]) - 1.12) <= 0.000001,
            "う horizontal point span does not match scale_x 1.12")
    require(abs((u_after_span[1] / u_before_span[1]) - 1.08) <= 0.000001,
            "う vertical point span does not match scale_y 1.08")
    require(abs(center(u_after)[0] - center(u_before)[0]) <= 0.000001,
            "う horizontal optical center shifted during scaling")
    require(abs((center(u_after)[1] - center(u_before)[1]) - (-20.0)) <= 0.000001,
            "う center did not receive the reviewed 20-unit downward shift")

    ko_before = stroke_bounds(USER_HANDWRITING_REFINED["こ"])
    ko_after = stroke_bounds(USER_HANDWRITING_OPTICALLY_NORMALIZED["こ"])
    require(span(ko_before) == span(ko_after), "こ size changed instead of translation-only correction")
    require(tuple(round(a - b, 6) for a, b in zip(center(ko_after), center(ko_before))) == (28.0, 0.0),
            "こ center did not move exactly +28 x")

    for small, large in (("ぅ", "う"), ("ゖ", "け"), ("ゎ", "わ")):
        require(len(KANA_STROKES[small]) == len(KANA_STROKES[large]),
                f"Small-kana derivation changed stroke count for {small} <- {large}")
        require([len(item.points) for item in KANA_STROKES[small]] ==
                [len(item.points) for item in KANA_STROKES[large]],
                f"Small-kana derivation changed point topology for {small} <- {large}")

    wa_bounds = stroke_bounds(USER_HANDWRITING_OPTICALLY_NORMALIZED["わ"])
    small_wa_bounds = stroke_bounds(KANA_STROKES["ゎ"])
    expected_small_wa_center = (
        480 + (center(wa_bounds)[0] - 480) * 0.72 + 14,
        500 + (center(wa_bounds)[1] - 500) * 0.72 - 26,
    )
    require(all(abs(actual - expected) <= 0.000001 for actual, expected in
                zip(center(small_wa_bounds), expected_small_wa_center)),
            "ゎ did not receive the reviewed +14 x/-14 y additional optical shift")

    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        ttf_cmap = ttf.getBestCmap()
        woff2_cmap = woff2.getBestCmap()
        for character in ("け", "う", "こ", "ぅ", "ゖ", "ゎ"):
            codepoint = ord(character)
            require(codepoint in ttf_cmap and codepoint in woff2_cmap,
                    f"Built fonts are missing {character} U+{codepoint:04X}")
            if codepoint not in ttf_cmap or codepoint not in woff2_cmap:
                continue
            ttf_name = ttf_cmap[codepoint]
            woff2_name = woff2_cmap[codepoint]
            ttf_metric = ttf["hmtx"][ttf_name]
            woff2_metric = woff2["hmtx"][woff2_name]
            ttf_bounds = font_bounds(ttf, ttf_name)
            woff2_bounds = font_bounds(woff2, woff2_name)
            require(ttf_metric == woff2_metric and ttf_bounds == woff2_bounds,
                    f"TTF/WOFF2 metrics or bounds differ for {character}")
            require(ttf_metric[0] == 960, f"Unexpected advance for {character}: {ttf_metric[0]}")
            require(0 <= ttf_bounds[0] < ttf_bounds[2] <= ttf_metric[0],
                    f"Horizontal clipping or unsafe bearings for {character}: {ttf_bounds}")
            require(ttf["hhea"].descent < ttf_bounds[1] < ttf_bounds[3] < ttf["hhea"].ascent,
                    f"Vertical clipping for {character}: {ttf_bounds}")
    finally:
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"け/う/こ optical verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("PASS: け/う/こ authoritative source hashes, strokes, and point topology are unchanged")
    print("PASS: only け/う/こ optical scale/translation changed among 46 Hiragana")
    print("PASS: ぅ/ゖ/ゎ derivation remains topology-preserving; ゎ has its reviewed right/down shift")
    print("PASS: TTF/WOFF2 metrics agree; advances, bearings, and bounds are safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
