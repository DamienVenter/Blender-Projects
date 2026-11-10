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


def one_view(view, res, check):
    bp = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))[view]
    sfx = "" if view == "left" else "_R"
    im = Image.open(os.path.join(HERE, "..", "..", "reference", "crf250r-2026", bp["file"])).convert("RGB")
    im_s = im.resize((im.width // DS, im.height // DS), Image.BILINEAR)
    a = np.asarray(im_s).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 110) & (r - g > 55) & (r - b > 45)
    # the stock decal's navy panel sits on the shroud and runs to its edge: counted as plastic, or the shroud's
    # outline gets a notch there (it showed as a slot in the render)
    red |= (b > 80) & (b - r > 40) & (b - g > 30)
    bright = red.copy()
    red = ndimage.binary_closing(red, iterations=2)
    red = ndimage.binary_fill_holes(red)
    red = ndimage.binary_opening(red, iterations=1)
    H, W = red.shape
    ii, jj = np.mgrid[0:H, 0:W]
    fa, ra = np.array(bp["front_axle_px"]), np.array(bp["rear_axle_px"])
    s = bp["mm_per_px"]
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]]) if bp["front_side"] == "left" else np.array([u[1], -u[0]])
    if v[1] > 0:
        v = -v
    PX = np.stack([jj * DS + DS / 2, ii * DS + DS / 2], axis=-1) - ra
    X = PX @ u * s
    Z = PX @ v * s + bp["rear_tyre_od_mm"] / 2
    # The shroud's leading edge is two layers: the outer skin stops 35 to 80 mm short of the front edge, and a
    # recessed inner wall, in shadow (dark red, r 80..160), runs on to the true front edge. The bright-red mask misses
    # the wall and leaves a slot in the outline: add the dark red there, and keep the skin's edge as its own line.
    # The zone stops 4 mm behind the fork tube's rear edge (tube axis through (1209.5, 800) at 26.40 deg, 25.5 mm
    # radius: parts.py): the gold tube carries dark red reflections of the plastics, which would join the shroud.
    tube_rear = 1209.5 - (Z - 800.0) * np.tan(np.radians(26.40)) - 25.5 / np.cos(np.radians(26.40)) - 4.0
    zone = (X > 930) & (X < np.minimum(tube_rear, 1200.0)) & (Z > 620) & (Z < 960)
    # red on the tube itself (reflections along its rear edge) is not plastic: without this the shroud's outline
    # grew a finger down the tube
    on_tube = (X > tube_rear + 2.0) & (X < tube_rear + 66.0) & (Z > 690) & (Z < 930)
    red &= ~on_tube
    bright &= ~on_tube
    dark = (r > 45) & (r - g > 35) & (r - b > 25) & ~bright & zone
    lit = (r > 165) & (r - g > 55) & (r - b > 45)                 # skin in the light
    shade = (r > 45) & (r - g > 35) & (r - b > 25) & ~lit        # the recessed wall
    skin = []
    for i in range(0, H, 2):
        cols = np.nonzero(zone[i] & (Z[i] > 680) & (Z[i] < 885))[0]
        if len(cols) < 20:
            continue
        if bp["front_side"] != "left":
            cols = cols[::-1]                              # walk from the front edge rearward
        line = np.where(lit[i, cols], 2, np.where(shade[i, cols], 1, 0))
        j = 0
        while j < len(line):                              # first shaded run of 8+ px (13 mm): the wall
            if line[j] == 1:
                k = j
                while k < len(line) and line[k] == 1:
                    k += 1
                if k - j >= 8:
                    kk = cols[min(k, len(cols) - 1)]
                    skin.append([round(float(X[i, kk]), 1), round(float(Z[i, kk]), 1)])
                    break
                j = k
            else:
                j += 1
    res["shroud_skin" + sfx] = skin
    red = ndimage.binary_fill_holes(ndimage.binary_closing(red | dark, iterations=2))
    # near its lower tip the wall and the skin part by a black gap 10 to 20 mm wide: closed here, so the shroud's
    # front is one shape (as fingers, its rolled edge came out as a comb). A simplification of the real part.
    closed = ndimage.binary_closing(red & zone, iterations=12)
    red |= closed & zone
    red = ndimage.binary_fill_holes(red)
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
    # everything red behind FENDER_X is the fender, flanks included (cut along the hand-read seam FENDER_LOWER, the
    # lower flank went to the side panel as a thin tongue that crumpled; the blade's edges now reach the true lower
    # boundary)
    fender = body & ~seat & (X < FENDER_X)
    shroud = body & ~seat & (X > shroud_x)
    parts.update(rear_fender=fender, shroud=shroud)
    # top lines, column by column (the seat and fender tops: what the 3D lofts follow)
    for name, (x0, x1) in (("seat_top", (75, 800)), ("fender_top", (-305, 110)), ("body_top", (-305, 1160)),
                           ("front_fender_top", (1215, 1712))):
        src = parts["front_fender"] if name == "front_fender_top" else body
        line = []
        for xq in np.arange(x0, x1 + 1, 10.0):
            col = src & (np.abs(X - xq) < 2.0)
            if col.any():
                line.append([round(float(xq), 1), round(float(Z[col].max()), 1)])
        res[name + sfx] = line
    line = []
    for xq in np.arange(1215, 1712, 10.0):                       # the front fender's lower edge
        col = parts["front_fender"] & (np.abs(X - xq) < 2.0)
        if col.any():
            line.append([round(float(xq), 1), round(float(Z[col].min()), 1)])
    res["front_fender_bottom" + sfx] = line
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
        c = max(gen.lines(0.5), key=len)                           # (col, row) in the reduced image
        pts = []
        for col, row in c:
            j, i = int(round(col)), int(round(row))
            i = min(max(i, 0), H - 1); j = min(max(j, 0), W - 1)
            pts.append((float(X[i, j]), float(Z[i, j])))
        pts = np.array(pts)
        keep = [pts[0]]
        for p in pts[1:]:
            if np.hypot(*(p - keep[-1])) >= 6.0:
                keep.append(p)
        res[name + sfx] = [[round(x, 1), round(z, 1)] for x, z in keep]
        xs, zs = np.array(keep)[:, 0], np.array(keep)[:, 1]
        print(f"{name + sfx:15s} {len(keep):4d} pts  x {xs.min():7.0f}..{xs.max():6.0f}  z {zs.min():6.0f}..{zs.max():6.0f}")
    return im, bp, u, v, ra, s


def main():
    out_path = sys.argv[1]
    res = {}
    im, bp, u, v, ra, s = one_view("left", res, True)
    one_view("right", res, False)
    json.dump(res, open(out_path, "w"))
    if len(sys.argv) > 2:
        ov = im.copy()
        d = ImageDraw.Draw(ov)
        cols = {"seat": (0, 120, 255), "rear_fender": (0, 200, 0), "shroud": (255, 160, 0), "side_panel": (160, 0, 255),
                "front_fender": (0, 200, 200), "fork_guard": (255, 0, 200), "number_plate": (90, 90, 90)}
        for name, poly in res.items():
            if "_top" in name or "_bottom" in name or name.endswith("_R"):
                continue
            P = []
            for x, z in poly:
                d_ = u * (x / s) + v * ((z - bp["rear_tyre_od_mm"] / 2) / s) + ra
                P.append(tuple(d_))
            d.line(P + [P[0]], fill=cols.get(name, (0, 0, 0)), width=5)
        ov.resize((2000, 1125)).save(sys.argv[2], quality=88)


if __name__ == "__main__":
    main()
