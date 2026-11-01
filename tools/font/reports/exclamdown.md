# 荃方位補寫體 1.044 — 新增 ¡

日期：2026-11-02（Asia/Taipei）。新增 U+00A1 INVERTED EXCLAMATION MARK，glyph name `exclamdown`，使西班牙文 `¡Hola!` 不再依賴瀏覽器 fallback。

## 建構

直接基底為 1.043 merge commit `5e495010e839b15f79add465b652903b935ba21b`，TTF SHA-256 `f823a1985a8c73f07773e860d4894483c15dce65872cf8d7d4c35f94dabd2141`。

新字形只使用原生 U+0021 `exclam`：繞 advance 中心與 ink 垂直中心旋轉 180°，transform `(-1,0,0,-1,215,658)`。沒有縮放、加粗、控制點修整或外部字型輪廓。原 `!` 完全不變。

- `¡` bounds：`(69,128,149,530)`
- advance／LSB／RSB：`215 / 69 / 66`
- ink width／height：`80 / 402`，與原 `!` 相同
- 點與主筆間距：`120 units`，與原 `!` 相同

## QA

- TTF 與 WOFF2 的 Unicode cmap format 4／12 均原生映射 U+00A1 → `exclamdown`，glyph ID 非 0。
- `verify_exclamdown.py` 以固定 1.043 SHA 逐字比較；10,532 個既有 glyph 的輪廓、水平／垂直 metrics、cmap 映射及 GPOS／GDEF／GSUB／MATH／OS/2／kern 排版表全部保留。
- 新字形固定附加於 glyph order 尾端，因此既有 glyph ID 不變；全域 ascent、descent 與行距不變。
- `verify_supplement_font.py` 另驗證 exact 180° transform、兩個獨立 contours、左右留白、點距與裁切。
- [PNG 樣張](../proofs/quanfangwei-exclamdown.png)與[HTML 樣張](../exclamdown-proof.html)涵蓋 `! ¡ ? ¿`、西班牙文句子及 16／24／32 px。

## 重現

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_exclamdown.py
python tools/font/render_exclamdown.py
npm test
```
