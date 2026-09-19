#!/usr/bin/env python3
"""Measure U+8E0A against immutable 1.027 and its original source drawing."""
from __future__ import annotations

from io import BytesIO
import hashlib
from pathlib import Path
import subprocess

from fontTools.ttLib import TTFont
from japanese.user_japanese_overrides import (
    SourceOpticalTransform, centered_optical_transform, transformed_glyph,
    glyph_bounds, install, add_mapping,
)
from render_kana_bottom_alignment_proof import measure as measure_groups

ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = '38f441c2bc0e2380c3cd7c1bf4afda1df2f3bc2f'
FONT_REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF = ROOT/FONT_REL
WOFF2 = TTF.with_suffix('.woff2')
SOURCE = ROOT/'assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf'
BASE_SHA256 = 'c7a6d88f48fd7ee10b328851612526629492d60ec7df1d684568a19cfd019cb6'
SOURCE_SHA256 = '1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db'
SOURCE_NAME = 'uni8E0A'
DERIVED_NAME = 'uni8E0A.qfwJaOptical'
REPORT = ROOT/'tools/font/reports/kanji-odoru-optical-size.json'
PROOF = ROOT/'tools/font/proofs/quanfangwei-kanji-odoru-optical-size.png'
TEXTS = ('踊', '俯いたままで踊って', '就算低著頭，也跳起舞', '踊って', '踊る', '踊り',
         '漢 字 日 本 音 楽 踊 跳 足')


def baseline_bytes():
    raw = subprocess.check_output(['git','show',f'{BASE_MAIN}:{FONT_REL}'],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest() == BASE_SHA256
    return raw


def metrics(font, character='踊'):
    name = font.getBestCmap().get(ord(character))
    if name is None:
        return None
    box = glyph_bounds(font,name)
    advance,lsb = font['hmtx'][name]
    glyph = font['glyf'][name]
    return dict(glyph=name, advance=advance, bounds=list(box),
                width=box[2]-box[0], height=box[3]-box[1],
                center=[(box[0]+box[2])/2,(box[1]+box[3])/2],
                lsb=lsb, rsb=advance-lsb-(glyph.xMax-glyph.xMin),
                ink_sidebearings=[box[0],advance-box[2]])


def candidates(font):
    reference = measure_groups(font)['han']
    calculated = reference['height']/metrics(font)['height']
    return calculated, tuple(round(calculated+d,6) for d in (-.03,0,.03))


def transform_for(font, scale):
    old = metrics(font)
    han = measure_groups(font)['han']
    # Ink-center scaling; then center in the unchanged advance and set ink
    # bottom to the accepted Han median. Translation is applied after scaling.
    dx = old['advance']/2-old['center'][0]
    dy = han['yMin']-(old['center'][1]-old['height']*scale/2)
    return SourceOpticalTransform(scale,scale,dx,dy)


def candidate_font(scale):
    font = TTFont(BytesIO(baseline_bytes()),recalcTimestamp=False)
    transform = transform_for(font,scale)
    matrix = centered_optical_transform(glyph_bounds(font,SOURCE_NAME),transform)
    glyph = transformed_glyph(font,SOURCE_NAME,matrix)
    glyph.recalcBounds(font['glyf'])
    install(font,DERIVED_NAME,glyph,font['hmtx'][SOURCE_NAME][0],glyph.xMin,SOURCE_NAME)
    add_mapping(font,0x8E0A,DERIVED_NAME)
    return font
