# Whip physics demo

A simulated (not hand-animated) whip over the 75 ft jump, with proxy shapes, so the physics can be judged
before any detailed modelling. Every number lives in `params.py` with its source.

## Pipeline
| Step | Command | Output |
|---|---|---|
| Tests | `python3 -m pytest -q test_physics.py` | must pass first |
| Replicate (current demo) | `python3 -u replicate.py OUT` | same files: Damien's measured 3D whip, smooth, with physics around it |
| Simulate (physics-flown whip) | `python3 -u sim.py OUT [--face-throttle N] [--reuse]` | `frames.json`, `scene.json`, `hud.json`, `summary.json`, `records.pkl` |
| Render + assemble | `python3 assemble.py OUT WORK VIDEOS` | `whip_demo.mp4`, `whip_vs_damien.mp4` (clip 1 shot A angle) |
| Overlay on his frames | `../analysis/attitude_overlay.py out.jpg FRAMES 30 -25,1,1.5,1600 40 52 64 --sim OUT/flight.npz` | simulated flight drawn next to his real frames |
| Physics sheet | `python3 physics_sheet.py OUT sheet.png` | one-page plots and key numbers |

`--face-throttle` skips the 7-minute throttle solve with a value it found before (recorded in the summary).
`--reuse` re-exports from `records.pkl` without simulating.

## Modules
- `params.py`: all constants with sources (site, jump geometry, bike, suspension, rider).
- `terrain.py`: jump profile and exact wheel-centre contact curves.
- `bike.py`, `rider.py`: mass properties (part breakdown; Winter / Drillis-Contini anthropometry), neutral attack pose, two-bone IK.
- `ground.py`: sagittal dynamics on the ground: bike rigid body, non-linear suspension, rider on absorbing legs, throttle and traction.
- `air.py`: airborne two-body dynamics with gyroscopic wheels and exact angular momentum conservation; hip shift; closed-loop rider (`run_control`) with throttle/brake.
- `whip_measured.py`: Damien's whip measured frame by frame from his clip (`../../research/whip-attitude-measured.md`).
- `sim.py`: solves face throttle and run-in speed, then flies Damien's measured whip: the closed-loop rider follows what
  his camera saw (bike angle in the picture, how side-on, torso lean); the angles that camera cannot see are knots the
  CMA-ES search places (`pip install cma`), held softly so angular momentum decides. Lip pull, landing, export.
  The pipeline refines around `Pipeline.X0` (best full search); a fresh search is `SIGMA0 = 0.25`, about 100 generations.
- `replicate.py`: the replica: bike attitude from `research/whip-attitude-3d/fit_clips23.json` (two-phone 3D
  measurement) through a quaternion spline, one smooth curve through the lip (pivot on the rear tyre); rider's unseen
  angles solved for reach and momentum (mismatch reported); physics for everything else.
- `pose.py`, `export.py`: per-frame transforms for every part, cameras (two matched to Damien's phones), data overlay.
  Smoothness: soft IK, joint and twist continuity, head smoothing, every object resampled onto whole frames.
- `build_scene.py`, `render_view.py`: Blender 5.2 scene (Workbench) and per-camera renders.

## Known simplifications (demo only)
- The rider is one rigid body in the air (the pose rotates about the peg midpoint); arms and legs follow by IK.
- Wheels are massless for the suspension (spin inertia is modelled); steering and throttle act in the air only.
- Drag uses a constant CdA of 0.80 m2 (the whip briefly raises it).
- The approach is a straight line; lateral drift from the whip is shown but not fed back into the ground model.
