# 荃方位補寫體 1.040 — Ü／ü 雙點間距

日期：2026-10-09（Asia/Taipei）。維護者提供 Ü／ü 雙點太靠近字身的兩張截圖。本版只移動這兩字的雙點，不改點形、大小、橫向位置、字身或字距。

## 實際基底與修訂

已核對 1.039 merge commit `83d20f266e231f89c5de3269f27dd8173624158a`，TTF SHA-256 為 `46d5ad8aa4ec713fb3c56aaf2e20417fa4c506e65e5cd10369bb59d8f53c2de2`。沿用原始辰宇落雁體輪廓、OFL、作者及衍生名稱；沒有引入外部字型或修改官方 source TTF。

| 字元 | 雙點 component 位移（前 → 後） | 字身與雙點的 ink 間距（前 → 後） |
|---|---|---|
| Ü U+00DC | (29, 88) → (29, 118) | 12 → 42 units |
| ü U+00FC | (35, -62) → (35, -32) | 15 → 45 units |

UPM=1024。其他 Ä／Ö／ä／ö 的間距原為 41／39／49／40 units，本版保留。雙點與 U/u 的原輪廓、hmtx、水平及垂直 advances 不變；兩個 composite 的 top bearing 減 30，保持同一垂直原點。沒有其他 glyph 以這兩個 composite 為 component。

原始 GPOS 的 U/u 上方 anchor class 由多種重音共享，直接提高它會連帶影響 acute／grave／macron 等標記。因此在原 lookup 的第一個位置加入限定 `U/u + uni0308` 的 MarkBasePos 子表：U `(174,595)`、u `(180,445)`，mark anchor 仍為 `(145,477)`。原子表完整保留，依 OpenType 第一個相符子表生效的規則，只有這兩組雙點取得新位置。lookup index、feature、script/language、GDEF、GSUB 不變。

## QA

- `verify_umlaut_clearance.py` 先確認兩個 composite 與限定 GPOS 子表的精確內容，再還原這些指定改動，比對基底全部 glyph bytes、cmap、hmtx/vmtx、hhea/vhea、GPOS/GDEF/GSUB/MATH。除兩個指定 composite 的位置外，10,529 glyph 保留，全部 IPA（含 1.039 的瘦長音符號）不變。
- HarfBuzz 測試會在記憶體中移除相關預組合 cmap，防止 NFC 自動重組繞過 GPOS。驗證 `U + U+0308`／`u + U+0308` 的 mark origin 與新 component 完全一致，零 advance；另對 24 組 U/u 的其他上／下重音強制分解 shaping，位置與基底完全一致。
- `verify_supplement_font.py` 檢查六個 Umlaut 預組合與強制分解位置、原始輪廓、授權及其他字型功能。`verify_german_ipa.py` 仍驗證 19 個 IPA、兩格式的 cmap format 4/12、76 組附加符號與最初 1.036 基底；先嚴格驗證並還原本版兩個指定例外，再執行歷史保留檢查。
- 網站 128 項測試。版本、TTF／WOFF2、五個 HTML 的 CSS 快取版本與樣張引用統一為 1.040。
- [瀏覽器報告](umlaut-browser.json)：全部六個樣字節點使用自訂 QFW，兩格式 NFC／NFD 與 base 的 advances 相等。包含 16／24／32 px、真實單字與其他重音。
- [對照 PNG](../proofs/quanfangwei-umlaut-clearance.png)、[瀏覽器 HTML](../umlaut-clearance-proof.html)、[PDF](../proofs/quanfangwei-umlaut-clearance.pdf)。PDF 字型子集嵌入，Ü／ü 文字可抽取，逐頁渲染確認沒有裁切。既有 IPA 瀏覽器／兩頁 PDF 也重跑。
- CI 執行網站、原 verifier、IPA／雙點 verifier，並要求 TTF／WOFF2 及 MODIFICATIONS 完全可重建。SHA 與比對結果記錄於 [1.040 歷史結果](https://github.com/chou-chuan-chuan/pastexam_supabase_google_login/blob/915e061f81e2d2a9032aaac0c820824ab623b037/tools/font/reports/german-ipa-results.json) 的 `umlaut_revision`。

## 重現

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_german_ipa.py --output tools/font/reports/german-ipa-results.json
npm test
python tools/font/render_umlaut_clearance.py
node tools/font/render_umlaut_clearance.cjs
```

使用 repo 固定版本的 Python dependencies；瀏覽器樣張需 Playwright + Chromium，可透過 `CHROME_BIN` 選用已安裝 Chrome。PDF metadata 不要求 byte-identical；正式字型與修改紀錄要求可重建。
