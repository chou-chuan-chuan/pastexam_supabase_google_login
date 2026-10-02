# Quantum physics symbols — Version 1.033

P0 + P1 + P2 + P3 now have **45/45 independent Unicode glyphs**, in both TTF and WOFF2. The pinned Version 1.032 baseline is commit `f0ed23419aa47965b9f5daa72d568381d79b42b3` with TTF SHA-256 `d46795a76391677f12251b8031e32189cf5b914784566ebe91a1d8ebd360d091`.

All **10,467 existing glyphs** retain exactly the same compiled outline bytes, coordinates, components, horizontal/vertical metrics, glyph IDs and cmap identities. The original font and kana sources are untouched. GSUB, GPOS, GDEF, kern (where present), OS/2, UPM and global vertical metrics are unchanged. Existing mixed Latin, CJK, kana and Greek shaping is identical.

## Outputs

- TTF: `assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf`
- WOFF2: `assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2`
- Name version: `Version 1.033`; TrueType fixed-point revision: approximately `1.033`.
- TTF SHA-256: `6677ad97fb50cf5c23747882eaee9ae147536311eaa9f1374b8deb21132090f2`
- WOFF2 SHA-256: `55b932690ac8833d2933a954ea8a434664f71e5880926ee157174586283b247b`

## Design and provenance

`tools/font/quantum_symbols.py` contains the exact reproducible recipes. Native h, Sigma, Delta, Pi, plusminus, prime, integral, bar and middle-dot outlines inform the derived family. All other contours are original project-local pressure strokes rendered by the existing stroke engine; no external font contours or bitmap tracing are used. Each addition has a dedicated `.qfwMath` glyph name and correct Unicode identity. The mathematical axis is near y=330, following the original equal, comparison and arrow family.

ℏ combines a slightly slanted native h with a distinct upper cross stroke; ∂ uses a loop and rising curved stroke distinct from d/δ. Mathematical brackets are narrower than CJK punctuation. Double/triple integrals compose the native integral with measured spacing. The alternate Greek forms have their own drawings. Script H/L/F use looped entry and exit strokes; black-letter R/I use broken stems. ℝ uses a clearly separated double stem. ℒ omits a crossbar to avoid confusion with the pound sign. These handwritten script/black-letter capitals remain the most useful targets for maintainer aesthetic review.

P0/P1/P2/P3 priority and provenance are retained in `analysis/font-gap-candidates.csv`. P2/P3 coverage is implemented, but their occurrence in unread lecture pages is still unverified. This is not a complete audit of the lecture folder. The supplied plan was recovered from the referenced conversation; that conversation's analysis files were not present in this repo, so this revision creates them. U+20D7 combining vector arrow, general MATH-table typesetting, stretch operators and arbitrary mark positioning remain outside the 45-codepoint scope.

## Calibration

- [45 labeled glyphs](../proofs/quanfangwei-quantum-glyphs.png)
- Context at [16 px](../proofs/quanfangwei-quantum-context-16.png), [24 px](../proofs/quanfangwei-quantum-context-24.png), [40 px](../proofs/quanfangwei-quantum-context-40.png), [64 px](../proofs/quanfangwei-quantum-context-64.png)
- [Interactive browser page](../quantum-calibration.html), served from the repo root.

PNG proofs load only the released TTF through Pillow/FreeType and reject every uncovered sample character, so no font fallback can hide missing glyphs. Visual review checked baseline, ink clearance, related-symbol distinction and formula spacing. Browser DOM confirmed WOFF2 loaded and the 45/45 audit; changing the size slider reached 16 px. Browser error/warning logs were empty. Browser screenshot capture was unavailable in this session; visual inspection uses the native TTF PNGs above, with WOFF2 glyph parity independently verified.

## Verification

```sh
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_quantum_symbols.py --write-report
python analysis/audit_font_coverage.py
python analysis/test_font_coverage.py
python tools/font/render_quantum_proof.py
node --test tests/*.test.mjs
```

`verify_quantum_symbols.py` pins the baseline hash, compares every Unicode cmap subtable, old glyph bytes/metrics, all layout tables, vertical metrics, name records, native HarfBuzz shaping and TTF/WOFF2 parity. New outlines have positive bearings and remain within existing metric boxes. It requires an exactly 45-glyph extension and a byte-identical canonical rebuild. The coverage audit rejects missing, empty or aliased glyphs and stale reports; negative controls remove ℏ and alias ∑ to Σ to prove failures are detected.

Historical checks validate the entire 1.033 extension before removing only those additions and restoring 1.032 metadata **in memory**. Their previous exact shape/position assertions remain intact. No production font or proof uses this restoration. The general verifier now expects the 45 extra glyphs and Version 1.033.

Validation completed: 127 Node tests; three coverage positive/negative controls; the general font verifier; the full quantum regression and deterministic rebuild; existing sokuon, French guillemets, Hiragana reference and kana/Han balance verifiers.

## Expected nonvisual binary changes

Changed tables: `head, hhea, maxp, hmtx, cmap, loca, glyf, name, post, vhea, vmtx`. `glyf`, `hmtx`, `vmtx`, `cmap` and `post` append the 45 additions; `loca`, `maxp` and horizontal/vertical metric counts reflect the larger font. `head` has the new revision/checksum; name IDs 3 and 5 have 1.033. Existing names, build timestamp and font family remain unchanged. FontTools reserializes the containers; WOFF2 is recompressed. CSS font URLs now use `?v=1.033` so cached clients receive the new coverage.
