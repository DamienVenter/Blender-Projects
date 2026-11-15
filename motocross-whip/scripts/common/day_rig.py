"""The daylight rig shared by the rider's and the bike's daylight renders (decision 55): a sun lamp and Blender's
multiple-scattering sky (its own sun disc off: the lamp is the sun) above a flat ground, as his photos 07, 08 and 09
were lit (one session, a clear sky, a high sun; research/rider-ledger/goggle.md "Daylight for his photos", and
research/scene-look.md "The daylight rig" for the fit of the sky).

    import day_rig
    rig = day_rig.build(scene)              # the world (sky over the ground) and the sun lamp
    day_rig.aim(rig, camera, phi, theta)    # the sun at (phi, theta) deg in the camera's frame: phi its direction
                                            # across the image (0 image right, 90 image up), theta its angle off the
                                            # line back to the camera; the sky's sun and the ground's light follow
    day_rig.aim(rig, camera, phi, theta, 78.0)   # the same, the world turned (no camera roll) so that the sun stands
                                            # 78 deg high: a his-photo view whose camera rides a posed head

The sun lamp is in the light group "sun", the world (sky and ground) in "sky": a linear render (scene_look "linear")
carries each part as its own pass (Combined_sun, Combined_sky) for the fits. DAY_RIG='{"sky_strength": 2.0}' (JSON)
overrides any value of RIG for a sweep; DAY_GAIN, DAY_SUN_W and DAY_SKY keep head_closeups.py's older overrides.

blender -b --factory-startup --python day_rig.py -- e1 ['{"aerosol_density": 0.5}']
    prints the sky's irradiance on a level ground at strength 1, per channel, by sun elevation (the table E1)
blender -b --factory-startup --python day_rig.py -- turn
    renders the rig turned for a tilted camera against the unturned rig seen by the turned camera (test_day_rig.py)
"""
import json
import math
import os

# ---- the rig. Sun: his photos' light went into the sun under decision 46's look (head_closeups.py's DAY_GAIN: 4
# W/m2 x 2^3.4, the look's exposure is referred to it); white (the sky model's own sun, (1.13, 0.98, 0.79) at 78 deg,
# fitted his shell's shade worse: 7.6 against 6.2 dE). Ground: his 07, the lit pavement over his white shell's top x
# 0.8. Sky (decision 55, research/scene-look.md "The daylight rig"): Blender's multiple-scattering sky at its default
# clear atmosphere, as bright against the lamp as against its own sun: its sun disc gives a level white plane
# SKY_SUN_Y (luminance, strength 1, the sun 78 deg high, 1024 samples), the lamp sun_w sin(78 deg). Fitted on his
# 07, 08 and 09 with the sky turned to his sun's height: the sky behind him in 09 at dE 1.4, his shell's shade at 6.2
# (decision 54's sky: 26.8); aerosols 0 to 4, air 0.5 to 2, ozone 0 to 3, altitude 1500 m and a weaker sky (0.16,
# the shade's own best, 5.7) moved the shade by 0.6 dE at most and the 09 sky by up to 17
SKY_SUN_Y = 141.03
SUN_ELEV = 78.0                          # deg, his 07's sun (the bike's shadow): the height the strength is set at
RIG = dict(
    sun_w=4.0 * 2.0 ** 3.4,              # W/m2 (Blender units) on a plane facing the sun
    sun_disc=0.53,                       # deg, the sun's angular diameter
    sun_rgb=(1.0, 1.0, 1.0),
    sky_strength=4.0 * 2.0 ** 3.4 * math.sin(math.radians(SUN_ELEV)) / SKY_SUN_Y,     # 0.2929
    air_density=1.0,
    aerosol_density=1.0,
    ozone_density=1.0,
    altitude=100.0,                      # m
    sky_ground_albedo=0.3,               # the sky model's own ground: no effect on 5.2's multiple-scattering sky
                                         # (0.1, 0.3 and 0.6 gave the same light on a level plane to 4 digits)
    ground=(0.41, 0.40, 0.36),           # albedo of the rig's ground (the world below the horizon)
)
SKY_KEYS = ("air_density", "aerosol_density", "ozone_density", "altitude")
# the sky's irradiance on a level ground at strength 1 (R, G, B), by the sun's elevation (deg): `e1` below, for
# RIG's sky
E1 = {50: (8.088, 13.984, 24.693), 60: (8.487, 14.734, 26.124), 70: (8.773, 15.273, 27.156),
      80: (8.946, 15.6, 27.782), 90: (9.005, 15.711, 27.994)}


def rig():
    """RIG with the environment's overrides (DAY_RIG JSON; DAY_GAIN, DAY_SUN_W, DAY_SKY)."""
    r = dict(RIG)
    if os.environ.get("DAY_GAIN") or os.environ.get("DAY_SUN_W"):
        g = float(os.environ.get("DAY_GAIN", 2.0 ** 3.4))
        r["sun_w"] = float(os.environ.get("DAY_SUN_W", 4.0 * g))
    if os.environ.get("DAY_SKY"):
        r["sky_strength"] = float(os.environ["DAY_SKY"])
    r.update(json.loads(os.environ.get("DAY_RIG", "{}") or "{}"))
    return r


def e1(elevation, table=None):
    """The sky's irradiance on a level ground at strength 1 (R, G, B) at a sun elevation (deg), from the table."""
    t = table or E1
    ks = sorted(t)
    x = min(max(elevation, ks[0]), ks[-1])
    for a, b in zip(ks, ks[1:]):
        if a <= x <= b:
            f = (x - a) / (b - a)
            return tuple(u + (v - u) * f for u, v in zip(t[a], t[b]))
    return tuple(t[ks[-1]])


def _sky(nt, r):
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False             # the lamp is the sun (with its disc on, 5.2's sky has no Vector input to turn it)
    for k in SKY_KEYS:
        setattr(sky, k, float(r[k]))
    sky.ground_albedo = float(r["sky_ground_albedo"])
    return sky


def build(scene, values=None):
    """The world (the sky above the horizon, the ground's radiance below it) and the sun lamp; every other light of
    the scene is removed. Returns the rig: its nodes, the sun object and the values used."""
    import bpy
    r = values or rig()
    for o in [o for o in scene.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    w = bpy.data.worlds.new("daylight")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    sky = _sky(nt, r)
    gain = nt.nodes.new("ShaderNodeVectorMath")            # the sky's strength (the ground is set as radiance)
    gain.operation = "SCALE"
    gain.inputs["Scale"].default_value = float(r["sky_strength"])
    nt.links.new(sky.outputs["Color"], gain.inputs[0])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    turn = nt.nodes.new("ShaderNodeVectorRotate")         # the world's directions into the sky's frame (aim)
    turn.rotation_type = "EULER_XYZ"
    nt.links.new(tc.outputs["Generated"], turn.inputs["Vector"])
    nt.links.new(turn.outputs["Vector"], sky.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(turn.outputs["Vector"], sep.inputs[0])
    up = nt.nodes.new("ShaderNodeMath")
    up.operation = "GREATER_THAN"
    up.inputs[1].default_value = 0.0
    nt.links.new(sep.outputs["Z"], up.inputs[0])
    gnd = nt.nodes.new("ShaderNodeRGB")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(up.outputs[0], mix.inputs["Factor"])
    nt.links.new(gnd.outputs[0], mix.inputs["A"])
    nt.links.new(gain.outputs[0], mix.inputs["B"])
    bg = nt.nodes["Background"]
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    L = bpy.data.lights.new("sun", "SUN")
    L.energy = float(r["sun_w"])
    L.color = tuple(float(c) for c in r["sun_rgb"])
    L.angle = math.radians(float(r["sun_disc"]))
    sun = bpy.data.objects.new("sun", L)
    scene.collection.objects.link(sun)
    for vl in scene.view_layers:                          # each part of the light as its own pass (linear renders)
        for n in ("sun", "sky"):
            if n not in vl.lightgroups:
                vl.lightgroups.add(name=n)
    sun.lightgroup = "sun"
    w.lightgroup = "sky"
    return dict(sky=sky, ground=gnd, sun=sun, turn=turn, values=r)


def photo_up(d_cam, elevation):
    """The world's up in the camera's frame (x right, y up, z back) for a photo whose sun, d_cam in that frame, stood
    `elevation` deg high: the camera without roll (up in its up-back plane: (0, cos b, -sin b), b its pitch) and the
    lower of the two pitches that give that elevation (a camera looking up less steeply; research/scene-look.md, "The
    daylight rig"). Without a solution (the sun cannot stand that high for any pitch), the pitch nearest to it."""
    a, b = d_cam[1], -d_cam[2]                         # up . d = a cos(pitch) + b sin(pitch)
    R, phi = math.hypot(a, b), math.atan2(b, a)
    s = math.sin(math.radians(elevation))
    pitch = phi - math.acos(min(s / R, 1.0)) if R > 0 else 0.0
    return (0.0, math.cos(pitch), -math.sin(pitch)), math.degrees(pitch)


def aim(rig_, cam, phi, theta, elevation=None):
    """The sun at (phi, theta) in the camera's frame (deg; module docstring). elevation (deg): the sun's height in the
    photo the view matches; the sky and the ground are then turned so that the world's up is the photo's (photo_up),
    whatever the pose of the blend the camera rides with: a camera fitted to his head in a whip looks up at it, the
    same camera on the seated rider may not, and the sky would be the one of another hour. None: the blend's own up.
    The sky's sun follows (Blender's sky: elevation asin(z), rotation atan2(x, y) in its frame, checked against a sun
    lamp on a matte sphere) and the ground's radiance is its albedo times the sun's and the sky's light on it over pi
    (Lambert), per channel. Returns the sun's direction (towards the sun, world frame)."""
    from mathutils import Quaternion, Vector
    r = rig_["values"]
    M = cam.matrix_world.to_3x3()
    right, up, back = M.col[0].normalized(), M.col[1].normalized(), M.col[2].normalized()   # back: to the camera
    p, t = math.radians(phi), math.radians(theta)
    d = (back * math.cos(t) + (right * math.cos(p) + up * math.sin(p)) * math.sin(t)).normalized()
    rig_["sun"].rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    q = Quaternion()                                              # elevation None: the blend's own up
    rig_["pitch"] = None
    if elevation is not None:
        u_cam, pitch = photo_up((math.cos(p) * math.sin(t), math.sin(p) * math.sin(t), math.cos(t)), elevation)
        u = (right * u_cam[0] + up * u_cam[1] + back * u_cam[2]).normalized()
        q = u.rotation_difference(Vector((0.0, 0.0, 1.0)))        # the world's directions into the sky's frame
        rig_["pitch"] = pitch
    rig_["turn"].inputs["Rotation"].default_value = q.to_euler("XYZ")
    de = q @ d
    el = math.asin(max(min(de.z, 1.0), -1.0))
    rig_["sky"].sun_elevation = el
    rig_["sky"].sun_rotation = math.atan2(de.x, de.y)
    sky_e = e1(math.degrees(el), r.get("e1"))
    e = [(r["sun_w"] * c * max(de.z, 0.0) + r["sky_strength"] * s) / math.pi for c, s in zip(r["sun_rgb"], sky_e)]
    rig_["ground"].outputs[0].default_value = (*[a * x for a, x in zip(r["ground"], e)], 1.0)
    rig_["elevation"] = math.degrees(el)
    return d


def measure_e1(values=None, elevations=(50, 60, 70, 80, 90), samples=1024):
    """The sky's irradiance on a level ground at strength 1, per channel, for each sun elevation: a white matte plane
    100 m across seen from straight above by a 4 x 4 px orthographic camera, lit by the sky alone (its radiance is
    E / pi). Run in Blender; a fresh scene."""
    import tempfile

    import bpy
    import numpy as np
    import exr
    r = dict(values or rig())
    r.update(sky_strength=1.0, ground=(0.0, 0.0, 0.0), sun_w=0.0)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False
    sc.render.resolution_x = sc.render.resolution_y = 4
    sc.view_settings.view_transform = "Standard"
    me = bpy.data.meshes.new("plane")
    me.from_pydata([(-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("plane", me)
    sc.collection.objects.link(ob)
    m = bpy.data.materials.new("white")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (1, 1, 1, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(dif.outputs[0], out.inputs[0])
    me.materials.append(m)
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = 0.1
    cam = bpy.data.objects.new("cam", cd)
    cam.location = (0, 0, 1)
    sc.collection.objects.link(cam)
    sc.camera = cam
    rg = build(sc, r)
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.exr_codec = "NONE"
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for el in elevations:
            rg["sky"].sun_elevation = math.radians(el)
            sc.render.filepath = os.path.join(tmp, "e%d.exr" % el)
            bpy.ops.render.render(write_still=True)
            ch = exr.read(sc.render.filepath)
            order = sorted([k for k in ch if k[-1] in "RGB"], key=lambda k: "RGB".index(k[-1]))
            rgb = [float(np.mean(ch[k])) for k in order]
            res[el] = tuple(round(math.pi * v, 3) for v in rgb)
    return res


def check_turn(samples=16, px=48):
    """aim with an elevation turns the sky and the ground; the same sky not turned, seen by the camera turned the
    other way, must give the same image. A camera on a tilted head (12 mm lens, wide enough for the ground's edge),
    the sun 78 deg high. Returns the sky's sun elevation (deg) and the 95th percentile of the relative difference.
    (Blender 5.2's sky has no Vector input while its own sun disc is on, so the disc cannot mark its sun.)"""
    import tempfile

    import bpy
    import numpy as np
    from mathutils import Euler
    import exr
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = px
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.exr_codec = "NONE"
    cd = bpy.data.cameras.new("c")
    cd.lens = 12
    cam = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.rotation_euler = (math.radians(100), math.radians(25), math.radians(40))
    bpy.context.view_layer.update()
    rg = build(sc)
    aim(rg, cam, 85.0, 130.0, elevation=78.0)
    q = Euler(tuple(rg["turn"].inputs["Rotation"].default_value), "XYZ").to_quaternion()

    def shot():
        with tempfile.TemporaryDirectory() as t:
            sc.render.filepath = os.path.join(t, "a.exr")
            bpy.ops.render.render(write_still=True)
            c = exr.read(sc.render.filepath)
            return np.stack([np.asarray(c[k]).reshape(px, px) for k in "RGB"], -1)
    a = shot()
    rg["turn"].inputs["Rotation"].default_value = (0.0, 0.0, 0.0)
    cam.matrix_world = q.to_matrix().to_4x4() @ cam.matrix_world
    b = shot()
    ground = int((a[..., 2] < a[..., 0]).sum())
    return rg["elevation"], float(np.percentile(np.abs(a - b) / (np.abs(b) + 1e-3), 95)), ground


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if a and a[0] == "e1":
        v = rig()
        v.update(json.loads(a[1]) if len(a) > 1 else {})
        print("E1", json.dumps({str(k): v for k, v in measure_e1(v).items()}))
    elif a and a[0] == "turn":
        el, p95, ground = check_turn()
        print("TURN elevation %.6f rel_p95 %.6f ground_px %d" % (el, p95, ground))
