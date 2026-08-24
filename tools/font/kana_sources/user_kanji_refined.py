"""Project-local configuration for the hybrid 懐 (U+61D0).

The hybrid glyph preserves the source face's original 懷 upper/left outline
and directly reuses the same face's native 衣 outline for the lower component.
U+5915 夕 is intentionally outside this override and remains untouched.

気 (U+6C17) and 付 (U+4ED8) retain the original source-font drawings.  Separate
derived copies receive optical vertical transforms in user_japanese_overrides.py
so the mixed sequence 気付け aligns with the refined Hiragana without changing
the original source glyphs.
"""

from __future__ import annotations

HYBRID_SOURCE_CHARACTER = {"懐": "懷"}
HYBRID_REPLACEMENT_CHARACTER = {"懐": "衣"}
HYBRID_KANJI_CHARACTERS = tuple(HYBRID_SOURCE_CHARACTER)
HYBRID_KEEP_LEFT_MAX = 330.0
HYBRID_KEEP_UPPER_MIN = 380.0
HYBRID_FINAL_SHIFT = (0.0, 30.0)
# Native 衣 is fitted into the lower-right component without changing its
# proportions: (uniform scale, dx, dy).
HYBRID_REPLACEMENT_TRANSFORM = (0.86, 310.0, -102.0)

USER_KANJI_OVERRIDE_CODEPOINTS = {ord(character) for character in HYBRID_KANJI_CHARACTERS}
ALIGNMENT_OVERRIDE_CHARACTERS = "気付"
