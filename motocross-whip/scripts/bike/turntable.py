"""Studio turntable of the built bike: the bike turns, the camera and the studio stay put. Frames are RGBA (the
shadow on a transparent film): put them on white (ffmpeg overlay or PIL) for Honda's white studio.

blender -b BIKE.blend --python-exit-code 1 --python turntable.py -- still DEG SIZE SAMPLES OUT.png
blender -b BIKE.blend --python-exit-code 1 --python turntable.py -- frames N SIZE SAMPLES OUTDIR [FIRST LAST]

DEG is the bike's yaw from the hero pose (0 = front-left three-quarter). `frames` renders frame k (1..N) at
k-1 of N steps round a full turn, so frame N+1 would equal frame 1 and the video loops without a seam.
Made 2026-11-12 because Damien's phone would not load the web viewer: a video and photos play everywhere.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
mode = args[0]
sc = bpy.context.scene

# the turntable: an empty under the middle of the bike's own bounds (world frame, metres); the bike's root hangs on it
meshes = [o for o in bpy.data.objects["bike"].children_recursive if o.type == "MESH"]
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
CENTRE = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0.0))
MID_Z = (lo.z + hi.z) / 2
print("BOUNDS", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi), flush=True)
HERO_YAW = math.radians(38.0)             # front wheel toward the camera, the left side showing
tt = bpy.data.objects.new("turntable", None)
sc.collection.objects.link(tt)
tt.location = CENTRE
bpy.context.view_layer.update()          # the empty's matrix must be current before the bike is hung on it
root = bpy.data.objects["bike"]
mw = root.matrix_world.copy()
root.parent = tt
root.matrix_parent_inverse = Matrix.Translation(-CENTRE)
root.matrix_world = mw

# fixed camera on the open side of the white sweep (+y), lens and height of a product shot
cd = bpy.data.cameras.new("tt_cam")
cd.lens = 70.0
cd.sensor_fit = "HORIZONTAL"
cd.sensor_width = 36.0
cam = bpy.data.objects.new("tt_cam", cd)
sc.collection.objects.link(cam)
cam.location = CENTRE + Vector((0.0, 5.2, 1.0))
cam.rotation_euler = (CENTRE + Vector((0.0, 0.0, MID_Z * 0.92)) - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

# the look tuned against the red of Honda's studio photos (build_bike.render, honda_* views): a shadow-catching floor
# on a transparent film (put on white afterwards), Standard view, an even dome of light, the lamps at half power
bpy.data.objects["cyc"].hide_render = True
bpy.data.objects["floor"].hide_render = False
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
for lo in bpy.data.objects:
    if lo.type == "LIGHT" and "base_energy" in lo:
        lo.data.energy = lo["base_energy"] * 0.5

size, samples = int(args[2]), int(args[3])
r = sc.render
r.engine = "CYCLES"
r.resolution_x = r.resolution_y = size
r.resolution_percentage = 100
r.film_transparent = True
r.image_settings.color_mode = "RGBA"
r.image_settings.file_format = "PNG"
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.cycles.device = "CPU"
sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure = "Standard", "None", -0.9


def pose(yaw):
    tt.rotation_euler = (0.0, 0.0, HERO_YAW + yaw)


if mode == "still":
    pose(math.radians(float(args[1])))
    r.filepath = args[4]
    bpy.ops.render.render(write_still=True)
    print("STILL", args[4], flush=True)
else:
    n = int(args[1])
    out = args[4]
    first, last = (int(args[5]), int(args[6])) if len(args) > 6 else (1, n)
    os.makedirs(out, exist_ok=True)
    for k in range(first, last + 1):
        path = os.path.join(out, "f%04d.png" % k)
        if os.path.exists(path):
            continue
        pose(2 * math.pi * (k - 1) / n)
        r.filepath = path
        bpy.ops.render.render(write_still=True)
        print("FRAME", k, flush=True)
