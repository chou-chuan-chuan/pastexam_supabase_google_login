"""User-handwriting Hiragana refined center-line sources.

Version 1.025: the new master sheet supersedes every older visual reference
for its 41 characters. Only なにぬねの keep their previous sources.
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


def S(*points, width=46, start=None, end=None, cap="round") -> Stroke:
    return Stroke(tuple(points), width, start, end, cap)

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
    'な': (
        S((577.9, 328.5), (617.5, 313.1), (729.7, 205.6), width=44.9, start=41.3, end=31.4),
        S((230.3, 599.8), (351.3, 599.8), width=44.9, start=41.3, end=31.4),
        S((577.9, 612.6), (604.3, 610.1), width=44.9, start=41.3, end=31.4),
        S((575.7, 338.7), (547.1, 351.5), (507.5, 351.5), (492.1, 336.2), width=44.9, start=41.3, end=31.4),
        S((476.7, 349.0), (489.9, 333.6), width=44.9, start=41.3, end=31.4),
        S((586.7, 794.4), (626.3, 776.5), (687.9, 692.0), width=44.9, start=41.3, end=31.4),
        S((687.9, 692.0), (679.1, 676.6), width=44.9, start=39.5, end=39.5),
        S((353.5, 597.3), (349.1, 277.3), (333.7, 251.7), width=44.9, start=41.3, end=31.4),
        S((393.1, 771.4), (366.7, 725.3), (357.9, 602.4), width=44.9, start=41.3, end=31.4),
        S((492.1, 331.0), (492.1, 272.2), (505.3, 233.8), (516.3, 226.1), width=44.9, start=41.3, end=31.4),
        S((575.7, 328.5), (564.7, 261.9), (547.1, 236.3), (520.7, 226.1), width=44.9, start=41.3, end=31.4),
        S((569.1, 515.4), (586.7, 497.4), (593.3, 466.7), (591.1, 395.0), (577.9, 341.3), width=44.9, start=41.3, end=31.4),
        S((577.9, 612.6), (549.3, 599.8), (360.1, 599.8), width=44.9, start=41.3, end=31.4),
    ),
    'に': (
        S((675.8, 579.4), (651.6, 597.3), (581.2, 579.4), (460.2, 597.3), (418.4, 574.2), width=48.4, start=44.5, end=33.9),
        S((438.2, 415.5), (458.0, 374.6), (480.0, 290.1), (521.8, 249.1), (618.6, 246.6), (757.2, 290.1), width=48.4, start=44.5, end=33.9),
        S((255.6, 282.4), (249.0, 259.4), width=48.4, start=44.5, end=33.9),
        S((337.0, 395.0), (317.2, 320.8), (297.4, 297.8), (257.8, 285.0), width=48.4, start=44.5, end=33.9),
        S((231.4, 753.4), (211.6, 727.8), (207.2, 697.1), (202.8, 497.4), (229.2, 313.1), (255.6, 285.0), width=48.4, start=44.5, end=33.9),
    ),
    'ぬ': (
        S((437.1, 601.1), (316.1, 596.0), (287.5, 573.0), width=49.8, start=45.8, end=34.9),
        S((217.1, 721.4), (252.3, 642.1), (254.5, 606.2), (267.7, 575.5), width=49.8, start=45.8, end=34.9),
        S((419.5, 736.8), (437.1, 698.4), (439.3, 603.7), width=49.8, start=45.8, end=34.9),
        S((267.7, 573.0), (208.3, 526.9), (170.9, 470.6), (162.1, 401.4), (177.5, 345.1), (272.1, 299.0), (351.3, 299.0), (399.7, 324.6), (419.5, 352.8), width=49.8, start=45.8, end=34.9),
        S((690.1, 342.6), (731.9, 329.8), (797.9, 263.2), width=49.8, start=45.8, end=34.9),
        S((269.9, 573.0), (287.5, 573.0), width=49.8, start=43.8, end=43.8),
        S((287.5, 573.0), (331.5, 455.2), (382.1, 386.1), (419.5, 352.8), width=49.8, start=45.8, end=34.9),
        S((676.9, 373.3), (687.9, 345.1), width=49.8, start=45.8, end=34.9),
        S((430.5, 350.2), (476.7, 309.3), (503.1, 304.2), width=49.8, start=45.8, end=34.9),
        S((448.1, 590.9), (439.3, 365.6), (430.5, 355.4), width=49.8, start=45.8, end=34.9),
        S((672.5, 373.3), (602.1, 370.7), (584.5, 340.0), (593.3, 291.4), (650.5, 276.0), (668.1, 293.9), (687.9, 342.6), width=49.8, start=45.8, end=34.9),
        S((450.3, 593.4), (505.3, 590.9), (577.9, 565.3), (635.1, 503.8), (665.9, 455.2), (674.7, 375.8), width=49.8, start=45.8, end=34.9),
    ),
    'ね': (
        S((695.6, 363.0), (638.4, 393.8), (570.2, 393.8), (526.2, 357.9), (521.8, 334.9), (526.2, 317.0), (576.8, 270.9), (642.8, 258.1), (669.2, 283.7), (695.6, 360.5), width=45.9, start=40.4, end=40.4),
        S((319.4, 514.1), (409.6, 562.7), (524.0, 585.8), (631.8, 588.3), (693.4, 567.8), (730.8, 542.2), (737.4, 511.5), (733.0, 427.0), (715.4, 363.0), width=45.9, start=42.2, end=32.1),
        S((317.2, 626.7), (220.4, 624.2), (185.2, 608.8), width=45.9, start=42.2, end=32.1),
        S((319.4, 624.2), (312.8, 606.2), (317.2, 514.1), width=45.9, start=42.2, end=32.1),
        S((697.8, 360.5), (713.2, 360.5), width=45.9, start=40.4, end=40.4),
        S((317.2, 511.5), (310.6, 480.8), width=45.9, start=42.2, end=32.1),
        S((310.6, 480.8), (266.6, 457.8), (240.2, 404.0), (209.4, 373.3), (196.2, 332.3), (172.0, 296.5), width=45.9, start=42.2, end=32.1),
        S((310.6, 480.8), (321.6, 462.9), (328.2, 391.2), (365.6, 217.1), (367.8, 142.9), width=45.9, start=42.2, end=32.1),
        S((715.4, 360.5), (761.6, 329.8), (788.0, 283.7), width=45.9, start=42.2, end=32.1),
        S((288.6, 829.0), (301.8, 675.4), (321.6, 642.1), width=45.9, start=42.2, end=32.1),
        S((308.4, 857.1), (288.6, 829.0), width=45.9, start=42.2, end=32.1),
        S((260.0, 841.8), (288.6, 829.0), width=45.9, start=42.2, end=32.1),
        S((394.2, 670.2), (323.8, 642.1), width=45.9, start=42.2, end=32.1),
    ),
    'の': (
        S((405.2, 658.7), (433.8, 679.2), (601.0, 663.8), (647.2, 640.8), (700.0, 594.7), (719.8, 541.0), (717.6, 443.7), (649.4, 349.0), (618.6, 320.8), (570.2, 328.5), width=45.9, start=42.2, end=32.1),
        S((405.2, 656.2), (407.4, 515.4), (385.4, 433.4), (350.2, 413.0), (308.4, 418.1), (284.2, 433.4), (251.2, 464.2), (240.2, 502.6), (244.6, 530.7), (317.2, 628.0), (354.6, 653.6), (403.0, 658.7), width=45.9, start=40.4, end=40.4),
    ),
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
