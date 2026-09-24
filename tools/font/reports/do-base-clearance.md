# Version 1.029 — Scoped `ど` base-size / dakuten clearance

## Result

Only the `と` body used inside `ど` is smaller. Standalone U+3068 `と` remains byte-identical to Version 1.028 (glyph signature SHA256 `4cb6195f74ba08259513fd33774ada9dbcbcd963580df3adf7171050939586fb`). The shared `uni3099` dakuten outline, its anchor, and its final U+3069 placement are unchanged.

The new unmapped helper glyph is `uni3068.qfwDoBase`. It is a uniform **0.94** copy of the accepted `uni3068`, scaled about the accepted ink's horizontal center and final bottom. Its 960-unit advance and `yMin = -14` are retained. No embolden or pressure compensation was added; the ordinary uniform outline scale remains natural in the 20/32/64/192 px proof.

## Measurements

All distances are measured from adaptively flattened production outlines. “Vertical clearance” is the minimum vertical contour separation over the body's and dakuten's shared X range; the nearest overall separation is diagonal.

| Output | Body scale | Body bounds | Dakuten bounds | Minimum outline clearance | Vertical clearance | Bottom delta |
|---|---:|---|---|---:|---:|---:|
| CURRENT 1.028 | 1.00 | `(215,-14,797,616)` | `(726,575,863,663)` | 20.105617 | 532.500000 | 0 |
| candidate A / FINAL | **0.94** | `(232,-14,780,578)` | `(726,575,863,663)` | **54.800000** | **545.250000** | **0** |
| candidate B | 0.96 | `(227,-14,785,591)` | `(726,575,863,663)` | 42.801869 | 539.444444 | 0 |
| candidate C | 0.98 | `(221,-14,791,603)` | `(726,575,863,663)` | 30.413813 | 535.250000 | 0 |

At 20 px, one nominal pixel is 51.2 font units. Candidate A is the smallest requested candidate and the only candidate in the measured range that exceeds that reference without moving the dakuten. Visual review shows a clear handwritten separation at 20 px while the mark remains attached rather than floating. The original and final dakuten component delta is exactly `(708,-160)`.

## Construction and shaping

- U+3068 remains mapped to the unchanged `uni3068`.
- U+3069 is composed from `uni3068.qfwDoBase` + `uni3099`.
- A narrowly scoped `ccmp` contextual substitution changes `uni3068` to `uni3068.qfwDoBase` only when immediately followed by `uni3099`.
- The helper has the same GPOS base anchor `(800,599)` as accepted `uni3068`; `uni3099` retains mark anchor `(92,759)`.
- Default HarfBuzz normalization makes precomposed `ど` and decomposed `ど` the same `uni3069` output. With recomposition deliberately disabled, the decomposed path produces `uni3068.qfwDoBase` plus `uni3099` at the same `(708,-160)` origin and the same 960-unit total advance.

No scoped anchor adjustment was necessary after the body shrink. The Version 1.027 `HIRAGANA_MARK_ANCHOR_Y_OFFSETS["て"] = 82` exception and both `て` / `で` glyphs are unchanged.

## Scope and validation

The focused verifier pins base main `2b9472342505f676146200b6fb02209a4b497c1e` and its TTF/WOFF2 hashes. Among existing glyphs, only `uni3069` changes; `uni3068.qfwDoBase` is the sole new glyph. All 185 unrelated kana and all 9,344 Han glyph signatures match Version 1.028. U+8E0A `踊` and its Version 1.028 optical helper remain unchanged.

- [Focused 20/32/64/192 px proof](../proofs/quanfangwei-do-base-clearance.png)
- [Machine-readable measurements](do-base-clearance.json)
- [Focused verifier](../verify_do_base_clearance.py)

No external font outline, CSS/JavaScript workaround, SQL/migration, or production database operation is involved.

Validation on the canonical Version 1.029 binaries:

- all 23 `tools/font/verify_*.py` entry points: PASS
- focused verifier and byte-identical TTF/WOFF2 rebuild: PASS
- 114 Node website regression tests: PASS
- every `assets/*.js` syntax check: PASS
- `git diff --check`: PASS
