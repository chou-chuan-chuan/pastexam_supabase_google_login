"""Reference loader for the maintainer-authored Hiragana SVG templates.

Version 1.011 keeps the 46 SVGs as reviewable structural source artwork, but
THE FONT BUILD NO LONGER INSTALLS THESE FILLED SVG OUTLINES DIRECTLY. Final
Hiragana outlines come from ``kana_sources.user_handwriting_refined`` and the
existing variable-width ``japanese.stroke_engine``. The helper below remains
available only for reference/proof comparison and provenance checks.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path


MODERN_HIRAGANA_ORDER = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
SVG_TEMPLATE_SOURCE_CHARACTERS = frozenset(MODERN_HIRAGANA_ORDER)
SVG_TEMPLATE_SMALL_MAP = {
    "ぁ": "あ", "ぃ": "い", "ぅ": "う", "ぇ": "え", "ぉ": "お",
    "ゃ": "や", "ゅ": "ゆ", "ょ": "よ", "っ": "つ", "ゎ": "わ",
    "ゕ": "か", "ゖ": "け",
}
SVG_TEMPLATE_CHARACTERS = frozenset(SVG_TEMPLATE_SOURCE_CHARACTERS | SVG_TEMPLATE_SMALL_MAP.keys())

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "references" / "user-hiragana-svg"
REFERENCE_SCALE = 1.10
REFERENCE_CENTER = (480, 500)
SMALL_SCALE = 0.72
SMALL_CENTER = (500, 470)
SMALL_SHIFT = (0, -12)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


@lru_cache(maxsize=None)
def svg_path_data(character: str) -> tuple[str, ...]:
    source = SVG_TEMPLATE_SMALL_MAP.get(character, character)
    if source not in SVG_TEMPLATE_SOURCE_CHARACTERS:
        raise KeyError(f"No user-handwriting SVG template for {character!r}")
    path = TEMPLATE_DIR / f"U+{ord(source):04X}.svg"
    if not path.is_file():
        raise FileNotFoundError(f"Missing user-handwriting SVG template: {path}")
    root = ET.parse(path).getroot()
    values = tuple(
        element.attrib["d"]
        for element in root.iter()
        if _local_name(element.tag) == "path" and element.attrib.get("d")
    )
    if not values:
        raise ValueError(f"SVG template contains no path data: {path}")
    return values


def svg_reference_transform(character: str, vertical_shift: float = -145) -> Transform:
    """Legacy/reference transform used only for visual comparison."""
    transform = Transform().translate(0, vertical_shift)
    if character in SVG_TEMPLATE_SMALL_MAP:
        transform = (
            transform
            .translate(SMALL_CENTER[0] + SMALL_SHIFT[0], SMALL_CENTER[1] + SMALL_SHIFT[1])
            .scale(SMALL_SCALE)
            .translate(-SMALL_CENTER[0], -SMALL_CENTER[1])
        )
    return (
        transform
        .translate(*REFERENCE_CENTER)
        .scale(REFERENCE_SCALE)
        .translate(-REFERENCE_CENTER[0], -REFERENCE_CENTER[1])
    )


def build_svg_reference_glyph(character: str, vertical_shift: float = -145):
    """Build a direct SVG outline ONLY for proof/reference comparison."""
    if character not in SVG_TEMPLATE_CHARACTERS:
        raise KeyError(f"Character is not covered by the user SVG templates: {character!r}")
    pen = TTGlyphPen(None)
    transformed = TransformPen(pen, svg_reference_transform(character, vertical_shift))
    for path_data in svg_path_data(character):
        parse_path(path_data, transformed)
    glyph = pen.glyph()
    if glyph.numberOfContours <= 0:
        raise ValueError(f"SVG template built an empty reference glyph for {character!r}")
    return glyph
