#!/usr/bin/env python3
"""Verify measured 1.026 scale against immutable 1.025, including all glyphs.

Expected reference hashes and base SHA are pinned, never rewritten here.
Default execution repeats the canonical build and checks byte determinism.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
import math
import subprocess
import sys

from fontTools.ttLib import TTFont
import uharfbuzz as hb

from measure_kana_kanji_balance import (
    ROOT, BASE_MAIN, FONT_REL, REFERENCE_PATH, GROUPS, HIRAGANA, KATAKANA, HAN,
    factors, measure_groups,
)
from japanese.stroke_engine import build_stroke_glyph, translate_strokes
from japanese.build_kana import (
    bounds, glyph_name, base_anchor, mark_name_for, DAKUTEN_ANCHOR,
    KANA_VERTICAL_SHIFT_1_026, JAPANESE_MARK_VERTICAL_SHIFT_1_026,
    JAPANESE_BOTTOM_ALIGNMENT_SHIFT, DAKUTEN_ANCHOR_1_026, apply_bottom_alignment,
    DO_BASE_GLYPH,
)
from kana_sources.full_data import (
    KANA_STROKES, VERSION_1_025_KANA_STROKES, ACCEPTED_LARGE_KANA_STROKES,
    BALANCED_LARGE_KANA_STROKES, SMALL_HIRAGANA_BASES, SMALL_KATAKANA_BASES,
    SMALL_HIRAGANA_OPTICAL_SHIFTS, YOON_SMALL_KANA_OFFSETS, scale,
    COMPOSITES, ITERATION_STROKES, JAPANESE_MARK_STROKES,
    DAKUTEN_STROKES, HANDAKUTEN_STROKES,
)
from kana_sources.han_balance import (
    HIRAGANA_HAN_BALANCE_SCALE, KATAKANA_HAN_BALANCE_SCALE,
    script_scale, optical_center, uniform_scale, balance_strokes,
)

TTF = ROOT / FONT_REL
WOFF2 = TTF.with_suffix('.woff2')
REFERENCE_SHA256 = '30bd110983e4cc1348168b69b774e124995b5aef66f396c39a4a74e24180ee01'
VARIANTS = {'uni3099.katakana', 'uni309A.katakana', DO_BASE_GLYPH}
EXPECTED_CHANGED_CHARACTERS = set(KANA_STROKES) | set(COMPOSITES) | set('ゝゞヽヾー゙゚゛゜')
YOON = tuple(a+b for a in 'きぎしじちにひびぴみり' for b in 'ゃゅょ')
KATAKANA_YOON = tuple(a+b for a in 'キギシジチニヒビピミリ' for b in 'ャュョ')


def git_bytes(path):
    return subprocess.check_output(['git', 'show', f'{BASE_MAIN}:{path}'], cwd=ROOT)


def old_font():
    return TTFont(BytesIO(git_bytes(FONT_REL)))


def signature(font, name):
    g = font['glyf'][name]
    coordinates, ends, flags = g.getCoordinates(font['glyf'])
    components = tuple(c.getComponentInfo() for c in g.components) if g.isComposite() else ()
    return g.numberOfContours, tuple(coordinates), tuple(ends), bytes(flags), components, font['hmtx'].metrics[name]


def assert_built(font, character, strokes, shift=KANA_VERTICAL_SHIFT_1_026, *, final=False):
    name = glyph_name(character)
    expected = build_stroke_glyph(translate_strokes(strokes, dy=shift))
    if final:
        apply_bottom_alignment(expected)
    assert expected.compile(font['glyf']) == font['glyf'][name].compile(font['glyf']), (character, 'unexpected outline')


def verify_shape_preservation():
    # Pin authoring inputs and 1.025 normalization, rather than reading raster
    # pixels or introducing another shape interpretation for this scale pass.
    unchanged = (
        'kana_sources/hiragana_master_v2.py', 'kana_sources/user_handwriting_refined.py',
        'kana_sources/user_handwriting_optical.py', 'kana_sources/master_data.py',
        'kana_sources/legibility_overrides.py', 'japanese/stroke_engine.py',
        'japanese/user_japanese_overrides.py', 'references/hiragana-master-v2-manifest.json',
        'references/hiragana-metric-targets.json', 'references/hiragana-metric-references.json',
        'references/hiragana-maintainer-master-v2.png',
        'references/hiragana-maintainer-master-v2-na-row.png',
    )
    for relative in unchanged:
        path = 'tools/font/' + relative
        current = (ROOT/path).read_bytes()
        baseline = git_bytes(path)
        if not path.endswith('.png'):
            current, baseline = current.replace(b'\r\n', b'\n'), baseline.replace(b'\r\n', b'\n')
        if relative == 'japanese/user_japanese_overrides.py':
            from verify_kanji_odoru_optical import without_odoru_source
            current = without_odoru_source(current)
        assert current == baseline, ('Accepted source changed', relative)
    with old_font() as old, TTFont(TTF) as new:
        for c, strokes in VERSION_1_025_KANA_STROKES.items():
            assert_built(old, c, strokes)
        for c, before in ACCEPTED_LARGE_KANA_STROKES.items():
            after = BALANCED_LARGE_KANA_STROKES[c]
            factor = script_scale(c)
            cx,cy = optical_center(before)
            assert len(after) == len(before)
            for a,b in zip(before,after):
                assert len(a.points) == len(b.points) and a.cap == b.cap
                for (x,y),(u,v) in zip(a.points,b.points):
                    assert math.isclose(u,cx+(x-cx)*factor,abs_tol=1e-10)
                    assert math.isclose(v,cy+(y-cy)*factor,abs_tol=1e-10)
                for field in ('width','start_width','end_width'):
                    a_value,b_value = getattr(a,field),getattr(b,field)
                    assert b_value is None if a_value is None else math.isclose(b_value,a_value*factor,abs_tol=1e-10)
        for c,strokes in KANA_STROKES.items():
            if c != 'と':
                assert_built(new,c,strokes,final=True)
            name = glyph_name(c)
            assert old['glyf'][name].numberOfContours == new['glyf'][name].numberOfContours, (c, 'loop/contour topology changed')
        for c in HIRAGANA+KATAKANA:
            if c == 'と':
                continue  # Version 1.030 uniform scale is pinned by verify_do_base_clearance.py.
            a,b = bounds(old,glyph_name(c)),bounds(new,glyph_name(c))
            factor=script_scale(c)
            # Each endpoint is quantized in both old and new rendered outlines.
            # Two units bound the interval error; the center gate is tighter.
            for lo,hi in ((0,2),(1,3)):
                assert abs((b[hi]-b[lo])-(a[hi]-a[lo])*factor)<=2,(c,'nonuniform size')
                placement = JAPANESE_BOTTOM_ALIGNMENT_SHIFT if lo == 1 else 0
                assert abs((b[hi]+b[lo])/2-placement-(a[hi]+a[lo])/2)<=.5,(c,'accepted pre-translation center moved')
    print('PASS: immutable 1.025 source files, all 46 Hiragana and all Katakana; one uniform geometry/pressure scale per script, accepted centers retained')


def verify_metrics():
    raw=REFERENCE_PATH.read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(raw).hexdigest()==REFERENCE_SHA256,'Metric reference snapshot changed'
    data=json.loads(raw)
    assert data['base_main']==BASE_MAIN and data['samples']==GROUPS
    assert len(HAN)==59 and len(HIRAGANA)==len(KATAKANA)==46
    assert data['balance']==factors(data['references'])
    assert HIRAGANA_HAN_BALANCE_SCALE==data['balance']['hiragana']['scale']
    assert KATAKANA_HAN_BALANCE_SCALE==data['balance']['katakana']['scale']
    old_bytes=git_bytes(FONT_REL)
    assert hashlib.sha256(old_bytes).hexdigest()==data['references']['production_1_025']['sha256']
    with TTFont(BytesIO(old_bytes)) as old,TTFont(TTF) as new:
        assert old['head'].unitsPerEm==new['head'].unitsPerEm==1024
        assert measure_groups(old)==data['references']['production_1_025']['groups']
        final=measure_groups(new)
        assert final['han']==data['references']['production_1_025']['groups']['han']
        for script in ('hiragana','katakana'):
            measured=final[script]['median']['height_em']
            target=data['balance'][script]['target_height_em']
            assert abs(measured-target)<=1/1024,(script,measured,target)
            print(f"PASS: {script} final Han-height ratio {final[script]['relative_to_han']['height_em']:.9f}; scale {data['balance'][script]['scale']:.12f}")
        report=json.loads((ROOT/'tools/font/reports/kana-kanji-scale-balance.json').read_text())
        # This report is the immutable accepted 1.026 size stage.
        from render_kana_bottom_alignment_proof import baseline_bytes
        with TTFont(BytesIO(baseline_bytes())) as accepted:
            assert report['final']==measure_groups(accepted) and report['balance']==data['balance'],'Stale historical report'


def verify_font_scope():
    with old_font() as old,TTFont(TTF) as new,TTFont(WOFF2) as web:
        from verify_kanji_odoru_optical import extend_historical_han_oracle
        extend_historical_han_oracle(old)
        assert old.getBestCmap()==new.getBestCmap()==web.getBestCmap()
        assert new.getGlyphOrder()==web.getGlyphOrder()
        assert [n for n in new.getGlyphOrder() if n not in VARIANTS]==old.getGlyphOrder()
        allowed={glyph_name(c) for c in EXPECTED_CHANGED_CHARACTERS}
        changed=set()
        han_names={name for cp,name in old.getBestCmap().items() if
                   0x3400<=cp<=0x9FFF or 0xF900<=cp<=0xFAFF or 0x20000<=cp<=0x323AF}
        han_hashes=[]
        for name in new.getGlyphOrder():
            current=signature(new,name)
            assert current==signature(web,name),('TTF/WOFF2 mismatch',name)
            if name not in VARIANTS:
                prior=signature(old,name)
                if prior!=current:
                    assert name in allowed,('Unrelated glyph changed',name)
                    changed.add(name)
                if name in han_names:
                    assert prior==current,('Han changed',name)
                    han_hashes.append((name,hashlib.sha256(repr(current).encode()).hexdigest()))
        assert changed==allowed,('Unexpected glyph change set',changed^allowed)
        for c in EXPECTED_CHANGED_CHARACTERS-set('゙゚゛゜'):
            name=glyph_name(c);bb=bounds(new,name)
            assert new['hmtx'].metrics[name][0]==960,(c,'advance')
            assert 0<=bb[0]<bb[2]<960 and new['hhea'].descent<bb[1]<bb[3]<new['hhea'].ascent,(c,'clipping',bb)
        for table,fields in (('hhea',('ascent','descent','lineGap')),
                            ('OS/2',('sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent'))):
            for field in fields:
                assert getattr(old[table],field)==getattr(new[table],field)==getattr(web[table],field),field
        for font in (new,web):
            assert font['name'].getDebugName(5)=='Version 1.030'
            assert abs(font['head'].fontRevision-1.030)<1/65536
        for table in ('GSUB','GPOS','GDEF'):
            assert new[table].compile(new)==web[table].compile(web),(table,'TTF/WOFF2 layout parity')
        aggregate=hashlib.sha256(repr(han_hashes).encode()).hexdigest()
        print(f'PASS: all {len(han_names)} Han hashes match the historical oracle plus pinned 1.028 踊; aggregate {aggregate}')
        print(f'PASS: exactly {len(changed)} kana/related glyphs scaled, two unmapped mark variants; all other glyphs and line metrics unchanged; entire TTF/WOFF2 parity')


def verify_derivatives():
    for small,large in SMALL_HIRAGANA_BASES.items():
        dx,dy=SMALL_HIRAGANA_OPTICAL_SHIFTS.get(small,(0,0))
        expected=scale(KANA_STROKES[large],.72,center=(480,500),shift=(dx,-12+dy))
        if small in YOON_SMALL_KANA_OFFSETS:
            expected=translate_strokes(expected,*YOON_SMALL_KANA_OFFSETS[small])
        assert KANA_STROKES[small]==expected,(small,'derivation')
    for small,large in SMALL_KATAKANA_BASES.items():
        assert KANA_STROKES[small]==scale(KANA_STROKES[large],.72),(small,'Katakana derivation')
    from verify_supplement_font import mark_to_base_anchors, outlines_intersect
    with TTFont(TTF) as font:
        for c in 'ゃゅょャュョ':
            assert bounds(font,glyph_name(c))[:2]==(180,24+JAPANESE_BOTTOM_ALIGNMENT_SHIFT),(c,'lower-left placement')
        for c,strokes in ITERATION_STROKES.items():
            assert_built(font,c,balance_strokes(c,strokes),final=True)
        assert_built(font,'ー',balance_strokes('ー',JAPANESE_MARK_STROKES['ー']),JAPANESE_MARK_VERTICAL_SHIFT_1_026,final=True)
        for c in ('あ','ア'):
            for kind,strokes in (('dakuten',DAKUTEN_STROKES),('handakuten',HANDAKUTEN_STROKES)):
                name=mark_name_for(c,kind)
                expected=apply_bottom_alignment(build_stroke_glyph(uniform_scale(strokes,script_scale(c),DAKUTEN_ANCHOR_1_026)))
                assert expected.compile(font['glyf'])==font['glyf'][name].compile(font['glyf']),name
                assert font['hmtx'].metrics[name][0]==0
                assert font['GDEF'].table.GlyphClassDef.classDefs[name]==3
        for c,mark in (('゛','uni3099'),('゜','uni309A')):
            assert font['hmtx'].metrics[glyph_name(c)][0]==300
            assert font['glyf'][glyph_name(c)].components[0].getComponentInfo()==(mark,(1,0,0,1,65,-165))
        composites={**COMPOSITES,'ゞ':('ゝ','dakuten'),'ヾ':('ヽ','dakuten')}
        for c,(base,kind) in composites.items():
            mark=mark_name_for(base,kind);b=DO_BASE_GLYPH if c=='ど' else glyph_name(base)
            anchor=base_anchor(font,glyph_name(base));delta=(anchor[0]-DAKUTEN_ANCHOR[0],anchor[1]-DAKUTEN_ANCHOR[1])
            parts=[p.getComponentInfo() for p in font['glyf'][glyph_name(c)].components]
            assert parts==[(b,(1,0,0,1,0,0)),(mark,(1,0,0,1,*delta))],(c,'composite')
            bp,mp,_=mark_to_base_anchors(font,mark,b)
            assert (bp[0]-mp[0],bp[1]-mp[1])==delta,(c,'GPOS')
            assert not outlines_intersect(font,b,mark,delta),(c,'mark collision')
        # Force decomposition for every voiced kana, including iteration marks.
        for table in font['cmap'].tables:
            if table.isUnicode() and hasattr(table,'cmap'):
                for c in composites:
                    table.cmap.pop(ord(c),None)
        stream=BytesIO();font.save(stream)
        hbfont=hb.Font(hb.Face(stream.getvalue()));hbfont.scale=(1024,1024)
        for c,(base,kind) in composites.items():
            mark='゙' if kind=='dakuten' else '゚'
            buf=hb.Buffer();buf.add_str(base+mark);buf.guess_segment_properties()
            hb.shape(hbfont,buf,{'ccmp':True,'mark':True})
            names=[font.getGlyphName(i.codepoint) for i in buf.glyph_infos]
            expected_base=DO_BASE_GLYPH if c=='ど' else glyph_name(base)
            assert names==[expected_base,mark_name_for(base,kind)],(c,'decomposed glyphs',names)
            p=buf.glyph_positions;anchor=base_anchor(font,glyph_name(base))
            assert (p[0].x_advance+p[1].x_offset,p[1].y_offset)==(anchor[0]-DAKUTEN_ANCHOR[0],anchor[1]-DAKUTEN_ANCHOR[1]),(c,'shaping')
            assert sum(q.x_advance for q in p)==960,c
    hbfont=hb.Font(hb.Face(TTF.read_bytes()));hbfont.scale=(1024,1024)
    with TTFont(TTF) as font:
        for pair in YOON+KATAKANA_YOON:
            buf=hb.Buffer();buf.add_str(pair);buf.guess_segment_properties();hb.shape(hbfont,buf)
            assert [font.getGlyphName(i.codepoint) for i in buf.glyph_infos]==[glyph_name(c) for c in pair],pair
            assert [p.x_advance for p in buf.glyph_positions]==[960,960],pair
    print('PASS: all 12 small Hiragana and Katakana derivations; 33+33 two-cell yoon; all voiced/iteration precomposed and decomposed marks identical and collision-free')


def verify_determinism():
    before=[p.read_bytes() for p in (TTF,WOFF2)]
    result=subprocess.run([sys.executable,str(ROOT/'tools/font/build_supplement_font.py')],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert before==[p.read_bytes() for p in (TTF,WOFF2)],'Rebuild is not byte-deterministic'
    print('PASS: byte-identical canonical TTF/WOFF2 rebuild')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-rebuild',action='store_true')
    args=parser.parse_args()
    verify_shape_preservation();verify_metrics();verify_font_scope();verify_derivatives()
    if not args.skip_rebuild:
        verify_determinism()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
