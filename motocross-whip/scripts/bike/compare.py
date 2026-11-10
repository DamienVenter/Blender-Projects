"""Score the model's shape against Honda's five studio photos, pixel for pixel.

The parts file (parts.py) is drawn flat through each photo's calibrated camera (cams.py), every face in its material
class, with a depth test. Profiles (left, right): compared with the photo's material map (segment.py): overlap (IoU)
of the whole silhouette and of each material class, an error table per region and a difference picture (photo only =
blue: missing from the model; model only = orange: not on the bike). Front, rear, top: overlap of the silhouette and
of the red plastics.

python3 compare.py PARTS.npz OUT_PREFIX           -> OUT_PREFIX_<view>.png, scores printed and saved as JSON
python3 compare.py sheet PARTS.npz OUT.jpg [views] -> the photo beside the model in flat class colours, per view
python3 compare.py intruders PARTS.npz            -> parts showing through the plastics in the profiles
compare.raster(parts, None, view, by_part=True)    -> which part is in front at each pixel
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams               # noqa: E402
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


def raster(parts_path, bp, view, scale=2, by_part=False):
    """The parts drawn flat through the photo's calibrated camera, each face in its material class, with a per-pixel
    depth test (a painter's sort by face distance let long faces such as the fork tubes paint over the number plate).
    by_part: each face carries its part's number (1-based, order of the file's names) instead of its class: tells
    which part is in front at a pixel."""
    data = np.load(parts_path)
    mats = [str(m) for m in data["materials"]]
    mclass = np.full(len(mats), METAL, np.uint8)
    for c, names in MAT_CLASS.items():
        for n in names:
            if n in mats:
                mclass[mats.index(n)] = c
    meta = json.loads(str(data["meta"])) if "meta" in data.files else {}
    for n, c in meta.get("class", {}).items():           # materials of plugin modules
        if n in mats:
            mclass[mats.index(n)] = {"red": RED, "black": BLACK}.get(c, METAL)
    cam = cams.CAMS[view]
    T, Dp, C = [], [], []
    for pi, name in enumerate([str(n) for n in data["names"]]):
        V = data[f"{name}__V"].astype(float)
        S, Fl, M = data[f"{name}__S"], data[f"{name}__F"], data[f"{name}__M"]
        P = cam.project(V) / scale
        dep = (V - cam.C) @ cam.F
        start = np.concatenate([[0], np.cumsum(S)[:-1]])
        for n_v in (3, 4):
            sel = np.nonzero(S == n_v)[0]
            if not len(sel):
                continue
            idx = Fl[start[sel][:, None] + np.arange(n_v)[None, :]]
            for tri in ((0, 1, 2),) if n_v == 3 else ((0, 1, 2), (0, 2, 3)):
                T.append(P[idx[:, tri]]); Dp.append(dep[idx[:, tri]])
                C.append(np.full(len(sel), pi + 1, np.uint8) if by_part else mclass[M[sel]])
    T, Dp, C = np.concatenate(T), np.concatenate(Dp), np.concatenate(C)
    W, H = cams.W // scale, cams.H // scale
    img = np.zeros((H, W), np.uint8)
    zbuf = np.full((H, W), np.inf)
    lo = np.floor(T.min(axis=1)).astype(int)
    hi = np.ceil(T.max(axis=1)).astype(int)
    size = (hi - lo).max(axis=1)
    # tiny triangles (spokes, chain, knobs): one pixel each at the centroid, far ones first
    small = size <= 2
    cen = T[small].mean(axis=1).astype(int)
    dz = Dp[small].mean(axis=1)
    ok = (cen[:, 0] >= 0) & (cen[:, 0] < W) & (cen[:, 1] >= 0) & (cen[:, 1] < H)
    o = np.argsort(-dz[ok])
    cx, cy, cz, cc = cen[ok][o, 0], cen[ok][o, 1], dz[ok][o], C[small][ok][o]
    img[cy, cx] = cc
    zbuf[cy, cx] = cz
    for i in np.nonzero(~small)[0]:
        x0, y0 = max(lo[i, 0], 0), max(lo[i, 1], 0)
        x1, y1 = min(hi[i, 0], W - 1), min(hi[i, 1], H - 1)
        if x1 < x0 or y1 < y0:
            continue
        (ax, ay), (bx, by), (cx_, cy_) = T[i]
        den = (by - cy_) * (ax - cx_) + (cx_ - bx) * (ay - cy_)
        if abs(den) < 1e-9:
            continue
        xs = np.arange(x0, x1 + 1) + 0.5
        ys = np.arange(y0, y1 + 1) + 0.5
        X_, Y_ = np.meshgrid(xs, ys)
        l1 = ((by - cy_) * (X_ - cx_) + (cx_ - bx) * (Y_ - cy_)) / den
        l2 = ((cy_ - ay) * (X_ - cx_) + (ax - cx_) * (Y_ - cy_)) / den
        l3 = 1.0 - l1 - l2
        ins = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not ins.any():
            continue
        z = l1 * Dp[i, 0] + l2 * Dp[i, 1] + l3 * Dp[i, 2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = ins & (z < sub)
        sub[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = C[i]
    return img


def score_other(parts_path, out_prefix, res):
    """Front, rear and top photos: overlap of the red plastics (and seat) and of the whole silhouette."""
    ref = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
    for view in ("front", "rear", "top"):
        a = np.asarray(Image.open(os.path.join(ref, cams.FILES[view])).convert("RGB").resize((cams.W // 2, cams.H // 2),
                                                                                          Image.BILINEAR)).astype(int)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        red = (r > 105) & (r - g > 55) & (r - b > 45)
        fg = a.min(axis=2) < 190
        mdl = raster(parts_path, None, view)
        iou = lambda p, q: float((p & q).sum() / max((p | q).sum(), 1))
        res[view] = {"silhouette": round(iou(fg | red, mdl > 0), 4), "red": round(iou(red, mdl == RED), 4)}
        img = np.full(red.shape + (3,), 255, np.uint8)
        img[fg & (mdl > 0)] = (215, 215, 215)
        img[red & (mdl == RED)] = (175, 175, 175)
        img[red & (mdl != RED)] = (40, 110, 255)             # red on the bike, not red in the model
        img[~red & (mdl == RED)] = (255, 140, 0)             # red in the model, not on the bike
        Image.fromarray(img).save(f"{out_prefix}_{view}.png")
        print(view, res[view])


def score(parts_path, out_prefix):
    bps = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))
    res = {}
    for view in ("left", "right"):
        cls, bp, im, X, Z = segment.classify(view)
        tgt = np.zeros_like(cls)
        for k, name in enumerate(segment.NAMES):
            if name in CLASS_OF:
                tgt[cls == k] = CLASS_OF[name]
        # the plastics' extracted outlines are red all over (stock decals and lettering sit on red plastic)
        outl = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-outlines.json")))
        pim = Image.new("L", (tgt.shape[1], tgt.shape[0]), 0)
        pd = ImageDraw.Draw(pim)
        for name, poly in outl.items():
            if "_top" in name or "_bottom" in name or (name.endswith("_R") != (view == "right")) or len(poly) < 8:
                continue
            if name.startswith("front_fender_R"):
                continue                                  # merged with the fork guard and plate in the right photo
            uu, vv = cams.linear_to_px(view, np.array(poly)[:, 0], np.array(poly)[:, 1])
            pd.polygon([(float(x) / 2, float(y) / 2) for x, y in zip(uu, vv)], fill=1)
        tgt[np.asarray(pim) > 0] = RED
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
    score_other(parts_path, out_prefix, res)
    json.dump(res, open(f"{out_prefix}_scores.json", "w"), indent=1)
    return res


def intruders(parts_path, min_cm2=1.0):
    """Parts that show where the photo has red plastic. In each profile, inside the plastics' extracted outlines,
    the part in front must be a plastic: any other part there is poking through (a hidden rail placed too far out,
    a radiator wider than its shroud) or the plastic has a hole. Prints the offenders with their area."""
    data = np.load(parts_path)
    names = [str(n) for n in data["names"]]
    outl = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-outlines.json")))
    found = {}
    for view in ("left", "right"):
        pim = Image.new("L", (cams.W // 2, cams.H // 2), 0)
        pd = ImageDraw.Draw(pim)
        for name, poly in outl.items():
            if "_top" in name or "_bottom" in name or (name.endswith("_R") != (view == "right")) or len(poly) < 8:
                continue
            if name.startswith(("front_fender_R", "number_plate", "fork_guard")):
                continue                     # the fork, bars and hoses really are in front of these in the photo
            uu, vv = cams.linear_to_px(view, np.array(poly)[:, 0], np.array(poly)[:, 1])
            pd.polygon([(float(x) / 2, float(y) / 2) for x, y in zip(uu, vv)], fill=1)
        from scipy import ndimage
        tgt = ndimage.binary_erosion(np.asarray(pim) > 0, iterations=4)        # stay clear of the outlines' edges
        cls = raster(parts_path, None, view)
        part = raster(parts_path, None, view, by_part=True)
        bad = tgt & (cls != RED)
        px_cm2 = (2 * 0.0783) ** 2                                             # one half-res pixel in cm2
        for i in np.unique(part[bad]):
            area = float((part[bad] == i).sum() * px_cm2)
            if area >= min_cm2:
                found[(view, names[i - 1] if i else "(hole: background shows)")] = round(area, 1)
    for (view, name), area in sorted(found.items(), key=lambda t: -t[1]):
        print(f"  {view:5s} {name:28s} {area:7.1f} cm2 in front of the plastics")
    if not found:
        print("  nothing shows through the plastics")
    return found


PALETTE = {0: (255, 255, 255), RED: (214, 40, 30), BLACK: (38, 38, 40), DARK: (90, 90, 95), METAL: (168, 172, 180)}


def sheet(parts_path, out_path, views=("left", "right", "front", "rear", "top"), crops=None):
    """Honda's photo beside the model drawn through the same camera (material classes in flat colours), one row per
    view. For looking at what the scores cannot say: which part is wrong, and how."""
    ref = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
    crops = crops or {"left": (150, 3850, 250, 2150), "right": (150, 3850, 250, 2150), "front": (1250, 2750, 150, 2150),
                      "rear": (1250, 2750, 150, 2150), "top": (700, 3300, 500, 1750)}
    rows = []
    for view in views:
        u0, u1, v0, v1 = crops[view]
        ph = Image.open(os.path.join(ref, cams.FILES[view])).convert("RGB").crop((u0, v0, u1, v1))
        mdl = raster(parts_path, None, view, scale=2)
        col = np.zeros(mdl.shape + (3,), np.uint8)
        for k, c in PALETTE.items():
            col[mdl == k] = c
        mi = Image.fromarray(col).crop((u0 // 2, v0 // 2, u1 // 2, v1 // 2))
        h = 900
        w = int(round(h * (u1 - u0) / (v1 - v0)))
        row = Image.new("RGB", (2 * w + 10, h), (255, 255, 255))
        row.paste(ph.resize((w, h), Image.LANCZOS), (0, 0))
        row.paste(mi.resize((w, h), Image.LANCZOS), (w + 10, 0))
        rows.append(row)
    Wd = max(r.width for r in rows)
    out = Image.new("RGB", (Wd, sum(r.height + 10 for r in rows)), (255, 255, 255))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + 10
    out.save(out_path, quality=90)


if __name__ == "__main__":
    if sys.argv[1] == "intruders":
        intruders(sys.argv[2])
    elif sys.argv[1] == "sheet":
        sheet(sys.argv[2], sys.argv[3], tuple(sys.argv[4].split(",")) if len(sys.argv) > 4 else
              ("left", "right", "front", "rear", "top"))
    else:
        score(sys.argv[1], sys.argv[2])
