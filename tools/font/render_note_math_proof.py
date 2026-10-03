#!/usr/bin/env python3
"""Render the shared note geometry with native outlines at matching sizes."""
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont
from math_layout import MathLayout
from note_math_layout import NoteMathLayout
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import replayRecording

ROOT=Path(__file__).resolve().parents[2]
FONT=ROOT/'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'


def main():
    with tempfile.TemporaryDirectory() as temp:
        native=MathLayout(FONT,temp)
        layout=NoteMathLayout(native.font)
        image=Image.new('RGB',(1200,1850),'#fffdf8');draw=ImageDraw.Draw(image)
        label=ImageFont.truetype(str(FONT),25)
        def metrics(text,size):
            return layout.text_metrics(text,size,native.text(text).width*layout.scale(size))
        def text(x,y,value,size):
            native.draw(draw,native.text(value),x,y,size*layout.math_scale,fill='#150592')
            return metrics(value,size)[0]
        def conjugate(x,y,value,size):
            width,ascent,_=metrics(value,size)
            text(x,y,value,size)
            rise,_=layout.conjugate_geometry(ascent,size)
            return width+1+text(x+width+1,y-rise,'*',size)
        draw.text((30,20),'Native font 1.034 / shared quantum-note layout',font=label,fill='#345')
        for size,y in ((32,140),(64,285)):
            draw.text((30,y-20),f'{size}px / 65% → full-size star',font=label,fill='#345')
            width=text(405,y,'Ψ',size)
            text(406+width,y-.51*size,'*',size*.65)
            conjugate(620,y,'Ψ',size)
        draw.text((30,340),'Integral bounds at upper/lower right; sum policy unchanged.',font=label,fill='#345')
        size=80;y=505;x=40
        x+=text(x,y,'= ',size)
        dx,uy,ly,bounds=layout.integral_geometry(metrics('∫',size*1.35),metrics('−∞',size*.55),metrics('∞',size*.55),size)
        text(x,y,'∫',size*1.35);text(x+dx,y+uy,'∞',size*.55);text(x+dx,y+ly,'−∞',size*.55)
        x+=bounds[0]
        x+=text(x,y,' dx ',size)
        x+=conjugate(x,y,'Ψ',size)
        text(x,y,'xΨ =',size)
        draw.text((30,610),'Native U+0302 hats / exact glyph outlines / original advances',font=label,fill='#345')
        # Draw the isolated mark directly, without dotted-circle insertion.
        mark=native.font.getGlyphID(native.font.getBestCmap()[0x302])
        native.shapes['\u0302']=[(mark,0,0,0)]
        x=45;y=755;size=74
        for base in ('x','p','H','A','B','ψ'):
            dx,dy,measured=layout.hat_geometry(base,metrics(base,size),size)
            text(x,y,base,size);text(x+dx,y+dy,'\u0302',size)
            x+=measured[0]+55
        draw.text((30,835),'Native arrows / base, scripts and optical clearance',font=label,fill='#345')
        x=45;y=965;size=74
        for base in ('E','k','r','p','j','S'):
            dx,dy,ratio,measured=layout.vector_geometry(base,metrics(base,size),size)
            text(x,y,base,size);text(x+dx,y+dy,'→',size*ratio)
            x+=measured[0]+55
        draw.text((30,1030),'Native radical / hook retained, stem and roof extended',font=label,fill='#345')
        class RasterOutline(BasePen):
            def _moveTo(self,p): self.points=[p]
            def _lineTo(self,p): self.points.append(p)
            def _curveToOne(self,p1,p2,p3):
                p0=self.points[-1]
                for k in range(1,33):
                    t=k/32;u=1-t
                    self.points.append(tuple(u**3*p0[i]+3*u*u*t*p1[i]+3*u*t*t*p2[i]+t**3*p3[i] for i in (0,1)))
            def _closePath(self): draw.polygon([(xx+x,yy+y) for xx,yy in self.points],fill='#150592')
        x=50;y=1210;size=74
        commands,off,_=layout.radical_geometry(metrics('2α',size),size)
        replayRecording(commands,RasterOutline(None));text(x+off,y,'2α',size)
        x=350
        numerator,denominator=metrics('π',size*.85),metrics('α',size*.85)
        content=layout.fraction_metrics(numerator,denominator,size)
        commands,off,_=layout.radical_geometry(content,size)
        replayRecording(commands,RasterOutline(None))
        axis=layout.fraction_axis(size);w=content[0]
        ox,oy=x,y;edge=size*.04;x+=off+edge;y-=axis
        replayRecording(layout.rule_outline(w-2*edge,size),RasterOutline(None));x,y=ox,oy
        text(x+off+(w-numerator[0])/2,y-axis-layout.numerator_gap(size)-numerator[2],'π',size*.85)
        text(x+off+(w-denominator[0])/2,y-axis+3+denominator[1],'α',size*.85)
        draw.text((30,1370),'Relation spacing / =  <  >  ≈  ∼  ≪  ≫  ∝  ⇒',font=label,fill='#345')
        x=45;y=1460;size=42
        for value in ('x=y','x<y','x≈y','x∼y','x≫y','x⇒y'):
            for char,(left,right) in zip(value,layout.relation_spacing(value,size)):
                x+=left;x+=text(x,y,char,size);x+=right
            x+=35
        draw.text((30,1530),'Existing spaces count toward the gap; font metrics stay unchanged.',font=label,fill='#345')
        draw.text((30,1600),'Short native minus / pressure-shaped fraction / closer numerator',font=label,fill='#345')
        size=74;x=45;y=1750
        x+=text(x,y,'=',size)+25
        ox,oy=x,y;x+=45*layout.scale(size);y-=layout.fraction_axis(size)
        replayRecording(layout.rule_outline(247*layout.scale(size),size),RasterOutline(None))
        x,y=ox+layout.math_advance('−',size)+25,oy
        text(x,y,'+',size)
        x=350
        numerator,denominator=metrics('ℏ',size*.85),metrics('2',size*.85)
        w,_,_=layout.fraction_metrics(numerator,denominator,size);axis=layout.fraction_axis(size)
        ox,oy=x,y;edge=size*.04;x+=edge;y-=axis
        replayRecording(layout.rule_outline(w-2*edge,size),RasterOutline(None));x,y=ox,oy
        text(x+(w-numerator[0])/2,y-axis-layout.numerator_gap(size)-numerator[2],'ℏ',size*.85)
        text(x+(w-denominator[0])/2,y-axis+3+denominator[1],'2',size*.85)
        image.save(ROOT/'tools/font/proofs/quanfangwei-note-operators.png')
    print('PASS: shared module proof rendered from current native font')


if __name__=='__main__':main()
