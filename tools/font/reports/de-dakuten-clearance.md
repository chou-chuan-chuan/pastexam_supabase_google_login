# Version 1.027 — Scoped て / で dakuten clearance

This is a same-version follow-up to the already merged bottom-alignment PR #34. The baseline is main `514297a9c801e981333fded9473d61489669b486`; its font SHA256 is `16eb157eadd5fcb100eba444b96cbaa925853116c8d514b675f3bad4e4671457`. Version remains **1.027**, documenting both global Kana–Han bottom alignment and this local clearance correction.

## Finding and measured correction

The previous `HIRAGANA_MARK_ANCHOR_Y_OFFSETS = {"て": 17}` passed a filled-outline intersection check but left a minimum diagonal gap of only **7.810250 units**, or **0.152544 px at 20 px**. This is too small to prevent the upper stroke and dakuten from visually merging in normal lyrics. A global downward translation cannot improve a relative gap because the base and mark move together.

The final correction changes only that scoped offset:

| Quantity | Before | After |
|---|---:|---:|
| `て` source mark-anchor offset | +17 | **+82** |
| Additional source offset | — | **+65** |
| Additional final rendered mark Y | — | **+58** |
| `て` GPOS base anchor | (787,614) | **(787,672)** |
| Shared dakuten mark anchor | (92,759) | (92,759), unchanged |
| Relative component / GPOS mark delta | (695,−145) | **(695,−87)** |
| `て` final ink bounds | (230,−8,744,612) | unchanged |
| Placed dakuten final ink bounds | (713,590,850,678) | **(713,648,850,736)** |
| `で` final composite bounds | (230,−8,850,678) | **(230,−8,850,736)** |
| Minimum diagonal ink clearance | 7.810250 | **51.224994** |
| Minimum local vertical ink clearance | 11 | **69** |
| Bounding-box vertical gap | −22 | **36** |

The scoped offset is retained at its existing pre-scale stage. Its +65 source increment becomes exactly +58 final integer Y through the accepted Hiragana anchor scale `0.894078195335`; this is why the two deltas differ. The shared global shift stays **−56**, `KANA_VERTICAL_SHIFT = −201`, and `JAPANESE_MARK_VERTICAL_SHIFT = −176`. The shift is never applied twice.

## Geometry and candidate selection

Measurements use the final production contours after Version 1.027 placement. Quadratic curves are adaptively flattened to 0.02-unit flatness, followed by segment-to-segment Euclidean distance. Filled-path intersection is independently checked. Vertical scans at at most 0.05-unit X intervals compare the upper base contour with the lower mark contour over their shared X region **713…744**.

The relevant upper stroke reaches the base’s yMax **612** near the upper-right turn. The local vertical minimum occurs at **x=733**, with base y=609 and mark y=678 after correction, giving 69 units. The closest diagonal witnesses are base **(733,609)** and mark **(765,649)**, giving `sqrt(32²+40²) = 51.224994`. This tests the nearby stroke region rather than inferring a gap from whole-glyph bounding boxes.

The reviewed target is one nominal pixel at the smallest requested 20 px size: `1024 / 20 = 51.2` font units. Every integer scoped offset from +17 upward was evaluated. **+82 is the first to reach that target**; +81 gives 50.447993 units. The verifier allows a 50…60-unit clearance envelope rather than requiring one exact pixel or one exact floating-point distance.

| Candidate source offset | Final local rise | Diagonal clearance | Local vertical gap | At 20 px | Review |
|---|---:|---:|---:|---:|---|
| +17 (original) | 0 | 7.810250 | 11 | 0.152544 px | Near-touching; insufficient |
| +72 | +49 | 44.400000 | 60 | 0.867188 px | Better, below one-pixel target |
| **+82** | **+58** | **51.224994** | **69** | **1.000488 px** | Selected: smallest setting meeting target |
| +92 | +67 | 58.523500 | 78 | 1.143037 px | Clear, unnecessary extra rise |

The selected dakuten remains compact at 32/64/192 px and visibly separates at 20 px. Comparison with `げ／ぜ／ど／べ` retains a natural handwriting rhythm; their original anchors and glyphs are untouched. The final `で` yMax 736 is within the existing typo ascender 819 and hhea/Windows ascent 967, so no line-metric change is needed.

## Precomposed / decomposed parity and scope

- Precomposed `で` (U+3067): **PASS**. It remains the unchanged `uni3066` base at identity plus unchanged `uni3099` at `(695,−87)`.
- Decomposed `で` (U+3066 U+3099): **PASS**, including a forced GPOS path with U+3067 removed from an in-memory cmap so HarfBuzz cannot hide a bad anchor by recomposing.
- Forced HarfBuzz positions: base `(advance=960, offset=0,0)`; mark `(advance=0, offset=−265,−87)`. The effective mark origin is `(960−265,−87) = (695,−87)`, exactly equal to the composite.
- TTF / WOFF2 parity: **PASS** for all glyphs, metrics and GPOS.
- Every glyph except `uni3067` is identical to the merged 1.027 baseline. The entire GPOS table differs only at `uni3066`’s base anchor Y. All other dakuten/handakuten bases and shared mark anchors are identical.
- `て` topology, center-lines, scale, pressure and final outline are unchanged. All Hiragana/Katakana sources, small kana, yōon, Han (including 壁 / 堅), Latin and unrelated punctuation remain unchanged.
- All advances and side bearings remain unchanged; hhea/OS/2 global metrics, UPM, GSUB/GDEF and name/version records remain unchanged. Only the authorized `で` composite height changes with its attachment.

## Visual proofs

- [20 / 32 / 64 / 192 px before/after](../proofs/quanfangwei-de-dakuten-clearance.png)
- [+17 / +72 / +82 / +92 candidates](../proofs/quanfangwei-de-dakuten-clearance-candidates.png)
- [Actual contours and nearest-distance witnesses](../proofs/quanfangwei-de-dakuten-clearance-geometry.png)
- [Machine-readable measurements](de-dakuten-clearance.json)

Each size includes `て`, `で`, forced-decomposed `で`, and `け げ／せ ぜ／て で／と ど／へ べ`. **20/32/64 px visual QA: PASS**, with the 192 px diagnostic reviewed for compactness and outline identity.

The focused proof explicitly uses **HarfBuzz shaping and FreeType rasterization**. A temporary proof-only PUA cmap addresses glyph IDs on Pillow builds without libraqm; it never enters the production font. This makes the decomposed visual comparison exercise the actual GPOS attachment, instead of relying on an unshaped combining-mark display. Earlier bottom-stage proof images are retained as historical placement evidence; this focused proof supersedes their `で` attachment QA.

## Verification

The focused [verifier](../verify_de_dakuten_clearance.py) checks the merged baseline hash, a positive geometric gap, the two exact permitted changes, all other glyphs/anchors/metrics, and forced precomposed/decomposed parity in both TTF and WOFF2. The bottom-alignment verifier retains its exact −56 oracle with one explicit +58 local `で` exception and invokes this focused check. Reverting to +17 fails the clearance requirement even though outlines technically do not intersect.

All **21 font verifiers passed** (20 existing plus the focused clearance verifier). The master, bottom-alignment and scale-balance verifiers each ran the default canonical rebuild sequentially; all three reproduced TTF and WOFF2 byte-for-byte. Every other verifier ran against the completed output.

```text
verify_cjk_vertical_alignment.py  PASS
verify_de_dakuten_clearance.py  PASS
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
- `node --check` on all `assets/*.js`: **16 passed**.
- `git diff --check`: **PASS**.
- Whole-font TTF/WOFF2, precomposed/decomposed, all 33+33 yōon, small-kana, Han and global-metric regression gates: **PASS**.

## Current output hashes

- TTF: `c7a6d88f48fd7ee10b328851612526629492d60ec7df1d684568a19cfd019cb6` (9,261,228 bytes).
- WOFF2: `d6c4a0b6fd393d8d2a5e59de55892c4354d939ac19fe1b30673f79a547c457bb` (4,701,152 bytes).

No external Japanese outline, base redesign, global dakuten adjustment, CSS/JS workaround, SQL/migration or production database change. Version stays **1.027**.
