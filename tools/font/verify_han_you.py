#!/usr/bin/env python3
"""Verify the one-point U+6182 repair against the released 1.045 fonts."""

import copy
import hashlib
from io import BytesIO
from pathlib import Path
import subprocess

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
REL = "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular"
BASE_COMMIT = "a7727aaa63204839c4f21dbd92ec38ca5e835417"
BASE_SHA = {
    ".ttf": "be9bd8ca13d5ca580b6310a1523c4f966a0c0824c9bc59cf146508c022bbe15c",
    ".woff2": "9edbef4df2ca1138ed0c7a8728de8fbd8a6b35bddfb18d8644b3535a7b5c85ed",
}
TARGET = "uni6182"
HEADER_EXTREMA = {"hhea": {"minRightSideBearing": -273},
                  "vhea": {"minTopSideBearing": -112}}


def released_bytes(extension):
    data = subprocess.check_output(
        ["git", "show", f"{BASE_COMMIT}:{REL}{extension}"], cwd=ROOT
    )
    assert hashlib.sha256(data).hexdigest() == BASE_SHA[extension]
    return data


def verify(extension):
    old = TTFont(BytesIO(released_bytes(extension)), recalcBBoxes=False)
    new = TTFont(ROOT / (REL + extension), recalcBBoxes=False)
    order = old.getGlyphOrder()
    assert new.getGlyphOrder() == order
    assert new.getBestCmap()[0x6182] == TARGET
    for tag in ("cmap", "hmtx", "GDEF", "GPOS", "GSUB", "MATH", "OS/2", "kern", "post"):
        if tag in old:
            assert old.getTableData(tag) == new.getTableData(tag), tag
    for tag, fields in HEADER_EXTREMA.items():
        header = copy.deepcopy(new[tag])
        for field, expected in fields.items():
            assert getattr(header, field) == expected
            setattr(header, field, getattr(old[tag], field))
        assert header.compile(new) == old[tag].compile(old), tag

    old_glyf, new_glyf = old["glyf"], new["glyf"]
    changed = [g for g in order if old_glyf[g].compile(old_glyf) != new_glyf[g].compile(new_glyf)]
    assert changed == [TARGET], changed
    for g in order:
        if g != TARGET:
            assert old["vmtx"][g] == new["vmtx"][g], g
            glyph = new_glyf[g]
            assert not glyph.isComposite() or TARGET not in glyph.getComponentNames(new_glyf), g

    before, after = old_glyf[TARGET], new_glyf[TARGET]
    points = list(before.coordinates)
    controls = list(before.flags)
    i = points.index((1610, 1096))
    assert not controls[i] & 1
    assert list(after.coordinates) == points[:i] + points[i+1:]
    assert list(after.flags) == controls[:i] + controls[i+1:]
    assert after.endPtsOfContours == [end - (end >= i) for end in before.endPtsOfContours]
    assert (before.xMin, before.yMin, before.xMax, before.yMax) == (86, -135, 1610, 1096)
    assert (after.xMin, after.yMin, after.xMax, after.yMax) == (86, -135, 780, 775)
    advance, bearing = old["vmtx"][TARGET]
    assert new["vmtx"][TARGET] == (advance, bearing + before.yMax - after.yMax)
    assert new["head"].yMax == 931


if __name__ == "__main__":
    for ext in (".ttf", ".woff2"):
        verify(ext)
    print("PASS: U+6182 alone loses one stray control; cmap, advances and vertical origin preserved")
