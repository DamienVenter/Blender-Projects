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

## Exact-shape pass (2026-11-10, after "get the shape EXACTLY right, every tiny detail")
- Damien wants the STOCK Honda shape exact first (no graphics, no colours yet), following Honda's reference photos.
  Build with `build_bike.py ... stock NAME`.
- **Score, do not eyeball.** `compare.py PARTS.npz PREFIX` draws the parts flat from the photo's own camera in 6 s
  (no Blender) and scores them against the photo's material map (`segment.py`): silhouette overlap, per-material
  overlap, a per-region error table (cm2 missing / extra / wrong material) and a difference picture (blue = on the
  bike, missing from the model; orange = in the model, not on the bike). v0.1 scored 78 % silhouette; after this
  pass 85 %. Row scans of photo vs model classes along a z line settle any single question in numbers.
- **Extract, do not trace by eye.** `extract.py` pulls exact outlines from the material map (class + window + seed,
  erode to cut bridges, grow back, fill): frame spars with their bracket holes, both swingarm arms, the muffler,
  the black lower panels. Eyeballed grid readings were 20 to 30 mm off (header pipe, down tube, skid plate); class
  rows (front edge per z row) gave them directly.
- **Honda's studio photos are perspective views from raised cameras pitched down**, not blueprints. `cams.py` holds
  one calibrated pinhole camera per photo (see the next section). Every stored outline is "image-plane" (true on
  the centre plane only): cast it with `cams.CAMS[view].on_plane(u, v, 'y', y)` before building a part at lateral
  position y (3 % at 0.15 m).
- **Measured on the photo, overriding the spec sheet**: fork axis 26.75 deg in the axle-line frame = 27.7 deg to the
  ground (the 27 deg 33 min US/GS spec, not 28 deg 24 min), axle 39 mm ahead of the tube axis, trail 115 mm (spec
  117). Method: search for the two parallel tube edges in the gradient image over the whole tube (single-edge
  searches lock onto the brake hose). Check trail against rake and offsets before trusting an assumed axle lead.
- Tread pitch from the photo: Fourier analysis of the silhouette's edge radius along the lower arc: front 41 knob
  pitches per revolution, rear 46 (with a 3-pitch pattern).
- The photo's class "dark" is lit black rubber as often as dark metal: score it as matching either.
- The shock is hidden behind the pivot plates in profile (white gap behind them): do not place it by guess.
- Open question: only one fork tube is visible in the left photo although perspective should show the far one
  17 mm behind it (the front wheel may be steered a few degrees in the photo). Check against the front photo.

## Plastics pass (2026-11-10, "start with the plastics"): what went wrong and what works
### Cameras first. A wrong camera looks like a wrong shape.
- `cams.py`: five pinhole cameras in the axle-line frame. Sides: 4.7 m abeam, 1.13 m high, f 6073 px. Front: 4.69 m
  ahead of the front axle, 1.04 m high, 5.3 deg down, f 6942. Rear: 5.17 m behind the rear axle, 1.18 m high,
  6.2 deg down, f 7652. Top: 13.5 m up, f 14078, image right = -x, image up = -y. One rig: all about 1 m high,
  5 to 6 deg down. `python3 cams.py` refits, prints residuals and writes research/bike-cameras.json.
- **My first front and rear cameras were wrong by 0.4 m in height and 6.5 deg in pitch.** They were solved from
  exactly as many landmarks as unknowns, and one landmark was misread: the red seen under the fender nose in the
  front photo is the fender's rear flap behind the fork (the tyre's knobs are IN FRONT of it), not the nose. The
  symptoms did not point at the camera: the fender's shape "disagreed" between the top, side and front photos by
  30 mm, and the shrouds showed as slivers. Rules:
  1. Fit with MORE landmarks than unknowns and print the residuals (front: 6 landmarks, under 11 px; rear: 5, under
     7 px). Keep one landmark out as a check (footpeg tips in the rear photo: predicted 1671 / 2329, measured 1673 /
     2328).
  2. A tyre is the best landmark: a circle of known radius at a known place. Its top and bottom tangent rows fix
     distance and pitch. If the photo's tyre top is not where the camera puts it, the camera is wrong.
  3. Check what is in front of what before naming a landmark (zoom to pixels: `pxgrid.py VIEW U0 V0 U1 V1 STEP OUT`).
  4. When photos disagree about a shape, suspect the camera before the shape.
- Never read numbers off a displayed or scaled picture. Print class runs along rows or columns (red / gold / dark /
  other with their pixel ranges) and convert with the camera. I mis-scaled crops three times in one day.

### Measuring
- Gold fork tubes reflect the red plastics: a "red" mask picks up strips on the tubes and widens anything next to
  them (the front fender in the front photo read 25 px too wide on one side). Use the clean side and mirror, or
  require the run to touch the part.
- Dark shapes inside a plastic's outline can be decals (the stock navy "CRF" letters), not openings. Cutting them as
  vents left slits in the shrouds. Only the side panel's air intake is a real opening.
- **Shadowed plastic is still plastic.** The shroud's leading edge is two layers: the outer skin stops 35 to 80 mm
  short and a recessed inner wall, dark red in the photo (r 80..160), runs on to the true front edge. A bright-red
  mask (r > 110) missed the wall and left a slot in the outline. `outlines.py` now adds dark red in that zone and
  stores the skin's edge as its own line (`shroud_skin`); both sides agree within 2 mm. Zoom to pixels before
  deciding what a gap in a mask is.
- A translucent or tinted neighbour (the muffler behind the fender root is drawn half transparent, pink over red)
  makes a mask's edge ragged there: the side panel's rear tip still carries a small tongue from it.
- A part hidden in one view is often edge-on in another: the rear mud flap is behind the tyre in the rear photo but
  shows as a thin black strip in the left photo, which gives its fore-aft position exactly (x 0.34 to 0.32).
- Measured plastics facts (all through the refitted cameras): shroud half-width 0.200 at the front (top photo 0.199
  to 0.202, front photo 0.200), side face upright, top 38 mm rounded in by 28 mm, leading edge rolled in 12 mm; side
  panels 0.159 left, 0.175 right (bulge over the muffler); front fender widest +-0.100 at x 1.51 where its EDGES are
  62 mm below the centre line (arched section); fender nose tip at row 902 of the front photo; fork guards from
  58..68 mm to 131 mm off the centre line (tubes at +-99 mm: the guards sit inboard of the tubes); radiators' black
  from 0.130 to 0.189.

### Building
- **Photo panels** (`plastics.photo_panel`): mesh the plastic's outline in the profile photo's pixel space, put each
  vertex on the surface y = surf(x, z) along its pixel's ray. The model's side view is then exactly the photo's
  outline whatever the surface is; the surface comes from the top photo (plan envelope) and the front / rear
  silhouettes. A deck that is edge-on in profile (shroud tops) cannot be part of the panel: build it separately.
- A plan envelope crossed by the handlebar or cables is cut short there: fit a smooth curve with a robust loss
  (`_shroud_plan`), do not smooth the glitch into the surface.
- Ordering contour points by angle: measure the angle so it does not wrap inside the range (the plate's half
  outline, sorted by atan2 from the +u axis, jumped at mid height and folded the polygon along the centre line:
  slits in the front view).
- **Every part inferred from one photo must be scored in all five.** Skirts I gave the rear fender from the rear
  photo hung out behind the side panel in the profile. The red seen under the tail from behind is a set of
  rear-facing walls with two bolts (`fender_mounts`), hidden behind the side panels in profile.

### Surface quality: look at close-ups before showing anything
- Scores, flat sheets and full-frame matched renders all looked fine while the plastics were crumpled foil with torn
  edges. Render close-ups every time: `BIKE_CLOSEUPS="name:x,y,z:tx,ty,tz:lens;..."` adds cameras to build_bike.py
  (ground frame; 20 samples is enough to judge a surface).
- What crumpled them, in the order found:
  1. Pixel noise of the traced outlines (1 to 3 px). `plastics.clean_outline`: resample every 3 px, Gaussian along
     the curve (5 px = 4 mm). Thin slivers shrink under it: do not rely on a tip thinner than 10 mm.
  2. Rolled edges and shoulders written as functions of a separately smoothed edge table (x - edge(z)): the panel's
     real boundary wanders about that table, so the roll zig-zags. Write them as functions of the DISTANCE from the
     pixel to the outline's own front-facing or top-facing part (`plastics.Edges`): zero exactly on the edge.
  3. That distance taken to the outline's points (3 px apart) beats against the mesh's edge vertices (5 px apart):
     scallops every centimetre. Take it to the edge sampled every 0.25 px.
  4. An axis-aligned vertex grid cannot follow a 12 mm roll: `plate2d(..., rings=(...))` adds rows of vertices
     parallel to the outline through the rolled zone.
  5. Fingers in the outline: red reflections on the fork tube joined the shroud's mask, and the shadowed wall and
     the skin part near the lower tip. Count sharp reversals along a cleaned outline (turn over 100 deg within
     12 samples): more than the part's real tips means a finger.
  6. A raised plateau that stopped dead (height not faded with its width) left a 5 mm step across the fender nose.
- Seams drawn by hand between touching plastics hand slivers to the wrong part (the fender's lower flank went to the
  side panel as a tongue). Cut where the parts really meet (a vertical cut at the fender's root) and let the lofted
  part's edge line follow the mask's true lower boundary; overlap the two parts by 20 mm so no gap opens.

### Checking
- `python3 -m pytest -q test_bike.py` (2 minutes) before any render: cameras, agreement between photos, photo-panel
  exactness, score floors for all five views, intruders.
- `compare.py PARTS.npz PREFIX` now scores all five photos (silhouette and red overlap for front, rear, top). The flat
  renderer needs a per-pixel depth test: a painter's sort by face distance let the long fork tubes paint over the
  number plate.
- `compare.py sheet PARTS.npz OUT.jpg [views]`: photo beside the model in flat class colours, per view. Look at it
  after every change: the scores do not say which part is wrong.
- `compare.raster(..., by_part=True)` gives the part in front at each pixel: found the plate's slits in a minute.
- `compare.py intruders PARTS.npz`: parts that show where the photo has red plastic. It found, in one run each: the
  radiator coming through the shroud's side (white wedges in the render that looked like holes), the estimated
  subframe rails coming through the shroud's rear end and the fender's root, the tank beside the seat's nose. Hidden
  parts placed by estimate must sit INSIDE the measured plastics. Run it after every build.
- White shapes on a plastic in a render are one of three things. Check in this order with `raster(by_part=True)`:
  another part poking through, a notch in the outline, a mirror-like facet. Do not guess.
- Scores, plastics pass start to end (red overlap): left 0.78 to 0.87, right 0.80 to 0.88, front 0.52 to 0.75,
  rear 0.40 to 0.53, top 0.76 to 0.82. Rear stays low: the fender's underside tunnel is only stood in for.
- `audit.py` (run on the .blend): clashes between objects and loose pieces more than 4 mm from anything. Collars and
  bolts stand ON a panel's face along its normal (finite differences of the surface), bosses start behind its 3 mm
  shell; a part that "fixes to" another stops 0.5 mm short of it. A lap strip laid across a crease dips under the
  ridge between its own vertices (3 mm): keep it inside one facet. The fenders' shells are the 3 mm ABOVE their
  modelled surface (their faces point down, solidify offset -1).

## Plastics, second pass (2026-11-10): seat, creases, bolts, tail, fork guards
- **The traced outline `side_panel` takes in the seat's skirt** (the first pass split it from the seat along the
  foam's edge). The real seam is a dark line 8 px wide, read per column as a pair of steps in r + g (`SEAM_PX`): the
  "HONDA" is printed on the seat's skirt, not on the panel. `_panel` cuts the outline at the seam (`_cut`: polygon
  to mask to contour); the seat is a loft of top, foam radius and skirt down to that seam.
- Finding creases: per column (or row), steps of smoothed r + g across 8 px where both sides are red plastic; a line
  is real when it shows at the same place in neighbouring columns. Decals, bolts and seams give the big steps
  (over 80), creases the small ones (20 to 60). Build a crease as a change of the surface's angle on a row of
  vertices: `plate_lines(..., lines=)`; pockets get their edge and a second row inside it (`_inset_convex`).
- `smooth_poly` on a polygon of a few corner points moves the corners: the tail wall's top edge fell 24 rows (17 mm)
  and both corners were cut off (the first pass's stand-in plate had it too). Resample every few px, then smooth.
- Never extend a traced line along its end slope: the shroud skin line's ends run along the rows, and the extension
  cut a wedge 150 px back into the skin. Go straight on along the rows and curve out through the edge.
- A seat base flush with the skirt showed as a black band along the seam, came through the foam's edge over the tail
  and failed the intruder test: recess it 4 mm above the skirt's lower edge and 6 mm inside the cover everywhere.
- The intruder test counts every non-red part inside a plastic's outline over 2 cm2 per view and part (only the side
  panel's intake is exempt). The 8 body bolts are three parts (shroud, seat, panel: 1.4 cm2 a view each). The
  shroud's two air outlets can only be red pockets, not openings onto black louvres, until that test knows them.
- The number plate is symmetric within 2 px wherever the hose does not cross it; only the top corners differ (left
  one cut off, right one square). The red above its right top corner (rows 224..299, u 2124..2186, beside the bar
  pad) is not identified: not built.
- **The shroud's saw-toothed leading edge is in the traced outline**: the fork tube and the cables cross the edge in
  the profile photos and the mask follows them. The first pass has the same teeth (rendered side by side). Next:
  replace that stretch of the outline (count the reversals) by a smooth curve before any more work on the shroud.
- `plastics.SHROUD_LAYERS = 2` builds skin and inner wall as two shells, the shoulder's measured crease and the vent
  pockets. Its close-ups were not clean (teeth as above, ragged pockets): 1 (the first pass's surface) is built.
- Parts estimated by other passes that the measured plastics run into: `parts.tank` (rear end wider and higher
  than the seat's nose, 0.10 wide under the shroud decks where the top photo shows 0.055), `parts.radiators` (top
  outer corner at y 0.177, z 0.939 inside the shoulder the front photo measures), the subframe rails of
  `parts.frame` through the tail wall, the seat and the side panels.
- Scores after this pass (red overlap, before to after): left 0.871 to 0.894, right 0.883 to 0.899, front 0.749 to
  0.755, rear 0.531 to 0.537, top 0.822 to 0.819.
- Blender: `honda_left|right|front|rear|top` cameras reproduce Honda's cameras (parented to the bike's root so they
  follow the tilt onto the ground). They render on a transparent film with a shadow-catching floor (put the PNG on
  white) and with the Standard view transform: AgX turns brightly lit red plastics salmon in the studio set-up.
  Lights are hidden from the camera (the front and rear cameras look straight past them).
