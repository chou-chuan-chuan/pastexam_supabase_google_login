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


# Every accepted modern Hiragana is listed so this file doubles as the optical
# review record. Identity entries were reviewed and intentionally retained.
HIRAGANA_OPTICAL_TRANSFORMS: dict[str, OpticalTransform] = {
    "あ": OpticalTransform(0.98),
    "い": OpticalTransform(),
    # Version 1.024: the new two-stroke maintainer source remains within the
    # previously reviewed う optical body; retain its scoped normalization.
    "う": OpticalTransform(1.08, 0.0, -20.0, scale_x=1.12, scale_y=1.08),
    "え": OpticalTransform(),
    # Version 1.024: the repaired three-stroke maintainer source fills the
    # accepted Hiragana zone with balanced left/right space.
    "お": OpticalTransform(),
    "か": OpticalTransform(),
    # Version 1.021: keep the reviewed 0.96 size and move the new four-stroke
    # source 24 units right to balance its visual weight in mixed kana text.
    "き": OpticalTransform(0.96, 24.0, 0.0),
    "く": OpticalTransform(),
    # Version 1.016: retain size and move the accepted drawing right/down.
    "け": OpticalTransform(1.0, 28.0, -26.0, scale_x=1.06, scale_y=1.0),
    # Version 1.016: retain size and move the accepted drawing slightly right.
    "こ": OpticalTransform(1.0, 28.0, 0.0),
    "さ": OpticalTransform(),
    "し": OpticalTransform(),
    # Keep the accepted handwritten structure and reviewed optical body. The
    # Version 1.024 repair changes only per-stroke pressure in the source; this
    # established placement remains intentionally unchanged.
    "す": OpticalTransform(1.04, 59.0, -47.0, scale_x=1.60, scale_y=1.04),
    "せ": OpticalTransform(),
    "そ": OpticalTransform(),
    "た": OpticalTransform(0.96),
    "ち": OpticalTransform(0.96),
    "つ": OpticalTransform(1.07, 0.0, -6.0),
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
    "へ": OpticalTransform(1.08, 0.0, 8.0),
    "ほ": OpticalTransform(1.04),
    "ま": OpticalTransform(0.98),
    "み": OpticalTransform(),
    "む": OpticalTransform(),
    "め": OpticalTransform(),
    "も": OpticalTransform(),
    # Version 1.022: the new three-stroke source is already proportioned and
    # centered for the family, so no additional optical transform is needed.
    "や": OpticalTransform(),
    "ゆ": OpticalTransform(),
    "よ": OpticalTransform(1.04),
    "ら": OpticalTransform(1.05),
    "り": OpticalTransform(0.97, 12.5, 25.0),
    "る": OpticalTransform(1.14),
    "れ": OpticalTransform(0.95),
    "ろ": OpticalTransform(1.10),
    "わ": OpticalTransform(0.94),
    "を": OpticalTransform(0.84),
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
