"""Exact side outlines of the bike's non-plastic parts from the material map of Honda's profile photo (segment.py).

Each part: a material class (or several), a window in bike mm, a seed point on the part; the class mask is eroded a
little (breaks hair-thin bridges to neighbours), the component under the seed is kept, grown back inside the mask,
holes filled, and its contour written as a polygon in mm. Output: research/bike-outlines2.json.

python3 extract.py OUT.json [CHECK.jpg]
"""
import json
import os
import sys

import contourpy
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import segment            # noqa: E402

RED, BLACK, DARK, ALU, GOLD, BRONZE = 1, 2, 3, 4, 5, 6
# name: (view, classes, window (x0, x1, z0, z1) mm, seed (x, z) mm, erosion px, cuts: lines ((x, z), (x, z)) removed)
PIVOT_CUT = [((575, 440), (575, 500)), ((560, 610), (600, 640))]
PARTS = {
    "frame": ("left", (ALU,), (470, 1010, 300, 900), (700, 715), 2, PIVOT_CUT),
    "down_tube": ("left", (ALU,), (900, 1030, 380, 680), (985, 560), 1, []),
    "cradle": ("left", (ALU,), (560, 960, 320, 400), (750, 348), 1, []),
    "swingarm": ("left", (ALU,), (-80, 590, 250, 520), (280, 400), 2, [((575, 440), (575, 500))]),
    "lower_panel": ("left", (BLACK,), (180, 640, 440, 880), (430, 720), 2, []),
    "skid": ("left", (BLACK,), (560, 1010, 290, 440), (880, 350), 1, []),
    "frame_R": ("right", (ALU,), (470, 1010, 300, 900), (700, 715), 2, PIVOT_CUT),
    "swingarm_R": ("right", (ALU,), (-80, 590, 250, 520), (280, 400), 2, [((575, 440), (575, 500))]),
    "muffler": ("right", (ALU,), (-120, 520, 560, 930), (120, 770), 2, []),
    "header": ("right", (BRONZE, GOLD), (560, 1060, 360, 720), (900, 470), 0, []),
    "lower_panel_R": ("right", (BLACK,), (180, 640, 440, 880), (430, 720), 2, []),
}


def extract(cls, X, Z, spec):
    view, classes, (x0, x1, z0, z1), seed, er, cuts = spec
    m = np.isin(cls, classes) & (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
    if cuts:
        img = Image.fromarray((m * 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        for (xa, za), (xb, zb) in cuts:
            pa = np.unravel_index(np.argmin((X - xa) ** 2 + (Z - za) ** 2), X.shape)
            pb = np.unravel_index(np.argmin((X - xb) ** 2 + (Z - zb) ** 2), X.shape)
            d.line([(pa[1], pa[0]), (pb[1], pb[0])], fill=0, width=3)
        m = np.asarray(img) > 0
    core = ndimage.binary_erosion(m, iterations=er) if er else m
    lab, n = ndimage.label(core)
    si = np.unravel_index(np.argmin((X - seed[0]) ** 2 + (Z - seed[1]) ** 2), X.shape)
    k = lab[si]
    if k == 0:                                             # seed not on the part: nearest labelled pixel
        d2 = np.where(lab > 0, (X - seed[0]) ** 2 + (Z - seed[1]) ** 2, 1e12)
        k = lab[np.unravel_index(np.argmin(d2), X.shape)]
    comp = lab == k
    if er:
        comp = ndimage.binary_dilation(comp, iterations=er + 1) & m
    comp = ndimage.binary_fill_holes(ndimage.binary_closing(comp, iterations=2))
    comp = ndimage.binary_opening(comp, iterations=1)
    lab2, n2 = ndimage.label(comp)
    if n2 > 1:
        comp = lab2 == (np.argmax(ndimage.sum(comp, lab2, range(1, n2 + 1))) + 1)
    gen = contourpy.contour_generator(z=comp.astype(float))
    lines = gen.lines(0.5)
    if not lines:
        return None, comp
    c = max(lines, key=len)
    H, W = comp.shape
    pts = []
    for col, row in c:
        i0, j0 = min(int(row), H - 2), min(int(col), W - 2)
        fi, fj = row - i0, col - j0
        x = (X[i0, j0] * (1 - fi) * (1 - fj) + X[i0 + 1, j0] * fi * (1 - fj) + X[i0, j0 + 1] * (1 - fi) * fj
             + X[i0 + 1, j0 + 1] * fi * fj)
        z = (Z[i0, j0] * (1 - fi) * (1 - fj) + Z[i0 + 1, j0] * fi * (1 - fj) + Z[i0, j0 + 1] * (1 - fi) * fj
             + Z[i0 + 1, j0 + 1] * fi * fj)
        pts.append((x, z))
    pts = np.array(pts)
    keep = [pts[0]]
    for p in pts[1:]:
        if np.hypot(*(p - keep[-1])) >= 4.0:
            keep.append(p)
    return np.array(keep), comp


def main():
    seg = {v: segment.classify(v) for v in ("left", "right")}
    res, masks = {}, {"left": {}, "right": {}}
    for name, spec in PARTS.items():
        cls, bp, im, X, Z = seg[spec[0]]
        poly, comp = extract(cls, X, Z, spec)
        if poly is None:
            print(f"{name:14s} NOT FOUND")
            continue
        res[name] = [[round(float(x), 1), round(float(z), 1)] for x, z in poly]
        masks[spec[0]][name] = comp
        print(f"{name:14s} {len(poly):4d} pts  x {poly[:, 0].min():7.0f}..{poly[:, 0].max():6.0f}  "
              f"z {poly[:, 1].min():6.0f}..{poly[:, 1].max():6.0f}  area {comp.sum() * (bp['mm_per_px'] * 2) ** 2 / 100:.0f} cm2")
    json.dump(res, open(sys.argv[1], "w"))
    if len(sys.argv) > 2:
        cols = [(0, 90, 255), (0, 170, 60), (200, 0, 200), (255, 120, 0), (0, 160, 170), (120, 60, 0), (220, 0, 0),
                (90, 0, 180), (0, 0, 0)]
        tiles = []
        for v in ("left", "right"):
            cls, bp, im, X, Z = seg[v]
            a = (np.asarray(im).astype(np.float32) * 0.45 + 140).clip(0, 255).astype(np.uint8)
            for (name, comp), c in zip(masks[v].items(), cols):
                a[comp & ~ndimage.binary_erosion(comp, iterations=2)] = c
            tiles.append(Image.fromarray(a).crop((300, 330, 1750, 960)))
        sh = Image.new("RGB", (1450, 1260))
        sh.paste(tiles[0], (0, 0)); sh.paste(tiles[1], (0, 630))
        sh.save(sys.argv[2], quality=90)


if __name__ == "__main__":
    main()
