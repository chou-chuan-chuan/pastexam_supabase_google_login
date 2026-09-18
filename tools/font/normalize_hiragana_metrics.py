#!/usr/bin/env python3
"""Fit current handwriting to reviewed, dimensionless Japanese size targets.

This offline authoring step reads scalar measurements only. It updates the
project's source-preserving optical transforms; it cannot read external fonts.
Run before the canonical build, then review proofs and pin the new manifest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from statistics import median

from fontTools.pens.boundsPen import BoundsPen
from japanese.stroke_engine import build_stroke_glyph, scale_stroke_weight, translate_strokes
from kana_sources.hiragana_master_v2 import TARGETS
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED
from kana_sources.user_handwriting_optical import OpticalTransform, transform_strokes

ROOT = Path(__file__).resolve().parents[2]
REFERENCES = ROOT/'tools/font/references/hiragana-metric-references.json'
TARGET_FILE = ROOT/'tools/font/references/hiragana-metric-targets.json'
UPM = 1024
ADVANCE = 960


def rendered_bounds(character, transform):
    strokes = transform_strokes(USER_HANDWRITING_REFINED[character], transform)
    glyph = build_stroke_glyph(translate_strokes(scale_stroke_weight(strokes,1.10),dy=-145))
    pen = BoundsPen(None)
    glyph.draw(pen,None)
    return tuple(round(v) for v in pen.bounds)


def targets(reference_data, character):
    refs=reference_data['references']
    external={k:median(refs[r]['glyphs'][character][k] for r in ('noto','source_han'))
              for k in ('width_em','height_em','center_x_em','center_y_em')}
    old=refs['production_1_024']['glyphs'][character]
    target={k:median((external[k],old[k])) for k in ('height_em','center_x_em','center_y_em')}
    envelope={
        'height_em':[target['height_em']*.95,target['height_em']*1.05],
        'width_em':[min(external['width_em'],old['width_em'])*.9,
                    min(max(external['width_em'],old['width_em'])*1.1,(ADVANCE-40)/UPM)],
        'center_x_em':[target['center_x_em']-.02,target['center_x_em']+.02],
        'center_y_em':[target['center_y_em']-.02,target['center_y_em']+.02],
    }
    return target,envelope


def fit(character, target, envelope):
    # Scale only center-lines. Pressure stays in the family renderer's units.
    # Search actual rendered bounds, since fixed pressure is not scaled ink.
    desired_height=target['height_em']*UPM
    lo,hi=.5,1.6
    for _ in range(17):
        scale=(lo+hi)/2
        b=rendered_bounds(character,OpticalTransform(scale))
        if b[3]-b[1]<desired_height:lo=scale
        else:hi=scale
    candidates=[round(lo,6),round(hi,6)]
    scale=min(candidates,key=lambda s:abs((lambda b:b[3]-b[1])(rendered_bounds(character,OpticalTransform(s)))-desired_height))
    b=rendered_bounds(character,OpticalTransform(scale))
    # Any width conflict must be reviewed, never silently distorted or cropped.
    assert envelope['width_em'][0] <= (b[2]-b[0])/UPM <= envelope['width_em'][1],(character,'width envelope')
    dx=round(target['center_x_em']*UPM-(b[0]+b[2])/2,4)
    dy=round(target['center_y_em']*UPM-(b[1]+b[3])/2,4)
    transform=OpticalTransform(scale,dx,dy)
    return transform,rendered_bounds(character,transform)


def main():
    raw=REFERENCES.read_bytes().replace(b'\r\n',b'\n');references=json.loads(raw)
    result={
        'version':'1.025', 'reference_metrics_sha256':hashlib.sha256(raw).hexdigest(),
        'upm':UPM, 'advance':ADVANCE,
        'method':'Median of one external Japanese metric group and immutable production 1.024 for height and box-center x/y. Width is a sanity envelope, not a target aspect ratio. Uniform center-line scale, fixed family pressure, then dx/dy.',
        'glyphs':{},
    }
    optical_path=ROOT/'tools/font/kana_sources/user_handwriting_optical.py'
    optical=optical_path.read_text()
    for character in TARGETS:
        target,envelope=targets(references,character)
        transform,bounds=fit(character,target,envelope)
        result['glyphs'][character]={'target':target,'envelope':envelope,
            'transform':vars(transform),'expected_rendered_bounds':bounds}
        replacement=f'"{character}": OpticalTransform({transform.scale}, {transform.dx}, {transform.dy}),'
        optical,count=re.subn(r'"'+character+r'": OpticalTransform\([^\n]*\),',replacement,optical)
        assert count==1,character
        print(character,transform,bounds,flush=True)
    optical=optical.replace('# Version 1.025: re-reviewed uniform photo fits need no additional transform.\n# All 46 sources, including the supplementary na-row, use freshly reviewed fits.',
        '# Version 1.025: uniform size/center fits from dimensionless standard Japanese\n# metrics and production 1.024. See references/hiragana-metric-targets.json.\n# These transforms preserve pen topology/aspect and do not scale pressure.')
    optical_path.write_text(optical)
    TARGET_FILE.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':main()
