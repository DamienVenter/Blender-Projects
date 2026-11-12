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
  "target": "barpad": the pad's face artwork (emblem above two RENTHAL lines) -> barpad.png (build_barpad).
  "side": "top": the tank sticker painted on a crop of the top view (template_top.png): top.png (build_top).
  "band": true (a wrap on bare metal, the swingarm): also writes the sticker's extent to KIT_DIR/bands.json
  ({part: {side: [[x, z_low, z_high], ...]}}) so the build wraps only the faces under the sticker.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

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
    bands = {}
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
        inr = (ax >= 0) & (ay >= 0) & (ax < art.width) & (ay < art.height)
        if p.get("band"):
            # a wrap on bare metal: every texel of the sticker itself, also where a part that carries no kit (the
            # chain over the swingarm) hides it in the side view, so the faces under it are wrapped too
            others = [names.index(q["part"]) + 1 for q in kit["panels"]
                      if q["side"] == side and q.get("target", "side") == "side" and q["part"] != p["part"]]
            ok = inr & ~np.isin(front, others) & sticker(a, ax, ay, inr)
            bands[p["part"]] = band(ok, x, z)
        else:
            ok = inr & (front == names.index(p["part"]) + 1)
        out[ok] = a[ay[ok], ax[ok]]
        print(side, p["part"], "texels", int(ok.sum()))
    Image.fromarray(out).save(os.path.join(kdir, f"side_{'L' if side == 'left' else 'R'}.png"), optimize=True)
    return bands


def sticker(a, ax, ay, inr):
    """The texels a wrap sticker covers: its black, its ink and its white lettering, not the bare aluminium the
    artwork shows round it nor the white page; small specks and gaps closed (5 px)."""
    px = np.full(inr.shape + (3,), 255, np.int16)                  # outside the artwork: page, joined to its own
    px[inr] = a[ay[inr], ax[inr]]
    mx, mn = px.max(-1), px.min(-1)
    alu = (mx - mn < 28) & (mn > 120) & (mx < 236)                  # grey metal: neither black, nor ink, nor white
    page = mn >= 236
    letters = on_black(page & ~ndi_fill_border(page), (mx < 90) | ((px[..., 0] > 140) & (mn < 90)))
    st = inr & ~alu & (~page | letters)
    st = np.asarray(Image.fromarray((st * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    return np.asarray(Image.fromarray((st * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0


def on_black(m, dark):
    """The blobs of m mostly ringed by dark (white letters on the black sticker), not by metal (the white of a slot
    through the aluminium axle block)."""
    from scipy import ndimage as ndi
    lab, n = ndi.label(m)
    ring = ndi.binary_dilation(m, iterations=4) & ~m
    rl = ndi.grey_dilation(lab, size=9) * ring
    tot = np.bincount(rl.ravel(), minlength=n + 1)
    drk = np.bincount(rl.ravel(), weights=dark.ravel(), minlength=n + 1)
    keep = drk > 0.6 * np.maximum(tot, 1)
    keep[0] = False
    return keep[lab]


def ndi_fill_border(m):
    """The parts of mask m that touch the image border (the page round the part)."""
    from scipy import ndimage as ndi
    lab, _ = ndi.label(m)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    return np.isin(lab, list(edge))


def band(st, x, z, step=0.004):
    """Where a wrap sticker sits on its bare metal part (bands.json): for each 4 mm of x the lowest and highest z of
    the sticker's texels. The build wraps a face with the kit only inside this band; the metal keeps its own
    material outside it."""
    out = []
    for x0 in np.arange(x.min(), x.max(), step):
        cols = (x[0] >= x0) & (x[0] < x0 + step)
        rows = st[:, cols].any(1)
        if rows.sum() < 4:
            continue
        zz = z[:, 0][rows]
        out.append([round(float(x0 + step / 2), 4), round(float(zz.min()), 4), round(float(zz.max()), 4)])
    return out


def build_top(kit, tdir, kdir):
    """The tank sticker and the shroud decks, painted on a crop of the top view (kit_template.py, front at the top,
    the bike's right at the right) -> top.png over maps.json "top" (x0..x1 forward, y0..y1 left, ppm). Texels take the
    artwork where the part seen from above is one of the panel's parts ("tank,shroud_decks")."""
    panels = [p for p in kit["panels"] if p["side"] == "top" and "target" not in p]     # not the seat (build_flat)
    if not panels:
        return
    fr = json.load(open(os.path.join(tdir, "frame.json")))
    names, t = fr["names"], fr["top"]
    tm = json.load(open(os.path.join(kdir, "maps.json")))["top"]
    W = int(round((tm["y1"] - tm["y0"]) * tm["ppm"]))
    H = int(round((tm["x1"] - tm["x0"]) * tm["ppm"]))
    c, r = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    y = tm["y1"] - c / tm["ppm"]
    x = tm["x1"] - r / tm["ppm"]
    ut = (t["Y1"] - y) * fr["PPM"]
    vt = (t["X1"] - x) * fr["PPM"]
    pid = np.asarray(Image.open(os.path.join(tdir, "parts_top.png")))
    front = pid[np.clip(vt.astype(int), 0, pid.shape[0] - 1), np.clip(ut.astype(int), 0, pid.shape[1] - 1)]
    out = np.empty((H, W, 3), np.uint8)
    out[:] = RED
    for p in panels:
        art = Image.open(os.path.join(kdir, p["art"])).convert("RGB")
        u0, v0, u1, v1 = p["crop"]
        pl, pt = p.get("pad", [0, 0])
        k = art.width / ((u1 - u0) + 2 * pl)
        a = np.asarray(art)
        ax = ((ut - u0 + pl) * k).astype(int)
        ay = ((vt - v0 + pt) * k).astype(int)
        ids = [names.index(n) + 1 for n in p["part"].split(",")]
        ok = np.isin(front, ids) & (ax >= 0) & (ay >= 0) & (ax < art.width) & (ay < art.height)
        out[ok] = a[ay[ok], ax[ok]]
        print("top", p["part"], "texels", int(ok.sum()))
    Image.fromarray(out).save(os.path.join(kdir, "top.png"), optimize=True)


def build_barpad(kit, kdir):
    """Damien's Renthal pad (photos 04, 10): barpad.png in livery.barpad's three bands (build_bike.uv_for "barpad"):
    bottom third the front and rear faces (each read from its own side), middle the pad's top (forward = up in the
    image), top third the end caps. The face artwork's lower rows (the two RENTHAL lines) go on the faces at the pad's
    full length, its upper rows (the emblem) on the top at "top_scale" of the face's scale; the rest is the pad's red."""
    p = next((q for q in kit["panels"] if q.get("target") == "barpad"), None)
    if p is None:
        return
    W, H = 840, 720                                         # 210 x 180 mm at 4000 px/m, as livery.barpad
    B = H // 3
    art = Image.open(os.path.join(kdir, p["art"])).convert("RGB")
    a = np.asarray(art)
    red = tuple(int(v) for v in np.median(a[(a[..., 0] > 150) & (a[..., 1] < 80)], axis=0))
    out = Image.new("RGB", (W, H), red)
    t0, t1 = p["top_rows"]
    f0, f1 = p["face_rows"]
    face = art.crop((0, f0, art.width, f1))
    k = W * p.get("face_length", 1.0) / art.width           # the lettering's share of the pad's length
    face = face.resize((round(art.width * k), max(1, round(face.height * k))), Image.LANCZOS)
    out.paste(face, ((W - face.width) // 2, 2 * B + (B - face.height) // 2))
    top = art.crop((0, t0, art.width, t1))
    ink = np.asarray(top).astype(int)
    cols = np.nonzero(((ink[..., 1] > 120) | (ink.max(-1) < 70)).any(0))[0]
    top = top.crop((max(cols.min() - 10, 0), 0, min(cols.max() + 11, art.width), top.height))
    kt = k * p.get("top_scale", 1.0)
    top = top.resize((round(top.width * kt), round(top.height * kt)), Image.LANCZOS)
    out.paste(top, ((W - top.width) // 2, B + (B - top.height) // 2))
    out.save(os.path.join(kdir, "barpad.png"), optimize=True)
    print("barpad red", red, "face", face.size, "top", top.size)


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
    bands = {}
    for side in ("left", "right"):
        for part, b in build_side(kit, side, tdir, kdir).items():
            bands.setdefault(part, {})[side] = b
    json.dump(bands, open(os.path.join(kdir, "bands.json"), "w"))
    print("bands", {k: {s: len(v) for s, v in b.items()} for k, b in bands.items()})
    build_top(kit, tdir, kdir)
    build_barpad(kit, kdir)
    build_flat(kit, kdir)


if __name__ == "__main__":
    main()
