# Japanese kana legibility visual review

Review date: 2026-08-10

## Version 1.006 finding

The first Phase 1 proof was technically valid but did not pass a stricter reader-recognition gate. In lyric lines, `の` could read as `0`, counters in several looping hiragana were ambiguous, and the directional contrast in `シ／ツ` and `ソ／ン` was too subtle. Code-point coverage alone was therefore not accepted as visual completion.

## Version 1.007 gate result

- Master proof: reviewed from 16 px through 120 px after canonical-structure corrections; stroke weight remains compatible with the source references.
- Full hiragana proof: passed at 16, 20, 24, 32, 48, and 72 px. No visible clipping, contour seam, or mark collision was found.
- Full katakana proof: passed at 16, 20, 24, 32, 48, and 72 px. Angular strokes retain slight terminal and pressure irregularity rather than a geometric sans construction.
- Japanese lyric proof: `の` now uses an open spiral instead of a closed zero-like loop; the revised looping hiragana keep visible counters at 16, 20, 24, 32, 48, and 72 px.
- Dakuten proof: passed at 16, 20, 24, 32, 48, 72, and 120 px. Composed and decomposed pairs use the same mark contour, optical origin, and 960-unit total advance.
- Duplicate-outline audit: only `へ` / `ヘ`, the expected shared hiragana/katakana form, are identical among the Phase 1 kana.

## Version 1.008 template and alignment gate

- The user-supplied handwritten gojūon chart is used as a structural and proportional reference only; its raster outlines are not traced or embedded.
- Pre-fix measurements put Hiragana/Katakana median optical centers roughly 145 font units above the source Chinese sample.
- All kana center-line outlines now receive a deterministic -145 y translation; center punctuation receives -120 y. The Japanese GPOS base-anchor y moves from 835 to 690, so composed and decomposed dakuten remain identical after alignment.
- `quanfangwei-cjk-kana-alignment-proof.png` confirms Chinese, Hiragana, and Katakana share the same baseline without CSS offsets at 16, 20, 24, 32, 48, 72, and 120 px.

## Source/style judgment

- Stroke weight is based on the measured official-source short-run median of about 51 font units.
- Endpoints are tapered or softly rounded, with small deterministic pressure variation.
- Dakuten uses two separately angled short handwritten strokes derived from the source's quotation/apostrophe/semicolon/dot vocabulary.
- Handakuten is an intentionally non-geometric variable-width loop derived from the source's handwritten circle and enclosure vocabulary.
- No external Japanese font outline was loaded, copied, traced, skewed, or distorted.

## Proofs

- `tools/font/proofs/quanfangwei-kana-master-proof.png`
- `tools/font/proofs/quanfangwei-hiragana-proof.png`
- `tools/font/proofs/quanfangwei-katakana-proof.png`
- `tools/font/proofs/quanfangwei-dakuten-proof.png`
- `tools/font/proofs/quanfangwei-japanese-lyrics-proof.png`

## Browser note

The local HTTP server returned 200 for the WOFF2, browser proof, and Japanese song fixture. Direct Chrome DevTools / Rendered Fonts inspection remains pending because the Codex Chrome extension was not connected in this environment; this report does not treat the automated fontTools/HarfBuzz checks as a substitute for that missing UI observation.
