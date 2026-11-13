"""Damien the rider in Blender: body mesh with UVs, the MakeHuman default skeleton, skin weights, optional pose.

blender -b --factory-startup --python-exit-code 1 --python build_rider.py -- BODY.npz OUT_DIR [views] [POSE.json]

The body is built in body.py's MB frame (z up, facing -y) under an empty "rider" turned +90 deg about z, so in the
world it faces +x like the bike (x forward, y left, z up). views: comma list of front, side, back, three (renders
on a white studio floor, 1200 x 1600) or none. POSE.json: {"bones": {name: [w, x, y, z] quaternion}, "root":
[x, y, z, yaw_deg]} applied to the armature (pose.py writes it).

Gear: RIDER_GEAR="a.npz,b.npz" adds gear modules' parts (helmet.py, boots.py, ...). A gear npz holds
  names            part names
  mats             material names; materials: JSON {name: {rgb: [r, g, b] sRGB 0..255, rough, metal, coat, sheen,
                   alpha, image: file under textures/rider/ or absolute, normal: file, bump}}
  <p>__V, <p>__F, <p>__FS   vertices (MB rest frame of body.py, metres), faces as a flat list with sizes
  <p>__M           material index of each face (into mats)
  <p>__UV          optional face-corner UVs (sum(FS) x 2)
  <p>__bone        a bone name: the part rides that bone rigidly (helmet: "head"), or
  <p>__wv, <p>__wb, <p>__ww   skin weights (vertex, bone index into body.npz "bones", weight): it deforms
  <p>__smooth      optional: 1 = smooth shading (default), 0 = flat
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


def apply_pose(root, rig, pose):
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


VIEWDEF = {"front": ((3.4, 0.0, 1.0), 50), "side": ((0.0, 3.4, 1.0), 50), "back": ((-3.4, 0.0, 1.0), 50),
           "three": ((2.6, 2.2, 1.35), 50)}


def render(name, target=(0.0, 0.0, 0.93)):
    loc, lens = VIEWDEF[name]
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
    for gpath in [p for p in os.environ.get("RIDER_GEAR", "").split(",") if p]:
        add_gear(os.path.abspath(gpath), rig, [str(n) for n in d["bones"]])
    if POSE:
        apply_pose(root, rig, json.load(open(POSE)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "rider.blend"))
    if VIEWS:
        studio()
        for v in VIEWS:
            render(v)


main()
