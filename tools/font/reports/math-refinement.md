# Version 1.034 — 筆畫、帽號與分數中線

以已合併的 1.033（`ca34467431ddc05e15368c244d1128687a074605`）為基準。P0/P1/P2/P3 的 45 個獨立碼位全部保留。P2/P3 仍屬預備需求，不代表其餘講義已逐頁確認。

## 粗細

`∑ ∇ ∏` 的原生來源輪廓在 1.033 放大時連同筆畫變粗；本版分別從邊界內縮 10／10／5 units，保留筆形、孔洞、字寬與中心。這是輪廓減重，沒有再縮放字面。Left side bearing 隨新的 xMin 更新。原字體的 `Σ Δ Π ±` 完全保留，`∓` 也保留與原生 `±` 相同的筆畫。

96 px raster 的有效筆畫寬度（UPM 1024；以既有 `hxprHABCLFαβγδεθφψρ=+<>∫∥←→` 為參照）如下。這是像素距離量測，並非每處曲線的固定線寬。

| 字元 | 1.033 | 1.034 | 原生參照中位數 |
|---|---:|---:|---:|
| ∑ | 7.00 px | 4.75 px | 4.75 px |
| ∇ | 6.75 px | 4.75 px | 4.75 px |
| ∏ | 5.50 px | 4.75 px | 4.75 px |

20／32／64／96 px 的新筆畫皆落在原生中位數的 1.00–1.083 倍；候選內縮 A=8/8/3、B=10/10/5、C=12/12/7 中選 B。[候選圖](../proofs/quanfangwei-math-weight-candidates.png)；[正式前後比較](../proofs/quanfangwei-math-refinement.png)。

## 帽號

沿用原生 U+0302 零字寬輪廓，只新增一個限定這個 mark 的 GPOS lookup。38 個 base 為 `xprLBαβγδεζηθικλμνξοπρστυφχψωϵϕϑϱℋℒℱℜℑ`；實際墨跡間距約 40.7–48.3 units，帽號頂端保持在現有 typographic ascender 內。原本已組成 `â ê î ô û Ĥ Â` 的路徑、其他重音與來源 GPOS lookup 不變。

可輸入 `x̂²p̂ + 2x̂p̂x̂ + p̂x̂²`；U+0302 放在 base 後、上標前。已用 HarfBuzz shaping 和 FreeType 實際呈現帽號，不靠 fallback 或圖片覆蓋。重複算子保持原字串的總 advance。MATH top-accent attachment 同步提供數學排版器所需中心。

## 分數

新增 OpenType MATH 表：AxisHeight=330，與原生 `=` 墨跡中心 329.5 對齊；FractionRuleThickness=36，分子／分母最小墨跡間距各 72 units。字型全域 baseline、ascender、descender 都不變。校準頁新增原生 MathML 分數；PNG 校準器依實際分子／分母墨跡及 MATH 值排版，兩條橫線共用同一數學軸。

使用者截圖來自哪個筆記排版器目前未確認，repo 中沒有該原圖的生成程式。本版已修正字型數學參數與本 repo 校準器，但無法保證外部程式自畫的分數線會採用 MATH 值。沒有新增可伸展算子組件或 U+20D7。

## 驗證與重現

- 10,509 個其餘 glyph 的 bytes、outline、horizontal/vertical metrics 不變；所有 10,512 個 glyph 的 advance 不變。
- cmap、既有 GPOS lookup、GSUB、GDEF、OS/2、hhea、vhea、vmtx、kern 保持；新增單一 scoped GPOS lookup 及 MATH 表。
- 三個符號的輪廓／left bearing 變更已明列。非視覺資料更新包括版本 name ID 3/5、head revision/checksum 和打包 table offset/checksum；glyf/loca/hmtx 對應三個輪廓變更，maxp 與全域 bounds 不變；WOFF2 重新壓縮。
- TTF／WOFF2 幾何、metrics、GPOS、MATH 一致；45/45 coverage audit 和缺字／錯碼負控制通過。
- 完整字型檢查、歷史促音回歸、127 項網站測試通過；canonical rebuild 的兩個檔案逐 byte 相同。
- 建置環境為 Python 3.9 與 `requirements.txt` 固定版本；未使用其他字型的 outline。

機器可讀：[完整回歸與筆畫量測](math-refinement.json)、[分數校準](math-layout-proof.json)、[coverage](../../../analysis/font-coverage.json)。執行命令見 [工具 README](../README.md)。

| 檔案 | SHA-256 |
|---|---|
| TTF | `e902a5e108c8da8e0ea75939148c5f55df01d5399487d760fd94bd8d0647656c` |
| WOFF2 | `15a21205d545b1d4e97162eae0a48f6b9430914ba8305be4ab497f01fd9b84c9` |
