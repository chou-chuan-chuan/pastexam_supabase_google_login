#!/usr/bin/env python3
"""Render the Version 1.016 け/う/こ before-and-after optical proof."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "proofs/quanfangwei-ke-u-optical-proof.png"
SIZES = (16, 20, 24, 32, 48, 72)
INK = "#251c36"
MUTED = "#72677e"
ACCENT = "#d95a84"
GRID = "#ddd5e7"
PAPER = "#fffdf9"


def face(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def glyph_cell(draw: ImageDraw.ImageDraw, font_path: Path, x: int, y: int,
               character: str, label: str) -> None:
    width, height = 260, 260
    baseline = y + 200
    draw.rounded_rectangle((x, y, x + width, y + height), radius=18,
                           outline=GRID, width=2, fill="#ffffff")
    draw.line((x + 20, baseline, x + width - 20, baseline), fill="#ead7df", width=2)
    draw.text((x + width / 2, baseline), character, font=face(font_path, 180),
              fill=INK, anchor="ms")
    draw.text((x + width / 2, y + 238), label, font=face(font_path, 20),
              fill=MUTED, anchor="mm")


def text_row(draw: ImageDraw.ImageDraw, before: Path, after: Path,
             y: int, size: int, text: str) -> int:
    draw.text((35, y), f"{size}px", font=face(after, 19), fill=MUTED)
    draw.text((145, y), text, font=face(before, size), fill=INK)
    draw.text((1260, y), text, font=face(after, size), fill=INK)
    return y + max(size + 26, 56)


def section(draw: ImageDraw.ImageDraw, before: Path, after: Path, y: int,
            character: str, codepoint: str, transform: str,
            samples: tuple[str, ...]) -> int:
    heading = face(after, 30)
    label = face(after, 22)
    draw.text((35, y), f"{codepoint} {character}", font=heading, fill="#42245e")
    draw.text((210, y + 4), transform, font=label, fill=MUTED)
    y += 52
    glyph_cell(draw, before, 330, y, character, "before")
    glyph_cell(draw, after, 1510, y, character, "after")
    y += 300
    draw.text((145, y), "Before", font=label, fill=MUTED)
    draw.text((1260, y), "After", font=label, fill=ACCENT)
    y += 42
    for size in SIZES:
        y = text_row(draw, before, after, y, size, samples[0])
    for sample in samples[1:]:
        draw.text((145, y), sample, font=face(before, 48), fill=INK)
        draw.text((1260, y), sample, font=face(after, 48), fill=INK)
        y += 78
    return y


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-font", type=Path, required=True)
    parser.add_argument("--after-font", type=Path, default=CURRENT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.before_font.is_file() or not args.after_font.is_file():
        raise SystemExit("Both before/after TTF files must exist")

    image = Image.new("RGB", (2400, 6900), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(args.after_font, 42)
    label = face(args.after_font, 22)
    draw.text((35, 28), "Version 1.016 — け / う / こ / 変 / わ review", font=title, fill="#42245e")
    draw.text((35, 88), "Before: accepted Version 1.015", font=label, fill=MUTED)
    draw.text((1260, 88), "After: topology-preserving outer transforms", font=label, fill=ACCENT)
    draw.line((35, 128, 2365, 128), fill=GRID, width=2)

    y = section(
        draw, args.before_font, args.after_font, 158,
        "け", "U+3051", "scale_x 1.00 → 1.06 | scale_y 1.00 | dx +28 | dy -26",
        ("無茶苦茶に走り続けた", "続けた", "け　け　け"),
    )
    draw.line((35, y + 12, 2365, y + 12), fill=GRID, width=2)
    y = section(
        draw, args.before_font, args.after_font, y + 44,
        "う", "U+3046", "scale_x 1.00 → 1.12 | scale_y 1.00 → 1.08 | dx 0 | dy -20",
        ("今日も明日も生きて行こう", "こう　行こう", "う　う　う"),
    )
    draw.line((35, y + 12, 2365, y + 12), fill=GRID, width=2)
    y = section(
        draw, args.before_font, args.after_font, y + 44,
        "こ", "U+3053", "scale_x 1.00 | scale_y 1.00 | dx +28 | dy 0",
        ("この声が届くまで", "こころ　この声", "こ　こ　こ"),
    )
    draw.line((35, y + 12, 2365, y + 12), fill=GRID, width=2)
    y = section(
        draw, args.before_font, args.after_font, y + 44,
        "変", "U+5909", "uniform scale 0.80 | dx +19.25 | dy +35 | embolden 8",
        ("くるくる変わる月の色を追い着く", "変わる　変化", "変　変　変"),
    )
    draw.line((35, y + 12, 2365, y + 12), fill=GRID, width=2)
    y = section(
        draw, args.before_font, args.after_font, y + 44,
        "わ", "U+308F", "Version 1.016 user-reference rewrite | 2 strokes | derived ゎ follows",
        ("くるくる変わる月の色を追い着く", "変わる　わたし", "わ　わ　わ", "わ　ゎ　わ　ゎ"),
    )
    draw.text((35, 6860),
              "The native 変 outline is preserved; わ is the sole reviewed handwritten topology rewrite and ゎ derives from it.",
              font=face(args.after_font, 18), fill=MUTED)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
