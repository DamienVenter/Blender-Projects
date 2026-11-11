"""Cameras of Honda's four three-quarter studio photos (lf34, lr34, rf34, rr34), fitted to the model.

python3 fit34.py PARTS.npz [views]      refits and writes research/bike-cameras-34.json (cams.py loads it)

The five main cameras (cams.py) were fitted to landmarks read in the photos; the model built through them now
overlaps those photos by 87 to 89 %. A three-quarter photo shows the same bike from a new angle, so its camera is
fitted to the MODEL: first to six landmarks read by eye (to start), then by maximising the overlap of the red
plastics and of the black parts (tyres, chain, lower panels) between the photo and the model drawn through the
camera. Seven unknowns: position (3), yaw, pitch, roll, focal length; principal point at the photo's centre, as for
the other five (same studio, same lens series).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.optimize import least_squares, minimize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams          # noqa: E402
import compare       # noqa: E402

REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
OUT = os.path.join(HERE, "..", "..", "research", "bike-cameras-34.json")
FILES = {"lf34": "studio_left-front-34_honda-eu-25ym-475601_4000x2250.jpg",
         "lr34": "studio_left-rear-34_honda-eu-25ym-475599_4000x2250.jpg",
         "rf34": "studio_right-front-34_honda-eu-25ym-475595_4000x2250.jpg",
         "rr34": "studio_right-rear-34_honda-eu-25ym-475597_4000x2250.jpg"}

# 3D landmarks, axle-line frame, read off the model (bike_v3, 2026-11-11) or the shared constants
L3 = {"bar_L": cams.BAR_END, "bar_R": (cams.BAR_END[0], -cams.BAR_END[1], cams.BAR_END[2]),
      "axle_L": (0.0, 0.136, cams.AXLE_Z), "axle_R": (0.0, -0.143, cams.AXLE_Z),
      "muffler_out": (-0.0196, -0.138, 0.845), "tail": (-0.3005, 0.0, 0.998), "nose": (1.7075, 0.0, 0.785)}
# their pixels, read by eye on 1600 px wide previews (x 2.5): good to about 5 px, only a start for the overlap fit
L2 = {"lr34": {"bar_L": (1475, 338), "bar_R": (2170, 308), "axle_L": (2707, 1600), "muffler_out": (2912, 868),
               "tail": (3170, 680), "nose": (1143, 795)},
      "rr34": {"bar_L": (1825, 305), "bar_R": (2525, 340), "axle_R": (1275, 1600), "muffler_out": (1300, 888),
               "tail": (833, 683), "nose": (2855, 795)},
      "lf34": {"bar_L": (2195, 355), "bar_R": (1525, 318), "axle_L": (2770, 1370), "tail": (2943, 545),
               "nose": (975, 963)},
      "rf34": {"bar_L": (2488, 318), "bar_R": (1800, 355), "axle_R": (1200, 1363), "tail": (1058, 545),
               "nose": (3020, 963)}}
START = {"lr34": (-3.5, 3.6, 1.3), "rr34": (-3.5, -3.6, 1.3), "lf34": (4.5, 3.6, 1.3), "rf34": (4.5, -3.6, 1.3)}


def make(p):
    """p = (x, y, z, yaw, pitch, roll, f): camera at (x, y, z) looking along yaw (from +x, about z) and pitch (down)."""
    x, y, z, yaw, pitch, roll, f = p
    F = (math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch))
    return cams.Cam((x, y, z), F, (0, 0, 1.0), f, roll)


def start(view):
    C = np.array(START[view])
    t = np.array([0.75, 0.0, 0.62])
    d = t - C
    return [*C, math.atan2(d[1], d[0]), -math.atan2(d[2], math.hypot(d[0], d[1])), 0.0, 6000.0]


def fit_landmarks(view):
    names = list(L2[view])
    P = np.array([L3[n] for n in names])
    uv = np.array([L2[view][n] for n in names], float)

    def res(p):
        return (make(p).project(P) - uv).ravel()
    sol = least_squares(res, start(view), x_scale=[1, 1, 0.3, 0.1, 0.05, 0.02, 1000])
    return sol.x, sol.fun.reshape(-1, 2)


def photo_masks(view, scale):
    im = Image.open(os.path.join(REF, FILES[view])).convert("RGB")
    im = np.asarray(im.resize((cams.W // scale, cams.H // scale), Image.BOX)).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    red = (r > 120) & (r - g > 70) & (r - b > 50)
    dark = (r + g + b) < 180
    return red, dark


def overlap(view, p, parts_path, red, dark, scale):
    cams.CAMS[view] = make(p)
    img = compare.raster(parts_path, None, view, scale=scale)
    mr, md = img == compare.RED, img == compare.BLACK
    iou = lambda a, b: (a & b).sum() / max((a | b).sum(), 1)
    return iou(mr, red), iou(md, dark)


def main():
    parts_path = sys.argv[1]
    views = sys.argv[2].split(",") if len(sys.argv) > 2 else list(L2)
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for view in views:
        p0, r0 = fit_landmarks(view)
        print(view, "landmark fit residuals px", np.round(r0, 1).tolist())
        red, dark = photo_masks(view, 8)
        f0 = overlap(view, p0, parts_path, red, dark, 8)
        print(view, "start overlap red %.3f dark %.3f" % f0)
        scl = np.array([0.02, 0.02, 0.02, 0.004, 0.004, 0.004, 40.0])
        best = [None, -1]

        def cost(q):
            p = p0 + q * scl
            a, b = overlap(view, p, parts_path, red, dark, 8)
            if a + b > best[1]:
                best[:] = [p, a + b]
            return -(a + b)
        minimize(cost, np.zeros(7), method="Nelder-Mead", options=dict(maxfev=160, xatol=0.05, fatol=1e-4,
                                                                         initial_simplex=np.vstack([np.zeros(7), 2 * np.eye(7)])))
        p = best[0]
        red4, dark4 = photo_masks(view, 4)
        f1 = overlap(view, p, parts_path, red4, dark4, 4)
        c = make(p)
        print(view, "fitted overlap red %.3f dark %.3f (scale 4)" % f1, "C", np.round(c.C, 3), "f %.0f" % c.f)
        print(view, "landmarks after the fit px", {n: np.round(c.project([L3[n]])[0] - L2[view][n], 1).tolist()
                                                     for n in L2[view]})
        out[view] = dict(c.to_dict(), params=[float(q) for q in p], file=FILES[view],
                         overlap=dict(red=round(float(f1[0]), 4), dark=round(float(f1[1]), 4)))
        json.dump(out, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
