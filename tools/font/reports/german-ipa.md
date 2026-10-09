# 荃方位補寫體 1.037 — 基礎德文 IPA

檢查日期：2026-10-09（Asia/Taipei）。本次範圍只有指定的 19 個基礎缺碼位；不代表所有德語方言、細式轉寫、外來語、歌唱或完整 IPA 均已覆蓋。

## 來源、基底與授權

實際維護 repo 為 `chou-chuan-chuan/pastexam_supabase_google_login`，基底 main commit `def988885120a7921c940073ee1bd2454ecdeb92`。repo 的 v1.036 TTF 經重新讀取後，其 SHA-256 確為 `77f3b2578241b14901e588b5a5b8b18f2550e1d194fad9ea9a0af136da32b103`，與使用者 2026-10-09 下載檢查基準一致；此結論來自本次驗證，不是預先假定最新版相同。

使用者上傳的 93 筆 JSON 原樣保存於 [german-ipa-baseline.json](german-ipa-baseline.json)。Verifier 核對每筆舊 present 值，並從資料中的「基礎」分類獨立取得 19 個缺字，與建置範圍交叉核對。19 個中曾用於筆記的 12 個為 `ɐ ɔ ə ɛ ʁ ʃ ʊ ʏ ˈ ˌ ː U+032F`。歷史 fallback 補字不等於主字型覆蓋。

原始辰宇落雁體 `ChenYuluoyan-2.0-Thin.ttf` SHA-256 仍為 `1289e42a6d1ec995d0cb23aee89efc69fc95749fbd54a610057a3e992dc453db`，未改動。沿用 repo 的 `build_supplement_font.py` 與原創手寫 stroke engine，保留 OFL 1.1、copyright、原作者 credit、來源及獨立衍生名稱；未導入其他字型輪廓。字型內的 license/URL/copyright name records 亦與基底一致。重建未修改前的 v1.036 得到與 repo 完全相同的 TTF、WOFF2。

## 字形與排版

| 類別 | 新增碼位 |
|---|---|
| 母音 | ɛ U+025B、ɪ U+026A、ɔ U+0254、ʊ U+028A、ʏ U+028F、ø U+00F8、ə U+0259、ɐ U+0250 |
| 子音 | ɡ U+0261、ʃ U+0283、ʒ U+0292、ŋ U+014B、ʁ U+0281、ʔ U+0294 |
| 標記 | ˈ U+02C8、ˌ U+02CC、ː U+02D0、U+032F、U+0329 |

- ɛ、ɪ、ʏ 從既有 ε、I、Y 輪廓按 Latin x-height 衍生。ø 沿用原 o 並加入手寫斜線，以輪廓聯集避免交叉處白洞。ɡ 為原單層 g 的獨立 glyph 副本；普通 g 保持不變。此字型的兩者外觀相同是既有單層手寫風格所致，Unicode / glyph ID 並未混用。
- 其餘字形使用原創中心線筆畫與既有 stroke engine，對齊約 y=110..435 的小寫字面。ə 保留清楚的橫畫；ɐ 採 turned double-storey a 結構，避免把單層 a 直接旋轉後與 turned alpha 混淆；ʁ 採上下反轉 small-cap R 的結構。ʃ、ŋ 保留必要下伸部。
- ː 使用上下相對的三角形，與原本冒號的點狀輪廓不同。主／次重音分別位於上方與下方；兩者皆有自己的 advance。
- U+0329、U+032F 的 hmtx advance 為零，GDEF class 為 mark。新增一個 GPOS MarkBasePos lookup，附加到既有可啟用的 mark feature；不替換舊 GPOS。
- 38 個基本 IPA/Latin base 各有 ink 水平中心與底部 anchor。兩個 mark 各以自身 ink 頂部作 anchor，令 mark 與 base 的垂直 bounding-box 間距固定 45 units（UPM 1024），並保持在原有字型行框內。`n̩ l̩ m̩ i̯ ɐ̯ aɪ̯` 已確認；雙母音的 mark 附著在第二個字母。
- 本次不提供完整 IPA 的任意堆疊 mark-to-mark、連結弧或未列出的 base 定位；ʀ、ɾ、ʰ、U+0361 等擴充仍未完成。

形體身分參照 [IPA 官方圖表](https://www.internationalphoneticassociation.org/content/full-ipa-chart)，定位機制參照 [OpenType GPOS 規格](https://learn.microsoft.com/en-us/typography/opentype/spec/gpos)。這些是結構／規格參考，沒有複製其字型輪廓。

## 驗證與證據

- [german-ipa-results.json](german-ipa-results.json)：兩格式輸出 SHA、cmap platform/encoding/format、覆蓋、HarfBuzz 與基底保留結果。
- TTF、WOFF2 的全部四個 Unicode cmap 子表（兩個 format 4、兩個 format 12）均映射 19 個新增碼位到相同的非零 glyph；沒有空輪廓或新增字形超出行框。
- 兩格式分別驗證 76 個 base/mark 組合：零 x/y advance、base advance 不變、ink 中心偏差不超過 3 units、固定 45-unit gap、下緣不裁切。另檢查停用 mark feature 後定位確實不同，確認不是僅靠 renderer 猜測位置。
- 全部 10,512 個既有 glyph 的順序、完整 glyf 資料、hmtx/vmtx 不變；全部既有 Unicode mapping 保留。移除唯一新增 lookup 與新增 glyph classes 後，GPOS/GDEF 與原版 byte-identical；GSUB、MATH 及既有行距、授權 metadata 保留。hhea/vhea 只有因新 glyph 導致的 metrics 記錄數改變。
- [瀏覽器檢查](german-ipa-browser.json)：Chrome 154，29 個 sample nodes 均由自訂 QuanFangwei 字型繪製，無 fallback。Canvas 確認 TTF／WOFF2 的六組指定組合 advance 相同。DOM labels 使用系統字型，並非樣字的一部分。
- [瀏覽器樣張](../proofs/quanfangwei-german-ipa-browser.png)、[兩頁 PDF](../proofs/quanfangwei-german-ipa.pdf)、[可重新開啟的 HTML](../german-ipa-proof.html)：檢視大字形、16/24/32 px、TTF／WOFF2 貼附與既有中／日／德／法／數學混排。PDF 經 Poppler 逐頁渲染檢視無裁切；19 個 Unicode 可抽取，QFW 字型子集已嵌入。
- 網站測試：128 項通過；涵蓋既有網站功能與新增 IPA manifest／版本化 proof 引用。
- 既有 `verify_supplement_font.py` 通過；新增 `verify_german_ipa.py` 通過。兩格式重新建置 SHA 完全一致。新增 GitHub Actions 將網站測試、這兩個 verifier 與 byte-identical release rebuild 設為 PR／main 的 CI 檢查。

## 重現

使用 repo 所列的固定版本 dependencies，並取得完整 Git 歷史供既有 regression verifier 讀取舊版本。

```sh
python -m pip install -r tools/font/requirements.txt
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_german_ipa.py --output tools/font/reports/german-ipa-results.json
npm test
```

瀏覽器 proof 另需 Playwright + Chromium（或 `CHROME_BIN` 指向已安裝的 Chrome），執行 `node tools/font/render_german_ipa_browser.cjs`。此工具只使用獨立 headless profile，驗證 sample 使用的實際字型，並輸出 PNG、PDF 與 JSON。PDF 的時間 metadata 不作 byte-reproducibility 要求；TTF／WOFF2 必須完全可重建。

版本 1.037 同步更新 name table、head.fontRevision、manifest、建置時間／unique ID、README、MODIFICATIONS、verifier 與 CSS 兩個字型 URL 的 `?v=1.037`，使既有瀏覽器快取更新。五個正式 HTML 入口也對 style.css 加上相同版本參數，避免快取的舊 CSS 繼續引用舊字型 URL。網站 Family 名稱與檔名不變；未涉及 SQL、資料庫或登入流程。
