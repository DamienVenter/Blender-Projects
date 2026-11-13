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
- **Damien's phone does not load the 3D viewer artifact** (2026-11-12: neither the 78 MB six-file page nor the
  7.8 MB Draco one: "Still won't load. Find a different way"). Show the bike as studio stills and a turntable video
  sent with SendUserFile: `turntable.py` on a built .blend (the bike turns, camera and lights stay; Honda's studio
  look: Standard view, exposure -0.9, world 0.7, lamps at half, shadow-catcher floor on a transparent film), then
  `onwhite.py` (clears the denoiser's faint alpha noise, else grey streaks show on white) and ffmpeg to H.264 MP4
  (yuv420p, faststart). About 25 s a frame at 1080 px, 24 samples; stills 1600 px, 64 samples.
- Damien looks at the viewer on his phone, and wants a CLEAN bike: the bike alone, full screen, no text panels or
  numbers (2026-11-12: "not loading. Too much info anyways. just give me a clean bike that's it"). Numbers and
  comparison sheets go in the checkpoint folder and a short chat message, not on the page.
- Page: `motocross-whip/viewer/bike.html` (three.js 0.147 from jsDelivr, OrbitControls, GLTFLoader, DRACOLoader,
  RoomEnvironment reflections, a canvas-gradient contact shadow instead of shadow maps). Model: `export_web.py` on a
  built .blend (Draco, 14/10/12-bit quantization: 58 MB -> 5.9 MB), then `glb2json.py OUT.glb bike.json` (one file).
  Publish with `files` = bike.json plus `draco/draco_decoder.js`, `draco/draco_wasm_wrapper.js`,
  `draco/draco_decoder.wasm` (contentType application/wasm; copies in `viewer/draco/`). The page uses the wasm
  decoder when it can compile WebAssembly and the plain JS one otherwise.
- The artifact host lets a page fetch only files published beside it (CDNs serve scripts only), keeps each file
  under 16 MB and each publish under 64 MB. The 78 MB, six-file v0.5 page did not load on Damien's phone: keep the
  model one compressed file under about 10 MB.
- Test with Playwright before publishing, at 390x844 and desktop, once with `delete window.WebAssembly` to exercise
  the JS decoder. Software GL is slow with a million vertices: screenshot timeout 240 s, device scale factor 1.

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
- **The shrouds stayed crumpled after all six, and what cured them (2026-11-10).** Cause: every height was a function
  of the DISTANCE to a traced outline that still wandered (56 changes of curvature sign round the shroud, 4 px
  quantised trace), over zones far wider than a rim: a 28 mm shoulder within 38 mm of the "top-facing" edge, a
  12 mm lip from the "front-facing" edge, and those two masks switched on and off 4 to 5 times along the edge. Each
  wiggle of the outline became a dent 30 mm deep into the panel; the step to the inner wall crossed an axis-aligned
  grid and saw-toothed; the deck was placed from a filtered copy of the same edge, so a slit opened. Cure, in
  `plastics.py` (`smooth_pieces`, `conforming_mesh`, `shell`, `_shroud`):
  1. Outline = corners read in the photo + one robust B-spline per piece (knots 40 px, cables and brackets bridged):
     10 curvature sign changes, 99.5 % of the traced area. Thresholds on the photo itself (first bright-red pixel
     per row) gave the skin's own edge to 1 px, identical in the left and mirrored right photo: build both sides
     from the left.
  2. Surface = plan(x) minus a roof that depends only on the height above ONE smooth crease curve
     (lean = hh^2 / (hh + r)), checked against the front and top photos. Nothing depends on the outline except the
     rims' last 8 mm, and those are carried by rings of vertices at exact offsets from the boundary.
  3. Mesh = the boundary's own points, rings, rows ON each crease and 2.5 px either side (70 deg auto-smooth turns
     a lone row into a soft bend 7 mm wide), a staggered grid, Delaunay, and a check that every boundary edge is in
     the triangulation.
  4. Two parts that are one skin (roof and bolt plate) share the edge's 3D points: the plate's rows start FROM the
     shell's top-edge vertices. Two rims 6 px apart make one wavy ridge: keep features 14 px apart or merge them.
  A shroud-only Cycles preview (5 s a view) lets you look ten times for the price of one full close-up run.
- Seams drawn by hand between touching plastics hand slivers to the wrong part (the fender's lower flank went to the
  side panel as a tongue). Cut where the parts really meet (a vertical cut at the fender's root) and let the lofted
  part's edge line follow the mask's true lower boundary; overlap the two parts by 20 mm so no gap opens.
- **Gloss needs C2 (2026-11-13, decision 37 round 2: the side panels' upper rear "crumpled like a plastic bag").** A
  gloss face shows every break in its CURVATURE as a line in its reflections; C1 is not enough. What dented it, all
  in `plastics._panel`: measured lines read straight from reading to reading (a kink at every reading, and the
  face's lean with it), smoothstep blends, hard min/max clamps, a blend between two sections that disagree by 4 to
  5 mm, a measured line held level past its last reading. Cures: `fair_line` (a cubic smoothing spline through the
  readings, to their precision, carried on at the end's slope), `spline_table`, `smootherstep`, `smin`/`smax`;
  blend only where the two things agree (measure that first), over the widest stretch the photos allow. Mesh: the
  crease row ON the surface's own crease (0.3 px off it cut teeth), rows 2.5 px either side wherever the facets
  beside it are wider than 6 px, and rows through every round (a 45 deg turn across one 15 px triangle wobbles).
  Measure before and after: the normal along rows parallel to the creases (waves against a running mean, kinks
  step to step) and the smooth-shaded vertex normals against the surface's (test_detail_plastics
  `test_decision37_panel_upper_rear_is_fair`: waves 9 -> 3.5 deg, kinks 5 -> 0.3, mesh 39 -> 7). Then look under a
  raking sun with the panel in plain gloss red (`scripts/bike/rake.py BLEND -- OUT "sp07:rakeL:red"`): a printed kit
  hides waves.

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
- **After merging the other modules** (2026-11-10): mounts aimed at a first-pass part were wrong at once (a fender
  pad sat 48 mm inside the new lower clamp; 22 mm bosses behind the body bolts ran into the new radiators and
  subframe). Read the other module's mounting points first: the plate's boss and pegs now end 0.3 mm short of the
  bridges of `detail_front`'s clamps (`fk`, `T_LO`, `FACE_UP`), leaving the plate and meeting the clamp square to
  each face (a slanted tube end cuts into both); the tail wall takes its x from the subframe's rear cross member.
- Which side of a single surface Blender's 3 mm shell lies on follows the ring order, and other modules assume
  one: `detail_front` puts the fender nose's bosses 0.3 mm under the fender's INNER skin, so the front fender's
  rings run left to right (shell under the surface). Check with `contact.py`-style full distances, not by reasoning.
- `audit.py` calls a piece floating when none of about 40 sampled vertices is within 4 mm of another object, and its
  clash depth is the size of the crossing faces, not the penetration. A big panel on small mounts reads as floating
  (front fender 11.7 mm by the audit, 1.0 mm from the clamp's bosses over all vertices; number plate 7.5 against
  0.5 mm). Measure true gaps from every vertex before adding geometry for the audit's sake.
- Shroud decks: take the deck's height and outer edge from the shroud's own surface along the UPPER envelope of its
  outline (all top-facing points in order of x mixed in lower edges that face up: wrinkled decks), and keep the
  edge inside the inner face of the panel's shell.
- Scores after this pass (red overlap, before to after): left 0.871 to 0.894, right 0.883 to 0.899, front 0.749 to
  0.755, rear 0.531 to 0.537, top 0.822 to 0.819.
- Blender: `honda_left|right|front|rear|top` cameras reproduce Honda's cameras (parented to the bike's root so they
  follow the tilt onto the ground). They render on a transparent film with a shadow-catching floor (put the PNG on
  white) and with the Standard view transform: AgX turns brightly lit red plastics salmon in the studio set-up.
  Lights are hidden from the camera (the front and rear cameras look straight past them).

## Detail pass (2026-11-10, "find your inconsistencies, add detail to every tiny bit"): five agents, one bike
### How the work is split
- `parts.py` loads plugin modules (`detail_front`, `detail_engine`, `detail_wheels`, `detail_chassis`,
  `detail_plastics`). Each defines `PARTS`, `REPLACES`, `FRONT_END`, `MATERIALS`, `CLASS`, `THIN`, `BEVEL`,
  `SMOOTH`; the metadata travels in the parts file to `build_bike.py` and `compare.py`. One module per assembly,
  one test file per module (`test_detail_<name>.py`), so agents never edit the same file.
- One agent per assembly, each in its own git worktree, each with a written brief (what to build, vertex budget,
  which photos to measure, what to report). Fresh agents hold one assembly in mind; the coordinator holds none of
  the code and only merges, checks shared numbers and runs the whole-bike audit.
- Round 1 builds. Round 2 fixes clashes: resume the SAME agents (they know their code) with the audit's clash
  list, each line with its box and deepest point, and the rule "the estimated dimension yields to the measured
  one". 29 clashes fell to 7 in one round.
- Shared geometry that two modules must agree on goes in `parts.py` as a function both import
  (`parts.chain_top(x)`: the chain rides on it, the swingarm's slider sits 9 mm under it). Do not let one module
  copy numbers out of another: the clutch cable route was copied and cut through a boss one round later.
- Fetch before launching worktree agents: `git fetch origin "+refs/heads/main:refs/remotes/origin/main"`.

### Shared reference points: what the agents found wrong, and how each was checked before changing it
Every one of these was a number the whole bike hung on. An agent's claim is a lead, not a fact: measure it again.
- **Tyre radius.** The blueprint's circles lay 8 mm inside the knob tips. Rays from each axle over the free arc of
  the tyre in both side photos give 359 and 334 mm; real 80/100-21 and 100/90-19 tyres are that size; and Honda's
  overall length (wheelbase + both radii) came out 3 mm short instead of 18. Three sources, then change it.
- **The axle height is a datum, the tyre radius is a measurement.** They were one constant. Now `AXLE_Z` (frame),
  `R_FRONT`/`R_REAR` (tyres), `GROUND_DROP` and `parts.to_ground()` (the only place that puts points on the ground).
- **End cameras.** With the true radii and bar ends the front camera's residuals fell from 10.7 px to 1.7 px. A fit
  that leaves 10 px on one landmark is telling you a landmark is wrong. Fit once WITHOUT a doubtful landmark and
  read it back: the rear photo alone gave the bar ends' height to 0.5 mm of the side photos'.
- **Reading on the centre plane.** A point off the centre plane, read on it, is wrong by (camera height - z) * y / D:
  18 mm for the swingarm pivot cap (y 0.14), 13 mm for the countershaft, 30 mm for the footpegs. Cast every
  feature on the plane it is on (`CAMS[view].on_plane(u, v, "y", value)`). The pivot then gave 584.5 mm to the
  axle against the spec's 585.2.
- **Look before computing.** The countershaft was "hidden behind the cover" for two passes. One crop of the left
  photo with candidate positions drawn on it showed the sprocket's hub in plain sight, 11 mm from every guess,
  and showed the chain's top run lifted over the slider (so the chain is not a taut two-tangent loop).
- Honda's photos disagree with each other by up to 14 mm on some points (bar ends fore-aft: side photos 0.903,
  top photo 0.917; footpeg height: rear photo 0.401, left 0.413). Use the mean and write both numbers down.
- Against the spec sheet the photo bike's seat is 20 mm and its belly up to 18 mm high while length, bar height,
  width, swingarm and footpegs agree within 3 mm. Cause not found; the model follows the photos.

### Micro pass (2026-11-11, "perform as if each tiny component is a separate build"): what the first round taught
- Brief = one list of separate builds per agent, each with anatomy, references, numbers, build, check (`pair.py`
  photo beside model, same camera, any box of any of the nine studio photos), ledger entry and commit
  (`research/detail-ledger/<module>.md`). Agents finish 5 to 9 of 10 to 12 components per 700k-token run; an agent
  that "ran out of room" is replaced by a fresh one briefed with the ledger, not resumed.
- Look at the agents' own check images before merging: "done" muffler had lumpy faces, "done" frame rear was a flat
  slab beside a ribbed casting. Send the agent back with the image name and pixel boxes of each difference.
- **Rear axle in Honda's photos is higher than `parts.RA`.** Five independent reads, each cast on its own plane:
  sprocket bolt circle +5.7 mm, axle bore +8 (left) and +11 (right), rear disc bolt circle +8.4, the tyre's own
  outline (rear-most knob and top) +5; the front tyre's outline puts the front axle only +2. The studio bike's
  swingarm sits about 0.7 deg lower than the build pose (sag). RA stays (the whole rear hangs on it, and the whole
  wheel pair is under 6 px off); hub parts are measured about the photo's own centre and built about RA. When the
  rear suspension is rigged, the studio pose is the swingarm 0.7 deg down from the build pose.
- An agent's "the camera scale is 6 % off" (tread rows closer in the end photos than predicted) was rejected: the
  end cameras' vertical scale is pinned at the wheel by the tyre (axle to ground) and their distance by the
  bar-to-axle perspective, and the model's rear tyre is 100.9 mm at its widest against a nominal 100.
- Two modules both named a part `rear_brake`; the later plugin silently dropped the other's pedal. `parts.build()`
  now raises when a plugin's part would replace another plugin's (unless it lists it in REPLACES) or two plugins
  define one material differently (test in test_bike.py).
- `compare.intruders` flagged the muffler "inside the fender" after the fender changed. Check the photo's pixels
  there before blaming the traced outline: 58 % were red, so the panel's edge was short, not the trace wrong. On the
  right side the same check later failed where only 10 % was red (the can's pink reflection of the panel, traced as
  panel). The check now looks only where the photo itself shows red (`compare.photo_red`: closed over highlights,
  grown 3 px); a test removes the rear fender and makes sure the hole is still found.
- The handlebar's own top sits on the front photo's bar edge within 3 px (test), 6 mm under Honda's 1262 mm; the
  throttle hood stands 12 mm over it in the photos. The overall height test takes the cockpit's top within -8/+15.
- Disk: agents left 2 GB each of .npz/.blend in their scratch folders and the disk filled during a test run. Tell
  agents to delete their big intermediates; after merging, delete them and remove the merged worktrees.
- Agent output per run: about 6 components of a 10 to 13 list. Plan rounds, not one heroic run.
- From the cockpit rounds: a feature ahead of or behind a ruler's plane reads at the wrong place in an end photo
  (the bar is swept 16 deg: 25 mm of depth moves a point 7 mm along it); pick it in two calibrated photos and
  triangulate. `geom.tube()` orients its section from the world's up, so a strap round a tilted axis twists: build
  such rings in the object's own frame. Relief lettering seen from the front: the viewer's right is the bike's left;
  check one letter in a close-up. build_bike.py drops ALL of a part's UVs if Blender removes one degenerate face:
  keep UV-mapped pieces (buttons, decals, knurl) free of zero-area faces.
- Near the front axle the side cameras put features off their projection by an amount that grows with y: about
  (+13.7, -10.3) px x y / 0.128 m in LEFT. Measure fork-foot and disc-guard features relative to the photo's own
  axle (or flatten the photo onto the feature's plane), not through the camera alone. (Round 4 of the front.)

### The audit (`audit.py`)
- `blender -b BIKE.blend --python-exit-code 1 --python audit.py -- OUT.json 25`: every pair of objects that cut
  each other (face pairs, depth, box, deepest point: WORLD coordinates) and every loose piece more than 4 mm from
  any surface. Run it on the built .blend, after modifiers.
- Measure distances to surfaces, not vertices: a bolt on a big flat face is far from that face's corners. The
  first version flagged such bolts and an agent "fixed" them with zero-area triangles. An audit that can be
  satisfied by a trick will be. Say in the brief: no tricks to satisfy the audit.
- Nesting is not a clash (axle in hub, stem in its bore): name it in the report. Seats of 1 mm or less are fine.

### Running agents and renders: small things that cost an hour each
- An agent can hang: no transcript event and no process for over an hour, and messages only queue. Look at its
  worktree (`git -C <worktree> status`, newest file times) and `ps`; if nothing moves, stop it and send it a
  message, which resumes it from its transcript with the worktree intact. Tell it to commit first.
- A broad brief gets the hard item skipped (the plastics agent did ten things and left the shrouds crumpled). The
  shrouds were fixed by a fresh agent with that one job, the required method written out, and a cap on render runs.
- Tell every modelling agent to LOOK at close-ups of its own parts: scores and tests passed with a crumpled frame,
  bolts through the bar pad and mirrored lettering.
- `BIKE_STUDIO_RES` is "W,H" (two numbers). A `BIKE_CLOSEUPS` camera is named exactly as written and must be in
  the views list under that name (use `cu_...` names). A wrong name renders nothing and exits 0: count the PNGs.
- Viewer: https://claude.ai/artifact/ToCZsujHJ7qgqiXYWK2Dzv, version 8 = the clean page with model v0.5 (Draco).
  Publish `viewer/bike.html` with that `url` and the `files` map above to update it.

## Damien's sticker kit (2026-11-12, "use ai... put it on the bike, ZERO difference")
- Pipeline, all scripted (`scripts/bike`): `kit_template.py PARTS OUT` (orthographic left, right and TOP views of the
  model, part-id maps, frame.json) -> `kit_crops.py OUT SIDE PART[,PART] ASPECT tpl.png` (one panel's outline padded to
  an aspect the image model offers) -> OpenArt Nano Banana Pro image2image, 4K, two images: the template crop first,
  then crops of HIS photos -> pick, check the art against the template outline (overlay the template's dark lines)
  -> `textures/damien-v1/art/` at 2x the template's pixels, entry in `kit.json` with crop, pad and the history id ->
  `kit_mirror.py KIT PART` for the right side -> `kit_canvas.py KIT TEMPLATE_DIR` -> side_L/R.png, top.png,
  plate.png, seat.png, bands.json -> `build_bike.py ... livery`.
- Prompts that work: "Faithful copying job, not a redesign", the template's orientation in words (which end is the
  front), the colour layout read off the photo region by region, "keep the template's exact outline... pure white
  outside... no other text". Whole-bike prompts invent a kit; one panel per call does not. Of two images one often
  invents logos or brands (DUNLOP on a Pirelli kit): reject it even if it looks better. Writing in the AI's output
  can come back mirrored ("NSU" for USN): read every word before keeping an image.
- Right side = left art mirrored, then every word set back to READ (`kit_mirror.py`). A plain unmirrored copy is
  right only for level writing; a slanted word (the swingarm) must be carried by the mirror and then a reflection
  across the line perpendicular to its writing direction, i.e. rotated by -2x its slope about its centre: it then
  runs along the mirrored part, letter tops still to the same edge. Layers pick lettering by ink colour, a box, and
  filters: `on_black` (white ink only where ringed by the black sticker: brushed aluminium highlights and the white
  slot through the axle block are as light as white ink), `glyphs` (drop long or sparse blobs: pinstripes, gloss
  streaks), `solid` (a logo plate with its letters, PIRELLI), `angle` (a column of level logos is taller than wide,
  so its long axis is not its writing direction). Checked on photo 03: his right swingarm reads "PSALM 91" at the
  axle end, the outlined "PSALM" at the pivot end.
- A wrap on bare metal (swingarm): map only the faces under the sticker. `kit_canvas` writes the sticker's band (per
  4 mm of x, z low and high, from the art's own black/ink pixels, not the AI's grey "aluminium" round it) to
  bands.json, also where the chain hides the arm in the side view; `build_bike.in_band` wraps a face inside it at
  any |ny| > 0.3. The first try (only `swing_L/R` faces with |ny| > 0.6) left the cast front section and the rounded
  edges bare: half the outlined PSALM and a sticker band half the arm's height.
- Tops: a "top" texture seen from above as the rider sees it (front at the image's top, the bike's right at its
  right; maps.json "top"): the tank's top faces (tank_ti, z > 0.97) and the shroud decks' tops take it. The fuel cap
  is its own geometry: the art's black disc under it need not line up exactly.
- Bookkeeping traps: the seat is ALSO a "top" panel (target seat); filtering panels by side dropped it once. A camera
  at -y in the studio scene looks at the back of the backdrop (all grey): use right_rear_34 for the right side.
- Read his photos for WHERE a graphic sits, not only what it is: the Renthal pad's AI face came back 2.5:1 while the
  pad's face is 3.5:1, because photo 04 sees the face AND the top: the emblem is on the pad's top, the two RENTHAL
  lines on its faces (`kit_canvas.build_barpad`). His right grip is light grey with a red flange and bar-end ring,
  the left black: the right grip has its own materials (grip_r*, stock black; his colours in the livery block).
- The top view is the bike's whole length (same X0..X1 as the side views), so the tank and both fender tops are
  painted on crops of one template: `kit_canvas.build_top` fills top.png, fender.png and front_fender.png ("texture"
  per panel; maps with "ppm"). Moving the frame shifted the tank crop by (1.90 - 1.25) x 1700 px; top.png came out
  identical to the texel, which is the check to run after any change of framing. Image-model art often paints
  lighting into a flat sticker (a gloss streak, a red glow): reject it, or flatten that colour to its median.
- Never read a test result through a pipe: `pytest ... | tail` exits 0 whatever pytest did. Write the output to a
  file and echo pytest's own exit code (`pytest ...  > out.txt; echo $?`). Renaming a material (the right grip's)
  broke four tests that pick faces by material name; one such run was reported as passing.

## Side panels drawn by script (2026-11-13, decision 37, Damien: they "look weird")
- Image-model art fails on lettering and repeats: cracks and ticks through the 1s, jagged wedges, a level centred
  PSALM 91, and white cut-outs where kit_mirror lifted words. A panel that is mostly lettering is drawn by script
  (`kit_sidepanel.py`): rings traced from clean sources (his plate art's own 114 and name, Leatt's official logo
  file, a real font), filled at 3x supersampling; zones, flake and splatter procedural; every placement measured.
  Same art size and crop as before, so `kit_canvas` maps it unchanged. Ledger: `research/detail-ledger/side-panels.md`.
- Photo 03 ("right-side" in its file name) shows the LEFT side: chain, chain slider and shift lever. Check a photo's
  side by such parts before measuring on it. No photo shows the right side panel.
- Measuring a flat panel on a long-lens photo (07): an affine from 4 or more landmarks (2.2 px rms). A homography
  from 5 points was badly skewed; it needs many more points than its 8 unknowns.
- Lettering slanted along a sloped edge (PSALM 91, the name): a vertical shear, verticals stay vertical as in 07,
  not a rotation.
- Reflections are not graphics: the white "swoosh stripes" on the black tail move between 02 and 03 and are absent
  in 06. The red band along the panel's lower rear in 03 is the plastic's own lip.
- Flake vinyl is METAL: its look is what it reflects, not a colour. The same panel reads light silver in shade (02:
  the sky in every flake), bright worms on a dark base in 03, dark navy in sun (07). Round 1 calibrated a diffuse
  colour on 02 (0.20/0.60/0.98 of the 114's white) and got a coarse black and white salt and pepper at half white:
  the coordinator's "too coarse, too bright, too contrasty". Round 2: measure the ALBEDO where the flake reflects
  little (03, the closest view, 0.88 mm a pixel up the panel: base (43, 43, 51), specks over 32 percent by Otsu, 1 to
  2 px long; 07 in sun: (28, 38, 58) against the white) and make the specks metal in the material map. Then check it
  in renders through each photo's camera: a studio shows it lighter than a tent or the sun does (the grey cyc is in
  every flake). Draw specks as the photo shows them (bent strokes 1 to 2 mm, 0.65 mm wide, 3x supersampled), not as
  smooth noise mapped through quantiles (round blobs).
- A flat metal flake does not sparkle: every flake on a flat panel mirrors the same direction, so the zone just goes
  grey. Sparkle is each flake's own tilt: a normal map (Rayleigh 12 deg per axis, EST), on the base layer only (the
  clear laminate, Principled's coat, stays smooth). It raised the zone's pixel contrast in sp07 by 40 percent (std 16 -> 23).
- Draw extra random layers from `rng.spawn(1)[0]`: the main stream, and so every other random element of the art,
  stays as it was (the colour art and material map came out byte-identical).
- Raster slits: the template's side view leaves texel slits inside a panel where faces meet edge-on or the subframe
  tube leaks through. Art mapped only onto the panel's part id leaves them plain red: red cracks through the 114.
  kit.json `"close_slits": true` gives the panel the enclosed holes of its mask that no other kit part owns
  (left 369 slit texels to 0, right 53 to 0; test_kit counts them).
- Right side by the same script: zones from the mirrored geometry, each word placed by F M F_src (mirror the
  placement and the word's source about its own box centre), so det > 0 and it reads normally. Test the determinant,
  the mirrored place, and that the right art is not the left one flipped (IoU).
- Inner and back faces: a projected livery lands on both skins of a shell (round 1 showed the right panel's inner
  skin, a mirrored VENTER, behind the shock in sp03). `kit_faces.py`, called by `build_bike.kit_materials` for every
  kit part, gives them the part's plain plastic. Shells: a kit face is inner when another face of the same part lies
  within 6 mm in front of it along the projection and parallel to it (|n1.n2| > 0.8); do not trust normals, not all
  shells are wound outward. Single surfaces (THIN, solidified inward): decide per CONNECTED SURFACE by the
  area-weighted vote of n.d (per face, a fork guard wrapped round its tube split 83/14 percent), and let the
  Solidify modifier's `material_offset` put the other side's material on the shell (slots: fronts, then backs).
- Per-texel maps (round 2): kit.json `"mat"` (glTF metallic-roughness: G roughness, B metallic) and `"nrm"` (tangent
  normal, 128 + 127 n), the artwork's size; `kit_canvas.Maps` maps them exactly like the colour into
  `<texture>_mr.png` / `_n.png` (only for textures that have one; defaults: kit.json "material", flat), and
  `build_bike.principled` wires them when the files exist (Separate Color G -> Roughness, B -> Metallic; Normal Map),
  so the glTF carries them. Side panels: laminate 0.12, flake base 0.40, specks metal 0.25 to 0.35, everything else
  the kit default 0.34.
- A camera fitted to one of his photos is a standard view: `fit_dv.py` (landmarks: art px of the panel's graphics
  placed on the model's outer skin, plus a few model points, seven unknowns with a weak lens prior) writes
  `research/bike-cameras-damien.json`, build_bike makes each entry a camera with the photo's own size
  (dv03_left_rear), test_bike refits it against the current model.
