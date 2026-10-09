"""Pin 1.041 and verify that only the turned-a outline changes."""
from german_ipa import name, bounds

PREVIOUS_COMMIT='2e246a77524dacdfc338e337959f86b3976a8d0b'
PREVIOUS_SHA='799787cc846495ad6bc63d9129cc9685f46135db772f19c621fc61ea0d03fab1'


def verify_revision(previous, current, shape):
    assert previous.getGlyphOrder()==current.getGlyphOrder()
    changed=[g for g in previous.getGlyphOrder()
             if previous['glyf'][g].compile(previous['glyf'])!=current['glyf'][g].compile(current['glyf'])]
    assert changed==[name('ɐ')],changed
    for tag in ['cmap','hmtx','vmtx','hhea','vhea','GPOS','GDEF','GSUB','MATH']:
        assert previous[tag].compile(previous)==current[tag].compile(current),tag
    assert bounds(previous,name('ɐ'))==bounds(current,name('ɐ'))==(35,110,255,410)
    assert current['hmtx'][name('ɐ')]==(290,35)
    assert current['glyf'][name('ɐ')].numberOfContours==2, 'Upper bowl must remain open inside'
    for text in ['e ə ɐ a','ˈmʏtɐ ˈzɔmɐ ˈbɛsɐ','ɐ̯ i̯ aɪ̯ n̩ l̩ m̩',
                 '„Come and rock me Amadeus“ “Hallo”','Ü Ü ü ü ÄÖäö',
                 '中文 あいう マスズ ぱぴぷぺぽ']:
        assert shape(previous,text)==shape(current,text),('layout changed',text)
    return {'previous_commit':PREVIOUS_COMMIT,'previous_sha256':PREVIOUS_SHA,
            'changed_glyphs':changed,'preserved_glyphs':len(current.getGlyphOrder())-1,
            'bounds':[35,110,255,410],'advance':290,'metrics_and_layout_preserved':True}
