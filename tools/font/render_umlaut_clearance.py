#!/usr/bin/env python3
"""Compare 1.039 source dot placement with 1.040 at the same text size."""
from io import BytesIO
from pathlib import Path
import hashlib
import subprocess
from PIL import Image, ImageDraw, ImageFont
from verify_umlaut_clearance import PREVIOUS_COMMIT, PREVIOUS_SHA

ROOT=Path(__file__).resolve().parents[2]
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'

def main():
    before=subprocess.check_output(['git','show',f'{PREVIOUS_COMMIT}:{REL}'],cwd=ROOT)
    assert hashlib.sha256(before).hexdigest()==PREVIOUS_SHA
    after=(ROOT/REL).read_bytes()
    im=Image.new('RGB',(1120,660),'#fffdf8');d=ImageDraw.Draw(im)
    label=ImageFont.truetype(BytesIO(after),30)
    for y,title,data in [(20,'1.039 - before',before),(340,'1.040 - more space above U / u',after)]:
        d.text((35,y),title,font=label,fill='#52636d')
        d.text((35,y+40),'Ü ü   Ä Ö ä ö',font=ImageFont.truetype(BytesIO(data),144),fill='#182b35')
        d.text((35,y+220),'über   müde   Übung   für',font=ImageFont.truetype(BytesIO(data),62),fill='#182b35')
    im.save(ROOT/'tools/font/proofs/quanfangwei-umlaut-clearance.png')

if __name__=='__main__':main()
