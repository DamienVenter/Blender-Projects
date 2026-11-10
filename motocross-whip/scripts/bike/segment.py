"""Material classes of every pixel of a calibrated studio profile photo (the target the model is scored against).

Classes: 0 background, 1 red plastic, 2 black (tyres, plastics, seat base, hoses), 3 dark metal/grey, 4 aluminium and
other bright metal, 5 gold (fork tubes), 6 bronze (header pipe). Bright aluminium highlights that reach white are
recovered by filling holes inside the bike's outline (the background is the white connected to the image border plus
white enclosed between spokes, kept as background by a size test).

python3 segment.py VIEW OUT.npy [CHECK.jpg]
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
NAMES = ["background", "red", "black", "dark", "alu", "gold", "bronze"]
COLORS = np.array([(255, 255, 255), (220, 30, 40), (25, 25, 28), (95, 95, 100), (170, 190, 215), (225, 175, 60),
                   (150, 90, 40)], np.uint8)


def classify(view, scale=2):
    bp = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))[view]
    im = Image.open(os.path.join(REF, bp["file"])).convert("RGB")
    im = im.resize((im.width // scale, im.height // scale), Image.LANCZOS)
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = mx - mn
    white = (mn > 226) & (sat < 16)
    # bike coordinates of every pixel (axle-line frame, mm)
    fa, ra = np.array(bp["front_axle_px"]) / scale, np.array(bp["rear_axle_px"]) / scale
    s_mm = bp["mm_per_px"] * scale
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]]) if bp["front_side"] == "left" else np.array([u[1], -u[0]])
    if v[1] > 0:
        v = -v
    ii, jj = np.mgrid[0:r.shape[0], 0:r.shape[1]]
    PX = np.stack([jj + 0.5, ii + 0.5], axis=-1) - ra
    X = PX @ u * s_mm
    Z = PX @ v * s_mm + bp["rear_tyre_od_mm"] / 2
    # between the spokes the studio background is a shade darker than outside: looser white inside the rims
    in_wheel = (np.hypot(X, Z - bp["rear_tyre_od_mm"] / 2) < 236) | \
               (np.hypot(X - 1483, Z - bp["rear_tyre_od_mm"] / 2) < 262)
    white |= in_wheel & (mn > 198) & (sat < 14)
    ground = Z < 4.0                                   # floor and the tyres' soft shadow
    cls = np.zeros(r.shape, np.uint8)
    red = (r > 105) & (r - g > 55) & (r - b > 45) & (g < 110)
    gold = (r > 120) & (r - b > 45) & (g > 0.52 * r) & (g < 0.92 * r) & ~red & (mx > 140)
    bronze = (r > 70) & (r - b > 28) & (g > 0.5 * r) & (g < 0.9 * r) & ~red & ~gold & (mx <= 140) & (sat > 28)
    black = (mx < 62) & ~red
    dark = (mx >= 62) & (mx < 128) & (sat < 40) & ~red & ~bronze
    alu = (mx >= 128) & (sat < 40) & ~white & ~red & ~gold
    cls[alu] = 4; cls[dark] = 3; cls[black] = 2; cls[bronze] = 6; cls[gold] = 5; cls[red] = 1
    # white: background if connected to the border, or a large enclosed area (between spokes); small white islands
    # inside the bike are highlights or white lettering -> take the class around them
    lab, n = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndimage.sum(white, lab, range(1, n + 1))
    unknown = (cls == 0) & ~white
    for k in range(1, n + 1):
        if k in border or sizes[k - 1] > 900 or in_wheel[lab == k].any():
            continue
        unknown |= lab == k
    if unknown.any():                                  # nearest classified pixel
        known = (cls > 0)
        idx = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
        fill = cls[idx[0], idx[1]]
        near = ndimage.distance_transform_edt(~known) < 14
        cls[unknown & near] = fill[unknown & near]
    cls[ground] = 0
    cls[in_wheel & white] = 0
    return cls, bp, im, X, Z


def main():
    view, out = sys.argv[1], sys.argv[2]
    cls, bp, im, X, Z = classify(view)
    np.save(out, cls)
    print({NAMES[k]: int((cls == k).sum()) for k in range(len(NAMES))})
    if len(sys.argv) > 3:
        Image.fromarray(COLORS[cls]).save(sys.argv[3], quality=92)


if __name__ == "__main__":
    main()
