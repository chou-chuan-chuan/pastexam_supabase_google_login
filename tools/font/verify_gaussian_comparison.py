#!/usr/bin/env python3
"""Verify the paired Fourier-density widths and their plotted arrow endpoints."""
import math
import cmath
from note_figure_layout import gaussian_comparison_panels, spectrum_note_frame

for alpha in (.25, 1, 4):
    dx=2*math.sqrt(2*alpha)
    dk=2/math.sqrt(2*alpha)
    assert math.isclose(math.exp(-(dx/2)**2/(2*alpha)),1/math.e)
    assert math.isclose(math.exp(-2*alpha*(dk/2)**2),1/math.e)
    assert math.isclose(dx*dk,4)
    sigma_k=1/(2*math.sqrt(alpha))
    assert math.isclose(dk,2*math.sqrt(2)*sigma_k)

for x,y,w in ((0,0,661),(47,1358,661),(0,0,500)):
    panels=gaussian_comparison_panels(x,y,w)
    assert panels[0]['left']+panels[0]['span']<panels[1]['left']
    assert panels[0]['height']==panels[1]['height']
    nx,ny,nw,nh=spectrum_note_frame(x,y,w)
    assert x<=nx<nx+nw<=x+w
    for panel in panels:
        a,ay,b=panel['arrow']
        assert ny+nh<panel['baseline']-panel['height']-17
        for endpoint in (a,b):
            z=(endpoint-panel['center'])/(panel['sigma']*panel['span'])
            curve_y=panel['baseline']-panel['height']*math.exp(-z*z/2)
            assert math.isclose(curve_y,ay)
        assert panel['left']<a<b<panel['left']+panel['span']
print('PASS: Gaussian density widths, uncertainty-width convention, and 1/e arrow endpoints')

# Numerically check the added general identity with a real positive quadratic
# coefficient and complex linear/constant terms, including the Fourier case.
for a,b,c in ((.7,.3+.8j,.2-.1j),(2,-1.2j,.1),(.25,1.1,-.3+.5j)):
    extent=abs(b.real)/(2*a)+12/math.sqrt(a)
    n=8000;step=2*extent/n
    integrand=lambda y:cmath.exp(-a*y*y+b*y+c)
    observed=step/3*(integrand(-extent)+integrand(extent)+sum((4 if k%2 else 2)*integrand(-extent+k*step) for k in range(1,n)))
    expected=math.sqrt(math.pi/a)*cmath.exp(b*b/(4*a)+c)
    assert abs(observed-expected)<1e-9*max(1,abs(expected))
print('PASS: 3 general Gaussian integrals with complex linear and constant terms')
