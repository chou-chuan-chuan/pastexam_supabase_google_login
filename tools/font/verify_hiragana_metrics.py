#!/usr/bin/env python3
"""Verify size targets without opening or embedding any external font."""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
from statistics import median
import subprocess

from fontTools.ttLib import TTFont
from kana_sources.hiragana_master_v2 import TARGETS
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS
from measure_hiragana_reference_metrics import measure, BASE_MAIN, FONT_REL

ROOT=Path(__file__).resolve().parents[2]
REFERENCE_PATH=ROOT/'tools/font/references/hiragana-metric-references.json'
TARGET_PATH=ROOT/'tools/font/references/hiragana-metric-targets.json'
FONT_PATH=ROOT/FONT_REL
EXPECTED_REFERENCE_HASH='c2c24d33caf3f62264ce028ab9651b5cbc44b0d0de4017b32668bb60833c3595'


def verify_metrics():
    raw=REFERENCE_PATH.read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(raw).hexdigest()==EXPECTED_REFERENCE_HASH,'Reference metric snapshot changed'
    data=json.loads(raw);refs=data['references'];fits=json.loads(TARGET_PATH.read_text())
    assert fits['reference_metrics_sha256']==EXPECTED_REFERENCE_HASH
    assert set(fits['glyphs'])==set(TARGETS)
    assert all(set(r['glyphs'])==set(TARGETS) for r in refs.values())
    assert refs['noto']['upm']==refs['source_han']['upm']==1000
    assert refs['production_1_024']['upm']==1024
    old_bytes=subprocess.check_output(['git','show',f'{BASE_MAIN}:{FONT_REL}'],cwd=ROOT)
    assert hashlib.sha256(old_bytes).hexdigest()==refs['production_1_024']['sha256']
    family={}
    with TTFont(BytesIO(old_bytes)) as old,TTFont(FONT_PATH) as new:
        assert new['head'].unitsPerEm==1024
        for c in TARGETS:
            prior=refs['production_1_024']['glyphs'][c]
            assert measure(old,c)==prior,(c,'immutable production measurements')
            record=fits['glyphs'][c];actual=measure(new,c)
            family[c]=actual
            assert vars(HIRAGANA_OPTICAL_TRANSFORMS[c])==record['transform'],(c,'reviewed uniform fit')
            assert record['transform']['scale_x'] is None and record['transform']['scale_y'] is None
            for key,tolerance in (('height_em',1.5/1024),('center_x_em',1/1024),('center_y_em',1/1024)):
                external=median(refs[r]['glyphs'][c][key] for r in ('noto','source_han'))
                target=median((external,prior[key]))
                assert record['target'][key]==target,(c,'UPM-normalized target')
                assert abs(actual[key]-target)<=tolerance,(c,key,'target deviation',actual[key]-target)
            for key,(lower,upper) in record['envelope'].items():
                assert lower<=actual[key]<=upper,(c,key,'outside reference envelope')
            assert actual['advance_em']==960/1024,(c,'full-width advance')
            assert all(abs(a-b)<=1 for a,b in zip(actual['bounds'],record['expected_rendered_bounds'])),(c,'rendered fit')
    median_height=median(m['height_em'] for m in family.values())
    median_width=median(m['width_em'] for m in family.values())
    flagged={c for c,m in family.items() if m['height_em']<.75*median_height or
             m['width_em']<.7*median_width or m['width_em']>1.4*median_width}
    assert flagged==set('うくりつへ'),('Unreviewed family size outliers',flagged)
    print('PASS: 46 UPM-normalized standard/production targets; uniform fits; height within 1.5 units and centers within 1 unit; full-width advances and width envelopes')
    print('PASS: family size gate; reviewed narrow う/く/り and shallow つ/へ retain handwriting and meet individual reference targets')


if __name__=='__main__':verify_metrics()
