#!/usr/bin/env python3
"""Gate fidelity against actual photos and isolate changes to eight source families."""

from io import BytesIO
import subprocess
import sys

from fontTools.ttLib import TTFont

from kana_sources.maintainer_photo_sources import PHOTO_SOURCES
from kana_sources.user_handwriting_refined import USER_HANDWRITING_REFINED
from kana_sources.user_handwriting_optical import HIRAGANA_OPTICAL_TRANSFORMS, OpticalTransform
from render_handwriting_fidelity_proof import ROOT, FONT, BEFORE_REVISION, before_font, masks, measurements

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPECTED_CHANGED = set("あいうおさきとりぁぃぅぉざぎどゔ")


def signature(font, name):
    glyph = font["glyf"][name]
    coordinates, endpoints, flags = glyph.getCoordinates(font["glyf"])
    return (glyph.numberOfContours, tuple(coordinates), tuple(endpoints), bytes(flags),
            font["hmtx"].metrics[name])


def main():
    old_bytes = before_font()
    old_sources = {}
    code = subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}",
        "show", f"{BEFORE_REVISION}:tools/font/kana_sources/user_handwriting_refined.py"], cwd=ROOT)
    exec(compile(code, "previous_PR_sources", "exec"), old_sources)
    for character, source in USER_HANDWRITING_REFINED.items():
        if character not in PHOTO_SOURCES:
            assert source == old_sources["USER_HANDWRITING_REFINED"][character], character
    for character in PHOTO_SOURCES:
        assert HIRAGANA_OPTICAL_TRANSFORMS[character] == OpticalTransform(), character
        ref, old, new = masks(character, old_bytes)
        previous, revised = measurements(ref, old), measurements(ref, new)
        # Independent raster references are the oracle, not a hash of generated data.
        # IoU measures ink overlap (including weight), not perceived similarity.
        assert revised["ink_iou"] >= .78, (character, revised)
        assert revised["ink_iou"] > previous["ink_iou"] + .15, (character, previous, revised)
        assert revised["mean_ink_distance_photo_px"] <= .12, (character, revised)
        print(f"PASS photo {character}: overlap {previous['ink_iou']:.1%} -> {revised['ink_iou']:.1%}")
    with TTFont(BytesIO(old_bytes)) as before, TTFont(FONT) as after, TTFont(FONT.with_suffix(".woff2")) as web:
        assert before.getBestCmap() == after.getBestCmap() == web.getBestCmap()
        assert before.getGlyphOrder() == after.getGlyphOrder() == web.getGlyphOrder()
        allowed_names = {after.getBestCmap()[ord(c)] for c in EXPECTED_CHANGED}
        changed_names = set()
        for name in after.getGlyphOrder():
            new_signature = signature(after, name)
            assert new_signature == signature(web, name), f"TTF/WOFF2 mismatch: {name}"
            if new_signature != signature(before, name):
                changed_names.add(name)
                assert name in allowed_names, f"Unrelated glyph drift: {name}"
        assert changed_names == allowed_names, (changed_names, allowed_names)
        for name in allowed_names:
            glyph = after["glyf"][name]
            assert after["hmtx"].metrics[name][0] == 960
            assert 0 <= glyph.xMin < glyph.xMax < 960
            assert after["hhea"].descent < glyph.yMin < glyph.yMax < after["hhea"].ascent
        for table, fields in (("hhea", ("ascent", "descent", "lineGap")),
                              ("OS/2", ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent"))):
            for field in fields:
                assert getattr(before[table], field) == getattr(after[table], field), field
    print("PASS: exactly eight bases + four small vowels + four voiced derivatives changed")
    print("PASS: all other outlines/metrics, す/ず, yōon, 壁/堅, and global line metrics unchanged")
    print("PASS: entire TTF/WOFF2 outline/metric parity; no clipping or advance changes")


if __name__ == "__main__":
    main()
