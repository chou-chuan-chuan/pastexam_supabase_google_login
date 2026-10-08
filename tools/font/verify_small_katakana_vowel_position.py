#!/usr/bin/env python3
"""Prove the five 1.035 translations against SHA-pinned 1.034 font/source data."""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import subprocess
import sys

from fontTools.ttLib import TTFont
from verify_sokuon_position import box, signature, shaper, shape

ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = 'c92e280b97b32c71ea17c0d974254761adc9a8ab'
FONT_REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF = ROOT / FONT_REL
WOFF2 = TTF.with_suffix('.woff2')
REPORT = ROOT / 'tools/font/reports/small-katakana-vowel-position.md'
BASE_HASHES = {
    'ttf': 'e902a5e108c8da8e0ea75939148c5f55df01d5399487d760fd94bd8d0647656c',
    'woff2': '15a21205d545b1d4e97162eae0a48f6b9430914ba8305be4ab497f01fd9b84c9',
}
# Independently measured from the immutable baseline, not production metadata.
TRANSLATIONS = {'ァ': (-98, -81), 'ィ': (-158, -79), 'ゥ': (-136, -55),
                'ェ': (-108, -107), 'ォ': (-116, -55)}
REFERENCES = 'ャュョッ'
SAMPLES = tuple('ヴァ ヴィ ヴェ ヴォ ファ フィ フェ フォ ウィ ウェ ウォ ティ ディ トゥ ドゥ シェ ジェ チェ ツァ ツィ ツェ ツォ クァ クィ クェ クォ グァ スィ ズィ ヴォイ ヴァイ ファッ フィル'.split())
REQUIRED = tuple('ヴァ ヴィ ヴェ ヴォ ファ フィ フェ フォ ティ トゥ ツァ ツォ'.split())
COMPARISONS = ('ャ　ュ　ョ　ッ', 'ァ　ィ　ゥ　ェ　ォ', 'キャ　キッ', 'ファ　フィ', 'ヴァ　ヴィ', 'ティ　トゥ')


def git_bytes(path):
    return subprocess.check_output(['git', 'show', f'{BASE_MAIN}:{path}'], cwd=ROOT)


@lru_cache(maxsize=2)
def baseline_bytes(extension='ttf'):
    raw = git_bytes(Path(FONT_REL).with_suffix('.' + extension).as_posix())
    assert hashlib.sha256(raw).hexdigest() == BASE_HASHES[extension]
    return raw


def without_small_vowel_source(raw):
    start = b'# BEGIN SMALL KATAKANA VOWEL POSITIONING 1.035\n'
    end = b'# END SMALL KATAKANA VOWEL POSITIONING 1.035\n\n'
    assert raw.count(start) == raw.count(end) == 1
    before, rest = raw.split(start)
    _, after = rest.split(end)
    return before + after


def verify_sources():
    from kana_sources import full_data as current
    relative = 'tools/font/kana_sources/full_data.py'
    original = git_bytes(relative)
    assert without_small_vowel_source((ROOT / relative).read_bytes()) == original
    previous = {}
    exec(compile(original, f'{BASE_MAIN}:{relative}', 'exec'), previous)
    assert current.SMALL_KATAKANA_VOWEL_OFFSETS == TRANSLATIONS
    for key in ('YOON_SMALL_KANA_OFFSETS', 'SOKUON_SMALL_KANA_OFFSETS'):
        assert getattr(current, key) == previous[key]
        assert not set(TRANSLATIONS) & set(getattr(current, key))
    assert current.KANA_STROKES.keys() == previous['KANA_STROKES'].keys()
    for c, strokes in previous['KANA_STROKES'].items():
        actual = current.KANA_STROKES[c]
        if c not in TRANSLATIONS:
            assert actual == strokes, (c, 'unrelated source changed')
            continue
        dx, dy = TRANSLATIONS[c]
        assert len(actual) == len(strokes)
        for a, b in zip(strokes, actual):
            assert (a.width, a.start_width, a.end_width, a.cap) == (b.width, b.start_width, b.end_width, b.cap)
            assert len(a.points) == len(b.points)
            for (x, y), (u, v) in zip(a.points, b.points):
                assert math.isclose(u, x + dx, abs_tol=1e-10)
                assert math.isclose(v, y + dy, abs_tol=1e-10)
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE_MAIN, '--',
        'tools/font/kana_sources', 'tools/font/japanese', 'tools/font/references',
        'assets/fonts/chenyuluoyan', 'tools/font/quantum_symbols.py',
        'tools/font/math_refinement.py'], cwd=ROOT, text=True).splitlines()
    for path in paths:
        if path != relative:
            assert (ROOT / path).read_bytes() == git_bytes(path), ('Frozen input changed', path)
    print('PASS: source topology/pressure/scale, other kana, reference offsets and global layers frozen')


def verify_translation(old, new, c):
    dx, dy = TRANSLATIONS[c]
    name = old.getBestCmap()[ord(c)]
    assert new.getBestCmap()[ord(c)] == name
    a, b = signature(old, name), signature(new, name)
    assert a[0] > 0 and not a[4]
    assert a[5][0] == 960
    assert b == (a[0], tuple((x + dx, y + dy) for x, y in a[1]), *a[2:5],
                 (960, a[5][1] + dx), a[6]), (c, 'not an exact point translation')
    assert old['glyf'][name].program.getBytecode() == new['glyf'][name].program.getBytecode()
    before, after = box(old, name), box(new, name)
    assert after == tuple(v + (dx if i % 2 == 0 else dy) for i, v in enumerate(before))
    assert (after[2]-after[0], after[3]-after[1]) == (before[2]-before[0], before[3]-before[1])
    assert after[:2] == (180, -32)
    # Optical ink center belongs to the cell's lower-left quadrant.
    assert (after[0]+after[2])/2 < 480 and (after[1]+after[3])/2 < 312
    assert 0 < after[0] < after[2] < 960
    assert max(new['hhea'].descent, new['OS/2'].sTypoDescender, -new['OS/2'].usWinDescent) < after[1]
    assert after[3] < min(new['hhea'].ascent, new['OS/2'].sTypoAscender, new['OS/2'].usWinAscent)
    return before, after


def check_font(old, new):
    from verify_kana_refinements import restore_1_035_for_historical_checks
    restore_1_035_for_historical_checks(new)
    assert old['name'].getDebugName(5) == 'Version 1.034'
    assert new['name'].getDebugName(5) == 'Version 1.035'
    assert abs(new['head'].fontRevision - 1.035) < 1 / 65536
    assert old.getGlyphOrder() == new.getGlyphOrder()
    assert old.getBestCmap() == new.getBestCmap()
    allowed = {old.getBestCmap()[ord(c)] for c in TRANSLATIONS}
    changed = set()
    for name in old.getGlyphOrder():
        if signature(old, name) != signature(new, name):
            changed.add(name)
        if name not in allowed:
            assert signature(old, name) == signature(new, name), ('Unrelated glyph drift', name)
            assert old['glyf'][name].compile(old['glyf']) == new['glyf'][name].compile(new['glyf']), name
    assert changed == allowed
    for c in TRANSLATIONS:
        verify_translation(old, new, c)
    assert set(old.keys()) == set(new.keys())
    # Every non-outline/offset/version table remains byte-identical, including MATH.
    for tag in old.keys():
        if tag not in {'GlyphOrder', 'head', 'name', 'glyf', 'loca', 'hmtx'}:
            assert old[tag].compile(old) == new[tag].compile(new), ('Unrelated table', tag)
    for field, value in vars(old['head']).items():
        if field not in {'checkSumAdjustment', 'fontRevision'}:
            # WOFF2 sets the lossless-transform flag, as did baseline WOFF2.
            expected = value | 0x800 if field == 'flags' and new.flavor == 'woff2' else value
            assert getattr(new['head'], field) == expected, ('head', field)
    assert len(old['name'].names) == len(new['name'].names)
    for record in old['name'].names:
        actual = new['name'].getName(record.nameID, record.platformID, record.platEncID, record.langID)
        expected = record.toUnicode().replace('1.034', '1.035') if record.nameID in (3, 5) else record.toUnicode()
        assert actual.toUnicode() == expected


def restore_1_034_for_historical_checks(font):
    """Validate all 1.035 changes, then undo only those changes in memory."""
    from verify_kana_refinements import restore_1_035_for_historical_checks
    restore_1_035_for_historical_checks(font)
    if font['name'].getDebugName(5) != 'Version 1.035':
        return
    with TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False) as old:
        check_font(old, font)
        for c in TRANSLATIONS:
            name = old.getBestCmap()[ord(c)]
            font['glyf'][name] = copy.deepcopy(old['glyf'][name])
            font['hmtx'][name] = old['hmtx'][name]
        for tag in ('head', 'name', 'loca'):
            font[tag] = copy.deepcopy(old[tag])
    if hasattr(font, '_quantum_shaper'):
        del font._quantum_shaper


def verify():
    verify_sources()
    baseline_bytes('woff2')
    with TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False) as old, TTFont(TTF, recalcTimestamp=False) as new, TTFont(WOFF2, recalcTimestamp=False) as web:
        check_font(old, new)
        check_font(old, web)
        for name in new.getGlyphOrder():
            assert signature(new, name) == signature(web, name), ('TTF/WOFF2 parity', name)
        references = {c: box(new, new.getBestCmap()[ord(c)]) for c in REFERENCES}
        assert {b[:2] for b in references.values()} == {(180, -32)}
        faces = [shaper(f) for f in (old, new, web)]
        for text in SAMPLES + COMPARISONS:
            results = [shape(f, face, text) for f, face in zip((old, new, web), faces)]
            assert results[0] == results[1] == results[2], text
            assert len(results[0]) == len(text), (text, 'unexpected ligature')
            for c, (name, advance, ya, x, y) in zip(text, results[0]):
                expected = old['hmtx'][old.getBestCmap()[ord(c)]][0] if c == '　' else 960
                assert name != '.notdef' and advance == expected and (ya, x, y) == (0, 0, 0), text
        manifest = json.loads((ROOT / 'tools/font/glyph_manifest.json').read_text())
        assert manifest['derived_font']['version'] == '1.036'
        layer = manifest['small_katakana_vowel_positioning']
        assert layer['translations'] == {c: list(v) for c, v in TRANSLATIONS.items()}
        assert layer['final_ink_anchor'] == [180, -32]
        rows = []
        for c, delta in TRANSLATIONS.items():
            a, b = verify_translation(old, new, c)
            rows.append(f'| {c} | `{a}` | `{b}` | {a[2]-a[0]} | {a[3]-a[1]} | `(0, 0)` | `{delta}` | {b[0]} | {b[1]} | 960 |')
        report = '\n'.join([
            '# Small Katakana vowel lower-left positioning — Version 1.035', '',
            f'Base main: `{BASE_MAIN}`. Previous version: 1.034. New version: 1.035.', '',
            '| Glyph | Old bounds | New bounds | Unchanged width | Unchanged height | Old local dx/dy | New local dx/dy | Final xMin | Final yMin | Advance |',
            '|---|---|---|---|---|---|---|---|---|---|', *rows, '',
            'Coordinates are final font units (UPM 1024, Y upward). Local offsets exclude the unchanged global -145 and -56 layers. Each offset is calculated separately after existing scale and pressure construction. No rescaling, outline redesign or stroke-weight change.', '',
            '## Unchanged positioning references', '',
            '| Glyph | Final ink bounds |', '|---|---|',
            *[f'| {c} | `{b}` |' for c, b in references.items()], '',
            'Accepted final lower-left target: **(180, -32)**. All five ink centers lie left of x=480 and below y=312 in identical 960 × 1024 cells (y=-200..824). Left clearance is 180 units; bottom cell clearance is 168 units. All glyphs are inside the unchanged font vertical metrics.', '',
            '## Regression evidence', '',
            f'- Pinned Version 1.034 TTF SHA-256: `{BASE_HASHES["ttf"]}`.',
            f'- Pinned Version 1.034 WOFF2 SHA-256: `{BASE_HASHES["woff2"]}`.',
            f'- Only five glyphs change; all {len(old.getGlyphOrder())-5} other glyphs have bit-identical outline bytes and identical horizontal/vertical metrics.',
            '- Every target point moves by exactly its expected delta. Contour count, endpoints, flags, instructions, width, height, pressure and 960-unit advance are preserved.',
            '- Large ア/イ/ウ/エ/オ, ャュョッ, all Hiragana (including small vowels and ゃゅょっ), ヮヵヶ, all marks, Han, Latin, French and quantum/math glyphs remain unchanged.',
            '- Source layers, global alignment/metrics and layout tables including MATH/GPOS/GSUB are unchanged. TTF/WOFF2 parity and no clipping verified.',
            '- Historical verifiers validate this exact delta before restoring the 1.034 oracle in memory; their previous assertions remain active.',
            '- Default verifier execution repeats the canonical build and requires byte-identical TTF/WOFF2 output.', '',
            '## Special-sound QA', '',
            'All examples shape identically before/after in TTF and WOFF2: no missing glyphs, ligatures, kerning tricks, negative spacing or changed text advances. Each kana keeps its separate 960-unit cell.', '',
            *[f'- `{text}`: PASS.' for text in SAMPLES], '',
            'Comparisons: ' + '; '.join(f'`{s}`' for s in COMPARISONS) + '.', '',
            '## Proofs', '',
            '- [Visible cells, centers, baseline and ink bounds](../proofs/quanfangwei-small-katakana-vowels-cell.png).',
            '- [Version 1.034 BEFORE / Version 1.035 AFTER at 20, 32, 64 and 192 px, all requested special sounds and family comparisons](../proofs/quanfangwei-small-katakana-vowels-before-after.png).', '',
            'No external font outline used. No CSS/JS workaround (only the existing font URL cache token is bumped). No SQL/migration or production database changes.', '',
        ])
    print('PASS: only ァィゥェォ translated; exact dimensions/topology/960 advances retained')
    print('PASS: all other glyph bytes/metrics and layout tables unchanged; TTF/WOFF2 parity; all 33 special-sound samples')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-rebuild', action='store_true')
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()
    report = verify()
    if not args.skip_rebuild:
        before = [p.read_bytes() for p in (TTF, WOFF2)]
        subprocess.run([sys.executable, str(ROOT / 'tools/font/build_supplement_font.py')], cwd=ROOT, check=True)
        assert before == [p.read_bytes() for p in (TTF, WOFF2)], 'Non-deterministic TTF/WOFF2 rebuild'
        print('PASS: byte-identical deterministic TTF/WOFF2 rebuild')
    if args.write_report:
        REPORT.write_text(report, encoding='utf-8')
    else:
        assert REPORT.read_text(encoding='utf-8') == report, 'Stale small-vowel metric report'


if __name__ == '__main__':
    main()
