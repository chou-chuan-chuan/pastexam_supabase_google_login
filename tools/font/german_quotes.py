"""Match U+201C to the existing thin U+201E handwriting without text rewriting."""
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
