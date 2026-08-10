"""Build Phase 1 kana, marks, and missing Japanese punctuation."""

from __future__ import annotations

from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from japanese.stroke_engine import build_stroke_glyph, translate_strokes
from kana_sources.full_data import (
    COMPOSITES,
    DAKUTEN_STROKES,
    HANDAKUTEN_STROKES,
    ITERATION_STROKES,
    JAPANESE_MARK_STROKES,
    KANA_STROKES,
)


KANA_ADVANCE = 960
SPACING_MARK_ADVANCE = 300
KANA_VERTICAL_SHIFT = -145
JAPANESE_MARK_VERTICAL_SHIFT = -120
DAKUTEN_ANCHOR = (92, 815)
HANDAKUTEN_ANCHOR = (92, 815)
KANA_BASE_ANCHOR_Y = 835 + KANA_VERTICAL_SHIFT


def glyph_name(character: str) -> str:
    return f"uni{ord(character):04X}"


def add_mapping(font: TTFont, codepoint: int, name: str) -> None:
    mapped = 0
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format != 14:
            table.cmap[codepoint] = name
            mapped += 1
    if not mapped:
        raise RuntimeError(f"No Unicode cmap accepts U+{codepoint:04X}")


def install(font: TTFont, name: str, glyph, advance: int, vertical_source: str) -> None:
    order = font.getGlyphOrder()
    if name not in order:
        order.append(name)
        font.setGlyphOrder(order)
    font["glyf"][name] = glyph
    glyph.recalcBounds(font["glyf"])
    font["hmtx"].metrics[name] = (advance, glyph.xMin)
    if "vmtx" in font:
        font["vmtx"].metrics[name] = font["vmtx"].metrics[vertical_source]
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def bounds(font: TTFont, name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        return (0, 0, 0, 0)
    return tuple(round(value) for value in pen.bounds)


def base_anchor(font: TTFont, name: str) -> tuple[int, int]:
    x_min, _, x_max, _ = bounds(font, name)
    return (min(835, max(710, x_max + 48)), KANA_BASE_ANCHOR_Y)


def composite(font: TTFont, base_name: str, mark_name: str, dx: int, dy: int):
    pen = TTGlyphPen(font.getGlyphSet())
    pen.addComponent(base_name, (1, 0, 0, 1, 0, 0))
    pen.addComponent(mark_name, (1, 0, 0, 1, dx, dy))
    return pen.glyph()


def append_mark_positioning(font: TTFont, anchors: dict[str, tuple[int, int]]) -> None:
    if "GPOS" not in font or "GDEF" not in font:
        raise RuntimeError("Source GPOS/GDEF tables are required")
    marks = {
        "uni3099": (0, buildAnchor(*DAKUTEN_ANCHOR)),
        "uni309A": (0, buildAnchor(*HANDAKUTEN_ANCHOR)),
    }
    bases = {name: {0: buildAnchor(*anchor)} for name, anchor in anchors.items()}
    subtable = buildMarkBasePosSubtable(marks, bases, font.getReverseGlyphMap())
    lookup = otTables.Lookup()
    lookup.LookupType = 4
    lookup.LookupFlag = 0
    lookup.SubTable = [subtable]
    lookup.SubTableCount = 1
    gpos = font["GPOS"].table
    lookup_index = len(gpos.LookupList.Lookup)
    gpos.LookupList.Lookup.append(lookup)
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)
    features = [record.Feature for record in gpos.FeatureList.FeatureRecord if record.FeatureTag == "mark"]
    if not features:
        raise RuntimeError("Source GPOS has no mark feature")
    for feature in features:
        feature.LookupListIndex.append(lookup_index)
        feature.LookupCount = len(feature.LookupListIndex)
    classes = font["GDEF"].table.GlyphClassDef
    if classes is None:
        classes = otTables.ClassDef()
        classes.classDefs = {}
        font["GDEF"].table.GlyphClassDef = classes
    classes.classDefs["uni3099"] = 3
    classes.classDefs["uni309A"] = 3


def build_japanese_phase1(font: TTFont) -> dict:
    """Add Phase 1 glyphs and return deterministic construction metadata."""
    cmap = font.getBestCmap()
    vertical_source = cmap[0x4E00]
    added: list[str] = []

    # Whole-glyph original drawings.
    for character, strokes in KANA_STROKES.items():
        if ord(character) in font.getBestCmap():
            continue
        name = glyph_name(character)
        positioned_strokes = translate_strokes(strokes, dy=KANA_VERTICAL_SHIFT)
        install(font, name, build_stroke_glyph(positioned_strokes), KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(character), name)
        added.append(character)

    for character, strokes in {**ITERATION_STROKES, **JAPANESE_MARK_STROKES}.items():
        if ord(character) in font.getBestCmap():
            continue
        name = glyph_name(character)
        vertical_shift = KANA_VERTICAL_SHIFT if character in ITERATION_STROKES else JAPANESE_MARK_VERTICAL_SHIFT
        positioned_strokes = translate_strokes(strokes, dy=vertical_shift)
        install(font, name, build_stroke_glyph(positioned_strokes), KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(character), name)
        added.append(character)

    # Combining dakuten and handakuten are original short-stroke/circle designs.
    mark_sources = {"uni3099": DAKUTEN_STROKES, "uni309A": HANDAKUTEN_STROKES}
    for name, strokes in mark_sources.items():
        codepoint = int(name[3:], 16)
        glyph = build_stroke_glyph(strokes)
        install(font, name, glyph, 0, vertical_source)
        add_mapping(font, codepoint, name)
        added.append(chr(codepoint))

    # Spacing forms share exactly the reviewed combining-mark contours.
    for codepoint, mark_name in ((0x309B, "uni3099"), (0x309C, "uni309A")):
        name = glyph_name(chr(codepoint))
        pen = TTGlyphPen(font.getGlyphSet())
        pen.addComponent(mark_name, (1, 0, 0, 1, 65, -20 + KANA_VERTICAL_SHIFT))
        install(font, name, pen.glyph(), SPACING_MARK_ADVANCE, vertical_source)
        add_mapping(font, codepoint, name)
        added.append(chr(codepoint))

    anchors = {
        glyph_name(character): base_anchor(font, glyph_name(character))
        for character in KANA_STROKES
    }
    anchors.update({glyph_name(character): base_anchor(font, glyph_name(character)) for character in ITERATION_STROKES})

    # Precomposed kana use the same component and delta as GPOS decomposition.
    for target, (base, mark_kind) in COMPOSITES.items():
        target_name = glyph_name(target)
        base_name = glyph_name(base)
        mark_name = "uni309A" if mark_kind == "handakuten" else "uni3099"
        mark_anchor = HANDAKUTEN_ANCHOR if mark_kind == "handakuten" else DAKUTEN_ANCHOR
        anchor = anchors[base_name]
        delta = (anchor[0] - mark_anchor[0], anchor[1] - mark_anchor[1])
        install(font, target_name, composite(font, base_name, mark_name, *delta), KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(target), target_name)
        added.append(target)

    for target, base in (("ゞ", "ゝ"), ("ヾ", "ヽ")):
        target_name, base_name = glyph_name(target), glyph_name(base)
        anchor = anchors[base_name]
        delta = (anchor[0] - DAKUTEN_ANCHOR[0], anchor[1] - DAKUTEN_ANCHOR[1])
        install(font, target_name, composite(font, base_name, "uni3099", *delta), KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(target), target_name)
        added.append(target)

    append_mark_positioning(font, anchors)
    return {
        "added_characters": added,
        "base_anchors": anchors,
        "dakuten_mark_anchor": DAKUTEN_ANCHOR,
        "handakuten_mark_anchor": HANDAKUTEN_ANCHOR,
        "kana_advance": KANA_ADVANCE,
    }
