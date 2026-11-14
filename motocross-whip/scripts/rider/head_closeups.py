"""Close-ups of Damien's head (helmet, goggle) from a saved rider blend, at the views matched to his photos.

blender -b --python-exit-code 1 --python head_closeups.py -- RIDER.blend OUT_DIR [views] [samples] [light]

views: comma list of the names in VIEWS (default all). light: "studio" (default, build_rider.studio()) or
"daylight" (a sun and Blender's sky, for comparisons with his outdoor photos 07, 08, 09; see daylight()). The
cameras are set in the rest frame of build_rider.py
(rider standing at the origin facing +x, z up, his head at rest) and carried with his head into the blend's pose:
each camera rides the helmet shell's rigid motion (the shell is parented to the "head" bone), so a view shows his
head from the same side whatever the pose, as in the photo it was matched to.

Sources of the views (rest frame, metres; target near the goggle lens centre):
  p09, p07, p08   the goggle round 2/3 views matched by eye to his photos 09 (front-left from below), 07 (left
                  side, riding pan) and 08 (his right from below); research/rider-ledger/goggle.md
  front, isol     square on and front-left three-quarter at goggle height, for the frame and lens shape
  cam07           the camera fitted to his photo 07 (research/rider-cameras.json, fitted to the bike), the render
                  cropped round his head: the true angle of that photo when the blend has the bike in it
The studio matches build_rider.studio(): Cycles, AgX, the same world and two area lights.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
VIEWS = {  # name: (camera, target, lens mm, (w, h)) in the rest frame
    "p09": ((0.95, 0.55, 1.30), (0.07, 0.0, 1.71), 60, (1200, 1200)),
    "p07": ((0.02, 1.10, 1.62), (0.00, 0.0, 1.71), 60, (1200, 1200)),
    "p08": ((0.70, -0.85, 1.25), (0.05, 0.0, 1.72), 60, (1200, 1200)),
    "front": ((0.80, 0.0, 1.74), (0.08, 0.0, 1.73), 85, (1200, 900)),
    "isol": ((0.62, 0.48, 1.78), (0.08, 0.0, 1.73), 85, (1200, 900)),
}
CAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "research", "rider-cameras.json")
PHOTO_CROP = 0.16        # the photo views: half size of the crop round the head, as a fraction of the photo width
NAMES = [v for v in argv[2].split(",")] if len(argv) > 2 and argv[2] else list(VIEWS) + ["cam07"]
SAMPLES = int(argv[3]) if len(argv) > 3 and argv[3] else 64
LIGHT = argv[4] if len(argv) > 4 else "studio"
os.makedirs(OUT, exist_ok=True)

# Daylight (research/rider-ledger/goggle.md, "Daylight for his photos"): his photos 07, 08 and 09 were taken in one
# session under a clear sky with the sun near the zenith (photo 07: the bike's shadow lies right under it, a little
# towards the camera: sun about 78 deg high, just beyond the bike). Per view, the sun's direction relative to the
# camera: (phi, theta) in deg, phi its direction across the image (0 image right, 90 image up), theta its angle off
# the line back to the camera. 07: the view's camera looks up 4.7 deg, so theta = 90 + (90 - 78) + 4.7 (the sun 78
# deg high); 08, 09: the light on his white shell comes from image up (luminance gradient at 85 and 81 deg), the
# cameras look up at him from the ground, and theta was chosen among 115 to 145 deg by matching the rendered shell's
# lit / shaded ratio to the photo's (sun elevations 73 and 70 deg).
DAY_SUN = {"p07": (90.0, 106.7), "p08": (85.0, 130.0), "p09": (81.0, 130.0)}
DAY_SUN_OTHER = (90.0, 110.0)      # the views with no photo
DAY_SUN_DISC = 0.53                # deg, the sun's angular diameter
DAY_SUN_W = float(os.environ.get("DAY_SUN_W", 4.0))       # sun lamp irradiance (W/m2, Blender units)
# the sky's strength: a clear sky at a high sun gives about 12 % of the global light on the ground as diffuse light
# (clear-sky models), so its light on a horizontal plane is 0.136 of the sun's there; Blender 5.2's
# multiple-scattering sky at strength 1 puts 14.9 (luminance) on it at sun elevations 60 to 75 deg (measured)
DAY_SKY_E1 = 14.9
DAY_SKY = float(os.environ.get("DAY_SKY", 0.136 * DAY_SUN_W * math.cos(math.radians(15)) / DAY_SKY_E1))
DAY_GROUND = (0.41, 0.40, 0.36)    # ground albedo (his 07: the lit pavement / his white shell top x 0.8)
DAY_THETA = os.environ.get("DAY_THETA")                   # override theta (deg) for the calibration sweep
# the photos' exposure: his phone exposes for him, so his white shell's lit half is near white (median linear
# luminance 0.84 in 08, 0.86 in 09). AgX compresses highlights: the render's lit shell reaches 0.45 / 0.51 at +1.3 EV,
# 0.55 / 0.59 at +2.0 and 0.62 / 0.66 at +2.6, where the frame and the sky wash out; +2.0 is kept (the ledger)
DAY_EXPOSURE = float(os.environ.get("DAY_EXPOSURE", 2.0))


def head_motion():
    """World matrix taking the rest frame to the posed head: the helmet shell's world matrix times the inverse of
    its rest placement (mesh coordinates are body.py's MB frame; the rest rider is that frame turned +90 deg about
    z, build_rider.py)."""
    shell = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent_type == "BONE"
                 and o.parent_bone == "head" and "shell" in o.name.lower())
    rest = Matrix.Rotation(math.pi / 2, 4, "Z")
    zs = [(rest @ v.co).z for v in shell.data.vertices]
    assert 1.4 < min(zs) and max(zs) < 2.1, (min(zs), max(zs))      # the rest helmet sits at head height
    return shell.matrix_world @ rest.inverted(), shell.name


def studio(sc):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.92, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    for loc, en in (((3, -3, 5), 600), ((-3, 2, 4), 250)):
        L = bpy.data.lights.new("key", "AREA")
        L.energy = en
        L.size = 2.5
        o = bpy.data.objects.new("key", L)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.9)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(o)


def daylight(sc):
    """A sun lamp and Blender's multiple-scattering sky (its own sun disc off: the lamp is the sun) above a flat
    ground colour (the arena's light from below); AgX as the studio, at the photos' exposure (DAY_EXPOSURE). The
    sun is aimed per view (day_sun)."""
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = DAY_EXPOSURE
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    w = bpy.data.worlds.new("daylight")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    up = nt.nodes.new("ShaderNodeMath")
    up.operation = "GREATER_THAN"
    up.inputs[1].default_value = 0.0
    nt.links.new(sep.outputs["Z"], up.inputs[0])
    gnd = nt.nodes.new("ShaderNodeRGB")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(up.outputs[0], mix.inputs["Factor"])
    nt.links.new(gnd.outputs[0], mix.inputs["A"])
    nt.links.new(sky.outputs["Color"], mix.inputs["B"])
    bg = nt.nodes["Background"]
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = DAY_SKY
    L = bpy.data.lights.new("sun", "SUN")
    L.energy = DAY_SUN_W
    L.angle = math.radians(DAY_SUN_DISC)
    sun = bpy.data.objects.new("sun", L)
    sc.collection.objects.link(sun)
    return dict(sky=sky, ground=gnd, sun=sun)


def day_sun(day, name, cam):
    """Aim the sun for a view: (phi, theta) of DAY_SUN in the camera's frame; the sky's sun follows (Blender's sky:
    elevation asin(z), rotation atan2(x, y), checked against a sun lamp on a matte sphere), and the ground's
    radiance is the albedo times the sun's and the sky's light on it over pi (Lambert)."""
    phi, theta = DAY_SUN.get(name, DAY_SUN_OTHER)
    if DAY_THETA:
        theta = float(DAY_THETA)
    M = cam.matrix_world.to_3x3()
    right, up, back = M.col[0].normalized(), M.col[1].normalized(), M.col[2].normalized()   # back: to the camera
    p, t = math.radians(phi), math.radians(theta)
    d = (back * math.cos(t) + (right * math.cos(p) + up * math.sin(p)) * math.sin(t)).normalized()
    day["sun"].rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    day["sky"].sun_elevation = math.asin(max(min(d.z, 1.0), -1.0))
    day["sky"].sun_rotation = math.atan2(d.x, d.y)
    e = (DAY_SUN_W * max(d.z, 0.0) + DAY_SKY_E1 * DAY_SKY) / math.pi       # the ground's radiance per albedo
    day["ground"].outputs[0].default_value = (*[a * e / max(DAY_SKY, 1e-6) for a in DAY_GROUND], 1.0)
    print("DAYLIGHT", name, "sun", [round(v, 3) for v in d], "elevation %.1f deg" % math.degrees(math.asin(d.z)))


def photo_view(sc, name, D, scale=2, day=None):
    """A fitted photo camera (as build_rider.photo_camera), rendered only in a square round the posed head."""
    import json
    from bpy_extras.object_utils import world_to_camera_view
    spec = json.load(open(CAMS))[name]
    cam = bpy.data.objects.new("cam_" + name, bpy.data.cameras.new("cam_" + name))
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.lens = spec["f"] * 36.0 / spec["W"]
    rv = Vector(spec["rotvec"])
    R = Matrix.Rotation(rv.length, 3, rv.normalized()) if rv.length > 0 else Matrix.Identity(3)
    cam.matrix_world = Matrix.Translation(Vector(spec["C"])) @ R.transposed().to_4x4()
    sc.collection.objects.link(cam)
    sc.camera = cam
    if day:
        day_sun(day, name, cam)
    sc.render.resolution_x, sc.render.resolution_y = int(spec["W"] * scale), int(spec["H"] * scale)
    bpy.context.view_layer.update()
    c = world_to_camera_view(sc, cam, D @ Vector((0.04, 0.0, 1.70)))      # the head's centre, rest frame
    hx, hy = PHOTO_CROP, PHOTO_CROP * spec["W"] / spec["H"]
    sc.render.border_min_x, sc.render.border_max_x = max(0.0, c.x - hx), min(1.0, c.x + hx)
    sc.render.border_min_y, sc.render.border_max_y = max(0.0, c.y - hy), min(1.0, c.y + hy)
    sc.render.use_border = sc.render.use_crop_to_border = True
    sc.render.filepath = os.path.join(OUT, f"head_{name}.png")
    bpy.ops.render.render(write_still=True)
    sc.render.use_border = sc.render.use_crop_to_border = False
    print("RENDERED", sc.render.filepath, "head at", round(c.x * spec["W"]), round((1 - c.y) * spec["H"]), "px")


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    if LIGHT not in ("studio", "daylight"):
        raise SystemExit("light must be studio or daylight, not %r" % LIGHT)
    day = daylight(sc) if LIGHT == "daylight" else studio(sc)
    D, shell = head_motion()
    print("HEAD", shell, [round(x, 4) for x in D.translation])
    for name in NAMES:
        if name.startswith("cam"):
            photo_view(sc, name, D, day=day)
            continue
        loc, tgt, lens, (w, h) = VIEWS[name]
        rot = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_matrix().to_4x4()
        cam = bpy.data.objects.new("cam_" + name, bpy.data.cameras.new("cam_" + name))
        cam.data.lens = lens
        cam.matrix_world = D @ Matrix.Translation(Vector(loc)) @ rot
        sc.collection.objects.link(cam)
        sc.camera = cam
        if day:
            bpy.context.view_layer.update()
            day_sun(day, name, cam)
        sc.render.resolution_x, sc.render.resolution_y = w, h
        sc.render.filepath = os.path.join(OUT, f"head_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


main()
