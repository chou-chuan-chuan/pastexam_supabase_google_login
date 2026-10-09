#!/usr/bin/env python3
"""Render the released 1.038 and smaller 1.039 length mark at equal font sizes."""
from io import BytesIO
from pathlib import Path
import hashlib
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
REL = 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
BEFORE = '67dbcd6ebb14ce2c3aa69610dc86c9f09ba71b57'
SHA = '90c121d22a3a80282496ff11c13e1e13f9469dc7686e4259bdbbc5ff0ef1b339'

def main():
    old = subprocess.check_output(['git','show',f'{BEFORE}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(old).hexdigest() == SHA
    new = (ROOT/REL).read_bytes()
    image = Image.new('RGB',(1100,640),'#fffdf8')
    draw = ImageDraw.Draw(image)
    label = ImageFont.truetype(BytesIO(new),30)
    for y,title,data in [(24,'1.038 - before',old),(328,'1.039 - smaller, slimmer triangles',new)]:
        draw.text((40,y),title,font=label,fill='#52636d')
        draw.text((40,y+50),'aː   iː   uː   øː   :  ː',font=ImageFont.truetype(BytesIO(data),132),fill='#182b35')
        draw.text((40,y+205),'ˈʃpʁaːxə    øːl    ˈmuːtɐ',font=ImageFont.truetype(BytesIO(data),48),fill='#182b35')
    image.save(ROOT/'tools/font/proofs/quanfangwei-ipa-length.png')

if __name__ == '__main__':
    main()
