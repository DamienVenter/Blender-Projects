"""The scene look, shared by the bike and the rider (decision 54): how scene-linear renders become display pixels.

    import scene_look
    scene_look.apply(scene, "daylight")      # the look fitted to his phone's photos (head_closeups' daylight rig)
    scene_look.apply(scene, "scene")         # the same look for the studio-lit scene views (EV_SCENE on the gains)
    scene_look.apply(scene, "studio")        # Standard, for comparisons with Leatt's and Honda's studio photos
    scene_look.apply(scene, "d46")           # decision 46's AgX - Punchy at -0.6 (the look before this one)
    scene_look.apply(scene, "linear")        # scene-referred EXR (multilayer, float, uncompressed) for fitting

The look (research/scene-look.md; fitted by look_fit.py on pixel-aligned pairs of his photos 07, 08 and 09, each
held out in turn, and checked on the bike's red in his 07), in a compositor node group and the Standard view:
  1. per-channel gains (his phone's white balance and the exposure);
  2. a tone curve with a toe and a shoulder on the largest channel, the others scaled with it (the hue and the
     channel ratios kept: a tone curve per channel crushed the weak channels of saturated colours, the bike's red
     to G 7 where his photos show 47): T(u) = m u^P / (1 + u^P), m so that T(XMAX) = 1;
  3. the Standard view (the sRGB curve).
The view's curve mapping cannot do step 2 (per channel; its film-like mode still puts the smallest channel through
the curve), so the look lives in the compositor: renders show it; the viewport shows it with Viewport Shading's
Compositor set to Camera or Always. display() is the same look in numpy, the reference test_scene_look.py holds
Blender's output to (within a level).

SCENE_LOOK=<kind> in the environment overrides the kind every caller asks for (SCENE_LOOK=linear renders the pairs
of the look fit through the unchanged scripts; SCENE_LOOK=d46 renders the old look for before / after sheets).
"""
import json
import os

KINDS = ("daylight", "scene", "studio", "d46", "linear")
LUMA = (0.2126, 0.7152, 0.0722)      # Rec.709 luminance (Blender's scene linear is Rec.709)

# ---- the fitted look (look_fit.py fit, "final", all three photos; research/scene-look.md "The fit"), on
# head_closeups' daylight rig (sun 4 x 2^3.4 W/m2). log2 of the gains: WB his phone's white balance read off the
# white shell (red and blue against green), EV the exposure (the mean of the photos' own: 07 -0.21, 08 +0.64, 09
# -0.43 stops off it, his phone exposing each shot); ev in apply() adds to EV for another rig
EV = 0.102
WB = (0.234, 0.0, -0.302)
GAINS = tuple(2.0 ** (EV + w) for w in WB)
P = 2.59                              # the toe: T(u) ~ u^P in the darks; the shoulder rolls off above u ~ 1
XMAX = 8.0                            # the curve's white: T(XMAX) = 1 (gained scene-linear)
# "scene": the studio-lit views (build_bike, build_rider, rake, head_closeups' studio) under white lamps: the tone
# curve without the daylight white balance (the phone's correction for the blue sky light), EV_SCENE stops over EV
# keeping linear mid grey (0.18) where decision 46's AgX - Punchy at -0.6 put it, for which those rigs were lit
EV_SCENE = 0.832                      # 0.18 -> 69 as under AgX - Punchy -0.6 (look_apply.py, Blender 5.2.3)
GROUP = "scene_look"                  # the compositor node group apply() builds


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


def model(lin, gains=GAINS, p=P, sat=1.0, base="max", xmax=XMAX):
    """Scene-linear (..., 3) to sRGB-encoded display values in 0..1: (saturation), per-channel gains, the tone
    curve, the sRGB curve. base "max": this module's look, the curve on the largest channel and the others scaled
    with it; "standard": the curve on each channel; "pbrn": Khronos PBR Neutral in place of the curve."""
    import numpy as np
    x = saturate(lin, sat) * np.asarray(gains, float)
    if base == "max":
        m = x.max(-1, keepdims=True)
        x = x * tone(m, p, xmax) / np.maximum(m, 1e-9)
    elif base == "pbrn":
        x = pbr_neutral(x)
    else:
        x = tone(x, p, xmax)
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


def _plain(scene, view, look, ev):
    """A view transform and look alone: no curve mapping, no white balance, and this module's compositor group
    taken off (a group of the script's own stays)."""
    vs = scene.view_settings
    vs.view_transform, vs.look, vs.exposure = view, look, ev
    vs.gamma = 1.0
    vs.use_curve_mapping = False
    vs.use_white_balance = False
    g = scene.compositing_node_group
    if g is not None and g.name.startswith(GROUP):
        scene.compositing_node_group = None


def _compositor(scene, gains, p=P, xmax=XMAX):
    """Gains and the max-RGB tone curve as a compositor node group (math nodes, float): x = max(gain * channel, 0);
    M = max(x); out = x * T(min(M, xmax)) / max(M, 1e-9), alpha passed through; then the Standard view."""
    import bpy
    if scene.compositing_node_group is not None and not scene.compositing_node_group.name.startswith(GROUP):
        raise RuntimeError("the scene already has a compositor group (%s): the look would replace it"
                           % scene.compositing_node_group.name)
    _plain(scene, "Standard", "None", 0.0)
    old = bpy.data.node_groups.get(GROUP)
    if old is not None:
        bpy.data.node_groups.remove(old)
    g = bpy.data.node_groups.new(GROUP, "CompositorNodeTree")
    g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = g.nodes, g.links

    def math(op, a, b, x=0.0):
        n = N.new("ShaderNodeMath")
        n.operation, n.use_clamp, n.location = op, False, (x, 0.0)
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    rl = N.new("CompositorNodeRLayers")
    rl.scene = scene
    sep = N.new("CompositorNodeSeparateColor")
    L.new(rl.outputs["Image"], sep.inputs["Image"])
    x = [math("MAXIMUM", math("MULTIPLY", sep.outputs[c], float(k)), 0.0) for c, k in zip(("Red", "Green", "Blue"), gains)]
    M = math("MAXIMUM", math("MAXIMUM", x[0], x[1]), x[2])
    up = math("POWER", math("MINIMUM", M, xmax), p)
    T = math("MULTIPLY", math("DIVIDE", up, math("ADD", up, 1.0)), (1.0 + xmax ** p) / xmax ** p)
    k = math("DIVIDE", T, math("MAXIMUM", M, 1e-9))
    comb = N.new("CompositorNodeCombineColor")
    for c, xc in zip(("Red", "Green", "Blue"), x):
        L.new(math("MULTIPLY", xc, k), comb.inputs[c])
    L.new(sep.outputs["Alpha"], comb.inputs["Alpha"])
    out = N.new("NodeGroupOutput")
    L.new(comb.outputs["Image"], out.inputs[0])
    g["scene_look"] = dict(gains=[float(v) for v in gains], p=float(p), xmax=float(xmax))
    scene.compositing_node_group = g
    scene.render.use_compositing = True
    # 5.2's default compositor device is the GPU (no GPU on the build server: EGL errors, then a fall-back) and its
    # precision AUTO may run half floats there: the CPU at full precision gives the same pixels everywhere
    scene.render.compositor_device = "CPU"
    scene.render.compositor_precision = "FULL"


def _linear(scene):
    """Scene-referred output for the look fit: Standard, no look, exposure 0; a multilayer float EXR without
    compression (common/exr.py reads it) with the albedo (Diffuse Color), Depth and Material Index passes. Every
    material gets a pass index (1 + its place in the sorted names); SCENE_LOOK_INDEX=<path> writes that table."""
    import bpy
    _plain(scene, "Standard", "None", 0.0)
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
    """Set the scene's look: the view settings and, for "daylight" and "scene", the compositor group. ev: an
    exposure offset in stops (a rig brighter or darker than the one the look was fitted on). Returns the kind
    applied (SCENE_LOOK overrides)."""
    k = kind_of(kind)
    if k in ("daylight", "scene"):
        _compositor(scene, gains_of(k, ev))
    elif k == "linear":
        _linear(scene)
    elif k == "studio":
        _plain(scene, "Standard", "None", ev)
    else:                                            # d46
        _plain(scene, "AgX", "AgX - Punchy", -0.6 + ev)
    return k


def describe(scene):
    """One line on the scene's look, for the scripts' logs."""
    vs = scene.view_settings
    g = scene.compositing_node_group
    q = dict(g["scene_look"]) if g is not None and "scene_look" in g else None
    if q:
        q = "gains %s p %.3g" % (tuple(round(v, 3) for v in q["gains"]), q["p"])
    return "look %s %s %.2f compositor %s" % (vs.view_transform, vs.look, vs.exposure, q)
