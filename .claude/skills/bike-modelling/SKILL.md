---
name: bike-modelling
description: How Damien's CRF250R is modelled by script from calibrated studio photos (blueprints), his own photos and the spec sheet, and how it is checked, rendered and shown. Use before changing motocross-whip/scripts/bike or modelling any vehicle part.
---

# Modelling the bike (learned 2026-11-10, bike v0.1)

## Pipeline (motocross-whip/scripts/bike)
1. `blueprint.py`: Honda's studio profile photos are near orthographic. Fit a circle to each tyre's knob tips (lower
   arc only, outlier rejection: the chain and sprocket fool a plain fit) -> axle centres; scale = wheelbase 1483 mm /
   centre distance (0.78 mm per px). Output research/bike-blueprint.json.
2. `gridview.py` / `topview.py`: millimetre-gridded crops of the profile and top photos. Read positions off them
   (pivot, peg, sprocket, engine outline, frame) and write them in parts.py with the tag GRID or TOP.
3. `outlines.py`: red-plastic outlines extracted automatically (mask, holes filled, contourpy), the big touching body
   split along hand-read seams; seat and fender TOP LINES taken column by column (a thin seat strip breaks apart).
4. `parts.py` (plain numpy/scipy, no Blender): every part as meshes, each number tagged SPEC/BP/OUT/GRID/TOP/DV/EST.
   `geom.py` has the toolkit: tube sweeps, lathes, lofts, panels from outlines (Delaunay with interior grid),
   `plate2d` (2D shapes with holes: discs, sprockets), prisms. 1 s for the whole bike: iterate fast.
5. `livery.py`: textures painted in bike coordinates (side projection; front at the image's left on the left side
   and at its right on the right side so lettering reads on both).
6. `build_bike.py` (Blender): materials by name, UVs by projection per material, solidify for single surfaces,
   bevel for machined parts, studio, cameras, renders, .blend and .glb.

## Frames (got this wrong once)
- Outlines and grid readings are in the blueprint's AXLE-LINE frame (both axles at the rear tyre radius). Build in
  that frame and tilt the whole bike nose-up about the rear axle by atan((R_front - R_rear) / wheelbase) = 0.93 deg
  with a root empty, so both tyres stand on the ground. The rake in the axle-line frame is 28.4 - 0.93 deg.
- Front-end parts are children of a `steer` empty on the steering axis (parent inverse = translation by -STEER0), so
  steering is one rotation about the stored axis.

## Checks
- Render an orthographic camera with the photo's exact scale and framing (`profile_left`) and compare with the photo.
  Project the axles through the camera in Blender (`world_to_camera_view`) for numbers: within 4 to 9 mm.
  Do not trust a circle fit on the render with a dark threshold: it locks onto the black rims.
- Compare renders with Damien's photos at his camera angles (dv01, dv02, dv04) side by side.

## Rendering gotchas
- A single-sided floor whose faces point down renders BLACK in Cycles (no light from behind). Wind the faces so the
  normals face the bike.
- Saturated red: AgX "Medium High Contrast" with strong studio light turned his red salmon-pink. AgX - Punchy,
  exposure -0.6 and little clear coat match his bike.
- Relative texture paths load as magenta: pass absolute paths to bpy.data.images.load.
- Solid discs and sprockets hide the spokes: real ones are rings full of holes (`plate2d`).
- Bar pad lettering must read from the front AND from the seat: pick the UV direction by the face normal.

## Showing it
- Interactive viewer: motocross-whip/viewer/bike-v0.html (three.js 0.147 from jsDelivr, OrbitControls, GLTFLoader,
  a PMREM studio environment so metals reflect). Artifacts do not serve .glb: convert with `glb2json.py` (same model,
  buffer as a data URI) and load the .json.
