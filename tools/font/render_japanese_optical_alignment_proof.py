#!/usr/bin/env python3
"""Render the Version 1.015 す/Han optical-alignment review proof."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "proofs/quanfangwei-japanese-optical-alignment-proof.png"
SIZES = (16, 20, 24, 32, 48, 72)
INK = "#251c36"
MUTED = "#72677e"
ACCENT = "#d95a84"
GRID = "#ddd5e7"
PAPER = "#fffdf9"


def face(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def draw_text_row(
    draw: ImageDraw.ImageDraw,
    before_font: Path,
    after_font: Path,
    y: int,
    size: int,
    text: str,
) -> int:
    draw.text((45, y), f"{size}px", font=face(after_font, 21), fill=MUTED)
    draw.text((180, y), text, font=face(before_font, size), fill=INK)
    draw.text((1430, y), text, font=face(after_font, size), fill=INK)
    return y + max(size + 28, 58)


def draw_glyph_cell(
    draw: ImageDraw.ImageDraw,
    font_path: Path,
    x: int,
    y: int,
    character: str,
    label: str,
) -> None:
    width = 240
    height = 240
    baseline = y + 185
    draw.rounded_rectangle((x, y, x + width, y + height), radius=18, outline=GRID, width=2, fill="#ffffff")
    draw.line((x + 20, baseline, x + width - 20, baseline), fill="#ead7df", width=2)
    draw.text((x + width / 2, baseline), character, font=face(font_path, 170), fill=INK, anchor="ms")
    draw.text((x + width / 2, y + 218), label, font=face(font_path, 21), fill=MUTED, anchor="mm")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-font", type=Path, required=True)
    parser.add_argument("--after-font", type=Path, default=CURRENT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.before_font.is_file() or not args.after_font.is_file():
        raise SystemExit("Both before/after TTF files must exist")

    image = Image.new("RGB", (2700, 3320), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(args.after_font, 42)
    heading = face(args.after_font, 30)
    label = face(args.after_font, 23)

    draw.text((45, 30), "Version 1.015 — Japanese glyph optical alignment", font=title, fill="#42245e")
    draw.text((45, 88), "Before: accepted Version 1.014", font=label, fill=MUTED)
    draw.text((1430, 88), "After: topology/source-preserving transforms", font=label, fill=ACCENT)
    draw.line((45, 128, 2655, 128), fill=GRID, width=2)

    draw.text((45, 155), "U+3059 す — horizontal width only", font=heading, fill="#42245e")
    draw.text((45, 198), "scale_x 1.04 → 1.60  |  scale_y 1.04 unchanged  |  optical center shifted right and down", font=label, fill=MUTED)
    draw_glyph_cell(draw, args.before_font, 360, 245, "す", "before")
    draw_glyph_cell(draw, args.after_font, 1610, 245, "す", "after")

    y = 555
    draw.text((180, y), "Before", font=label, fill=MUTED)
    draw.text((1430, y), "After", font=label, fill=ACCENT)
    y += 44
    for size in SIZES:
        y = draw_text_row(draw, args.before_font, args.after_font, y, size, "影を残すから")
    draw.text((180, y + 4), "雲がまだ二人の影を残すから", font=face(args.before_font, 40), fill=INK)
    draw.text((1430, y + 4), "雲がまだ二人の影を残すから", font=face(args.after_font, 40), fill=INK)
    y += 74
    draw.text((180, y), "す　す　す", font=face(args.before_font, 72), fill=INK)
    draw.text((1430, y), "す　す　す", font=face(args.after_font, 72), fill=INK)
    y += 120
    draw.line((45, y, 2655, y), fill=GRID, width=2)

    y += 28
    draw.text((45, y), "Shared Han optical copies — source outlines and advances preserved", font=heading, fill="#42245e")
    y += 48
    draw.text((45, y), "恋 .98/+17.5/+35   哀 .93/+15.5/+36   奧 .94/+19/+34.5   優 .90/+19.5/+35   寄 .92/+18.5/+36", font=label, fill=MUTED)
    y += 48
    for index, character in enumerate("恋哀奧優寄"):
        x_before = 50 + index * 260
        x_after = 1400 + index * 250
        draw_glyph_cell(draw, args.before_font, x_before, y, character, "before")
        draw_glyph_cell(draw, args.after_font, x_after, y, character, "after")
    y += 300
    draw.text((180, y), "哀　奧　優　寄", font=face(args.before_font, 72), fill=INK)
    draw.text((1430, y), "哀　奧　優　寄", font=face(args.after_font, 72), fill=INK)
    y += 104
    draw.text((180, y), "Before", font=label, fill=MUTED)
    draw.text((1430, y), "After", font=label, fill=ACCENT)
    y += 42
    for size in SIZES:
        y = draw_text_row(draw, args.before_font, args.after_font, y, size, "君が恋しい　君が恋しい")
        y = draw_text_row(draw, args.before_font, args.after_font, y, size, "哀しみを抱いて　奧深い森を歩く")
        y = draw_text_row(draw, args.before_font, args.after_font, y, size, "優しい風が吹く　寄り添う二人")

    draw.text((45, 3275), "Review codepoints: す U+3059 / 恋 U+604B / 哀 U+54C0 / 奧 U+5967 / 優 U+512A / 寄 U+5BC4 — 奥 U+5965 unchanged", font=face(args.after_font, 19), fill=MUTED)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
