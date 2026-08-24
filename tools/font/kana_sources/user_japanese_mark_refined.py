"""Dedicated project-local center-line source for 々 (U+3005).

The supplied user reference defines the structural relationship only.  The
raster is not embedded or traced; these original center-lines are rendered by
the existing QuanFangwei variable-width handwriting stroke engine.
"""

from __future__ import annotations

from japanese.stroke_engine import Stroke


def S(*points, width=48, start=None, end=None, cap="round") -> Stroke:
    return Stroke(tuple(points), width, start, end, cap)


USER_JAPANESE_MARK_REFINED: dict[str, tuple[Stroke, ...]] = {
    "々": (
        S((355, 800), (410, 778), (425, 730), (390, 650),
          (330, 535), (250, 420), (150, 305), width=54, start=48, end=30),
        S((380, 560), (505, 578), (640, 590), (720, 575),
          width=48, start=43, end=31),
        S((715, 575), (650, 470), (570, 365), (500, 318),
          width=53, start=47, end=31),
        S((335, 365), (450, 340), (560, 295), (660, 205),
          width=54, start=47, end=31),
    ),
}
