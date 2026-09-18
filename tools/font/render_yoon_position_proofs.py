#!/usr/bin/env python3
"""Render the Version 1.023 yōon grid, cell diagnostic, and before/after proofs."""

from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_DIR = Path(__file__).resolve().parent / "proofs"
GRID_PATH = PROOF_DIR / "quanfangwei-yoon-position-proof.png"
CELL_PATH = PROOF_DIR / "quanfangwei-yoon-cell-diagnostic.png"
COMPARE_PATH = PROOF_DIR / "quanfangwei-yoon-before-after-proof.png"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
UPM = 1024
ADVANCE = 960
PAPER = "#fffdf9"
INK = "#18131d"
MUTED = "#716477"
ACCENT = "#8e3f70"
GRID = "#dccfdf"
BASELINE = "#d47373"
BOUNDS = "#6285b8"

ROWS = (
    ("K", "きゃ", "きゅ", "きょ", "キャ", "キュ", "キョ"),
    ("SH", "しゃ", "しゅ", "しょ", "シャ", "シュ", "ショ"),
    ("CH", "ちゃ", "ちゅ", "ちょ", "チャ", "チュ", "チョ"),
    ("N", "にゃ", "にゅ", "にょ", "ニャ", "ニュ", "ニョ"),
    ("H", "ひゃ", "ひゅ", "ひょ", "ヒャ", "ヒュ", "ヒョ"),
    ("M", "みゃ", "みゅ", "みょ", "ミャ", "ミュ", "ミョ"),
    ("R", "りゃ", "りゅ", "りょ", "リャ", "リュ", "リョ"),
    ("G", "ぎゃ", "ぎゅ", "ぎょ", "ギャ", "ギュ", "ギョ"),
    ("J", "じゃ", "じゅ", "じょ", "ジャ", "ジュ", "ジョ"),
    ("B", "びゃ", "びゅ", "びょ", "ビャ", "ビュ", "ビョ"),
    ("P", "ぴゃ", "ぴゅ", "ぴょ", "ピャ", "ピュ", "ピョ"),
)


def face(source, size: int):
    return ImageFont.truetype(source, size)


def baseline_font_bytes() -> bytes:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH],
        cwd=REPO_ROOT,
    )


def draw_pair(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, size: int) -> None:
    x, baseline = xy
    cell = ADVANCE / UPM * size
    top = baseline - size * 0.82
    bottom = baseline + size * 0.18
    for index in range(2):
        left = x + index * cell
        draw.rectangle((left, top, left + cell, bottom), outline=GRID, width=1)
    draw.line((x, baseline, x + 2 * cell, baseline), fill="#eadde8", width=1)
    draw.text((x, baseline), text, font=font, fill=INK, anchor="ls")


def render_grid(after_font) -> None:
    image = Image.new("RGB", (1540, 2380), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 44)
    label = face(str(FONT_PATH), 25)
    sample = face(str(FONT_PATH), 72)
    draw.text((55, 42), "QuanFangwei 1.023 — yōon lower-left in-cell positioning", font=title, fill=ACCENT)
    draw.text((55, 100), "Each faint box is one 960-unit advance cell; no ligatures or pair-specific spacing.", font=label, fill=MUTED)
    for block, heading, offset in ((0, "HIRAGANA", 0), (1, "KATAKANA", 3)):
        block_x = 55 + block * 750
        draw.text((block_x, 165), heading, font=face(str(FONT_PATH), 32), fill=ACCENT)
        for col, heading2 in enumerate(("YA", "YU", "YO")):
            draw.text((block_x + 100 + col * 210, 220), heading2, font=label, fill=MUTED)
        for row_index, row in enumerate(ROWS):
            baseline = 320 + row_index * 178
            draw.text((block_x, baseline - 25), row[0], font=label, fill=MUTED)
            for col in range(3):
                draw_pair(draw, (block_x + 80 + col * 210, baseline), row[1 + offset + col], sample, 72)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    image.save(GRID_PATH)


def glyph_bounds(font: TTFont, character: str) -> tuple[int, int, int, int]:
    name = font.getBestCmap()[ord(character)]
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"No bounds for {character}")
    return tuple(round(value) for value in pen.bounds)


def render_cells() -> None:
    image = Image.new("RGB", (1660, 1160), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 42)
    label = face(str(FONT_PATH), 22)
    glyph_face = face(str(FONT_PATH), 300)
    font = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        draw.text((48, 38), "Yōon individual-cell diagnostic — 1024 UPM / 960 advance", font=title, fill=ACCENT)
        for index, character in enumerate("ゃゅょャュョ"):
            col, row = index % 3, index // 3
            x, y = 70 + col * 530, 150 + row * 500
            size = 300
            scale = size / UPM
            cell_width = ADVANCE * scale
            baseline = y + 330
            glyph_box = glyph_bounds(font, character)
            draw.rectangle((x, baseline - UPM * scale, x + cell_width, baseline), outline=GRID, width=3)
            draw.line((x, baseline, x + cell_width, baseline), fill=BASELINE, width=3)
            draw.line((x, baseline - UPM * scale, x, baseline + 18), fill=ACCENT, width=4)
            draw.line((x + cell_width, baseline - UPM * scale, x + cell_width, baseline + 18), fill=MUTED, width=3)
            bx0 = x + glyph_box[0] * scale
            bx1 = x + glyph_box[2] * scale
            by0 = baseline - glyph_box[3] * scale
            by1 = baseline - glyph_box[1] * scale
            draw.rectangle((bx0, by0, bx1, by1), outline=BOUNDS, width=3)
            draw.text((x, baseline), character, font=glyph_face, fill=INK, anchor="ls")
            advance, lsb = font["hmtx"].metrics[f"uni{ord(character):04X}"]
            rsb = advance - glyph_box[2]
            draw.text((x, y + 365), f"{character}  U+{ord(character):04X}", font=label, fill=ACCENT)
            draw.text((x, y + 400), f"bounds {glyph_box} | advance {advance}", font=label, fill=MUTED)
            draw.text((x, y + 435), f"LSB {lsb} | RSB {rsb} | red=origin/baseline | blue=ink", font=label, fill=MUTED)
    finally:
        font.close()
    image.save(CELL_PATH)


def render_comparison(before_font, after_font) -> None:
    image = Image.new("RGB", (1560, 1120), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 42)
    label = face(str(FONT_PATH), 26)
    before = face(before_font, 105)
    after = face(after_font, 105)
    draw.text((48, 38), "Yōon optical positioning — before / after", font=title, fill=ACCENT)
    draw.text((48, 98), "Only the small-kana ink moves left/down; every character keeps its own cell.", font=label, fill=MUTED)
    samples = ("きゃ   きゅ   きょ", "しゃ   しゅ   しょ", "キャ   キュ   キョ", "シャ   シュ   ショ")
    for col, (heading, font) in enumerate((("BEFORE — origin/main 1.022", before), ("AFTER — Version 1.023", after))):
        x = 55 + col * 760
        draw.text((x, 185), heading, font=label, fill=ACCENT if col else MUTED)
        for row, text in enumerate(samples):
            baseline = 340 + row * 190
            draw.line((x, baseline, x + 690, baseline), fill=GRID, width=1)
            draw.text((x, baseline), text, font=font, fill=INK, anchor="ls")
    image.save(COMPARE_PATH)


def main() -> int:
    before_bytes = baseline_font_bytes()
    render_grid(str(FONT_PATH))
    render_cells()
    render_comparison(BytesIO(before_bytes), str(FONT_PATH))
    print(f"Wrote {GRID_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {CELL_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {COMPARE_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
