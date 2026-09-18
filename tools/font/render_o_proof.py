#!/usr/bin/env python3
"""Render the Version 1.024 repaired handwritten お / derived ぉ proof."""

from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+304A-o-maintainer-handwritten.png"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-hiragana-o-proof.png"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PAPER = "#fffdf9"
INK = "#17131a"
MUTED = "#716477"
ACCENT = "#8e3f70"
GRID = "#ddcfdf"


def face(source, size: int):
    return ImageFont.truetype(source, size)


def bounds(font: TTFont, character: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[f"uni{ord(character):04X}"].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"No bounds for {character}")
    return tuple(round(value) for value in pen.bounds)


def draw_cell(draw, x: int, y: int, character: str, font, label: str) -> None:
    size = 250
    cell = round(960 / 1024 * size)
    baseline = y + 290
    draw.rectangle((x, baseline - size, x + cell, baseline), outline=GRID, width=2)
    draw.line((x, baseline, x + cell, baseline), fill="#d77a7a", width=2)
    draw.text((x, baseline), character, font=font, fill=INK, anchor="ls")
    draw.text((x, baseline + 20), label, font=face(str(FONT_PATH), 21), fill=MUTED)


def main() -> int:
    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = face(BytesIO(before_bytes), 230)
    after = face(str(FONT_PATH), 230)
    reference = Image.open(REFERENCE_PATH).convert("RGB")
    reference.thumbnail((360, 340))
    font = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        o_bounds, small_bounds = bounds(font, "お"), bounds(font, "ぉ")
    finally:
        font.close()

    image = Image.new("RGB", (1900, 1780), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 42)
    label = face(str(FONT_PATH), 25)
    text = face(str(FONT_PATH), 68)
    draw.text((50, 38), "QuanFangwei 1.024 — repaired maintainer-handwritten お / derived ぉ", font=title, fill=ACCENT)
    draw.text((50, 95), f"お bounds={o_bounds}, ぉ bounds={small_bounds}, advances=960; ぉ uses normal small-kana positioning", font=label, fill=MUTED)

    panels = ((50, 150, 520, 620), (555, 150, 1175, 620), (1210, 150, 1850, 620))
    for panel in panels:
        draw.rounded_rectangle(panel, radius=18, outline=GRID, width=2, fill="white")
    image.paste(reference, (105, 215))
    draw.text((85, 565), "authoritative maintainer reference", font=label, fill=MUTED)
    draw.text((600, 195), "OLD お — origin/main 1.023", font=label, fill=MUTED)
    draw.line((610, 520, 1120, 520), fill=GRID, width=2)
    draw.text((730, 520), "お", font=before, fill=INK, anchor="ls")
    draw.text((1250, 195), "NEW 1.024 お / derived ぉ", font=label, fill=ACCENT)
    draw.line((1260, 520, 1810, 520), fill=GRID, width=2)
    draw.text((1315, 520), "お ぉ", font=after, fill=INK, anchor="ls")

    draw.text((55, 680), "INDIVIDUAL CELLS", font=label, fill=ACCENT)
    draw_cell(draw, 310, 655, "お", face(str(FONT_PATH), 250), "new お — 960-unit cell")
    draw_cell(draw, 810, 655, "ぉ", face(str(FONT_PATH), 250), "derived ぉ — normal small-kana path")
    draw.text((55, 1050), "NORMAL SMALL-VOWEL COMPARISON", font=label, fill=ACCENT)
    draw.line((55, 1170, 1845, 1170), fill=GRID, width=1)
    draw.text((120, 1170), "あぁ   いぃ   うぅ   えぇ   おぉ", font=face(str(FONT_PATH), 100), fill=INK, anchor="ls")

    samples = (("孤立／反復", "お   ぉ   おお   おぉ"),
               ("自然文字 1", "おはよう   おねがい"),
               ("自然文字 2", "おおきい   おやすみ"))
    y = 1285
    for heading, sample in samples:
        draw.text((55, y), heading, font=label, fill=MUTED)
        draw.text((315, y + 58), sample, font=text, fill=INK, anchor="ls")
        draw.line((300, y + 70, 1845, y + 70), fill=GRID, width=1)
        y += 150

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH)
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")
    print(f"お bounds={o_bounds}, ぉ bounds={small_bounds}, advances=960")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
