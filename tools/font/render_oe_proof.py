#!/usr/bin/env python3
"""Render a focused multi-size proof for native uppercase/lowercase OE ligatures."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-oe-proof.png"
SIZES = (18, 28, 44, 72, 120)
WORDS = "cœur   sœur   œuvre   bœuf   vœu"
CAPITAL_WORDS = "Œuvre   ŒUVRE   Œuvre / œuvre"


def glyph_bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {glyph_name} has no outline")
    return tuple(round(value) for value in pen.bounds)


def main() -> None:
    ttfont = TTFont(FONT_PATH, recalcTimestamp=False)
    cmap = ttfont.getBestCmap()
    expected = {0x0152: "OE", 0x0153: "oe"}
    for codepoint, glyph_name in expected.items():
        if cmap.get(codepoint) != glyph_name:
            raise RuntimeError(f"U+{codepoint:04X} is not rendered by QuanFangwei: {cmap.get(codepoint)!r}")
    metrics = {}
    for codepoint, glyph_name in expected.items():
        glyph_box = glyph_bounds(ttfont, glyph_name)
        advance, lsb = ttfont["hmtx"].metrics[glyph_name]
        metrics[codepoint] = (glyph_box, advance, lsb, advance - glyph_box[2])
    ttfont.close()

    image = Image.new("RGB", (2000, 1900), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 44)
    info_font = ImageFont.truetype(str(FONT_PATH), 24)
    draw.text((60, 48), "QuanFangwei Version 1.021 — French Œ / œ proof", font=title_font, fill="#24152d")
    upper_bounds, upper_advance, upper_lsb, upper_rsb = metrics[0x0152]
    lower_bounds, lower_advance, lower_lsb, lower_rsb = metrics[0x0153]
    draw.text(
        (60, 110),
        f"U+0152 → OE   bounds={upper_bounds}   advance={upper_advance}   LSB/RSB={upper_lsb}/{upper_rsb}",
        font=info_font,
        fill="#5f456a",
    )
    draw.text(
        (60, 145),
        f"U+0153 → oe   bounds={lower_bounds}   advance={lower_advance}   LSB/RSB={lower_lsb}/{lower_rsb}",
        font=info_font,
        fill="#5f456a",
    )

    y = 205
    for size in SIZES:
        font = ImageFont.truetype(str(FONT_PATH), size)
        row_height = max(175, round(size * 2.15))
        lower_baseline = y + round(row_height * 0.43)
        upper_baseline = y + round(row_height * 0.84)
        draw.line((55, lower_baseline, 1945, lower_baseline), fill="#d5bfe0", width=1)
        draw.line((55, upper_baseline, 1945, upper_baseline), fill="#eadff0", width=1)
        draw.text((60, y + 8), f"{size}px", font=info_font, fill="#765b80")
        draw.text((155, lower_baseline), "œ   Œ", font=font, fill="#161018", anchor="ls")
        draw.text((420, lower_baseline), WORDS, font=font, fill="#161018", anchor="ls")
        draw.text((420, upper_baseline), CAPITAL_WORDS, font=font, fill="#161018", anchor="ls")
        y += row_height

    compare_font = ImageFont.truetype(str(FONT_PATH), 76)
    draw.rounded_rectangle((55, y + 10, 1945, y + 280), radius=18, outline="#c7aed4", width=2, fill="#fbf5fd")
    draw.text((80, y + 45), "spacing comparison:", font=info_font, fill="#765b80")
    draw.text((420, y + 120), "o e     oe     œ", font=compare_font, fill="#161018", anchor="ls")
    draw.text((420, y + 225), "O E     OE     Œ", font=compare_font, fill="#161018", anchor="ls")
    y += 310

    phrase_font = ImageFont.truetype(str(FONT_PATH), 52)
    draw.text((60, y + 55), "Personne ne fait battre mon cœur", font=phrase_font, fill="#161018")
    draw.text((60, y + 125), "Œuvre / œuvre", font=phrase_font, fill="#161018")

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH)
    print(f"PASS: U+0152 maps to OE and U+0153 maps to oe in {FONT_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
