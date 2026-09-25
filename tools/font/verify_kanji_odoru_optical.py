#!/usr/bin/env python3
"""Verify the sole 1.028 glyph extension against immutable complete 1.027.

Default execution also rebuilds the canonical TTF/WOFF2 byte-for-byte.
Historical verifiers use the narrowly defined independent Han extension below;
their original kana/source/mark assertions otherwise remain in force.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
import subprocess
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from verify_french_guillemets import historical_cmap, historical_order
import uharfbuzz as hb

from measure_kanji_odoru_optical import (
    ROOT, BASE_MAIN, TTF, WOFF2, SOURCE, SOURCE_SHA256, SOURCE_NAME,
    DERIVED_NAME, REPORT, TEXTS, baseline_bytes, metrics, candidates, measure_groups,
)
from japanese.user_japanese_overrides import SHARED_HAN_OPTICAL_TRANSFORMS
from japanese.build_kana import DO_BASE_GLYPH

SCALE = 1.208475
EXPECTED_TRANSFORM = (SCALE,SCALE,-43/6,-17.499875,0.0,None)
EXPECTED_BOUNDS = (28.875,-14,797.3913043478261,699)
OVERRIDE_BLOCK = '''    # Version 1.028: 713/590 measured Han-height fit; fixed 826 advance.
    # Ink-center scale, centered X, Han median bottom -14, no embolden.
    "踊": SourceOpticalTransform(1.208475, 1.208475, -43/6, -17.499875),
'''


def signature(font,name):
    glyph=font['glyf'][name]
    coordinates,ends,flags=glyph.getCoordinates(font['glyf'])
    components=tuple(c.getComponentInfo() for c in glyph.components) if glyph.isComposite() else ()
    return glyph.numberOfContours,tuple(coordinates),tuple(ends),bytes(flags),components,font['hmtx'][name]


def without_odoru_source(raw):
    block=OVERRIDE_BLOCK.encode()
    assert raw.count(block)==1,'Only the exact reviewed 踊 source entry is permitted'
    return raw.replace(block,b'')


def verify_transform_record():
    assert tuple(vars(SHARED_HAN_OPTICAL_TRANSFORMS['踊']).values()) == EXPECTED_TRANSFORM


def expected_glyph(font):
    # Independent oracle: the source ink center is (2521/6,360). After
    # scaling it moves to (413,342.500125), with theoretical bottom -14.
    # TTGlyphPen applies the project's integer rounding to each source point.
    verify_transform_record()
    matrix=Transform(SCALE,0,0,SCALE,413-SCALE*(2521/6),-14-SCALE*65)
    pen=TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()[SOURCE_NAME].draw(TransformPen(pen,matrix))
    glyph=pen.glyph();glyph.recalcBounds(font['glyf'])
    return glyph


def extend_historical_han_oracle(font):
    """Add only the pinned 1.028 extension to an older regression oracle.

    This never reads new output geometry. Original glyphs and all historical
    kana expectations remain unchanged. Order matches the existing builder:
    scoped optical copies precede the older 気/付 alignment copies.
    """
    assert DERIVED_NAME not in font.getGlyphOrder()
    assert font.getBestCmap()[0x8E0A] == SOURCE_NAME
    glyph=expected_glyph(font)
    order=font.getGlyphOrder();order.insert(order.index('uni6C17.qfwJaAlign'),DERIVED_NAME)
    font.setGlyphOrder(order);font['glyf'][DERIVED_NAME]=glyph
    font['hmtx'][DERIVED_NAME]=(826,glyph.xMin)
    if 'vmtx' in font:
        font['vmtx'][DERIVED_NAME]=font['vmtx'][SOURCE_NAME]
    font['maxp'].numGlyphs=len(order)
    font['hhea'].numberOfHMetrics+=1
    for table in font['cmap'].tables:
        if table.isUnicode() and table.format!=14:
            table.cmap[0x8E0A]=DERIVED_NAME


def verify_source_scope():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA256
    roots=['tools/font/kana_sources','tools/font/references','tools/font/japanese']
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE_MAIN,'--',*roots],cwd=ROOT,text=True).splitlines()
    for path in paths:
        if path.endswith('japanese/build_kana.py'):
            # Version 1.030's independently verified と/ど refinement lives here.
            continue
        old=subprocess.check_output(['git','show',f'{BASE_MAIN}:{path}'],cwd=ROOT)
        new=(ROOT/path).read_bytes().replace(b'\r\n',b'\n') if path.endswith(('.py','.json','.md','.svg','.txt','.csv')) else (ROOT/path).read_bytes()
        if path.endswith('japanese/user_japanese_overrides.py'):
            new=without_odoru_source(new)
        assert new==old,('Frozen source changed',path)
    print(f'PASS: {len(paths)} source/reference files pinned; original font SHA256; only exact 踊 transform entry added; no external outline input')


def shaped_bounds(font,text,face):
    buffer=hb.Buffer();buffer.add_str(text);buffer.guess_segment_properties();hb.shape(face,buffer)
    from japanese.user_japanese_overrides import glyph_bounds
    cursor=0;boxes=[]
    for info,pos in zip(buffer.glyph_infos,buffer.glyph_positions):
        name=font.getGlyphName(info.codepoint)
        assert name!='.notdef',text
        if name!='space':
            b=glyph_bounds(font,name)
            boxes.append((name,(cursor+pos.x_offset+b[0],b[1]+pos.y_offset,cursor+pos.x_offset+b[2],b[3]+pos.y_offset)))
        cursor+=pos.x_advance
    return boxes,cursor


def verify():
    verify_source_scope();verify_transform_record()
    with TTFont(BytesIO(baseline_bytes())) as old,TTFont(SOURCE) as source,TTFont(TTF) as new,TTFont(WOFF2) as web:
        assert old['name'].getDebugName(5)=='Version 1.027'
        assert old.getBestCmap()[0x8E0A]==source.getBestCmap()[0x8E0A]==SOURCE_NAME
        from verify_japanese_optical_alignment import drawing
        assert drawing(source,SOURCE_NAME)==drawing(old,SOURCE_NAME)==drawing(new,SOURCE_NAME)
        expected_order=old.getGlyphOrder().copy()
        expected_order.insert(expected_order.index('uni6C17.qfwJaAlign'),DERIVED_NAME)
        expected_order.insert(expected_order.index('uni304C'),DO_BASE_GLYPH)
        assert historical_order(new)==historical_order(web)==expected_order
        expected_cmap=old.getBestCmap().copy();expected_cmap[0x8E0A]=DERIVED_NAME
        assert historical_cmap(new)==historical_cmap(web)==expected_cmap
        for font in (new,web):
            assert all(t.cmap[0x8E0A]==DERIVED_NAME for t in font['cmap'].tables if t.isUnicode() and t.format!=14)
            actual=font['glyf'][DERIVED_NAME]
            assert actual.compile(font['glyf'])==expected_glyph(source).compile(source['glyf'])
            m=metrics(font)
            assert tuple(m['bounds'])==EXPECTED_BOUNDS,m
            assert m['advance']==old['hmtx'][SOURCE_NAME][0]==826
            assert (m['lsb'],m['rsb'])==(27,26)
            assert min(m['ink_sidebearings'])>=28 and abs(m['center'][0]-413)<.5
            assert max(font['hhea'].descent,font['OS/2'].sTypoDescender,-font['OS/2'].usWinDescent)<m['bounds'][1]
            assert m['bounds'][3]<min(font['hhea'].ascent,font['OS/2'].sTypoAscender,font['OS/2'].usWinAscent)
            assert font['name'].getDebugName(5)=='Version 1.031'
            assert abs(font['head'].fontRevision-1.031)<1/65536
            assert font['head'].unitsPerEm==old['head'].unitsPerEm==1024
        hashes=[]
        for name in old.getGlyphOrder():
            value=signature(old,name)
            if name not in {'uni3068','uni3069'}:
                assert value==signature(new,name)==signature(web,name),('Existing glyph changed',name)
            if 'vmtx' in old:
                assert old['vmtx'][name]==new['vmtx'][name]==web['vmtx'][name]
            if name not in {'uni3068','uni3069'}:
                hashes.append((name,hashlib.sha256(repr(value).encode()).hexdigest()))
        assert signature(new,DERIVED_NAME)==signature(web,DERIVED_NAME)
        assert signature(new,DO_BASE_GLYPH)==signature(web,DO_BASE_GLYPH)
        han={name for cp,name in old.getBestCmap().items() if cp!=0x8E0A and (0x3400<=cp<=0x9fff or 0xf900<=cp<=0xfaff or 0x20000<=cp<=0x323af)}
        from render_kana_bottom_alignment_proof import MOVED_NAMES
        summary={}
        for group,names in [('unrelated_han',han),('kana',MOVED_NAMES),('all_existing',set(old.getGlyphOrder()))]:
            selected=[item for item in hashes if item[0] in names]
            summary[group]={'count':len(selected),'sha256':hashlib.sha256(repr(selected).encode()).hexdigest()}
        assert summary['unrelated_han']['count']==9343 and summary['kana']['count']==185
        # Global metrics stay fixed. The existing Han copy and voiced helper
        # add two entries; the appended guillemets share one final advance.
        assert old['OS/2'].compile(old)==new['OS/2'].compile(new)==web['OS/2'].compile(web)
        for tag in ('GSUB','GPOS','GDEF'):
            assert new[tag].compile(new)==web[tag].compile(web),tag
        old['hhea'].numberOfHMetrics+=3
        assert old['hhea'].compile(old)==new['hhea'].compile(new)==web['hhea'].compile(web)
        assert new['name'].compile(new)==web['name'].compile(web)
        for record in old['name'].names:
            new_record=new['name'].getName(record.nameID,record.platformID,record.platEncID,record.langID)
            expected=record.toUnicode()
            if record.nameID == 3:
                parts=expected.split(';');parts[0]='1.031';parts[-1]='20260925';expected=';'.join(parts)
            elif record.nameID == 5:
                expected=expected.replace('1.027','1.031')
            assert new_record.toUnicode()==expected,('Name drift',record.nameID)
        gaps={}
        old_shaper=hb.Font(hb.Face(baseline_bytes()))
        new_shaper=hb.Font(hb.Face(TTF.read_bytes()))
        old_shaper.scale=new_shaper.scale=(1024,1024)
        for text in TEXTS:
            boxes,advance=shaped_bounds(new,text,new_shaper)
            assert advance==shaped_bounds(old,text,old_shaper)[1],('Text layout width changed',text)
            pair_gaps=[right[1][0]-left[1][2] for left,right in zip(boxes,boxes[1:]) if DERIVED_NAME in (left[0],right[0])]
            assert all(g>0 for g in pair_gaps),('Adjacent ink collision',text,pair_gaps)
            if pair_gaps:gaps[text]=pair_gaps
        report=json.loads(REPORT.read_text())
        assert report['base_main']==BASE_MAIN and report['version']=='1.028'
        for key,font in [('before',old),('after',new)]:
            assert {k:report[key][k] for k in metrics(font)}==metrics(font)
        assert report['han']==measure_groups(old)['han']==measure_groups(new)['han']
        calculated,scales=candidates(old)
        assert report['calculated_scale']==calculated and tuple(map(float,report['candidates']))==scales
        assert report['selected_transform']==vars(SHARED_HAN_OPTICAL_TRANSFORMS['踊'])
        print('PASS: original drawing -> uniform derived copy; exact rounded bounds, unchanged 826 advance, positive bearings, no clipping/embolden')
        print('PASS: TTF/WOFF2 parity; unchanged global metrics and every non-と/ど existing outline/metric; 1.030 layout scope is delegated to its focused verifier')
        print('PASS: immutable hashes '+json.dumps(summary,ensure_ascii=False))
        print('PASS: shaped lyric advance unchanged; adjacent ink gaps '+json.dumps(gaps,ensure_ascii=False))
        return summary,gaps


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-rebuild',action='store_true')
    args=parser.parse_args();verify()
    if not args.skip_rebuild:
        from verify_kana_kanji_scale_balance import verify_determinism
        verify_determinism()


if __name__=='__main__':
    main()
