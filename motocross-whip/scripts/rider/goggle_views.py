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

Round 7: GOGGLE_VIEWS_CAMS another camera file (same format), GOGGLE_VIEWS_FRAME_RGB "r,g,b" the frame's base colour
(sRGB) for another colourway (the white ISO held-out check: 236,236,232), GOGGLE_VIEWS_LENS_VLT a plain grey
see-through lens of that visible light transmission in place of his mirror (Leatt's Light Grey 58 %: 0.58), so the
nose comb behind it shows as in Leatt's photos. Each of the double lens's four faces is a thin surface: a Fresnel
(IOR 1.5) reflection over a grey see-through that lets the lights' rays pass, tinted so that the four faces together
pass the VLT at normal incidence (a Principled transmission tints and refracts at every face and stops the lights'
rays: a 150 grey tint left 0.3^4 of the light, and the comb did not show at all).

Round 8: light "daylight" (head_closeups.py's sun and sky, the sun aimed by the camera's "sun": [phi, theta]) for
his outdoor photos; a camera may carry "offset" (m, the point it looks round, default the origin) and "box" (photo
px: only that part is rendered, at GOGGLE_VIEWS_SCALE); the helmet's clear coat (coat_rough, spec) as build_rider.

Round 9: a camera may carry "lights": [[x, y, z, W], ...] for the three area lights (m, about the origin, aimed at
it; the MY27 back view: a key from his right and behind, a fill from his left, a dim top light, so the tail's rolls
shade as in Leatt's photo, where the front rig lit them flat). The strap's woven fabric (goggle_strap_art.py: the
print, its normal map, the weave tile and its mask) through the material's "detail". GOGGLE_VIEWS_STRAP_TEX another
print image (textures/rider name or path) for another colourway's strap (the MY27 back check),
GOGGLE_VIEWS_SLIDE_RGB "r,g,b" the slides' colour (sRGB), GOGGLE_VIEWS_DENOISE 0 to render without the denoiser
(the 1:1 fabric checks: it smooths the weave away at low samples).

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
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import day_rig  # noqa: E402  (decision 55: the daylight rig shared with head_closeups and the bike)
import scene_look  # noqa: E402  (decision 54: the daylight look shared with head_closeups and the bike)
TEXDIR = os.path.normpath(os.path.join(HERE, "..", "..", "textures", "rider"))
CAMS = os.environ.get("GOGGLE_VIEWS_CAMS") or os.path.normpath(os.path.join(HERE, "..", "..", "research",
                                                                  "goggle-cameras.json"))
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
FRAME_RGB = [int(v) for v in os.environ.get("GOGGLE_VIEWS_FRAME_RGB", "").split(",") if v]   # sRGB 0..255
LENS_VLT = float(os.environ.get("GOGGLE_VIEWS_LENS_VLT", "0") or 0)                          # 0..1, 0: his mirror
# round 9: the strap and slides in another colourway (the MY27 Blue/Red comparison): a print image (absolute path) and
# the slides' colour
STRAP_TEX = os.environ.get("GOGGLE_VIEWS_STRAP_TEX", "")
SLIDE_RGB = [int(v) for v in os.environ.get("GOGGLE_VIEWS_SLIDE_RGB", "").split(",") if v]
DENOISE = os.environ.get("GOGGLE_VIEWS_DENOISE", "1") != "0"     # round 9: 0 for 1:1 crops of the strap's weave
# round 10, decision 46 (the render look, as the bike's): Standard for the studio comparisons with Leatt's photos (plain
# AgX read pale in every sheet: the strap a third less saturated than both photos); in daylight the scene look's
# daylight kind (decision 54, was AgX - Punchy 0.6 EV under the photos' exposure). GOGGLE_VIEWS_LOOK=agx: rounds 4 to
# 9's plain AgX
LOOK = os.environ.get("GOGGLE_VIEWS_LOOK", "d46")
STUDIO_EV = float(os.environ.get("GOGGLE_VIEWS_STUDIO_EV", "0.0"))
# round 10, the weave's shimmer test (two frames of a whip-distance view): GOGGLE_VIEWS_SEED the sampling seed (the
# animation's seed changes every frame), GOGGLE_VIEWS_CAM_MM "dx,dy,dz" the camera moved along its own right, up and
# back axes (mm), GOGGLE_VIEWS_NO_DETAIL 1 the build without the weave tile, GOGGLE_VIEWS_WEAVE_TEX another tile
# (path), GOGGLE_VIEWS_BUMP its relief's bump strength, GOGGLE_VIEWS_MASK "mat,mat" a mask render (those materials
# white, the rest black, no lights)
SEED = int(os.environ.get("GOGGLE_VIEWS_SEED", "0"))
CAM_MM = [float(v) for v in os.environ.get("GOGGLE_VIEWS_CAM_MM", "0,0,0").split(",")]
NO_DETAIL = os.environ.get("GOGGLE_VIEWS_NO_DETAIL", "0") != "0"
WEAVE_TEX = os.environ.get("GOGGLE_VIEWS_WEAVE_TEX", "")
MASK = [m for m in os.environ.get("GOGGLE_VIEWS_MASK", "").split(",") if m]
os.makedirs(OUT, exist_ok=True)


def lin(c):
    c = np.asarray(c, float) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).tolist()) + (1.0,)


def material(name, spec):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    if MASK:                                       # round 10: a mask render (the shimmer test's strap pixels)
        nt.nodes.remove(p)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1, 1, 1, 1) if name in MASK else (0, 0, 0, 1)
        nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        return m
    if "thin_vlt" in spec:                        # round 7: one face of a see-through lens (LENS_VLT)
        nt.nodes.remove(p)
        # Fresnel from outside the plastic on both faces: the see-through does not bend the ray, so on a back face
        # the Fresnel node's own inside view (IOR 1/1.5) gave total internal reflection past 42 deg, and the lens
        # turned into a grey mirror where the camera looks through it obliquely
        fr, fb = nt.nodes.new("ShaderNodeFresnel"), nt.nodes.new("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value, fb.inputs["IOR"].default_value = 1.5, 1.0 / 1.5
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        d, w, a = (nt.nodes.new("ShaderNodeMath") for _ in range(3))
        d.operation, w.operation, a.operation = "SUBTRACT", "MULTIPLY", "ADD"
        nt.links.new(fb.outputs["Fac"], d.inputs[0])
        nt.links.new(fr.outputs["Fac"], d.inputs[1])
        nt.links.new(d.outputs[0], w.inputs[0])
        nt.links.new(geo.outputs["Backfacing"], w.inputs[1])
        nt.links.new(w.outputs[0], a.inputs[0])
        nt.links.new(fr.outputs["Fac"], a.inputs[1])
        see = nt.nodes.new("ShaderNodeBsdfTransparent")
        t = min(1.0, spec["thin_vlt"] ** 0.25 / (1.0 - 0.04))       # 4 % reflected per face at normal incidence
        see.inputs["Color"].default_value = (t, t, t, 1.0)
        gl = nt.nodes.new("ShaderNodeBsdfGlossy")
        gl.inputs["Roughness"].default_value = 0.02
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(a.outputs[0], mix.inputs[0])
        nt.links.new(see.outputs[0], mix.inputs[1])
        nt.links.new(gl.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        return m
    if "rgb" in spec:
        p.inputs["Base Color"].default_value = lin(spec["rgb"])
    p.inputs["Roughness"].default_value = spec.get("rough", 0.5)
    p.inputs["Metallic"].default_value = spec.get("metal", 0.0)
    p.inputs["Coat Weight"].default_value = spec.get("coat", 0.0)
    if "coat_rough" in spec:                       # round 8: as build_rider.gear_material (the helmet's clear coat)
        p.inputs["Coat Roughness"].default_value = spec["coat_rough"]
    if "spec" in spec:
        p.inputs["Specular IOR Level"].default_value = spec["spec"]
    p.inputs["Sheen Weight"].default_value = spec.get("sheen", 0.0)
    if "transmission" in spec:
        p.inputs["Transmission Weight"].default_value = spec["transmission"]
    if "thin_film" in spec:
        p.inputs["Thin Film Thickness"].default_value = spec["thin_film"].get("thickness_nm", 500.0)
        p.inputs["Thin Film IOR"].default_value = spec["thin_film"].get("ior", 1.5)
    base = nrm = None
    if "image" in spec:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEXDIR, spec["image"]))
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        base = t.outputs["Color"]
    if "normal" in spec:                           # round 9: as build_rider.gear_material (the strap's weave)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEXDIR, spec["normal"]))
        t.image.colorspace_settings.name = "Non-Color"
        n = nt.nodes.new("ShaderNodeNormalMap")
        n.inputs["Strength"].default_value = spec.get("normal_strength", 1.0)
        nt.links.new(t.outputs["Color"], n.inputs["Color"])
        nt.links.new(n.outputs["Normal"], p.inputs["Normal"])
        nrm = n.outputs["Normal"]
    if "detail" in spec:                           # round 9: the weave tile (goggle_strap_art.detail_nodes)
        sys.path.insert(0, HERE)
        import goggle_strap_art
        goggle_strap_art.detail_nodes(nt, p, spec, TEXDIR, base, nrm)
    return m


def load(path):
    g = np.load(path)
    spec = json.loads(str(g["materials"]))
    if FRAME_RGB:                                  # round 7: the frame in another colourway (the white ISO)
        spec["goggle_frame"] = dict(spec["goggle_frame"], rgb=FRAME_RGB)
    if LENS_VLT:                                   # ... and a plain see-through lens (no mirror)
        for m in ("goggle_lens_mirror", "goggle_lens_clear"):
            spec[m] = dict(thin_vlt=LENS_VLT)
    if STRAP_TEX:
        for m in ("goggle_strap", "goggle_strap_rim"):
            if m in spec:
                spec[m] = dict(spec[m], image=STRAP_TEX)
    if SLIDE_RGB and "goggle_slide" in spec:
        spec["goggle_slide"] = dict(spec["goggle_slide"], rgb=SLIDE_RGB)
    for m in [m for m in spec if "detail" in spec[m]]:
        if NO_DETAIL:
            spec[m] = {k: v for k, v in spec[m].items() if k != "detail"}
        elif WEAVE_TEX:
            spec[m] = dict(spec[m], detail=dict(spec[m]["detail"], image=WEAVE_TEX))
        if os.environ.get("GOGGLE_VIEWS_BUMP") and not NO_DETAIL:              # the weave relief's strength
            spec[m]["detail"] = dict(spec[m]["detail"], bump_strength=float(os.environ["GOGGLE_VIEWS_BUMP"]))
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
    sc.cycles.use_denoising = DENOISE
    sc.view_settings.view_transform = "AgX"
    if LOOK == "d46":
        vs = sc.view_settings
        vs.view_transform, vs.look, vs.exposure = "Standard", "None", STUDIO_EV
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    # the backdrop seen by the camera is Leatt's light grey (236/255: strength 5.0 renders about 234 under AgX; under
    # Standard 236 is linear 0.839, so 1.0 at 0 EV); the light it casts is kept low so the frame keeps its colour (a
    # bright world washed the pink out)
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.84, 0.84, 0.84, 1)
    bg.inputs["Strength"].default_value = 5.0 if LOOK != "d46" else 0.839 / 0.84 / 2.0 ** STUDIO_EV
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
        KEYS.append((o, loc))
        KEY_W.append(en)


KEYS, KEY_W = [], []


def place_lights(s):
    """Round 9: a camera's own studio rig, as a photographer moves the lights round with the camera: "lights", the
    three area lights' [x, y, z, W] (GOGGLE frame; aimed at the origin). Leatt's MY27 back view: two side lights
    grazing the strap's back (the doubled strap's folds by the right slide bright on their right sides and dark at
    the creases, 93 to 154 of 255 across each fold; the left slide's centre bar lit on its left wall) and a dim one
    above. Without it the back is lit only by the front rig's 90 W light above it, the folds read flat."""
    rig = s.get("lights") or [list(loc) + [en] for (o, loc), en in zip(KEYS, KEY_W)]
    for (o, _), (x, y, z, w) in zip(KEYS, rig):
        o.location = (x, y, z)
        o.data.energy = w
        o.rotation_euler = (Vector((0, 0, 0)) - Vector((x, y, z))).to_track_quat("-Z", "Y").to_euler()


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


def camera(sc, name, x, W, H, offset=(0.0, 0.0, 0.0)):
    az, el, roll, d, f, u0, v0 = x
    a, e = math.radians(az), math.radians(el)
    dirn = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    C = Vector(offset) + dirn * d
    fwd = -dirn
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd)
    r = math.radians(roll)
    right, up = right * math.cos(r) + up * math.sin(r), up * math.cos(r) - right * math.sin(r)
    M = Matrix((right, up, -fwd)).transposed().to_4x4()
    M.translation = C + (right * CAM_MM[0] + up * CAM_MM[1] - fwd * CAM_MM[2]) / 1000.0
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


def daylight(sc):
    """Round 8, for his outdoor photos 07, 08 and 09: the daylight rig shared with head_closeups.py and the bike
    (common/day_rig.py, decision 55: a 0.53 deg sun lamp, Blender's multiple-scattering sky over a flat ground, each
    value and its source there) and the scene look's daylight kind (decision 54), fitted on that rig. The sun is aimed
    per camera by its "sun": [phi, theta] (day_sun)."""
    rig = day_rig.rig()
    if LOOK == "agx":                              # rounds 4 to 9's plain AgX, under their 4 W/m2 sun
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.exposure = DAY_EXPOSURE - math.log2(rig["sun_w"] / 4.0)
    else:
        scene_look.apply(sc, "daylight")
    return day_rig.build(sc, rig)


DAY_EXPOSURE = 2.0                                 # the plain AgX's exposure under rounds 4 to 9's 4 W/m2 sun


def day_sun(day, cam, phi_theta):
    """The sun at (phi, theta) in the camera's frame (phi across the image, 90 = image up; theta off the line back
    to the camera): day_rig.aim, as head_closeups.day_sun (the sky's sun follows, the ground is lit by both)."""
    day_rig.aim(day, cam, *phi_theta)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    load(NPZ)
    studio(sc)
    sc.cycles.seed = SEED
    day = None
    if MASK:                                       # no lights, a black world: only the emission
        for o in [o for o in sc.objects if o.type == "LIGHT"]:
            bpy.data.objects.remove(o)
        KEYS.clear()
        for n in sc.world.node_tree.nodes:
            if n.type == "BACKGROUND":
                n.inputs["Strength"].default_value = 0.0
        sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure = "Standard", "None", 0.0
        sc.cycles.use_denoising = False
    elif LIGHT == "daylight":
        day = daylight(sc)
    elif LIGHT != "studio":
        rake(sc, LIGHT)
    print("CYCLES samples %d adaptive %s %.3f denoise %s %s seed %d look %s %s %.2f" % (
        sc.cycles.samples, sc.cycles.use_adaptive_sampling, sc.cycles.adaptive_threshold, sc.cycles.use_denoising,
        sc.cycles.denoiser, sc.cycles.seed, sc.view_settings.view_transform, sc.view_settings.look,
        sc.view_settings.exposure))
    for name in NAMES:
        s = SPEC[name]
        camera(sc, name, s["x"], s["W"], s["H"], s.get("offset", (0.0, 0.0, 0.0)))
        if LIGHT == "studio":                      # daylight removes the studio's lights; a rake hides them
            place_lights(s)
        if day:
            bpy.context.view_layer.update()
            day_sun(day, sc.camera, s.get("sun", (90.0, 110.0)))
        sc.render.use_border = sc.render.use_crop_to_border = "box" in s       # round 8: only the photo's box
        if "box" in s:
            x0, y0, x1, y1 = s["box"]
            sc.render.border_min_x, sc.render.border_max_x = x0 / s["W"], x1 / s["W"]
            sc.render.border_min_y, sc.render.border_max_y = 1 - y1 / s["H"], 1 - y0 / s["H"]
        sc.render.filepath = os.path.join(OUT, name + ("" if LIGHT == "studio" else "_" + LIGHT) + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


main()
