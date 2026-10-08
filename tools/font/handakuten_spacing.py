"""Move all ten native handakuten attachments outward without changing ink."""
from kana_sources.full_data import COMPOSITES

HANDAKUTEN_OFFSET = (16, 24)
HANDAKUTEN_MARKS = ('uni309A', 'uni309A.katakana')


def refine_handakuten_spacing(font):
    dx, dy = HANDAKUTEN_OFFSET
    seen = []
    # Moving a mark anchor oppositely moves its attached ink by the requested
    # delta. Base anchors, dakuten and the handakuten outlines remain untouched.
    for lookup in font['GPOS'].table.LookupList.Lookup:
        if lookup.LookupType != 4:
            continue
        for subtable in lookup.SubTable:
            for name, record in zip(subtable.MarkCoverage.glyphs, subtable.MarkArray.MarkRecord):
                if name in HANDAKUTEN_MARKS:
                    record.MarkAnchor.XCoordinate -= dx
                    record.MarkAnchor.YCoordinate -= dy
                    seen.append(name)
    assert sorted(seen) == sorted(HANDAKUTEN_MARKS)
    for character, (_, kind) in COMPOSITES.items():
        if kind != 'handakuten':
            continue
        glyph = font['glyf'][font.getBestCmap()[ord(character)]]
        assert len(glyph.components) == 2
        mark = glyph.components[1]
        assert mark.glyphName in HANDAKUTEN_MARKS
        mark.x += dx
        mark.y += dy
        glyph.recalcBounds(font['glyf'])
