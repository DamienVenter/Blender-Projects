"""Build the whip demo scene in Blender 5.2 from the simulation export.

blender -b --factory-startup --python-exit-code 1 --python build_scene.py -- DATA_DIR OUT_BLEND

DATA_DIR holds frames.json (per-frame transforms) and scene.json (terrain, cameras,
bike geometry). Proxy geometry only: the demo is about motion and physics.
Animation is written with the Blender 5 layered-action API (channelbags).
"""
import bisect
import json
import math
import sys

import bmesh
import bpy
from bpy_extras import anim_utils
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
DATA, OUT = argv[0], argv[1]
with open(f"{DATA}/scene.json") as f:
    SC = json.load(f)
with open(f"{DATA}/frames.json") as f:
    FR = json.load(f)

FPS = 120

# start from an empty scene (factory startup ships a cube, a light and a camera)
for _ob in list(bpy.data.objects):
    bpy.data.objects.remove(_ob, do_unlink=True)

# ---------------------------------------------------------------- helpers

def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


MATS = {}


def mat(name, hexcol, rough=0.5, metal=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    col = srgb(hexcol)
    m.diffuse_color = col                      # Workbench "Material" colour
    m.roughness = rough
    m.metallic = metal
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = col
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    MATS[name] = m
    return m


def new_obj(name, bm, material, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def tube(p0, p1, r0, r1=None, ry0=None, ry1=None, seg=20, rings=2, caps=True, x_hint=(0, 0, 1)):
    """Tapered elliptical tube from p0 to p1 (local coords). ry = radius across the x_hint-perpendicular."""
    r1 = r0 if r1 is None else r1
    ry0 = r0 if ry0 is None else ry0
    ry1 = r1 if ry1 is None else ry1
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0).normalized()
    hint = Vector(x_hint)
    if abs(ax.dot(hint)) > 0.95:
        hint = Vector((1, 0, 0)) if abs(ax.x) < 0.9 else Vector((0, 1, 0))
    u = (hint - ax * ax.dot(hint)).normalized()
    v = ax.cross(u)
    bm = bmesh.new()
    loops = []
    n = rings + 1
    for k in range(n):
        f = k / rings
        c = p0.lerp(p1, f)
        ra, rb = r0 + (r1 - r0) * f, ry0 + (ry1 - ry0) * f
        loops.append([bm.verts.new(c + u * (ra * math.cos(a)) + v * (rb * math.sin(a)))
                      for a in (2 * math.pi * i / seg for i in range(seg))])
    for k in range(rings):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((loops[k][i], loops[k][j], loops[k + 1][j], loops[k + 1][i]))
    if caps:
        bm.faces.new(list(reversed(loops[0])))
        bm.faces.new(loops[-1])
    return bm


def box(center, size, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Diagonal(Vector(size)).to_4x4()
    if rot:
        m = rot.to_4x4() @ m
    m = Matrix.Translation(Vector(center)) @ m
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return bm


def ellipsoid(center, radii, seg=24, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(center)) @ Matrix.Diagonal(Vector(radii)).to_4x4(),
                        verts=bm.verts)
    return bm


def torus_y(center, R, r, seg=48, sides=12):
    """Torus around the local Y axis."""
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(sides):
            b = 2 * math.pi * j / sides
            rr = R + r * math.cos(b)
            ring.append(bm.verts.new((center[0] + rr * math.cos(a), center[1] + r * math.sin(b),
                                      center[2] + rr * math.sin(a))))
        rings.append(ring)
    for i in range(seg):
        for j in range(sides):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % sides],
                          rings[i][(j + 1) % sides]))
    return bm


def merge(*bms):
    out = bmesh.new()
    for b in bms:
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


# ---------------------------------------------------------------- materials
RED = mat("honda_red", "#C8102E", 0.35)
WHITE_PL = mat("plastic_white", "#EDEDED", 0.4)
ALU = mat("aluminium", "#B8BCC2", 0.3, 1.0)
DARK = mat("engine_dark", "#3A3C40", 0.5, 0.6)
BLACK = mat("rubber", "#151515", 0.85)
RIM = mat("rim_black", "#202020", 0.35, 0.8)
GOLD = mat("fork_gold", "#C9A24A", 0.25, 1.0)
STEEL = mat("exhaust_steel", "#9EA3A8", 0.3, 1.0)
MARK = mat("spin_marker", "#F2C200", 0.5)
JERSEY = mat("jersey", "#1F3B63", 0.8)
PANTS = mat("pants", "#3B3F45", 0.8)
BOOT = mat("boots", "#E6E6E6", 0.5)
HELMET = mat("helmet", "#F4F4F4", 0.25)
VISOR = mat("goggles", "#111111", 0.2)
GLOVE = mat("gloves", "#202020", 0.7)
DIRT = mat("dirt", "#B08A5E", 0.95)
DIRT_DARK = mat("dirt_track", "#8E6B47", 0.95)
RAMP_STEEL = mat("ramp_steel", "#6E5A4A", 0.7, 0.6)
RAMP_FRAME = mat("ramp_frame", "#2A2A2A", 0.6, 0.8)
MARKER = mat("distance_marker", "#FFFFFF", 0.6)

# ---------------------------------------------------------------- bike (bike frame, metres)
G = SC["bike"]
fa = G["fork_axis"]          # (u, w) unit, up the fork
ax_f = G["front_axle"]       # (u, w) full extension


def F(d):                    # point on the fork axis, d metres above the front axle (u, w)
    return (ax_f[0] + fa[0] * d, ax_f[1] + fa[1] * d)


frame_parts = []
# engine and head
frame_parts.append(box((0.78, 0, 0.50), (0.36, 0.27, 0.34)))
frame_parts.append(box((0.88, 0, 0.74), (0.20, 0.22, 0.24), Matrix.Rotation(math.radians(-15), 3, "Y")))
# twin spar frame
for s in (1, -1):
    frame_parts.append(tube((1.08, 0.11 * s, 0.96), (0.72, 0.13 * s, 0.84), 0.035, ry0=0.02, x_hint=(0, 0, 1)))
    frame_parts.append(tube((0.72, 0.13 * s, 0.84), (0.57, 0.12 * s, 0.47), 0.04, ry0=0.02, x_hint=(1, 0, 0)))
    frame_parts.append(tube((0.92, 0.06 * s, 0.70), (0.86, 0.06 * s, 0.33), 0.018))
    frame_parts.append(tube((0.86, 0.06 * s, 0.33), (0.57, 0.08 * s, 0.40), 0.018))
    # subframe
    frame_parts.append(tube((0.62, 0.11 * s, 0.86), (-0.12, 0.10 * s, 0.93), 0.014))
    frame_parts.append(tube((0.56, 0.10 * s, 0.55), (-0.05, 0.10 * s, 0.88), 0.012))
    # footpegs
    frame_parts.append(box((G["peg"][0], 0.205 * s, G["peg"][1] - 0.012), (0.06, 0.10, 0.025)))
# steering head and clamps
frame_parts.append(tube((F(0.80)[0], 0.0, F(0.80)[1]), (F(0.97)[0], 0.0, F(0.97)[1]), 0.03))
ALU_PARTS = merge(*frame_parts)

bike = {}
root_frame = new_obj("bike_frame", ALU_PARTS, ALU)
bike["frame"] = root_frame


def child(name, bm, material):
    ob = new_obj(name, bm, material, root_frame)
    return ob


def uw(p, y=0.0):
    return (p[0], y, p[1])


child("bike_engine", merge(box((0.78, 0, 0.50), (0.37, 0.25, 0.35)),
                           box((0.70, 0, 0.30), (0.30, 0.22, 0.10))), DARK)
child("bike_tank_shrouds", merge(box((0.86, 0, 0.93), (0.42, 0.40, 0.18), Matrix.Rotation(math.radians(8), 3, "Y")),
                                 box((1.00, 0, 0.84), (0.20, 0.46, 0.26), Matrix.Rotation(math.radians(20), 3, "Y"))), RED)
child("bike_seat", box((0.42, 0, 0.96), (0.80, 0.24, 0.07), Matrix.Rotation(math.radians(3), 3, "Y")), RED)
child("bike_sidepanels_fender", merge(box((0.18, 0, 0.86), (0.56, 0.30, 0.14), Matrix.Rotation(math.radians(-6), 3, "Y")),
                                      box((-0.18, 0, 0.98), (0.45, 0.22, 0.03), Matrix.Rotation(math.radians(-10), 3, "Y"))), RED)
child("bike_front_fender", box((1.50, 0, 0.93), (0.48, 0.17, 0.03), Matrix.Rotation(math.radians(14), 3, "Y")), RED)
plate_c = F(0.95)
child("bike_number_plate", box((plate_c[0] + 0.07, 0, plate_c[1] - 0.06), (0.02, 0.26, 0.26),
                               Matrix.Rotation(math.radians(G["rake_deg"]), 3, "Y")), WHITE_PL)
child("bike_muffler", tube((0.29, -0.15, 0.72), (-0.08, -0.15, 0.89), 0.058, x_hint=(0, 1, 0)), STEEL)
child("bike_header", merge(tube((0.96, -0.02, 0.66), (0.98, -0.08, 0.45), 0.022),
                           tube((0.98, -0.08, 0.45), (0.60, -0.14, 0.60), 0.022),
                           tube((0.60, -0.14, 0.60), (0.30, -0.15, 0.72), 0.03)), STEEL)
uppers = []
for s in (1, -1):
    a, b = F(0.45), F(0.97)
    uppers.append(tube((a[0], 0.095 * s, a[1]), (b[0], 0.095 * s, b[1]), 0.0245))
child("bike_fork_uppers", merge(*uppers), GOLD)
clamps = merge(box((F(0.82)[0], 0, F(0.82)[1]), (0.07, 0.26, 0.035), Matrix.Rotation(math.radians(G["rake_deg"]), 3, "Y")),
               box((F(0.96)[0], 0, F(0.96)[1]), (0.07, 0.26, 0.035), Matrix.Rotation(math.radians(G["rake_deg"]), 3, "Y")))
child("bike_clamps", clamps, ALU)
grip = G["grip"]
gh = G["grip_half"]
bar = merge(tube((grip[0], gh + 0.06, grip[1]), (grip[0] + 0.03, 0.15, grip[1] - 0.01), 0.011),
            tube((grip[0] + 0.03, 0.15, grip[1] - 0.01), (grip[0] + 0.05, -0.15, grip[1] - 0.01), 0.011),
            tube((grip[0] + 0.05, -0.15, grip[1] - 0.01), (grip[0], -gh - 0.06, grip[1]), 0.011),
            tube((grip[0] + 0.05, 0.0, grip[1] - 0.02), (F(0.97)[0], 0.0, F(0.97)[1]), 0.015))
child("bike_bars", bar, ALU)
child("bike_grips", merge(tube((grip[0], gh - 0.065, grip[1]), (grip[0], gh + 0.065, grip[1]), 0.017),
                          tube((grip[0], -gh - 0.065, grip[1]), (grip[0], -gh + 0.065, grip[1]), 0.017)), BLACK)

# fork lowers + front wheel (animated)
lowers = []
for s in (1, -1):
    a, b = F(0.0), F(0.47)
    lowers.append(tube((a[0], 0.095 * s, a[1]), (b[0], 0.095 * s, b[1]), 0.031))
fork_lower = new_obj("bike_fork_lower", merge(*lowers), RED)
bike["fork_lower"] = fork_lower


def wheel(name, R, section, disc_side, disc_r):
    parts = [torus_y((0, 0, 0), R - section / 2, section / 2)]
    rim = [torus_y((0, 0, 0), R - section - 0.005, 0.012, sides=8)]
    hub = [tube((0, -0.07, 0), (0, 0.07, 0), 0.04, x_hint=(1, 0, 0))]
    spokes = []
    for i in range(6):
        a = 2 * math.pi * i / 6
        spokes.append(tube((0.04 * math.cos(a), 0, 0.04 * math.sin(a)),
                           ((R - section - 0.01) * math.cos(a), 0, (R - section - 0.01) * math.sin(a)), 0.006, seg=6))
    disc = [tube((0, disc_side * 0.075, 0), (0, disc_side * 0.08, 0), disc_r, x_hint=(1, 0, 0), seg=32)]
    tyre = new_obj(name, merge(*parts), BLACK)
    new_obj(name + "_rim", merge(*rim, *hub), RIM, tyre)
    new_obj(name + "_spokes", merge(*spokes), MARK, tyre)
    new_obj(name + "_disc", merge(*disc), STEEL, tyre)
    return tyre


bike["front_wheel"] = wheel("bike_front_wheel", G["r_front"], 0.085, 1, 0.13)
bike["rear_wheel"] = wheel("bike_rear_wheel", G["r_rear"], 0.10, -1, 0.12)
piv = G["pivot"]
ra = G["rear_axle"]
arms = []
for s in (1, -1):
    arms.append(tube((0.0, 0.12 * s, 0.0), (ra[0] - piv[0], 0.12 * s, ra[1] - piv[1]), 0.03, ry0=0.016, x_hint=(0, 0, 1)))
bike["swingarm"] = new_obj("bike_swingarm", merge(*arms), ALU)

# ---------------------------------------------------------------- rider (segment meshes)
R = SC["rider"]
lm = R["landmarks"]
pel = Vector(lm["pelvis"])
rider = {}
rider["pelvis"] = new_obj("rider_pelvis", ellipsoid((0, 0, 0.0), (0.13, 0.19, 0.12)), PANTS)
sh_rel = Vector(lm["shoulder_mid"]) - pel
rider["torso"] = new_obj("rider_torso", merge(
    tube((0, 0, 0.05), tuple(sh_rel * 0.98), 0.115, 0.14, ry0=0.17, ry1=0.21, x_hint=(1, 0, 0), rings=4),
    ellipsoid(tuple(sh_rel * 0.92), (0.13, 0.23, 0.10))), JERSEY)
helmet = merge(ellipsoid((0, 0, 0.01), (0.155, 0.135, 0.145)),
               box((0.13, 0, -0.07), (0.10, 0.16, 0.08)),           # chin bar
               box((0.12, 0, 0.13), (0.18, 0.20, 0.02), Matrix.Rotation(math.radians(-12), 3, "Y")))  # peak
rider["head"] = new_obj("rider_helmet", helmet, HELMET)
new_obj("rider_goggles", box((0.14, 0, 0.035), (0.04, 0.17, 0.05)), VISOR, rider["head"])
for s in ("l", "r"):
    L = R["lengths"]
    rider[f"thigh_{s}"] = new_obj(f"rider_thigh_{s}", tube((0, 0, 0), (0, 0, L["thigh"]), 0.085, 0.062), PANTS)
    rider[f"shank_{s}"] = new_obj(f"rider_shank_{s}", merge(
        tube((0, 0, 0), (0, 0, 0.12), 0.062, 0.066), tube((0, 0, 0.12), (0, 0, L["shank"]), 0.066, 0.055)), BOOT)
    rider[f"foot_{s}"] = new_obj(f"rider_boot_{s}", box((0.0, 0, 0.07), (0.10, 0.11, 0.30)), BOOT)
    rider[f"upper_arm_{s}"] = new_obj(f"rider_upper_arm_{s}", tube((0, 0, 0), (0, 0, L["upper_arm"]), 0.055, 0.045), JERSEY)
    rider[f"forearm_{s}"] = new_obj(f"rider_forearm_{s}", tube((0, 0, 0), (0, 0, L["forearm"] - 0.05), 0.045, 0.035), JERSEY)
    rider[f"hand_{s}"] = new_obj(f"rider_glove_{s}", ellipsoid((0, 0, 0), (0.05, 0.06, 0.045)), GLOVE)

# ---------------------------------------------------------------- terrain
T = SC["terrain"]
xs, zs = T["xs"], T["zs"]
k = T["keys"]


def ramp_mesh():
    W = SC["ramp_width"] / 2
    pts = [(x, z) for x, z in zip(xs, zs) if k["ramp_bottom"] - 0.01 <= x <= 0.0]
    bm = bmesh.new()
    top_l = [bm.verts.new((x, W, z)) for x, z in pts]
    top_r = [bm.verts.new((x, -W, z)) for x, z in pts]
    thick = 0.02
    for i in range(len(pts) - 1):
        bm.faces.new((top_l[i], top_r[i], top_r[i + 1], top_l[i + 1]))
    side = []
    for sgn in (1, -1):
        vs_top = [bm.verts.new((x, sgn * (W + 0.01), z + 0.04)) for x, z in pts]
        vs_bot = [bm.verts.new((x, sgn * (W + 0.01), max(z - 0.25, 0.0))) for x, z in pts]
        for i in range(len(pts) - 1):
            bm.faces.new((vs_top[i], vs_top[i + 1], vs_bot[i + 1], vs_bot[i]))
    deck = new_obj("ramp_deck", bm, RAMP_STEEL)
    # support frame: posts and braces under the deck every 1 m
    parts = []
    xm = k["ramp_bottom"]
    x = xm + 1.0
    while x <= 0.0:
        z = float(next(zz for xx, zz in zip(xs, zs) if xx >= x))
        for sgn in (1, -1):
            parts.append(tube((x, sgn * (W - 0.05), 0.0), (x, sgn * (W - 0.05), z - 0.02), 0.04, seg=8))
        parts.append(tube((x, W - 0.05, z * 0.5), (x, -W + 0.05, z * 0.5), 0.03, seg=8))
        x += 1.0
    for sgn in (1, -1):
        parts.append(tube((0.0, sgn * (W - 0.05), 0.0), (0.0, sgn * (W - 0.05), k["lip_height"] - 0.02), 0.05, seg=8))
        parts.append(tube((xm + 1.0, sgn * (W - 0.05), 0.05), (0.0, sgn * (W - 0.05), 0.05), 0.04, seg=8))
    new_obj("ramp_frame", merge(*parts), RAMP_FRAME)
    return deck


ramp_mesh()


def landing_mesh():
    Wt = SC["landing_width"] / 2
    side = math.tan(math.radians(40))
    x0, x1 = k["landing_back_foot"] - 0.5, k["landing_bottom"] + 1.0
    nx = int((x1 - x0) / 0.1) + 1
    ys = [i * 0.1 for i in range(-int((Wt + 8) / 0.1), int((Wt + 8) / 0.1) + 1)]
    bm = bmesh.new()
    verts = []
    for i in range(nx):
        x = x0 + i * 0.1
        j = bisect.bisect_left(xs, x)
        j = min(max(j, 1), len(xs) - 1)
        f = (x - xs[j - 1]) / (xs[j] - xs[j - 1])
        zc = zs[j - 1] * (1 - f) + zs[j] * f
        row = []
        for y in ys:
            h = zc - max(abs(y) - Wt, 0.0) * side
            row.append(bm.verts.new((x, y, max(h, 0.0) + 0.002)))
        verts.append(row)
    for i in range(nx - 1):
        for j in range(len(ys) - 1):
            bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1]))
    return new_obj("landing_mound", bm, DIRT)


landing_mesh()
gb = bmesh.new()
bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=1.0)
bmesh.ops.transform(gb, matrix=Matrix.Translation((0, 0, 0)) @ Matrix.Diagonal((150, 90, 1)).to_4x4(), verts=gb.verts)
new_obj("ground", gb, DIRT)
tr = bmesh.new()
bmesh.ops.create_grid(tr, x_segments=1, y_segments=1, size=1.0)
bmesh.ops.transform(tr, matrix=Matrix.Translation(((k["ramp_bottom"] - 60) / 2 - 0.5, 0, 0.003))
                    @ Matrix.Diagonal(((60 + abs(k["ramp_bottom"])) / 2, 1.8, 1)).to_4x4(), verts=tr.verts)
new_obj("run_in_track", tr, DIRT_DARK)
ro = bmesh.new()
bmesh.ops.create_grid(ro, x_segments=1, y_segments=1, size=1.0)
bmesh.ops.transform(ro, matrix=Matrix.Translation((k["landing_bottom"] + 30, 0, 0.003))
                    @ Matrix.Diagonal((30, 2.2, 1)).to_4x4(), verts=ro.verts)
new_obj("run_out_track", ro, DIRT_DARK)
# distance markers every 5 m from the lip on the camera side (+Y), and cones along the run-in
marks = []
for d in range(-60, 61, 5):
    xm = float(d)
    marks.append(box((xm, 12.0, 0.5), (0.12, 0.12, 1.0)))
    if d % 10 == 0:
        marks.append(box((xm, 12.0, 1.05), (0.5, 0.05, 0.12)))
new_obj("distance_markers", merge(*marks), MARKER)
for d in range(-25, 31, 5):
    if d < 0 and d > k["ramp_bottom"]:
        continue
    cu = bpy.data.curves.new(f"lbl{d}", "FONT")
    cu.body = f"{d} m" if d else "LIP"
    cu.size = 0.6
    cu.align_x = "CENTER"
    ob = bpy.data.objects.new(f"label_{d}", cu)
    ob.location = (d, 12.0, 1.35)
    ob.rotation_euler = (math.radians(90), 0, math.radians(180))
    ob.data.materials.append(MARKER)
    bpy.context.scene.collection.objects.link(ob)

# ---------------------------------------------------------------- animation
objs = {**{f"bike:{k2}": v for k2, v in bike.items()}, **{f"rider:{k2}": v for k2, v in rider.items()}}
names = FR["objects"]
frames = FR["frames"]
nf = len(frames)
for idx, key in enumerate(names):
    ob = objs[key]
    ob.rotation_mode = "QUATERNION"
    act = bpy.data.actions.new(f"act_{ob.name}")
    slot = act.slots.new(id_type="OBJECT", name=ob.name)
    ob.animation_data_create()
    ob.animation_data.action = act
    ob.animation_data.action_slot = slot
    cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
    chans = [("location", i) for i in range(3)] + [("rotation_quaternion", i) for i in range(4)]
    for c, (path, i) in enumerate(chans):
        fc = cb.fcurves.new(path, index=i, group_name="Object Transforms")
        fc.keyframe_points.add(nf)
        co = []
        for fr in frames:
            co += [fr["f"], fr["tf"][idx][c]]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items["LINEAR"].value] * nf)
        fc.update()

# ---------------------------------------------------------------- cameras
scn = bpy.context.scene
scn.render.fps = 120
scn.frame_start = 1
scn.frame_end = int(frames[-1]["f"])
for cam in SC["cameras"]:
    cd = bpy.data.cameras.new(cam["name"])
    cd.lens = cam["lens"]
    cd.sensor_width = 36.0
    cd.clip_end = 400
    co = bpy.data.objects.new(cam["name"], cd)
    scn.collection.objects.link(co)
    co.rotation_mode = "QUATERNION"
    if "path" in cam:
        act = bpy.data.actions.new(f"act_{cam['name']}")
        slot = act.slots.new(id_type="OBJECT", name=cam["name"])
        co.animation_data_create()
        co.animation_data.action = act
        co.animation_data.action_slot = slot
        cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
        n = len(cam["path"])
        for c in range(7):
            path, i = ("location", c) if c < 3 else ("rotation_quaternion", c - 3)
            fc = cb.fcurves.new(path, index=i)
            fc.keyframe_points.add(n)
            co_list = []
            for p in cam["path"]:
                co_list += [p[0], p[1 + c]]
            fc.keyframe_points.foreach_set("co", co_list)
            fc.keyframe_points.foreach_set("interpolation", [bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items["LINEAR"].value] * n)
            fc.update()

# ---------------------------------------------------------------- render setup (Workbench)
scn.render.engine = "BLENDER_WORKBENCH"
sh = scn.display.shading
sh.light = "STUDIO"
sh.studio_light = "outdoor.sl"
sh.use_world_space_lighting = True
sh.studiolight_rotate_z = 0.6
sh.color_type = "MATERIAL"
sh.show_shadows = True
sh.shadow_intensity = 0.55
sh.show_cavity = True
sh.cavity_type = "BOTH"
sh.show_specular_highlight = True
scn.display.light_direction = (-0.45, 0.35, 0.82)
scn.display.shadow_shift = 0.02
scn.display.render_aa = "8"
scn.world = bpy.data.worlds.new("sky") if scn.world is None else scn.world
scn.world.color = srgb("#9CC3E6")[:3]
scn.view_settings.view_transform = "Standard"
scn.render.image_settings.file_format = "PNG"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD OK", OUT, "frames", nf, "objects", len(names))
