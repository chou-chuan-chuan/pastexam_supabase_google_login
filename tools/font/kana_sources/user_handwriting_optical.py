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


# Version 1.025: uniform size/center fits from dimensionless standard Japanese
# metrics and production 1.024. See references/hiragana-metric-targets.json.
# These transforms preserve pen topology/aspect and do not scale pressure.
HIRAGANA_OPTICAL_TRANSFORMS: dict[str, OpticalTransform] = {
    "あ": OpticalTransform(1.143952, 19.334, 9.464),
    "い": OpticalTransform(1.16928, 29.776, -3.354),
    "う": OpticalTransform(1.113119, 6.826, 6.66),
    "え": OpticalTransform(1.056177, 21.144, 7.232),
    "お": OpticalTransform(1.128032, 30.08, 15.352),
    "か": OpticalTransform(0.973462, 27.258, 9.804),
    "き": OpticalTransform(1.141468, 21.614, 11.25),
    "く": OpticalTransform(1.033786, 0.5713, 6.684),
    "け": OpticalTransform(1.116316, 41.496, -11.174),
    "こ": OpticalTransform(1.009348, 30.298, -9.932),
    "さ": OpticalTransform(1.135719, 21.37, 11.786),
    "し": OpticalTransform(1.046484, 50.31, 6.624),
    "す": OpticalTransform(1.148392, 64.15, -9.822),
    "せ": OpticalTransform(1.241908, 9.802, 10.524),
    "そ": OpticalTransform(0.994174, 17.374, 3.0852),
    "た": OpticalTransform(1.142265, 17.804, 10.804),
    "ち": OpticalTransform(1.142458, 4.772, 8.918),
    "つ": OpticalTransform(0.932826, 11.136, 8.734),
    "て": OpticalTransform(1.04473, 10.802, -5.568),
    "と": OpticalTransform(1.10382, 26.752, 11.5),
    "な": OpticalTransform(1.104894, 22.156, 11.006),
    "に": OpticalTransform(1.066407, 22.388, 1.862),
    "ぬ": OpticalTransform(1.17419, 28.246, 16.114),
    "ね": OpticalTransform(1.20191, 23.418, 12.286),
    "の": OpticalTransform(0.959665, 17.726, -7.628),
    "は": OpticalTransform(1.0844, 34.39, 7.154),
    "ひ": OpticalTransform(1.253447, 29.58, -5.366),
    "ふ": OpticalTransform(1.18348, 16.274, 7.964),
    "へ": OpticalTransform(1.177765, 18.042, 11.6421),
    "ほ": OpticalTransform(1.09223, 32.866, 7.374),
    "ま": OpticalTransform(1.146067, 27.288, 9.738),
    "み": OpticalTransform(1.239516, 21.87, -6.854),
    "む": OpticalTransform(1.068027, 19.084, 7.756),
    "め": OpticalTransform(0.984943, 16.702, 10.178),
    "も": OpticalTransform(1.085869, 8.034, 8.976),
    "や": OpticalTransform(1.151094, 12.588, 10.03),
    "ゆ": OpticalTransform(1.129014, 26.234, 3.874),
    "よ": OpticalTransform(1.063839, 10.386, 4.934),
    "ら": OpticalTransform(1.08649, 24.93, 8.5033),
    "り": OpticalTransform(1.138791, 19.524, 8.952),
    "る": OpticalTransform(1.009113, 12.058, -1.484),
    "れ": OpticalTransform(1.282132, 22.918, 10.286),
    "ろ": OpticalTransform(0.972211, 7.76, -4.3511),
    "わ": OpticalTransform(1.111751, 19.4053, 21.036),
    "を": OpticalTransform(1.18494, 9.862, 9.018),
    "ん": OpticalTransform(1.068027, 24.138, 8.94),
}

assert set(HIRAGANA_OPTICAL_TRANSFORMS) == set(MODERN_HIRAGANA_ORDER)

USER_HANDWRITING_OPTICALLY_NORMALIZED = {
    character: transform_strokes(
        USER_HANDWRITING_REFINED[character],
        HIRAGANA_OPTICAL_TRANSFORMS[character],
    )
    for character in MODERN_HIRAGANA_ORDER
}
