"""Build Hiragana glyphs from the maintainer's user-authored SVG templates.

The SVG files are project-local source artwork created from the maintainer's
own handwritten chart.  Their path data uses the font's y-up coordinates.
The SVG group transform exists only for upright browser display and is
intentionally ignored here; only each path's ``d`` attribute is parsed.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path


SVG_TEMPLATE_SOURCE_ORDER = (
    "あかさたなはまやら"
    "いきしちにひみり"
    "うくすつぬふむゆる"
    "えけせてねへめれ"
    "おこそとのほもよろ"
)
SVG_TEMPLATE_SOURCE_CHARACTERS = frozenset(SVG_TEMPLATE_SOURCE_ORDER)
SVG_TEMPLATE_SMALL_MAP = {
    "ぁ": "あ", "ぃ": "い", "ぅ": "う", "ぇ": "え", "ぉ": "お",
    "ゃ": "や", "ゅ": "ゆ", "ょ": "よ", "っ": "つ",
    "ゕ": "か", "ゖ": "け",
}
SVG_TEMPLATE_CHARACTERS = frozenset(SVG_TEMPLATE_SOURCE_CHARACTERS | SVG_TEMPLATE_SMALL_MAP.keys())

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "references" / "user-hiragana-svg"
GLOBAL_SCALE = 1.10
GLOBAL_CENTER = (480, 500)
SMALL_SCALE = 0.72
SMALL_CENTER = (500, 470)
SMALL_SHIFT = (0, -12)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


@lru_cache(maxsize=None)
def svg_path_data(character: str) -> tuple[str, ...]:
    """Return raw y-up path data for one source character."""
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


def svg_template_transform(character: str, vertical_shift: float = -145) -> Transform:
    """Return the deterministic template-to-font affine transform."""
    # Transform chaining is intentionally written in reverse visual order:
    # fontTools applies the rightmost transform first.  Thus source paths are
    # globally optically scaled, optionally reduced for small kana, then moved
    # to the shared Japanese baseline.
    transform = Transform().translate(0, vertical_shift)
    if character in SVG_TEMPLATE_SMALL_MAP:
        transform = (
            transform
            .translate(SMALL_CENTER[0] + SMALL_SHIFT[0], SMALL_CENTER[1] + SMALL_SHIFT[1])
            .scale(SMALL_SCALE)
            .translate(-SMALL_CENTER[0], -SMALL_CENTER[1])
        )
    transform = (
        transform
        .translate(*GLOBAL_CENTER)
        .scale(GLOBAL_SCALE)
        .translate(-GLOBAL_CENTER[0], -GLOBAL_CENTER[1])
    )
    return transform


def build_svg_template_glyph(character: str, vertical_shift: float = -145):
    """Build one simple TrueType glyph from a reviewed SVG template."""
    if character not in SVG_TEMPLATE_CHARACTERS:
        raise KeyError(f"Character is not covered by the user SVG templates: {character!r}")
    pen = TTGlyphPen(None)
    transformed = TransformPen(pen, svg_template_transform(character, vertical_shift))
    for path_data in svg_path_data(character):
        parse_path(path_data, transformed)
    glyph = pen.glyph()
    if glyph.numberOfContours <= 0:
        raise ValueError(f"SVG template built an empty glyph for {character!r}")
    return glyph
