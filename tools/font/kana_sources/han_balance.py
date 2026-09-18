"""Version 1.026 uniform optical scale, downstream of accepted 1.025 shapes.

Factors come from references/kana-kanji-balance-metrics.json. The builder
never reads an external font or re-fits individual glyphs. Pressure scales
with geometry so caps, taper, loops and aspect ratios retain their design.
"""
from functools import lru_cache

from japanese.stroke_engine import Stroke, build_stroke_glyph

HIRAGANA_HAN_BALANCE_SCALE = 0.894078195335
KATAKANA_HAN_BALANCE_SCALE = 0.946843040146


def script_scale(character):
    return KATAKANA_HAN_BALANCE_SCALE if 0x30A0 <= ord(character) <= 0x30FF else HIRAGANA_HAN_BALANCE_SCALE


@lru_cache(maxsize=None)
def optical_center(strokes):
    """Stable accepted ink-box center in the center-line coordinate system."""
    glyph = build_stroke_glyph(strokes)
    glyph.recalcBounds({})
    return ((glyph.xMin + glyph.xMax) / 2, (glyph.yMin + glyph.yMax) / 2)


def uniform_scale(strokes, factor, center):
    cx, cy = center
    return tuple(Stroke(
        tuple((cx + (x-cx)*factor, cy + (y-cy)*factor) for x, y in s.points),
        s.width * factor,
        None if s.start_width is None else s.start_width * factor,
        None if s.end_width is None else s.end_width * factor,
        s.cap,
    ) for s in strokes)


def balance_strokes(character, strokes):
    return uniform_scale(strokes, script_scale(character), optical_center(strokes))
