#!/usr/bin/env python3
"""Render U+5965 before/after metric overlays for optical QA."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "proofs/quanfangwei-oku-optical-diagnostic-proof.png"
REFERENCE_CENTER_Y = 354.0
PAPER = "#fffdf9"
INK = "#251c36"
MUTED = "#72677e"
ADVANCE = "#3778bf"
BOUNDS = "#c13f74"
CENTER = "#16856b"
REFERENCE = "#d17a22"
BASELINE = "#9a91a5"


def face(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def measure(path: Path, character: str) -> dict[str, object]:
    with TTFont(path, recalcTimestamp=False) as font:
        glyph_name = font.getBestCmap()[ord(character)]
        pen = BoundsPen(font.getGlyphSet())
        font.getGlyphSet()[glyph_name].draw(pen)
        if pen.bounds is None:
            raise RuntimeError(f"{character} has no ink bounds")
        advance, lsb = font["hmtx"].metrics[glyph_name]
        x_min, y_min, x_max, y_max = pen.bounds
        return {
            "glyph_name": glyph_name,
            "character": character,
            "bounds": pen.bounds,
            "advance": advance,
            "lsb": lsb,
            "rsb": advance - lsb - (x_max - x_min),
            "upm": font["head"].unitsPerEm,
            "ascent": font["hhea"].ascent,
            "descent": font["hhea"].descent,
        }


def panel(draw: ImageDraw.ImageDraw, path: Path, data: dict[str, object], left: int, title: str) -> None:
    size = 600
    scale = size / float(data["upm"])
    origin_x = left + 220
    baseline_y = 930
    advance = float(data["advance"])
    x_min, y_min, x_max, y_max = (float(value) for value in data["bounds"])
    ascent = float(data["ascent"])
    descent = float(data["descent"])

    draw.text((left + 30, 185), title, font=face(path, 30), fill=INK)
    draw.text(
        (left + 30, 235),
        f"glyph={data['glyph_name']}  bounds=({x_min:.0f}, {y_min:.0f}, {x_max:.0f}, {y_max:.0f})",
        font=face(path, 17),
        fill=MUTED,
    )
    draw.text(
        (left + 30, 270),
        f"ink={x_max - x_min:.2f} x {y_max - y_min:.2f}  center=({(x_min + x_max) / 2:.2f}, {(y_min + y_max) / 2:.2f})  advance={advance:.0f}  LSB/RSB={data['lsb']}/{data['rsb']:.0f}",
        font=face(path, 16),
        fill=MUTED,
    )

    advance_box = (
        origin_x,
        baseline_y - ascent * scale,
        origin_x + advance * scale,
        baseline_y - descent * scale,
    )
    ink_box = (
        origin_x + x_min * scale,
        baseline_y - y_max * scale,
        origin_x + x_max * scale,
        baseline_y - y_min * scale,
    )
    center_x = origin_x + ((x_min + x_max) / 2) * scale
    center_y = baseline_y - ((y_min + y_max) / 2) * scale
    reference_y = baseline_y - REFERENCE_CENTER_Y * scale

    draw.rectangle(advance_box, outline=ADVANCE, width=4)
    draw.line((origin_x - 40, baseline_y, origin_x + advance * scale + 40, baseline_y), fill=BASELINE, width=3)
    draw.line((origin_x - 40, reference_y, origin_x + advance * scale + 40, reference_y), fill=REFERENCE, width=4)
    draw.text((origin_x + advance * scale + 52, reference_y - 15), "奧 center y=354", font=face(path, 18), fill=REFERENCE)
    draw.text((origin_x + advance * scale + 52, baseline_y - 15), "baseline", font=face(path, 18), fill=BASELINE)
    draw.text((origin_x, baseline_y), str(data["character"]), font=face(path, size), fill=INK, anchor="ls")
    draw.rectangle(ink_box, outline=BOUNDS, width=4)
    draw.ellipse((center_x - 10, center_y - 10, center_x + 10, center_y + 10), fill=CENTER)
    draw.line((center_x - 22, center_y, center_x + 22, center_y), fill=CENTER, width=3)
    draw.line((center_x, center_y - 22, center_x, center_y + 22), fill=CENTER, width=3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-font", type=Path, required=True)
    parser.add_argument("--after-font", type=Path, default=CURRENT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.before_font.is_file() or not args.after_font.is_file():
        raise SystemExit("Both before/after TTF files must exist")

    image = Image.new("RGB", (3700, 1280), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "U+5965 奥 vs U+5967 奧 — optical metric diagnostic", font=face(args.after_font, 42), fill=INK)
    draw.text((55, 95), "Blue: advance box   Pink: ink bounds   Green: ink center   Orange: authoritative 奧 center y=354", font=face(args.after_font, 22), fill=MUTED)
    panel(draw, args.before_font, measure(args.before_font, "奥"), 55, "Before 奥 — origin/main 1.018")
    panel(draw, args.after_font, measure(args.after_font, "奧"), 1260, "Reference 奧 — authoritative target")
    panel(draw, args.after_font, measure(args.after_font, "奥"), 2465, "After 奥 — optical derived copy 1.020")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
