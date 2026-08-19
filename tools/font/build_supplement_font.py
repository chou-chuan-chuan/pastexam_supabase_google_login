#!/usr/bin/env python3
"""Build the OFL-compliant QuanFangwei supplemental font deterministically."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from fontTools import version as fonttools_version
from fontTools.misc.transform import Transform
from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.ttProgram import Program

from japanese.build_kana import build_japanese_phase1
from japanese.user_japanese_overrides import build_user_japanese_overrides


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
SOURCE_FONT = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
SOURCE_LICENSE = REPO_ROOT / "assets/fonts/chenyuluoyan/license.txt"
OUTPUT_DIR = REPO_ROOT / "assets/fonts/quanfangwei-supplement"
OUTPUT_TTF = OUTPUT_DIR / "QuanFangweiSupplementScript-Regular.ttf"
OUTPUT_WOFF2 = OUTPUT_DIR / "QuanFangweiSupplementScript-Regular.woff2"
OUTPUT_OFL = OUTPUT_DIR / "OFL.txt"
OUTPUT_MODIFICATIONS = OUTPUT_DIR / "MODIFICATIONS.md"
MANIFEST_PATH = TOOLS_DIR / "glyph_manifest.json"

SOURCE_SHA256 = "1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db"
FAMILY_EN = "QuanFangwei Supplement Script"
FAMILY_ZH = "荃方位補寫體"
SUBFAMILY = "Regular"
FULL_EN = f"{FAMILY_EN} {SUBFAMILY}"
FULL_ZH = f"{FAMILY_ZH} {SUBFAMILY}"
POSTSCRIPT_NAME = "QuanFangweiSupplementScript-Regular"
VERSION = "1.012"
BUILD_DATE = "2026-08-20"
UNIQUE_ID = f"{VERSION};QFW;{POSTSCRIPT_NAME};20260820"
MAC_EPOCH = datetime(1904, 1, 1, tzinfo=timezone.utc)
BUILD_TIMESTAMP = int((datetime(2026, 8, 11, tzinfo=timezone.utc) - MAC_EPOCH).total_seconds())

# These anchors reproduce the existing Ccedilla component transform exactly.
# The cedilla top-center (95, 91) attaches to C at (221, 91), yielding the
# optically reviewed +126 x / 0 y placement and the existing 26-unit gap.
CEDILLA_MARK_ANCHOR = (95, 91)
C_CEDILLA_BASE_ANCHOR = (221, 91)
C_LOWER_CEDILLA_BASE_ANCHOR = (176, 101)

# The source font already supplies U+0308 and the six precomposed Umlauts.
# These are the source GPOS anchors/component transforms that must remain
# unchanged.  U+00A8 reuses the same two handwritten dots as a spacing mark.
DIAERESIS_ADVANCE = 300


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def glyph_bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    glyph_set = font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    if pen.bounds is None:
        fail(f"Glyph {glyph_name!r} has no drawable bounds")
    return tuple(round(value) for value in pen.bounds)


def install_glyph(font: TTFont, glyph_name: str, glyph, advance: int, lsb: int, vertical_source: str) -> None:
    order = font.getGlyphOrder()
    if glyph_name not in order:
        order.append(glyph_name)
        font.setGlyphOrder(order)
    font["glyf"][glyph_name] = glyph
    glyph.recalcBounds(font["glyf"])
    font["hmtx"].metrics[glyph_name] = (int(advance), int(lsb))
    if "vmtx" in font:
        font["vmtx"].metrics[glyph_name] = font["vmtx"].metrics[vertical_source]
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def transformed_simple_glyph(font: TTFont, source_name: str, transform: Transform):
    source = font.getGlyphSet()[source_name]
    pen = TTGlyphPen(None)
    source.draw(TransformPen(pen, transform))
    return pen.glyph()


def transformed_contours(font: TTFont, source_name: str, contour_indices: set[int], transform: Transform):
    """Copy selected source contours through an affine transform."""
    recording = RecordingPen()
    font.getGlyphSet()[source_name].draw(recording)
    contours: list[list[tuple[str, tuple]]] = []
    current: list[tuple[str, tuple]] = []
    for operation in recording.value:
        current.append(operation)
        if operation[0] in {"closePath", "endPath"}:
            contours.append(current)
            current = []
    if current:
        contours.append(current)
    if not contour_indices or max(contour_indices) >= len(contours):
        fail(f"Glyph {source_name!r} does not contain requested contours {sorted(contour_indices)}")
    pen = TTGlyphPen(None)
    transformed_pen = TransformPen(pen, transform)
    for index, contour in enumerate(contours):
        if index in contour_indices:
            replayRecording(contour, transformed_pen)
    return pen.glyph()


def add_unicode_mapping(font: TTFont, codepoint: int, glyph_name: str) -> None:
    mapped = 0
    for subtable in font["cmap"].tables:
        if subtable.isUnicode() and hasattr(subtable, "cmap") and subtable.format != 14:
            subtable.cmap[codepoint] = glyph_name
            mapped += 1
    if not mapped:
        fail(f"No Unicode cmap subtable accepted U+{codepoint:04X}")


def build_questiondown(font: TTFont) -> None:
    cmap = font.getBestCmap()
    source_name = cmap.get(0x003F)
    if source_name is None:
        fail("Source font is missing U+003F QUESTION MARK")
    x_min, y_min, x_max, y_max = glyph_bounds(font, source_name)
    advance, _ = font["hmtx"].metrics[source_name]
    # Begin with the source question's exact 180-degree rotation. Then apply a
    # small optical translation: the inverted mark sits closer to the capital
    # line and its top dot is tightened toward the main stroke. These values are
    # deliberately expressed in font units so the build remains deterministic.
    transform = Transform(-1, 0, 0, -1, advance + 3, y_min + y_max - 12)
    glyph = transformed_simple_glyph(font, source_name, transform)
    if len(glyph.endPtsOfContours) < 2:
        fail("Source question must contain separate main-stroke and dot contours")
    dot_start = glyph.endPtsOfContours[0] + 1
    dot_end = glyph.endPtsOfContours[1]
    for point_index in range(dot_start, dot_end + 1):
        x, y = glyph.coordinates[point_index]
        glyph.coordinates[point_index] = (x, y - 8)
    glyph.recalcBounds(font["glyf"])
    install_glyph(font, "questiondown", glyph, advance, glyph.xMin, source_name)
    add_unicode_mapping(font, 0x00BF, "questiondown")


def build_cedilla_and_ccedilla(font: TTFont) -> None:
    cmap = font.getBestCmap()
    c_name = cmap.get(0x0043)
    lower_c_name = cmap.get(0x0063)
    comma_name = cmap.get(0x002C)
    semicolon_name = cmap.get(0x003B)
    if c_name is None:
        fail("Source font is missing U+0043 LATIN CAPITAL LETTER C")
    if lower_c_name is None:
        fail("Source font is missing U+0063 LATIN SMALL LETTER C")
    if comma_name is None:
        fail("Source font is missing U+002C COMMA, required to derive the cedilla")
    if semicolon_name is None:
        fail("Source font is missing U+003B SEMICOLON, required to derive the cedilla")

    c_bounds = glyph_bounds(font, c_name)
    # Use the semicolon's lower handwritten tail (itself a source-native stroke)
    # rather than a mechanically translated comma. Widen it slightly, shorten
    # it vertically, and add a restrained counter-clockwise rotation. This
    # produces a distinct cedilla hook while preserving the original curve and
    # point language.
    angle = math.radians(-7)
    scale_x = 1.16
    scale_y = 0.82
    base_transform = Transform(
        math.cos(angle) * scale_x,
        math.sin(angle) * scale_x,
        -math.sin(angle) * scale_y,
        math.cos(angle) * scale_y,
        0,
        0,
    )
    cedilla_glyph = transformed_contours(font, semicolon_name, {0}, base_transform)
    cedilla_glyph.recalcBounds(font["glyf"])
    standalone_advance = 190
    target_center = standalone_advance / 2
    target_top = c_bounds[1] - 26
    current_center = (cedilla_glyph.xMin + cedilla_glyph.xMax) / 2
    correction = Transform(1, 0, 0, 1, round(target_center - current_center), target_top - cedilla_glyph.yMax)
    cedilla_glyph = transformed_contours(font, semicolon_name, {0}, correction.transform(base_transform))
    cedilla_glyph.recalcBounds(font["glyf"])
    install_glyph(font, "cedilla", cedilla_glyph, standalone_advance, cedilla_glyph.xMin, semicolon_name)
    add_unicode_mapping(font, 0x00B8, "cedilla")

    cedilla_bounds = glyph_bounds(font, "cedilla")
    c_advance, c_lsb = font["hmtx"].metrics[c_name]
    # The open C carries more ink on the left. Place the cedilla at a restrained
    # optical center between its ink-heavy left side and mathematical center.
    c_center = (c_bounds[0] + c_bounds[2]) / 2 - (c_bounds[2] - c_bounds[0]) * 0.035
    cedilla_center = (cedilla_bounds[0] + cedilla_bounds[2]) / 2
    cedilla_dx = round(c_center - cedilla_center)
    composite_pen = TTGlyphPen(font.getGlyphSet())
    composite_pen.addComponent(c_name, (1, 0, 0, 1, 0, 0))
    composite_pen.addComponent("cedilla", (1, 0, 0, 1, cedilla_dx, 0))
    install_glyph(font, "Ccedilla", composite_pen.glyph(), c_advance, c_lsb, c_name)
    add_unicode_mapping(font, 0x00C7, "Ccedilla")

    lower_c_advance, lower_c_lsb = font["hmtx"].metrics[lower_c_name]
    lower_composite_pen = TTGlyphPen(font.getGlyphSet())
    lower_composite_pen.addComponent(lower_c_name, (1, 0, 0, 1, 0, 0))
    lower_composite_pen.addComponent("cedilla", (1, 0, 0, 1, 81, 10))
    install_glyph(font, "ccedilla", lower_composite_pen.glyph(), lower_c_advance, lower_c_lsb, lower_c_name)
    add_unicode_mapping(font, 0x00E7, "ccedilla")

    # U+0327 shares the reviewed U+00B8 outline by component reference, but is
    # a true combining mark with zero advance. Its GPOS anchors are installed
    # separately below so C/c + U+0327 land on the same pixels as the matching
    # precomposed Ccedilla/ccedilla glyphs.
    combining_pen = TTGlyphPen(font.getGlyphSet())
    combining_pen.addComponent("cedilla", (1, 0, 0, 1, 0, 0))
    install_glyph(font, "uni0327", combining_pen.glyph(), 0, cedilla_glyph.xMin, semicolon_name)
    add_unicode_mapping(font, 0x0327, "uni0327")


def build_german_additions(font: TTFont) -> None:
    """Add only the German glyphs missing from the official source font."""
    cmap = font.getBestCmap()
    for codepoint, label in ((0x0308, "COMBINING DIAERESIS"), (0x03B2, "GREEK SMALL LETTER BETA")):
        if codepoint not in cmap:
            fail(f"Source font is missing required {label} (U+{codepoint:04X})")

    # U+00A8 is an identity composite of the source-native U+0308 pair. Its
    # 300-unit advance gives the 60..240 ink bounds balanced 60/60 bearings.
    spacing_pen = TTGlyphPen(font.getGlyphSet())
    spacing_pen.addComponent(cmap[0x0308], (1, 0, 0, 1, 0, 0))
    install_glyph(font, "dieresis", spacing_pen.glyph(), DIAERESIS_ADVANCE, 60, cmap[0x0308])
    add_unicode_mapping(font, 0x00A8, "dieresis")

    # The visual reference explicitly calls for a beta-like sharp s. Reuse the
    # source font's own single-contour beta handwriting under distinct Unicode
    # and glyph names; this is not a cmap alias and does not modify U+03B2.
    beta_name = cmap[0x03B2]
    germandbls = transformed_simple_glyph(font, beta_name, Transform(1, 0, 0, 1, 0, 0))
    germandbls.recalcBounds(font["glyf"])
    install_glyph(font, "germandbls", germandbls, 391, germandbls.xMin, beta_name)
    add_unicode_mapping(font, 0x00DF, "germandbls")

    # Capital sharp S keeps the same beta-like stroke language, but compresses
    # the descender into the capital zone and widens the bowls optically.
    capital = transformed_simple_glyph(font, beta_name, Transform(1.10, 0, 0, 0.74, 0, 204))
    capital.recalcBounds(font["glyf"])
    install_glyph(font, "uni1E9E", capital, 430, capital.xMin, beta_name)
    add_unicode_mapping(font, 0x1E9E, "uni1E9E")


def add_cedilla_mark_positioning(font: TTFont) -> None:
    """Append a minimal mark-to-base lookup without replacing source GPOS."""
    if "GPOS" not in font or "GDEF" not in font:
        fail("Source font must retain its GPOS and GDEF tables")

    gpos = font["GPOS"].table
    if not gpos.LookupList or not gpos.FeatureList:
        fail("Source GPOS is missing lookup or feature lists")

    subtable = buildMarkBasePosSubtable(
        {"uni0327": (0, buildAnchor(*CEDILLA_MARK_ANCHOR))},
        {
            "C": {0: buildAnchor(*C_CEDILLA_BASE_ANCHOR)},
            "c": {0: buildAnchor(*C_LOWER_CEDILLA_BASE_ANCHOR)},
        },
        font.getReverseGlyphMap(),
    )
    lookup = otTables.Lookup()
    lookup.LookupType = 4
    lookup.LookupFlag = 0
    lookup.SubTable = [subtable]
    lookup.SubTableCount = 1

    lookup_index = len(gpos.LookupList.Lookup)
    gpos.LookupList.Lookup.append(lookup)
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)

    mark_features = [
        record.Feature
        for record in gpos.FeatureList.FeatureRecord
        if record.FeatureTag == "mark"
    ]
    if not mark_features:
        fail("Source GPOS has no mark feature to extend")
    for feature in mark_features:
        feature.LookupListIndex.append(lookup_index)
        feature.LookupCount = len(feature.LookupListIndex)

    glyph_classes = font["GDEF"].table.GlyphClassDef
    if glyph_classes is None:
        glyph_classes = otTables.ClassDef()
        glyph_classes.classDefs = {}
        font["GDEF"].table.GlyphClassDef = glyph_classes
    glyph_classes.classDefs["uni0327"] = 3


def set_name_records(font: TTFont) -> None:
    table = font["name"]
    replaced_ids = {1, 2, 3, 4, 5, 6, 10, 16, 17}
    table.names = [record for record in table.names if record.nameID not in replaced_ids]

    localized = {
        1: (FAMILY_EN, FAMILY_ZH),
        2: (SUBFAMILY, SUBFAMILY),
        3: (UNIQUE_ID, UNIQUE_ID),
        4: (FULL_EN, FULL_ZH),
        5: (f"Version {VERSION}", f"Version {VERSION}"),
        6: (POSTSCRIPT_NAME, POSTSCRIPT_NAME),
        10: (
            "QuanFangwei Supplement Script is an independently modified OFL 1.1 derivative of ChenYuluoyan Thin. It preserves the source Chinese and Latin glyphs except for explicitly documented maintainer-approved Japanese shared-codepoint overrides, and adds Spanish, French, German, modern Japanese kana, combining sound marks, and common Japanese punctuation. It is not an official release by the original authors.",
            "荃方位補寫體是基於辰宇落雁體、依 SIL Open Font License 1.1 獨立製作的衍生版本；除文件明列的維護者核准日文 shared-codepoint 覆寫外，保留原始中文與 Latin，並補入西班牙文、法文、德文、現代日文假名、濁音組合符號與常用日文標點。本修改版不是原作者官方發布版本。",
        ),
        16: (FAMILY_EN, FAMILY_ZH),
        17: (SUBFAMILY, SUBFAMILY),
    }
    for name_id, (english, traditional_chinese) in localized.items():
        table.setName(english, name_id, 3, 1, 0x0409)
        table.setName(traditional_chinese, name_id, 3, 1, 0x0404)
        table.setName(english, name_id, 0, 4, 0)
        if all(ord(character) < 128 for character in english):
            table.setName(english, name_id, 1, 0, 0)


def remove_truetype_hinting(font: TTFont) -> None:
    """Remove source hint bytecode that exceeds FreeType's function-definition limit."""
    glyf = font["glyf"]
    for glyph_name in font.getGlyphOrder():
        glyph = glyf[glyph_name]
        if hasattr(glyph, "program"):
            glyph.program = Program()
    for table_tag in ("fpgm", "prep", "cvt "):
        if table_tag in font:
            del font[table_tag]


def validate_inputs(manifest: dict) -> None:
    if not SOURCE_FONT.is_file() or not SOURCE_LICENSE.is_file():
        fail("The official source TTF or OFL license file is missing")
    if sha256(SOURCE_FONT) != SOURCE_SHA256:
        fail("The official source TTF hash changed; refusing to overwrite or build from an unreviewed source")

    for item in manifest.get("glyphs", []):
        character = item["character"]
        expected_codepoint = int(item["codepoint"].removeprefix("U+"), 16)
        if len(character) != 1 or ord(character) != expected_codepoint:
            fail(f"Manifest character/codepoint mismatch for {item['codepoint']}")
        actual_name = unicodedata.name(character)
        if actual_name != item["unicode_name"]:
            fail(f"Unicode name mismatch for {item['codepoint']}: {actual_name}")
        reference_name = item.get("reference_image")
        if reference_name:
            reference = TOOLS_DIR / reference_name
            if not reference.is_file():
                fail(f"Missing reference image: {reference}")
            with Image.open(reference) as image:
                image.verify()
        print(f"{character} {item['codepoint']} {actual_name} expected_glyph={item['glyph_name']}")


def write_modifications() -> None:
    content = f"""# MODIFICATIONS

- 衍生字型名稱：荃方位補寫體
- 英文名稱：QuanFangwei Supplement Script
- 原始字型名稱：辰宇落雁體 2.0 Thin / ChenYuluoyan 2.0 Thin
- 原始字型官方來源：https://github.com/Chenyu-otf/chenyuluoyan_thin
- 原始授權：SIL Open Font License 1.1
- Reserved Font Name：原字型保留名稱「辰宇落雁」與「Chenyuluoyan」未用作衍生 Family Name
- 修改者：`pastexam_supabase_google_login` 專案維護者（衍生版維護者，不是原字型作者）
- 修改日期：{BUILD_DATE}
- 版本：Version {VERSION}
- Japanese Phase 1：完整現代平假名、片假名、小假名、預組合濁音／半濁音、U+3099／U+309A combining marks、U+309B／U+309C spacing marks、iteration marks、middle dot、長音與常用標點
- Kana legibility revision：重畫容易誤認的現代假名骨架，尤其讓 U+306E `の` 保持清楚開口，並強化 `お`／`ぬ`／`め`／`る` 及 `シ`／`ツ`／`ソ`／`ン` 的識別差異；仍未載入或複製外部字型輪廓
- Kana template/alignment revision：Version 1.011 不再把掃描表格中的 cell 位置當成字型 metrics；46 個基本平假名 center-line 各自重新置中到 (480,500)，結構 x/y 分別作 1.10／1.28 optical scale，再沿用 -145 units 的共同 build-time baseline shift。最終 verifier 直接比較平假名與來源中文字的 median optical center
- User-handwriting refined revision：維護者本人手寫 SVG 現在涵蓋完整 46 個現代基本平假名（Version 1.011 新增 わ／を／ん）。SVG 只作結構／比例來源，不再直接安裝 filled outline；預先整理的 center-line branches 位於 `kana_sources/user_handwriting_refined.py`
- Special Japanese refinement（Version 1.012）：`す` 擴大中央 counter，`り` 延長下方收尾；新增維護者手寫 `懐／夕`；`気／付` 保留原 glyph drawing，僅依 refined `け` 的實際 bounds 做 build-time 垂直 optical normalization。原 glyph 仍保留在 glyph set，只有四個明列 code point 的 cmap 改指向衍生 glyph
- 假名輪廓：46 個現代基本平假名以維護者本人手寫結構為骨架，再交由 repository 原有 variable-width handwriting renderer 產生最終 TrueType 輪廓；target center-line width 為 42–50 units，renderer 再加入 deterministic pressure/taper/handwritten terminals。小平假名從 refined base 確定性縮放，濁音／半濁音仍共用 base + mark components
- 濁點：兩個不等寬、略有壓力與角度差的短筆，視覺參考原字型 apostrophe、quotation-like strokes、semicolon 與中文點筆；未複製其他日本字型
- 半濁點：以不完全幾何、寬度與曲率略變的封閉手寫小圈重畫，視覺參考原字型 U+3002、口、日等圓／框形筆勢；未複製其他日本字型
- Japanese combining：U+3099 `uni3099` 與 U+309A `uni309A` advance 均為 0，加入 GDEF mark class 與 GPOS MarkBasePos；預組合與分解形式共用同一 mark contour 與 anchor delta
- Japanese kanji：Version 1.012 明確覆寫 U+61D0 `懐` 與 U+5915 `夕`，兩者以維護者本人手寫 reference 整理為 center-line 並交由既有 variable-width renderer 重建；U+6C17 `気` 與 U+4ED8 `付` 僅建立保留原來源輪廓的垂直 optical transform copy，以和 `け` 對齊。其他 shared Unicode 漢字仍沿用原始辰宇落雁字形
- Known limitations：Phase 1 不保證所有 Jōyō Kanji 日本字形變體、vertical typesetting、ruby typography、完整 Ainu extensions、historical kana、half-width katakana 或所有標點變體；一般現代日文歌曲的假名部分應完整顯示
- Future Phase 2：依本機 TXT／LRC／JSON 歌詞的缺字頻率補足實際漢字，並個別審查 Japanese regional glyph variants；不抓取網路歌詞
- 補寫字元：U+00BF `questiondown`、U+00C7 `Ccedilla`、U+00E7 `ccedilla`、U+0327 `uni0327`、U+00A8 `dieresis`、U+00DF `germandbls`、U+1E9E `uni1E9E`
- German coverage：Ä Ö Ü／ä ö ü／ß ẞ，並同時支援 U+0308 `uni0308` 的分解表示；原始字型已存在六個 Umlaut 與 U+0308，其 cmap、輪廓、components、metrics、GDEF 與 GPOS 錨點均原封不動保留
- U+00A8 `dieresis`：以 identity component 共享原字型 U+0308 `uni0308` 的兩個手寫點，advance 300、左右各約 60 units；不是外部字型或幾何圓
- U+0308 `uni0308`：沿用原始 zero advance、GDEF mark class 與既有 MarkBasePos。mark anchor <145 477>；base anchors A <272 622>、O <235 564>、U <174 565>、a <172 464>、o <153 420>、u <180 415>
- Ä Ö Ü／ä ö ü：保留原字型既有 composite glyph；各自由原始 A/O/U/a/o/u 加上 `uni0308` 組成，component transforms 分別為 +127/+145、+90/+87、+29/+88、+27/-13、+8/-57、+35/-62
- U+00DF `germandbls`：依使用者提供的字母表參考，直接沿用原字型 U+03B2 `beta` 的單一連續手寫輪廓與原生比例；維持獨立 glyph name／Unicode mapping，advance 391
- U+1E9E `uni1E9E`：使用同一原字型 `beta` 輪廓語言，水平 110%、垂直 74%、上移 204 units，使 descender 收入 capital zone，形成較寬的 beta-like 大寫版本，advance 430
- ß／ẞ 的 beta-like 方向是依最新視覺參考採用；沒有將 U+00DF／U+1E9E cmap 指向 Greek beta，也沒有修改 U+03B2。未使用 Arial、Times、Noto、Google Fonts 或任何其他外部字型輪廓
- U+00BF 第一版建構：將原始 U+003F `question` 機械式旋轉 180°
- U+00BF 光學修正：旋轉後整體平移 +3 x／-12 y font units，圓點再下移 8 units，使句首高度、左右留白及點與主筆間距更自然；不修改來源 glyph
- U+00C7 建構：保留原始 U+0043 `C`，與新增的 U+00B8 `cedilla` 組成 composite glyph
- U+00E7 建構：保留原始 U+0063 `c`，與同一 U+00B8 `cedilla` 組成 composite glyph；cedilla transform 為 +81 x／+10 y，advance 與 side bearings 保持原始 c
- U+0327 建構：以 identity component 共享 U+00B8 `cedilla` 的同一精修輪廓來源；advance width 為 0，不作 spacing character
- U+0327 定位：保留原始 GPOS/GDEF，在既有 `mark` feature 附加 MarkBasePos lookup；C base anchor 為 <221 91>、c base anchor 為 <176 101>、mark anchor 為 <95 91>，分別重現 U+00C7 的 +126 x／0 y 與 U+00E7 的 +81 x／+10 y cedilla 位移
- HarfBuzz 驗證：在記憶體副本分別移除 U+00C7／U+00E7 cmap 以強制分解 shaping；C/c advances 471/345、`uni0327` advance 0、offsets -345/0 與 -264/+10，最終 mark origins 為 +126/0 與 +81/+10
- Unicode 表示：U+00C7／U+00E7 使用預組合 `Ccedilla`／`ccedilla`；U+0043／U+0063 + U+0327 保留分解 code points，經 GPOS 定位後得到相同 cedilla 造型、大小、光學中心與 26-unit gap
- Cedilla 第一版建構：原字型沒有 U+00B8 與 U+00E7，因此直接將 U+002C `comma` 向下定位
- Cedilla 光學修正：改用原始 U+003B `semicolon` 的下方手寫尾筆，水平 116%、垂直 82%、旋轉 -7°，再置於 C 的光學中心下方並保留 26 units 間距；comma、J、j、g、y 僅作同字型風格比較
- 美學限制：自動檢查只能驗證 bounds、留白、中心、碰撞與裁切；筆勢是否自然仍以多尺寸 proof 與瀏覽器人工目視為準
- Hinting：移除原始 TrueType hint bytecode；原始檔的 function definitions 超過 FreeType/Pillow 限制，輪廓、cmap、glyph 順序與 metrics 均保留
- FontForge：目前建置環境未安裝，未使用 FontForge GUI 或 scripting API
- fontTools：{fonttools_version}
- 建置指令：`python tools/font/build_supplement_font.py`
- 驗證指令：`python tools/font/verify_supplement_font.py`
- Proof 指令：`python tools/font/render_proof.py`

荃方位補寫體是基於辰宇落雁體，依 SIL Open Font License 1.1 製作的缺字補寫版本。本修改版由專案維護者獨立製作，不是原作者官方版本，也不代表原作者背書。
"""
    OUTPUT_MODIFICATIONS.write_text(content, encoding="utf-8", newline="\n")


def write_ofl() -> None:
    lines = SOURCE_LICENSE.read_text(encoding="utf-8").splitlines()
    OUTPUT_OFL.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        validate_inputs(manifest)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        font = TTFont(SOURCE_FONT, recalcBBoxes=True, recalcTimestamp=False)
        if "glyf" not in font or "hmtx" not in font:
            fail("This builder requires a TrueType glyf/hmtx source font")
        source_cmap = font.getBestCmap()
        for codepoint in (0x00BF, 0x00C7, 0x00E7, 0x0327, 0x00A8, 0x00DF, 0x1E9E):
            if codepoint in source_cmap:
                fail(f"Source unexpectedly already contains U+{codepoint:04X}; review the migration before rebuilding")

        build_questiondown(font)
        build_cedilla_and_ccedilla(font)
        add_cedilla_mark_positioning(font)
        build_german_additions(font)
        japanese_metadata = build_japanese_phase1(font)
        japanese_override_metadata = build_user_japanese_overrides(font)
        set_name_records(font)
        remove_truetype_hinting(font)
        font["head"].fontRevision = 1.012
        font["head"].modified = BUILD_TIMESTAMP
        if "DSIG" in font:
            del font["DSIG"]

        temp_ttf = OUTPUT_TTF.with_suffix(".tmp.ttf")
        temp_woff2 = OUTPUT_WOFF2.with_suffix(".tmp.woff2")
        font.save(temp_ttf, reorderTables=True)
        font.close()
        temp_ttf.replace(OUTPUT_TTF)

        webfont = TTFont(OUTPUT_TTF, recalcTimestamp=False)
        webfont.flavor = "woff2"
        webfont.save(temp_woff2, reorderTables=True)
        webfont.close()
        temp_woff2.replace(OUTPUT_WOFF2)

        write_ofl()
        write_modifications()
        print(f"Japanese Phase 1 added {len(japanese_metadata['added_characters'])} code points")
        print(f"Built {OUTPUT_TTF.relative_to(REPO_ROOT)}")
        print(f"Built {OUTPUT_WOFF2.relative_to(REPO_ROOT)}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
