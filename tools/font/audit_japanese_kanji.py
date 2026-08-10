#!/usr/bin/env python3
"""Audit kanji used by local TXT/LRC/JSON lyric inputs without web access."""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REPORT_DIR = Path(__file__).resolve().parent / "reports"
JSON_REPORT = REPORT_DIR / "japanese_kanji_missing.json"
MARKDOWN_REPORT = REPORT_DIR / "japanese_kanji_missing.md"
INPUT_SUFFIXES = {".txt", ".lrc", ".json"}
DISCOVERY_WORDS = ("lyric", "song", "fixture", "sample", "test")
EXCLUDED_PARTS = {".git", "node_modules", "proofs", "reports", "kana_sources"}


def is_kanji(character: str) -> bool:
    codepoint = ord(character)
    return 0x3400 <= codepoint <= 0x4DBF or 0x4E00 <= codepoint <= 0x9FFF or 0xF900 <= codepoint <= 0xFAFF


def json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from json_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from json_strings(item)


def read_strings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            return list(json_strings(json.loads(text)))
        except json.JSONDecodeError:
            return [text]
    return [text]


def discover_inputs() -> list[Path]:
    result = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in INPUT_SUFFIXES:
            continue
        relative = path.relative_to(REPO_ROOT)
        if EXCLUDED_PARTS.intersection(relative.parts):
            continue
        lowered = str(relative).lower()
        if any(word in lowered for word in DISCOVERY_WORDS):
            result.append(path)
    return sorted(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, help="TXT, LRC, JSON, or directories containing them")
    args = parser.parse_args()
    inputs: list[Path] = []
    if args.inputs:
        for supplied in args.inputs:
            path = supplied if supplied.is_absolute() else REPO_ROOT / supplied
            if path.is_dir():
                inputs.extend(sorted(child for child in path.rglob("*") if child.suffix.lower() in INPUT_SUFFIXES))
            elif path.suffix.lower() in INPUT_SUFFIXES:
                inputs.append(path)
    else:
        inputs = discover_inputs()

    counts: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)
    for path in inputs:
        relative = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        for text in read_strings(path):
            for character in text:
                if is_kanji(character):
                    counts[character] += 1
                    sources[character].add(relative)

    with TTFont(FONT_PATH, recalcTimestamp=False) as font:
        cmap = font.getBestCmap()
        rows = []
        for character, frequency in sorted(counts.items(), key=lambda item: (-item[1], ord(item[0]))):
            exists = ord(character) in cmap
            priority = "P0" if not exists and frequency >= 10 else "P1" if not exists and frequency >= 3 else "P2" if not exists else "covered"
            rows.append({
                "character": character,
                "codepoint": f"U+{ord(character):04X}",
                "unicode_name": unicodedata.name(character, "<UNASSIGNED>"),
                "frequency": frequency,
                "exists_in_font": exists,
                "missing": not exists,
                "source_files": sorted(sources[character]),
                "suggested_priority": priority,
            })
    payload = {
        "font": str(FONT_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "input_files": [str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in inputs],
        "input_note": "No matching repository lyric TXT/LRC/JSON inputs were found; pass files or directories as arguments." if not inputs else "Only local inputs were audited; no lyrics were fetched from the web.",
        "unique_kanji": len(rows),
        "missing_unique_kanji": sum(row["missing"] for row in rows),
        "characters": rows,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Japanese kanji coverage audit",
        "",
        f"- Input files: {len(inputs)}",
        f"- Unique kanji: {payload['unique_kanji']}",
        f"- Missing unique kanji: {payload['missing_unique_kanji']}",
        f"- Note: {payload['input_note']}",
        "- Phase 1 does not add kanji. Shared Unicode code points use the existing source glyph; Japanese regional variants are Phase 2.",
        "",
        "| Character | Code point | Frequency | Exists | Missing | Source files | Priority |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['character']} | {row['codepoint']} | {row['frequency']} | "
            f"{'yes' if row['exists_in_font'] else 'no'} | {'yes' if row['missing'] else 'no'} | "
            f"{', '.join(row['source_files'])} | {row['suggested_priority']} |"
        )
    MARKDOWN_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {JSON_REPORT.relative_to(REPO_ROOT)}")
    print(f"Wrote {MARKDOWN_REPORT.relative_to(REPO_ROOT)}")
    print(f"inputs={len(inputs)} unique_kanji={len(rows)} missing={payload['missing_unique_kanji']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
