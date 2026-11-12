"""Right-side kit artwork from the left side's: mirror the panel, then set each word back so it reads.

python3 kit_mirror.py KIT_DIR PART

Kit makers draw the right side as the left side's mirror image (the shapes and stripes swap ends) with every word and
logo set to read normally. A plain horizontal flip mirrors the lettering too, so each lettering "layer" is put back:
its pixels (picked by ink colour, optionally inside a box of the left art) are carried to the mirrored place by the
mirror followed by a reflection across the line perpendicular to the layer's own writing direction. Net effect: the
word is rotated about its centre so that it runs along the mirrored part (its letter tops keep facing the same edge of
the part) and reads left to right as seen from the right. For level writing that is a plain unmirrored copy; for the
swingarm's slanted words it tilts them the other way, as on Damien's right side (photo 03).

KIT_DIR/kit.json "mirror" entries: {"part": "swingarm", "left": "art/swingarm_L.png", "right": "art/swingarm_R.png",
  "layers": [{"ink": ["red"]}, {"ink": ["white"], "on_black": true}, {"ink": ["red", "white"], "box": [x0, y0, x1, y1]}]}
  on_black: only ink enclosed by the black sticker (bare aluminium next to it is as light as white ink).
  angle: the writing direction in degrees (image x right, y down) when the layer's long axis is not it (a column of
  level logos); solid: the layer's ink with the holes in it filled (a logo plate with its letters); glyphs: drop
  long sparse blobs of the ink (pinstripes, gloss streaks), keep the letters.
The writing direction of a layer is the long axis of its pixels (fine for words and logo boxes, which are long).
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

INKS = {
    "red": lambda a: (a[..., 0] > 140) & (a[..., 1] < 90) & (a[..., 2] < 90),
    "white": lambda a: (a.min(-1) > 200) & ((a.max(-1) - a.min(-1)) < 30),
    "yellow": lambda a: (a[..., 0] > 180) & (a[..., 1] > 150) & (a[..., 2] < 110),
}


def part_region(a):
    """The panel itself: everything that is not the white page around it (holes in the panel stay part of it)."""
    page = (a.min(-1) > 235)
    lab, _ = ndi.label(page)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    outside = np.isin(lab, list(border))
    return ~outside


def layer_mask(a, region, layer):
    m = np.zeros(a.shape[:2], bool)
    for ink in layer["ink"]:
        m |= INKS[ink](a)
    m &= region
    if "box" in layer:
        x0, y0, x1, y1 = layer["box"]
        b = np.zeros_like(m)
        b[y0:y1, x0:x1] = True
        m &= b
    lab, n = ndi.label(m)
    keep = np.ones(n + 1, bool)
    if layer.get("on_black"):                                   # only lettering on the black sticker: not the bare
        dark = (a.max(-1) < 90) | INKS["red"](a)               # aluminium, whose highlights are as light as white ink
        ring = ndi.binary_dilation(m, iterations=4) & ~m
        rl = ndi.grey_dilation(lab, size=9) * ring              # each ring pixel tagged with its blob
        tot = np.bincount(rl.ravel(), minlength=n + 1)
        drk = np.bincount(rl.ravel(), weights=dark.ravel(), minlength=n + 1)
        keep &= drk > 0.6 * np.maximum(tot, 1)
    if layer.get("on_black") or layer.get("glyphs"):
        for i, s in enumerate(ndi.find_objects(lab)):            # glyphs fill their box well and are compact;
            h, w = s[0].stop - s[0].start, s[1].stop - s[1].start   # gloss streaks and pinstripes are sparse (a
            if (lab[s] == i + 1).sum() < 0.2 * h * w or max(h, w) > 10 * min(h, w):   # curve) or long and thin
                keep[i + 1] = False
    keep[0] = False
    m = keep[lab]
    if layer.get("solid"):                                      # a logo on its own plate (black letters in the
        m = ndi.binary_fill_holes(ndi.binary_closing(m, iterations=2))   # yellow PIRELLI box): the plate whole
    return m


def mirror_art(a, layers):
    H, W = a.shape[:2]
    region = part_region(a)
    out = a[:, ::-1].copy()
    region_m = region[:, ::-1]
    masks = [layer_mask(a, region, L) for L in layers]
    # 1. take the mirrored lettering out: fill from the nearest panel pixel that is not lettering (black, mostly)
    gone = np.zeros((H, W), bool)
    for m in masks:
        gone |= ndi.binary_dilation(m, iterations=3)
    gone_m = gone[:, ::-1] & region_m
    keep = ~gone_m & region_m
    _, (ky, kx) = ndi.distance_transform_edt(~keep, return_indices=True)
    out[gone_m] = out[ky[gone_m], kx[gone_m]]
    # 2. each layer back at its mirrored place, reading the right way
    stats = []
    for L, m in zip(layers, masks):
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            stats.append(dict(layer=L, pixels=0))
            continue
        c = np.array([xs.mean(), ys.mean()])
        P = np.stack([xs - c[0], ys - c[1]])
        if "angle" in L:                                        # given: a stack of level logos is taller than wide
            t = np.radians(L["angle"])
            d = np.array([np.cos(t), np.sin(t)])
        else:
            w, v = np.linalg.eigh(P @ P.T)
            d = v[:, np.argmax(w)]                              # writing direction (image x right, y down)
        dm = np.array([-d[0], d[1]])                            # the same direction after the flip
        cm = np.array([W - 1 - c[0], c[1]])
        src = ndi.binary_dilation(m, iterations=1)              # with the anti-aliased edge
        R =int(np.ceil(np.sqrt(((P ** 2).sum(0)).max()))) + 4
        qx, qy = np.meshgrid(np.arange(int(cm[0]) - R, int(cm[0]) + R + 1),
                             np.arange(int(cm[1]) - R, int(cm[1]) + R + 1))
        ok = (qx >= 0) & (qy >= 0) & (qx < W) & (qy < H)
        qx, qy = qx[ok], qy[ok]
        s = np.stack([qx - cm[0], qy - cm[1]])
        rm = s - 2 * (dm @ s) * dm[:, None]                     # undo the reflection (its own inverse)
        px = np.round(c[0] - rm[0]).astype(int)                 # undo the flip
        py = np.round(c[1] + rm[1]).astype(int)
        inb = (px >= 0) & (py >= 0) & (px < W) & (py < H)
        qx, qy, px, py = qx[inb], qy[inb], px[inb], py[inb]
        hit = src[py, px] & region_m[qy, qx]
        out[qy[hit], qx[hit]] = a[py[hit], px[hit]]
        ang = float(np.degrees(np.arctan2(d[1], d[0])))
        stats.append(dict(ink=L["ink"], box=L.get("box"), pixels=int(m.sum()), centre=[round(float(c[0])), round(float(c[1]))],
                          direction_deg=round(ang if abs(ang) <= 90 else ang - 180 * np.sign(ang), 1),
                          painted=int(hit.sum())))
    return out, stats


def main():
    kdir, part = sys.argv[1], sys.argv[2]
    kit = json.load(open(os.path.join(kdir, "kit.json")))
    e = next(m for m in kit["mirror"] if m["part"] == part)
    a = np.asarray(Image.open(os.path.join(kdir, e["left"])).convert("RGB"))
    out, stats = mirror_art(a, e["layers"])
    Image.fromarray(out).save(os.path.join(kdir, e["right"]), optimize=True)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
