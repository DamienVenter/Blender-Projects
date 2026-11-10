"""Score the model's shape against Honda's studio profile photos, pixel for pixel.

The parts file (parts.py) is drawn flat from the photo's own camera (orthographic, same scale and position: the parts
are built in the photo's axle-line frame), every face in its material class, nearest last. The result is compared
with the photo's material map (segment.py): overlap (IoU) of the whole silhouette and of each material class, and a
difference picture (photo only = blue: missing from the model; model only = orange: not on the bike).

python3 compare.py PARTS.npz OUT_PREFIX      -> OUT_PREFIX_left.jpg, OUT_PREFIX_right.jpg, scores printed and saved
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import camera             # noqa: E402
import segment            # noqa: E402

RED, BLACK, DARK, METAL = 1, 2, 3, 4
# "dark" pixels of the photo are lit black rubber or plastic as often as dark metal: they match either class
CLASS_OF = {"red": RED, "black": BLACK, "dark": DARK, "alu": METAL, "gold": METAL, "bronze": METAL}
MAT_CLASS = {
    RED: ["livery_L", "livery_R", "livery_fender", "fender_front", "seat", "plate", "barpad", "fork_guard", "red_anod",
          "plastic_red"],
    BLACK: ["rubber", "plastic_black", "black_texture", "rubber_black", "rim", "grip", "bar_black", "anod_black",
            "engine_black", "louvre", "radiator", "muffler_cap", "shock_body", "chain", "cable"],
}


# regions of the profile (bike mm: x0, x1, z0, z1) for the error table
REGIONS = {"front wheel": (1120, 1850, 0, 690), "rear wheel": (-340, 340, 0, 640), "fork, plate, bars": (1040, 1340, 690, 1300),
           "front fender": (1340, 1750, 690, 1000), "engine bay": (590, 1040, 290, 700), "pivot, pegs, linkage": (340, 590, 200, 640),
           "shroud, tank": (590, 1040, 700, 1100), "seat, side panel": (100, 590, 640, 1100), "tail, muffler": (-340, 100, 640, 1100)}


def raster(parts_path, bp, view, scale=2):
    data = np.load(parts_path)
    mats = [str(m) for m in data["materials"]]
    mclass = np.full(len(mats), METAL, np.uint8)
    for c, names in MAT_CLASS.items():
        for n in names:
            if n in mats:
                mclass[mats.index(n)] = c
    W, H = bp["size_px"][0] // scale, bp["size_px"][1] // scale
    fa, ra = np.array(bp["front_axle_px"]) / scale, np.array(bp["rear_axle_px"]) / scale
    s = bp["mm_per_px"] * scale / 1000.0
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]]) if bp["front_side"] == "left" else np.array([u[1], -u[0]])
    if v[1] > 0:
        v = -v
    r0 = bp["rear_tyre_od_mm"] / 2000.0
    polys = []
    for name in [str(n) for n in data["names"]]:
        V = data[f"{name}__V"].astype(float)
        S, Fl, M = data[f"{name}__S"], data[f"{name}__F"], data[f"{name}__M"]
        xi, zi = camera.project(view, V[:, 0], V[:, 1], V[:, 2])           # the photo's perspective
        P = ra + np.outer(xi / s, u) + np.outer((zi - r0) / s, v)
        k = 0
        for sz, mi in zip(S, M):
            idx = Fl[k:k + sz]
            k += sz
            polys.append((float(V[idx, 1].mean()), mclass[mi], P[idx]))
    polys.sort(key=lambda t: t[0] if view == "left" else -t[0])          # far first, near last
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for _, c, P in polys:
        d.polygon([tuple(p) for p in P], fill=int(c))
    return np.asarray(img)


def score(parts_path, out_prefix):
    bps = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))
    res = {}
    for view in ("left", "right"):
        cls, bp, im, X, Z = segment.classify(view)
        tgt = np.zeros_like(cls)
        for k, name in enumerate(segment.NAMES):
            if name in CLASS_OF:
                tgt[cls == k] = CLASS_OF[name]
        mdl = raster(parts_path, bp, view).copy()
        mdl[Z < 4.0] = 0
        iou = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1))
        amb = (tgt == DARK) & ((mdl == BLACK) | (mdl == METAL))
        same = ((tgt == mdl) & (tgt > 0)) | amb
        tgt = np.where(amb, mdl, tgt)                        # ambiguous pixels take the model's class
        r = {"silhouette": iou(tgt > 0, mdl > 0), "red": iou(tgt == RED, mdl == RED),
             "black": iou(tgt == BLACK, mdl == BLACK), "metal": iou(tgt == METAL, mdl == METAL),
             "same_class": float(same.sum() / max(((tgt > 0) | (mdl > 0)).sum(), 1))}
        res[view] = {k: round(v, 4) for k, v in r.items()}
        # where the error is: area (cm2) missing from the model / extra in the model / wrong material, per region
        px_cm2 = (bp["mm_per_px"] * 2 / 10.0) ** 2
        regions = {}
        for name, (x0, x1, z0, z1) in REGIONS.items():
            w = (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)
            regions[name] = [round(float(((tgt > 0) & (mdl == 0) & w).sum() * px_cm2)),
                             round(float(((tgt == 0) & (mdl > 0) & w).sum() * px_cm2)),
                             round(float(((tgt > 0) & (mdl > 0) & (tgt != mdl) & w).sum() * px_cm2))]
        res[view]["regions_missing_extra_wrong_cm2"] = regions
        a = np.full(tgt.shape + (3,), 255, np.uint8)
        both = (tgt > 0) & (mdl > 0)
        a[both & (tgt == mdl)] = (205, 205, 205)
        a[both & (tgt != mdl)] = (150, 150, 150)
        a[(tgt > 0) & (mdl == 0)] = (40, 110, 255)           # on the bike, missing from the model
        a[(tgt == 0) & (mdl > 0)] = (255, 140, 0)            # in the model, not on the bike
        Image.fromarray(a).save(f"{out_prefix}_{view}.png")
        print(view, {k: v for k, v in res[view].items() if k != "regions_missing_extra_wrong_cm2"})
        for name, (mi, ex, wr) in regions.items():
            print(f"    {name:22s} missing {mi:5d}  extra {ex:5d}  wrong material {wr:5d} cm2")
    json.dump(res, open(f"{out_prefix}_scores.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    score(sys.argv[1], sys.argv[2])
