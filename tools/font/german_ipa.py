"""Basic German IPA, v1.037. Only source-native outlines and original strokes.

The source's Latin x-height is roughly y=110..435 at 1024 UPM. New strokes
use its thin, gently varying pressure; no outlines from an external IPA font.
The scope is 19 codepoints, not the complete IPA inventory.
"""
from fontTools.misc.transform import Transform
from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable
from fontTools.pens.recordingPen import DecomposingRecordingPen
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


def build_german_ipa(font):
    cmap = font.getBestCmap()
    if any(ord(c) in cmap for c in BASIC_IPA):
        raise ValueError('IPA source mapping already exists; review before replacing it')
    additions = {}
    for c, source, turned in [('ɛ','ε',False), ('ɪ','I',False), ('ʏ','Y',False)]:
        additions[c] = fit(font, source, rotation=turned)
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
        # Distinctive IPA structures need authored strokes: rotating the source's
        # single-storey a resembles turned alpha, and rotating cursive e obscures
        # the schwa crossbar. Inverted small-cap R reflects vertically, not 180°.
        'ɔ': (340, [([(62,407),(150,427),(235,405),(281,330),(267,226),(214,144),(141,121),(63,140)],36)]),
        'ə': (340, [([(58,388),(115,427),(217,418),(272,348),(275,254),(249,163),(179,124),(101,143),(61,203),(54,271),(272,277)],34)]),
        'ɐ': (350, [([(65,426),(60,321),(61,204),(97,131),(189,117),(267,154)],34),
                    ([(61,289),(137,312),(237,332),(276,378),(247,425),(171,437),(99,408),(64,350)],34)]),
        'ʁ': (365, [([(62,430),(59,269),(57,117),(162,116),(269,140),(290,198),(249,251),(158,271),(60,269)],34),
                    ([(170,270),(237,349),(298,432)],34)]),
        'ʊ': (380, [([(42,421),(105,417),(98,347),(78,242),(108,144),(183,119),(263,153),(295,245),(278,344),(268,416),(331,424)],32)]),
        'ʃ': (280, [([(253,585),(210,619),(154,576),(139,448),(122,269),(106,78),(83,-68),(35,-104),(4,-77)],34)]),
        'ʒ': (335, [([(62,424),(151,432),(261,425),(183,340),(139,300),(236,301),(282,245),(272,148),(216,88),(126,86),(62,121)],34)]),
        'ŋ': (375, [([(68,406),(66,292),(54,135),(112,272),(194,372),(257,358),(280,272),(283,117),(277,-34),(244,-116),(180,-129)],34)]),
        'ʔ': (310, [([(52,492),(69,558),(140,589),(221,573),(250,521),(229,454),(167,405),(148,332),(146,119)],34)]),
        'ˈ': (180, [([(109,615),(86,447)],30)]),
        'ˌ': (180, [([(109,105),(86,-63)],30)]),
        '\u0329': (0, [([(3,-12),(-3,-103)],26)]),
        '\u032f': (0, [([(-83,-79),(-54,-32),(0,-14),(51,-33),(82,-80)],26)]),
    }
    for c, (advance, strokes) in originals.items():
        additions[c] = (build_stroke_glyph(tuple(stroke(p,w) for p,w in strokes)), advance)
    # Two opposed triangular wedges, deliberately distinguishable from colon.
    pen = TTGlyphPen(None)
    for points in [[(53,430),(156,431),(104,301)], [(55,111),(154,110),(105,239)]]:
        pen.moveTo(points[0])
        for p in points[1:]:
            pen.lineTo(p)
        pen.closePath()
    additions['ː'] = (pen.glyph(), 210)
    order = font.getGlyphOrder()
    font.setGlyphOrder(order + [name(c) for c in BASIC_IPA])
    for c in BASIC_IPA:
        glyph, advance = additions[c]
        glyph.recalcBounds(font['glyf'])
        font['glyf'][name(c)] = glyph
        font['hmtx'][name(c)] = (advance, glyph.xMin)
        if 'vmtx' in font:
            font['vmtx'][name(c)] = font['vmtx'][cmap[ord('a')]]
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
