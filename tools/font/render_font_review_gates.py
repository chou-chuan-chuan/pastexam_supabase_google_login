#!/usr/bin/env python3
"""Render the required visual gates for handwriting optical review."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_DIR = REPO_ROOT / "tools/font/proofs"
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"

HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
CHANGED = "あ き す た ち つ ぬ ね の へ ほ ま よ ら り る れ ろ わ を"

BEFORE_AFTER = PROOF_DIR / "quanfangwei-hiragana-optical-before-after-proof.png"
SMALL_KANA = PROOF_DIR / "quanfangwei-small-kana-ya-proof.png"
SPECIALS = PROOF_DIR / "quanfangwei-user-japanese-specials-proof.png"
MIXED = PROOF_DIR / "quanfangwei-user-japanese-mixed-proof.png"


def face(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def render_half_grid(draw, font_path: Path, x0: int, y0: int, heading: str) -> None:
    draw.text((x0, y0), heading, font=face(font_path, 34), fill="#35215f")
    cell_w, cell_h = 118, 145
    grid_y = y0 + 58
    glyph_font = face(font_path, 92)
    label_font = face(font_path, 14)
    for index, character in enumerate(HIRAGANA):
        row, column = divmod(index, 10)
        x = x0 + column * cell_w
        y = grid_y + row * cell_h
        draw.rectangle((x, y, x + cell_w, y + cell_h), fill="white", outline="#d7d2db", width=2)
        draw.text((x + 6, y + 5), f"{character} U+{ord(character):04X}", font=label_font, fill="#716779")
        baseline = y + 119
        draw.line((x + 7, baseline + 2, x + cell_w - 7, baseline + 2), fill="#efc7cf", width=1)
        draw.text((x + cell_w / 2, baseline), character, font=glyph_font, fill="#111", anchor="ms")


def render_before_after(baseline_font: Path) -> None:
    image = Image.new("RGB", (2500, 960), "#fffdf9")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), "Gate B — accepted 1.013 baseline / topology-preserving optical transforms", font=face(CURRENT_FONT, 35), fill="#35215f")
    render_half_grid(draw, baseline_font, 45, 90, "Before — accepted USER_HANDWRITING_REFINED")
    render_half_grid(draw, CURRENT_FONT, 1295, 90, "After — uniform scale + translation only")
    draw.text((45, 880), f"Optically adjusted: {CHANGED}", font=face(CURRENT_FONT, 23), fill="#5e5264")
    draw.text((45, 918), "All other modern Hiragana are explicit reviewed identity transforms; no stroke branches or point topology changed.", font=face(CURRENT_FONT, 19), fill="#5e5264")
    image.save(BEFORE_AFTER, "PNG", optimize=True)


def render_small_kana() -> None:
    image = Image.new("RGB", (1900, 1320), "#fffdf9")
    draw = ImageDraw.Draw(image)
    draw.text((55, 32), "Gate C — all small Hiragana derived from normalized large forms", font=face(CURRENT_FONT, 39), fill="#35215f")
    draw.rounded_rectangle((55, 105, 650, 625), radius=28, fill="white", outline="#d7d2db", width=3)
    draw.text((352, 410), "よ　ょ", font=face(CURRENT_FONT, 230), fill="#111", anchor="mm")
    draw.text((352, 555), "よ → ょ  same structure, 0.72 scale", font=face(CURRENT_FONT, 23), fill="#5e5264", anchor="mm")
    draw.text((710, 145), "やゃ　ゆゅ", font=face(CURRENT_FONT, 132), fill="#111")
    draw.text((1260, 145), "よょ　つっ", font=face(CURRENT_FONT, 132), fill="#111")
    draw.text((710, 345), "Each pair has identical stroke and point topology", font=face(CURRENT_FONT, 24), fill="#5e5264")
    draw.text((710, 485), "あぁ  いぃ  うぅ  えぇ  おぉ", font=face(CURRENT_FONT, 88), fill="#111")
    draw.text((710, 590), "わゎ  かゕ  けゖ", font=face(CURRENT_FONT, 88), fill="#111")
    y = 700
    for size in (48, 72, 120):
        baseline = y + size
        draw.text((55, baseline), f"{size}px", font=face(CURRENT_FONT, 22), fill="#6d35c5", anchor="ls")
        draw.line((165, baseline + 3, 1840, baseline + 3), fill="#efc7cf", width=1)
        sample = "ぁぃぅぇぉ　ゃゅょっ" if size == 120 else "ぁぃぅぇぉ　ゃゅょっ　きゃ しゃ ちゃ にゃ りゃ"
        draw.text((190, baseline), sample, font=face(CURRENT_FONT, size), fill="#111", anchor="ls")
        y = baseline + 72
    draw.text((55, 1175), "Mixed text", font=face(CURRENT_FONT, 24), fill="#6d35c5")
    draw.text((55, 1255), "静かな夜に　きゃっと笑った君を思い出す", font=face(CURRENT_FONT, 64), fill="#111")
    image.save(SMALL_KANA, "PNG", optimize=True)


def render_specials() -> None:
    image = Image.new("RGB", (2000, 1580), "#fffdf9")
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "Gate D — native 懷 upper + native 衣 lower / dedicated 々", font=face(CURRENT_FONT, 40), fill="#35215f")
    panels = [(55, 115, 935, 870, "懐", "U+61D0"), (1065, 115, 1945, 870, "々", "U+3005")]
    for left, top, right, bottom, character, code in panels:
        draw.rounded_rectangle((left, top, right, bottom), radius=30, fill="white", outline="#d7d2db", width=3)
        draw.line((left + 40, bottom - 110, right - 40, bottom - 110), fill="#efc7cf", width=2)
        draw.text(((left + right) / 2, bottom - 115), character, font=face(CURRENT_FONT, 540), fill="#111", anchor="ms")
        draw.text(((left + right) / 2, bottom - 55), code, font=face(CURRENT_FONT, 27), fill="#5e5264", anchor="ms")
    draw.text((55, 950), "Native 懷 and 衣 are the component sources; 夕 is an unmodified control:", font=face(CURRENT_FONT, 26), fill="#6d35c5")
    control_baseline = 1460
    draw.line((55, control_baseline + 5, 1945, control_baseline + 5), fill="#efc7cf", width=2)
    draw.text((55, control_baseline), "懷　懐　衣　々　夕", font=face(CURRENT_FONT, 190), fill="#111", anchor="ls")
    image.save(SPECIALS, "PNG", optimize=True)


def render_mixed() -> None:
    lines = [
        "懐かしい風が頬を撫でて",
        "日々の思い出",
        "時々",
        "色々",
    ]
    sizes = (24, 32, 48, 72, 112)
    image = Image.new("RGB", (2100, 2550), "#fffdf9")
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "Gate E — required Japanese mixed-text proof", font=face(CURRENT_FONT, 40), fill="#35215f")
    y = 115
    for size in sizes:
        label = face(CURRENT_FONT, 20)
        text_face = face(CURRENT_FONT, size)
        draw.text((55, y + 5), f"{size}px", font=label, fill="#6d35c5")
        baseline = y + 45 + size
        for line in lines:
            draw.line((150, baseline + 3, 2040, baseline + 3), fill="#efc7cf", width=1)
            draw.text((170, baseline), line, font=text_face, fill="#111", anchor="ls")
            baseline += max(52, round(size * 1.45))
        y = baseline + 30
    image.save(MIXED, "PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-font", type=Path, required=True)
    args = parser.parse_args()
    if not args.baseline_font.is_file():
        raise FileNotFoundError(args.baseline_font)
    if not CURRENT_FONT.is_file():
        raise FileNotFoundError(CURRENT_FONT)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    render_before_after(args.baseline_font)
    render_small_kana()
    render_specials()
    render_mixed()
    for path in (BEFORE_AFTER, SMALL_KANA, SPECIALS, MIXED):
        print(f"Rendered {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
