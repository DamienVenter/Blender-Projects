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
  A right-side panel made by flipping a left one ("mirror_of": the left crop) sits at the mirrored crop: the right
  view is the left view flipped, u_right = (X1 - X0) * PPM - u_left.
  "target": "plate" or "seat": artwork painted on that texture's own crop (its pixels: the plate seen from the front,
  the seat from above); fills plate.png / seat.png (pixel "size") where the artwork is not white.
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
    span = (fr["X1"] - fr["X0"]) * fr["PPM"]
    for p in kit["panels"]:
        if p["side"] != side or p.get("target", "side") != "side":
            continue
        art = Image.open(os.path.join(kdir, p["art"])).convert("RGB")
        if "mirror_of" in p:
            a0, b0, a1, b1 = p["mirror_of"]
            p = dict(p, crop=[span - a1, b0, span - a0, b1])
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


def build_flat(kit, kdir):
    """Artwork painted on a texture's own crop: the plate (front view) and the seat (top view)."""
    for p in kit["panels"]:
        if p.get("target") not in ("plate", "seat"):
            continue
        W, H = p.get("size", p.get("plate_size"))
        out = np.empty((H, W, 3), np.uint8)
        out[:] = RED
        art = Image.open(os.path.join(kdir, p["art"])).convert("RGB")
        u0, v0, u1, v1 = p["crop"]
        pl, pt = p.get("pad", [0, 0])
        cw = (u1 - u0) + 2 * pl
        k = art.width / cw
        c, r = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
        ax = ((c - u0 + pl) * k).astype(int)
        ay = ((r - v0 + pt) * k).astype(int)
        ok = (ax >= 0) & (ay >= 0) & (ax < art.width) & (ay < art.height)
        a = np.asarray(art)
        px = np.zeros((H, W, 3), np.uint8)
        px[ok] = a[ay[ok], ax[ok]]
        mpath = os.path.join(kdir, "masks", p["target"] + ".png")
        if os.path.exists(mpath):                               # the part's own outline (kit_masks.py): white in
            art_px = ok & (np.asarray(Image.open(mpath)) > 0)   # the artwork (the number, the name) stays white
        else:
            art_px = ok & (px.astype(int).sum(2) < 735)         # else: the artwork, not its white surround
        out[art_px] = px[art_px]
        Image.fromarray(out).save(os.path.join(kdir, p["target"] + ".png"), optimize=True)
        print(p["target"], "texels", int(art_px.sum()))


def main():
    kdir, tdir = sys.argv[1], sys.argv[2]
    kit = json.load(open(os.path.join(kdir, "kit.json")))
    for side in ("left", "right"):
        build_side(kit, side, tdir, kdir)
    build_flat(kit, kdir)


if __name__ == "__main__":
    main()
