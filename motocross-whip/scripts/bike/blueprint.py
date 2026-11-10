"""Calibrate Honda's studio profile photos as metric blueprints.

The studio photos are taken from far away with a long lens (near orthographic). In each profile the two tyres are
found as dark blobs against the white background; a circle is fitted to each tyre's outer envelope (knob tips) by
least squares; the axle centres are the circle centres. Scale = wheelbase (1483 mm, research/crf250r-2026.md) /
centre distance in pixels. Output: blueprint.json {view: {front_axle_px, rear_axle_px, mm_per_px, tilt_deg,
front_tyre_od_mm, rear_tyre_od_mm}} so any pixel maps to bike-frame metres (x forward, z up, origin at the ground
under the rear axle).

python3 blueprint.py OUT.json
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
WHEELBASE_MM = 1483.0
VIEWS = {
    # name: (file, which side of the image the front wheel is on)
    "left": ("studio_left-profile_honda-eu-25ym-475600_4000x2250.jpg", "left"),
    "right": ("studio_right-profile_honda-eu-25ym-475596_4000x2250.jpg", "right"),
}


def tyre_circle(dark, cx0, cy0, r0):
    """Circle through the knob tips: for each direction the farthest dark pixel within 1.25 r0 of the guess."""
    H, W = dark.shape
    pts = []
    for a in np.linspace(0, 2 * math.pi, 720, endpoint=False):
        rs = np.arange(0.6 * r0, 1.25 * r0, 1.0)
        xs = (cx0 + rs * math.cos(a)).astype(int)
        ys = (cy0 + rs * math.sin(a)).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        d = np.zeros_like(rs, bool)
        d[ok] = dark[ys[ok], xs[ok]]
        if d.any():
            k = np.nonzero(d)[0].max()
            pts.append((xs[k], ys[k]))
    P = np.array(pts, float)
    # the upper part of a wheel is crossed by fenders, forks and plastics: keep the lower 200 degrees, which are
    # free tyre against white
    keep = P[:, 1] > cy0 - 0.35 * r0
    P = P[keep]
    x = np.array([cx0, cy0, r0])
    for _ in range(4):                     # refit without the points that are not tyre (chain, sprocket, guard)
        f = lambda p: np.hypot(P[:, 0] - p[0], P[:, 1] - p[1]) - p[2]
        x = least_squares(f, x, loss="soft_l1", f_scale=3.0).x
        r = np.abs(f(x))
        P = P[r < max(12.0, 2.5 * np.median(r))]
    f = lambda p: np.hypot(P[:, 0] - p[0], P[:, 1] - p[1]) - p[2]
    return x, float(np.sqrt(np.mean(f(x) ** 2))), len(P)


def calibrate(name):
    fn, front_side = VIEWS[name]
    im = np.asarray(Image.open(os.path.join(REF, fn)).convert("L")).astype(int)
    dark = im < 90
    H, W = im.shape
    # first guesses from the dark mass in the lower half, split into the image's left and right halves
    ys, xs = np.nonzero(dark[H // 2:, :])
    ys = ys + H // 2
    res = {}
    for side, sel in (("img_left", xs < W / 2), ("img_right", xs >= W / 2)):
        x, y = xs[sel], ys[sel]
        cx0, cy0 = float(np.median(x)), float(np.percentile(y, 50))
        r0 = 0.5 * (np.percentile(y, 99.5) - np.percentile(y, 2))
        (cx, cy, r), rms, n = tyre_circle(dark, cx0, cy0, max(r0, 300))
        (cx, cy, r), rms, n = tyre_circle(dark, cx, cy, r)
        res[side] = (cx, cy, r, rms, n)
    fa = res["img_left"] if front_side == "left" else res["img_right"]
    ra = res["img_right"] if front_side == "left" else res["img_left"]
    d = math.hypot(fa[0] - ra[0], fa[1] - ra[1])
    mmpx = WHEELBASE_MM / d
    tilt = math.degrees(math.atan2(-(fa[1] - ra[1]), abs(fa[0] - ra[0])))
    return {"file": fn, "front_side": front_side, "size_px": [W, H],
            "front_axle_px": [round(fa[0], 1), round(fa[1], 1)], "rear_axle_px": [round(ra[0], 1), round(ra[1], 1)],
            "mm_per_px": round(mmpx, 5), "tilt_deg": round(tilt, 3),
            "front_tyre_od_mm": round(2 * fa[2] * mmpx, 1), "rear_tyre_od_mm": round(2 * ra[2] * mmpx, 1),
            "fit_rms_px": [round(fa[3], 2), round(ra[3], 2)], "fit_points": [fa[4], ra[4]]}


def to_bike(view, px, py):
    """Pixel -> bike frame metres (x forward, z up; origin on the ground line under the rear axle)."""
    fa, ra = np.array(view["front_axle_px"]), np.array(view["rear_axle_px"])
    s = view["mm_per_px"] / 1000.0
    u = (fa - ra) / np.linalg.norm(fa - ra)                 # image direction of 'forward'
    v = np.array([u[1], -u[0]]) if view["front_side"] == "right" else np.array([-u[1], u[0]])
    if v[1] > 0:                                             # 'up' must point up the image
        v = -v
    d = np.array([px, py], float) - ra
    r_rear = view["rear_tyre_od_mm"] / 2000.0
    return float(d @ u * s), float(d @ v * s + r_rear)


def main():
    out = {name: calibrate(name) for name in VIEWS}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    for k, v in out.items():
        print(k, json.dumps(v))


if __name__ == "__main__":
    main()
