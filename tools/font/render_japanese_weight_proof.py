#!/usr/bin/env python3
"""Render the single Stage-A Japanese stroke-weight review sheet."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from audit_japanese_weight import (
    CURRENT_FONT,
    JAPANESE_MARKS,
    KATAKANA,
    LARGE_HIRAGANA,
    SMALL_HIRAGANA,
    SOURCE_HAN,
    dehinted_source,
)


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "proofs/quanfangwei-japanese-weight-before-after-proof.png"
SIZES = (16, 20, 24, 32, 48, 72)
PAPER = "#fffdf9"
INK = "#211b28"
MUTED = "#716978"
ACCENT = "#b63866"
GRID = "#ddd5e3"
WIDTH = 3400
LEFT_X = 180
RIGHT_X = 1750
LYRICS = (
    "無茶苦茶に走り続けた",
    "今日も明日も生きて行こう",
    "雲がまだ二人の影を残すから",
    "君が恋しい",
    "可哀想なふりをして",
    "足元の花に気付けないまま",
)


def face(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def chunks(text: str, length: int) -> tuple[str, ...]:
    return tuple(text[index:index + length] for index in range(0, len(text), length))


def heading(draw: ImageDraw.ImageDraw, font_path: Path, y: int, title: str, note: str) -> int:
    draw.line((40, y, WIDTH - 40, y), fill=GRID, width=2)
    draw.text((50, y + 22), title, font=face(font_path, 34), fill="#45255d")
    draw.text((50, y + 70), note, font=face(font_path, 20), fill=MUTED)
    return y + 112


def before_after_labels(draw: ImageDraw.ImageDraw, font_path: Path, y: int) -> int:
    draw.text((LEFT_X, y), "Before — Version 1.016 main", font=face(font_path, 22), fill=MUTED)
    draw.text((RIGHT_X, y), "After — pressure-only normalization", font=face(font_path, 22), fill=ACCENT)
    return y + 40


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-font", type=Path, required=True)
    parser.add_argument("--after-font", type=Path, default=CURRENT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.before_font.is_file() or not args.after_font.is_file():
        raise SystemExit("Both before/after TTF files must exist")

    image = Image.new("RGB", (WIDTH, 10500), PAPER)
    draw = ImageDraw.Draw(image)
    title_font = face(args.after_font, 44)
    note_font = face(args.after_font, 20)
    draw.text((50, 28), "QuanFangwei Japanese stroke-weight harmonization — Stage A", font=title_font, fill="#45255d")
    draw.text((50, 88), "Same glyph topology and optical transforms; only stroke pressure changes. No CSS stroke or synthesis.", font=note_font, fill=MUTED)

    with tempfile.TemporaryDirectory(prefix="qfw-weight-proof-") as temp_dir:
        source_raster = Path(temp_dir) / "ChenYuluoyan-dehinted.ttf"
        dehinted_source(source_raster)
        y = heading(draw, args.after_font, 135, "Proof 1 — source Han vs Hiragana vs Katakana", "Same nominal px size and rasterizer; official source uses a temporary dehinted raster copy only.")
        for size in SIZES:
            step = max(54, size + 20)
            draw.text((50, y), f"{size}px", font=note_font, fill=ACCENT)
            draw.text((150, y), "Source Han", font=note_font, fill=MUTED)
            draw.text((410, y), SOURCE_HAN, font=face(source_raster, size), fill=INK)
            draw.text((1600, y), "Hiragana", font=note_font, fill=MUTED)
            draw.text((1830, y), LARGE_HIRAGANA[:20], font=face(args.after_font, size), fill=INK)
            y += step
            draw.text((150, y), "Katakana", font=note_font, fill=MUTED)
            draw.text((410, y), KATAKANA[:30], font=face(args.after_font, size), fill=INK)
            y += step + 10

    y = heading(draw, args.after_font, y + 8, "Proof 2 — complete 46 accepted Hiragana", "Before/after side by side; point topology and outer optical transforms are unchanged.")
    y = before_after_labels(draw, args.after_font, y)
    for line in chunks(LARGE_HIRAGANA, 16):
        draw.text((LEFT_X, y), line, font=face(args.before_font, 58), fill=INK)
        draw.text((RIGHT_X, y), line, font=face(args.after_font, 58), fill=INK)
        y += 78
    for size in SIZES:
        sample = "あいうえお けこす をるわ"
        draw.text((50, y), f"{size}px", font=note_font, fill=ACCENT)
        draw.text((LEFT_X, y), sample, font=face(args.before_font, size), fill=INK)
        draw.text((RIGHT_X, y), sample, font=face(args.after_font, size), fill=INK)
        y += max(52, size + 18)

    y = heading(draw, args.after_font, y + 8, "Proof 3 — small Hiragana vs normalized large bases", "Small kana remain 0.72-size derivations; inherited pressure compensation prevents a separate thin weight.")
    y = before_after_labels(draw, args.after_font, y)
    large_small = "やゆよつあいうえお　ゃゅょっぁぃぅぇぉ"
    for size in SIZES:
        draw.text((50, y), f"{size}px", font=note_font, fill=ACCENT)
        draw.text((LEFT_X, y), large_small, font=face(args.before_font, size), fill=INK)
        draw.text((RIGHT_X, y), large_small, font=face(args.after_font, size), fill=INK)
        y += max(54, size + 20)
    draw.text((LEFT_X, y), SMALL_HIRAGANA, font=face(args.before_font, 72), fill=INK)
    draw.text((RIGHT_X, y), SMALL_HIRAGANA, font=face(args.after_font, 72), fill=INK)
    y += 100

    y = heading(draw, args.after_font, y + 8, "Proof 4 — complete Katakana and Japanese marks", "Katakana uses one pressure layer; dakuten, handakuten, and long sound mark are separately calibrated.")
    y = before_after_labels(draw, args.after_font, y)
    for line in chunks(KATAKANA, 18):
        draw.text((LEFT_X, y), line, font=face(args.before_font, 48), fill=INK)
        draw.text((RIGHT_X, y), line, font=face(args.after_font, 48), fill=INK)
        y += 66
    mark_line = "゙ ゚ ゛ ゜ ゝ ゞ ヽ ヾ 々 ・ ー"
    draw.text((LEFT_X, y), mark_line, font=face(args.before_font, 64), fill=INK)
    draw.text((RIGHT_X, y), mark_line, font=face(args.after_font, 64), fill=INK)
    y += 92
    for size in SIZES:
        sample = "カタカナ ヴ ガ パ　" + JAPANESE_MARKS
        draw.text((50, y), f"{size}px", font=note_font, fill=ACCENT)
        draw.text((LEFT_X, y), sample, font=face(args.before_font, size), fill=INK)
        draw.text((RIGHT_X, y), sample, font=face(args.after_font, size), fill=INK)
        y += max(54, size + 20)

    y = heading(draw, args.after_font, y + 8, "Proof 5 — real mixed lyrics", "All required lines at 16/20/24/32/48/72 px; same baseline, no CSS adjustment.")
    y = before_after_labels(draw, args.after_font, y)
    for size in SIZES:
        draw.text((50, y), f"{size}px", font=note_font, fill=ACCENT)
        line_step = max(48, round(size * 1.35))
        for lyric in LYRICS:
            draw.line((LEFT_X, y + size + 3, WIDTH - 50, y + size + 3), fill="#eee8f0", width=1)
            draw.text((LEFT_X, y), lyric, font=face(args.before_font, size), fill=INK)
            draw.text((RIGHT_X, y), lyric, font=face(args.after_font, size), fill=INK)
            y += line_step
        y += 24

    image = image.crop((0, 0, WIDTH, min(image.height, y + 55)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, "PNG", optimize=True)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
