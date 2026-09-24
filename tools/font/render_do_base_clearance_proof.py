#!/usr/bin/env python3
"""Render the reviewed U+3069 body-size candidates and final proof."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import tempfile

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from PIL import Image, ImageDraw, ImageFont
import uharfbuzz as hb

from measure_do_base_clearance import (
    BASE_MAIN, CANDIDATES, DO_BASE_GLYPH, FINAL_DO_SCALE, FINAL_TO_SCALE, PROOF, REPORT,
    TTF, baseline_bytes, candidate_font, derived_glyph, measure,
)
from verify_supplement_font import bounds


BACKGROUND = "#fffdf9"
INK = "#211b28"
MUTED = "#736c76"
ACCENT = "#813b56"
label = lambda size: ImageFont.load_default(size=size)


class ShapedFont:
    """HarfBuzz shaping plus PUA-addressed FreeType glyph drawing."""

    def __init__(self, path: Path, temp: Path):
        raw = path.read_bytes()
        self.normal = hb.Font(hb.Face(raw))
        self.normal.scale = (1024, 1024)
        font = TTFont(BytesIO(raw), recalcTimestamp=False)
        for table in font["cmap"].tables:
            if table.isUnicode() and hasattr(table, "cmap"):
                table.cmap.pop(0x3069, None)
        stream = BytesIO()
        font.save(stream)
        self.decomposed = hb.Font(hb.Face(stream.getvalue()))
        self.decomposed.scale = (1024, 1024)
        pua = CmapSubtable.newSubtable(12)
        pua.platformID, pua.platEncID, pua.language = 3, 10, 0
        pua.cmap = {0xF0000 + i: name for i, name in enumerate(font.getGlyphOrder())}
        font["cmap"].tables = [pua]
        self.path = temp / f"{path.stem}-{len(list(temp.iterdir()))}-glyphs.ttf"
        font.save(self.path)
        self.sizes = {}

    def draw(self, draw, x, baseline, text, size, fill=INK, force_decomposed=False):
        if size not in self.sizes:
            self.sizes[size] = ImageFont.truetype(str(self.path), size)
        face = self.decomposed if force_decomposed else self.normal
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(face, buffer, {"ccmp": True, "mark": True})
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions):
            draw.text(
                (x + position.x_offset * size / 1024, baseline - position.y_offset * size / 1024),
                chr(0xF0000 + info.codepoint), font=self.sizes[size], anchor="ls", fill=fill,
            )
            x += position.x_advance * size / 1024
        return x


def render_panel(versions, size):
    rows = (
        ("standalone / precomposed / decomposed", "と　ど　ど"),
        ("comparison", "と　ど"),
        ("retained TE / DE", "て　で"),
        ("combined comparison", "と　ど　て　で"),
        ("natural", "どこ"), ("natural", "どう"), ("natural", "だけど"),
        ("natural", "けれど"), ("natural", "踊って"), ("natural", "何度"), ("natural", "今度"),
    )
    column = 700
    step = max(size + 33, 66)
    height = 76 + len(rows) * step
    image = Image.new("RGB", (column * len(versions), height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for i, (caption, shaped) in enumerate(versions):
        left = i * column + 20
        draw.text((left, 12), f"{size}px | {caption}", font=label(22), fill=ACCENT)
        for row, (kind, text) in enumerate(rows):
            baseline = 66 + row * step + size
            draw.text((left, baseline - size - 4), kind, font=label(14), fill=MUTED)
            draw.line((left, baseline, left + column - 35, baseline), fill="#e4dde4")
            if text == "と　ど　ど":
                x = shaped.draw(draw, left + 170, baseline, "と　ど　", size)
                shaped.draw(draw, x, baseline, "ど", size, force_decomposed=True)
            else:
                shaped.draw(draw, left + 170, baseline, text, size)
    return image


def main():
    with tempfile.TemporaryDirectory(prefix="qfw-do-proof-") as directory:
        temp = Path(directory)
        before_path = temp / "current-1.029.ttf"
        before_path.write_bytes(baseline_bytes())
        versions = [("CURRENT 1.029", ShapedFont(before_path, temp))]
        candidate_metrics = {}
        for index, (to_scale, do_scale) in enumerate(CANDIDATES):
            font = candidate_font(to_scale, do_scale)
            path = temp / f"candidate-{to_scale:.2f}-{do_scale:.2f}.ttf"
            font.save(path)
            baseline = TTFont(BytesIO(baseline_bytes()))
            _, to_transform = derived_glyph(baseline, "uni3068", to_scale)
            _, do_transform = derived_glyph(font, "uni3068", do_scale)
            candidate_metrics[chr(65 + index)] = {
                "label": f"candidate {chr(65 + index)}",
                "standalone_to_scale": to_scale,
                "voiced_relative_scale": do_scale,
                "voiced_effective_scale": to_scale * do_scale,
                "standalone_to_transform": list(to_transform),
                "voiced_transform": list(do_transform),
                "standalone_to_bounds": list(bounds(font, "uni3068")),
                **measure(font),
            }
            versions.append((f"candidate {chr(65 + index)} · と {to_scale:.2f} / ど ×{do_scale:.2f}", ShapedFont(path, temp)))
            font.close()
        versions.append((f"FINAL · と {FINAL_TO_SCALE:.2f} / ど ×{FINAL_DO_SCALE:.2f}", ShapedFont(TTF, temp)))

        panels = [render_panel(versions, size) for size in (20, 32, 64, 192)]
        canvas = Image.new("RGB", (max(p.width for p in panels), 94 + sum(p.height for p in panels)), BACKGROUND)
        draw = ImageDraw.Draw(canvas)
        draw.text((20, 12), "QuanFangwei 1.030 | subtle TO reduction + clearer DO / dakuten gap", font=label(30), fill=INK)
        draw.text((20, 52), "Actual 20 / 32 / 64 / 192 px; HarfBuzz + FreeType; dakuten position fixed; bottom fixed at -14", font=label(21), fill=MUTED)
        y = 94
        for panel in panels:
            canvas.paste(panel, (0, y))
            y += panel.height
        canvas.save(PROOF, optimize=True)

        with TTFont(BytesIO(baseline_bytes())) as before, TTFont(TTF) as final:
            result = {
                "base_main": BASE_MAIN,
                "version": "1.030",
                "current": {
                    "standalone_to_scale": 1.0,
                    "standalone_to_bounds": list(bounds(before, "uni3068")),
                    "voiced_effective_scale": 0.94,
                    **measure(before),
                },
                "candidates": candidate_metrics,
                "final_to_scale": FINAL_TO_SCALE,
                "final_do_relative_scale": FINAL_DO_SCALE,
                "final": {
                    "standalone_to_scale": FINAL_TO_SCALE,
                    "standalone_to_bounds": list(bounds(final, "uni3068")),
                    "voiced_relative_scale": FINAL_DO_SCALE,
                    "voiced_effective_scale": FINAL_TO_SCALE * FINAL_DO_SCALE,
                    **measure(final),
                },
            }
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"proof": str(PROOF), "report": str(REPORT), **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
