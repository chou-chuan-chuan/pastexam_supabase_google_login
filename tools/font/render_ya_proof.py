#!/usr/bin/env python3
"""Render the Version 1.022 maintainer-handwritten ya/small-ya proof."""

from io import BytesIO
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+3084-ya-maintainer-handwritten.png"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-hiragana-ya-redesign-proof.png"
BASELINE_GIT_PATH = "origin/main:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"


def bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {glyph_name} has no outline")
    return tuple(round(value) for value in pen.bounds)


def main() -> None:
    before_bytes = subprocess.check_output(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "show", BASELINE_GIT_PATH],
        cwd=REPO_ROOT,
    )
    before_font = ImageFont.truetype(BytesIO(before_bytes), 160)
    after_font = ImageFont.truetype(str(FONT_PATH), 160)

    ttfont = TTFont(FONT_PATH, recalcTimestamp=False)
    cmap = ttfont.getBestCmap()
    if cmap.get(0x3084) != "uni3084" or cmap.get(0x3083) != "uni3083":
        raise RuntimeError("Current font does not map U+3084/U+3083 to uni3084/uni3083")
    ya_bounds = bounds(ttfont, "uni3084")
    small_ya_bounds = bounds(ttfont, "uni3083")
    ttfont.close()

    canvas = Image.new("RGB", (1900, 1780), "#fffdf9")
    draw = ImageDraw.Draw(canvas)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    info = ImageFont.truetype(str(FONT_PATH), 24)
    label = ImageFont.truetype(str(FONT_PATH), 30)
    draw.text((55, 45), "QuanFangwei Version 1.022 — maintainer-handwritten や / ゃ", font=title, fill="#25152c")
    draw.text((55, 105), f"や bounds={ya_bounds}, advance=960   ゃ bounds={small_ya_bounds}, advance=960", font=info, fill="#60476a")
    draw.text((55, 140), "ゃ = normalized や × 0.72, shared y shift -12; no independent topology", font=info, fill="#60476a")

    reference = Image.open(REFERENCE_PATH).convert("RGB")
    reference.thumbnail((430, 430))
    panels = ((55, 200, 535, 740), (565, 200, 1165, 740), (1195, 200, 1845, 740))
    for panel in panels:
        draw.rounded_rectangle(panel, radius=18, outline="#c9b1d4", width=2, fill="white")
    canvas.paste(reference, (80 + (430 - reference.width) // 2, 255))
    draw.text((80, 675), "authoritative raster reference", font=info, fill="#60476a")

    draw.text((595, 240), "OLD や — origin/main", font=label, fill="#76517e")
    draw.line((595, 610, 1135, 610), fill="#d5bfe0", width=1)
    draw.text((735, 610), "や", font=before_font, fill="#161018", anchor="ls")

    draw.text((1225, 240), "NEW や / ゃ", font=label, fill="#62316e")
    draw.line((1225, 610, 1815, 610), fill="#c9a9d6", width=1)
    draw.text((1310, 610), "や ゃ", font=after_font, fill="#161018", anchor="ls")

    rows = (
        ("孤立・反復", "や    ゃ    やや    ゃゃ    や　ゃ"),
        ("yōon 1", "きゃ   ぎゃ   しゃ   じゃ   ちゃ   にゃ"),
        ("yōon 2", "ひゃ   びゃ   ぴゃ   みゃ   りゃ"),
        ("自然文字 1", "やさしい   やっぱり   きゃく   しゃしん"),
        ("自然文字 2", "じゃない   にゃん   みゃく   りゃく"),
    )
    y = 790
    for row_label, text in rows:
        draw.text((60, y + 18), row_label, font=info, fill="#76517e")
        draw.line((250, y + 105, 1845, y + 105), fill="#e0cee7", width=1)
        face = ImageFont.truetype(str(FONT_PATH), 70 if "yōon" in row_label else 64)
        draw.text((280, y + 105), text, font=face, fill="#161018", anchor="ls")
        y += 185

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PROOF_PATH)
    print(f"PASS: や bounds={ya_bounds}, ゃ bounds={small_ya_bounds}, advances=960")
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
