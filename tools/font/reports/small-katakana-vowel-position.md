# Small Katakana vowel lower-left positioning — Version 1.035

Base main: `c92e280b97b32c71ea17c0d974254761adc9a8ab`. Previous version: 1.034. New version: 1.035.

| Glyph | Old bounds | New bounds | Unchanged width | Unchanged height | Old local dx/dy | New local dx/dy | Final xMin | Final yMin | Advance |
|---|---|---|---|---|---|---|---|---|---|
| ァ | `(278, 49, 700, 463)` | `(180, -32, 602, 382)` | 422 | 414 | `(0, 0)` | `(-98, -81)` | 180 | -32 | 960 |
| ィ | `(338, 47, 659, 499)` | `(180, -32, 501, 420)` | 321 | 452 | `(0, 0)` | `(-158, -79)` | 180 | -32 | 960 |
| ゥ | `(316, 23, 683, 523)` | `(180, -32, 547, 468)` | 367 | 500 | `(0, 0)` | `(-136, -55)` | 180 | -32 | 960 |
| ェ | `(288, 75, 708, 438)` | `(180, -32, 600, 331)` | 420 | 363 | `(0, 0)` | `(-108, -107)` | 180 | -32 | 960 |
| ォ | `(296, 23, 700, 515)` | `(180, -32, 584, 460)` | 404 | 492 | `(0, 0)` | `(-116, -55)` | 180 | -32 | 960 |

Coordinates are final font units (UPM 1024, Y upward). Local offsets exclude the unchanged global -145 and -56 layers. Each offset is calculated separately after existing scale and pressure construction. No rescaling, outline redesign or stroke-weight change.

## Unchanged positioning references

| Glyph | Final ink bounds |
|---|---|
| ャ | `(180, -32, 584, 430)` |
| ュ | `(180, -32, 549, 253)` |
| ョ | `(180, -32, 502, 276)` |
| ッ | `(180, -32, 517, 338)` |

Accepted final lower-left target: **(180, -32)**. All five ink centers lie left of x=480 and below y=312 in identical 960 × 1024 cells (y=-200..824). Left clearance is 180 units; bottom cell clearance is 168 units. All glyphs are inside the unchanged font vertical metrics.

## Regression evidence

- Pinned Version 1.034 TTF SHA-256: `e902a5e108c8da8e0ea75939148c5f55df01d5399487d760fd94bd8d0647656c`.
- Pinned Version 1.034 WOFF2 SHA-256: `15a21205d545b1d4e97162eae0a48f6b9430914ba8305be4ab497f01fd9b84c9`.
- Only five glyphs change; all 10507 other glyphs have bit-identical outline bytes and identical horizontal/vertical metrics.
- Every target point moves by exactly its expected delta. Contour count, endpoints, flags, instructions, width, height, pressure and 960-unit advance are preserved.
- Large ア/イ/ウ/エ/オ, ャュョッ, all Hiragana (including small vowels and ゃゅょっ), ヮヵヶ, all marks, Han, Latin, French and quantum/math glyphs remain unchanged.
- Source layers, global alignment/metrics and layout tables including MATH/GPOS/GSUB are unchanged. TTF/WOFF2 parity and no clipping verified.
- Historical verifiers validate this exact delta before restoring the 1.034 oracle in memory; their previous assertions remain active.
- Default verifier execution repeats the canonical build and requires byte-identical TTF/WOFF2 output.

## Special-sound QA

All examples shape identically before/after in TTF and WOFF2: no missing glyphs, ligatures, kerning tricks, negative spacing or changed text advances. Each kana keeps its separate 960-unit cell.

- `ヴァ`: PASS.
- `ヴィ`: PASS.
- `ヴェ`: PASS.
- `ヴォ`: PASS.
- `ファ`: PASS.
- `フィ`: PASS.
- `フェ`: PASS.
- `フォ`: PASS.
- `ウィ`: PASS.
- `ウェ`: PASS.
- `ウォ`: PASS.
- `ティ`: PASS.
- `ディ`: PASS.
- `トゥ`: PASS.
- `ドゥ`: PASS.
- `シェ`: PASS.
- `ジェ`: PASS.
- `チェ`: PASS.
- `ツァ`: PASS.
- `ツィ`: PASS.
- `ツェ`: PASS.
- `ツォ`: PASS.
- `クァ`: PASS.
- `クィ`: PASS.
- `クェ`: PASS.
- `クォ`: PASS.
- `グァ`: PASS.
- `スィ`: PASS.
- `ズィ`: PASS.
- `ヴォイ`: PASS.
- `ヴァイ`: PASS.
- `ファッ`: PASS.
- `フィル`: PASS.

Comparisons: `ャ　ュ　ョ　ッ`; `ァ　ィ　ゥ　ェ　ォ`; `キャ　キッ`; `ファ　フィ`; `ヴァ　ヴィ`; `ティ　トゥ`.

## Proofs

- [Visible cells, centers, baseline and ink bounds](../proofs/quanfangwei-small-katakana-vowels-cell.png).
- [Version 1.034 BEFORE / Version 1.035 AFTER at 20, 32, 64 and 192 px, all requested special sounds and family comparisons](../proofs/quanfangwei-small-katakana-vowels-before-after.png).

No external font outline used. No CSS/JS workaround (only the existing font URL cache token is bumped). No SQL/migration or production database changes.
