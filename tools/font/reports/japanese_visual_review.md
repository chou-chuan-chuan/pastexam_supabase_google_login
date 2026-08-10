# Japanese Phase 1 visual review

Review date: 2026-08-10

## Gate result

- Master proof: passed before full expansion. The requested master hiragana, katakana, and small kana remain legible from 16 px through 120 px and use the same thin, pressure-varying handwritten language as the source references.
- Full hiragana proof: passed at 16, 20, 24, 32, 48, and 72 px. No visible clipping, contour seam, or mark collision was found.
- Full katakana proof: passed at 16, 20, 24, 32, 48, and 72 px. Angular strokes retain slight terminal and pressure irregularity rather than a geometric sans construction.
- Japanese lyric proof: passed at 16, 20, 24, 32, 48, and 72 px. Shared-code-point kanji and new kana keep a compatible baseline and line rhythm.
- Dakuten proof: passed at 16, 20, 24, 32, 48, 72, and 120 px. Composed and decomposed pairs use the same mark contour, optical origin, and 960-unit total advance.
- Duplicate-outline audit: only `へ` / `ヘ`, the expected shared hiragana/katakana form, are identical among the Phase 1 kana.

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
