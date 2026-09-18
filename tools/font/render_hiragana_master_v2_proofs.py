#!/usr/bin/env python3
"""Actual-font master-sheet fidelity, family, derivative, and lyric-size proofs."""
from __future__ import annotations
import json
from io import BytesIO
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt
from render_japanese_weight_proof import LYRICS
from kana_sources.hiragana_master_v2 import MASTER_SOURCES, ROWS, TARGETS, NA_ROW
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
PROOFS = ROOT / 'tools/font/proofs'
BASIC_ROWS = ROWS
YOON = tuple(a+b for a in 'きぎしじちにひびぴみり' for b in 'ゃゅょ')
NATURAL = ('ありがとう','おはよう','よろしく','すき','きれい','さようなら','おやすみ',
           'わたし','ひとり','こころ','せかい','ちょっと','もっと','ありがとう、またね。')
VOICED = ('がぎぐげご','ざじずぜぞ','だぢづでど','ばびぶべぼ','ぱぴぷぺぽ','ゔ')

def font(size):
    return ImageFont.truetype(str(FONT), size)


def masks(character, zoom=4):
    source = MASTER_SOURCES[character]
    crop = source.crop
    reference_path = ROOT / 'tools/font/references' / source.reference
    ref = ImageOps.invert(Image.open(reference_path).convert('L').crop(crop))
    ref = ref.resize((ref.width*zoom, ref.height*zoom), Image.Resampling.LANCZOS)
    current = Image.new('L', ref.size)
    x,y = source.to_source(crop[0], crop[1])
    optical = HIRAGANA_OPTICAL_TRANSFORMS[character]
    assert optical.scale_x is None and optical.scale_y is None
    x = 480 + (x-480)*optical.scale + optical.dx
    y = 500 + (y-500)*optical.scale + optical.dy
    size = round(1024*zoom/(source.scale*optical.scale))
    factor = size/1024
    ImageDraw.Draw(current).text((-x*factor, (y-145)*factor), character,
                                font=font(size), fill=255, anchor='ls')
    return ref,current


def measurements(ref, current):
    a,b = np.asarray(ref)>=128, np.asarray(current)>=128
    return {'ink_iou':round(float((a&b).sum()/(a|b).sum()),4),
            'mean_ink_distance_photo_px':round(float((distance_transform_edt(~a)[b].mean()+
                       distance_transform_edt(~b)[a].mean())/8),4)}


def heading(draw,title,subtitle=''):
    draw.text((28,18),title,fill='#202331',font=ImageFont.load_default(size=25))
    draw.text((28,54),subtitle,fill='#5b6472',font=ImageFont.load_default(size=17))


def main():
    PROOFS.mkdir(exist_ok=True)
    paired=Image.new('RGB',(2040,1440),'#faf9f6')
    heading(ImageDraw.Draw(paired),'Complete Maintainer Master v2: reference / generated font',
            'Left: 41-glyph main sheet + supplementary na-row. Right: actual TTF. Identical fit within each paired cell.')
    diagnostic = Image.new('RGB',(1300,2140),'#faf9f6')
    d = ImageDraw.Draw(diagnostic)
    heading(d,'Master v2: actual TTF / reference overlay',
            'Red = handwriting, blue = production font. Uniform fit only; production pressure differs from raster ink.')
    metrics = {}
    for i,c in enumerate(TARGETS):
        source=MASTER_SOURCES[c]
        # Each source uses its own authoritative image; the combined proof
        # inserts the na-row and preserves all intentional empty cells.
        ref,new=masks(c)
        row=next(i for i,line in enumerate(ROWS) if c in line)
        col=ROWS[row].index(c)
        for side,mask in enumerate((ref,new)):
            cell=ImageOps.invert(mask).convert('RGB')
            cell.thumbnail((155,108),Image.Resampling.LANCZOS)
            paired.paste(cell,(55+col*185+side*1020+(155-cell.width)//2,100+row*117))
        a=np.asarray(ref,dtype=float)/255;b=np.asarray(new,dtype=float)/255
        overlay=Image.fromarray(np.stack([255*(1-b*.85),255*(1-np.maximum(a,b)*.85),255*(1-a*.85)],axis=2).astype('uint8'))
        overlay.thumbnail((225,160),Image.Resampling.LANCZOS)
        px=20+(i%5)*258;py=95+(i//5)*202
        diagnostic.paste(overlay,(px+(225-overlay.width)//2,py))
        d.text((px,py+162),c,font=font(26),fill='#202331')
        metrics[c]=measurements(ref,new)
        d.text((px+38,py+166),f"gap {metrics[c]['mean_ink_distance_photo_px']:.2f}px",font=ImageFont.load_default(size=15),fill='#5b6472')
    paired.save(PROOFS/'quanfangwei-hiragana-master-v2-comparison.png')
    diagnostic.save(PROOFS/'quanfangwei-hiragana-master-v2-overlay.png')
    (PROOFS/'quanfangwei-hiragana-master-v2-fidelity.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')

    full=Image.new('RGB',(1020,1440),'#faf9f6');d=ImageDraw.Draw(full)
    heading(d,'Complete Maintainer Master v2 / Version 1.025','All 46 basic Hiragana refreshed. Main sheet + supplementary na-row. Same font and size throughout.')
    for row,chars in enumerate(BASIC_ROWS):
        y=100+row*117
        for col,c in enumerate(chars):
            if c==' ':continue
            x=55+col*185;d.line((x,y+92,x+160,y+92),fill='#dcdfe3')
            d.text((x,y+92),c,font=font(115),fill='#243f61',anchor='ls')
    full.save(PROOFS/'quanfangwei-hiragana-master-v2-full-46.png')
    full.save(PROOFS/'quanfangwei-hiragana-master-v2-proof.png')

    weight=Image.new('RGB',(1590,1580),'white');d=ImageDraw.Draw(weight)
    heading(d,'Family weight / common baseline / all 46 refreshed','Rows at 24, 32, 48 and 72 px. Normal lyric-size comparisons use identical rendering.')
    for row,chars in enumerate(BASIC_ROWS):
        y=145+row*124
        for x,size in ((50,24),(300,32),(650,48),(1040,72)):
            d.line((x,y,x+350,y),fill='#dcdfe3');d.text((x,y),' '.join(chars.replace(' ','')),font=font(size),fill='#151922',anchor='ls')
    weight.save(PROOFS/'quanfangwei-hiragana-master-v2-family-weight.png')

    text=Image.new('RGB',(2800,1480),'white');d=ImageDraw.Draw(text)
    heading(d,'Production text / Version 1.025','Natural text at 24 / 32 / 48 / 72 px; existing repository lyric fixture follows unchanged.')
    for i,phrase in enumerate(NATURAL):
        y=135+i*72
        for x,size in ((25,24),(475,32),(975,48),(1695,72)):
            d.text((x,y),phrase,font=font(size),fill='#151922',anchor='ls')
    for i,phrase in enumerate(LYRICS):
        d.text((28+(i%2)*1350,1160+(i//2)*68),phrase,font=font(48),fill='#151922')
    text.save(PROOFS/'quanfangwei-hiragana-master-v2-production-text.png')

    derived=Image.new('RGB',(1500,3000),'white');d=ImageDraw.Draw(derived)
    heading(d,'Small kana, marks and full yoon regression','All combinations at 24 / 48 / 72 px. Each small kana keeps its own 960-unit advance.')
    katakana_yoon = tuple(a+b for a in 'キギシジチニヒビピミリ' for b in 'ャュョ')
    lines=['ぁぃぅぇぉ','っ ゃゅょ','ゎ ゕゖ',*VOICED,
           *(' '.join(YOON[i:i+3]) for i in range(0,len(YOON),3)),
           *(' '.join(katakana_yoon[i:i+3]) for i in range(0,len(katakana_yoon),3))]
    for i,line in enumerate(lines):
        for x,size in ((25,24),(350,48),(870,72)):
            d.text((x,135+i*79),line,font=font(size),fill='#151922',anchor='ls')
    derived.save(PROOFS/'quanfangwei-hiragana-master-v2-derivatives-yoon.png')
    render_na_proofs()
    print('Rendered nine master-v2 proofs and fidelity metrics')
    print(json.dumps(metrics,ensure_ascii=False))

def render_na_proofs():
    # Immutable pre-revision font, not a locally installed Japanese typeface.
    base='d89ee8b2b5f4c858e5dade853972194892037f93'
    old_bytes=subprocess.check_output(['git','show',f'{base}:{FONT.relative_to(ROOT)}'],cwd=ROOT)
    old_font=ImageFont.truetype(BytesIO(old_bytes),115)
    focused=Image.new('RGB',(1180,660),'#faf9f6');d=ImageDraw.Draw(focused)
    heading(d,'Na-row fidelity / same Version 1.025','Maintainer reference, previous 1.024, new complete Master v2. Old/new use identical 115 px size and baseline.')
    for y,label in ((150,'Reference'),(345,'Old 1.024'),(540,'New 1.025')):
        d.text((25,y),label,fill='#5b6472',font=ImageFont.load_default(size=18))
    for col,c in enumerate(NA_ROW):
        x=170+col*195
        ref,_=masks(c);ref=ImageOps.invert(ref).convert('RGB');ref.thumbnail((160,145),Image.Resampling.LANCZOS)
        focused.paste(ref,(x+(160-ref.width)//2,110))
        for y,face in ((385,old_font),(580,font(115))):
            d.line((x,y,x+160,y),fill='#dcdfe3')
            d.text((x,y),c,font=face,fill='#243f61',anchor='ls')
    focused.save(PROOFS/'quanfangwei-hiragana-master-v2-na-row.png')
    samples=('なに','なの','こんにちは','ねこ','ぬの','この','もの','なのに','あなた','おねがい','にゃ','にゅ','にょ')
    proof=Image.new('RGB',(1800,1200),'white');d=ImageDraw.Draw(proof)
    heading(d,'Na-row text and yoon / complete Master v2','24 / 48 / 72 px. Natural spacing; each yoon is two glyphs with independent advances.')
    for i,phrase in enumerate(samples):
        y=150+i*80
        for x,size in ((40,24),(530,48),(1110,72)):
            d.line((x,y,x+570,y),fill='#e8e9eb')
            d.text((x,y),phrase,font=font(size),fill='#151922',anchor='ls')
    proof.save(PROOFS/'quanfangwei-hiragana-master-v2-na-text.png')

if __name__=='__main__':main()
