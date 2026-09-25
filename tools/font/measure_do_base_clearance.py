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

from japanese.build_kana import DO_BASE_GLYPH, KANA_ADVANCE, composite, install
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
BASE_MAIN = "b2e1d1613eedfa432cdd4580e813771932d8fa54"
BASE_TTF_SHA256 = "056f7e3c12891229993bd80d13da650ce95f429d27ff1545c3c5504d3a1cc702"
BASE_WOFF2_SHA256 = "f1293e7e05f0003e47a3e521d54b8ad32e036d74f1c1f2cb2cf6664073e3f165"
CANDIDATES = ((0.99, 0.92), (0.98, 0.92), (0.97, 0.92))
FINAL_TO_SCALE = 0.98
FINAL_DO_SCALE = 0.92


def baseline_bytes(path: Path = FONT_REL) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE_MAIN}:{path.as_posix()}"], cwd=ROOT)


def baseline_hashes() -> None:
    assert hashlib.sha256(baseline_bytes()).hexdigest() == BASE_TTF_SHA256
    assert hashlib.sha256(baseline_bytes(FONT_REL.with_suffix(".woff2"))).hexdigest() == BASE_WOFF2_SHA256


def derived_glyph(font: TTFont, source_name: str, scale: float):
    x0, y0, x1, _ = bounds(font, source_name)
    center_x = (x0 + x1) / 2
    transform = Transform(scale, 0, 0, scale, center_x * (1 - scale), y0 * (1 - scale))
    pen = TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()[source_name].draw(TransformPen(pen, transform))
    return pen.glyph(), transform


def candidate_font(to_scale: float, do_scale: float) -> TTFont:
    """Apply a standalone と scale and a second voiced-only scale to 1.029."""
    font = TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False)
    to_glyph, _ = derived_glyph(font, "uni3068", to_scale)
    install(font, "uni3068", to_glyph, KANA_ADVANCE, "uni3068")
    do_glyph, _ = derived_glyph(font, "uni3068", do_scale)
    install(font, DO_BASE_GLYPH, do_glyph, KANA_ADVANCE, "uni3068")
    base_anchor, mark_anchor, _ = mark_to_base_anchors(font, "uni3099", "uni3068")
    delta = (base_anchor[0] - mark_anchor[0], base_anchor[1] - mark_anchor[1])
    install(font, "uni3069", composite(font, DO_BASE_GLYPH, "uni3099", *delta), KANA_ADVANCE, "uni3068")
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
