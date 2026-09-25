# 荃方位補寫體建置工具

## Current output: Version 1.031 — French guillemet coverage

Native U+00AB `«` (`guillemotleft`) and U+00BB `»` (`guillemotright`) use two transformed components of the original ChenYuluoyan `less` / `greater`. Inspection found no source `« » ‹ ›`. No external font outline was used. A compact 327-unit advance and ink centered around y=290 fit lowercase French prose. All existing glyphs, advances, vertical metrics and layout tables remain unchanged.

[Source, metrics and validation report](reports/french-guillemets.md), [16/20/32/64/192 px proof](proofs/quanfangwei-french-guillemets.png).

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_french_guillemets.py
python tools/font/render_french_guillemets_proof.py
```

The dedicated verifier pins both 1.030 font binaries at base main `4a65b8be24216aa3cf5d23b9e2ba783c0b66090c`, independently checks the exact authorized component recipes, hashes every existing glyph and metric, checks all Unicode cmaps and HarfBuzz shaping, and rebuilds both outputs to require byte identity. Historical verifiers keep their original assertions and explicitly allow only this independently verified two-glyph extension. The proof renderer loads the generated TTF directly with Pillow/FreeType, checks every sample character, and cannot select a fallback font.

## Retained stage: Version 1.030 — Subtle `と` reduction and clearer `ど` separation

Standalone U+3068 `と` is uniformly scaled to **0.98** around its horizontal ink center and fixed bottom `-14`. The unmapped `uni3068.qfwDoBase` used by U+3069 `ど` is then scaled to **0.92** of that revised body, an effective **0.9016** scale relative to Version 1.029. The shared dakuten and `(708,-160)` delta remain unchanged; clearance increases **54.800000 → 78.800000 units** while both forms retain a 960-unit advance. No embolden or scoped anchor move is used.

A narrow `ccmp` rule selects the helper only for decomposed U+3068 U+3099. GPOS includes the helper with the accepted `(800,599)` base anchor, so precomposed and forced-decomposed output is positionally equivalent. Other marks, all unrelated kana and Han, the Version 1.027 `て/で` correction, and the Version 1.028 `踊` correction remain unchanged.

[Measurement / visual QA / validation report](reports/do-base-clearance.md), [CURRENT / A 0.99×0.92 / B 0.98×0.92 / C 0.97×0.92 / FINAL proof at 20/32/64/192 px](proofs/quanfangwei-do-base-clearance.png).

```sh
python tools/font/render_do_base_clearance_proof.py
python tools/font/verify_do_base_clearance.py
```

## Retained Han stage: Version 1.028 — Scoped 踊 optical-size correction

Only U+8E0A maps to a new `uni8E0A.qfwJaOptical` copy of the unchanged original `uni8E0A`. The 59-Han median height is 713; its old height is 590. Candidates `1.178475 / 1.208475 / 1.238475` were compared at actual 20/32/64 px. The selected uniform scale **1.208475** uses the original ink center, then `dx = -43/6`, `dy = -17.499875` to center within the original **826-unit advance** and align the bottom at **−14**. Final ink is `(28.875, -14, 797.391304, 699)`, LSB/RSB **27/26**, with no boundary embolden.

[Complete measurement / visual QA / validation report](reports/kanji-odoru-optical-size.md), [before / three candidates / final proof at 20/32/64/192 px and cell guides](proofs/quanfangwei-kanji-odoru-optical-size.png).

```sh
python tools/font/render_kanji_odoru_optical_proof.py
python tools/font/verify_kanji_odoru_optical.py
```

The focused verifier pins merged 1.027 main `38f441c2bc0e2380c3cd7c1bf4afda1df2f3bc2f` and both original/accepted font SHA256 values. It verifies the independent rounded transform, sole cmap extension, every pre-existing glyph/metric, all 9,343 unrelated Han and 187 kana hashes, all layout tables, TTF/WOFF2 parity, lyric advances and positive adjacent ink gaps, and a byte-identical canonical rebuild. Older verifiers retain their historical oracles with only this independently generated and pinned Han extension; their previous source/scale/position assertions remain intact.

Version 1.027 kana is frozen byte-for-byte at the glyph/metrics/layout level: Hiragana/Katakana scale, −56 global shift, lower-left yōon, marks and `て/で` clearance. The ten preceding Han optical overrides, Latin and punctuation remain unchanged. No CSS/JS workaround, SQL/migration or production DB operation.

## Retained kana stage: Version 1.027 — Kana–Han bottom alignment

Version 1.027 also includes a scoped **て / で dakuten-clearance correction** after the initial bottom-alignment merge. The existing `HIRAGANA_MARK_ANCHOR_Y_OFFSETS["て"]` changes `17 → 82`; because it is applied before the accepted 1.026 anchor scale, +65 source units produce exactly **+58 final Y** for this one attachment. The actual minimum diagonal ink gap increases `7.810 → 51.225` units. The −56 global shift and every base/mark outline, other attachment, advance and global metric stay fixed.

[Scoped clearance report](reports/de-dakuten-clearance.md), [20/32/64/192 px HarfBuzz-shaped proof](proofs/quanfangwei-de-dakuten-clearance.png), [contour-distance diagnostic](proofs/quanfangwei-de-dakuten-clearance-geometry.png), [candidates](proofs/quanfangwei-de-dakuten-clearance-candidates.png).

```sh
python tools/font/render_de_dakuten_clearance_proof.py
python tools/font/verify_de_dakuten_clearance.py
```

The focused verifier pins merged main `514297a9c801e981333fded9473d61489669b486`, allows only the `uni3067` mark component and `uni3066` GPOS base anchor to move by +58, and checks an actual positive clearance envelope. Its precomposed/decomposed checks force the GPOS path, and the proof uses HarfBuzz plus FreeType even on Pillow builds without libraqm. The bottom-alignment verifier includes the same explicit local exception and runs the focused check. The bottom-alignment proofs below retain the initially merged placement stage; the focused proof above shows the corrected final `で`.

The accepted 1.026 glyph coordinates receive one final integer translation `(0,-56)`, after pressure rendering and quantization. `JAPANESE_BOTTOM_ALIGNMENT_SHIFT = -56` is shared by Hiragana, Katakana, all small kana, iteration marks, long sound mark, spacing marks and both script-specific combining-mark designs. Except for the scoped `て` correction above, composite offsets stay identical; the shared Japanese GPOS base and mark anchor Y values both move by -56, retaining every relative attachment.

The unchanged 59-Han sample has median ink yMin `-14`; the pooled 92-kana sample has `41.5`. The measured delta is `-55.5`, rounded to `-56`. Candidates `-64 / -56 / -48` were rendered before selection. Hiragana median yMin becomes `-11.5`, Katakana `-15`. Size factors remain `0.894078195335 / 0.946843040146`; all base/mark outlines, widths, heights, advances, side bearings and source files remain identical; only the scoped `で` composite extent changes with its raised attachment. Effective `KANA_VERTICAL_SHIFT` is `-201` and kana-related `JAPANESE_MARK_VERTICAL_SHIFT` is `-176`. Unrelated punctuation retains its old placement.

[Measurement / visual QA report](reports/kana-bottom-alignment.md), [32 px before/after](proofs/quanfangwei-kana-bottom-alignment.png), [20 px](proofs/quanfangwei-kana-bottom-alignment-small.png), [64 px](proofs/quanfangwei-kana-bottom-alignment-large.png), [candidates](proofs/quanfangwei-kana-bottom-alignment-candidates.png), [bottom guides](proofs/quanfangwei-kana-bottom-alignment-guides.png), [small kana and marks](proofs/quanfangwei-kana-bottom-alignment-derivatives.png).

```sh
python tools/font/build_supplement_font.py
python tools/font/render_kana_bottom_alignment_proof.py
python tools/font/verify_kana_bottom_alignment.py
```

The new verifier pins main `19cf20cf94feb047245f630506ca909af2e7e49b` and its TTF SHA256. It checks all 187 moved glyphs (185 mapped plus two existing mark variants), every other glyph, all 9,344 mapped Han hashes, complete source/reference bytes, GPOS deltas, shaping, exact TTF/WOFF2 parity, clipping and byte-identical rebuild. All hhea/OS/2 globals and UPM remain unchanged. Six yōon lower-left anchors move from `(180,24)` to `(180,-32)` with the rest of the script; their internal offsets are unchanged. Existing standalone combining marks have a historical typographic-ascender overhang that is reduced by this shift; all outlines fit unchanged hhea/Windows bounds and attached text also fits the typographic box.

The complete existing verifier suite remains supported. Old center gates now inspect the accepted pre-translation size stage and additionally check the current bottom target. The historical 1.025/1.026 reports and proofs below are intentionally unchanged; the kana renderers above document the retained 1.027 stages, while the 1.028 renderer at the top documents the current 踊 correction.

## Retained size stage: Version 1.026 — Kana–Han mixed-script optical balance

Version 1.025 shapes and per-glyph normalization are accepted and unchanged. The accepted 1.026 pipeline (before the 1.027 final translation) is:

`Master v2 source → accepted 1.025 normalization/pressure → one script-wide uniform Han-balance scale → small derivation → lower-left yōon translation → marks/composites`.

- A deterministic 59-character Han sample comes from the six requested mixed lines plus all existing lyric and Chinese/Japanese alignment fixtures. All 46 basic kana in each script form the kana sample.
- Noto Sans CJK JP / Source Han Sans JP supply **kana/Han ratios only**. QuanFangwei's unchanged Han body supplies absolute size. `HIRAGANA_HAN_BALANCE_SCALE = 0.894078195335`, `KATAKANA_HAN_BALANCE_SCALE = 0.946843040146`.
- `kana_sources/han_balance.py` uniformly scales coordinates and pressure around the accepted ink-box center. No source-point changes, new per-glyph fits or x/y stretching. All ordinary advances stay 960.
- The 12 small Hiragana inherit the balanced large base once. Existing small-Katakana construction is retained. Six yōon translations are derived from ink bounds to preserve `(180,24)`.
- Marks retain their design and receive the base script's scale. Two unmapped Katakana mark variants and a narrowly scoped GSUB `ccmp` mark selection preserve precomposed/decomposed equality. GPOS anchors scale with the accepted base-to-mark gap. No kana ligatures or pair-spacing rules.
- Iteration marks and `ー` follow the relevant script scale. Other punctuation, all Han (including `壁／堅`), Latin/French/German, CSS/JS and database code are unchanged.

[Historical size report and validation](reports/kana-kanji-scale-balance.md), [32 px mixed proof](proofs/quanfangwei-kana-kanji-scale-balance.png), [20 px](proofs/quanfangwei-kana-kanji-scale-balance-small.png), [64 px](proofs/quanfangwei-kana-kanji-scale-balance-large.png), [same-em cells](proofs/quanfangwei-kana-kanji-same-em.png), [derivatives](proofs/quanfangwei-kana-kanji-derivatives.png).

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_kana_kanji_scale_balance.py
```

The new verifier pins immutable base `e19227dbb31666e8373045a2edeb3456d00bd373`, all accepted source files, exact scalar-reference SHA256, all glyphs, advances, both-script shaping and TTF/WOFF2 parity. Exactly 185 kana/related mapped glyphs may change; two unmapped mark-size variants are added. All 9,344 mapped Han glyphs remain identical. Default verification repeats the canonical build byte-for-byte; `--skip-rebuild` skips only that repeat.

The existing verifier entry points remain supported. The master verifier retains 1.025 provenance gates and checks current output through the new balance verifier. The absolute-metric verifier checks its immutable 1.025 intermediate stage, then the current Han-relative ratios. The pressure verifier retains the accepted 1.025 weight gate and compares current kana to its uniformly scaled raster weight with explicit pixel-quantization tolerance. Source and taper hashes are still exact.

External font binaries are analysis-only, outside the repository. `measure_kana_kanji_balance.py --noto /path/to/NotoSansCJKjp-Regular.otf --source-han /path/to/SourceHanSansJP-Regular.otf` reproduces the scalar snapshot; it is not part of normal builds. No external contours or raster autotracing are used.

The following 1.025 discussion and proof links document the **accepted shape stage**, not 1.026 final optical size. Do not rerun its historical proof renderers over 1.026 output; use the current renderer above. The original absolute-metric targets and reference files are intentionally immutable.

## Retained shape authority: Version 1.025 — Complete Maintainer Hiragana Master v2

All 46 modern basic Hiragana are refreshed from the maintainer's complete Master v2 source set. Both authoritative references are maintainer-owned:

- Main 41-glyph sheet: `references/hiragana-maintainer-master-v2.png`, SHA256 `779559e9a7f3e7fe914987f882c2029f50881a53b092318db3d356f9792e8db1`.
- Supplementary na-row sheet: `references/hiragana-maintainer-master-v2-na-row.png`, SHA256 `6a85555d562e9e2633b72a2aa4c7567cf5479a3f162b570de3b62039ce81e821`.

Together they supersede every older reference for all 46 basic Hiragana, including the earlier legibility-reviewed `の`. The new na-row explicitly supersedes the previous preserve-na-row rule. No basic Hiragana intentionally remains on an older authoritative source. Older images and historical notes remain provenance only.

`kana_sources/hiragana_master_v2.py` records the explicit eleven-row combined mapping, intentional gaps, glyph crops and manually interpreted pixel-space pen paths. Each drawing first receives an arbitrary uniform source-coordinate fit; absolute production size then comes from standard Japanese metrics through a reviewed uniform optical scale and dx/dy. No aspect distortion is applied. The unchanged variable-width renderer and family pressure factors produce the final outlines. Raster thickness is not literal production weight. No raster outline, autotrace or external Japanese font outline is installed.

`なにぬねの` use new clean center-lines from the supplementary sheet and freshly reviewed uniform metric-based optical transforms. No small na-row forms are introduced. Every normal small Hiragana still uses the normal 0.72-scale path (including the existing scoped `ゎ` adjustment). `ゃゅょ` first derive from the new `やゆよ`; only their post-scale deltas are recalibrated to preserve the reviewed `(180,24)` lower-left ink anchor. Katakana sources and `ャュョ` deltas are unchanged. All 26 voiced/semi-voiced Hiragana use the revised base plus the unchanged shared marks; bounds-derived anchors and GPOS are verified, including forced decomposed HarfBuzz shaping and collision checks.

Noto Sans CJK JP Regular (UPM 1000) and Source Han Sans JP Regular (UPM 1000) were measured from temporary files outside the repository. Their 46 Hiragana metric sets are identical and count as one standard reference; production 1.024 (UPM 1024) is the independent continuity reference. Each target height and box center is their median in em ratios. Width is a sanity envelope, retaining handwritten aspect. All 46 use uniform scale plus dx/dy; advance remains 960. External binaries/outlines are neither committed nor read by the canonical build. See [per-glyph metrics, family size gate and flagged outlier review](reports/hiragana-standard-metrics.md), [full CSV](reports/hiragana-standard-metrics.csv), and [same-em box proof](proofs/quanfangwei-hiragana-standard-metrics.png).

Large normalization precedes all small derivation. After reviewing the normalized bases, only the `て` mark anchor requires an extra +17 y to keep `で` separated; shared dakuten/handakuten contours remain unchanged.

The former live `け` measurement used for `気／付` is frozen at its accepted Version 1.024 bounds `(276,6,740,659)`, preventing unrelated Han movement. All Han output, including `壁／堅`, and all Latin/French/German output remains identical. The global engine, metrics and web code are unchanged.

```sh
python tools/font/build_supplement_font.py
python tools/font/render_hiragana_master_v2_proofs.py
python tools/font/render_hiragana_metrics_proof.py
python tools/font/verify_hiragana_metrics.py
python tools/font/verify_supplement_font.py
python tools/font/verify_hiragana_master_v2.py
python tools/font/verify_handwritten_hiragana_svg.py
python tools/font/verify_yoon_position.py
python tools/font/verify_japanese_weight.py
python tools/font/verify_japanese_optical_alignment.py
```

The 1.025 revision was verified against immutable base `d89ee8b2b5f4c858e5dade853972194892037f93`: exactly 84 dependent outputs changed (46 bases + 12 small + 26 voiced), with all 46 drawings independently checked against reference pixels and a byte-identical rebuild. Those source hashes, normalization records and proofs are retained. Current verifier entry points use the 1.026 scale contract described above, with accepted 1.025 geometry as the shape oracle.

[Complete measurements and validation report](reports/hiragana-master-v2.md). [Source manifest](references/hiragana-master-v2-manifest.json). Historical 1.025 proof files:

- [Complete master row arrangement](proofs/quanfangwei-hiragana-master-v2-proof.png)
- [Reference / generated font](proofs/quanfangwei-hiragana-master-v2-comparison.png)
- [Per-glyph overlays](proofs/quanfangwei-hiragana-master-v2-overlay.png)
- [All 46 from the complete Master v2](proofs/quanfangwei-hiragana-master-v2-full-46.png)
- [Na-row reference / old / new](proofs/quanfangwei-hiragana-master-v2-na-row.png)
- [Na-row samples and にゃ/にゅ/にょ](proofs/quanfangwei-hiragana-master-v2-na-text.png)
- [Family weight](proofs/quanfangwei-hiragana-master-v2-family-weight.png)
- [Production text and unchanged existing lyric fixtures](proofs/quanfangwei-hiragana-master-v2-production-text.png)
- [All small, voiced and yōon combinations](proofs/quanfangwei-hiragana-master-v2-derivatives-yoon.png)

Build environment for this revision: Python 3.12, repository-pinned fontTools/Pillow/uharfbuzz/skia-pathops/NumPy/SciPy; Brotli 1.1.0 wheel because 1.0.9 has no Python 3.12 macOS wheel and this machine has no compiler. The repository dependency pins remain unchanged. Determinism is verified within this environment; no cross-Brotli compressed-byte identity is claimed.

## Historical build and revision notes

這套流程從 repository 內未修改的官方 `ChenYuluoyan-2.0-Thin.ttf` 建立獨立命名的「荃方位補寫體 / QuanFangwei Supplement Script」。它依 SIL Open Font License 1.1 製作，並非原作者官方更新版。

目前 Windows 驗證環境沒有 FontForge，因此實際可重複流程使用 fontTools 的 TrueType pen、composite glyph、OpenType layout builder 與 WOFF2 writer，不依賴 FontForge GUI。輸出是可由 fontTools 與瀏覽器正常開啟的真實 TTF／WOFF2；若未來採用 FontForge，必須保持 manifest、名稱、輪廓建構與驗證條件一致。

若需要另外安裝 FontForge，可從 [FontForge 官方 Windows 下載頁](https://fontforge.org/en-US/downloads/windows/)取得安裝程式，安裝後重新開啟 PowerShell 並執行 `fontforge --version`。目前這份建置腳本的受驗證路徑是下方的標準 Python/fontTools 命令；沒有假設或冒充 FontForge scripting API 已執行。

## 環境與命令

```powershell
python -m pip install -r tools/font/requirements.txt
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/render_proof.py
python tools/font/render_oe_proof.py
python tools/font/render_ki_proof.py
python tools/font/render_ya_proof.py
python tools/font/render_yoon_position_proofs.py
python tools/font/verify_yoon_position.py
python tools/font/render_o_proof.py
python tools/font/verify_hiragana_o.py
python tools/font/render_handwriting_fidelity_proof.py
python tools/font/verify_handwriting_fidelity.py
python tools/font/render_su_proof.py
python tools/font/verify_hiragana_su.py
python tools/font/render_cjk_vertical_alignment_proof.py
python tools/font/verify_cjk_vertical_alignment.py
python tools/font/analyze_glyphs.py
python tools/font/audit_japanese_coverage.py
python tools/font/audit_japanese_kanji.py [optional TXT/LRC/JSON paths]
python tools/font/audit_japanese_weight.py
python tools/font/verify_japanese_weight.py
python tools/font/analyze_oku_optical_alignment.py
python tools/font/verify_oku_optical_alignment.py
```

建置腳本會先輸出每個參考字元、Unicode code point、Unicode name 與預期 glyph name，並驗證兩張 reference PNG 可開啟。來源 TTF 的 SHA-256 也會被核對；不符合已審核的官方檔案時建置會失敗。所有暫存輸出先寫入衍生目錄，完成後才替換正式檔案，不會修改原始 TTF。

官方原始 TTF 的 TrueType hint program 在 FreeType/Pillow 會觸發 `too many function definitions`。衍生版建置會清除 hint bytecode 與 `fpgm`／`prep`／`cvt ` tables，保留實際輪廓、cmap、glyph 順序、advance 與垂直 metrics，讓 proof 與網頁字型解析保持穩定。

## 檔案

- `glyph_manifest.json`：字元身分、來源 glyph 與建構方法。
- `references/U+00BF-questiondown.png`：`¿` 身分參考圖。
- `references/U+00C7-Ccedilla.png`：`Ç` 身分參考圖。
- `references/U+304D-ki-maintainer-handwritten.png`：Version 1.021 維護者新提供的 `き` 結構參考；不直接作為 filled outline 安裝。
- `references/U+3084-ya-maintainer-handwritten.png`：Version 1.022 維護者新提供的 `や` 結構參考；不直接作為 filled outline 安裝。
- `references/U+304A-o-maintainer-handwritten.png`：Version 1.023 維護者新提供的 `お` 結構與比例權威參考；僅作 provenance，不直接安裝、autotrace 或轉成 filled outline。
- `references/U+3046-u-maintainer-handwritten.png`：Version 1.024 維護者新提供的 `う` 結構與比例權威參考；僅作 provenance，final outline 仍由 project-local center-lines 與既有 renderer 產生。
- `references/U+3042-U+3044-U+3055-U+304D-maintainer-handwritten.png`：Version 1.024 維護者 `あ／い／さ／き` 權威 reference sheet；黑色外框用於量測比例、筆寬與 medial skeleton，不直接安裝 bitmap contour。
- `references/U+3068-U+308A-maintainer-handwritten.png`：Version 1.024 維護者 `と／り` 權威 reference sheet；使用相同 center-line → renderer 流程。
- `build_supplement_font.py`：建立 TTF、WOFF2、OFL 與修改紀錄。
- `verify_supplement_font.py`：驗證 cmap、glyph、metadata、授權與來源保存。
- `render_proof.py`：以輸出 TTF 產生 glyph analysis、16／24／32／48／72 px 輔助線 proof 與自然文字 proof。
- `render_oe_proof.py`：確認 U+0152／U+0153 cmap 後，以目前輸出 TTF 產生 `Œ`／`œ`、法文單字、production phrase，以及 `O E`／`OE`／`Œ` 和 `o e`／`oe`／`œ` 多尺寸 proof。
- `render_ki_proof.py`：將 `origin/main` 舊版與 Version 1.021 新版 `き`／`ぎ` 並列，並輸出 24／32／48／72 px 的 `きき`、`ぎき`、`ぎん`、`きれい`、`好き`、`大きい`。
- `render_ya_proof.py`：並列維護者 raster reference、`origin/main` 舊版 `や` 與 Version 1.022 新版 `や`／`ゃ`，並驗收常見 yōon 與自然文字組合。
- `render_yoon_position_proofs.py`：產生 Version 1.023 平假名／片假名 YA・YU・YO 完整 proof grid、六字 960-unit cell diagnostic 與 origin/main before/after proof。
- `verify_yoon_position.py`：驗證 `ゃゅょャュョ` 只作 scoped translation、advance 不變、大字 source 與非 yōon 小假名不變，以及 TTF／WOFF2 一致。
- `render_o_proof.py`：並列 maintainer reference、origin/main 1.023 舊 `お`、Version 1.024 repaired `お／ぉ`、個別 cell、普通小母音對與自然文字。
- `verify_hiragana_o.py`：驗證 `お` 三筆 `[6,29,4]` photo-coordinate topology、`ぉ` 普通 0.72-scale derivation、無 yōon offset、控制字不變，以及 TTF／WOFF2 一致。
- `render_su_proof.py`：並列 origin/main 1.023 與 Version 1.024 `す／ず`，並顯示平假名字重 row 與自然文字。
- `verify_hiragana_su.py`：驗證 `す` 只作局部 pressure repair、兩筆 center-line／optical placement 不變、`ず` 繼承新版 base 且 dakuten transform 不變。
- `render_u_proof.py`：並列 maintainer reference、origin/main 舊 `う` 與 Version 1.024 `う／ぅ／ゔ`，並顯示 glyph cells、自然文字與 voiced-vowel sequences。
- `verify_hiragana_u.py`：驗證 `う` 權威兩筆 source、`ぅ` 一般 0.72-scale 衍生、無 yōon offset、`ゔ` bounds-derived dakuten placement、控制字不變與 TTF／WOFF2 一致。
- `render_hiragana_maintainer_batch_proof.py`：並列兩張新 reference sheets、origin/main 舊字與新版 `あ／い／さ／き／と／り`，並顯示衍生字、yōon 組合、五十音 family rows 與自然文字。
- `verify_hiragana_maintainer_batch.py`：驗證六個新 source topology／bounds、identity transforms、`ぁ／ぃ` 普通小假名、`ざ／ぎ／ど` composite、`き／り` yōon composition、非 target source 不變及 TTF／WOFF2 parity。
- `render_cjk_vertical_alignment_proof.py`：產生 `壁／堅` 個別 glyph box 與日文／中文完整行文字 before/after proof。
- `verify_cjk_vertical_alignment.py`：驗證 `壁／堅` 只作 `dy +97／+55` source-identical translation，advance、x 位置、topology、全域 line metrics 與 control Han 不變，TTF／WOFF2 一致且無 clipping。
- `analyze_glyphs.py`：列出 TTF／WOFF2 指定 cmap、advance、bounds、components、glyph count 與 cedilla anchors。
- `browser-proof.html`：本機瀏覽器 Rendered Fonts 驗收頁。
- `kana_sources/master_data.py`／`full_data.py`：可版本控制、可重建的原創假名 center-line source。
- `japanese/`：stroke renderer、假名／mark／標點 build 模組與 metrics／GPOS orchestration。
- `audit_japanese_coverage.py`：掃描 Hiragana、Katakana、CJK Symbols and Punctuation 與 Katakana Phonetic Extensions。
- `audit_japanese_kanji.py`：只分析本機 TXT／LRC／JSON；不抓取網路歌詞。
- `reports/kana_style_analysis.md`：官方來源筆畫粗細、端點、曲線、傾斜、重心、baseline 與字框分析。

### Japanese Phase 1 Support（Version 1.012）

- 基本平假名、片假名、small kana、濁音、半濁音、iteration marks、`・`、`ー` 與指定常用日文標點完整進入同一 Family。
- 新假名使用一致的 `uniXXXX` glyph naming；官方來源已存在且正常的標點保持原 glyph mapping、輪廓、metrics 與 glyph order。
- U+3099 `uni3099` 與 U+309A `uni309A` advance 0，屬 GDEF mark class；U+309B／U+309C 是 advance 300 的 spacing forms。
- 預組合與分解形式共用同一 mark contour，GPOS MarkBasePos delta 亦與 composite component delta 完全相同。
- 假名以 960-unit advance 對齊原字型 CJK 約 944-unit median advance，同時保持原 1024 UPM、ascent/descent 與繁中 glyph 不變。
- 所有新輪廓都由本 repository 的 original center-line data 產生；沒有載入或 trace 任何外部日本字型輪廓。
- `kana_sources/legibility_overrides.py` 保存第二輪辨識度修正；`の` 維持明顯開口與內收尾筆，並刻意拉開 `シ／ツ`、`ソ／ン` 的主筆方向。
- Version 1.008 依使用者提供的標準手寫表校對字形結構；build-time kana y shift 為 -145 units，中央日文符號為 -120 units，GPOS kana base anchor y 為 690。`proofs/quanfangwei-cjk-kana-alignment-proof.png` 以同一 face、size、baseline 驗證中日混排，沒有 CSS 位移。
- Version 1.009 的 `kana_sources/hiragana_redesign.py` 保存完整現代平假名的第三輪原創 center-line source；`さ／ち` 下段分離，`の` 使用斜入、左回環與右側長收筆。`proofs/quanfangwei-hiragana-redesign-proof.png` 以 120 px 字格與 48 px 歌詞行驗收辨識度。
- Japanese kanji 目前沿用 shared Unicode code point 的既有辰宇落雁 glyph；不建立大規模 `locl JAN`。
- U+5965 `奥` 保留官方 `uni5965` source drawing，並以 U+5967 `奧` 為 authoritative browser reference，映射到 non-uniform `scale_x 0.921976`、`scale_y 0.855348`、dx +9、dy +34.5 的 derived optical copy，再套用 4-unit boundary embolden；advance 790，final LSB／RSB 122／122。以 `analyze_oku_optical_alignment.py`、`verify_oku_optical_alignment.py` 與正式 WOFF2 `oku-browser-proof.html` 驗收。

Known limitations：Phase 1 不保證所有 Jōyō Kanji 日本字形變體、vertical writing、ruby typography、完整 Ainu extensions、historical kana、half-width katakana 或所有標點變體。Phase 2 會以實際 TXT／LRC／JSON 歌詞缺字頻率與 regional-variant review 為基礎。

## 字形建構

- `き`／`ぎ`：Version 1.021 將維護者新提供的 U+304D PNG 視為 authoritative structural reference，只替換 `USER_HANDWRITING_REFINED["き"]`。舊 12 branches 改成 4 個 clean center-line strokes；reviewed optical transform 保留 0.96 scale，並依混排 QA 增加 `dx +24` 修正視覺偏左。PNG 不直接安裝或盲目 autotrace；final outline 經既有 variable-width renderer。U+304E `ぎ` 仍是 `uni304D` + `uni3099` composite，bounds-derived anchor 隨新版 `き` 自動更新，無手動或全域 dakuten 修改。
- `や`／`ゃ`：Version 1.022 將維護者新提供的 U+3084 PNG 視為 authoritative structural reference，只替換 `USER_HANDWRITING_REFINED["や"]`。舊 7 branches 改成 compact hooked cross-stroke、分離 upper mark 與長斜下行筆的 3 個 clean center-lines；新 source 使用 identity optical transform。`ゃ` 仍由 normalized `や` 以 0.72 scale 及 shared -12 y shift 衝生，無獨立 topology。PNG 不直接安裝或 autotrace，final outline 經既有 variable-width renderer，未使用外部日文字型輪廓。
- `ゃゅょ`／`ャュョ`：Version 1.023 保留現有 0.72-scale construction 與 source topology，只在 scaling 後以 `YOON_SMALL_KANA_OFFSETS` 逐字向左下移動。六字仍各佔獨立 960-unit advance cell；沒有 ligature、kerning pair、negative advance、CSS／JS workaround 或外部日文 outline。`やゆよ`／`ヤユヨ` 與其他小假名不變。
- `お`／`ぉ`：Version 1.023 另以 maintainer 新手寫 PNG 明確授權替換 U+304A 舊 8-branch topology，重建為 upper cross、連續 tall vertical/open lower body、detached right mark 三筆 center-lines。U+3049 由新 normalized `お` 以 0.72 scale 及 shared `(0,-12)` 重建，不屬於 yōon，不套用 `YOON_SMALL_KANA_OFFSETS`。
- `壁`／`堅`：Version 1.023 將官方來源輪廓以 identity scale 複製到獨立 `.qfwJaOptical` glyph，只套用 `dy +45／+35`。兩字的 source drawing、topology、x placement、advance 不變；沒有 global CJK baseline／line metrics 或 CSS／JS 位移。
- Version 1.024 repair：`お／あ／い／う／さ／き／と／り` 依原照片座標手工採樣 pen paths，單一等比例縮放入字格，八字 optical transforms 均為 identity（取消 `う` 舊軸向拉伸）；筆壓與收筆交由既有 renderer。`す` 保留兩筆來源及局部 taper 修正；新版 `き` supersede 1.021；`ぁ／ぃ／ぅ／ぉ` 保持普通小假名路徑，`ざ／ぎ／ど／ず／ゔ` 繼承 base。`壁／堅` dy +97／+55、bottom 同為 -15；沒有全域 weight／baseline 修改。
- `kana_sources/maintainer_photo_sources.py`：八字原照片座標、獨立 glyph crops、單一等比 normalization 與輕度筆壓。正式 build 不讀取 raster pixel data。
- `render_handwriting_fidelity_proof.py`：原圖／immutable previous PR／實際新 TTF／紅藍疊圖，沒有 x/y 分開拉伸；另輸出 ink-overlap metrics JSON（診斷數值，不是主觀相似度）。
- `verify_handwriting_fidelity.py`：以真實 reference pixels 驗證輪廓貼合，逐一比對整份 font，限定八個 base 加八個衍生 glyph 可變；其他字形、yōon、`す／ず`、`壁／堅` 與 global metrics 必須相同。
- `OE`：U+0152 LATIN CAPITAL LIGATURE OE，Version 1.021 新增。只組合官方來源中未修改的大寫 `O`／`E` identity components，保持原生 cap-height、stroke weight 與 baseline；`E` 依實測 `O` ink width 的 10% 向左 tuck，並以 final ink xMax 加來源 `E` right side bearing 決定 advance。
- `oe`：U+0153 LATIN SMALL LIGATURE OE，同版新增。只組合未修改的小寫 `o`／`e` identity components，以相同 bounds-derived 規則形成緊湊連字。`Œ`／`œ` 都是衍生版的法文補寫字元，不是原始辰宇落雁體既有字形；未載入或複製外部 outline，也未用 CSS／JavaScript 改寫 `Œuvre` 或 `cœur`。
- `questiondown`：第一版是將原字型 `question` 機械式旋轉 180°。本次仍以該輪廓為唯一來源，但旋轉後平移 +3 x／-12 y font units，並將圓點再下移 8 units；這讓上端落在 cap height 內、底部接近其他句首符號，並把點與主筆間距由機械鏡射調成 60 units。原始 `question` 未修改，advance width 仍為 312。
- `cedilla`：第一版只是將原始 `comma` 向下移，外觀偏小且容易像黏在 C 下方的逗號。原字型沒有 U+00B8 或 U+00E7；精修版改用原始 `semicolon` 的下方尾筆輪廓，水平縮放 116%、垂直縮短為 82%，再旋轉 -7°。`comma`、`J`、`j`、`g`、`y` 用於比較同字型的尾筆、曲率與下伸深度，沒有從其他字型複製輪廓。
- `Ccedilla`：以完全未改形的原始 `C` 加上精修 `cedilla` component 組成。Cedilla 置於 C 的光學中心（不是單純 bounds 中心）且保留 26 units 的正間距；advance 與 side bearings 與原始 C 相同。
- `ccedilla`：U+00E7 LATIN SMALL LETTER C WITH CEDILLA。以完全未改形的原始 `c` 加上同一精修 `cedilla` component 組成，位移 `+81 x / +10 y`，維持 26 units gap；advance 與 side bearings 與原始 c 相同。
- `uni0327`：U+0327 COMBINING CEDILLA。以 identity component 共享精修 `cedilla` 輪廓，advance width 為 0，並在 GDEF 標記為 mark。建置保留原始 GPOS/GDEF，只在既有 `mark` feature 附加單一 MarkBasePos lookup；C/c base anchors `<221 91>`／`<176 101>` 與 mark anchor `<95 91>` 分別產生 `+126/0`／`+81/+10` 位移，與 `Ccedilla`／`ccedilla` components 完全一致。預組合及分解的大小寫形式都由字型原生支援，不透過 JavaScript 強制 NFC normalization。

### German support（Version 1.005）

- 原始字型已包含 `Adieresis`／`Odieresis`／`Udieresis`／`adieresis`／`odieresis`／`udieresis` 與 zero-advance `uni0308`，本版不重畫、不覆蓋。原始 mark anchor `<145 477>` 及 A/O/U/a/o/u base anchors `<272 622>`／`<235 564>`／`<174 565>`／`<172 464>`／`<153 420>`／`<180 415>` 均保留，所以 composed 與 decomposed Umlaut 使用同一筆畫與定位。
- `dieresis`：U+00A8 spacing DIAERESIS。identity-reference 原始 `uni0308` 的兩個手寫點，advance 300、左右約 60 units；U+0308 自身仍為 advance 0。點不是幾何圓，也沒有取自其他字型。
- `germandbls`：U+00DF ß。依最新提供的手寫字母表參考，採用官方原字型 U+03B2 `beta` 的單一連續輪廓與原生比例；仍建立獨立 `germandbls` glyph 和 U+00DF cmap，不是把文字 code point 改成 U+03B2。
- `uni1E9E`：U+1E9E ẞ。使用同一 `beta` 輪廓語言，水平 110%、垂直 74%、上移 204 units，使 descender 收入 capital zone；advance 430，保留獨立 `uni1E9E` glyph 與 U+1E9E cmap。
- U+03B2 原始 glyph、cmap 與 metrics 完全不變；ß／ẞ 的輪廓只來自 repository 內官方辰宇落雁體，未使用 Arial、Times、Noto、Google Fonts 或任何外部字型輪廓。

`verify_supplement_font.py` 除了既有格式、cmap、名稱、授權及來源保存檢查，也量化檢查 `¿` 的 advance、side bearings、bounds center、點與主筆間距和 clipping，以及 `Ç`／`Ç`、`ç`／`ç` 的原始 base identity component、共用 cedilla 輪廓、zero advance、GDEF class、GPOS anchors、光學中心、碰撞、descender 與 advance。驗證也確認原始 GPOS lookups 未被覆蓋，並以 uharfbuzz 強制走大小寫分解序列，確認 mark origins 與預組合 components 完全相同。這些檢查不能替代美學判斷；筆勢、字面平衡與小尺寸辨識度仍須查看：

- `proofs/quanfangwei-glyph-analysis.png` 與對應 JSON 度量紀錄
- `proofs/quanfangwei-optical-proof.png`（含 baseline、ascender、descender、advance box）
- `proofs/quanfangwei-natural-proof.png`（無輔助線自然文字）
- `proofs/quanfangwei-cedilla-proof.png` 與 `.txt`（預組合／分解形式、code points、16／24／32／48／72／120 px 對照）
- `proofs/quanfangwei-german-proof.png` 與 `.txt`（16／20／24／32／48／72／120 px Umlaut 及真實德文）
- `proofs/quanfangwei-sharp-s-proof.png`（144 px ß／ẞ、baseline、x-height、cap-height、ascender、descender 與 advance box）
- `proofs/quanfangwei-oe-proof.png`（18／28／44／72／120 px 的 `Œ`／`œ`、法文單字、baseline、大小寫 spacing 比較與 production phrase）
- `proofs/quanfangwei-ki-proof.png`（維護者 raster reference、origin/main 舊版、Version 1.021 新版與 `き`／`ぎ` 多尺寸混排）
- `proofs/quanfangwei-hiragana-ya-redesign-proof.png`（維護者 raster reference、origin/main 舊版、Version 1.022 `や`／`ゃ`、yōon 與自然文字混排）
- `proofs/quanfangwei-yoon-position-proof.png`（平假名／片假名完整 K、SH、CH、N、H、M、R、G、J、B、P 網格）
- `proofs/quanfangwei-yoon-cell-diagnostic.png`（六字 advance origin、cell edge、baseline、ink bounds 與 sidebearing）
- `proofs/quanfangwei-yoon-before-after-proof.png`（origin/main 1.022 與 Version 1.023 左下位移對照）
- `proofs/quanfangwei-hiragana-o-proof.png`（maintainer reference、OLD/NEW `お`、derived `ぉ`、glyph cell、小母音對與自然文字）
- `proofs/quanfangwei-hiragana-su-proof.png`（OLD/NEW `す／ず`、Hiragana family weight 與自然文字）
- `proofs/quanfangwei-cjk-vertical-alignment-proof.png`（`壁／堅` bounds/optical-center diagnostics 與日文／中文行文字 before/after）

## 新增下一個缺字

1. 用 Python `unicodedata` 確認實際字元、code point 與 Unicode name。
2. 將 reference image 與項目加入 `glyph_manifest.json`。
3. 優先轉換或組合原字型現有 glyph，不從未授權字型複製輪廓。
4. 在 `build_supplement_font.py` 加入確定性建構函式。
5. 在 `verify_supplement_font.py` 加入 cmap、輪廓、bounds 與 advance 驗證。
6. 重新輸出 TTF 與 WOFF2。
7. 產生 proof image 並目視確認。
8. 在瀏覽器確認 Network、`document.fonts` 與 Rendered Fonts，排除 fallback。
9. 更新 `MODIFICATIONS.md` 與網站 README。

OFL 的 Reserved Font Name 不可用於修改版主要 Family／Full／PostScript／Typographic Family 名稱。原作者、來源與 Reserved Font Name 只能在 copyright、license、credit 或修改說明中保留。


### User-authored Hiragana SVG revision（Version 1.010）

- `tools/font/references/user-hiragana-template-source.png` 是專案維護者本人提供的原始手寫稿。
- 來源稿中的 43 個基本平假名保存為獨立 SVG，並由字型建置程式直接轉成 TrueType 輪廓。
- 來源稿沒有 `わ／を／ん`；這三字與片假名仍沿用既有 project-local center-line 設計。
- `ぁぃぅぇぉゃゅょっゕゖ` 由對應 SVG 基底作確定性縮放；濁音／半濁音繼續共用 base 與 mark components。
- 來源、SVG hash、轉換參數與逐字 cell mapping 記錄於 `references/user-hiragana-template-manifest.json`。
- 驗收指令：`python tools/font/verify_handwritten_hiragana_svg.py` 與 `python tools/font/render_handwritten_hiragana_proof.py`。


### Refined user-handwriting Hiragana（Version 1.011）

- 維護者本人手寫 SVG 已補齊完整 46 個現代基本平假名；Version 1.011 新增 `わ／を／ん`。
- SVG 現在只作字形結構與比例 reference；最終 TTF 不再直接安裝 SVG filled outline。
- `kana_sources/user_handwriting_refined.py` 保存從手寫 reference 整理出的確定性 center-line branches，並交由既有 variable-width handwriting renderer 建構。
- 每字重新置中至 `(480,500)`；結構 x/y scale 為 `1.10/1.28`，target stroke width `42–50` units，build-time y shift 仍為 `-145`。
- `ぁぃぅぇぉゃゅょっゎゕゖ` 由 refined bases 確定性縮放；濁音／半濁音繼續共用原有 GPOS/GDEF mark flow。
- 主要驗收圖：`proofs/quanfangwei-user-handwritten-hiragana-proof.png`、`proofs/quanfangwei-user-handwritten-mixed-proof.png`、`proofs/quanfangwei-cjk-kana-alignment-proof.png`。
- 驗證：`python tools/font/verify_handwritten_hiragana_svg.py`。


### Special Japanese refinement（Version 1.012）

- `す`：中央 loop/counter 擴大，16–24 px 仍保留可辨識內白。
- `り`：第二筆下方收尾延長，讓歌詞尺寸的尾巴更明顯。
- `懐` U+61D0、`夕` U+5915：以維護者本人最新手寫圖為結構來源，整理為 center-line 後交由既有 variable-width handwriting renderer 重建，不直接嵌入 raster。
- `気` U+6C17、`付` U+4ED8：原始 source glyph drawing 不修改；新增 derived optical copies，只做 vertical scale/translation，使 `気付け` 的 ink center/height 更接近 refined `け`。
- 只有上述四個 Han code point 是原始 cmap identity 的明列例外；source glyph 本身仍保留且 verifier 會比較 drawing 未變。
- Proof：`proofs/quanfangwei-special-japanese-1.012-proof.png`、`proofs/quanfangwei-special-japanese-1.012-mixed-proof.png`。
- Verification：`python tools/font/verify_special_japanese_overrides.py`。


### Version 1.013 stable-release scope

- `懐` (U+61D0) is intentionally left on the original ChenYuluoyan source glyph.
- `々` (U+3005) uses the existing Phase-1 handwritten mark; the later experimental redraw is not shipped.
- `夕` (U+5915) remains on the original source glyph.
- Other reviewed Hiragana refinements and the existing `気`/`付` mixed-alignment work remain included.

### Version 1.014 optical normalization and approved special glyphs

- `USER_HANDWRITING_REFINED` remains the authoritative 46-Hiragana topology. `kana_sources/user_handwriting_optical.py` applies only uniform per-glyph scale and translation around it.
- Every small Hiragana derives from its normalized large form at 0.72 scale; large `や` remains an identity control and `ゃ` shares its topology.
- `懐` combines the native source-face `懷` upper/left outline with a uniformly scaled and positioned native `衣` lower outline. The original `懐`、`懷`、`衣` drawings remain present and unchanged.
- `々` uses dedicated project-local center-lines rendered by the existing variable-width engine; its approved right/lower gestures intersect. `夕` remains completely unchanged.
- Visual gates: `proofs/quanfangwei-hiragana-optical-before-after-proof.png`、`proofs/quanfangwei-small-kana-ya-proof.png`、`proofs/quanfangwei-user-japanese-specials-proof.png`、`proofs/quanfangwei-user-japanese-mixed-proof.png`.
- Verification: `python tools/font/verify_handwritten_hiragana_svg.py` and `python tools/font/verify_special_japanese_overrides.py`.

### Version 1.015 Japanese glyph optical alignment

- `す` keeps the authoritative Version 1.014 handwritten branches and point order; only the outer transform widens it from effective `scale_x=1.04` to `1.60`, retains `scale_y=1.04`, and shifts its optical center right and down.
- Version 1.015 的 `恋／哀／奧／優／寄` 使用各自記錄的等比例 source-derived transform；當時 U+5965 `奥` 尚未調整，Version 1.020 採用獨立 non-uniform optical derived copy。
- Version 1.016 adds the same source-preserving derived mechanism for `変` U+5909: uniform `0.80` scale around its native ink center, `dx +19.25 / dy +35`, then an `8-unit` boundary embolden on the derived copy to restore the source face's apparent stroke weight.
- These are shared-cmap derived copies because the current font has no `locl JAN`; no broad language-specific GSUB architecture is introduced.
- Proof: `proofs/quanfangwei-japanese-optical-alignment-proof.png` at 16／20／24／32／48／72 px.
- Verification: `python tools/font/verify_japanese_optical_alignment.py`.

### Version 1.016 け／う optical adjustment

- `け` keeps its accepted source branches; only the outer transform widens it to `scale_x=1.06` while retaining `scale_y=1.00`, then moves it `+28 x / -26 y`.
- `う` keeps its accepted source branches, is adjusted to `scale_x=1.12`／`scale_y=1.08` around `(480,500)`, and receives only `dy=-20` translation.
- `こ` keeps its accepted source branches and size; only the outer transform moves it `+28 x`.
- `わ` U+308F is the explicit Version 1.016 user-reference topology rewrite: two project-local center-line strokes rendered by the existing variable-width engine. `ゎ` derives at the existing 0.72 scale, then receives an additional `+14 x / -14 y` right/down optical shift.
- The other 45 Hiragana source topologies and all unlisted transforms remain unchanged. Small kana continue deriving from the normalized large forms.
- Proof: `proofs/quanfangwei-ke-u-optical-proof.png` at 16／20／24／32／48／72 px.
- Verification: `python tools/font/verify_hiragana_ke_u_optical.py`.

### Version 1.017 Japanese stroke-weight harmonization

- `japanese/stroke_engine.py` 新增 `scale_stroke_weight()`，只比例調整 `width`、`start_width`、`end_width`，保留 center-line points、stroke topology、cap 與 taper ratio。
- 大平假名使用 ×1.10；小平假名從 normalized large kana 的 0.72 字面縮放繼承相同壓力補償；片假名使用 ×1.14。Dakuten ×1.10、handakuten ×1.20、長音 `ー` ×1.10。
- Iteration marks、`々`、`・`、`〆` 與 source-derived Han 本來已接近 source weight，保持 ×1.00。沒有 CSS stroke、font synthesis、outline expansion 或 glyph regeneration。
- `audit_japanese_weight.py` 在 16／20／24／32／48／72／96 px 使用 4× supersampling、alpha 128 threshold 與短 scanline ink runs 量測 horizontal／vertical effective stroke weight 與 ink density。
- `verify_japanese_weight.py` 驗證 46 字 points／stroke count／topology hash、optical transform hash、source TTF hash、全部 source glyph drawing prefix、TTF／WOFF2 cmap／metrics／bounds、clipping 與 small-kana weight gate。
- Proof: `proofs/quanfangwei-japanese-weight-before-after-proof.png`；量測報告：`reports/japanese_weight_audit.json`.

### Version 1.018 容 optical alignment

- U+5BB9 `容` 保留官方辰宇落雁來源 glyph drawing，並沿用既有 shared-Han derived-copy 機制；沒有建立大規模 `locl JAN`。
- 最終參數為 `scale_x=1.00`、`scale_y=1.00`、`dx=+19.45`、`dy=+35`。Advance 872 不變；因 outline 平移，LSB／RSB 由來源的 85／126 改為 104／107。
- 不修改其他 Han，也不重新生成或改動 `USER_HANDWRITING_REFINED` 46 平假名 topology。
- Proof：`proofs/quanfangwei-yong-alignment-proof.png`（16／20／24／32／48／72 px）；Stage B verifier：`python tools/font/verify_yong_alignment.py`。

### Version 1.020 奥 optical alignment

- U+5965 `奥` 使用現有 shared-Han derived-copy 架構；官方 source glyph `uni5965` 保留且 drawing identity 不變。
- U+5967 `奧` 是 authoritative primary reference：bounds `(122,-53,668,761)`、ink `546×814`、center `(395,354)`、advance 790、LSB／RSB 122／122；`目写影深身` 與既有 alignment sample 只作 secondary context。原始 `奥` 為 bounds `(91,-153,678,793)`、ink `587×946`、center `(384.5,320)`、advance 798。
- Browser-native E-family QA confirmed that the source aspect ratio cannot match both reference dimensions with a uniform scale. The accepted derived copy uses `scale_x=0.921976`、`scale_y=0.855348`、`dx=+9`、`dy=+34.5` and the approved 4-unit boundary embolden. Advance is 790; final bounds are about `(122.75,-53,668,760.75)`, ink `545.25×813.75`, center `(395.375,353.875)`, and LSB／RSB 122／122.
- 正式 WOFF2 browser proof `oku-browser-proof.html` 是視覺驗收依據；Pillow proof 僅作 rasterizer diagnostics。Measurement report：`reports/oku-optical-alignment.json`；verification：`python tools/font/verify_oku_optical_alignment.py`。
