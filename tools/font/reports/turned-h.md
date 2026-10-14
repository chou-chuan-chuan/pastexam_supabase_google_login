# 荃方位補寫體 1.043 — 新增 ɥ

日期：2026-10-15（Asia/Taipei）。使用者截圖中的 `ɥ` 在 1.042 缺少 cmap 映射。本版新增 U+0265 LATIN SMALL LETTER TURNED H；碼位名稱與字形身分依 [Unicode IPA Extensions chart](https://www.unicode.org/charts/PDF/U0250.pdf) 核對。未宣稱所有擴充 IPA 已補齊。

## 基底與來源

直接基底為 1.042 merge commit `9b896f7a5475e05ab81f8163222968e67224d85c`，TTF SHA-256 `50cfc3581585766c5d74fd41a251131893e2c47746f1c200090a182263b72360`。本次已 fetch 並核對遠端 main 與本地字型；不假設最初 1.036 就是最新基底。

使用既有字型的 `h` 輪廓旋轉 180 度並平移，transform `(-1,0,0,-1,303,546)`。未縮放、加粗或匯入外部字型輪廓，保留辰宇落雁體來源筆觸、OFL、作者及衍生名稱。結果 ink bounds `(19,-70,284,435)`，advance 306、left bearing 19；右側下伸筆與原生 y 的彎尾可區別。原 h 完全保留。

只新增 `uni0265.qfwIPA`，其餘 10,531 glyph 輪廓及水平／垂直 metrics 不變。cmap 在所有 Unicode 子表增加 U+0265 非零 glyph；GDEF 新增 base class，既有 IPA GPOS lookup 增加一個 base anchor `(152,-115)`。既有 38 個 base anchors 和兩個 mark anchors 不變；ɥ 的兩個下方標記均有 zero advance、45-unit ink gap，未改行距或全域 bounds。

## QA

- 以固定 SHA 的 1.042 逐 glyph 比對，確認單一新增、無覆蓋；精確驗證 ɥ 等於原生 h 的旋轉副本。
- 移除新增 GPOS base／GDEF class 後，排版表與 1.042 byte-identical。GSUB、MATH、OS/2 保留；hhea/vhea 僅 metrics count 隨新 glyph 增加。既有中日文、德文、IPA、引號與雙點的 HarfBuzz glyph IDs、advances、offsets 不變。
- 仍核對最初 1.036 SHA 與 93 筆 audit。原 19 項基礎需求獨立保留，本版另加 1 個擴充；cmap format 4／12 非零 glyph、39×2 共 78 組 mark positioning。ɥ̯／ɥ̩ 僅作定位測試，非宣稱詞音轉寫需要這些組合。
- 128 項網站測試、既有字型 verifier、正式 TTF／WOFF2／MODIFICATIONS 完全可重建；CI 執行相同字型與網站驗證。
- [瀏覽器報告](turned-h-browser.json)：6 個本次樣字節點確實使用 QFW，TTF／WOFF2 字寬一致，無頁面錯誤。另有 30 個完整 IPA 樣字節點與瀏覽器 zero-advance 檢查。
- [PNG](../proofs/quanfangwei-turned-h.png)、[HTML](../turned-h-proof.html)、[PDF](../proofs/quanfangwei-turned-h.pdf)：包含截圖文字 `3. [ɥ]`、h／ɥ／u／y、16／24／32 px。PDF 與完整 IPA PDF 共三頁已渲染檢視，ɥ Unicode 可抽取且 QFW 子集嵌入。
- 發行 metadata、manifest、網站 CSS／字型快取引用更新 1.043。無登入、資料庫或正文替換改動。

SHA 與驗證結果：[german-ipa-results.json](german-ipa-results.json) 的 `turned_h_revision`。

## 重現

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_german_ipa.py --output tools/font/reports/german-ipa-results.json
npm test
python tools/font/render_turned_h.py
node tools/font/render_turned_h.cjs
node tools/font/render_german_ipa_browser.cjs
```

使用 repo 固定 Python dependencies；瀏覽器需 Playwright／Chromium，可設定 `CHROME_BIN`。PDF 時間 metadata 不要求 byte-identical，正式字型與 MODIFICATIONS 要求可重建。
