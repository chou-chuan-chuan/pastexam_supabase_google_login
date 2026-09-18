#!/usr/bin/env python3
"""Render isolated and mixed-line before/after proof for 壁 and 堅."""

from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-cjk-vertical-alignment-proof.png"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PAPER = "#fffdf9"
INK = "#17131a"
MUTED = "#716477"
ACCENT = "#8e3f70"
GRID = "#ddcfdf"
BLUE = "#6183b2"


def face(source, size: int):
    return ImageFont.truetype(source, size)


def glyph_bounds(font: TTFont, character: str) -> tuple[int, int, int, int]:
    name = font.getBestCmap()[ord(character)]
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"No bounds for {character}")
    return tuple(round(value) for value in pen.bounds)


def diagnostic(draw, x: int, y: int, character: str, font_path, ttfont: TTFont, heading: str) -> None:
    size = 260
    scale = size / 1024
    name = ttfont.getBestCmap()[ord(character)]
    advance = ttfont["hmtx"].metrics[name][0]
    cell = advance * scale
    baseline = y + 310
    b = glyph_bounds(ttfont, character)
    draw.text((x, y), heading, font=face(str(FONT_PATH), 23), fill=ACCENT)
    draw.rectangle((x, baseline - size, x + cell, baseline), outline=GRID, width=3)
    draw.line((x, baseline, x + cell, baseline), fill="#d77a7a", width=3)
    draw.rectangle((x + b[0] * scale, baseline - b[3] * scale,
                    x + b[2] * scale, baseline - b[1] * scale), outline=BLUE, width=3)
    draw.text((x, baseline), character, font=face(font_path, size), fill=INK, anchor="ls")
    center_y = (b[1] + b[3]) / 2
    draw.text((x, baseline + 18), f"bounds={b}  centerY={center_y:g}  advance={advance}",
              font=face(str(FONT_PATH), 20), fill=MUTED)


def main() -> int:
    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before_io = BytesIO(before_bytes)
    before_font = TTFont(BytesIO(before_bytes), recalcTimestamp=False)
    after_font = TTFont(FONT_PATH, recalcTimestamp=False)
    image = Image.new("RGB", (2100, 2120), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 44)
    label = face(str(FONT_PATH), 24)
    draw.text((50, 38), "QuanFangwei 1.023 — 壁 / 堅 vertical optical alignment", font=title, fill=ACCENT)
    draw.text((50, 100), "Placement-only source copies: 壁 dy 0 → +45; 堅 dy 0 → +35; blue=ink bounds, red=baseline", font=label, fill=MUTED)
    try:
        diagnostic(draw, 90, 165, "壁", before_io, before_font, "BEFORE 壁")
        diagnostic(draw, 600, 165, "壁", str(FONT_PATH), after_font, "AFTER 壁")
        diagnostic(draw, 1110, 165, "堅", BytesIO(before_bytes), before_font, "BEFORE 堅")
        diagnostic(draw, 1620, 165, "堅", str(FONT_PATH), after_font, "AFTER 堅")
    finally:
        before_font.close()
        after_font.close()

    draw.text((50, 620), "MIXED-LINE BEFORE / AFTER", font=face(str(FONT_PATH), 30), fill=ACCENT)
    before_text = face(BytesIO(before_bytes), 62)
    after_text = face(str(FONT_PATH), 62)
    lines = (
        "君のかっこよさは鉄壁のシェイプじゃないとこにだって",
        "你的堅強，不只存在於那些巍然聳立之上",
        "鉄壁    壁紙    堅強    中堅    堅持",
    )
    y = 720
    for text in lines:
        draw.text((55, y), "BEFORE", font=label, fill=MUTED)
        draw.line((220, y + 72, 2040, y + 72), fill=GRID, width=1)
        draw.text((240, y + 72), text, font=before_text, fill=INK, anchor="ls")
        draw.text((55, y + 125), "AFTER", font=label, fill=ACCENT)
        draw.line((220, y + 197, 2040, y + 197), fill=GRID, width=1)
        draw.text((240, y + 197), text, font=after_text, fill=INK, anchor="ls")
        y += 410

    draw.text((50, 2020), "No global baseline/line-metric change; no glyph redesign; no CSS/JS positioning.",
              font=label, fill=MUTED)
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH)
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
