"""Close-ups of Damien's head (helmet, goggle) from a saved rider blend, at the views matched to his photos.

blender -b --python-exit-code 1 --python head_closeups.py -- RIDER.blend OUT_DIR [views] [samples]

views: comma list of the names in VIEWS (default all). The cameras are set in the rest frame of build_rider.py
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
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
os.makedirs(OUT, exist_ok=True)


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


def photo_view(sc, name, D, scale=2):
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
    studio(sc)
    D, shell = head_motion()
    print("HEAD", shell, [round(x, 4) for x in D.translation])
    for name in NAMES:
        if name.startswith("cam"):
            photo_view(sc, name, D)
            continue
        loc, tgt, lens, (w, h) = VIEWS[name]
        rot = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_matrix().to_4x4()
        cam = bpy.data.objects.new("cam_" + name, bpy.data.cameras.new("cam_" + name))
        cam.data.lens = lens
        cam.matrix_world = D @ Matrix.Translation(Vector(loc)) @ rot
        sc.collection.objects.link(cam)
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = w, h
        sc.render.filepath = os.path.join(OUT, f"head_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


main()
