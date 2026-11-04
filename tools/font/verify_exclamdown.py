#!/usr/bin/env python3
"""Verify the 1.044 inverted-exclamation addition against released 1.043."""

from __future__ import annotations

import argparse
import copy
import hashlib
from io import BytesIO
from pathlib import Path
import subprocess

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
import uharfbuzz as hb


ROOT = Path(__file__).resolve().parents[2]
REL = "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
PREVIOUS_COMMIT = "5e495010e839b15f79add465b652903b935ba21b"
PREVIOUS_SHA256 = "f823a1985a8c73f07773e860d4894483c15dce65872cf8d7d4c35f94dabd2141"


def bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    assert pen.bounds is not None
    return tuple(round(value) for value in pen.bounds)


def drawing(font: TTFont, glyph_name: str):
    pen = RecordingPen()
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.value


def shape(font: TTFont, text: str):
    raw = BytesIO()
    font.flavor = None
    font.save(raw)
    hb_font = hb.Font(hb.Face(raw.getvalue()))
    hb_font.scale = (font["head"].unitsPerEm,) * 2
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(hb_font, buffer)
    return [
        (info.codepoint, info.cluster, pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset)
        for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)
    ]


def verify(previous: TTFont, current: TTFont) -> None:
    old_order = previous.getGlyphOrder()
    assert current.getGlyphOrder() == old_order + ["exclamdown"]
    assert 0x00A1 not in previous.getBestCmap()
    assert current.getBestCmap()[0x00A1] == "exclamdown"

    for glyph_name in old_order:
        if glyph_name not in {"uni30F2", "uni30FA"}:
            assert previous["glyf"][glyph_name].compile(previous["glyf"]) == current["glyf"][glyph_name].compile(current["glyf"]), glyph_name
        assert previous["hmtx"][glyph_name] == current["hmtx"][glyph_name], glyph_name
        if "vmtx" in previous:
            assert previous["vmtx"][glyph_name] == current["vmtx"][glyph_name], glyph_name

    for old, new in zip(previous["cmap"].tables, current["cmap"].tables):
        assert (old.platformID, old.platEncID, old.format) == (new.platformID, new.platEncID, new.format)
        expected = dict(old.cmap)
        if new.isUnicode() and new.format != 14:
            expected[0x00A1] = "exclamdown"
        assert new.cmap == expected
    assert len(previous["cmap"].tables) == len(current["cmap"].tables)

    source_name = current.getBestCmap()[0x0021]
    source_bounds = bounds(current, source_name)
    advance = current["hmtx"][source_name][0]
    expected_pen = RecordingPen()
    transform = Transform(-1, 0, 0, -1, advance, source_bounds[1] + source_bounds[3])
    current.getGlyphSet()[source_name].draw(TransformPen(expected_pen, transform))
    assert drawing(current, "exclamdown") == expected_pen.value
    assert bounds(current, "exclamdown") == (69, 128, 149, 530)
    assert current["hmtx"]["exclamdown"] == (215, 69)
    assert current["vmtx"]["exclamdown"] == previous["vmtx"][source_name]

    for tag in ("GPOS", "GDEF", "GSUB", "MATH", "OS/2", "kern"):
        if tag in previous:
            assert previous[tag].compile(previous) == current[tag].compile(current), tag
    for tag, count_field in (("hhea", "numberOfHMetrics"), ("vhea", "numberOfVMetrics")):
        if tag in previous:
            header = copy.deepcopy(current[tag])
            setattr(header, count_field, getattr(previous[tag], count_field))
            assert header.compile(current) == previous[tag].compile(previous), tag

    for text in (
        "¿Qué? ¡Hola!",
        "Œuvre cœur Ç ç ÄÖÜ äöü ßẞ",
        "ɥ ɛɪɔʊʏ əɐ ɐ̯ n̩",
        "中文 あいう マスズ ぱぴぷぺぽ",
        "∑ ∇ ∏ x̂ p̂ ℏ",
    ):
        if "¡" not in text:
            assert shape(previous, text) == shape(current, text), text
    assert all(item[0] > 0 for item in shape(current, "¡Hola! ¿Qué?"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    raw = args.baseline.read_bytes() if args.baseline else subprocess.check_output(
        ["git", "show", f"{PREVIOUS_COMMIT}:{REL}"], cwd=ROOT
    )
    assert hashlib.sha256(raw).hexdigest() == PREVIOUS_SHA256
    for extension in (".ttf", ".woff2"):
        verify(TTFont(BytesIO(raw)), TTFont((ROOT / REL).with_suffix(extension)))
    print("PASS: U+00A1 remains an exact rotated source exclamation; the independently verified 1.045 ヲ/ヺ change is the only later outline exception")


if __name__ == "__main__":
    main()
