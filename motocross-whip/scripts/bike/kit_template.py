"""Flat side views of the model for the sticker kit (Damien's kit, 2026-11-12).

python3 kit_template.py PARTS.npz OUTDIR

Writes, for each side, an orthographic view of the whole bike at PPM pixels a metre (axle-line frame, x forward,
z up; the LEFT view has the front at the image's left, the RIGHT view at its right, as a person sees each side):
  template_<side>.png   the plastics in light grey with dark outlines (the canvas the kit is painted on), every
                        other part pale, for an image model or a person to paint the kit onto
  parts_<side>.png      the part number of each pixel (8 bit, 0 = nothing), for masks
  frame.json            the framing: pixel (u, v) of a point = ((X1 - x) * PPM, (Z1 - z) * PPM) on the left,
                        ((x - X0) * PPM, (Z1 - z) * PPM) on the right
and the tank top seen from above as the rider sees it (front at the image's top, the bike's right at its right), for
the tank sticker and the shroud tops: template_top.png, parts_top.png; pixel (u, v) = ((TY1 - y) * PPM, (TX1 - x) * PPM)
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams      # noqa: E402
import compare   # noqa: E402

X0, X1, Z0, Z1 = -0.40, 1.90, -0.06, 1.32
PPM = 1700
W, H = int((X1 - X0) * PPM), int((Z1 - Z0) * PPM)
PLASTICS = ["shrouds", "side_panels", "rear_fender", "front_fender", "number_plate", "fork_guards", "shroud_decks",
            "tail_under", "fender_flap", "seat", "tank", "swingarm", "rear_flap", "mudguard_top"]
TX0, TX1, TY0, TY1 = X0, X1, -0.22, 0.22                       # the top view: the whole bike's length
TW, TH = int((TY1 - TY0) * PPM), int((TX1 - TX0) * PPM)


class OrthoTop:
    """Looking straight down, the rider's way round: front at the image's top, the bike's right at its right."""
    F = np.array([0.0, 0.0, -1.0])
    C = np.array([0.0, 0.0, 10.0])

    def project(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        return np.stack([(TY1 - P[:, 1]) * PPM, (TX1 - P[:, 0]) * PPM], axis=-1)


def paint(pid, names, W, H):
    """Template image: plastics light grey with dark outlines, every other part pale."""
    plast = np.isin(pid, [names.index(n) + 1 for n in PLASTICS if n in names])
    img = np.full((H, W, 3), 255, np.uint8)
    img[pid > 0] = (236, 236, 238)
    img[plast] = (205, 205, 208)
    edges = np.asarray(Image.fromarray(pid.astype(np.uint8)).filter(ImageFilter.FIND_EDGES)) > 0
    edges = np.asarray(Image.fromarray((edges * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    img[edges & (pid > 0)] = (40, 40, 44)
    return img, int(plast.sum())


class Ortho:
    """An orthographic camera looking at the bike from one side, in the shape compare.raster expects."""

    def __init__(self, side):
        self.side = side
        self.F = np.array([0.0, -1.0, 0.0]) if side == "left" else np.array([0.0, 1.0, 0.0])
        self.C = np.array([0.0, 10.0, 0.0]) * (1 if side == "left" else -1)

    def project(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        u = (X1 - P[:, 0]) * PPM if self.side == "left" else (P[:, 0] - X0) * PPM     # left: front at the image's left
        return np.stack([u, (Z1 - P[:, 2]) * PPM], axis=-1)


def main():
    parts_path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    names = [str(n) for n in np.load(parts_path)["names"]]
    W0, H0 = cams.W, cams.H
    cams.W, cams.H = W, H
    try:
        for side in ("left", "right"):
            cams.CAMS["kit_" + side] = Ortho(side)
            pid = compare.raster(parts_path, None, "kit_" + side, scale=1, by_part=True)
            Image.fromarray(pid.astype(np.uint8)).save(os.path.join(out, f"parts_{side}.png"))
            img, n = paint(pid, names, W, H)
            Image.fromarray(img).save(os.path.join(out, f"template_{side}.png"))
            print(side, W, H, "plastics px", n)
        cams.W, cams.H = TW, TH
        cams.CAMS["kit_top"] = OrthoTop()
        pid = compare.raster(parts_path, None, "kit_top", scale=1, by_part=True)
        Image.fromarray(pid.astype(np.uint8)).save(os.path.join(out, "parts_top.png"))
        img, n = paint(pid, names, TW, TH)
        Image.fromarray(img).save(os.path.join(out, "template_top.png"))
        print("top", TW, TH, "plastics px", n)
    finally:
        cams.W, cams.H = W0, H0
    json.dump(dict(X0=X0, X1=X1, Z0=Z0, Z1=Z1, PPM=PPM, W=W, H=H, names=names, plastics=PLASTICS,
                   top=dict(X0=TX0, X1=TX1, Y0=TY0, Y1=TY1, W=TW, H=TH)),
              open(os.path.join(out, "frame.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
