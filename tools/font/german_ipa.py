"""Basic German IPA, v1.042. Only source-native outlines and original strokes.

The source's Latin x-height is roughly y=110..435 at 1024 UPM. New strokes
use its thin, gently varying pressure; no outlines from an external IPA font.
The scope is 19 codepoints, not the complete IPA inventory.
"""
from fontTools.misc.transform import Transform
from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen, replayRecording
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables import otTables
from japanese.stroke_engine import Stroke, build_stroke_glyph, glyph_path, path_to_glyph
import pathops

BASIC_IPA = 'ɛɪɔʊʏøəɐɡʃʒŋʁʔˈˌː\u032f\u0329'
MARKS = '\u032f\u0329'
MARK_GAP = 45
BASES = 'aeiouyœɛɪɔʊʏøəɐɡʃʒŋʁʔpbtdkfvszhçxmnjlr'


def name(c):
    return f'uni{ord(c):04X}.qfwIPA'


def bounds(font, glyph_name):
    glyph = font['glyf'][glyph_name]
    glyph.recalcBounds(font['glyf'])
    return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax


def transformed(font, char, transform):
    recording = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[font.getBestCmap()[ord(char)]].draw(recording)
    pen = TTGlyphPen(None)
    recording.replay(TransformPen(pen, transform))
    return pen.glyph()


def fit(font, char, bottom=110, height=325, rotation=False):
    source = font.getBestCmap()[ord(char)]
    x0, y0, x1, y1 = bounds(font, source)
    scale = height / (y1-y0)
    width = round((x1-x0)*scale)
    transform = (Transform(-scale, 0, 0, -scale, 35+x1*scale, bottom+y1*scale)
                 if rotation else Transform(scale, 0, 0, scale, 35-x0*scale, bottom-y0*scale))
    return transformed(font, char, transform), width+70


def stroke(points, width=34):
    return Stroke(tuple(points), width=width, start_width=width*.95, end_width=width*.80)


def outline_path(font, char, transform=Transform()):
    path = pathops.Path()
    font.getGlyphSet()[font.getBestCmap()[ord(char)]].draw(TransformPen(path.getPen(), transform))
    return path


def rectangle(x0,y0,x1,y1):
    path=pathops.Path(); pen=path.getPen()
    pen.moveTo((x0,y0));pen.lineTo((x1,y0));pen.lineTo((x1,y1));pen.lineTo((x0,y1));pen.closePath()
    return path


def weight(glyph, radius):
    """Restore weight lost when reducing capitals; preserve native irregularity."""
    path=pathops.Path();glyph.draw(path.getPen(),None)
    edge=pathops.Path();glyph.draw(edge.getPen(),None)
    edge.stroke(2*radius,pathops.LineCap.ROUND_CAP,pathops.LineJoin.ROUND_JOIN,4)
    edge.convertConicsToQuads(.1)
    return path_to_glyph(pathops.op(path,edge,pathops.PathOp.UNION))


# Preview A selected after maintainer review. Native g/f/n bodies and heavy
# punctuation remain reference strokes; optical outsets target thinner forms.
WEIGHT_RADII = {'ɛ':2.5, 'ɪ':3, 'ɔ':1.5, 'ʊ':3, 'ʏ':3, 'ø':2,
                'ɐ':3.5, 'ʒ':3, 'ʁ':2, 'ʔ':1.5,
                '\u032f':2, '\u0329':2}
SLANTS = {'ɛ':.02, 'ɪ':.04, 'ʊ':.04, 'ʏ':.04, 'ɐ':.07, 'ʒ':.05}


def refine_weight(glyph, char, glyf):
    """Slightly thicken/shear while retaining the approved ink box and counters."""
    if char not in WEIGHT_RADII:
        return glyph
    glyph.recalcBounds(glyf)
    x0, y0, x1, y1 = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
    contours = glyph.numberOfContours
    glyph = weight(glyph, WEIGHT_RADII[char])
    pen = TTGlyphPen(None)
    glyph.draw(TransformPen(pen, Transform(1, 0, SLANTS.get(char, 0), 1, 0, 0)), glyf)
    glyph = pen.glyph()
    glyph.recalcBounds(glyf)
    sx = (x1-x0)/(glyph.xMax-glyph.xMin)
    sy = (y1-y0)/(glyph.yMax-glyph.yMin)
    pen = TTGlyphPen(None)
    glyph.draw(TransformPen(pen, Transform(sx, 0, 0, sy,
               x0-sx*glyph.xMin, y0-sy*glyph.yMin)), glyf)
    glyph = pen.glyph()
    glyph.recalcBounds(glyf)
    assert (glyph.xMin,glyph.yMin,glyph.xMax,glyph.yMax) == (x0,y0,x1,y1)
    assert glyph.numberOfContours == contours, (char, 'counter/contour changed')
    return glyph


def source_question_body(font):
    recording=RecordingPen();font.getGlyphSet()[font.getBestCmap()[ord('?')]].draw(recording)
    contour=[]
    for op in recording.value:
        contour.append(op)
        if op[0]=='closePath':break
    pen=TTGlyphPen(None);replayRecording(contour,pen);glyph=pen.glyph()
    # Keep the original upper hook and terminal shape. Extend only its stem.
    for i,(x,y) in enumerate(glyph.coordinates):
        if y<390:glyph.coordinates[i]=(x,round(110+(y-288)*280/102))
    return glyph


def source_native_additions(font):
    cmap=font.getBestCmap();out={}
    # The handwritten open c is reflected and lightly sheared, not regularized.
    out['ɔ']=(transformed(font,'c',Transform(-.92,0,.18,1.10,328, -25)),390)
    # Keep original capital-R contour topology and compensate its reflected lean.
    r=transformed(font,'R',Transform())
    for i,(x,y) in enumerate(r.coordinates):
        if x>310:r.coordinates[i]=(round(310+(x-310)*.50),y)
    pen=TTGlyphPen(None)
    r.draw(TransformPen(pen,Transform(.72,0,-.21,-.711,125,507)),font['glyf'])
    out['ʁ']=(weight(pen.glyph(),3),425)
    # Native n joined to the native g descender, with a shared 115..165 overlap.
    body=outline_path(font,'n')
    tail=outline_path(font,'g',Transform(1,0,0,1,77,0))
    tail=pathops.op(tail,rectangle(-100,-300,450,165),pathops.PathOp.INTERSECTION)
    out['ŋ']=(path_to_glyph(pathops.op(body,tail,pathops.PathOp.UNION)),390)
    # Native f's upper hook and stem, with its crossbar removed. The lower hook
    # is the source j body cropped below y=180, shifted into the same stem.
    f=outline_path(font,'f',Transform(1,0,0,1,-90,-40))
    cut=rectangle(-100,270,117,405)
    f=pathops.op(f,cut,pathops.PathOp.DIFFERENCE)
    f=pathops.op(f,rectangle(169,290,400,405),pathops.PathOp.DIFFERENCE)
    j=outline_path(font,'j',Transform(1,0,0,1,-10,-140))
    j=pathops.op(j,rectangle(-100,-250,400,40),pathops.PathOp.INTERSECTION)
    out['ʃ']=(path_to_glyph(pathops.op(f,j,pathops.PathOp.UNION)),300)
    out['ʔ']=(source_question_body(font),312)
    # The source U supplies the asymmetry and pressure; short native quote
    # strokes rotated horizontally close in the horseshoe's top terminals.
    u=outline_path(font,'U',Transform(.88,0,0,.67,0,44))
    for x,y in [(30,375),(220,392)]:
        cap=outline_path(font,"'",Transform(0,.60,-.80,0,x+526.4,y-20))
        u=pathops.op(u,cap,pathops.PathOp.UNION)
    out['ʊ']=(weight(path_to_glyph(u),2),380)
    # Actual source punctuation, not generic geometric strokes.
    out['ˈ']=(transformed(font,"'",Transform(1,0,0,1.25,40,-207)),180)
    out['ˌ']=(transformed(font,"'",Transform(1,0,0,1.25,40,-723)),180)
    out['\u0329']=(transformed(font,"'",Transform(.56,0,0,.80,-32.5,-526.4)),0)
    out['\u032f']=(transformed(font,'\u0306',Transform(1,0,0,-1,145,453)),0)
    pen=TTGlyphPen(None)
    transformed(font,'▼',Transform(.31,0,0,.31,33,266)).draw(pen,font['glyf'])
    transformed(font,'▲',Transform(.31,0,0,.31,33,62)).draw(pen,font['glyf'])
    glyph = pen.glyph()
    glyph.recalcBounds(font['glyf'])
    # Reduce height to 65% and width to 48% around the ink center.
    # Keep its advance so existing IPA lines do not reflow.
    cx = (glyph.xMin + glyph.xMax) / 2
    cy = (glyph.yMin + glyph.yMax) / 2
    pen = TTGlyphPen(None)
    glyph.draw(TransformPen(pen, Transform(.48, 0, 0, .65, .52*cx, .35*cy)), font['glyf'])
    out['ː']=(pen.glyph(),210)
    return out


def build_german_ipa(font):
    cmap = font.getBestCmap()
    if any(ord(c) in cmap for c in BASIC_IPA):
        raise ValueError('IPA source mapping already exists; review before replacing it')
    additions = {}
    for c, source, turned in [('ɛ','ε',False), ('ɪ','I',False), ('ʏ','Y',False)]:
        glyph,advance=fit(font, source, rotation=turned)
        additions[c]=(weight(glyph,{'ɛ':3,'ɪ':6,'ʏ':8}[c]),advance)
    # Ordinary g is already single-storey in this handwriting. Keep that
    # legitimate shape, but install a separate IPA glyph and Unicode mapping.
    additions['ɡ'] = (transformed(font, 'g', Transform()), font['hmtx'][cmap[ord('g')]][0])
    # Slashed o retains the exact source o; the slash is an original thin stroke.
    source_o = pathops.Path()
    font.getGlyphSet()[cmap[ord('o')]].draw(source_o.getPen())
    slash = glyph_path((stroke([(55,105),(250,441)],29),))
    additions['ø'] = (path_to_glyph(pathops.op(source_o, slash, pathops.PathOp.UNION)),
                      font['hmtx'][cmap[ord('o')]][0])
    originals = {
        # Keep essential turned-a / ezh structures, but use the source's
        # irregular turns, rightward lean and 40..48-unit handwritten pressure.
        'ɐ': (290, [([(34,436),(82,435),(83,351),(77,250),(86,171),(139,125),(222,132),(270,177)],44),
                    ([(83,353),(123,422),(206,434),(267,401),(276,352),(236,297),(168,280),(111,296),(83,353)],42)]),
        'ʒ': (350, [([(66,414),(154,432),(271,444),(191,348),(137,284),(232,286),(282,220),(264,99),(218,18),(130,-6),(58,33)],44)]),
    }
    for c, (advance, strokes) in originals.items():
        additions[c] = (build_stroke_glyph(tuple(stroke(p,w) for p,w in strokes)), advance)
    additions.update(source_native_additions(font))
    # 1.042: derive schwa directly from native e rotated 180 degrees. Fit the
    # existing compact ink box; retain native pressure, without added outsets.
    x0, y0, x1, y1 = bounds(font, cmap[ord('e')])
    sx, sy = 235 / (x1-x0), 295 / (y1-y0)
    additions['ə'] = (transformed(font, 'e', Transform(-sx, 0, 0, -sy,
                       35+sx*x1, 110+sy*y1)), 305)
    # 1.042: round upper bowl and projecting left terminal distinguish turned a
    # from native e. Preserve the approved 220 x 300 ink box and 290 advance.
    glyph, advance = additions['ɐ']
    glyph.recalcBounds(font['glyf'])
    sx = 220 / (glyph.xMax - glyph.xMin)
    sy = 300 / (glyph.yMax - glyph.yMin)
    pen = TTGlyphPen(None)
    glyph.draw(TransformPen(pen, Transform(sx, 0, 0, sy,
               35-sx*glyph.xMin, 110-sy*glyph.yMin)), font['glyf'])
    additions['ɐ'] = (pen.glyph(), advance)
    order = font.getGlyphOrder()
    font.setGlyphOrder(order + [name(c) for c in BASIC_IPA])
    for c in BASIC_IPA:
        glyph, advance = additions[c]
        glyph = refine_weight(glyph, c, font['glyf'])
        glyph.recalcBounds(font['glyf'])
        font['glyf'][name(c)] = glyph
        font['hmtx'][name(c)] = (advance, glyph.xMin)
        if 'vmtx' in font:
            source = cmap[ord('g' if c == 'ɡ' else 'a')]
            vadvance, top_bearing = font['vmtx'][source]
            # Share the source's vertical origin (819), not its raw bearing:
            # a tall esh must not enlarge the global vertical extent.
            origin = bounds(font, source)[3] + top_bearing
            font['vmtx'][name(c)] = (vadvance, origin - glyph.yMax)
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format != 14:
                table.cmap[ord(c)] = name(c)
    font['maxp'].numGlyphs = len(font.getGlyphOrder())
    add_mark_positioning(font)


def add_mark_positioning(font):
    cmap = font.getBestCmap()
    marks = {name(c): (0, buildAnchor(0, bounds(font,name(c))[3])) for c in MARKS}
    bases = {}
    for c in BASES:
        glyph_name = cmap[ord(c)]
        x0,y0,x1,_ = bounds(font, glyph_name)
        bases[glyph_name] = {0: buildAnchor(round((x0+x1)/2), y0-MARK_GAP)}
    sub = buildMarkBasePosSubtable(marks, bases, font.getReverseGlyphMap())
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable, lookup.SubTableCount = [sub], 1
    gpos = font['GPOS'].table
    index = len(gpos.LookupList.Lookup)
    gpos.LookupList.Lookup.append(lookup)
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)
    features = [r.Feature for r in gpos.FeatureList.FeatureRecord if r.FeatureTag == 'mark']
    if not features:
        raise ValueError('Expected the existing source mark feature')
    for feature in features:
        feature.LookupListIndex.append(index)
        feature.LookupCount = len(feature.LookupListIndex)
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    for c in BASIC_IPA:
        classes[name(c)] = 3 if c in MARKS else 1
