#!/usr/bin/env python3
"""Render actual font ink, visible full-width cells and all requested samples."""
from pathlib import Path
import tempfile

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from render_do_base_clearance_proof import ShapedFont
from verify_sokuon_position import (TTF, ROOT, baseline_bytes, box, HIRAGANA_SAMPLES,
                                    KATAKANA_SAMPLES, COMPARISONS)

PROOFS = ROOT / 'tools/font/proofs'
BG, INK, MUTED = '#fffdf9', '#211b28', '#736c76'
ACCENT, GUIDE, BOUNDS = '#813b56', '#b9c7d4', '#008575'


def label(size):
    return ImageFont.load_default(size=size)


def cells(path, shaped):
    width, height = 1480, 1430
    image = Image.new('RGB', (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.text((24, 18), 'Version 1.032 | Sokuon inside its own 960-unit cell', font=label(30), fill=INK)
    draw.text((24, 61), 'Gray: advance box | dashed: x/y center | rose: baseline | teal: ink bounds', font=label(20), fill=MUTED)
    draw.text((24, 91), 'Em cell: x=0..960, y=-200..824 (1024 UPM). All small anchors: xMin=180, yMin=-32.', font=label(19), fill=MUTED)
    size = 300
    scale = size / 1024
    with TTFont(path) as font:
        for row, text in enumerate(('つっツッ', 'ゃゅょっ', 'ャュョッ')):
            for col, c in enumerate(text):
                x, top = 36 + col * 365, 170 + row * 420
                baseline = top + 824 * scale
                right, bottom = x + 960 * scale, top + size
                cx, cy = (x + right) / 2, (top + bottom) / 2
                draw.rectangle((x, top, right, bottom), outline=GUIDE, width=2)
                for y in range(round(top), round(bottom), 12):
                    draw.line((cx, y, cx, min(y + 6, bottom)), fill=GUIDE)
                for xx in range(round(x), round(right), 12):
                    draw.line((xx, cy, min(xx + 6, right), cy), fill=GUIDE)
                draw.line((x, baseline, right, baseline), fill=ACCENT, width=2)
                shaped.draw(draw, x, baseline, c, size)
                b = box(font, font.getBestCmap()[ord(c)])
                draw.rectangle((x+b[0]*scale, baseline-b[3]*scale, x+b[2]*scale, baseline-b[1]*scale), outline=BOUNDS, width=2)
                draw.text((x, top-34), f'U+{ord(c):04X}  |  advance 960', font=label(19), fill=INK)
                draw.text((x, bottom+14), f'Ink {b}', font=label(17), fill=BOUNDS)
                draw.text((x, bottom+40), f'Size {b[2]-b[0]} x {b[3]-b[1]}', font=label(17), fill=MUTED)
    image.save(PROOFS / 'quanfangwei-sokuon-cell-position.png', optimize=True)


def comparison(versions):
    required = ('ちょっと', 'もっと', 'きっと', 'サッカー', 'カップ', 'ベッド')
    sections = [(f'{size}px | required before / after', size, required) for size in (20, 32, 64, 192)]
    sections += [('64px | all natural examples', 64, HIRAGANA_SAMPLES + KATAKANA_SAMPLES),
                 ('64px | reviewed yoon / sokuon comparison', 64, COMPARISONS)]
    column = 960
    height = 120 + sum(64 + len(rows) * (size + 25) for _, size, rows in sections)
    image = Image.new('RGB', (column * 2, height), BG)
    draw = ImageDraw.Draw(image)
    draw.text((24, 16), 'Sokuon lower-left placement | unchanged size, topology and full-width advances', font=label(29), fill=INK)
    draw.text((24, 60), 'Actual 20 / 32 / 64 / 192 px. HarfBuzz + FreeType; canonical font only; no fallback.', font=label(22), fill=MUTED)
    top = 120
    for title, size, rows in sections:
        for col, (version, shaped) in enumerate(versions):
            left = 24 + col * column
            draw.text((left, top), f'{version} | {title}', font=label(23), fill=ACCENT)
            for i, text in enumerate(rows):
                baseline = top + 52 + size + i * (size + 25)
                draw.line((left, baseline, left + column - 48, baseline), fill='#e4dde4')
                end = shaped.draw(draw, left + 12, baseline, text, size)
                assert end < left + column - 24, (text, 'clipped row')
        top += 64 + len(rows) * (size + 25)
    image.save(PROOFS / 'quanfangwei-sokuon-before-after.png', optimize=True)


def main():
    with tempfile.TemporaryDirectory(prefix='qfw-sokuon-proof-') as directory:
        temp = Path(directory)
        before = temp / 'before-1.031.ttf'
        before.write_bytes(baseline_bytes())
        # Fail explicitly for missing sample glyphs, never silently fall back.
        for path in (before, TTF):
            with TTFont(path) as font:
                chars = ''.join(HIRAGANA_SAMPLES + KATAKANA_SAMPLES + COMPARISONS) + 'つっツッゃゅょャュョ'
                assert all(ord(c) in font.getBestCmap() for c in chars)
        versions = [('Version 1.031 BEFORE', ShapedFont(before, temp)),
                    ('Version 1.032 AFTER', ShapedFont(TTF, temp))]
        cells(TTF, versions[1][1])
        comparison(versions)
    print('Rendered quanfangwei-sokuon-cell-position.png and quanfangwei-sokuon-before-after.png')


if __name__ == '__main__':
    main()
