"""Independent preservation/clearance checks for the 1.040 U/u diaeresis shift."""
import copy
from unicodedata import normalize

PREVIOUS_COMMIT = '83d20f266e231f89c5de3269f27dd8173624158a'
PREVIOUS_SHA = '46d5ad8aa4ec713fb3c56aaf2e20417fa4c506e65e5cd10369bb59d8f53c2de2'
TARGETS = {'Udieresis':('U',29,88,118,42),'udieresis':('u',35,-62,-32,45)}


def original_umlaut_layout(font):
    """Validate the two precise edits before removing them for old-baseline QA."""
    restored = copy.deepcopy(font)
    lookup = restored['GPOS'].table.LookupList.Lookup[2]
    assert lookup.LookupType == 4 and lookup.SubTableCount == 2
    sub = lookup.SubTable[0]
    assert sub.MarkCoverage.glyphs == ['uni0308'] and sub.BaseCoverage.glyphs == ['U','u']
    assert sub.ClassCount == 1 and sub.MarkArray.MarkCount == 1 and sub.BaseArray.BaseCount == 2
    rec = sub.MarkArray.MarkRecord[0]
    assert rec.Class == 0 and (rec.MarkAnchor.XCoordinate,rec.MarkAnchor.YCoordinate) == (145,477)
    for base,record in zip(sub.BaseCoverage.glyphs,sub.BaseArray.BaseRecord):
        anchor = record.BaseAnchor[0]
        assert len(record.BaseAnchor)==1 and (anchor.XCoordinate,anchor.YCoordinate) == {'U':(174,595),'u':(180,445)}[base]
    lookup.SubTable.pop(0)
    lookup.SubTableCount -= 1
    for target,(base,x,old_y,new_y,gap) in TARGETS.items():
        g=restored['glyf'][target]
        assert [c.getComponentInfo() for c in g.components] == [(base,(1,0,0,1,0,0)),('uni0308',(1,0,0,1,x,new_y))]
        body=restored['glyf'][base];body.recalcBounds(restored['glyf'])
        dots=restored['glyf']['uni0308'];dots.recalcBounds(restored['glyf'])
        assert dots.yMin+new_y-body.yMax == gap
        g.components[1].y = old_y
        g.recalcBounds(restored['glyf'])
        advance,bearing=restored['vmtx'][target]
        restored['vmtx'][target]=(advance,bearing+30)
    return restored


def verify_revision(previous,current,shape):
    restored=original_umlaut_layout(current)
    assert previous.getGlyphOrder()==restored.getGlyphOrder()
    for g in previous.getGlyphOrder():
        assert previous['glyf'][g].compile(previous['glyf']) == restored['glyf'][g].compile(restored['glyf']),('outline',g)
    for tag in ['cmap','hmtx','vmtx','hhea','vhea','GPOS','GDEF','GSUB','MATH']:
        assert previous[tag].compile(previous)==restored[tag].compile(restored),tag
    # Compare the decomposed renderer path; suppress NFC by removing relevant
    # composed mappings only in memory, with ccmp off during HarfBuzz shaping.
    old=copy.deepcopy(previous);new=copy.deepcopy(current)
    other_marks = '\u0307\u0300\u0301\u030b\u0302\u030c\u0306\u030a\u0303\u0304\u030d\u0324'
    composed = {ord(c) for base in 'Uu' for mark in other_marks+'\u0308'
                if len(c := normalize('NFC',base+mark)) == 1}
    for font in [old,new]:
        for table in font['cmap'].tables:
            if table.isUnicode():
                for cp in composed:table.cmap.pop(cp,None)
    for base,dx,dy in [('U',29,118),('u',35,-32)]:
        s=shape(new,base+'\u0308',{'ccmp':False})
        assert len(s)==2 and s[1][2:4]==(0,0)
        assert (s[0][2]+s[1][4],s[1][5])==(dx,dy)
        before=shape(old,base+'\u0308',{'ccmp':False})
        assert s[0]==before[0] and s[1][:5]==before[1][:5] and s[1][5]-before[1][5]==30
    # All other marks in the original shared class keep their actual positions.
    for base in 'Uu':
        for mark in other_marks:
            before=shape(old,base+mark,{'ccmp':False})
            after=shape(new,base+mark,{'ccmp':False})
            assert len(after)==2 and all(item[0]>0 for item in after),(base,mark)
            assert before==after,(base,mark)
    for text in ['ÄÖ äö ÄÖ äö','n̩ l̩ m̩ i̯ ɐ̯ aɪ̯','ˈʃpʁaːxə','ぱぴぷぺぽ ぱぴぷぺぽ','中文 ∑ ∇ x̂']:
        assert shape(previous,text)==shape(current,text),('shaping',text)
    return {'previous_commit':PREVIOUS_COMMIT,'previous_sha256':PREVIOUS_SHA,
            'changed_composites':['Udieresis','udieresis'],'preserved_glyphs':len(current.getGlyphOrder())-2,
            'clearance_units':{'Ü':42,'ü':45},'dot_shift_y':30,
            'other_accents_and_ipa_preserved':True}
