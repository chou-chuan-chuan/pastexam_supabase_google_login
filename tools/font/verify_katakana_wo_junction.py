#!/usr/bin/env python3
"""Verify the scoped Version 1.045 Katakana WO junction repair."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
import subprocess

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
REL = "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular"
PREVIOUS_COMMIT = "6cf7b42e031d7e85836156ff8eaefd21061b0435"
PREVIOUS_SHA256 = {
    ".ttf": "5e169fca032f5232204572c18fe0378c3c179fb04a516e8d189de94e7dbe899d",
    ".woff2": "06d842237db255af66d0f1f6dacc56c429fbc282518c5e41e18803732c3beb79",
}
TARGET = "uni30F2"


def released_bytes(extension: str) -> bytes:
    data = subprocess.check_output(
        ["git", "show", f"{PREVIOUS_COMMIT}:{REL}{extension}"], cwd=ROOT
    )
    assert hashlib.sha256(data).hexdigest() == PREVIOUS_SHA256[extension]
    return data


def bounds(font: TTFont, glyph_name: str) -> tuple[int, int, int, int]:
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    assert pen.bounds is not None
    return tuple(round(value) for value in pen.bounds)


def connected_components(font_bytes: bytes, size: int) -> int:
    font = ImageFont.truetype(BytesIO(font_bytes), size)
    image = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(image)
    draw.text((size // 4, size // 8), "ヲ", font=font, fill=255)
    pixels = image.load()
    active = {
        (x, y)
        for y in range(image.height)
        for x in range(image.width)
        if pixels[x, y] >= 24
    }
    components = 0
    while active:
        components += 1
        stack = [active.pop()]
        while stack:
            x, y = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    neighbor = (x + dx, y + dy)
                    if neighbor in active:
                        active.remove(neighbor)
                        stack.append(neighbor)
    return components


def verify(extension: str) -> None:
    old_raw = released_bytes(extension)
    new_raw = (ROOT / f"{REL}{extension}").read_bytes()
    old = TTFont(BytesIO(old_raw))
    new = TTFont(BytesIO(new_raw))

    assert old["name"].getDebugName(5) == "Version 1.044"
    assert new["name"].getDebugName(5) == "Version 1.045"
    assert abs(new["head"].fontRevision - 1.045) < 1 / 65536
    assert new.getGlyphOrder() == old.getGlyphOrder()
    assert new.getBestCmap() == old.getBestCmap()
    assert new.getBestCmap()[0x30F2] == TARGET
    assert new.getBestCmap()[0x30FA] == "uni30FA"

    changed = []
    for glyph_name in old.getGlyphOrder():
        if old["glyf"][glyph_name].compile(old["glyf"]) != new["glyf"][glyph_name].compile(new["glyf"]):
            changed.append(glyph_name)
        assert old["hmtx"][glyph_name] == new["hmtx"][glyph_name], glyph_name
        if "vmtx" in old:
            assert old["vmtx"][glyph_name] == new["vmtx"][glyph_name], glyph_name
    assert changed == [TARGET, "uni30FA"], changed

    assert old["hmtx"][TARGET] == new["hmtx"][TARGET] == (960, bounds(new, TARGET)[0])
    old_vo = old["glyf"]["uni30FA"]
    new_vo = new["glyf"]["uni30FA"]
    assert [(part.glyphName, part.x, part.y, part.flags) for part in old_vo.components] == [
        (part.glyphName, part.x, part.y, part.flags) for part in new_vo.components
    ]
    assert bounds(old, TARGET) == (223, -20, 749, 544)
    assert bounds(new, TARGET) == (223, -21, 749, 544)

    for tag in ("cmap", "GDEF", "GSUB", "GPOS", "MATH", "OS/2", "hhea", "hmtx", "vhea", "vmtx", "kern", "post"):
        if tag in old:
            assert old[tag].compile(old) == new[tag].compile(new), tag

    if extension == ".ttf":
        assert connected_components(old_raw, 192) >= 2
        for size in (16, 24, 32, 64, 192):
            assert connected_components(new_raw, size) == 1, size


def main() -> None:
    for extension in (".ttf", ".woff2"):
        verify(extension)
    print("PASS: ヲ has one connected ink body at 16/24/32/64/192 px; only uni30F2 outline and uni30FA inherited bounds changed, while all metrics, mappings, layout tables, component offsets, and other glyphs are preserved")


if __name__ == "__main__":
    main()
