"""User-maintainer Japanese overrides for Version 1.012.

The maintainer-provided handwriting reference supplies the structural source
for 懐 (U+61D0) and 夕 (U+5915). The final outlines are regenerated through
the project variable-width handwriting stroke engine; the raster reference
is not embedded in the font. 気 (U+6C17) and 付 (U+4ED8) retain their original
source outlines but receive optically normalized vertical transforms so the
sequence 気付け aligns with refined Hiragana in mixed Japanese text.
"""

from __future__ import annotations

from japanese.stroke_engine import Stroke


def S(*points, width=44, start=None, end=None, cap="round") -> Stroke:
    return Stroke(tuple(points), width, start, end, cap)


USER_KANJI_REFINED: dict[str, tuple[Stroke, ...]] = {
    '懐': (
        S((441.9, 840.0), (439.4, 822.2), (492.7, 774.0), width=42.0, start=37.8, end=26.9),
        S((510.4, 644.6), (523.1, 530.4), width=42.0, start=37.8, end=26.9),
        S((647.5, 743.6), (568.8, 725.8), (421.6, 730.9), (355.7, 710.6), width=42.0, start=37.8, end=26.9),
        S((490.1, 317.3), (459.7, 312.2), (398.8, 276.7), width=42.0, start=37.8, end=26.9),
        S((743.9, 434.0), (713.4, 413.7), (579.0, 413.7), width=42.0, start=37.8, end=26.9),
        S((594.2, 654.8), (510.4, 647.2), width=42.0, start=37.8, end=26.9),
        S((528.2, 484.8), (561.2, 456.9), (576.4, 416.3), width=42.0, start=37.8, end=26.9),
        S((558.7, 406.1), (530.7, 413.7), (421.6, 413.7), (391.2, 406.1), width=42.0, start=37.8, end=26.9),
        S((675.4, 289.4), (713.4, 340.1), width=42.0, start=37.8, end=26.9),
        S((525.7, 527.9), (561.2, 527.9), width=42.0, start=37.8, end=26.9),
        S((492.7, 319.9), (548.5, 368.1), (561.2, 403.6), width=42.0, start=37.8, end=26.9),
        S((804.8, 160.0), (776.9, 187.9), (746.4, 198.1), width=42.0, start=37.8, end=26.9),
        S((492.7, 314.8), (518.1, 200.6), (528.2, 185.4), (556.1, 187.9), (591.6, 228.5), (609.4, 233.6), width=42.0, start=37.8, end=26.9),
        S((596.7, 652.2), (599.3, 571.0), (563.7, 530.4), width=42.0, start=37.8, end=26.9),
        S((287.2, 228.5), (259.3, 545.7), width=42.0, start=37.8, end=26.9),
        S((743.9, 200.6), (738.8, 218.4), (680.4, 266.6), (675.4, 286.9), width=42.0, start=37.8, end=26.9),
        S((429.3, 576.1), (414.0, 649.7), width=42.0, start=37.8, end=26.9),
        S((287.2, 223.4), (287.2, 167.6), width=42.0, start=37.8, end=26.9),
        S((241.5, 776.6), (249.1, 599.0), (259.3, 550.7), width=42.0, start=37.8, end=26.9),
        S((672.8, 289.4), (650.0, 294.5), (596.7, 345.2), (589.1, 342.7), width=42.0, start=37.8, end=26.9),
        S((416.6, 652.2), (507.9, 647.2), width=42.0, start=37.8, end=26.9),
        S((680.4, 530.4), (683.0, 652.2), (596.7, 654.8), width=42.0, start=37.8, end=26.9),
        S((677.9, 527.9), (563.7, 525.4), width=42.0, start=37.8, end=26.9),
        S((173.0, 472.1), (167.9, 553.3), (155.2, 599.0), width=42.0, start=37.8, end=26.9),
        S((261.8, 548.2), (299.9, 543.1), (365.8, 502.5), (396.3, 520.3), (520.6, 527.9), width=42.0, start=37.8, end=26.9),
    ),
    '夕': (
        S((317.5, 692.0), (338.2, 795.5), (364.8, 825.0), width=46.0, start=41.4, end=29.4),
        S((320.5, 689.1), (397.3, 659.5), (536.1, 638.9), (624.8, 609.3), (630.7, 568.0), (601.1, 508.9), (574.5, 281.4), (565.7, 272.5), width=46.0, start=41.4, end=29.4),
        S((267.3, 476.4), (270.2, 544.3), (293.9, 647.7), (317.5, 689.1), width=46.0, start=41.4, end=29.4),
        S((323.4, 334.5), (353.0, 349.3), (432.7, 308.0), (524.3, 281.4), width=46.0, start=41.4, end=29.4),
        S((565.7, 266.6), (577.5, 248.9), (692.7, 175.0), width=46.0, start=41.4, end=29.4),
    ),
}

USER_KANJI_OVERRIDE_CODEPOINTS = {ord(character) for character in USER_KANJI_REFINED}
ALIGNMENT_OVERRIDE_CHARACTERS = "気付"
