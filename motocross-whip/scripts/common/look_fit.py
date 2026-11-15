"""Fit the scene look (decision 54) on pixel-aligned pairs: his photo beside a scene-linear render of the same view.

python3 look_fit.py pairs OUT.npz VIEW=EXR [VIEW=EXR ...] --index INDEX.json
    VIEW: p07, p08, p09 (head_closeups.py's views of his photos, research/his-photo-cameras.json, rendered at its
    HIS_SCALE: the render box-averaged to the photo's crop lies on the photo pixel for pixel) or cam07 (the bike's
    camera fitted to his photo 07, research/rider-cameras.json, the whole frame at 2x). EXR: the view rendered with
    SCENE_LOOK=linear (scene_look.apply's "linear": multilayer float, albedo, depth and material index passes);
    INDEX.json the material index table it wrote (SCENE_LOOK_INDEX).
python3 look_fit.py fit PAIRS.npz --work DIR --out FIT.json
    every candidate look (MODELS, and "final": the shipped procedure) fitted on all three photos and on each two of
    them, the third held out; DIR caches decision 46's look on the pairs and the AgX table (both made by Blender)
python3 look_fit.py report PAIRS.npz --work DIR --out REPORT.json
    scene_look.apply(scene, "daylight") against decision 46's look, both through Blender, per view and class

Pairs keep only photo pixels whose 4x4 (2x2) render block is one material, one albedo class and away from the class's
edge (eroded by about the camera's landmark rms). Classes (trusted materials, the brief of decision 54): the
helmet's white shell and magenta print, its black print, the goggle's frame, the bike's red and black plastics, the
white boots, the sky; and the kit (jersey, pant, gloves) and the other prints. FIT_CLASSES says which had usable
pairs.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import exr          # noqa: E402
import scene_look   # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PHOTO_DIR = os.path.join(ROOT, "reference", "damien-bike-2026-11-12")
HIS = json.load(open(os.path.join(ROOT, "research", "his-photo-cameras.json")))["cameras"]
HIS_SCALE = 4          # head_closeups.HIS_SCALE
CAM_SCALE = 2          # head_closeups.photo_view's scale
VIEWS = {"p07": (HIS["07"]["photo"], tuple(HIS["07"]["crop"]), HIS_SCALE),
         "p08": (HIS["08"]["photo"], tuple(HIS["08"]["crop"]), HIS_SCALE),
         "p09": (HIS["09"]["photo"], tuple(HIS["09"]["crop"]), HIS_SCALE),
         "cam07": ("07_left-side-riding-pan.jpg", None, CAM_SCALE)}
TRUSTED = ("white", "magenta", "black", "frame", "red", "bike_black", "boot", "sky")
KIT = ("jersey_magenta", "jersey_lime", "jersey_teal", "jersey_dark", "pant_magenta", "pant_dark", "pant_lime",
       "glove", "teal", "purple")
CLASSES = TRUSTED + KIT
# the trusted classes the fit uses: the others had no usable pairs (research/scene-look.md, "Pairs"): the goggle's
# frame 8 px in p07 and off its thin part in p08; the sky a cream-white glow round the sun in the render, deep blue
# in his photos (the rig's sky, not the look); the bike's red and black and the boots in cam07 lie up to 15 px off
# (its camera's rms) on the bike and wherever the unfitted riding pose differs, and RED was tuned to the old look
FIT_CLASSES = ("white", "magenta", "black")
# the class masks are eroded by about the camera's landmark rms (his-photo-cameras.json: 2.6, 4.5, 8.3 px; cam07 14.8
# px, rider-cameras.json); a shift search inside the helmet gave a different best shift for each feature (p07:
# luminance (2, 6), its gradient (-1, 7), red-green chroma (9, -5) px), so the cameras are used as fitted
ERODE = {"p07": 3, "p08": 5, "p09": 8, "cam07": 8}
SKY_VIEWS = ("p08", "p09")    # his 07 has the street behind him, not the sky


def srgb_to_lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def box(a, s):
    h, w = a.shape[0] // s, a.shape[1] // s
    return a[:h * s, :w * s].reshape(h, s, w, s, *a.shape[2:])


def erode(m, r):
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o[1:] &= out[:-1]
        o[:-1] &= out[1:]
        o[:, 1:] &= out[:, :-1]
        o[:, :-1] &= out[:, 1:]
        out = o
    return out


def hsv(rgb):
    """Hue (deg), saturation, value of sRGB-encoded colours in 0..1."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def classify(mat, alb, sky, names):
    """Class of each photo pixel from the render's material and albedo (the Diffuse Color pass, read through the
    sRGB curve: hue, saturation and value of the paint itself, whatever the light on it)."""
    inv = {v: k for k, v in names.items()}
    nm = np.vectorize(lambda i: inv.get(int(i), ""))(mat).astype(str)
    h, s, v = hsv(scene_look.oetf(np.clip(alb, 0, 1)))
    white = (s < 0.1) & (v > 0.75)
    dark = v < 0.22
    sat = (s > 0.75) & (v > 0.3)
    magenta = sat & (h >= 310) & (h <= 350)
    red = sat & ((h >= 352) | (h <= 10))
    lime = sat & (h >= 60) & (h <= 100)
    teal = (s > 0.3) & (v > 0.4) & (h >= 150) & (h <= 200)
    purple = sat & (h >= 255) & (h <= 300)
    cls = np.full(mat.shape, "", object)
    helmet = nm == "helmet_paint"
    cls[helmet & white] = "white"
    cls[helmet & magenta] = "magenta"
    cls[helmet & dark] = "black"
    cls[helmet & teal] = "teal"
    cls[helmet & purple] = "purple"
    cls[nm == "goggle_frame"] = "frame"
    bike_red = np.isin(nm, ["livery_L", "livery_R", "livery_fender", "livery_top", "fender_front", "plate",
                            "plastic_red", "fork_guard"])
    cls[bike_red & red] = "red"
    cls[(bike_red | np.isin(nm, ["plastic_black", "black_texture"])) & dark] = "bike_black"
    boots = np.char.startswith(nm, "boot_")
    cls[boots & white] = "boot"
    jersey = np.isin(nm, ["jersey_print", "jersey_print_hd"])
    cls[jersey & magenta] = "jersey_magenta"
    cls[jersey & lime] = "jersey_lime"
    cls[jersey & teal] = "jersey_teal"
    cls[jersey & dark] = "jersey_dark"
    pant = nm == "pant_print"
    cls[pant & magenta] = "pant_magenta"
    cls[pant & dark] = "pant_dark"
    cls[pant & lime] = "pant_lime"
    cls[np.char.startswith(nm, "glove_fabric") & dark] = "glove"
    cls[sky] = "sky"
    return cls


def load_view(view, path, names):
    """Render blocks (linear mean, albedo, class) and the photo crop on the same pixels."""
    photo, crop, s = VIEWS[view]
    ch = exr.read(path)
    lin = exr.layer(ch, "Combined")[..., :3]
    alb = exr.layer(ch, "Diffuse Color")[..., :3]
    mat = exr.layer(ch, "Material Index")[..., 0]
    dep = exr.layer(ch, "Depth")[..., 0]
    B = box(lin, s)
    lin_b = B.mean((1, 3))
    alb_B = box(alb, s)
    alb_b = alb_B.mean((1, 3))
    alb_sd = alb_B.std((1, 3)).max(-1)
    M = box(mat, s)
    m0 = M[:, 0, :, 0]
    pure = (M == m0[:, None, :, None]).all((1, 3)) & (alb_sd < 0.03)
    sky = (box(dep, s) > 1e9).all((1, 3))
    cls = classify(np.where(pure, m0, -1), alb_b, sky, names)
    im = Image.open(os.path.join(PHOTO_DIR, photo)).convert("RGB")
    if crop:
        x, y, n = crop
        im = im.crop((x, y, x + n, y + n))
    ph = np.asarray(im).astype(np.float32) / 255.0
    h, w = lin_b.shape[:2]
    if ph.shape[:2] != (h, w):
        raise ValueError("%s: photo %s against render blocks %s" % (view, ph.shape[:2], (h, w)))
    return dict(lin=lin_b, alb=alb_b, cls=cls, photo=ph)


def pairs(out, specs, index):
    names = json.load(open(index))
    cols = {k: [] for k in ("view", "cls", "photo", "lin", "alb", "yx")}
    for spec in specs:
        view, path = spec.split("=")
        d = load_view(view, path, names)
        ph = d["photo"]
        print(view)
        for c in CLASSES:
            if c == "sky" and view not in SKY_VIEWS:
                continue
            m = erode(d["cls"] == c, ERODE[view])
            n = int(m.sum())
            if not n:
                continue
            yy, xx = np.nonzero(m)
            cols["view"] += [view] * n
            cols["cls"] += [c] * n
            cols["photo"].append(ph[m])
            cols["lin"].append(d["lin"][m])
            cols["alb"].append(d["alb"][m])
            cols["yx"].append(np.stack([yy, xx], -1))
            print("  %-15s %6d px  photo median %s" % (c, n, (np.median(ph[m], 0) * 255).round().astype(int).tolist()))
    np.savez_compressed(out, view=np.array(cols["view"]), cls=np.array(cols["cls"]),
                        photo=np.concatenate(cols["photo"]).astype(np.float32),
                        lin=np.concatenate(cols["lin"]).astype(np.float32),
                        alb=np.concatenate(cols["alb"]).astype(np.float32),
                        yx=np.concatenate(cols["yx"]).astype(np.int16))


# ---------------------------------------------------------------- the fit
MODELS = {  # name: (free parameters, base). Every model: saturation, then gains, then the base (scene_look.model)
    "standard_ev": (("ev",), "plain"),                          # the Standard view, exposure only
    "standard_wb": (("ev", "wr", "wb"), "plain"),               # and white balance
    "pbrn_sat": (("ev", "wr", "wb", "sat"), "pbrn"),            # Khronos PBR Neutral with gains and saturation
    "agx_sat": (("ev", "wr", "wb", "sat"), "agx"),              # AgX - Punchy with compositor gains and saturation
    "curve": (("ev", "wr", "wb", "p"), "standard"),             # the tone curve per channel (the curve mapping's)
    "curve_sat": (("ev", "wr", "wb", "p", "sat"), "standard"),  # and saturation
    "max": (("ev", "wr", "wb", "p"), "max"),                    # the tone curve on max(R,G,B), hue kept: the look
}
START = dict(ev=0.0, wr=0.0, wb=0.0, p=1.5, sat=1.0)
BOUNDS = dict(p=(0.5, 6.0), sat=(0.5, 2.5))
_AGX = {}


def agx_lut(cache):
    """AgX - Punchy at exposure 0, sampled by Blender itself on a grid of 2^t per channel (t -12..6, half stops) and
    read back by trilinear interpolation in t (its 8-bit output: within a level of Blender's)."""
    if "f" not in _AGX:
        from scipy.interpolate import RegularGridInterpolator
        t = np.arange(-12.0, 6.01, 0.5)
        if not os.path.exists(cache):
            T = np.stack(np.meshgrid(t, t, t, indexing="ij"), -1).reshape(-1, 3)
            np.save(cache, blender_look(2.0 ** T, "d46", 0.6).reshape(len(t), len(t), len(t), 3).astype(np.float32))
        _AGX["f"] = RegularGridInterpolator((t, t, t), np.load(cache))
    return _AGX["f"]


def params(model_name, x):
    names, base = MODELS[model_name]
    q = dict(START)
    q.update(zip(names, x))
    g = 2.0 ** q["ev"] * np.array([2.0 ** q["wr"], 1.0, 2.0 ** q["wb"]])
    return dict(gains=g, p=q["p"], sat=q["sat"], base=base)


def display(lin, gains, p, sat, base, agx_cache=None):
    """The candidate looks in numpy: scene_look.model for "standard", "pbrn" and "max", the plain Standard view, or AgX -
    Punchy through its Blender-sampled table."""
    if base in ("standard", "pbrn", "max"):
        return scene_look.model(lin, gains=gains, p=p, sat=sat, base=base)
    x = scene_look.saturate(lin, sat) * gains
    if base == "plain":
        return scene_look.oetf(np.clip(x, 0.0, 1.0))
    return agx_lut(agx_cache)(np.clip(np.log2(np.maximum(x, 2.0 ** -12)), -12.0, 6.0))


def weights(view, cls):
    """Every (view, class) group weighs the same, whatever its pixel count."""
    w = np.zeros(len(cls))
    for key in set(zip(view, cls)):
        m = (view == key[0]) & (cls == key[1])
        w[m] = 1.0 / m.sum()
    return w / w.sum()


def stats(disp, groups):
    """Per (view, class) group: CIELAB of the median colour, and L* of the 25 % and 75 % luminance quantiles (the
    shaded and the lit side: the tone curve's slope inside the class)."""
    out = []
    for m in groups:
        d = disp[m] * 255.0
        Y = d @ np.array(scene_look.LUMA)
        out.append(np.concatenate([lab(np.median(d, 0)), lab(np.repeat(np.percentile(Y, [25, 75])[:, None], 3, 1))[:, 0]]))
    return np.array(out)


def fit(P, views, classes=FIT_CLASSES, model_name="curve_sat", agx_cache=None, per_view_ev=False, fixed=None):
    """Least squares on what the report measures: per (view, class), its median colour's CIELAB and its quartiles'
    L*, render against photo (dE units), every group weighing the same, soft L1 at 10 (a class the look cannot reach,
    a material's error, pulls less). Pixels whose classes lie up to the cameras' rms off the photo's, and the
    lit / shade spread inside a class, made a per-pixel loss prefer spread over colour (AgX: pixels better, medians
    from 21 to 30 dE). per_view_ev: an exposure per photo (his phone's auto exposure) in place of the shared one,
    which is then their mean. fixed: parameters held at given values (the held-out photo's own exposure fit). Returns
    the free parameters and the model's arguments."""
    from scipy.optimize import least_squares
    keys = [(v, c) for v in views for c in classes if ((P["view"] == v) & (P["cls"] == c)).sum() >= 20]
    m = np.isin(P["view"], views) & np.isin(P["cls"], classes)
    lin = P["lin"][m]
    groups = [(P["view"][m] == v) & (P["cls"][m] == c) for v, c in keys]
    target = stats(P["photo"][m], groups)
    fixed = fixed or {}
    names = [n for n in MODELS[model_name][0] if n not in fixed and not (per_view_ev and n == "ev")]
    evs = ["ev_" + v for v in views] if per_view_ev else []
    vv = P["view"][m]

    def unpack(x):
        q = dict(fixed, **dict(zip(names, x)))
        if per_view_ev:
            q["ev"] = float(np.mean(x[len(names):]))
        return q

    def res(x):
        q = unpack(x)
        args = params(model_name, [q.get(n, START[n]) for n in MODELS[model_name][0]])
        li = lin
        if per_view_ev:
            off = np.zeros(len(lin))
            for v, e in zip(views, x[len(names):]):
                off[vv == v] = e - q["ev"]
            li = lin * 2.0 ** off[:, None]
        return (stats(display(li, agx_cache=agx_cache, **args), groups) - target).ravel()

    x0 = [START[n] for n in names] + [0.0] * len(evs)
    lo = [BOUNDS.get(n, (-8.0, 8.0))[0] for n in names + evs]
    hi = [BOUNDS.get(n, (-8.0, 8.0))[1] for n in names + evs]
    r = least_squares(res, x0, bounds=(lo, hi), loss="soft_l1", f_scale=10.0, diff_step=1e-2)
    q = unpack(r.x)
    out = {n: round(float(q[n]), 4) for n in MODELS[model_name][0] if n in q}
    out.update({e: round(float(v), 4) for e, v in zip(evs, r.x[len(names):])})
    return out, params(model_name, [q.get(n, START[n]) for n in MODELS[model_name][0]])


def load_pairs(paths):
    Ps = [dict(np.load(p)) for p in paths]
    return {k: np.concatenate([P[k] for P in Ps]) for k in Ps[0]}


def lab(rgb8):
    """CIELAB (D65) of sRGB-encoded 8-bit colours, for the medians' colour difference (CIE76 dE)."""
    x = srgb_to_lin(np.asarray(rgb8, float) / 255.0) @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192],
                                                                  [0.1805, 0.0722, 0.9505]])
    x = x / np.array([0.95047, 1.0, 1.08883])
    f = np.where(x > (6 / 29) ** 3, np.cbrt(x), x / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def blender_look(lin, kind, ev=0.0, blender="blender"):
    """Display values (0..1) of scene-linear pixels (N, 3) through scene_look.apply(scene, kind, ev) in Blender
    itself (look_apply.py: a render, view settings and compositor)."""
    import subprocess
    import tempfile
    n = len(lin)
    w = int(min(512, max(4, np.ceil(np.sqrt(n)))))
    h = max(4, -(-n // w))              # Blender renders at least 4 px each way (a smaller image gets black rows)
    a = np.zeros((h * w, 3), np.float32)
    a[:n] = lin
    with tempfile.TemporaryDirectory() as t:
        np.save(os.path.join(t, "in.npy"), a.reshape(h, w, 3))
        subprocess.run([blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python",
                        os.path.join(HERE, "look_apply.py"), "--", os.path.join(t, "in.npy"), os.path.join(t, "out.png"),
                        kind, str(ev)], check=True, capture_output=True)
        return np.asarray(Image.open(os.path.join(t, "out.png")).convert("RGB")).reshape(-1, 3)[:n] / 255.0


def table(P, looks, views=None, classes=CLASSES):
    """Rows per (view, class): n, the photo's median and each look's (8-bit), and per look the medians' dE and the
    pixels' mean |dRGB| (8-bit, per channel)."""
    rows = []
    for v in sorted(set(P["view"])) if views is None else views:
        for c in classes:
            m = (P["view"] == v) & (P["cls"] == c)
            if m.sum() < 20:
                continue
            ph = np.median(P["photo"][m] * 255.0, 0)
            row = dict(view=v, cls=c, n=int(m.sum()), photo=ph.round().astype(int).tolist())
            for name, disp in looks.items():
                md = np.median(disp[m] * 255.0, 0)
                row[name] = dict(median=md.round().astype(int).tolist(), dE=float(np.linalg.norm(lab(md) - lab(ph))),
                                 mae=float(np.abs(disp[m] - P["photo"][m]).mean() * 255.0))
            rows.append(row)
    return rows


def print_table(rows, names):
    print("%-6s %-15s %6s  %-15s" % ("view", "class", "n", "photo") +
          "".join("  %-15s %5s %5s" % (k, "dE", "mae") for k in names))
    for r in rows:
        print("%-6s %-15s %6d  %-15s" % (r["view"], r["cls"], r["n"], r["photo"]) +
              "".join("  %-15s %5.1f %5.1f" % (r[k]["median"], r[k]["dE"], r[k]["mae"]) for k in names))


def mean_dE(rows, look, views):
    d = [r[look]["dE"] for r in rows if r["view"] in views]
    return round(float(np.mean(d)), 1) if d else None


def before(P, work):
    """Decision 46's look (AgX - Punchy -0.6) on the pairs, through Blender (cached in the work folder)."""
    path = os.path.join(work, "before_d46.npy")
    if not os.path.exists(path) or len(np.load(path)) != len(P["lin"]):
        np.save(path, blender_look(P["lin"], "d46"))
    return np.load(path)


def white_balance(P, views):
    """His phone's white balance, read off the white shell (neutral paint): per photo, log2 of the photo's linear
    median over the render's, red and blue against green; the median over the photos."""
    r = []
    for v in views:
        m = (P["view"] == v) & (P["cls"] == "white")
        q = np.log2(srgb_to_lin(np.median(P["photo"][m], 0)) / np.median(P["lin"][m], 0))
        r.append((q[0] - q[1], q[2] - q[1]))
    return dict(wr=round(float(np.median([a for a, _ in r])), 4), wb=round(float(np.median([b for _, b in r])), 4))


FINAL = ("max", ("white", "black"))        # the shipped procedure: white balance from the shell, then ev and p


def own_exposure(P, view, x, wb):
    """A photo's own exposure (his phone's auto exposure for that shot): ev fitted on its white and black with the
    curve (p) and the white balance held."""
    e, _ = fit(P, [view], FINAL[1], FINAL[0], fixed=dict(wb, p=x["p"]))
    return e["ev"]


def fit_all(P, work, out):
    """Every candidate look, fitted on all three of his photos and on each pair of them (the third held out);
    mean dE of the class medians on the fitted and the held-out photos, before (decision 46) and after. "final":
    the shipped procedure: white balance from the white shell; the curve (p) fitted on the shell and the black
    print with one exposure per photo (his phone exposes each shot itself: a shared one bent p to make up the
    difference, 4.0 against 2.2 to 2.9 from each photo alone), the look's EV their mean; magenta a check on the
    materials. Its held-out photo is scored at that EV ("held_after") and at its own exposure ("held_own"), its
    fitted photos at the EV and at theirs ("fit_own")."""
    b = before(P, work)
    views = sorted(set(P["view"]))
    res = {}
    for name in list(MODELS) + ["final"]:
        res[name] = {}
        for hold in [None] + views:
            fv = [v for v in views if v != hold]
            own = None
            if name == "final":
                wb = white_balance(P, fv)
                x, q = fit(P, fv, FINAL[1], FINAL[0], fixed=wb, per_view_ev=True)
                if hold:
                    x["ev_" + hold] = round(float(own_exposure(P, hold, x, wb)), 4)
                own = np.ones(len(P["lin"]))
                for v in views:
                    own[P["view"] == v] = 2.0 ** (x["ev_" + v] - x["ev"])
            else:
                x, q = fit(P, fv, FIT_CLASSES, name, agx_cache=os.path.join(work, "agx_lut.npy"))
            d = display(P["lin"], agx_cache=os.path.join(work, "agx_lut.npy"), **q)
            looks = {"before": b, "after": d}
            if own is not None:
                looks["own"] = display(P["lin"] * own[:, None], **q)
            rows = table(P, looks, classes=FIT_CLASSES)
            key = "all" if hold is None else "hold " + hold
            res[name][key] = dict(params=x, fit_before=mean_dE(rows, "before", fv), fit_after=mean_dE(rows, "after", fv),
                                  held_before=mean_dE(rows, "before", [hold]), held_after=mean_dE(rows, "after", [hold]),
                                  rows=rows)
            if own is not None:
                res[name][key].update(fit_own=mean_dE(rows, "own", fv), held_own=mean_dE(rows, "own", [hold]))
            print("%-12s %-9s %s  fitted dE %s -> %s  held %s -> %s%s" % (
                name, key, x, res[name][key]["fit_before"], res[name][key]["fit_after"], res[name][key]["held_before"],
                res[name][key]["held_after"], "" if own is None else "  own exposure: fitted %s held %s" % (
                    res[name][key]["fit_own"], res[name][key]["held_own"])), flush=True)
    json.dump(res, open(out, "w"), indent=1)


def report(P, work, out):
    """The module's look (scene_look.apply "daylight") against decision 46's, both through Blender, per view and
    class."""
    b = before(P, work)
    a = blender_look(P["lin"], "daylight")
    rows = table(P, {"before": b, "after": a}, classes=FIT_CLASSES)
    print_table(rows, ["before", "after"])
    views = sorted(set(P["view"]))
    print("mean dE before %s after %s" % (mean_dE(rows, "before", views), mean_dE(rows, "after", views)))
    json.dump(rows, open(out, "w"), indent=1)


def red_test(rgb):
    """The bike's red plastic as an image shows it (sRGB-encoded 0..1): hue within 15 deg of red, saturation over
    0.5, value over 0.3. Applied alike to his photo and to our render's display."""
    h, s, v = hsv(rgb)
    return ((h >= 345) | (h <= 15)) & (s > 0.5) & (v > 0.3)


def red_stats(rgb):
    """Median and lit median (the top quartile by luma Y', Rec.709 weights on the encoded values: the red channel
    clips under the scene look, so the top quartile by value is ill-defined) of the red pixels, 8-bit, and their
    count."""
    y = rgb @ np.asarray(scene_look.LUMA)
    lit = rgb[y >= np.percentile(y, 75)]
    return dict(n=len(rgb), median=(np.median(rgb, 0) * 255).round(1).tolist(),
                lit=(np.median(lit, 0) * 255).round(1).tolist())


def bike_red(exr_path, index, red_srgb, work, ev7=0.0):
    """The bike's red in his photo 07 (cam07) against our render's plain red surfaces (albedo RED: plastic_red,
    fork_guard and the kit textures' plain red), through decision 46's look and the scene look (at the look's EV and
    at photo 07's own exposure, ev7 stops off it: fit.json "final"); and the albedo that brings the scene look's red
    (median and lit median) onto the photo's at photo 07's exposure."""
    names = json.load(open(index))
    d = load_view("cam07", exr_path, names)
    red_lin = srgb_to_lin(np.asarray(red_srgb, float) / 255.0)
    # the Diffuse Color pass carries the base colour under the clear coat's Fresnel loss (0.602 for RED's 0.631)
    a = d["alb"]
    plain = (a[..., 0] > 0.85 * red_lin[0]) & (a[..., 0] < 1.02 * red_lin[0]) & \
            (a[..., 1] < 2 * red_lin[1] + 0.004) & (a[..., 2] < 2 * red_lin[2] + 0.004)
    bike = np.isin(d["cls"], ["red", "bike_black"]) | plain
    region = ~erode(~bike, 15)                     # the bike's red parts and 15 px round them (cam07's rms)
    ph = d["photo"][region]
    photo = red_stats(ph[red_test(ph)])
    lin = d["lin"][erode(plain, 1)]
    out = dict(photo=photo, n_render=int(len(lin)))
    for key, kind, ev in (("d46", "d46", 0.0), ("daylight", "daylight", 0.0), ("daylight_ev7", "daylight", ev7)):
        disp = blender_look(lin, kind, ev)
        out[key] = red_stats(disp[red_test(disp)])
    # the albedo. Each plain red pixel: lin = alb E e + S, E the diffuse light on it (red channel), e the light's
    # colour (the white shell's lin / albedo in this render, against red), S a grey reflection (the clear coat and
    # the specular: the green channel is nearly all of it). A new albedo a: lin' = a E e + S; a fitted so that the
    # scene look's red (median and lit median, CIELAB) meets the photo's
    from scipy.optimize import least_squares
    alb = d["alb"][erode(plain, 1)]
    wm = d["cls"] == "white"
    e = np.median(d["lin"][wm] / np.maximum(d["alb"][wm], 1e-3), 0)
    e = e / e[0]
    E = np.maximum((lin[:, 0] - lin[:, 1]) / (alb[:, 0] - alb[:, 1] * e[1]), 0.0)
    S = np.maximum(lin[:, 1] - alb[:, 1] * e[1] * E, 0.0)

    def relit(a):
        return np.asarray(a)[None, :] * E[:, None] * e[None, :] + S[:, None]

    def look(a, blender=False):
        disp = blender_look(relit(a), "daylight", ev7) if blender else scene_look.display(relit(a), "daylight", ev7)
        return red_stats(disp[red_test(disp)])

    goal = np.concatenate([lab(photo["median"]), lab(photo["lit"])])

    def resid(la):
        disp = scene_look.display(relit(np.exp(la)), "daylight", ev7)
        if red_test(disp).sum() < 1000:                 # no longer a red: far off
            return np.full(6, 100.0)
        st = look(np.exp(la))
        return np.concatenate([lab(st["median"]), lab(st["lit"])]) - goal
    a0 = np.median(alb, 0)
    r = least_squares(resid, np.log(a0), diff_step=1e-2, bounds=(np.log(1e-4), 0.0))
    a_fit = np.exp(r.x)
    coat = float(np.median(alb[:, 0])) / red_lin[0]           # the Diffuse Color pass over the base colour
    base = np.clip(a_fit / coat, 0, 1)
    new8 = (scene_look.oetf(base) * 255).round().astype(int)
    # both checked through Blender: the old albedo relit (the model's own check against the render above) and the
    # new one rounded to 8 bits as build_bike.py takes it
    st_old = look(a0, True)
    st_new = look(srgb_to_lin(new8 / 255.0) * coat, True)

    def dE(st):
        return [round(float(np.linalg.norm(lab(st[k]) - lab(photo[k]))), 1) for k in ("median", "lit")]
    out.update(light_colour=e.round(3).tolist(), coat=round(coat, 3), reflection_median=round(float(np.median(S)), 4),
               relit_old=st_old, relit_new=st_new, red_new=new8.tolist(), dE_old=dE(st_old), dE_new=dE(st_new),
               dE_d46=dE(out["d46"]), dE_daylight=dE(out["daylight"]), dE_daylight_ev7=dE(out["daylight_ev7"]),
               ev7=ev7)
    print(json.dumps(out, indent=1))
    return out


def sheet(view, exr_path, out, panel_scale=2, ev=0.0, region=None, vertical=False):
    """A before / after sheet: his photo (Lanczos up to the panel scale) | decision 46's look | the scene look
    ("daylight" at ev), both renders from the view's linear EXR (box-averaged to panel_scale x the photo's pixels,
    then through Blender's look_apply). region "x0,y0,x1,y1" in the photo's (crop's) pixels; vertical stacks the
    panels (wide views)."""
    from PIL import ImageDraw, ImageFont
    photo, crop, s = VIEWS[view]
    lin = exr.layer(exr.read(exr_path), "Combined")[..., :3]
    im = Image.open(os.path.join(PHOTO_DIR, photo)).convert("RGB")
    if crop:
        x, y, n = crop
        im = im.crop((x, y, x + n, y + n))
    x0, y0, x1, y1 = (0, 0, im.width, im.height) if region is None else region
    im = im.crop((x0, y0, x1, y1))
    k = s // panel_scale
    lin = lin[y0 * s:y1 * s, x0 * s:x1 * s]
    lin = box(lin, k).mean((1, 3)) if k > 1 else lin
    panels = [np.asarray(im.resize((lin.shape[1], lin.shape[0]), Image.LANCZOS)).astype(float) / 255.0,
              blender_look(lin.reshape(-1, 3), "d46").reshape(lin.shape),
              blender_look(lin.reshape(-1, 3), "daylight", ev).reshape(lin.shape)]
    labels = ["his photo %s" % photo.split("_")[0], "AgX - Punchy -0.6 (decision 46)",
              "scene look, daylight (decision 54)%s" % ("" if ev == 0 else ", %+.2f EV" % ev)]
    font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", max(14, lin.shape[1] // 40)) \
        if os.path.exists("/usr/share/fonts/opentype/inter/Inter-Regular.otf") else ImageFont.load_default()
    tiles = []
    for p, t in zip(panels, labels):
        tile = Image.fromarray((np.clip(p, 0, 1) * 255).round().astype(np.uint8))
        bar = Image.new("RGB", (tile.width, font.size + 12), (24, 24, 24))
        ImageDraw.Draw(bar).text((8, 5), t, fill=(235, 235, 235), font=font)
        both = Image.new("RGB", (tile.width, tile.height + bar.height))
        both.paste(bar, (0, 0))
        both.paste(tile, (0, bar.height))
        tiles.append(both)
    g = 6
    if vertical:
        sh = Image.new("RGB", (tiles[0].width, sum(t.height for t in tiles) + 2 * g), (255, 255, 255))
        for i, t in enumerate(tiles):
            sh.paste(t, (0, i * (t.height + g)))
    else:
        sh = Image.new("RGB", (sum(t.width for t in tiles) + 2 * g, tiles[0].height), (255, 255, 255))
        for i, t in enumerate(tiles):
            sh.paste(t, (i * (t.width + g), 0))
    sh.save(out, quality=92)
    print("SHEET", out, sh.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "pairs":
        i = a.index("--index")
        pairs(a[1], a[2:i], a[i + 1])
    elif a[0] == "bike":                         # bike EXR INDEX R,G,B --work DIR --out OUT.json [--ev7 EV]
        res = bike_red(a[1], a[2], [int(v) for v in a[3].split(",")], a[a.index("--work") + 1],
                       float(a[a.index("--ev7") + 1]) if "--ev7" in a else 0.0)
        json.dump(res, open(a[a.index("--out") + 1], "w"), indent=1)
    elif a[0] == "sheet":                        # sheet VIEW EXR OUT.jpg [--scale S] [--ev EV] [--region x0,y0,x1,y1] [--vertical]
        opt = {k: a[a.index(k) + 1] for k in ("--scale", "--ev", "--region") if k in a}
        sheet(a[1], a[2], a[3], int(opt.get("--scale", 2)), float(opt.get("--ev", 0.0)),
              tuple(int(v) for v in opt["--region"].split(",")) if "--region" in opt else None, "--vertical" in a)
    elif a[0] in ("fit", "report"):
        P = load_pairs([a[1]])
        work, out = a[a.index("--work") + 1], a[a.index("--out") + 1]
        (fit_all if a[0] == "fit" else report)(P, work, out)
