"""The scene look, shared by the bike and the rider (decision 54): how scene-linear renders become display pixels.

    import scene_look
    scene_look.apply(scene, "daylight")      # the look fitted to his phone's photos (head_closeups' daylight rig)
    scene_look.apply(scene, "scene")         # the same look for the studio-lit scene views (EV_SCENE on the gains)
    scene_look.apply(scene, "studio")        # Standard, for comparisons with Leatt's and Honda's studio photos
    scene_look.apply(scene, "d46")           # decision 46's AgX - Punchy at -0.6 (the look before this one)
    scene_look.apply(scene, "linear")        # scene-referred EXR (multilayer, float, uncompressed) for fitting

The look (research/scene-look.md; fitted by look_fit.py on pixel-aligned pairs of his photos 07 and 09, tested on
08 and on the bike in his 07), all in the view settings, so the viewport shows it as the renders do:
  1. per-channel gains (his phone's white balance and the exposure): the curve mapping's white level, 1 / gain;
  2. a tone curve per channel with a toe and a shoulder: the curve mapping's C curve, the log-logistic
     T(u) = m u^P / (1 + u^P), m so that T(XMAX) = 1 (Blender applies it to scene-linear values, before the view);
  3. the Standard view (the sRGB curve, clipped).
display() is the same look in numpy, the reference test_scene_look.py holds Blender's output to (within a level).

SCENE_LOOK=<kind> in the environment overrides the kind every caller asks for (SCENE_LOOK=linear renders the pairs
of the look fit through the unchanged scripts; SCENE_LOOK=d46 renders the old look for before / after sheets).
"""
import json
import os

KINDS = ("daylight", "scene", "studio", "d46", "linear")
LUMA = (0.2126, 0.7152, 0.0722)      # Rec.709 luminance (Blender's scene linear is Rec.709)

# ---- the fitted look (look_fit.py fit, "final", all three photos; research/scene-look.md "The fit"), on
# head_closeups' daylight rig (sun 4 x 2^3.4 W/m2). log2 of the gains: WB his phone's white balance read off the
# white shell (red and blue against green), EV the exposure; ev in apply() adds to EV for another rig
EV = 0.075
WB = (0.234, 0.0, -0.302)
GAINS = tuple(2.0 ** (EV + w) for w in WB)
P = 2.52                              # the toe: T(u) ~ u^P in the darks; the shoulder rolls off above u ~ 1
XMAX = 8.0                            # the curve's white: T(XMAX) = 1 (gained scene-linear)
CURVE_POINTS = 48                     # control points of the view's C curve (its table: 257 entries over 0..XMAX)
# "scene": the studio-lit views (build_bike, build_rider, rake, head_closeups' studio) under white lamps: the tone
# curve without the daylight white balance (the phone's correction for the blue sky light), EV_SCENE stops over EV
# keeping linear mid grey (0.18) where decision 46's AgX - Punchy at -0.6 put it, for which those rigs were lit
EV_SCENE = 0.815                      # 0.18 -> 69 as under AgX - Punchy -0.6 (look_apply.py, Blender 5.2.3)


def oetf(x):
    """Linear to sRGB-encoded (the Standard view's curve), numpy."""
    import numpy as np
    x = np.clip(np.asarray(x, float), 0.0, None)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def eotf(y):
    """sRGB-encoded to linear, numpy."""
    import numpy as np
    y = np.asarray(y, float)
    return np.where(y <= 0.04045, y / 12.92, ((y + 0.055) / 1.055) ** 2.4)


def saturate(x, sat):
    """Saturation about the Rec.709 luminance, negatives clipped (a stage the fit tried: look_fit.py curve_sat)."""
    import numpy as np
    x = np.asarray(x, float)
    if sat == 1.0:
        return np.clip(x, 0.0, None)
    L = (x @ np.asarray(LUMA))[..., None]
    return np.clip(L + sat * (x - L), 0.0, None)


def tone(u, p=P, xmax=XMAX):
    """The tone curve, per channel: the log-logistic m u^p / (1 + u^p) scaled so that T(xmax) = 1, clipped to
    0..1; p > 1 is the toe (darks, and the weak channels of saturated colours, pressed down), the shoulder rolls the
    highlights off towards xmax."""
    import numpy as np
    u = np.clip(np.asarray(u, float), 0.0, xmax)
    m = (1.0 + xmax ** p) / xmax ** p
    up = np.power(u, p)
    return np.clip(m * up / (1.0 + up), 0.0, 1.0)


def pbr_neutral(c):
    """Khronos PBR Neutral (the published reference formula), linear in, linear out, numpy (a base the fit tried)."""
    import numpy as np
    c = np.asarray(c, float).copy()
    x = c.min(-1, keepdims=True)
    off = np.where(x < 0.08, x - 6.25 * x * x, 0.04)
    c = c - off
    peak = c.max(-1, keepdims=True)
    s0, d = 0.8 - 0.04, 0.2 + 0.04
    newp = 1 - d * d / (peak + d - s0)
    hi = peak >= s0
    c2 = c * np.where(hi, newp / np.maximum(peak, 1e-9), 1.0)
    g = 1 - 1 / (0.15 * (peak - newp) + 1)
    c2 = np.where(hi, c2 * (1 - g) + newp * g, c2)
    return c2


def model(lin, gains=GAINS, p=P, sat=1.0, base="standard", xmax=XMAX):
    """Scene-linear (..., 3) to sRGB-encoded display values in 0..1: (saturation), per-channel gains, the tone
    curve, the sRGB curve (base "standard": this module's look; "pbrn": Khronos PBR Neutral in place of the curve)."""
    import numpy as np
    x = saturate(lin, sat) * np.asarray(gains, float)
    x = pbr_neutral(x) if base == "pbrn" else tone(x, p, xmax)
    return oetf(np.clip(x, 0.0, 1.0))


def gains_of(kind, ev=0.0):
    """The per-channel gains of a kind: daylight GAINS; scene the exposure alone, EV + EV_SCENE; times 2^ev."""
    if kind == "scene":
        return (2.0 ** (EV + EV_SCENE + ev),) * 3
    return tuple(g * 2.0 ** ev for g in GAINS)


def display(lin, kind="daylight", ev=0.0):
    """What apply(scene, kind, ev) makes of scene-linear pixels, in numpy (daylight, scene and studio)."""
    import numpy as np
    if kind == "studio":
        return oetf(np.clip(np.asarray(lin, float) * 2.0 ** ev, 0.0, 1.0))
    return model(lin, gains=gains_of(kind, ev))


def kind_of(kind):
    k = os.environ.get("SCENE_LOOK") or kind
    if k not in KINDS:
        raise ValueError("scene look must be one of %s, not %r" % (", ".join(KINDS), k))
    return k


def _plain(vs, view, look, ev):
    vs.view_transform, vs.look, vs.exposure = view, look, ev
    vs.gamma = 1.0
    vs.use_curve_mapping = False
    vs.use_white_balance = False


def _curve(vs, gains):
    """Gains and the tone curve in the view's curve mapping (Blender applies it to scene-linear values, before the
    view's exposure): white level 1 / gain per channel, the C curve sampled on T (denser in the toe), R, G and B
    straight over the same range."""
    _plain(vs, "Standard", "None", 0.0)
    vs.use_curve_mapping = True
    cm = vs.curve_mapping
    cm.tone = "STANDARD"
    cm.extend = "HORIZONTAL"
    cm.use_clip = True
    cm.clip_min_x, cm.clip_min_y, cm.clip_max_x, cm.clip_max_y = 0.0, 0.0, XMAX, 1.0
    cm.black_level = (0.0, 0.0, 0.0)
    cm.white_level = tuple(1.0 / g for g in gains)
    for i, c in enumerate(cm.curves):
        if i == 3:
            us = [XMAX * (j / (CURVE_POINTS - 1)) ** 2 for j in range(CURVE_POINTS)]
            pts = [(u, float(tone(u))) for u in us]
        else:
            pts = [(0.0, 0.0), (XMAX, XMAX)]
        while len(c.points) > 2:
            c.points.remove(c.points[-1])
        c.points[0].location = pts[0]
        c.points[1].location = pts[-1]
        for q in pts[1:-1]:
            c.points.new(*q)
        for q in c.points:
            q.handle_type = "AUTO"
    cm.update()


def _linear(scene):
    """Scene-referred output for the look fit: Standard, no look, exposure 0; a multilayer float EXR without
    compression (common/exr.py reads it) with the albedo (Diffuse Color), Depth and Material Index passes. Every
    material gets a pass index (1 + its place in the sorted names); SCENE_LOOK_INDEX=<path> writes that table."""
    import bpy
    _plain(scene.view_settings, "Standard", "None", 0.0)
    im = scene.render.image_settings
    im.media_type = "MULTI_LAYER_IMAGE"
    im.file_format = "OPEN_EXR_MULTILAYER"
    im.color_depth = "32"
    im.exr_codec = "NONE"
    for vl in scene.view_layers:
        vl.use_pass_diffuse_color = True
        vl.use_pass_z = True
        vl.use_pass_material_index = True
    names = sorted(m.name for m in bpy.data.materials)
    for i, n in enumerate(names):
        bpy.data.materials[n].pass_index = i + 1
    if os.environ.get("SCENE_LOOK_INDEX"):
        json.dump({n: i + 1 for i, n in enumerate(names)}, open(os.environ["SCENE_LOOK_INDEX"], "w"), indent=0)


def apply(scene, kind="daylight", ev=0.0):
    """Set the scene's look in its view settings. ev: an exposure offset in stops (a rig brighter or darker than
    the one the look was fitted on). Returns the kind applied (SCENE_LOOK overrides)."""
    k = kind_of(kind)
    vs = scene.view_settings
    if k in ("daylight", "scene"):
        _curve(vs, gains_of(k, ev))
    elif k == "linear":
        _linear(scene)
    elif k == "studio":
        _plain(vs, "Standard", "None", ev)
    else:                                            # d46
        _plain(vs, "AgX", "AgX - Punchy", -0.6 + ev)
    return k


def describe(scene):
    """One line on the scene's look, for the scripts' logs."""
    vs = scene.view_settings
    g = tuple(round(1.0 / w, 3) for w in vs.curve_mapping.white_level) if vs.use_curve_mapping else None
    return "look %s %s %.2f curve gains %s" % (vs.view_transform, vs.look, vs.exposure, g)
