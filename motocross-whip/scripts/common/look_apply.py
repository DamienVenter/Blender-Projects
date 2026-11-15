"""Put scene-linear pixels through a scene look in Blender itself: a render, so the view settings and the compositor
both apply, as they do to the scripts' renders.

blender -b --factory-startup --python-exit-code 1 --python look_apply.py -- IN.npy OUT.png KIND [EV]

IN.npy: (H, W, 3) float32, scene-linear Rec.709, rows top to bottom. The pixels go into a float image ("Linear
Rec.709") on an emission plane that fills an orthographic camera at one render pixel per texel (closest texel, one
sample, a 0.01 px pixel filter: each pixel is its texel exactly), rendered by Cycles under
scene_look.apply(scene, KIND, EV) and written as an 8-bit RGB PNG without dither. Used by look_fit.py (the look
before and after on the fit's pairs) and test_scene_look.py (a fixed swatch chart against scene_look.display).
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene_look  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, kind = argv[0], argv[1], argv[2]
ev = float(argv[3]) if len(argv) > 3 else 0.0
a = np.load(src).astype(np.float32)
H, W = a.shape[:2]
if min(H, W) < 4:
    raise SystemExit("look_apply: at least 4 x 4 pixels (Blender renders a smaller image with black rows added)")
img = bpy.data.images.new("lin", W, H, alpha=True, float_buffer=True)
img.colorspace_settings.name = "Linear Rec.709"
img.pixels.foreach_set(np.concatenate([a[::-1], np.ones((H, W, 1), np.float32)], -1).ravel())   # rows bottom up
sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
me = bpy.data.meshes.new("plane")
me.from_pydata([(-W / H, -1, 0), (W / H, -1, 0), (W / H, 1, 0), (-W / H, 1, 0)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new()
for i, xy in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
    uv.data[i].uv = xy
pl = bpy.data.objects.new("plane", me)
sc.collection.objects.link(pl)
m = bpy.data.materials.new("emit")
nt = m.node_tree if m.node_tree else None
if nt is None:
    m.use_nodes = True
    nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"
em = nt.nodes.new("ShaderNodeEmission")
mo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs[0], mo.inputs[0])
me.materials.append(m)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.0 * max(W / H, 1.0)
cam.location = (0.0, 0.0, 1.0)
sc.collection.objects.link(cam)
sc.camera = cam
sc.world = None
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 1
sc.cycles.use_denoising = False
sc.cycles.use_adaptive_sampling = False
sc.cycles.filter_width = 0.01
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.dither_intensity = 0.0
scene_look.apply(sc, kind, ev=ev)
im = sc.render.image_settings
im.media_type = "IMAGE"
im.file_format = "PNG"
im.color_mode = "RGB"
im.color_depth = "8"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("LOOK_APPLY", kind, ev, scene_look.describe(sc), out)
