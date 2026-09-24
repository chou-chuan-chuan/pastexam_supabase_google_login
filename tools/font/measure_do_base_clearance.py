#!/usr/bin/env python3
"""Build and measure scoped U+3069 voiced-base candidates."""
from __future__ import annotations

from io import BytesIO
import hashlib
from pathlib import Path
import subprocess

import numpy as np
from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from japanese.build_kana import (
    DO_BASE_GLYPH, KANA_ADVANCE, append_do_base_selection,
    append_mark_positioning, composite, install,
)
from measure_de_dakuten_clearance import (
    contour_distance, segments, vertical_intersections,
)
from verify_supplement_font import bounds, mark_to_base_anchors, outlines_intersect


ROOT = Path(__file__).resolve().parents[2]
FONT_REL = Path("assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf")
TTF = ROOT / FONT_REL
WOFF2 = TTF.with_suffix(".woff2")
REPORT = ROOT / "tools/font/reports/do-base-clearance.json"
PROOF = ROOT / "tools/font/proofs/quanfangwei-do-base-clearance.png"
BASE_MAIN = "2b9472342505f676146200b6fb02209a4b497c1e"
BASE_TTF_SHA256 = "88dd082bba1c3bdd32edc7799137faba2e6f360dea6813d2c3b3350a1dcc96c0"
BASE_WOFF2_SHA256 = "dc337b159a623f20c6213d9906a3065f6df3f56ad198986282cf6fbe3153b1d2"
CANDIDATE_SCALES = (0.94, 0.96, 0.98)
FINAL_SCALE = 0.94


def baseline_bytes(path: Path = FONT_REL) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE_MAIN}:{path}"], cwd=ROOT)


def baseline_hashes() -> None:
    assert hashlib.sha256(baseline_bytes()).hexdigest() == BASE_TTF_SHA256
    assert hashlib.sha256(baseline_bytes(FONT_REL.with_suffix(".woff2"))).hexdigest() == BASE_WOFF2_SHA256


def derived_glyph(font: TTFont, scale: float):
    x0, y0, x1, _ = bounds(font, "uni3068")
    center_x = (x0 + x1) / 2
    transform = Transform(scale, 0, 0, scale, center_x * (1 - scale), y0 * (1 - scale))
    pen = TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()["uni3068"].draw(TransformPen(pen, transform))
    return pen.glyph(), transform


def candidate_font(scale: float) -> TTFont:
    """Extend immutable 1.028 with exactly the proposed scoped construction."""
    font = TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False)
    glyph, _ = derived_glyph(font, scale)
    install(font, DO_BASE_GLYPH, glyph, KANA_ADVANCE, "uni3068")
    base_anchor, mark_anchor, _ = mark_to_base_anchors(font, "uni3099", "uni3068")
    delta = (base_anchor[0] - mark_anchor[0], base_anchor[1] - mark_anchor[1])
    install(font, "uni3069", composite(font, DO_BASE_GLYPH, "uni3099", *delta), KANA_ADVANCE, "uni3068")
    append_mark_positioning(font, {DO_BASE_GLYPH: base_anchor})
    append_do_base_selection(font)
    return font


def measure(font: TTFont, base_name: str = DO_BASE_GLYPH) -> dict:
    base_anchor, mark_anchor, _ = mark_to_base_anchors(font, "uni3099", base_name)
    delta = (base_anchor[0] - mark_anchor[0], base_anchor[1] - mark_anchor[1])
    base_bounds = bounds(font, base_name)
    mark_bounds = bounds(font, "uni3099")
    placed = tuple(mark_bounds[i] + delta[i % 2] for i in range(4))
    base_segments = segments(font, base_name)
    mark_segments = segments(font, "uni3099", delta)
    distance, base_point, mark_point = contour_distance(base_segments, mark_segments)
    intersects = outlines_intersect(font, base_name, "uni3099", delta)
    lo, hi = max(base_bounds[0], placed[0]), min(base_bounds[2], placed[2])
    vertical = []
    if lo < hi:
        for x in np.linspace(lo, hi, max(2, int((hi - lo) / .05) + 1)):
            base_y = vertical_intersections(base_segments, x)
            mark_y = vertical_intersections(mark_segments, x)
            if len(base_y) and len(mark_y):
                vertical.append((float(min(mark_y) - max(base_y)), float(x), float(max(base_y)), float(min(mark_y))))
    return {
        "body_bounds": list(base_bounds),
        "dakuten_bounds": list(placed),
        "body_anchor": list(base_anchor),
        "dakuten_anchor": list(mark_anchor),
        "dakuten_delta": list(delta),
        "minimum_clearance": 0.0 if intersects else distance,
        "intersects": intersects,
        "closest_body_point": base_point.tolist(),
        "closest_dakuten_point": mark_point.tolist(),
        "x_overlap": [lo, hi],
        "minimum_vertical_gap": list(min(vertical)) if vertical else None,
        "bottom_alignment_difference": base_bounds[1] - bounds(font, "uni3068")[1],
    }
