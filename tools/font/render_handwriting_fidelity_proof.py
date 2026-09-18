#!/usr/bin/env python3
"""Compare the actual built TTF to each original photograph without axis warping."""

from __future__ import annotations

import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt

from kana_sources.maintainer_photo_sources import PHOTO_SOURCES

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
REFERENCES = ROOT / "tools/font/references"
PROOFS = ROOT / "tools/font/proofs"
# Immutable PR state rejected by the maintainer, not a moving origin/main.
BEFORE_REVISION = "a2a57059a4c1d9b9d8cbd15c5b6fe5003e58e1f8"


def before_font():
    return subprocess.check_output([
        "git", "-c", f"safe.directory={ROOT.as_posix()}", "show",
        f"{BEFORE_REVISION}:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf",
    ], cwd=ROOT)


def masks(character, old_bytes):
    source = PHOTO_SOURCES[character]
    zoom = 4
    crop = source.crop
    reference = Image.open(REFERENCES / source.reference).convert("L").crop(crop)
    reference = ImageOps.invert(reference).resize(
        (reference.width * zoom, reference.height * zoom), Image.Resampling.LANCZOS)
    current = Image.new("L", reference.size)
    x, y = source.to_source(crop[0], crop[1])
    font_size = round(1024 * zoom / source.scale)
    factor = font_size / 1024
    ImageDraw.Draw(current).text((-x * factor, (y - 145) * factor), character,
        font=ImageFont.truetype(str(FONT), font_size), fill=255, anchor="ls")

    # Previous shape is fitted with ONE uniform scale, never stretched to match.
    old_font = ImageFont.truetype(BytesIO(old_bytes), 1024)
    box = old_font.getbbox(character)
    previous = Image.new("L", (box[2] - box[0] + 4, box[3] - box[1] + 4))
    ImageDraw.Draw(previous).text((2 - box[0], 2 - box[1]), character, font=old_font, fill=255)
    previous = previous.crop(previous.getbbox())
    reference_box = reference.point(lambda value: 255 if value > 128 else 0).getbbox()
    width, height = reference_box[2] - reference_box[0], reference_box[3] - reference_box[1]
    fit = min(width / previous.width, height / previous.height)
    previous = previous.resize((round(previous.width * fit), round(previous.height * fit)), Image.Resampling.LANCZOS)
    old_mask = Image.new("L", reference.size)
    old_mask.paste(previous, (reference_box[0] + (width - previous.width) // 2,
                             reference_box[1] + (height - previous.height) // 2))
    return reference, old_mask, current


def measurements(reference, candidate):
    ref = np.asarray(reference) >= 128
    ink = np.asarray(candidate) >= 128
    overlap = float(np.count_nonzero(ref & ink) / np.count_nonzero(ref | ink))
    # Symmetric nearest-ink distance, expressed in the original photograph px.
    distance = float((distance_transform_edt(~ref)[ink].mean() +
                      distance_transform_edt(~ink)[ref].mean()) / 8)
    return {"ink_iou": round(overlap, 4), "mean_ink_distance_photo_px": round(distance, 4)}


def main():
    PROOFS.mkdir(exist_ok=True)
    old_bytes = before_font()
    image = Image.new("RGB", (1600, 2570), "#fffdf9")
    draw = ImageDraw.Draw(image)
    label = ImageFont.load_default(size=24)
    small = ImageFont.load_default(size=19)
    kana = ImageFont.truetype(str(FONT), 32)
    draw.text((30, 22), "Handwriting fidelity: original photo / previous PR / revised font / overlay", font=label, fill="#23202a")
    draw.text((30, 60), "Uniform scale only. Red = reference, blue = font, dark = overlap. Ink overlap is not a perceived-similarity score.", font=small, fill="#635966")
    for i, text in enumerate(("YOUR PHOTO", "PREVIOUS PR", "REVISED TTF", "PHOTO + TTF")):
        draw.text((35 + i * 395, 105), text, font=label, fill="#635966")
    report = {"before_revision": BEFORE_REVISION, "glyphs": {}}
    for row, character in enumerate("おあいうさきとり"):
        reference, previous, current = masks(character, old_bytes)
        old_score, new_score = measurements(reference, previous), measurements(reference, current)
        ref = np.asarray(reference, dtype=float) / 255
        ink = np.asarray(current, dtype=float) / 255
        overlay = np.stack([255 * (1 - ink * .85), 255 * (1 - np.maximum(ref, ink) * .85),
                            255 * (1 - ref * .85)], axis=2).astype("uint8")
        panels = [ImageOps.invert(reference).convert("RGB"), ImageOps.invert(previous).convert("RGB"),
                  ImageOps.invert(current).convert("RGB"), Image.fromarray(overlay)]
        y = 150 + row * 300
        draw.text((6, y + 110), character, font=kana, fill="#23202a")
        for column, panel in enumerate(panels):
            panel.thumbnail((320, 242), Image.Resampling.LANCZOS)
            x = 45 + column * 395
            image.paste(panel, (x + (330 - panel.width) // 2, y + (242 - panel.height) // 2))
        draw.text((445, y + 249), f"Overlap {old_score['ink_iou']:.1%}", font=small, fill="#635966")
        draw.text((840, y + 249), f"Overlap {new_score['ink_iou']:.1%}", font=small, fill="#635966")
        draw.text((1235, y + 249), f"Mean ink gap {new_score['mean_ink_distance_photo_px']:.2f}px", font=small, fill="#635966")
        draw.line((30, y + 290, 1570, y + 290), fill="#ddd5df")
        report["glyphs"][character] = {"previous": old_score, "revised": new_score,
            "reference": source_path(character), "uniform_scale": PHOTO_SOURCES[character].scale}
    image.save(PROOFS / "quanfangwei-handwriting-fidelity-proof.png")
    (PROOFS / "quanfangwei-handwriting-fidelity-metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def source_path(character):
    return "tools/font/references/" + PHOTO_SOURCES[character].reference


if __name__ == "__main__":
    main()
