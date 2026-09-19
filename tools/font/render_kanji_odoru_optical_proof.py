#!/usr/bin/env python3
"""HarfBuzz/FreeType before/candidate/final proof, plus actual ink guides."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import tempfile

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from measure_kanji_odoru_optical import (
    ROOT, BASE_MAIN, TTF, SOURCE, REPORT, PROOF, TEXTS, baseline_bytes,
    metrics, candidates, candidate_font, transform_for, measure_groups,
)
from render_de_dakuten_clearance_proof import ShapedFont
from measure_de_dakuten_clearance import segments

BACKGROUND = '#fffdf9'
INK = '#211b28'
MUTED = '#736c76'
label = lambda size: ImageFont.load_default(size=size)


def rows(versions, size):
    # Each column uses actual pixel sizes, with no image rescaling.
    width = 800
    step = size+22
    height = 98+len(TEXTS)*step
    image = Image.new('RGB',(width*len(versions),height),BACKGROUND)
    draw = ImageDraw.Draw(image)
    for i,(caption,shaped) in enumerate(versions):
        x = i*width+22
        draw.text((x,14),f'{size}px | {caption}',font=label(23),fill=INK)
        for j,text in enumerate(TEXTS):
            baseline = 85+j*step
            draw.line((x,baseline,x+width-44,baseline),fill='#e8e2e8')
            shaped.draw(draw,x,baseline,text,size,INK)
    return image


def diagnostic(old,new):
    image=Image.new('RGB',(1600,860),BACKGROUND);draw=ImageDraw.Draw(image)
    han=measure_groups(old)['han']
    for i,(font,caption,color) in enumerate(((old,'BEFORE','#a7627e'),(new,'FINAL','#246c9c'))):
        ox,oy=50+i*790,700;scale=.72
        xy=lambda p:(ox+p[0]*scale,oy-p[1]*scale)
        m=metrics(font);box=m['bounds']
        draw.text((ox,18),caption+' - original 826-unit advance cell',font=label(23),fill=INK)
        draw.rectangle((*xy((0,819)),*xy((826,-205))),outline='#c3bec9',width=2)
        for y,title in ((0,'baseline'),(han['yMin'],'Han bottom -14'),(han['yMax'],'Han top 701.818')):
            draw.line((*xy((0,y)),*xy((826,y))),fill='#729682',width=2)
            draw.text(xy((830,y)),title,font=label(13),fill='#477961')
        for other,c in ((metrics(old),'#dca6b9'),(metrics(new),'#96bdd8')):
            b=other['bounds'];draw.rectangle((*xy((b[0],b[3])),*xy((b[2],b[1]))),outline=c,width=2)
        for a,b in segments(font,m['glyph']):
            draw.line((*xy(a),*xy(b)),fill=color,width=2)
        x,y=xy(m['center']);draw.line((x-8,y,x+8,y),fill=INK,width=2);draw.line((x,y-8,x,y+8),fill=INK,width=2)
        draw.text((ox,780),f'Ink center: {m["center"][0]:.3f}, {m["center"][1]:.3f}',font=label(19),fill=INK)
        draw.text((ox,811),f'LSB / RSB: {m["lsb"]} / {m["rsb"]}; width / height: {m["width"]:.3f} / {m["height"]:.3f}',font=label(18),fill=MUTED)
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates-only',action='store_true')
    args=parser.parse_args()
    with TTFont(BytesIO(baseline_bytes())) as old, tempfile.TemporaryDirectory(prefix='qfw-odoru-proof-') as temp:
        temp=Path(temp);old_path=temp/'before.ttf';old_path.write_bytes(baseline_bytes())
        calculated,scales=candidates(old)
        versions=[('BEFORE 1.000000',ShapedFont(old_path,temp))];candidate_metrics={}
        for scale in scales:
            font=candidate_font(scale);path=temp/f'candidate-{scale:.6f}.ttf';font.save(path)
            candidate_metrics[str(scale)]={'transform':vars(transform_for(old,scale)),**metrics(font)}
            versions.append((f'CANDIDATE {scale:.6f}',ShapedFont(path,temp)))
            font.close()
        if not args.candidates_only:
            from japanese.user_japanese_overrides import SHARED_HAN_OPTICAL_TRANSFORMS
            selected=SHARED_HAN_OPTICAL_TRANSFORMS['踊']
            versions.append((f'FINAL {selected.scale_x:.6f}',ShapedFont(TTF,temp)))
        panels=[rows(versions,size) for size in (20,32,64)]
        # Separate full-resolution inspection strips; not canonical artifacts.
        for size,panel in zip((20,32,64),panels):
            panel.save(f'/private/tmp/qfw-odoru-{size}.png')
        large=Image.new('RGB',(800*len(versions),280),BACKGROUND);draw=ImageDraw.Draw(large)
        for i,(caption,shaped) in enumerate(versions):
            draw.text((i*800+22,10),'192px | '+caption,font=label(23),fill=INK)
            shaped.draw(draw,i*800+220,250,'踊',192,INK)
        panels.append(large)
        if not args.candidates_only:
            with TTFont(TTF) as new,TTFont(SOURCE) as source:
                panels.append(diagnostic(old,new))
                result=dict(base_main=BASE_MAIN,version='1.028',source=metrics(source),before=metrics(old),after=metrics(new),
                            han=measure_groups(old)['han'],calculated_scale=calculated,candidates=candidate_metrics,
                            selected_transform=vars(selected),comparators={c:metrics(old,c) for c in dict.fromkeys('足跳躍踏路俯就算低著頭也起舞漢字日本音楽')})
                for key in ('before','after'):
                    m=result[key];han=result['han']
                    m['han_height_ratio']=m['height']/han['height']
                    m['han_area_ratio']=m['height']*m['width']/(han['height']*han['width'])
                REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        image=Image.new('RGB',(max(p.width for p in panels),95+sum(p.height for p in panels)),BACKGROUND)
        draw=ImageDraw.Draw(image)
        draw.text((22,14),'QuanFangwei 1.028 | U+8E0A optical size | original drawing, uniform scale, fixed advance',font=label(29),fill=INK)
        draw.text((22,57),f'Han height 713 / old height 590 = {calculated:.9f}; 20 / 32 / 64 / 192px; HarfBuzz + FreeType',font=label(22),fill=MUTED)
        y=95
        for panel in panels:
            image.paste(panel,(0,y));y+=panel.height
        target=Path('/private/tmp/qfw-odoru-candidates.png') if args.candidates_only else PROOF
        image.save(target,optimize=True)
        print(json.dumps({'proof':str(target),'calculated':calculated,'candidates':candidate_metrics},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
