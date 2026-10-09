"""Raise only U/u diaeresis by 30 units; retain native dots and other accents."""
from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable


def refine_umlaut_clearance(font):
    glyf = font['glyf']
    for name, original_y in [('Udieresis',88),('udieresis',-62)]:
        glyph = glyf[name]
        mark = glyph.components[1]
        assert mark.glyphName == 'uni0308' and mark.y == original_y
        mark.y += 30
        glyph.recalcBounds(glyf)
        advance, bearing = font['vmtx'][name]
        font['vmtx'][name] = (advance, bearing-30)
    # The original upper-mark anchor class is shared by acute, grave, macron,
    # etc. A first, narrowly covered subtable changes only U/u + diaeresis.
    # OpenType applies the first matching subtable in this lookup.
    lookup = font['GPOS'].table.LookupList.Lookup[2]
    source = lookup.SubTable[0]
    assert lookup.LookupType == 4 and source.MarkCoverage.glyphs[0] == 'uni0308'
    subtable = buildMarkBasePosSubtable(
        {'uni0308':(0,buildAnchor(145,477))},
        {'U':{0:buildAnchor(174,595)},'u':{0:buildAnchor(180,445)}},
        font.getReverseGlyphMap())
    lookup.SubTable.insert(0,subtable)
    lookup.SubTableCount += 1
