"""User-maintainer Japanese overrides for Version 1.013.

The maintainer's handwriting is the structural source for 懐 (U+61D0) and
夕 (U+5915).  These are authored as project-local center-lines and rendered by
the existing variable-width handwriting stroke engine; the raster reference is
not embedded and no external Japanese font outline is used.

気 (U+6C17) and 付 (U+4ED8) retain the original source-font drawings.  Separate
derived copies receive optical vertical transforms in user_japanese_overrides.py
so the mixed sequence 気付け aligns with the refined Hiragana without changing
the original source glyphs.
"""

from __future__ import annotations

from japanese.stroke_engine import Stroke


def S(*points, width=44, start=None, end=None, cap="round") -> Stroke:
    return Stroke(tuple(points), width, start, end, cap)


USER_KANJI_REFINED: dict[str, tuple[Stroke, ...]] = {
}

USER_KANJI_OVERRIDE_CODEPOINTS = {ord(character) for character in USER_KANJI_REFINED}
ALIGNMENT_OVERRIDE_CHARACTERS = "気付"
