#!/usr/bin/env python3
"""Compare turned a with unchanged e/schwa/a at matching sizes."""
from io import BytesIO
from pathlib import Path
import hashlib
import subprocess
from PIL import Image, ImageDraw, ImageFont
from verify_turned_a import PREVIOUS_COMMIT, PREVIOUS_SHA
ROOT=Path(__file__).resolve().parents[2]
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'

def main():
    old=subprocess.check_output(['git','show',f'{PREVIOUS_COMMIT}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(old).hexdigest()==PREVIOUS_SHA
    new=(ROOT/REL).read_bytes()
    im=Image.new('RGB',(1250,700),'#fffdf8');d=ImageDraw.Draw(im)
    label=ImageFont.truetype(BytesIO(new),30)
    for y,title,data in [(10,'1.041 - before',old),(350,'1.042 - native schwa / turned a',new)]:
        d.text((30,y),title,font=label,fill='#52636d')
        d.text((30,y+30),'e    ə    ɐ    a',font=ImageFont.truetype(BytesIO(data),210),fill='#182b35')
        d.text((30,y+225),'ˈmʏtɐ    ˈzɔmɐ    ˈbɛsɐ',font=ImageFont.truetype(BytesIO(data),92),fill='#182b35')
    im.save(ROOT/'tools/font/proofs/quanfangwei-turned-a.png')

if __name__=='__main__':main()
