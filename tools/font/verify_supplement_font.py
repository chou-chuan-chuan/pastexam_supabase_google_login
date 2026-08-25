#!/usr/bin/env python3
"""Verify the supplemental TTF/WOFF2, metadata, glyphs, and source preservation."""

from __future__ import annotations

import hashlib
import math
import sys
from io import BytesIO
from pathlib import Path
from statistics import median

import uharfbuzz as hb
from fontTools.misc.testTools import getXML
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from kana_sources.legibility_overrides import LEGIBLE_KANA
from kana_sources.full_data import HIRAGANA_BASE, KATAKANA_BASE, KANA_STROKES


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
SOURCE_LICENSE = REPO_ROOT / "assets/fonts/chenyuluoyan/license.txt"
OUTPUT_DIR = REPO_ROOT / "assets/fonts/quanfangwei-supplement"
TTF_PATH = OUTPUT_DIR / "QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = OUTPUT_DIR / "QuanFangweiSupplementScript-Regular.woff2"
OFL_PATH = OUTPUT_DIR / "OFL.txt"

FAMILY_EN = "QuanFangwei Supplement Script"
FAMILY_ZH = "荃方位補寫體"
FULL_EN = "QuanFangwei Supplement Script Regular"
FULL_ZH = "荃方位補寫體 Regular"
POSTSCRIPT_NAME = "QuanFangweiSupplementScript-Regular"
VERSION = "1.015"
UNIQUE_ID = "1.015;QFW;QuanFangweiSupplementScript-Regular;20260825"
SOURCE_SHA256 = "1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db"
CEDILLA_MARK_ANCHOR = (95, 91)
C_CEDILLA_BASE_ANCHOR = (221, 91)
C_LOWER_CEDILLA_BASE_ANCHOR = (176, 101)
DIAERESIS_MARK_ANCHOR = (145, 477)
UMLAUT_DATA = {
    0x00C4: (0x0041, "Adieresis", "A", (127, 145), (272, 622)),
    0x00D6: (0x004F, "Odieresis", "O", (90, 87), (235, 564)),
    0x00DC: (0x0055, "Udieresis", "U", (29, 88), (174, 565)),
    0x00E4: (0x0061, "adieresis", "a", (27, -13), (172, 464)),
    0x00F6: (0x006F, "odieresis", "o", (8, -57), (153, 420)),
    0x00FC: (0x0075, "udieresis", "u", (35, -62), (180, 415)),
}
HIRAGANA_REQUIRED = set(range(0x3041, 0x3097)) | {0x3099, 0x309A, 0x309B, 0x309C, 0x309D, 0x309E}
KATAKANA_REQUIRED = set(range(0x30A1, 0x30FB)) | {0x30FB, 0x30FC, 0x30FD, 0x30FE}
JAPANESE_PUNCTUATION_REQUIRED = {
    0x3000, 0x3001, 0x3002, 0x3005, 0x3006, 0x3007,
    *range(0x3008, 0x3012), 0x3014, 0x3015, 0x301C,
}
JAPANESE_REQUIRED = HIRAGANA_REQUIRED | KATAKANA_REQUIRED | JAPANESE_PUNCTUATION_REQUIRED
KANA_ADVANCE = 960
JAPANESE_SOURCE_CMAP_OVERRIDES = {
    0x3005, 0x4ED8, 0x512A, 0x54C0, 0x5967,
    0x5BC4, 0x604B, 0x61D0, 0x6C17,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text(path: Path) -> str:
    return "\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines())


def names(font: TTFont, name_id: int) -> set[str]:
    values = set()
    for record in font["name"].names:
        if record.nameID == name_id:
            try:
                values.add(record.toUnicode())
            except UnicodeDecodeError:
                pass
    return values


def bounds(font: TTFont, glyph_name: str):
    glyph_set = font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.bounds


def drawing(font: TTFont, glyph_name: str):
    pen = RecordingPen()
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.value


def contour_bounds(font: TTFont, glyph_name: str) -> list[tuple[int, int, int, int]]:
    glyph = font["glyf"][glyph_name]
    if glyph.isComposite():
        return []
    coordinates, end_points, _ = glyph.getCoordinates(font["glyf"])
    result = []
    start = 0
    for end in end_points:
        contour = coordinates[start : end + 1]
        xs = [point[0] for point in contour]
        ys = [point[1] for point in contour]
        result.append((min(xs), min(ys), max(xs), max(ys)))
        start = end + 1
    return result


def mark_to_base_anchors(font: TTFont, mark_name: str, base_name: str):
    """Return mark/base anchors and lookup index for one GPOS type-4 rule."""
    if "GPOS" not in font:
        return None
    for lookup_index, lookup in enumerate(font["GPOS"].table.LookupList.Lookup):
        if lookup.LookupType != 4:
            continue
        for subtable in lookup.SubTable:
            if mark_name not in subtable.MarkCoverage.glyphs or base_name not in subtable.BaseCoverage.glyphs:
                continue
            mark_index = subtable.MarkCoverage.glyphs.index(mark_name)
            base_index = subtable.BaseCoverage.glyphs.index(base_name)
            mark_record = subtable.MarkArray.MarkRecord[mark_index]
            base_anchor = subtable.BaseArray.BaseRecord[base_index].BaseAnchor[mark_record.Class]
            mark_anchor = mark_record.MarkAnchor
            return (
                (base_anchor.XCoordinate, base_anchor.YCoordinate),
                (mark_anchor.XCoordinate, mark_anchor.YCoordinate),
                lookup_index,
            )
    return None


def harfbuzz_decomposed_positions(path: Path, base_codepoint: int, mark_codepoint: int, precomposed_codepoint: int):
    """Force the decomposed path and return HarfBuzz glyph positions.

    HarfBuzz normally recomposes a base + U+0327 when the precomposed glyph is
    available. Removing only that cmap entry from an in-memory copy forces the
    engine to exercise this font's MarkBasePos lookup without changing output.
    """
    font = TTFont(path, recalcTimestamp=False)
    try:
        for subtable in font["cmap"].tables:
            if subtable.isUnicode() and hasattr(subtable, "cmap"):
                subtable.cmap.pop(precomposed_codepoint, None)
        buffer = BytesIO()
        font.flavor = None
        font.save(buffer, reorderTables=True)
        face = hb.Face(buffer.getvalue())
        hb_font = hb.Font(face)
        upm = font["head"].unitsPerEm
        hb_font.scale = (upm, upm)
        hb_buffer = hb.Buffer()
        hb_buffer.add_codepoints([base_codepoint, mark_codepoint])
        hb_buffer.guess_segment_properties()
        hb.shape(hb_font, hb_buffer, {"ccmp": False, "mark": True})
        return [
            (
                font.getGlyphName(info.codepoint),
                position.x_advance,
                position.y_advance,
                position.x_offset,
                position.y_offset,
            )
            for info, position in zip(hb_buffer.glyph_infos, hb_buffer.glyph_positions)
        ]
    finally:
        font.close()


def verify() -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for path in (SOURCE, SOURCE_LICENSE, TTF_PATH, WOFF2_PATH, OFL_PATH):
        require(path.is_file(), f"Missing required file: {path}")
    if errors:
        return errors

    require(sha256(SOURCE) == SOURCE_SHA256, "Official source TTF was modified")
    require(normalized_text(SOURCE_LICENSE) == normalized_text(OFL_PATH), "OFL.txt does not contain the complete source OFL license text")
    require(TTF_PATH.read_bytes()[:4] == b"\x00\x01\x00\x00", "TTF signature is invalid")
    require(WOFF2_PATH.read_bytes()[:4] == b"wOF2", "WOFF2 signature is invalid")

    try:
        source = TTFont(SOURCE, recalcTimestamp=False)
        ttf = TTFont(TTF_PATH, recalcTimestamp=False)
        woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    except Exception as error:
        errors.append(f"A font failed to open: {error}")
        return errors

    source_cmap = source.getBestCmap()
    ttf_cmap = ttf.getBestCmap()
    woff2_cmap = woff2.getBestCmap()
    required = {
        0x00A8: "dieresis",
        0x00BF: "questiondown",
        0x00C4: "Adieresis",
        0x00C7: "Ccedilla",
        0x00D6: "Odieresis",
        0x00DC: "Udieresis",
        0x00DF: "germandbls",
        0x00E4: "adieresis",
        0x00E7: "ccedilla",
        0x00F6: "odieresis",
        0x00FC: "udieresis",
        0x0308: "uni0308",
        0x0327: "uni0327",
        0x1E9E: "uni1E9E",
        **{codepoint: f"uni{codepoint:04X}" for codepoint in JAPANESE_REQUIRED if codepoint not in source_cmap},
    }
    # Version 1.014 intentionally replaces the Phase-1 U+3005 cmap target
    # with a dedicated, independently verifiable project-local drawing.
    required[0x3005] = "uni3005.qfwUser"
    for codepoint, glyph_name in required.items():
        require(ttf_cmap.get(codepoint) == glyph_name, f"TTF U+{codepoint:04X} does not map to {glyph_name}")
        require(woff2_cmap.get(codepoint) == glyph_name, f"WOFF2 U+{codepoint:04X} does not map to {glyph_name}")
        if glyph_name in ttf["glyf"].glyphs:
            glyph = ttf["glyf"][glyph_name]
            has_content = bool(glyph.components) if glyph.isComposite() else glyph.numberOfContours > 0
            require(has_content, f"TTF glyph {glyph_name} has no outline or components")
            glyph_bounds = bounds(ttf, glyph_name)
            require(glyph_bounds is not None, f"TTF glyph {glyph_name} has no bounds")
            if glyph_bounds:
                upm = ttf["head"].unitsPerEm
                require(all(-2 * upm <= value <= 3 * upm for value in glyph_bounds), f"TTF glyph {glyph_name} has extreme bounds {glyph_bounds}")
            advance, _ = ttf["hmtx"].metrics[glyph_name]
            if codepoint in (0x0308, 0x0327, 0x3099, 0x309A):
                require(advance == 0, f"TTF combining mark U+{codepoint:04X} advance must be zero, found {advance}")
            else:
                require(0 < advance < 2 * ttf["head"].unitsPerEm, f"TTF glyph {glyph_name} has unreasonable advance {advance}")
        else:
            errors.append(f"TTF glyf table is missing {glyph_name}")

    require(ttf_cmap.get(0x00B8) == "cedilla", "TTF supporting U+00B8 cedilla mapping is missing")
    require(woff2_cmap.get(0x00B8) == "cedilla", "WOFF2 supporting U+00B8 cedilla mapping is missing")
    if "Ccedilla" in ttf["glyf"].glyphs:
        ccedilla = ttf["glyf"]["Ccedilla"]
        components = [component.glyphName for component in ccedilla.components] if ccedilla.isComposite() else []
        require(components == ["C", "cedilla"], f"Ccedilla components are incorrect: {components}")
    if "ccedilla" in ttf["glyf"].glyphs:
        ccedilla = ttf["glyf"]["ccedilla"]
        components = [component.glyphName for component in ccedilla.components] if ccedilla.isComposite() else []
        require(components == ["c", "cedilla"], f"ccedilla components are incorrect: {components}")
    if "uni0327" in ttf["glyf"].glyphs:
        combining = ttf["glyf"]["uni0327"]
        component_info = [component.getComponentInfo() for component in combining.components] if combining.isComposite() else []
        require(
            component_info == [("cedilla", (1, 0, 0, 1, 0, 0))],
            f"uni0327 must share the cedilla outline by identity component: {component_info}",
        )
        require(ttf["GDEF"].table.GlyphClassDef.classDefs.get("uni0327") == 3, "uni0327 is not classified as a GDEF mark")

    if "dieresis" in ttf["glyf"].glyphs:
        spacing = ttf["glyf"]["dieresis"]
        component_info = [component.getComponentInfo() for component in spacing.components] if spacing.isComposite() else []
        require(component_info == [("uni0308", (1, 0, 0, 1, 0, 0))], f"dieresis must identity-reference uni0308: {component_info}")
        require(ttf["hmtx"].metrics["dieresis"] == (300, 60), f"dieresis spacing metrics are incorrect: {ttf['hmtx'].metrics['dieresis']}")
        require(bounds(ttf, "dieresis") == bounds(ttf, "uni0308"), "Spacing and combining diaeresis bounds differ despite identity component reuse")
    require(ttf["GDEF"].table.GlyphClassDef.classDefs.get("uni0308") == 3, "uni0308 source mark class was lost")
    for mark_name in ("uni3099", "uni309A"):
        require(ttf["hmtx"].metrics[mark_name][0] == 0, f"{mark_name} advance is not zero")
        require(ttf["GDEF"].table.GlyphClassDef.classDefs.get(mark_name) == 3, f"{mark_name} is not a GDEF mark")
    for spacing_name in ("uni309B", "uni309C"):
        require(ttf["hmtx"].metrics[spacing_name][0] > 0, f"{spacing_name} spacing advance must be positive")

    for codepoint in sorted(HIRAGANA_REQUIRED | KATAKANA_REQUIRED):
        glyph_name = ttf_cmap.get(codepoint)
        require(glyph_name is not None, f"Required Japanese code point U+{codepoint:04X} is missing")
        if glyph_name is None:
            continue
        glyph_bounds = bounds(ttf, glyph_name)
        require(glyph_bounds is not None, f"Japanese glyph {glyph_name} has no bounds")
        if glyph_bounds:
            require(ttf["hhea"].descent < glyph_bounds[1] < glyph_bounds[3] < ttf["hhea"].ascent,
                    f"Japanese glyph {glyph_name} clips vertical metrics: {glyph_bounds}")
            require(-80 <= glyph_bounds[0] and glyph_bounds[2] <= 1040,
                    f"Japanese glyph {glyph_name} has extreme horizontal bounds: {glyph_bounds}")
        advance = ttf["hmtx"].metrics[glyph_name][0]
        if codepoint in (0x3099, 0x309A):
            require(advance == 0, f"Combining Japanese mark U+{codepoint:04X} must have zero advance")
        elif codepoint in (0x309B, 0x309C):
            require(advance == 300, f"Spacing Japanese mark U+{codepoint:04X} must have 300 advance")
        else:
            require(advance == KANA_ADVANCE, f"Japanese glyph U+{codepoint:04X} has unexpected advance {advance}")
        require(ttf["hmtx"].metrics[glyph_name] == woff2["hmtx"].metrics[glyph_name],
                f"WOFF2 Japanese metrics differ for {glyph_name}")
        require(bounds(ttf, glyph_name) == bounds(woff2, glyph_name), f"WOFF2 Japanese bounds differ for {glyph_name}")

    def median_optical_center(characters: str) -> float:
        centers = []
        for character in characters:
            glyph_bounds = bounds(ttf, ttf_cmap[ord(character)])
            centers.append((glyph_bounds[1] + glyph_bounds[3]) / 2)
        return median(centers)

    han_alignment_sample = "平仮名片君愛声夢春心明日夜空"
    han_center = median_optical_center(han_alignment_sample)
    hiragana_center = median_optical_center(HIRAGANA_BASE)
    katakana_center = median_optical_center(KATAKANA_BASE)
    require(abs(hiragana_center - han_center) <= 35,
            f"Hiragana optical center floats relative to Chinese: hira={hiragana_center}, han={han_center}")
    require(abs(katakana_center - han_center) <= 35,
            f"Katakana optical center floats relative to Chinese: kata={katakana_center}, han={han_center}")

    no_points = [point for stroke in KANA_STROKES["の"] for point in stroke.points]
    no_x_values = [point[0] for point in no_points]
    no_y_values = [point[1] for point in no_points]
    require(max(no_x_values) - min(no_x_values) >= 300 and max(no_y_values) - min(no_y_values) >= 300,
            f"refined hiragana no needs a broad handwritten loop, found x={min(no_x_values)}..{max(no_x_values)} "
            f"y={min(no_y_values)}..{max(no_y_values)}")

    for character in ("シ", "ン"):
        start, end = LEGIBLE_KANA[character][-1].points[0], LEGIBLE_KANA[character][-1].points[-1]
        require(end[0] - start[0] >= 400 and end[1] - start[1] >= 450,
                f"{character} main stroke must rise clearly toward the right: {start} -> {end}")
    for character in ("ツ", "ソ"):
        start, end = LEGIBLE_KANA[character][-1].points[0], LEGIBLE_KANA[character][-1].points[-1]
        require(end[0] - start[0] <= -400 and end[1] - start[1] <= -500,
                f"{character} main stroke must fall clearly toward the left: {start} -> {end}")

    for base_cp, mark_cp, precomposed_cp in (
        (0x304B, 0x3099, 0x304C), (0x306F, 0x309A, 0x3071),
        (0x30AB, 0x3099, 0x30AC), (0x30CF, 0x309A, 0x30D1),
    ):
        base_name = ttf_cmap[base_cp]
        mark_name = ttf_cmap[mark_cp]
        precomposed_name = ttf_cmap[precomposed_cp]
        anchor_info = mark_to_base_anchors(ttf, mark_name, base_name)
        require(anchor_info is not None, f"GPOS has no rule for U+{base_cp:04X} + U+{mark_cp:04X}")
        glyph = ttf["glyf"][precomposed_name]
        components = [component.getComponentInfo() for component in glyph.components] if glyph.isComposite() else []
        require(len(components) == 2 and components[0][0] == base_name and components[1][0] == mark_name,
                f"{precomposed_name} does not share the reviewed base and mark components: {components}")
        if anchor_info and len(components) == 2:
            base_anchor, mark_anchor, _ = anchor_info
            delta = (base_anchor[0] - mark_anchor[0], base_anchor[1] - mark_anchor[1])
            require(components[1][1][4:6] == delta,
                    f"{precomposed_name} component delta differs from GPOS: {components[1][1][4:6]} vs {delta}")
            hb_positions = harfbuzz_decomposed_positions(TTF_PATH, base_cp, mark_cp, precomposed_cp)
            require(len(hb_positions) == 2 and hb_positions[0][0] == base_name and hb_positions[1][0] == mark_name,
                    f"HarfBuzz did not keep decomposed Japanese sequence: {hb_positions}")
            if len(hb_positions) == 2:
                mark_origin = hb_positions[0][1] + hb_positions[1][3]
                require((mark_origin, hb_positions[1][4]) == delta,
                        f"HarfBuzz mark origin differs from precomposed delta: {(mark_origin, hb_positions[1][4])} vs {delta}")
                require(sum(position[1] for position in hb_positions) == KANA_ADVANCE,
                        f"Decomposed Japanese advance differs from precomposed: {hb_positions}")

    # All six source Umlaut composites and their original base outlines remain
    # byte-for-byte/drawing-equivalent. Existing source GPOS anchors must make
    # the decomposed form land at the same component transform.
    for precomposed, (base_cp, glyph_name, base_name, delta, base_anchor) in UMLAUT_DATA.items():
        require(drawing(source, base_name) == drawing(ttf, base_name), f"Original {base_name} outline changed")
        require(drawing(source, "uni0308") == drawing(ttf, "uni0308"), "Original uni0308 outline changed")
        require(source["hmtx"].metrics[base_name] == ttf["hmtx"].metrics[base_name], f"Original {base_name} metrics changed")
        glyph = ttf["glyf"][glyph_name]
        components = [component.getComponentInfo() for component in glyph.components] if glyph.isComposite() else []
        expected_components = [(base_name, (1, 0, 0, 1, 0, 0)), ("uni0308", (1, 0, 0, 1, delta[0], delta[1]))]
        require(components == expected_components, f"{glyph_name} source composite changed: {components}")
        anchor_info = mark_to_base_anchors(ttf, "uni0308", base_name)
        require(anchor_info is not None, f"GPOS has no source rule for {base_name} + uni0308")
        if anchor_info:
            actual_base, actual_mark, _ = anchor_info
            require(actual_base == base_anchor, f"{base_name} diaeresis base anchor changed: {actual_base}")
            require(actual_mark == DIAERESIS_MARK_ANCHOR, f"uni0308 mark anchor changed for {base_name}: {actual_mark}")
            require((actual_base[0] - actual_mark[0], actual_base[1] - actual_mark[1]) == delta, f"{base_name}+uni0308 delta differs from {glyph_name}")
        hb_positions = harfbuzz_decomposed_positions(TTF_PATH, base_cp, 0x0308, precomposed)
        base_advance = ttf["hmtx"].metrics[base_name][0]
        expected_hb = [(base_name, base_advance, 0, 0, 0), ("uni0308", 0, 0, delta[0] - base_advance, delta[1])]
        require(hb_positions == expected_hb, f"HarfBuzz {base_name}+uni0308 shaping differs from {glyph_name}: {hb_positions}")

    expected_contours = {"germandbls": 1, "uni1E9E": 1}
    for glyph_name, minimum_height in (("germandbls", 700), ("uni1E9E", 540)):
        glyph = ttf["glyf"][glyph_name]
        require(not glyph.isComposite() and glyph.numberOfContours > 0, f"{glyph_name} must be a non-empty joined outline")
        require(glyph.numberOfContours == expected_contours[glyph_name], f"{glyph_name} has disconnected or sliver contours: {glyph.numberOfContours}")
        glyph_bounds = bounds(ttf, glyph_name)
        advance, lsb = ttf["hmtx"].metrics[glyph_name]
        require(glyph_bounds[3] - glyph_bounds[1] >= minimum_height, f"{glyph_name} is too short: {glyph_bounds}")
        require(0 <= lsb <= 80 and glyph_bounds[2] < advance + 30, f"{glyph_name} has unreasonable horizontal metrics: advance={advance}, lsb={lsb}, bounds={glyph_bounds}")
        require(ttf["hhea"].descent < glyph_bounds[1] < glyph_bounds[3] < ttf["hhea"].ascent, f"{glyph_name} is vertically clipped: {glyph_bounds}")
    require(drawing(ttf, "germandbls") != drawing(ttf, "B"), "germandbls incorrectly duplicates B")
    require(drawing(ttf, "uni1E9E") != drawing(ttf, "B"), "uni1E9E incorrectly duplicates B")
    if 0x03B2 in source_cmap:
        beta_name = source_cmap[0x03B2]
        require(drawing(ttf, "germandbls") == drawing(source, beta_name), "germandbls no longer reproduces the approved source beta handwriting")
        require(bounds(ttf, "germandbls") == bounds(source, beta_name), "germandbls bounds differ from the approved source beta")
        require(ttf["hmtx"].metrics["germandbls"] == (391, 50), "germandbls beta-like metrics are incorrect")
        require(bounds(ttf, "uni1E9E") == (55, 85, 375, 648), f"uni1E9E beta-like capital bounds are incorrect: {bounds(ttf, 'uni1E9E')}")
        require(ttf["hmtx"].metrics["uni1E9E"] == (430, 55), "uni1E9E beta-like capital metrics are incorrect")
        require(drawing(ttf, "uni1E9E") != drawing(ttf, beta_name), "uni1E9E must retain its capital optical transform")
        require(drawing(source, beta_name) == drawing(ttf, beta_name), "Original Greek beta changed")

    source_question = source_cmap.get(0x003F)
    source_c = source_cmap.get(0x0043)
    source_lower_c = source_cmap.get(0x0063)
    require(source_question is not None and drawing(source, source_question) == drawing(ttf, source_question), "Original question outline changed")
    require(source_c is not None and drawing(source, source_c) == drawing(ttf, source_c), "Original C outline changed")
    require(source_lower_c is not None and drawing(source, source_lower_c) == drawing(ttf, source_lower_c), "Original c outline changed")
    if source_question:
        source_question_bounds = bounds(source, source_question)
        inverted_bounds = bounds(ttf, "questiondown")
        question_advance = source["hmtx"].metrics[source_question][0]
        inverted_advance, inverted_lsb = ttf["hmtx"].metrics["questiondown"]
        inverted_rsb = inverted_advance - inverted_bounds[2]
        source_center = (source_question_bounds[0] + source_question_bounds[2]) / 2
        inverted_center = (inverted_bounds[0] + inverted_bounds[2]) / 2
        require(abs(inverted_advance - question_advance) <= max(16, question_advance * 0.05), "questiondown advance differs excessively from question")
        require(inverted_lsb >= 0 and inverted_rsb >= 0, f"questiondown has a negative side bearing: lsb={inverted_lsb}, rsb={inverted_rsb}")
        require(abs(inverted_lsb - inverted_rsb) <= 20, f"questiondown side bearings are optically unbalanced: lsb={inverted_lsb}, rsb={inverted_rsb}")
        require(abs(source_center - inverted_center) <= 12, f"questiondown visual-bounds center moved too far: source={source_center}, derived={inverted_center}")
        require(ttf["hhea"].descent < inverted_bounds[1] < inverted_bounds[3] < ttf["hhea"].ascent, f"questiondown is clipped by vertical metrics: {inverted_bounds}")
        question_contours = sorted(contour_bounds(ttf, "questiondown"), key=lambda item: (item[2] - item[0]) * (item[3] - item[1]), reverse=True)
        require(len(question_contours) == 2, f"questiondown should retain two source contours, found {len(question_contours)}")
        if len(question_contours) == 2:
            main, dot = question_contours
            dot_gap = dot[1] - main[3]
            require(35 <= dot_gap <= 100, f"questiondown dot-to-stroke gap is unreasonable: {dot_gap}")
            require(dot[1] > main[3], "questiondown dot collides with the main stroke")
    if source_c:
        c_bounds = bounds(source, source_c)
        c_advance, c_lsb = source["hmtx"].metrics[source_c]
        ccedilla_advance, ccedilla_lsb = ttf["hmtx"].metrics["Ccedilla"]
        cedilla_bounds = bounds(ttf, "cedilla")
        require(ccedilla_advance == c_advance, "Ccedilla advance differs from C")
        require(ccedilla_lsb == c_lsb, "Ccedilla left side bearing differs from C")
        require(ttf["hhea"].descent < bounds(ttf, "Ccedilla")[1], "Ccedilla extends beyond the safe descender")
        require(80 <= cedilla_bounds[2] - cedilla_bounds[0] <= 120, f"cedilla width is outside the optical range: {cedilla_bounds}")
        require(110 <= cedilla_bounds[3] - cedilla_bounds[1] <= 160, f"cedilla height is outside the optical range: {cedilla_bounds}")
        cedilla_advance, cedilla_lsb = ttf["hmtx"].metrics["cedilla"]
        require(cedilla_lsb >= 0 and cedilla_advance - cedilla_bounds[2] >= 0, "cedilla has a negative side bearing")
        if "Ccedilla" in ttf["glyf"].glyphs and ttf["glyf"]["Ccedilla"].isComposite():
            ccedilla = ttf["glyf"]["Ccedilla"]
            component_info = [component.getComponentInfo() for component in ccedilla.components]
            require(component_info[0] == ("C", (1, 0, 0, 1, 0, 0)), f"Ccedilla does not use the original C unchanged: {component_info[0]}")
            _, cedilla_transform = component_info[1]
            require(cedilla_transform[:4] == (1, 0, 0, 1), f"Ccedilla scales or distorts its cedilla component: {cedilla_transform}")
            placed_center = (cedilla_bounds[0] + cedilla_bounds[2]) / 2 + cedilla_transform[4]
            optical_c_center = (c_bounds[0] + c_bounds[2]) / 2 - (c_bounds[2] - c_bounds[0]) * 0.035
            require(abs(placed_center - optical_c_center) <= 10, f"cedilla is not aligned to C's optical center: {placed_center} vs {optical_c_center}")
            placed_top = cedilla_bounds[3] + cedilla_transform[5]
            gap = c_bounds[1] - placed_top
            require(16 <= gap <= 40, f"cedilla-to-C gap is outside the collision-safe range: {gap}")
            anchor_info = mark_to_base_anchors(ttf, "uni0327", source_c)
            require(anchor_info is not None, "GPOS has no mark-to-base rule for C + uni0327")
            if anchor_info:
                base_anchor, mark_anchor, lookup_index = anchor_info
                require(base_anchor == C_CEDILLA_BASE_ANCHOR, f"C base anchor is incorrect: {base_anchor}")
                require(mark_anchor == CEDILLA_MARK_ANCHOR, f"uni0327 mark anchor is incorrect: {mark_anchor}")
                mark_dx = base_anchor[0] - mark_anchor[0]
                mark_dy = base_anchor[1] - mark_anchor[1]
                require((mark_dx, mark_dy) == cedilla_transform[4:6], f"Decomposed positioning differs from Ccedilla: {(mark_dx, mark_dy)} vs {cedilla_transform[4:6]}")
                combining_bounds = bounds(ttf, "uni0327")
                decomposed_center = (combining_bounds[0] + combining_bounds[2]) / 2 + mark_dx
                decomposed_top = combining_bounds[3] + mark_dy
                decomposed_gap = c_bounds[1] - decomposed_top
                require(abs(decomposed_center - placed_center) <= 1, f"Decomposed cedilla center differs from Ccedilla: {decomposed_center} vs {placed_center}")
                require(abs(decomposed_gap - gap) <= 1, f"Decomposed cedilla gap differs from Ccedilla: {decomposed_gap} vs {gap}")
                require(decomposed_top < c_bounds[1], f"Combining cedilla collides with C: top={decomposed_top}, C bottom={c_bounds[1]}")
                require(ttf["hhea"].descent < combining_bounds[1] + mark_dy, f"Combining cedilla exceeds the safe descender: {combining_bounds}")
                mark_features = [record.Feature.LookupListIndex for record in ttf["GPOS"].table.FeatureList.FeatureRecord if record.FeatureTag == "mark"]
                require(any(lookup_index in indices for indices in mark_features), "Cedilla MarkBasePos lookup is not referenced by the mark feature")
    if source_lower_c:
        lower_c_bounds = bounds(source, source_lower_c)
        lower_c_advance, lower_c_lsb = source["hmtx"].metrics[source_lower_c]
        lower_ccedilla_advance, lower_ccedilla_lsb = ttf["hmtx"].metrics["ccedilla"]
        require(lower_ccedilla_advance == lower_c_advance, "ccedilla advance differs from c")
        require(lower_ccedilla_lsb == lower_c_lsb, "ccedilla left side bearing differs from c")
        require(ttf["hhea"].descent < bounds(ttf, "ccedilla")[1], "ccedilla extends beyond the safe descender")
        if "ccedilla" in ttf["glyf"].glyphs and ttf["glyf"]["ccedilla"].isComposite():
            lower_ccedilla = ttf["glyf"]["ccedilla"]
            lower_components = [component.getComponentInfo() for component in lower_ccedilla.components]
            require(lower_components[0] == ("c", (1, 0, 0, 1, 0, 0)), f"ccedilla does not use original c unchanged: {lower_components[0]}")
            _, lower_cedilla_transform = lower_components[1]
            require(lower_cedilla_transform == (1, 0, 0, 1, 81, 10), f"ccedilla cedilla transform is incorrect: {lower_cedilla_transform}")
            lower_placed_center = (cedilla_bounds[0] + cedilla_bounds[2]) / 2 + lower_cedilla_transform[4]
            lower_optical_center = (lower_c_bounds[0] + lower_c_bounds[2]) / 2 - (lower_c_bounds[2] - lower_c_bounds[0]) * 0.035
            require(abs(lower_placed_center - lower_optical_center) <= 10, f"cedilla is not aligned to c's optical center: {lower_placed_center} vs {lower_optical_center}")
            lower_placed_top = cedilla_bounds[3] + lower_cedilla_transform[5]
            lower_gap = lower_c_bounds[1] - lower_placed_top
            require(16 <= lower_gap <= 40, f"cedilla-to-c gap is outside the collision-safe range: {lower_gap}")
            lower_anchor_info = mark_to_base_anchors(ttf, "uni0327", source_lower_c)
            require(lower_anchor_info is not None, "GPOS has no mark-to-base rule for c + uni0327")
            if lower_anchor_info:
                lower_base_anchor, lower_mark_anchor, _ = lower_anchor_info
                require(lower_base_anchor == C_LOWER_CEDILLA_BASE_ANCHOR, f"c base anchor is incorrect: {lower_base_anchor}")
                require(lower_mark_anchor == CEDILLA_MARK_ANCHOR, f"uni0327 mark anchor is incorrect for c: {lower_mark_anchor}")
                lower_mark_delta = (
                    lower_base_anchor[0] - lower_mark_anchor[0],
                    lower_base_anchor[1] - lower_mark_anchor[1],
                )
                require(lower_mark_delta == lower_cedilla_transform[4:6], f"Decomposed lowercase positioning differs from ccedilla: {lower_mark_delta} vs {lower_cedilla_transform[4:6]}")
                combining_bounds = bounds(ttf, "uni0327")
                decomposed_lower_center = (combining_bounds[0] + combining_bounds[2]) / 2 + lower_mark_delta[0]
                decomposed_lower_gap = lower_c_bounds[1] - (combining_bounds[3] + lower_mark_delta[1])
                require(abs(decomposed_lower_center - lower_placed_center) <= 1, f"Decomposed lowercase cedilla center differs: {decomposed_lower_center} vs {lower_placed_center}")
                require(abs(decomposed_lower_gap - lower_gap) <= 1, f"Decomposed lowercase cedilla gap differs: {decomposed_lower_gap} vs {lower_gap}")
    require(not any(tag in ttf for tag in ("fpgm", "prep", "cvt ")), "Derived TTF still contains incompatible hint program tables")

    require(set(source_cmap).issubset(ttf_cmap), "One or more original cmap codepoints were removed")
    for codepoint, glyph_name in source_cmap.items():
        if codepoint in JAPANESE_SOURCE_CMAP_OVERRIDES:
            continue
        require(ttf_cmap.get(codepoint) == glyph_name, f"Original cmap mapping changed at U+{codepoint:04X}")
    require(ttf_cmap == woff2_cmap, "WOFF2 decoded cmap differs from TTF cmap")
    compared_glyphs = (
        "questiondown", "cedilla", "Ccedilla", "ccedilla", "uni0327",
        "dieresis", "uni0308", "Adieresis", "Odieresis", "Udieresis",
        "adieresis", "odieresis", "udieresis", "germandbls", "uni1E9E",
    )
    for glyph_name in compared_glyphs:
        require(bounds(ttf, glyph_name) == bounds(woff2, glyph_name), f"WOFF2 bounds differ from TTF for {glyph_name}")
        require(ttf["hmtx"].metrics[glyph_name] == woff2["hmtx"].metrics[glyph_name], f"WOFF2 metrics differ from TTF for {glyph_name}")
    require(mark_to_base_anchors(ttf, "uni0327", "C") == mark_to_base_anchors(woff2, "uni0327", "C"), "WOFF2 mark anchors differ from TTF")
    require(mark_to_base_anchors(ttf, "uni0327", "c") == mark_to_base_anchors(woff2, "uni0327", "c"), "WOFF2 lowercase mark anchors differ from TTF")
    for _, (_, _, base_name, _, _) in UMLAUT_DATA.items():
        require(mark_to_base_anchors(ttf, "uni0308", base_name) == mark_to_base_anchors(woff2, "uni0308", base_name), f"WOFF2 {base_name}/uni0308 anchors differ from TTF")
    source_order = source.getGlyphOrder()
    ttf_order = ttf.getGlyphOrder()
    require(ttf_order[: len(source_order)] == source_order, "Original glyph order or glyph set was altered")
    require(len(ttf_order) == len(source_order) + 204, "Derived glyph count did not increase by exactly 204")
    require(ttf_order == woff2.getGlyphOrder(), "WOFF2 glyph order differs from TTF")

    source_lookups = source["GPOS"].table.LookupList.Lookup
    derived_lookups = ttf["GPOS"].table.LookupList.Lookup
    require(len(derived_lookups) == len(source_lookups) + 2, "Derived GPOS should append exactly two lookups")
    for index, source_lookup in enumerate(source_lookups):
        require(getXML(source_lookup.toXML, source) == getXML(derived_lookups[index].toXML, ttf), f"Original GPOS lookup {index} changed")
    for glyph_name, glyph_class in source["GDEF"].table.GlyphClassDef.classDefs.items():
        require(ttf["GDEF"].table.GlyphClassDef.classDefs.get(glyph_name) == glyph_class, f"Original GDEF class changed for {glyph_name}")
    hb_positions = harfbuzz_decomposed_positions(TTF_PATH, 0x0043, 0x0327, 0x00C7)
    require(
        hb_positions == [("C", 471, 0, 0, 0), ("uni0327", 0, 0, -345, 0)],
        f"HarfBuzz decomposed shaping is incorrect: {hb_positions}",
    )
    lower_hb_positions = harfbuzz_decomposed_positions(TTF_PATH, 0x0063, 0x0327, 0x00E7)
    require(
        lower_hb_positions == [("c", 345, 0, 0, 0), ("uni0327", 0, 0, -264, 10)],
        f"HarfBuzz lowercase decomposed shaping is incorrect: {lower_hb_positions}",
    )

    require(FAMILY_EN in names(ttf, 1) and FAMILY_ZH in names(ttf, 1), "Family Name records are incomplete")
    require(FULL_EN in names(ttf, 4) and FULL_ZH in names(ttf, 4), "Full Name records are incomplete")
    require(names(ttf, 6) == {POSTSCRIPT_NAME}, "PostScript Name is incorrect")
    require(UNIQUE_ID in names(ttf, 3), "Unique ID is incorrect")
    require(f"Version {VERSION}" in names(ttf, 5), "Version name record is incorrect")
    require(FAMILY_EN in names(ttf, 16) and FAMILY_ZH in names(ttf, 16), "Typographic Family records are incomplete")
    require("Regular" in names(ttf, 17), "Typographic Subfamily record is missing")
    for name_id in (1, 4, 6, 16):
        joined = " ".join(names(ttf, name_id))
        require("辰宇落雁" not in joined and "chenyuluoyan" not in joined.lower(), f"Reserved Font Name appears in primary name ID {name_id}")

    license_text = " ".join(names(ttf, 13)).lower()
    license_url = " ".join(names(ttf, 14)).lower()
    require("open font license" in license_text or "ofl" in license_text, "OFL license metadata is missing")
    require("ofl" in license_url, "OFL license URL metadata is missing")

    require(ttf["head"].unitsPerEm == source["head"].unitsPerEm, "unitsPerEm changed")
    require((ttf["hhea"].ascent, ttf["hhea"].descent) == (source["hhea"].ascent, source["hhea"].descent), "hhea ascent/descent changed")
    source_os2 = source["OS/2"]
    ttf_os2 = ttf["OS/2"]
    source_metrics = (source_os2.sTypoAscender, source_os2.sTypoDescender, source_os2.usWinAscent, source_os2.usWinDescent)
    ttf_metrics = (ttf_os2.sTypoAscender, ttf_os2.sTypoDescender, ttf_os2.usWinAscent, ttf_os2.usWinDescent)
    require(ttf_metrics == source_metrics, "OS/2 vertical metrics changed")
    require(names(ttf, 1) == names(woff2, 1), "WOFF2 Family Name differs from TTF")
    require(names(ttf, 6) == names(woff2, 6), "WOFF2 PostScript Name differs from TTF")

    source.close()
    ttf.close()
    woff2.close()
    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"Verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("PASS: TTF and WOFF2 open successfully")
    print("PASS: cedilla and complete German cmap coverage map correctly in TTF and WOFF2")
    print("PASS: uni0327 has zero advance, shared cedilla outline, GDEF mark class, and GPOS C/c anchors")
    print("PASS: HarfBuzz shapes forced C/c + U+0327 at the matching +126/0 and +81/+10 mark origins")
    print("PASS: HarfBuzz shapes A/O/U/a/o/u + U+0308 at the source composed-glyph positions")
    print("PASS: U+00A8 shares uni0308 outlines; U+0308 has zero advance and preserved source GPOS")
    print("PASS: germandbls/uni1E9E use continuous beta-like source outlines with distinct German cmaps")
    print("PASS: complete Phase 1 Hiragana, Katakana, Japanese punctuation, and iteration marks are mapped")
    print("PASS: hiragana no and the shi/tsu/so/n directional pairs retain recognizable source geometry")
    print("PASS: Hiragana and Katakana optical centers align with the source Chinese sample")
    print("PASS: uni3099/uni309A have zero advance, GDEF mark class, and GPOS anchors matching precomposed kana")
    print("PASS: original cmap mappings are preserved except nine documented Japanese overrides; original glyph order remains a prefix")
    print("PASS: names, OFL metadata, metrics, bounds, and advances are valid")
    print("PASS: optical metric checks cover side bearings, centers, gaps, collision, and clipping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
