#!/usr/bin/env python3
"""Render the Version 1.024 maintainer-handwritten う / derived ぅ / verified ゔ proof."""

from __future__ import annotations

import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+3046-u-maintainer-handwritten.png"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-hiragana-u-proof.png"
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
    before = face(BytesIO(before_bytes), 230)
    after = face(str(FONT_PATH), 230)
    after_trio = face(str(FONT_PATH), 180)
    reference = Image.open(REFERENCE_PATH).convert("RGB")
    reference.thumbnail((360, 340))
    ttf = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        metrics = {character: bounds(ttf, character) for character in "うぅゔ"}
    finally:
        ttf.close()

    image = Image.new("RGB", (1900, 1820), PAPER)
    draw = ImageDraw.Draw(image)
    title = face(str(FONT_PATH), 42)
    label = face(str(FONT_PATH), 25)
    text = face(str(FONT_PATH), 68)
    draw.text((50, 38), "QuanFangwei 1.024 — maintainer-handwritten う / derived ぅ / verified ゔ", font=title, fill=ACCENT)
    draw.text((50, 95), f"bounds: う={metrics['う']}  ぅ={metrics['ぅ']}  ゔ={metrics['ゔ']}; advances=960", font=label, fill=MUTED)

    panels = ((50, 150, 520, 620), (555, 150, 1175, 620), (1210, 150, 1850, 620))
    for panel in panels:
        draw.rounded_rectangle(panel, radius=18, outline=GRID, width=2, fill="white")
    image.paste(reference, (120, 210))
    draw.text((85, 565), "authoritative maintainer reference", font=label, fill=MUTED)
    draw.text((600, 195), "OLD う — origin/main 1.023", font=label, fill=MUTED)
    draw.line((610, 520, 1120, 520), fill=GRID, width=2)
    draw.text((730, 520), "う", font=before, fill=INK, anchor="ls")
    draw.text((1250, 195), "NEW 1.024 う / ぅ / ゔ", font=label, fill=ACCENT)
    draw.line((1260, 520, 1810, 520), fill=GRID, width=2)
    draw.text((1260, 520), "う ぅ ゔ", font=after_trio, fill=INK, anchor="ls")

    draw.text((55, 680), "FAMILY WEIGHT / NORMAL SMALL-KANA PATH", font=label, fill=ACCENT)
    draw.line((55, 835, 1845, 835), fill=GRID, width=1)
    draw.text((110, 835), "あ  い  う  え  お    き  や  す", font=face(str(FONT_PATH), 98), fill=INK, anchor="ls")
    draw.line((55, 970, 1845, 970), fill=GRID, width=1)
    draw.text((110, 970), "う   ぅ   ゔ    うう   うぅ   ゔう   うゔ", font=face(str(FONT_PATH), 88), fill=INK, anchor="ls")

    rows = (
        ("natural 1", "うた   うれしい   ありがとう"),
        ("natural 2", "つよい   ゔう   うゔ"),
        ("vu sequences", "ゔぁ   ゔぃ   ゔ   ゔぇ   ゔぉ"),
    )
    y = 1115
    for heading, sample in rows:
        draw.text((55, y), heading, font=label, fill=MUTED)
        draw.line((300, y + 75, 1845, y + 75), fill=GRID, width=1)
        draw.text((330, y + 75), sample, font=text, fill=INK, anchor="ls")
        y += 190

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH)
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")
    print(f"う={metrics['う']} ぅ={metrics['ぅ']} ゔ={metrics['ゔ']} advances=960")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
