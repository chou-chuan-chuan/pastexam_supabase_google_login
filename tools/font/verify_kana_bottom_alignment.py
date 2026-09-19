#!/usr/bin/env python3
"""Pin 1.026 and prove 1.027 is exactly one kana-only integer Y translation.

Default execution repeats the canonical build and compares both output bytes.
Historical shape/scale verifiers remain responsible for their accepted stages.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from io import BytesIO
import json
import subprocess
import sys

from fontTools.ttLib import TTFont

from render_kana_bottom_alignment_proof import (
    ROOT, BASE_MAIN, FONT, REPORT, GROUPS, MARK_NAMES, MOVED_NAMES,
    MOVED_CHARACTERS, baseline_bytes, measure, measured_candidates,
)
from japanese.build_kana import (
    JAPANESE_BOTTOM_ALIGNMENT_SHIFT as DELTA, KANA_VERTICAL_SHIFT,
    JAPANESE_MARK_VERTICAL_SHIFT, DAKUTEN_ANCHOR, HANDAKUTEN_ANCHOR,
)
from kana_sources.han_balance import HIRAGANA_HAN_BALANCE_SCALE, KATAKANA_HAN_BALANCE_SCALE

BASE_TTF_SHA256 = 'ffc8732aebdc74f84d3776c932b7b3ec251a59001639945f8b22efea070fc346'
WOFF2 = FONT.with_suffix('.woff2')


def accepted_font():
    raw = baseline_bytes()
    assert hashlib.sha256(raw).hexdigest() == BASE_TTF_SHA256, 'Unexpected 1.026 baseline'
    return TTFont(BytesIO(raw))


def verify_sources():
    # Freeze the entire source/normalization/pressure tree, not just 46 names.
    roots = ['tools/font/kana_sources', 'tools/font/references',
             'tools/font/japanese/stroke_engine.py',
             'tools/font/japanese/user_japanese_overrides.py']
    paths = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', BASE_MAIN, '--', *roots], cwd=ROOT, text=True).splitlines()
    for path in paths:
        expected = subprocess.check_output(['git', 'show', f'{BASE_MAIN}:{path}'], cwd=ROOT)
        current = (ROOT/path).read_bytes()
        if (ROOT/path).suffix in {'.py', '.json', '.svg', '.md', '.txt', '.csv'}:
            current = current.replace(b'\r\n', b'\n')
        assert current == expected, ('Frozen source/reference changed', path)
    assert HIRAGANA_HAN_BALANCE_SCALE == 0.894078195335
    assert KATAKANA_HAN_BALANCE_SCALE == 0.946843040146
    assert (DELTA, KANA_VERTICAL_SHIFT, JAPANESE_MARK_VERTICAL_SHIFT) == (-56, -201, -176)
    assert DAKUTEN_ANCHOR == HANDAKUTEN_ANCHOR == (92, 759)
    print(f'PASS: {len(paths)} immutable source/reference files; all 46+46 basic kana, pressure, small derivation and 1.026 scales frozen')


def verify_metrics():
    with accepted_font() as old, TTFont(FONT) as new:
        before, after = measure(old), measure(new)
    raw_delta, candidates = measured_candidates(before)
    assert len(GROUPS['han']) == 59 and len(GROUPS['combined_kana']) == 92
    assert (before['han']['yMin'], before['hiragana']['yMin'], before['katakana']['yMin']) == (-14, 44.5, 41)
    assert raw_delta == -55.5 and candidates == (-64, -56, -48)
    assert DELTA == round(raw_delta) < 0
    assert after['han'] == before['han']
    for group in ('hiragana', 'katakana', 'combined_kana'):
        for key in ('yMin', 'yMax', 'center_y', 'bottom_min', 'bottom_max'):
            assert after[group][key] == before[group][key]+DELTA, (group, key)
        for key in ('height', 'width', 'count', 'characters'):
            assert after[group][key] == before[group][key], (group, key)
        assert after[group]['bottom_quartiles'] == [v+DELTA for v in before[group]['bottom_quartiles']]
    assert abs(after['combined_kana']['yMin']-after['han']['yMin']) <= .5
    report = json.loads(REPORT.read_text())
    assert report['base_main'] == BASE_MAIN and report['version'] == '1.027'
    assert report['before'] == before and report['after'] == after
    assert report['measured_delta'] == raw_delta and report['final_delta'] == DELTA
    assert report['candidate_deltas'] == list(candidates)
    for delta in candidates:
        expected = copy.deepcopy(before)
        for group in ('hiragana', 'katakana', 'combined_kana'):
            for key in ('yMin', 'yMax', 'center_y', 'bottom_min', 'bottom_max'):
                expected[group][key] += delta
            expected[group]['bottom_quartiles'] = [v+delta for v in expected[group]['bottom_quartiles']]
        assert report['candidates'][str(delta)] == expected, ('Candidate report', delta)
    print('PASS: 59-Han / 92-kana ink-bottom measurement, all three candidates, unchanged sizes and exact before/after report')


def verify_translation():
    from verify_kana_kanji_scale_balance import signature
    with accepted_font() as old, TTFont(FONT) as new, TTFont(WOFF2) as web:
        assert old.getGlyphOrder() == new.getGlyphOrder() == web.getGlyphOrder()
        assert old.getBestCmap() == new.getBestCmap() == web.getBestCmap()
        assert len(MOVED_NAMES) == 187 and len(MOVED_CHARACTERS) == 185
        assert old['hmtx'].metrics == new['hmtx'].metrics == web['hmtx'].metrics
        if 'vmtx' in old:
            assert old['vmtx'].metrics == new['vmtx'].metrics == web['vmtx'].metrics
        han_names = {n for cp,n in old.getBestCmap().items() if
                     0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x323AF}
        hashes = []
        changed = set()
        for name in new.getGlyphOrder():
            prior, current = signature(old,name), signature(new,name)
            assert current == signature(web,name), ('TTF/WOFF2 glyph parity',name)
            delta = DELTA if name in MOVED_NAMES else 0
            expected = (prior[0], tuple((x,y+delta) for x,y in prior[1]), *prior[2:])
            assert current == expected, ('Not an exact Y-only translation',name)
            if prior != current:
                changed.add(name)
            a,b = old['glyf'][name],new['glyf'][name]
            if hasattr(a,'xMin'):
                assert (b.xMin,b.yMin,b.xMax,b.yMax) == (a.xMin,a.yMin+delta,a.xMax,a.yMax+delta),name
            if name in han_names:
                assert prior == current, ('Han changed',name)
                hashes.append((name,hashlib.sha256(repr(current).encode()).hexdigest()))
        assert changed == MOVED_NAMES
        assert len(han_names) == 9344
        for table in ('hhea','OS/2','GSUB','GDEF'):
            assert old[table].compile(old) == new[table].compile(new) == web[table].compile(web),table
        # GPOS may change only the shared Japanese base/mark Y anchor values.
        expected_gpos = copy.deepcopy(old['GPOS'])
        matches = 0
        for lookup in expected_gpos.table.LookupList.Lookup:
            if lookup.LookupType != 4:
                continue
            for sub in lookup.SubTable:
                if set(sub.MarkCoverage.glyphs) == MARK_NAMES:
                    matches += 1
                    for record in sub.MarkArray.MarkRecord:
                        record.MarkAnchor.YCoordinate += DELTA
                    for record in sub.BaseArray.BaseRecord:
                        for anchor in record.BaseAnchor:
                            if anchor:
                                anchor.YCoordinate += DELTA
        assert matches == 1
        assert expected_gpos.compile(old) == new['GPOS'].compile(new) == web['GPOS'].compile(web)
        assert old['head'].unitsPerEm == new['head'].unitsPerEm == web['head'].unitsPerEm == 1024
        for font in (new,web):
            assert font['name'].getDebugName(5) == 'Version 1.027'
            assert abs(font['head'].fontRevision-1.027) < 1/65536
        for name in MOVED_NAMES:
            g = new['glyf'][name]
            assert g.yMin > max(new['hhea'].descent,-new['OS/2'].usWinDescent),name
            assert g.yMax < min(new['hhea'].ascent,new['OS/2'].usWinAscent),name
            if name not in MARK_NAMES:
                assert new['OS/2'].sTypoDescender < g.yMin < g.yMax < new['OS/2'].sTypoAscender,name
            # Downward motion reduces any existing standalone mark top overhang.
            assert g.yMax <= old['glyf'][name].yMax
        for c in 'ゃゅょャュョ':
            g = new['glyf'][f'uni{ord(c):04X}']
            assert (g.xMin,g.yMin) == (180,-32),c
        aggregate = hashlib.sha256(repr(hashes).encode()).hexdigest()
        print(f'PASS: {len(han_names)} unchanged Han hashes (including 壁/堅); aggregate {aggregate}')
        print('PASS: exactly 187 glyphs translated (0,-56); every point, contour, composite offset, advance, side bearing and width/height checked; all unrelated glyphs frozen')
        print('PASS: TTF/WOFF2 parity; unchanged global metrics/GSUB/GDEF; Japanese GPOS anchors move together; no new clipping')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-rebuild',action='store_true')
    args = parser.parse_args()
    verify_sources(); verify_metrics(); verify_translation()
    from verify_kana_kanji_scale_balance import verify_derivatives, verify_determinism
    verify_derivatives()
    if not args.skip_rebuild:
        verify_determinism()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
