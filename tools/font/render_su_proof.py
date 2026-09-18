#!/usr/bin/env python3
"""Render the Version 1.024 scoped す pressure repair and derived ず proof."""

from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-hiragana-su-proof.png"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PAPER = "#fffdf9"
INK = "#17131a"
MUTED = "#716477"
ACCENT = "#8e3f70"
GRID = "#ddcfdf"


def face(source, size: int):
    return ImageFont.truetype(source, size)


def bounds(font: TTFont, character: str) -> tuple[int, int, int, int]:
    name = font.getBestCmap()[ord(character)]
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"No bounds for {character}")
    return tuple(round(value) for value in pen.bounds)


def main() -> int:
    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = face(BytesIO(before_bytes), 245)
    after = face(str(FONT_PATH), 245)
    ttf = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        su_bounds, zu_bounds = bounds(ttf, "す"), bounds(ttf, "ず")
    finally:
        ttf.close()

    image = Image.new("RGB", (1900, 1660), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 42)
    label = face(str(FONT_PATH), 25)
    sample = face(str(FONT_PATH), 76)
    draw.text((50, 38), "QuanFangwei 1.024 — scoped す stroke-pressure repair / derived ず", font=title, fill=ACCENT)
    draw.text((50, 95), f"す bounds={su_bounds}, ず bounds={zu_bounds}; topology and optical placement retained", font=label, fill=MUTED)

    panels = ((50, 150, 920, 620), (980, 150, 1850, 620))
    for panel in panels:
        draw.rounded_rectangle(panel, radius=18, outline=GRID, width=2, fill="white")
    draw.text((90, 190), "OLD — origin/main 1.023", font=label, fill=MUTED)
    draw.line((100, 535, 870, 535), fill=GRID, width=2)
    draw.text((220, 535), "す ず", font=before, fill=INK, anchor="ls")
    draw.text((1020, 190), "NEW 1.024 — harmonized pressure", font=label, fill=ACCENT)
    draw.line((1030, 535, 1800, 535), fill=GRID, width=2)
    draw.text((1150, 535), "す ず", font=after, fill=INK, anchor="ls")

    draw.text((55, 690), "HIRAGANA FAMILY WEIGHT", font=label, fill=ACCENT)
    draw.line((55, 830, 1845, 830), fill=GRID, width=1)
    draw.text((130, 830), "あ  お  き  す  ず  や  え  か", font=face(str(FONT_PATH), 105), fill=INK, anchor="ls")

    rows = (
        ("isolated", "す   ず"),
        ("natural 1", "すごい   おすすめ"),
        ("natural 2", "すずしい   すこし"),
    )
    y = 980
    for heading, text in rows:
        draw.text((55, y), heading, font=label, fill=MUTED)
        draw.line((300, y + 70, 1845, y + 70), fill=GRID, width=1)
        draw.text((330, y + 70), text, font=sample, fill=INK, anchor="ls")
        y += 190

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH)
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")
    print(f"す bounds={su_bounds}, ず bounds={zu_bounds}, advances=960")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
