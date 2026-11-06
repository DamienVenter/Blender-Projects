"""Render one camera view of the demo scene with Workbench.

blender -b DEMO.blend --python-exit-code 1 --python render_view.py -- CAM RES_X RES_Y F_START F_END STEP OUT_DIR
Frames are written as OUT_DIR/f_#####.png (Blender frame numbers, 120 fps timeline).
"""
import sys
import bpy

cam, rx, ry, f0, f1, step, out = sys.argv[sys.argv.index("--") + 1:]
scn = bpy.context.scene
scn.camera = bpy.data.objects[cam]
scn.render.resolution_x, scn.render.resolution_y = int(rx), int(ry)
scn.render.resolution_percentage = 100
scn.frame_start, scn.frame_end, scn.frame_step = int(f0), int(f1), int(step)
scn.render.filepath = f"{out}/f_#####"
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_mode = "RGB"
bpy.ops.render.render(animation=True)
print("RENDER OK", cam, f0, f1, step)
