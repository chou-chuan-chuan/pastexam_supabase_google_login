"""Trim protruding stroke ends only at the reviewed マ and ス junctions."""
import pathops

from japanese.stroke_engine import stroke_path, path_to_glyph, translate_strokes
from japanese.build_kana import KANA_VERTICAL_SHIFT_1_026, apply_bottom_alignment
from kana_sources.full_data import KANA_STROKES

# Character: (trimmed stroke, supporting stroke, support start/end point).
JUNCTION_TRIMS = {'マ': (1, 2, 0, -1), 'ス': (2, 1, 2, 3)}


def refined_junction_glyph(character):
    """Clip the protruding pen end where the unchanged supporting ink hides it.

    Keep all accepted center-lines and pressure values. The clipping line follows
    two existing support points; only the named stroke is clipped. The other
    strokes are unioned back unchanged, burying the cut inside existing ink.
    """
    strokes = translate_strokes(KANA_STROKES[character], dy=KANA_VERTICAL_SHIFT_1_026)
    trimmed, support, first, last = JUNCTION_TRIMS[character]
    start, end = strokes[support].points[first], strokes[support].points[last]
    dx, dy = end[0] - start[0], end[1] - start[1]
    nx, ny = -dy, dx
    # A half-plane polygon extending well beyond the 1024-unit em.
    points = [(start[0]-20*dx, start[1]-20*dy),
              (end[0]+20*dx, end[1]+20*dy),
              (end[0]+20*dx+20*nx, end[1]+20*dy+20*ny),
              (start[0]-20*dx+20*nx, start[1]-20*dy+20*ny)]
    clip = pathops.Path()
    pen = clip.getPen()
    pen.moveTo(points[0])
    for point in points[1:]:
        pen.lineTo(point)
    pen.closePath()
    paths = [stroke_path(stroke) for stroke in strokes]
    paths[trimmed] = pathops.op(paths[trimmed], clip, pathops.PathOp.INTERSECTION)
    ink = paths[0]
    for part in paths[1:]:
        ink = pathops.op(ink, part, pathops.PathOp.UNION)
    return apply_bottom_alignment(path_to_glyph(pathops.simplify(ink)))


def refine_katakana_junctions(font):
    for character in JUNCTION_TRIMS:
        name = font.getBestCmap()[ord(character)]
        before = font['glyf'][name]
        before.recalcBounds(font['glyf'])
        glyph = refined_junction_glyph(character)
        glyph.recalcBounds(font['glyf'])
        assert (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax) == (before.xMin, before.yMin, before.xMax, before.yMax)
        assert glyph.numberOfContours == before.numberOfContours == 1
        assert font['hmtx'][name][0] == 960
        font['glyf'][name] = glyph
