#!/usr/bin/env python3
"""Render the requested turned h in the actual release font."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2]
FONT=ROOT/'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
image=Image.new('RGB',(1200,500),'#fffdf8');draw=ImageDraw.Draw(image)
draw.text((30,10),'1.043 - native h / turned h',font=ImageFont.truetype(str(FONT),32),fill='#52636d')
draw.text((30,55),'h    ɥ    u    y',font=ImageFont.truetype(str(FONT),220),fill='#182b35')
draw.text((30,315),'3. [ɥ]     [ɥi]     [ɥɛ]',font=ImageFont.truetype(str(FONT),100),fill='#203e68')
image.save(ROOT/'tools/font/proofs/quanfangwei-turned-h.png')
