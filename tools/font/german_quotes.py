"""Match U+201C/U+201D to the existing thin U+201E handwriting."""
from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


def refine_german_quotes(font):
    # Turn the unchanged low 99-form into the upper 66-form at the same size.
    # Retain the old upper quote's ink center x=97 and top y=671.
    pen=TTGlyphPen(None)
    font['glyf']['quotedblbase'].draw(TransformPen(pen,Transform(-1,0,0,-1,203,624)),font['glyf'])
    font['glyf']['quotedblleft']=pen.glyph()
    font['hmtx']['quotedblleft']=(196,44)

    # U+201C is also an English opener. Match its U+201D partner as well,
    # retaining the 99 direction and the old horizontal center/advance.
    pen=TTGlyphPen(None)
    font['glyf']['quotedblbase'].draw(TransformPen(pen,Transform(1,0,0,1,-4,589)),font['glyf'])
    font['glyf']['quotedblright']=pen.glyph()
    font['hmtx']['quotedblright']=(209,49)
    advance,bearing=font['vmtx']['quotedblright']
    font['vmtx']['quotedblright']=(advance,bearing-5)
