"""Damien the rider in Blender: body mesh with UVs, the MakeHuman default skeleton, skin weights, optional pose.

blender -b --factory-startup --python-exit-code 1 --python build_rider.py -- BODY.npz OUT_DIR [views] [POSE.json]

The body is built in body.py's MB frame (z up, facing -y) under an empty "rider" turned +90 deg about z, so in the
world it faces +x like the bike (x forward, y left, z up). views: comma list of front, side, back, three (renders
on a white studio floor, 1200 x 1600) or none. POSE.json: {"bones": {name: [w, x, y, z] quaternion}, "root":
[x, y, z, yaw_deg]} applied to the armature (pose.py writes it).

Gear: RIDER_GEAR="a.npz,b.npz" adds gear modules' parts (helmet.py, boots.py, ...). A gear npz holds
  names            part names
  mats             material names; materials: JSON {name: {rgb: [r, g, b] sRGB 0..255, rough, metal, coat, sheen,
                   alpha, transmission, thin_film: {thickness_nm, ior}, image: file under textures/rider/ or
                   absolute, normal: file, bump}}
  <p>__V, <p>__F, <p>__FS   vertices (MB rest frame of body.py, metres), faces as a flat list with sizes
  <p>__M           material index of each face (into mats)
  <p>__UV          optional face-corner UVs (sum(FS) x 2)
  <p>__bone        a bone name: the part rides that bone rigidly (helmet: "head"), or
  <p>__wv, <p>__wb, <p>__ww   skin weights (vertex, bone index into body.npz "bones", weight): it deforms
  <p>__smooth      optional: 1 = smooth shading (default), 0 = flat
  hide_body        optional: body vertex ids the gear covers completely; they are masked out of the render so
                   skin never shows through (a vertex group "covered" and a Mask modifier on the body)
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
BODY, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
VIEWS = [v for v in (argv[2].split(",") if len(argv) > 2 else ["front", "side"]) if v and v != "none"]
POSE = argv[3] if len(argv) > 3 else None
SAMPLES = int(os.environ.get("RIDER_SAMPLES", "48"))
os.makedirs(OUT, exist_ok=True)


def lin(c):
    c = np.asarray(c, float) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)) + (1.0,)


def skin_material():
    """Skin, for the body under the kit (only the face shows through the goggles). Subsurface for skin."""
    m = bpy.data.materials.new("skin")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin((198, 150, 122))
    p.inputs["Roughness"].default_value = 0.5
    p.inputs["Subsurface Weight"].default_value = 0.15
    p.inputs["Subsurface Radius"].default_value = (0.012, 0.004, 0.002)
    return m


def build(d):
    root = bpy.data.objects.new("rider", None)
    root.rotation_euler = (0.0, 0.0, math.pi / 2)              # MB faces -y; the bike faces +x
    bpy.context.scene.collection.objects.link(root)
    # armature
    arm = bpy.data.armatures.new("rider_rig")
    rig = bpy.data.objects.new("rider_rig", arm)
    rig.parent = root
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    names = [str(n) for n in d["bones"]]
    eb = {}
    for i, n in enumerate(names):
        b = arm.edit_bones.new(n)
        b.head = Vector(d["heads"][i].tolist())
        b.tail = Vector(d["tails"][i].tolist())
        if (b.tail - b.head).length < 1e-5:
            b.tail = b.head + Vector((0, 0, 0.01))
        b.roll = float(d["rolls"][i])
        eb[n] = b
    for i, n in enumerate(names):
        p = str(d["parents"][i])
        if p:
            eb[n].parent = eb[p]
            eb[n].use_connect = bool(d["connect"][i])
    bpy.ops.object.mode_set(mode="OBJECT")
    # mesh
    V = d["V"]
    FS, F = d["FS"], d["F"]
    starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
    me = bpy.data.meshes.new("rider_body")
    me.from_pydata(V.tolist(), [], [F[s:s + n].tolist() for s, n in zip(starts, FS)])
    uv = me.uv_layers.new(name="UVMap")
    uv.data.foreach_set("uv", d["UV"].astype(np.float32).ravel())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.validate()
    me.materials.append(skin_material())
    body = bpy.data.objects.new("rider_body", me)
    body.parent = rig
    bpy.context.scene.collection.objects.link(body)
    groups = {n: body.vertex_groups.new(name=n) for n in names}
    wv, ww, wb = d["w_vert"], d["w_val"], d["w_bone"]
    for bi in np.unique(wb):
        sel = wb == bi
        g = groups[names[bi]]
        for vi, x in zip(wv[sel].tolist(), ww[sel].tolist()):
            g.add([vi], float(x), "REPLACE")
    mod = body.modifiers.new("skeleton", "ARMATURE")
    mod.object = rig
    sub = body.modifiers.new("smooth", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    return root, rig, body


TEXDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textures", "rider")


def gear_material(name, spec):
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
    if "alpha" in spec:
        p.inputs["Alpha"].default_value = spec["alpha"]
    if "transmission" in spec:
        p.inputs["Transmission Weight"].default_value = spec["transmission"]
    if "thin_film" in spec:                                       # an iridescent mirror coating (goggle lens)
        p.inputs["Thin Film Thickness"].default_value = spec["thin_film"].get("thickness_nm", 500.0)
        p.inputs["Thin Film IOR"].default_value = spec["thin_film"].get("ior", 1.5)
    if "image" in spec:
        f = spec["image"] if os.path.isabs(spec["image"]) else os.path.join(TEXDIR, spec["image"])
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(f)
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    if "normal" in spec:
        f = spec["normal"] if os.path.isabs(spec["normal"]) else os.path.join(TEXDIR, spec["normal"])
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(f)
        t.image.colorspace_settings.name = "Non-Color"
        n = nt.nodes.new("ShaderNodeNormalMap")
        n.inputs["Strength"].default_value = spec.get("normal_strength", 1.0)
        nt.links.new(t.outputs["Color"], n.inputs["Color"])
        nt.links.new(n.outputs["Normal"], p.inputs["Normal"])
    elif "bump" in spec:
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = spec["bump"]
        tx = nt.nodes.new("ShaderNodeTexNoise")
        tx.inputs["Scale"].default_value = spec.get("bump_scale", 600.0)
        nt.links.new(tx.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return m


def add_gear(path, rig, body_bones):
    g = np.load(path)
    mats_spec = json.loads(str(g["materials"]))
    mats = [str(m) for m in g["mats"]]
    bmats = {m: bpy.data.materials.get(m) or gear_material(m, mats_spec.get(m, {})) for m in mats}
    out = []
    for name in [str(n) for n in g["names"]]:
        V, F, FS, M = g[name + "__V"], g[name + "__F"], g[name + "__FS"], g[name + "__M"]
        starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], [F[s:s + n].tolist() for s, n in zip(starts, FS)])
        used = sorted(set(M.tolist()))
        for mi in used:
            me.materials.append(bmats[mats[mi]])
        slot = {mi: k for k, mi in enumerate(used)}
        me.polygons.foreach_set("material_index", [slot[int(mi)] for mi in M])
        if name + "__UV" in g:
            uv = me.uv_layers.new(name="UVMap")
            uv.data.foreach_set("uv", g[name + "__UV"].astype(np.float32).ravel())
        smooth = bool(int(g[name + "__smooth"])) if name + "__smooth" in g else True
        me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
        me.validate()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        if name + "__bone" in g:                                  # rigid on one bone, at its rest place
            bone = str(g[name + "__bone"])
            ob.parent = rig
            ob.parent_type = "BONE"
            ob.parent_bone = bone
            pb = rig.data.bones[bone]
            ob.matrix_parent_inverse = (Matrix.Translation(pb.tail_local) @ pb.matrix_local.to_3x3().to_4x4()).inverted()
        else:
            ob.parent = rig
            groups = {}
            for vi, bi, w in zip(g[name + "__wv"].tolist(), g[name + "__wb"].tolist(), g[name + "__ww"].tolist()):
                bn = body_bones[bi]
                if bn not in groups:
                    groups[bn] = ob.vertex_groups.new(name=bn)
                groups[bn].add([vi], float(w), "REPLACE")
            mod = ob.modifiers.new("skeleton", "ARMATURE")
            mod.object = rig
        out.append(ob)
    return out


def to_arm(p):
    """Bike ground frame (x forward, y left, z up) -> armature space (MB: facing -y, left at +x); the root empty
    stays at the origin turned +90 deg, so the armature's space is the ground frame turned -90 deg."""
    x, y, z = p
    return Vector((y, -x, z))


def _set(pb, M):
    pb.matrix = M
    bpy.context.view_layer.update()


def rotate_about(pb, axis, ang, pivot=None):
    """Turn a pose bone (and so its children) by ang about an armature-space axis through pivot (default its head)."""
    M = pb.matrix.copy()
    c = M.translation if pivot is None else pivot
    R = Matrix.Rotation(ang, 4, axis)
    _set(pb, Matrix.Translation(c) @ R @ Matrix.Translation(-c) @ M)


def aim(pb, target, twist_ref=None):
    """Turn a pose bone about its head so its tail points at target (minimal turn)."""
    M = pb.matrix.copy()
    h = M.translation
    cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    want = (Vector(target) - h).normalized()
    q = cur.rotation_difference(want)
    _set(pb, Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M)


def two_bone(a, b_len, c_len, target, pole):
    """Middle joint of a two-segment chain from a towards target, bending towards pole."""
    a, t, pole = Vector(a), Vector(target), Vector(pole).normalized()
    d = t - a
    L = min(d.length, (b_len + c_len) * 0.9999)
    u = d.normalized()
    x = (b_len ** 2 - c_len ** 2 + L ** 2) / (2 * L)
    h = math.sqrt(max(b_len ** 2 - x ** 2, 0.0))
    side = (pole - u * pole.dot(u)).normalized()
    return a + u * x + side * h, a + u * L


def aim_pose(rig, p):
    """Pose from targets (pose.py): pelvis, spine lean, head, legs to the pegs, arms to the grips, curled fingers.
    Returns the placement errors (m) of the hands and feet."""
    pbs = rig.pose.bones
    for pb in pbs:
        pb.rotation_mode = "QUATERNION"
    X = Vector((1, 0, 0))                                         # his left: the pitch axis in armature space
    rest = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in rig.data.bones}
    # pelvis: tip forward, then move the hip joints' midpoint onto the target
    rotate_about(pbs["root"], X, math.radians(p["pelvis_pitch"]))
    roll = math.radians(p.get("pelvis_roll", 0.0))                # + = right hip down (foot to the ground)
    if roll:
        rotate_about(pbs["root"], Vector((0, 1, 0)), -roll)
    hip = (pbs["upperleg01.L"].head + pbs["upperleg01.R"].head) / 2
    M = pbs["root"].matrix.copy()
    _set(pbs["root"], Matrix.Translation(to_arm(p["pelvis"]) - hip) @ M)
    # spine: the rest of the lean, shared over the five spine bones
    extra = math.radians(p["spine_lean"] - p["pelvis_pitch"])
    for n in ("spine05", "spine04", "spine03", "spine02", "spine01"):
        rotate_about(pbs[n], X, extra / 5)
        if roll:
            rotate_about(pbs[n], Vector((0, 1, 0)), roll / 5)      # the trunk stays upright over a rolled pelvis
    # neck and head: bring the head back to head_pitch from vertical (the face looks ahead)
    up = (pbs["head"].tail - pbs["head"].head).normalized()
    tilt = math.atan2(-up.y, up.z)                              # forward tilt now (facing -y)
    corr = math.radians(p["head_pitch"]) - tilt
    for n in ("neck01", "neck02", "neck03", "head"):
        rotate_about(pbs[n], X, corr / 4)
    err = {}
    # legs
    for s in ("L", "R"):
        sg = 1 if s == "L" else -1
        H = pbs[f"upperleg01.{s}"].head.copy()
        K0, A0 = rest[f"lowerleg01.{s}"][0], rest[f"foot.{s}"][0]
        hip0 = rest[f"upperleg01.{s}"][0]
        balls0 = [rest[f"toe{i}-1.{s}"][0] for i in range(1, 6)]
        ball0 = sum(balls0, Vector()) / 5
        ball0.z = 0.0                                             # the sole under the ball
        B = to_arm(p["balls"][s])
        A = B + (A0 - ball0)                                      # foot level, pointing ahead
        pole = to_arm(Vector(p["knee_pole"]) * Vector((1, sg, 1)))
        K, A = two_bone(H, (K0 - hip0).length, (A0 - K0).length, A, pole)
        aim(pbs[f"upperleg01.{s}"], K)
        aim(pbs[f"upperleg02.{s}"], K)
        aim(pbs[f"lowerleg01.{s}"], A)
        aim(pbs[f"lowerleg02.{s}"], A)
        foot_dir = rest[f"foot.{s}"][1] - rest[f"foot.{s}"][0]
        aim(pbs[f"foot.{s}"], pbs[f"foot.{s}"].head + foot_dir)
        toes = sum([pbs[f"toe{i}-1.{s}"].head for i in range(1, 6)], Vector()) / 5
        err["foot_" + s] = ((toes - B) - (sum(balls0, Vector()) / 5 - ball0)).length
    # arms
    for s in ("L", "R"):
        sg = 1 if s == "L" else -1
        S = pbs[f"upperarm01.{s}"].head.copy()
        E0, W0 = rest[f"lowerarm01.{s}"][0], rest[f"wrist.{s}"][0]
        S0 = rest[f"upperarm01.{s}"][0]
        G = to_arm(p["hands"][s])
        u = (G - S).normalized()
        up = Vector((0, 0, 1))
        dors = (up - u * up.dot(u)).normalized()                   # square to the forearm's line, upwards
        Hc = G + dors * 0.036                                      # the hand's bone line rides 36 mm over the grip
        W = Hc - u * 0.075                                         # axis (16 mm grip radius + palm; gloves.py)
        pole = to_arm(Vector(p["elbow_pole"]) * Vector((1, sg, 1)))
        E, W = two_bone(S, (E0 - S0).length, (W0 - E0).length, W, pole)
        aim(pbs[f"upperarm01.{s}"], E)
        aim(pbs[f"upperarm02.{s}"], E)
        aim(pbs[f"lowerarm01.{s}"], W)
        aim(pbs[f"lowerarm02.{s}"], W)
        aim(pbs[f"wrist.{s}"], Hc + (Hc - W).normalized() * 0.02)
        err["hand_" + s] = (pbs[f"wrist.{s}"].head - W).length
        for f in range(1, 6):                                      # close the hand round the grip
            for j in (1, 2, 3):
                pb = pbs.get(f"finger{f}-{j}.{s}")
                if pb is not None:
                    ang = ((0.45, 0.35, 0.3)[j - 1] if f == 1 else (1.25, 1.35, 1.0)[j - 1])   # wrapped round
                    rotate_about(pb, (pb.matrix.to_3x3() @ Vector((1, 0, 0))).normalized(), ang)
    return err


def apply_pose(root, rig, pose):
    if "pelvis" in pose:                                          # targets (pose.py)
        err = aim_pose(rig, pose)
        print("POSE errors (m):", {k: round(v, 4) for k, v in err.items()})
        return
    for n, q in pose.get("bones", {}).items():
        pb = rig.pose.bones.get(n)
        if pb is not None:
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = Quaternion(q)
    if "root" in pose:
        x, y, z, yaw = pose["root"]
        root.location = (x, y, z)
        root.rotation_euler = (0.0, 0.0, math.pi / 2 + math.radians(yaw))


def studio():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1600
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.92, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    bpy.ops.mesh.primitive_plane_add(size=20)
    floor = bpy.context.active_object
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1)
    floor.data.materials.append(fm)
    for loc, en in (((3, -3, 5), 600), ((-3, 2, 4), 250)):
        L = bpy.data.lights.new("key", "AREA")
        L.energy = en
        L.size = 2.5
        o = bpy.data.objects.new("key", L)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.9)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(o)


VIEWDEF = {"front": ((3.4, 0.0, 1.0), 50, (0.0, 0.0, 0.93)), "side": ((0.0, 3.4, 1.0), 50, (0.0, 0.0, 0.93)),
           "back": ((-3.4, 0.0, 1.0), 50, (0.0, 0.0, 0.93)), "three": ((2.6, 2.2, 1.35), 50, (0.0, 0.0, 0.93)),
           # on the bike (ground frame of the bike): his left side, front-left three-quarter, photo 05's angle
           "bike_left": ((0.75, 4.6, 0.95), 40, (0.70, 0.0, 0.85)),
           "bike_34": ((3.3, 2.6, 1.45), 40, (0.70, 0.0, 0.90)),
           "bike_front": ((4.6, 0.0, 1.15), 40, (0.70, 0.0, 0.95)),
           "p05": ((1.25, 3.6, 1.10), 34, (0.75, 0.0, 0.90)),
           "hand_L": ((1.30, 0.80, 1.42), 55, (0.92, 0.36, 1.23), (1200, 900)),        # left hand on its grip
           "hand_R_top": ((0.62, -0.30, 1.75), 55, (0.92, -0.36, 1.22), (1200, 900)),  # right hand, rider's eye
           # the camera build_bike's cu_p07 close-up used for his photo 07 (1332 x 888, riding, left side)
           "p07": ((0.80, 4.6, 0.95), 45, (0.78, 0.0, 0.62), (1332, 888))}


def photo_camera(spec, scale=2):
    """A camera fitted to one of his photos (research/rider-cameras.json): focal length in pixels, rotation vector
    (world -> camera: x right, y up, looking along -z) and centre, at the photo's own size times scale."""
    cam = bpy.data.objects.new("cam_photo", bpy.data.cameras.new("cam_photo"))
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.lens = spec["f"] * 36.0 / spec["W"]
    R = Matrix.Rotation(np.linalg.norm(spec["rotvec"]), 3, Vector(spec["rotvec"]).normalized()) \
        if np.linalg.norm(spec["rotvec"]) > 0 else Matrix.Identity(3)
    cam.matrix_world = Matrix.Translation(Vector(spec["C"])) @ R.transposed().to_4x4()
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = int(spec["W"] * scale), int(spec["H"] * scale)
    return cam


# close-ups: RIDER_CLOSEUPS="name:x,y,z:tx,ty,tz:lens[:w,h];..." (world frame: x forward, y left, z up)
for _spec in filter(None, os.environ.get("RIDER_CLOSEUPS", "").split(";")):
    _f = _spec.split(":")
    VIEWDEF[_f[0]] = (tuple(map(float, _f[1].split(","))), float(_f[3]), tuple(map(float, _f[2].split(","))),
                      tuple(map(int, _f[4].split(","))) if len(_f) > 4 else (1200, 900))


def render(name):
    sc = bpy.context.scene
    if name.startswith("photo:"):                                 # photo:<camera name> from RIDER_CAMS json
        spec = json.load(open(os.environ["RIDER_CAMS"]))[name[6:]]
        cam = photo_camera(spec)
        sc.collection.objects.link(cam)
        sc.camera = cam
        sc.render.filepath = os.path.join(OUT, f"rider_{name[6:]}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)
        sc.render.resolution_x, sc.render.resolution_y = 1200, 1600
        return
    loc, lens, target = VIEWDEF[name][:3]
    res = VIEWDEF[name][3] if len(VIEWDEF[name]) > 3 else (1200, 1600)
    sc.render.resolution_x, sc.render.resolution_y = res
    cam = bpy.data.objects.new("cam_" + name, bpy.data.cameras.new("cam_" + name))
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = os.path.join(OUT, f"rider_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", bpy.context.scene.render.filepath)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    d = np.load(BODY)
    root, rig, body = build(d)
    covered = set()
    for gpath in [p for p in os.environ.get("RIDER_GEAR", "").split(",") if p]:
        add_gear(os.path.abspath(gpath), rig, [str(n) for n in d["bones"]])
        g = np.load(os.path.abspath(gpath))
        if "hide_body" in g:
            covered |= set(g["hide_body"].tolist())
    if covered:
        vg = body.vertex_groups.new(name="covered")
        vg.add(sorted(covered), 1.0, "REPLACE")
        m = body.modifiers.new("covered", "MASK")
        m.vertex_group = "covered"
        m.invert_vertex_group = True
        body.modifiers.move(len(body.modifiers) - 1, 1)          # armature, mask, then the subdivision
    if POSE:
        apply_pose(root, rig, json.load(open(POSE)))
    bike = os.environ.get("RIDER_BIKE")                           # "bike.blend::collection": the bike to sit on
    if bike:
        f, col = bike.split("::")
        with bpy.data.libraries.load(f, link=False) as (src, dst):
            dst.collections = [col]
        for c in dst.collections:
            bpy.context.scene.collection.children.link(c)
    bpy.ops.file.pack_all()                                       # textures inside the file: it opens anywhere
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "rider.blend"))
    if VIEWS:
        studio()
        for v in VIEWS:
            render(v)


main()
