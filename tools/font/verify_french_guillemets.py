#!/usr/bin/env python3
"""Verify source-only French guillemets, frozen existing glyphs, and rebuilds."""
from __future__ import annotations

import argparse
import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
import pathops
import uharfbuzz as hb

from render_french_guillemets_proof import SAMPLES, validate_coverage

ROOT = Path(__file__).resolve().parents[2]
FONT_REL = "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
TTF = ROOT / FONT_REL
WOFF2 = TTF.with_suffix(".woff2")
SOURCE = ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
REPORT = ROOT / "tools/font/reports/french-guillemets.json"
BASE_MAIN = "4a65b8be24216aa3cf5d23b9e2ba783c0b66090c"
BASE_HASHES = {
    "ttf": "3f55c6f6ab16bf5a070ec67bd88027ec595c50597ec68a3ae5f0c78fbc426f39",
    "woff2": "d7f4dcf5845ab5a06285e18da53eae623ca830a6b8f019f6757b31679834a739",
}
SOURCE_HASH = "1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db"
GUILLEMETS = {0xAB: "guillemotleft", 0xBB: "guillemotright"}
# Independent approved recipes: no import from the production builder.
RECIPES = {
    "guillemotleft": [("less", (.75, 0, 0, .75, -6, 43)), ("less", (.75, 0, 0, .75, 106, 43))],
    "guillemotright": [("greater", (.453125, -.4375, .2109375, .9375, -30, 7)), ("greater", (.453125, -.4375, .2109375, .9375, 91, 7))],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def baseline_bytes(extension="ttf"):
    relative = str(Path(FONT_REL).with_suffix("." + extension)).replace("\\", "/")
    raw = subprocess.check_output(["git", "show", f"{BASE_MAIN}:{relative}"], cwd=ROOT)
    assert digest(raw) == BASE_HASHES[extension], f"Pinned baseline {extension} changed"
    return raw


def signature(font, name):
    glyph = font["glyf"][name]
    coords, ends, flags = glyph.getCoordinates(font["glyf"])
    components = tuple(c.getComponentInfo() for c in glyph.components) if glyph.isComposite() else ()
    return (glyph.numberOfContours, tuple(coords), tuple(ends), bytes(flags), components,
            font["hmtx"][name], font["vmtx"][name] if "vmtx" in font else None)


def box(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    assert pen.bounds is not None, name
    return pen.bounds


def historical_cmap(font):
    """Exclude only the verified 1.031 extension from older regression oracles."""
    cmap = font.getBestCmap().copy()
    for cp, name in GUILLEMETS.items():
        assert cmap.pop(cp, None) == name
    return cmap


def historical_order(font):
    order = font.getGlyphOrder()
    assert order[-2:] == list(GUILLEMETS.values())
    return order[:-2]


def verify():
    assert digest(SOURCE.read_bytes()) == SOURCE_HASH
    baseline_bytes("woff2")
    with TTFont(BytesIO(baseline_bytes())) as old, TTFont(SOURCE) as source, TTFont(TTF) as new, TTFont(WOFF2) as web:
        assert old["name"].getDebugName(5) == "Version 1.030"
        for font in (source, old):
            assert all(cp not in font.getBestCmap() for cp in (0xAB, 0xBB, 0x2039, 0x203A))
        assert source.getBestCmap()[60] == "less" and source.getBestCmap()[62] == "greater"
        assert new.getGlyphOrder() == old.getGlyphOrder() + list(GUILLEMETS.values()) == web.getGlyphOrder()
        expected_cmap = old.getBestCmap() | GUILLEMETS
        assert new.getBestCmap() == web.getBestCmap() == expected_cmap
        for name in ("less", "greater"):
            assert signature(source, name) == signature(new, name), f"Authorized source {name} modified"
        metrics = {}
        for font in (new, web):
            assert font["name"].getDebugName(5) == "Version 1.031"
            assert abs(font["head"].fontRevision - 1.031) < 1 / 65536
            for table in font["cmap"].tables:
                if table.isUnicode() and table.format != 14:
                    assert all(table.cmap.get(cp) == name for cp, name in GUILLEMETS.items())
            for name, expected in RECIPES.items():
                glyph = font["glyf"][name]
                assert glyph.isComposite() and len(glyph.components) == 2
                assert [c.getComponentInfo() for c in glyph.components] == expected
                assert len(glyph.getCoordinates(font["glyf"])[1]) == 2, "Missing real contours"
                x0, y0, x1, y1 = box(font, name)
                advance, lsb = font["hmtx"][name]
                rsb = advance - lsb - (glyph.xMax - glyph.xMin)
                assert advance == 327 < 2 * source["hmtx"][expected[0][0]][0]
                assert 30 <= lsb <= 34 and 30 <= rsb <= 34
                assert abs(x0 - (advance - x1)) < 2
                assert abs((y0 + y1) / 2 - 290) < 1 and 250 < y1 - y0 < 259
                assert max(font["hhea"].descent, font["OS/2"].sTypoDescender, -font["OS/2"].usWinDescent) < y0
                assert y1 < min(font["hhea"].ascent, font["OS/2"].sTypoAscender, font["OS/2"].usWinAscent)
                paths = []
                for source_name, transform in expected:
                    path = pathops.Path()
                    source.getGlyphSet()[source_name].draw(TransformPen(path.getPen(), transform))
                    paths.append(path)
                assert not list(pathops.op(*paths, pathops.PathOp.INTERSECTION)), "Chevron contours overlap"
                metrics[name] = dict(bounds=[x0, y0, x1, y1], glyf_bounds=[glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax], advance=advance, lsb=lsb, rsb=rsb,
                                     ink_sidebearings=[x0, advance-x1], components=expected)
            a, b = (box(font, n) for n in GUILLEMETS.values())
            assert abs((a[2]-a[0]) - (b[2]-b[0])) < 1
            assert max(abs(a[i]-b[i]) for i in (1, 3)) < 4
        hashes = []
        for name in old.getGlyphOrder():
            before = signature(old, name)
            assert before == signature(new, name) == signature(web, name), f"Unrelated glyph changed: {name}"
            assert old["glyf"][name].compile(old["glyf"]) == new["glyf"][name].compile(new["glyf"]), f"Glyph bytes changed: {name}"
            hashes.append((name, digest(repr(before).encode())))
        for name in GUILLEMETS.values():
            assert signature(new, name) == signature(web, name)
        for tag in ("OS/2", "GSUB", "GPOS", "GDEF"):
            if tag in old:
                assert old[tag].compile(old) == new[tag].compile(new) == web[tag].compile(web), tag
        prior_vhea = copy.deepcopy(old["vhea"])
        assert new["vmtx"]["guillemotleft"][0] != new["vmtx"]["guillemotright"][0]
        prior_vhea.numberOfVMetrics = len(new.getGlyphOrder())
        assert prior_vhea.compile(old) == new["vhea"].compile(new) == web["vhea"].compile(web)
        prior_hhea = copy.deepcopy(old["hhea"])
        prior_hhea.numberOfHMetrics += 1
        assert prior_hhea.compile(old) == new["hhea"].compile(new) == web["hhea"].compile(web)
        for font in (new, web):
            raw = BytesIO()
            font.flavor = None
            font.save(raw, reorderTables=True)
            shaper = hb.Font(hb.Face(raw.getvalue()))
            for text in SAMPLES:
                buffer = hb.Buffer()
                buffer.add_str(text)
                buffer.guess_segment_properties()
                hb.shape(shaper, buffer)
                assert all(info.codepoint != 0 for info in buffer.glyph_infos), f".notdef in {text}"
                shaped_names = [font.getGlyphName(info.codepoint) for info in buffer.glyph_infos]
                assert shaped_names.count("guillemotleft") == text.count("«")
                assert shaped_names.count("guillemotright") == text.count("»")
        manifest = json.loads((ROOT / "tools/font/glyph_manifest.json").read_text(encoding="utf-8"))
        assert manifest["derived_font"]["version"] == "1.031"
        for name, recipe in RECIPES.items():
            entry = next(item for item in manifest["glyphs"] if item["glyph_name"] == name)
            assert entry["component_transforms"] == [list(transform) for _, transform in recipe]
            assert entry["source_glyphs"][0]["glyph_name"] == recipe[0][0]
        punctuation = {}
        for cp in (0x27, 0x22, 0x201C, 0x201D, 60, 62, 0x78, 0x61, 0x65):
            name = old.getBestCmap()[cp]
            bounds = box(old, name)
            advance, lsb = old["hmtx"][name]
            punctuation[f"U+{cp:04X}"] = dict(glyph=name, bounds=bounds, advance=advance, lsb=lsb, ink_rsb=advance-bounds[2])
        result = dict(version="1.031", previous_version="1.030", base_main=BASE_MAIN,
                      source_sha256=SOURCE_HASH, baseline_sha256=BASE_HASHES,
                      source_coverage={f"U+{cp:04X}": source.getBestCmap().get(cp) for cp in (0xAB,0xBB,0x2039,0x203A,60,62)},
                      original_ttf_woff2_guillemets="absent", glyphs=metrics, punctuation_reference=punctuation,
                      unchanged_glyph_count=len(hashes), unchanged_glyph_sha256=digest(repr(hashes).encode()),
                      cmap_ttf_woff2="native; no .notdef", renderer="Pillow/FreeType; generated TTF only; every character checked",
                      external_font_outlines=False)
    validate_coverage()
    print(f"PASS: both native TTF/WOFF2 guillemets use only original less/greater components")
    print(f"PASS: compact advances, balanced bearings/midline, separate contours, shaping without .notdef")
    print(f"PASS: all {result['unchanged_glyph_count']} existing glyphs/metrics and all layout tables unchanged")
    return result


def verify_determinism():
    before = [p.read_bytes() for p in (TTF, WOFF2)]
    result = subprocess.run([sys.executable, str(ROOT / "tools/font/build_supplement_font.py")], cwd=ROOT, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == [p.read_bytes() for p in (TTF, WOFF2)], "Non-deterministic canonical rebuild"
    print("PASS: byte-identical deterministic TTF/WOFF2 rebuild")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-rebuild", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    result = verify()
    if not args.skip_rebuild:
        verify_determinism()
    if args.write_report:
        result["deterministic_rebuild"] = not args.skip_rebuild
        result["output_sha256"] = {p.suffix[1:]: digest(p.read_bytes()) for p in (TTF, WOFF2)}
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
