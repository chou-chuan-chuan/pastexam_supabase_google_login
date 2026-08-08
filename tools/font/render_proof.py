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
CEDILLA_PROOF_PATH = PROOF_DIR / "quanfangwei-cedilla-proof.png"
CEDILLA_PROOF_TEXT_PATH = PROOF_DIR / "quanfangwei-cedilla-proof.txt"
GERMAN_PROOF_PATH = PROOF_DIR / "quanfangwei-german-proof.png"
GERMAN_PROOF_TEXT_PATH = PROOF_DIR / "quanfangwei-german-proof.txt"
SHARP_S_PROOF_PATH = PROOF_DIR / "quanfangwei-sharp-s-proof.png"

SIZES = [16, 24, 32, 48, 72]
PRECOMPOSED_C_CEDILLA = "\u00C7"
DECOMPOSED_C_CEDILLA = "C\u0327"
PRECOMPOSED_LOWER_C_CEDILLA = "\u00E7"
DECOMPOSED_LOWER_C_CEDILLA = "c\u0327"
CEDILLA_COMPONENT_OFFSETS = {"C": (126, 0), "c": (81, 10)}
DIAERESIS_COMPONENT_OFFSETS = {
    "A": (127, 145), "O": (90, 87), "U": (29, 88),
    "a": (27, -13), "o": (8, -57), "u": (35, -62),
}
GERMAN_SIZES = [16, 20, 24, 32, 48, 72, 120]
PROOF_LINES = [
    "? ¿ ? ¿",
    "C Ç C Ç",
    "¿Qué canción?   ¿Dónde estás?",
    "ÇA VA   FRANÇAIS   LEÇON   GARÇON",
    "歌曲 ¿ Ç PDF   聽見歌曲，也讀見每一句。",
]
ANALYSIS_CODEPOINTS = [
    0x003F, 0x00BF, 0x0043, 0x0063, 0x002C, 0x003B, 0x004A, 0x006A,
    0x0067, 0x0079, 0x00A8, 0x00B8, 0x00C4, 0x00C7, 0x00D6, 0x00DC,
    0x00DF, 0x00E4, 0x00E7, 0x00F6, 0x00FC, 0x0308, 0x0327, 0x1E9E,
]

CEDILLA_PROOF_LINES = [
    f"C {PRECOMPOSED_C_CEDILLA} {DECOMPOSED_C_CEDILLA} C",
    f"c {PRECOMPOSED_LOWER_C_CEDILLA} {DECOMPOSED_LOWER_C_CEDILLA} c",
    f"{PRECOMPOSED_C_CEDILLA}A    {DECOMPOSED_C_CEDILLA}A",
    f"{PRECOMPOSED_LOWER_C_CEDILLA}a    {DECOMPOSED_LOWER_C_CEDILLA}a",
    f"FRAN{PRECOMPOSED_C_CEDILLA}AIS    FRANC\u0327AIS",
    f"fran{PRECOMPOSED_LOWER_C_CEDILLA}ais    franc\u0327ais",
    f"LE{PRECOMPOSED_C_CEDILLA}ON    LEC\u0327ON",
    f"GAR{PRECOMPOSED_C_CEDILLA}ON    GARC\u0327ON",
    f"¿QUÉ?    歌曲 {PRECOMPOSED_C_CEDILLA} {DECOMPOSED_C_CEDILLA} PDF",
]


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


def draw_gpos_text(draw: ImageDraw.ImageDraw, position, text: str, font: ImageFont.FreeTypeFont, fill, upm: int) -> float:
    """Draw text while applying the font's reviewed combining-mark deltas.

    Pillow in the pinned proof environment has no RAQM/HarfBuzz support, so
    this small proof-only shaper applies the same +126/0 mark placement encoded
    in GPOS. The verifier separately exercises the real table with HarfBuzz;
    the browser fixture remains available for Chromium Rendered Fonts checks.
    """
    cursor_x, baseline = position
    previous_origin = cursor_x
    previous_character = ""
    scale = font.size / upm
    for character in text:
        mark_offsets = CEDILLA_COMPONENT_OFFSETS if character == "\u0327" else DIAERESIS_COMPONENT_OFFSETS if character == "\u0308" else None
        if mark_offsets is not None and previous_character in mark_offsets:
            offset_x, offset_y = mark_offsets[previous_character]
            spacing_mark = "\u00B8" if character == "\u0327" else "\u00A8"
            draw.text(
                (previous_origin + offset_x * scale, baseline - offset_y * scale),
                spacing_mark,
                font=font,
                fill=fill,
                anchor="ls",
            )
            previous_character = character
            continue
        previous_origin = cursor_x
        draw.text((cursor_x, baseline), character, font=font, fill=fill, anchor="ls")
        cursor_x += font.getlength(character)
        previous_character = character
    return cursor_x


def gpos_text_length(text: str, font: ImageFont.FreeTypeFont) -> float:
    return sum(font.getlength(character) for character in text if character not in {"\u0308", "\u0327"})


def raster_sequence_metrics(text: str, size: int, upm: int) -> tuple[tuple[int, int, int, int] | None, float]:
    image = Image.new("L", (max(500, size * 6), max(260, size * 3)), 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT_PATH), size)
    baseline = max(180, size * 2)
    draw_gpos_text(draw, (80, baseline), text, font, 255, upm)
    return image.getbbox(), round(gpos_text_length(text, font), 3)


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


def render_cedilla(derived: TTFont) -> None:
    upm = derived["head"].unitsPerEm
    width = 2500
    block_heights = [max(300, 95 + len(CEDILLA_PROOF_LINES) * max(34, round(size * 1.42))) for size in SIZES]
    zoom_height = 750
    height = 180 + sum(block_heights) + zoom_height
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 42)
    label_font = ImageFont.truetype(str(FONT_PATH), 22)
    draw.text((60, 42), "荃方位補寫體 Ç / ç + COMBINING CEDILLA proof", font=title_font, fill="#4f276c")
    draw.text((60, 105), "C <221 91>    c <176 101>    mark <95 91>    advance 0", font=label_font, fill="#5e5264")

    y = 160
    text_report = [
        "QuanFangwei Supplement Script cedilla proof",
        "precomposed: Ç = U+00C7",
        "decomposed: Ç = U+0043 U+0327",
        "precomposed lowercase: ç = U+00E7",
        "decomposed lowercase: ç = U+0063 U+0327",
        "base anchors: C <221 91>, c <176 101>",
        "mark anchor: <95 91>",
        "mark advance: 0",
        "",
        *CEDILLA_PROOF_LINES,
        "",
        "Raster metrics (proof-only anchor shaper; verifier uses HarfBuzz):",
    ]
    for size, block_height in zip(SIZES, block_heights):
        font = ImageFont.truetype(str(FONT_PATH), size)
        line_step = max(34, round(size * 1.42))
        draw.text((60, y + 5), f"{size} px", font=label_font, fill="#6d35c5")
        baseline = y + 55 + size
        for line in CEDILLA_PROOF_LINES:
            draw.line((165, baseline + 2, width - 60, baseline + 2), fill="#e8a5b2", width=1)
            draw_gpos_text(draw, (175, baseline), line, font, "#17121f", upm)
            baseline += line_step
        pre_bbox, pre_advance = raster_sequence_metrics(PRECOMPOSED_C_CEDILLA, size, upm)
        dec_bbox, dec_advance = raster_sequence_metrics(DECOMPOSED_C_CEDILLA, size, upm)
        text_report.append(
            f"{size}px: U+00C7 bbox={pre_bbox} advance={pre_advance}; "
            f"U+0043+U+0327 bbox={dec_bbox} advance={dec_advance}"
        )
        lower_pre_bbox, lower_pre_advance = raster_sequence_metrics(PRECOMPOSED_LOWER_C_CEDILLA, size, upm)
        lower_dec_bbox, lower_dec_advance = raster_sequence_metrics(DECOMPOSED_LOWER_C_CEDILLA, size, upm)
        text_report.append(
            f"{size}px: U+00E7 bbox={lower_pre_bbox} advance={lower_pre_advance}; "
            f"U+0063+U+0327 bbox={lower_dec_bbox} advance={lower_dec_advance}"
        )
        y += block_height

    zoom_font = ImageFont.truetype(str(FONT_PATH), 120)
    zoom_label = ImageFont.truetype(str(FONT_PATH), 28)
    draw.text((60, y + 10), "120 px close-up", font=zoom_label, fill="#6d35c5")
    baseline = y + 250
    draw.line((165, baseline, width - 80, baseline), fill="#df5d74", width=2)
    draw.rectangle((165, y + 65, 900, y + 350), outline="#c7b5d4", width=2)
    draw.rectangle((1040, y + 65, 1775, y + 350), outline="#c7b5d4", width=2)
    draw.text((190, y + 78), "U+00C7", font=zoom_label, fill="#5e5264")
    draw.text((1065, y + 78), "U+0043 U+0327", font=zoom_label, fill="#5e5264")
    draw_gpos_text(draw, (430, baseline), PRECOMPOSED_C_CEDILLA, zoom_font, "#17121f", upm)
    draw_gpos_text(draw, (1305, baseline), DECOMPOSED_C_CEDILLA, zoom_font, "#17121f", upm)
    pre_bbox, pre_advance = raster_sequence_metrics(PRECOMPOSED_C_CEDILLA, 120, upm)
    dec_bbox, dec_advance = raster_sequence_metrics(DECOMPOSED_C_CEDILLA, 120, upm)
    text_report.append(
        f"120px: U+00C7 bbox={pre_bbox} advance={pre_advance}; "
        f"U+0043+U+0327 bbox={dec_bbox} advance={dec_advance}"
    )
    lower_baseline = y + 575
    draw.line((165, lower_baseline, width - 80, lower_baseline), fill="#df5d74", width=2)
    draw.rectangle((165, y + 390, 900, y + 675), outline="#c7b5d4", width=2)
    draw.rectangle((1040, y + 390, 1775, y + 675), outline="#c7b5d4", width=2)
    draw.text((190, y + 403), "U+00E7", font=zoom_label, fill="#5e5264")
    draw.text((1065, y + 403), "U+0063 U+0327", font=zoom_label, fill="#5e5264")
    draw_gpos_text(draw, (430, lower_baseline), PRECOMPOSED_LOWER_C_CEDILLA, zoom_font, "#17121f", upm)
    draw_gpos_text(draw, (1305, lower_baseline), DECOMPOSED_LOWER_C_CEDILLA, zoom_font, "#17121f", upm)
    lower_pre_bbox, lower_pre_advance = raster_sequence_metrics(PRECOMPOSED_LOWER_C_CEDILLA, 120, upm)
    lower_dec_bbox, lower_dec_advance = raster_sequence_metrics(DECOMPOSED_LOWER_C_CEDILLA, 120, upm)
    text_report.append(
        f"120px: U+00E7 bbox={lower_pre_bbox} advance={lower_pre_advance}; "
        f"U+0063+U+0327 bbox={lower_dec_bbox} advance={lower_dec_advance}"
    )

    image.save(CEDILLA_PROOF_PATH, "PNG", optimize=True)
    CEDILLA_PROOF_TEXT_PATH.write_text("\n".join(text_report) + "\n", encoding="utf-8", newline="\n")


def codepoints(text: str) -> str:
    return " ".join(f"U+{ord(character):04X}" for character in text)


def render_german(derived: TTFont) -> None:
    """Render German text and composed/decomposed Umlaut comparisons."""
    upm = derived["head"].unitsPerEm
    comparison_lines = [
        "Ä Ö Ü    A\u0308 O\u0308 U\u0308",
        "ä ö ü    a\u0308 o\u0308 u\u0308",
        "A Ä A   O Ö O   U Ü U",
        "a ä a   o ö o   u ü u   Ç ç   ¿ ?   ß ẞ",
    ]
    corpus_lines = [
        "Füße   Straße   STRAẞE   Größe   größer   Mädchen",
        "schön   über   für   früh   grün   Köln",
        "München   Düsseldorf   Österreich",
        "Fußball   Fußgänger   Straßenbahn",
        "Ich weiß, dass du schön bist.",
        "Grüße aus München!",
        "Über den Wolken muss die Freiheit wohl grenzenlos sein.",
    ]
    block_heights = [110 + len(comparison_lines) * max(38, round(size * 1.45)) for size in GERMAN_SIZES]
    corpus_height = 150 + len(corpus_lines) * 72
    width = 2700
    height = 150 + sum(block_heights) + corpus_height
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 42)
    label_font = ImageFont.truetype(str(FONT_PATH), 22)
    draw.text((60, 38), "荃方位補寫體 German / Umlaut proof", font=title_font, fill="#4f276c")
    draw.text((60, 98), "U+0308 advance 0 · source GPOS preserved · composed / decomposed", font=label_font, fill="#5e5264")

    report = [
        "QuanFangwei Supplement Script German proof",
        "spacing diaeresis: ¨ = U+00A8 (advance 300)",
        "combining diaeresis: ̈ = U+0308 (advance 0)",
        "mark anchor: <145 477>",
        "base anchors: A <272 622>, O <235 564>, U <174 565>, a <172 464>, o <153 420>, u <180 415>",
        "precomposed: Ä Ö Ü ä ö ü",
        "decomposed: Ä Ö Ü ä ö ü",
        f"precomposed code points: {codepoints('ÄÖÜäöü')}",
        f"decomposed code points: {codepoints('ÄÖÜäöü')}",
        "",
        *comparison_lines,
        *corpus_lines,
        "",
        "Raster metrics (proof-only anchor shaper; verifier uses HarfBuzz):",
    ]
    y = 145
    pairs = [("Ä", "A\u0308"), ("Ö", "O\u0308"), ("Ü", "U\u0308"), ("ä", "a\u0308"), ("ö", "o\u0308"), ("ü", "u\u0308")]
    for size, block_height in zip(GERMAN_SIZES, block_heights):
        font = ImageFont.truetype(str(FONT_PATH), size)
        line_step = max(38, round(size * 1.45))
        draw.text((60, y + 5), f"{size} px", font=label_font, fill="#6d35c5")
        baseline = y + 55 + size
        for line in comparison_lines:
            draw.line((165, baseline + 2, width - 60, baseline + 2), fill="#e8a5b2", width=1)
            draw_gpos_text(draw, (175, baseline), line, font, "#17121f", upm)
            baseline += line_step
        for precomposed, decomposed in pairs:
            pre_bbox, pre_advance = raster_sequence_metrics(precomposed, size, upm)
            dec_bbox, dec_advance = raster_sequence_metrics(decomposed, size, upm)
            report.append(f"{size}px {codepoints(precomposed)} bbox={pre_bbox} advance={pre_advance}; {codepoints(decomposed)} bbox={dec_bbox} advance={dec_advance}")
        y += block_height

    corpus_font = ImageFont.truetype(str(FONT_PATH), 36)
    draw.text((60, y + 10), "German text coverage", font=label_font, fill="#6d35c5")
    baseline = y + 85
    for line in corpus_lines:
        draw.line((165, baseline + 3, width - 60, baseline + 3), fill="#e8a5b2", width=1)
        draw.text((175, baseline), line, font=corpus_font, fill="#17121f", anchor="ls")
        baseline += 72
    image.save(GERMAN_PROOF_PATH, "PNG", optimize=True)
    GERMAN_PROOF_TEXT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")


def render_sharp_s(derived: TTFont) -> None:
    """Render enlarged ß/ẞ comparisons with font metric and advance guides."""
    upm = derived["head"].unitsPerEm
    ascent = derived["hhea"].ascent
    descent = derived["hhea"].descent
    cap_height = getattr(derived["OS/2"], "sCapHeight", 650)
    x_height = getattr(derived["OS/2"], "sxHeight", 450)
    size = 144
    scale = size / upm
    lines = ["β ß ẞ β", "s ß s", "S ẞ S", "b β ß b", "B β ẞ B", "Straße", "STRAẞE"]
    width, height = 2500, 1980
    image = Image.new("RGB", (width, height), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 42)
    label_font = ImageFont.truetype(str(FONT_PATH), 22)
    font = ImageFont.truetype(str(FONT_PATH), size)
    draw.text((60, 38), "荃方位補寫體 ß / ẞ enlarged proof", font=title_font, fill="#4f276c")
    draw.text((60, 100), "approved beta-like direction · source U+03B2 handwriting · 144 px", font=label_font, fill="#5e5264")
    baseline = 330
    for line in lines:
        start_x = 260
        advance = gpos_text_length(line, font)
        asc_y = baseline - ascent * scale
        cap_y = baseline - cap_height * scale
        x_y = baseline - x_height * scale
        desc_y = baseline - descent * scale
        draw.line((start_x, asc_y, width - 80, asc_y), fill="#7aa9d8", width=1)
        draw.line((start_x, cap_y, width - 80, cap_y), fill="#8d75c7", width=1)
        draw.line((start_x, x_y, width - 80, x_y), fill="#d4a43d", width=1)
        draw.line((start_x, baseline, width - 80, baseline), fill="#df5d74", width=2)
        draw.line((start_x, desc_y, width - 80, desc_y), fill="#83b98a", width=1)
        draw.rectangle((start_x, asc_y, start_x + advance, desc_y), outline="#c7b5d4", width=1)
        draw.text((60, asc_y), "ascent", font=label_font, fill="#527aa6")
        draw.text((60, cap_y), "cap", font=label_font, fill="#7059a9")
        draw.text((60, x_y), "x-height", font=label_font, fill="#9c741c")
        draw.text((60, baseline), "baseline", font=label_font, fill="#b34559", anchor="ls")
        draw.text((60, desc_y), "descender", font=label_font, fill="#4e8656")
        draw.text((start_x, baseline), line, font=font, fill="#17121f", anchor="ls")
        draw.text((start_x + advance + 25, baseline), f"advance {advance:.1f}px", font=label_font, fill="#5e5264", anchor="ls")
        baseline += 235
    image.save(SHARP_S_PROOF_PATH, "PNG", optimize=True)


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
        render_cedilla(derived)
        render_german(derived)
        render_sharp_s(derived)
    finally:
        source.close()
        derived.close()
    for path in (
        ANALYSIS_PROOF_PATH,
        ANALYSIS_JSON_PATH,
        OPTICAL_PROOF_PATH,
        NATURAL_PROOF_PATH,
        LEGACY_PROOF_PATH,
        CEDILLA_PROOF_PATH,
        CEDILLA_PROOF_TEXT_PATH,
        GERMAN_PROOF_PATH,
        GERMAN_PROOF_TEXT_PATH,
        SHARP_S_PROOF_PATH,
    ):
        print(f"Rendered {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
