#!/usr/bin/env python3
"""Pin Version 1.031 and prove that 1.032 changes only two ink translations."""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import subprocess
import sys

from fontTools.ttLib import TTFont
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = '3a093edd962410d129c9955d2b28bddb0866070c'
FONT_REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
TTF = ROOT / FONT_REL
WOFF2 = TTF.with_suffix('.woff2')
REPORT = ROOT / 'tools/font/reports/sokuon-position.md'
BASE_HASHES = {
    'ttf': 'a035c9b19384eeef2ffb85b45face710cbb18bddf2b3825f3caf5032c89f57b7',
    'woff2': '5124866790745a283011661df3be14169d787a70d4408dd1de0fe4ff3adbdd1b',
}
# Independent measured expectations, never imported from production offsets.
TRANSLATIONS = {'っ': (-107, -138), 'ッ': (-155, -88)}
YOON = 'ゃゅょャュョ'
HIRAGANA_SAMPLES = ('さっか', 'ちょっと', 'もっと', 'きっと', 'ずっと', 'やった', 'あった', 'いっぱい', 'まって', 'だった', 'きっかけ')
KATAKANA_SAMPLES = ('カップ', 'サッカー', 'ベッド', 'バッグ', 'チケット', 'ネット', 'ロック', 'ポップ', 'セット', 'スタッフ')
COMPARISONS = ('きゃ　きっ', 'しゃ　しっ', 'ちゃ　ちっ', 'キャ　キッ', 'シャ　シッ', 'チャ　チッ')


def git_bytes(path):
    return subprocess.check_output(['git', 'show', f'{BASE_MAIN}:{path}'], cwd=ROOT)


@lru_cache(maxsize=2)
def baseline_bytes(extension='ttf'):
    raw = git_bytes(str(Path(FONT_REL).with_suffix('.' + extension)))
    assert hashlib.sha256(raw).hexdigest() == BASE_HASHES[extension]
    return raw


def box(font, name):
    g = font['glyf'][name]
    g.recalcBounds(font['glyf'])
    return g.xMin, g.yMin, g.xMax, g.yMax


def signature(font, name):
    g = font['glyf'][name]
    coordinates, ends, flags = g.getCoordinates(font['glyf'])
    parts = tuple(c.getComponentInfo() for c in g.components) if g.isComposite() else ()
    return (g.numberOfContours, tuple(coordinates), tuple(ends), bytes(flags), parts,
            font['hmtx'][name], font['vmtx'][name] if 'vmtx' in font else None)


def verify_translation(old, new, character):
    dx, dy = TRANSLATIONS[character]
    name = old.getBestCmap()[ord(character)]
    assert new.getBestCmap()[ord(character)] == name
    a, b = signature(old, name), signature(new, name)
    assert a[0] > 0 and not a[4], 'Expected a simple accepted small form'
    assert b == (a[0], tuple((x + dx, y + dy) for x, y in a[1]), *a[2:5],
                 (960, a[5][1] + dx), a[6]), (character, 'not translation-only')
    assert a[5][0] == 960
    before, after = box(old, name), box(new, name)
    assert after == tuple(v + (dx if i % 2 == 0 else dy) for i, v in enumerate(before))
    assert (after[2] - after[0], after[3] - after[1]) == (before[2] - before[0], before[3] - before[1])
    assert after[:2] == (180, -32)
    assert 0 < after[0] < after[2] < 960
    assert max(new['hhea'].descent, new['OS/2'].sTypoDescender, -new['OS/2'].usWinDescent) < after[1]
    assert after[3] < min(new['hhea'].ascent, new['OS/2'].sTypoAscender, new['OS/2'].usWinAscent)
    return before, after


def restore_1_031_sokuon(font):
    """Validate the exact new delta, then undo it in an in-memory old-stage oracle.

    Historical gates retain all original assertions instead of exempting glyphs.
    Never used by production, the new verifier, or proof rendering.
    """
    from verify_quantum_symbols import restore_1_032_for_historical_checks
    restore_1_032_for_historical_checks(font)
    with TTFont(BytesIO(baseline_bytes())) as old:
        for c, (dx, dy) in TRANSLATIONS.items():
            verify_translation(old, font, c)
            name = font.getBestCmap()[ord(c)]
            font['glyf'][name].coordinates.translate((-dx, -dy))
            font['glyf'][name].recalcBounds(font['glyf'])
            advance, lsb = font['hmtx'][name]
            font['hmtx'][name] = (advance, lsb - dx)
            assert signature(old, name) == signature(font, name)


def without_sokuon_source(raw):
    start = b'# BEGIN SOKUON POSITIONING 1.032\n'
    end = b'# END SOKUON POSITIONING 1.032\n\n'
    assert raw.count(start) == raw.count(end) == 1
    before, rest = raw.split(start)
    _, after = rest.split(end)
    return before + after


def verify_sources():
    from kana_sources import full_data as current
    relative = 'tools/font/kana_sources/full_data.py'
    original = git_bytes(relative)
    assert without_sokuon_source((ROOT / relative).read_bytes()) == original
    previous = {}
    exec(compile(original, f'{BASE_MAIN}:{relative}', 'exec'), previous)
    assert current.SOKUON_SMALL_KANA_OFFSETS == TRANSLATIONS
    assert current.YOON_SMALL_KANA_OFFSETS == previous['YOON_SMALL_KANA_OFFSETS']
    assert not set(current.SOKUON_SMALL_KANA_OFFSETS) & set(current.YOON_SMALL_KANA_OFFSETS)
    assert current.KANA_STROKES.keys() == previous['KANA_STROKES'].keys()
    for c, strokes in previous['KANA_STROKES'].items():
        final = current.KANA_STROKES[c]
        if c not in TRANSLATIONS:
            assert final == strokes, (c, 'source changed')
            continue
        dx, dy = TRANSLATIONS[c]
        assert len(final) == len(strokes)
        for a, b in zip(strokes, final):
            assert (a.width, a.start_width, a.end_width, a.cap) == (b.width, b.start_width, b.end_width, b.cap)
            assert len(a.points) == len(b.points)
            for (x, y), (u, v) in zip(a.points, b.points):
                assert math.isclose(u, x + dx, abs_tol=1e-10)
                assert math.isclose(v, y + dy, abs_tol=1e-10)
    # Freeze global alignment, scale, topology, source outlines and references.
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE_MAIN, '--',
        'tools/font/kana_sources', 'tools/font/japanese', 'tools/font/references',
        'assets/fonts/chenyuluoyan'], cwd=ROOT, text=True).splitlines()
    for path in paths:
        if path != relative:
            assert (ROOT / path).read_bytes() == git_bytes(path), ('Frozen input changed', path)
    print('PASS: all large/other small kana sources, yoon offsets, pressure, topology and global layers unchanged')


def shaper(font):
    stream = BytesIO()
    font.flavor = None
    font.save(stream)
    face = hb.Font(hb.Face(stream.getvalue()))
    face.scale = (1024, 1024)
    return face


def shape(font, face, text):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(face, buf)
    return [(font.getGlyphName(i.codepoint), p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def verify():
    verify_sources()
    baseline_bytes('woff2')
    with TTFont(BytesIO(baseline_bytes()), recalcTimestamp=False) as old, TTFont(TTF, recalcTimestamp=False) as new, TTFont(WOFF2, recalcTimestamp=False) as web:
        from verify_quantum_symbols import restore_1_032_for_historical_checks
        restore_1_032_for_historical_checks(new)
        restore_1_032_for_historical_checks(web)
        assert old['name'].getDebugName(5) == 'Version 1.031'
        assert old.getGlyphOrder() == new.getGlyphOrder() == web.getGlyphOrder()
        assert old.getBestCmap() == new.getBestCmap() == web.getBestCmap()
        for font in (new, web):
            assert font['name'].getDebugName(5) == 'Version 1.032'
            assert abs(font['head'].fontRevision - 1.032) < 1 / 65536
            assert font['head'].unitsPerEm == old['head'].unitsPerEm == 1024
            for c in TRANSLATIONS:
                verify_translation(old, font, c)
        changed = {old.getBestCmap()[ord(c)] for c in TRANSLATIONS}
        for name in old.getGlyphOrder():
            assert signature(new, name) == signature(web, name), ('TTF/WOFF2 parity', name)
            if name not in changed:
                assert signature(old, name) == signature(new, name), ('Unrelated glyph', name)
                assert old['glyf'][name].compile(old['glyf']) == new['glyf'][name].compile(new['glyf']), name
        for tag in ('cmap', 'GSUB', 'GPOS', 'GDEF', 'kern', 'OS/2', 'hhea', 'vhea', 'vmtx'):
            assert (tag in old) == (tag in new) == (tag in web)
            if tag in old:
                assert old[tag].compile(old) == new[tag].compile(new) == web[tag].compile(web), tag
        for record in old['name'].names:
            for font in (new, web):
                actual = font['name'].getName(record.nameID, record.platformID, record.platEncID, record.langID)
                expected = record.toUnicode().replace('1.031', '1.032') if record.nameID in (3, 5) else record.toUnicode()
                assert actual.toUnicode() == expected
        references = {c: box(old, old.getBestCmap()[ord(c)]) for c in YOON}
        assert {b[:2] for b in references.values()} == {(180, -32)}
        old_face, new_face, web_face = (shaper(f) for f in (old, new, web))
        for text in HIRAGANA_SAMPLES + KATAKANA_SAMPLES + COMPARISONS:
            result = shape(old, old_face, text)
            assert result == shape(new, new_face, text) == shape(web, web_face, text), text
            assert len(result) == len(text), (text, 'unexpected ligature')
            for c, (n, advance, ya, x, y) in zip(text, result):
                expected_advance = old['hmtx'][old.getBestCmap()[ord(c)]][0] if c == '　' else 960
                assert n != '.notdef' and advance == expected_advance and (ya, x, y) == (0, 0, 0), text
        manifest = json.loads((ROOT / 'tools/font/glyph_manifest.json').read_text())
        assert manifest['derived_font']['version'] == '1.034'
        assert manifest['sokuon_positioning']['translations'] == {c: list(v) for c, v in TRANSLATIONS.items()}
        rows = []
        for c, (dx, dy) in TRANSLATIONS.items():
            before, after = verify_translation(old, new, c)
            rows.append(f'| {c} | `{before}` | `{after}` | {before[2]-before[0]} × {before[3]-before[1]} | `(0, 0)` | `({dx}, {dy})` | `(180, -32)` | 960 |')
        report = '\n'.join([
            '# Sokuon lower-left optical positioning — Version 1.032', '',
            f'Base main: `{BASE_MAIN}` (Version 1.031). Only post-construction integer x/y translation is applied.', '',
            '| Glyph | Old bounds | New bounds | Unchanged width × height | Old local dx/dy | New local dx/dy | Final xMin/yMin | Advance |',
            '|---|---|---|---|---|---|---|---|', *rows, '',
            'Bounds are final font units (UPM 1024; Y increases upward). Local offsets exclude the unchanged global -145 and -56 translations. No second shrinking, pressure change, redesign, kerning or ligature is applied.', '',
            '## Measured Version 1.031 yōon reference', '',
            '| Glyph | Final ink bounds | Anchor |', '|---|---|---|',
            *[f'| {c} | `{b}` | `(180, -32)` |' for c, b in references.items()], '',
            'Each sokuon translation is independently derived from its own accepted bounds and its script’s reviewed yōon anchor. The shared final anchor leaves 180 units of left clearance and remains inside the font’s vertical metrics. The different heights of the glyphs are preserved.', '',
            '## Verification', '',
            f'- Pinned baseline TTF SHA256: `{BASE_HASHES["ttf"]}`.',
            f'- Pinned baseline WOFF2 SHA256: `{BASE_HASHES["woff2"]}`.',
            f'- All {len(old.getGlyphOrder())-2} other glyphs retain identical outline bytes and horizontal/vertical metrics, including つ/ツ, all six yōon and all other small kana.',
            '- Every sokuon contour point moves by exactly its expected dx/dy; contour endpoints, flags, stroke widths, dimensions and advances remain unchanged.',
            '- TTF/WOFF2 glyph parity; unchanged cmap, layout and global metric tables; no clipping.',
            '- Every requested natural phrase and yōon comparison shapes identically before/after, with separate 960-unit kana cells, unchanged separator-space advances, no missing glyphs or pair adjustments.',
            '- Historical gates first validate and undo only these two exact translations in memory, preserving their existing regression assertions.',
            '- Run `python tools/font/verify_sokuon_position.py` for verification plus a byte-identical canonical rebuild.', '',
            '## Visual QA', '',
            '- [Visible cells, guides, baseline and ink bounds](../proofs/quanfangwei-sokuon-cell-position.png).',
            '- [Version 1.031 / 1.032 at 20, 32, 64 and 192 px; all natural phrases and yōon comparisons](../proofs/quanfangwei-sokuon-before-after.png).',
            '- Both small forms now share the reviewed lower-left anchor; full-size bases and surrounding glyph placement remain unchanged.', '',
            'No external font outline, CSS/JS workaround, SQL or migration. Production database untouched.', '',
        ])
    print('PASS: only っ (-107,-138) and ッ (-155,-88) translated; exact size/topology/960 advances preserved')
    print('PASS: all other glyph bytes/metrics, layout tables and requested sample shaping unchanged; TTF/WOFF2 parity')
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
        assert before == [p.read_bytes() for p in (TTF, WOFF2)], 'Non-deterministic rebuild'
        print('PASS: byte-identical deterministic TTF and WOFF2 rebuild')
    if args.write_report:
        REPORT.write_text(report, encoding='utf-8')
    else:
        assert REPORT.read_text(encoding='utf-8') == report, 'Stale sokuon metric report'


if __name__ == '__main__':
    main()
