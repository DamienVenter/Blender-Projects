"""Side outlines of the red plastics from the calibrated left-profile blueprint (bike frame, mm).

Red pixels (decal holes filled) split into connected parts; the one big body (shroud, seat, side panel and rear fender
touch in the photo) is split along the seams read off the millimetre grids (gridview.py). Each part's outer contour
is extracted (contourpy), simplified and written as a polygon. Output: research/bike-outlines.json
{part: [[x_mm, z_mm], ...]}.
python3 outlines.py OUT.json [CHECK.jpg]
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
from blueprint import to_bike                 # noqa: E402

DS = 2                                        # work at half resolution (about 1.6 mm per pixel)
# seams (mm), read off the gridded crops: seat underside, rear fender underside, shroud/side-panel boundary
SEAT_BOTTOM = [(800, 1002), (700, 973), (550, 964), (300, 972), (100, 988), (40, 995)]
FENDER_LOWER = [(110, 925), (0, 938), (-100, 962), (-200, 980), (-320, 1000)]
SHROUD_REAR = [(860, 1010), (700, 930), (600, 885), (590, 850), (590, 600)]      # shroud is in front of this line
SEAT_X = (75, 800)
FENDER_X = 95


def interp(pts, q, axis=0):
    a = np.array(pts, float)
    order = np.argsort(a[:, axis])
    return np.interp(q, a[order, axis], a[order, 1 - axis])


def main():
    out_path = sys.argv[1]
    bp = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))["left"]
    im = Image.open(os.path.join(HERE, "..", "..", "reference", "crf250r-2026", bp["file"])).convert("RGB")
    im_s = im.resize((im.width // DS, im.height // DS), Image.BILINEAR)
    a = np.asarray(im_s).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 110) & (r - g > 55) & (r - b > 45)
    red = ndimage.binary_closing(red, iterations=2)
    red = ndimage.binary_fill_holes(red)
    red = ndimage.binary_opening(red, iterations=1)
    H, W = red.shape
    # bike coordinates of every pixel centre
    ii, jj = np.mgrid[0:H, 0:W]
    X = np.zeros((H, W)); Z = np.zeros((H, W))
    fa, ra = np.array(bp["front_axle_px"]), np.array(bp["rear_axle_px"])
    s = bp["mm_per_px"]
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]])
    if v[1] > 0:
        v = -v
    PX = np.stack([jj * DS + DS / 2, ii * DS + DS / 2], axis=-1) - ra
    X = PX @ u * s
    Z = PX @ v * s + bp["rear_tyre_od_mm"] / 2
    lab, n = ndimage.label(red)
    sizes = ndimage.sum(red, lab, range(1, n + 1))
    parts = {}
    for k in np.argsort(-sizes)[:4]:
        m = lab == k + 1
        cx, cz = X[m].mean(), Z[m].mean()
        if cx < 1100 and sizes[k] == sizes.max():
            body = m
        elif cx > 1300 and cz > 700:
            parts["front_fender"] = m
        elif cx > 1250 and cz < 700:
            parts["fork_guard"] = m
        elif cz > 950:
            parts["number_plate"] = m
    seat_b = interp(SEAT_BOTTOM, X)
    fend_l = interp(FENDER_LOWER, X)
    shroud_x = interp(SHROUD_REAR, Z, axis=1)
    seat = body & (Z > seat_b) & (X > SEAT_X[0]) & (X < SEAT_X[1])
    fender = body & ~seat & (X < FENDER_X) & (Z > fend_l)
    shroud = body & ~seat & (X > shroud_x)
    side = body & ~seat & ~fender & ~shroud
    parts.update(seat=seat, rear_fender=fender, shroud=shroud, side_panel=side)
    res = {}
    # top lines, column by column (the seat and fender tops: what the 3D lofts follow)
    for name, (x0, x1) in (("seat_top", (75, 800)), ("fender_top", (-305, 110)), ("body_top", (-305, 1160))):
        line = []
        for xq in np.arange(x0, x1 + 1, 10.0):
            col = body & (np.abs(X - xq) < 2.0)
            if col.any():
                line.append([round(float(xq), 1), round(float(Z[col].max()), 1)])
        res[name] = line
    parts["seat"] = body & (Z > seat_b - 3) & (X > SEAT_X[0]) & (X < SEAT_X[1])
    parts["side_panel"] = body & ~parts["seat"] & ~fender & ~shroud
    for name, m in parts.items():
        if name == "seat":
            continue                                  # the seat is lofted from seat_top
        m = ndimage.binary_opening(m, iterations=1)
        lab2, n2 = ndimage.label(m)
        if n2 > 1:                                                 # keep the main piece
            sz = ndimage.sum(m, lab2, range(1, n2 + 1))
            m = lab2 == (np.argmax(sz) + 1)
        gen = contourpy.contour_generator(z=m.astype(float))
        lines = gen.lines(0.5)
        c = max(lines, key=len)                                    # (col, row) in the reduced image
        pts = []
        for col, row in c:
            j, i = int(round(col)), int(round(row))
            i = min(max(i, 0), H - 1); j = min(max(j, 0), W - 1)
            pts.append((float(X[i, j]), float(Z[i, j])))
        pts = np.array(pts)
        # simplify: keep points at least 6 mm apart
        keep = [pts[0]]
        for p in pts[1:]:
            if np.hypot(*(p - keep[-1])) >= 6.0:
                keep.append(p)
        res[name] = [[round(x, 1), round(z, 1)] for x, z in keep]
        xs, zs = np.array(keep)[:, 0], np.array(keep)[:, 1]
        print(f"{name:13s} {len(keep):4d} pts  x {xs.min():7.0f}..{xs.max():6.0f}  z {zs.min():6.0f}..{zs.max():6.0f}")
    json.dump(res, open(out_path, "w"))
    if len(sys.argv) > 2:
        ov = im.copy()
        d = ImageDraw.Draw(ov)
        cols = {"seat": (0, 120, 255), "rear_fender": (0, 200, 0), "shroud": (255, 160, 0), "side_panel": (160, 0, 255),
                "front_fender": (0, 200, 200), "fork_guard": (255, 0, 200), "number_plate": (90, 90, 90)}
        for name, poly in res.items():
            if name.endswith("_top"):
                continue
            P = []
            for x, z in poly:
                d_ = u * (x / s) + v * ((z - bp["rear_tyre_od_mm"] / 2) / s) + ra
                P.append(tuple(d_))
            d.line(P + [P[0]], fill=cols.get(name, (0, 0, 0)), width=5)
        ov.resize((2000, 1125)).save(sys.argv[2], quality=88)


if __name__ == "__main__":
    main()
