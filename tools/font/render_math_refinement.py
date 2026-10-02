#!/usr/bin/env python3
"""Source/old/new weight comparison plus actual HarfBuzz hats and fractions."""
from pathlib import Path
import tempfile
import subprocess
import json
from PIL import Image,ImageDraw,ImageFont
from math_layout import MathLayout,row

ROOT=Path(__file__).resolve().parents[2]
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
BASE='ca34467431ddc05e15368c244d1128687a074605'
OUT=ROOT/'tools/font/proofs'
HAT_SAMPLES=('x̂  p̂  Ĥ  L̂  ψ̂  φ̂  ρ̂','(x̂²p̂ + 2x̂p̂x̂ + p̂x̂²) / 4','â ê î ô û   â ê î ô û')


def check_fraction_layout(layout):
    """Tall ink and descenders must not pull fraction rules off the equals axis."""
    cases=[]
    for numerator,denominator in (
        (layout.text('x'),layout.text('y')),
        (layout.text('d⟨x⟩'),layout.text('dt')),
        (row(layout.text('dx'),layout.sub('c')),layout.text('dt')),
        (layout.text('ψ̂'),layout.text('ρ')),
    ):
        fraction=layout.fraction(numerator,denominator)
        assert len(fraction.rules)==1
        left,axis,right,thickness=fraction.rules[0]
        assert axis==330 and thickness==36 and right>left
        # Read each placed run's shaped ink instead of relying on Box bounds.
        numerator_bottom=min(layout.text(text).bottom*scale+y
            for text,x,y,scale in fraction.runs[:len(numerator.runs)])
        denominator_top=max(layout.text(text).top*scale+y
            for text,x,y,scale in fraction.runs[len(numerator.runs):])
        ngap=numerator_bottom-(axis+thickness/2)
        dgap=axis-thickness/2-denominator_top
        assert ngap>=72-1e-6 and dgap>=72-1e-6
        cases.append(dict(numerator=[r[0] for r in numerator.runs],
            denominator=[r[0] for r in denominator.runs],axis=axis,
            numerator_ink_gap=ngap,denominator_ink_gap=dgap))
    return cases


def main():
    with tempfile.TemporaryDirectory() as temp:
        oldpath=Path(temp)/'old.ttf';oldpath.write_bytes(subprocess.check_output(['git','show',f'{BASE}:{REL}'],cwd=ROOT))
        old=MathLayout(oldpath,temp);new=MathLayout(ROOT/REL,temp)
        regression=check_fraction_layout(new)
        label=ImageFont.truetype(str(ROOT/REL),25)
        image=Image.new('RGB',(1600,1250),'#fffdf8');draw=ImageDraw.Draw(image)
        draw.text((30,20),'QuanFangwei 1.034 / native weights / actual shaped hats / MATH fraction axis',font=label,fill='#345')
        y=110
        for size in (32,64,120):
            for caption,font in [('1.033',old),('1.034',new)]:
                draw.text((30,y-size*.5),f'{caption} / {size}px',font=label,fill='#567')
                font.draw(draw,font.text('∑ ∇ ∏   = x p H ∫   Σ Δ Π'),250,y,size)
                y+=size+20
        for sample in HAT_SAMPLES:
            new.draw(draw,new.text(sample),40,y,64);y+=95
        # Exact screenshot structure, with c as a true subscript and a fixed axis.
        numerator=row(new.text('dx'),new.sub('c'))
        left=row(new.text('p'),new.sub('c'),new.text(' = m '),new.fraction(numerator,new.text('dt')))
        right=row(new.text(' ⇒ ⟨p⟩ = m '),new.fraction(new.text('d⟨x⟩'),new.text('dt')))
        formula=row(left,right)
        y+=50;size=74
        axis_y=y-new.constants.AxisHeight.Value*size/1024
        draw.line((30,axis_y,1520,axis_y),fill='#d6e0e4')
        new.draw(draw,formula,40,y,size)
        draw.text((30,y+85),'Fraction rules and = share y=330; independent numerator/denominator ink gaps.',font=label,fill='#567')
        OUT.mkdir(exist_ok=True);image.save(OUT/'quanfangwei-math-refinement.png')
        metrics=dict(axis=new.constants.AxisHeight.Value,rule_thickness=new.constants.FractionRuleThickness.Value,
          fraction_rules=formula.rules,formula_bounds=[formula.bottom,formula.top],hat_samples=list(HAT_SAMPLES),
          fraction_regression=regression)
        (ROOT/'tools/font/reports/math-layout-proof.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
    print('PASS: shaped hats and both fraction rules rendered from current TTF; no fallback')

if __name__=='__main__':main()
