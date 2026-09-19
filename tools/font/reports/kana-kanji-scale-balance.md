# Version 1.026 — Kana–Han mixed-script optical balance

Base main: `e19227dbb31666e8373045a2edeb3456d00bd373` (merged PR #32, Version 1.025).

The accepted Master v2 handwriting and per-glyph normalization are unchanged. Only one uniform scale per script follows the 1.025 stage. External fonts provide relative proportions; the unchanged QuanFangwei Han ink body supplies the absolute size.

**Han sample (59 unique characters):** 君鉄壁今日天気私音楽聴好夜家帰東京新映画見優人無茶苦走続明生行雲二影残恋可哀想足元花付平仮名片声愛夢中文本語對齊春風吹

Sample selection: every unique Han character in the six requested lines, all six existing lyric fixtures and the four existing Chinese/Japanese alignment fixtures, in first-appearance order. `壁` is one of 59; `堅` is reserved for QA. No frequency weighting or hand-picked exclusions.

Optical height/width = exact ink bounding box / UPM. Optical center = bounding-box midpoint. The secondary area statistic is **bounding-box area**, not ink coverage. Each kana sample is the complete 46 modern basic characters, excluding small/voiced forms.

Hiragana: あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん

Katakana: アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン

| Font | UPM | Han median height/em | Hiragana height/em | Katakana height/em | Hira/Han | Kata/Han |
|---|---:|---:|---:|---:|---:|---:|
| Noto Sans CJK JP Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603 | 1000 | 0.919000000 | 0.829148431 | 0.783500000 | 0.902228978 | 0.852557127 |
| Source Han Sans JP Version 2.005;addfeatures 5.0.0b21 | 1000 | 0.919000000 | 0.829148431 | 0.783500000 | 0.902228978 | 0.852557127 |
| QuanFangwei Supplement Script Version 1.025 | 1024 | 0.696289062 | 0.702636719 | 0.626953125 | 1.009116410 | 0.900420757 |
| QuanFangwei Version 1.026 | 1024 | 0.696289062 | 0.628417969 | 0.593261719 | 0.902524544 | 0.852033661 |

Median of the Noto and Source Han ratios is used as one related standards reference family; neither external absolute kana height enters the target.

| Script | Standard ratio | QFW Han × ratio = target height/em | Shared scale |
|---|---:|---:|---:|
| hiragana | 0.902228978322 | 0.628212169476 | 0.894078195335 |
| katakana | 0.852557127312 | 0.593626202904 | 0.946843040146 |

`HIRAGANA_HAN_BALANCE_SCALE = 0.894078195335`; `KATAKANA_HAN_BALANCE_SCALE = 0.946843040146`.

Factor = (QuanFangwei Han median height × standard kana/Han ratio) / 1.025 kana median height. Both measured factors are below 1. Final median heights are within one font unit of the analytical targets after outline quantization.

## Secondary diagnostics

| Font | Script | Median width/em | Width/Han | Median bbox area/em² | Area/Han | Median center-y/em | Center-y minus Han/em |
|---|---|---:|---:|---:|---:|---:|---:|
| Noto Sans CJK JP Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603 | hiragana | 0.800000000 | 0.868621064 | 0.659272500 | 0.789770141 | 0.370500000 | -0.008000000 |
| Noto Sans CJK JP Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603 | katakana | 0.791500000 | 0.859391965 | 0.594232000 | 0.711855402 | 0.363250000 | -0.015250000 |
| Source Han Sans JP Version 2.005;addfeatures 5.0.0b21 | hiragana | 0.800000000 | 0.868621064 | 0.659272500 | 0.790643780 | 0.370500000 | -0.008000000 |
| Source Han Sans JP Version 2.005;addfeatures 5.0.0b21 | katakana | 0.791500000 | 0.859391965 | 0.594232000 | 0.712642852 | 0.363250000 | -0.015250000 |
| QuanFangwei Supplement Script Version 1.025 | hiragana | 0.633300781 | 0.942587209 | 0.434756279 | 0.981703217 | 0.359863281 | 0.018066406 |
| QuanFangwei Supplement Script Version 1.025 | katakana | 0.528320312 | 0.786337209 | 0.304872513 | 0.688418641 | 0.337646484 | -0.004150391 |
| QuanFangwei Version 1.026 | hiragana | 0.566894531 | 0.843750000 | 0.347736359 | 0.785207526 | 0.359863281 | 0.018066406 |
| QuanFangwei Version 1.026 | katakana | 0.500488281 | 0.744912791 | 0.273685932 | 0.617997653 | 0.337646484 | -0.004150391 |

These secondary statistics are diagnostics, not extra per-glyph fitting targets. The handwritten width and open counters differ from sans-serif references by design.

## Construction and scope

- Scale around each accepted ink-box center; scale geometry and pressure together. No axis stretching, source-point edits or additional per-glyph normalization.
- The 12 small Hiragana derive from balanced large bases via the existing 0.72 geometry / 0.92 pressure relationship. Existing Katakana derivations are retained. No second balance scale is applied to derived small forms.
- All six yōon glyphs keep `(xMin,yMin)=(180,24)` using translation only. Advances stay 960; no ligatures or pair positioning.
- Dakuten/handakuten designs scale with each script about their existing mark anchor. Two unmapped Katakana mark variants allow precomposed and decomposed forms to share the same size. GSUB `ccmp` selects these marks after Katakana; GPOS and composite anchors apply the same scaled 1.025 offset. This is contextual mark selection, not a ligature or character-spacing rule.
- Iteration marks use their script factor. `ー` uses the Katakana factor. Spacing/standalone combining marks use the Hiragana factor. General punctuation is unchanged.
- All Han, including 壁/堅 and all prior transforms, Latin/French/German, CSS/JS and application/database code remain unchanged.

Yōon translations after derivation: `{'ゃ': (-79, -77), 'ゅ': (-105, -77), 'ょ': (-93, -97), 'ャ': (-98, -83), 'ュ': (-146, -131), 'ョ': (-157, -129)}`.

## Proofs

- [Normal lyric size, 32 px](../proofs/quanfangwei-kana-kanji-scale-balance.png)
- [Small text, 20 px](../proofs/quanfangwei-kana-kanji-scale-balance-small.png)
- [Large text, 64 px](../proofs/quanfangwei-kana-kanji-scale-balance-large.png)
- [Identical 960-unit cell diagnostics](../proofs/quanfangwei-kana-kanji-same-em.png)
- [Small kana, all 33 Hiragana yōon, voiced forms and marks](../proofs/quanfangwei-kana-kanji-derivatives.png)

Proofs use actual 1.025 and 1.026 TTFs at identical font sizes and baselines, with the original text unchanged. The measured factors were rendered before acceptance; no arbitrary alternative factor was substituted.

## Provenance

The build needs neither external fonts nor raster reconstruction. The 1.025 master and absolute-metric reports remain historical records of the accepted stage. The current mixed-script size gate is this ratio report.

- [Noto Sans CJK JP Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603](https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf), SHA256 `68a3fc98800b2a27b371f2fb79991daf3633bd89309d4ffaa6946fd587f375b5`.
- [Source Han Sans JP Version 2.005;addfeatures 5.0.0b21](https://github.com/adobe-fonts/source-han-sans/blob/release/SubsetOTF/JP/SourceHanSansJP-Regular.otf), SHA256 `40d1b760d1135539f6b6e0ee2b9f415de6d97576f7676840b06306c7c190c074`.

## Visual QA and validation record

Reviewed the actual-font A/B proofs at **20 px (small), 32 px (normal lyrics), and 64 px (large)**. The measured candidate is accepted without an arbitrary factor adjustment:

- Kana no longer dominate the Han body in the requested sentences and unchanged production fixtures. Han keeps its natural variation; the same-width cells retain the established line rhythm.
- Handwritten loops, openings, crossings and taper retain the 1.025 identity. No glyph was reinterpreted from a raster. Optical centers remain within 0.5 font unit of their accepted positions after rounding.
- All 12 small Hiragana remain distinctly small; all 33 Hiragana yōon pairs, including にゃ/にゅ/にょ, retain two 960-unit cells and the reviewed lower-left placement. Katakana yōon also passes all 33 combinations.
- The 26 voiced/semi-voiced Hiragana and all Katakana voiced forms retain clear marks at the appropriate script size. Forced decomposed shaping matches precomposed components and offsets; all checked marks are collision-free. Iteration, long-sound, spacing and combining marks were inspected.
- Same-em diagnostics preserve the accepted baseline and centers. 壁/堅 remain unchanged. Small kana's measured effective-weight/Han ratio is 0.875 at quantized raster sizes; it matches the uniformly scaled 1.025 design within one supersampled scan-run quantum plus outline rounding. No independent pressure redesign was applied.

**All 19 font verifier entry points passed.** Both the new balance verifier and the master verifier completed their default byte-identical canonical TTF/WOFF2 rebuild checks. Source points and all kana contour counts remain unchanged; only uniform geometry/pressure scale and necessary small-kana translations are applied. All ordinary kana advances are 960; the mark advances remain 0 (combining) / 300 (spacing).

All **9,344 mapped Han glyph hashes** are unchanged; aggregate hash of ordered `(glyph name, signature SHA256)` records: `c8216eea043a73ed70cac1495a046503ad07bcd9198e6441b5fe31d886ef4fcc`. The entire font comparison permits exactly 185 kana/related mapped glyph changes and two unmapped mark-size variants. All other glyphs, including Latin/French/German, are identical. TTF/WOFF2 glyphs, metrics and layout tables agree.

| Verifier | Result |
|---|---|
| `verify_cjk_vertical_alignment.py` | PASS |
| `verify_handwriting_fidelity.py` | PASS |
| `verify_handwritten_hiragana_svg.py` | PASS |
| `verify_hiragana_ke_u_optical.py` | PASS |
| `verify_hiragana_maintainer_batch.py` | PASS |
| `verify_hiragana_master_v2.py` | PASS |
| `verify_hiragana_metrics.py` | PASS |
| `verify_hiragana_o.py` | PASS |
| `verify_hiragana_su.py` | PASS |
| `verify_hiragana_u.py` | PASS |
| `verify_hiragana_ya.py` | PASS |
| `verify_japanese_optical_alignment.py` | PASS |
| `verify_japanese_weight.py` | PASS |
| `verify_kana_kanji_scale_balance.py` | PASS |
| `verify_oku_optical_alignment.py` | PASS |
| `verify_special_japanese_overrides.py` | PASS |
| `verify_supplement_font.py` | PASS |
| `verify_yong_alignment.py` | PASS |
| `verify_yoon_position.py` | PASS |

- `node --test tests/*.test.mjs`: **93 passed, 0 failed**.
- `node --check` on every `assets/*.js`: **16 files passed**.
- `git diff --check`: passed.
- No CSS/JS application changes, no SQL/migration, no Supabase action, production DB untouched. PR is intended for review with no auto-merge.

Build environment: Python 3.12 with the existing pinned fontTools 4.55.3, Pillow 10.2.0, uharfbuzz 0.40.1, skia-pathops 0.8.0.post1, NumPy 1.26.4 and SciPy 1.11.4. As in 1.025, this machine uses the Brotli 1.1.0 wheel because pinned 1.0.9 lacks a compatible Python 3.12 wheel and no compiler is installed. Repository dependency pins are unchanged; byte determinism was verified in this environment.

Reviewed artifact SHA256:

| Artifact | SHA256 |
|---|---|
| `QuanFangweiSupplementScript-Regular.ttf` | `ffc8732aebdc74f84d3776c932b7b3ec251a59001639945f8b22efea070fc346` |
| `QuanFangweiSupplementScript-Regular.woff2` | `fbae197eeaa1f4086a2635cec1100df876f3ab15291ea98adf1518172b331fa6` |
| `quanfangwei-kana-kanji-derivatives.png` | `33aaab0eeb77c5a0dd9675182c1a94532c76107caebcd50de16cec688dba2d3a` |
| `quanfangwei-kana-kanji-same-em.png` | `d66d8544415aee1e598007242cf4c6b0b72f81021d0fa41940783d8c26c09429` |
| `quanfangwei-kana-kanji-scale-balance-large.png` | `68ca63af9797dc0ec27704196f033207c431bb558903aa0f86524470ce804ae7` |
| `quanfangwei-kana-kanji-scale-balance-small.png` | `1a28b2522fab7f969ebbe1e76936edcda72a509a815fca2bfc4d423948972a07` |
| `quanfangwei-kana-kanji-scale-balance.png` | `fdb031cb9c0ffefac7ea5581bcebbb4811a1db1848a34ae671757d38c4b344e7` |
