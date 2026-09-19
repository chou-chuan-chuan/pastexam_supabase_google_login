"""Build Phase 1 kana, marks, and missing Japanese punctuation."""

from __future__ import annotations

from functools import lru_cache

from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable, buildCoverage, buildLookup, buildSingleSubstSubtable
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
    VERSION_1_025_KANA_STROKES,
)
from kana_sources.han_balance import balance_strokes, script_scale, uniform_scale


KANA_ADVANCE = 960
SPACING_MARK_ADVANCE = 300
# 1.026 geometry is frozen. Apply the integer translation AFTER rendering so
# every outline coordinate changes by exactly (0, delta), without re-rounding
# curves or rerunning the pressure engine at a different origin.
KANA_VERTICAL_SHIFT_1_026 = -145
JAPANESE_MARK_VERTICAL_SHIFT_1_026 = -120
# Han median yMin - pooled 92-kana median yMin = -14 - 41.5 = -55.5.
# Reviewed candidates: -64 / -56 / -48. See reports/kana-bottom-alignment.md.
JAPANESE_BOTTOM_ALIGNMENT_SHIFT = -56
KANA_VERTICAL_SHIFT = KANA_VERTICAL_SHIFT_1_026 + JAPANESE_BOTTOM_ALIGNMENT_SHIFT
JAPANESE_MARK_VERTICAL_SHIFT = JAPANESE_MARK_VERTICAL_SHIFT_1_026 + JAPANESE_BOTTOM_ALIGNMENT_SHIFT
DAKUTEN_ANCHOR_1_026 = (92, 815)
DAKUTEN_ANCHOR = (92, DAKUTEN_ANCHOR_1_026[1] + JAPANESE_BOTTOM_ALIGNMENT_SHIFT)
HANDAKUTEN_ANCHOR = DAKUTEN_ANCHOR
KANA_BASE_ANCHOR_Y = 835 + KANA_VERTICAL_SHIFT
# Version 1.027: +17 left a 7.81-unit diagonal gap, visually touching at 20px.
# +82 is the smallest integer scoped offset reaching a 51.2-unit (one 20px
# pixel) gap after the accepted anchor scale: +65 here becomes +58 final Y.
# Only て's base anchor changes; shared mark outlines/anchors stay unchanged.
# See reports/de-dakuten-clearance.md for measurements and candidate proofs.
HIRAGANA_MARK_ANCHOR_Y_OFFSETS = {"て": 82}


def apply_bottom_alignment(glyph):
    """Translate each simple kana/mark source once; composites inherit it."""
    assert not glyph.isComposite()
    glyph.coordinates.translate((0, JAPANESE_BOTTOM_ALIGNMENT_SHIFT))
    return glyph


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


@lru_cache(maxsize=None)
def accepted_base_bounds(character):
    strokes = (VERSION_1_025_KANA_STROKES[character] if character in VERSION_1_025_KANA_STROKES
               else ITERATION_STROKES[character])
    glyph = build_stroke_glyph(translate_strokes(strokes, dy=KANA_VERTICAL_SHIFT_1_026))
    glyph.recalcBounds({})
    return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax


def base_anchor(font: TTFont, name: str) -> tuple[int, int]:
    """Scale the accepted anchor with its base, retaining the reviewed gap."""
    character = chr(int(name[3:], 16))
    x0, y0, x1, y1 = accepted_base_bounds(character)
    cx, cy = (x0+x1)/2, (y0+y1)/2
    old_x = min(835, max(710, x1 + 48))
    old_y = KANA_BASE_ANCHOR_Y - JAPANESE_BOTTOM_ALIGNMENT_SHIFT + HIRAGANA_MARK_ANCHOR_Y_OFFSETS.get(character, 0)
    factor = script_scale(character)
    return round(cx + (old_x-cx)*factor), round(cy + (old_y-cy)*factor) + JAPANESE_BOTTOM_ALIGNMENT_SHIFT


def mark_name_for(base: str, kind: str) -> str:
    name = 'uni309A' if kind == 'handakuten' else 'uni3099'
    return name + ('.katakana' if 0x30A0 <= ord(base) <= 0x30FF else '')


def append_katakana_mark_selection(font):
    """Contextual mark size only; no ligature, new character, or pair spacing.

    The Unicode combining marks use the Hiragana scale. A ccmp rule selects
    the identically designed Katakana-size marks after any Katakana base.
    Precomposed forms reference those same glyphs, giving identical output.
    Existing GSUB lookups/features remain intact.
    """
    gsub = font['GSUB'].table
    lookups = gsub.LookupList.Lookup
    mapping = {n: n + '.katakana' for n in ('uni3099', 'uni309A')}
    single_index = len(lookups)
    lookups.append(buildLookup([buildSingleSubstSubtable(mapping)]))
    context = otTables.ChainContextSubst()
    context.Format = 3
    context.BacktrackGlyphCount = 1
    context.BacktrackCoverage = [buildCoverage(
        [glyph_name(c) for c in (*KANA_STROKES, *ITERATION_STROKES) if 0x30A0 <= ord(c) <= 0x30FF],
        font.getReverseGlyphMap())]
    context.InputGlyphCount = 1
    context.InputCoverage = [buildCoverage(list(mapping), font.getReverseGlyphMap())]
    context.LookAheadGlyphCount = 0
    context.LookAheadCoverage = []
    record = otTables.SubstLookupRecord()
    record.SequenceIndex = 0
    record.LookupListIndex = single_index
    context.SubstCount = 1
    context.SubstLookupRecord = [record]
    context_index = len(lookups)
    lookups.append(buildLookup([context]))
    gsub.LookupList.LookupCount = len(lookups)
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag == 'ccmp':
            record.Feature.LookupListIndex.append(context_index)
            record.Feature.LookupCount = len(record.Feature.LookupListIndex)


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
        "uni3099.katakana": (0, buildAnchor(*DAKUTEN_ANCHOR)),
        "uni309A.katakana": (0, buildAnchor(*HANDAKUTEN_ANCHOR)),
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
    classes.classDefs["uni3099.katakana"] = 3
    classes.classDefs["uni309A.katakana"] = 3


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
        positioned_strokes = translate_strokes(strokes, dy=KANA_VERTICAL_SHIFT_1_026)
        glyph = apply_bottom_alignment(build_stroke_glyph(positioned_strokes))
        install(font, name, glyph, KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(character), name)
        added.append(character)

    for character, strokes in {**ITERATION_STROKES, **JAPANESE_MARK_STROKES}.items():
        if ord(character) in font.getBestCmap():
            continue
        name = glyph_name(character)
        vertical_shift = KANA_VERTICAL_SHIFT_1_026 if character in ITERATION_STROKES else JAPANESE_MARK_VERTICAL_SHIFT_1_026
        if character in ITERATION_STROKES or character == 'ー':
            strokes = balance_strokes(character, strokes)
        positioned_strokes = translate_strokes(strokes, dy=vertical_shift)
        glyph = build_stroke_glyph(positioned_strokes)
        if character in ITERATION_STROKES or character == 'ー':
            glyph = apply_bottom_alignment(glyph)
        install(font, name, glyph, KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(character), name)
        added.append(character)

    # Combining dakuten and handakuten are original short-stroke/circle designs.
    mark_sources = {"uni3099": DAKUTEN_STROKES, "uni309A": HANDAKUTEN_STROKES}
    for name, strokes in mark_sources.items():
        codepoint = int(name[3:], 16)
        glyph = apply_bottom_alignment(build_stroke_glyph(uniform_scale(strokes, script_scale('あ'), DAKUTEN_ANCHOR_1_026)))
        install(font, name, glyph, 0, vertical_source)
        add_mapping(font, codepoint, name)
        added.append(chr(codepoint))
        variant = apply_bottom_alignment(build_stroke_glyph(uniform_scale(strokes, script_scale('ア'), DAKUTEN_ANCHOR_1_026)))
        install(font, name + '.katakana', variant, 0, vertical_source)

    # Spacing forms share exactly the reviewed combining-mark contours.
    for codepoint, mark_name in ((0x309B, "uni3099"), (0x309C, "uni309A")):
        name = glyph_name(chr(codepoint))
        pen = TTGlyphPen(font.getGlyphSet())
        # The shared combining-mark source already moved; retain the exact
        # accepted component delta so spacing forms receive the shift once.
        pen.addComponent(mark_name, (1, 0, 0, 1, 65, -20 + KANA_VERTICAL_SHIFT_1_026))
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
        mark_name = mark_name_for(base, mark_kind)
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
        install(font, target_name, composite(font, base_name, mark_name_for(base, 'dakuten'), *delta), KANA_ADVANCE, vertical_source)
        add_mapping(font, ord(target), target_name)
        added.append(target)

    append_mark_positioning(font, anchors)
    append_katakana_mark_selection(font)
    return {
        "added_characters": added,
        "base_anchors": anchors,
        "dakuten_mark_anchor": DAKUTEN_ANCHOR,
        "handakuten_mark_anchor": HANDAKUTEN_ANCHOR,
        "kana_advance": KANA_ADVANCE,
    }
