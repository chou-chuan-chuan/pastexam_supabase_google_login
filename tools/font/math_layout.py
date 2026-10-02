"""Small native-font proof layout: shaped text, scripts and axis-aligned fractions.

This is a calibration renderer, not a general TeX parser. Coordinates inside a
Box are font units with Y upward. Fraction placement reads the font's MATH table.
"""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.pens.boundsPen import BoundsPen
from PIL import ImageFont
import uharfbuzz as hb

@dataclass
class Box:
    width: float
    bottom: float
    top: float
    runs: list
    rules: list

    def moved(self,x=0,y=0,scale=1):
        return Box(self.width*scale,self.bottom*scale+y,self.top*scale+y,
            [(t,xx*scale+x,yy*scale+y,s*scale) for t,xx,yy,s in self.runs],
            [(a*scale+x,b*scale+y,c*scale+x,w*scale) for a,b,c,w in self.rules])


def row(*boxes,gap=0):
    x=0;runs=[];rules=[];lo=[];hi=[]
    for box in boxes:
        b=box.moved(x);runs+=b.runs;rules+=b.rules;lo.append(b.bottom);hi.append(b.top);x+=box.width+gap
    return Box(max(0,x-gap),min(lo,default=0),max(hi,default=0),runs,rules)


class MathLayout:
    def __init__(self,path,temp):
        self.raw=Path(path).read_bytes();self.font=TTFont(BytesIO(self.raw),recalcTimestamp=False)
        self.hb=hb.Font(hb.Face(self.raw));self.hb.scale=(1024,1024)
        self.glyphs=self.font.getGlyphSet();self.shapes={};self.faces={}
        self.constants=self.font['MATH'].table.MathConstants if 'MATH' in self.font else None
        # Only proof rasterization uses PUA addressing; production cmap is untouched.
        raster=TTFont(BytesIO(self.raw),recalcTimestamp=False)
        table=CmapSubtable.newSubtable(12);table.platformID=3;table.platEncID=10;table.language=0
        table.cmap={0xF0000+i:n for i,n in enumerate(raster.getGlyphOrder())}
        raster['cmap'].tables=[table]
        self.path=Path(temp)/(Path(path).stem+'-proof.ttf');raster.save(self.path)

    def shape(self,text):
        if text not in self.shapes:
            b=hb.Buffer();b.add_str(text);b.guess_segment_properties();hb.shape(self.hb,b)
            assert all(i.codepoint for i in b.glyph_infos),text
            self.shapes[text]=[(i.codepoint,p.x_advance,p.x_offset,p.y_offset) for i,p in zip(b.glyph_infos,b.glyph_positions)]
        return self.shapes[text]

    def text(self,text):
        x=0;bottom=[];top=[]
        for gid,adv,dx,dy in self.shape(text):
            pen=BoundsPen(self.glyphs);self.glyphs[self.font.getGlyphName(gid)].draw(pen)
            if pen.bounds:bottom.append(pen.bounds[1]+dy);top.append(pen.bounds[3]+dy)
            x+=adv
        return Box(x,min(bottom,default=0),max(top,default=0),[(text,0,0,1)],[])

    def sub(self,text):return self.text(text).moved(y=-180,scale=.7)
    def sup(self,text):return self.text(text).moved(y=380,scale=.7)

    def fraction(self,numerator,denominator):
        assert self.constants is not None,'Fractions require explicit MATH constants'
        c=self.constants;axis=c.AxisHeight.Value;thickness=c.FractionRuleThickness.Value
        ngap=c.FractionNumeratorGapMin.Value;dgap=c.FractionDenominatorGapMin.Value
        n=numerator.moved(scale=.85);d=denominator.moved(scale=.85)
        width=max(n.width,d.width)+100
        n=n.moved((width-n.width)/2,axis+thickness/2+ngap-n.bottom)
        d=d.moved((width-d.width)/2,axis-thickness/2-dgap-d.top)
        return Box(width,d.bottom,n.top,n.runs+d.runs,[(0,axis,width,thickness)])

    def draw(self,draw,box,x,baseline,size,fill='#151c2b'):
        factor=size/1024
        for text,rx,ry,scale in box.runs:
            pixels=max(1,round(size*scale))
            if pixels not in self.faces:self.faces[pixels]=ImageFont.truetype(str(self.path),pixels)
            cursor=x+rx*factor
            for gid,advance,dx,dy in self.shape(text):
                draw.text((cursor+dx*factor*scale,baseline-(ry+dy*scale)*factor),chr(0xF0000+gid),font=self.faces[pixels],anchor='ls',fill=fill)
                cursor+=advance*factor*scale
        for start,y,end,width in box.rules:
            draw.line((x+start*factor,baseline-y*factor,x+end*factor,baseline-y*factor),fill=fill,width=max(1,round(width*factor)))
