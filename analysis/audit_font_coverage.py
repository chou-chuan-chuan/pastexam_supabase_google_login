#!/usr/bin/env python3
"""Audit the explicit 45-codepoint plan; a missing/aliased glyph is a failure.

P2/P3 remain candidate lecture requirements even though font coverage is now
implemented. Lecture provenance is the user's supplied plan, not PDF extraction.
Run --write to regenerate reports; default execution detects stale reports.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unicodedata
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_FONT=ROOT/'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
GROUPS={'P0':'ℏ∂∝−↔','P1':'∑∇⋅⟨⟩≈≃∼≤≥≪≫⇒⇔','P2':'∏∓†″ℓ⊗‖∬∭ϵϕ≲≳','P3':'∀∃∈∉ℝℂℋℒℱℜℑϑϱ'}
EVIDENCE={'P0':'existing calibration page; supplied plan','P1':'two previously visually read lectures; supplied plan','P2':'possible later-topic requirement; not page-verified','P3':'optional mathematical notation; not currently necessary'}


def audit(path):
    rows=[];failures=[]
    with TTFont(path) as font:
        cm=font.getBestCmap()
        for group,chars in GROUPS.items():
            for c in chars:
                cp=ord(c);expected=f'uni{cp:04X}.qfwMath';actual=cm.get(cp)
                covered=actual==expected and font['glyf'][actual].numberOfContours!=0
                if not covered:failures.append(f'U+{cp:04X}: expected nonempty {expected}, found {actual}')
                for table in font['cmap'].tables:
                    if table.isUnicode() and table.format!=14 and table.cmap.get(cp)!=expected:
                        failures.append(f'U+{cp:04X}: inconsistent Unicode cmap {table.platformID}/{table.platEncID}')
                rows.append(dict(priority=group,character=c,codepoint=f'U+{cp:04X}',unicode_name=unicodedata.name(c),glyph=actual or '',status='present' if covered else 'missing_or_invalid',requirement_evidence=EVIDENCE[group]))
        version=font['name'].getDebugName(5);revision=font['head'].fontRevision
        if version!='Version 1.036' or abs(revision-1.036)>=1/65536:failures.append(f'Unexpected font version: {version} / {revision}')
        result=dict(font=path.name,version=version,font_revision=revision,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    scope='45 independent P0/P1/P2/P3 codepoints; not an exhaustive lecture-folder audit',
                    total_unicode_codepoints=len(cm),expected_count=45,present_count=sum(r['status']=='present' for r in rows),
                    priorities={g:dict(expected=len(chars),present=sum(r['status']=='present' for r in rows if r['priority']==g),evidence=EVIDENCE[g]) for g,chars in GROUPS.items()},
                    excluded=[dict(codepoint='U+20D7',reason='Combining vector arrow and positioning are outside this 45-codepoint scope',present=0x20D7 in cm)],glyphs=rows,failures=failures)
    return result,rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--font',type=Path,default=DEFAULT_FONT);p.add_argument('--write',action='store_true');args=p.parse_args()
    result,rows=audit(args.font)
    js=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    if args.font.resolve()==DEFAULT_FONT.resolve():
        for path,content in [(ROOT/'analysis/font-coverage.json',js),(ROOT/'analysis/font-gap-candidates.csv',stream.getvalue())]:
            if args.write:path.write_text(content,encoding='utf-8')
            elif not path.exists() or path.read_text()!=content:result['failures'].append(f'Stale report: {path.name}; run --write')
    if result['failures']:
        print('\n'.join(result['failures']),file=sys.stderr);return 1
    print(f"PASS: P0 5/5, P1 14/14, P2 13/13, P3 13/13; {result['version']}; SHA-256 {result['sha256']}")
    return 0

if __name__=='__main__':raise SystemExit(main())
