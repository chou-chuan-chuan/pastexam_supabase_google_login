#!/usr/bin/env python3
"""Measure scalar kana/Han proportions; external fonts never enter the build."""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
from statistics import median
import subprocess

from fontTools.ttLib import TTFont
from measure_hiragana_reference_metrics import measure, URLS
from render_japanese_weight_proof import LYRICS

ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = 'e19227dbb31666e8373045a2edeb3456d00bd373'
FONT_REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
REFERENCE_PATH = ROOT / 'tools/font/references/kana-kanji-balance-metrics.json'
HIRAGANA = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
KATAKANA = ''.join(chr(ord(c) + 0x60) for c in HIRAGANA)
MIXED_LINES = (
    '君のかっこよさは鉄壁のシェイプじゃないところにだって',
    '今日はとてもいい天気ですね',
    '私は音楽を聴くのが好きです',
    '夜になったら家に帰ります',
    '東京で新しい映画を見ました',
    '優しい人になりたい',
)
# Verbatim existing render_proof.py Chinese/Japanese alignment fixtures.
CHINESE_JAPANESE_LINES = (
    '平仮名 ひらがな　片仮名 カタカナ',
    '君の声　愛のストーリー　夢の中',
    '中文日本語對齊　あいうえお アイウエオ',
    '平あ仮ア名な片カ　春の風が吹いている',
)
CALIBRATION_LINES = MIXED_LINES + LYRICS + CHINESE_JAPANESE_LINES
HAN = ''.join(dict.fromkeys(c for line in CALIBRATION_LINES for c in line if 0x4E00 <= ord(c) <= 0x9FFF))
GROUPS = {'han': HAN, 'hiragana': HIRAGANA, 'katakana': KATAKANA}


def measure_groups(font):
    result = {}
    for group, characters in GROUPS.items():
        glyphs = {c: measure(font, c) for c in characters}
        for row in glyphs.values():
            row['bbox_area_em2'] = row['width_em'] * row['height_em']
        result[group] = {
            'glyphs': glyphs,
            'median': {k: median(r[k] for r in glyphs.values()) for k in
                       ('height_em', 'width_em', 'bbox_area_em2', 'center_y_em')},
        }
    han = result['han']['median']
    for group in ('hiragana', 'katakana'):
        metrics = result[group]['median']
        result[group]['relative_to_han'] = {
            k: metrics[k] / han[k] for k in ('height_em', 'width_em', 'bbox_area_em2')
        }
        result[group]['relative_to_han']['center_y_delta_em'] = metrics['center_y_em'] - han['center_y_em']
    return result


def record(data, provenance):
    with TTFont(BytesIO(data)) as font:
        return {
            'family': font['name'].getDebugName(1), 'version': font['name'].getDebugName(5),
            'upm': font['head'].unitsPerEm, 'sha256': hashlib.sha256(data).hexdigest(),
            'provenance': provenance, 'groups': measure_groups(font),
        }


def factors(references):
    result = {}
    current = references['production_1_025']['groups']
    for script in ('hiragana', 'katakana'):
        standard = median(references[r]['groups'][script]['relative_to_han']['height_em']
                          for r in ('noto', 'source_han'))
        target = current['han']['median']['height_em'] * standard
        result[script] = {
            'standard_height_ratio': standard, 'target_height_em': target,
            'scale': round(target / current[script]['median']['height_em'], 12),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--noto', type=Path, required=True)
    parser.add_argument('--source-han', type=Path, required=True)
    args = parser.parse_args()
    for path in (args.noto, args.source_han):
        if path.resolve().is_relative_to(ROOT):
            parser.error('External reference binaries must stay outside the repository')
    refs = {key: record(path.read_bytes(), URLS[key]) for key, path in
            (('noto', args.noto), ('source_han', args.source_han))}
    before = subprocess.check_output(['git', 'show', f'{BASE_MAIN}:{FONT_REL}'], cwd=ROOT)
    refs['production_1_025'] = record(before, f'{BASE_MAIN}:{FONT_REL}')
    result = {
        'schema': 1, 'base_main': BASE_MAIN, 'version': '1.026',
        'measurement': 'Exact ink bounds / UPM; center is bbox midpoint. Area is bounding-box area, not ink coverage.',
        'policy': 'Median height over each complete 46-kana script and the same unique Han sample. Median of the two external kana/Han ratios is one related reference family. QuanFangwei Han supplies absolute size. No contours retained.',
        'calibration_lines': CALIBRATION_LINES, 'samples': GROUPS,
        'references': refs, 'balance': factors(refs),
    }
    REFERENCE_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Han sample:', len(HAN), HAN)
    print(json.dumps(result['balance'], indent=2))
    print('Reference SHA256:', hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
