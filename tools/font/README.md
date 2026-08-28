# 荃方位補寫體建置工具

這套流程從 repository 內未修改的官方 `ChenYuluoyan-2.0-Thin.ttf` 建立獨立命名的「荃方位補寫體 / QuanFangwei Supplement Script」。它依 SIL Open Font License 1.1 製作，並非原作者官方更新版。

目前 Windows 驗證環境沒有 FontForge，因此實際可重複流程使用 fontTools 的 TrueType pen、composite glyph、OpenType layout builder 與 WOFF2 writer，不依賴 FontForge GUI。輸出是可由 fontTools 與瀏覽器正常開啟的真實 TTF／WOFF2；若未來採用 FontForge，必須保持 manifest、名稱、輪廓建構與驗證條件一致。

若需要另外安裝 FontForge，可從 [FontForge 官方 Windows 下載頁](https://fontforge.org/en-US/downloads/windows/)取得安裝程式，安裝後重新開啟 PowerShell 並執行 `fontforge --version`。目前這份建置腳本的受驗證路徑是下方的標準 Python/fontTools 命令；沒有假設或冒充 FontForge scripting API 已執行。

## 環境與命令

```powershell
python -m pip install -r tools/font/requirements.txt
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/render_proof.py
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
- `build_supplement_font.py`：建立 TTF、WOFF2、OFL 與修改紀錄。
- `verify_supplement_font.py`：驗證 cmap、glyph、metadata、授權與來源保存。
- `render_proof.py`：以輸出 TTF 產生 glyph analysis、16／24／32／48／72 px 輔助線 proof 與自然文字 proof。
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
- U+5965 `奥` 保留官方 `uni5965` source drawing，並以 U+5967 `奧` 為主要 reference，映射到 uniform 0.895、dx +10.5、dy +34 的 derived optical copy，再套用 6-unit boundary embolden 恢復筆重；advance 790，derived LSB／RSB 為 128／129。以 `analyze_oku_optical_alignment.py`、`verify_oku_optical_alignment.py`、`render_oku_optical_alignment_proof.py`、`render_oku_diagnostic_proof.py` 與 `oku-browser-proof.html` 驗收。

Known limitations：Phase 1 不保證所有 Jōyō Kanji 日本字形變體、vertical writing、ruby typography、完整 Ainu extensions、historical kana、half-width katakana 或所有標點變體。Phase 2 會以實際 TXT／LRC／JSON 歌詞缺字頻率與 regional-variant review 為基礎。

## 字形建構

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
- Version 1.015 的 `恋／哀／奧／優／寄` 使用各自記錄的等比例 source-derived transform；當時 U+5965 `奥` 尚未調整，Version 1.019 才加入獨立 optical derived copy。
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

### Version 1.019 奥 optical alignment

- U+5965 `奥` 使用現有 shared-Han derived-copy 架構；官方 source glyph `uni5965` 保留且 drawing identity 不變。
- U+5967 `奧` 是 authoritative primary reference：bounds `(122,-53,668,761)`、ink `546×814`、center `(395,354)`、advance 790、LSB／RSB 122／122；`目写影深身` 與既有 alignment sample 只作 secondary context。原始 `奥` 為 bounds `(91,-153,678,793)`、ink `587×946`、center `(384.5,320)`、advance 798。
- Uniform scale 0.895 取 `奥`→`奧` width ratio 與 height ratio 的幾何平均（等效 ink area），避免非等比扭曲；`dx +10.5`／`dy +34` 將中心對齊 `(395,354)`。6-unit boundary embolden 讓 16–48 px effective stroke 與 `奧` 相同，72 px 僅差 0.25 px，並避免 8-unit 版本偏粗。Advance 改為 790；final bounds 約 `(128.8,-72,661,780.7)`，LSB／RSB 128／129。
- Proof：`proofs/quanfangwei-oku-optical-alignment-proof.png` 與 `proofs/quanfangwei-oku-optical-diagnostic-proof.png`；measurement report：`reports/oku-optical-alignment.json`；verification：`python tools/font/verify_oku_optical_alignment.py`。
