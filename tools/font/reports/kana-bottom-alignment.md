# Version 1.027 — Kana–Han bottom alignment

Base main: `19cf20cf94feb047245f630506ca909af2e7e49b` (Version 1.026). Branch: `fix/quanfangwei-kana-bottom-align-han`.

Only final vertical placement changes. The accepted 1.026 font is extracted from the immutable base commit; its SHA256 is `ffc8732aebdc74f84d3776c932b7b3ec251a59001639945f8b22efea070fc346`. Before/after measurements use actual curve ink bounds, not control-point boxes or optical centers. All values below are font units, UPM 1024. The machine-readable record is [kana-bottom-alignment.json](kana-bottom-alignment.json).

## Samples and bottom target

The exact same deterministic 59-Han sample as Version 1.026 is reused:

君鉄壁今日天気私音楽聴好夜家帰東京新映画見優人無茶苦走続明生行雲二影残恋可哀想足元花付平仮名片声愛夢中文本語對齊春風吹

All 46 modern basic Hiragana and all 46 modern basic Katakana are included. The pooled median gives both scripts equal weight; it is not an average of their two medians.

`measured delta = Han median yMin − pooled 92-kana median yMin = −14 − 41.5 = −55.5`. An integer translation of **−56** avoids new outline rounding. Separate script targets would be −58.5 and −55, only 3.5 units apart, so one shared delta is appropriate.

| Group | Count | yMin before → after | yMax before → after | Ink-box center Y before → after | Median width | Median height |
|---|---:|---:|---:|---:|---:|---:|
| Han | 59 | -14 → -14 | 701.818182 → 701.818182 | 350 → 350 | 688 (unchanged) | 713 (unchanged) |
| Hiragana | 46 | 44.5 → -11.5 | 688.5 → 632.5 | 368.5 → 312.5 | 580.5 (unchanged) | 643.5 (unchanged) |
| Katakana | 46 | 41 → -15 | 646.5 → 590.5 | 345.75 → 289.75 | 512.5 (unchanged) | 607.5 (unchanged) |
| Pooled kana | 92 | 41.5 → -14.5 | 672 → 616 | 356.75 → 300.75 | 531 (unchanged) | 622.5 (unchanged) |

The center column is the median of each glyph’s ink-box center, not the center of the two family medians. It is reported for top/line-rhythm review; it does not determine the shift.

| Bottom distribution | Before min / Q1 / median / Q3 / max | After min / Q1 / median / Q3 / max |
|---|---|---|
| han | -121 / -48.45 / -14 / 30.907407 / 148 | -121 / -48.45 / -14 / 30.907407 / 148 |
| hiragana | 6 / 27.25 / 44.5 / 60.25 / 134 | -50 / -28.75 / -11.5 / 4.25 / 78 |
| katakana | 4 / 28 / 41 / 61 / 142 | -52 / -28 / -15 / 5 / 86 |

Individual bottoms retain their natural variation. No per-glyph baseline fits or separate script deltas are introduced.

## Candidate review

All three candidates were rendered from the exact accepted 1.026 TTF before choosing the production delta. The 64 px candidate proof includes all eight requested mixed-script lines.

| Candidate delta | Hiragana median yMin | Katakana median yMin | Pooled median yMin | Pooled distance to Han | Review |
|---:|---:|---:|---:|---:|---|
| -64 | -19.5 | -23.0 | -22.5 | 8.5 | Slightly lower than the Han target |
| -56 | -11.5 | -15.0 | -14.5 | 0.5 | Selected: closest median, coherent line rhythm |
| -48 | -3.5 | -7.0 | -6.5 | 7.5 | Leaves a small upward bias |

All candidates fit unchanged hhea/Windows bounds. At −56 the pooled bottom misses the robust Han target by just 0.5 unit. The selected shift corresponds to 1.09375 px at 20 px, 1.75 px at 32 px and 3.5 px at 64 px. The before/after proofs show better shared bottom rhythm without visibly sunken kana. The intentionally smaller 1.026 kana tops remain lower than the Han tops; their size is accepted and is not changed to force top alignment.

## Exact placement and preserved contracts

- `JAPANESE_BOTTOM_ALIGNMENT_SHIFT = -56` is the single additional translation.
- `KANA_VERTICAL_SHIFT: -145 → -201`; kana-related `JAPANESE_MARK_VERTICAL_SHIFT: -120 → -176`.
- `HIRAGANA_HAN_BALANCE_SCALE = 0.894078195335`, `KATAKANA_HAN_BALANCE_SCALE = 0.946843040146`, unchanged.
- Build the accepted 1.026 contours at their original rendering origin, then translate integer TrueType coordinates once. No rerender at a new origin, new fitting, pressure adjustment, x movement, resize or external outlines.
- Every one of 187 moved glyphs (185 mapped plus the two existing unmapped Katakana mark variants) has exactly the same contour topology, flags, x coordinates, width and height. Every Y coordinate is the corresponding accepted coordinate minus 56.
- Every hmtx/vmtx entry is unchanged: ordinary kana retain advance 960, combining marks 0, spacing dakuten/handakuten 300; left/right metrics remain unchanged.
- All 84 tracked source/reference files, including the complete Master v2 sources, Katakana sources, normalization, pressure, small derivation, yōon offsets and Han transforms, match immutable 1.026 bytes.
- All 9,344 mapped Han glyph hashes are identical. Aggregate: `c8216eea043a73ed70cac1495a046503ad07bcd9198e6441b5fe31d886ef4fcc`. `壁／堅` and every unrelated glyph, including Latin and punctuation such as `・／〆／々`, are unchanged.

## Small kana, yōon and mark QA

All 12 small Hiragana `ぁぃぅぇぉっゃゅょゎゕゖ` and all 12 small Katakana `ァィゥェォッャュョヮヵヶ` move with their full-size bases and retain the exact relative geometry. The six yōon ink anchors move from `(180,24)` to `(180,-32)` with the entire script. Existing internal offsets are unchanged; there are no pair-specific positions, ligatures or CSS offsets.

Visual review covers all 33 Hiragana pairs below; shaping checks additionally cover the corresponding 33 Katakana pairs. Each remains two glyphs with advances `[960,960]`.

```text
きゃ きゅ きょ
ぎゃ ぎゅ ぎょ
しゃ しゅ しょ
じゃ じゅ じょ
ちゃ ちゅ ちょ
にゃ にゅ にょ
ひゃ ひゅ ひょ
びゃ びゅ びょ
ぴゃ ぴゅ ぴょ
みゃ みゅ みょ
りゃ りゅ りょ
```

The Japanese GPOS mark anchor moves `(92,815) → (92,759)` and all Japanese base anchors move by exactly the same delta. Composite component offsets stay byte-for-byte equivalent, so marks receive the translation once and preserve their reviewed gaps. GSUB/GDEF tables are unchanged. All voiced/semi-voiced kana and voiced iteration marks pass forced-decomposition HarfBuzz parity and collision checks. Visual pairs include `が/が`, `ぎ/ぎ`, `ず/ず`, `で/で`, `ば/ば`, `ぱ/ぱ`, `ゔ/ゔ` and Katakana equivalents. `゛゜ゝゞヽヾー` move coherently; no marks float at the former height.

## Global metrics and clipping

UPM remains 1024. Complete hhea and OS/2 tables are byte-identical to 1.026: hhea ascent/descent/lineGap `967 / -362 / 92`; OS/2 typo `819 / -205 / 92`; Windows ascent/descent `967 / 362`. No global metric is changed.

Moved glyph bounds span Y `-52 … 837`, within the existing hhea/Windows clipping bounds. All normal kana, precomposed attachments and spacing marks also fit the typographic box. Standalone combining-mark variants already extended above the typo ascender in 1.026 (maximum yMax 893); the new maximum is 837, so this existing overhang is reduced. The typographic ascender governs line spacing and is not itself the hhea/Windows clipping edge. No new clipping or metric expansion is required.

## Proofs inspected

- [Primary 32 px before/after](../proofs/quanfangwei-kana-bottom-alignment.png)
- [20 px lyric size](../proofs/quanfangwei-kana-bottom-alignment-small.png)
- [64 px enlarged view](../proofs/quanfangwei-kana-bottom-alignment-large.png)
- [−64 / −56 / −48 candidate comparison](../proofs/quanfangwei-kana-bottom-alignment-candidates.png)
- [Common baseline and Han/old/new median-bottom guides](../proofs/quanfangwei-kana-bottom-alignment-guides.png)
- [Small kana, all requested yōon and marks](../proofs/quanfangwei-kana-bottom-alignment-derivatives.png)

The mixed proofs contain all eight requested lines plus six existing lyric fixtures and four Chinese/Japanese alignment fixtures. Baselines, letter sizes and advances are equal in each before/after pair. Guides show `漢字日本音楽世界鉄壁`, `あいうえおかきくけこ` and `アイウエオカキクケコ`. Visual inspection at 20/32/64 px found intact terminals/counters, readable kana, coherent marks, unchanged Han and a more consistent bottom rhythm.

## Output hashes

- TTF (9,261,228 bytes): `16eb157eadd5fcb100eba444b96cbaa925853116c8d514b675f3bad4e4671457`.
- WOFF2 (4,700,500 bytes): `46b399fa28773694ef0faa9048f7563843df6898ef31b6d7974373c4de1430b3`.

## Validation

All **20 font verifier entry points passed**: the 19 existing verifiers plus [verify_kana_bottom_alignment.py](../verify_kana_bottom_alignment.py). The new verifier uses immutable 1.026 as an independent point-by-point oracle. Historical center gates still check the accepted pre-translation stage and also enforce the new bottom target.

The master, scale-balance and bottom-alignment verifiers each ran their default canonical rebuild sequentially and confirmed byte-identical TTF and WOFF2. Full-glyph TTF/WOFF2 parity, source preservation, shaping, collision and clipping checks passed.

```text
verify_cjk_vertical_alignment.py  PASS
verify_handwriting_fidelity.py  PASS
verify_handwritten_hiragana_svg.py  PASS
verify_hiragana_ke_u_optical.py  PASS
verify_hiragana_maintainer_batch.py  PASS
verify_hiragana_master_v2.py  PASS
verify_hiragana_metrics.py  PASS
verify_hiragana_o.py  PASS
verify_hiragana_su.py  PASS
verify_hiragana_u.py  PASS
verify_hiragana_ya.py  PASS
verify_japanese_optical_alignment.py  PASS
verify_japanese_weight.py  PASS
verify_kana_bottom_alignment.py  PASS
verify_kana_kanji_scale_balance.py  PASS
verify_oku_optical_alignment.py  PASS
verify_special_japanese_overrides.py  PASS
verify_supplement_font.py  PASS
verify_yong_alignment.py  PASS
verify_yoon_position.py  PASS
```

- `node --test tests/*.test.mjs`: **93 passed, 0 failed**.
- `node --check` on every `assets/*.js`: **16 passed**.
- `git diff --check`: **passed**.
- Source-scope check: no changed Master v2/Katakana source or reference files, Han transform/renderer files, website CSS/JS, or Supabase files. The only test metadata change is the expected manifest version `1.026 → 1.027`.

No CSS/JS workaround, SQL/migration, Supabase, playlist, YouTube or production DB change. The PR is not configured for auto-merge.
