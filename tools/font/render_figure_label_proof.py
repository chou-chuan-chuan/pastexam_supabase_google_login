#!/usr/bin/env python3
"""Small native-font before/after proof; no lecture content required."""
from pathlib import Path
import math
from PIL import Image,ImageDraw,ImageFont
from note_figure_layout import label_offset
ROOT=Path(__file__).resolve().parents[2]
FONT=ROOT/'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'

def main():
    image=Image.new('RGB',(1400,860),'white');draw=ImageDraw.Draw(image)
    font=ImageFont.truetype(str(FONT),30)
    for title,origin,adjust in [('Before',65,False),('After',475,True)]:
        draw.text((35,origin-40),title,font=font,fill='#345')
        w,h=661,155;baseline=h*.65
        def pt(x,y):return 35+x*2,origin+y*2
        draw.line([pt(0,baseline),pt(w-30,baseline)],fill='#5B308B',width=2)
        for phase,ink in [(0,'#5B308B'),(.7,'#150592')]:
            draw.line([pt((w-65)*i/360,baseline-h*.25*math.sin(i/360*6*math.pi-phase)) for i in range(361)],fill=ink,width=2)
        for y in range(25,int(baseline+25),6):
            draw.line([pt(w*.22,y),pt(w*.22,y+3)],fill='#5B308B',width=1)
        dx,dy=label_offset('wave_fixed',h) if adjust else (0,0)
        draw.text(pt(w*.24+dx,baseline+35+dy),'fixed x',font=font,fill='#5B308B',anchor='ls')
    image.save(ROOT/'tools/font/proofs/note-figure-label-clearance.png')

if __name__=='__main__':main()
