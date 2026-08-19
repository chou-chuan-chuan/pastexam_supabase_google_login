"""Build Version 1.012 user-maintainer Japanese shared-codepoint overrides.

Two Han characters (懐 U+61D0 and 夕 U+5915) are rebuilt from the maintainer's
own handwriting center-lines.  気 U+6C17 and 付 U+4ED8 keep the source font's
original drawings, but are installed under distinct derived glyph names with
an optical vertical transform so the mixed sequence 気付け aligns better with
refined Hiragana.  Original source glyphs remain present and unmodified.
"""

from __future__ import annotations

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from japanese.stroke_engine import build_stroke_glyph
from kana_sources.user_kanji_refined import (
    ALIGNMENT_OVERRIDE_CHARACTERS,
    USER_KANJI_REFINED,
)


USER_OVERRIDE_SUFFIX = ".qfwUser"
ALIGN_OVERRIDE_SUFFIX = ".qfwJaAlign"
ALIGNMENT_REFERENCE = "け"
ALIGNMENT_TARGET_HEIGHT_FACTOR = 1.08
ALIGNMENT_SCALE_CLAMP = (0.82, 1.06)


def glyph_bounds(font: TTFont, glyph_name: str) -> tuple[float, float, float, float]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {glyph_name!r} has no bounds")
    return pen.bounds


def add_mapping(font: TTFont, codepoint: int, name: str) -> None:
    mapped = 0
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format != 14:
            table.cmap[codepoint] = name
            mapped += 1
    if not mapped:
        raise RuntimeError(f"No Unicode cmap accepts U+{codepoint:04X}")


def install(font: TTFont, name: str, glyph, advance: int, lsb: int, vertical_source: str) -> None:
    order = font.getGlyphOrder()
    if name not in order:
        order.append(name)
        font.setGlyphOrder(order)
    font["glyf"][name] = glyph
    glyph.recalcBounds(font["glyf"])
    font["hmtx"].metrics[name] = (int(advance), int(lsb))
    if "vmtx" in font:
        font["vmtx"].metrics[name] = font["vmtx"].metrics[vertical_source]
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def transformed_glyph(font: TTFont, source_name: str, transform: Transform):
    pen = TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()[source_name].draw(TransformPen(pen, transform))
    return pen.glyph()


def build_user_japanese_overrides(font: TTFont) -> dict:
    cmap = font.getBestCmap()
    metadata: dict[str, object] = {
        "handwritten": {},
        "alignment": {},
    }

    # Rebuild the two explicitly approved Han characters from the maintainer's
    # own structural handwriting data while preserving the source advance.
    for character, strokes in USER_KANJI_REFINED.items():
        codepoint = ord(character)
        source_name = cmap.get(codepoint)
        if source_name is None:
            raise RuntimeError(f"Source font is missing U+{codepoint:04X} {character}")
        advance, _ = font["hmtx"].metrics[source_name]
        target_name = f"uni{codepoint:04X}{USER_OVERRIDE_SUFFIX}"
        glyph = build_stroke_glyph(strokes)
        glyph.recalcBounds(font["glyf"])
        install(font, target_name, glyph, advance, glyph.xMin, source_name)
        add_mapping(font, codepoint, target_name)
        metadata["handwritten"][character] = {
            "source_glyph": source_name,
            "derived_glyph": target_name,
            "advance": advance,
        }

    # Re-read cmap after the handwritten remaps.  The reference Hiragana glyph
    # already exists because this function runs after build_japanese_phase1().
    cmap = font.getBestCmap()
    reference_name = cmap.get(ord(ALIGNMENT_REFERENCE))
    if reference_name is None:
        raise RuntimeError("Refined Hiragana reference glyph け is unavailable")
    ref_bounds = glyph_bounds(font, reference_name)
    ref_height = ref_bounds[3] - ref_bounds[1]
    ref_center = (ref_bounds[1] + ref_bounds[3]) / 2
    target_height = ref_height * ALIGNMENT_TARGET_HEIGHT_FACTOR

    for character in ALIGNMENT_OVERRIDE_CHARACTERS:
        codepoint = ord(character)
        source_name = cmap.get(codepoint)
        if source_name is None:
            raise RuntimeError(f"Source font is missing U+{codepoint:04X} {character}")
        source_bounds = glyph_bounds(font, source_name)
        source_height = source_bounds[3] - source_bounds[1]
        source_center = (source_bounds[1] + source_bounds[3]) / 2
        scale_y = target_height / source_height
        scale_y = min(ALIGNMENT_SCALE_CLAMP[1], max(ALIGNMENT_SCALE_CLAMP[0], scale_y))
        dy = ref_center - source_center * scale_y
        transform = Transform(1, 0, 0, scale_y, 0, dy)
        target_name = f"{source_name}{ALIGN_OVERRIDE_SUFFIX}"
        glyph = transformed_glyph(font, source_name, transform)
        glyph.recalcBounds(font["glyf"])
        advance, lsb = font["hmtx"].metrics[source_name]
        install(font, target_name, glyph, advance, lsb, source_name)
        add_mapping(font, codepoint, target_name)
        metadata["alignment"][character] = {
            "source_glyph": source_name,
            "derived_glyph": target_name,
            "scale_y": round(scale_y, 6),
            "dy": round(dy, 3),
            "reference_glyph": reference_name,
        }

    return metadata
