#!/usr/bin/env python3
"""Render actual 1.025/1.026 fonts at identical sizes, with no outline refitting."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import subprocess
import tempfile

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from measure_kana_kanji_balance import (
    ROOT, BASE_MAIN, FONT_REL, REFERENCE_PATH, MIXED_LINES, CHINESE_JAPANESE_LINES,
    HIRAGANA, KATAKANA, HAN, measure_groups,
)
from render_japanese_weight_proof import LYRICS
from japanese.build_kana import bounds
from kana_sources.full_data import YOON_SMALL_KANA_OFFSETS

PROOFS = ROOT / 'tools/font/proofs'
REPORTS = ROOT / 'tools/font/reports'
FONT = ROOT / FONT_REL
PAPER, INK, ACCENT, MUTED = '#fffdf9', '#211b28', '#72364d', '#736c76'


def label(size=20):
    return ImageFont.load_default(size=size)


def face(path, size):
    return ImageFont.truetype(str(path), size)


def comparison(before, lines, size, name, subtitle):
    step = max(38, int(size * 1.4))
    image = Image.new('RGB', (1960, 200 + size + len(lines) * (step * 2 + 24)), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((28, 18), f'Kana / Han optical balance - {size}px', font=label(28), fill=INK)
    draw.text((28, 62), subtitle, font=label(18), fill=MUTED)
    draw.text((28, 91), 'A = 1.025    B = 1.026 measured scale    |    identical font size, advance and baseline', font=label(18), fill=MUTED)
    y = 140 + size
    for text in lines:
        for mark, path in (('A', before), ('B', FONT)):
            draw.text((30, y-size*.7), mark, font=label(18), fill=ACCENT)
            draw.line((80, y, 1930, y), fill='#e8e2e8')
            draw.text((85, y), text, font=face(path, size), anchor='ls', fill=INK)
            y += step
        y += 24
    image.save(PROOFS / name, optimize=True)


def diagnostic():
    rows = [('HAN', '漢字日本音楽鉄壁人心'), ('HIRAGANA', 'あいうえお'),
            ('HIRAGANA', 'かきくけこ'), ('HIRAGANA', 'さしすせそ'),
            ('KATAKANA', 'アイウエオ'), ('KATAKANA', 'カキクケコ'), ('KATAKANA', 'シャュョ')]
    image = Image.new('RGB', (1720, 120 + 210*len(rows)), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((28, 18), '1.026 - identical 960-unit cells', font=label(28), fill=INK)
    draw.text((28, 60), 'Gray: cell / baseline    Red: actual ink bounds    Blue: ink-box center', font=label(18), fill=MUTED)
    with TTFont(FONT) as font:
        for row, (group, chars) in enumerate(rows):
            top = 115 + row*210
            draw.text((28, top), group, font=label(17), fill=ACCENT)
            baseline = top+137
            for i, c in enumerate(chars):
                x = 40+i*165
                # 128 px/em => 960-unit advance is 120 px, ascender-space 104.
                draw.rectangle((x, baseline-104, x+120, baseline+24), outline='#bcb6bf')
                draw.line((x, baseline, x+120, baseline), fill='#a7a1aa')
                draw.text((x, baseline), c, font=face(FONT, 128), anchor='ls', fill=INK)
                bb = bounds(font, font.getBestCmap()[ord(c)])
                x0,y0,x1,y1 = bb
                draw.rectangle((x+x0/8, baseline-y1/8, x+x1/8, baseline-y0/8), outline='#ba5276')
                cx,cy = x+(x0+x1)/16, baseline-(y0+y1)/16
                draw.line((cx-4,cy,cx+4,cy), fill='#2279a0', width=2)
                draw.line((cx,cy-4,cx,cy+4), fill='#2279a0', width=2)
                draw.text((x, baseline+31), f'U+{ord(c):04X}', font=label(14), fill=MUTED)
    image.save(PROOFS / 'quanfangwei-kana-kanji-same-em.png', optimize=True)


def report():
    data = json.loads(REFERENCE_PATH.read_text())
    with TTFont(FONT) as font:
        final = measure_groups(font)
    summary = {'base_main': BASE_MAIN, 'version': '1.026', 'han_sample': HAN,
               'balance': data['balance'], 'final': final}
    (REPORTS / 'kana-kanji-scale-balance.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    lines = ['# Version 1.026 — Kana–Han mixed-script optical balance', '',
             f'Base main: `{BASE_MAIN}` (merged PR #32, Version 1.025).', '',
             'The accepted Master v2 handwriting and per-glyph normalization are unchanged. '
             'Only one uniform scale per script follows the 1.025 stage. External fonts provide '
             'relative proportions; the unchanged QuanFangwei Han ink body supplies the absolute size.', '',
             f'**Han sample ({len(HAN)} unique characters):** {HAN}', '',
             'Sample selection: every unique Han character in the six requested lines, all six existing '
             'lyric fixtures and the four existing Chinese/Japanese alignment fixtures, in first-appearance order. '
             '`壁` is one of 59; `堅` is reserved for QA. No frequency weighting or hand-picked exclusions.', '',
             'Optical height/width = exact ink bounding box / UPM. Optical center = bounding-box midpoint. '
             'The secondary area statistic is **bounding-box area**, not ink coverage. '
             'Each kana sample is the complete 46 modern basic characters, excluding small/voiced forms.', '',
             f'Hiragana: {HIRAGANA}', '', f'Katakana: {KATAKANA}', '',
             '| Font | UPM | Han median height/em | Hiragana height/em | Katakana height/em | Hira/Han | Kata/Han |',
             '|---|---:|---:|---:|---:|---:|---:|']
    groups = []
    for key in ('noto','source_han','production_1_025'):
        ref=data['references'][key]
        groups.append((ref['family']+' '+ref['version'], ref['upm'], ref['groups']))
    groups.append(('QuanFangwei Version 1.026',1024,final))
    for title,upm,group in groups:
        h,hi,ka=(group[g]['median']['height_em'] for g in ('han','hiragana','katakana'))
        lines.append(f'| {title} | {upm} | {h:.9f} | {hi:.9f} | {ka:.9f} | {hi/h:.9f} | {ka/h:.9f} |')
    lines += ['', 'Median of the Noto and Source Han ratios is used as one related standards reference family; '
              'neither external absolute kana height enters the target.', '',
              '| Script | Standard ratio | QFW Han × ratio = target height/em | Shared scale |',
              '|---|---:|---:|---:|']
    for key in ('hiragana','katakana'):
        r=data['balance'][key]
        lines.append(f"| {key} | {r['standard_height_ratio']:.12f} | {r['target_height_em']:.12f} | {r['scale']:.12f} |")
    lines += ['', '`HIRAGANA_HAN_BALANCE_SCALE = 0.894078195335`; '
              '`KATAKANA_HAN_BALANCE_SCALE = 0.946843040146`.', '',
              'Factor = (QuanFangwei Han median height × standard kana/Han ratio) / 1.025 kana median height. '
              'Both measured factors are below 1. Final median heights are within one font unit of the analytical targets after outline quantization.', '',
              '## Secondary diagnostics', '',
              '| Font | Script | Median width/em | Width/Han | Median bbox area/em² | Area/Han | Median center-y/em | Center-y minus Han/em |',
              '|---|---|---:|---:|---:|---:|---:|---:|']
    for title,_,group in groups:
        for key in ('hiragana','katakana'):
            m=group[key]['median'];r=group[key]['relative_to_han']
            lines.append(f"| {title} | {key} | {m['width_em']:.9f} | {r['width_em']:.9f} | {m['bbox_area_em2']:.9f} | {r['bbox_area_em2']:.9f} | {m['center_y_em']:.9f} | {r['center_y_delta_em']:.9f} |")
    lines += ['', 'These secondary statistics are diagnostics, not extra per-glyph fitting targets. '
              'The handwritten width and open counters differ from sans-serif references by design.', '',
              '## Construction and scope', '',
              '- Scale around each accepted ink-box center; scale geometry and pressure together. '
              'No axis stretching, source-point edits or additional per-glyph normalization.',
              '- The 12 small Hiragana derive from balanced large bases via the existing 0.72 geometry / 0.92 pressure relationship. '
              'Existing Katakana derivations are retained. No second balance scale is applied to derived small forms.',
              '- All six yōon glyphs keep `(xMin,yMin)=(180,24)` using translation only. Advances stay 960; no ligatures or pair positioning.',
              '- Dakuten/handakuten designs scale with each script about their existing mark anchor. '
              'Two unmapped Katakana mark variants allow precomposed and decomposed forms to share the same size. '
              'GSUB `ccmp` selects these marks after Katakana; GPOS and composite anchors apply the same scaled 1.025 offset. '
              'This is contextual mark selection, not a ligature or character-spacing rule.',
              '- Iteration marks use their script factor. `ー` uses the Katakana factor. '
              'Spacing/standalone combining marks use the Hiragana factor. General punctuation is unchanged.',
              '- All Han, including 壁/堅 and all prior transforms, Latin/French/German, '
              'CSS/JS and application/database code remain unchanged.', '',
              'Yōon translations after derivation: `'+repr(YOON_SMALL_KANA_OFFSETS)+'`.', '',
              '## Proofs', '',
              '- [Normal lyric size, 32 px](../proofs/quanfangwei-kana-kanji-scale-balance.png)',
              '- [Small text, 20 px](../proofs/quanfangwei-kana-kanji-scale-balance-small.png)',
              '- [Large text, 64 px](../proofs/quanfangwei-kana-kanji-scale-balance-large.png)',
              '- [Identical 960-unit cell diagnostics](../proofs/quanfangwei-kana-kanji-same-em.png)',
              '- [Small kana, all 33 Hiragana yōon, voiced forms and marks](../proofs/quanfangwei-kana-kanji-derivatives.png)', '',
              'Proofs use actual 1.025 and 1.026 TTFs at identical font sizes and baselines, with the original text unchanged. '
              'The measured factors were rendered before acceptance; no arbitrary alternative factor was substituted.', '',
              '## Provenance', '',
              'The build needs neither external fonts nor raster reconstruction. '
              'The 1.025 master and absolute-metric reports remain historical records of the accepted stage. '
              'The current mixed-script size gate is this ratio report.', '']
    for key in ('noto','source_han'):
        ref=data['references'][key]
        lines += [f"- [{ref['family']} {ref['version']}]({ref['provenance']}), SHA256 `{ref['sha256']}`."]
    (REPORTS / 'kana-kanji-scale-balance.md').write_text('\n'.join(lines)+'\n')


def main():
    before_bytes = subprocess.check_output(['git','show',f'{BASE_MAIN}:{FONT_REL}'],cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='qfw-balance-proof-') as temp:
        before=Path(temp)/'1.025.ttf';before.write_bytes(before_bytes)
        for size,suffix in ((32,''),(20,'-small'),(64,'-large')):
            comparison(before,MIXED_LINES+LYRICS+CHINESE_JAPANESE_LINES,size,
                       f'quanfangwei-kana-kanji-scale-balance{suffix}.png',
                       'Requested mixed lines + unchanged production lyric and Chinese/Japanese fixtures')
        derivative_lines = (
            'あぁ いぃ うぅ えぇ おぉ つっ やゃ ゆゅ よょ わゎ かゕ けゖ',
            'アァ イィ ウゥ エェ オォ ツッ ヤャ ユュ ヨョ ワヮ カヵ ケヶ',
            *(' '.join(a+b for b in 'ゃゅょ') for a in 'きぎしじちにひびぴみり'),
            'がぎぐげご ざじずぜぞ だぢづでど',
            'ばびぶべぼ ぱぴぷぺぽ ゔ',
            'ガギグゲゴ ザジズゼゾ ダヂヅデド',
            'バビブベボ パピプペポ ヴ ヷヸヹヺ',
            'キャ キュ キョ シャ シュ ショ ニャ ニュ ニョ',
            'ゝ ゞ ヽ ヾ ー ゛ ゜  あ゙ ぱ  ア゙ パ',
            '壁 堅 鉄壁 堅い心 かべ カベ 平仮名 片仮名',
        )
        comparison(before,derivative_lines,48,'quanfangwei-kana-kanji-derivatives.png',
                   'Same accepted shapes; full-width cells, lower-left yoon and shared mark designs')
    diagnostic()
    report()
    print('Wrote five proof PNGs and metric report (Markdown + scalar JSON).')


if __name__ == '__main__':
    main()
