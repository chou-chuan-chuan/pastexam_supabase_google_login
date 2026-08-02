#!/usr/bin/env python3
"""Build the OFL-compliant QuanFangwei supplemental font deterministically."""

from __future__ import annotations

import hashlib
import json
import sys
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from fontTools import version as fonttools_version
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.ttProgram import Program


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
VERSION = "1.000"
BUILD_DATE = "2026-08-02"
UNIQUE_ID = f"{VERSION};QFW;{POSTSCRIPT_NAME};20260802"
MAC_EPOCH = datetime(1904, 1, 1, tzinfo=timezone.utc)
BUILD_TIMESTAMP = int((datetime(2026, 8, 2, tzinfo=timezone.utc) - MAC_EPOCH).total_seconds())


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
    transform = Transform(-1, 0, 0, -1, advance, y_min + y_max)
    glyph = transformed_simple_glyph(font, source_name, transform)
    install_glyph(font, "questiondown", glyph, advance, advance - x_max, source_name)
    add_unicode_mapping(font, 0x00BF, "questiondown")


def build_cedilla_and_ccedilla(font: TTFont) -> None:
    cmap = font.getBestCmap()
    c_name = cmap.get(0x0043)
    comma_name = cmap.get(0x002C)
    if c_name is None:
        fail("Source font is missing U+0043 LATIN CAPITAL LETTER C")
    if comma_name is None:
        fail("Source font is missing U+002C COMMA, required to derive the cedilla")

    c_bounds = glyph_bounds(font, c_name)
    comma_bounds = glyph_bounds(font, comma_name)
    comma_advance, comma_lsb = font["hmtx"].metrics[comma_name]
    upm = font["head"].unitsPerEm
    gap = max(12, round(upm * 0.012))
    target_top = c_bounds[1] - gap
    cedilla_dy = target_top - comma_bounds[3]
    cedilla_glyph = transformed_simple_glyph(font, comma_name, Transform(1, 0, 0, 1, 0, cedilla_dy))
    install_glyph(font, "cedilla", cedilla_glyph, comma_advance, comma_lsb, comma_name)
    add_unicode_mapping(font, 0x00B8, "cedilla")

    cedilla_bounds = glyph_bounds(font, "cedilla")
    c_advance, c_lsb = font["hmtx"].metrics[c_name]
    c_center = (c_bounds[0] + c_bounds[2]) / 2
    cedilla_center = (cedilla_bounds[0] + cedilla_bounds[2]) / 2
    cedilla_dx = round(c_center - cedilla_center)
    composite_pen = TTGlyphPen(font.getGlyphSet())
    composite_pen.addComponent(c_name, (1, 0, 0, 1, 0, 0))
    composite_pen.addComponent("cedilla", (1, 0, 0, 1, cedilla_dx, 0))
    install_glyph(font, "Ccedilla", composite_pen.glyph(), c_advance, c_lsb, c_name)
    add_unicode_mapping(font, 0x00C7, "Ccedilla")


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
            "QuanFangwei Supplement Script is an independently modified OFL 1.1 derivative of ChenYuluoyan Thin. It adds U+00BF and U+00C7 and is not an official release by the original authors.",
            "荃方位補寫體是基於辰宇落雁體、依 SIL Open Font License 1.1 獨立製作的缺字補寫版本，新增 U+00BF 與 U+00C7；本修改版不是原作者官方發布版本。",
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
        reference = TOOLS_DIR / item["reference_image"]
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
- 新增字元：U+00BF `questiondown`、U+00C7 `Ccedilla`
- U+00BF 建構：將原始 U+003F `question` 以 advance width 與可視高度中心旋轉 180°，不修改來源 glyph
- U+00C7 建構：保留原始 U+0043 `C`，與新增的 U+00B8 `cedilla` 組成 composite glyph
- Cedilla 來源：原字型沒有 U+00B8 與 U+00E7；新增 cedilla 由原始 U+002C `comma` 的手寫輪廓向下定位而成
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
        for codepoint in (0x00BF, 0x00C7):
            if codepoint in source_cmap:
                fail(f"Source unexpectedly already contains U+{codepoint:04X}; review the migration before rebuilding")

        build_questiondown(font)
        build_cedilla_and_ccedilla(font)
        set_name_records(font)
        remove_truetype_hinting(font)
        font["head"].fontRevision = 1.0
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
        print(f"Built {OUTPUT_TTF.relative_to(REPO_ROOT)}")
        print(f"Built {OUTPUT_WOFF2.relative_to(REPO_ROOT)}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
