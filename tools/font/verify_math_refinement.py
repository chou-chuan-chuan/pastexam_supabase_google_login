#!/usr/bin/env python3
"""Pin 1.033 and allow only three lighter outlines, a hat lookup and MATH."""
import argparse
import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import statistics
import subprocess
import sys
from fontTools.ttLib import TTFont
from verify_quantum_symbols import signature,shape,box

ROOT=Path(__file__).resolve().parents[2]
BASE='ca34467431ddc05e15368c244d1128687a074605'
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF=ROOT/REL;WOFF2=TTF.with_suffix('.woff2')
BASE_SHA='6677ad97fb50cf5c23747882eaee9ae147536311eaa9f1374b8deb21132090f2'
CHANGED='∑∇∏'
HATS='xprLBαβγδεζηθικλμνξοπρστυφχψωϵϕϑϱℋℒℱℜℑ'
REFS='hxprHABCLFαβγδεθφψρ=+<>∫∥←→'


def baseline():
    raw=subprocess.check_output(['git','show',f'{BASE}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    return TTFont(BytesIO(raw),recalcTimestamp=False)


def check(old,new):
    assert old.getGlyphOrder()==new.getGlyphOrder()
    assert old.getBestCmap()==new.getBestCmap()
    cm=old.getBestCmap();allowed={cm[ord(c)] for c in CHANGED};changed=set()
    for n in old.getGlyphOrder():
        if signature(old,n)!=signature(new,n):changed.add(n)
        if n not in allowed:
            assert old['glyf'][n].compile(old['glyf'])==new['glyf'][n].compile(new['glyf']),n
        assert old['hmtx'][n][0]==new['hmtx'][n][0],('advance',n)
        assert old['vmtx'][n]==new['vmtx'][n],('vertical metric',n)
    assert changed==allowed,changed
    for c,contours in zip(CHANGED,(1,2,1)):
        n=cm[ord(c)];a=box(old,n);b=box(new,n)
        assert a[0]<b[0]<b[2]<a[2] and a[1]<b[1]<b[3]<a[3],(c,'inset')
        assert new['glyf'][n].numberOfContours==contours,(c,'lost counter or detached ink')
        assert new['hmtx'][n][1]==new['glyf'][n].xMin
    assert new['name'].getDebugName(5)=='Version 1.034'
    assert abs(new['head'].fontRevision-1.034)<1/65536
    for record in old['name'].names:
        actual=new['name'].getName(record.nameID,record.platformID,record.platEncID,record.langID)
        text=record.toUnicode().replace('1.033','1.034') if record.nameID in (3,5) else record.toUnicode()
        assert actual.toUnicode()==text
    for tag in ('cmap','GSUB','GDEF','OS/2','hhea','vhea','vmtx','gasp','kern'):
        assert (tag in new)==(tag in old)
        if tag in old:assert old[tag].compile(old)==new[tag].compile(new),tag
    assert new['head'].unitsPerEm==old['head'].unitsPerEm==1024
    before=old['GPOS'].table;after=new['GPOS'].table
    assert after.LookupList.LookupCount==before.LookupList.LookupCount+1
    lookup=after.LookupList.Lookup[-1]
    assert lookup.LookupType==4 and lookup.LookupFlag==0 and lookup.SubTableCount==1
    sub=lookup.SubTable[0];mark=cm[0x302]
    assert sub.MarkCoverage.glyphs==[mark]
    assert set(sub.BaseCoverage.glyphs)=={cm[ord(c)] for c in HATS}
    assert sub.ClassCount==1
    # Strip only the authorized appended lookup, then require exact GPOS identity.
    retained=copy.deepcopy(new['GPOS']);g=retained.table
    g.LookupList.Lookup.pop();g.LookupList.LookupCount-=1
    for record in g.FeatureList.FeatureRecord:
        if record.FeatureTag=='mark':
            assert record.Feature.LookupListIndex.pop()==before.LookupList.LookupCount
            record.Feature.LookupCount-=1
    assert retained.compile(new)==old['GPOS'].compile(old)
    assert 'MATH' not in old and 'MATH' in new
    constants=new['MATH'].table.MathConstants
    assert constants.AxisHeight.Value==330 and constants.FractionRuleThickness.Value==36
    assert abs(sum(box(new,cm[ord('=')])[1::2])/2-constants.AxisHeight.Value)<1
    assert constants.FractionNumeratorGapMin.Value==constants.FractionDenominatorGapMin.Value==72
    assert constants.ScriptPercentScaleDown==70 and constants.ScriptScriptPercentScaleDown==50
    hat_metrics={}
    for c in HATS:
        shaped=shape(new,c+'̂');assert len(shaped)==2 and shaped[1][0]==mark,c
        n,adv,ya,dx,dy=shaped[0];mn,ma,my,mx,yy=shaped[1]
        assert (ma,my)==(0,0) and adv==old['hmtx'][cm[ord(c)]][0]
        b=box(new,n);m=box(new,mn)
        left=adv+mx+m[0];right=adv+mx+m[2]
        bottom=m[1]+yy;top=m[3]+yy;gap=bottom-b[3]
        assert 30<=gap<=49,(c,'hat clearance',gap)
        assert abs((left+right)/2-(b[0]+b[2])/2)<2,(c,'hat centering')
        assert top<new['OS/2'].sTypoAscender and bottom>b[3],(c,'hat clipping')
        hat_metrics[c]=dict(ink_gap=gap,top=top,x_offset=mx,y_offset=yy,advance=adv)
    # Do not disturb orthographic accents, other marks, or non-hatted operators.
    for text in ('x p r L B ψ φ ρ ∑ ∇ ∏','â ê î ô û â ê î ô û Ĥ Â','x̃ p̃ ẋ p̈ Ç Ç Ä Ä','量子物理 漢字 って どっち で キャッチ'):
        assert shape(old,text)==shape(new,text),text
    for text in ('x̂²p̂','x̂p̂x̂','p̂x̂²','(x̂²p̂ + 2x̂p̂x̂ + p̂x̂²) / 4'):
        assert sum(p[1] for p in shape(new,text))==sum(p[1] for p in shape(old,text))
    assert set(new.keys())==set(old.keys())|{'MATH'}
    return hat_metrics


def restore_1_033_for_historical_checks(font):
    if font['name'].getDebugName(5)!='Version 1.034':return
    with baseline() as old:
        check(old,font)
        for c in CHANGED:
            n=old.getBestCmap()[ord(c)]
            font['glyf'][n]=copy.deepcopy(old['glyf'][n]);font['hmtx'][n]=old['hmtx'][n]
        for tag in ('head','name','maxp','GPOS','loca'):font[tag]=copy.deepcopy(old[tag])
        del font['MATH']
    if hasattr(font,'_quantum_shaper'):del font._quantum_shaper


def verify(rebuild=True):
    with baseline() as old,TTFont(TTF,recalcTimestamp=False) as new,TTFont(WOFF2,recalcTimestamp=False) as web:
        hats=check(old,new);check(old,web)
        for n in new.getGlyphOrder():assert signature(new,n)==signature(web,n),n
        assert new['MATH'].compile(new)==web['MATH'].compile(web)
        assert new['GPOS'].compile(new)==web['GPOS'].compile(web)
        # Keep all original 45-codepoint checks, evaluated on validated 1.033 stage.
        from verify_quantum_symbols import baseline as original_baseline,check_font
        restored=TTFont(TTF,recalcTimestamp=False);restore_1_033_for_historical_checks(restored)
        with original_baseline() as original:check_font(original,restored)
        count=len(old.getGlyphOrder())
    from audit_japanese_weight import glyph_measurement
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as temp:
        oldpath=Path(temp)/'1.033.ttf';oldpath.write_bytes(subprocess.check_output(['git','show',f'{BASE}:{REL}'],cwd=ROOT))
        weight={}
        for size in (20,32,64,96):
            reference=statistics.median(glyph_measurement(TTF,c,size)['effective_stroke_px'] for c in REFS)
            weight[str(size)]={'reference_median_px':reference,'glyphs':{}}
            for c in CHANGED:
                before=glyph_measurement(oldpath,c,size)['effective_stroke_px'];after=glyph_measurement(TTF,c,size)['effective_stroke_px']
                assert after<before and .8<=after/reference<=1.2,(size,c,before,after,reference)
                weight[str(size)]['glyphs'][c]=dict(before_px=before,after_px=after,reference_ratio=after/reference)
    if rebuild:
        before=[p.read_bytes() for p in (TTF,WOFF2)]
        proc=subprocess.run([sys.executable,str(ROOT/'tools/font/build_supplement_font.py')],cwd=ROOT,capture_output=True)
        assert proc.returncode==0,proc.stdout+proc.stderr
        assert before==[p.read_bytes() for p in (TTF,WOFF2)],'Non-deterministic rebuild'
    return dict(version='1.034',base_commit=BASE,baseline_ttf_sha256=BASE_SHA,
        hashes={p.suffix[1:]:hashlib.sha256(p.read_bytes()).hexdigest() for p in (TTF,WOFF2)},
        changed_outlines=list(CHANGED),preserved_glyphs=count-3,all_advances_unchanged=True,
        cmap_unchanged=True,coverage=45,source_lookups_unchanged=True,hat_metrics=hats,
        axis_height=330,fraction_rule_thickness=36,stroke_weight=weight,
        ttf_woff2_parity=True,deterministic_rebuild=rebuild)


def main():
    p=argparse.ArgumentParser();p.add_argument('--skip-rebuild',action='store_true');p.add_argument('--write-report',action='store_true');a=p.parse_args()
    r=verify(not a.skip_rebuild)
    if a.write_report:(ROOT/'tools/font/reports/math-refinement.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(f"PASS: only three authorized outlines changed; {r['preserved_glyphs']} glyphs frozen; all advances/cmaps unchanged")
    print('PASS: native combining hats; scoped GPOS; MATH axis/fraction rules; 45-codepoint coverage; measured weight')
    print('SHA-256:',r['hashes']);print('Deterministic rebuild:',r['deterministic_rebuild'])

if __name__=='__main__':main()
