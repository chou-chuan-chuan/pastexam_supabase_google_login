"""Check the single turned-h addition against the released 1.042 font."""
import copy
from fontTools.misc.transform import Transform
from german_ipa import bounds, name, transformed

PREVIOUS_COMMIT='9b896f7a5475e05ab81f8163222968e67224d85c'
PREVIOUS_SHA='50cfc3581585766c5d74fd41a251131893e2c47746f1c200090a182263b72360'


def verify_revision(previous,current,shape):
    added=name('ɥ')
    assert 0x0265 not in previous.getBestCmap()
    assert current.getGlyphOrder()==previous.getGlyphOrder()+[added]
    for g in previous.getGlyphOrder():
        assert previous['glyf'][g].compile(previous['glyf'])==current['glyf'][g].compile(current['glyf']),g
        assert previous['hmtx'][g]==current['hmtx'][g],g
        assert previous['vmtx'][g]==current['vmtx'][g],g
    for old,new in zip(previous['cmap'].tables,current['cmap'].tables):
        assert (old.platformID,old.platEncID,old.format)==(new.platformID,new.platEncID,new.format)
        expected=dict(old.cmap)
        if new.isUnicode() and new.format!=14:expected[0x0265]=added
        assert new.cmap==expected
    assert len(previous['cmap'].tables)==len(current['cmap'].tables)
    expected=transformed(current,'h',Transform(-1,0,0,-1,303,546))
    assert expected.compile(current['glyf'])==current['glyf'][added].compile(current['glyf'])
    assert bounds(current,added)==(19,-70,284,435)
    assert current['hmtx'][added]==(306,19)
    assert current['vmtx'][added][1]+435==819
    # Removing the single new base from the existing IPA lookup must recover
    # exactly the released layout; all old anchors remain byte-identical.
    gpos=copy.deepcopy(current['GPOS'])
    sub=gpos.table.LookupList.Lookup[-1].SubTable[0]
    index=sub.BaseCoverage.glyphs.index(added)
    assert sub.BaseArray.BaseRecord[index].BaseAnchor[0].XCoordinate==152
    assert sub.BaseArray.BaseRecord[index].BaseAnchor[0].YCoordinate==-115
    sub.BaseCoverage.glyphs.pop(index);sub.BaseArray.BaseRecord.pop(index)
    sub.BaseArray.BaseCount-=1
    assert gpos.compile(current)==previous['GPOS'].compile(previous)
    gdef=copy.deepcopy(current['GDEF'])
    assert gdef.table.GlyphClassDef.classDefs.pop(added)==1
    assert gdef.compile(current)==previous['GDEF'].compile(previous)
    for tag in ['GSUB','MATH','OS/2']:
        assert current[tag].compile(current)==previous[tag].compile(previous),tag
    for tag,count in [('hhea','numberOfHMetrics'),('vhea','numberOfVMetrics')]:
        header=copy.deepcopy(current[tag]);setattr(header,count,getattr(previous[tag],count))
        assert header.compile(current)==previous[tag].compile(previous),tag
    for text in ['e ə ɐ a','ˈmʏtɐ ˈzɔmɐ ˈbɛsɐ','ɐ̯ i̯ aɪ̯ n̩ l̩ m̩',
                 '„Come and rock me Amadeus“ “Hallo”','Ü Ü ü ü ÄÖäö','中文 あいう マスズ ぱぴぷぺぽ']:
        assert shape(previous,text)==shape(current,text),text
    for text in ['[ɥ]','ɥi','ɥɛ','ɥ̯','ɥ̩']:
        assert all(g[0]>0 for g in shape(current,text)),text
    return {'previous_commit':PREVIOUS_COMMIT,'previous_sha256':PREVIOUS_SHA,
            'added_glyphs':[added],'preserved_glyphs':len(previous.getGlyphOrder()),
            'bounds':[19,-70,284,435],'advance':306,'source':'native h rotated 180 degrees',
            'all_existing_outlines_metrics_and_layout_preserved':True}
