#!/usr/bin/env python3
"""Compare unchanged low quotes and matched upper quotes at equal text sizes."""
from io import BytesIO
from pathlib import Path
import hashlib
import subprocess
from PIL import Image, ImageDraw, ImageFont
from verify_german_quotes import PREVIOUS_COMMIT,PREVIOUS_SHA
ROOT=Path(__file__).resolve().parents[2]
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'

def main():
    old=subprocess.check_output(['git','show',f'{PREVIOUS_COMMIT}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(old).hexdigest()==PREVIOUS_SHA
    new=(ROOT/REL).read_bytes()
    im=Image.new('RGB',(1250,730),'#fffdf8');d=ImageDraw.Draw(im)
    label=ImageFont.truetype(BytesIO(new),30)
    for y,title,data in [(15,'1.040 - before',old),(370,'1.041 - smaller upper quote, matching strokes',new)]:
        d.text((30,y),title,font=label,fill='#52636d')
        d.text((30,y+35),'„Aa“    „ü“    “Aa”',font=ImageFont.truetype(BytesIO(data),140),fill='#182b35')
        d.text((30,y+225),'„Come and rock me Amadeus“',font=ImageFont.truetype(BytesIO(data),65),fill='#182b35')
    im.save(ROOT/'tools/font/proofs/quanfangwei-german-quotes.png')

if __name__=='__main__':main()
