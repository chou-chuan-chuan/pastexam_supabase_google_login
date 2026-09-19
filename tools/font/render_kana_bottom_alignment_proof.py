#!/usr/bin/env python3
"""Compare whole-system y translations of immutable 1.026, without refitting."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from statistics import median, quantiles
import subprocess
import tempfile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from measure_kana_kanji_balance import ROOT, FONT_REL, HAN, HIRAGANA, KATAKANA, MIXED_LINES, CHINESE_JAPANESE_LINES
from render_japanese_weight_proof import LYRICS
from kana_sources.full_data import KANA_STROKES, COMPOSITES

BASE_MAIN = '19cf20cf94feb047245f630506ca909af2e7e49b'
FONT = ROOT / FONT_REL
PROOFS = ROOT / 'tools/font/proofs'
REPORT = ROOT / 'tools/font/reports/kana-bottom-alignment.json'
GROUPS = {'han': HAN, 'hiragana': HIRAGANA, 'katakana': KATAKANA, 'combined_kana': HIRAGANA+KATAKANA}
MARK_NAMES = {'uni3099', 'uni309A', 'uni3099.katakana', 'uni309A.katakana'}
MOVED_CHARACTERS = set(KANA_STROKES) | set(COMPOSITES) | set('ゝゞヽヾー゙゚゛゜')
MOVED_NAMES = {f'uni{ord(c):04X}' for c in MOVED_CHARACTERS} | MARK_NAMES
LINES = MIXED_LINES + ('あなたのことを忘れない', '世界で一番大切な人')
PAPER, INK, MUTED = '#fffdf9', '#211b28', '#736c76'


def baseline_bytes():
    return subprocess.check_output(['git', 'show', f'{BASE_MAIN}:{FONT_REL}'], cwd=ROOT)


def ink_bounds(font, character):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[font.getBestCmap()[ord(character)]].draw(pen)
    return tuple(pen.bounds)


def measure(font):
    result = {}
    for group, characters in GROUPS.items():
        boxes = [ink_bounds(font, c) for c in characters]
        bottoms = [b[1] for b in boxes]
        result[group] = {
            'count': len(characters), 'characters': characters,
            'yMin': median(bottoms), 'yMax': median(b[3] for b in boxes),
            'center_y': median((b[1]+b[3])/2 for b in boxes),
            'height': median(b[3]-b[1] for b in boxes),
            'width': median(b[2]-b[0] for b in boxes),
            'bottom_min': min(bottoms), 'bottom_max': max(bottoms),
            'bottom_quartiles': quantiles(bottoms, n=4, method='inclusive'),
        }
    return result


def measured_candidates(before):
    delta = before['han']['yMin'] - before['combined_kana']['yMin']
    center = round(delta)  # integer TrueType translation, no second rounding
    return delta, (center-8, center, center+8)


def translated_candidate(data, delta):
    """Proof-only transform of accepted glyph coordinates and Japanese anchors.

    Simple component sources move once. Composite deltas remain identical.
    This never writes the production font or any handwriting source.
    """
    font = TTFont(BytesIO(data), recalcTimestamp=False)
    for name in MOVED_NAMES:
        glyph = font['glyf'][name]
        if not glyph.isComposite():
            glyph.coordinates.translate((0, delta))
    for name in MOVED_NAMES:
        font['glyf'][name].recalcBounds(font['glyf'])
    matches = 0
    for lookup in font['GPOS'].table.LookupList.Lookup:
        if lookup.LookupType != 4:
            continue
        for sub in lookup.SubTable:
            if set(sub.MarkCoverage.glyphs) == MARK_NAMES:
                matches += 1
                for record in sub.MarkArray.MarkRecord:
                    record.MarkAnchor.YCoordinate += delta
                for record in sub.BaseArray.BaseRecord:
                    for anchor in record.BaseAnchor:
                        if anchor:
                            anchor.YCoordinate += delta
    assert matches == 1
    return font


def label(size=20):
    return ImageFont.load_default(size=size)


def comparison(versions, lines, size, path, title):
    step = max(38, round(size*1.4))
    image = Image.new('RGB', (2040, 200+size+len(lines)*(len(versions)*step+25)), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((28, 18), title, font=label(28), fill=INK)
    draw.text((28, 60), f'{size}px - identical sizes, advances and common baseline; y translation only', font=label(18), fill=MUTED)
    y = 140+size
    for text in lines:
        for caption, font_path in versions:
            draw.text((22,y-size*.7), caption, font=label(16), fill='#813b56')
            draw.line((110,y,2005,y), fill='#e2dce3')
            draw.text((115,y), text, font=ImageFont.truetype(str(font_path),size), anchor='ls', fill=INK)
            y += step
        y += 25
    image.save(path, optimize=True)


def diagnostic(before_path, after_path, before, after, delta):
    rows = [('Han','漢字日本音楽世界鉄壁','han'),('Hiragana','あいうえおかきくけこ','hiragana'),
            ('Katakana','アイウエオカキクケコ','katakana')]
    image = Image.new('RGB',(1950,1240),PAPER)
    draw=ImageDraw.Draw(image)
    draw.text((28,18),'Kana / Han bottom alignment - identical 960-unit cells',font=label(28),fill=INK)
    draw.text((28,64),f'Black baseline y=0 | Green Han median yMin={before["han"]["yMin"]} | Orange 1.026 bottom | Blue 1.027 bottom',font=label(18),fill=MUTED)
    draw.text((28,94),f'All final kana move {delta} units; size and x placement are unchanged. Guide medians use the complete reference samples.',font=label(17),fill=MUTED)
    for i,(caption,characters,key) in enumerate(rows):
        top=150+i*355
        draw.text((28,top),caption,font=label(22),fill=INK)
        for j,(path,version) in enumerate(((before_path,'1.026'),(after_path,'1.027'))):
            baseline=top+135+j*155
            draw.text((24,baseline-70),version,font=label(18),fill=MUTED)
            for k,c in enumerate(characters):
                x=130+k*175
                draw.rectangle((x,baseline-108,x+120,baseline+28),outline='#d0c9d2')
                draw.text((x,baseline),c,font=ImageFont.truetype(str(path),128),anchor='ls',fill=INK)
            guides=[(0,'#4f4a53'),(before['han']['yMin'],'#2e996c')]
            if key!='han':
                guides += [(before[key]['yMin'],'#cf8733'),(after[key]['yMin'],'#3382bd')]
            for value,color in guides:
                yy=baseline-value/8
                draw.line((125,yy,1900,yy),fill=color,width=2)
    image.save(PROOFS/'quanfangwei-kana-bottom-alignment-guides.png',optimize=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates-only',action='store_true')
    args=parser.parse_args()
    raw=baseline_bytes()
    with TTFont(BytesIO(raw)) as font:
        assert font['name'].getDebugName(5)=='Version 1.026'
        before=measure(font)
    measured,candidates=measured_candidates(before)
    results={}
    with tempfile.TemporaryDirectory(prefix='qfw-bottom-proof-') as temp:
        old_path=Path(temp)/'1.026.ttf';old_path.write_bytes(raw)
        versions=[('1.026',old_path)]
        for delta in candidates:
            font=translated_candidate(raw,delta)
            path=Path(temp)/f'candidate-{delta}.ttf';font.save(path)
            results[str(delta)]=measure(font)
            limits=[]
            for name in MOVED_NAMES:
                glyph=font['glyf'][name]
                limits += [glyph.yMin,glyph.yMax]
            assert min(limits)>font['hhea'].descent and max(limits)<font['hhea'].ascent
            assert min(limits)>-font['OS/2'].usWinDescent and max(limits)<font['OS/2'].usWinAscent
            # Typographic ascender/descender set line spacing, not clipping.
            # Standalone combining marks already exceed sTypoAscender in 1.026;
            # lowering them reduces that existing overhang. Attached text fits.
            text_glyphs=[font['glyf'][n] for n in MOVED_NAMES-MARK_NAMES]
            assert min(g.yMin for g in text_glyphs)>font['OS/2'].sTypoDescender
            assert max(g.yMax for g in text_glyphs)<font['OS/2'].sTypoAscender
            versions.append((str(delta),path))
        comparison(versions,LINES,64,PROOFS/'quanfangwei-kana-bottom-alignment-candidates.png',
                   'Whole-system downward shift - measured candidates')
        diagnostic(old_path,versions[2][1],before,results[str(candidates[1])],candidates[1])
        if not args.candidates_only:
            from japanese.build_kana import JAPANESE_BOTTOM_ALIGNMENT_SHIFT
            with TTFont(FONT) as final_font:
                assert final_font['name'].getDebugName(5)=='Version 1.027'
                after=measure(final_font)
            for size,suffix in ((32,''),(20,'-small'),(64,'-large')):
                comparison([('1.026',old_path),('1.027',FONT)],LINES+LYRICS+CHINESE_JAPANESE_LINES,size,
                           PROOFS/f'quanfangwei-kana-bottom-alignment{suffix}.png','Kana / Han bottom alignment - before / after')
            derivative_lines=(
                'あぁ いぃ うぅ えぇ おぉ つっ やゃ ゆゅ よょ わゎ かゕ けゖ',
                'アァ イィ ウゥ エェ オォ ツッ ヤャ ユュ ヨョ ワヮ カヵ ケヶ',
                *(' '.join(a+b for b in 'ゃゅょ') for a in 'きぎしじちにひびぴみり'),
                'がぎぐげご ざじずぜぞ だぢづでど', 'ばびぶべぼ ぱぴぷぺぽ ゔ',
                'が が　ぎ ぎ　ず ず　で で　ば ば　ぱ ぱ　ゔ ゔ',
                'ガ ガ　ギ ギ　ズ ズ　デ デ　バ バ　パ パ　ヴ ヴ',
                'キャ キュ キョ シャ シュ ショ ニャ ニュ ニョ',
                '゛ ゜ ゝ ゞ ヽ ヾ ー　壁 堅 鉄壁 堅い心',
            )
            comparison([('1.026',old_path),('1.027',FONT)],derivative_lines,48,
                       PROOFS/'quanfangwei-kana-bottom-alignment-derivatives.png','Small kana, yoon and attached marks move together')
            diagnostic(old_path,FONT,before,after,JAPANESE_BOTTOM_ALIGNMENT_SHIFT)
            data={'base_main':BASE_MAIN,'version':'1.027','before':before,'measured_delta':measured,
                  'candidate_deltas':candidates,'candidates':results,'final_delta':JAPANESE_BOTTOM_ALIGNMENT_SHIFT,'after':after}
            REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'before':before,'measured_delta':measured,'candidates':candidates},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
