#!/usr/bin/env python3
"""Render Version 1.024 maintainer-source proof for あ/い/さ/き/と/り and derivatives."""

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
TOOLS_DIR = Path(__file__).resolve().parent
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REFERENCE_1 = TOOLS_DIR / "references/U+3042-U+3044-U+3055-U+304D-maintainer-handwritten.png"
REFERENCE_2 = TOOLS_DIR / "references/U+3068-U+308A-maintainer-handwritten.png"
PROOF_PATH = TOOLS_DIR / "proofs/quanfangwei-hiragana-maintainer-batch-proof.png"
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
    font.getGlyphSet()[font.getBestCmap()[ord(character)]].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"No bounds for {character}")
    return tuple(round(value) for value in pen.bounds)


def main() -> int:
    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH], cwd=REPO_ROOT)
    before = face(BytesIO(before_bytes), 130)
    after = face(str(FONT_PATH), 130)
    text = face(str(FONT_PATH), 66)
    label = face(str(FONT_PATH), 24)
    title = face(str(FONT_PATH), 40)
    ttf = TTFont(FONT_PATH, recalcTimestamp=False)
    try:
        metrics = {character: bounds(ttf, character) for character in "あいさきとりぁぃざぎど"}
    finally:
        ttf.close()

    image = Image.new("RGB", (2100, 2600), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((50, 35), "QuanFangwei 1.024 — new maintainer Hiragana sources", font=title, fill=ACCENT)
    draw.text((50, 88), "authoritative raster references → clean center-lines → existing variable-width renderer", font=label, fill=MUTED)

    ref1 = Image.open(REFERENCE_1).convert("RGB")
    ref2 = Image.open(REFERENCE_2).convert("RGB")
    ref1.thumbnail((450, 450))
    ref2.thumbnail((330, 450))
    for panel in ((50, 135, 550, 625), (585, 135, 965, 625), (1000, 135, 2050, 625)):
        draw.rounded_rectangle(panel, radius=18, outline=GRID, width=2, fill="white")
    image.paste(ref1, (75, 155))
    image.paste(ref2, (610, 155))
    draw.text((75, 580), "reference sheet: あ / い / さ / き", font=label, fill=MUTED)
    draw.text((610, 580), "reference sheet: と / り", font=label, fill=MUTED)
    draw.text((1035, 175), "OLD — origin/main 1.023", font=label, fill=MUTED)
    draw.text((1530, 175), "NEW — Version 1.024", font=label, fill=ACCENT)
    glyphs = "あいさきとり"
    for index, character in enumerate(glyphs):
        row = index // 3
        col = index % 3
        x = 1040 + col * 325
        y = 315 + row * 235
        draw.line((x, y + 55, x + 285, y + 55), fill=GRID, width=1)
        draw.text((x + 15, y + 55), character, font=before, fill="#9a8f9b", anchor="ls")
        draw.text((x + 150, y + 55), character, font=after, fill=INK, anchor="ls")

    draw.text((55, 680), "DERIVATIVES / COMPOSITION", font=label, fill=ACCENT)
    derivative_rows = (
        "あ / ぁ     い / ぃ     う / ぅ / ゔ",
        "さ / ざ     き / ぎ     と / ど",
        "きゃ きゅ きょ     ぎゃ ぎゅ ぎょ     りゃ りゅ りょ",
        "お / ぉ     す / ず",
    )
    y = 810
    for sample in derivative_rows:
        draw.line((55, y, 2045, y), fill=GRID, width=1)
        draw.text((95, y), sample, font=text, fill=INK, anchor="ls")
        y += 150

    draw.text((55, 1370), "HIRAGANA FAMILY WEIGHT / BASELINE", font=label, fill=ACCENT)
    family_rows = (
        "あ  い  う  え  お",
        "か  き  く  け  こ",
        "さ  し  す  せ  そ",
        "た  ち  つ  て  と",
        "ら  り  る  れ  ろ",
    )
    y = 1495
    for sample in family_rows:
        draw.line((55, y, 2045, y), fill=GRID, width=1)
        draw.text((110, y), sample, font=text, fill=INK, anchor="ls")
        y += 135

    draw.text((55, 2115), "NATURAL-TEXT QA", font=label, fill=ACCENT)
    natural_rows = (
        "うた  うれしい  ありがとう    あおい  あめ  いい  いろ  いち",
        "さくら  さいご  ざっし  ざんねん    きれい  すき  ぎん  きゃく  ぎゃく",
        "とても  とき  どう  どこ    りんご  りっぱ  りゃく  りょこう",
        "おはよう  おねがい  おおきい  おすすめ  すずしい",
    )
    y = 2240
    for sample in natural_rows:
        draw.line((55, y, 2045, y), fill=GRID, width=1)
        draw.text((80, y), sample, font=face(str(FONT_PATH), 48), fill=INK, anchor="ls")
        y += 85

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PROOF_PATH)
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")
    for character in "あいさきとりぁぃざぎど":
        print(f"{character} bounds={metrics[character]} advance=960")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
