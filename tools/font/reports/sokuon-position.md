# Sokuon lower-left optical positioning — Version 1.032

Base main: `3a093edd962410d129c9955d2b28bddb0866070c` (Version 1.031). Only post-construction integer x/y translation is applied.

| Glyph | Old bounds | New bounds | Unchanged width × height | Old local dx/dy | New local dx/dy | Final xMin/yMin | Advance |
|---|---|---|---|---|---|---|---|
| っ | `(287, 106, 688, 457)` | `(180, -32, 581, 319)` | 401 × 351 | `(0, 0)` | `(-107, -138)` | `(180, -32)` | 960 |
| ッ | `(335, 56, 672, 426)` | `(180, -32, 517, 338)` | 337 × 370 | `(0, 0)` | `(-155, -88)` | `(180, -32)` | 960 |

Bounds are final font units (UPM 1024; Y increases upward). Local offsets exclude the unchanged global -145 and -56 translations. No second shrinking, pressure change, redesign, kerning or ligature is applied.

## Measured Version 1.031 yōon reference

| Glyph | Final ink bounds | Anchor |
|---|---|---|
| ゃ | `(180, -32, 641, 477)` | `(180, -32)` |
| ゅ | `(180, -32, 607, 468)` | `(180, -32)` |
| ょ | `(180, -32, 607, 428)` | `(180, -32)` |
| ャ | `(180, -32, 584, 430)` | `(180, -32)` |
| ュ | `(180, -32, 549, 253)` | `(180, -32)` |
| ョ | `(180, -32, 502, 276)` | `(180, -32)` |

Each sokuon translation is independently derived from its own accepted bounds and its script’s reviewed yōon anchor. The shared final anchor leaves 180 units of left clearance and remains inside the font’s vertical metrics. The different heights of the glyphs are preserved.

## Verification

- Pinned baseline TTF SHA256: `a035c9b19384eeef2ffb85b45face710cbb18bddf2b3825f3caf5032c89f57b7`.
- Pinned baseline WOFF2 SHA256: `5124866790745a283011661df3be14169d787a70d4408dd1de0fe4ff3adbdd1b`.
- All 10465 other glyphs retain identical outline bytes and horizontal/vertical metrics, including つ/ツ, all six yōon and all other small kana.
- Every sokuon contour point moves by exactly its expected dx/dy; contour endpoints, flags, stroke widths, dimensions and advances remain unchanged.
- TTF/WOFF2 glyph parity; unchanged cmap, layout and global metric tables; no clipping.
- Every requested natural phrase and yōon comparison shapes identically before/after, with separate 960-unit kana cells, unchanged separator-space advances, no missing glyphs or pair adjustments.
- Historical gates first validate and undo only these two exact translations in memory, preserving their existing regression assertions.
- Run `python tools/font/verify_sokuon_position.py` for verification plus a byte-identical canonical rebuild.

## Visual QA

- [Visible cells, guides, baseline and ink bounds](../proofs/quanfangwei-sokuon-cell-position.png).
- [Version 1.031 / 1.032 at 20, 32, 64 and 192 px; all natural phrases and yōon comparisons](../proofs/quanfangwei-sokuon-before-after.png).
- Both small forms now share the reviewed lower-left anchor; full-size bases and surrounding glyph placement remain unchanged.

No external font outline, CSS/JS workaround, SQL or migration. Production database untouched.
