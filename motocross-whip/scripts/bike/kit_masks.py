"""Masks of the plate (front view) and the seat (top view) in their own textures, for kit_canvas.py: which texels
belong to the part, so white in the artwork (the race number, the rider's name) stays white.

python3 kit_masks.py PARTS.npz KIT_DIR      writes KIT_DIR/masks/plate.png and seat.png (sizes from kit.json)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts   # noqa: E402


def faces(d, part, keep):
    V = d[part + "__V"].astype(float)
    S, F, M = d[part + "__S"], d[part + "__F"], d[part + "__M"]
    mats = [str(m) for m in d["materials"]]
    start = np.concatenate([[0], np.cumsum(S)[:-1]])
    for fi, (s, n) in enumerate(zip(start, S)):
        P = V[F[s:s + n]]
        if keep(P, mats[M[fi]]):
            yield P


def main():
    d = np.load(sys.argv[1])
    kdir = sys.argv[2]
    maps = json.load(open(os.path.join(kdir, "maps.json")))
    kit = json.load(open(os.path.join(kdir, "kit.json")))
    size = {p["target"]: p.get("size", p.get("plate_size")) for p in kit["panels"] if p.get("target")}
    os.makedirs(os.path.join(kdir, "masks"), exist_ok=True)
    if "plate" in size:
        m, (W, H) = maps["plate"], size["plate"]
        img = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(img)

        def front(P, mat):
            n = np.cross(P[1] - P[0], P[2] - P[0])
            return np.linalg.norm(n) > 0 and abs(n[0]) / np.linalg.norm(n) > 0.45
        for P in faces(d, "number_plate", front):
            u = (P[:, 1] - m["u0"]) / (m["u1"] - m["u0"])
            v = ((P[:, 2] - 0.94) / math.cos(parts.RAKE) - m["s0"]) / (m["s1"] - m["s0"])
            dr.polygon([(float(a * W), float((1 - b) * H)) for a, b in zip(u, v)], fill=255)
        img.filter(ImageFilter.MaxFilter(5)).save(os.path.join(kdir, "masks", "plate.png"))
    if "seat" in size:
        m, (W, H) = maps["seat"], size["seat"]
        img = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(img)
        for P in faces(d, "seat", lambda P, mat: mat == "seat"):
            u = (m["x1"] - P[:, 0]) / (m["x1"] - m["x0"])
            v = (P[:, 1] - m["y0"]) / (m["y1"] - m["y0"])
            dr.polygon([(float(a * W), float((1 - b) * H)) for a, b in zip(u, v)], fill=255)
        img.filter(ImageFilter.MaxFilter(5)).save(os.path.join(kdir, "masks", "seat.png"))
    print("masks", sorted(size))


if __name__ == "__main__":
    main()
