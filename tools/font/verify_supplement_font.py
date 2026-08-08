#!/usr/bin/env python3
"""Verify the supplemental TTF/WOFF2, metadata, glyphs, and source preservation."""

from __future__ import annotations

import hashlib
import sys
from io import BytesIO
from pathlib import Path

import uharfbuzz as hb
from fontTools.misc.testTools import getXML
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont


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
VERSION = "1.001"
UNIQUE_ID = "1.001;QFW;QuanFangweiSupplementScript-Regular;20260808"
SOURCE_SHA256 = "1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db"
CEDILLA_MARK_ANCHOR = (95, 91)
C_CEDILLA_BASE_ANCHOR = (221, 91)


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


def harfbuzz_decomposed_positions(path: Path):
    """Force the decomposed path and return HarfBuzz glyph positions.

    HarfBuzz normally recomposes C + U+0327 when U+00C7 is available. Removing
    only that cmap entry from an in-memory copy forces the engine to exercise
    this font's C/uni0327 MarkBasePos lookup without changing any output file.
    """
    font = TTFont(path, recalcTimestamp=False)
    try:
        for subtable in font["cmap"].tables:
            if subtable.isUnicode() and hasattr(subtable, "cmap"):
                subtable.cmap.pop(0x00C7, None)
        buffer = BytesIO()
        font.flavor = None
        font.save(buffer, reorderTables=True)
        face = hb.Face(buffer.getvalue())
        hb_font = hb.Font(face)
        upm = font["head"].unitsPerEm
        hb_font.scale = (upm, upm)
        hb_buffer = hb.Buffer()
        hb_buffer.add_codepoints([0x0043, 0x0327])
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
    required = {0x00BF: "questiondown", 0x00C7: "Ccedilla", 0x0327: "uni0327"}
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
            if codepoint == 0x0327:
                require(advance == 0, f"TTF combining cedilla advance must be zero, found {advance}")
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
    if "uni0327" in ttf["glyf"].glyphs:
        combining = ttf["glyf"]["uni0327"]
        component_info = [component.getComponentInfo() for component in combining.components] if combining.isComposite() else []
        require(
            component_info == [("cedilla", (1, 0, 0, 1, 0, 0))],
            f"uni0327 must share the cedilla outline by identity component: {component_info}",
        )
        require(ttf["GDEF"].table.GlyphClassDef.classDefs.get("uni0327") == 3, "uni0327 is not classified as a GDEF mark")

    source_question = source_cmap.get(0x003F)
    source_c = source_cmap.get(0x0043)
    require(source_question is not None and drawing(source, source_question) == drawing(ttf, source_question), "Original question outline changed")
    require(source_c is not None and drawing(source, source_c) == drawing(ttf, source_c), "Original C outline changed")
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
    require(not any(tag in ttf for tag in ("fpgm", "prep", "cvt ")), "Derived TTF still contains incompatible hint program tables")

    require(set(source_cmap).issubset(ttf_cmap), "One or more original cmap codepoints were removed")
    for codepoint, glyph_name in source_cmap.items():
        require(ttf_cmap.get(codepoint) == glyph_name, f"Original cmap mapping changed at U+{codepoint:04X}")
    require(ttf_cmap == woff2_cmap, "WOFF2 decoded cmap differs from TTF cmap")
    for glyph_name in ("questiondown", "cedilla", "Ccedilla", "uni0327"):
        require(bounds(ttf, glyph_name) == bounds(woff2, glyph_name), f"WOFF2 bounds differ from TTF for {glyph_name}")
        require(ttf["hmtx"].metrics[glyph_name] == woff2["hmtx"].metrics[glyph_name], f"WOFF2 metrics differ from TTF for {glyph_name}")
    require(mark_to_base_anchors(ttf, "uni0327", "C") == mark_to_base_anchors(woff2, "uni0327", "C"), "WOFF2 mark anchors differ from TTF")
    source_order = source.getGlyphOrder()
    ttf_order = ttf.getGlyphOrder()
    require(ttf_order[: len(source_order)] == source_order, "Original glyph order or glyph set was altered")
    require(len(ttf_order) == len(source_order) + 4, "Derived glyph count did not increase by exactly four")
    require(ttf_order == woff2.getGlyphOrder(), "WOFF2 glyph order differs from TTF")

    source_lookups = source["GPOS"].table.LookupList.Lookup
    derived_lookups = ttf["GPOS"].table.LookupList.Lookup
    require(len(derived_lookups) == len(source_lookups) + 1, "Derived GPOS should append exactly one lookup")
    for index, source_lookup in enumerate(source_lookups):
        require(getXML(source_lookup.toXML, source) == getXML(derived_lookups[index].toXML, ttf), f"Original GPOS lookup {index} changed")
    for glyph_name, glyph_class in source["GDEF"].table.GlyphClassDef.classDefs.items():
        require(ttf["GDEF"].table.GlyphClassDef.classDefs.get(glyph_name) == glyph_class, f"Original GDEF class changed for {glyph_name}")
    hb_positions = harfbuzz_decomposed_positions(TTF_PATH)
    require(
        hb_positions == [("C", 471, 0, 0, 0), ("uni0327", 0, 0, -345, 0)],
        f"HarfBuzz decomposed shaping is incorrect: {hb_positions}",
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
    print("PASS: U+00BF -> questiondown, U+00C7 -> Ccedilla, and U+0327 -> uni0327 in both cmaps")
    print("PASS: uni0327 has zero advance, shared cedilla outline, GDEF mark class, and GPOS C anchors")
    print("PASS: HarfBuzz shapes forced C + U+0327 as C/uni0327 with mark origin at +126 x / 0 y")
    print("PASS: all original cmap mappings and glyph order are preserved")
    print("PASS: names, OFL metadata, metrics, bounds, and advances are valid")
    print("PASS: optical metric checks cover side bearings, centers, gaps, collision, and clipping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
