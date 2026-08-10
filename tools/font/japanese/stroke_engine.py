"""Original variable-width handwriting stroke renderer.

The inputs are center-line point data authored in this repository. No outline
from another Japanese font is loaded or traced.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


@dataclass(frozen=True)
class Stroke:
    points: tuple[tuple[float, float], ...]
    width: float = 48
    start_width: float | None = None
    end_width: float | None = None
    cap: str = "round"


def _catmull_rom(points: tuple[tuple[float, float], ...], steps: int = 12) -> list[tuple[float, float]]:
    if len(points) < 2:
        raise ValueError("A stroke needs at least two points")
    if len(points) == 2:
        return [
            (points[0][0] + (points[1][0] - points[0][0]) * i / steps,
             points[0][1] + (points[1][1] - points[0][1]) * i / steps)
            for i in range(steps + 1)
        ]
    padded = (points[0],) + points + (points[-1],)
    result: list[tuple[float, float]] = []
    for index in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[index - 1:index + 3]
        for step in range(steps):
            t = step / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
            result.append((x, y))
    result.append(points[-1])
    return result


def _polygon(points: list[tuple[float, float]]) -> pathops.Path:
    path = pathops.Path()
    pen = path.getPen()
    pen.moveTo(points[0])
    for point in points[1:]:
        pen.lineTo(point)
    pen.closePath()
    return path


def _hand_cap(center: tuple[float, float], radius: float, phase: float) -> pathops.Path:
    points = []
    for index in range(12):
        angle = phase + math.tau * index / 12
        irregularity = 1 + 0.045 * math.sin(index * 2.7 + phase * 3)
        points.append((
            center[0] + math.cos(angle) * radius * irregularity,
            center[1] + math.sin(angle) * radius * irregularity,
        ))
    return _polygon(points)


def stroke_path(stroke: Stroke) -> pathops.Path:
    samples = _catmull_rom(stroke.points)
    start_width = stroke.start_width if stroke.start_width is not None else stroke.width * 0.82
    end_width = stroke.end_width if stroke.end_width is not None else stroke.width * 0.68
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for index, point in enumerate(samples):
        before = samples[max(0, index - 1)]
        after = samples[min(len(samples) - 1, index + 1)]
        dx, dy = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        ratio = index / max(1, len(samples) - 1)
        pressure = start_width + (end_width - start_width) * ratio
        pressure *= 1 + 0.055 * math.sin(ratio * math.pi * 2.1 + len(stroke.points))
        radius = pressure / 2
        left.append((point[0] + nx * radius, point[1] + ny * radius))
        right.append((point[0] - nx * radius, point[1] - ny * radius))
    result = _polygon(left + list(reversed(right)))
    if stroke.cap == "round":
        result = pathops.op(result, _hand_cap(samples[0], start_width / 2, 0.17), pathops.PathOp.UNION)
        result = pathops.op(result, _hand_cap(samples[-1], end_width / 2, 0.41), pathops.PathOp.UNION)
    return pathops.simplify(result)


def glyph_path(strokes: tuple[Stroke, ...]) -> pathops.Path:
    result = stroke_path(strokes[0])
    for stroke in strokes[1:]:
        result = pathops.op(result, stroke_path(stroke), pathops.PathOp.UNION)
    return pathops.simplify(result)


def path_to_glyph(path: pathops.Path):
    pen = TTGlyphPen(None)
    path.draw(Cu2QuPen(pen, max_err=1.0))
    return pen.glyph()


def build_stroke_glyph(strokes: tuple[Stroke, ...]):
    return path_to_glyph(glyph_path(strokes))
