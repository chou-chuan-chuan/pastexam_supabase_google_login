#!/usr/bin/env python3
"""Render the 1.044 inverted-exclamation review proof."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
OUTPUT = ROOT / "tools/font/proofs/quanfangwei-exclamdown.png"

image = Image.new("RGB", (1440, 860), "#fffdf8")
draw = ImageDraw.Draw(image)
small = ImageFont.truetype(str(FONT), 34)
large = ImageFont.truetype(str(FONT), 230)
sentence = ImageFont.truetype(str(FONT), 92)
medium = ImageFont.truetype(str(FONT), 58)

draw.text((42, 30), "荃方位補寫體 1.044 · U+00A1 INVERTED EXCLAMATION MARK", font=small, fill="#52636d")
draw.text((55, 95), "!     ¡     ?     ¿", font=large, fill="#182b35")
draw.line((42, 370, 1398, 370), fill="#d7d1c7", width=2)
draw.text((42, 405), "¡Hola!  ¡Buenos días!  ¿Qué tal?", font=sentence, fill="#203e68")
draw.text((42, 545), "16 px   ¡Hola!   !¡   ?¿", font=ImageFont.truetype(str(FONT), 16), fill="#29343a")
draw.text((42, 590), "24 px   ¡Hola!   !¡   ?¿", font=ImageFont.truetype(str(FONT), 24), fill="#29343a")
draw.text((42, 650), "32 px   ¡Hola!   !¡   ?¿", font=ImageFont.truetype(str(FONT), 32), fill="#29343a")
draw.text((42, 725), "來源 !：215 advance · 新增 ¡：215 advance · 無外部字型輪廓", font=medium, fill="#52636d")
image.save(OUTPUT)
print(f"Rendered {OUTPUT.relative_to(ROOT)}")
