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
