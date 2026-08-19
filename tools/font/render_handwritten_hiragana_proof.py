#!/usr/bin/env python3
"""Render Version 1.011 complete Hiragana and mixed CJK/Kana proof sheets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
SOURCE_PATH = TOOLS_DIR / "references" / "user-hiragana-template-source-complete.png"
PROOF_DIR = TOOLS_DIR / "proofs"
GRID_PROOF = PROOF_DIR / "quanfangwei-user-handwritten-hiragana-proof.png"
MIXED_PROOF = PROOF_DIR / "quanfangwei-user-handwritten-mixed-proof.png"

ROWS = [
    ["あ","か","さ","た","な","は","ま","や","ら","わ","ん"],
    ["い","き","し","ち","に","ひ","み",None,"り",None,None],
    ["う","く","す","つ","ぬ","ふ","む","ゆ","る",None,None],
    ["え","け","せ","て","ね","へ","め",None,"れ",None,None],
    ["お","こ","そ","と","の","ほ","も","よ","ろ","を",None],
]
MIXED_LINES = [
    "空の青さに目を奪われて",
    "足元の花に気付けないまま",
    "懐かしい風が頬を撫でて",
    "君の香りを今も想ってる",
    "ねぇ今更になって思い出す",
    "色のない世界 残る香りに",
]
KEY_LINES = [
    "き　さ　　ぬ　め　　ね　れ　わ",
    "み　む　や　の　　わ　を　ん",
]


def render_grid() -> None:
    width = 2050
    margin = 45
    source = Image.open(SOURCE_PATH).convert("RGB")
    source.thumbnail((width - margin * 2, 620), Image.Resampling.LANCZOS)
    source_y = 115
    cell_w, cell_h = 175, 165
    grid_x = (width - cell_w * 11) // 2
    grid_y = source_y + source.height + 95
    height = grid_y + cell_h * 5 + 90
    image = Image.new("RGB", (width, height), "#fffdf9")
    image.paste(source, ((width-source.width)//2, source_y))
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT_PATH), 40)
    note = ImageFont.truetype(str(FONT_PATH), 20)
    glyph_font = ImageFont.truetype(str(FONT_PATH), 112)
    label_font = ImageFont.truetype(str(FONT_PATH), 16)
    draw.text((margin, 30), "荃方位補寫體 1.011 — 使用者手寫結構 × 辰宇落雁筆勢", font=title, fill="#35215f")
    draw.text((margin, 78), "上：完整手寫來源　下：refined center-line 經 variable-width stroke renderer 建置後的 TTF", font=note, fill="#5e5264")
    for row_index, row in enumerate(ROWS):
        for column, character in enumerate(row):
            x = grid_x + column * cell_w
            y = grid_y + row_index * cell_h
            draw.rectangle((x, y, x+cell_w, y+cell_h), outline="#d9d7dc", width=2, fill="#ffffff")
            if not character:
                continue
            draw.text((x+7, y+7), f"{character} U+{ord(character):04X}", font=label_font, fill="#756b79")
            baseline = y + 137
            draw.line((x+10, baseline, x+cell_w-10, baseline), fill="#efc7cf", width=1)
            draw.text((x+cell_w/2, baseline), character, font=glyph_font, fill="#111111", anchor="ms")
    draw.text((margin, height-45), "Version 1.011 補齊 わ／を／ん；SVG 僅作結構來源，最終輪廓不再直接安裝 SVG fill。", font=note, fill="#5e5264")
    image.save(GRID_PROOF, "PNG", optimize=True)


def render_mixed() -> None:
    width, height = 2350, 1770
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    note = ImageFont.truetype(str(FONT_PATH), 20)
    draw.text((55, 35), "QuanFangwei 1.011 — Chinese / refined Hiragana mixed-text proof", font=title, fill="#35215f")
    draw.text((55, 90), "Same face · same baseline · no CSS offset · key glyphs enlarged below", font=note, fill="#5e5264")
    y = 150
    for size in (24, 32, 48, 72):
        face = ImageFont.truetype(str(FONT_PATH), size)
        draw.text((55, y+4), f"{size}px", font=note, fill="#6d35c5")
        baseline = y + 48 + size
        step = max(58, round(size*1.55))
        for line in MIXED_LINES[:4]:
            draw.line((150, baseline+2, width-60, baseline+2), fill="#efc7cf", width=1)
            draw.text((165, baseline), line, font=face, fill="#111111", anchor="ls")
            baseline += step
        y = baseline + 35
    draw.text((55, y), "Key recognition / style check", font=note, fill="#6d35c5")
    key_face = ImageFont.truetype(str(FONT_PATH), 96)
    baseline = y + 125
    for line in KEY_LINES:
        draw.line((150, baseline+4, width-60, baseline+4), fill="#efc7cf", width=2)
        draw.text((165, baseline), line, font=key_face, fill="#111111", anchor="ls")
        baseline += 160
    image.save(MIXED_PROOF, "PNG", optimize=True)


def main() -> int:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Build the font first: {FONT_PATH}")
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Missing complete handwriting source: {SOURCE_PATH}")
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    render_grid()
    render_mixed()
    print(f"Rendered {GRID_PROOF.relative_to(REPO_ROOT)}")
    print(f"Rendered {MIXED_PROOF.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
