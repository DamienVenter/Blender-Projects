# 2026-11-10: bike v0.2, exact-shape pass (stock Honda, no graphics), state at the end of the session

`scripts/bike`: `segment.py` + `extract.py` (exact outlines from Honda's photos), `camera.py` (the photos'
perspective), `parts.py`, `build_bike.py ... stock bike_v1`, `compare.py` (scores).

| File | What it shows |
|---|---|
| `v02_vs_honda.jpg` | Honda's photo, the model from the same camera, the difference picture, a 3/4 view |
| `scores.json` | Match against both profile photos: silhouette 85 % (v0.1: 78 %), per material, error per region (cm2) |
| `render_profile_left.png`, `render_left_34_hero.png`, `render_right_rear_34.png` | Renders, stock colours |
| `bike_v1.glb` | The model (viewer: `viewer/bike-v0.html`, published with `glb2json.py`) |

Measured and exact now: axles, tyre diameters, fork tube line (within 4 mm), frame spars, swingarm arms, muffler
and lower panels (photo outlines), header pipe, down tube and skid plate positions, tread pitch.
Still crude: plastics are flat cut-outs (ragged edges, no sculpting), engine is a block, wheels (hubs, spoke
lacing, tread blocks), number plate, bars and controls, brakes, linkage, chain guide, every bolt and cable.
