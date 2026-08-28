#!/usr/bin/env python3
"""Render the U+5965 奥 optical-alignment before/after proof."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "proofs/quanfangwei-oku-optical-alignment-proof.png"
SIZES = (16, 20, 24, 32, 48, 72)
LINES = ("奥", "奧", "奥奧", "目の奥奧に", "目の奥奧にずっと写るシルエット")
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

    image = Image.new("RGB", (2600, 2600), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((55, 34), "U+5965 奥 — optical alignment", font=face(args.after_font, 42), fill=INK)
    draw.text(
        (55, 92),
        "U+5967 奧 is the primary reference | scale 0.895 | dx +10.5 | dy +34 | 8-unit weight compensation",
        font=face(args.after_font, 22),
        fill=MUTED,
    )
    draw.text((190, 150), "Before (origin/main 1.018)", font=face(args.after_font, 27), fill=MUTED)
    draw.text((1410, 150), "After (optical derived copy 1.019)", font=face(args.after_font, 27), fill=ACCENT)
    draw.line((55, 200, 2545, 200), fill=GRID, width=2)

    y = 235
    for size in SIZES:
        draw.text((55, y + 5), f"{size}px", font=face(args.after_font, 20), fill=MUTED)
        for text in LINES:
            baseline = y + max(size, 26)
            draw.line((180, baseline, 2520, baseline), fill="#eee8f2", width=1)
            draw.text((190, baseline), text, font=face(args.before_font, size), fill=INK, anchor="ls")
            draw.text((1410, baseline), text, font=face(args.after_font, size), fill=INK, anchor="ls")
            y += max(size + 22, 52)
        y += 24

    draw.text(
        (55, 2550),
        "Proof strings: 奥 / 奧 / 奥奧 / 目の奥奧に / 目の奥奧にずっと写るシルエット",
        font=face(args.after_font, 20),
        fill=MUTED,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
