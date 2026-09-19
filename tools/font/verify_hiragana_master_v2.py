#!/usr/bin/env python3
"""Verify immutable Master v2 sources and their current derived output.

Version 1.025 source/normalization manifests remain authoritative and unchanged.
Version 1.026 output is checked against that accepted stage through the shared
Han-balance contract, not against superseded absolute final-size targets.
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
from japanese.build_kana import bounds, base_anchor, DAKUTEN_ANCHOR, HANDAKUTEN_ANCHOR, HIRAGANA_MARK_ANCHOR_Y_OFFSETS
from japanese.user_japanese_overrides import SHARED_HAN_OPTICAL_TRANSFORMS, ALIGNMENT_REFERENCE_BOUNDS
from kana_sources.hiragana_master_v2 import MASTER_SOURCES, TARGETS, ROWS, REFERENCES, REFERENCE, NA_REFERENCE, NA_ROW
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED, MODERN_HIRAGANA_ORDER
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS
from kana_sources.full_data import (KANA_STROKES, COMPOSITES, scale, YOON_SMALL_KANA_OFFSETS,
                                    SMALL_HIRAGANA_OPTICAL_SHIFTS, VERSION_1_025_KANA_STROKES, VERSION_1_025_YOON_OFFSETS)

ROOT=Path(__file__).resolve().parents[2]
BASE_MAIN='d89ee8b2b5f4c858e5dade853972194892037f93'
FONT_REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF=ROOT/FONT_REL
WOFF2=TTF.with_suffix('.woff2')
MANIFEST=ROOT/'tools/font/references/hiragana-master-v2-manifest.json'
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
    assert len(TARGETS)==46 and set(MASTER_SOURCES)==set(TARGETS)==set(m['glyphs'])
    assert list(ROWS)==m['rows'] and MODERN_HIRAGANA_ORDER==TARGETS
    assert REFERENCES==m['references'] and set(REFERENCES)=={REFERENCE,NA_REFERENCE}
    for reference,expected_hash in REFERENCES.items():
        assert hashlib.sha256((ROOT/'tools/font/references'/reference).read_bytes()).hexdigest()==expected_hash,reference
    assert {c for c,s in MASTER_SOURCES.items() if s.reference==NA_REFERENCE}==set(NA_ROW)
    assert all(s.reference in REFERENCES for s in MASTER_SOURCES.values())
    assert not set(NA_ROW)&set(SMALL.values()),'No invented small na-row derivatives'
    for c in characters:
        source=USER_HANDWRITING_REFINED[c];record=m['glyphs'][c]
        assert digest(source)==record['source_sha256'],f'{c}: source hash'
        assert digest(source)!=record['old_source_sha256'],f'{c}: source was not replaced'
        assert source==MASTER_SOURCES[c].strokes(),f'{c}: master precedence'
        assert digest(MASTER_SOURCES[c])==record['recipe_sha256'],f'{c}: photo mapping/normalization'
        assert MASTER_SOURCES[c].reference==record['reference'],f'{c}: reference provenance'
        assert len(source)==record['new_branches'],f'{c}: branches'
        t=HIRAGANA_OPTICAL_TRANSFORMS[c]
        assert {'scale_x':t.scale,'scale_y':t.scale,'dx':t.dx,'dy':t.dy}==record['optical_transform'],f'{c}: stale optical transform'
        assert t.scale_x is None and t.scale_y is None,f'{c}: non-uniform distortion'
    katakana={c:digest(s) for c,s in VERSION_1_025_KANA_STROKES.items() if 0x30a1<=ord(c)<=0x30ff}
    assert katakana==m['baseline']['katakana'],'STOP: Katakana source/pressure/position drift'
    from verify_kanji_odoru_optical import verify_transform_record
    verify_transform_record()
    assert {c:vars(t) for c,t in SHARED_HAN_OPTICAL_TRANSFORMS.items() if c!='踊'}==m['baseline']['han_optical'],'Earlier Han transforms changed'
    assert tuple(m['baseline']['ke_alignment_reference_bounds'])==ALIGNMENT_REFERENCE_BOUNDS
    assert {c:list(v) for c,v in VERSION_1_025_YOON_OFFSETS.items()}==m['yoon_offsets']
    for c in 'ャュョ':
        assert list(VERSION_1_025_YOON_OFFSETS[c])==m['baseline']['yoon_offsets'][c]
    print('PASS: complete 46-glyph Master v2 source hashes/precedence; both reference hashes; accepted Katakana stage and Han preservation')


def verify_derivatives():
    from verify_kana_kanji_scale_balance import verify_derivatives as verify_current
    verify_current()


def verify_font_scope():
    from verify_kana_kanji_scale_balance import verify_font_scope as verify_current
    verify_current()


def verify_fidelity():
    from verify_kana_kanji_scale_balance import verify_shape_preservation as verify_current
    verify_current()


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
    from verify_hiragana_metrics import verify_metrics
    verify_metrics()
    if not args.skip_rebuild:verify_determinism()
    print('PASS: all required yoon pairs: '+' '.join(YOON))
    return 0

if __name__=='__main__':raise SystemExit(main())
