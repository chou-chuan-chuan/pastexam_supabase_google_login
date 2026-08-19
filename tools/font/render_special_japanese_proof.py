#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_DIR = REPO_ROOT / "tools/font/proofs"
PROOF_PATH = PROOF_DIR / "quanfangwei-stable-1.013-control-proof.png"
MIXED_PATH = PROOF_DIR / "quanfangwei-stable-1.013-mixed-proof.png"
SIZES = [16, 20, 24, 32, 48, 72]

def render(path, lines):
    width = 2400
    heights = [95 + len(lines) * max(52, round(size * 1.6)) for size in SIZES]
    image = Image.new("RGB", (width, 120 + sum(heights)), "white")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT_PATH), 38)
    label = ImageFont.truetype(str(FONT_PATH), 20)
    draw.text((55, 35), "QuanFangwei 1.013 stable release control", font=title, fill="black")
    y = 105
    for size, block_h in zip(SIZES, heights):
        face = ImageFont.truetype(str(FONT_PATH), size)
        step = max(52, round(size * 1.6))
        draw.text((55, y + 6), f"{size} px", font=label, fill="black")
        baseline = y + 50 + size
        for line in lines:
            draw.line((150, baseline + 3, width - 50, baseline + 3), fill=(215,215,215), width=1)
            draw.text((170, baseline), line, font=face, fill="black", anchor="ls")
            baseline += step
        y += block_h
    image.save(path, "PNG", optimize=True)

def main():
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    render(PROOF_PATH, [
        "す　り　懐　々",
        "日々　時々　人々　色々",
        "懐　夕　（source glyph controls）",
    ])
    render(MIXED_PATH, [
        "懐かしい風が頬を撫でて",
        "日々の思い出を今も胸に抱いて",
        "時々君の香りを思い出す",
        "君の香りを今も想ってる",
        "足元の花に気付けないまま",
    ])
    print("Rendered", PROOF_PATH)
    print("Rendered", MIXED_PATH)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
