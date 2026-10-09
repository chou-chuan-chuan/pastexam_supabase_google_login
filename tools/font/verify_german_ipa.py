#!/usr/bin/env python3
"""Verify both release formats, actual shaping and complete 1.036 preservation.

Requires the pinned baseline commit (CI checks out full history). --baseline
allows an already verified local TTF; its SHA is always checked.
"""
import argparse
import copy
import hashlib
from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import subprocess

from fontTools.ttLib import TTFont
import uharfbuzz as hb
from german_ipa import BASIC_IPA, BASES, MARKS, MARK_GAP, bounds, name

ROOT = Path(__file__).resolve().parents[2]
REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
BASE_COMMIT = 'def988885120a7921c940073ee1bd2454ecdeb92'
BASE_SHA = '77f3b2578241b14901e588b5a5b8b18f2550e1d194fad9ea9a0af136da32b103'
PREVIOUS_COMMIT = '7e8cb8730b4ca0d514aaba6a86fd97f912156921'
PREVIOUS_SHA = 'a480615b68e8a8d773497e9c75b320e395753290b1fb80b23582ba7d50559e04'
CONTEXTS = ['n̩','l̩','m̩','i̯','ɐ̯','aɪ̯','ˈʃpʁaːxə','ˈmʏtɐ','øːl',
            'ˈbɪtə','ˈzɔmɐ','ʔaɪ̯','ŋ','gɡ',':ː','中文 あいう マスズ ぱぴぷぺぽ ÄÖÜ äöü ßẞ œ ç']


@lru_cache(maxsize=8)
def harfbuzz_font(font):
    raw = BytesIO()
    font.flavor = None
    font.save(raw)
    hf = hb.Font(hb.Face(raw.getvalue()))
    hf.scale = (font['head'].unitsPerEm,)*2
    return hf


def shape(font, text, features=None):
    hf = harfbuzz_font(font)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hf, buf, features or {})
    return [(i.codepoint, i.cluster, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for i,p in zip(buf.glyph_infos,buf.glyph_positions)]


def preservation(old, new):
    assert new.getGlyphOrder()[:len(old.getGlyphOrder())] == old.getGlyphOrder()
    assert set(new.getGlyphOrder())-set(old.getGlyphOrder()) == {name(c) for c in BASIC_IPA}
    assert all(new.getBestCmap().get(cp)==g for cp,g in old.getBestCmap().items())
    assert set(new.getBestCmap())-set(old.getBestCmap()) == {ord(c) for c in BASIC_IPA}
    for g in old.getGlyphOrder():
        assert old['glyf'][g].compile(old['glyf']) == new['glyf'][g].compile(new['glyf']), ('outline',g)
        assert old['hmtx'][g] == new['hmtx'][g], ('advance/lsb',g)
        if 'vmtx' in old:
            assert old['vmtx'][g] == new['vmtx'][g], ('vertical metrics',g)
    # Remove only the explicitly added lookup/classes and demand byte-identical
    # original layout, including script/language activation and feature order.
    gpos = copy.deepcopy(new['GPOS'])
    assert gpos.table.LookupList.LookupCount == old['GPOS'].table.LookupList.LookupCount+1
    idx = gpos.table.LookupList.LookupCount-1
    gpos.table.LookupList.Lookup.pop()
    gpos.table.LookupList.LookupCount -= 1
    for rec in gpos.table.FeatureList.FeatureRecord:
        if rec.FeatureTag == 'mark':
            assert rec.Feature.LookupListIndex[-1] == idx
            rec.Feature.LookupListIndex.pop()
            rec.Feature.LookupCount -= 1
    assert gpos.compile(new) == old['GPOS'].compile(old), 'Existing GPOS changed'
    gdef = copy.deepcopy(new['GDEF'])
    for c in BASIC_IPA:
        del gdef.table.GlyphClassDef.classDefs[name(c)]
    assert gdef.compile(new) == old['GDEF'].compile(old), 'Existing GDEF changed'
    for tag in ['GSUB','MATH','kern']:
        if tag in old:
            assert old[tag].compile(old) == new[tag].compile(new), tag
    for tag, count in [('vhea','numberOfVMetrics'),('hhea','numberOfHMetrics')]:
        if tag in old:
            header=copy.deepcopy(new[tag])
            setattr(header,count,getattr(old[tag],count))
            assert header.compile(new)==old[tag].compile(old),tag
    for field in ['sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent','fsType']:
        assert getattr(old['OS/2'],field) == getattr(new['OS/2'],field),field
    for text in ['Ç ç ÄÖÜ äöü ÄÖÜ äöü','ぱぴぷぺぽ ぱぴぷぺぽ マスズ','ど ど パ パ','∑ ∇ ∏ x̂ p̂ ℏ 中文']:
        assert shape(old,text)==shape(new,text), ('existing shaping',text)


def weight_revision(previous, current):
    # A cosmetic revision must not silently alter layout or accepted size.
    expected = {name(c) for c in 'ɛɪɔʊʏøəɐʒʁʔ\u032f\u0329'}
    assert previous.getGlyphOrder() == current.getGlyphOrder()
    changed = set()
    for g in previous.getGlyphOrder():
        if previous['glyf'][g].compile(previous['glyf']) != current['glyf'][g].compile(current['glyf']):
            changed.add(g)
            assert bounds(previous,g) == bounds(current,g), (g,'approved size changed')
            assert previous['glyf'][g].numberOfContours == current['glyf'][g].numberOfContours
    assert changed == expected, ('unexpected outline changes', changed ^ expected)
    for tag in ['cmap','hmtx','vmtx','hhea','vhea','GPOS','GDEF','GSUB','MATH']:
        assert previous[tag].compile(previous) == current[tag].compile(current), tag
    for text in CONTEXTS:
        assert shape(previous,text) == shape(current,text), ('layout regression',text)
    return {'previous_commit':PREVIOUS_COMMIT,'previous_sha256':PREVIOUS_SHA,
            'changed_outlines':13,'preserved_outlines':len(current.getGlyphOrder())-13,
            'all_ink_bounds_and_layout_preserved':True}


def verify(font, old):
    preservation(old,font)
    tables = [t for t in font['cmap'].tables if t.isUnicode() and t.format in (4,12)]
    assert {t.format for t in tables} == {4,12}
    for t in tables:
        for c in BASIC_IPA:
            assert t.cmap.get(ord(c))==name(c) and font.getGlyphID(name(c))>0,(t.format,c)
    assert font['head'].unitsPerEm == old['head'].unitsPerEm
    assert abs(font['head'].fontRevision-1.038)<.0001
    assert font['name'].getDebugName(5)=='Version 1.038'
    for nid in [0,13,14]:
        assert font['name'].getDebugName(nid)==old['name'].getDebugName(nid),('license',nid)
    for c in BASIC_IPA:
        g=name(c);b=bounds(font,g)
        assert b[0]<b[2] and b[1]<b[3]
        assert font['hhea'].descent<=b[1]<b[3]<=font['hhea'].ascent,(c,b)
        assert font['hmtx'][g][0] == 0 if c in MARKS else font['hmtx'][g][0]>0
    for c,reference in [('ə','e'),('ɐ','a')]:
        b=bounds(font,name(c)); ref=bounds(old,old.getBestCmap()[ord(reference)])
        assert .88 <= (b[3]-b[1])/(ref[3]-ref[1]) <= .96, (c,'oversized bowl')
        assert b[1]==110 and font['hmtx'][name(c)][0]<=310, (c,'optical size/spacing')
    for c,count in {'ʊ':1,'ʃ':1,'ŋ':1,'ʁ':2,'ʔ':1,'ː':2}.items():
        assert font['glyf'][name(c)].numberOfContours==count, (c,'disconnected stroke or lost counter')
    for c in BASES:
        for mark in MARKS:
            text=c+mark; s=shape(font,text)
            assert len(s)==2 and all(v[0]>0 for v in s),(text,s)
            b,m=s;assert m[2:4]==(0,0),(text,'mark advance')
            assert b[2]==shape(font,c)[0][2],(text,'base advance')
            bb=bounds(font,font.getGlyphName(b[0]));mb=bounds(font,font.getGlyphName(m[0]))
            mx=b[2]+m[4];my=m[5]
            assert abs(mx+(mb[0]+mb[2])/2-(bb[0]+bb[2])/2)<=3,(text,'centering')
            assert bb[1]-(my+mb[3]) == MARK_GAP,(text,'vertical gap')
            assert my+mb[1]>=font['hhea'].descent,(text,'clipping')
    for text in CONTEXTS:
        assert all(v[0]>0 for v in shape(font,text)),('missing shaped glyph',text)
    # The diphthong mark attaches to the second letter, not the first.
    s=shape(font,'aɪ̯');assert s[2][4:]==shape(font,'ɪ̯')[1][4:]
    assert shape(font,'n̩')!=shape(font,'n̩',{'mark':False}), 'GPOS not activated'
    assert font.getBestCmap()[ord('g')]!=font.getBestCmap()[ord('ɡ')]
    assert font.getBestCmap()[ord(':')]!=font.getBestCmap()[ord('ː')]
    assert bounds(font,font.getBestCmap()[ord(':')])!=bounds(font,name('ː'))
    return {'unicode_cmap_tables':[(t.platformID,t.platEncID,t.format) for t in tables],
            'basic_additions':19, 'base_mark_pairs':len(BASES)*len(MARKS),
            'preserved_glyphs':len(old.getGlyphOrder()),'contexts':CONTEXTS,
            'compact_vowels':{c:{'bounds':bounds(font,name(c)),'advance':font['hmtx'][name(c)][0]} for c in 'əɐ'}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path)
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    raw=args.baseline.read_bytes() if args.baseline else subprocess.check_output(['git','show',f'{BASE_COMMIT}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    audit=json.loads((ROOT/'tools/font/reports/german-ipa-baseline.json').read_text())
    assert len(audit['rows'])==93 and audit['sha256']==BASE_SHA
    baseline=TTFont(BytesIO(raw)); cmap=baseline.getBestCmap()
    for row in audit['rows']:
        cp=int(row['unicode'][2:],16)
        present=cp in cmap and baseline.getGlyphID(cmap[cp])>0
        assert present==row['present'], ('supplied audit mismatch',row['unicode'])
    core={int(row['unicode'][2:],16) for row in audit['rows'] if row['group'].startswith('基礎') and not row['present']}
    assert len(core)==19 and core=={ord(c) for c in BASIC_IPA}
    previous_raw=subprocess.check_output(['git','show',f'{PREVIOUS_COMMIT}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(previous_raw).hexdigest()==PREVIOUS_SHA
    result={'baseline_commit':BASE_COMMIT,'baseline_sha256':BASE_SHA,'formats':{}}
    for extension in ['.ttf','.woff2']:
        path=(ROOT/REL).with_suffix(extension)
        result['formats'][extension]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                     **verify(TTFont(path),TTFont(BytesIO(raw))),
                                     'weight_revision':weight_revision(TTFont(BytesIO(previous_raw)),TTFont(path))}
    if args.output:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('PASS: 19 IPA additions, cmap 4/12, HarfBuzz attachments, complete baseline preservation')


if __name__=='__main__':
    main()
