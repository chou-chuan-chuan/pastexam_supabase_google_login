#!/usr/bin/env python3
"""Build and render the review gate for the first kana style masters."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from japanese.stroke_engine import build_stroke_glyph  # noqa: E402
from kana_sources.master_data import MASTER_GLYPHS, MASTER_ORDER  # noqa: E402


BASE_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_DIR = TOOLS_DIR / "proofs"
MASTER_FONT = PROOF_DIR / "quanfangwei-kana-master.ttf"
MASTER_PROOF = PROOF_DIR / "quanfangwei-kana-master-proof.png"
ADVANCE = 960


def add_mapping(font: TTFont, codepoint: int, glyph_name: str) -> None:
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format != 14:
            table.cmap[codepoint] = glyph_name


def install(font: TTFont, character: str) -> None:
    glyph_name = f"uni{ord(character):04X}"
    glyph = build_stroke_glyph(MASTER_GLYPHS[character])
    order = font.getGlyphOrder()
    if glyph_name not in order:
        order.append(glyph_name)
        font.setGlyphOrder(order)
    font["glyf"][glyph_name] = glyph
    glyph.recalcBounds(font["glyf"])
    font["hmtx"].metrics[glyph_name] = (ADVANCE, glyph.xMin)
    if "vmtx" in font:
        vertical_source = font.getBestCmap().get(0x4E00)
        font["vmtx"].metrics[glyph_name] = font["vmtx"].metrics[vertical_source]
    add_mapping(font, ord(character), glyph_name)
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def render() -> None:
    sizes = [16, 24, 32, 48, 72, 120]
    rows = [
        "あ い う え お   か さ た な は ま や ら わ ん",
        "ゃ ゅ ょ っ",
        "ア イ ウ エ オ   カ サ タ ナ ハ マ ヤ ラ ワ ン",
        "ャ ュ ョ ッ",
    ]
    width = 2900
    heights = [max(260, 115 + len(rows) * max(42, round(size * 1.45))) for size in sizes]
    image = Image.new("RGB", (width, 120 + sum(heights)), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(MASTER_FONT), 40)
    label = ImageFont.truetype(str(MASTER_FONT), 21)
    draw.text((60, 42), "QuanFangwei kana master proof — original outlines", font=title, fill="#4f276c")
    y = 110
    for size, block_height in zip(sizes, heights):
        face = ImageFont.truetype(str(MASTER_FONT), size)
        draw.text((60, y + 8), f"{size} px", font=label, fill="#6d35c5")
        baseline = y + 65 + size
        for row in rows:
            draw.line((170, baseline + 3, width - 60, baseline + 3), fill="#e8a5b2", width=1)
            draw.text((180, baseline), row, font=face, fill="#17121f", anchor="ls")
            baseline += max(42, round(size * 1.45))
        y += block_height
    image.save(MASTER_PROOF, "PNG", optimize=True)


def main() -> int:
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    font = TTFont(BASE_FONT, recalcTimestamp=False)
    try:
        existing = font.getBestCmap()
        for character in MASTER_ORDER:
            if ord(character) not in existing:
                install(font, character)
        font.save(MASTER_FONT, reorderTables=False)
    finally:
        font.close()
    render()
    print(f"Built {MASTER_FONT.relative_to(REPO_ROOT)}")
    print(f"Rendered {MASTER_PROOF.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
