# MODIFICATIONS

- 衍生字型名稱：荃方位補寫體
- 英文名稱：QuanFangwei Supplement Script
- 原始字型名稱：辰宇落雁體 2.0 Thin / ChenYuluoyan 2.0 Thin
- 原始字型官方來源：https://github.com/Chenyu-otf/chenyuluoyan_thin
- 原始授權：SIL Open Font License 1.1
- Reserved Font Name：原字型保留名稱「辰宇落雁」與「Chenyuluoyan」未用作衍生 Family Name
- 修改者：`pastexam_supabase_google_login` 專案維護者（衍生版維護者，不是原字型作者）
- 修改日期：2026-08-09
- 版本：Version 1.003
- 補寫字元：U+00BF `questiondown`、U+00C7 `Ccedilla`、U+00E7 `ccedilla`、U+0327 `uni0327`、U+00A8 `dieresis`、U+00DF `germandbls`、U+1E9E `uni1E9E`
- German coverage：Ä Ö Ü／ä ö ü／ß ẞ，並同時支援 U+0308 `uni0308` 的分解表示；原始字型已存在六個 Umlaut 與 U+0308，其 cmap、輪廓、components、metrics、GDEF 與 GPOS 錨點均原封不動保留
- U+00A8 `dieresis`：以 identity component 共享原字型 U+0308 `uni0308` 的兩個手寫點，advance 300、左右各約 60 units；不是外部字型或幾何圓
- U+0308 `uni0308`：沿用原始 zero advance、GDEF mark class 與既有 MarkBasePos。mark anchor <145 477>；base anchors A <272 622>、O <235 564>、U <174 565>、a <172 464>、o <153 420>、u <180 415>
- Ä Ö Ü／ä ö ü：保留原字型既有 composite glyph；各自由原始 A/O/U/a/o/u 加上 `uni0308` 組成，component transforms 分別為 +127/+145、+90/+87、+29/+88、+27/-13、+8/-57、+35/-62
- U+00DF `germandbls`：只使用原始 `f` 與 `s`；裁切 f 的上行筆勢與莖部、縮放並接合 s 的終筆，經輪廓 UNION 與 junction 清理成單一完整 glyph，advance 390
- U+1E9E `uni1E9E`：只使用原始 `P` 與 `S`；保留 P 的大寫莖與上 bowl、接合 S 下筆，並裁出斜向 counter opening，使其可辨識為 capital sharp S 而非 B，advance 475
- ß／ẞ 未使用 Greek beta，亦未使用 Arial、Times、Noto、Google Fonts 或任何其他外部字型輪廓；布林裁切只處理官方辰宇落雁體既有筆畫
- U+00BF 第一版建構：將原始 U+003F `question` 機械式旋轉 180°
- U+00BF 光學修正：旋轉後整體平移 +3 x／-12 y font units，圓點再下移 8 units，使句首高度、左右留白及點與主筆間距更自然；不修改來源 glyph
- U+00C7 建構：保留原始 U+0043 `C`，與新增的 U+00B8 `cedilla` 組成 composite glyph
- U+00E7 建構：保留原始 U+0063 `c`，與同一 U+00B8 `cedilla` 組成 composite glyph；cedilla transform 為 +81 x／+10 y，advance 與 side bearings 保持原始 c
- U+0327 建構：以 identity component 共享 U+00B8 `cedilla` 的同一精修輪廓來源；advance width 為 0，不作 spacing character
- U+0327 定位：保留原始 GPOS/GDEF，在既有 `mark` feature 附加 MarkBasePos lookup；C base anchor 為 <221 91>、c base anchor 為 <176 101>、mark anchor 為 <95 91>，分別重現 U+00C7 的 +126 x／0 y 與 U+00E7 的 +81 x／+10 y cedilla 位移
- HarfBuzz 驗證：在記憶體副本分別移除 U+00C7／U+00E7 cmap 以強制分解 shaping；C/c advances 471/345、`uni0327` advance 0、offsets -345/0 與 -264/+10，最終 mark origins 為 +126/0 與 +81/+10
- Unicode 表示：U+00C7／U+00E7 使用預組合 `Ccedilla`／`ccedilla`；U+0043／U+0063 + U+0327 保留分解 code points，經 GPOS 定位後得到相同 cedilla 造型、大小、光學中心與 26-unit gap
- Cedilla 第一版建構：原字型沒有 U+00B8 與 U+00E7，因此直接將 U+002C `comma` 向下定位
- Cedilla 光學修正：改用原始 U+003B `semicolon` 的下方手寫尾筆，水平 116%、垂直 82%、旋轉 -7°，再置於 C 的光學中心下方並保留 26 units 間距；comma、J、j、g、y 僅作同字型風格比較
- 美學限制：自動檢查只能驗證 bounds、留白、中心、碰撞與裁切；筆勢是否自然仍以多尺寸 proof 與瀏覽器人工目視為準
- Hinting：移除原始 TrueType hint bytecode；原始檔的 function definitions 超過 FreeType/Pillow 限制，輪廓、cmap、glyph 順序與 metrics 均保留
- FontForge：目前建置環境未安裝，未使用 FontForge GUI 或 scripting API
- fontTools：4.55.3
- 建置指令：`python tools/font/build_supplement_font.py`
- 驗證指令：`python tools/font/verify_supplement_font.py`
- Proof 指令：`python tools/font/render_proof.py`

荃方位補寫體是基於辰宇落雁體，依 SIL Open Font License 1.1 製作的缺字補寫版本。本修改版由專案維護者獨立製作，不是原作者官方版本，也不代表原作者背書。
