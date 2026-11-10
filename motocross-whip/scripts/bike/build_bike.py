"""Assemble Damien's bike in Blender from the generated parts (parts.py) and the livery (livery.py), then render
previews and export glTF.

blender -b --factory-startup --python-exit-code 1 --python build_bike.py -- PARTS.npz TEXTURES_DIR OUT_DIR [views]
  views: comma list of camera names (default all); 'none' to skip rendering
Writes OUT_DIR/bike_v0.blend, OUT_DIR/bike_v0.glb and OUT_DIR/render_<view>.png.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from bpy_extras import anim_utils  # noqa: F401  (kept for later animation of the steering)
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
PARTS, TEX, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1]), os.path.abspath(argv[2])
VIEWS = argv[3].split(",") if len(argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
BP = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))["left"]
MAPS = json.load(open(os.path.join(TEX, "maps.json")))
RAKE = math.radians(28.4)


def srgb(c):
    c = c / 255.0 if c > 1 else c
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb):
    return tuple(srgb(v) for v in rgb) + (1.0,)


# ---------------------------------------------------------------- materials
def principled(name, rgb=None, metal=0.0, rough=0.5, image=None, coat=0.0, aniso=0.0, bump=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    if rgb is not None:
        p.inputs["Base Color"].default_value = lin(rgb)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Anisotropic"].default_value = aniso
    p.inputs["Specular IOR Level"].default_value = spec
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.join(TEX, image))
        tex.interpolation = "Cubic"
        nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    if bump > 0:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 900.0
        noise.inputs["Detail"].default_value = 2.0
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        b.inputs["Distance"].default_value = 0.0004
        nt.links.new(noise.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    m.diffuse_color = lin(rgb) if rgb else (0.8, 0.1, 0.1, 1)
    return m


RED = (200, 16, 28)
MATS = {
    "livery_L": dict(image="side_L.png", rough=0.34, coat=0.08),
    "livery_R": dict(image="side_R.png", rough=0.34, coat=0.08),
    "livery_fender": dict(image="fender.png", rough=0.34, coat=0.08),
    "fender_front": dict(image="front_fender.png", rough=0.34, coat=0.08),
    "seat": dict(image="seat.png", rough=0.75, bump=0.35),
    "plate": dict(image="plate.png", rough=0.34, coat=0.08),
    "barpad": dict(image="barpad.png", rough=0.7),
    "swing_L": dict(image="swingarm_L.png", metal=0.6, rough=0.12),
    "swing_R": dict(image="swingarm_R.png", metal=0.6, rough=0.12),
    "fork_guard": dict(rgb=RED, rough=0.35),
    "black_texture": dict(rgb=(18, 18, 20), rough=0.6, bump=0.6),
    "plastic_black": dict(rgb=(14, 14, 16), rough=0.45),
    "alu_frame": dict(rgb=(205, 205, 208), metal=1.0, rough=0.32, aniso=0.6),
    "alu_swingarm": dict(rgb=(200, 200, 204), metal=1.0, rough=0.32, aniso=0.6),
    "alu_cast": dict(rgb=(175, 175, 178), metal=1.0, rough=0.5),
    "alu_machined": dict(rgb=(215, 215, 218), metal=1.0, rough=0.2),
    "fork_gold": dict(rgb=(214, 166, 92), metal=1.0, rough=0.16),
    "fork_inner": dict(rgb=(40, 40, 44), metal=1.0, rough=0.15),
    "fork_lug": dict(rgb=(180, 180, 184), metal=1.0, rough=0.35),
    "anod_black": dict(rgb=(18, 18, 20), metal=1.0, rough=0.3),
    "rubber": dict(rgb=(16, 16, 17), rough=0.85, bump=0.15),
    "rubber_black": dict(rgb=(20, 20, 21), rough=0.6),
    "rim": dict(rgb=(14, 14, 15), metal=1.0, rough=0.3),
    "hub": dict(rgb=(190, 190, 194), metal=1.0, rough=0.3),
    "spoke": dict(rgb=(185, 185, 190), metal=1.0, rough=0.22),
    "disc": dict(rgb=(150, 150, 155), metal=1.0, rough=0.35, aniso=0.4),
    "sprocket": dict(rgb=(170, 170, 175), metal=1.0, rough=0.4),
    "chain": dict(rgb=(50, 48, 46), metal=1.0, rough=0.45),
    "engine_case": dict(rgb=(150, 150, 154), metal=0.8, rough=0.45),
    "engine_cover": dict(rgb=(165, 165, 170), metal=0.9, rough=0.3),
    "engine_black": dict(rgb=(16, 16, 18), rough=0.5),
    "header_rust": dict(rgb=(120, 64, 32), metal=1.0, rough=0.55, bump=0.4),
    "muffler": dict(rgb=(190, 190, 195), metal=1.0, rough=0.28, aniso=0.5),
    "muffler_cap": dict(rgb=(40, 40, 42), metal=1.0, rough=0.35),
    "tank_ti": dict(rgb=(150, 140, 128), metal=1.0, rough=0.3),
    "radiator": dict(rgb=(22, 22, 24), metal=0.5, rough=0.6),
    "louvre": dict(rgb=(14, 14, 16), rough=0.5),
    "steel": dict(rgb=(170, 170, 175), metal=1.0, rough=0.3),
    "chrome": dict(rgb=(235, 235, 240), metal=1.0, rough=0.05),
    "shock_body": dict(rgb=(25, 25, 28), metal=1.0, rough=0.3),
    "spring": dict(rgb=(170, 170, 175), metal=1.0, rough=0.25),
    "caliper": dict(rgb=(120, 120, 125), metal=1.0, rough=0.35),
    "red_anod": dict(rgb=(190, 14, 20), metal=1.0, rough=0.25),
    "lever": dict(rgb=(180, 180, 185), metal=1.0, rough=0.3),
    "grip": dict(rgb=(22, 22, 24), rough=0.8, bump=0.3),
    "bar_black": dict(rgb=(20, 20, 22), metal=0.6, rough=0.35),
}

THIN = {"front_fender", "rear_fender", "number_plate", "fork_guards"}      # single surfaces: solidify
BEVEL = {"engine": 0.006, "frame": 0.003, "swingarm": 0.003, "clamps": 0.003}           # rounded machined edges
SMOOTH_ANGLE = {"shrouds": 70, "side_panels": 70, "seat": 70, "front_fender": 70, "rear_fender": 70,
                "number_plate": 70, "fork_guards": 70, "tank": 60}
FRONT_END = {"fork", "fork_guards", "clamps", "bars", "number_plate", "front_fender", "front_wheel"}


def uv_for(mat, co, nrm=(0.0, 0.0, 1.0)):
    """UV of one corner by the material's projection (textures painted by livery.py in bike coordinates)."""
    x, y, z = co
    if mat in ("livery_L", "livery_R"):
        s = MAPS["side"]
        u = (s["x1"] - x) / (s["x1"] - s["x0"]) if mat == "livery_L" else (x - s["x0"]) / (s["x1"] - s["x0"])
        return u, (z - s["z0"]) / (s["z1"] - s["z0"])
    if mat in ("swing_L", "swing_R"):
        s = MAPS["swingarm"]
        u = (s["x1"] - x) / (s["x1"] - s["x0"]) if mat == "swing_L" else (x - s["x0"]) / (s["x1"] - s["x0"])
        return u, (z - s["z0"]) / (s["z1"] - s["z0"])
    key = {"livery_fender": "fender", "fender_front": "front_fender", "seat": "seat"}.get(mat)
    if key:
        s = MAPS[key]
        return (s["x1"] - x) / (s["x1"] - s["x0"]), (y - s["y0"]) / (s["y1"] - s["y0"])
    if mat == "plate":
        s = MAPS["plate"]
        along = (z - 0.94) / math.cos(RAKE)
        return (y - s["u0"]) / (s["u1"] - s["u0"]), (along - s["s0"]) / (s["s1"] - s["s0"])
    if mat == "barpad":                           # lettering reads correctly from the front and from the seat
        u = (y + 0.105) / 0.21 if nrm[0] > 0.3 else (0.105 - y) / 0.21
        return u, (z - 1.17) / 0.05
    return 0.5, 0.5


def build_parts():
    data = np.load(PARTS)
    mats = [str(m) for m in data["materials"]]
    bmats = {}
    for m in mats:
        bmats[m] = principled(m, **MATS.get(m, dict(rgb=(200, 0, 200))))
    col = bpy.data.collections.new("bike_v0")
    bpy.context.scene.collection.children.link(col)
    steer0, up = data["steer_axis"]
    rx, ry, rz, pitch = data["ground"]
    # root: tilts the bike (built in the axle-line frame) nose-up about the rear axle so both tyres touch the ground
    root = bpy.data.objects.new("bike", None)
    Rm = Matrix.Rotation(-float(pitch), 4, "Y")
    ra = Vector((float(rx), float(ry), float(rz)))
    root.matrix_world = Matrix.Translation(ra) @ Rm @ Matrix.Translation(-ra)
    col.objects.link(root)
    steer = bpy.data.objects.new("steer", None)            # front end turns about this empty (steering axis)
    steer.parent = root
    steer.location = Vector(steer0.tolist())
    steer["axis"] = list(map(float, up))
    col.objects.link(steer)
    objs = {}
    for name in [str(n) for n in data["names"]]:
        V = data[f"{name}__V"]
        S = data[f"{name}__S"]
        Fl = data[f"{name}__F"]
        M = data[f"{name}__M"]
        faces, k = [], 0
        for sz in S:
            faces.append(tuple(Fl[k:k + sz]))
            k += sz
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], faces)
        me.validate(clean_customdata=False)
        used = sorted(set(M.tolist()))
        for mi in used:
            me.materials.append(bmats[mats[mi]])
        remap = {mi: i for i, mi in enumerate(used)}
        me.polygons.foreach_set("material_index", [remap[int(v)] for v in M[:len(me.polygons)]])
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            mname = mats[used[poly.material_index]]
            nrm = tuple(poly.normal)
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = uv_for(mname, (co.x, co.y, co.z), nrm)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(SMOOTH_ANGLE.get(name, 35)))
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        if name in THIN:
            sol = ob.modifiers.new("thickness", "SOLIDIFY")
            sol.thickness = 0.003
            sol.offset = -1.0
        if name in BEVEL:
            bv = ob.modifiers.new("edges", "BEVEL")
            bv.width = BEVEL[name]
            bv.segments = 2
            bv.limit_method = "ANGLE"
            bv.angle_limit = math.radians(40)
        if name in FRONT_END:
            ob.parent = steer
            ob.matrix_parent_inverse = Matrix.Translation(-Vector(steer0.tolist()))
        else:
            ob.parent = root
        objs[name] = ob
    return col, objs


# ---------------------------------------------------------------- studio
def studio():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("studio")
    sc.world = w
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.9, 0.9, 0.9, 1)
    bg.inputs["Strength"].default_value = 0.30
    # white cyclorama: floor curving up into a back wall behind the bike (far side, -y)
    me = bpy.data.meshes.new("cyc")
    verts, faces = [], []
    prof = [(-8.0, 0.0)]
    for a in np.linspace(0, math.pi / 2, 12):
        prof.append((-3.0 - 1.5 * math.sin(a), 1.5 - 1.5 * math.cos(a)))
    prof.append((-4.5, 6.0))
    prof = [(8.0, 0.0)] + [(-3.0 + 0.0, 0.0)] + prof[1:]
    xs = [-6.0, 8.0]
    for i, (yy, zz) in enumerate(prof):
        for x in xs:
            verts.append((x, yy, zz))
    for i in range(len(prof) - 1):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))          # normals toward the bike (up, forward)
    me.from_pydata(verts, [], faces)
    me.shade_smooth()
    cyc = bpy.data.objects.new("cyc", me)
    sc.collection.objects.link(cyc)
    cm = principled("cyc_white", rgb=(235, 235, 235), rough=0.7)
    me.materials.append(cm)

    def area(name, loc, target, size, power, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.size = size
        ld.energy = power
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        d = Vector(target) - Vector(loc)
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)

    area("key", (1.8, 3.2, 3.2), (0.75, 0, 0.6), 3.0, 420)
    area("fill", (0.2, -3.0, 2.2), (0.75, 0, 0.6), 3.5, 160)
    area("top", (0.75, 0.0, 4.0), (0.75, 0, 0.6), 4.0, 300)
    area("rim", (-2.5, 1.5, 2.0), (0.75, 0, 0.7), 2.0, 130)
    area("front", (4.0, 1.0, 1.4), (0.75, 0, 0.6), 2.5, 150)
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"              # closest to his bike's deep red (look test 2026-11-10)
    sc.view_settings.exposure = -0.6


def camera(name, loc, target, lens=50.0, ortho=None, roll=0.0, res=(1280, 720)):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.sensor_fit = "AUTO"
    cd.sensor_width = 36.0
    co = bpy.data.objects.new(name, cd)
    co.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat("-Z", "Y")
    co.rotation_euler = q.to_euler()
    if roll:
        co.rotation_euler.rotate_axis("Z", roll)
    bpy.context.scene.collection.objects.link(co)
    co["res"] = list(res)
    return co


def cameras():
    cams = []
    # Honda's left profile, reproduced: orthographic, same scale and framing as the 4000x2250 studio photo
    s = BP["mm_per_px"] / 1000.0
    fa, ra = np.array(BP["front_axle_px"]), np.array(BP["rear_axle_px"])
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]])
    if v[1] > 0:
        v = -v
    c_img = np.array([2000.0, 1125.0]) - ra
    cx, cz = c_img @ u * s, c_img @ v * s + BP["rear_tyre_od_mm"] / 2000.0       # axle-line frame
    pitch = float(np.load(PARTS)["ground"][3])
    r0 = np.array([0.0, BP["rear_tyre_od_mm"] / 2000.0])
    c, sn = math.cos(pitch), math.sin(pitch)
    d = np.array([cx, cz]) - r0
    gx, gz = r0 + np.array([c * d[0] - sn * d[1], sn * d[0] + c * d[1]])            # ground frame
    # the axle line is at PITCH to the ground in the model and at tilt_deg in the photo: roll the camera by the
    # difference so the model lands on the photo pixel for pixel
    roll = pitch - math.radians(BP["tilt_deg"])
    cams.append(camera("profile_left", (gx, 10.0, gz), (gx, 0.0, gz), ortho=4000 * s, roll=roll, res=(2000, 1125)))
    # angles of Damien's photos (DV 01: front-left three-quarter, low; DV 02: left side from the front; DV 04: cockpit)
    cams.append(camera("dv01_front_left", (2.75, 0.80, 1.05), (1.00, 0.0, 0.66), lens=26, res=(739, 1600)))
    cams.append(camera("dv02_left_front", (1.30, 0.95, 1.12), (0.42, 0.0, 0.72), lens=26, res=(739, 1600)))
    cams.append(camera("dv04_cockpit", (0.20, 0.0, 1.40), (1.40, 0.0, 0.98), lens=26, res=(900, 1600)))
    cams.append(camera("right_rear_34", (-1.2, -2.6, 1.25), (0.70, 0.0, 0.58), lens=40, res=(1600, 900)))
    cams.append(camera("left_34_hero", (2.4, 2.6, 1.15), (0.72, 0.0, 0.58), lens=40, res=(1600, 900)))
    return cams


def render(cams):
    sc = bpy.context.scene
    for co in cams:
        if VIEWS and co.name not in VIEWS:
            continue
        sc.camera = co
        sc.render.resolution_x, sc.render.resolution_y = co["res"]
        sc.render.resolution_percentage = 100
        sc.render.filepath = os.path.join(OUT, f"render_{co.name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath, flush=True)


def export_glb(col):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name in col.all_objects)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "bike_v0.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_image_format="JPEG", export_jpeg_quality=88)


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    col, objs = build_parts()
    studio()
    cams = cameras()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "bike_v0.blend"))
    export_glb(col)
    if VIEWS != ["none"]:
        render(cams)
    print("BUILD OK", len(objs), "parts")


main()
