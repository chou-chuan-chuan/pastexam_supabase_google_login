#!/usr/bin/env python3
"""Same-size source / initial IPA / native-style refinement comparison."""
import hashlib
from io import BytesIO
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
REL='assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
INITIAL='67dbcd6ebb14ce2c3aa69610dc86c9f09ba71b57'
INITIAL_SHA='90c121d22a3a80282496ff11c13e1e13f9469dc7686e4259bdbbc5ff0ef1b339'
BASE='def988885120a7921c940073ee1bd2454ecdeb92'
BASE_SHA='77f3b2578241b14901e588b5a5b8b18f2550e1d194fad9ea9a0af136da32b103'


def main():
    raw=[]
    for commit,digest in [(BASE,BASE_SHA),(INITIAL,INITIAL_SHA)]:
        data=subprocess.check_output(['git','show',f'{commit}:{REL}'],cwd=ROOT)
        assert hashlib.sha256(data).hexdigest()==digest
        raw.append(data)
    raw.append((ROOT/REL).read_bytes())
    fonts=[ImageFont.truetype(BytesIO(data),128) for data in raw]
    label=ImageFont.truetype(str(ROOT/REL),30)
    im=Image.new('RGB',(1600,1300),'#fffdf8');draw=ImageDraw.Draw(im)
    rows=[('Source Latin - unchanged',0,'a e c o u y g n m l f j R ?'),
          ('Previous 1.038 - same 128 px size',1,'ɛ ɪ ɔ ʊ ʏ ø ə ɐ ɡ'),
          ('',1,'ʃ ʒ ŋ ʁ ʔ ˈ ˌ ː n̩ i̯'),
          ('1.039 - smaller length mark',2,'ɛ ɪ ɔ ʊ ʏ ø ə ɐ ɡ'),
          ('',2,'ʃ ʒ ŋ ʁ ʔ ˈ ˌ ː n̩ i̯'),
          ('Context - native QFW only',2,'ˈʃpʁaːxə ˈmʏtɐ ˈzɔmɐ aɪ̯')]
    for i,(title,index,text) in enumerate(rows):
        y=20+i*210
        draw.text((40,y),title,font=label,fill='#52636d')
        draw.text((40,y+25),text,font=fonts[index],fill='#141820')
    im.save(ROOT/'tools/font/proofs/quanfangwei-german-ipa-style.png')
    print('PASS: source / initial / refined style comparison rendered at the same size')


if __name__=='__main__':main()
