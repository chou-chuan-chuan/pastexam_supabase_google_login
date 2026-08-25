#!/usr/bin/env python3
"""Render a compact before/after proof for U+5BB9 容."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "proofs/quanfangwei-yong-alignment-proof.png"
SIZES = (16, 20, 24, 32, 48, 72)
LINES = ("容", "笑容", "不管笑容變成什麼模樣", "你還是你啊")
PAPER = "#fffdf9"
INK = "#251c36"
MUTED = "#72677e"
ACCENT = "#b33f6a"
GRID = "#ddd5e7"


def face(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-font", type=Path, required=True)
    parser.add_argument("--after-font", type=Path, default=CURRENT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.before_font.is_file() or not args.after_font.is_file():
        raise SystemExit("Both before/after TTF files must exist")

    image = Image.new("RGB", (2400, 2040), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "U+5BB9 容 — optical alignment", font=face(args.after_font, 44), fill=INK)
    draw.text((55, 96), "Source drawing preserved | scale 1.00 / 1.00 | dx +19.45 | dy +35 | advance 872 unchanged", font=face(args.after_font, 23), fill=MUTED)
    draw.text((190, 155), "Before (Version 1.017)", font=face(args.after_font, 28), fill=MUTED)
    draw.text((1300, 155), "After (Version 1.018)", font=face(args.after_font, 28), fill=ACCENT)
    draw.line((55, 205, 2345, 205), fill=GRID, width=2)

    y = 250
    for size in SIZES:
        draw.text((55, y), f"{size}px", font=face(args.after_font, 21), fill=MUTED)
        for text in LINES:
            baseline = y + max(size, 26)
            draw.line((180, baseline, 2320, baseline), fill="#eee8f2", width=1)
            draw.text((190, baseline), text, font=face(args.before_font, size), fill=INK, anchor="ls")
            draw.text((1300, baseline), text, font=face(args.after_font, size), fill=INK, anchor="ls")
            y += max(size + 22, 54)
        y += 28

    draw.text((55, 1995), "Proof strings: 容 / 笑容 / 不管笑容變成什麼模樣 / 你還是你啊", font=face(args.after_font, 20), fill=MUTED)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
