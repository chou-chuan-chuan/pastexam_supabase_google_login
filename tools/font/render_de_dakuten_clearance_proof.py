#!/usr/bin/env python3
"""Before/candidate/after proof of the scoped て dakuten clearance."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import tempfile

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from PIL import Image, ImageDraw, ImageFont
import uharfbuzz as hb

from measure_de_dakuten_clearance import (
    ROOT, FONT_REL, BASE_MAIN, OLD_OFFSET, baseline_bytes, measure,
    candidate_font, offset_delta, segments,
)

PROOFS = ROOT/'tools/font/proofs'
REPORT = ROOT/'tools/font/reports/de-dakuten-clearance.json'
TARGET_GAP = 1024/20  # one nominal pixel at the smallest requested lyric size


class ShapedFont:
    """Use HarfBuzz GPOS even on Pillow builds without libraqm.

    A proof-only PUA cmap addresses individual glyph IDs for FreeType drawing.
    Original font bytes do the shaping; production files are never rewritten.
    Decomposed TE is forced through GPOS rather than silently recomposed.
    """
    def __init__(self, path, temp):
        raw = Path(path).read_bytes()
        self.normal = hb.Font(hb.Face(raw)); self.normal.scale = (1024,1024)
        font = TTFont(BytesIO(raw),recalcTimestamp=False)
        for table in font['cmap'].tables:
            if table.isUnicode() and hasattr(table,'cmap'):
                table.cmap.pop(0x3067,None)
        stream=BytesIO(); font.save(stream)
        self.decomposed=hb.Font(hb.Face(stream.getvalue()));self.decomposed.scale=(1024,1024)
        table=CmapSubtable.newSubtable(12);table.platformID=3;table.platEncID=10;table.language=0
        table.cmap={0xF0000+i:name for i,name in enumerate(font.getGlyphOrder())}
        font['cmap'].tables=[table]
        self.path=Path(temp)/f'{Path(path).stem}-glyphs.ttf';font.save(self.path)
        self.sizes={}

    def draw(self, draw, x, baseline, text, size, fill):
        if size not in self.sizes:
            self.sizes[size]=ImageFont.truetype(str(self.path),size)
        pieces=text.split('で')
        fragments=[]
        for i,piece in enumerate(pieces):
            if i:
                fragments.append(('で',self.decomposed))
            fragments.append((piece,self.normal))
        for fragment,font in fragments:
            if not fragment:
                continue
            buffer=hb.Buffer();buffer.add_str(fragment);buffer.guess_segment_properties()
            hb.shape(font,buffer,{'ccmp':True,'mark':True})
            for info,pos in zip(buffer.glyph_infos,buffer.glyph_positions):
                draw.text((x+pos.x_offset*size/1024,baseline-pos.y_offset*size/1024),
                          chr(0xF0000+info.codepoint),font=self.sizes[size],anchor='ls',fill=fill)
                x+=pos.x_advance*size/1024
        return x


def minimum_offset(font):
    for offset in range(OLD_OFFSET,151):
        metric = measure(font,extra_y=offset_delta(offset))
        if metric['minimum_clearance'] >= TARGET_GAP:
            return offset
    raise AssertionError('No compact local candidate meets the 20 px gap target')


def render_rows(versions,path):
    sizes = (20,32,64,192)
    lines = ('て　で　で', 'け げ　せ ぜ　て で　と ど　へ べ')
    width = 3800
    height = 115 + sum(65+len(lines)*len(versions)*(size+45) for size in sizes)
    image = Image.new('RGB',(width,height),'#fffdf9'); draw = ImageDraw.Draw(image)
    label = lambda size: ImageFont.load_default(size=size)
    draw.text((24,18),'Version 1.027 - scoped て / で dakuten clearance'.replace('て / で','TE / DE'),font=label(30),fill='#211b28')
    draw.text((24,65),'HarfBuzz + FreeType; forced GPOS for decomposed TE. Only the TE base anchor changes.',font=label(21),fill='#736c76')
    y = 115
    for size in sizes:
        draw.text((24,y),f'{size}px - precomposed / decomposed and neighboring dakuten bases',font=label(22),fill='#211b28');y+=65
        for text in lines:
            for caption,shaped_font in versions:
                baseline = y+size
                draw.text((24,baseline-size*.65),caption,font=label(20),fill='#813b56')
                draw.line((250,baseline,width-25,baseline),fill='#e2dce3')
                shaped_font.draw(draw,260,baseline,text,size,'#211b28')
                y+=size+45
    image.save(path,optimize=True)


def diagnostic(old,new):
    image = Image.new('RGB',(1800,840),'#fffdf9');draw = ImageDraw.Draw(image)
    label = lambda size: ImageFont.load_default(size=size)
    draw.text((28,18),'Final ink geometry - base (black), dakuten (blue), closest gap (red)',font=label(26),fill='#211b28')
    for i,(font,title) in enumerate(((old,'Before'),(new,'After'))):
        m = measure(font); ox,oy = 35+i*890,735; scale=.88
        xy = lambda p:(ox+p[0]*scale,oy-p[1]*scale)
        draw.text((ox,70),f'{title}: minimum diagonal gap {m["minimum_clearance"]:.3f} units',font=label(22),fill='#211b28')
        for name,delta,color in [('uni3066',(0,0),'#211b28'),('uni3099',m['mark_delta'],'#3382bd')]:
            for a,b in segments(font,name,delta):
                draw.line((*xy(a),*xy(b)),fill=color,width=2)
        draw.line((*xy(m['closest_base_point']),*xy(m['closest_mark_point'])),fill='#cb3c52',width=3)
        for key in ('closest_base_point','closest_mark_point'):
            x,y=xy(m[key]);draw.ellipse((x-4,y-4,x+4,y+4),fill='#cb3c52')
        v=m['minimum_vertical_gap']
        draw.text((ox,778),f'Local vertical gap {v[0]:.3f}; base top at x={v[1]:.3f}: y={v[2]:.3f}',font=label(18),fill='#736c76')
    image.save(PROOFS/'quanfangwei-de-dakuten-clearance-geometry.png',optimize=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates-only',action='store_true')
    args=parser.parse_args()
    raw=baseline_bytes()
    with TTFont(BytesIO(raw)) as old, tempfile.TemporaryDirectory(prefix='qfw-de-proof-') as temp:
        chosen=minimum_offset(old); offsets=(chosen-10,chosen,chosen+10)
        old_path=Path(temp)/'old.ttf';old_path.write_bytes(raw)
        old_shaped=ShapedFont(old_path,temp)
        versions=[('+17 old',old_shaped)];candidates={}
        for offset in offsets:
            font=candidate_font(offset);path=Path(temp)/f'{offset}.ttf';font.save(path)
            candidates[str(offset)]={'extra_rendered_y':offset_delta(offset),**measure(font)}
            versions.append((f'+{offset}',ShapedFont(path,temp)))
        render_rows(versions,PROOFS/'quanfangwei-de-dakuten-clearance-candidates.png')
        if not args.candidates_only:
            from japanese.build_kana import HIRAGANA_MARK_ANCHOR_Y_OFFSETS
            assert HIRAGANA_MARK_ANCHOR_Y_OFFSETS['て']==chosen
            with TTFont(ROOT/FONT_REL) as new:
                render_rows([('Before +17',old_shaped),(f'After +{chosen}',ShapedFont(ROOT/FONT_REL,temp))],PROOFS/'quanfangwei-de-dakuten-clearance.png')
                diagnostic(old,new)
                result={'base_main':BASE_MAIN,'version':'1.027','old_offset':OLD_OFFSET,'new_offset':chosen,
                        'additional_source_offset':chosen-OLD_OFFSET,'additional_rendered_y':offset_delta(chosen),
                        'target_gap':TARGET_GAP,'before':measure(old),'after':measure(new),
                        'previous_candidate':{'offset':chosen-1,**measure(old,extra_y=offset_delta(chosen-1))},
                        'candidates':candidates,'neighbors':{c:measure(new,c) for c in 'けせとへ'}}
                REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'minimum_offset':chosen,'target_gap':TARGET_GAP,'candidates':candidates},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
