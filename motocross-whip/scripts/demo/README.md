# Whip physics demo

A simulated (not hand-animated) whip over the 75 ft jump, with proxy shapes, so the physics can be judged
before any detailed modelling. Every number lives in `params.py` with its source.

## Pipeline
| Step | Command | Output |
|---|---|---|
| Tests | `python3 -m pytest -q test_physics.py` | must pass first |
| Simulate | `python3 -u sim.py OUT [--face-throttle N] [--reuse]` | `frames.json`, `scene.json`, `hud.json`, `summary.json`, `records.pkl` |
| Render + assemble | `python3 assemble.py OUT WORK VIDEOS` | `whip_demo.mp4`, `whip_vs_damien.mp4` |
| Physics sheet | `python3 physics_sheet.py OUT sheet.png` | one-page plots and key numbers |

`--face-throttle` skips the 7-minute throttle solve with a value it found before (recorded in the summary).
`--reuse` re-exports from `records.pkl` without simulating.

## Modules
- `params.py`: all constants with sources (site, jump geometry, bike, suspension, rider).
- `terrain.py`: jump profile and exact wheel-centre contact curves.
- `bike.py`, `rider.py`: mass properties (part breakdown; Winter / Drillis-Contini anthropometry), neutral attack pose, two-bone IK.
- `ground.py`: sagittal dynamics on the ground: bike rigid body, non-linear suspension, rider on absorbing legs, throttle and traction.
- `air.py`: airborne two-body dynamics with gyroscopic wheels, exact angular momentum conservation; forward and inverse formulations.
- `sim.py`: solves face throttle and run-in speed, optimises the whip inputs, lands, exports.
- `pose.py`, `export.py`: per-frame transforms for every part, cameras, data overlay.
- `build_scene.py`, `render_view.py`: Blender 5.2 scene (Workbench) and per-camera renders.

## Known simplifications (demo only)
- The rider is one rigid body in the air (the pose rotates about the peg midpoint); arms and legs follow by IK.
- Steering is fixed straight; wheels are massless for the suspension (spin inertia is modelled).
- Drag uses a constant CdA of 0.80 m2 (the whip briefly raises it).
- The approach is a straight line; lateral drift from the whip is shown but not fed back into the ground model.
