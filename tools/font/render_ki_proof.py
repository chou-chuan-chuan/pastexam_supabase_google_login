#!/usr/bin/env python3
"""Render the Version 1.021 maintainer-handwritten ki/gi review proof."""

from io import BytesIO
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REFERENCE_PATH = Path(__file__).resolve().parent / "references/U+304D-ki-maintainer-handwritten.png"
PROOF_PATH = Path(__file__).resolve().parent / "proofs/quanfangwei-ki-proof.png"
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
    before_font = ImageFont.truetype(BytesIO(before_bytes), 120)
    after_font = ImageFont.truetype(str(FONT_PATH), 120)

    ttfont = TTFont(FONT_PATH, recalcTimestamp=False)
    cmap = ttfont.getBestCmap()
    if cmap.get(0x304D) != "uni304D" or cmap.get(0x304E) != "uni304E":
        raise RuntimeError("Current font does not map U+304D/U+304E to uni304D/uni304E")
    ki_bounds = bounds(ttfont, "uni304D")
    gi_bounds = bounds(ttfont, "uni304E")
    gi = ttfont["glyf"]["uni304E"]
    components = [component.getComponentInfo() for component in gi.components] if gi.isComposite() else []
    if not components or components[0][0] != "uni304D" or components[1][0] != "uni3099":
        raise RuntimeError(f"U+304E does not inherit current ki + dakuten: {components}")
    ttfont.close()

    canvas = Image.new("RGB", (1900, 1500), "#fffdf9")
    draw = ImageDraw.Draw(canvas)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    info = ImageFont.truetype(str(FONT_PATH), 24)
    label = ImageFont.truetype(str(FONT_PATH), 30)
    draw.text((55, 45), "QuanFangwei Version 1.021 — maintainer-handwritten き / ぎ", font=title, fill="#25152c")
    draw.text((55, 105), f"き bounds={ki_bounds}, advance=960   ぎ bounds={gi_bounds}, advance=960", font=info, fill="#60476a")
    draw.text((55, 140), f"ぎ components={components}", font=info, fill="#60476a")

    reference = Image.open(REFERENCE_PATH).convert("RGB")
    reference.thumbnail((430, 500))
    draw.rounded_rectangle((55, 205, 525, 755), radius=18, outline="#c9b1d4", width=2, fill="white")
    canvas.paste(reference, (75 + (430 - reference.width) // 2, 235))
    draw.text((75, 710), "authoritative raster reference", font=info, fill="#60476a")

    draw.rounded_rectangle((555, 205, 1205, 755), radius=18, outline="#d8c6e0", width=2, fill="#fbf7fc")
    draw.text((585, 245), "Before (origin/main)", font=label, fill="#76517e")
    draw.line((585, 570, 1175, 570), fill="#d5bfe0", width=1)
    draw.text((690, 570), "き ぎ", font=before_font, fill="#161018", anchor="ls")

    draw.rounded_rectangle((1235, 205, 1845, 755), radius=18, outline="#9d72ae", width=3, fill="#f8effb")
    draw.text((1265, 245), "Version 1.021", font=label, fill="#62316e")
    draw.line((1265, 570, 1815, 570), fill="#c9a9d6", width=1)
    draw.text((1340, 570), "き ぎ", font=after_font, fill="#161018", anchor="ls")

    y = 805
    for size in (24, 32, 48, 72):
        face = ImageFont.truetype(str(FONT_PATH), size)
        baseline = y + max(80, round(size * 1.3))
        draw.line((55, baseline, 1845, baseline), fill="#e0cee7", width=1)
        draw.text((60, y + 5), f"{size}px", font=info, fill="#76517e")
        draw.text((180, baseline), "き   ぎ   きき   ぎき   ぎん   きれい   好き   大きい", font=face, fill="#161018", anchor="ls")
        y = baseline + 20

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PROOF_PATH)
    print("PASS: U+304E is a current uni304D + uni3099 composite")
    print(f"Wrote {PROOF_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
