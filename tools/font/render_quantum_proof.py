#!/usr/bin/env python3
"""Render calibration PNGs directly from the TTF, with no font fallback."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from quantum_symbols import GROUPS, CHARACTERS

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT/'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
OUT = ROOT/'tools/font/proofs'
SAMPLES = (
 'E = ℏω     p = ℏk     ΔxΔp ≥ ℏ/2',
 'iℏ ∂ψ/∂t = Hψ     ∂²ψ/∂x²     ∂ρ/∂t',
 'ψ(r,t) ∝ e^(i(k⋅r−ωt))',
 '⟨x⟩     ⟨p⟩     ⟨ψ|H|ψ⟩     ∇ψ     ∇⋅J',
 '∑ aₙ     ∏ ψᵢ     A ⇒ B     A ⇔ B     energy ↔ frequency',
 'a ≈ b     a ≃ b     a ∼ b     x ≤ y     x ≥ y',
 'x ≪ 1     E ≫ kT     a ≲ b     a ≳ b',
 'A†A     ψ″(x)     ℓ = 1     A ⊗ B     ‖ψ‖ = 1',
 '∬ f dxdy     ∭ ρ dxdydz     x = ±a     y = ∓b',
 '∀x ∈ ℝ     ∃z ∈ ℂ     x ∉ A     ψ ∈ ℋ',
 'ℒψ     ℱ(f)     ℜ(z)     ℑ(z)',
 'h / ℏ     ∂ / δ / d     l / ℓ / 1 / I     ν / v',
 'Σ / ∑     Π / ∏     · / ⋅     〈x〉 / ⟨x⟩     ∥ / ‖',
 'ε / ϵ     φ / ϕ     θ / ϑ     ρ / ϱ',
 'R / ℝ / ℜ     C / ℂ     H / ℋ     L / ℒ     F / ℱ     I / ℑ',
)
# Use only superscripts/subscripts actually present in the accepted font.
SAMPLES = tuple(s.replace('aₙ','a₁').replace('ψᵢ','ψ₁') for s in SAMPLES)


def validate_coverage():
    with TTFont(FONT) as font:
        missing = set(''.join(SAMPLES)+CHARACTERS)-{chr(cp) for cp in font.getBestCmap()}
        assert not missing, f'Native coverage missing: {missing}'


def main():
    validate_coverage();OUT.mkdir(exist_ok=True)
    im=Image.new('RGB',(1400,1400),'#fffdf8');d=ImageDraw.Draw(im)
    label=ImageFont.truetype(str(FONT),24);large=ImageFont.truetype(str(FONT),126)
    d.text((40,24),'QuanFangwei 1.033 / Quantum symbols / 45 native glyphs',font=label,fill='#223344')
    i=0
    for group,chars in GROUPS.items():
        for c in chars:
            x=35+(i%9)*151;y=100+(i//9)*250;i+=1
            d.rectangle((x,y,x+140,y+212),outline='#ddd8ce')
            d.line((x,y+156,x+140,y+156),fill='#aabccc')
            d.text((x+70,y+156),c,font=large,anchor='ms',fill='#141820')
            d.text((x+8,y+173),f'{group} U+{ord(c):04X}',font=label,fill='#345')
    im.save(OUT/'quanfangwei-quantum-glyphs.png')
    for size in (16,24,40,64):
        f=ImageFont.truetype(str(FONT),size)
        width=max(1200,round(max(f.getlength(s) for s in SAMPLES))+100)
        line=max(45,round(size*1.55));height=110+line*len(SAMPLES)
        im=Image.new('RGB',(width,height),'#fffdf8');d=ImageDraw.Draw(im)
        d.text((40,20),f'QuanFangwei 1.033 / native TTF only / {size} px',font=label,fill='#345')
        for i,s in enumerate(SAMPLES):
            y=100+line*i
            d.line((40,y,width-40,y),fill='#e0e6e9')
            d.text((40,y),s,font=f,anchor='ls',fill='#141820')
        im.save(OUT/f'quanfangwei-quantum-context-{size}.png')
    print('PASS: 45 labeled glyphs and all context samples rendered with native TTF; 16/24/40/64 px')

if __name__=='__main__':main()
