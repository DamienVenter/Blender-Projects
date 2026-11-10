"""Crop of a studio photo with a pixel grid (full-resolution pixel coordinates labelled), for reading features that
are then converted to 3D with cams.CAMS[view].on_plane.  python3 pxgrid.py VIEW U0 V0 U1 V1 STEP OUT.jpg [WIDTH]"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams
view, u0, v0, u1, v1, step, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
width = int(sys.argv[8]) if len(sys.argv) > 8 else 1800
im = Image.open(os.path.join(HERE, "..", "..", "reference", "crf250r-2026", cams.FILES[view])).convert("RGB")
crop = im.crop((u0, v0, u1, v1))
k = width / crop.width
crop = crop.resize((width, int(crop.height * k)), Image.LANCZOS)
d = ImageDraw.Draw(crop, "RGBA")
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 14)
for u in range((u0 // step + 1) * step, u1, step):
    x = (u - u0) * k
    d.line([(x, 0), (x, crop.height)], fill=(0, 120, 255, 90))
    d.text((x + 2, 2), str(u), fill=(0, 70, 200, 255), font=font)
for v in range((v0 // step + 1) * step, v1, step):
    y = (v - v0) * k
    d.line([(0, y), (crop.width, y)], fill=(0, 120, 255, 90))
    d.text((2, y + 1), str(v), fill=(0, 70, 200, 255), font=font)
crop.save(out, quality=90)
print(out, crop.size)
