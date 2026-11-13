"""Render cameras of a built bike .blend under a raking sun, to show waves in a gloss surface (decision 37 round 2).

blender -b BLEND --python-exit-code 1 --python rake.py -- OUTPREFIX "spec;spec;..."
  spec: camera[:x0,y0,x1,y1][:rakeL|:rakeR][:red]
    x0,y0,x1,y1  a crop in the camera's pixels
    rakeL/rakeR  the studio lights off, a low ambient, and a sun grazing the left (right) face from behind (0.5 deg
                 wide, nearly along the bike: direction (1, -/+0.10, -0.08) in the bike's frame): every dent is a dark
                 or light streak along the face
    red          the side panels in plain gloss red (no kit), to judge the shape alone: a printed kit hides waves
  Writes OUTPREFIX_<camera>[_<tags>].png.
"""
import math
import sys

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
pre = a[0]
sc = bpy.context.scene
sc.cycles.samples = 64
ob = bpy.data.objects["side_panels"]
kit_mats = list(ob.data.materials)
red = bpy.data.materials.new("gloss_red")
red.use_nodes = True
bs = red.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.75, 0.01, 0.015, 1)
bs.inputs["Roughness"].default_value = 0.2
bs.inputs["Coat Weight"].default_value = 0.5
bs.inputs["Coat Roughness"].default_value = 0.03
lights = [o for o in bpy.data.objects if o.type == "LIGHT"]
bg = sc.world.node_tree.nodes["Background"].inputs["Strength"]
for spec in a[1].split(";"):
    nm, *rest = spec.split(":")
    co = bpy.data.objects[nm]
    sc.camera = co
    crop = [r for r in rest if "," in r]
    rake = next((r for r in rest if r.startswith("rake")), None)
    for i in range(len(ob.data.materials)):
        ob.data.materials[i] = red if "red" in rest else kit_mats[i]
    sun = None
    for lo in lights:
        lo.hide_render = bool(rake)
    bg.default_value = 0.03 if rake else 0.30
    if rake:
        ld = bpy.data.lights.new("rake", "SUN")
        ld.energy = 5.0
        ld.angle = math.radians(0.5)
        sun = bpy.data.objects.new("rake", ld)
        root = bpy.data.objects["bike"]
        s = 1.0 if rake == "rakeL" else -1.0
        dl = root.matrix_world.to_3x3() @ Vector((1.0, -0.10 * s, -0.08))     # from behind, grazing the face
        sun.rotation_euler = dl.to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(sun)
    sc.render.resolution_x, sc.render.resolution_y = co["res"]
    sc.render.resolution_percentage = 100
    vs = sc.view_settings
    vs.view_transform, vs.look, vs.exposure = "AgX", "AgX - Punchy", -0.6
    bpy.data.objects["cyc"].hide_render = False
    bpy.data.objects["floor"].hide_render = True
    sc.render.film_transparent = False
    if crop:
        x0, y0, x1, y1 = (float(q) for q in crop[0].split(","))
        W, H = sc.render.resolution_x, sc.render.resolution_y
        sc.render.use_border = sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = x0 / W, x1 / W
        sc.render.border_min_y, sc.render.border_max_y = 1 - y1 / H, 1 - y0 / H
    else:
        sc.render.use_border = False
    tag = "_".join(r for r in rest if "," not in r)
    sc.render.filepath = f"{pre}_{nm}{'_' + tag if tag else ''}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, flush=True)
    if sun is not None:
        bpy.data.objects.remove(sun, do_unlink=True)
