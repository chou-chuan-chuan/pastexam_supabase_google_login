# 荃方位補寫體建置工具

這套流程從 repository 內未修改的官方 `ChenYuluoyan-2.0-Thin.ttf` 建立獨立命名的「荃方位補寫體 / QuanFangwei Supplement Script」。它依 SIL Open Font License 1.1 製作，並非原作者官方更新版。

目前 Windows 驗證環境沒有 FontForge，因此實際可重複流程使用 fontTools 的 TrueType pen、composite glyph 與 WOFF2 writer，不依賴 FontForge GUI。輸出是可由 fontTools 與瀏覽器正常開啟的真實 TTF／WOFF2；若未來採用 FontForge，必須保持 manifest、名稱、輪廓建構與驗證條件一致。

若需要另外安裝 FontForge，可從 [FontForge 官方 Windows 下載頁](https://fontforge.org/en-US/downloads/windows/)取得安裝程式，安裝後重新開啟 PowerShell 並執行 `fontforge --version`。目前這份建置腳本的受驗證路徑是下方的標準 Python/fontTools 命令；沒有假設或冒充 FontForge scripting API 已執行。

## 環境與命令

```powershell
python -m pip install -r tools/font/requirements.txt
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/render_proof.py
```

建置腳本會先輸出每個參考字元、Unicode code point、Unicode name 與預期 glyph name，並驗證兩張 reference PNG 可開啟。來源 TTF 的 SHA-256 也會被核對；不符合已審核的官方檔案時建置會失敗。所有暫存輸出先寫入衍生目錄，完成後才替換正式檔案，不會修改原始 TTF。

官方原始 TTF 的 TrueType hint program 在 FreeType/Pillow 會觸發 `too many function definitions`。衍生版建置會清除 hint bytecode 與 `fpgm`／`prep`／`cvt ` tables，保留實際輪廓、cmap、glyph 順序、advance 與垂直 metrics，讓 proof 與網頁字型解析保持穩定。

## 檔案

- `glyph_manifest.json`：字元身分、來源 glyph 與建構方法。
- `references/U+00BF-questiondown.png`：`¿` 身分參考圖。
- `references/U+00C7-Ccedilla.png`：`Ç` 身分參考圖。
- `build_supplement_font.py`：建立 TTF、WOFF2、OFL 與修改紀錄。
- `verify_supplement_font.py`：驗證 cmap、glyph、metadata、授權與來源保存。
- `render_proof.py`：以輸出 TTF 產生不使用 fallback 的 proof PNG。
- `browser-proof.html`：本機瀏覽器 Rendered Fonts 驗收頁。

## 字形建構

- `questiondown`：從原字型 `question` 輪廓，以 advance width 與可視 bounds 中心旋轉 180°。
- `cedilla`：原字型沒有 U+00B8 或 U+00E7，因此由原字型 `comma` 的手寫輪廓向下定位建立。
- `Ccedilla`：以未改形的原始 `C` 加上水平置中的 `cedilla` component 組成。

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
