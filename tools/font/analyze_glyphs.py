#!/usr/bin/env python3
"""Print reproducible cmap, metric, component, and GPOS cedilla inspection."""

from __future__ import annotations

from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = REPO_ROOT / "assets/fonts/quanfangwei-supplement"
FONT_PATHS = [
    FONT_DIR / "QuanFangweiSupplementScript-Regular.ttf",
    FONT_DIR / "QuanFangweiSupplementScript-Regular.woff2",
]
CODEPOINTS = [
    0x003F, 0x00A8, 0x00BF, 0x0041, 0x004F, 0x0055, 0x0061, 0x006F,
    0x0075, 0x00B8, 0x00C4, 0x00C7, 0x00D6, 0x00DC, 0x00DF, 0x00E4,
    0x00E7, 0x00F6, 0x00FC, 0x0308, 0x0327, 0x1E9E,
]


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def mark_rule(font: TTFont, base_name: str, mark_name: str):
    for lookup_index, lookup in enumerate(font["GPOS"].table.LookupList.Lookup):
        if lookup.LookupType != 4:
            continue
        for subtable in lookup.SubTable:
            if mark_name not in subtable.MarkCoverage.glyphs or base_name not in subtable.BaseCoverage.glyphs:
                continue
            mark_index = subtable.MarkCoverage.glyphs.index(mark_name)
            base_index = subtable.BaseCoverage.glyphs.index(base_name)
            mark_record = subtable.MarkArray.MarkRecord[mark_index]
            mark_anchor = mark_record.MarkAnchor
            base_anchor = subtable.BaseArray.BaseRecord[base_index].BaseAnchor[mark_record.Class]
            return lookup_index, (base_anchor.XCoordinate, base_anchor.YCoordinate), (mark_anchor.XCoordinate, mark_anchor.YCoordinate)
    return None


def main() -> int:
    for path in FONT_PATHS:
        font = TTFont(path, recalcTimestamp=False)
        try:
            print(f"{path.relative_to(REPO_ROOT)} glyph_count={len(font.getGlyphOrder())}")
            cmap = font.getBestCmap()
            for codepoint in CODEPOINTS:
                glyph_name = cmap.get(codepoint)
                if glyph_name is None:
                    print(f"  U+{codepoint:04X} -> MISSING")
                    continue
                glyph = font["glyf"][glyph_name]
                components = [component.getComponentInfo() for component in glyph.components] if glyph.isComposite() else []
                advance, lsb = font["hmtx"].metrics[glyph_name]
                print(
                    f"  U+{codepoint:04X} -> {glyph_name}; advance={advance}; lsb={lsb}; "
                    f"bounds={bounds(font, glyph_name)}; components={components}"
                )
            print(f"  GPOS C/uni0327={mark_rule(font, 'C', 'uni0327')}")
            print(f"  GPOS c/uni0327={mark_rule(font, 'c', 'uni0327')}")
            for base_name in ("A", "O", "U", "a", "o", "u"):
                print(f"  GPOS {base_name}/uni0308={mark_rule(font, base_name, 'uni0308')}")
        finally:
            font.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
