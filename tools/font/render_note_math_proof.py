#!/usr/bin/env python3
"""Render the shared note geometry with native outlines at matching sizes."""
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont
from math_layout import MathLayout
from note_math_layout import NoteMathLayout

ROOT=Path(__file__).resolve().parents[2]
FONT=ROOT/'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'


def main():
    with tempfile.TemporaryDirectory() as temp:
        native=MathLayout(FONT,temp)
        layout=NoteMathLayout(native.font)
        image=Image.new('RGB',(1200,620),'#fffdf8');draw=ImageDraw.Draw(image)
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
        image.save(ROOT/'tools/font/proofs/quanfangwei-note-operators.png')
    print('PASS: shared module proof rendered from current native font')


if __name__=='__main__':main()
