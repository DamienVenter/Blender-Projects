"""Gridded crop of a calibrated blueprint, with a labelled bike-frame grid (mm), for reading outlines.
python3 gridview.py VIEW X0 X1 Z0 Z1 STEP OUT.jpg [WIDTH]   (bike mm; VIEW left|right)"""
import json, sys, numpy as np, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
view, x0, x1, z0, z1, step, out = sys.argv[1], *map(float, sys.argv[2:7]), sys.argv[7]
width = int(sys.argv[8]) if len(sys.argv) > 8 else 1800
bp = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))[view]
im = Image.open(os.path.join(HERE, "..", "..", "reference", "crf250r-2026", bp["file"])).convert("RGB")
fa, ra = np.array(bp["front_axle_px"]), np.array(bp["rear_axle_px"])
s = bp["mm_per_px"]
u = (fa - ra) / np.linalg.norm(fa - ra)
v = np.array([-u[1], u[0]]) if bp["front_side"] == "left" else np.array([u[1], -u[0]])
if v[1] > 0: v = -v
r0 = bp["rear_tyre_od_mm"] / 2
def px(x, z):
    return ra + u * (x / s) + v * ((z - r0) / s)
corners = np.array([px(x, z) for x in (x0, x1) for z in (z0, z1)])
L, T = corners.min(axis=0); R, B = corners.max(axis=0)
crop = im.crop((int(L), int(T), int(R), int(B)))
k = width / crop.width
crop = crop.resize((width, int(crop.height * k)), Image.LANCZOS)
d = ImageDraw.Draw(crop, "RGBA")
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 15)
for x in np.arange(np.ceil(x0 / step) * step, x1 + 1, step):
    p, q = (px(x, z0) - (L, T)) * k, (px(x, z1) - (L, T)) * k
    d.line([tuple(p), tuple(q)], fill=(0, 140, 255, 110), width=1)
    d.text((p[0] + 2, min(p[1], q[1]) + 2), f"{x:.0f}", fill=(0, 90, 220, 255), font=font)
for z in np.arange(np.ceil(z0 / step) * step, z1 + 1, step):
    p, q = (px(x0, z) - (L, T)) * k, (px(x1, z) - (L, T)) * k
    d.line([tuple(p), tuple(q)], fill=(0, 140, 255, 110), width=1)
    d.text((min(p[0], q[0]) + 2, p[1] + 1), f"{z:.0f}", fill=(0, 90, 220, 255), font=font)
crop.save(out, quality=90)
print(out, crop.size)
