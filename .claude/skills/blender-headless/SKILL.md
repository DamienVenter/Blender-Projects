---
name: blender-headless
description: How to install, script and render Blender 5.2 headless on the cloud build server (no GPU). Use before running any Blender command in this repo.
---

# Blender headless on the build server

## Install
- `tools/setup_blender.sh` (idempotent). Pinned to 5.2.3 LTS; Damien runs 5.2.0 LTS, installed side by side as `blender-5.2.0` for compatibility checks.
- Builds come from `https://download.blender.org/release/Blender<series>/blender-<ver>-linux-x64.tar.xz`.

## Running scripts
- `blender -b --factory-startup --python script.py -- arg1 arg2`. Arguments after `--` are read from `sys.argv` (everything after the `--` index).
- Use `--factory-startup` so no user prefs or add-ons leak in.
- In background mode Blender exits once the script finishes.
- By default the exit code is 0 even when the script raises (verified 5.2.3). Always pass `--python-exit-code 1` BEFORE `--python` so a Python error fails the command: `blender -b --factory-startup --python-exit-code 1 --python script.py -- args`. `sys.exit(n)` inside a script returns `n`.

## Paths
- `//` (blend-relative) paths fail with "cannot save" when no `.blend` is loaded. Always use absolute paths in headless scripts that start from factory settings.

## Render engines on this machine (4 CPU cores, no GPU), measured 2026-11-06
| Engine | Works? | Default cube, 1920x1080 |
|---|---|---|
| Cycles CPU, 64 samples, denoised | Yes, out of the box | 11.6 s |
| EEVEE | Only after installing EGL + Mesa (done by setup script); runs on llvmpipe software OpenGL | 35.3 s |

- EEVEE prints `EGL Error (0x3009): EGL_BAD_MATCH` warnings on llvmpipe. They are harmless; the render completes.
- Conclusion: Cycles CPU is both faster and higher quality here. Use Cycles for all previews and checks. Workbench is fine for quick clay/wireframe checks.

## Python API (5.x gotchas that break 4.x habits)
Full checklist with sources: `motocross-whip/research/blender-pipeline.md` section 1. The ones that bite most:
- **Animation**: `action.fcurves` is gone (layered, slotted actions). Fast bulk keyframing pattern:
  ```python
  from bpy_extras import anim_utils
  act = bpy.data.actions.new("name"); slot = act.slots.new(id_type="OBJECT", name=ob.name)
  ob.animation_data_create(); ob.animation_data.action = act; ob.animation_data.action_slot = slot
  cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
  fc = cb.fcurves.new("location", index=0, group_name="Object Transforms")
  fc.keyframe_points.add(n); fc.keyframe_points.foreach_set("co", flat_frame_value_pairs); fc.update()
  ```
  Keyframes may sit on fractional frames: simulate at 120 Hz, key every half frame of a 60 fps timeline, or run the scene at 120 fps and render every 2nd frame for real time and every frame for 0.5x slow motion.
- **Materials**: never set `Material.use_nodes` / `World.use_nodes` (deprecated, nodes exist already). Address Principled BSDF sockets by NAME: 5.2 inserted `Thin Wall` at index 5, shifting every index after `Alpha`.
- **Geometry Nodes modifier inputs** (5.2): `mod.properties.inputs.Socket_2.value`, not `mod["Socket_2"]`.
- **Compositor**: `scene.node_tree` and the Composite node are gone; node options are inputs set by UI label. Set the compositor device to CPU on this server.
- **Video output**: set `image_settings.media_type` before `file_format`, or `'FFMPEG'` is rejected.
- **Sky**: `sky_type='NISHITA'` is rejected; use `MULTIPLE_SCATTERING`. EEVEE id is `BLENDER_EEVEE`. `bgl` is gone.
  Sun direction d (unit, towards the sun): `sun_elevation = asin(d.z)`, `sun_rotation = atan2(d.x, d.y)` (checked
  against a sun lamp on a matte sphere; the brightest equirect pixel misleads). At strength 1 the multiple-scattering
  sky puts about 14.9 (luminance units) on a horizontal plane at sun elevations 60 to 75 deg: scale its strength from
  that, not by eye (rider-modelling, round 6 daylight).
- **Colour**: keep the working space Linear Rec.709; AgX is the default view; looks are named like `'AgX - Punchy'`.
- Render passes are spelled out (`Depth`, not `Z`).

## Workbench for motion review
- `scene.display.shading` (light `STUDIO`, `color_type='MATERIAL'` uses `material.diffuse_color`, shadows, cavity) and `scene.display.render_aa`. Fast clay renders for judging motion.

## Render budget
- A trivial scene at 4K, 128 samples, Cycles CPU took 7.0 min per frame here. Final 4K60 animation needs a render farm (SheepIt supports 5.2 but sends files to volunteers: ask Damien first) or Damien's GPU.
