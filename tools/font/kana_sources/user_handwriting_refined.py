"""User-handwriting Hiragana refined center-line sources.

Version 1.025: the complete Master v2 (main sheet plus supplementary na-row)
supersedes every older visual reference for all 46 modern basic Hiragana.
The earlier revisions below are historical provenance.
Version 1.021 explicitly replaces only U+304D き from a newer maintainer PNG
structural reference; its four clean center-lines supersede the older branches.
Version 1.022 likewise replaces only U+3084 や from the maintainer's newly
supplied handwriting, using three clean center-lines for its compact hooked
cross-stroke, separate upper mark, and long naturally slanted descending stroke.
Version 1.024 repairs U+304A お against the maintainer's authoritative photo.
Its three clean center-lines now follow the photographed proportions more
closely: a rising upper cross, tall organic main stroke with a pointed left
turn into a broad asymmetric lower body, and a detached right mark.
The same revision explicitly replaces U+3046 う from a new maintainer photo
with a compact upper mark and one long asymmetric descending main stroke. It
also replaces U+3042 あ, U+3044 い, U+3055 さ, U+304D き, U+3068 と, and
U+308A り from two newly supplied maintainer-owned reference sheets. The new
U+304D source explicitly supersedes the Version 1.021 revision.
The SVG filled outlines are NOT installed directly.  They are reduced to
project-local center-line branches, optically normalized, and rendered through
the existing variable-width handwriting stroke engine so Japanese kana shares
weight, taper, terminals, and pressure variation with the derived source style.
No external Japanese font outline is loaded, traced, transformed, or embedded.
"""

from __future__ import annotations

from japanese.stroke_engine import Stroke
from kana_sources.hiragana_master_v2 import MASTER_SOURCES

USER_HANDWRITING_REFINED: dict[str, tuple[Stroke, ...]] = {
    'あ': MASTER_SOURCES["あ"].strokes(),
    'い': MASTER_SOURCES["い"].strokes(),
    'う': MASTER_SOURCES["う"].strokes(),
    'え': MASTER_SOURCES["え"].strokes(),
    'お': MASTER_SOURCES["お"].strokes(),
    'か': MASTER_SOURCES["か"].strokes(),
    'き': MASTER_SOURCES["き"].strokes(),
    'く': MASTER_SOURCES["く"].strokes(),
    'け': MASTER_SOURCES["け"].strokes(),
    'こ': MASTER_SOURCES["こ"].strokes(),
    'さ': MASTER_SOURCES["さ"].strokes(),
    'し': MASTER_SOURCES["し"].strokes(),
    'す': MASTER_SOURCES["す"].strokes(),
    'せ': MASTER_SOURCES["せ"].strokes(),
    'そ': MASTER_SOURCES["そ"].strokes(),
    'た': MASTER_SOURCES["た"].strokes(),
    'ち': MASTER_SOURCES["ち"].strokes(),
    'つ': MASTER_SOURCES["つ"].strokes(),
    'て': MASTER_SOURCES["て"].strokes(),
    'と': MASTER_SOURCES["と"].strokes(),
    'な': MASTER_SOURCES["な"].strokes(),
    'に': MASTER_SOURCES["に"].strokes(),
    'ぬ': MASTER_SOURCES["ぬ"].strokes(),
    'ね': MASTER_SOURCES["ね"].strokes(),
    'の': MASTER_SOURCES["の"].strokes(),
    'は': MASTER_SOURCES["は"].strokes(),
    'ひ': MASTER_SOURCES["ひ"].strokes(),
    'ふ': MASTER_SOURCES["ふ"].strokes(),
    'へ': MASTER_SOURCES["へ"].strokes(),
    'ほ': MASTER_SOURCES["ほ"].strokes(),
    'ま': MASTER_SOURCES["ま"].strokes(),
    'み': MASTER_SOURCES["み"].strokes(),
    'む': MASTER_SOURCES["む"].strokes(),
    'め': MASTER_SOURCES["め"].strokes(),
    'も': MASTER_SOURCES["も"].strokes(),
    'や': MASTER_SOURCES["や"].strokes(),
    'ゆ': MASTER_SOURCES["ゆ"].strokes(),
    'よ': MASTER_SOURCES["よ"].strokes(),
    'ら': MASTER_SOURCES["ら"].strokes(),
    'り': MASTER_SOURCES["り"].strokes(),
    'る': MASTER_SOURCES["る"].strokes(),
    'れ': MASTER_SOURCES["れ"].strokes(),
    'ろ': MASTER_SOURCES["ろ"].strokes(),
    'わ': MASTER_SOURCES["わ"].strokes(),
    'を': MASTER_SOURCES["を"].strokes(),
    'ん': MASTER_SOURCES["ん"].strokes(),
}

MODERN_HIRAGANA_ORDER = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
assert set(MODERN_HIRAGANA_ORDER) == set(USER_HANDWRITING_REFINED)
