"""Assemble Damien's bike in Blender from the generated parts (parts.py) and the livery (livery.py), then render
previews and export glTF.

blender -b --factory-startup --python-exit-code 1 --python build_bike.py -- PARTS.npz TEXTURES_DIR OUT_DIR [views]
        [stock|livery] [NAME]
  views: comma list of camera names ('all' for every one, 'none' to skip rendering); stock = plain Honda colours
  cameras: honda_left, honda_right, honda_front, honda_rear, honda_top (Honda's studio cameras, cams.py),
           honda_lf34, honda_lr34, honda_rf34, honda_rr34 (three-quarter photos, fit34.py),
           profile_left, left_34_hero, right_rear_34, dv01_front_left, dv02_left_front, dv04_cockpit
Writes OUT_DIR/NAME.blend, OUT_DIR/NAME.glb and OUT_DIR/render_<view>.png.
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
STOCK = len(argv) > 4 and argv[4] == "stock"        # plain stock Honda colours (shape work), no livery
NAME = argv[5] if len(argv) > 5 else "bike_v0"
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
BP = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))["left"]
MAPS = json.load(open(os.path.join(TEX, "maps.json")))
_npz = np.load(PARTS)
META = json.loads(str(_npz["meta"])) if "meta" in _npz.files else {}       # from parts.py and its plugins
_up = _npz["steer_axis"][1]
RAKE = math.atan2(-float(_up[0]), float(_up[2]))       # fork axis in the axle-line frame (parts.py, from the photo)
STUDIO_CAMS = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-cameras.json")))   # cams.py
_C34 = os.path.join(HERE, "..", "..", "research", "bike-cameras-34.json")         # fit34.py: three-quarter photos
if os.path.exists(_C34):
    STUDIO_CAMS.update({k: v for k, v in json.load(open(_C34)).items()})


def srgb(c):
    """One sRGB channel in 0..1 -> linear."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb):
    """An sRGB colour, 0..255 if any channel is over 1, else 0..1 -> linear RGBA. Decided for the whole colour, not per
    channel: per channel, (5, 32, 1) read its 1 as full blue (2026-11-11)."""
    k = 255.0 if max(rgb) > 1 else 1.0
    return tuple(srgb(v / k) for v in rgb) + (1.0,)


# ---------------------------------------------------------------- materials
def _tex_path(image):
    """A texture: absolute, in this livery's folder (TEX), or under motocross-whip/textures (e.g. "stock/grip_n.png")."""
    for p in (image, os.path.join(TEX, image), os.path.join(HERE, "..", "..", "textures", image)):
        if os.path.isabs(p) and os.path.exists(p) or os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(image)


def principled(name, rgb=None, metal=0.0, rough=0.5, image=None, coat=0.0, aniso=0.0, bump=0.0, spec=0.5,
               normal=None, normal_strength=1.0, sheen=0.0):
    """normal: a tangent-space normal map (OpenGL convention, +Y up) laid on the part's UVs (Mesh.uv, or uv_for);
    it is exported to glTF too, so the viewer shows grip patterns, seat covers and tyre lettering."""
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
        tex.image = bpy.data.images.load(_tex_path(image))
        tex.interpolation = "Cubic"
        nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    if sheen > 0:
        p.inputs["Sheen Weight"].default_value = sheen
    if normal:
        nt_img = nt.nodes.new("ShaderNodeTexImage")
        nt_img.image = bpy.data.images.load(_tex_path(normal))
        nt_img.image.colorspace_settings.name = "Non-Color"
        nt_img.interpolation = "Cubic"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(nt_img.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    if bump > 0 and not normal:
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


RED = (208, 10, 22)             # photo mean of the lit plastics is (240, 50, 60): tuned in the studio views
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

MATS.update({"header_steel": dict(rgb=(176, 168, 152), metal=1.0, rough=0.3),
             "cable": dict(rgb=(16, 16, 17), rough=0.5),
             "plastic_red": dict(rgb=RED, rough=0.34, coat=0.08)})
if STOCK:
    for k in ("livery_L", "livery_R", "livery_fender", "fender_front", "plate"):
        MATS[k] = dict(rgb=RED, rough=0.34, coat=0.08)
    MATS["seat"] = dict(rgb=(176, 18, 26), rough=0.8, bump=0.35)
    MATS["swing_L"] = MATS["swing_R"] = dict(rgb=(200, 200, 204), metal=1.0, rough=0.32, aniso=0.6)
# single surfaces: solidify (the number plate, panels and mudguard are built with their thickness)
# studio look for the honda_* cameras: world strength, lamp scale, exposure (BIKE_STUDIO="w,l,e" to test others)
STUDIO = tuple(float(v) for v in os.environ.get("BIKE_STUDIO", "0.7,0.5,-0.9").split(","))
THIN = {"front_fender", "rear_fender", "fork_guards", "fender_flap", "shroud_decks", "mud_flap"}
BEVEL = {"engine": 0.006, "frame": 0.003, "swingarm": 0.003, "clamps": 0.003}           # rounded machined edges
SMOOTH_ANGLE = {"shrouds": 70, "side_panels": 70, "seat": 70, "front_fender": 70, "rear_fender": 70,
                "number_plate": 70, "fork_guards": 70, "tank": 60, "fender_flap": 70, "shroud_decks": 70,
                "rear_inner": 60, "fender_mounts": 50, "mud_flap": 70}
FRONT_END = {"fork", "fork_guards", "clamps", "bars", "number_plate", "front_fender", "front_wheel", "fender_flap",
             "disc_guard"}


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
    if mat == "livery_top":                                         # from above, front at the image's top,
        s = MAPS["top"]                                             # the bike's right at its right
        return (s["y1"] - y) / (s["y1"] - s["y0"]), (x - s["x0"]) / (s["x1"] - s["x0"])
    key = {"livery_fender": "fender", "fender_front": "front_fender", "seat": "seat"}.get(mat)
    if key:
        s = MAPS[key]
        return (s["x1"] - x) / (s["x1"] - s["x0"]), (y - s["y0"]) / (s["y1"] - s["y0"])
    if mat == "plate":
        s = MAPS["plate"]
        along = (z - 0.94) / math.cos(RAKE)
        return (y - s["u0"]) / (s["u1"] - s["u0"]), (along - s["s0"]) / (s["s1"] - s["s0"])
    if mat == "barpad":
        # barpad.png in three bands (livery.barpad): lettering (front and rear faces, each read from its own side),
        # the pad's top, and its grey end caps. The pad's own axes: f forward, h up, leaning back by "tilt"
        q = META.get("uv", {}).get("barpad", dict(centre=[0.99, 1.18], half=[0.028, 0.030], y_half=0.105))
        (xc, zc), (hf, hh), yh, t = q["centre"], q["half"], q["y_half"], q.get("tilt", 0.0)
        ct, st = math.cos(t), math.sin(t)
        f, h = (x - xc) * ct + (z - zc) * st, -(x - xc) * st + (z - zc) * ct
        nf, nh = nrm[0] * ct + nrm[2] * st, -nrm[0] * st + nrm[2] * ct
        unit = lambda v: min(max(v, 0.02), 0.98)
        if abs(nrm[1]) > max(abs(nf), abs(nh)):                    # end cap
            return unit((f * (1 if nrm[1] > 0 else -1) + hf) / (2 * hf) * (2 * hf / (2 * yh))), (2 + unit((h + hh) / (2 * hh))) / 3
        if abs(nf) > abs(nh):                                      # front or rear face
            u = (y + yh) / (2 * yh) if nf > 0 else (yh - y) / (2 * yh)
            return u, unit((h + hh) / (2 * hh)) / 3
        return (yh - y) / (2 * yh), (1 + unit((f + hf) / (2 * hf))) / 3
    return 0.5, 0.5


MATS["bolt"] = dict(rgb=(158, 160, 166), metal=1.0, rough=0.38)
for _k, _v in META.get("materials", {}).items():
    MATS[_k] = {k: (tuple(v) if k == "rgb" else v) for k, v in _v.items()}
THIN |= set(META.get("thin", ()))
BEVEL.update(META.get("bevel", {}))
SMOOTH_ANGLE.update(META.get("smooth", {}))
if "front_end" in META:
    FRONT_END = set(META["front_end"])                 # one list for the whole pipeline: parts.py's


# Damien's sticker kit (2026-11-12): the plastics are built in plain `plastic_red`; with a livery their red faces take
# the kit's projections instead, by which way each face looks: sides (livery_L / livery_R, painted in the bike's side
# view), tops (livery_fender, fender_front, seen from above) and the plate's face (plate)
KIT_PARTS = {"shrouds", "side_panels", "shroud_decks", "rear_fender", "front_fender", "number_plate", "fork_guards",
             "swingarm"}
KIT_MATS = {"livery_L", "livery_R", "livery_fender", "fender_front", "plate"}
if not STOCK:
    MATS["intake_foam"] = dict(rgb=(12, 12, 13), rough=0.8)     # Damien's intake shows black, not Honda's green
    # his right grip (photos 10, 03): light grey diamond rubber, red flange and red ring at the bar end; left stays black
    MATS["grip_r"] = MATS["grip_r_bead"] = dict(rgb=(176, 178, 180), rough=0.6, bump=0.12)
    MATS["grip_r_end"] = MATS["grip_r_flange"] = dict(rgb=(196, 22, 28), rough=0.5)
    # his Renthal pad is red all over (photos 04, 10): no grey end caps
    MATS["pad_cap"] = dict(rgb=(214, 29, 46), rough=0.7)
if not STOCK and "top" in MAPS and os.path.exists(os.path.join(TEX, "top.png")):
    # the tank sticker (black, red splatter, 114 behind the cap) and the shroud decks, painted from above as the
    # rider sees them (top.png, MAPS["top"]): the tank's top and the decks' tops take it (kit_materials)
    MATS["livery_top"] = dict(image="top.png", rough=0.34, coat=0.08)
    KIT_MATS.add("livery_top")
    KIT_PARTS.add("tank")
if not STOCK and "seat" in MAPS and os.path.exists(os.path.join(TEX, "seat.png")):
    # Damien's GUTS seat cover, painted from above (seat.png, MAPS["seat"]): it replaces the stock cover's grain map
    MATS["seat"] = dict(image="seat.png", rough=0.7, sheen=0.4)
    KIT_MATS.add("seat")


BANDS = json.load(open(os.path.join(TEX, "bands.json"))) if os.path.exists(os.path.join(TEX, "bands.json")) else {}


_BAND_X = {}


def in_band(part, side, x, z, tol=0.0015):
    """Is (x, z) under the part's wrap sticker on that side (KIT_DIR/bands.json from kit_canvas.py)?"""
    b = BANDS.get(part, {}).get(side)
    if not b:
        return False
    xs = _BAND_X.setdefault((part, side), np.array([r[0] for r in b]))
    i = int(np.argmin(abs(xs - x)))
    return abs(xs[i] - x) <= 0.004 and b[i][1] - tol <= z <= b[i][2] + tol


def kit_materials(name, V, faces, M, mats):
    M = np.array(M, copy=True)
    red = mats.index("plastic_red") if "plastic_red" in mats else -1
    # Damien's kit also covers the side panel's lower black cover (the red band with his name and the bolt), his fork
    # guards (black, PIRELLI, MOTUL) and the swingarm's outer faces (his black wrap with PSALM 91)
    extra = {"side_panels": ("plastic_black", "black_texture"), "fork_guards": ("fork_guard",),
             "swingarm": ("alu_satin", "swing_L", "swing_R", "alu_cast", "alu_weld"), "tank": ("tank_ti",)}.get(name, ())
    black = {mats.index(k) for k in extra if k in mats}
    for k in ("livery_L", "livery_R", "livery_fender", "fender_front", "plate"):
        if k not in mats:
            mats.append(k)
    iL, iR, iF, iFF, iP = (mats.index(k) for k in ("livery_L", "livery_R", "livery_fender", "fender_front", "plate"))
    iT = -1
    if "livery_top" in MATS:
        if "livery_top" not in mats:
            mats.append("livery_top")
        iT = mats.index("livery_top")
    for fi, f in enumerate(faces):
        if fi >= len(M) or (M[fi] != red and M[fi] not in black) or len(f) < 3:
            continue
        p = V[list(f)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        ln = np.linalg.norm(n)
        if ln == 0:
            continue
        nx, ny, nz = n / ln
        # the side by where the face is, not by its normal: the plastics' shells are not all wound outward (the left
        # side panel's outer face looks inward), so a normal test put it on the right side's texture
        side = iL if p[:, 1].mean() >= 0 else iR
        if name == "front_fender":
            M[fi] = iFF if abs(nz) > max(abs(ny), 0.55) else side
        elif name == "rear_fender":
            M[fi] = iF if abs(nz) > max(abs(ny), 0.55) else side
        elif name == "number_plate":
            M[fi] = iP if abs(nx) > 0.45 else side
        elif name == "tank":                                       # its top between the decks: the tank sticker
            if iT >= 0 and abs(nz) > 0.5 and p[:, 2].mean() > 0.97:
                M[fi] = iT
        elif name == "shroud_decks":
            M[fi] = iT if iT >= 0 and abs(nz) > 0.5 else side
        elif name == "swingarm":
            # the wrap covers the arm's sides where kit_canvas found the sticker (bands.json); round it the metal
            # keeps its own finish (the art's grey "aluminium" there is only the AI's picture of it)
            if abs(ny) > 0.3 and in_band("swingarm", "left" if side == iL else "right", p[:, 0].mean(), p[:, 2].mean()):
                M[fi] = side
        else:
            M[fi] = side
    return M


def build_parts():
    data = np.load(PARTS)
    mats = [str(m) for m in data["materials"]]
    bmats = {}
    for m in mats:
        bmats[m] = principled(m, **MATS.get(m, dict(rgb=(200, 0, 200))))
    col = bpy.data.collections.new(NAME)
    bpy.context.scene.collection.children.link(col)
    steer0, up = data["steer_axis"]
    rx, ry, rz, pitch, drop = data["ground"]
    # root: tilts the bike (built in the axle-line frame) nose-up about the rear axle and lifts it so both tyres touch
    # the ground
    root = bpy.data.objects.new("bike", None)
    Rm = Matrix.Rotation(-float(pitch), 4, "Y")
    ra = Vector((float(rx), float(ry), float(rz)))
    root.matrix_world = Matrix.Translation(ra + Vector((0.0, 0.0, float(drop)))) @ Rm @ Matrix.Translation(-ra)
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
        if not STOCK and name in KIT_PARTS:
            M = kit_materials(name, V, faces, M, mats)
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], faces)
        me.validate(clean_customdata=False)
        used = sorted(set(M.tolist()))
        for mi in used:
            if mats[mi] not in bmats:
                bmats[mats[mi]] = principled(mats[mi], **MATS.get(mats[mi], dict(rgb=(200, 0, 200))))
        for mi in used:
            me.materials.append(bmats[mats[mi]])
        remap = {mi: i for i, mi in enumerate(used)}
        me.polygons.foreach_set("material_index", [remap[int(v)] for v in M[:len(me.polygons)]])
        uvl = me.uv_layers.new(name="UVMap")
        UV = data[f"{name}__UV"] if f"{name}__UV" in data.files else None       # the part's own UVs (Mesh.uv)
        if UV is not None and len(UV) != len(me.loops):           # validate() dropped a bad face: corners no longer line up
            print("WARNING: %s: %d UV corners for %d loops (a degenerate face was removed): UVs ignored"
                  % (name, len(UV), len(me.loops)), flush=True)
            UV = None
        for poly in me.polygons:
            mname = mats[used[poly.material_index]]
            nrm = tuple(poly.normal)
            for li in poly.loop_indices:
                # a face that takes the kit uses the kit's projection, not the part's own UVs (rib or grain maps)
                if UV is not None and not np.isnan(UV[li, 0]) and mname not in KIT_MATS:
                    uvl.data[li].uv = (float(UV[li, 0]), float(UV[li, 1]))
                    continue
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
    # plain floor without the back wall, used instead of the cyclorama by cameras on the far (-y) side of it
    fm = bpy.data.meshes.new("floor")
    fm.from_pydata([(-12, -12, 0), (12, -12, 0), (12, 12, 0), (-12, 12, 0)], [], [(0, 1, 2, 3)])
    fm.materials.append(cm)
    floor = bpy.data.objects.new("floor", fm)
    sc.collection.objects.link(floor)
    floor.hide_render = True
    floor.is_shadow_catcher = True

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
        lo.visible_camera = False                           # the front and rear studio cameras look past the lights
        lo["base_energy"] = power

    area("key", (1.8, 3.2, 3.2), (0.75, 0, 0.6), 3.0, 420)
    area("fill", (0.2, -3.0, 2.2), (0.75, 0, 0.6), 3.5, 160)
    area("top", (0.75, 0.0, 4.0), (0.75, 0, 0.6), 4.0, 300)
    area("rim", (-2.5, 1.5, 2.0), (0.75, 0, 0.7), 2.0, 130)
    area("front", (4.0, 1.0, 1.4), (0.75, 0, 0.6), 2.5, 150)
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = int(os.environ.get("BIKE_SAMPLES", "64"))
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"              # closest to his bike's deep red (look test 2026-11-10)
    sc.view_settings.exposure = -0.6
    if os.environ.get("BIKE_VIEW"):                        # look tests: e.g. BIKE_VIEW="Standard,None,-0.3"
        vt, look, ex = os.environ["BIKE_VIEW"].split(",")
        sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure = vt, look, float(ex)


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


def studio_camera(view, root, res=(2000, 1125)):
    """Honda's studio photo camera for VIEW (cams.py, axle-line frame), parented to the bike's root so it follows the
    tilt onto the ground: the render lands on the photo pixel for pixel."""
    c = STUDIO_CAMS[view]
    cd = bpy.data.cameras.new(f"honda_{view}")
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cd.lens = c["f"] * 36.0 / 4000.0
    cd.clip_end = 60.0
    co = bpy.data.objects.new(f"honda_{view}", cd)
    R, U, F = Vector(c["R"]), Vector(c["U"]), Vector(c["F"])
    M = Matrix(((R.x, U.x, -F.x, c["C"][0]), (R.y, U.y, -F.y, c["C"][1]), (R.z, U.z, -F.z, c["C"][2]), (0, 0, 0, 1)))
    bpy.context.scene.collection.objects.link(co)
    co.parent = root
    co.matrix_world = root.matrix_world @ M
    co["res"] = list(res)
    return co


def cameras(root=None):
    cams = []
    if root is not None:
        cams += [studio_camera(v, root, res=tuple(int(q) for q in os.environ.get("BIKE_STUDIO_RES", "2000,1125").split(",")))
                 for v in ("left", "right", "front", "rear", "top", "lf34", "lr34", "rf34", "rr34") if v in STUDIO_CAMS]
    # Honda's left profile, reproduced: orthographic, same scale and framing as the 4000x2250 studio photo
    s = BP["mm_per_px"] / 1000.0
    fa, ra = np.array(BP["front_axle_px"]), np.array(BP["rear_axle_px"])
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]])
    if v[1] > 0:
        v = -v
    c_img = np.array([2000.0, 1125.0]) - ra
    cx, cz = c_img @ u * s, c_img @ v * s + BP["rear_tyre_od_mm"] / 2000.0       # axle-line frame
    pitch, drop = (float(q) for q in np.load(PARTS)["ground"][3:5])
    r0 = np.array([0.0, BP["rear_tyre_od_mm"] / 2000.0])
    c, sn = math.cos(pitch), math.sin(pitch)
    d = np.array([cx, cz]) - r0
    gx, gz = r0 + np.array([c * d[0] - sn * d[1], sn * d[0] + c * d[1] + drop])     # ground frame
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
    # inspection close-ups: BIKE_CLOSEUPS="name:x,y,z:tx,ty,tz:lens;..." (ground frame, metres)
    for spec in filter(None, os.environ.get("BIKE_CLOSEUPS", "").split(";")):
        nm, loc, tgt, lens = spec.split(":")
        cams.append(camera(nm, tuple(map(float, loc.split(","))), tuple(map(float, tgt.split(","))),
                           lens=float(lens), res=(1200, 800)))
    return cams


def render(cams):
    sc = bpy.context.scene
    for co in cams:
        if VIEWS and VIEWS != ["all"] and co.name not in VIEWS:
            continue
        sc.camera = co
        # Honda's studio cameras stand all round the bike: no cyclorama wall, a shadow-catching floor and a
        # transparent film instead (put the PNG on white to get the studio photo's look)
        honda = co.name.startswith("honda_")
        bpy.data.objects["cyc"].hide_render = honda
        bpy.data.objects["floor"].hide_render = not honda
        sc.render.film_transparent = honda
        # AgX turns the brightly lit red plastics salmon in the studio set-up: Standard keeps Honda's red there
        vs = sc.view_settings
        vs.view_transform, vs.look, vs.exposure = ("Standard", "None", STUDIO[2]) if honda else ("AgX", "AgX - Punchy", -0.6)
        # studio views: an even dome of light and weaker lamps (the lamps alone left a grey haze on the shadow
        # catcher and washed the red to salmon); values tuned against the red of Honda's photo (STUDIO)
        sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = STUDIO[0] if honda else 0.30
        for lo in bpy.data.objects:
            if lo.type == "LIGHT":
                lo.data.energy = lo["base_energy"] * (STUDIO[1] if honda else 1.0)
        sc.render.resolution_x, sc.render.resolution_y = co["res"]
        sc.render.resolution_percentage = 100
        # BIKE_BORDER="u0,v0,u1,v1": only that box of a honda_* view, in the 4000x2250 photo's pixels (pair.py)
        border = os.environ.get("BIKE_BORDER") if honda else None
        sc.render.use_border = sc.render.use_crop_to_border = bool(border)
        if border:
            u0, v0, u1, v1 = (float(q) for q in border.split(","))
            sc.render.border_min_x, sc.render.border_max_x = u0 / 4000.0, u1 / 4000.0
            sc.render.border_min_y, sc.render.border_max_y = 1.0 - v1 / 2250.0, 1.0 - v0 / 2250.0
        sc.render.filepath = os.path.join(OUT, f"render_{co.name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath, flush=True)


def export_glb(col):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name in col.all_objects)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_image_format="JPEG", export_jpeg_quality=88)


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    col, objs = build_parts()
    studio()
    cams = cameras(bpy.data.objects["bike"])
    # textures go inside the file: their paths are absolute on the build server, so a delivered .blend opened on
    # Damien's machine would lose them (2026-11-12)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{NAME}.blend"))
    export_glb(col)
    if VIEWS != ["none"]:
        render(cams)
    print("BUILD OK", len(objs), "parts")


main()
