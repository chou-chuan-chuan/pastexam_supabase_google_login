"""45 quantum symbols: native source derivatives and original pressure strokes.

All coordinates are font units (UPM 1024), Y upward. New glyph names are
independent even when they borrow existing contours. No external font is used.
The 330-unit math axis follows the native equal/inequality/arrow family.
"""
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from japanese.stroke_engine import Stroke, glyph_path, path_to_glyph
import pathops

GROUPS = {
    'P0': 'ℏ∂∝−↔',
    'P1': '∑∇⋅⟨⟩≈≃∼≤≥≪≫⇒⇔',
    'P2': '∏∓†″ℓ⊗‖∬∭ϵϕ≲≳',
    'P3': '∀∃∈∉ℝℂℋℒℱℜℑϑϱ',
}
CHARACTERS = ''.join(GROUPS.values())
MAPPINGS = {ord(c): f'uni{ord(c):04X}.qfwMath' for c in CHARACTERS}


def stroke(*points, width=43):
    return Stroke(tuple(points), width, width*.98, width*.78)


def wave(y=330):
    return stroke((65,y-24),(145,y+25),(225,y+22),(315,y-22),(395,y-23),(465,y+24),width=40)


def bar(y=330, x1=65, x2=465):
    return stroke((x1,y-5),(x2,y+5),width=41)


def chevron(right=False, dx=0, dy=0):
    # Separate straight branches retain a crisp handwritten vertex.
    if right:
        return [stroke((65+dx,480+dy),(265+dx,330+dy)),stroke((265+dx,330+dy),(65+dx,180+dy))]
    return [stroke((265+dx,480+dy),(65+dx,330+dy)),stroke((65+dx,330+dy),(265+dx,180+dy))]


def recipes():
    """Return advance, source components (character, affine), original strokes."""
    r = {}
    def add(c, advance, strokes=(), components=()):
        r[c] = (advance, components, tuple(strokes))
    add('ℏ',370,[stroke((60,477),(245,503),width=37)],[('h',(1,0,.12,1,-3,0))])
    add('∂',380,[stroke((85,539),(173,604),(275,572),(297,454),(250,227),(175,131),(87,148),(66,248),(121,332),(216,351),(271,315))])
    add('∝',565,[stroke((496,461),(419,429),(312,271),(237,213),(140,238),(73,319),(101,400),(192,420),(273,365),(375,237),(480,227))])
    add('−',530,[bar()])
    add('↔',680,[bar(330,70,610),stroke((225,451),(65,330),(222,208)),stroke((465,451),(615,330),(465,208))])
    add('∑',560,components=[('Σ',(1.24,0,0,1.12,-1,-35))])
    add('∇',510,components=[('Δ',(1.2,0,0,-1.3,-13,806))])
    add('⋅',240,components=[('·',(1,0,0,1,35,-19))])
    add('⟨',255,[stroke((196,654),(70,333)),stroke((70,333),(192,16))])
    add('⟩',255,[stroke((63,654),(187,333)),stroke((187,333),(66,16))])
    add('∼',530,[wave()]);add('≈',530,[wave(400),wave(260)]);add('≃',530,[wave(408),bar(246)])
    for c,right in [('≤',False),('≥',True)]:
        add(c,355,chevron(right,0,72)+[bar(110,65,285)])
    for c,right in [('≪',False),('≫',True)]:
        add(c,535,chevron(right)+chevron(right,200))
    for c,both in [('⇒',False),('⇔',True)]:
        strokes=[bar(384,150 if both else 65,533),bar(276,150 if both else 65,533),stroke((462,478),(615,330),(462,183))]
        if both: strokes += [stroke((217,478),(65,330),(217,183))]
        add(c,680,strokes)
    add('∏',580,components=[('Π',(1.18,0,0,1.08,-9,-20))])
    add('∓',440,components=[('±',(1,0,0,-1,15,698))])
    add('†',380,[stroke((197,664),(184,130)),bar(455,68,312)])
    add('″',290,components=[('′',(1,0,0,1,18,0)),('′',(1,0,0,1,150,0))])
    add('ℓ',345,[stroke((77,219),(200,392),(262,535),(230,609),(163,551),(110,365),(100,183),(153,119),(257,162))])
    add('⊗',600,[stroke((300,572),(463,503),(530,330),(461,158),(295,93),(130,169),(67,338),(140,508),(300,572)),stroke((152,478),(445,186)),stroke((158,185),(440,477))])
    add('‖',330,components=[('|',(1,0,0,1,-14,0)),('|',(1,0,0,1,124,0))])
    add('∬',715,components=[('∫',(1,0,0,1,0,0)),('∫',(1,0,0,1,270,0))])
    add('∭',985,components=[('∫',(1,0,0,1,0,0)),('∫',(1,0,0,1,270,0)),('∫',(1,0,0,1,540,0))])
    add('ϵ',365,[stroke((287,456),(177,470),(84,398),(66,280),(109,161),(203,126),(290,152)),bar(307,68,264)])
    add('ϕ',440,[stroke((221,480),(91,432),(68,308),(122,206),(263,190),(365,258),(369,381),(299,464),(221,480)),stroke((254,624),(213,-91))])
    for c,right in [('≲',False),('≳',True)]:
        add(c,410,chevron(right,35,80)+[stroke((65,111),(138,145),(213,107),(285,82),(346,123),width=38)])
    add('∀',490,[stroke((67,603),(241,86)),stroke((241,86),(425,607)),bar(315,163,345)])
    add('∃',460,[bar(596,66,379),stroke((378,596),(365,108)),bar(350,104,371),bar(107,66,365)])
    member=[stroke((380,525),(209,528),(95,451),(72,331),(124,212),(234,167),(377,177)),bar(348,75,365)]
    add('∈',445,member);add('∉',445,member+[stroke((355,635),(109,83),width=35)])
    # Blackboard capitals: retain source gestures and add a separated inner stem.
    add('ℝ',570,[stroke((79,112),(138,586)),stroke((192,574),(135,118),width=32),stroke((138,586),(291,593),(422,550),(442,445),(353,363),(115,355)),stroke((281,360),(395,204),(507,112))])
    add('ℂ',500,[stroke((257,489),(171,430),(125,319),(165,213),(228,168),width=32)], [('C',(1,0,0,1,10,0))])
    # Script capitals with looped entry/exit gestures; not aliases of H/L/F.
    add('ℋ',670,[stroke((63,466),(111,577),(213,612),(231,541),(151,337),(112,112)),stroke((83,309),(225,348),(398,355),(543,421)),stroke((414,527),(538,600),(574,556),(509,367),(445,167),(469,110),(568,168))])
    add('ℒ',525,[stroke((122,428),(223,484),(319,579),(283,632),(213,575),(176,395),(138,211),(73,124),(177,126),(297,98),(428,160))])
    add('ℱ',580,[stroke((75,506),(161,594),(299,605),(435,578),(510,607)),stroke((298,599),(226,363),(148,111),(84,92)),stroke((144,337),(248,354),(409,371)),stroke((425,433),(390,280),width=36)])
    # Fraktur-like broken stems and diamond joins distinguish real/imaginary.
    add('ℜ',605,[stroke((68,511),(151,601)),stroke((151,601),(199,557),(156,319),(108,111)),stroke((139,328),(249,371),(239,560),(340,608)),stroke((340,608),(445,552),(471,441),(378,354),(249,371)),stroke((326,360),(405,210),(496,118),(551,171))])
    add('ℑ',435,[stroke((72,533),(170,603),(284,568),(356,608)),stroke((284,568),(237,402),(286,345),(222,260),(193,116),(99,63),(63,105)),stroke((130,435),(235,402)),stroke((106,284),(222,260))])
    add('ϑ',455,[stroke((72,432),(149,392),(285,401),(359,497),(320,582),(250,565),(225,460),(274,246),(234,153),(145,145),(81,241),(72,350))])
    add('ϱ',420,[stroke((95,-99),(79,49),(103,287),(155,426),(264,467),(324,407),(312,298),(224,247),(126,284)),stroke((103,80),(165,-26),(286,-52),(350,-6))])
    assert set(r) == set(CHARACTERS)
    return r


def build_quantum_symbols(font):
    # Imports here avoid a circular import during the canonical builder's import.
    from build_supplement_font import install_glyph, add_unicode_mapping
    cmap = font.getBestCmap()
    for c, (advance, components, strokes) in recipes().items():
        assert ord(c) not in cmap, f'Existing mapping must not be replaced: {c}'
        name = MAPPINGS[ord(c)]
        if components and not strokes:
            pen = TTGlyphPen(font.getGlyphSet())
            for source, transform in components:
                pen.addComponent(cmap[ord(source)], transform)
            glyph = pen.glyph()
        else:
            path = glyph_path(strokes)
            for source, transform in components:
                native = pathops.Path()
                font.getGlyphSet()[cmap[ord(source)]].draw(TransformPen(native.getPen(),transform))
                path = pathops.op(path,native,pathops.PathOp.UNION)
            glyph = path_to_glyph(path)
        glyph.recalcBounds(font['glyf'])
        install_glyph(font,name,glyph,advance,glyph.xMin,cmap[ord('=')])
        add_unicode_mapping(font,ord(c),name)
