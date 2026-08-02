#!/usr/bin/env python3
"""Render a visual proof using only the generated supplemental TTF."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-supplement-proof.png"
LINES = [
    "¿ ? ¿Qué canción?",
    "C Ç ÇA FRANÇAIS",
    "LEÇON GARÇON",
    "歌曲 ¿ Ç PDF",
    "聽見歌曲，也讀見每一句。",
]


def main() -> int:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Build the font first: {FONT_PATH}")
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(FONT_PATH), 72)
    label_font = ImageFont.truetype(str(FONT_PATH), 30)
    width = 1700
    margin = 72
    line_gap = 108
    height = margin * 2 + 70 + line_gap * len(LINES)
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    draw.text((margin, margin), "荃方位補寫體 · QuanFangwei Supplement Script", font=label_font, fill="#6d35c5")
    y = margin + 70
    for line in LINES:
        draw.text((margin, y), line, font=font, fill="#17121f")
        y += line_gap
    image.save(PROOF_PATH, "PNG", optimize=True)
    print(f"Rendered {PROOF_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
