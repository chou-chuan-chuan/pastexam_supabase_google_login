#!/usr/bin/env python3
"""Render the pinned 1.035 and current 1.036 native font at actual pixel sizes."""
from pathlib import Path
import tempfile

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from render_do_base_clearance_proof import ShapedFont
from verify_kana_refinements import ROOT, TTF, HANDAKUTEN, baseline_bytes

PROOFS = ROOT / 'tools/font/proofs'
BG, INK, MUTED, ACCENT = '#fffdf9', '#211b28', '#736c76', '#813b56'


def render(versions, title, subtitle, rows, filename):
    column = 1100
    sections = [(size, rows) for size in (20, 32, 64, 192)]
    height = 130 + sum(70 + len(texts) * (size + 28) for size, texts in sections)
    image = Image.new('RGB', (column * 2, height), BG)
    draw = ImageDraw.Draw(image)
    label = lambda size: ImageFont.load_default(size=size)
    draw.text((24, 16), title, font=label(29), fill=INK)
    draw.text((24, 60), subtitle, font=label(21), fill=MUTED)
    draw.text((24, 91), 'Actual 20 / 32 / 64 / 192 px. HarfBuzz + FreeType; native font only; no fallback.', font=label(21), fill=MUTED)
    top = 130
    for size, texts in sections:
        for col, (version, shaped) in enumerate(versions):
            left = 24 + col * column
            draw.text((left, top), f'{version} | {size}px', font=label(23), fill=ACCENT)
            for row, text in enumerate(texts):
                baseline = top + 52 + size + row * (size + 28)
                draw.line((left, baseline, left + column - 48, baseline), fill='#e4dde4')
                end = shaped.draw(draw, left + 12, baseline, text, size)
                assert end < left + column - 24, (text, 'clipped row')
        top += 70 + len(texts) * (size + 28)
    image.save(PROOFS / filename, optimize=True)


def main():
    junctions = ('マ ス ズ', 'マイク', 'マッチ', 'スイス', 'ズーム')
    hands = tuple(HANDAKUTEN)
    with tempfile.TemporaryDirectory(prefix='qfw-kana-proof-') as directory:
        temp = Path(directory)
        before = temp / 'before-1.035.ttf'
        before.write_bytes(baseline_bytes())
        for path in (before, TTF):
            with TTFont(path) as font:
                assert all(ord(c) in font.getBestCmap() for c in ''.join(junctions + hands))
        versions = [('Version 1.035 BEFORE', ShapedFont(before, temp)),
                    ('Version 1.036 AFTER', ShapedFont(TTF, temp))]
        render(versions, 'Katakana junctions | local protruding stroke ends removed',
               'MA and SU retain their original bounds, stroke weight and advances. ZU inherits the corrected SU body.',
               junctions, 'quanfangwei-katakana-junctions.png')
        render(versions, 'Handakuten spacing | all ten attachments move outward',
               'Each ring moves right 16 and up 24 font units. Ring outlines, body outlines and 960-unit advances are unchanged.',
               hands, 'quanfangwei-handakuten-spacing.png')
    print('Rendered native junction and handakuten comparisons at 20, 32, 64 and 192 px')


if __name__ == '__main__':
    main()
