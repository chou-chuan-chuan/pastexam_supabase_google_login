#!/usr/bin/env python3
"""Render the actual built font against the user handwriting source sheet."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
SOURCE_PATH = TOOLS_DIR / "references" / "user-hiragana-template-source.png"
PROOF_PATH = TOOLS_DIR / "proofs" / "quanfangwei-user-handwritten-hiragana-proof.png"
ROWS = [
    ["あ","か","さ","た","な","は","ま","や","ら"],
    ["い","き","し","ち","に","ひ","み",None,"り"],
    ["う","く","す","つ","ぬ","ふ","む","ゆ","る"],
    ["え","け","せ","て","ね","へ","め",None,"れ"],
    ["お","こ","そ","と","の","ほ","も","よ","ろ"],
]


def main() -> int:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Build the font first: {FONT_PATH}")
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Missing handwriting source: {SOURCE_PATH}")

    width = 1560
    margin = 55
    source = Image.open(SOURCE_PATH).convert("RGB")
    source.thumbnail((width - margin * 2, 750), Image.Resampling.LANCZOS)
    source_x = (width - source.width) // 2
    source_y = 145

    cell_w, cell_h = 155, 155
    grid_x = (width - cell_w * 9) // 2
    grid_y = source_y + source.height + 125
    height = grid_y + cell_h * 5 + 105
    image = Image.new("RGB", (width, height), "#fffdf9")
    image.paste(source, (source_x, source_y))
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    note = ImageFont.truetype(str(FONT_PATH), 22)
    glyph_font = ImageFont.truetype(str(FONT_PATH), 112)
    label_font = ImageFont.truetype(str(FONT_PATH), 17)
    draw.text((margin, 38), "荃方位補寫體 1.010 — 使用者手寫平假名 SVG 驗收", font=title, fill="#35215f")
    draw.text((margin, 96), "上：原始手寫稿　下：實際由建置後 TTF 渲染的 43 個 SVG 來源字形", font=note, fill="#5e5264")
    draw.text((margin, grid_y - 48), "Built TTF rendering · same baseline and advance", font=note, fill="#6d35c5")

    for row_index, row in enumerate(ROWS):
        for column, character in enumerate(row):
            x = grid_x + column * cell_w
            y = grid_y + row_index * cell_h
            draw.rectangle((x, y, x + cell_w, y + cell_h), outline="#d7d7dc", width=2, fill="#ffffff")
            if not character:
                continue
            draw.text((x + 8, y + 7), f"{character} U+{ord(character):04X}", font=label_font, fill="#807584")
            baseline = y + 128
            draw.line((x + 12, baseline, x + cell_w - 12, baseline), fill="#e8a5b2", width=1)
            draw.text((x + cell_w / 2, baseline), character, font=glyph_font, fill="#111111", anchor="ms")

    draw.text(
        (margin, height - 55),
        "來源圖未包含 わ・を・ん；這三字、片假名與歷史假名維持既有設計。濁音會以新 SVG 基底組合。",
        font=note,
        fill="#5e5264",
    )
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH, "PNG", optimize=True)
    print(f"Rendered {PROOF_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
