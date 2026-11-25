#!/usr/bin/env python3
"""Check that 1.047 changes only the two fullwidth square bracket glyphs."""

from io import BytesIO

from fontTools.ttLib import TTFont

from verify_han_you import REL, ROOT, release_1046


def verify(extension):
    old = TTFont(BytesIO(release_1046(extension)), recalcBBoxes=False)
    new = TTFont(ROOT / (REL + extension), recalcBBoxes=False)
    order = old.getGlyphOrder()
    assert new.getGlyphOrder() == order
    cmap = old.getBestCmap()
    targets = {cmap[0xFF3B], cmap[0xFF3D]}
    old_glyf, new_glyf = old["glyf"], new["glyf"]
    for tag in ("cmap", "GDEF", "GPOS", "GSUB", "MATH", "OS/2", "kern", "post"):
        if tag in old:
            assert old.getTableData(tag) == new.getTableData(tag), tag
    assert {name for name in order if old_glyf[name].compile(old_glyf)
            != new_glyf[name].compile(new_glyf)} == targets
    for name in order:
        if name in targets:
            old_advance, old_bearing = old["vmtx"][name]
            new_advance, new_bearing = new["vmtx"][name]
            assert new_advance == old_advance
            assert new_glyf[name].yMax + new_bearing == old_glyf[name].yMax + old_bearing
        else:
            assert new["hmtx"][name] == old["hmtx"][name], name
            assert new["vmtx"][name] == old["vmtx"][name], name


if __name__ == "__main__":
    for ext in (".ttf", ".woff2"):
        verify(ext)
    print("PASS: only U+FF3B/U+FF3D outlines and bearings changed; both vertical origins preserved")
