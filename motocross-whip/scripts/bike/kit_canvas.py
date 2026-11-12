"""Damien's sticker kit (v1, 2026-11-12): panel artwork -> the livery textures the build maps onto the plastics.

python3 kit_canvas.py KIT_DIR TEMPLATE_DIR

Each panel's artwork was painted (by an image model, from Damien's photos; see KIT_DIR/kit.json) onto a crop of the
model's flat side view made by kit_template.py, so an artwork pixel maps straight back to a point of the side view,
and from there into the side textures that build_bike.uv_for projects onto the plastics:
  side_L.png / side_R.png   x X0..X1, z Z0..Z1 (KIT_DIR/maps.json "side"), PPM pixels a metre; left: front at the
                            image's left; right: front at its right (as each side is seen)
Every texel takes the artwork of the panel that is in front at that point of the side view (parts_<side>.png); texels
of panels without artwork yet keep the plain plastic red.

kit.json: {"panels": [{"side": "left", "part": "side_panels", "art": "art/sidepanel_L.png",
                        "crop": [u0, v0, u1, v1], "pad": [left, top]}, ...]}
  crop: the template crop (template pixels) the artwork was painted on; pad: white added left and top to make the
  crop the artwork's aspect ratio before upload. The artwork may be any size: it is scaled back to the padded crop.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

RED = (208, 10, 22)


def build_side(kit, side, tdir, kdir):
    fr = json.load(open(os.path.join(tdir, "frame.json")))
    names = fr["names"]
    sm = json.load(open(os.path.join(kdir, "maps.json")))["side"]
    W = int(round((sm["x1"] - sm["x0"]) * sm["ppm"]))
    H = int(round((sm["z1"] - sm["z0"]) * sm["ppm"]))
    c, r = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    x = sm["x1"] - c / sm["ppm"] if side == "left" else sm["x0"] + c / sm["ppm"]
    z = sm["z1"] - r / sm["ppm"]
    ut = (fr["X1"] - x) * fr["PPM"] if side == "left" else (x - fr["X0"]) * fr["PPM"]
    vt = (fr["Z1"] - z) * fr["PPM"]
    pid = np.asarray(Image.open(os.path.join(tdir, f"parts_{side}.png")))
    ui = np.clip(ut.astype(int), 0, pid.shape[1] - 1)
    vi = np.clip(vt.astype(int), 0, pid.shape[0] - 1)
    front = pid[vi, ui]
    out = np.empty((H, W, 3), np.uint8)
    out[:] = RED
    for p in kit["panels"]:
        if p["side"] != side:
            continue
        art = Image.open(os.path.join(kdir, p["art"])).convert("RGB")
        u0, v0, u1, v1 = p["crop"]
        pl, pt = p.get("pad", [0, 0])
        cw, ch = (u1 - u0) + 2 * pl, (v1 - v0) + 2 * pt              # the padded crop the artwork covers
        k = art.width / cw
        a = np.asarray(art)
        ax = ((ut - u0 + pl) * k).astype(int)
        ay = ((vt - v0 + pt) * k).astype(int)
        ok = (front == names.index(p["part"]) + 1) & (ax >= 0) & (ay >= 0) & (ax < art.width) & (ay < art.height)
        out[ok] = a[ay[ok], ax[ok]]
        print(side, p["part"], "texels", int(ok.sum()))
    Image.fromarray(out).save(os.path.join(kdir, f"side_{'L' if side == 'left' else 'R'}.png"), optimize=True)


def main():
    kdir, tdir = sys.argv[1], sys.argv[2]
    kit = json.load(open(os.path.join(kdir, "kit.json")))
    for side in ("left", "right"):
        build_side(kit, side, tdir, kdir)


if __name__ == "__main__":
    main()
