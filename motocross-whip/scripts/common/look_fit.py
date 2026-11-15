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
python3 look_fit.py bike EXR INDEX.json REDS --out OUT.json [--ev7 EV] [--also NAME=R,G,B;...]
    the bike's red in his 07 (cam07's EXR) under the scene look at photo 07's exposure (scene_look.PHOTO_EV), and
    the albedo that matches it on the plastic's diffuse body (the plain red pixels with little gloss, their diffuse
    light alone; the photo's red_test pixels), every red relit with the diffuse light passes (bike_red). REDS: the
    reds the render holds, "R,G,B[;R,G,B]" (8-bit base colours); --also other reds to report
python3 look_fit.py honda VIEW EXR INDEX.json REDS --out OUT.json [--ev EV] [--also NAME=R,G,B;...]
    the same against Honda's studio photo of VIEW (build_bike.py's honda_<VIEW>, stock, SCENE_LOOK=linear, at
    BIKE_STUDIO_RES 2000,1125) under the studio look at EV (build_bike.STUDIO's) on all of the red (honda_red)
python3 look_fit.py gear OUT.json VIEW=EXR [VIEW=EXR ...] --index INDEX.json [--no-tint]
    the kit, gloves and boots (and the bike's tyres, a neutral check) in his views p07, p08, p09 and cam07 (linear
    EXRs with the diffuse passes) at each photo's exposure and tint of its darks (scene_look.PHOTO_EV, PHOTO_TINT;
    --no-tint leaves the tint out): colour-gated regions on both sides, each its diffuse body, and the albedo and
    the albedo that meets the photo at each scale of the rest (specular, sheen, coat; gear, decision 59)
python3 look_fit.py darks OUT.json VIEW=EXR [VIEW=EXR ...] --index INDEX.json
    his phone's lift of the darks and 07's tint (scene_look.DARK_LIFT, PHOTO_TINT) fitted on the neutral blacks
    outside the gear (the helmet's black print in p07 and p08, the tyres in cam07), the gear's darks held out
    (dark_fit; decision 59)
python3 look_fit.py boot_white OUT.json
    the boots' white against the helmet's white shell in each photo of his that sees them (BOOT_BOXES; decision 59)
python3 look_fit.py sheet VIEW EXR OUT.jpg [--scale S] [--ev EV] [--region x0,y0,x1,y1] [--vertical]
    photo | decision 46's look | the scene look, for the checkpoints (sheet)

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
    cls[(nm == "tyre") & dark] = "tyre"                  # the bike's black rubber: a neutral check (decision 59)
    cls[sky] = "sky"
    return cls


def load_view(view, path, names):
    """Render blocks (linear mean, albedo, class) and the photo crop on the same pixels; with the diffuse light
    passes (decision 55's renders), "light" too: Diffuse Direct + Indirect, so that a block's colour with another
    albedo is lin + light x (new - old) (relight)."""
    photo, crop, s = VIEWS[view]
    ch = exr.read(path)
    lin = exr.layer(ch, "Combined")[..., :3]
    alb = exr.layer(ch, "Diffuse Color")[..., :3]
    mat = exr.layer(ch, "Material Index")[..., 0]
    dep = exr.layer(ch, "Depth")[..., 0]
    try:
        light = exr.layer(ch, "Diffuse Direct")[..., :3] + exr.layer(ch, "Diffuse Indirect")[..., :3]
        light_b = box(light, s).mean((1, 3))
    except KeyError:
        light_b = None
    try:                                         # round 2b's renders: the gloss (specular layer and clear coat)
        gloss_b = box(gloss(ch), s).mean((1, 3))
    except KeyError:
        gloss_b = None
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
    return dict(lin=lin_b, alb=alb_b, cls=cls, photo=ph, light=light_b, gloss=gloss_b)


def gloss(ch):
    """The render's gloss: (Glossy Direct + Indirect) x Glossy Color, the specular layer and the clear coat (what
    the surroundings put on a surface: Cycles' coat is a glossy closure). KeyError without the passes."""
    return (exr.layer(ch, "Glossy Direct")[..., :3] + exr.layer(ch, "Glossy Indirect")[..., :3]) * \
        exr.layer(ch, "Glossy Color")[..., :3]


def relight(lin, light, alb, new):
    """A pixel's scene-linear colour with another diffuse albedo: Combined = the diffuse light x the albedo (the
    Diffuse Color pass) + the rest (specular, clear coat, sheen), so lin + light x (new - alb). Exact but for the
    light the surface throws back on others (interreflection)."""
    return lin + light * (np.asarray(new, float) - alb)


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


def blender_look(lin, kind, ev=0.0, blender="blender", tint=None):
    """Display values (0..1) of scene-linear pixels (N, 3) through scene_look.apply(scene, kind, ev, tint) in Blender
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
                        kind, str(ev)] + ([",".join(map(repr, tint))] if tint else []), check=True, capture_output=True)
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
    """The bike's red plastic's body as an image shows it (sRGB-encoded 0..1; decision 55 round 2b, the coordinator's
    gate on his 07): red the largest channel, saturation over 0.5, value over 77 / 255, G and B each under 0.45 R.
    The clear coat's pinkish highlights (the surroundings in it) fail it. Applied alike to the photos and to our
    renders' display. (Round 2's gate, hue within 15 deg of red, kept the highlights.)"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    s = (mx - rgb.min(-1)) / (mx + 1e-9)
    return (r >= mx) & (s > 0.5) & (mx > 77 / 255) & (g < 0.45 * r) & (b < 0.45 * r)


def red_stats(rgb):
    """Median and lit median (the top quartile by luma Y', Rec.709 weights on the encoded values: the red channel
    clips under the scene look, so the top quartile by value is ill-defined) of the red pixels, 8-bit, and their
    count."""
    y = rgb @ np.asarray(scene_look.LUMA)
    lit = rgb[y >= np.percentile(y, 75)]
    return dict(n=len(rgb), median=(np.median(rgb, 0) * 255).round(1).tolist(),
                lit=(np.median(lit, 0) * 255).round(1).tolist())


def plain_red(alb, reds):
    """The render's plain red surfaces: the Diffuse Color pass at one of the plastic's reds (8-bit sRGB base
    colours: a blend's material may hold an older red than the textures), and each pixel's coat factor (the pass over
    the base colour: the clear coat's Fresnel loss, neutral, 0.955 for the plastic). A pixel's red is the one nearest
    to its G / R and B / R; it passes when its R is 0.85 to 1.02 of that red's and its G and B under twice."""
    reds = np.atleast_2d(np.asarray(reds, float))
    lr = srgb_to_lin(reds / 255.0)
    ratio = alb[..., 1:] / np.maximum(alb[..., :1], 1e-6)
    near = np.argmin([np.abs(ratio - r[1:] / r[0]).sum(-1) for r in lr], 0)
    r = lr[near]
    m = (alb[..., 0] > 0.85 * r[..., 0]) & (alb[..., 0] < 1.02 * r[..., 0]) & \
        (alb[..., 1] < 2 * r[..., 1] + 0.004) & (alb[..., 2] < 2 * r[..., 2] + 0.004)
    return m, alb[..., 0] / r[..., 0]


# the render's diffuse body (decision 55, round 2b): plain red pixels whose gloss (the specular layer and the coat:
# the surroundings) is under this share of their colour, channels summed; the fit takes their diffuse light alone
GLOSS_SHARE = 0.2


def red_colour(R, a, part):
    """Scene-linear colour of the red pixels R (dict: lin, light, alb) with albedo a (Diffuse Color pass units):
    "body" the diffuse body alone, light x a (no reflection); "all" everything (relight: the gloss and the rest
    kept)."""
    return R["light"] * np.asarray(a, float) if part == "body" else relight(R["lin"], R["light"], R["alb"], a)


def fit_red(R, photo, look, part="body", a0=None):
    """The albedo (Diffuse Color pass units) whose red, every pixel of R (red_colour's part) put through look
    (scene-linear to display) and red_test, meets the photo's (red_stats: median and lit median, CIELAB)."""
    from scipy.optimize import least_squares
    goal = np.concatenate([lab(photo["median"]), lab(photo["lit"])])

    def resid(la):
        disp = look(red_colour(R, np.exp(la), part))
        ok = red_test(disp)
        if ok.sum() < 0.2 * len(disp):                 # no longer a red: far off
            return np.full(6, 100.0)
        st = red_stats(disp[ok])
        return np.concatenate([lab(st["median"]), lab(st["lit"])]) - goal
    x0 = np.log(np.maximum(np.median(R["alb"], 0) if a0 is None else a0, 2e-4))
    r = least_squares(resid, x0, diff_step=1e-2, bounds=(np.log(1e-4), 0.0))
    return np.exp(r.x)


def red_result(R, photo, coat, reds8, kind, ev):
    """Each red of reds8 (name: 8-bit sRGB base colour, as build_bike.RED takes it) on the pixels R, its body and all
    of it, through Blender's own look, against the photo's (dE76 of the median and the lit median), and what the
    surroundings add (all minus body, 8-bit medians)."""
    def st(a, part):
        disp = blender_look(red_colour(R, a, part), kind, ev)
        return red_stats(disp[red_test(disp)])

    def dE(s):
        return [round(float(np.linalg.norm(lab(s[k]) - lab(photo[k]))), 1) for k in ("median", "lit")]
    out = {}
    for name, c8 in reds8.items():
        a = srgb_to_lin(np.asarray(c8, float) / 255.0) * coat
        body, both = st(a, "body"), st(a, "all")
        out[name] = dict(red=list(c8), body=body, all=both, dE_body=dE(body), dE_all=dE(both),
                         surroundings=[round(x - y, 1) for x, y in zip(both["median"], body["median"])])
    return out


def to_red8(a_fit, coat):
    """A fitted albedo (pass units) as build_bike.RED takes it: the base colour under the coat's loss, 8-bit sRGB."""
    return (scene_look.oetf(np.clip(np.asarray(a_fit) / coat, 0, 1)) * 255).round().astype(int).tolist()


def bike_red(exr_path, index, reds, ev7=0.0, also=None):
    """The bike's red in his photo 07 (cam07's EXR with the diffuse and gloss passes) against our render's plain red
    surfaces (plain_red: plastic_red, fork_guard and the kit textures' plain red) under the scene look at photo 07's
    own exposure (ev7: scene_look.PHOTO_EV), on the plastic's diffuse body (decision 55, round 2b): in the render the
    plain red pixels whose gloss is under GLOSS_SHARE, their diffuse light alone; in the photo the red pixels that
    pass red_test (the coat's highlights do not) on the bike's red parts and 15 px round them (cam07's rms). Returns
    the albedo that brings the body's red (median and lit median) onto the photo's, and every red's numbers (the
    render's own reds, the fit's, and also: name -> 8-bit)."""
    d = load_view("cam07", exr_path, json.load(open(index)))
    if d["light"] is None or d["gloss"] is None:
        raise SystemExit("%s has no diffuse and gloss passes: render it with scene_look's linear kind" % exr_path)
    plain, coat = plain_red(d["alb"], reds)
    bike = np.isin(d["cls"], ["red", "bike_black"]) | plain
    region = ~erode(~bike, 15)                     # the bike's red parts and 15 px round them (cam07's rms)
    ph = d["photo"][region]
    photo = red_stats(ph[red_test(ph)])
    m = erode(plain, 1)
    share = d["gloss"].sum(-1) / np.maximum(d["lin"].sum(-1), 1e-9)
    body = m & (share < GLOSS_SHARE)
    R = {k: d[k][body] for k in ("lin", "light", "alb")}
    coat = float(np.median(coat[body]))
    look = lambda x: scene_look.display(x, "daylight", ev7)          # noqa: E731
    a = fit_red(R, photo, look, "body", srgb_to_lin(np.asarray(reds[-1], float) / 255.0) * coat)
    fit8 = to_red8(a, coat)
    reds8 = {"render_%d" % i: list(r) for i, r in enumerate(reds)}
    reds8.update(also or {})
    reds8["fit"] = fit8
    out = dict(view="cam07", photo=photo, n_plain=int(m.sum()), n_body=int(body.sum()),
               gloss_share_median=round(float(np.median(share[m])), 3), coat=round(coat, 3), fit_pass=a.round(4).tolist(),
               red_fit=fit8, reds=red_result(R, photo, coat, reds8, "daylight", ev7), kind="daylight", ev=ev7)
    print(json.dumps(out, indent=1))
    return out


HONDA_DIR = os.path.join(ROOT, "reference", "crf250r-2026")
HONDA = {"left": "studio_left-profile_honda-eu-25ym-475600_4000x2250.jpg",       # bike/pair.py FILES
         "right": "studio_right-profile_honda-eu-25ym-475596_4000x2250.jpg",
         "lf34": "studio_left-front-34_honda-eu-25ym-475601_4000x2250.jpg",
         "rf34": "studio_right-front-34_honda-eu-25ym-475595_4000x2250.jpg"}


def honda_photo(view, shape):
    """Honda's studio photo of a view, box-averaged in linear light to a render's pixels (half its 4000 x 2250),
    sRGB-encoded 0..1."""
    im = Image.open(os.path.join(HONDA_DIR, HONDA[view])).convert("RGB")
    s = im.width // shape[1]
    return scene_look.oetf(box(srgb_to_lin(np.asarray(im).astype(np.float32) / 255.0), s).mean((1, 3)))


def honda_red(exr_path, index, view, reds, ev, also=None):
    """The same for Honda's studio photo of a view (build_bike.py's honda_<view> camera, rendered stock at half the
    photo's 4000 x 2250) under the studio look (Standard at ev, build_bike.STUDIO): the plain red, eroded 2 px (the
    studio cameras' fit), where the photo passes red_test too (Honda's white and black graphics and the coat's
    highlights do not). Honda's photo holds their studio's reflections, so the comparison is on all of the red
    ("all"); the albedo fitted to it alone is Honda's own best (not used: one red, his 07's, decision 55)."""
    ch = exr.read(exr_path)
    lin = exr.layer(ch, "Combined")[..., :3]
    alb = exr.layer(ch, "Diffuse Color")[..., :3]
    try:
        light = exr.layer(ch, "Diffuse Direct")[..., :3] + exr.layer(ch, "Diffuse Indirect")[..., :3]
    except KeyError:                                # decision 54's linear renders: the red as rendered, no fit
        light = None
    mat = exr.layer(ch, "Material Index")[..., 0]
    names = json.load(open(index))
    reds_m = [names[n] for n in names if n.startswith("livery") or n in ("plastic_red", "fork_guard", "fender_front")]
    ph = honda_photo(view, lin.shape)
    plain, coat = plain_red(alb, reds)
    plain = erode(plain & np.isin(mat, reds_m), 2)
    photo_px = ph[plain]
    keep = red_test(photo_px)
    photo = red_stats(photo_px[keep])
    m = np.zeros_like(plain)
    m[plain] = keep                                 # the render's pixels where the photo is plain red too
    if light is None:
        disp = blender_look(lin[m], "studio", ev)
        st = red_stats(disp[red_test(disp)])
        out = dict(view="honda_" + view, photo=photo, n_render=int(m.sum()), n_plain=int(plain.sum()), reds={
            "render_0": dict(red=list(reds[0]), all=st, dE_all=[round(float(np.linalg.norm(lab(st[k]) - lab(photo[k]))), 1)
                                                               for k in ("median", "lit")])}, kind="studio", ev=ev)
        print(json.dumps(out, indent=1))
        return out
    R = dict(lin=lin[m], light=light[m], alb=alb[m])
    coat = float(np.median(coat[m]))
    a = fit_red(R, photo, lambda x: scene_look.display(x, "studio", ev), "all")
    reds8 = {"render_%d" % i: list(r) for i, r in enumerate(reds)}
    reds8.update(also or {})
    reds8["honda_own"] = to_red8(a, coat)
    out = dict(view="honda_" + view, photo=photo, n_render=int(m.sum()), n_plain=int(plain.sum()), coat=round(coat, 3),
               reds=red_result(R, photo, coat, reds8, "studio", ev), kind="studio", ev=ev)
    print(json.dumps(out, indent=1))
    return out


# ---------------------------------------------------------------- the gear (decision 59)
# The kit, gloves and boots against his photos. The pose is not fitted to his photos, so there are no pixel pairs:
# colour-gated regions. Render: the class's pixels; photo: the pixels inside the garment's render mask dilated
# GEAR_REGION px (about the pose's error; the helmet, goggle and bike classes taken out) that pass the same colour
# gate. Each class: (garment, gate); the tyre is the bike's black rubber, a neutral check on the darks.
GEAR = {"jersey_magenta": ("jersey", "magenta"), "jersey_lime": ("jersey", "lime"), "jersey_teal": ("jersey", "teal"),
        "jersey_dark": ("jersey", "dark"), "pant_magenta": ("pant", "magenta"), "pant_lime": ("pant", "lime"),
        "pant_dark": ("pant", "dark"), "glove": ("glove", "dark"), "boot": ("boot", "white"), "tyre": ("tyre", "dark")}
GARMENT = {g: tuple(c for c, (gg, _) in GEAR.items() if gg == g) for g in ("jersey", "pant", "glove", "boot", "tyre")}
GEAR_EXCLUDE = ("white", "magenta", "black", "teal", "purple", "frame", "red", "bike_black")
GEAR_REGION = {"p07": 20, "p08": 20, "p09": 20, "cam07": 25}
GEAR_BODY = 90          # the diffuse body: each side's pixels under the class's 90th luminance percentile (glints out)
GEAR_K = (0.5, 1.0, 2.0)  # gear_fit: the albedo at these scales of the grey layer (1: as now)


def gear_gate(rgb, kind):
    """The colour gates (sRGB-encoded 0..1), the same on photo and render: pink hue 315 to 352, lime 55 to 110, teal
    150 to 205, dark value under 0.3 and saturation under 0.6, white saturation under 0.2 and value over 0.6."""
    h, s, v = hsv(rgb)
    return {"magenta": (s > 0.45) & (v > 0.2) & (h >= 315) & (h <= 352),
            "lime": (s > 0.45) & (v > 0.3) & (h >= 55) & (h <= 110),
            "teal": (s > 0.25) & (v > 0.3) & (h >= 150) & (h <= 205),
            "dark": (v < 0.3) & (s < 0.6),
            "white": (s < 0.2) & (v > 0.6)}[kind]


def luma_L(rgb):
    """L* of the 10 % and 90 % luminance quantiles (the shade and the lit side) of display pixels (0..1)."""
    Y = (rgb * 255.0) @ np.array(scene_look.LUMA)
    return lab(np.repeat(np.percentile(Y, [10, 90])[:, None], 3, 1))[:, 0]


def gear_stats(rgb):
    """Median (8-bit), its L*, C*, hue, and the L* of the 10 % and 90 % luminance quantiles."""
    med = np.median(rgb * 255.0, 0)
    L = lab(med)
    q = luma_L(rgb)
    return dict(n=int(len(rgb)), median=med.round().astype(int).tolist(), L=round(float(L[0]), 1),
                C=round(float(np.hypot(L[1], L[2])), 1), h=int(round(float(np.degrees(np.arctan2(L[2], L[1])) % 360))),
                q10=round(float(q[0]), 1), q90=round(float(q[1]), 1))


def body(rgb, keep=None):
    """The diffuse body: the pixels under the GEAR_BODY luminance percentile (a mask; keep: restrict to it first)."""
    Y = rgb @ np.array(scene_look.LUMA)
    m = np.ones(len(rgb), bool) if keep is None else keep.copy()
    return m & (Y <= np.percentile(Y[m], GEAR_BODY))


def gear_fit(lin, light, alb, photo, look, ks=GEAR_K):
    """What the material should do. Each class pixel is its diffuse part D = light x albedo (Diffuse Direct +
    Indirect times the Diffuse Color pass) and the rest G = Combined - D (specular, sheen, coat); one albedo a for
    the class (pass units) at a scale k of the rest, lin' = D a / albedo + k G, fitted so that the diffuse body's
    median (CIELAB) and q10 and q90 L* meet the photo's body's; for each k in ks (1: the grey layer as now). The
    body's numbers cannot tell k from the albedo (classes made with k 0.6 fit as well at k 2.3 with a third of the
    albedo, test_gear_look.py): k is the maker's studio photos' to say (the highlights), the albedo then follows
    from his photos at that k. rest_share = G's share of the pixel's light now (median)."""
    from scipy.optimize import least_squares
    D = light * alb
    G = np.maximum(lin - D, 0.0)
    goal = np.concatenate([lab(np.median(photo * 255.0, 0)), luma_L(photo)])
    a0 = np.maximum(np.median(alb, 0), 1e-3)
    share = float(np.median((G @ np.array(scene_look.LUMA)) / np.maximum(lin @ np.array(scene_look.LUMA), 1e-6)))
    out = dict(albedo8_now=(scene_look.oetf(a0) * 255).round().astype(int).tolist(), rest_share=round(share, 3), k={})
    for k in ks:
        def lin_of(x):
            return D * (np.exp(x) / np.maximum(alb, 1e-4)) + k * G

        def resid(x):
            d = look(lin_of(x))
            d = d[body(d)]
            return np.concatenate([lab(np.median(d * 255.0, 0)), luma_L(d)]) - goal
        r = least_squares(resid, np.log(a0), diff_step=1e-2, bounds=(np.full(3, np.log(1e-4)), np.zeros(3)))
        a = np.exp(r.x)
        d = look(lin_of(r.x))
        out["k"][str(k)] = dict(albedo=a.round(4).tolist(), albedo8=(scene_look.oetf(a) * 255).round().astype(int).tolist(),
                                fitted=gear_stats(d[body(d)]), resid=np.round(r.fun, 1).tolist())
    return out


def gear_region(d, view, c):
    """One gear class in a loaded view (load_view): the photo's pixels (inside the garment's render mask dilated
    GEAR_REGION px, the helmet, goggle and bike classes out, through the class's colour gate) and the render's class
    pixels through the same gate under the look without the photo's tint (the material's pixels: a tint must not
    move pixels in or out of the gate). Returns (photo px, render lin, render light, render albedo) or None."""
    garment, kind = GEAR[c]
    cls = d["cls"]
    rm = cls == c
    if rm.sum() < 50:
        return None
    excl = ~erode(~np.isin(cls, GEAR_EXCLUDE), 3)
    region = ~erode(~np.isin(cls, GARMENT[garment]), GEAR_REGION[view]) & ~excl
    ph = d["photo"][region]
    ph = ph[gear_gate(ph, kind)]
    g = gear_gate(scene_look.display(d["lin"][rm], "daylight", scene_look.photo_ev(view)), kind)
    if len(ph) < 50 or g.sum() < 20:
        return None
    pick = lambda k: None if d.get(k) is None else d[k][rm][g]                   # noqa: E731
    return ph, pick("lin"), pick("light"), pick("alb")


def gear(view, exr_path, index, tint=True, fit=True):
    """The gear's classes in one of his views (p07, p08, p09 or cam07; a linear EXR with the diffuse passes) at the
    photo's exposure (scene_look.photo_ev) and, with tint, its tint of the darks (scene_look.photo_tint): photo and
    ours (each its diffuse body), dE of the medians, and the material fit (gear_fit). Rows per class."""
    d = load_view(view, exr_path, json.load(open(index)))
    if d["light"] is None:
        raise SystemExit("%s has no diffuse light passes: render it with scene_look's linear kind" % exr_path)
    ev = scene_look.photo_ev(view)
    t = scene_look.photo_tint(view) if tint else None
    look = lambda x: scene_look.display(x, "daylight", ev, t)                  # noqa: E731
    rows = []
    for c in GEAR:
        r = gear_region(d, view, c)
        if r is None:
            continue
        ph, lin, light, alb = r
        disp = look(lin)
        ph_b, ours_b = ph[body(ph)], disp[body(disp)]
        row = dict(view=view, cls=c, ev=ev, tint=t, photo=gear_stats(ph_b), ours=gear_stats(ours_b),
                   dE=round(float(np.linalg.norm(lab(np.median(ours_b * 255, 0)) - lab(np.median(ph_b * 255, 0)))), 1))
        if fit and c != "tyre":
            row["fit"] = gear_fit(lin, light, alb, ph_b, look)
        rows.append(row)
        f = lambda s: "%-15s L%3.0f C%3.0f h%3d q%3.0f-%-3.0f" % (str(s["median"]), s["L"], s["C"], s["h"], s["q10"],  # noqa: E731
                                                                  s["q90"])
        print("%-5s %-15s n %5d/%5d | photo %s | ours %s | dE %5.1f%s" % (
            view, c, row["photo"]["n"], row["ours"]["n"], f(row["photo"]), f(row["ours"]), row["dE"],
            "" if "fit" not in row else " | albedo %s, rest %2.0f%% -> at k %s" % (
                row["fit"]["albedo8_now"], 100 * row["fit"]["rest_share"], ", ".join(
                    "%s %s (dE %.1f)" % (k, q["albedo8"], float(np.linalg.norm(q["resid"][:3])))
                    for k, q in row["fit"]["k"].items()))), flush=True)
    return rows


# ---------------------------------------------------------------- the darks (decision 59)
# scene_look.DARK_LIFT and PHOTO_TINT["07"], fitted on the neutral blacks outside the gear: the helmet's black print
# (pixel pairs, the class eroded by ERODE) in his 07 and 08 and the tyres' rubber in cam07 (gear_region); his 09's
# black print has no pairs at its camera's rms, the gear's darks are held out. Each set's median, CIELAB.
DARKS_FIT = (("p07", "black"), ("p08", "black"), ("cam07", "tyre"))
DARKS_HELD = ("jersey_dark", "pant_dark", "glove")


def dark_sets(specs, index):
    """{(view, class): (photo px, render lin)}: the black print's pairs and the dark gear classes' bodies."""
    names = json.load(open(index))
    sets = {}
    for spec in specs:
        view, path = spec.split("=")
        d = load_view(view, path, names)
        m = erode(d["cls"] == "black", ERODE[view])
        if m.sum() >= 20:
            sets[(view, "black")] = (d["photo"][m], d["lin"][m])
        for c in ("tyre",) + DARKS_HELD:
            r = gear_region(d, view, c)
            if r is not None:
                ph, lin = r[0], r[1]
                base = scene_look.display(lin, "daylight", scene_look.photo_ev(view))
                sets[(view, c)] = (ph[body(ph)], lin[body(base)])
    return sets


def dark_fit(sets):
    """One neutral lift for all his photos and 07's tint on top (x = lift, tint R, G, B; display units), least
    squares on the CIELAB medians of DARKS_FIT. Returns x and per set the photo's median and ours before (no lift),
    with the lift as shipped (scene_look's) and with x."""
    from scipy.optimize import least_squares
    lift0 = scene_look.DARK_LIFT

    def ours(key, x):
        v = key[0]
        scene_look.DARK_LIFT = 0.0
        d = scene_look.display(sets[key][1], "daylight", scene_look.photo_ev(v))
        scene_look.DARK_LIFT = lift0
        if x is None:
            return np.median(d * 255.0, 0)
        o = np.full(3, x[0]) + (np.asarray(x[1:4]) if scene_look.photo_tint(v) is not None else 0.0)
        return np.median(scene_look.lift(d, o) * 255.0, 0)
    fit_keys = [k for k in DARKS_FIT if k in sets]
    r = least_squares(lambda x: np.concatenate([lab(ours(k, x)) - lab(np.median(sets[k][0] * 255.0, 0))
                                                for k in fit_keys]),
                      np.array([0.03, 0.0, 0.0, 0.05]), bounds=([-0.05] + [-0.1] * 3, [0.3] * 4))
    x = r.x
    shipped = np.r_[lift0, scene_look.PHOTO_TINT.get("07", (0.0, 0.0, 0.0))]
    rows = []
    for k in sets:
        ph = np.median(sets[k][0] * 255.0, 0)
        row = dict(view=k[0], cls=k[1], fitted=k in fit_keys, n=[len(sets[k][0]), len(sets[k][1])],
                   photo=ph.round().astype(int).tolist())
        for nm, xx in (("before", None), ("shipped", shipped), ("fit", x)):
            q = ours(k, xx)
            row[nm] = q.round().astype(int).tolist()
            row["dE_" + nm] = round(float(np.linalg.norm(lab(q) - lab(ph))), 1)
        rows.append(row)
        print("%-5s %-12s %-4s photo %-15s | before %-15s %5.1f | shipped %-15s %5.1f | fit %-15s %5.1f" % (
            k[0], k[1], "FIT" if row["fitted"] else "held", row["photo"], row["before"], row["dE_before"],
            row["shipped"], row["dE_shipped"], row["fit"], row["dE_fit"]))
    out = dict(lift=round(float(x[0]), 4), tint07=np.round(x[1:], 4).tolist(), rows=rows)
    for grp in (True, False):
        rr = [q for q in rows if q["fitted"]] if grp else [q for q in rows if q["cls"] in DARKS_HELD]
        for nm in ("before", "shipped", "fit"):
            out["mean_%s_%s" % ("fitted" if grp else "held", nm)] = round(float(np.mean([q["dE_" + nm] for q in rr])), 1)
    print("lift %.4f (%.1f levels), 07's tint %s; mean dE fitted %s -> %s, held out %s -> %s" % (
        x[0], x[0] * 255, out["tint07"], out["mean_fitted_before"], out["mean_fitted_fit"], out["mean_held_before"],
        out["mean_held_fit"]))
    return out


# ---------------------------------------------------------------- the boots' white (decision 59)
# Every photo of his that sees the boots: the boot's white against the helmet's white shell in the same photo (the
# same sun, the same exposure). Boxes (x0, y0, x1, y1, full-resolution pixels) round each boot and the helmet.
BOOT_BOXES = {"05": ("damien-bike-2026-11-10/05_damien-seated-left-side.jpg",
                     [(368, 864, 448, 1040), (272, 1024, 392, 1144)], (248, 360, 408, 512)),
              "06": ("damien-bike-2026-11-12/06_whip-from-below_rear-left.jpg", [(560, 820, 740, 1000)],
                     (200, 460, 310, 590)),
              "08": ("damien-bike-2026-11-12/08_whip-from-below_right-side.jpg", [(560, 200, 800, 380)],
                     (1100, 210, 1300, 400)),
              "09": ("damien-bike-2026-11-12/09_whip-from-below_left-front.jpg", [(620, 590, 830, 730)],
                     (1120, 290, 1270, 470))}


def boot_white():
    """Per photo: the white pixels (saturation under 0.25, value over 0.45) in the boxes, the lit side (the top
    luminance quartile, glints over the 98th percentile out), its median (8-bit) and the boot / helmet ratio of the
    lit sides' linear medians, per channel and in luminance."""
    ref = os.path.join(ROOT, "reference")
    out = {}

    def lit(im, boxes):
        a = np.concatenate([np.asarray(im.crop(b)).reshape(-1, 3) for b in boxes]).astype(float) / 255.0
        mx = a.max(1)
        a = a[((mx - a.min(1)) / np.maximum(mx, 1e-6) < 0.25) & (mx > 0.45)]
        Y = srgb_to_lin(a) @ np.array(scene_look.LUMA)
        return a[(Y >= np.percentile(Y, 75)) & (Y <= np.percentile(Y, 98))]
    for k, (f, boots, helm) in BOOT_BOXES.items():
        im = Image.open(os.path.join(ref, f)).convert("RGB")
        b, h = lit(im, boots), lit(im, [helm])
        rb, rh = srgb_to_lin(np.median(b, 0)), srgb_to_lin(np.median(h, 0))
        out[k] = dict(boot=(np.median(b, 0) * 255).round().astype(int).tolist(), n_boot=len(b),
                      helmet=(np.median(h, 0) * 255).round().astype(int).tolist(), n_helmet=len(h),
                      ratio=(rb / rh).round(3).tolist(),
                      ratio_Y=round(float(rb @ np.array(scene_look.LUMA) / (rh @ np.array(scene_look.LUMA))), 3))
        print("%s boot lit %-16s helmet lit %-16s boot / helmet %s, luminance %.3f" % (
            k, out[k]["boot"], out[k]["helmet"], out[k]["ratio"], out[k]["ratio_Y"]))
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
    elif a[0] in ("bike", "honda"):              # bike EXR INDEX REDS ... / honda VIEW EXR INDEX REDS ...
        def reds_of(s):                          # "R,G,B[;R,G,B...]"
            return [[int(v) for v in r.split(",")] for r in s.split(";")]
        also = {k: [int(v) for v in c.split(",")] for k, c in
                (x.split("=") for x in a[a.index("--also") + 1].split(";"))} if "--also" in a else None
        if a[0] == "bike":
            res = bike_red(a[1], a[2], reds_of(a[3]),
                           float(a[a.index("--ev7") + 1]) if "--ev7" in a else scene_look.PHOTO_EV["07"], also)
        else:
            res = honda_red(a[2], a[3], a[1], reds_of(a[4]), float(a[a.index("--ev") + 1]) if "--ev" in a else -0.9,
                            also)
        json.dump(res, open(a[a.index("--out") + 1], "w"), indent=1)
    elif a[0] == "gear":                         # gear OUT.json VIEW=EXR [VIEW=EXR ...] --index INDEX.json [--no-tint]
        i = a.index("--index")
        res = []
        for spec in [s for s in a[2:i] if "=" in s]:
            v, p = spec.split("=")
            res += gear(v, p, a[i + 1], tint="--no-tint" not in a)
        json.dump(res, open(a[1], "w"), indent=1)
    elif a[0] == "boot_white":                   # boot_white OUT.json
        json.dump(boot_white(), open(a[1], "w"), indent=1)
    elif a[0] == "darks":                        # darks OUT.json VIEW=EXR [VIEW=EXR ...] --index INDEX.json
        i = a.index("--index")
        json.dump(dark_fit(dark_sets(a[2:i], a[i + 1])), open(a[1], "w"), indent=1)
    elif a[0] == "sheet":                        # sheet VIEW EXR OUT.jpg [--scale S] [--ev EV] [--region x0,y0,x1,y1] [--vertical]
        opt = {k: a[a.index(k) + 1] for k in ("--scale", "--ev", "--region") if k in a}
        sheet(a[1], a[2], a[3], int(opt.get("--scale", 2)), float(opt.get("--ev", 0.0)),
              tuple(int(v) for v in opt["--region"].split(",")) if "--region" in opt else None, "--vertical" in a)
    elif a[0] in ("fit", "report"):
        P = load_pairs([a[1]])
        work, out = a[a.index("--work") + 1], a[a.index("--out") + 1]
        (fit_all if a[0] == "fit" else report)(P, work, out)
