# Version 1.025 — Maintainer Hiragana master sheet v2

Base main SHA: `d89ee8b2b5f4c858e5dade853972194892037f93`
Branch: `feat/quanfangwei-hiragana-master-sheet-v2`
Previous font version: **1.024**. New font version: **1.025**.
HEAD: the local feature-branch commit containing this report; the completion message records its exact SHA. Publication is pending GitHub write access (the connector returned HTTP 403; local Git has no saved credentials).

Master reference: [`tools/font/references/hiragana-maintainer-master-v2.png`](../references/hiragana-maintainer-master-v2.png)
Master reference SHA256: `779559e9a7f3e7fe914987f882c2029f50881a53b092318db3d356f9792e8db1`

The latest full sheet supersedes all older visual references for overlapping characters. Historical references remain in the repository. All 41 shown Hiragana were rebuilt as manually interpreted center-line strokes in original photo coordinates, uniformly normalized per glyph, then rendered through the unchanged variable-width engine. No external Japanese outlines, bitmap contours or raster autotracing were used.

41 replaced: **あ い う え お か き く け こ さ し す せ そ た ち つ て と は ひ ふ へ ほ ま み む め も や ゆ よ ら り る れ ろ わ を ん**

5 preserved: **な に ぬ ね の**. Source points, branches, pressure, optical transforms and final outlines/metrics are unchanged.

## Per-glyph measurements

Bounds are `(xMin, yMin, xMax, yMax)` in font units; source bounds precede the shared `-145` build translation. Every outer optical transform was reviewed against the new geometry and is identity `(scale_x=1, scale_y=1, dx=0, dy=0)`. Uniform photo fit parameters, crop bounds, recipe hashes, source hashes, ink centers and sidebearings are recorded in the [manifest](../references/hiragana-master-v2-manifest.json).

| Glyph | Old branches | New branches | Source bounds | Rendered bounds | Advance | Optical sx/sy/dx/dy |
|---|---:|---:|---|---|---:|---|
| あ | 3 | 3 | (214.77, 185, 745.23, 825) | (194, 22, 765, 701) | 960 | 1 / 1 / 0 / 0 |
| い | 2 | 2 | (165, 249.06, 795, 760.94) | (141, 79, 815, 638) | 960 | 1 / 1 / 0 / 0 |
| う | 2 | 2 | (331.9, 185, 628.1, 825) | (311, 21, 651, 701) | 960 | 1 / 1 / 0 / 0 |
| え | 4 | 2 | (222.3, 185, 737.7, 825) | (202, 21, 758, 702) | 960 | 1 / 1 / 0 / 0 |
| お | 3 | 3 | (185.71, 185, 774.29, 825) | (165, 20, 793, 701) | 960 | 1 / 1 / 0 / 0 |
| か | 7 | 3 | (181.54, 185, 778.46, 825) | (160, 20, 799, 702) | 960 | 1 / 1 / 0 / 0 |
| き | 4 | 4 | (276.36, 185, 683.64, 825) | (254, 19, 704, 702) | 960 | 1 / 1 / 0 / 0 |
| く | 5 | 1 | (314.84, 185, 645.16, 825) | (289, 20, 665, 702) | 960 | 1 / 1 / 0 / 0 |
| け | 7 | 3 | (187.83, 185, 772.17, 825) | (166, 20, 792, 702) | 960 | 1 / 1 / 0 / 0 |
| こ | 4 | 2 | (180, 205, 780, 805) | (158, 39, 800, 684) | 960 | 1 / 1 / 0 / 0 |
| さ | 3 | 3 | (277.74, 185, 682.26, 825) | (256, 20, 702, 702) | 960 | 1 / 1 / 0 / 0 |
| し | 1 | 1 | (241.7, 185, 718.3, 825) | (220, 15, 738, 702) | 960 | 1 / 1 / 0 / 0 |
| す | 2 | 2 | (247.27, 185, 712.73, 825) | (227, 21, 732, 701) | 960 | 1 / 1 / 0 / 0 |
| せ | 7 | 3 | (170, 245, 790, 765) | (148, 77, 810, 642) | 960 | 1 / 1 / 0 / 0 |
| そ | 8 | 2 | (231.11, 185, 728.89, 825) | (214, 20, 736, 702) | 960 | 1 / 1 / 0 / 0 |
| た | 9 | 4 | (256.31, 185, 703.69, 825) | (235, 19, 724, 702) | 960 | 1 / 1 / 0 / 0 |
| ち | 7 | 2 | (242.86, 185, 717.14, 825) | (221, 19, 739, 702) | 960 | 1 / 1 / 0 / 0 |
| つ | 1 | 1 | (175, 216.94, 785, 743.06) | (153, 52, 806, 621) | 960 | 1 / 1 / 0 / 0 |
| て | 5 | 1 | (228.56, 195, 731.44, 815) | (200, 30, 753, 696) | 960 | 1 / 1 / 0 / 0 |
| と | 2 | 2 | (204.14, 190, 755.86, 790) | (183, 25, 776, 667) | 960 | 1 / 1 / 0 / 0 |
| は | 8 | 3 | (170, 195, 790, 815) | (145, 23, 810, 692) | 960 | 1 / 1 / 0 / 0 |
| ひ | 5 | 1 | (160, 255.77, 800, 754.23) | (138, 86, 820, 632) | 960 | 1 / 1 / 0 / 0 |
| ふ | 10 | 4 | (170, 226, 790, 784) | (148, 59, 810, 661) | 960 | 1 / 1 / 0 / 0 |
| へ | 2 | 1 | (160, 297.38, 800, 682.62) | (138, 133, 820, 558) | 960 | 1 / 1 / 0 / 0 |
| ほ | 10 | 4 | (160, 238.89, 800, 771.11) | (137, 65, 820, 648) | 960 | 1 / 1 / 0 / 0 |
| ま | 12 | 3 | (252.8, 185, 707.2, 825) | (231, 19, 727, 702) | 960 | 1 / 1 / 0 / 0 |
| み | 8 | 2 | (170, 247.84, 790, 762.16) | (148, 83, 810, 639) | 960 | 1 / 1 / 0 / 0 |
| む | 10 | 3 | (231.84, 185, 728.16, 825) | (210, 19, 748, 702) | 960 | 1 / 1 / 0 / 0 |
| め | 9 | 2 | (160, 185, 800, 825) | (134, 14, 821, 702) | 960 | 1 / 1 / 0 / 0 |
| も | 11 | 3 | (246.02, 185, 713.98, 825) | (224, 18, 734, 702) | 960 | 1 / 1 / 0 / 0 |
| や | 3 | 3 | (192.99, 185, 767.01, 825) | (171, 20, 789, 702) | 960 | 1 / 1 / 0 / 0 |
| ゆ | 9 | 2 | (210.69, 185, 749.31, 825) | (189, 20, 771, 702) | 960 | 1 / 1 / 0 / 0 |
| よ | 5 | 2 | (193.85, 195, 766.15, 815) | (171, 30, 786, 692) | 960 | 1 / 1 / 0 / 0 |
| ら | 4 | 2 | (232.73, 185, 727.27, 825) | (209, 20, 750, 702) | 960 | 1 / 1 / 0 / 0 |
| り | 2 | 2 | (314.84, 185, 645.16, 825) | (291, 20, 665, 702) | 960 | 1 / 1 / 0 / 0 |
| る | 6 | 1 | (254.69, 185, 705.31, 825) | (226, 16, 726, 706) | 960 | 1 / 1 / 0 / 0 |
| れ | 10 | 2 | (160, 220.56, 800, 789.44) | (138, 56, 820, 667) | 960 | 1 / 1 / 0 / 0 |
| ろ | 5 | 1 | (250.31, 190, 709.69, 820) | (223, 25, 732, 697) | 960 | 1 / 1 / 0 / 0 |
| わ | 2 | 2 | (187.5, 190, 772.5, 820) | (166, 25, 795, 697) | 960 | 1 / 1 / 0 / 0 |
| を | 11 | 3 | (219.26, 185, 740.74, 825) | (198, 19, 763, 702) | 960 | 1 / 1 / 0 / 0 |
| ん | 3 | 1 | (167.19, 185, 792.81, 825) | (143, 13, 813, 702) | 960 | 1 / 1 / 0 / 0 |

## Derived forms and yōon

All small derivatives regenerated from the new bases: `ぁぃぅぇぉ` · `っ` · `ゃゅょ` · `ゎ` · `ゕゖ`. Normal small kana use the existing normal derivation; `ゎ` retains its pre-existing scoped +14/-14 adjustment. No unrelated independent small-glyph topology was introduced.

The three Hiragana yōon offsets were recalibrated **after** derivation to keep the reviewed actual-font lower-left anchor `(180,24)` despite changed source geometry:

| Glyph | Previous dx/dy | New dx/dy | Ink anchor | Advance |
|---|---|---|---|---:|
| ゃ | (-104, -74) | (-74, -74) | (180,24) | 960 |
| ゅ | (-120, -84) | (-86, -74) | (180,24) | 960 |
| ょ | (-122, -114) | (-73, -81) | (180,24) | 960 |
| ャ | (-87, -70) | (-87, -70) | (180,24) | 960 |
| ュ | (-136, -123) | (-136, -123) | (180,24) | 960 |
| ョ | (-148, -120) | (-148, -120) | (180,24) | 960 |

Katakana `ャュョ` shapes, offsets, weight and positions remain unchanged. The six yōon glyphs occupy independent 960-unit cells; ordinary small kana do not receive yōon offsets.

All 26 voiced/semi-voiced forms passed current-base component identity, unchanged shared mark shape, bounds-derived anchor, GPOS, forced decomposed HarfBuzz placement, non-collision and advance checks:

`がぎぐげご` · `ざじずぜぞ` · `だぢづでど` · `ばびぶべぼ` · `ぱぴぷぺぽ` · `ゔ`

All required yōon combinations were rendered at 24/48/72 px and shaped as two 960-unit glyphs:

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

`に` stays unchanged; `にゃ／にゅ／にょ` were still reviewed against the new small forms. Full parallel Katakana combinations are included in the proof.

## Proofs and visual review

- [Master-sheet row arrangement](../proofs/quanfangwei-hiragana-master-v2-proof.png)
- [Reference handwriting vs actual generated font](../proofs/quanfangwei-hiragana-master-v2-comparison.png)
- [All 41 per-glyph reference/font overlays](../proofs/quanfangwei-hiragana-master-v2-overlay.png)
- [Full 46 Hiragana: blue new sources / amber preserved na-row](../proofs/quanfangwei-hiragana-master-v2-full-46.png)
- [Family weight, shared baseline, 24/32/48/72 px](../proofs/quanfangwei-hiragana-master-v2-family-weight.png)
- [Production text and unchanged existing lyric fixtures](../proofs/quanfangwei-hiragana-master-v2-production-text.png)
- [All small, voiced and yōon combinations](../proofs/quanfangwei-hiragana-master-v2-derivatives-yoon.png)

Visual review covered structure, proportions, openings, detached strokes, weight, baseline, optical height/width, ink density and sidebearings. Initial overlays led to scoped trajectory corrections in え／は／ひ／み／む／ゆ／れ. The final drawings retain handwritten asymmetry; the preserved na-row remains recognizable as the same family. Counters and marks remain readable at normal lyric sizes.

Independent raster diagnostics: ink IoU 58.6%–84.9%; mean symmetric nearest-ink gap 0.038–0.349 original-photo pixels. These are geometric diagnostics, not perceptual similarity scores; production pressure intentionally differs from photographed ink thickness.
[Per-glyph fidelity metrics](../proofs/quanfangwei-hiragana-master-v2-fidelity.json).

## Preservation evidence

| Preserved source | SHA256 of complete authoritative Stroke tuple |
|---|---|
| な | `6aa958a31e053bb848c9274f142d9876e0e9a8c44acbfcd7414627e15cf03435` |
| に | `b2042f21e67c3b0012256c3f47053cab690fbd27a06b5b5462a59e735101089b` |
| ぬ | `510fed8b31b07533325c78417a9bec3ea82efa57266900f299976da072f66523` |
| ね | `2996faa5ee5ff765247369d80d0b869fa68492451d51939463c380e0b5e5cbc9` |
| の | `3a02c92a52f0c9fe46880c2ec67dbeba3dde0b1f17010e86a51a8736ee658a0b` |

Katakana topology and final output: **unchanged**. All source hashes, including small forms, are pinned in the manifest.

All Han output: **unchanged**. `壁／堅` transforms remain identity scale/x with `dy +97/+55`; both bottoms remain -15. The accepted `気／付` reference measurement `(276,6,740,659)` is frozen to prevent the new `け` from changing unrelated Han alignment. All other Han transforms remain unchanged.

Whole-font comparison against immutable base main allows exactly **79 changed glyphs = 41 bases + 12 small forms + 26 voiced/semi-voiced forms**. Every other outline, component, advance and sidebearing is identical, including Latin/French/German, Japanese marks and all Han. Source glyph order, cmap and global line metrics remain unchanged.

## Validation

- Canonical `python tools/font/build_supplement_font.py`: passed; TTF and WOFF2 rebuilt from project-local sources.
- `python tools/font/verify_hiragana_master_v2.py`: passed, including byte-identical repeat build of both formats.
- `python tools/font/verify_supplement_font.py`: passed; cmap, metadata, licensing, marks, source preservation and TTF/WOFF2 agreement.
- Every existing `tools/font/verify_*.py` entry point: passed; superseded shape snapshots now verify the current master-sheet contract. Historical reference hash checks remain.
- Existing Japanese weight gates: passed without changing the ±10% family effective-stroke limits or the small-kana weight gate.
- All required small/yōon/dakuten/handakuten and Japanese/Han alignment checks: passed.
- `node --test tests/*.test.mjs`: **93 passed, 0 failed**.
- `node --check` for every `assets/*.js`: **16 passed**.
- `git diff --check`: passed.

Build environment: Python 3.12; pinned fontTools 4.55.3, Pillow 10.2.0, uharfbuzz 0.40.1, skia-pathops 0.8.0.post1, NumPy 1.26.4, SciPy 1.11.4. Brotli **1.1.0** was used locally because the 1.0.9 pin has no compatible Python 3.12 macOS wheel and no compiler is installed. Repository dependency pins were preserved. Byte determinism is verified within this environment; cross-Brotli compressed-byte identity is not claimed.

CSS remains unchanged as requested, including its existing `?v=1.024` font URLs; browsers may retain cached font bytes until normal cache revalidation. No production deployment/cache purge was performed.

## Scope confirmations

- Latest full sheet supersedes older overlapping references; all 41 shown Hiragana rebuilt.
- `なにぬねの` unchanged; normal small kana keep normal derivation.
- `ゃゅょ` retain reviewed lower-left positioning; Katakana source topology unchanged.
- No external Japanese font outline used; TTF/WOFF2 built canonically.
- No SQL/migration; production database untouched.
- No CSS/JS layout, Supabase/auth, playlist or YouTube changes.
- Main was not modified directly; no rebase; feature PR was not auto-merged.

## Output SHA256

- `QuanFangweiSupplementScript-Regular.ttf`: `b8a2fbc231b5a785ede85eea19dc50595e69c358223e0710cfd5d4dcbae5b945`
- `QuanFangweiSupplementScript-Regular.woff2`: `52475b18cfa68f33552e332393de669966b027e3743c30ebd385395475cb0bed`
