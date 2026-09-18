#!/usr/bin/env python3
"""Extract scalar metrics only from local Japanese reference fonts.

External font files stay outside the repository. This analysis tool writes
only bounding boxes, em ratios, metadata and hashes, never contours, curves,
components or point data. The canonical font builder never opens these fonts.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from kana_sources.hiragana_master_v2 import TARGETS

ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = 'd89ee8b2b5f4c858e5dade853972194892037f93'
FONT_REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
OUTPUT = ROOT / 'tools/font/references/hiragana-metric-references.json'
URLS = {
    'noto': 'https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf',
    'source_han': 'https://github.com/adobe-fonts/source-han-sans/blob/release/SubsetOTF/JP/SourceHanSansJP-Regular.otf',
}


def measure(font, character):
    """Optical box = actual ink bounds; optical center = box midpoint."""
    glyphs = font.getGlyphSet()
    name = font.getBestCmap()[ord(character)]
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    x0,y0,x1,y1 = pen.bounds
    upm = font['head'].unitsPerEm
    advance = font['hmtx'].metrics[name][0]
    return {
        'bounds': list(pen.bounds),
        'bounds_em': [v/upm for v in pen.bounds],
        'width_em': (x1-x0)/upm, 'height_em': (y1-y0)/upm,
        'center_x_em': (x0+x1)/(2*upm), 'center_y_em': (y0+y1)/(2*upm),
        'advance_em': advance/upm, 'width_cell': (x1-x0)/advance,
        'baseline_bottom_em': y0/upm, 'baseline_top_em': y1/upm,
    }


def record(data, provenance):
    with TTFont(BytesIO(data)) as font:
        return {
            'family': font['name'].getDebugName(1),
            'style': font['name'].getDebugName(2),
            'version': font['name'].getDebugName(5),
            'upm': font['head'].unitsPerEm,
            'sha256': hashlib.sha256(data).hexdigest(),
            'provenance': provenance,
            'glyphs': {c: measure(font,c) for c in TARGETS},
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--noto', type=Path, required=True)
    parser.add_argument('--source-han', type=Path, required=True)
    args = parser.parse_args()
    for path in (args.noto,args.source_han):
        if path.resolve().is_relative_to(ROOT):
            parser.error('External reference binaries must be outside the repository')
    references = {key:record(path.read_bytes(), URLS[key])
                  for key,path in (('noto',args.noto),('source_han',args.source_han))}
    old_bytes = subprocess.check_output(['git','show',f'{BASE_MAIN}:{FONT_REL}'],cwd=ROOT)
    references['production_1_024'] = record(old_bytes,f'{BASE_MAIN}:{FONT_REL}')
    max_difference = max(abs(references['noto']['glyphs'][c][k]-references['source_han']['glyphs'][c][k])
                         for c in TARGETS for k in ('width_em','height_em','center_x_em','center_y_em'))
    result = {
        'schema': 1,
        'measurement': 'Actual ink bounding box and its midpoint, normalized by each font UPM; no outline data retained.',
        'references': references,
        'external_max_metric_difference_em': max_difference,
        'external_family_policy': 'Noto/Source Han form one external metric group; their per-character median is combined with the independent production font, so related designs are not double-weighted.',
    }
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'Wrote scalar metrics for all {len(TARGETS)} Hiragana; external max difference = {max_difference:.6f} em')
    for key,value in references.items():print(key,value['family'],value['version'],'UPM',value['upm'],value['sha256'])


if __name__ == '__main__':main()
