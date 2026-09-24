#!/usr/bin/env python3
"""Verify the Version 1.029 scoped U+3069 voiced-base correction."""
from __future__ import annotations

import argparse
import copy
import hashlib
from io import BytesIO
import json

from fontTools.ttLib import TTFont
import uharfbuzz as hb

from japanese.build_kana import (
    DO_BASE_GLYPH, DO_BASE_SCALE, HIRAGANA_MARK_ANCHOR_Y_OFFSETS, KANA_ADVANCE,
)
from measure_do_base_clearance import (
    BASE_MAIN, CANDIDATE_SCALES, FINAL_SCALE, REPORT, TTF, WOFF2,
    baseline_bytes, baseline_hashes, derived_glyph, measure,
)
from verify_kana_kanji_scale_balance import signature, verify_determinism
from verify_supplement_font import bounds, harfbuzz_decomposed_positions, mark_to_base_anchors


def glyph_hash(font: TTFont, name: str) -> str:
    return hashlib.sha256(repr(signature(font, name)).encode()).hexdigest()


def shaped(font_path, text, remove_precomposed=False):
    raw = font_path.read_bytes()
    font = TTFont(BytesIO(raw), recalcTimestamp=False)
    if remove_precomposed:
        for table in font["cmap"].tables:
            if table.isUnicode() and hasattr(table, "cmap"):
                table.cmap.pop(0x3069, None)
        stream = BytesIO()
        font.flavor = None
        font.save(stream, reorderTables=True)
        raw = stream.getvalue()
    face = hb.Font(hb.Face(raw))
    face.scale = (1024, 1024)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(face, buffer, {"ccmp": True, "mark": True})
    return [
        (font.getGlyphName(info.codepoint), pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset)
        for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)
    ]


def verify():
    baseline_hashes()
    assert DO_BASE_SCALE == FINAL_SCALE == min(CANDIDATE_SCALES) == 0.94
    assert HIRAGANA_MARK_ANCHOR_Y_OFFSETS == {"て": 82}
    with TTFont(BytesIO(baseline_bytes())) as old, TTFont(TTF) as new, TTFont(WOFF2) as web:
        assert old["name"].getDebugName(5) == "Version 1.028"
        for font in (new, web):
            assert font["name"].getDebugName(5) == "Version 1.029"
            assert abs(font["head"].fontRevision - 1.029) < 1 / 65536
            assert font["head"].unitsPerEm == 1024

        assert old.getBestCmap() == new.getBestCmap() == web.getBestCmap()
        assert DO_BASE_GLYPH not in new.getBestCmap().values()
        expected_order = old.getGlyphOrder().copy()
        expected_order.insert(expected_order.index("uni304C"), DO_BASE_GLYPH)
        assert new.getGlyphOrder() == web.getGlyphOrder() == expected_order

        # Standalone U+3068 is the immutable 1.028 drawing and metrics.
        assert old.getBestCmap()[0x3068] == new.getBestCmap()[0x3068] == "uni3068"
        assert signature(old, "uni3068") == signature(new, "uni3068") == signature(web, "uni3068")
        assert glyph_hash(old, "uni3068") == glyph_hash(new, "uni3068")

        expected, transform = derived_glyph(old, FINAL_SCALE)
        expected.recalcBounds(old["glyf"])
        for font in (new, web):
            actual = font["glyf"][DO_BASE_GLYPH]
            assert actual.compile(font["glyf"]) == expected.compile(old["glyf"])
            assert font["hmtx"].metrics[DO_BASE_GLYPH][0] == KANA_ADVANCE
            assert bounds(font, DO_BASE_GLYPH) == (232, -14, 780, 578)
            assert bounds(font, DO_BASE_GLYPH)[1] == bounds(font, "uni3068")[1]
            for name in (DO_BASE_GLYPH, "uni3069"):
                x0, y0, x1, y1 = bounds(font, name)
                assert 0 <= x0 < x1 < KANA_ADVANCE
                assert max(font["hhea"].descent, font["OS/2"].sTypoDescender, -font["OS/2"].usWinDescent) < y0
                assert y1 < min(font["hhea"].ascent, font["OS/2"].sTypoAscender, font["OS/2"].usWinAscent)
        assert transform.xx == transform.yy == FINAL_SCALE and transform.xy == transform.yx == 0

        old_anchor = mark_to_base_anchors(old, "uni3099", "uni3068")[:2]
        for font in (new, web):
            assert mark_to_base_anchors(font, "uni3099", DO_BASE_GLYPH)[:2] == old_anchor
            parts = [part.getComponentInfo() for part in font["glyf"]["uni3069"].components]
            assert parts == [
                (DO_BASE_GLYPH, (1, 0, 0, 1, 0, 0)),
                ("uni3099", (1, 0, 0, 1, 708, -160)),
            ]
            assert font["hmtx"].metrics["uni3069"][0] == KANA_ADVANCE
            assert signature(font, DO_BASE_GLYPH) == signature(new, DO_BASE_GLYPH)
            assert signature(font, "uni3069") == signature(new, "uni3069")

        before, after = measure(old, "uni3068"), measure(new)
        assert not before["intersects"] and not after["intersects"]
        assert 20 < before["minimum_clearance"] < 21
        assert 54 < after["minimum_clearance"] < 55
        assert after["minimum_clearance"] > 1024 / 20
        assert before["dakuten_bounds"] == after["dakuten_bounds"] == [726, 575, 863, 663]
        assert before["dakuten_delta"] == after["dakuten_delta"] == [708, -160]
        assert after["bottom_alignment_difference"] == 0

        assert shaped(TTF, "と") == [("uni3068", 960, 0, 0, 0)]
        assert shaped(TTF, "と゚", True)[0][0] == "uni3068"
        default_precomposed = shaped(TTF, "ど")
        default_decomposed = shaped(TTF, "ど")
        assert default_precomposed == default_decomposed == [("uni3069", 960, 0, 0, 0)]
        for path in (TTF, WOFF2):
            forced = harfbuzz_decomposed_positions(path, 0x3068, 0x3099, 0x3069)
            assert forced == [
                (DO_BASE_GLYPH, 960, 0, 0, 0),
                ("uni3099", 0, 0, -252, -160),
            ], forced
            assert shaped(path, "ど", True) == forced

        changed = []
        for name in old.getGlyphOrder():
            if signature(old, name) != signature(new, name):
                changed.append(name)
            if name != "uni3069":
                assert signature(old, name) == signature(new, name) == signature(web, name), name
        assert changed == ["uni3069"]
        assert signature(old, "uni3099") == signature(new, "uni3099")
        assert signature(old, "uni3066") == signature(new, "uni3066")
        assert signature(old, "uni3067") == signature(new, "uni3067")

        kana_names = {name for cp, name in old.getBestCmap().items() if 0x3040 <= cp <= 0x30FF and cp != 0x3069}
        han_names = {name for cp, name in old.getBestCmap().items() if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x323AF}
        kana_digest = hashlib.sha256(repr([(n, glyph_hash(new, n)) for n in sorted(kana_names)]).encode()).hexdigest()
        han_digest = hashlib.sha256(repr([(n, glyph_hash(new, n)) for n in sorted(han_names)]).encode()).hexdigest()
        assert all(signature(old, n) == signature(new, n) == signature(web, n) for n in kana_names | han_names)

        # The existing て / で exception and all non-layout global tables stay fixed.
        assert mark_to_base_anchors(old, "uni3099", "uni3066") == mark_to_base_anchors(new, "uni3099", "uni3066")
        assert [c.getComponentInfo() for c in old["glyf"]["uni3067"].components] == [c.getComponentInfo() for c in new["glyf"]["uni3067"].components]
        for tag in ("OS/2", "hhea"):
            prior = copy.deepcopy(old[tag])
            if tag == "hhea":
                prior.numberOfHMetrics += 1
            assert prior.compile(old) == new[tag].compile(new) == web[tag].compile(web)

        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report["base_main"] == BASE_MAIN and report["version"] == "1.029"
        assert report["final_scale"] == FINAL_SCALE
        assert tuple(map(float, report["candidates"])) == CANDIDATE_SCALES
        assert report["current"] == {"body_scale": 1.0, **before}
        assert report["final"] == {"body_scale": FINAL_SCALE, **after}

        print(f"PASS: standalone と hash {glyph_hash(new, 'uni3068')} is identical to 1.028")
        print(f"PASS: ど helper {DO_BASE_GLYPH} uses uniform {FINAL_SCALE:.2f} scale, fixed bottom, 960 advance; clearance {before['minimum_clearance']:.6f} -> {after['minimum_clearance']:.6f}")
        print("PASS: dakuten outline/position unchanged; precomposed and forced decomposed paths are positionally equivalent")
        print(f"PASS: unchanged て/で; unrelated kana {len(kana_names)} digest {kana_digest}; Han {len(han_names)} digest {han_digest}")
        return {"kana_count": len(kana_names), "kana_sha256": kana_digest, "han_count": len(han_names), "han_sha256": han_digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-rebuild", action="store_true")
    args = parser.parse_args()
    verify()
    if not args.skip_rebuild:
        verify_determinism()


if __name__ == "__main__":
    main()
