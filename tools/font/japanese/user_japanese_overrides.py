"""Build dedicated user-reference Japanese shared-codepoint overrides.

懐 U+61D0 combines the source face's native 懷 and 衣 outlines. 々 U+3005 is
rebuilt from dedicated project-local center-lines.
夕 U+5915 is deliberately untouched. 気 U+6C17, 付 U+4ED8, and 容 U+5BB9 keep the source font's
original drawings, but are installed under distinct derived glyph names with
an optical vertical transform so the mixed sequence 気付け aligns better with
refined Hiragana.  Original source glyphs remain present and unmodified.
"""

from __future__ import annotations

from dataclasses import dataclass

import pathops

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from japanese.stroke_engine import (
    build_stroke_glyph,
    path_to_glyph,
    translate_strokes,
)
from kana_sources.user_kanji_refined import (
    ALIGNMENT_OVERRIDE_CHARACTERS,
    HYBRID_FINAL_SHIFT,
    HYBRID_KANJI_CHARACTERS,
    HYBRID_KEEP_LEFT_MAX,
    HYBRID_KEEP_UPPER_MIN,
    HYBRID_REPLACEMENT_CHARACTER,
    HYBRID_REPLACEMENT_TRANSFORM,
    HYBRID_SOURCE_CHARACTER,
)
from kana_sources.user_japanese_mark_refined import USER_JAPANESE_MARK_REFINED


USER_OVERRIDE_SUFFIX = ".qfwUser"
USER_MARK_POSITION = (45.0, -120.0)
USER_MARK_ADVANCE = 960
ALIGN_OVERRIDE_SUFFIX = ".qfwJaAlign"
ALIGNMENT_REFERENCE = "け"
ALIGNMENT_TARGET_HEIGHT_FACTOR = 1.04
ALIGNMENT_SCALE_CLAMP = (0.88, 1.04)
ALIGNMENT_OPTICAL_Y = {"気": 30.0, "付": 6.0}
OPTICAL_ALIGNMENT_SUFFIX = ".qfwJaOptical"
OKU_REFERENCE_CENTER = (395.0, 354.0)


@dataclass(frozen=True)
class SourceOpticalTransform:
    """Scale around source ink center, then translate without altering source."""

    scale_x: float
    scale_y: float
    dx: float
    dy: float
    embolden: float = 0.0
    advance: int | None = None


# These shared Han codepoints have no language-specific cmap distinction in the
# current font. Conservative derived copies improve Japanese mixed-text balance
# while the original ChenYuluoyan glyph drawings remain present and untouched.
SHARED_HAN_OPTICAL_TRANSFORMS: dict[str, SourceOpticalTransform] = {
    "奥": SourceOpticalTransform(0.921976, 0.855348, 9.0, 34.5, 4.0, advance=790),
    "容": SourceOpticalTransform(1.00, 1.00, 19.45, 35.0),
    "変": SourceOpticalTransform(0.80, 0.80, 19.25, 35.0, 8.0),
    "恋": SourceOpticalTransform(0.98, 0.98, 17.5, 35.0),
    "哀": SourceOpticalTransform(0.93, 0.93, 15.5, 36.0),
    "奧": SourceOpticalTransform(0.94, 0.94, 19.0, 34.5),
    "優": SourceOpticalTransform(0.90, 0.90, 19.5, 35.0),
    "寄": SourceOpticalTransform(0.92, 0.92, 18.5, 36.0),
}


def glyph_bounds(font: TTFont, glyph_name: str) -> tuple[float, float, float, float]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"Glyph {glyph_name!r} has no bounds")
    return pen.bounds


def add_mapping(font: TTFont, codepoint: int, name: str) -> None:
    mapped = 0
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format != 14:
            table.cmap[codepoint] = name
            mapped += 1
    if not mapped:
        raise RuntimeError(f"No Unicode cmap accepts U+{codepoint:04X}")


def install(font: TTFont, name: str, glyph, advance: int, lsb: int, vertical_source: str) -> None:
    order = font.getGlyphOrder()
    if name not in order:
        order.append(name)
        font.setGlyphOrder(order)
    font["glyf"][name] = glyph
    glyph.recalcBounds(font["glyf"])
    font["hmtx"].metrics[name] = (int(advance), int(lsb))
    if "vmtx" in font:
        font["vmtx"].metrics[name] = font["vmtx"].metrics[vertical_source]
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def transformed_glyph(font: TTFont, source_name: str, transform: Transform):
    pen = TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()[source_name].draw(TransformPen(pen, transform))
    return pen.glyph()


def transformed_emboldened_glyph(
    font: TTFont,
    source_name: str,
    transform: Transform,
    embolden: float,
):
    """Transform a source outline, then restore weight without changing it."""
    def cubic_path() -> pathops.Path:
        result = pathops.Path()
        cubic_pen = Qu2CuPen(result.getPen(), max_err=1.0, all_cubic=True)
        font.getGlyphSet()[source_name].draw(TransformPen(cubic_pen, transform))
        return result

    # PathOps boolean operations do not accept TrueType CONIC verbs. Convert
    # the temporary work path to cubic curves; path_to_glyph converts the final
    # union back to quadratic outlines for the built TTF.
    original = cubic_path()
    boundary = cubic_path()
    boundary.stroke(
        embolden,
        pathops.LineCap.BUTT_CAP,
        pathops.LineJoin.BEVEL_JOIN,
        4.0,
    )
    combined = pathops.op(original, boundary, pathops.PathOp.UNION)
    return path_to_glyph(pathops.simplify(combined))


def centered_optical_transform(
    source_bounds: tuple[float, float, float, float],
    transform: SourceOpticalTransform,
) -> Transform:
    """Return a matrix that scales around ink center before dx/dy translation."""
    x_min, y_min, x_max, y_max = source_bounds
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    return Transform(
        transform.scale_x,
        0,
        0,
        transform.scale_y,
        center_x * (1 - transform.scale_x) + transform.dx,
        center_y * (1 - transform.scale_y) + transform.dy,
    )


def rectangle_path(x_min: float, y_min: float, x_max: float, y_max: float) -> pathops.Path:
    path = pathops.Path()
    pen = path.getPen()
    pen.moveTo((x_min, y_min))
    pen.lineTo((x_max, y_min))
    pen.lineTo((x_max, y_max))
    pen.lineTo((x_min, y_max))
    pen.closePath()
    return path


def hybrid_kanji_glyph(font: TTFont, source_name: str, replacement_name: str):
    """Keep native 懷 upper/left outlines and fit the native 衣 below them."""
    source_path = pathops.Path()
    source_transform = Transform(1, 0, 0, 1, *HYBRID_FINAL_SHIFT)
    font.getGlyphSet()[source_name].draw(TransformPen(source_path.getPen(), source_transform))
    left_region = rectangle_path(-200, -300, HYBRID_KEEP_LEFT_MAX, 1200)
    upper_region = rectangle_path(HYBRID_KEEP_LEFT_MAX, HYBRID_KEEP_UPPER_MIN, 1400, 1200)
    keep_region = pathops.op(left_region, upper_region, pathops.PathOp.UNION)
    kept_source = pathops.op(source_path, keep_region, pathops.PathOp.INTERSECTION)
    replacement = pathops.Path()
    scale, dx, dy = HYBRID_REPLACEMENT_TRANSFORM
    replacement_transform = Transform(scale, 0, 0, scale, dx, dy)
    font.getGlyphSet()[replacement_name].draw(
        TransformPen(replacement.getPen(), replacement_transform)
    )
    combined = pathops.op(kept_source, replacement, pathops.PathOp.UNION)
    return path_to_glyph(pathops.simplify(combined))


def build_user_japanese_overrides(font: TTFont) -> dict:
    cmap = font.getBestCmap()
    metadata: dict[str, object] = {
        "handwritten": {},
        "marks": {},
        "alignment": {},
        "optical_alignment": {},
    }

    # Rebuild the approved hybrid Han character from the source face's native
    # 懷 and 衣 structures while preserving the target codepoint and advance.
    for character in HYBRID_KANJI_CHARACTERS:
        codepoint = ord(character)
        source_name = cmap.get(codepoint)
        if source_name is None:
            raise RuntimeError(f"Source font is missing U+{codepoint:04X} {character}")
        advance, _ = font["hmtx"].metrics[source_name]
        target_name = f"uni{codepoint:04X}{USER_OVERRIDE_SUFFIX}"
        style_character = HYBRID_SOURCE_CHARACTER[character]
        style_source_name = cmap.get(ord(style_character))
        if style_source_name is None:
            raise RuntimeError(f"Source font is missing style source {style_character}")
        replacement_character = HYBRID_REPLACEMENT_CHARACTER[character]
        replacement_source_name = cmap.get(ord(replacement_character))
        if replacement_source_name is None:
            raise RuntimeError(
                f"Source font is missing replacement source {replacement_character}"
            )
        glyph = hybrid_kanji_glyph(font, style_source_name, replacement_source_name)
        glyph.recalcBounds(font["glyf"])
        install(font, target_name, glyph, advance, glyph.xMin, source_name)
        add_mapping(font, codepoint, target_name)
        metadata["handwritten"][character] = {
            "source_glyph": source_name,
            "style_source_character": style_character,
            "style_source_glyph": style_source_name,
            "replacement_source_character": replacement_character,
            "replacement_source_glyph": replacement_source_name,
            "replacement_transform": HYBRID_REPLACEMENT_TRANSFORM,
            "derived_glyph": target_name,
            "advance": advance,
            "hybrid_final_shift": HYBRID_FINAL_SHIFT,
        }

    # Install the dedicated 々 drawing even when the source font already maps
    # that shared codepoint. The former Phase-1 mark is not used as input.
    cmap = font.getBestCmap()
    vertical_fallback = cmap[0x4E00]
    for character, strokes in USER_JAPANESE_MARK_REFINED.items():
        codepoint = ord(character)
        source_name = cmap.get(codepoint)
        vertical_source = source_name or vertical_fallback
        advance = USER_MARK_ADVANCE
        target_name = f"uni{codepoint:04X}{USER_OVERRIDE_SUFFIX}"
        positioned_strokes = translate_strokes(
            strokes,
            dx=USER_MARK_POSITION[0],
            dy=USER_MARK_POSITION[1],
        )
        glyph = build_stroke_glyph(positioned_strokes)
        glyph.recalcBounds(font["glyf"])
        install(font, target_name, glyph, advance, glyph.xMin, vertical_source)
        add_mapping(font, codepoint, target_name)
        metadata["marks"][character] = {
            "source_glyph": source_name,
            "derived_glyph": target_name,
            "advance": advance,
            "dx": USER_MARK_POSITION[0],
            "dy": USER_MARK_POSITION[1],
        }

    # Install source-preserving optical copies for the explicitly reviewed
    # shared Han codepoints. This deliberately does not add a broad locl JAN
    # system; source outlines stay unchanged and advances remain source-native.
    cmap = font.getBestCmap()
    for character, optical in SHARED_HAN_OPTICAL_TRANSFORMS.items():
        codepoint = ord(character)
        source_name = cmap.get(codepoint)
        if source_name is None:
            raise RuntimeError(f"Source font is missing U+{codepoint:04X} {character}")
        source_bounds = glyph_bounds(font, source_name)
        target_name = f"{source_name}{OPTICAL_ALIGNMENT_SUFFIX}"
        source_advance, _ = font["hmtx"].metrics[source_name]
        advance = optical.advance if optical.advance is not None else source_advance
        if character == "奥":
            # PathOps boundary expansion is slightly sensitive to sub-unit
            # translation. Build at the authoritative reference center first,
            # then translate the completed outline until its measured center
            # matches the browser-approved E1 copy. The recorded dx/dy remain
            # the final effective translation after scaling and emboldening.
            source_center_x = (source_bounds[0] + source_bounds[2]) / 2
            source_center_y = (source_bounds[1] + source_bounds[3]) / 2
            effective_dx = OKU_REFERENCE_CENTER[0] - source_center_x
            effective_dy = OKU_REFERENCE_CENTER[1] - source_center_y
            initial = SourceOpticalTransform(
                optical.scale_x,
                optical.scale_y,
                effective_dx,
                effective_dy,
                optical.embolden,
                optical.advance,
            )
            matrix = centered_optical_transform(source_bounds, initial)
            glyph = transformed_emboldened_glyph(font, source_name, matrix, optical.embolden)
            glyph.recalcBounds(font["glyf"])
            install(font, target_name, glyph, advance, glyph.xMin, source_name)
            for _iteration in range(4):
                actual_bounds = glyph_bounds(font, target_name)
                actual_center_x = (actual_bounds[0] + actual_bounds[2]) / 2
                actual_center_y = (actual_bounds[1] + actual_bounds[3]) / 2
                correction_x = OKU_REFERENCE_CENTER[0] - actual_center_x
                correction_y = OKU_REFERENCE_CENTER[1] - actual_center_y
                if abs(correction_x) <= 0.001 and abs(correction_y) <= 0.001:
                    break
                glyph = transformed_glyph(
                    font,
                    target_name,
                    Transform(1, 0, 0, 1, correction_x, correction_y),
                )
                glyph.recalcBounds(font["glyf"])
                install(font, target_name, glyph, advance, glyph.xMin, source_name)
                effective_dx += correction_x
                effective_dy += correction_y
            if abs(effective_dx - optical.dx) > 0.001 or abs(effective_dy - optical.dy) > 0.001:
                raise RuntimeError(
                    f"U+5965 final centering changed: dx={effective_dx}, dy={effective_dy}"
                )
        else:
            matrix = centered_optical_transform(source_bounds, optical)
            glyph = (
                transformed_emboldened_glyph(font, source_name, matrix, optical.embolden)
                if optical.embolden
                else transformed_glyph(font, source_name, matrix)
            )
            glyph.recalcBounds(font["glyf"])
            install(font, target_name, glyph, advance, glyph.xMin, source_name)
        add_mapping(font, codepoint, target_name)
        metadata["optical_alignment"][character] = {
            "source_glyph": source_name,
            "derived_glyph": target_name,
            "scale_x": optical.scale_x,
            "scale_y": optical.scale_y,
            "dx": optical.dx,
            "dy": optical.dy,
            "embolden": optical.embolden,
            "matrix_dx": round(matrix.dx, 3),
            "matrix_dy": round(matrix.dy, 3),
            "advance": advance,
            "source_advance": source_advance,
        }

    # Re-read cmap after the handwritten remaps.  The reference Hiragana glyph
    # already exists because this function runs after build_japanese_phase1().
    cmap = font.getBestCmap()
    reference_name = cmap.get(ord(ALIGNMENT_REFERENCE))
    if reference_name is None:
        raise RuntimeError("Refined Hiragana reference glyph け is unavailable")
    ref_bounds = glyph_bounds(font, reference_name)
    ref_height = ref_bounds[3] - ref_bounds[1]
    ref_center = (ref_bounds[1] + ref_bounds[3]) / 2
    target_height = ref_height * ALIGNMENT_TARGET_HEIGHT_FACTOR

    for character in ALIGNMENT_OVERRIDE_CHARACTERS:
        codepoint = ord(character)
        source_name = cmap.get(codepoint)
        if source_name is None:
            raise RuntimeError(f"Source font is missing U+{codepoint:04X} {character}")
        source_bounds = glyph_bounds(font, source_name)
        source_height = source_bounds[3] - source_bounds[1]
        source_center = (source_bounds[1] + source_bounds[3]) / 2
        scale_y = target_height / source_height
        scale_y = min(ALIGNMENT_SCALE_CLAMP[1], max(ALIGNMENT_SCALE_CLAMP[0], scale_y))
        dy = ref_center - source_center * scale_y + ALIGNMENT_OPTICAL_Y.get(character, 0.0)
        transform = Transform(1, 0, 0, scale_y, 0, dy)
        target_name = f"{source_name}{ALIGN_OVERRIDE_SUFFIX}"
        glyph = transformed_glyph(font, source_name, transform)
        glyph.recalcBounds(font["glyf"])
        advance, lsb = font["hmtx"].metrics[source_name]
        install(font, target_name, glyph, advance, lsb, source_name)
        add_mapping(font, codepoint, target_name)
        metadata["alignment"][character] = {
            "source_glyph": source_name,
            "derived_glyph": target_name,
            "scale_y": round(scale_y, 6),
            "dy": round(dy, 3),
            "optical_y_correction": ALIGNMENT_OPTICAL_Y.get(character, 0.0),
            "reference_glyph": reference_name,
        }

    return metadata
