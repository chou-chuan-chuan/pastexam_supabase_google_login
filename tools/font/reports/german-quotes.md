# 荃方位補寫體 1.041 — 成對引號筆觸一致

日期：2026-10-09（Asia/Taipei）。保留低引號 `„`，讓德文 `„…“` 的上引號匹配其大小與筆觸；同時讓英文 `“…”` 的兩個上引號成對一致。沒有文字替換或合併 Unicode 碼位。

## 來源與修訂

直接基底為已合併 1.040 commit `915e061f81e2d2a9032aaac0c820824ab623b037`，TTF SHA-256 `e9215fa2d8a347fa6a0dae36b0b9ac92156ecda324fb4e64ca7f9f26013628fb`。保留官方來源、OFL、作者與衍生名稱，無外部字型輪廓。

| 字元 | 做法 | 最終 ink bounds | advance |
|---|---|---|---|
| „ U+201E | 原字完全保留 | (53,-47,159,82) | 211 |
| “ U+201C | 低引號旋轉 180 度，transform (-1,0,0,-1,203,624) | (44,542,150,671) | 196 |
| ” U+201D | 低引號平移，transform (1,0,0,1,-4,589) | (49,542,155,671) | 209 |

三字 ink 都為 106×129 units、同一組兩筆原輪廓。兩個上引號的垂直位置一致；分別保留原水平 ink 中心與 advance。低引號保持原低位。上引號由原 156×183／172×178 縮為與低引號相同的大小，不另加粗或重畫。

U+201D 的 ink 頂部比原來高 5 units，因此 top bearing 減 5，保持同一垂直原點。其他 vmtx、全部水平與垂直 advances、行距與 layout 不變。兩個 glyph 都沒有被其他 composite 引用。直引號、單引號、guillemets 不變；未新增其他缺字。

## QA

- `verify_german_quotes.py` 比對精確繪圖指令，確認兩個上引號分別為未改低引號的旋轉與平移副本；檢查兩輪廓、相同尺寸、上下位置、advances 與垂直原點。
- 對 1.040 核對 SHA 並逐 glyph 比對，只有 `quotedblleft`／`quotedblright` 改變，其他 10,529 glyph bytes 與 hmtx 保留。cmap、hhea/vhea、GPOS/GDEF/GSUB/MATH byte-identical；vmtx 只有上述 U+201D top bearing 例外。
- HarfBuzz 比對指定句子、德文／英文／法文引號、Ü／ü、IPA、中日文情境，glyph IDs、advances 與 offsets 不變。最初 1.036 QA 精確驗證並限定雙點與兩個上引號的例外，其他 glyph 維持完整比對。
- 128 項網站測試、既有字型 verifier、19 個 IPA cmap 4/12 與 76 組組合定位。CI 要求正式 TTF／WOFF2 及 MODIFICATIONS 完全可重建。
- [瀏覽器報告](german-quotes-browser.json)：六個樣字節點均使用自訂 QFW，TTF／WOFF2 字寬相同。包含指定句子、16／24／32 px、兩種引號配對。
- [對照 PNG](../proofs/quanfangwei-german-quotes.png)、[HTML](../german-quotes-proof.html)、[PDF](../proofs/quanfangwei-german-quotes.pdf)。引號及 IPA PDF 重新渲染檢視，文字可抽取、QFW 子集嵌入。
- 版本、metadata、manifest、網站 CSS／字型快取引用統一 1.041。Ü／ü 間距與 IPA 瘦長音符號保留；無登入、資料庫或文字正規化改動。

SHA 與比對證據：[1.041 的 german-ipa-results.json](https://github.com/chou-chuan-chuan/pastexam_supabase_google_login/blob/2e246a77524dacdfc338e337959f86b3976a8d0b/tools/font/reports/german-ipa-results.json) 的 `quote_revision`。

## 重現

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_german_ipa.py --output tools/font/reports/german-ipa-results.json
npm test
python tools/font/render_german_quotes.py
node tools/font/render_german_quotes.cjs
```

沿用 repo 固定 Python dependencies；瀏覽器需 Playwright／Chromium，可設定 `CHROME_BIN`。PDF 時間 metadata 不要求 byte-identical，正式字型與 MODIFICATIONS 要求可重建。
