"""Calibrate Honda's studio TOP photo and draw a bike-frame grid on it (x forward mm, y left mm).

Scale and position from the extremes along the bike's centre line: the front tyre's leading point (x = front axle
+ front tyre radius) and the rear fender's tip (x from the profile blueprint). The bike points left in the photo.
python3 topview.py CALIB_OUT.json [GRID.jpg X0 X1 STEP]
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
FILE = "studio_top_honda-eu-25ym-475594_4000x2250.jpg"
X_FRONT_TIP = 1483.0 + 701.1 / 2        # front axle + front tyre radius (bike-blueprint.json, left view)
X_REAR_TIP = -303.0                     # rear fender tip in the left profile (comp 7 extent)

im = Image.open(os.path.join(REF, FILE)).convert("RGB")
a = np.asarray(im).astype(int)
bright = a.sum(axis=2) / 3
fg = bright < 200                                         # anything not white background
H, W = fg.shape
rows = np.nonzero(fg.any(axis=1))[0]
# centre line: the row band through the middle of the bike (front tyre and rear fender tip lie on it)
ys, xs = np.nonzero(fg)
yc = float(np.median(ys[(xs > np.percentile(xs, 40)) & (xs < np.percentile(xs, 60))]))
band = fg[int(yc) - 25:int(yc) + 25, :]
cols = np.nonzero(band.any(axis=0))[0]
x_front_px, x_rear_px = cols.min(), cols.max()
s = (X_FRONT_TIP - X_REAR_TIP) / (x_rear_px - x_front_px)     # mm per px
calib = {"file": FILE, "centre_row_px": yc, "front_tip_px": int(x_front_px), "rear_tip_px": int(x_rear_px),
         "mm_per_px": s, "x_front_tip_mm": X_FRONT_TIP, "x_rear_tip_mm": X_REAR_TIP}
json.dump(calib, open(sys.argv[1], "w"), indent=1)
print(json.dumps(calib))
if len(sys.argv) > 2:
    out, x0, x1, step = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    px = lambda x, y: (x_front_px + (X_FRONT_TIP - x) / s, yc - y / s)
    L, T = px(x1, 500); R, B = px(x0, -500)
    crop = im.crop((int(L), int(T), int(R), int(B)))
    k = 2000 / crop.width
    crop = crop.resize((2000, int(crop.height * k)), Image.LANCZOS)
    d = ImageDraw.Draw(crop, "RGBA")
    font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 15)
    for x in np.arange(np.ceil(x0 / step) * step, x1 + 1, step):
        p = (px(x, 0)[0] - L) * k
        d.line([(p, 0), (p, crop.height)], fill=(0, 140, 255, 100))
        d.text((p + 2, 2), f"{x:.0f}", fill=(0, 90, 220, 255), font=font)
    for y in np.arange(-500, 501, 25):
        q = (px(0, y)[1] - T) * k
        d.line([(0, q), (crop.width, q)], fill=(0, 140, 255, 100 if y % 100 else 200))
        d.text((2, q + 1), f"{y:.0f}", fill=(0, 90, 220, 255), font=font)
    crop.save(out, quality=90)
    print(out, crop.size)
