"""Remove a stray control point from the native U+6182 outline."""


TARGET = "uni6182"
STRAY_CONTROL = (1610, 1096)


def refine_han_you(font):
    if font.getBestCmap().get(0x6182) != TARGET:
        raise ValueError("Unexpected U+6182 mapping")
    glyf = font["glyf"]
    glyph = glyf[TARGET]
    glyph.recalcBounds(glyf)
    matches = [i for i, point in enumerate(glyph.coordinates) if point == STRAY_CONTROL]
    if len(matches) != 1:
        raise ValueError("Expected one stray control point in U+6182")
    point = matches[0]
    if (list(glyph.coordinates[point-1:point+2]) != [(437, 66), STRAY_CONTROL, (394, 27)]
            or any(flag & 1 for flag in glyph.flags[point-1:point+2])):
        raise ValueError("Unexpected control sequence in U+6182")

    # The two adjacent quadratic controls already describe the local stroke.
    # Delete the excursion and leave every other point and flag intact.
    old_top = glyph.yMax
    del glyph.coordinates[point]
    del glyph.flags[point]
    glyph.endPtsOfContours = [end - (end >= point) for end in glyph.endPtsOfContours]
    glyph.recalcBounds(glyf)
    advance, bearing = font["vmtx"][TARGET]
    font["vmtx"][TARGET] = (advance, bearing + old_top - glyph.yMax)
