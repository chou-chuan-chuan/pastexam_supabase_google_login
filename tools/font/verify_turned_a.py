"""Pin 1.041 and verify that only the schwa and turned-a outlines change."""
from german_ipa import name, bounds, transformed
from fontTools.misc.transform import Transform

PREVIOUS_COMMIT='2e246a77524dacdfc338e337959f86b3976a8d0b'
PREVIOUS_SHA='799787cc846495ad6bc63d9129cc9685f46135db772f19c621fc61ea0d03fab1'


def verify_revision(previous, current, shape):
    assert previous.getGlyphOrder()==current.getGlyphOrder()
    changed=[g for g in previous.getGlyphOrder()
             if previous['glyf'][g].compile(previous['glyf'])!=current['glyf'][g].compile(current['glyf'])]
    assert changed==[name('ə'),name('ɐ')],changed
    assert bounds(current,name('ə'))==bounds(previous,name('ə'))==(35,110,270,405)
    assert current['hmtx'][name('ə')]==(305,35)
    x0,y0,x1,y1=bounds(current,current.getBestCmap()[ord('e')])
    sx,sy=235/(x1-x0),295/(y1-y0)
    expected=transformed(current,'e',Transform(-sx,0,0,-sy,35+sx*x1,110+sy*y1))
    assert expected.compile(current['glyf'])==current['glyf'][name('ə')].compile(current['glyf']), 'Schwa must be the rotated native e'
    assert current['glyf'][name('ə')].numberOfContours==2
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
            'changed_glyphs':changed,'preserved_glyphs':len(current.getGlyphOrder())-2,
            'bounds':{'ə':[35,110,270,405],'ɐ':[35,110,255,410]},
            'advances':{'ə':305,'ɐ':290},'schwa_uses_rotated_native_e':True,'metrics_and_layout_preserved':True}
