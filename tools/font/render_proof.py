#!/usr/bin/env python3
"""Render optical, natural-text, and glyph-analysis proofs for the derived font."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
SOURCE_FONT_PATH = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_DIR = TOOLS_DIR / "proofs"
OPTICAL_PROOF_PATH = PROOF_DIR / "quanfangwei-optical-proof.png"
NATURAL_PROOF_PATH = PROOF_DIR / "quanfangwei-natural-proof.png"
LEGACY_PROOF_PATH = PROOF_DIR / "quanfangwei-supplement-proof.png"
ANALYSIS_PROOF_PATH = PROOF_DIR / "quanfangwei-glyph-analysis.png"
ANALYSIS_JSON_PATH = PROOF_DIR / "quanfangwei-glyph-analysis.json"

SIZES = [16, 24, 32, 48, 72]
PROOF_LINES = [
    "? ¿ ? ¿",
    "C Ç C Ç",
    "¿Qué canción?   ¿Dónde estás?",
    "ÇA VA   FRANÇAIS   LEÇON   GARÇON",
    "歌曲 ¿ Ç PDF   聽見歌曲，也讀見每一句。",
]
ANALYSIS_CODEPOINTS = [0x003F, 0x00BF, 0x0043, 0x002C, 0x003B, 0x004A, 0x006A, 0x0067, 0x0079, 0x00B8, 0x00C7]


def glyph_bounds(font: TTFont, glyph_name: str) -> tuple[float, float, float, float]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        raise ValueError(f"Glyph {glyph_name!r} has no bounds")
    return tuple(round(value, 2) for value in pen.bounds)


def glyph_metrics(font: TTFont, codepoint: int) -> dict:
    glyph_name = font.getBestCmap().get(codepoint)
    if glyph_name is None:
        return {"character": chr(codepoint), "codepoint": f"U+{codepoint:04X}", "missing": True}
    bounds = glyph_bounds(font, glyph_name)
    advance, lsb = font["hmtx"].metrics[glyph_name]
    raw = font["glyf"][glyph_name]
    components = []
    contour_count = raw.numberOfContours
    if raw.isComposite():
        contour_count = 0
        components = [
            {
                "glyph": component.glyphName,
                "x": component.x,
                "y": component.y,
            }
            for component in raw.components
        ]
    cap_height = getattr(font["OS/2"], "sCapHeight", font["hhea"].ascent)
    return {
        "character": chr(codepoint),
        "codepoint": f"U+{codepoint:04X}",
        "glyph_name": glyph_name,
        "bounds": bounds,
        "advance_width": advance,
        "left_side_bearing": lsb,
        "right_side_bearing": round(advance - bounds[2], 2),
        "contour_count": contour_count,
        "components": components,
        "visual_bounds_center": [round((bounds[0] + bounds[2]) / 2, 2), round((bounds[1] + bounds[3]) / 2, 2)],
        "top_overshoot_from_cap_height": round(bounds[3] - cap_height, 2),
        "bottom_overshoot_below_baseline": round(max(0, -bounds[1]), 2),
        "distance_from_baseline": round(bounds[1], 2),
        "safe_space_to_ascender": round(font["hhea"].ascent - bounds[3], 2),
        "safe_space_to_descender": round(bounds[1] - font["hhea"].descent, 2),
    }


def render_analysis(source: TTFont, derived: TTFont) -> None:
    source_cmap = source.getBestCmap()
    analysis = {
        "font_metrics": {
            "units_per_em": derived["head"].unitsPerEm,
            "ascender": derived["hhea"].ascent,
            "descender": derived["hhea"].descent,
            "cap_height": getattr(derived["OS/2"], "sCapHeight", None),
            "x_height": getattr(derived["OS/2"], "sxHeight", None),
        },
        "glyphs": {},
    }
    for codepoint in ANALYSIS_CODEPOINTS:
        metric_font = source if codepoint in source_cmap else derived
        analysis["glyphs"][f"U+{codepoint:04X}"] = glyph_metrics(metric_font, codepoint)
    ANALYSIS_JSON_PATH.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    width, height = 1900, 1320
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 42)
    display_font = ImageFont.truetype(str(FONT_PATH), 132)
    label_font = ImageFont.truetype(str(FONT_PATH), 25)
    draw.text((70, 48), "荃方位補寫體：補寫字形分析", font=title_font, fill="#4f276c")

    tiles = [("question", "?"), ("questiondown", "¿"), ("C", "C"), ("Ccedilla", "Ç"), ("comma", ","), ("cedilla", "¸")]
    tile_y = 145
    tile_width = 280
    for index, (name, character) in enumerate(tiles):
        x = 70 + index * 300
        draw.rounded_rectangle((x, tile_y, x + tile_width, tile_y + 270), radius=18, outline="#d8c6e6", width=2, fill="#ffffff")
        baseline = tile_y + 190
        draw.line((x + 20, baseline, x + tile_width - 20, baseline), fill="#df5d74", width=2)
        draw.text((x + 65, baseline), character, font=display_font, fill="#17121f", anchor="ls")
        draw.text((x + 18, tile_y + 222), name, font=label_font, fill="#5e5264")

    rows = ["? ¿ ? ¿", "C Ç C Ç", ", ¸ , ¸", "; J j g y", "ÇA ¿Qué FRANÇAIS"]
    y = 485
    row_font = ImageFont.truetype(str(FONT_PATH), 92)
    for row in rows:
        baseline = y + 100
        draw.line((70, baseline, width - 70, baseline), fill="#e8a5b2", width=2)
        draw.text((90, baseline), row, font=row_font, fill="#17121f", anchor="ls")
        y += 155
    image.save(ANALYSIS_PROOF_PATH, "PNG", optimize=True)


def render_optical(derived: TTFont) -> None:
    upm = derived["head"].unitsPerEm
    ascender = derived["hhea"].ascent
    descender = derived["hhea"].descent
    width = 2200
    block_heights = []
    for size in SIZES:
        scale = size / upm
        line_step = max(38, round((ascender - descender) * scale + 12))
        block_heights.append(max(250, round(75 + (ascender - descender) * scale + (len(PROOF_LINES) - 1) * line_step)))
    height = 90 + sum(block_heights) + 80
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 36)
    label_font = ImageFont.truetype(str(FONT_PATH), 20)
    draw.text((60, 36), "Optical proof — baseline / ascender / descender / advance box", font=title_font, fill="#4f276c")

    y = 100
    for size, block_height in zip(SIZES, block_heights):
        font = ImageFont.truetype(str(FONT_PATH), size)
        scale = size / upm
        line_step = max(38, round((ascender - descender) * scale + 12))
        draw.text((60, y + 4), f"{size} px", font=label_font, fill="#6d35c5")
        baseline = y + 40 + round(ascender * scale)
        for line in PROOF_LINES:
            start_x = 165
            advance = font.getlength(line)
            asc_y = baseline - round(ascender * scale)
            desc_y = baseline - round(descender * scale)
            draw.line((start_x, asc_y, width - 55, asc_y), fill="#7aa9d8", width=1)
            draw.line((start_x, baseline, width - 55, baseline), fill="#df5d74", width=1)
            draw.line((start_x, desc_y, width - 55, desc_y), fill="#83b98a", width=1)
            draw.rectangle((start_x, asc_y, start_x + advance, desc_y), outline="#c7b5d4", width=1)
            draw.text((start_x, baseline), line, font=font, fill="#17121f", anchor="ls")
            baseline += line_step
        y += block_height
    image.save(OPTICAL_PROOF_PATH, "PNG", optimize=True)


def render_natural() -> None:
    width = 2200
    block_heights = [
        max(230, round(78 + (len(PROOF_LINES) - 1) * max(34, size * 1.45) + size * 1.4))
        for size in SIZES
    ]
    height = 90 + sum(block_heights) + 80
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 36)
    label_font = ImageFont.truetype(str(FONT_PATH), 20)
    draw.text((60, 36), "荃方位補寫體 — 自然文字多尺寸驗收", font=title_font, fill="#4f276c")
    y = 100
    for size, block_height in zip(SIZES, block_heights):
        font = ImageFont.truetype(str(FONT_PATH), size)
        draw.text((60, y + 4), f"{size} px", font=label_font, fill="#6d35c5")
        text_y = y + 38
        line_step = max(34, round(size * 1.45))
        for line in PROOF_LINES:
            draw.text((165, text_y), line, font=font, fill="#17121f")
            text_y += line_step
        y += block_height
    image.save(NATURAL_PROOF_PATH, "PNG", optimize=True)
    image.save(LEGACY_PROOF_PATH, "PNG", optimize=True)


def main() -> int:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Build the font first: {FONT_PATH}")
    if not SOURCE_FONT_PATH.is_file():
        raise FileNotFoundError(f"Missing source font: {SOURCE_FONT_PATH}")
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    source = TTFont(SOURCE_FONT_PATH, recalcTimestamp=False)
    derived = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        render_analysis(source, derived)
        render_optical(derived)
        render_natural()
    finally:
        source.close()
        derived.close()
    for path in (ANALYSIS_PROOF_PATH, ANALYSIS_JSON_PATH, OPTICAL_PROOF_PATH, NATURAL_PROOF_PATH, LEGACY_PROOF_PATH):
        print(f"Rendered {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
