"""The goggle alone rendered at the cameras fitted to Leatt's goggle-alone photos, for the side-by-side checks.

python3 goggle.py --free GOGGLE.npz
blender -b --factory-startup --python-exit-code 1 --python goggle_views.py -- GOGGLE.npz OUT_DIR [views] [samples] \
    [light]

Cameras: research/goggle-cameras.json, one per photo: [az, el, roll (deg), d (m), f (px), u0, v0 (px)] in the
GOGGLE frame (goggle.py: x his left, y back, z up, origin at the lens front centre), the camera at distance d from
the origin in the direction (sin az cos el, -cos az cos el, sin el), looking at it, rolled by roll, principal point
(W/2 + u0, H/2 + v0) on the photo's W x H pixels (y down). Fitted by the round 6 goggle fit (outline and creases
at full resolution; the landmark views iso55, phy and phr held at round 5's fit with their landmarks; frg and chee
fitted to the finished shape only: research/rider-ledger/goggle.md). Studio: Cycles, AgX, Leatt's light grey
backdrop (camera rays only; a dim world lights the rest) and three area lights, 1 m square (round 6: 2 m lights
spread a highlight over 15 % of the frame's face in iso55, where Leatt's photo shows small, crisp ones; at 1 m its
edge width matches the photo, the ledger goggle.md section 8).

light (round 6): "studio" (default) or a raking sun that shows every dent and wave in the frame as a dark or light
streak (after the bike's rake.py: the studio lights off, the ambient at 12 %, a 0.5 deg sun, AgX Punchy):
"rakeT" from above, "rakeB" from below, "rakeL" from his left, "rakeR" from his right, each 20 deg in front of the
lens's front plane. A rake writes OUT_DIR/<view>_<light>.png.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.normpath(os.path.join(HERE, "..", "..", "textures", "rider"))
CAMS = os.path.normpath(os.path.join(HERE, "..", "..", "research", "goggle-cameras.json"))
argv = sys.argv[sys.argv.index("--") + 1:]
NPZ, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
SPEC = json.load(open(CAMS))
NAMES = argv[2].split(",") if len(argv) > 2 and argv[2] else [k for k in SPEC if not k.startswith("_")]
SAMPLES = int(argv[3]) if len(argv) > 3 and argv[3] else 64
LIGHT = argv[4] if len(argv) > 4 else "studio"
RAKE = {"rakeT": (0.0, -0.36, 1.0), "rakeL": (1.0, -0.36, 0.15), "rakeR": (-1.0, -0.36, 0.15),
        "rakeB": (0.0, -0.36, -1.0)}   # towards the sun
SCALE = float(os.environ.get("GOGGLE_VIEWS_SCALE", "0.5"))
LIGHT_SIZE = float(os.environ.get("GOGGLE_VIEWS_LIGHT_SIZE", "1.0"))       # the studio's area lights (m; round 6)
os.makedirs(OUT, exist_ok=True)


def lin(c):
    c = np.asarray(c, float) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).tolist()) + (1.0,)


def material(name, spec):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    if "rgb" in spec:
        p.inputs["Base Color"].default_value = lin(spec["rgb"])
    p.inputs["Roughness"].default_value = spec.get("rough", 0.5)
    p.inputs["Metallic"].default_value = spec.get("metal", 0.0)
    p.inputs["Coat Weight"].default_value = spec.get("coat", 0.0)
    p.inputs["Sheen Weight"].default_value = spec.get("sheen", 0.0)
    if "transmission" in spec:
        p.inputs["Transmission Weight"].default_value = spec["transmission"]
    if "thin_film" in spec:
        p.inputs["Thin Film Thickness"].default_value = spec["thin_film"].get("thickness_nm", 500.0)
        p.inputs["Thin Film IOR"].default_value = spec["thin_film"].get("ior", 1.5)
    if "image" in spec:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEXDIR, spec["image"]))
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    return m


def load(path):
    g = np.load(path)
    spec = json.loads(str(g["materials"]))
    mats = [str(m) for m in g["mats"]]
    bm = {m: material(m, spec.get(m, {})) for m in mats}
    for name in [str(n) for n in g["names"]]:
        V, F, FS, M = g[name + "__V"], g[name + "__F"], g[name + "__FS"], g[name + "__M"]
        starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], [F[s:s + n].tolist() for s, n in zip(starts, FS)])
        used = sorted(set(M.tolist()))
        for mi in used:
            me.materials.append(bm[mats[mi]])
        slot = {mi: k for k, mi in enumerate(used)}
        me.polygons.foreach_set("material_index", [slot[int(mi)] for mi in M])
        if name + "__UV" in g:
            uv = me.uv_layers.new(name="UVMap")
            uv.data.foreach_set("uv", g[name + "__UV"].astype(np.float32).ravel())
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.validate()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)


def studio(sc):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    # the backdrop seen by the camera is Leatt's light grey (236/255: strength 5.0 renders about 234 under AgX); the
    # light it casts is kept low so the frame keeps its colour (a bright world washed the pink out)
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.84, 0.84, 0.84, 1)
    bg.inputs["Strength"].default_value = 5.0
    amb = nt.nodes.new("ShaderNodeBackground")
    amb.inputs["Color"].default_value = (0.84, 0.84, 0.84, 1)
    amb.inputs["Strength"].default_value = 0.25
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(amb.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs["Surface"])
    for loc, en in (((-1.5, -2.5, 2.5), 300), ((2.0, -1.5, 1.0), 110), ((0.0, 2.0, 2.0), 90)):
        L = bpy.data.lights.new("key", "AREA")
        L.energy = en
        L.size = LIGHT_SIZE
        o = bpy.data.objects.new("key", L)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(o)


def rake(sc, which):
    """The studio's lights off and its ambient low, a sun grazing the frame's front faces (RAKE)."""
    if which not in RAKE:
        raise SystemExit("light: studio or one of " + ", ".join(RAKE))
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        o.hide_render = True
    for n in sc.world.node_tree.nodes:
        if n.type == "BACKGROUND" and n.inputs["Strength"].default_value < 1.0:
            n.inputs["Strength"].default_value *= 0.12
    L = bpy.data.lights.new("rake", "SUN")
    L.energy = 5.0
    L.angle = math.radians(0.5)
    o = bpy.data.objects.new("rake", L)
    o.rotation_euler = Vector(RAKE[which]).normalized().to_track_quat("Z", "Y").to_euler()
    sc.collection.objects.link(o)
    vs = sc.view_settings
    vs.view_transform, vs.look, vs.exposure = "AgX", "AgX - Punchy", 0.0


def camera(sc, name, x, W, H):
    az, el, roll, d, f, u0, v0 = x
    a, e = math.radians(az), math.radians(el)
    dirn = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    C = dirn * d
    fwd = -dirn
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd)
    r = math.radians(roll)
    right, up = right * math.cos(r) + up * math.sin(r), up * math.cos(r) - right * math.sin(r)
    M = Matrix((right, up, -fwd)).transposed().to_4x4()
    M.translation = C
    cam = bpy.data.objects.new("cam_" + name, bpy.data.cameras.new("cam_" + name))
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.lens = f * 36.0 / W
    cam.data.shift_x = -u0 / W
    cam.data.shift_y = v0 / W
    cam.data.clip_start = 0.05
    cam.matrix_world = M
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = int(W * SCALE), int(H * SCALE)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    load(NPZ)
    studio(sc)
    if LIGHT != "studio":
        rake(sc, LIGHT)
    for name in NAMES:
        s = SPEC[name]
        camera(sc, name, s["x"], s["W"], s["H"])
        sc.render.filepath = os.path.join(OUT, name + ("" if LIGHT == "studio" else "_" + LIGHT) + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


main()
