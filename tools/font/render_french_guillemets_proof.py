#!/usr/bin/env python3
"""Render native-only French guillemets; Pillow/FreeType has no font fallback."""
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF = ROOT / "tools/font/proofs/quanfangwei-french-guillemets.png"
SIZES = (16, 20, 32, 64, 192)
SAMPLES = (
    "«     »",
    "<  «  »",
    ">  «  »",
    "« je t’aime »",
    "personne ne murmure « je t’aime »",
    "et pleins d’ennuis, personne ne murmure « je t’aime »",
    "« Bonjour »",
    "« Hélène »",
    "« C’est la vie »",
)
TITLE = "QuanFangwei 1.031 / French guillemets / native font only"
NOTE = "Source < > components / 327 unit advance / no fallback"


def validate_coverage():
    with TTFont(FONT) as font:
        cmap = font.getBestCmap()
        assert cmap.get(0xAB) == "guillemotleft"
        assert cmap.get(0xBB) == "guillemotright"
        text = TITLE + NOTE + " ".join(SAMPLES) + "16 px20 px32 px64 px192 px diagnostic"
        missing = sorted({ord(c) for c in text if not cmap.get(ord(c)) or cmap[ord(c)] == ".notdef"})
        assert not missing, f"Proof would contain missing glyphs: {missing}"


def main():
    validate_coverage()
    fonts = {size: ImageFont.truetype(str(FONT), size) for size in SIZES}
    # Render true pixel sizes. The 192 px sentence determines the canvas width;
    # do not shrink the diagnostic or silently wrap the requested sentence.
    width = max(1400, int(max(fonts[192].getlength(s) for s in SAMPLES)) + 120)
    heights = {size: max(32, round(size * 1.15)) for size in SIZES}
    height = 150 + sum(65 + len(SAMPLES) * heights[size] for size in SIZES)
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    label = ImageFont.truetype(str(FONT), 26)
    draw.text((40, 25), TITLE, font=fonts[32], fill="#24152d")
    draw.text((40, 73), NOTE, font=label, fill="#665570")
    top = 140
    for size in SIZES:
        draw.line((40, top, width - 40, top), fill="#dbcedf", width=1)
        draw.text((40, top + 10), f"{size} px" + (" diagnostic" if size == 192 else ""), font=label, fill="#665570")
        baseline = top + 50 + round(size * .9)
        for text in SAMPLES:
            draw.text((40, baseline), text, font=fonts[size], fill="#18131b", anchor="ls")
            baseline += heights[size]
        top += 65 + len(SAMPLES) * heights[size]
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF)
    print(f"PASS: every proof character has native coverage; only {FONT.name} is loaded")
    print(f"Wrote {PROOF.relative_to(ROOT)} ({width} x {height})")


if __name__ == "__main__":
    main()
