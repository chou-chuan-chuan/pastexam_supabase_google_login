#!/usr/bin/env python3
"""Render the Version 1.044/1.045 Katakana WO junction comparison."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
OUTPUT = ROOT / "tools/font/proofs/quanfangwei-katakana-wo-junction.png"
PREVIOUS_COMMIT = "6cf7b42e031d7e85836156ff8eaefd21061b0435"
REL = "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"


def sample(font_bytes: bytes, text: str, size: int, width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(BytesIO(font_bytes), size)
    box = draw.textbbox((0, 0), text, font=font)
    x = (width - (box[2] - box[0])) // 2 - box[0]
    y = (height - (box[3] - box[1])) // 2 - box[1]
    draw.text((x, y), text, font=font, fill="#171923")
    return image


def main() -> None:
    before = subprocess.check_output(["git", "show", f"{PREVIOUS_COMMIT}:{REL}"], cwd=ROOT)
    after = CURRENT.read_bytes()
    image = Image.new("RGB", (1600, 1300), "#f5f1e9")
    draw = ImageDraw.Draw(image)
    label = lambda size: ImageFont.load_default(size=size)
    draw.text((42, 28), "QuanFangwei Supplement Script 1.045 | Katakana WO upper-right junction", font=label(30), fill="#26333b")
    draw.text((42, 72), "The descending main stroke now starts at the end of the upper horizontal. Lower horizontal and 960-unit advance remain.", font=label(21), fill="#66747b")

    columns = ((before, "1.044 BEFORE | detached top"), (after, "1.045 AFTER | connected top"))
    for index, (font_bytes, heading) in enumerate(columns):
        left = 42 + index * 770
        draw.text((left, 122), heading, font=label(25), fill="#8a3f52" if index == 0 else "#24684e")
        large = sample(font_bytes, "ヲ", 430, 700, 500)
        image.paste(large, (left, 160))
        draw.rectangle((left, 160, left + 700, 660), outline="#d5cec3", width=2)

        close = sample(font_bytes, "ヲ", 760, 1000, 900)
        crop = close.crop((430, 80, 920, 470)).resize((700, 300), Image.Resampling.LANCZOS)
        image.paste(crop, (left, 690))
        draw.rectangle((left, 690, left + 700, 990), outline="#d5cec3", width=2)

    draw.text((42, 1018), "Actual small-size rendering", font=label(25), fill="#26333b")
    small_text = "ヲ  ラ  ヲラ  カヲ  ラヲ  ヲヺ"
    for row, size in enumerate((16, 24, 32, 64)):
        y = 1060 + row * 38
        draw.text((42, y), f"{size}px", font=label(18), fill="#66747b")
        before_font = ImageFont.truetype(BytesIO(before), size)
        after_font = ImageFont.truetype(BytesIO(after), size)
        draw.text((120, y), small_text, font=before_font, fill="#8a3f52")
        draw.text((830, y), small_text, font=after_font, fill="#24684e")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, optimize=True)
    print(f"Rendered {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
