#!/usr/bin/env python3
"""Independently verify all 45 mappings and freeze the complete 1.032 font."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
import uharfbuzz as hb

ROOT=Path(__file__).resolve().parents[2]
BASE='f0ed23419aa47965b9f5daa72d568381d79b42b3'
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF=ROOT/REL
WOFF2=TTF.with_suffix('.woff2')
BASE_SHA='d46795a76391677f12251b8031e32189cf5b914784566ebe91a1d8ebd360d091'
# Independent oracle: do not import the production recipe's coverage set.
REQUIRED='ℏ∂∝−↔∑∇⋅⟨⟩≈≃∼≤≥≪≫⇒⇔∏∓†″ℓ⊗‖∬∭ϵϕ≲≳∀∃∈∉ℝℂℋℒℱℜℑϑϱ'
EXPECTED={ord(c):f'uni{ord(c):04X}.qfwMath' for c in REQUIRED}
LAYOUT=('GSUB','GPOS','GDEF','kern','OS/2')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def baseline():
    raw=subprocess.check_output(['git','show',f'{BASE}:{REL}'],cwd=ROOT)
    assert digest(raw)==BASE_SHA,'Untrusted baseline'
    return TTFont(BytesIO(raw),recalcTimestamp=False)


def signature(font,n):
    g=font['glyf'][n]
    coords,ends,flags=g.getCoordinates(font['glyf'])
    return (g.numberOfContours,tuple(coords),tuple(ends),bytes(flags),
            tuple(c.getComponentInfo() for c in g.components) if g.isComposite() else (),
            font['hmtx'][n],font['vmtx'][n] if 'vmtx' in font else None)


def box(font,n):
    pen=BoundsPen(font.getGlyphSet());font.getGlyphSet()[n].draw(pen)
    return pen.bounds


def shape(font,text):
    if not hasattr(font, '_quantum_shaper'):
        raw=BytesIO();flavor=font.flavor;font.flavor=None;font.save(raw);font.flavor=flavor
        font._quantum_shaper=hb.Font(hb.Face(raw.getvalue()));font._quantum_shaper.scale=(1024,1024)
    face=font._quantum_shaper
    b=hb.Buffer();b.add_str(text);b.guess_segment_properties();hb.shape(face,b)
    return [(font.getGlyphName(i.codepoint),p.x_advance,p.y_advance,p.x_offset,p.y_offset)
            for i,p in zip(b.glyph_infos,b.glyph_positions)]


def check_font(old,new):
    assert len(EXPECTED)==45
    assert new.getGlyphOrder()[:len(old.getGlyphOrder())]==old.getGlyphOrder()
    assert set(new.getGlyphOrder()[len(old.getGlyphOrder()):])==set(EXPECTED.values())
    assert len(new.getGlyphOrder())==len(old.getGlyphOrder())+45
    assert not set(EXPECTED)&set(old.getBestCmap())
    assert new.getBestCmap()==old.getBestCmap()|EXPECTED
    assert len(new['cmap'].tables)==len(old['cmap'].tables)
    for a,b in zip(old['cmap'].tables,new['cmap'].tables):
        assert (a.platformID,a.platEncID,a.format,a.language)==(b.platformID,b.platEncID,b.format,b.language)
        assert b.cmap==a.cmap|(EXPECTED if a.isUnicode() and a.format!=14 else {})
    for n in old.getGlyphOrder():
        assert signature(old,n)==signature(new,n),f'Existing glyph/metrics changed: {n}'
        assert old['glyf'][n].compile(old['glyf'])==new['glyf'][n].compile(new['glyf']),f'Existing glyph bytes: {n}'
    for tag in LAYOUT:
        assert (tag in old)==(tag in new)
        if tag in old:assert old[tag].compile(old)==new[tag].compile(new),f'Layout/global metrics changed: {tag}'
    for tag,fields in [('hhea',('ascent','descent','lineGap','advanceWidthMax','minLeftSideBearing','minRightSideBearing','xMaxExtent','caretSlopeRise','caretSlopeRun','caretOffset')),('vhea',('ascent','descent','lineGap','advanceHeightMax','minTopSideBearing','minBottomSideBearing','yMaxExtent'))]:
        if tag in old:
            for field in fields:assert getattr(old[tag],field)==getattr(new[tag],field),(tag,field)
    assert new['head'].unitsPerEm==old['head'].unitsPerEm==1024
    assert abs(new['head'].fontRevision-1.033)<1/65536
    assert new['name'].getDebugName(5)=='Version 1.033'
    for a in old['name'].names:
        b=new['name'].getName(a.nameID,a.platformID,a.platEncID,a.langID)
        expected=a.toUnicode().replace('1.032','1.033') if a.nameID in (3,5) else a.toUnicode()
        assert b.toUnicode()==expected,('name',a.nameID)
    assert len(old['name'].names)==len(new['name'].names)
    metrics={}
    for cp,n in EXPECTED.items():
        g=new['glyf'][n];bb=box(new,n);advance,lsb=new['hmtx'][n]
        assert bb and g.numberOfContours!=0 and n!='.notdef'
        assert 0<=bb[0]<bb[2]<advance,(chr(cp),'horizontal clipping',bb,advance)
        assert max(new['hhea'].descent,new['OS/2'].sTypoDescender,-new['OS/2'].usWinDescent)<bb[1]<bb[3]<min(new['hhea'].ascent,new['OS/2'].sTypoAscender,new['OS/2'].usWinAscent),(chr(cp),'vertical clipping',bb)
        assert lsb==g.xMin and advance>0
        if 'vmtx' in new:
            assert new['vmtx'][n]==old['vmtx'][old.getBestCmap()[ord('=')]]
        metrics[f'U+{cp:04X}']=dict(character=chr(cp),glyph=n,bounds=bb,advance=advance,lsb=lsb,rsb=advance-g.xMax)
    # Source identities and visual distinction are both required.
    for added,existing in [('ℏ','h'),('∂','δ'),('∑','Σ'),('∏','Π'),('⋅','·'),('⟨','〈'),('⟩','〉'),('‖','∥'),('ϵ','ε'),('ϕ','φ'),('ϑ','θ'),('ϱ','ρ'),('ℝ','R'),('ℂ','C'),('ℋ','H'),('ℒ','L'),('ℱ','F'),('ℜ','R'),('ℑ','I')]:
        a=new.getBestCmap()[ord(added)];b=new.getBestCmap()[ord(existing)]
        assert a!=b and signature(new,a)!=signature(new,b),(added,existing)
    changed=[]
    assert set(old.keys())==set(new.keys())
    for tag in old.keys():
        if tag=='GlyphOrder':continue
        if old[tag].compile(old)!=new[tag].compile(new):changed.append(tag)
    allowed={'head','name','maxp','glyf','loca','hmtx','vmtx','hhea','vhea','post','cmap'}
    assert set(changed)<=allowed,changed
    return metrics,changed



def restore_1_032_for_historical_checks(font):
    """Validate the entire extension before removing only it in memory.

    Old verifiers keep their exact historical assertions. Production binaries
    and their proofs never pass through this function. This is not an exemption:
    every original glyph byte/metric and layout table must match pinned 1.032.
    """
    if font['name'].getDebugName(5) == 'Version 1.034':
        from verify_math_refinement import restore_1_033_for_historical_checks
        restore_1_033_for_historical_checks(font)
    if font['name'].getDebugName(5) != 'Version 1.033':
        return
    import copy
    with baseline() as old:
        check_font(old,font)
        for name in EXPECTED.values():
            del font['glyf'][name]
            del font['hmtx'].metrics[name]
            if 'vmtx' in font:del font['vmtx'].metrics[name]
        font.setGlyphOrder(old.getGlyphOrder())
        for tag in ('head','name','maxp','hhea','vhea','post','loca','cmap'):
            if tag in old:font[tag]=copy.deepcopy(old[tag])


def verify(rebuild=False):
    with baseline() as old,TTFont(TTF,recalcTimestamp=False) as new,TTFont(WOFF2,recalcTimestamp=False) as web:
        metrics,changed=check_font(old,new);check_font(old,web)
        assert new.getGlyphOrder()==web.getGlyphOrder()
        for n in new.getGlyphOrder():assert signature(new,n)==signature(web,n),('web parity',n)
        from render_quantum_proof import SAMPLES,validate_coverage
        validate_coverage()
        for font in (new,web):
            for c in REQUIRED:
                assert shape(font,c)==[(EXPECTED[ord(c)],font['hmtx'][EXPECTED[ord(c)]][0],0,0,0)],('native shaping',c)
            for sample in SAMPLES:
                assert all(row[0]!='.notdef' for row in shape(font,sample)),sample
        for text in ('Ça Ça Ä Ä Œuvre cœur Straße','って どっち がっこう キャッチ ツァ で ど','量子物理 容壁堅踊 漢字','αβγδεζηθικλμνξοπρστυφχψω','± × · ÷ ∕ √ ∞ = ≠ ≡ ∫ ∮ Δ ← → ↑ ↓ ∴ ∵ ⊥ ∥'):
            assert shape(old,text)==shape(new,text)==shape(web,text),('existing shaping',text)
        count=len(old.getGlyphOrder())
    if rebuild:
        before=[p.read_bytes() for p in (TTF,WOFF2)]
        result=subprocess.run([sys.executable,str(ROOT/'tools/font/build_supplement_font.py')],cwd=ROOT,capture_output=True)
        assert result.returncode==0,result.stdout+result.stderr
        assert before==[p.read_bytes() for p in (TTF,WOFF2)],'Non-deterministic build'
    return dict(version='1.033',base_commit=BASE,baseline_ttf_sha256=BASE_SHA,
                hashes={p.suffix[1:]:digest(p.read_bytes()) for p in (TTF,WOFF2)},
                added_codepoints=45,preserved_glyphs=count,existing_outline_or_metric_changes=0,
                layout_tables_unchanged=True,changed_tables=changed,deterministic_rebuild=rebuild,
                ttf_woff2_parity=True,glyphs=metrics)


def main():
    with TTFont(TTF) as font:
        if font['name'].getDebugName(5)=='Version 1.034':
            from verify_math_refinement import main as current_main
            return current_main()
    p=argparse.ArgumentParser();p.add_argument('--skip-rebuild',action='store_true');p.add_argument('--write-report',action='store_true');args=p.parse_args()
    result=verify(not args.skip_rebuild)
    if args.write_report:
        (ROOT/'tools/font/reports/quantum-symbols.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f"PASS: 45 mappings; {result['preserved_glyphs']} existing glyph bytes/metrics unchanged; layout and native shaping preserved; TTF/WOFF2 parity")
    print('SHA-256:',json.dumps(result['hashes']));print('Changed tables:',', '.join(result['changed_tables']))
    if not args.skip_rebuild:print('PASS: byte-identical canonical rebuild')

if __name__=='__main__':main()
