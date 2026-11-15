"""Close-ups of Damien's head (helmet, goggle) from a saved rider blend, at the views matched to his photos.

blender -b --python-exit-code 1 --python head_closeups.py -- RIDER.blend OUT_DIR [views] [samples] [light]

views: comma list of the names in VIEWS (default all). light: "studio" (default, build_rider.studio()) or
"daylight" (a sun and Blender's sky, for comparisons with his outdoor photos 07, 08, 09; see daylight()). The
cameras ride the helmet shell's rigid motion (the shell is parented to the "head" bone), so a view shows his
head from the same side whatever the pose, as in the photo it was matched to.

Sources of the views:
  p09, p07, p08   his photos 09 (front-left from below), 07 (left side, riding pan) and 08 (from below, his head
                  pitched far down: the crown faces the camera): each photo's camera fitted to the helmet in its own
                  frame (his_cameras.py, research/his-photo-cameras.json; decision 47), placed by the shell's
                  gear_frame (helmet.extras). The render is the photo's crop round his head (the comparison sheets'
                  crop, x y size in photo px) at HIS_SCALE x the photo's pixels, so it lies 1:1 on the crop
  front, isol     square on and front-left three-quarter at goggle height, for the frame and lens shape (rest frame
                  of build_rider.py, metres: rider standing at the origin facing +x, z up; target near the goggle
                  lens centre)
  cam07           the camera fitted to his photo 07 (research/rider-cameras.json, fitted to the bike), the render
                  cropped round his head: the true angle of that photo when the blend has the bike in it
The studio matches build_rider.studio(): Cycles, the same world and two area lights, and the scene look shared with
the bike (scene_look.py "scene", decision 54); the daylight uses its "daylight" kind, fitted to these views' pairs
with his photos 07, 08 and 09 (research/scene-look.md).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
import day_rig  # noqa: E402  (decision 55: the daylight rig shared with goggle_views.py and the bike)
import scene_look  # noqa: E402  (decision 54: the look shared with the bike)

argv = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HIS_VIEWS = ("p09", "p07", "p08")          # his photos' cameras in the helmet frame (his-photo-cameras.json)
HIS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "research", "his-photo-cameras.json")
HIS_SCALE = 4                              # render px per photo px (07's 240 px crop renders 960 px)
VIEWS = {  # name: (camera, target, lens mm, (w, h)) in the rest frame
    "front": ((0.80, 0.0, 1.74), (0.08, 0.0, 1.73), 85, (1200, 900)),
    "isol": ((0.62, 0.48, 1.78), (0.08, 0.0, 1.73), 85, (1200, 900)),
}
CAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "research", "rider-cameras.json")
PHOTO_CROP = 0.16        # the photo views: half size of the crop round the head, as a fraction of the photo width
NAMES = [v for v in argv[2].split(",")] if len(argv) > 2 and argv[2] else [*HIS_VIEWS, *VIEWS, "cam07"]
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
# cam07 (the bike's camera fitted to the same photo 07, research/rider-cameras.json) takes p07's sun and height
# (decision 55, round 2b: DAY_SUN_OTHER on the blend's up put that sun about 75 deg high, p07's on the blend's up 78.5)
DAY_SUN = {"p07": (90.0, 106.7), "cam07": (90.0, 106.7), "p08": (85.0, 130.0), "p09": (81.0, 130.0)}
DAY_SUN_OTHER = (90.0, 110.0)      # the views with no photo
SUN_HEIGHT_VIEWS = (*HIS_VIEWS, "cam07")   # the views of his photos: the sun DAY_ELEV high (below)
# The light: the daylight rig shared with goggle_views.py and the bike (common/day_rig.py, decision 55: its sun, sky
# and ground, each value and its source; DAY_GAIN, DAY_SUN_W and DAY_SKY still override it there). His photos' views
# turn the sky and the ground so that the sun stands DAY_ELEV high, as in 07 (one session): their cameras ride the
# helmet, so the blend's pose alone set the sun's height (the seated rider gave 67, 13 and 36 deg); the camera
# without roll and the lower of the two pitches (day_rig.photo_up: 07 4.7 deg, as cam07 fitted to the bike; 08 and
# 09 about 29 and 30 deg, his head about 6 m above a camera 12 m away, research/scene-look.md "The daylight rig")
DAY_ELEV = 78.0
DAY_THETA = os.environ.get("DAY_THETA")                   # override theta (deg) for the calibration sweep
DAY_EV = float(os.environ.get("DAY_EV", 0.0))             # exposure offset (stops) on the look, for sweeps


def head_motion():
    """World matrix taking the rest frame to the posed head: the helmet shell's world matrix times the inverse of
    its rest placement (mesh coordinates are body.py's MB frame; the rest rider is that frame turned +90 deg about
    z, build_rider.py)."""
    shell = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent_type == "BONE"
                 and o.parent_bone == "head" and "shell" in o.name.lower())
    rest = Matrix.Rotation(math.pi / 2, 4, "Z")
    zs = [(rest @ v.co).z for v in shell.data.vertices]
    assert 1.4 < min(zs) and max(zs) < 2.1, (min(zs), max(zs))      # the rest helmet sits at head height
    return shell.matrix_world @ rest.inverted(), shell


def studio(sc):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    scene_look.apply(sc, "scene")
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
    """The daylight rig shared with goggle_views.py and the bike (day_rig.build: a sun lamp and Blender's
    multiple-scattering sky above a flat ground) and the scene look's daylight kind. The sun is aimed per view
    (day_sun)."""
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    scene_look.apply(sc, "daylight", ev=DAY_EV)
    return day_rig.build(sc)


def day_sun(day, name, cam):
    """Aim the sun for a view: (phi, theta) of DAY_SUN in the camera's frame (day_rig.aim: the sky's sun and the
    ground's light follow)."""
    phi, theta = DAY_SUN.get(name, DAY_SUN_OTHER)
    if DAY_THETA:
        theta = float(DAY_THETA)
    d = day_rig.aim(day, cam, phi, theta, DAY_ELEV if name in SUN_HEIGHT_VIEWS else None)
    # a view of one of his photos at that photo's own exposure (decision 55) and its own tint of the darks
    # (decision 59: 07's phone), the others at the one look
    scene_look.apply(bpy.context.scene, "daylight", ev=DAY_EV + scene_look.photo_ev(name),
                     tint=scene_look.photo_tint(name))
    print("DAYLIGHT", name, "sun", [round(v, 3) for v in d], "elevation %.1f deg" % day["elevation"],
          "camera pitch %.1f deg" % day["pitch"] if name in SUN_HEIGHT_VIEWS else "(the blend's up)")


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


def his_view(sc, name, shell, day=None):
    """His photo's camera, fitted in the helmet frame (rows of R: x right, y up, z forward; u = cx + f x / z,
    v = cy - f y / z), carried by the shell: world = shell's matrix @ gear_frame (helmet -> mesh) @ camera. Only the
    photo's crop round his head is rendered, at HIS_SCALE x its pixels."""
    import json
    spec = json.load(open(HIS))["cameras"][name[1:]]
    if "gear_frame" not in shell:
        raise SystemExit("the helmet shell has no gear_frame: rebuild the rider from a gear npz of helmet.py")
    F = Matrix([shell["gear_frame"][4 * i:4 * i + 4] for i in range(4)])
    R, C = spec["R"], spec["C"]
    M = Matrix([[R[0][i], R[1][i], -R[2][i], C[i]] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]])
    W, H = spec["W"], spec["H"]
    cam = bpy.data.objects.new("cam_" + name, bpy.data.cameras.new("cam_" + name))
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.lens = spec["f"] * 36.0 / W
    cam.data.shift_x = (W / 2 - spec["cx"]) / W                 # Blender's shift: in units of the wider side
    cam.data.shift_y = (spec["cy"] - H / 2) / W
    cam.matrix_world = shell.matrix_world @ F @ M
    sc.collection.objects.link(cam)
    sc.camera = cam
    if day:
        day_sun(day, name, cam)
    sc.render.resolution_x, sc.render.resolution_y = W * HIS_SCALE, H * HIS_SCALE
    x, y, n = spec["crop"]
    sc.render.border_min_x, sc.render.border_max_x = x / W, (x + n) / W
    sc.render.border_min_y, sc.render.border_max_y = 1 - (y + n) / H, 1 - y / H
    sc.render.use_border = sc.render.use_crop_to_border = True
    sc.render.filepath = os.path.join(OUT, f"head_{name}.png")
    bpy.ops.render.render(write_still=True)
    sc.render.use_border = sc.render.use_crop_to_border = False
    print("RENDERED", sc.render.filepath, "camera", [round(v, 3) for v in cam.matrix_world.translation],
          "crop", spec["crop"], "landmark rms %.1f px" % spec["landmark_rms_px"])


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    if LIGHT not in ("studio", "daylight"):
        raise SystemExit("light must be studio or daylight, not %r" % LIGHT)
    day = daylight(sc) if LIGHT == "daylight" else studio(sc)
    D, shell = head_motion()
    print("HEAD", shell.name, [round(x, 4) for x in D.translation])
    for name in NAMES:
        if name in HIS_VIEWS:
            his_view(sc, name, shell, day=day)
            continue
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
