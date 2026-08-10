#!/usr/bin/env python3
"""Measure source handwriting traits used by the original kana designs."""

from __future__ import annotations

import statistics
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FONT = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
REPORT = Path(__file__).resolve().parent / "reports/kana_style_analysis.md"
PROOF = Path(__file__).resolve().parent / "proofs/kana-style-reference.png"
REFERENCE_CHARACTERS = "一丨丿乀丶乙了口日心女子之也乃川久九千小大"


def bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        return (0, 0, 0, 0)
    return tuple(round(value) for value in pen.bounds)


def run_lengths(mask: Image.Image) -> list[int]:
    """Collect short horizontal/vertical ink runs as a stroke-weight proxy."""
    pixels = mask.load()
    width, height = mask.size
    runs: list[int] = []
    for horizontal in (True, False):
        outer = height if horizontal else width
        inner = width if horizontal else height
        for outer_index in range(outer):
            start = None
            for inner_index in range(inner + 1):
                value = 0
                if inner_index < inner:
                    x, y = (inner_index, outer_index) if horizontal else (outer_index, inner_index)
                    value = pixels[x, y]
                if value and start is None:
                    start = inner_index
                elif not value and start is not None:
                    length = inner_index - start
                    if 8 <= length <= 115:
                        runs.append(length)
                    start = None
    return runs


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    with TTFont(SOURCE_FONT, recalcTimestamp=False) as font:
        # The official font contains legacy hint programs that exceed the
        # FreeType interpreter limit in this environment. Strip them only from
        # a throwaway render copy; SOURCE_FONT itself is never written.
        with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temporary:
            render_path = Path(temporary.name)
        render_font = TTFont(SOURCE_FONT, recalcTimestamp=False)
        for tag in ("fpgm", "prep", "cvt "):
            if tag in render_font:
                del render_font[tag]
        render_font.save(render_path, reorderTables=False)
        render_font.close()
        face = ImageFont.truetype(str(render_path), 420)
        cmap = font.getBestCmap()
        metrics = []
        missing = []
        stroke_samples: list[int] = []
        for character in REFERENCE_CHARACTERS:
            glyph_name = cmap.get(ord(character))
            if glyph_name is None:
                missing.append(character)
                continue
            glyph_bounds = bounds(font, glyph_name)
            advance, lsb = font["hmtx"].metrics[glyph_name]
            metrics.append((character, glyph_name, advance, lsb, glyph_bounds))
            mask = Image.new("L", (520, 560), 0)
            draw = ImageDraw.Draw(mask)
            draw.text((50, 470), character, font=face, fill=255, anchor="ls")
            stroke_samples.extend(run_lengths(mask))

        advances = [item[2] for item in metrics]
        widths = [item[4][2] - item[4][0] for item in metrics]
        heights = [item[4][3] - item[4][1] for item in metrics]
        centers = [((item[4][0] + item[4][2]) / 2, (item[4][1] + item[4][3]) / 2) for item in metrics]
        em = font["head"].unitsPerEm
        stroke_px = statistics.median(stroke_samples) if stroke_samples else 0
        stroke_units = stroke_px * em / 420

        lines = [
            "# Kana style analysis",
            "",
            "This report measures only the official ChenYuluoyan source. The kana contours are original work and do not use external Japanese font outlines.",
            "",
            "## Aggregate observations",
            "",
            f"- Units per em: {em}",
            f"- hhea ascent/descent: {font['hhea'].ascent} / {font['hhea'].descent}",
            f"- Median reference advance: {statistics.median(advances):.1f} units",
            f"- Median ink width/height: {statistics.median(widths):.1f} / {statistics.median(heights):.1f} units",
            f"- Median short-run stroke proxy: {stroke_units:.1f} font units ({stroke_px:.1f}px at 420px proof size)",
            f"- Median optical center: x={statistics.median(x for x, _ in centers):.1f}, y={statistics.median(y for _, y in centers):.1f}",
            f"- Requested references absent from the official source cmap: {' '.join(missing) if missing else 'none'}",
            "- Endpoint style: pressure-like rounded or tapered ends; short dots often lean down-right and are not geometric capsules.",
            "- Curve character: loose quadratic sweeps with visibly changing curvature, restrained hooks, and open counters.",
            "- Handwriting slant: mostly upright with local rightward motion on falling strokes; no global mechanical italic transform.",
            "- Center of gravity: slightly above the geometric center, with generous lower and side breathing room.",
            "- Character-box use: variable rather than monospaced-looking ink, while CJK advances cluster around the em width.",
            "- Baseline/optical center: glyph ink stays comfortably inside the source ascent/descent; kana target y=70..850 with optical center near y=455.",
            "- Natural irregularity: stroke widths, joins, and terminal angles vary slightly; repeated primitives receive per-glyph optical adjustment.",
            "",
            "## Reference glyph metrics",
            "",
            "| Character | Glyph | Advance | LSB | Bounds | Ink box (% em) |",
            "|---|---|---:|---:|---|---:|",
        ]
        for character, glyph_name, advance, lsb, glyph_bounds in metrics:
            ink_ratio = (glyph_bounds[2] - glyph_bounds[0]) * (glyph_bounds[3] - glyph_bounds[1]) / (em * em) * 100
            lines.append(f"| {character} | {glyph_name} | {advance} | {lsb} | {glyph_bounds} | {ink_ratio:.1f}% |")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    image = Image.new("RGB", (1900, 1080), "#fffdf9")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(render_path), 38)
    label = ImageFont.truetype(str(render_path), 19)
    display = ImageFont.truetype(str(render_path), 150)
    draw.text((50, 40), "Kana style references — official source strokes only", font=title, fill="#4f276c")
    for index, character in enumerate(REFERENCE_CHARACTERS):
        col, row = index % 8, index // 8
        x, y = 50 + col * 230, 120 + row * 285
        draw.rounded_rectangle((x, y, x + 205, y + 245), 14, fill="#ffffff", outline="#d8c6e6", width=2)
        baseline = y + 178
        draw.line((x + 12, baseline, x + 193, baseline), fill="#df5d74", width=1)
        draw.text((x + 28, baseline), character, font=display, fill="#17121f", anchor="ls")
        draw.text((x + 12, y + 207), f"{character} U+{ord(character):04X}", font=label, fill="#5e5264")
    image.save(PROOF, "PNG", optimize=True)
    render_path.unlink(missing_ok=True)
    print(f"Wrote {REPORT.relative_to(REPO_ROOT)}")
    print(f"Wrote {PROOF.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
