# 荃方位補寫體 1.042 — ə／ɐ 字形修訂

日期：2026-10-09（Asia/Taipei）。`ə` 依維護者要求改由字型原有 `e` 旋轉 180° 後再順時針轉 12°，直接保留原筆觸。原本 U+0250 `ɐ` 的上方字腔偏扁，斜向連接筆近似 `e` 的橫畫。新版以較圓的封閉上字腔、左上短尾、左側主筆和下方開口弧線，凸顯倒置 a 的結構。

## 基底與範圍

直接基底為已合併 1.041 commit `2e246a77524dacdfc338e337959f86b3976a8d0b`，TTF SHA-256 `799787cc846495ad6bc63d9129cc9685f46135db772f19c621fc61ea0d03fab1`。ə 使用原生 e 輪廓，ɐ 採用 repo 自製中心線筆畫，未匯入或描摹其他字型輪廓；OFL、來源與衍生名稱保留。

只改 `uni0259.qfwIPA`／`uni0250.qfwIPA` 輪廓。ə 的原生 e 先旋轉 180°，再順時針轉 12°，之後縮放，配合原有 ink bounds `(35,110,270,405)`、advance 305；不另加粗。ɐ 既有 44／42-unit 筆畫寬度、筆壓變化、3.5-unit optical outset 與 0.07 shear 參數保留；新中心線正規化至原 ink bounds `(35,110,255,410)`（220×300 units）。advance 仍為 290、左 bearing 35，垂直 metrics、組合定位與行距均不變。未新增擴充 IPA。

## QA

- `verify_turned_a.py` 以 SHA 固定的 1.041 為基底，逐字形比對只有 `ə`／`ɐ` 改變，其他 10,529 glyph bytes 保留；精確核對 ə 等於原生 e 的旋轉／縮放輪廓。檢查 `ɐ` 仍有兩個輪廓（包含未填滿的上字腔）、原尺寸與字距。
- cmap、hmtx、vmtx、hhea、vhea、GPOS、GDEF、GSUB、MATH 逐表 byte-identical；HarfBuzz 比對 e／ə／ɐ、德語詞例、組合符號、引號、雙點與中日文的 glyph IDs、advances、offsets 不變。
- 持續驗證最初 1.036 SHA 和 93 筆 audit，19 個基礎 IPA 的 cmap format 4／12 非零 glyph、76 組零 advance 組合定位；既有字型 verifier 與 128 項網站測試。
- [瀏覽器報告](turned-a-browser.json)：六個樣字節點均確實使用 QFW，自訂 TTF／WOFF2 寬度相同，無頁面錯誤。包含 16／24／32 px 和 `ɐ̯`。
- [前後對照 PNG](../proofs/quanfangwei-turned-a.png)、[HTML](../turned-a-proof.html)、[PDF](../proofs/quanfangwei-turned-a.pdf)。另重新輸出完整 IPA 樣張。PDF 共三頁逐頁渲染檢視，QFW 子集嵌入、Unicode 文字可抽取。
- 正式 TTF／WOFF2 與 MODIFICATIONS 必須可完全重建，CI 同樣檢查。版本 metadata、manifest、CSS 與網站引用快取版本統一為 1.042。

最新 SHA 及逐字形結果：[german-ipa-results.json](german-ipa-results.json) 的 `turned_vowels_revision`。

## 重現

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_german_ipa.py --output tools/font/reports/german-ipa-results.json
npm test
python tools/font/render_turned_a.py
node tools/font/render_turned_a.cjs
node tools/font/render_german_ipa_browser.cjs
```

使用 repo 固定 Python dependencies；瀏覽器需 Playwright／Chromium，可設定 `CHROME_BIN`。PDF 的時間 metadata 不要求 byte-identical；正式字型與 MODIFICATIONS 要求可重建。
