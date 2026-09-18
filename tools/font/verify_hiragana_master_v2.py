#!/usr/bin/env python3
"""Verify the immutable master-v2 contract, raster fidelity and complete font diff.

Expected hashes are reviewed data, never refreshed by this verifier. The old
font comes from the immutable base commit, so merging this PR cannot silently
move the oracle. Default execution also repeats the canonical build and checks
both output files byte-for-byte. --skip-rebuild is for component checks only.
"""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

from fontTools.ttLib import TTFont
from japanese.stroke_engine import build_stroke_glyph, translate_strokes
from japanese.build_kana import bounds, base_anchor, DAKUTEN_ANCHOR, HANDAKUTEN_ANCHOR
from japanese.user_japanese_overrides import SHARED_HAN_OPTICAL_TRANSFORMS, ALIGNMENT_REFERENCE_BOUNDS
from kana_sources.hiragana_master_v2 import MASTER_SOURCES, TARGETS, ROWS, REFERENCE, REFERENCE_SHA256
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED, MODERN_HIRAGANA_ORDER
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS, OpticalTransform
from kana_sources.full_data import (KANA_STROKES, COMPOSITES, scale, YOON_SMALL_KANA_OFFSETS,
                                    SMALL_HIRAGANA_OPTICAL_SHIFTS)

ROOT=Path(__file__).resolve().parents[2]
BASE_MAIN='d89ee8b2b5f4c858e5dade853972194892037f93'
FONT_REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF=ROOT/FONT_REL
WOFF2=TTF.with_suffix('.woff2')
MANIFEST=ROOT/'tools/font/references/hiragana-master-v2-manifest.json'
PRESERVED='なにぬねの'
SMALL=dict(zip('ぁぃぅぇぉっゃゅょゎゕゖ','あいうえおつやゆよわかけ'))
VOICED='がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゔ'
YOON=tuple(a+b for a in 'きぎしじちにひびぴみり' for b in 'ゃゅょ')
EXPECTED_CHANGED=set(TARGETS+''.join(SMALL)+VOICED)


def digest(value):
    return hashlib.sha256(repr(value).encode('utf-8')).hexdigest()


def signature(font,name):
    g=font['glyf'][name]
    coordinates,ends,flags=g.getCoordinates(font['glyf'])
    components=tuple(c.getComponentInfo() for c in g.components) if g.isComposite() else ()
    return (g.numberOfContours,tuple(coordinates),tuple(ends),bytes(flags),components,font['hmtx'].metrics[name])


def manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def verify_sources(characters=TARGETS):
    m=manifest()
    assert m['base_main']==BASE_MAIN and m['version']=='1.025'
    assert len(TARGETS)==41 and set(MASTER_SOURCES)==set(TARGETS)
    assert list(ROWS)==m['rows'] and set(MODERN_HIRAGANA_ORDER)==set(TARGETS+PRESERVED)
    assert hashlib.sha256((ROOT/'tools/font/references'/REFERENCE).read_bytes()).hexdigest()==REFERENCE_SHA256==m['reference_sha256']
    for c in characters:
        source=USER_HANDWRITING_REFINED[c];record=m['glyphs'][c]
        assert digest(source)==record['source_sha256'],f'{c}: source hash'
        assert digest(source)!=record['old_source_sha256'],f'{c}: source was not replaced'
        assert source==MASTER_SOURCES[c].strokes(),f'{c}: master precedence'
        assert digest(MASTER_SOURCES[c])==record['recipe_sha256'],f'{c}: photo mapping/normalization'
        assert len(source)==record['new_branches'],f'{c}: branches'
        assert HIRAGANA_OPTICAL_TRANSFORMS[c]==OpticalTransform(),f'{c}: stale optical transform'
    for c in PRESERVED:
        assert digest(USER_HANDWRITING_REFINED[c])==m['baseline']['sources'][c]['sha256'],f'STOP: {c} changed'
        assert vars(HIRAGANA_OPTICAL_TRANSFORMS[c])==m['baseline']['sources'][c]['optical'],f'{c}: optical drift'
    katakana={c:digest(s) for c,s in KANA_STROKES.items() if 0x30a1<=ord(c)<=0x30ff}
    assert katakana==m['baseline']['katakana'],'STOP: Katakana source/pressure/position drift'
    assert {c:vars(t) for c,t in SHARED_HAN_OPTICAL_TRANSFORMS.items()}==m['baseline']['han_optical'],'Han transforms changed'
    assert tuple(m['baseline']['ke_alignment_reference_bounds'])==ALIGNMENT_REFERENCE_BOUNDS
    assert {c:list(v) for c,v in YOON_SMALL_KANA_OFFSETS.items()}==m['yoon_offsets']
    for c in 'ャュョ':
        assert list(YOON_SMALL_KANA_OFFSETS[c])==m['baseline']['yoon_offsets'][c]
    print('PASS: master source hashes/precedence; exact na-row, Katakana and Han preservation')


def verify_derivatives():
    for small,large in SMALL.items():
        dx,dy=SMALL_HIRAGANA_OPTICAL_SHIFTS.get(small,(0,0))
        expected=scale(KANA_STROKES[large],.72,center=(480,500),shift=(dx,-12+dy))
        if small in 'ゃゅょ':
            expected=translate_strokes(expected,*YOON_SMALL_KANA_OFFSETS[small])
        else:
            assert small not in YOON_SMALL_KANA_OFFSETS,f'Normal small {small} has yoon offset'
        assert KANA_STROKES[small]==expected,f'{small}: full derived points/pressure/position mismatch'
    with TTFont(TTF) as f:
        for c in TARGETS+''.join(SMALL):
            n=f.getBestCmap()[ord(c)]
            expected=build_stroke_glyph(translate_strokes(KANA_STROKES[c],dy=-145))
            assert expected.compile(f['glyf'])==f['glyf'][n].compile(f['glyf']),f'{c}: built outline differs from current source'
        from verify_supplement_font import mark_to_base_anchors, outlines_intersect
        for c in VOICED:
            base,kind=COMPOSITES[c]
            assert base in TARGETS
            n=f'uni{ord(c):04X}';b=f'uni{ord(base):04X}'
            mark='uni3099' if kind=='dakuten' else 'uni309A'
            anchor=DAKUTEN_ANCHOR if kind=='dakuten' else HANDAKUTEN_ANCHOR
            ba=base_anchor(f,b);delta=(ba[0]-anchor[0],ba[1]-anchor[1])
            actual=[part.getComponentInfo() for part in f['glyf'][n].components]
            assert actual==[(b,(1,0,0,1,0,0)),(mark,(1,0,0,1,*delta))],f'{c}: composite'
            base_pos,mark_pos,_=mark_to_base_anchors(f,mark,b)
            assert (base_pos[0]-mark_pos[0],base_pos[1]-mark_pos[1])==delta,f'{c}: GPOS'
            assert not outlines_intersect(f,b,mark,delta),f'{c}: mark collision'
        # One in-memory font forces all 26 decomposed sequences; production
        # binaries remain untouched. Also shape every requested two-cell yoon.
        import uharfbuzz as hb
        for table in f['cmap'].tables:
            if table.isUnicode() and hasattr(table,'cmap'):
                for c in VOICED:table.cmap.pop(ord(c),None)
        buffer=BytesIO();f.save(buffer)
        hbfont=hb.Font(hb.Face(buffer.getvalue()));hbfont.scale=(1024,1024)
        for c in VOICED:
            base,kind=COMPOSITES[c];mark='゙' if kind=='dakuten' else '゚'
            buf=hb.Buffer();buf.add_str(base+mark);buf.guess_segment_properties()
            hb.shape(hbfont,buf,{'ccmp':False,'mark':True})
            names=[f.getGlyphName(i.codepoint) for i in buf.glyph_infos]
            positions=buf.glyph_positions
            assert names==[f'uni{ord(base):04X}',f'uni{ord(mark):04X}'],(c,names)
            ba=base_anchor(f,names[0]);delta=(ba[0]-92,ba[1]-815)
            assert (positions[0].x_advance+positions[1].x_offset,positions[1].y_offset)==delta,c
            assert sum(p.x_advance for p in positions)==960,c
        # Use the unmodified production face for precomposed first kana.
        hbfont=hb.Font(hb.Face(TTF.read_bytes()));hbfont.scale=(1024,1024)
        for pair in YOON:
            buf=hb.Buffer();buf.add_str(pair);buf.guess_segment_properties();hb.shape(hbfont,buf)
            assert [f.getGlyphName(i.codepoint) for i in buf.glyph_infos]==[f'uni{ord(c):04X}' for c in pair],pair
            assert [p.x_advance for p in buf.glyph_positions]==[960,960],pair
        for c in 'ゃゅょャュョ':
            n=f'uni{ord(c):04X}';bb=bounds(f,n)
            assert bb[:2]==(180,24),(c,bb,'reviewed lower-left anchor')
            assert f['hmtx'].metrics[n][0]==960 and bb[2]<960
    print('PASS: all 12 small forms; ordinary path vs yoon; 26 composites and decomposed mark positioning')


def verify_font_scope():
    old_bytes=subprocess.check_output(['git','show',f'{BASE_MAIN}:{FONT_REL}'],cwd=ROOT)
    with TTFont(BytesIO(old_bytes)) as old,TTFont(TTF) as f,TTFont(WOFF2) as web:
        assert old.getBestCmap()==f.getBestCmap()==web.getBestCmap()
        assert old.getGlyphOrder()==f.getGlyphOrder()==web.getGlyphOrder()
        allowed={f.getBestCmap()[ord(c)] for c in EXPECTED_CHANGED}
        changed=set()
        for n in f.getGlyphOrder():
            current=signature(f,n)
            assert current==signature(web,n),f'TTF/WOFF2 mismatch: {n}'
            if current!=signature(old,n):
                assert n in allowed,f'STOP: unrelated glyph drift: {n}'
                changed.add(n)
        assert changed==allowed,('Expected all 79 dependent glyphs to change',allowed-changed)
        for n in allowed:
            x0,y0,x1,y1=bounds(f,n)
            assert f['hmtx'].metrics[n][0]==960 and 0<=x0<x1<960,(n,'advance/clipping')
            assert f['hhea'].descent<y0<y1<f['hhea'].ascent,(n,'vertical clipping')
        for table,fields in (('hhea',('ascent','descent','lineGap')),
                            ('OS/2',('sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent'))):
            for field in fields:assert getattr(old[table],field)==getattr(f[table],field)==getattr(web[table],field),field
        assert any(r.toUnicode()=='Version 1.025' for r in f['name'].names if r.nameID==5)
    print('PASS: exactly 41 bases + 12 small + 26 voiced changed; entire TTF/WOFF2 parity, safe bounds and advances')


def verify_fidelity():
    from render_hiragana_master_v2_proofs import masks,measurements
    for c in TARGETS:
        result=measurements(*masks(c))
        # Raster thickness is not production weight. These generous geometric
        # gates detect wrong cells/structure; the overlays remain the visual QA.
        assert result['ink_iou']>=.55,(c,'ink overlap',result)
        assert result['mean_ink_distance_photo_px']<=.5,(c,'photo mismatch',result)
    print('PASS: all 41 actual TTF glyphs match independent reference pixels (IoU >= .55; mean gap <= .5 px)')


def verify_determinism():
    paths=(TTF,WOFF2)
    before=[p.read_bytes() for p in paths]
    result=subprocess.run([sys.executable,str(ROOT/'tools/font/build_supplement_font.py')],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert before==[p.read_bytes() for p in paths],'Canonical rebuild is not byte-deterministic'
    print('PASS: canonical rebuild produces byte-identical TTF and WOFF2')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-rebuild',action='store_true')
    args=parser.parse_args()
    verify_sources();verify_derivatives();verify_font_scope();verify_fidelity()
    if not args.skip_rebuild:verify_determinism()
    print('PASS: all required yoon pairs: '+' '.join(YOON))
    return 0

if __name__=='__main__':raise SystemExit(main())
