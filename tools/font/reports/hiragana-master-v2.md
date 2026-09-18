# Version 1.025 — Complete Maintainer Hiragana Master v2

Base main SHA: `d89ee8b2b5f4c858e5dade853972194892037f93`
Branch: `feat/quanfangwei-hiragana-master-sheet-v2`
Previous production version: **1.024**. This PR remains **1.025** after both updates.
HEAD: the feature-branch commit containing this report; its exact SHA is recorded in the completion message.

The complete authority set consists of two maintainer-owned references:

- [hiragana-maintainer-master-v2.png](../references/hiragana-maintainer-master-v2.png); SHA256 `779559e9a7f3e7fe914987f882c2029f50881a53b092318db3d356f9792e8db1`.
- [hiragana-maintainer-master-v2-na-row.png](../references/hiragana-maintainer-master-v2-na-row.png); SHA256 `6a85555d562e9e2633b72a2aa4c7567cf5479a3f162b570de3b62039ce81e821`.

The main 41-glyph sheet and supplementary na-row sheet together supersede all older references for all 46 modern basic Hiragana. The newly supplied na-row explicitly supersedes the former preserve-na-row rule, including the older legibility-reviewed `の`. No basic Hiragana intentionally remains on an older authoritative source. Historical references remain in the repository for provenance only.

**46 replaced / refreshed from Maintainer Master v2:**

```text
あ い う え お
か き く け こ
さ し す せ そ
た ち つ て と
な に ぬ ね の
は ひ ふ へ ほ
ま み む め も
や   ゆ   よ
ら り る れ ろ
わ       を
ん
```

All trajectories were manually interpreted from maintainer handwriting. No external Japanese outline, curve, point, component, stroke shape, bitmap contour or autotrace was used in production. The unchanged QuanFangwei variable-width renderer supplies stroke pressure and terminals.

## Absolute size normalization

Noto Sans CJK JP Regular and Source Han Sans JP Regular were measured outside the repository for scalar metrics only. Their 46-glyph bounds and box-center ratios are identical; they count as one external standard reference, paired with immutable QuanFangwei 1.024 for continuity. All coordinates are divided by the font UPM (1000 external / 1024 QuanFangwei). External binaries are not committed or read by the canonical build.

Each glyph uses the median standard/production height and box center, then a **uniform scale plus dx/dy**, retaining the handwriting’s relative proportions. Width is a sanity envelope, not an external aspect template. No non-uniform exceptions. All full-width advances remain 960. Large normalization precedes all small derivation.

[Complete per-character comparison, source versions/hashes, target formulas, family distribution, deviations and reviewed outliers](hiragana-standard-metrics.md) · [CSV](hiragana-standard-metrics.csv) · [same-em boxes/centers proof](../proofs/quanfangwei-hiragana-standard-metrics.png).

| Family metric (em) | Median | Minimum | Maximum |
|---|---:|---:|---:|
| width_em | 0.633301 | 0.365234 | 0.841797 |
| height_em | 0.702637 | 0.482422 | 0.783203 |
| center_x_em | 0.488770 | 0.466309 | 0.530762 |
| center_y_em | 0.359863 | 0.338379 | 0.374023 |

Every glyph fits its individual target within 1.5 font units in height and 1 unit in x/y box center. The naturally narrow `う・く・り` and shallow `つ・へ` trigger family outlier flags; all were visually reviewed, retain the supplied handwriting, and remain inside their individual reference envelopes.

## Per-glyph source and output measurements

Bounds are `(xMin, yMin, xMax, yMax)` in QuanFangwei font units. Source bounds describe the authoritative center-lines before the outer metric transform and shared −145 build translation. Rendered bounds are the final actual TTF. Scale applies equally to x/y; dx/dy are font units. Complete per-glyph source hashes, recipe hashes, crop bounds, pressure, ink centers and sidebearings are in the [manifest](../references/hiragana-master-v2-manifest.json).

| Glyph | Old branches | New branches | Source bounds | Rendered bounds | Advance | Scale x/y | dx / dy |
|---|---:|---:|---|---|---:|---:|---|
| あ | 3 | 3 | (214.7748, 185, 745.2252, 825) | (175, -14, 822, 757) | 960 | 1.143952 | +19.3340 / +9.4640 |
| い | 2 | 2 | (165, 249.0625, 795, 760.9375) | (118, 32, 898, 679) | 960 | 1.169280 | +29.7760 / -3.3540 |
| う | 2 | 2 | (331.9008, 185, 628.0992, 825) | (301, -8, 675, 745) | 960 | 1.113119 | +6.8260 / +6.6600 |
| え | 4 | 2 | (222.3009, 185, 737.6991, 825) | (209, 11, 793, 728) | 960 | 1.056177 | +21.1440 / +7.2320 |
| お | 3 | 3 | (185.7143, 185, 774.2857, 825) | (158, -5, 861, 758) | 960 | 1.128032 | +30.0800 / +15.3520 |
| か | 7 | 3 | (181.5385, 185, 778.4615, 825) | (195, 38, 818, 704) | 960 | 0.973462 | +27.2580 / +9.8040 |
| き | 4 | 4 | (276.3636, 185, 683.6364, 825) | (247, -14, 754, 760) | 960 | 1.141468 | +21.6140 / +11.2500 |
| く | 5 | 1 | (314.8387, 185, 645.1613, 825) | (284, 16, 671, 720) | 960 | 1.033786 | +0.5713 / +6.6840 |
| け | 7 | 3 | (187.8261, 185, 772.1739, 825) | (174, -28, 868, 729) | 960 | 1.116316 | +41.4960 / -11.1740 |
| こ | 4 | 2 | (180, 205, 780, 805) | (186, 27, 833, 677) | 960 | 1.009348 | +30.2980 / -9.9320 |
| さ | 3 | 3 | (277.7358, 185, 682.2642, 825) | (250, -11, 751, 758) | 960 | 1.135719 | +21.3700 / +11.7860 |
| し | 1 | 1 | (241.7021, 185, 718.2979, 825) | (259, 7, 800, 724) | 960 | 1.046484 | +50.3100 / +6.6240 |
| す | 2 | 2 | (247.2727, 185, 712.7273, 825) | (256, -35, 831, 740) | 960 | 1.148392 | +64.1500 / -9.8220 |
| せ | 7 | 3 | (170, 245, 790, 765) | (83, 26, 895, 717) | 960 | 1.241908 | +9.8020 / +10.5240 |
| そ | 8 | 2 | (231.1111, 185, 728.8889, 825) | (232, 25, 752, 704) | 960 | 0.994174 | +17.3740 / +3.0852 |
| た | 9 | 4 | (256.3107, 185, 703.6893, 825) | (221, -15, 773, 759) | 960 | 1.142265 | +17.8040 / +10.8040 |
| ち | 7 | 2 | (242.8571, 185, 717.1429, 825) | (192, -17, 778, 758) | 960 | 1.142458 | +4.7720 / +8.9180 |
| つ | 1 | 1 | (175, 216.9375, 785, 743.0625) | (185, 80, 796, 613) | 960 | 0.932826 | +11.1360 / +8.7340 |
| て | 5 | 1 | (228.5556, 195, 731.4444, 815) | (200, 11, 775, 705) | 960 | 1.044730 | +10.8020 / -5.5680 |
| と | 2 | 2 | (204.1379, 190, 755.8621, 790) | (181, 5, 831, 709) | 960 | 1.103820 | +26.7520 / +11.5000 |
| な | 13 | 4 | (207.5248, 185, 752.4752, 825) | (180, -4, 823, 747) | 960 | 1.104894 | +22.1560 / +11.0060 |
| に | 5 | 3 | (160, 204.2, 800, 805.8) | (138, 22, 864, 705) | 960 | 1.066407 | +22.3880 / +1.8620 |
| ぬ | 12 | 2 | (160, 244.1597, 800, 765.8403) | (107, 47, 904, 706) | 960 | 1.174190 | +28.2460 / +16.1140 |
| ね | 13 | 2 | (160, 197.0755, 800, 812.9245) | (97, -20, 908, 766) | 960 | 1.201910 | +23.4180 / +12.2860 |
| の | 2 | 1 | (160, 217.9897, 800, 792.0103) | (165, 57, 826, 651) | 960 | 0.959665 | +17.7260 / -7.6280 |
| は | 8 | 3 | (170, 195, 790, 815) | (153, 4, 871, 726) | 960 | 1.084400 | +34.3900 / +7.1540 |
| ひ | 5 | 1 | (160, 255.7692, 800, 754.2308) | (87, 19, 931, 691) | 960 | 1.253447 | +29.5800 / -5.3660 |
| ふ | 10 | 4 | (170, 226, 790, 784) | (108, 17, 883, 721) | 960 | 1.183480 | +16.2740 / +7.9640 |
| へ | 2 | 1 | (160, 297.3786, 800, 682.6214) | (100, 108, 895, 602) | 960 | 1.177765 | +18.0420 / +11.6421 |
| ほ | 10 | 4 | (160, 238.8947, 800, 771.1053) | (140, 48, 882, 681) | 960 | 1.092230 | +32.8660 / +7.3740 |
| ま | 12 | 3 | (252.8, 185, 707.2, 825) | (225, -18, 788, 760) | 960 | 1.146067 | +27.2880 / +9.7380 |
| み | 8 | 2 | (170, 247.8409, 790, 762.1591) | (96, 16, 906, 696) | 960 | 1.239516 | +21.8700 / -6.8540 |
| む | 10 | 3 | (231.8367, 185, 728.1633, 825) | (212, 5, 784, 732) | 960 | 1.068027 | +19.0840 / +7.7560 |
| め | 9 | 2 | (160, 185, 800, 825) | (155, 29, 832, 708) | 960 | 0.984943 | +16.7020 / +10.1780 |
| も | 11 | 3 | (246.0215, 185, 713.9785, 825) | (212, -1, 762, 739) | 960 | 1.085869 | +8.0340 / +8.9760 |
| や | 3 | 3 | (192.9897, 185, 767.0103, 825) | (141, -17, 845, 762) | 960 | 1.151094 | +12.5880 / +10.0300 |
| ゆ | 9 | 2 | (210.6931, 185, 749.3069, 825) | (181, -17, 832, 748) | 960 | 1.129014 | +26.2340 / +3.8740 |
| よ | 5 | 2 | (193.8462, 195, 766.1538, 815) | (163, 15, 815, 717) | 960 | 1.063839 | +10.3860 / +4.9340 |
| ら | 4 | 2 | (232.7273, 185, 727.2727, 825) | (213, 1, 796, 739) | 960 | 1.086490 | +24.9300 / +8.5033 |
| り | 2 | 2 | (314.8387, 185, 645.1613, 825) | (288, -15, 708, 756) | 960 | 1.138791 | +19.5240 / +8.9520 |
| る | 6 | 1 | (254.6939, 185, 705.3061, 825) | (235, 12, 740, 707) | 960 | 1.009113 | +12.0580 / -1.4840 |
| れ | 10 | 2 | (160, 220.5556, 800, 789.4444) | (71, -13, 933, 759) | 960 | 1.282132 | +22.9180 / +10.2860 |
| ろ | 5 | 1 | (250.3125, 190, 709.6875, 820) | (238, 29, 734, 684) | 960 | 0.972211 | +7.7600 / -4.3511 |
| わ | 2 | 2 | (187.5, 190, 772.5, 820) | (153, 12, 847, 754) | 960 | 1.111751 | +19.4053 / +21.0360 |
| を | 11 | 3 | (219.2593, 185, 740.7407, 825) | (159, -30, 821, 772) | 960 | 1.184940 | +9.8620 / +9.0180 |
| ん | 3 | 1 | (167.191, 185, 792.809, 825) | (146, 0, 858, 733) | 960 | 1.068027 | +24.1380 / +8.9400 |

## Na-row visual QA

[Reference / old 1.024 / new 1.025](../proofs/quanfangwei-hiragana-master-v2-na-row.png) · [Normal-size text and にゃ/にゅ/にょ](../proofs/quanfangwei-hiragana-master-v2-na-text.png).

| Glyph | Visual review |
|---|---|
| な | Crossing structure, detached upper-right mark and compact lower-right loop preserved; readable at 24/48/72 px. |
| に | Loose right horizontals and asymmetrical left/right spacing preserved; baseline, family weight and width checked. |
| ぬ | Organic looping body, left opening and small right counter remain visible; no geometric oval substituted. |
| ね | Vertical/curved rhythm and loose lower loop retained; no old fragmented topology reused. |
| の | New single flowing path replaces the older two-branch source; inner loop and open terminal read as の at normal lyric sizes. |

Samples reviewed: `なに` · `なの` · `こんにちは` · `ねこ` · `ぬの` · `この` · `もの` · `なのに` · `あなた` · `おねがい`. Weight, baseline, width, sidebearing, inter-character spacing and readability were inspected. No small forms of the na-row were introduced.

`にゃ／にゅ／にょ` use the new normalized `に` plus derived `ゃ／ゅ／ょ`. Visual QA at 24/48/72 px passed. HarfBuzz confirms two independent glyphs, two 960-unit advances and no pair-specific ligature. The small forms retain the reviewed lower-left ink anchor `(180,24)`.

## Small, voiced and yōon forms

All 12 small forms are derived after large normalization through the existing pipeline: `ぁぃぅぇぉ` · `っ` · `ゃゅょ` · `ゎ` · `ゕゖ`. Ordinary small kana do not receive yōon offsets; `ゎ` retains its earlier +14/−14 scoped adjustment.

| Small kana | Previous 1.024 dx/dy | Final 1.025 dx/dy | Ink anchor | Advance |
|---|---|---|---|---:|
| ゃ | (-104, -74) | (-51, -47) | (180,24) | 960 |
| ゅ | (-120, -84) | (-80, -47) | (180,24) | 960 |
| ょ | (-122, -114) | (-67, -70) | (180,24) | 960 |
| ャ | (-87, -70) | (-87, -70) | (180,24) | 960 |
| ュ | (-136, -123) | (-136, -123) | (180,24) | 960 |
| ョ | (-148, -120) | (-148, -120) | (180,24) | 960 |

Katakana `ャュョ` source shapes, offsets, weight and placement remain unchanged.

All 26 voiced/semi-voiced forms passed base-component identity, shared-mark identity, bounds-derived anchor placement, GPOS, forced decomposed HarfBuzz positioning, collision and advance checks: `がぎぐげご` · `ざじずぜぞ` · `だぢづでど` · `ばびぶべぼ` · `ぱぴぷぺぽ` · `ゔ`.

Metric normalization caused one collision: `て` touched the dakuten in `で`. Only its base mark anchor was raised by 17 units (+5 to clear the intersection plus 12 for separation), in both composed and decomposed rendering. All mark designs and all other vertical base-anchor settings are unchanged.

All required yōon pairs were rendered at 24/48/72 px and shaped as two 960-unit glyphs:

- きゃ きゅ きょ
- ぎゃ ぎゅ ぎょ
- しゃ しゅ しょ
- じゃ じゅ じょ
- ちゃ ちゅ ちょ
- にゃ にゅ にょ
- ひゃ ひゅ ひょ
- びゃ びゅ びょ
- ぴゃ ぴゅ ぴょ
- みゃ みゅ みょ
- りゃ りゅ りょ

## Proofs

- [Complete master arrangement](../proofs/quanfangwei-hiragana-master-v2-proof.png)
- [Both references vs generated font](../proofs/quanfangwei-hiragana-master-v2-comparison.png)
- [All 46 reference/font overlays](../proofs/quanfangwei-hiragana-master-v2-overlay.png)
- [All 46 current master sources](../proofs/quanfangwei-hiragana-master-v2-full-46.png)
- [Family weight and baseline, 24/32/48/72 px](../proofs/quanfangwei-hiragana-master-v2-family-weight.png)
- [Production text and unchanged lyric fixtures](../proofs/quanfangwei-hiragana-master-v2-production-text.png)
- [Small, voiced and full Hiragana/Katakana yōon proof](../proofs/quanfangwei-hiragana-master-v2-derivatives-yoon.png)
- [Na-row reference / old / new](../proofs/quanfangwei-hiragana-master-v2-na-row.png)
- [Na-row words and にゃ/にゅ/にょ](../proofs/quanfangwei-hiragana-master-v2-na-text.png)
- [Same-em standard metric boxes and centers](../proofs/quanfangwei-hiragana-standard-metrics.png)

Shape fidelity proofs undo the reviewed uniform metric fit to compare relative handwriting structure in source-photo coordinates. Absolute-size QA uses the separate common-em metric-box proof and normal-size text. No external reference outline is shown.

Independent raster diagnostics: ink IoU 58.1%–91.3%; mean symmetric nearest-ink gap 0.017–0.347 original-photo pixels. These measure geometry, not perceptual similarity; production pressure intentionally differs from raster ink thickness. [Per-glyph fidelity data](../proofs/quanfangwei-hiragana-master-v2-fidelity.json).

## Preservation and validation

Whole-font comparison against immutable main permits exactly **84 changed glyph outputs: 46 bases + 12 small + 26 voiced/semi-voiced forms**. Every other outline, component, advance and sidebearing remains identical. Katakana topology/output, Latin/French/German, all Han and shared Japanese marks are unchanged. Cmap, glyph order and global line metrics are preserved.

`壁／堅` retain dy +97/+55, identity scale/x and rendered bottoms −15. The accepted `気／付` reference bounds `(276,6,740,659)` remain frozen; all other Han transforms stay unchanged.

- Canonical TTF/WOFF2 build and byte-identical repeat build: passed.
- Master-v2 source, provenance, all-46 raster fidelity and whole-font parity checks: passed.
- UPM-normalized per-character target/envelope and uniform-transform checks: passed.
- All existing font verifier entry points, small/yōon/mark checks and Japanese/Han alignment checks: passed.
- Existing family pressure gates: passed with their original ±10% effective-stroke limits and small-kana gate.
- Web tests: **93 passed, 0 failed**. All **16** `assets/*.js` syntax checks passed.
- `git diff --check`: passed. [Machine validation summary](hiragana-master-v2-validation.json).

Build environment: Python 3.12; pinned fontTools 4.55.3, Pillow 10.2.0, uharfbuzz 0.40.1, skia-pathops 0.8.0.post1, NumPy 1.26.4 and SciPy 1.11.4. Brotli 1.1.0 was used locally because the 1.0.9 pin has no compatible Python 3.12 macOS wheel and no compiler is installed. Repository pins are unchanged. Determinism is verified in this environment; cross-Brotli compressed-byte identity is not claimed.

CSS remains unchanged, including its existing `?v=1.024` URLs; browser caches may retain earlier bytes until normal revalidation. No deployment/cache purge was performed.

## Scope confirmations

- All 46 modern basic Hiragana use the latest maintainer handwriting; the supplemental na-row supersedes the preserve-na-row rule. None intentionally uses an older authoritative source.
- Standard Japanese fonts supplied scalar metrics only. No external Japanese outlines or binaries were incorporated.
- Full-width advances, yōon behavior, Katakana topology and existing Han fixes remain intact.
- No SQL/migration, production DB, CSS/JS layout, Supabase/auth, playlist or YouTube changes.
- Same feature branch and Version 1.025; no rebase or direct main modification; no auto-merge.

## Output SHA256

- `QuanFangweiSupplementScript-Regular.ttf`: `e982101a8a2a0d2bd46221239e88ffdbdeaedadb9c8d07d6326666a99bfd3024`
- `QuanFangweiSupplementScript-Regular.woff2`: `95b3a4e970a05e55dd757184a056bb6e6996e5f7f0ff11b0a7bc518cd0d9107c`
