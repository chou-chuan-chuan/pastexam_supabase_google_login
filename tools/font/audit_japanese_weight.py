#!/usr/bin/env python3
"""Deterministically audit source-Han and Japanese effective stroke weight.

The audit rasterizes at 4x the requested CSS pixel size, thresholds coverage at
50%, and measures short contiguous ink runs on both axes.  Vertical scan runs
estimate horizontal-stroke weight; horizontal scan runs estimate vertical-
stroke weight.  Long runs are excluded because they represent stroke length,
counters, or intersections rather than local thickness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.ttProgram import Program


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FONT = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
CURRENT_FONT = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
DEFAULT_REPORT = Path(__file__).resolve().parent / "reports/japanese_weight_audit.json"
SOURCE_SHA256 = "1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db"
SIZES = (16, 20, 24, 32, 48, 72, 96)
SUPERSAMPLE = 4
ALPHA_THRESHOLD = 128

SOURCE_HAN = "一十口日田心女君愛聲夢春明夜空"
LARGE_HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
SMALL_HIRAGANA = "ぁぃぅぇぉゃゅょっゎゕゖ"
KATAKANA = "".join(chr(cp) for cp in range(0x30A1, 0x30FB))
JAPANESE_MARKS = "゙゚゛゜ゝゞヽヾ々・ー〆"
PROJECT_DERIVED_HAN = "懐気付奥容恋哀奧優寄変"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dehinted_source(destination: Path) -> None:
    """Write a temporary raster-only copy; never touch the official source."""
    font = TTFont(SOURCE_FONT, recalcTimestamp=False)
    try:
        for glyph_name in font.getGlyphOrder():
            glyph = font["glyf"][glyph_name]
            if hasattr(glyph, "program"):
                glyph.program = Program()
        for tag in ("fpgm", "prep", "cvt "):
            if tag in font:
                del font[tag]
        font.save(destination, reorderTables=True)
    finally:
        font.close()


def contiguous_runs(line: np.ndarray) -> list[int]:
    padded = np.pad(line.astype(np.int8), (1, 1))
    changes = np.flatnonzero(np.diff(padded))
    return [int(end - start) for start, end in zip(changes[::2], changes[1::2])]


def render_mask(font_path: Path, character: str, size: int) -> tuple[np.ndarray, np.ndarray]:
    render_size = size * SUPERSAMPLE
    padding = render_size
    canvas_size = render_size * 3
    image = Image.new("L", (canvas_size, canvas_size), 0)
    draw = ImageDraw.Draw(image)
    face = ImageFont.truetype(str(font_path), render_size)
    bbox = draw.textbbox((padding, padding), character, font=face, anchor="lt")
    draw.text((padding, padding), character, font=face, fill=255, anchor="lt")
    alpha = np.asarray(image, dtype=np.uint8)
    nonzero = np.argwhere(alpha > 0)
    if nonzero.size == 0:
        raise ValueError(f"No raster ink for {character} U+{ord(character):04X} at {size}px; bbox={bbox}")
    y0, x0 = nonzero.min(axis=0)
    y1, x1 = nonzero.max(axis=0) + 1
    alpha = alpha[y0:y1, x0:x1]
    return alpha >= ALPHA_THRESHOLD, alpha


def glyph_measurement(font_path: Path, character: str, size: int) -> dict[str, float]:
    mask, alpha = render_mask(font_path, character, size)
    maximum_thickness = max(2, round(size * SUPERSAMPLE * 0.18))
    horizontal_runs = [run for row in mask for run in contiguous_runs(row) if run <= maximum_thickness]
    vertical_runs = [run for column in mask.T for run in contiguous_runs(column) if run <= maximum_thickness]
    if not horizontal_runs or not vertical_runs:
        raise ValueError(f"Insufficient scan runs for {character} at {size}px")
    vertical_weight = statistics.median(horizontal_runs) / SUPERSAMPLE
    horizontal_weight = statistics.median(vertical_runs) / SUPERSAMPLE
    effective_weight = statistics.median(horizontal_runs + vertical_runs) / SUPERSAMPLE
    ink_density = float(alpha.sum()) / 255.0 / ((size * SUPERSAMPLE) ** 2)
    return {
        "effective_stroke_px": round(effective_weight, 4),
        "horizontal_stroke_px": round(horizontal_weight, 4),
        "vertical_stroke_px": round(vertical_weight, 4),
        "ink_density_em2": round(ink_density, 6),
    }


def group_measurement(font_path: Path, characters: str, size: int) -> dict[str, float | int]:
    values = [glyph_measurement(font_path, character, size) for character in characters]
    result: dict[str, float | int] = {"glyph_count": len(values)}
    for key in values[0]:
        result[key] = round(statistics.median(value[key] for value in values), 6)
    return result


def aggregate_ratio(group: dict[str, dict], source: dict[str, dict], key: str) -> float:
    ratios = [group[str(size)][key] / source[str(size)][key] for size in SIZES]
    return round(statistics.median(ratios), 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", type=Path, default=CURRENT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    if sha256(SOURCE_FONT) != SOURCE_SHA256:
        raise SystemExit("Official ChenYuluoyan source hash changed")
    if not args.font.is_file():
        raise SystemExit(f"Missing audited font: {args.font}")

    with tempfile.TemporaryDirectory(prefix="qfw-weight-audit-") as temp_dir:
        raster_source = Path(temp_dir) / "ChenYuluoyan-dehinted.ttf"
        dehinted_source(raster_source)
        definitions = {
            "source_han": (raster_source, SOURCE_HAN),
            "large_hiragana": (args.font, LARGE_HIRAGANA),
            "small_hiragana": (args.font, SMALL_HIRAGANA),
            "katakana": (args.font, KATAKANA),
            "japanese_marks": (args.font, JAPANESE_MARKS),
            "project_derived_han": (args.font, PROJECT_DERIVED_HAN),
        }
        groups = {
            name: {str(size): group_measurement(font_path, characters, size) for size in SIZES}
            for name, (font_path, characters) in definitions.items()
        }

    source = groups["source_han"]
    ratios = {
        name: {
            key: aggregate_ratio(group, source, key)
            for key in ("effective_stroke_px", "horizontal_stroke_px", "vertical_stroke_px", "ink_density_em2")
        }
        for name, group in groups.items()
        if name != "source_han"
    }
    report = {
        "method": {
            "sizes_px": list(SIZES),
            "supersample": SUPERSAMPLE,
            "alpha_threshold": ALPHA_THRESHOLD,
            "maximum_local_run_em": 0.18,
            "source_font_sha256": SOURCE_SHA256,
            "source_hinting": "removed only in a temporary raster copy",
        },
        "characters": {
            "source_han": SOURCE_HAN,
            "large_hiragana": LARGE_HIRAGANA,
            "small_hiragana": SMALL_HIRAGANA,
            "katakana": KATAKANA,
            "japanese_marks": JAPANESE_MARKS,
            "project_derived_han": PROJECT_DERIVED_HAN,
        },
        "groups": groups,
        "median_ratio_to_source_han": ratios,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(ratios, ensure_ascii=False, indent=2))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
