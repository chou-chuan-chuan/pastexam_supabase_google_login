# Version 1.028 — Scoped 踊 optical-size correction

Base main: `38f441c2bc0e2380c3cd7c1bf4afda1df2f3bc2f` (complete accepted Version 1.027, including the final て/で clearance).
Branch: `fix/quanfangwei-kanji-odoru-optical-size`.
The current output changes only the U+8E0A mapping to one new source-preserving derived copy. Every existing glyph remains present and unchanged.

## Source inspection before modification

Both the original ChenYuluoyan cmap and accepted 1.027 cmap map U+8E0A to `uni8E0A`; its decomposed drawing commands and measured geometry are identical. U+8E0A is the only cmap alias for that source glyph. Original source SHA256: `1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db`. Accepted 1.027 TTF SHA256: `c7a6d88f48fd7ee10b328851612526629492d60ec7df1d684568a19cfd019cb6`.

The new cmap target is `uni8E0A.qfwJaOptical`. The original `uni8E0A` is retained with its original drawing and metrics. There is no new raster, center-line interpretation, font download, external Japanese outline or outline dependency. The only production construction change is the additional record in `SHARED_HAN_OPTICAL_TRANSFORMS`; existing drawing/rounding/installation code is unchanged.

## Measurement and selected transform

All units are font units (UPM 1024). Optical bounds are actual quadratic-curve ink bounds, not control-point extrema. “Center” means ink-box center, not an ink-area centroid. TrueType LSB/RSB use the stored control-point bounds; optical sidebearings are listed separately.

| Metric | Before 1.027 | Final 1.028 |
|---|---:|---:|
| cmap glyph | uni8E0A | uni8E0A.qfwJaOptical |
| Advance | 826 | 826 |
| Actual ink bounds | (102.333333, 65, 738, 655) | (28.875, −14, 797.391304, 699) |
| Optical width | 635.666667 | 768.516304 |
| Optical height | 590 | 713 |
| Ink-box center | (420.166667, 360) | (413.133152, 342.5) |
| LSB / RSB | 101 / 86 | 27 / 26 |
| Optical left / right clearance | 102.333333 / 88 | 28.875 / 28.608696 |
| Height / Han median | 0.827489481 | 1.000000000 |
| Ink-box area / product of Han median dimensions | 0.764545756 | 1.117029512 |

The unchanged 59-Han sample from 1.026/1.027 is:

`君鉄壁今日天気私音楽聴好夜家帰東京新映画見優人無茶苦走続明生行雲二影残恋可哀想足元花付平仮名片声愛夢中文本語對齊春風吹`

Its median optical width / height are **688 / 713**, median bottom / top **−14 / 701.818182**, and median ink center Y **350**. These are independent medians: top minus bottom need not equal median height. 踊 is not in this sample, so the reference itself remains unchanged. The area ratio uses `median width × median height`, not filled stroke area.

Calculated uniform scale: `713 / 590 = 1.2084745762711864`, rounded to six decimals for the reviewed record. Each candidate scales around the old ink center, then independently centers X inside the original 826-unit cell and sets the bottom to −14. No origin-based scaling or advance change.

| Candidate | Rounded ink W × H | Height / Han | LSB / RSB | Review |
|---|---:|---:|---:|---|
| 1.178475 | 749.025974 × 695 | 0.974754558 | 37 / 36 | Clear improvement; slightly more compact within the mixed lyric. |
| **1.208475** | **768.516304 × 713** | **1.000000000** | **27 / 26** | Selected: natural Han presence and bottom, still open and recognizable at lyric sizes. |
| 1.238475 | 786.962733 × 731 | 1.025245442 | 18 / 17 | Still contained, but larger/darker and tighter in the original advance than needed. |

Final `scale_x == scale_y == 1.208475`; post-center translation **dx = −43/6 = −7.166666667**, **dy = −17.499875**. Source proportions and handwriting remain intact, subject only to the existing integer TrueType point rounding. Nominal transformed center before rounding is `(413,342.500125)`. Rounded actual center X differs from 413 by just 0.133152 units.

No boundary embolden or other weight correction is used. The normal stroke-size increase comes solely from uniform outline enlargement. The final glyph is inside both the existing advance and all hhea/Windows/typographic vertical bounds; global UPM/line metrics remain unchanged.

## Available structural and lyric comparators

All requested structural comparators are available. They are measured and shown as context, not independently modified. The family contains natural width/height variation, especially short 日 and tall 算/舞; the fix does not force every Han to identical dimensions.

| Character | Current glyph | Optical width | Optical height | Bottom | Advance |
|---|---|---:|---:|---:|---:|
| 足 | `uni8DB3` | 841.000 | 622.000 | 39.000 | 955 |
| 跳 | `uni8DF3` | 782.000 | 554.000 | 73.000 | 952 |
| 躍 | `uni8E8D` | 913.500 | 701.000 | -1.000 | 1089 |
| 踏 | `uni8E0F` | 781.000 | 694.000 | 23.000 | 953 |
| 路 | `uni8DEF` | 745.167 | 687.000 | 37.000 | 914 |
| 俯 | `uni4FEF` | 712.000 | 688.000 | -24.000 | 922 |
| 就 | `uni5C31` | 834.000 | 726.474 | -33.474 | 1050 |
| 算 | `uni7B97` | 590.167 | 1042.400 | -189.000 | 755 |
| 低 | `uni4F4E` | 838.000 | 603.000 | 19.000 | 1049 |
| 著 | `uni8457` | 536.000 | 872.000 | -63.000 | 703 |
| 頭 | `uni982D` | 807.000 | 665.615 | 17.385 | 967 |
| 也 | `uni4E5F` | 724.000 | 530.000 | 55.000 | 939 |
| 起 | `uni8D77` | 866.000 | 600.000 | 50.000 | 1027 |
| 舞 | `uni821E` | 626.000 | 966.000 | -153.000 | 784 |
| 漢 | `uni6F22` | 927.471 | 856.000 | -58.000 | 1085 |
| 字 | `uni5B57` | 577.286 | 842.000 | -41.000 | 789 |
| 日 | `uni65E5` | 305.000 | 455.000 | 122.000 | 535 |
| 本 | `uni672C` | 566.727 | 770.000 | -35.000 | 732 |
| 音 | `uni97F3` | 627.000 | 643.935 | 27.815 | 786 |
| 楽 | `uni697D` | 661.900 | 890.000 | -95.000 | 821 |

## Visual QA

[Production-like proof](../proofs/quanfangwei-kanji-odoru-optical-size.png) includes before, all three candidates and final, with all required lines at **20 / 32 / 64 px**, a **192 px** glyph diagnostic, and a large technical panel. The technical panel overlays old/new ink boxes in the same original 826-unit advance cell, ink-box center crosses, baseline and unchanged Han median bottom/top guides. Pink is old, blue is new.

The proof uses the production font with HarfBuzz shaping and FreeType rasterization. A proof-only glyph-ID-to-PUA cmap permits faithful HarfBuzz offsets even on Pillow without libraqm; it does not alter repository font binaries. TTF/decoded WOFF2 glyph/layout equality is verified. These PNGs document this rasterizer; browser anti-aliasing can vary.

Inspected actual-size 20/32/64 px crops and the enlarged diagnostic:

- `俯いたままで踊って`: selected 踊 no longer reads as a small, floating glyph. Its original foot/body proportions, open spaces and terminals remain visible. The bottom now belongs to the Han line, and its strokes do not become excessively dark.
- `就算低著頭，也跳起舞`: the unmodified Chinese companion line remains an honest context reference.
- `踊って`, `踊る`, `踊り`: no clipping or collision with the next kana. All advances and phrase widths are exactly unchanged.
- `漢 字 日 本 音 楽 踊 跳 足`: the new 踊 fits the variable handwritten Han family without imposing a new global size.
- Existing て/で clearance, the shared −56 kana translation and lower-left small kana/yōon positioning remain identical.

HarfBuzz placed ink-box gaps for the production lyric are **138.875 units before 踊** and **315.608696 after it** (about **2.712 / 6.164 px at 20 px**). Positive disjoint X intervals prove no outline collision for these neighboring glyphs. Following gaps in 踊る / 踊り are **290.608696 / 338.608696** units. No pair-specific layout rule is introduced.

## Frozen output and verification

The focused verifier compares against the immutable complete 1.027 font, independently reconstructs the uniform transform from the original font, and checks the entire old glyph set. The production font gains exactly one glyph; no old drawing is rewritten. Only U+8E0A cmap changes. In addition to geometry/advance, unchanged hashes include contour structure, every coordinate and flag, component transforms and horizontal metrics; vertical metrics are also checked.

| Group unchanged from accepted 1.027 | Count | Aggregate SHA256 |
|---|---:|---|
| Unrelated mapped Han | 9,343 | `fb09f7808a981f618148f45b3457a7be156caa395ea7fa4553454063559fa8ba` |
| All kana-related glyphs, including two script mark variants | 187 | `eaa5234e505097e2f76822efcd29b8d1dcb8cd3048228a837e6c228f6a20a22a` |
| Every pre-existing glyph, including original uni8E0A | 10,463 | `131431bcd0af6030d8fca69540cf6a6a7c11656d5989db30d01aef1017384c37` |

All ten accepted Han overrides **壁 堅 奥 容 変 恋 哀 奧 優 寄** retain their exact transform, drawing and metrics. The complete Japanese source/reference tree is pinned (87 files), allowing only the exact new three-line 踊 record. All kana source/pressure/normalization, scale factors `0.894078195335 / 0.946843040146`, −56 translation, small derivation, yōon and `て/で` geometry/GPOS are frozen. Latin, punctuation, GSUB/GPOS/GDEF and line metrics also remain identical; hhea's metric-record count increases by one solely for the new glyph.

Historical 1.025/1.026/1.027 verifiers add only an independently generated, pinned 踊 extension to their old expected font. Their existing source, translation, pressure, topology and attachment gates are preserved. The new focused verifier separately checks directly against unextended 1.027. Historical measurement/reference JSON files are not rewritten.

Validation completed successfully on 2026-09-19:

- All **22 font verifiers** passed, including the new focused `verify_kanji_odoru_optical.py` and all 21 existing verifiers.
- Four independent default verifier runs performed canonical builds and confirmed **byte-identical TTF/WOFF2** output: Master v2, kana bottom alignment, kana/Han scale balance and the new 踊 verifier. Rebuilds ran sequentially; remaining read-only verifiers ran only afterward.
- `node --test tests/*.test.mjs`: **93 passed, 0 failed**.
- `node --check` on all `assets/*.js`: **16 passed**.
- `git diff --check`: passed. Production CSS/JS and SQL paths are unchanged.

Font verifier coverage: `verify_cjk_vertical_alignment.py`, `verify_de_dakuten_clearance.py`, `verify_handwriting_fidelity.py`, `verify_handwritten_hiragana_svg.py`, `verify_hiragana_ke_u_optical.py`, `verify_hiragana_maintainer_batch.py`, `verify_hiragana_master_v2.py`, `verify_hiragana_metrics.py`, `verify_hiragana_o.py`, `verify_hiragana_su.py`, `verify_hiragana_u.py`, `verify_hiragana_ya.py`, `verify_japanese_optical_alignment.py`, `verify_japanese_weight.py`, `verify_kana_bottom_alignment.py`, `verify_kana_kanji_scale_balance.py`, `verify_kanji_odoru_optical.py`, `verify_oku_optical_alignment.py`, `verify_special_japanese_overrides.py`, `verify_supplement_font.py`, `verify_yong_alignment.py`, `verify_yoon_position.py`.

Validation runtime: Python 3.12 with fontTools 4.55.3, Pillow 10.2.0, uharfbuzz 0.40.1, skia-pathops 0.8.0.post1, NumPy 1.26.4, SciPy 1.11.4 and Brotli 1.1.0. The existing requirements pin remains unchanged; this Python 3.12 environment has Brotli 1.1.0, and all four actual rebuild comparisons were byte-identical.

## Output fingerprints

| Output | Bytes | SHA256 |
|---|---:|---|
| TTF | 9,262,096 | `88dd082bba1c3bdd32edc7799137faba2e6f360dea6813d2c3b3350a1dcc96c0` |
| WOFF2 | 4,701,776 | `dc337b159a623f20c6213d9906a3065f6df3f56ad198986282cf6fbe3153b1d2` |

No external outline, kana change, CSS/JS workaround, SQL/migration or production DB operation. The focused PR targets main and is not auto-merged.
