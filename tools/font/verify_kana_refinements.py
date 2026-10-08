#!/usr/bin/env python3
"""Pin 1.035 and verify local マ/ス trims and ten handakuten translations in 1.036."""
import argparse
import copy
from functools import lru_cache
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

from fontTools.ttLib import TTFont
import pathops
from verify_sokuon_position import box, signature, shaper, shape

ROOT = Path(__file__).resolve().parents[2]
BASE = '9b61867b073f1f90bce11ba0996f68febf7c47da'
REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF = ROOT / REL
WOFF2 = TTF.with_suffix('.woff2')
REPORT = ROOT / 'tools/font/reports/kana-refinements.md'
HASHES = {'ttf': '30ca99dfa4e828c8088afb7487404c00d3e4c7f56bcd14389d7064a61e6c4ccc',
          'woff2': 'dc4643763538bbcc26139acb12dc5aced48060632f503e640bebcf0c2955b204'}
PATCHES = {'マ': (410, 105, 490, 180), 'ス': (490, 165, 535, 220)}
BOUNDS = {'マ': (198, 48, 768, 537), 'ス': (251, -15, 740, 549)}
REMOVED_AREAS = {'マ': (1800, 1820), 'ス': (460, 480)}
HANDAKUTEN = 'ぱぴぷぺぽパピプペポ'
HAND_DELTA = (16, 24)
HAND_MARKS = ('uni309A', 'uni309A.katakana')
SAMPLES = ('マ', 'ママ', 'マイク', 'マッチ', 'マニュアル', 'ス', 'スイス', 'ズーム', 'スズ', 'ヴァ ファ ティ トゥ', 'キャ キッ')


@lru_cache(maxsize=2)
def baseline_bytes(extension='ttf'):
    path = Path(REL).with_suffix('.' + extension).as_posix()
    raw = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest() == HASHES[extension]
    return raw


def path(font, name):
    result = pathops.Path()
    font.getGlyphSet()[name].draw(result.getPen())
    return result


def edges(font, name):
    points, ends, flags = font['glyf'][name].getCoordinates(font['glyf'])
    assert len(ends) == 1 and set(flags) == {1}, 'Expected one accepted polygon contour'
    points = list(points)
    return set(zip(points, points[1:] + points[:1]))


def check_handakuten(old, new):
    from measure_de_dakuten_clearance import segments, contour_distance
    expected_gpos = copy.deepcopy(old['GPOS'])
    seen = []
    for lookup in expected_gpos.table.LookupList.Lookup:
        if lookup.LookupType != 4:
            continue
        for sub in lookup.SubTable:
            for name, record in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
                if name in HAND_MARKS:
                    assert (record.MarkAnchor.XCoordinate, record.MarkAnchor.YCoordinate) == (92, 759)
                    record.MarkAnchor.XCoordinate -= HAND_DELTA[0]
                    record.MarkAnchor.YCoordinate -= HAND_DELTA[1]
                    seen.append(name)
    assert sorted(seen) == sorted(HAND_MARKS)
    assert expected_gpos.compile(old) == new['GPOS'].compile(new), 'Unrelated GPOS edit'
    gaps = {}
    for c in HANDAKUTEN:
        name = old.getBestCmap()[ord(c)]
        a = [p.getComponentInfo() for p in old['glyf'][name].components]
        b = [p.getComponentInfo() for p in new['glyf'][name].components]
        assert len(a) == len(b) == 2 and a[0] == b[0]
        mark, transform = a[1]
        assert mark in HAND_MARKS and transform[:4] == (1, 0, 0, 1)
        dx, dy = HAND_DELTA
        assert b[1] == (mark, (*transform[:4], transform[4]+dx, transform[5]+dy))
        assert old['hmtx'][name] == new['hmtx'][name] and new['hmtx'][name][0] == 960
        bb = box(new, name)
        assert 0 < bb[0] < bb[2] < 960
        assert new['hhea'].descent < bb[1] < bb[3] < new['hhea'].ascent
        body = segments(old, a[0][0])
        prior = contour_distance(body, segments(old, mark, transform[4:]))[0]
        after = contour_distance(body, segments(new, mark, b[1][1][4:]))[0]
        assert after > prior and after >= 51.2, (c, 'insufficient clearance', prior, after)
        gaps[c] = (prior, after)
    return gaps


def check_decomposed(old, new):
    # Remove only precomposed handakuten mappings to force native mark positioning.
    faces = []
    for font in (old, new):
        original = font['cmap']
        font['cmap'] = copy.deepcopy(original)
        for table in font['cmap'].tables:
            if table.isUnicode() and hasattr(table, 'cmap'):
                for c in HANDAKUTEN:
                    table.cmap.pop(ord(c), None)
        faces.append(shaper(font))
        font['cmap'] = original
    for c, base in zip(HANDAKUTEN, 'はひふへほハヒフヘホ'):
        a, b = [shape(font, face, base+'\u309a') for font, face in zip((old, new), faces)]
        assert len(a) == len(b) == 2 and a[0] == b[0]
        name, advance, ya, x, y = a[1]
        assert name in HAND_MARKS and (advance, ya) == (0, 0)
        assert b[1] == (name, 0, 0, x+HAND_DELTA[0], y+HAND_DELTA[1]), c
    for text in ('が ぎ ぐ げ ご ガ ギ グ ゲ ゴ ず ズ', 'は\u3099 ハ\u3099', '゜'):
        assert shape(old, faces[0], text) == shape(new, faces[1], text), text


def check_font(old, new):
    assert old['name'].getDebugName(5) == 'Version 1.035'
    assert new['name'].getDebugName(5) == 'Version 1.036'
    assert abs(new['head'].fontRevision - 1.036) < 1/65536
    assert old.getGlyphOrder() == new.getGlyphOrder()
    assert old.getBestCmap() == new.getBestCmap()
    bases = {old.getBestCmap()[ord(c)] for c in PATCHES}
    zu = old.getBestCmap()[ord('ズ')]
    hand_names = {old.getBestCmap()[ord(c)] for c in HANDAKUTEN}
    affected = bases | {zu} | hand_names
    for name in old.getGlyphOrder():
        assert old['hmtx'][name] == new['hmtx'][name], ('horizontal metric', name)
        assert old['vmtx'][name] == new['vmtx'][name], ('vertical metric', name)
        if name not in affected:
            assert signature(old, name) == signature(new, name), ('unrelated glyph', name)
        if name not in bases | hand_names:
            assert old['glyf'][name].compile(old['glyf']) == new['glyf'][name].compile(new['glyf']), name
    measurements = {}
    for c, patch in PATCHES.items():
        name = old.getBestCmap()[ord(c)]
        assert box(old, name) == box(new, name) == BOUNDS[c]
        assert old['hmtx'][name] == new['hmtx'][name] == (960, BOUNDS[c][0])
        changed_edges = edges(old, name) ^ edges(new, name)
        assert changed_edges
        # Every changed segment lies in the small junction patch; the rest is exact.
        for edge in changed_edges:
            for x, y in edge:
                assert patch[0] <= x <= patch[2] and patch[1] <= y <= patch[3], (c, 'nonlocal edit', edge)
        before, after = path(old, name), path(new, name)
        removed = pathops.op(before, after, pathops.PathOp.DIFFERENCE)
        added = pathops.op(after, before, pathops.PathOp.DIFFERENCE)
        assert REMOVED_AREAS[c][0] < removed.area < REMOVED_AREAS[c][1], (c, 'protrusion not removed', removed.area)
        assert added.area < 2, (c, 'unexpected added ink', added.area)
        assert old['glyf'][name].program.getBytecode() == new['glyf'][name].program.getBytecode()
        measurements[c] = (removed.area, added.area)
    assert box(old, zu) == box(new, zu)
    parts = [component.getComponentInfo() for component in new['glyf'][zu].components]
    assert parts == [component.getComponentInfo() for component in old['glyf'][zu].components]
    assert parts[0] == (old.getBestCmap()[ord('ス')], (1, 0, 0, 1, 0, 0))
    assert set(old.keys()) == set(new.keys())
    for tag in old.keys():
        if tag not in {'GlyphOrder', 'head', 'name', 'glyf', 'loca', 'GPOS'}:
            assert old[tag].compile(old) == new[tag].compile(new), ('unrelated table', tag)
    for field, value in vars(old['head']).items():
        if field not in {'fontRevision', 'checkSumAdjustment'}:
            expected = value | 0x800 if field == 'flags' and new.flavor == 'woff2' else value
            assert getattr(new['head'], field) == expected, field
    assert len(old['name'].names) == len(new['name'].names)
    for record in old['name'].names:
        actual = new['name'].getName(record.nameID, record.platformID, record.platEncID, record.langID)
        expected = record.toUnicode().replace('1.035', '1.036') if record.nameID in (3, 5) else record.toUnicode()
        assert actual.toUnicode() == expected
    return measurements, check_handakuten(old, new)


def restore_1_035_for_historical_checks(font):
    if font['name'].getDebugName(5) != 'Version 1.036':
        return
    with TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False) as old:
        check_font(old, font)
        for c in ''.join(PATCHES) + HANDAKUTEN:
            name = old.getBestCmap()[ord(c)]
            font['glyf'][name] = copy.deepcopy(old['glyf'][name])
        for tag in ('head', 'name', 'loca', 'GPOS'):
            font[tag] = copy.deepcopy(old[tag])
        if font.flavor == 'woff2':
            font['head'].flags |= 0x800
    if hasattr(font, '_quantum_shaper'):
        del font._quantum_shaper


def verify():
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--',
        'tools/font/kana_sources', 'tools/font/japanese', 'tools/font/references',
        'assets/fonts/chenyuluoyan'], cwd=ROOT, text=True).splitlines()
    for item in paths:
        assert (ROOT/item).read_bytes() == subprocess.check_output(['git', 'show', f'{BASE}:{item}'], cwd=ROOT), item
    baseline_bytes('woff2')
    with TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False) as old, TTFont(TTF, recalcTimestamp=False) as new, TTFont(WOFF2, recalcTimestamp=False) as web:
        measurements, gaps = check_font(old, new)
        check_font(old, web)
        for name in new.getGlyphOrder():
            assert signature(new, name) == signature(web, name), ('TTF/WOFF2 parity', name)
        faces = [shaper(f) for f in (old, new, web)]
        for sample in SAMPLES + tuple(HANDAKUTEN):
            results = [shape(f, face, sample) for f, face in zip((old, new, web), faces)]
            assert results[0] == results[1] == results[2], sample
            assert all(row[0] != '.notdef' for row in results[0]), sample
        check_decomposed(old, new)
        check_decomposed(old, web)
        manifest = json.loads((ROOT/'tools/font/glyph_manifest.json').read_text())
        assert manifest['derived_font']['version'] == '1.036'
        assert manifest['katakana_junction_refinement']['changed_bases'] == 'マス'
        assert manifest['handakuten_spacing']['translation'] == list(HAND_DELTA)
        count = len(old.getGlyphOrder())-13
    rows = []
    for c, (removed, added) in measurements.items():
        b = BOUNDS[c]
        rows.append(f'| {c} | `{b}` | {b[2]-b[0]} × {b[3]-b[1]} | 960 | `{PATCHES[c]}` | {removed:.6f} | {added:.6f} |')
    report = '\n'.join([
        '# Kana junction and handakuten refinements — Version 1.036', '',
        f'Baseline: `{BASE}` (Version 1.035).', '',
        'Remove the マ approach-stroke tail below-left of its crossing and the ス branch-start bump above-left of its junction. Clip only the protruding stroke end; unchanged supporting ink covers the cut. All accepted source center-lines and pressure values remain untouched.', '',
        '| Base | Unchanged final bounds | Unchanged size | Advance | Local change region | Removed area (units²) | Quantization addition (units²) |',
        '|---|---|---|---|---|---|---|', *rows, '',
        '- Both bases retain one contour, no holes or detached fragments, and their original 960-unit metrics.',
        '- Every changed outline segment stays within the listed junction patch; every edge outside it is identical. Added area from integer quantization is less than two square font units per glyph.',
        '- ズ inherits the corrected ス body through its unchanged composite. Dakuten outline, attachment, component bytes, overall bounds and metrics remain identical.',
        '- All ten handakuten attachments move by `(16,24)`. Both ring outlines remain bit-identical; their GPOS mark anchors move from `(92,759)` to `(76,735)` while all base anchors and dakuten remain unchanged.',
        '- Forced decomposed HarfBuzz shaping agrees with the precomposed component deltas for all ten forms; combining marks retain zero advance and bases retain 960.',
        f'- All {count} other glyphs retain bit-identical outline bytes and metrics, including the five 1.035 small vowels and ャュョッ.',
        '- All source drawings, script scales, pressure, global alignment and spacing remain unchanged. Only the two handakuten GPOS mark anchors change in the layout tables.',
        '- TTF/WOFF2 parity; unchanged sample shaping; byte-identical canonical rebuild required by the default verifier.', '',
        '[Junction before/after proof](../proofs/quanfangwei-katakana-junctions.png) · [Handakuten before/after proof](../proofs/quanfangwei-handakuten-spacing.png). Both include actual 20, 32, 64 and 192 px rendering.', '',
        '## Handakuten minimum ink clearance', '',
        '| Glyph | Before (units) | After (units) |', '|---|---|---|',
        *[f'| {c} | {a:.3f} | {b:.3f} |' for c, (a, b) in gaps.items()], '',
        'No external font outline, CSS/JS positioning workaround, SQL/migration or database change.', '',
    ])
    print('PASS: local マ/ス trims and ten handakuten translations; all other outlines/metrics frozen; native mark parity; deterministic scope')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-rebuild', action='store_true')
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()
    report = verify()
    if not args.skip_rebuild:
        before = [p.read_bytes() for p in (TTF, WOFF2)]
        subprocess.run([sys.executable, str(ROOT/'tools/font/build_supplement_font.py')], cwd=ROOT, check=True)
        assert before == [p.read_bytes() for p in (TTF, WOFF2)]
        print('PASS: byte-identical deterministic TTF/WOFF2 rebuild')
    if args.write_report:
        REPORT.write_text(report)
    else:
        assert REPORT.read_text() == report


if __name__ == '__main__':
    main()
