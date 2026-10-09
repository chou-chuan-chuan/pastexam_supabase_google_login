# 荃方位補寫體 1.041 — 德文成對引號筆觸

日期：2026-10-09（Asia/Taipei）。維護者指定保留左側低引號 `„`，縮小、減輕右側上引號 `“`，讓兩者筆形一致；維持一低一高的位置。沒有替換文字內容或將不同 Unicode 引號映射成同一 glyph。

## 來源與修訂

直接基底為已合併 1.040 commit `915e061f81e2d2a9032aaac0c820824ab623b037`，TTF SHA-256 `e9215fa2d8a347fa6a0dae36b0b9ac92156ecda324fb4e64ca7f9f26013628fb`。保留官方辰宇落雁體、OFL、作者與衍生名稱；沒有外部字型輪廓。

- U+201E `quotedblbase`（„）完全不變，ink 為 `(53,-47,159,82)`，106×129 units。
- U+201C `quotedblleft`（“）直接由上述低引號旋轉 180 度，再置於原上引號的水平 ink 中心 x=97、頂部 y=671。transform 為 `(-1,0,0,-1,203,624)`，沒有加粗、縮放或重畫筆觸。
- 上引號 ink 由 `(19,488,175,671)`／156×183 改為 `(44,542,150,671)`／106×129。新的筆畫幾何與低引號完全相同，只改方向和位置。
- advance 維持 196，左 side bearing 改為 44 以對應實際 ink；vmtx、垂直原點、行距、cmap 與所有 layout tables 保留。沒有其他 composite 引用此 glyph。
- U+201C 也是英文的開引號，所以使用這個碼位的地方都會顯示新筆形。U+201D、直引號、法文 guillemets 及單引號不改。本次沒有補 U+201A 等其他缺字。

## 驗證

- `verify_german_quotes.py` 精確比對上引號的繪圖指令，確保它就是未修改低引號的旋轉副本；檢查兩輪廓、位置、106×129 尺寸與 advance。
- 對 1.040 完整逐 glyph 比對：僅 `quotedblleft` 改變，其餘 10,530 glyph bytes 及 hmtx 保留，所有 advance 相同；cmap、vmtx、hhea/vhea、GPOS/GDEF/GSUB/MATH byte-identical。
- HarfBuzz 比對指定句子、德文／英文／法文引號、Ü／ü 預組合與分解、IPA 與中日文情境，glyph IDs／advances／offsets 全部不變。
- 最初 1.036 基底 QA 維持；歷史 Ü／ü 位移先精確驗證後還原，上引號則先驗證精確新形體再作唯一輪廓例外。其餘基底 glyph 全部照原規則檢查。
- 128 項網站測試、既有字型 verifier、19 個 IPA 的 cmap 4/12 與 76 組組合定位檢查；CI 另要求 release rebuild byte-identical。
- [瀏覽器檢查](german-quotes-browser.json)：六個樣字節點皆使用自訂 QFW，TTF／WOFF2 的字寬一致；16／24／32 px 與指定句子均有樣張。
- [對照 PNG](../proofs/quanfangwei-german-quotes.png)、[HTML](../german-quotes-proof.html)、[PDF](../proofs/quanfangwei-german-quotes.pdf)。引號 PDF 與既有 IPA PDF 均重新渲染並檢視；文字碼位可抽取，QFW 子集嵌入。
- name table、head revision、manifest、verifier、五個 HTML 的 CSS 快取及字型 URL 同步 1.041。沒有登入、資料庫或文字自動替換改動。

最新 SHA 與比對證據位於 [german-ipa-results.json](german-ipa-results.json) 的 `quote_revision`。

## 重現

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_german_ipa.py --output tools/font/reports/german-ipa-results.json
npm test
python tools/font/render_german_quotes.py
node tools/font/render_german_quotes.cjs
```

沿用 repo 固定版本 Python dependencies；瀏覽器 proof 需 Playwright／Chromium，可使用 `CHROME_BIN`。PDF 時間 metadata 不作 byte-identical 要求，正式 TTF／WOFF2 與 MODIFICATIONS 必須可重建。
