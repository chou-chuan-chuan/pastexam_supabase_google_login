#!/usr/bin/env python3
"""Actual-font master-sheet fidelity, family, derivative, and lyric-size proofs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt
from render_japanese_weight_proof import LYRICS
from kana_sources.hiragana_master_v2 import MASTER_SOURCES, REFERENCE, ROWS, TARGETS

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
PROOFS = ROOT / 'tools/font/proofs'
REFERENCE_PATH = ROOT / 'tools/font/references' / REFERENCE
BASIC_ROWS = ('あいうえお','かきくけこ','さしすせそ','たちつてと','なにぬねの',
              'はひふへほ','まみむめも','や ゆ よ','らりるれろ','わ を ん')
YOON = tuple(a+b for a in 'きぎしじちにひびぴみり' for b in 'ゃゅょ')
NATURAL = ('ありがとう','おはよう','よろしく','すき','きれい','さようなら','おやすみ',
           'わたし','ひとり','こころ','せかい','ちょっと','もっと','ありがとう、またね。')
VOICED = ('がぎぐげご','ざじずぜぞ','だぢづでど','ばびぶべぼ','ぱぴぷぺぽ','ゔ')

def font(size):
    return ImageFont.truetype(str(FONT), size)


def masks(character, zoom=4):
    source = MASTER_SOURCES[character]
    crop = source.crop
    ref = ImageOps.invert(Image.open(REFERENCE_PATH).convert('L').crop(crop))
    ref = ref.resize((ref.width*zoom, ref.height*zoom), Image.Resampling.LANCZOS)
    current = Image.new('L', ref.size)
    x,y = source.to_source(crop[0], crop[1])
    size = round(1024*zoom/source.scale)
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
    reference = Image.open(REFERENCE_PATH).convert('RGB')
    generated = Image.new('RGB',reference.size,'white')
    diagnostic = Image.new('RGB',(1300,1940),'#faf9f6')
    d = ImageDraw.Draw(diagnostic)
    heading(d,'Master v2: actual TTF / reference overlay',
            'Red = handwriting, blue = production font. Uniform fit only; production pressure differs from raster ink.')
    metrics = {}
    for i,c in enumerate(TARGETS):
        source=MASTER_SOURCES[c]
        # Render each crop independently at 4x, then place back into original sheet.
        ref,new=masks(c)
        candidate=ImageOps.invert(new).convert('RGB')
        candidate=candidate.resize((source.crop[2]-source.crop[0],source.crop[3]-source.crop[1]),Image.Resampling.LANCZOS)
        generated.paste(candidate,source.crop[:2])
        a=np.asarray(ref,dtype=float)/255;b=np.asarray(new,dtype=float)/255
        overlay=Image.fromarray(np.stack([255*(1-b*.85),255*(1-np.maximum(a,b)*.85),255*(1-a*.85)],axis=2).astype('uint8'))
        overlay.thumbnail((225,160),Image.Resampling.LANCZOS)
        px=20+(i%5)*258;py=95+(i//5)*202
        diagnostic.paste(overlay,(px+(225-overlay.width)//2,py))
        d.text((px,py+162),c,font=font(26),fill='#202331')
        metrics[c]=measurements(ref,new)
        d.text((px+38,py+166),f"gap {metrics[c]['mean_ink_distance_photo_px']:.2f}px",font=ImageFont.load_default(size=15),fill='#5b6472')
    generated.save(PROOFS/'quanfangwei-hiragana-master-v2-proof.png')
    paired=Image.new('RGB',(reference.width*2,reference.height+82),'#faf9f6')
    heading(ImageDraw.Draw(paired),'Maintainer master sheet v2: reference / generated font',
            '41 handwritten sources. Intentional empty cells retained. Actual TTF rendered through the family stroke engine.')
    paired.paste(reference,(0,82));paired.paste(generated,(reference.width,82))
    paired.save(PROOFS/'quanfangwei-hiragana-master-v2-comparison.png')
    diagnostic.save(PROOFS/'quanfangwei-hiragana-master-v2-overlay.png')
    (PROOFS/'quanfangwei-hiragana-master-v2-fidelity.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')

    full=Image.new('RGB',(1020,1300),'#faf9f6');d=ImageDraw.Draw(full)
    heading(d,'All 46 basic Hiragana / Version 1.025','Blue: 41 new master sources. Amber: five unchanged na-row sources. Same font and size throughout.')
    for row,chars in enumerate(BASIC_ROWS):
        y=100+row*117
        if row==4:d.rectangle((20,y-4,995,y+106),fill='#fff0d0')
        for col,c in enumerate(chars):
            if c==' ':continue
            x=55+col*185;d.line((x,y+92,x+160,y+92),fill='#dcdfe3')
            d.text((x,y+92),c,font=font(115),fill='#966000' if c in 'なにぬねの' else '#243f61',anchor='ls')
    full.save(PROOFS/'quanfangwei-hiragana-master-v2-full-46.png')

    weight=Image.new('RGB',(1590,1450),'white');d=ImageDraw.Draw(weight)
    heading(d,'Family weight / common baseline / unchanged na-row','Rows at 24, 32, 48 and 72 px. Normal lyric-size comparisons use identical rendering.')
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
    print('Rendered seven master-v2 proofs and fidelity metrics')
    print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':main()
