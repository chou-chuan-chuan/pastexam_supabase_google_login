#!/usr/bin/env python3
"""Render Version 1.012 close-up and mixed-text review proofs."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_DIR = Path(__file__).resolve().parent / "proofs"
OUT = PROOF_DIR / "quanfangwei-special-japanese-1.012-proof.png"
MIXED = PROOF_DIR / "quanfangwei-special-japanese-1.012-mixed-proof.png"


def render_closeup() -> None:
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 2400, 1500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    label = ImageFont.truetype(str(FONT_PATH), 24)
    face = ImageFont.truetype(str(FONT_PATH), 170)
    draw.text((60, 45), "QuanFangwei 1.012 — special Japanese review", font=title, fill="black")
    rows = [
        ("す    り    懐    夕", "kana counter / tail + maintainer Han rewrites"),
        ("気 付 け", "mixed optical alignment close-up"),
        ("懐かしい風が頬を撫でて", "Japanese phrase using 懐"),
        ("君の香りを今も想ってる", "Japanese phrase using り"),
    ]
    y = 220
    for text, note in rows:
        baseline = y + 190
        draw.line((160, baseline, width - 80, baseline), fill="#bbbbbb", width=2)
        draw.text((180, baseline), text, font=face, fill="black", anchor="ls")
        draw.text((180, y + 10), note, font=label, fill="#555555")
        y += 300
    image.save(OUT, "PNG", optimize=True)


def render_mixed() -> None:
    width = 3000
    sizes = [24, 32, 48, 72, 120]
    lines = [
        "足元の花に気付けないまま",
        "懐かしい風が頬を撫でて",
        "君の香りを今も想ってる",
        "すり　気付け　懐夕",
    ]
    heights = [120 + len(lines) * max(62, int(size * 1.6)) for size in sizes]
    image = Image.new("RGB", (width, 120 + sum(heights)), "white")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    label = ImageFont.truetype(str(FONT_PATH), 22)
    draw.text((55, 38), "QuanFangwei 1.012 — mixed Japanese alignment proof", font=title, fill="black")
    y = 105
    for size, block in zip(sizes, heights):
        face = ImageFont.truetype(str(FONT_PATH), size)
        step = max(62, int(size * 1.6))
        draw.text((55, y + 10), f"{size}px", font=label, fill="#555555")
        baseline = y + 62 + size
        for line in lines:
            draw.line((160, baseline, width - 55, baseline), fill="#dddddd", width=1 if size < 72 else 2)
            draw.text((175, baseline), line, font=face, fill="black", anchor="ls")
            baseline += step
        y += block
    image.save(MIXED, "PNG", optimize=True)


def main() -> int:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Build font first: {FONT_PATH}")
    render_closeup(); render_mixed()
    print(f"Rendered {OUT.relative_to(REPO_ROOT)}")
    print(f"Rendered {MIXED.relative_to(REPO_ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
