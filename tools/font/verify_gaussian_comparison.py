#!/usr/bin/env python3
"""Verify the paired Fourier-density widths and their plotted arrow endpoints."""
import math
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
