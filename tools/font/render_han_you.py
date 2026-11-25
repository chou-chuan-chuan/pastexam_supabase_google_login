#!/usr/bin/env python3
"""Compare 1.045 and the current U+6182 at equal font sizes."""

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from verify_han_you import ROOT, REL, released_bytes


def main():
    before = released_bytes(".ttf")
    after = (ROOT / (REL + ".ttf")).read_bytes()
    proof = Image.new("RGB", (970, 510), "#fffdf8")
    draw = ImageDraw.Draw(proof)
    draw.line((485, 25, 485, 485), fill="#d8dfdd")
    for index, (version, data) in enumerate((("1.045", before), ("1.046", after))):
        x = 32 + 485 * index
        label = ImageFont.truetype(BytesIO(after), 36)
        draw.text((x, 12), version + (" 修正前" if index == 0 else " 修正後"),
                  font=label, fill="#435563")
        for size, y, sample in ((220, 50, "憂。"), (68, 319, "憂心、擔憂"),
                                (32, 418, "無憂無慮 ／ 憂い")):
            font = ImageFont.truetype(BytesIO(data), size)
            draw.text((x, y), sample, font=font, fill="#182b35")
    proof.save(ROOT / "tools/font/proofs/quanfangwei-han-you.png")


if __name__ == "__main__":
    main()
