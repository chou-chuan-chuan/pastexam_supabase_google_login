#!/usr/bin/env python3
"""Verify topology-preserving Japanese stroke-weight harmonization."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
import tempfile
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from audit_japanese_weight import (
    JAPANESE_MARKS,
    KATAKANA,
    LARGE_HIRAGANA,
    PROJECT_DERIVED_HAN,
    SIZES,
    SMALL_HIRAGANA,
    SOURCE_FONT,
    SOURCE_HAN,
    SOURCE_SHA256,
    dehinted_source,
    group_measurement,
    sha256,
)
from kana_sources.full_data import (
    DAKUTEN_WEIGHT_FACTOR,
    HANDAKUTEN_WEIGHT_FACTOR,
    KANA_STROKES,
    KATAKANA_WEIGHT_FACTOR,
    LARGE_HIRAGANA_WEIGHT_FACTOR,
    LONG_SOUND_MARK_WEIGHT_FACTOR,
)
from kana_sources.user_handwriting_optical import (
    HIRAGANA_OPTICAL_TRANSFORMS,
    USER_HANDWRITING_OPTICALLY_NORMALIZED,
)
from kana_sources.user_handwriting_refined import (
    MODERN_HIRAGANA_ORDER,
    USER_HANDWRITING_REFINED,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"
EXPECTED_POINT_HASH = "c21b34ac3f8ccbbac3c3065619e0c5f9810049e43dfb524cfcbce68d0cf0d1ff"
EXPECTED_TOPOLOGY_HASH = "12628b5acb30b083570d79435880d4dae45937f506198ef3e1723a7e7b380538"
EXPECTED_SOURCE_STROKE_HASH = "864dd149905722d695d1f969c45ac12c4d78829499d08244ecfbe015e5fb3161"
EXPECTED_OPTICAL_HASH = "9e4cc1aef97f6f380f8cbf1a98e3fcc244408df97f24ae2d52b80e80e9f76829"
EXPECTED_STROKE_COUNT = 310
EXPECTED_POINT_COUNT = 1261
EXPECTED_FACTORS = {
    "large_hiragana": 1.10,
    "katakana": 1.14,
    "dakuten": 1.10,
    "handakuten": 1.20,
    "long_sound_mark": 1.10,
}


def digest(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def ratio(group: dict[str, dict], source: dict[str, dict], key: str) -> float:
    return statistics.median(group[str(size)][key] / source[str(size)][key] for size in SIZES)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(sha256(SOURCE_FONT) == SOURCE_SHA256, "Official source TTF hash changed")
    require(TTF_PATH.is_file() and WOFF2_PATH.is_file(), "Built TTF/WOFF2 is missing")

    points = [(character, [list(stroke.points) for stroke in USER_HANDWRITING_REFINED[character]])
              for character in MODERN_HIRAGANA_ORDER]
    topology = [(character, [len(stroke.points) for stroke in USER_HANDWRITING_REFINED[character]])
                for character in MODERN_HIRAGANA_ORDER]
    source_strokes = [
        (character, [(stroke.points, stroke.width, stroke.start_width, stroke.end_width, stroke.cap)
                     for stroke in USER_HANDWRITING_REFINED[character]])
        for character in MODERN_HIRAGANA_ORDER
    ]
    optical = [(character, vars(HIRAGANA_OPTICAL_TRANSFORMS[character]))
               for character in MODERN_HIRAGANA_ORDER]
    require(digest(points) == EXPECTED_POINT_HASH, "Accepted 46-Hiragana point coordinates changed")
    require(digest(topology) == EXPECTED_TOPOLOGY_HASH, "Accepted 46-Hiragana topology hash changed")
    require(digest(source_strokes) == EXPECTED_SOURCE_STROKE_HASH,
            "USER_HANDWRITING_REFINED pressure/topology source changed instead of using the outer layer")
    require(digest(optical) == EXPECTED_OPTICAL_HASH, "Current per-glyph optical transforms changed or reset")
    require(sum(len(USER_HANDWRITING_REFINED[c]) for c in MODERN_HIRAGANA_ORDER) == EXPECTED_STROKE_COUNT,
            "Accepted 46-Hiragana stroke count changed")
    require(sum(len(stroke.points) for c in MODERN_HIRAGANA_ORDER for stroke in USER_HANDWRITING_REFINED[c]) == EXPECTED_POINT_COUNT,
            "Accepted 46-Hiragana point count changed")

    actual_factors = {
        "large_hiragana": LARGE_HIRAGANA_WEIGHT_FACTOR,
        "katakana": KATAKANA_WEIGHT_FACTOR,
        "dakuten": DAKUTEN_WEIGHT_FACTOR,
        "handakuten": HANDAKUTEN_WEIGHT_FACTOR,
        "long_sound_mark": LONG_SOUND_MARK_WEIGHT_FACTOR,
    }
    require(actual_factors == EXPECTED_FACTORS, f"Reviewed weight factors changed: {actual_factors}")
    for character in MODERN_HIRAGANA_ORDER:
        source = USER_HANDWRITING_OPTICALLY_NORMALIZED[character]
        normalized = KANA_STROKES[character]
        require(len(normalized) == len(source), f"Stroke count changed in pressure layer for {character}")
        for before, after in zip(source, normalized):
            require(after.points == before.points, f"Pressure layer moved points for {character}")
            require(math.isclose(after.width, before.width * LARGE_HIRAGANA_WEIGHT_FACTOR),
                    f"Main width factor differs for {character}")
            if before.start_width is not None:
                require(math.isclose(after.start_width, before.start_width * LARGE_HIRAGANA_WEIGHT_FACTOR),
                        f"Start-width taper ratio differs for {character}")
            if before.end_width is not None:
                require(math.isclose(after.end_width, before.end_width * LARGE_HIRAGANA_WEIGHT_FACTOR),
                        f"End-width taper ratio differs for {character}")

    source_font = TTFont(SOURCE_FONT, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        scmap, tcmap, wcmap = source_font.getBestCmap(), ttf.getBestCmap(), woff2.getBestCmap()
        require(tcmap == wcmap, "TTF/WOFF2 cmap differs")
        reviewed = LARGE_HIRAGANA + SMALL_HIRAGANA + KATAKANA + JAPANESE_MARKS + PROJECT_DERIVED_HAN
        for character in reviewed:
            name = tcmap.get(ord(character))
            require(name is not None, f"Built font is missing {character} U+{ord(character):04X}")
            if name is None:
                continue
            tb, wb = bounds(ttf, name), bounds(woff2, name)
            require(tb == wb, f"TTF/WOFF2 bounds differ for {character}: {tb} != {wb}")
            require(ttf["hmtx"].metrics[name] == woff2["hmtx"].metrics[name],
                    f"TTF/WOFF2 metrics differ for {character}")
            if tb:
                require(ttf["hhea"].descent < tb[1] < tb[3] < ttf["hhea"].ascent,
                        f"Vertical clipping for {character}: {tb}")
                advance = ttf["hmtx"].metrics[name][0]
                if advance > 0:
                    require(-80 <= tb[0] and tb[2] <= max(1040, advance + 80),
                            f"Horizontal clipping for {character}: advance={advance}, bounds={tb}")

        source_order = source_font.getGlyphOrder()
        require(ttf.getGlyphOrder()[:len(source_order)] == source_order,
                "Original source glyph set/order is no longer the derived-font prefix")
    finally:
        source_font.close()
        ttf.close()
        woff2.close()

    with tempfile.TemporaryDirectory(prefix="qfw-weight-verify-") as temp_dir:
        raster_source = Path(temp_dir) / "ChenYuluoyan-dehinted.ttf"
        dehinted_source(raster_source)
        # Compare the complete compiled original-glyph prefix against the same
        # deterministic dehinting used by the builder. This covers every source
        # Chinese drawing in one binary gate without expanding thousands of
        # outlines through a drawing pen.
        dehinted = TTFont(raster_source, recalcTimestamp=False)
        derived = TTFont(TTF_PATH, recalcTimestamp=False)
        try:
            prefix_end = derived["loca"].locations[len(dehinted.getGlyphOrder())]
            source_end = dehinted["loca"].locations[-1]
            require(source_end == prefix_end, "Original glyf prefix length changed")
            require(dehinted.reader["glyf"][:source_end] == derived.reader["glyf"][:prefix_end],
                    "One or more source glyph drawings changed in the derived TTF")
        finally:
            dehinted.close()
            derived.close()
        source_measurements = {str(size): group_measurement(raster_source, SOURCE_HAN, size) for size in SIZES}
        measured_groups = {
            "large_hiragana": {str(size): group_measurement(TTF_PATH, LARGE_HIRAGANA, size) for size in SIZES},
            "small_hiragana": {str(size): group_measurement(TTF_PATH, SMALL_HIRAGANA, size) for size in SIZES},
            "katakana": {str(size): group_measurement(TTF_PATH, KATAKANA, size) for size in SIZES},
            "japanese_marks": {str(size): group_measurement(TTF_PATH, JAPANESE_MARKS, size) for size in SIZES},
            "project_derived_han": {str(size): group_measurement(TTF_PATH, PROJECT_DERIVED_HAN, size) for size in SIZES},
        }
        for name, measurements in measured_groups.items():
            effective_ratio = ratio(measurements, source_measurements, "effective_stroke_px")
            require(0.90 <= effective_ratio <= 1.10,
                    f"{name} effective stroke ratio is outside source ±10%: {effective_ratio:.4f}")
        small_ratio = ratio(measured_groups["small_hiragana"], source_measurements, "effective_stroke_px")
        large_ratio = ratio(measured_groups["large_hiragana"], source_measurements, "effective_stroke_px")
        require(small_ratio >= large_ratio - 0.10,
                f"Small Hiragana becomes a separate thin weight: small={small_ratio:.4f}, large={large_ratio:.4f}")

    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        print(f"Japanese weight verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("PASS: 46-Hiragana point coordinates, stroke counts, topology hash, and optical transforms are unchanged")
    print("PASS: pressure multipliers preserve all width taper ratios")
    print("PASS: official source hash and all source CJK drawings are unchanged")
    print("PASS: TTF/WOFF2 cmap, metrics, and bounds agree without clipping")
    print("PASS: large/small Hiragana, Katakana, marks, and derived Han remain within source effective-weight range")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
