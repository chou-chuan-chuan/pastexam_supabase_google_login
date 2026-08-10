#!/usr/bin/env python3
"""Audit Japanese Unicode coverage in the official and derived fonts."""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path

from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FONT = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
DERIVED_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REPORT_DIR = Path(__file__).resolve().parent / "reports"
JSON_REPORT = REPORT_DIR / "japanese_coverage.json"
MARKDOWN_REPORT = REPORT_DIR / "japanese_coverage.md"

BLOCKS = (
    ("cjk_symbols_and_punctuation", 0x3000, 0x303F),
    ("hiragana", 0x3040, 0x309F),
    ("katakana", 0x30A0, 0x30FF),
    ("katakana_phonetic_extensions", 0x31F0, 0x31FF),
)

HIRAGANA_REQUIRED = set(range(0x3041, 0x3097)) | {0x3099, 0x309A, 0x309B, 0x309C, 0x309D, 0x309E}
KATAKANA_REQUIRED = set(range(0x30A1, 0x30FB)) | {0x30FB, 0x30FC, 0x30FD, 0x30FE}
PUNCTUATION_REQUIRED = {
    0x3000, 0x3001, 0x3002, 0x3005, 0x3006, 0x3007,
    *range(0x3008, 0x3012), 0x3014, 0x3015, 0x301C,
}
PHASE1_REQUIRED = HIRAGANA_REQUIRED | KATAKANA_REQUIRED | PUNCTUATION_REQUIRED

# A deliberately small, repository-local Phase 1 lyric sample. Kanji are
# statistics only and are never used to source or construct kana outlines.
COMMON_LYRIC_KANJI = set("君声聞一度愛夜空見上言会夢中春風吹心明日晴")


def unicode_name(codepoint: int) -> str:
    return unicodedata.name(chr(codepoint), "<UNASSIGNED>")


def record(codepoint: int, category: str, source_cmap: dict[int, str], derived_cmap: dict[int, str]) -> dict:
    source_name = source_cmap.get(codepoint)
    derived_name = derived_cmap.get(codepoint)
    required = codepoint in PHASE1_REQUIRED
    return {
        "character": chr(codepoint),
        "codepoint": f"U+{codepoint:04X}",
        "unicode_name": unicode_name(codepoint),
        "source_font_has_glyph": source_name is not None,
        "derived_font_has_glyph": derived_name is not None,
        "glyph_name": derived_name or source_name,
        "needs_addition": required and derived_name is None,
        "category": category,
        "phase_1_required": required,
    }


def summarize(records: list[dict]) -> dict:
    by_category: dict[str, dict] = {}
    for category in sorted({item["category"] for item in records}):
        items = [item for item in records if item["category"] == category]
        required = [item for item in items if item["phase_1_required"]]
        by_category[category] = {
            "audited": len(items),
            "source_present": sum(item["source_font_has_glyph"] for item in items),
            "derived_present": sum(item["derived_font_has_glyph"] for item in items),
            "phase_1_required": len(required),
            "phase_1_missing": sum(item["needs_addition"] for item in required),
        }
    return by_category


def main() -> int:
    if not SOURCE_FONT.is_file():
        raise FileNotFoundError(SOURCE_FONT)
    if not DERIVED_FONT.is_file():
        raise FileNotFoundError(DERIVED_FONT)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with TTFont(SOURCE_FONT, recalcTimestamp=False) as source, TTFont(DERIVED_FONT, recalcTimestamp=False) as derived:
        source_cmap = source.getBestCmap()
        derived_cmap = derived.getBestCmap()
        records = [
            record(codepoint, category, source_cmap, derived_cmap)
            for category, start, end in BLOCKS
            for codepoint in range(start, end + 1)
        ]
        records.extend(
            record(ord(character), "common_japanese_kanji_sample", source_cmap, derived_cmap)
            for character in sorted(COMMON_LYRIC_KANJI, key=ord)
        )
        cjk_advances = Counter(
            source["hmtx"].metrics[glyph_name][0]
            for codepoint, glyph_name in source_cmap.items()
            if 0x4E00 <= codepoint <= 0x9FFF
        )
        payload = {
            "source_font": str(SOURCE_FONT.relative_to(REPO_ROOT)).replace("\\", "/"),
            "derived_font": str(DERIVED_FONT.relative_to(REPO_ROOT)).replace("\\", "/"),
            "source_glyph_count": len(source.getGlyphOrder()),
            "derived_glyph_count": len(derived.getGlyphOrder()),
            "units_per_em": source["head"].unitsPerEm,
            "source_hhea": {"ascent": source["hhea"].ascent, "descent": source["hhea"].descent},
            "source_cjk_codepoints": sum(0x4E00 <= cp <= 0x9FFF for cp in source_cmap),
            "source_cjk_advance_widths": [
                {"advance": advance, "count": count}
                for advance, count in cjk_advances.most_common()
            ],
            "summary": summarize(records),
            "records": records,
        }

    JSON_REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Japanese coverage audit",
        "",
        f"- Source: `{payload['source_font']}`",
        f"- Derived: `{payload['derived_font']}`",
        f"- Units per em: {payload['units_per_em']}",
        f"- Source CJK Unified Ideographs coverage: {payload['source_cjk_codepoints']} code points",
        "- Katakana Phonetic Extensions are audited only; they are not Phase 1 requirements.",
        "- Japanese kanji entries are coverage statistics only. Shared code points continue to use the existing source glyph.",
        "",
        "## Summary",
        "",
        "| Category | Audited | Source present | Derived present | Phase 1 required | Phase 1 missing |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for category, values in payload["summary"].items():
        lines.append(
            f"| {category} | {values['audited']} | {values['source_present']} | "
            f"{values['derived_present']} | {values['phase_1_required']} | {values['phase_1_missing']} |"
        )
    lines.extend([
        "",
        "## Code points",
        "",
        "| Character | Code point | Unicode name | Source | Derived | Glyph name | Add | Category | Phase 1 |",
        "|---|---|---|---:|---:|---|---:|---|---:|",
    ])
    for item in records:
        display = item["character"] if item["character"].strip() else "SPACE"
        lines.append(
            f"| {display} | {item['codepoint']} | {item['unicode_name']} | "
            f"{'yes' if item['source_font_has_glyph'] else 'no'} | "
            f"{'yes' if item['derived_font_has_glyph'] else 'no'} | "
            f"{item['glyph_name'] or ''} | {'yes' if item['needs_addition'] else 'no'} | "
            f"{item['category']} | {'yes' if item['phase_1_required'] else 'no'} |"
        )
    MARKDOWN_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {JSON_REPORT.relative_to(REPO_ROOT)}")
    print(f"Wrote {MARKDOWN_REPORT.relative_to(REPO_ROOT)}")
    for category, values in payload["summary"].items():
        print(category, values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
