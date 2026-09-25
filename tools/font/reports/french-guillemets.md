# Version 1.031 — French guillemet coverage

Base main: `4a65b8be24216aa3cf5d23b9e2ba783c0b66090c` (Version 1.030).
Branch: `feat/quanfangwei-french-guillemets`.

## Inspected coverage and authorized source

| Code point | Original ChenYuluoyan | Previous QuanFangwei TTF | Previous WOFF2 |
| --- | --- | --- | --- |
| U+00AB `«` | absent | absent | absent |
| U+00BB `»` | absent | absent | absent |
| U+2039 `‹` | absent | absent | absent |
| U+203A `›` | absent | absent | absent |
| U+003C `<` | `less` | `less` | `less` |
| U+003E `>` | `greater` | `greater` | `greater` |

The original source SHA256 is
`1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db`.
The two new glyphs reuse only the complete original `less` / `greater`
drawings as TrueType components. No external font outline was used.
No existing source or supplemental glyph was redrawn or replaced.

## Construction and metrics

Transforms use fontTools order `(xx, xy, yx, yy, dx, dy)`; all linear values
are exactly representable in TrueType F2Dot14. UPM is 1024.

| Glyph | Components of | Component transforms | Advance | LSB / RSB | TrueType bounds |
| --- | --- | --- | --- | --- | --- |
| `guillemotleft` U+00AB | `less` U+003C | `(0.75,0,0,0.75,-6,43)`; `(0.75,0,0,0.75,106,43)` | 327 | 32 / 33 | `(32,163,294,417)` |
| `guillemotright` U+00BB | `greater` U+003E | `(0.453125,-0.4375,0.2109375,0.9375,-30,7)`; `(0.453125,-0.4375,0.2109375,0.9375,91,7)` | 327 | 32 / 32 | `(32,159,295,420)` |

The original `greater` has a shallow upper arm. Its affine rotation and width
normalization make that arm readable in a compact double quotation glyph,
while retaining every original curve and its taper. This avoids the colliding
upper arms found in a trial with upright duplicated `greater` components.
Neither glyph is two full ASCII advances: those would be 576 and 582 units.
The new glyphs are both 327 units (about 5.1 px at 16 px and 6.4 px at 20 px).
Their actual curve bounds are almost the same width and center near y=290;
control-point bounds above are slightly larger than the visible right curve.
The component outlines do not intersect.

Reference measurements in the unchanged current font:

| Reference | Advance | Curve bounds | LSB / ink RSB |
| --- | --- | --- | --- |
| `'` | 117 | `(33,533,83,658)` | 33 / 34 |
| `"` | 250 | `(70,485,186,624)` | 70 / 64 |
| `“` | 196 | `(19,488,175,671)` | 19 / 21 |
| `”` | 209 | `(18.143,493.115,188,666)` | 16 / 21 |
| `<` | 288 | `(50,160,251,499)` | 50 / 37 |
| `>` | 291 | `(42,194,255,465)` | 42 / 36 |
| `x` | 335 | `(33,136,303,465)` | 33 / 32 |
| `a` | 387 | `(34,104,350,427)` | 34 / 37 |
| `e` | 295 | `(32,110,260,435)` | 32 / 35 |

The guillemets occupy the visual middle of lowercase text, below the high
curly quotes. Both stay within the existing hhea and OS/2 vertical metrics.
Ascent, descent, line gaps and OpenType layout tables remain unchanged.
Only new metric entries and their encoded counts are added: the final two
horizontal advances share one compressed hmtx entry, while vertical advances
are inherited from their respective original source glyphs.

## Proof and visual review

[Native-only PNG proof](../proofs/quanfangwei-french-guillemets.png) and
[renderer](../render_french_guillemets_proof.py).

All nine requested sample rows are rendered at actual 16, 20, 32, 64 and
192 px, including isolated marks, `< / >` comparisons, all three French
sentences, and `« Bonjour »`, `« Hélène »`, `« C’est la vie »`.
The renderer checks every displayed character in the generated TTF cmap,
then loads only that TTF through Pillow/FreeType. It has no fallback-font
selection path. HarfBuzz additionally verifies every sample against both
decoded TTF and WOFF2 without `.notdef` or substituted guillemets.

| Size | `« je t’aime »` visual review |
| --- | --- |
| 16 px | Pass: compact recognizable pairs at the lowercase midline |
| 20 px | Pass: distinct chevrons, comfortable phrase spacing |
| 32 px | Pass: balanced left/right size and handwritten stroke character |
| 64 px | Pass: source taper retained, no collision or oversized marks |
| 192 px | Pass: diagnostic curves remain separate and coherent with Latin |

The BEFORE state is documented by the pinned 1.030 cmaps, where both code
points are absent. No browser-specific fallback screenshot is claimed;
the proof shows only the generated native AFTER glyphs.

## Regression validation

[Dedicated verifier](../verify_french_guillemets.py) and
[machine-readable measurements and immutable hashes](french-guillemets.json).

The verifier checks every existing glyph's complete coordinates, flags,
components, horizontal/vertical metrics and compiled TTF bytes against the
pinned base. It also checks TTF/WOFF2 parity, exact authorized recipes,
nonintersecting outlines, sane metrics and optical balance, unchanged layout
tables, metadata, manifest, native-only shaping and byte-identical rebuilds.

Historical font verifiers retain their original shape/scale/source oracles.
Their current-version checks and whole-font counts now recognize the two
appended guillemets. The existing `measure_do_base_clearance.py` Git reader
uses `Path.as_posix()` so its immutable revision lookup also works on Windows.

Validation completed:

- Canonical build: pass, Version 1.031 in TTF and WOFF2.
- Dedicated French guillemet verifier: pass; all 10,465 prior glyphs unchanged.
- All 23 existing font verifiers: pass. Verifiers supporting `--skip-rebuild`
  use that option; the shared canonical TTF/WOFF2 rebuild is checked once below.
- Deterministic rebuild: both canonical files byte-identical.
- Final proof rerender: byte-identical to the visually reviewed PNG.
- `node --test tests/*.test.mjs`: 114 passed, 0 failed.
- `node --check` on all 17 `assets/*.js`: pass.
- `git diff --check`: pass.

Existing font verifier results:

- `verify_cjk_vertical_alignment.py`: PASS
- `verify_de_dakuten_clearance.py`: PASS
- `verify_do_base_clearance.py`: PASS
- `verify_handwriting_fidelity.py`: PASS
- `verify_handwritten_hiragana_svg.py`: PASS
- `verify_hiragana_ke_u_optical.py`: PASS
- `verify_hiragana_maintainer_batch.py`: PASS
- `verify_hiragana_master_v2.py`: PASS
- `verify_hiragana_metrics.py`: PASS
- `verify_hiragana_o.py`: PASS
- `verify_hiragana_su.py`: PASS
- `verify_hiragana_u.py`: PASS
- `verify_hiragana_ya.py`: PASS
- `verify_japanese_optical_alignment.py`: PASS
- `verify_japanese_weight.py`: PASS
- `verify_kana_bottom_alignment.py`: PASS
- `verify_kana_kanji_scale_balance.py`: PASS
- `verify_kanji_odoru_optical.py`: PASS
- `verify_oku_optical_alignment.py`: PASS
- `verify_special_japanese_overrides.py`: PASS
- `verify_supplement_font.py`: PASS
- `verify_yong_alignment.py`: PASS
- `verify_yoon_position.py`: PASS

Unchanged-glyph aggregate SHA256: `8f301a45882413bb9866ea1c6f76ba5ea28c8a7f1b3e409483c0e9405b552aa2`.

- Final TTF SHA256: `a035c9b19384eeef2ffb85b45face710cbb18bddf2b3825f3caf5032c89f57b7`.
- Final WOFF2 SHA256: `5124866790745a283011661df3be14169d787a70d4408dd1de0fe4ff3adbdd1b`.

Build environment: Windows, Python 3.11.7, fontTools 4.55.3, Pillow 10.2.0,
Brotli 1.0.9, uharfbuzz 0.40.1, skia-pathops 0.8.0.post1, NumPy 1.26.4,
SciPy 1.11.4 (all repository dependency pins retained). The full verifier suite
runs with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` for existing UTF-8 reports
and Japanese diagnostic output on Windows.

There is no website CSS/JS workaround, text replacement, SQL/migration,
Supabase or production database operation. `config.js` is unchanged.
Existing Latin, French accents, Œ/œ, German, Spanish, kana and Han glyphs
are preserved. The actual French U+00AB/U+00BB text is unchanged.
