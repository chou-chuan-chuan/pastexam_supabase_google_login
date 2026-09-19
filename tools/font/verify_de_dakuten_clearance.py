#!/usr/bin/env python3
"""Verify the only post-merge 1.027 change: scoped て / で mark clearance."""
from __future__ import annotations

import copy
import hashlib
from io import BytesIO
import json
import math

from fontTools.ttLib import TTFont
import uharfbuzz as hb

from measure_de_dakuten_clearance import (
    ROOT, FONT_REL, BASE_MAIN, BASE_TTF_SHA256, baseline_bytes,
    OLD_OFFSET, measure, offset_delta,
)
from japanese.build_kana import HIRAGANA_MARK_ANCHOR_Y_OFFSETS
from verify_kana_kanji_scale_balance import signature
from verify_supplement_font import harfbuzz_decomposed_positions

EXPECTED_OFFSET = 82
EXPECTED_RENDERED_DELTA = 58
TTF = ROOT/FONT_REL
WOFF2 = TTF.with_suffix('.woff2')


def adjust_te_anchor(gpos, delta):
    matches = 0
    for lookup in gpos.table.LookupList.Lookup:
        if lookup.LookupType == 4:
            for sub in lookup.SubTable:
                if 'uni3099' in sub.MarkCoverage.glyphs and 'uni3066' in sub.BaseCoverage.glyphs:
                    matches += 1
                    record = sub.BaseArray.BaseRecord[sub.BaseCoverage.glyphs.index('uni3066')]
                    for anchor in record.BaseAnchor:
                        if anchor:
                            anchor.YCoordinate += delta
    assert matches == 1


def verify():
    raw = baseline_bytes()
    assert hashlib.sha256(raw).hexdigest() == BASE_TTF_SHA256
    assert HIRAGANA_MARK_ANCHOR_Y_OFFSETS == {'て':EXPECTED_OFFSET}
    assert offset_delta(EXPECTED_OFFSET) == EXPECTED_RENDERED_DELTA
    with TTFont(BytesIO(raw)) as old, TTFont(TTF) as new, TTFont(WOFF2) as web:
        before,after = measure(old),measure(new)
        assert not before['intersects'] and before['minimum_clearance'] < 10
        assert not after['intersects']
        # A reviewed one-pixel gap at 20 px is 51.2 units. Allow >1 unit
        # contour/flattening margin, not an exact pixel or contour-point match.
        assert 50 <= after['minimum_clearance'] <= 60,after
        assert after['minimum_vertical_gap'][0] >= 65,after
        assert before['base_bounds'] == after['base_bounds'] == [230,-8,744,612]
        assert after['mark_bounds'] == [713,648,850,736]
        assert after['mark_delta'] == [695,-87]
        for neighbor in 'けせとへ':
            assert measure(old,neighbor) == measure(new,neighbor),neighbor

        assert old.getBestCmap() == new.getBestCmap() == web.getBestCmap()
        assert old.getGlyphOrder() == new.getGlyphOrder() == web.getGlyphOrder()
        changed=[]
        for name in old.getGlyphOrder():
            prior,current=signature(old,name),signature(new,name)
            assert current == signature(web,name),('TTF/WOFF2 mismatch',name)
            if prior != current:
                changed.append(name)
            if name == 'uni3067':
                expected=copy.deepcopy(old['glyf'][name])
                expected.components[1].y += EXPECTED_RENDERED_DELTA
                expected.recalcBounds(old['glyf'])
                assert expected.compile(old['glyf']) == new['glyf'][name].compile(new['glyf'])
            else:
                assert prior == current,('Unrelated glyph changed',name)
        assert changed == ['uni3067'],changed
        for table in ('hmtx','hhea','OS/2','GSUB','GDEF','name'):
            assert old[table].compile(old) == new[table].compile(new) == web[table].compile(web),table
        if 'vmtx' in old:
            assert old['vmtx'].metrics == new['vmtx'].metrics == web['vmtx'].metrics
        expected_gpos=copy.deepcopy(old['GPOS']);adjust_te_anchor(expected_gpos,EXPECTED_RENDERED_DELTA)
        assert expected_gpos.compile(old) == new['GPOS'].compile(new) == web['GPOS'].compile(web)
        for font in (old,new,web):
            assert font['name'].getDebugName(5) == 'Version 1.027'
            assert abs(font['head'].fontRevision-1.027) < 1/65536
            assert font['head'].unitsPerEm == 1024
        assert new['OS/2'].sTypoDescender < new['glyf']['uni3067'].yMin < new['glyf']['uni3067'].yMax < new['OS/2'].sTypoAscender

        parts=[p.getComponentInfo() for p in new['glyf']['uni3067'].components]
        assert parts == [('uni3066',(1,0,0,1,0,0)),('uni3099',(1,0,0,1,695,-87))]
        hbfont=hb.Font(hb.Face(TTF.read_bytes()));hbfont.scale=(1024,1024)
        for text in ('で','で'):
            buffer=hb.Buffer();buffer.add_str(text);buffer.guess_segment_properties();hb.shape(hbfont,buffer)
            assert [new.getGlyphName(i.codepoint) for i in buffer.glyph_infos] == ['uni3067']
            assert [p.x_advance for p in buffer.glyph_positions] == [960]
        for path in (TTF,WOFF2):
            positions=harfbuzz_decomposed_positions(path,0x3066,0x3099,0x3067)
            assert positions == [('uni3066',960,0,0,0),('uni3099',0,0,-265,-87)],positions
            assert (positions[0][1]+positions[1][3],positions[1][4]) == (695,-87)

        report=json.loads((ROOT/'tools/font/reports/de-dakuten-clearance.json').read_text())
        assert report['base_main'] == BASE_MAIN and report['version'] == '1.027'
        assert report['old_offset'] == OLD_OFFSET and report['new_offset'] == EXPECTED_OFFSET
        assert report['additional_source_offset'] == 65 and report['additional_rendered_y'] == EXPECTED_RENDERED_DELTA
        assert report['before'] == before and report['after'] == after
        assert report['previous_candidate']['offset'] == EXPECTED_OFFSET-1
        previous=measure(old,extra_y=offset_delta(EXPECTED_OFFSET-1))
        assert previous['minimum_clearance'] < report['target_gap'] <= after['minimum_clearance']
        for offset,metric in report['candidates'].items():
            actual=measure(old,extra_y=offset_delta(int(offset)))
            assert math.isclose(metric['minimum_clearance'],actual['minimum_clearance'],abs_tol=.05)
        print(f"PASS: old gap {before['minimum_clearance']:.6f} → {after['minimum_clearance']:.6f} units; local vertical gap {after['minimum_vertical_gap'][0]}; no touching/intersection")
        print('PASS: only uni3067 mark component and uni3066 GPOS base anchor change (+58 final Y); every other glyph/anchor/metric unchanged')
        print('PASS: unchanged て topology, global kana/mark placement, Han and version 1.027; TTF/WOFF2 and forced precomposed/decomposed parity')


if __name__=='__main__':
    verify()
