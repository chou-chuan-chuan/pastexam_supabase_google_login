#!/usr/bin/env python3
"""Measure U+5965 against representative ChenYuluoyan Han glyphs."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from audit_japanese_weight import glyph_measurement
from japanese.user_japanese_overrides import SHARED_HAN_OPTICAL_TRANSFORMS


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
OUTPUT_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REPORT_PATH = Path(__file__).resolve().parent / "reports/oku-optical-alignment.json"
TARGET = "奥"
REQUIRED_REFERENCES = "目写影深身"
EXISTING_ALIGNMENT_SAMPLE = "平仮名片君愛声夢春心明日夜空"
REFERENCE_CHARACTERS = REQUIRED_REFERENCES + EXISTING_ALIGNMENT_SAMPLE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def round_value(value: float) -> float:
    return round(float(value), 3)


def measure(font: TTFont, character: str) -> dict[str, object]:
    glyph_name = font.getBestCmap()[ord(character)]
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"U+{ord(character):04X} {character} has no ink bounds")
    x_min, y_min, x_max, y_max = pen.bounds
    advance, lsb = font["hmtx"].metrics[glyph_name]
    glyph = font["glyf"][glyph_name]
    return {
        "character": character,
        "codepoint": f"U+{ord(character):04X}",
        "glyph_name": glyph_name,
        "xMin": round_value(x_min),
        "xMax": round_value(x_max),
        "yMin": round_value(y_min),
        "yMax": round_value(y_max),
        "ink_width": round_value(x_max - x_min),
        "ink_height": round_value(y_max - y_min),
        "optical_center_x": round_value((x_min + x_max) / 2),
        "optical_center_y": round_value((y_min + y_max) / 2),
        "advance": int(advance),
        "lsb": int(lsb),
        "rsb": int(advance - lsb - (glyph.xMax - glyph.xMin)),
        "outline_rsb": round_value(advance - lsb - (x_max - x_min)),
    }


def median_box(records: list[dict[str, object]]) -> dict[str, float]:
    fields = (
        "xMin",
        "xMax",
        "yMin",
        "yMax",
        "ink_width",
        "ink_height",
        "optical_center_x",
        "optical_center_y",
        "advance",
        "lsb",
        "rsb",
    )
    return {
        field: round_value(statistics.median(float(record[field]) for record in records))
        for field in fields
    }


def main() -> int:
    transform = SHARED_HAN_OPTICAL_TRANSFORMS[TARGET]
    with TTFont(SOURCE_PATH, recalcTimestamp=False) as source:
        before = measure(source, TARGET)
        references = [measure(source, character) for character in REFERENCE_CHARACTERS]
    with TTFont(OUTPUT_PATH, recalcTimestamp=False) as output:
        current_output = measure(output, TARGET)
        authoritative_reference = measure(output, "奧")
    current_output["ink_density_16px_em2"] = glyph_measurement(OUTPUT_PATH, TARGET, 16)["ink_density_em2"]
    authoritative_reference["ink_density_16px_em2"] = glyph_measurement(OUTPUT_PATH, "奧", 16)["ink_density_em2"]
    width_scale = float(authoritative_reference["ink_width"]) / float(before["ink_width"])
    height_scale = float(authoritative_reference["ink_height"]) / float(before["ink_height"])
    area_scale = math.sqrt(width_scale * height_scale)
    payload = {
        "target": TARGET,
        "before_source": before,
        "reference_characters": REFERENCE_CHARACTERS,
        "required_reference_characters": REQUIRED_REFERENCES,
        "existing_alignment_sample": EXISTING_ALIGNMENT_SAMPLE,
        "reference_measurements": references,
        "reference_median": median_box(references),
        "authoritative_reference": authoritative_reference,
        "source_to_reference_ratios": {
            "raw_width_ratio": round_value(width_scale),
            "raw_height_ratio": round_value(height_scale),
            "geometric_mean_diagnostic_only": round_value(area_scale),
        },
        "transform": {
            "scale_x": transform.scale_x,
            "scale_y": transform.scale_y,
            "dx": transform.dx,
            "dy": transform.dy,
            "embolden": transform.embolden,
            "advance": transform.advance,
        },
        "current_output": current_output,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
