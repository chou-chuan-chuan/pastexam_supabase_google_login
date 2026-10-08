# Kana junction and handakuten refinements — Version 1.036

Baseline: `9b61867b073f1f90bce11ba0996f68febf7c47da` (Version 1.035).

Remove the マ approach-stroke tail below-left of its crossing and the ス branch-start bump above-left of its junction. Clip only the protruding stroke end; unchanged supporting ink covers the cut. All accepted source center-lines and pressure values remain untouched.

| Base | Unchanged final bounds | Unchanged size | Advance | Local change region | Removed area (units²) | Quantization addition (units²) |
|---|---|---|---|---|---|---|
| マ | `(198, 48, 768, 537)` | 570 × 489 | 960 | `(410, 105, 490, 180)` | 1813.608032 | 0.608143 |
| ス | `(251, -15, 740, 549)` | 489 × 564 | 960 | `(490, 165, 535, 220)` | 469.972748 | 1.472839 |

- Both bases retain one contour, no holes or detached fragments, and their original 960-unit metrics.
- Every changed outline segment stays within the listed junction patch; every edge outside it is identical. Added area from integer quantization is less than two square font units per glyph.
- ズ inherits the corrected ス body through its unchanged composite. Dakuten outline, attachment, component bytes, overall bounds and metrics remain identical.
- All ten handakuten attachments move by `(16,24)`. Both ring outlines remain bit-identical; their GPOS mark anchors move from `(92,759)` to `(76,735)` while all base anchors and dakuten remain unchanged.
- Forced decomposed HarfBuzz shaping agrees with the precomposed component deltas for all ten forms; combining marks retain zero advance and bases retain 960.
- All 10499 other glyphs retain bit-identical outline bytes and metrics, including the five 1.035 small vowels and ャュョッ.
- All source drawings, script scales, pressure, global alignment and spacing remain unchanged. Only the two handakuten GPOS mark anchors change in the layout tables.
- TTF/WOFF2 parity; unchanged sample shaping; byte-identical canonical rebuild required by the default verifier.

[Junction before/after proof](../proofs/quanfangwei-katakana-junctions.png) · [Handakuten before/after proof](../proofs/quanfangwei-handakuten-spacing.png). Both include actual 20, 32, 64 and 192 px rendering.

## Handakuten minimum ink clearance

| Glyph | Before (units) | After (units) |
|---|---|---|
| ぱ | 52.240 | 78.643 |
| ぴ | 31.113 | 59.397 |
| ぷ | 210.440 | 233.266 |
| ぺ | 293.847 | 322.531 |
| ぽ | 31.385 | 55.946 |
| パ | 136.693 | 161.533 |
| ピ | 97.247 | 126.052 |
| プ | 27.348 | 56.180 |
| ペ | 281.783 | 309.731 |
| ポ | 107.019 | 135.447 |

No external font outline, CSS/JS positioning workaround, SQL/migration or database change.
