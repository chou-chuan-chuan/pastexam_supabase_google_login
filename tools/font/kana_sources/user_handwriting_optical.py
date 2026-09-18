"""Optical transforms around the accepted user-handwriting Hiragana source.

The accepted ``USER_HANDWRITING_REFINED`` center-lines are authoritative,
including the explicit Version 1.021 topology replacement for U+304D き and
the Version 1.022 topology replacement for U+3084 や.
This module never substitutes an older kana source and never changes branch or
point topology.  It only applies conservative per-glyph scale and translation
transforms after the accepted source has been installed. Axis-specific scaling
is reserved for an explicitly reviewed optical-width correction such as す.

Stroke pressure is intentionally left unchanged: the adjustment changes the
optical body size while preserving the established handwriting weight.
"""

from __future__ import annotations

from dataclasses import dataclass

from japanese.stroke_engine import Stroke
from kana_sources.user_handwriting_refined import (
    MODERN_HIRAGANA_ORDER,
    USER_HANDWRITING_REFINED,
)


@dataclass(frozen=True)
class OpticalTransform:
    scale: float = 1.0
    dx: float = 0.0
    dy: float = 0.0
    scale_x: float | None = None
    scale_y: float | None = None


OPTICAL_CENTER = (480.0, 500.0)


def transform_strokes(
    strokes: tuple[Stroke, ...],
    transform: OpticalTransform,
    center: tuple[float, float] = OPTICAL_CENTER,
) -> tuple[Stroke, ...]:
    """Apply a topology-preserving center-line transform."""
    if transform == OpticalTransform():
        return strokes
    scale_x = transform.scale if transform.scale_x is None else transform.scale_x
    scale_y = transform.scale if transform.scale_y is None else transform.scale_y
    return tuple(
        Stroke(
            tuple(
                (
                    center[0] + (x - center[0]) * scale_x + transform.dx,
                    center[1] + (y - center[1]) * scale_y + transform.dy,
                )
                for x, y in stroke.points
            ),
            stroke.width,
            stroke.start_width,
            stroke.end_width,
            stroke.cap,
        )
        for stroke in strokes
    )


# Version 1.025: re-reviewed uniform photo fits need no additional transform.
# Only the omitted na-row retains its exact previous optical adjustments.
HIRAGANA_OPTICAL_TRANSFORMS: dict[str, OpticalTransform] = {
    "あ": OpticalTransform(),
    "い": OpticalTransform(),
    "う": OpticalTransform(),
    "え": OpticalTransform(),
    "お": OpticalTransform(),
    "か": OpticalTransform(),
    "き": OpticalTransform(),
    "く": OpticalTransform(),
    "け": OpticalTransform(),
    "こ": OpticalTransform(),
    "さ": OpticalTransform(),
    "し": OpticalTransform(),
    "す": OpticalTransform(),
    "せ": OpticalTransform(),
    "そ": OpticalTransform(),
    "た": OpticalTransform(),
    "ち": OpticalTransform(),
    "つ": OpticalTransform(),
    "て": OpticalTransform(),
    "と": OpticalTransform(),
    "な": OpticalTransform(),
    "に": OpticalTransform(),
    "ぬ": OpticalTransform(0.97),
    "ね": OpticalTransform(0.95),
    "の": OpticalTransform(1.06),
    "は": OpticalTransform(),
    "ひ": OpticalTransform(),
    "ふ": OpticalTransform(),
    "へ": OpticalTransform(),
    "ほ": OpticalTransform(),
    "ま": OpticalTransform(),
    "み": OpticalTransform(),
    "む": OpticalTransform(),
    "め": OpticalTransform(),
    "も": OpticalTransform(),
    "や": OpticalTransform(),
    "ゆ": OpticalTransform(),
    "よ": OpticalTransform(),
    "ら": OpticalTransform(),
    "り": OpticalTransform(),
    "る": OpticalTransform(),
    "れ": OpticalTransform(),
    "ろ": OpticalTransform(),
    "わ": OpticalTransform(),
    "を": OpticalTransform(),
    "ん": OpticalTransform(),
}

assert set(HIRAGANA_OPTICAL_TRANSFORMS) == set(MODERN_HIRAGANA_ORDER)

USER_HANDWRITING_OPTICALLY_NORMALIZED = {
    character: transform_strokes(
        USER_HANDWRITING_REFINED[character],
        HIRAGANA_OPTICAL_TRANSFORMS[character],
    )
    for character in MODERN_HIRAGANA_ORDER
}
