"""Measurements of the plastics from Honda's top and front studio photos (pixels; converted to metres by the
builders through cams.CAMS[view].on_plane, because the conversion needs each feature's height or distance).

Writes research/bike-plastics.json:
  top             per image column u: rows of the red envelope (v_min = right side of the bike, v_max = left side),
                  of the seat (its cover is a lighter red: green channel above 45), and of the gap between the
                  shrouds at the tank
  front_plate_px  number plate outline in the front photo (polygon, px)
  front_plate_rt  the plate's top right corner in that photo: right edge per row, top row, inner column
Everything else read from the front and rear photos (shroud rims, fender, flap, fork guards, mudguard, the walls
under the tail) is quoted row by row in the builders' docstrings and can be reprinted with rowscan.py.

python3 measure.py OUT.json [CHECK.jpg]
"""
import json
import os
import sys

import contourpy
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams           # noqa: E402

REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")


def load(view):
    a = np.asarray(Image.open(os.path.join(REF, cams.FILES[view])).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 105) & (r - g > 55) & (r - b > 45)
    bg = (a.min(axis=2) > 222) & (a.max(axis=2) - a.min(axis=2) < 18)
    return a, red, bg


def contour(mask):
    gen = contourpy.contour_generator(z=mask.astype(float))
    c = max(gen.lines(0.5), key=len)
    keep = [c[0]]
    for p in c[1:]:
        if np.hypot(*(p - keep[-1])) >= 3.0:
            keep.append(p)
    return np.array(keep)


def main():
    out = {}
    # ---------------- top
    a, red, bg = load("top")
    seat = red & (a[..., 1] > 45) & (a[..., 0] > 200)
    seat = ndimage.binary_opening(seat, iterations=3)
    lab, n = ndimage.label(seat)
    seat = lab == (np.argmax(ndimage.sum(seat, lab, range(1, n + 1))) + 1)
    seat = ndimage.binary_fill_holes(ndimage.binary_closing(seat, iterations=4))
    redc = ndimage.binary_closing(red, iterations=2)
    top = []
    for u in range(940, 3196, 6):
        rows = np.nonzero(redc[:, u])[0]
        if len(rows) < 4:
            continue
        e = {"u": u, "red": [int(rows.min()), int(rows.max())]}
        srows = np.nonzero(seat[:, u])[0]
        if len(srows) > 10:
            e["seat"] = [int(srows.min()), int(srows.max())]
        # gap between the two shrouds around the centre line (tank, steering head)
        c = ~redc[1000:1250, u]
        if c[123 - 4:123 + 4].all():
            lo = 1123 - np.argmax(~c[:123][::-1])          # first red row above the centre
            hi = 1123 + np.argmax(~c[123:])
            e["gap"] = [int(lo), int(hi)]
        top.append(e)
    out["top"] = top
    # ---------------- front
    a, red, bg = load("front")
    m = red.copy()
    m[:299] = False; m[607:] = False; m[:, :1780] = False; m[:, 2222:] = False
    # the plate's raised centre panel is edged by bright creases: close them before taking the component, or only
    # the centre panel comes out
    m = ndimage.binary_closing(m, iterations=4)
    m[:299] = False; m[607:] = False
    lab, n = ndimage.label(m)
    k = lab[420, 1900]
    plate = ndimage.binary_fill_holes(lab == k)
    plate = ndimage.binary_opening(plate, iterations=2)
    out["front_plate_px"] = np.round(contour(plate), 1).tolist()
    # the plate's top right corner (the bike's left). The mask above stops at row 299, the top edge of the plate's
    # left half; on the right the red runs on above it beside the bar pad (rows 268..296: u 2125..2186, with a 5 px
    # dark gap to the pad at u 2119..2123), and the corner is square where the left one is cut off
    rt = {"left": 2124, "edge": []}
    v = 300
    while v > 200 and red[v, 2124:2200].sum() > 30:
        v -= 1
    rt["top"] = v + 1
    for vv in range(rt["top"], 352, 4):
        cols = np.nonzero(red[vv, 2100:2215])[0]
        rt["edge"].append([vv, int(2100 + cols.max())])
    out["front_plate_rt"] = rt
    json.dump(out, open(sys.argv[1], "w"))
    print("top columns", len(top), "| plate pts", len(out["front_plate_px"]))
    if len(sys.argv) > 2:
        im = Image.open(os.path.join(REF, cams.FILES["front"])).convert("RGB")
        d = ImageDraw.Draw(im)
        d.line([tuple(p) for p in out["front_plate_px"]] + [tuple(out["front_plate_px"][0])], fill=(0, 90, 255), width=4)
        im.crop((1600, 200, 2400, 1300)).save(sys.argv[2], quality=88)


if __name__ == "__main__":
    main()
