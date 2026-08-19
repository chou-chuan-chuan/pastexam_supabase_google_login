# User-authored Hiragana SVG template — Version 1.010

## Source and authorship

- Source file: `tools/font/references/user-hiragana-template-source.png`
- SHA-256: `dea3c4c8576744dd609161940aae594a92bb9864b174a54dfce53759c32f0a00`
- The image is the project maintainer's own handwriting, supplied directly for this font revision.
- No external Japanese font outline is loaded, copied, or embedded.

## Coverage

The source sheet contains 43 basic modern Hiragana:

`あかさたなはまやらいきしちにひみりうくすつぬふむゆるえけせてねへめれおこそとのほもよろ`

It does **not** contain `わ・を・ん`; those three retain the existing project-local center-line design. Katakana, historical kana, marks, punctuation, and Japanese kanji are unchanged by this revision.

Eleven small forms are generated deterministically from the reviewed SVG bases:

`ぁぃぅぇぉゃゅょっゕゖ`

Precomposed voiced and semi-voiced kana continue to share their base glyph and mark components, so forms such as `が・じ・づ・ば・ぱ・ゔ` inherit the new handwritten bases automatically.

## Vector construction

- The raster handwriting was segmented by its original grid cells.
- After a light blur, ink was thresholded at 215 and dilated once with a 3×3 kernel to bring the median stroke weight close to the existing font's approximately 51-unit handwriting stroke.
- Contours were simplified and normalized into a 960×1024 y-up SVG coordinate system.
- Each SVG is preserved as version-controlled source artwork.
- Build-time optical transform: scale 110% around `(480, 500)`, then apply the existing kana vertical shift of `-145` units.
- This revision intentionally vectorizes the maintainer's own raster handwriting; earlier “structure-only / no raster tracing” statements apply only to the previous center-line revision and are superseded for these 43 glyphs.

## Review artifacts

- `tools/font/references/user-hiragana-template.svg`
- `tools/font/references/user-hiragana-template-manifest.json`
- `tools/font/proofs/quanfangwei-user-handwritten-hiragana-proof.png`

## Verification

Run:

```powershell
python tools/font/build_supplement_font.py
python tools/font/verify_supplement_font.py
python tools/font/verify_handwritten_hiragana_svg.py
python tools/font/render_proof.py
python tools/font/render_handwritten_hiragana_proof.py
node --test tests/font.test.mjs
```

`verify_handwritten_hiragana_svg.py` checks the source-image and SVG hashes, then compares every built SVG-derived outline against a fresh deterministic build from the versioned SVG data.
