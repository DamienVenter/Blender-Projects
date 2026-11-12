"""The bike for the web viewer: one Draco-compressed glTF of a built .blend, small enough for a phone.

blender -b BIKE.blend --python-exit-code 1 --python export_web.py -- OUT.glb [POS,NORMAL,UV quantization bits]
python3 glb2json.py OUT.glb viewer/bike.json          (the artifact host serves .json, not .glb)

2026-11-12: Damien's phone did not load the 78 MB, 6-file viewer of model v0.5 (1.37 million vertices). Draco with
14-bit positions, 10-bit normals and 12-bit UVs gives 5.9 MB (7.8 MB as JSON) with no visible loss. The page
(`viewer/bike.html`) decodes it with three.js r147's DRACOLoader; the decoder files are published beside the page
in `draco/` (from cdn.jsdelivr.net/npm/three@0.147.0/examples/js/libs/draco/, copies in `viewer/draco/`), because
the artifact host lets a page fetch only its own files.
"""
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
qpos, qnorm, quv = (int(v) for v in (args[1] if len(args) > 1 else "14,10,12").split(","))
col = next(c for c in bpy.data.collections if c.name.startswith("bike"))
for ob in bpy.context.scene.objects:
    ob.select_set(ob.name in col.all_objects)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_apply=True,
                          export_image_format="JPEG", export_jpeg_quality=85,
                          export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
                          export_draco_position_quantization=qpos, export_draco_normal_quantization=qnorm,
                          export_draco_texcoord_quantization=quv)
print("EXPORTED", out, col.name)
