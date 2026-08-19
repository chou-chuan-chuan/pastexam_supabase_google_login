# User-handwriting Hiragana refinement — Version 1.011

Version 1.011 changes the role of the maintainer-owned Hiragana SVGs.  The SVG
filled outlines are retained as versioned structural references, but they are
**not installed directly as font glyph outlines**.  Instead, all 46 modern
basic Hiragana are represented by pre-generated project-local center-line
branches in `kana_sources/user_handwriting_refined.py`; the existing
`japanese.stroke_engine` then supplies variable width, pressure variation,
rounded/handwritten terminals, and taper.

## Source coverage

- Version 1.010 source chart: 43 basic Hiragana.
- Version 1.011 complete source chart: adds `わ` / `を` / `ん`.
- Final basic source coverage: all 46 modern Hiragana.
- Small `ぁぃぅぇぉゃゅょっゎゕゖ` are deterministically derived from the
  corresponding refined basic forms.
- Dakuten / handakuten composites continue to share the existing mark contours
  and GPOS deltas.

## Style normalization

The handwritten structural references are normalized before the final
variable-width renderer:

- x structural scale: `1.10`
- y structural scale: `1.28`
- per-glyph recenter: `(480, 500)` in the 960×1024 design space
- target stroke width range: `42–50` font units before renderer pressure/taper
- build-time Kana vertical shift remains `-145` units
- final 1.011 verification compares the median Hiragana optical center with a
  source-CJK sample and requires a difference of at most 30 font units

Per-glyph recentering is deliberate: cell placement in the scanned handwriting
chart must not become a font side-bearing or baseline artifact.

## Recognition gates

The refinement explicitly reviews `き / さ / し / ち / ぬ / ね / の / み /
む / め / や / れ / わ / を / ん`.  In particular:

- `む` retains the short detached mark from the maintainer's handwriting.
- `ぬ` and `め` must remain structurally distinct.
- `き` and `さ` remain distinct at the lower structure.
- `ね`, `れ`, and `わ` retain different right-side structures.
- `わ`, `を`, and `ん` now have maintainer-authored SVG references rather than
  falling back to the previous project-local source.

## Proofs

After rebuilding, inspect:

- `tools/font/proofs/quanfangwei-user-handwritten-hiragana-proof.png`
- `tools/font/proofs/quanfangwei-user-handwritten-mixed-proof.png`
- `tools/font/proofs/quanfangwei-cjk-kana-alignment-proof.png`
- `tools/font/proofs/quanfangwei-japanese-lyrics-proof.png`

The mixed proof is the primary acceptance artifact for deciding whether the
refined Hiragana visually belongs to the same handwriting system as the source
Chinese glyphs.
