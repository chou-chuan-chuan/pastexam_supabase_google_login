# Katakana `ヲ` upper-right junction — Version 1.045

## Result

The detached upper horizontal in U+30F2 `ヲ` is now joined to the descending right-side stroke. The stroke begins inside the original right/top bounds, descends through the existing lower horizontal, and continues along the accepted curve. This removes the `ラ`-like reading while keeping the handwritten pressure and proportions.

## Scope and metrics

| Check | Version 1.044 | Version 1.045 |
| --- | ---: | ---: |
| Glyph | `uni30F2` | `uni30F2` |
| Advance | 960 | 960 |
| LSB | 223 | 223 |
| Ink bounds | `(223, -20, 749, 544)` | `(223, -21, 749, 544)` |
| Connected raster components at 192 px | 2 | 1 |

The one-unit bottom difference is a deterministic consequence of re-interpolating the same tapered main stroke as one continuous path. Its horizontal bounds, top, cell metrics and baseline placement are unchanged.

U+30FA `ヺ` remains the same two-component glyph (`uni30F2` plus `uni3099.katakana`) with the same component offsets. It inherits the repaired base without a new outline or mark-position change.

## Regression evidence

- Baseline commit: `6cf7b42e031d7e85836156ff8eaefd21061b0435` (Version 1.044).
- Baseline SHA-256: TTF `5e169fca032f5232204572c18fe0378c3c179fb04a516e8d189de94e7dbe899d`; WOFF2 `06d842237db255af66d0f1f6dacc56c429fbc282518c5e41e18803732c3beb79`.
- Version 1.045 SHA-256: TTF `be9bd8ca13d5ca580b6310a1523c4f966a0c0824c9bc59cf146508c022bbe15c`; WOFF2 `9edbef4df2ca1138ed0c7a8728de8fbd8a6b35bddfb18d8644b3535a7b5c85ed`.
- `uni30F2` is the only changed simple outline. `uni30FA` changes only its stored inherited bounds; its two components, transforms and mark offset are byte-for-byte equivalent.
- Every horizontal/vertical metric, Unicode mapping, glyph order and GDEF/GSUB/GPOS/MATH/OS/2/kern table is preserved.
- Raster connectivity passes at 16, 24, 32, 64 and 192 px.

Run:

```sh
python tools/font/verify_katakana_wo_junction.py
python tools/font/render_katakana_wo_junction.py
```

Visual proof: [`quanfangwei-katakana-wo-junction.png`](../proofs/quanfangwei-katakana-wo-junction.png).
