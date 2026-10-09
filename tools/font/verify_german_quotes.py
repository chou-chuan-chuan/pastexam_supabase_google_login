"""Check the single quote revision against released 1.040."""
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

PREVIOUS_COMMIT='915e061f81e2d2a9032aaac0c820824ab623b037'
PREVIOUS_SHA='e9215fa2d8a347fa6a0dae36b0b9ac92156ecda324fb4e64ca7f9f26013628fb'


def verify_quote_shape(font):
    glyf=font['glyf'];low=glyf['quotedblbase'];high=glyf['quotedblleft']
    low.recalcBounds(glyf);high.recalcBounds(glyf)
    assert (low.xMin,low.yMin,low.xMax,low.yMax)==(53,-47,159,82)
    assert (high.xMin,high.yMin,high.xMax,high.yMax)==(44,542,150,671)
    assert low.numberOfContours==high.numberOfContours==2
    expected=RecordingPen();actual=RecordingPen()
    low.draw(TransformPen(expected,Transform(-1,0,0,-1,203,624)),glyf)
    high.draw(actual,glyf)
    assert actual.value==expected.value, 'Upper quote must preserve the exact low-quote strokes'
    assert font['hmtx']['quotedblleft']==(196,44)
    assert font.getBestCmap()[0x201C]=='quotedblleft'
    assert font.getBestCmap()[0x201E]=='quotedblbase'


def verify_revision(previous,current,shape):
    verify_quote_shape(current)
    assert previous.getGlyphOrder()==current.getGlyphOrder()
    changed=[]
    for g in previous.getGlyphOrder():
        if previous['glyf'][g].compile(previous['glyf'])!=current['glyf'][g].compile(current['glyf']):changed.append(g)
        assert previous['hmtx'][g][0]==current['hmtx'][g][0]
        if g!='quotedblleft':assert previous['hmtx'][g]==current['hmtx'][g]
    assert changed==['quotedblleft'],changed
    for tag in ['cmap','vmtx','hhea','vhea','GPOS','GDEF','GSUB','MATH']:
        assert previous[tag].compile(previous)==current[tag].compile(current),tag
    for text in ['„Come and rock me Amadeus“','„Hallo“','„ü“','“Hello”','«Bonjour»',
                 'Ü Ü ü ü ÄÖäö','aː øː n̩ l̩ m̩ i̯ ɐ̯ aɪ̯','中文 あいう マスズ ぱぴぷぺぽ']:
        assert shape(previous,text)==shape(current,text),('layout changed',text)
    return {'previous_commit':PREVIOUS_COMMIT,'previous_sha256':PREVIOUS_SHA,
            'changed_glyph':'quotedblleft','preserved_glyphs':len(current.getGlyphOrder())-1,
            'before_bounds':[19,488,175,671],'after_bounds':[44,542,150,671],
            'advance':196,'low_quote_and_layout_preserved':True}
