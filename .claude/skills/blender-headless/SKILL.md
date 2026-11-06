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

## Python API
- Blender 5.x changed parts of the API versus 4.x. See `motocross-whip/research/blender-pipeline.md` (5.x breaking-changes checklist) before writing new scripts, and add any new gotcha found to this file.
