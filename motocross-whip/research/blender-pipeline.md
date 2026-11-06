# Blender pipeline research: Motocross Whip

Researched 2026-11-06 for the build server (Blender 5.2.3 LTS, Python 3.13.13, 4 CPU cores, 15 GB RAM, no GPU) and Damien's machine (Blender 5.2.0 LTS).

**Legend**
- **verified locally**: checked by a script on this server's Blender 5.2.3 (`blender -b --factory-startup`). Where it says "5.2.0 and 5.2.3", the same check also ran on `blender-5.2.0`.
- Anything not marked comes from the cited source and was not tested here.
- Test scripts lived in the session scratchpad and were not kept in the repo.
- Numbers marked "estimate" are starting points from experience or simple maths, not measurements. Replace them with measured values from Damien's photos and kit when we have them.

**Contents**
1. Blender 5.x API checklist (vs 4.x)
2. Recommended toolchain
3. Notes per area: human, rig, cloth, assets, tyres/spokes/chain/decals, dust
4. Physically based material values
5. Render settings and 4K60 feasibility
6. Matching real motorsport camera work
7. Web viewer (glTF + three.js)
8. Blender MCP and automation
9. Sources

---

## 1. Blender 5.x API checklist (vs 4.x)

Official sources: release notes for [5.0](https://developer.blender.org/docs/release_notes/5.0/), [5.1](https://developer.blender.org/docs/release_notes/5.1/), [5.2](https://developer.blender.org/docs/release_notes/5.2/), plus their Python API pages ([5.0](https://developer.blender.org/docs/release_notes/5.0/python_api/), [5.1](https://developer.blender.org/docs/release_notes/5.1/python_api/), [5.2](https://developer.blender.org/docs/release_notes/5.2/python_api/)). Release dates: 5.0 on 2025-11-18, 5.1 on 2026-03-17, 5.2 LTS on 2026-07-14 (supported until July 2028).

General rule that prevents most breakage: **address node sockets by name, never by index; read enum values from the error message of a bad assignment, not from `bl_rna...enum_items`** (dynamic enums such as `render.engine` and `view_transform` list only a placeholder there, verified locally).

### 1.1 Headless and command line
- [ ] Pass `--python-exit-code 1` before `--python`, otherwise a Python exception still exits with code 0 (verified locally, also in the `blender-headless` skill).
- [ ] Use absolute paths. `//` paths fail when no .blend is loaded.
- [ ] Argument order matters: options apply in order, so put `-o` (output path) before `-f`/`-a` (`blender --help`, verified locally).
- [ ] 5.0 logging rewrite: `--debug-cycles` becomes `--log cycles`, `--debug-ffmpeg` becomes `--log video`, `--verbose` becomes `--log-level`. Background render progress output changed format, so any log parser must be rewritten ([5.0 Core](https://developer.blender.org/docs/release_notes/5.0/core/)).
- [ ] 5.1: the Python user site-packages directory is no longer loaded. Use `--python-use-user-env` if a script needs pip-installed user modules ([5.1 Core](https://developer.blender.org/docs/release_notes/5.1/core/)). Flag present in `blender --help` (verified locally).
- [ ] Online access preference is off in factory settings (`bpy.app.online_access == False`, verified locally). Extensions that respect it (MPFB does) skip network features unless Blender runs with `--online-mode`.
- [ ] UNIX: `TMP` is ignored, use `TMPDIR` (5.0 Core).
- [ ] 5.2: `wm.save_auto_save` lets a script write an autosave on demand ([5.2 Core](https://developer.blender.org/docs/release_notes/5.2/core/)); operator present (verified locally).
- [ ] 5.2: `gpu.init()` initialises the GPU backend in background mode (5.2 Python API).

### 1.2 Render engines, EEVEE, Cycles
- [ ] EEVEE engine identifier is `BLENDER_EEVEE` again (4.2 to 4.5 used `BLENDER_EEVEE_NEXT`). Valid engines on 5.2.3: `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES` (verified locally).
- [ ] `scene.eevee.gtao_distance` moved to `view_layer.eevee.ambient_occlusion_distance`; `use_gtao` and `gtao_quality` removed (5.0 Python API). `view_layer.eevee` has `ambient_occlusion_distance` (verified locally).
- [ ] Render pass names are spelled out: "DiffCol" is "Diffuse Color", "IndexMA" is "Material Index", "Z" is "Depth" ([5.0 Rendering](https://developer.blender.org/docs/release_notes/5.0/rendering/)). The Render Layers node shows `Depth` and `Vector` outputs (verified locally).
- [ ] Cycles volumes default to unbiased null scattering; step rate and max steps only apply with `scene.cycles.volume_biased = True` ([5.0 Cycles](https://developer.blender.org/docs/release_notes/5.0/cycles/)). Default False (verified locally).
- [ ] Cycles "Use Tiling" option removed; tiling is always on. Default `cycles.tile_size = 2048` (verified locally).
- [ ] Objects without a material now get a specular component in Cycles (5.0 Cycles). Grey placeholder renders look different from 4.x.
- [ ] Adaptive subdivision is no longer experimental (5.0 Cycles). Useful for tyre knobs and dirt displacement.
- [ ] Normal Map node: with displacement it uses the undisplaced normal (5.0); 5.1 adds the choice of base mesh and an OpenGL/DirectX switch. On 5.2.3 the node has `convention` (`'OPENGL'` default) and `base` (`'DISPLACED'` default) (verified locally). Poly Haven and ambientCG ship both GL and DX normal maps: pick the GL file or set `convention='DIRECTX'`.
- [ ] 5.2 subsurface: Random Walk radius scaling changed to match other renderers; old files convert to `'RANDOM_WALK_LEGACY'`. `subsurface_method` options: `BURLEY`, `RANDOM_WALK`, `RANDOM_WALK_SKIN`, `RANDOM_WALK_LEGACY` (verified locally, 5.2.0 and 5.2.3). Skin values tuned in 4.x will look different.
- [ ] 5.2 Cycles texture cache: `scene.render.use_texture_cache` and `scene.render.use_auto_generate_texture_cache` (verified locally). It writes `.tx` files into a `blender_tx/` folder next to each image ([5.2 Cycles](https://developer.blender.org/docs/release_notes/5.2/cycles/), [manual](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/performance.html)). Add `blender_tx/` to `.gitignore` so caches never reach Git LFS. CLI: `blender scene.blend --command maketx`.
- [ ] 5.2 Raycast shader node can read attributes at the hit point (Cycles only; EEVEE outputs zero).
- [ ] Shader "Time" node (5.2) is the node type `GeometryNodeInputSceneTime` inside material trees; there is no `ShaderNodeTime` (verified locally).
- [ ] 5.0 Cycles OSL camera: aperture position no longer scales with focal length (only matters for custom OSL cameras).

### 1.3 Colour management
- [ ] Each blend file has a working colour space: `bpy.data.colorspace.working_space` (read-only, default `"Linear Rec.709"`, interop id `lin_rec709_scene`). Change it only with `bpy.ops.wm.set_working_color_space` (verified locally). Options per [5.0 Color Management](https://developer.blender.org/docs/release_notes/5.0/color_management/): Linear Rec.709, Linear Rec.2020, ACEScg. **Recommendation: keep Linear Rec.709**, since CC0 textures and the physicallybased.info values used below are linear sRGB/Rec.709.
- [ ] View transforms on 5.2.3: `Standard`, `ACES 1.3`, `ACES 2.0`, `Khronos PBR Neutral`, `AgX` (default), `Filmic`, `Filmic Log`, `False Color`, `Raw` (verified locally). The 5.0 notes add ACES 1.3 and ACES 2.0 in standard and HDR versions, plus AgX HDR.
- [ ] Look names carry a prefix: `'AgX - Punchy'`, `'AgX - Base Contrast'`, `'AgX - Medium High Contrast'`, `'AgX - High Contrast'` and so on, plus `'None'` (verified locally).
- [ ] Display devices: `sRGB`, `Display P3`, `Rec.1886`, `Rec.2020`, `Rec.2100-PQ`, `Rec.2100-HLG` (verified locally). HDR video needs a Rec.2100 display setting, H.265 or AV1, 10 or 12 bit ([5.0 Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.0/pipeline_io/)).
- [ ] New env var `BLENDER_OCIO` overrides the OCIO config for Blender only (5.0).
- [ ] Brush and palette colours are now scene linear (5.0). Not relevant to scripts that set node `default_value`, which was always scene linear.

### 1.4 Materials and shader nodes
- [ ] `Material.use_nodes` and `World.use_nodes` raise `DeprecationWarning` ("expected to be removed in Blender 6.0"). New materials and worlds already have a node tree with Principled BSDF + Material Output, or Background + World Output (verified locally). Do not set `use_nodes`.
- [ ] **Principled BSDF inputs in 5.2 (verified locally, 5.2.0 and 5.2.3), in order:** `Base Color`, `Metallic`, `Roughness`, `IOR`, `Alpha`, **`Thin Wall`** (new in 5.2, boolean), `Normal`, `Weight`, `Diffuse Roughness`, `Subsurface Weight`, `Subsurface Radius`, `Subsurface Scale`, `Subsurface IOR`, `Subsurface Anisotropy`, `Specular IOR Level`, `Specular Tint`, `Anisotropic`, `Anisotropic Rotation`, `Tangent`, `Transmission Weight`, `Coat Weight`, `Coat Roughness`, `Coat IOR`, `Coat Tint`, `Coat Normal`, `Sheen Weight`, `Sheen Roughness`, `Sheen Tint`, `Emission Color`, `Emission Strength`, `Thin Film Thickness`, `Thin Film IOR`. Because `Thin Wall` sits at index 5, every index after `Alpha` shifted versus 4.x. Node properties: `distribution` (default `MULTI_GGX`), `subsurface_method` (default `RANDOM_WALK`).
- [ ] Defaults worth knowing (verified locally): Roughness 0.5, IOR 1.5, Coat Roughness 0.03, Coat IOR 1.5, Subsurface Scale 0.005, Thin Film IOR 1.33.
- [ ] Removed node types: `ShaderNodeSeparateRGB`/`CombineRGB` (use `ShaderNodeSeparateColor`/`CombineColor`), `ShaderNodeTexPointDensity` (5.0), `ShaderNodeTexMusgrave` (merged into Noise in 4.1) (verified locally). `ShaderNodeMixRGB` still exists but prefer `ShaderNodeMix`.
- [ ] Sky Texture: `sky_type='NISHITA'` is rejected; types are `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING` (default), `PREETHAM`, `HOSEK_WILKIE` (verified locally). 5.0 notes say the `sun_direction`, `turbidity` and `ground_albedo` inputs were removed, yet these RNA properties still exist on 5.2.3 (verified locally). Do not build on them.
- [ ] Voronoi texture uses a new hash in 5.0, so patterns differ from 4.x (5.0 Rendering).
- [ ] Material Output nodes inside a node group no longer take priority over outputs outside it (5.0 Rendering).
- [ ] EEVEE material settings: `shadow_method` gone (4.2); use `surface_render_method` (`'DITHERED'` or `'BLENDED'`). `blend_method` still exists (verified locally).
- [ ] Shader nodes gained Repeat Zones, Closures, Bundles and Menu Switch (5.0). Cycles unrolls repeat zones with a fixed count.

### 1.5 Animation, actions, armatures
- [ ] **Legacy Action API removed**: `action.fcurves`, `action.groups`, `action.id_root` no longer exist (verified locally). Actions are layered/slotted: data lives in channelbags per slot. `action_slot.target_id_type` replaces `id_root`. The `action_group` argument became `group_name` (5.0 Python API). Working pattern (verified locally):

```python
import bpy
from bpy_extras import anim_utils

act = bpy.data.actions.new("Whip")
slot = act.slots.new(id_type='OBJECT', name="Bike")       # identifier "OBBike"
ob.animation_data_create()
ob.animation_data.action = act
ob.animation_data.action_slot = slot
cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
fc = cb.fcurves.new("rotation_euler", index=2, group_name="Object Transforms")
fc.keyframe_points.insert(1, 0.0)

# replacement for "for fc in ob.animation_data.action.fcurves":
for fc in anim_utils.animdata_get_channelbag_for_assigned_slot(ob.animation_data).fcurves:
    ...
```

- [ ] `ob.keyframe_insert("location", frame=1)` still works and creates the action, a slot (`OB<name>`), one layer and a `KEYFRAME` strip (verified locally).
- [ ] 5.2: preference "Only Insert Available" is on in factory settings (`preferences.edit.use_keyframe_insert_available == True`, verified locally). Python `keyframe_insert()` on a fresh object still created F-Curves (verified locally); UI keying behaves differently from 4.x.
- [ ] Bone selection and visibility moved to pose bones (5.0): `Bone.select`, `select_head`, `select_tail` removed; `PoseBone.select` and `PoseBone.hide` exist; `Bone.hide` now affects edit bones (verified locally). Animated bone visibility F-Curves need `anim.version_bone_hide_property` (exists, verified locally).
- [ ] Drivers created from Python no longer get an F-Curve modifier; they get two keyframes (5.0 Animation & Rigging).
- [ ] `ANIM_OT_convert_legacy_action` removed (5.1). `action.layer_prev`/`layer_next` removed (5.0).
- [ ] "Copy Global Transform" is built in; its add-on properties moved to `scene.tool_settings` (5.0).
- [ ] FBX and BVH imports name their action slots "Slot" (5.0).
- [ ] 5.1: action and shape key evaluation is much faster ([5.1 Animation](https://developer.blender.org/docs/release_notes/5.1/animation_rigging/)), which helps long rider animations.

### 1.6 Custom properties (IDProperties)
- [ ] `bpy.props` data is stored apart from user custom properties (5.0). `scene['cycles']` raises `KeyError` (verified locally). Use `obj.property_unset('cycles')` instead of `del obj['cycles']`; versioning code uses `obj.bl_system_properties_get()` (exists, verified locally).
- [ ] A `set` callback without `get` is now an error; read-only props use the `READ_ONLY` option; `get_transform`/`set_transform` are new (5.0).
- [ ] 5.2: IDProperty nesting is capped at 1024 levels.

### 1.7 Geometry Nodes
- [ ] **5.2: Geometry Nodes modifier inputs are RNA properties, not IDProperties.** `mod["Socket_2"]` raises `TypeError: this type doesn't support IDProperties` (verified locally). Use:

```python
inp = getattr(mod.properties.inputs, socket.identifier)   # e.g. "Socket_2"
inp.value = 3.0                    # was mod["Socket_2"] = 3.0
inp.type = 'ATTRIBUTE'             # was mod["Socket_2_use_attribute"] = True
inp.attribute_name = "wear"        # was mod["Socket_2_attribute_name"]
getattr(mod.properties.outputs, out_identifier).attribute_name = "out"
```
  Each input exposes `name`, `value`, `type`, `attribute_name` (verified locally, 5.2.0 and 5.2.3).
- [ ] 5.2: Compare and Random Value socket identifiers changed. On 5.2.3 Compare has dynamically typed `A`/`B`; Random Value has `Min`, `Max`, `ID`, `Seed` in and `Value` out (verified locally). 4.x scripts using `A_VEC3`, `Min_001` and similar break.
- [ ] 5.0: Random Value produces different numbers for the same seed, so scatter layouts differ from 4.x. The `id` attribute is a generic attribute now.
- [ ] 5.2: meshes created from scratch in Geometry Nodes no longer take the object's mesh name.
- [ ] 5.1 and 5.2: node tool assets must be re-saved in the new version.
- [ ] 5.0 Geometry-Nodes-based modifiers: Array, Scatter on Surface, Instance on Elements, Randomize Instances, Curve to Tube, Geometry Input. They are node group assets in `datafiles/assets/nodes/geometry_nodes_essentials.blend`, along with `Smooth by Angle`, `Capture Rest Geometry` and others (verified locally). The classic Array modifier remains.
- [ ] Volume grid nodes (5.0, 5.1): Points to SDF Grid, Field to Grid, Grid to Mesh and filters. `GeometryNodePointsToSDFGrid`, `GeometryNodeFieldToGrid` exist (verified locally).
- [ ] 5.2: new Lists data type, Mesh Bevel node (`GeometryNodeMeshBevel`), Merge Points, Transfer Attributes, Set NURBS Order/Weight ([5.2 Geometry Nodes](https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/)).
- [ ] 5.2 experimental physics: assets `Cloth Dynamics (Experimental)`, `Hair Dynamics`, `Collider`, `Set Effector`, `Custom Force`, `Custom Effector` in `geometry_nodes_dynamics_assets.blend`, built on `GeometryNodeXPBDSolver` (verified locally). The notes warn the design may still break between releases ([5.2 Physics](https://developer.blender.org/docs/release_notes/5.2/physics/)).

### 1.8 Compositor
- [ ] `scene.node_tree` is gone. Create a `'CompositorNodeTree'` node group and assign it to `scene.compositing_node_group`. The Composite node is gone too: the Group Output's first Color input is the result. `scene.use_nodes` is deprecated (always True). Verified with a headless render that wrote the file (verified locally):

```python
ng = bpy.data.node_groups.new("Comp", 'CompositorNodeTree')
scene.compositing_node_group = ng
ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
rl = ng.nodes.new('CompositorNodeRLayers')
out = ng.nodes.new('NodeGroupOutput')
ng.links.new(rl.outputs['Image'], out.inputs[0])
```
- [ ] Node options became menu input sockets. Example: `CompositorNodeGlare.glare_type` does not exist; set `glare.inputs['Type'].default_value = 'Fog Glow'`. The value is the UI label, not an enum identifier (verified locally). Denoise node inputs: `Image`, `Albedo`, `Normal`, `HDR`, `Prefilter` (default `'Accurate'`), `Quality` (default `'Follow Scene'`) (verified locally).
- [ ] File Output node: `base_path`, `file_slots`, `layer_slots` removed. Now `directory`, `file_name`, `file_output_items`, `format`, `save_as_render`, `use_file_extension` (verified locally).
- [ ] File Output appends frame numbers only for animation renders. `bpy.ops.render.render(animation=False)` no longer adds one: use `####` in the name, or `animation=True, frame_start=, frame_end=` (both parameters exist, verified locally) ([5.0 Compositor](https://developer.blender.org/docs/release_notes/5.0/compositor/)).
- [ ] Renames: Z Combine is Depth Combine; Alpha Over inputs are Background/Foreground; Color Correction "Lift" is "Offset"; `CompositorNodeGamma` replaced by `ShaderNodeGamma`; Bokeh Blur Size is in pixels; Color Balance LGG works in linear (5.0).
- [ ] 5.1: the Mix node's Mix mode also mixes alpha ([5.1 Compositor](https://developer.blender.org/docs/release_notes/5.1/compositor/)).
- [ ] **`scene.render.compositor_device` defaults to `'GPU'`** (verified locally, 5.2.0 and 5.2.3). On this GPU-less server compositing went through EGL/llvmpipe (EGL_BAD_MATCH warnings) and still finished. Set `'CPU'` explicitly in headless render scripts.

### 1.9 Image and video output
- [ ] Set `image_settings.media_type` **before** `file_format`. With `media_type='IMAGE'`, `file_format='FFMPEG'` raises an error (verified locally). `media_type`: `IMAGE`, `MULTI_LAYER_IMAGE` (selects `OPEN_EXR_MULTILAYER`), `VIDEO` (selects `FFMPEG`) (verified locally).
- [ ] Image formats on 5.2.3: `AVIF` (5.1), `JPEG`, `OPEN_EXR`, `PNG`, `WEBP`, `BMP`, `CINEON`, `DPX`, `IRIS`, `JPEG2000`, `HDR`, `TARGA`, `TARGA_RAW`, `TIFF`. EXR codecs include `HTJ2K` (5.1), `DWAA`, `DWAB`, `PIZ`, `ZIP` (verified locally).
- [ ] Multilayer EXR writes multi-part files by default; an "Interleave" option restores the old layout for older tools (5.0).
- [ ] FFmpeg codecs available: `AV1`, `H264`, `H265`, `PRORES`, `DNXHD`, `FFV1` and more (verified locally). A system `ffmpeg` is also installed at `/usr/bin/ffmpeg` (verified locally).

### 1.10 Mesh, modelling, UV
- [ ] Boolean solver `'FAST'` is now `'FLOAT'`; options `FLOAT`, `EXACT`, `MANIFOLD` (verified locally).
- [ ] UV selection is shared across UV maps: `MeshUVLoopLayer.vertex_selection`/`edge_selection` and `BMLoopUV.select`/`select_edge` removed; UV pin attribute is not created on access, use the `_ensure()` functions (5.0 Python API).
- [ ] Merge by Distance has a "Centroid" option on by default (5.0 Modeling).
- [ ] `mesh.radial_symmetry` holds sculpt radial symmetry (verified locally).
- [ ] Attribute references stay valid when other attributes are added or removed (5.0 Modeling).
- [ ] mathutils types expose float32 buffers, and matrices are non-contiguous (5.0). Check numpy code that wraps `Vector`/`Matrix` memory. Bundled numpy is 2.3.4 (verified locally).

### 1.11 GPU and drawing
- [ ] `bgl` removed: `import bgl` fails (verified locally). `Image.bindcode` removed (verified locally). Use the `gpu` module and `gpu.texture.from_image()`.
- [ ] Creating shaders directly from GLSL source was removed (5.0).

### 1.12 Import and export
- [ ] Collada (.dae) removed: `wm.collada_export`/`collada_import` absent (verified locally).
- [ ] FBX: the C++ importer `bpy.ops.wm.fbx_import` is the default; `import_scene.fbx` is the legacy Python one. Both present (verified locally).
- [ ] glTF exporter 5.2 (add-on version 5.2.41, verified locally): meshopt compression (`export_meshopt_compression_enable`, `export_meshopt_extension` = `EXT_meshopt_compression` or `KHR_meshopt_compression`), Draco (`export_draco_mesh_compression_enable`), image format `AUTO`/`JPEG`/`WEBP`/`NONE`, point clouds, `KHR_materials_iridescence` and `KHR_materials_dispersion` ([5.2 Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.2/pipeline_io/)). Draco and meshopt both exported headless (verified locally, 5.2.0 and 5.2.3 expose the options).
- [ ] USD operator renames (5.0): `import_subdiv` is `import_subdivision`, `attr_import_mode` is `property_import_mode`, `export_textures` replaced by `export_textures_mode`.
- [ ] Alembic: `Scene.alembic_export` API and `visible_objects_only` removed (5.0).

### 1.13 Physics and caches
- [ ] Point caches always use ZSTD; LZO/LZMA caches from older files must be deleted and re-baked; the compression property is gone (verified locally) ([5.0 Physics](https://developer.blender.org/docs/release_notes/5.0/physics/)).
- [ ] Smoke vorticity no longer scales with time scale/time step, so results change when those are non-default (5.0).
- [ ] Classic cloth bakes headless with `bpy.ops.ptcache.bake(bake=True)` inside `bpy.context.temp_override(scene=..., active_object=..., point_cache=...)`; Mantaflow bakes with `bpy.ops.fluid.bake_all()` under a similar override (verified locally, see 3.3 and 3.6).

### 1.14 Core, files, Python runtime
- [ ] Python 3.13 since 5.1 (3.13.13 on 5.2.3 and 5.2.0, verified locally). Libraries follow VFX Platform 2026: OpenColorIO 2.5, OpenEXR 3.4, OpenVDB 13.0 ([5.1](https://developer.blender.org/docs/release_notes/5.1/)).
- [ ] .blend header changed in 5.0: only 4.5 LTS and newer can open 5.x files. Compression on save is the default (`preferences.filepaths.use_file_compression == True`, verified locally). Data-block names can be 255 bytes (a 200-character name kept, verified locally) and are truncated in 4.5.
- [ ] Some bundled modules became private (5.0): `rna_info`, `bl_ui_utils`, `keyingsets_utils`, `graphviz_export` and others.
- [ ] Additions worth using: `bpy.data.file_path_foreach()` (5.0, gains `EXPAND_*` options in 5.2), `bpy.data.all_ids` (5.2), `bpy.app.cachedir` (5.1), `bpy.app.handlers.exit_pre` (5.1), slice steps on mathutils types (5.2), `render.render(frame_start=, frame_end=)` (5.0).
- [ ] Paint/sculpt API renames (5.0 to 5.2: `sculpt_tool` is `sculpt_brush_type`, automasking moved to `mesh_automasking_settings`, stroke flags folded into `brush.stroke_method`). Only matters if we script sculpting.

### 1.15 Changed earlier in 4.x (only if porting older scripts)
- [ ] 4.0 Principled v2 names: `Subsurface Weight`, `Specular IOR Level`, `Coat Weight`, `Sheen Weight`, `Transmission Weight`, `Emission Color` (present on 5.2.3, verified locally). Metallic edge tint uses `Specular Tint` with the F82 tint model ([4.0 Shading](https://developer.blender.org/docs/release_notes/4.0/shading/)).
- [ ] 4.1: `mesh.use_auto_smooth`, `auto_smooth_angle`, `calc_normals`, `calc_normals_split` gone; use `mesh.set_sharp_from_angle(angle=...)`, `mesh.corner_normals`, `mesh.normals_domain`, or the "Smooth by Angle" asset (verified locally). `face_maps` gone (verified locally).
- [ ] 4.2: EEVEE Next (material `surface_render_method`), extensions platform; many add-ons moved online. Rigify, glTF, FBX, Node Wrangler stayed bundled (5.2.3 core add-ons: `cycles`, `hydra_storm`, `io_anim_bvh`, `io_curve_svg`, `io_mesh_uv_layout`, `io_scene_fbx`, `io_scene_gltf2`, `node_wrangler`, `pose_library`, `rigify`, `ui_translate`, `viewport_vr_preview`, verified locally).
- [ ] 4.4: slotted actions introduced (fully enforced in 5.0, see 1.5).

### 1.16 5.2.0 (Damien) vs 5.2.3 (server)
- Identical on everything checked (verified locally on both): Principled socket list including `Thin Wall`, GN `mod.properties`, glTF Draco and meshopt options, subsurface methods, compositor device default, Python 3.13.13.
- A .blend saved by 5.2.3 with a baked cloth cache opened in 5.2.0 with the cache intact (verified locally). Keep using `blender-5.2.0` for the final delivery check, as `CLAUDE.md` requires.

---

## 2. Recommended toolchain

| Tool | Purpose | Licence | Works headless in 5.2? | Source |
|---|---|---|---|---|
| Blender 5.2.3 LTS (5.2.0 for checks) | Everything | GPL | Yes (verified locally) | [blender.org](https://www.blender.org/download/) |
| Cycles, CPU, with OpenImageDenoise, OSL, Embree | Final and preview renders | Apache 2.0 | Yes. `_cycles.with_openimagedenoise`, `with_osl`, `with_embree` all True; device list shows only CPU (verified locally) | [Cycles manual](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html) |
| MPFB 2.0.18 (MakeHuman for Blender) | Rider body from parameters, built-in rigs including Rigify | Code GPL-3.0-or-later; assets CC0 1.0 | **Yes (verified locally):** installed from the extensions platform into an isolated user folder, created a male base mesh, solved the height macro to 1.85 m, added `rigify.human`, generated the rig. Needs Blender 4.2+, no max version | [extensions.blender.org/add-ons/mpfb](https://extensions.blender.org/add-ons/mpfb/), [GitHub](https://github.com/makehumancommunity/mpfb2), [assets licence](https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.ASSETS.md) |
| Rigify (bundled) | Production rig with IK/FK limbs, IK hand and foot controls | GPL | Yes. Bundled in `addons_core`, not enabled by default: `addon_utils.enable("rigify")`, then `bpy.ops.pose.rigify_generate()` (verified locally) | [Rigify manual](https://docs.blender.org/manual/en/latest/addons/rigify/index.html) |
| CloudRig 2.2.31 | Alternative rig generator (Blender Studio) | GPL-3.0-or-later | Not tested. Listed for Blender 5.0 to 6.0 | [extensions API listing](https://extensions.blender.org/) |
| Anny (NAVER LABS Europe) | Parametric human model built on MakeHuman/MPFB2 assets | Apache 2.0 (optional SMPL-X topology is non-commercial) | Not a Blender add-on (Python package); not tested | [blog](https://europe.naverlabs.com/blog/anny-a-free-to-use-3d-human-parametric-model-for-all-ages/), [PyPI](https://pypi.org/project/anny/) |
| CharMorph | Alternative character creator (MB-Lab successor) | Code GPL; MB-Lab base AGPL; other bases CC | Latest found release targets 4.4. Not recommended | [GitHub](https://github.com/Upliner/CharMorph) |
| Cloth modifier (built in) | Jersey and pants secondary motion | GPL | Yes: pinned, self-colliding 6.5k-vertex cloth baked 60 frames in 16.2 s (verified locally) | [Cloth shape](https://docs.blender.org/manual/en/latest/physics/cloth/settings/shape.html), [collisions](https://docs.blender.org/manual/en/latest/physics/cloth/settings/collisions.html) |
| Cloth Dynamics (Experimental), GN, 5.2 | XPBD cloth with pinning, tearing | GPL (bundled asset) | Assets present (verified locally); simulation not tested. Experimental | [5.2 Physics](https://developer.blender.org/docs/release_notes/5.2/physics/) |
| GarmentCode / pygarment | Parametric sewing patterns for jersey and pants panels | MIT (v1.0.0; check current licence file) | Outside Blender; no Blender integration found. Import panels as SVG with bundled `io_curve_svg` | [GitHub](https://github.com/maria-korosteleva/GarmentCode), [PyPI](https://pypi.org/project/pygarment/) |
| Poly Haven + API | HDRIs, textures, models | Assets CC0; API free incl. commercial, needs a unique User-Agent/Referer, "Powered by Poly Haven" credit only for apps built on the live API | Yes: plain HTTPS from Python/curl (verified locally) | [licence](https://polyhaven.com/license), [API](https://github.com/Poly-Haven/Public-API), [API ToS](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md) |
| ambientCG + API v2 | Textures (rubber, plastic, leather, fabric, ground, rust) | CC0 | Yes: `/api/v2/full_json` queries (verified locally) | [API docs](https://docs.ambientcg.com/api/) |
| physicallybased.info API | Measured base colour, IOR, F82 tint | CC0 1.0 | Yes: `https://api.physicallybased.info/v2/materials` (verified locally) | [repo](https://github.com/AntonPalmqvist/physically-based-api) |
| Sun Position 4.4.0 (extension) | Sun direction from place, date, time (KOTW day shot) | GPL-3.0-or-later | Not tested. Blender 4.2+ | [extensions platform](https://extensions.blender.org/) |
| Mantaflow (built in) | Dust clouds | GPL (part of Blender) | Yes: smoke bake res 64 in 7.0 s, res 128 in 89.5 s for 60 frames (verified locally) | [Fluid manual](https://docs.blender.org/manual/en/latest/physics/fluid/index.html) |
| Geometry Nodes simulation zones | Roost particles, clods, chain motion | GPL | Bake operators present (`object.simulation_nodes_cache_bake`, `geometry_node_bake_single`, verified locally); simulation not tested | [Simulation Zone](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/simulation_zone.html) |
| glTF exporter (bundled) | GLB for the web viewer | Apache 2.0 | Yes: Draco and meshopt GLBs written headless (verified locally) | [glTF manual](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html) |
| glTF Transform CLI 4.5.1 | Resize textures, KTX2/WebP/AVIF, meshopt, `optimize` | MIT | Node 22 is on the server (verified locally); CLI not installed or tested | [gltf-transform.dev/cli](https://gltf-transform.dev/cli) |
| three.js 0.186.1 | Web viewer | MIT | Browser side. GLTFLoader 0.186.1 supports Draco, EXT/KHR meshopt, Basis/KTX2, WebP, AVIF, clearcoat, sheen, transmission, anisotropy, iridescence, dispersion (checked in source) | [npm](https://www.npmjs.com/package/three), [jsDelivr](https://cdn.jsdelivr.net/npm/three@0.186.1/) |
| model-viewer 4.4.0 | Simpler drop-in viewer alternative | Apache 2.0 | Browser side; needs three ^0.183.0 as peer | [modelviewer.dev](https://modelviewer.dev/), [npm](https://www.npmjs.com/package/@google/model-viewer) |
| ahujasid/blender-mcp | LLM control of a GUI Blender | MIT | No (needs the GUI add-on panel and a socket server). Not useful here | [GitHub](https://github.com/ahujasid/blender-mcp) |
| SheepIt render farm | Free distributed rendering | Free, points based | Blender 5.2 available since 2026-07-15 per its news. Rules in 5.4 | [FAQ](https://www.sheepit-renderfarm.com/faq), [news](https://www.sheepit-renderfarm.com/news) |

---

## 3. Notes per area

### 3.1 Human body from measurements (MPFB)
- MPFB code is GPL-3.0-or-later; its asset licence file is CC0 1.0 ([LICENSE.ASSETS.md](https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.ASSETS.md)). Anny's package notes describe the MPFB2-derived MakeHuman assets as CC0 1.0 ([PyPI](https://pypi.org/project/anny/)). Third-party community assets (clothes, hair) can carry other licences; check each one. We model Leatt gear ourselves anyway.
- Install headless (verified locally, isolated user folder):
  `BLENDER_USER_RESOURCES=<dir> blender -b --factory-startup --command extension install-file -r user_default -e add-on-mpfb-v2.0.18.zip`.
  Then run scripts without `--factory-startup`, with the same `BLENDER_USER_RESOURCES`, so the extension loads. Module name: `bl_ext.user_default.mpfb`.
- Scripted creation (verified locally): `HumanService.create_human(macro_detail_dict=..., scale=0.1)` makes a metre-scale base mesh (19,158 vertices). Macros: `gender, age, muscle, weight, proportions, height, cupsize, firmness, race{asian, caucasian, african}`, each 0 to 1. Set with `HumanObjectProperties.set_value(name, value, entity_reference=basemesh)` and then `TargetService.reapply_macro_details(basemesh)`.
- Height: with gender 1.0, age 0.5, muscle 0.6, weight 0.5, the default male measured 1.729 m. A binary search on the `height` macro reached **1.850 m at height = 0.5945** (verified locally, measured on the `body` vertex group, sole to crown). Re-solve after changing other macros, because they change stature too. Damien's photos will drive proportions (arm span, inseam, shoulder width) later.
- Rig: `HumanService.add_builtin_rig(basemesh, "rigify.human")` adds a metarig fitted to the body with weights; `bpy.ops.pose.rigify_generate()` then produced `Human.rigify` with 930 bones (verified locally).

### 3.2 Rigging and IK (hands on bars, feet on pegs)
- Rigify generated controls include `hand_ik.L/R`, `foot_ik.L/R`, `foot_heel_ik`, `toe_ik`, pole targets `upper_arm_ik_target.L/R` and `thigh_ik_target.L/R` (verified locally).
- IK/FK switch: custom property `IK_FK` on `upper_arm_parent.L/R` and `thigh_parent.L/R`; **0.0 = IK, 1.0 = FK** (the IK constraint influence is driven as `1 - IK_FK`; default 0.0; read in Rigify source `rigs/limbs/limb_rigs.py`). Also `IK_parent`, `pole_parent`, `IK_Stretch` and `FK_limb_follow` (verified locally).
- Hands on handlebars: put an empty (or bone) at each grip on the bike's handlebar and give `hand_ik.L/R` a Child Of constraint to it ([Child Of](https://docs.blender.org/manual/en/latest/animation/constraints/relationship/child_of.html)). During the whip the hands then follow the bars automatically. Keep `IK_Stretch` at 0 so arms never exceed their length; check reach by script.
- Feet on pegs: same pattern for `foot_ik.L/R`, constrained to empties on the footpegs. Animate the constraint influence for any foot-off moments in Damien's style.
- Pole targets control elbows and knees. Animate them for the elbows-up attack position and knee grip.
- Alternatives: CloudRig (GPL, Blender 5.0 to 6.0, not tested). Auto-Rig Pro is paid, so it is outside this list.

### 3.3 Cloth for jersey and pants
- Built-in cloth (verified headless): pin with a vertex group (`settings.vertex_group_mass`, weight = pin strength), `pin_stiffness`; `use_sewing_springs` with a non-zero `sewing_force_max` (the manual warns zero can explode); `shrink_min` for sewing; `use_dynamic_mesh` lets armature and shape-key changes above the Cloth modifier update the rest shape every frame; `rest_shape_key` starts from a pre-draped key ([Shape](https://docs.blender.org/manual/en/latest/physics/cloth/settings/shape.html)).
- Collision: the body needs a Collision modifier placed **after** the Armature modifier ([Collision](https://docs.blender.org/manual/en/latest/physics/collision.html)). Cloth `collision_settings.distance_min` defaults to 0.015 m (verified locally), too loose for a fitted jersey. Use a few millimetres with collision thickness to match (estimate; tune on tests). Turn on self-collision for close-ups (manual tip). The troubleshooting order in the manual: raise Distance, then raise Quality and Collision Quality, then fix frames in Edit Mode ([Collisions](https://docs.blender.org/manual/en/latest/physics/cloth/settings/collisions.html)).
- Defaults on 5.2.3 (verified locally): quality 5, mass 0.3 kg, tension/compression 15, shear 5, bending 0.5, air damping 1.0, collision quality 2.
- Suggested workflow (recommendation): build pattern panels (GarmentCode or hand-drawn, imported as SVG), sew them around the 185 cm body in a rest pose, apply as the garment mesh, bind to the rig with weights transferred from the body (Data Transfer modifier), then run cloth only for secondary motion. Pin waist, collar, cuffs, and the pants areas under knee braces and boots. The whip has fast accelerations: expect to raise Quality steps. The manual notes higher Quality helps fast-moving collisions.
- Speed reference: 6,561-vertex grid, pinned edge, self-collision, quality 8, 60 frames: 16.2 s bake on this server (verified locally). Garment meshes at 20k to 40k vertices with self-collision will take minutes per shot, which is fine.
- Fabric detail ("fabric weave" in `PROJECT.md`): Poly Haven `bi_stretch` (tagged polyester, real size about 26 cm square), `jersey_melange`, `cotton_jersey`; ambientCG `Fabric0xx` sets. Use Sheen for the soft rim on polyester (see section 4).
- 5.2 experimental GN Cloth Dynamics (XPBD) is worth a test but not a production dependency, since the notes say it may break.

### 3.4 Textures, HDRIs and scripted download
**Scripted download (verified locally):**
- Poly Haven: `GET https://api.polyhaven.com/assets?t=hdris&c=<category>`, `GET https://api.polyhaven.com/info/<id>`, `GET https://api.polyhaven.com/files/<id>` returns per-resolution URLs and md5. Example: `dirt_bike_track_01` 4K `.exr` is 20.2 MB, `.hdr` 25.8 MB. Send a unique User-Agent (API ToS). Texture entries include real-world `dimensions` in mm, which sets UV scale.
- ambientCG: `GET https://ambientcg.com/api/v2/full_json?type=Material&q=rust&include=downloadData` returns zip links such as `https://ambientcg.com/get?file=Metal063_4K-JPG.zip`.
- Store downloads under `motocross-whip/textures/` through Git LFS, and record asset ID, resolution and md5 in a manifest so scripts can re-fetch them.

**HDRIs (Poly Haven, CC0, all from the API listing on 2026-11-06):**

| Use | HDRI ID | Why | Max res |
|---|---|---|---|
| Day, first choice | `dirt_bike_track_01` | Literally a sunlit dirt bike track: "warm late-morning/afternoon light, partly cloudy sky, high-contrast directional sun, dry dusty terrain and tire marks". Has backplates | 16K |
| Day, clean sky for compositing our own set | `qwantani_noon_puresky`, `kloofendal_43d_clear_puresky` | Clear midday pure skies, no ground to fight our set | 24K |
| Day, arid dirt alternatives | `goegap` (desert dirt, midday, clear), `aarfontein_dirt_road`, `quarry_02`, `dry_cracked_lake` | Dry, high-contrast sun | 16K to 24K |
| Day, stadium context | `orlando_stadium` | Clear midday stadium | 24K |
| Night ambient | `moonless_golf` (clear, stars), `kloppenheim_07_puresky`, `satara_night` | Dark sky fill only | 16K to 24K |

Poly Haven has 61 night HDRIs and none is tagged stadium or floodlight (checked through the API). For the night version, use a dark sky HDRI at low strength and build the stadium floodlights as Cycles spot/area lights (IES profiles if available) aimed at the ramp and landing. The match to KOTW 2025 lighting comes from `research/kotw-2025.md` when written.

**Material textures:**

| Need | Poly Haven IDs (CC0) | ambientCG IDs (CC0) |
|---|---|---|
| Dirt, soil, ruts | `muddy_tracks` (tyre tracks, 2.25 m), `brown_mud_dry`, `brown_mud_02`, `dry_mud_field_001`, `red_dirt_mud_01`, `aerial_mud_1` (8 m, ruts) | `Ground0xx` series, e.g. `Ground109`, `Ground106` |
| Gravel, stones | `gravel_road`, `gravelly_sand`, `sandy_gravel`, `rocky_trail` | `Gravel043`, `Gravel023`, `Gravel040` |
| Rusted steel | `rusty_metal_02`, `rusty_metal_sheet`, `rusty_corrugated_iron`, `metal_plate_02` | `Rust009`, `Metal063`, `CorrugatedSteel007A` |
| Rubber | `rubber_tiles` (flooring, limited use) | `Rubber001` to `Rubber004` |
| Plastic | none in the Poly Haven catalogue | `Plastic006` to `Plastic018B` |
| Brushed metal | none | `Metal009`, `Metal011`, `Metal012`, `Metal051A` |
| Leather | `brown_leather`, `leather_white`, `fabric_leather_01` | `Leather026` to `Leather039` |
| Fabric | `bi_stretch` (polyester), `jersey_melange`, `cotton_jersey`, `scuba_suede` | `Fabric0xx` series |

Anodised aluminium, chrome, clear-coated paint and carbon fibre are better built procedurally from the values in section 4 plus scratch and weave maps. No dedicated carbon fibre texture was found in either catalogue.

### 3.5 Tyres, spokes, chain, decals
- **Knobby tyres**: model one tread pitch (one row of knobs plus the carcass strip) flat, repeat it with the Array modifier, then wrap it into a ring with Simple Deform (Bend, 360 degrees) or a Curve modifier on a circle ([Array](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/array.html), [Simple Deform](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/simple_deform.html), [Curve](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/curve.html)). The GN equivalent is Instance on Points on a Curve Circle with "Align Rotation to Vector" on the tangent, which also allows per-knob wear from a seeded Random Value. Add mould lines, sidewall lettering and vent spews as normal or displacement maps; adaptive subdivision is production-ready in 5.0.
- Sizes from dealer spec listings for the 2026 CRF250R: front 80/100-21, rear 100/90-19 ([De Wildt Marine listing](https://dewildtmarine.com/helper/printad/adId/38772899)), Pirelli Scorpion MX32 ([Autotrader](https://motorcycles.autotrader.com/motorcycles/2026/honda/crf250r/201816181), [Thompson's](https://www.thompsonsmotorsports.com/inventory/v1/Current/Honda/Motorcycle/Competition/CRF250R/Base---25016651)). Nominal outside diameters from the size code: front 21 in (533.4 mm) + 2 x 80 mm = 693.4 mm; rear 19 in (482.6 mm) + 2 x 90 mm = 662.6 mm. Size-code arithmetic only: measure Damien's tyres and check against `research/crf250r-2026.md`.
- **Spoke wheels**: one spoke (J-bend head, nipple) modelled once, then instanced at the hub flange holes with GN or an Array with an object offset; set the cross pattern with a rotation offset. Take spoke count and lacing from Damien's photos.
- **Chain**: #520 chain, 13T front / 50T rear for the 2026 CRF250R ([MotorcycleDB](https://www.motorcycledb.com/CRF250R_2026/69204)). 520 means 5/8 in pitch (15.875 mm) and 1/4 in roller width ([USA Roller Chain](https://usarollerchain.com/products/520-chain-10ft)). Sprocket pitch radius = p / (2 sin(180 deg / N)): **13T = 33.17 mm, 50T = 126.41 mm** (computed). Build one inner and one outer link, then either (a) Array (Fit Curve) + Curve modifier on a closed path around both sprockets, sliding the object along the deform axis to animate, or (b) GN: Resample Curve with count = link count (even integer), Sample Curve at factor + offset, Instance on Points alternating inner and outer link with `index % 2`. Drive the offset from rear wheel rotation: chain speed = rear sprocket angular speed x 126.41 mm.
- **Decals and sticker kit**: draw the kit as vector art, export high-resolution PNG with alpha, and lay out the plastics' UV islands like the flat die-cut shapes so the art maps one to one. For "sticker edges", make each decal a separate thin shell (duplicate the faces, Solidify by the film thickness measured from a real kit, Shrinkwrap to the plastic ([Shrinkwrap](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/shrinkwrap.html))). That gives a real edge that catches light and can lift or scuff. Material values in section 4. The extensions platform has decal tools (for example "[BAM] Decalit", GPL, Blender 5.0+), not tested.

### 3.6 Dust and roost
| Method | Use | CPU cost here | Notes |
|---|---|---|---|
| Particle system (legacy) with instanced clods and stones | Roost from the rear tyre at takeoff and landing | Low | Emit from the tyre contact patch; collision with ground; bake before rendering (manual note on motion blur) ([Particles](https://docs.blender.org/manual/en/latest/physics/particles/index.html)) |
| GN Simulation Zone | Custom roost: clods that break up, dust points, deterministic, bakeable | Low to medium | Bake via `object.simulation_nodes_cache_bake` (operator present, verified locally) |
| GN points to volume (`Points to Volume`, grid nodes) | Dust puffs from simulated points, no fluid solver | Medium (render is the cost) | Shade with Principled Volume; cheaper than Mantaflow to iterate |
| Mantaflow gas | Billowing dust cloud at landing | 60 frames: res 64 took 7.0 s, res 128 took 89.5 s to bake (verified locally) | Volumes are the most expensive thing to render in Cycles. Keep dust in its own view layer and test render cost early. 5.0 made unbiased volume sampling the default |

Recommendation: GN or particle roost for solid debris (fast, sharp, motion blurred) plus a small number of baked Mantaflow or GN volume puffs, rendered as a separate layer so their samples can be tuned apart from the hero.

---

## 4. Physically based material values

Base colours are **linear Rec.709/sRGB**, the default Blender working space, so they go straight into Principled `default_value` from Python. physicallybased.info values come from its v2 API, which labels them `srgb-linear` (verified locally). For metals, Blender's `Specular Tint` is the F82 edge tint ([4.0 Shading](https://developer.blender.org/docs/release_notes/4.0/shading/), [Principled manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html)), and physicallybased.info publishes an F82 colour. **Roughness values are estimates** unless a source is given: physicallybased.info lists smooth references (roughness 0) for most entries. Final values get matched to Damien's photos.

| Material | Base Color (linear) | Metallic | Roughness | IOR | Other Principled inputs | Basis |
|---|---|---|---|---|---|---|
| MX plastics, polypropylene (fenders, shrouds, side panels) | from photos and brand colour | 0 | 0.2 to 0.35 new, 0.4 to 0.6 scuffed (estimate) | 1.49 | Thin Wall off (solid shells, about 2 to 3 mm, estimate) | PP IOR 1.492 ([physicallybased.info](https://physicallybased.info/)); aftermarket CRF250R kits are polypropylene ([Rtech](https://www.firestormmotorcycles.com.au/honda-crf250r-2022-2024-rtech-white-plastics-kit), Polisport "DGP" glass-fibre PP ([Cycle Gear](https://www.cyclegear.com/parts/polisport-mx-restyle-body-kit-honda-crf250r-crf450r-rwe-r-s-2021-2024))). Honda OEM grade not found |
| ABS parts | from photos | 0 | 0.3 to 0.5 (estimate) | 1.54 | | ABS n_D 1.54 ([US patent 5343317](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5343317)) |
| Glossy vinyl decal (printed PVC film, gloss laminate) | printed artwork | 0 | 0.1 to 0.2 under the coat (estimate) | 1.54 | Coat Weight 1.0, Coat IOR 1.5, Coat Roughness 0.03 to 0.08 (estimate); separate shell for the edge | PVC IOR 1.542 ([physicallybased.info](https://physicallybased.info/)) |
| Anodised aluminium (hubs, triple clamps, bar clamps) | Al (0.916, 0.923, 0.924) | 1 | 0.2 to 0.45 depending on finish (estimate) | n/a | Coat Weight 1.0 with Coat Tint = dye colour models absorption in the oxide layer; Coat IOR 1.6 to 1.76 (estimate: porous anodic oxide sits below sapphire 1.76); Specular Tint = Al F82 (0.910, 0.936, 0.959) | Al values ([physicallybased.info](https://physicallybased.info/)); sapphire 1.762 to 1.778 ([Wikipedia list](https://en.wikipedia.org/wiki/List_of_refractive_indices)); Coat Tint models absorption ([manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html)) |
| Brushed stainless steel (brake discs, exhaust) | (0.669, 0.639, 0.598) | 1 | 0.25 to 0.4 (estimate) | n/a | Specular Tint F82 (0.789, 0.823, 0.870); Anisotropic 0.5 to 0.8 with Tangent along the brushing (estimate) | Stainless Steel ([physicallybased.info](https://physicallybased.info/)) |
| Chrome plating | (0.654, 0.685, 0.701) | 1 | 0.02 to 0.08 (estimate) | n/a | Specular Tint F82 (0.688, 0.728, 0.798) | Chromium ([physicallybased.info](https://physicallybased.info/)) |
| Raw or painted steel (ramp, frame welds) | iron (0.530, 0.513, 0.494) bare | 1 bare, 0 painted | 0.3 to 0.6 bare (estimate) | 1.5 paint | Iron Specular Tint F82 (0.765, 0.767, 0.802); rust via Poly Haven maps | Iron ([physicallybased.info](https://physicallybased.info/)) |
| Tyre rubber | (0.023, 0.023, 0.023) | 0 | 0.7 (measured reference); dust raises it | 1.5 | Dust layer mixed by AO/cavity | Tire ([physicallybased.info](https://physicallybased.info/)) |
| Carbon fibre (epoxy over weave) | very dark, 0.01 to 0.03 (estimate) | 0 | 0.3 to 0.5 under the coat (estimate) | 1.5 | Coat Weight 1.0, Coat Roughness 0.02 to 0.05, Coat IOR 1.5 (estimate); Anisotropic 0.5+ with Tangent from the weave map | Estimate; clear coat like Car Paint 1.5 ([physicallybased.info](https://physicallybased.info/)) |
| Polyester jersey fabric | dye colour | 0 | 0.6 to 0.8 (estimate) | 1.575 | Sheen Weight 0.3 to 1.0, Sheen Roughness 0.3 to 0.5 (estimate); weave normal map; Thin Wall on for single-sheet vented mesh panels (5.2) | PET IOR 1.575 ([physicallybased.info](https://physicallybased.info/), [Wikipedia list](https://en.wikipedia.org/wiki/List_of_refractive_indices)); Sheen "simulates very small fibers" ([manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html)) |
| Nylon (pants shell, Cordura-type panels) | dye colour | 0 | 0.5 to 0.8 (estimate) | 1.53 | Low Sheen | Nylon 6 n_D 1.53 ([Complex Plastics](https://complexplastics.com/chartnyl.htm)) |
| Leather (knee panels, boot and glove patches) | from photos | 0 | 0.4 to 0.7 (estimate) | 1.5 (estimate) | Poly Haven `leather_white`, `brown_leather` normal and roughness maps | Estimate |
| Helmet paint with clear coat | from photos | 0 (metallic paints: separate flake layer) | base 0.3 to 0.5 (estimate) | 1.5 | Coat Weight 1.0, Coat IOR 1.5, Coat Roughness 0.01 to 0.04 (estimate) | Car paint is pigmented basecoat + clear topcoat, IOR 1.5 ([physicallybased.info](https://physicallybased.info/)) |
| Goggle lens (polycarbonate) | (1, 1, 1) clear, tint via Coat Tint or volume absorption | 0 | 0.0 to 0.02 | 1.585 | Transmission Weight 1.0; mirror/iridium coating via Thin Film Thickness (hundreds of nm, tune) and Thin Film IOR; model real thickness, Thin Wall off | PC IOR 1.5848 ([physicallybased.info](https://physicallybased.info/)); Thin Film is Cycles only ([manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html)) |
| Dry dirt reference | sand (0.440, 0.386, 0.231) | 0 | 0.9 | 1.5 | Real colour from KOTW photos | Sand ([physicallybased.info](https://physicallybased.info/)) |
| Skin (for any visible skin) | Skin I to VI, e.g. Skin II (0.799, 0.485, 0.347) | 0 | 0.5 | 1.4 | Subsurface Radius (0.482, 0.169, 0.109) per database; note 5.2 SSS rescale | Skin ([physicallybased.info](https://physicallybased.info/)) |

Calibration aid: physicallybased.info's "Gray Card" (0.18 linear, roughness 0.9) makes a good reference sphere in every lighting test.

---

## 5. Render settings and 4K60 feasibility

### 5.1 Recommended Cycles settings (final 4K frames)
Defaults below are from 5.2.3 (verified locally). Recommendations are starting points to tune on test frames.

| Setting | 5.2.3 default | Recommendation | Why / source |
|---|---|---|---|
| `render.engine` | `BLENDER_EEVEE` | `CYCLES` | Cycles CPU is faster and better here than EEVEE on llvmpipe (`blender-headless` skill) |
| `cycles.samples` | 4096 | 256 to 512 cap, with adaptive sampling | Adaptive sampling stops early where noise is low ([Sampling](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html)) |
| `cycles.adaptive_threshold` | 0.01 | 0.01 hero shots, 0.02 tests | Typical 0.1 to 0.001, lower is cleaner (manual) |
| `cycles.time_limit` | 0 | Set per frame as a safety cap | Does not include pre-render time (manual) |
| Denoiser | OIDN, Albedo+Normal, prefilter Accurate, quality High | Keep | OIDN "typically provides the highest quality" (manual). `denoising_use_gpu` is False here |
| Two-stage denoise option | n/a | Render multilayer EXR with denoising data, then `bpy.ops.cycles.denoise_animation` | Operator exists; needs denoising passes and multilayer EXR output (verified locally) |
| Light paths | max 12, diffuse 4, glossy 4, transmission 12, transparent 8, clamp indirect 10 | Day: diffuse 3, glossy 4, transmission 8; caustics off unless the goggle lens needs them (estimate, A/B test on one frame) | Fewer bounces trade accuracy for speed ([Light Paths](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/light_paths.html)) |
| `cycles.use_light_tree` | True | Keep (important for the night version with many floodlights) | |
| `cycles.use_guiding` | False | Try True for the night version | Path guiding is CPU only and helps hard-to-reach light (manual) |
| Motion blur | off, shutter 0.5, position CENTER | On, `motion_blur_shutter = 0.5` (180 degrees), CENTER | Shutter is in frames ([Motion Blur](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/motion_blur.html)) |
| `object.cycles.motion_steps` | 1 | 3 to 5 on wheels, sprockets, chain, rotating parts | Curved blur for rotation (estimate on count) |
| Deform blur | on per object | Keep on for rider, cloth, suspension | Bake all simulations first (manual note) |
| `render.use_persistent_data` | False | True for animation | Keeps render data between frames ([Performance](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/performance.html)). Watch the 15 GB RAM |
| Texture cache (5.2) | off | On with auto generate when texture count grows | Cuts memory and startup time (5.2 Cycles) |
| `render.compositor_device` | GPU | CPU | No GPU here (1.8) |
| Colour | AgX, look None | AgX with `'AgX - Base Contrast'` or `'AgX - Medium High Contrast'` for the photoreal grade; `Khronos PBR Neutral` or `Standard` when checking brand colours | Valid names in 1.3 |
| Output | PNG 8-bit | OpenEXR half float (`color_depth='16'`), DWAA or PIZ, multilayer only when passes are needed; encode video afterwards with ffmpeg | Frame files survive crashes and resume; SheepIt requires compressed EXR |
| Resume-safe frames | `use_overwrite` True, `use_placeholder` False | `use_overwrite=False`, `use_placeholder=True` | Several processes or restarts skip finished frames |
| Film filter | Blackman-Harris 1.5 | Keep | |

Example command (5.2 CLI, order matters):
`blender -b shot.blend --python-exit-code 1 -o /abs/renders/shot01/frame_#### -F OPEN_EXR -s 1 -e 720 -a`

### 5.2 Measured timings on this server (verified locally)
Test scene: 4 spheres (Principled with coat, metal, rubber-like, coat), a 40 m ground plane with noise bump, multiple-scattering Sky texture, AgX, 128 max samples, adaptive threshold 0.01, OIDN.

| Resolution | Samples | Motion blur | Time per frame |
|---|---|---|---|
| 960 x 540 | 128 | off | 25.2 s |
| 960 x 540 | 128 | on, 0.5 shutter | 30.0 s (+19%) |
| 1920 x 1080 | 128 | off | 103.8 s |
| 3840 x 2160 | 128 | off | 420.0 s (7.0 min); short probes ran in parallel, so slightly pessimistic |

Time scales almost linearly with pixel count (4x per resolution doubling). Default-cube reference from the `blender-headless` skill: 1080p, 64 samples, 11.6 s.

### 5.3 Feasibility of 4K60 on this machine
- Frames per camera version: 8 to 12 s at 60 fps = **480 to 720 frames** (`PROJECT.md` decision 11). Several camera versions multiply this.
- Floor from the trivial test scene: 7 min x 480 to 720 frames = **56 to 84 hours per camera version**.
- The real shot (high-poly bike, 185 cm rider with cloth, textured set, dust volumes, motion blur, DOF) will cost several times more per frame. That is an estimate until we measure a representative frame. At an assumed 30 min per frame, one 720-frame version takes 360 hours (15 days) of continuous rendering.
- Conclusion: this server is fine for look development, stills, low-resolution animation previews and final 4K checkpoints. A final 4K60 animation with several camera versions needs a render farm or GPU time. Measure one representative 4K frame as soon as the scene exists, then decide.

### 5.4 Render farms and cloud
**SheepIt (free, community)** ([FAQ](https://www.sheepit-renderfarm.com/faq), [news](https://www.sheepit-renderfarm.com/news), [home](https://www.sheepit-renderfarm.com/)):
- Free; you earn points by rendering for others. Points per frame depend on render time scaled to a reference machine (Intel Core i5-9600, 6 cores, and RTX 3060 for GPU).
- "Blender 5.2 is available!" posted 2026-07-15; home page says Cycles, EEVEE and Workbench are included. About 440 machines were online when checked.
- Limits: 2,048 MB per project (zip with relative paths; split large simulation caches); OpenEXR output max 4096 x 2160 (our 3840 x 2160 fits) and EXR compression required; at most 3 projects rendering at once; **owners cannot run their own scripts**, so bake and apply everything procedural into the .blend first; fluid caches discouraged because of size; no NSFW.
- Per-frame time limit: not stated in the current FAQ. An older news post mentioned up to 20 minutes per frame on the reference machine, which may be out of date.
- Privacy: rendering happens on volunteers' machines, so they receive the project files. This is an inference from how a distributed farm works; the FAQ does not address it. `PROJECT.md` says real logos and branding are private for now, so **ask Damien before sending the project to SheepIt**.
- AMD and Apple GPU support news (2026-08-10) supersedes the FAQ line about AMD support ending in 2023.

**Paid options:** Super Renders Farm states support for Blender up to 5.2 ([its page](https://superrendersfarm.com/blender-render-farm)). GarageFarm, RebusFarm, Ranch Computing and iRender support Blender, but I found no statement of 5.2 support; confirm before uploading ([GarageFarm](https://garagefarm.net/blender-render-farm), [RebusFarm](https://rebusfarm.net/3d-software/blender-render-farm)). Rented GPU servers (RunPod, Vast.ai and similar) can run the same headless scripts with `cycles.device='GPU'`; no prices or speeds verified here.

---

## 6. Matching real motorsport camera work

**Shutter**
- Shutter speed = (shutter angle / 360) / fps ([RED shutter angle tutorial](https://www.reddigitalcinema.com/red-101/shutter-angle-tutorial)). At 60 fps: 180 degrees = 1/120 s, 90 degrees = 1/240 s, 45 degrees = 1/480 s. RED: about 180 degrees gives the standard cinematic look; narrower angles look more staccato and show crisp detail in fast action.
- Blender: `render.motion_blur_shutter` is in frames, so 0.5 = 180 degrees, 0.25 = 90 degrees.
- Expected blur at 180 degrees and 60 fps (computed): at 60 km/h the bike moves 27.8 cm per frame and 13.9 cm during the exposure; at 70 km/h, 32.4 cm and 16.2 cm. The rear wheel (nominal 662.6 mm OD) at 60 km/h turns 8.0 rev/s: 48 degrees per frame, 24 degrees smeared per exposure, so spokes blur into a disc while knobs stay readable at the hub side. A camera that pans with the bike keeps the bike sharp and smears the background; a locked-off camera does the reverse.
- Stills for reference matching: about 1/1000 s freezes motocross action, but also freezes the wheels so they look static; panning shots use about 1/60 to 1/250 s ([Fstoppers](https://fstoppers.com/education/equipment-recommendations-photographing-motocross-279647), [PhotographyTalk](https://www.photographytalk.com/motorsport-photography-how-to-capture-speed-and-panning-shots/), [Digital Camera World](https://digitalcameraworld.com/tutorials/how-to-capture-perfect-panning-shots-in-motorsport-photography)). Damien's photos tell us which look each reference uses.

**Focal lengths** ([Fstoppers](https://fstoppers.com/education/equipment-recommendations-photographing-motocross-279647)): 24 mm for wide environment shots, 24-70 mm at local tracks, around 200 mm to isolate riders from a distance, 300 mm excellent but heavy, 10 mm fisheye sparingly. Practical plan: one long-lens side profile of the whip (200 to 400 mm from the side of the gap), one wide low angle near the lip (16 to 24 mm), one tracking or follow camera.

**Depth of field** (thin-lens formulas, circle of confusion 0.03 mm, full-frame 36 mm sensor, which is Blender's default `sensor_width`, verified locally; method per [Wikipedia: Depth of field](https://en.wikipedia.org/wiki/Depth_of_field)):

| Lens | Aperture | Focus distance | Sharp zone |
|---|---|---|---|
| 200 mm | f/4 | 30 m | 27.5 to 33.0 m (5.4 m) |
| 200 mm | f/2.8 | 30 m | 28.2 to 32.0 m (3.8 m) |
| 400 mm | f/5.6 | 60 m | 56.5 to 64.0 m (7.5 m) |
| 70 mm | f/4 | 15 m | 11.0 to 23.7 m |
| 35 mm | f/5.6 | 8 m | 3.8 m to infinity |
| 24 mm | f/8 | 5 m | 1.6 m to infinity |

Fstoppers suggests f/4 to f/6.3 for daytime races and wider apertures under lights. So: only long lenses give visible background blur in daylight, and the night version can use f/2.8. Blender camera DOF properties: `cam.dof.use_dof`, `focus_object`, `focus_distance`, `aperture_fstop`, `aperture_blades`, `aperture_rotation`, `aperture_ratio` (verified locally). Track focus with `focus_object` on an empty at the rider's chest.

---

## 7. Web viewer (glTF + three.js)

### 7.1 Export settings (verified locally)
```python
bpy.ops.export_scene.gltf(
    filepath="/abs/path/bike.glb", export_format='GLB',
    use_selection=True, export_apply=True,          # apply modifiers (Array, Simple Deform, Solidify...)
    export_yup=True,                                # default
    export_image_format='WEBP', export_image_quality=85,
    export_meshopt_compression_enable=True,         # or export_draco_mesh_compression_enable=True
    export_tangents=True,                           # needed for anisotropy and normal maps
    export_animations=False)                        # static model viewers
```
Test sphere scene sizes: plain 599 KB, meshopt 400 KB, Draco 357 KB (verified locally). Draco compresses geometry harder; meshopt also handles animation and decodes faster. Both are supported by three.js.

### 7.2 What survives export (verified locally on 5.2.3)
| Blender material feature | glTF result |
|---|---|
| Base Color, Metallic, Roughness, Normal map, Emission, Alpha | Core glTF PBR (`baseColorFactor` / textures) |
| Coat Weight | `KHR_materials_clearcoat` |
| Sheen Weight / Tint | `KHR_materials_sheen` |
| Transmission Weight + IOR | `KHR_materials_transmission` + `KHR_materials_ior` |
| Anisotropic | `KHR_materials_anisotropy` |
| Image texture as WebP | `EXT_texture_webp` |
| **Procedural textures (Noise into Base Color)** | **Dropped**: the material lost both texture and colour factor. Bake procedural looks to images before export |
| **Thin Film on Principled alone** | **Not exported.** `KHR_materials_iridescence` needs the custom "glTF Material Output" node group with an Iridescence Factor socket (exporter source and [glTF manual](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html)) |
| Thin Wall, subsurface, OSL, volumes, Cycles-only nodes | No exporter extension module for them (exporter source lists anisotropy, clearcoat, dispersion, emission, ior, iridescence, sheen, specular, transmission, variants, volume). Expect the web model to be simpler than the render |

The glTF manual says glTF requires PNG or JPEG images and the add-on converts other formats automatically; the exporter's `export_image_format='WEBP'` option writes `EXT_texture_webp` instead (verified locally). Texture budget (estimate): 2048 px for large parts (tank shrouds, seat, tyres), 1024 px for small parts, 4096 only for the decal sheet if needed. Use gltf-transform for KTX2/Basis if GPU memory matters.

### 7.3 Viewer setup
- **three.js 0.186.1** (MIT; pinned version older than two weeks, 0.187.0 came out 2026-10-30). Load from jsDelivr: `GLTFLoader`, `DRACOLoader` with decoder path `https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/libs/draco/gltf/`, `MeshoptDecoder` from `examples/jsm/libs/meshopt_decoder.module.js`, `OrbitControls`, and `RoomEnvironment` or an `HDRLoader` environment (all URLs return 200, checked). Set `renderer.toneMapping = THREE.AgXToneMapping` (constant 6) or `THREE.NeutralToneMapping` (7), `outputColorSpace = SRGBColorSpace` (constants checked in source). Do not assume three.js AgX matches Blender's OCIO AgX exactly: compare a render and the viewer side by side.

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
// importmap: "three" -> https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js
//            "three/addons/" -> https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.toneMapping = THREE.AgXToneMapping;
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
const draco = new DRACOLoader().setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/libs/draco/gltf/');
const loader = new GLTFLoader().setDRACOLoader(draco).setMeshoptDecoder(MeshoptDecoder);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.minDistance = 0.3; controls.maxDistance = 8;  // metres
```
- **model-viewer 4.4.0** (Apache 2.0) is the zero-code alternative: `camera-controls`, `environment-image`, `tone-mapping`, `shadow-intensity` attributes. Draco and KTX2 decoders default to a Google CDN; meshopt needs `meshoptDecoderLocation` set ([loading docs](https://modelviewer.dev/examples/loading/)).
- **Artifact constraints** (our review pages are private Artifacts, `CLAUDE.md`): scripts only from cdnjs, jsDelivr, unpkg and a few other allowed CDNs, with exact versions at least two weeks old; each binary file at most 15 MB and the page at most 16 MB. So: three.js from jsDelivr with jsDelivr decoders (avoid model-viewer's default Google CDN decoders), GLB under 15 MB (meshopt/Draco + WebP + 1K to 2K textures), split bike and rider into separate GLBs if needed.

---

## 8. Blender MCP and automation
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) (MIT): a Blender add-on runs a socket server inside a GUI Blender, and an MCP server forwards LLM tool calls to it (`execute_blender_code`, Poly Haven, Sketchfab, Hyper3D, Hunyuan3D). The README documents only the GUI flow ("Start MCP Server"/"Connect"), warns that the socket has no authentication or encryption, and that arbitrary code execution is the main tool. **Not useful here**: we already run `bpy` scripts headless directly, which keeps the scripts as source of truth as `CLAUDE.md` requires, and we fetch Poly Haven assets with plain HTTPS.
- Projects that claim headless use (not verified, maintenance unknown): [sandraschi/blender-mcp](https://github.com/sandraschi/blender-mcp), [blender-remote](https://pypi.org/project/blender-remote/1.2.0rc2/), [mcpBlender](https://pypi.org/project/mcpBlender-tspspi/). They wrap `blender --background`, which we already do.
- Our automation: one Python script per build step in `motocross-whip/scripts/`, each run as `blender -b --factory-startup --python-exit-code 1 --python step.py -- args`, writing a .blend and a check report (dimensions against spec tables, fixed-angle renders).

---

## 9. Sources
Official Blender
- Release notes: [5.0](https://developer.blender.org/docs/release_notes/5.0/), [5.0 Python API](https://developer.blender.org/docs/release_notes/5.0/python_api/), [5.0 Color Management](https://developer.blender.org/docs/release_notes/5.0/color_management/), [5.0 Compositor](https://developer.blender.org/docs/release_notes/5.0/compositor/), [5.0 Cycles](https://developer.blender.org/docs/release_notes/5.0/cycles/), [5.0 EEVEE](https://developer.blender.org/docs/release_notes/5.0/eevee/), [5.0 Geometry Nodes](https://developer.blender.org/docs/release_notes/5.0/geometry_nodes/), [5.0 Animation & Rigging](https://developer.blender.org/docs/release_notes/5.0/animation_rigging/), [5.0 Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.0/pipeline_io/), [5.0 Core](https://developer.blender.org/docs/release_notes/5.0/core/), [5.0 Rendering](https://developer.blender.org/docs/release_notes/5.0/rendering/), [5.0 Physics](https://developer.blender.org/docs/release_notes/5.0/physics/), [5.0 Modeling](https://developer.blender.org/docs/release_notes/5.0/modeling/)
- [5.1](https://developer.blender.org/docs/release_notes/5.1/), [5.1 Python API](https://developer.blender.org/docs/release_notes/5.1/python_api/), [5.1 Cycles](https://developer.blender.org/docs/release_notes/5.1/cycles/), [5.1 Rendering](https://developer.blender.org/docs/release_notes/5.1/rendering/), [5.1 Compositor](https://developer.blender.org/docs/release_notes/5.1/compositor/), [5.1 Geometry Nodes](https://developer.blender.org/docs/release_notes/5.1/geometry_nodes/), [5.1 Animation & Rigging](https://developer.blender.org/docs/release_notes/5.1/animation_rigging/), [5.1 Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.1/pipeline_io/), [5.1 EEVEE](https://developer.blender.org/docs/release_notes/5.1/eevee/), [5.1 Core](https://developer.blender.org/docs/release_notes/5.1/core/)
- [5.2](https://developer.blender.org/docs/release_notes/5.2/), [5.2 Python API](https://developer.blender.org/docs/release_notes/5.2/python_api/), [5.2 Cycles](https://developer.blender.org/docs/release_notes/5.2/cycles/), [5.2 Rendering](https://developer.blender.org/docs/release_notes/5.2/rendering/), [5.2 Geometry Nodes](https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/), [5.2 Compositor](https://developer.blender.org/docs/release_notes/5.2/compositor/), [5.2 Physics](https://developer.blender.org/docs/release_notes/5.2/physics/), [5.2 Animation & Rigging](https://developer.blender.org/docs/release_notes/5.2/animation_rigging/), [5.2 Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.2/pipeline_io/), [5.2 Core](https://developer.blender.org/docs/release_notes/5.2/core/)
- [4.0 Shading](https://developer.blender.org/docs/release_notes/4.0/shading/) (F82 tint)
- Manual (5.2): [Principled BSDF](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html), [Cycles Sampling](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html), [Light Paths](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/light_paths.html), [Motion Blur](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/motion_blur.html), [Performance](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/performance.html), [Color Management](https://docs.blender.org/manual/en/latest/render/color_management/index.html), [glTF 2.0](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html), [Rigify](https://docs.blender.org/manual/en/latest/addons/rigify/index.html), [Cloth Shape](https://docs.blender.org/manual/en/latest/physics/cloth/settings/shape.html), [Cloth Collisions](https://docs.blender.org/manual/en/latest/physics/cloth/settings/collisions.html), [Collision](https://docs.blender.org/manual/en/latest/physics/collision.html), [Fluid](https://docs.blender.org/manual/en/latest/physics/fluid/index.html), [Particles](https://docs.blender.org/manual/en/latest/physics/particles/index.html), [Simulation Zone](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/simulation_zone.html), [Array](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/array.html), [Curve](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/curve.html), [Simple Deform](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/simple_deform.html), [Shrinkwrap](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/shrinkwrap.html), [Child Of](https://docs.blender.org/manual/en/latest/animation/constraints/relationship/child_of.html), [IK Solver](https://docs.blender.org/manual/en/latest/animation/constraints/tracking/ik_solver.html), [Command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html); Python API [bpy_extras.anim_utils](https://docs.blender.org/api/current/bpy_extras.anim_utils.html), [Gotchas](https://docs.blender.org/api/current/info_gotcha.html)
- Manual source text (cloth, collision, Cycles pages): [projects.blender.org/blender/blender-manual](https://projects.blender.org/blender/blender-manual)

Tools and assets
- MPFB: [extension page](https://extensions.blender.org/add-ons/mpfb/), [GitHub](https://github.com/makehumancommunity/mpfb2), [asset licence](https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.ASSETS.md)
- Anny: [NAVER LABS blog](https://europe.naverlabs.com/blog/anny-a-free-to-use-3d-human-parametric-model-for-all-ages/), [PyPI](https://pypi.org/project/anny/), [paper](https://arxiv.org/abs/2511.03589)
- CharMorph: [GitHub](https://github.com/Upliner/CharMorph), [CG Channel](https://www.cgchannel.com/2025/03/check-out-new-open-source-3d-character-generator-charmorph/)
- GarmentCode: [GitHub](https://github.com/maria-korosteleva/GarmentCode), [pygarment](https://pypi.org/project/pygarment/)
- Poly Haven: [licence](https://polyhaven.com/license), [Public API](https://github.com/Poly-Haven/Public-API), [API ToS](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md), [dirt_bike_track_01](https://polyhaven.com/a/dirt_bike_track_01)
- ambientCG: [API docs](https://docs.ambientcg.com/api/)
- physicallybased.info: [site](https://physicallybased.info/), [API repo, CC0](https://github.com/AntonPalmqvist/physically-based-api)
- Refractive indices: [Wikipedia list](https://en.wikipedia.org/wiki/List_of_refractive_indices), [Complex Plastics nylon chart](https://complexplastics.com/chartnyl.htm), [US patent 5343317](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5343317)
- Bike data: [MotorcycleDB 2026 CRF250R](https://www.motorcycledb.com/CRF250R_2026/69204), [Autotrader listing](https://motorcycles.autotrader.com/motorcycles/2026/honda/crf250r/201816181), [Thompson's Motorsports](https://www.thompsonsmotorsports.com/inventory/v1/Current/Honda/Motorcycle/Competition/CRF250R/Base---25016651), [USA Roller Chain 520](https://usarollerchain.com/products/520-chain-10ft), [Rtech plastics](https://www.firestormmotorcycles.com.au/honda-crf250r-2022-2024-rtech-white-plastics-kit), [Polisport kit](https://www.cyclegear.com/parts/polisport-mx-restyle-body-kit-honda-crf250r-crf450r-rwe-r-s-2021-2024)
- Web: [three.js npm](https://www.npmjs.com/package/three), [three.js 0.186.1 on jsDelivr](https://cdn.jsdelivr.net/npm/three@0.186.1/), [model-viewer](https://modelviewer.dev/), [model-viewer loading](https://modelviewer.dev/examples/loading/), [glTF Transform CLI](https://gltf-transform.dev/cli)
- MCP: [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), [sandraschi/blender-mcp](https://github.com/sandraschi/blender-mcp), [blender-remote](https://pypi.org/project/blender-remote/1.2.0rc2/), [mcpBlender](https://pypi.org/project/mcpBlender-tspspi/)
- Render farms: [SheepIt FAQ](https://www.sheepit-renderfarm.com/faq), [SheepIt news](https://www.sheepit-renderfarm.com/news), [Super Renders Farm](https://superrendersfarm.com/blender-render-farm), [GarageFarm](https://garagefarm.net/blender-render-farm), [RebusFarm](https://rebusfarm.net/3d-software/blender-render-farm)
- Photography: [RED shutter angle](https://www.reddigitalcinema.com/red-101/shutter-angle-tutorial), [Fstoppers motocross gear](https://fstoppers.com/education/equipment-recommendations-photographing-motocross-279647), [PhotographyTalk panning](https://www.photographytalk.com/motorsport-photography-how-to-capture-speed-and-panning-shots/), [Digital Camera World panning](https://digitalcameraworld.com/tutorials/how-to-capture-perfect-panning-shots-in-motorsport-photography), [Wikipedia: Depth of field](https://en.wikipedia.org/wiki/Depth_of_field)
