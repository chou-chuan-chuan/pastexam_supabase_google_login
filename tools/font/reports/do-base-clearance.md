# Version 1.030 — Subtle `と` reduction and clearer `ど` separation

## Result

This follow-up starts from the merged Version 1.029 design. Standalone U+3068 `と` is uniformly scaled to **0.98** around its horizontal ink center and fixed `yMin = -14`. The unmapped `uni3068.qfwDoBase` used inside `ど` is then uniformly scaled to **0.92** of that new standalone body, for an effective scale of **0.9016** relative to Version 1.029 `と`.

Both bodies keep their 960-unit advance and bottom alignment. The shared `uni3099` dakuten outline, anchor, and final `(708,-160)` component delta remain unchanged. No embolden or pressure compensation is used.

## Measurements

All distances are measured from adaptively flattened production outlines. “Vertical clearance” is the minimum vertical contour separation over the body's and dakuten's shared X range; the nearest overall separation is diagonal.

| Output | Standalone `と` scale | `ど` body relative scale | Effective voiced scale | Standalone bounds | `ど` body bounds | Dakuten bounds | Minimum outline clearance | Vertical clearance |
|---|---:|---:|---:|---|---|---|---:|---:|
| CURRENT 1.029 | 1.00 | 0.94 | 0.9400 | `(215,-14,797,616)` | `(232,-14,780,578)` | `(726,575,863,663)` | 54.800000 | 545.250000 |
| candidate A | 0.99 | 0.92 | 0.9108 | `(218,-14,794,610)` | `(241,-14,771,560)` | `(726,575,863,663)` | 72.800000 | 553.500000 |
| candidate B / FINAL | **0.98** | **0.92** | **0.9016** | **`(221,-14,791,603)`** | **`(244,-14,768,554)`** | `(726,575,863,663)` | **78.800000** | **557.000000** |
| candidate C | 0.97 | 0.92 | 0.8924 | `(224,-14,788,597)` | `(247,-14,765,548)` | `(726,575,863,663)` | 84.800000 | 560.666667 |

Candidate B is the final choice: the 2% standalone reduction is visible only as a subtle refinement, while the second scoped reduction makes the dakuten separation clearly stronger without making the mark appear detached. The final 78.8-unit outline gap is about 1.54 nominal pixels at 20 px.

## Construction and shaping

- U+3068 maps to the subtly reduced `uni3068`.
- U+3069 is composed from `uni3068.qfwDoBase` + unchanged `uni3099`.
- The narrow `ccmp` contextual substitution still changes decomposed `uni3068` to `uni3068.qfwDoBase` only when immediately followed by `uni3099`.
- The helper retains the GPOS base anchor `(800,599)` and `uni3099` retains mark anchor `(92,759)`.
- Precomposed `ど` and decomposed `ど` retain equivalent output, the same `(708,-160)` mark origin, and the same 960-unit total advance.

## Scope and validation

The focused verifier pins merged Version 1.029 main `b2e1d1613eedfa432cdd4580e813771932d8fa54` and its TTF/WOFF2 hashes. Only `uni3068`, `uni3068.qfwDoBase`, and `uni3069` change. The shared dakuten, all unrelated kana, all Han, the Version 1.027 `て／で` correction, and the Version 1.028 `踊` correction remain unchanged.

- [Focused 20/32/64/192 px proof](../proofs/quanfangwei-do-base-clearance.png)
- [Machine-readable measurements](do-base-clearance.json)
- [Focused verifier](../verify_do_base_clearance.py)

No external font outline, CSS/JavaScript workaround, SQL/migration, or production database operation is involved.

Validation on the canonical Version 1.030 binaries:

- all 23 `tools/font/verify_*.py` entry points: PASS
- focused verifier and byte-identical TTF/WOFF2 rebuild: PASS
- 114 Node website regression tests: PASS
- every `assets/*.js` syntax check: PASS
- `git diff --check`: PASS
