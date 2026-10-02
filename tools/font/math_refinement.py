"""Scoped 1.034 math weight, combining-hat positioning and fraction constants."""
from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable, buildMathTable
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.ttLib.tables import otTables
from japanese.stroke_engine import path_to_glyph
import pathops

# Remove this radius from the boundary, without scaling glyph bodies or advances.
WEIGHT_INSET = {'∑': 10, '∇': 10, '∏': 5}
# Override only this combining mark; existing accents and source lookups stay intact.
HAT_BASES = 'xp rLB'.replace(' ','') + 'αβγδεζηθικλμνξοπρστυφχψωϵϕϑϱℋℒℱℜℑ'
HAT_GAP = 48
MATH_AXIS = 330
RULE_THICKNESS = 36


def bounds(font,name):
    pen=BoundsPen(font.getGlyphSet());font.getGlyphSet()[name].draw(pen)
    assert pen.bounds is not None
    return pen.bounds


def inset_glyph(font,name,radius):
    def source_path():
        path=pathops.Path()
        recording=DecomposingRecordingPen(font.getGlyphSet())
        font.getGlyphSet()[name].draw(recording)
        recording.replay(Qu2CuPen(path.getPen(),max_err=.25,all_cubic=True))
        return path
    original=source_path();boundary=source_path()
    boundary.stroke(2*radius,pathops.LineCap.ROUND_CAP,pathops.LineJoin.ROUND_JOIN,4)
    boundary.convertConicsToQuads(.1)
    return path_to_glyph(pathops.simplify(pathops.op(original,boundary,pathops.PathOp.DIFFERENCE)))


def harmonize_weight(font,insets=WEIGHT_INSET):
    cmap=font.getBestCmap()
    for c,radius in insets.items():
        name=cmap[ord(c)];advance,_=font['hmtx'][name]
        glyph=inset_glyph(font,name,radius);glyph.recalcBounds(font['glyf'])
        font['glyf'][name]=glyph
        font['hmtx'][name]=(advance,glyph.xMin)


def add_operator_hats(font):
    cmap=font.getBestCmap();mark=cmap[0x302]
    # Match the existing source attachment coordinate; no new glyph or remapping.
    mark_anchor=(-142,420)
    mb=bounds(font,mark)
    bases={}
    for c in HAT_BASES:
        name=cmap[ord(c)];b=bounds(font,name)
        # Account for the native mark's ink baseline, not its origin.
        center=round((b[0]+b[2])/2)
        y=round(min(b[3]+HAT_GAP-mb[1]+mark_anchor[1],
                    font['OS/2'].sTypoAscender-4-mb[3]+mark_anchor[1]))
        bases[name]={0:buildAnchor(center,y)}
    sub=buildMarkBasePosSubtable({mark:(0,buildAnchor(*mark_anchor))},bases,font.getReverseGlyphMap())
    lookup=otTables.Lookup();lookup.LookupType=4;lookup.LookupFlag=0;lookup.SubTable=[sub];lookup.SubTableCount=1
    g=font['GPOS'].table;index=len(g.LookupList.Lookup)
    g.LookupList.Lookup.append(lookup);g.LookupList.LookupCount+=1
    features=[r.Feature for r in g.FeatureList.FeatureRecord if r.FeatureTag=='mark']
    assert features
    for feature in features:
        feature.LookupListIndex.append(index);feature.LookupCount+=1


def add_math_constants(font):
    # Values in UPM=1024 font units. Existing '=' ink center is 329.5.
    c=dict(ScriptPercentScaleDown=70,ScriptScriptPercentScaleDown=50,
      DelimitedSubFormulaMinHeight=1500,DisplayOperatorMinHeight=700,MathLeading=80,
      AxisHeight=MATH_AXIS,AccentBaseHeight=465,FlattenedAccentBaseHeight=620,
      SubscriptShiftDown=200,SubscriptTopMax=370,SubscriptBaselineDropMin=100,
      SuperscriptShiftUp=380,SuperscriptShiftUpCramped=330,SuperscriptBottomMin=120,
      SuperscriptBaselineDropMax=200,SubSuperscriptGapMin=144,
      SuperscriptBottomMaxWithSubscript=370,SpaceAfterScript=40,
      UpperLimitGapMin=72,UpperLimitBaselineRiseMin=180,
      LowerLimitGapMin=72,LowerLimitBaselineDropMin=500,
      StackTopShiftUp=400,StackTopDisplayStyleShiftUp=550,
      StackBottomShiftDown=250,StackBottomDisplayStyleShiftDown=400,
      StackGapMin=108,StackDisplayStyleGapMin=252,
      StretchStackTopShiftUp=400,StretchStackBottomShiftDown=250,
      StretchStackGapAboveMin=72,StretchStackGapBelowMin=72,
      FractionNumeratorShiftUp=400,FractionNumeratorDisplayStyleShiftUp=500,
      FractionDenominatorShiftDown=250,FractionDenominatorDisplayStyleShiftDown=350,
      FractionNumeratorGapMin=72,FractionNumDisplayStyleGapMin=108,
      FractionRuleThickness=RULE_THICKNESS,FractionDenominatorGapMin=72,
      FractionDenomDisplayStyleGapMin=108,SkewedFractionHorizontalGap=100,SkewedFractionVerticalGap=80,
      OverbarVerticalGap=108,OverbarRuleThickness=RULE_THICKNESS,OverbarExtraAscender=36,
      UnderbarVerticalGap=108,UnderbarRuleThickness=RULE_THICKNESS,UnderbarExtraDescender=36,
      RadicalVerticalGap=45,RadicalDisplayStyleVerticalGap=150,RadicalRuleThickness=RULE_THICKNESS,
      RadicalExtraAscender=36,RadicalKernBeforeDegree=284,RadicalKernAfterDegree=-568,
      RadicalDegreeBottomRaisePercent=60)
    cmap=font.getBestCmap()
    centers={cmap[ord(c)]:round(sum(bounds(font,cmap[ord(c)])[::2])/2) for c in HAT_BASES+'HAT'}
    centers[cmap[0x302]]=-142
    centers[cmap[ord('^')]]=round(sum(bounds(font,cmap[ord('^')])[::2])/2)
    buildMathTable(font,constants=c,topAccentAttachments=centers)


def refine_math(font):
    harmonize_weight(font)
    add_operator_hats(font)
    add_math_constants(font)
