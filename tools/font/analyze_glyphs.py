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
CODEPOINTS = [0x003F, 0x00BF, 0x0043, 0x00B8, 0x00C7, 0x0327]


def bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def mark_rule(font: TTFont):
    for lookup_index, lookup in enumerate(font["GPOS"].table.LookupList.Lookup):
        if lookup.LookupType != 4:
            continue
        for subtable in lookup.SubTable:
            if "uni0327" not in subtable.MarkCoverage.glyphs or "C" not in subtable.BaseCoverage.glyphs:
                continue
            mark_index = subtable.MarkCoverage.glyphs.index("uni0327")
            base_index = subtable.BaseCoverage.glyphs.index("C")
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
            print(f"  GPOS C/uni0327={mark_rule(font)}")
        finally:
            font.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
