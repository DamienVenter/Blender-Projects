---
name: rider-modelling
description: How Damien the rider is built (body from MakeHuman's CC0 data shaped to his measurements, skeleton, pose, Leatt gear) and checked. Use before changing motocross-whip/scripts/rider or modelling any person or riding gear.
---

# Rider modelling (motocross-whip/scripts/rider)

## Body (2026-11-13)
- Source: MakeHuman's base mesh, shape targets and default skeleton with skin weights, CC0 since 2020
  (static.makehumancommunity.org FAQ "What changed regarding the license in 2020"). They ship inside MPFB 2.0.18
  (extensions.blender.org); `tools/fetch_makehuman.sh` downloads it pinned by sha256 and keeps only data/ in
  ~/.cache/makehuman. MPFB's own code is GPL and is not used: `mhdata.py` reads the files.
- Hosts from the build server: github.com is refused by the proxy (403); files.makehumancommunity.org,
  static.makehumancommunity.org and extensions.blender.org work. The "system assets" zip (280 MB) has skins and
  clothes but NOT the base mesh and targets: those are in MPFB's data/.
- Formats: base.obj in decimetres, y up, facing +z, left at +x; one vertex list for the body and the helpers
  (groups 'body', 'helper-*', 'joint-*'), and targets index that list. Targets are gzip text "index dx dy dz"; the
  average shapes are empty files. Rig JSON numbers are in "MB" = metres, z up, facing -y: MB = 0.1 (x, -z, y).
  Joint strategies: CUBE (centre of the joint-<name> helper cube), VERTEX, MEAN. Our default shape reproduces the
  rig file's joints within 1.9 mm (test).
- Macro rule (macro.json): each slider splits into its two neighbouring named levels with linear weights; the shape
  = base + race x gender x age targets + universal-gender-age-muscle-weight + height/... + proportions/...
  (+ breast/... for female shapes).
- His numbers: 1.85 m, 80 kg body (gear separate, 8.5 kg), lean athletic, age not given (25). The skin is closed
  (no boundary edges), so mass = (volume - 3.1 L gas) x 1.065 kg/L, exact. The weight slider is solved for it,
  the height slider for the stature. MakeHuman's "average" man at 1.85 m weighs 68 kg (BMI 20) and more muscle
  makes it tighter, not bigger: his BMI 23.4 needs weight about 0.67 with muscle 0.75.
- Proportions vs Drillis and Contini: legs within 1 to 3 %; acromion to fingertip 0.80 m vs 0.81; MakeHuman puts
  the elbow joint high (upper arm 27.5 cm, forearm 28.3 cm): reach is right, the split is not. Hip joint centres
  22.7 cm apart (wide). Watch both when posing.
- Blender: build_rider.py makes the mesh (UVs per face corner, smooth, subsurf 1), the armature (heads, tails,
  rolls, parents, connect flags from the rig file) and vertex groups, under an empty "rider" turned +90 deg about
  z so he faces +x like the bike.

## Pose on the bike (2026-11-13)
- Contacts come from the bike model in its ground frame (parts.to_ground): grips 60 mm in from the bar ends
  (0.914, +-0.352, 1.228), peg tops (0.551, +-0.179, 0.446), seat top about 0.98 at its low point (x 0.53). The
  boot sole (25 mm, estimated) lifts the ball of the foot off the peg.
- pose.py writes targets; build_rider.aim_pose turns them into bones: pelvis tipped and moved (hip joints'
  midpoint), the trunk's extra lean shared over spine05..01, the neck and head brought back to look ahead,
  two-bone IK for legs and arms with pole directions, each MakeHuman split bone (upperleg01/02, lowerarm01/02)
  aimed at the same joint, fingers curled. Hands land within 0.3 mm, feet within 9 mm.
- His photo 05 (seated, stopped) has a fitted camera (research/rider-cameras.json, 6 bike landmarks, 5.3 px rms;
  a telephoto from 7.5 m). Through it his body sits right on the bike (thigh, knee, peg foot, reach). The boot on
  the ground there is his RIGHT foot on the far side: a ground point that "lands on the wrong side" may simply be
  the far foot. It is out of reach with the bike upright: the bike leans onto that foot, and the lean cannot be
  fitted from axles, contacts and grips (it trades against camera roll).
- Photo 07 (panning, seated riding) cannot be fitted from the axles, contacts and fender tips: with him on board
  the suspension sags (the rear fender tip sits 13 px above the front tip where the unladen model has it 0.19 m
  higher). A free sag pitch and drop make the fit degenerate (camera underground). Needs more frame landmarks, or
  the bike posed with rider sag. build_bike's cu_p07 camera was placed by eye, never overlaid.
- Read pose renders carefully: a scaled sheet fooled me into "both poses are identical"; projecting the joints onto
  the render (world_to_camera_view) showed the skin follows the skeleton exactly.

## Helmet and goggle (2026-11-13, `helmet.py`, ledger `research/rider-ledger/helmet.md`)
- **More views of the same shell**: us.leatt.com product JSON of older colourways (V25 Royal, Glamis, ...) carries
  near-orthographic Left, Right, Back, Top and Turbine views of the 8.5; MY27 kits show it with the goggle on
  (grey background, no alpha). Same shell: compare outlines first.
- **Scale from a known part**: the goggle strap (45 mm, Leatt spec) measured across its run in a side view with the
  goggle on; carry it to the alpha-matted profile by a similarity fit of the outlines (chamfer, 18 px). Allow for
  perspective (strap 0.13 m nearer the camera than the centre plane: about 9 %). Cross-check: the top view scaled
  by the profile's length put the visor tip 3 mm from the profile's.
- **Shell as a width field over the side profile**: x = +-hw(y, z) over the traced profile domain; rims (centre
  plane) and free edges (face port, lower edge) are parts of the outline; hw = W(z) Q(y) f(d_rim / L) with a
  superellipse falloff, fitted to the back and top silhouettes by least squares with a smoothness penalty
  (alternating multiplicative updates oscillate). The nearest-rim distance has creases on its medial axis: smooth
  the field away from the rims (Gaussian, 10 mm). Rings of vertices at falloff-even offsets from the rims.
- Collinear outline points at a rim/edge corner give Delaunay slivers whose winding flips: drop |area| ~ 0.
- **Fit on the head**: port top edge 40 mm above the eye centres, then pitch and fore-aft for an even stand-off
  (51 mm all round on his head); the shell came out pitched 18 deg nose down from Leatt's profile photo.
- **Graphics by projection**: fit a pinhole camera to each product photo against the model's outline (Powell then
  Nelder-Mead, about 2 min a view), rasterise an atlas (islands by face normal), sample each texel from the views
  that see it (cos^4, depth buffer from the texels themselves), mirror point as fallback. Mask anything in front
  of the helmet (the goggle in iso-right). Studio reflections come along: replaced by the traced, redrawn print
  (helmet_art.py, section below).
- **The big side LEATT in Leatt's iso-right and his photos is the goggle strap's print**, not the helmet's.
- Text on a strap reads correctly on both sides from outside if it runs in one direction from the left outrigger
  round the back. An outrigger face seen from the other side mirrors its UVs: give each side its own image half.
- A head pitch put on the head bone alone drives the chin bar into the throat; share it over neck01-03 and head.
- Test closure and orientation of the solid (every directed edge once each way) before trusting winding numbers.

## Helmet art: clean flat print (2026-11-13, `helmet_art.py`, ledger research/rider-ledger/helmet.md section 3)
- **Measure the print in the photos, never copy their pixels.** Trace: de-light each view (second-order SH of
  the normal fitted to the white base, robust, then a local white correction), give each texel ONE owning view
  (cos^2 times preferences; blending two misregistered views doubles edges), class the de-lit colours into the
  inks, smooth and vectorise the class maps; design gradients become fitted colour fields inside their region.
  Draw: polygons, fields, then logos from Leatt's own files and procedural parts. The old projection had a
  luminance spread of 40 levels inside the white base; the drawn print has 0.
- Moulded black plastic (grip panel triangles, chin vent mesh, port trim) catches the studio light as grey and white
  streaks that class as white print: hand-mark those regions once on one photo (FORCE), applied to each texel's
  design point (the mirror for the other side). A hand-mark sets the region, never the colour: fit the colour
  fields only from texels whose own colour is that ink.
- A view shows other things where the camera puts the shell: the visor seen from behind in the back view, the back
  band and spoiler seen edge-on at the top view's far edge. Mask them per view (NOT_SHELL) or they land on the
  crown as streaks. Small classed islands under 3 mm^2 away from an island edge are glints: refill them.
- **Check every camera against the print's centre line, not only the outline.** The back camera fitted to the
  outline alone sat 6.9 deg yawed and 4.9 deg rolled (the centre line 25 to 125 px off, the back LEATT drawn 16 mm
  off centre) and nobody saw it, because renders through the same camera look right. One more term (rms offset of
  the shell's x = 0 line from the stripe's stem) gave an upright, straight-behind camera with a BETTER outline
  (chamfer 9.0 against 11.2 px). The front-iso cameras could not be fixed that way: matching the brow badge cost
  4.7 px of outline, so their 14 to 17 mm offset at the brow comes from the shell's estimated front shape.
- An official file laid on a surface whose shape differs from the real one fits badly (visor LEATT IoU 0.49 even with
  a free aspect) and eats the print round it: trace such a mark instead and say so.
- No seams: colour the elements per texel from the texel's own 3D point (they run across island edges), take the
  polygons' own colour where they only partly cover a texel (nearest colour where none does), and bleed every
  off-island texel from the nearest island texel (distance transform indices).
- **Clear coat in Blender 5.2's Principled BSDF does not switch off the base's own specular.** A base at rough 0.22
  under coat 1 added a soft satin glow round the sharp coat highlight (test spheres). For print under a clear coat
  set Specular IOR Level 0 (the print/coat interface reflects next to nothing), coat IOR 1.5, coat rough about 0.03.
- Prove a quality test on the bad case: the flat-print test (luminance spread under 4, local deviation over 2 on
  under 5 % of the white and black interiors) passes the drawn art and fails the old projected texture.
- **Review at 1:1, not only at sheet size.** Renders through the fitted cameras at the photos' own 1920 px, cropped
  beside the photo, showed what 500 px sheets hid: ragged visor chevrons, white dashes across the stripe, iso-traced
  copies of the chevrons 10 to 25 mm off. (`py/crops.py` in the helmet3 scratch: 480 px crops, photo | old | new.)
- A small repeated mark seen square-on in one photo (the visor's chevrons, top view, 4 px per mm): vectorise it
  from that photo (sub-pixel contour at half contrast, Douglas-Peucker 0.6 px) and project it through that camera,
  and let that view own the surface (VISOR_PREF); traced through a mixture of views on a surface whose slope
  differs, it came out ragged and doubled.
- Moulded detail shows in a photo as shading (a crease, the shadow under a raised edge, a vent recess lit pale
  blue): mark the region white where the model has no such shape (FORCE_VISOR), or it is baked in as paint.
- **Atlas-space smoothing mixes unrelated surfaces at island edges.** On a rippled slope faces alternate between two
  islands (crown's back: T and B), leaving thin fragments; their region and field colours came from whatever lay
  next to them in the atlas (light teal lines), and the faces nobody saw stayed white base (dashes across the
  stripe). Fix: an unseen texel within 3 mm of a seen one takes its colour (on the shell, KD-tree), and island edges
  and fragments under 160 mm^2 take the nearest island interior's colour on the shell.
- A gloss coat on a mesh with small ripples shows them as banded reflections (the crown's back seen from the top):
  that is geometry, not print; check it in the old render before blaming the texture.
- **No ink is lighter than the white base.** A de-lit colour above it (any channel over 255 with white at
  226/229/235) is a reflection or the shading fit extrapolated to a face turned away from the light: that view must
  not own the texel. Without this rule the iso-left view of his rear lower side (facing down, dark magenta in the
  photo) drew a saturated pink glow that no highlight test caught.
- **A hand-mark sets a region, never a colour, and a texel no view owns has no colour.** Fit colour fields only
  from texels a view owns. The stripe's end on the back is hand-marked teal, masked in the back view and seen by the
  top view only edge-on: its unmeasured colours entered the teal field as a pure white glow.
- Splat the texture into a view at its own resolution (one point per texel). A half-resolution splat samples bleed
  texels at island edges and shows white dashes that are in neither the texture nor the renders.

## Goggle round 2, eyes, brow badge (2026-11-13, `goggle.py`, ledger research/rider-ledger/goggle.md)
- **Leatt shows the Velocity 5.5 alone only from five angles** (ISO, Front = the same angle, Back, Exploded,
  lens) in all 70 colourway images. The views that measure it are the MY27 8.5 kit's ("Velocity 5.5 goggles are
  included"; moto-8-5-helmet-kit): four sides with the goggle on the same shell. The kits' image order differs by
  colourway (Blue_Red _3 is the right side, _4 the back): check each.
- **Camera fits to a shell model carry the shell's errors**: front-iso cameras fitted to the helmet silhouette put
  the goggle 20 to 60 mm off sideways (the shell's estimated brow and chin bias them); the near-orthographic side
  views agreed within 2 mm. Measure depths and heights in side views (back-project the mask onto x = 0) and take
  only shapes from oblique views, averaged left and right so a common bias cancels. A 50-parameter silhouette
  optimisation over all views wandered into nonsense (an outline point at -600 mm): fix what the side views give,
  then compare by overlay.
- Fitting cameras: grid-start (az, el, roll; scale and shift from the masks' area and centroid) before Powell, or
  it walks off to a wrong azimuth. Ignore the face port (the goggle) and z-buffer the goggle against the helmet
  when comparing it (numpy rasteriser); the photo's goggle = red components mostly inside the grown port zone.
- **A projected texture doubles detail where the model's depth is wrong**: the brow badge under the visor stands
  16 mm ahead of the real brow, so the two side views put "LEATT" 19 mm either side: repaint such details by script
  from back-projected outlines, each view centred on itself.
- Goggle shape: a lens cylinder (ellipse plan) with outlines in (arc length, height); the frame is rings round its
  cross-section swept along the outlines. Outlines as straight runs with 5 mm fillets look moulded; a smooth spline
  through the same points looked generic. Add support rings 0.35 mm either side of every edge or smooth shading
  turns the bezel into a tube. The Velocity's nose: the opening arches up (19 mm), the bridge hangs in front of the
  nose to the beak, the frame is shallow there and the foam runs on the opening's edge (the first foam sat on his
  nose tip). Outrigger LEATT: letter tops towards the strap on both sides (reads up on his right, down on his left).
- Colour under the studio (white world, AgX): saturated flat colours render pastel; a goggle frame base of
  200/6/70 rendered 188/85/97. Take a darker base and check the render against the photo's hue (round 3 below).
- Purple mirror lens: metallic 0.94 on a purple base with a 430 nm thin film (IOR 1.33) reads deep purple square
  on; test swatches first (curved strips under the studio), the film's colour swings fast with thickness.
- **Eyes**: MakeHuman's eye proxy is fitted to helper vertices (not in body.npz); rebuild the shaped mesh from the
  body's macro (body.npz meta) to get them. The proxy eyeball is a 15.8 mm sphere (larger than anatomy) at the
  helper sphere's centre: that is where his lids close round it. A separate refracting cornea dome over a painted
  iris looked like a glass bead: bulge the eyeball itself over the iris and give it a clear coat.

## Goggle round 3: the shape pass (2026-11-13, same files)
- **A product shot of the item alone is a calibrated view once a camera is fitted to the item's own silhouette**
  (here Leatt's ISO, 5.3 px/mm): grid, then Powell at 240 and 480 px on IoU + edge chamfer both ways, the strap cut
  off in both masks. Then back-project photo pixels onto the model's lens surface to read (s, z) per control point
  and move each one along its normal; refit the camera on the final shape. Elevation is the weak axis of an
  oblique single view (el -5 and +8 cost almost the same): take heights from it, depths from the side views.
  Check the Blender render of that camera against the numpy projection (IoU 0.997 here) before trusting a sheet.
- **Round 2's "rounded tube" came from the cross-section, not the outline**: the Velocity is a narrow flat front
  rim (3 mm, 1.5 mm proud of the lens) round a lens that fills the front, then flat faces with crisp 0.8 mm
  edges: a band rising back to the outline edge (8 to 10 mm on top and the tall side faces, 3 to 4 at the cheeks),
  a top surface, a 1.5 mm step to the vent row. Keep each face's rings separate with support rings.
- **Kit-photo outline errors: compare edges, not filled masks**, and align first: the red frame in a photo is a
  ring (the lens is clear), so filled-silhouette IoU said 0.2 for a good fit. Edge-to-edge chamfer, both ways, raw
  and after a 2D shift + scale (removes the helmet-fitted camera's bias, 16 to 30 mm in the front-iso views);
  photo edges over 15 mm from any model edge are clutter (strap stripe). In the Blue/Red kit the frame's side faces
  are not red, so model-to-photo in the side views is inflated there: read photo-to-model.
- Colour from his daylight photos, not Leatt's studio: his 08/09 frame median 165/20/54 (hue 346). AgX turns reds
  about +9 deg towards orange and caps saturation near 0.61: set the base bluer (150/0/58, hue 337) and measure the
  render's hue in the same view (347).
- Lettering: use Leatt's own logo file (us.leatt.com header logo, transparent PNG) stamped at its own aspect into
  the textures (strap, outriggers: mirror one half exactly) and as small cells on the frame; never redraw it.
- Clearance: his nose tip sits 5.6 mm behind the lens front at the notch: the frame there can be 5 to 6 mm deep
  only. Foam: march it along the lens normal from a 13 mm band inside the face opening (march tolerance 2.5 mm,
  fill misses from the neighbouring rows) or it pokes through his cheeks.
- render.sh needs its full output path: with an unset `$W` it wrote to /r3w/his at the filesystem root.
- **Worn gear is not the product shot: check every join where two parts meet on the body.** The goggle fitted
  alone to Leatt's ISO had its outriggers 22 to 41 mm inside the helmet shell and the strap starting 30 to 40 mm
  further out on the shell; Damien saw it at once ("not properly connected to it's strap"). Keep the free shape for
  the product-shot comparison and build a worn shape on the helmet (goggle.outrigger_grids(mount=shell_mount(prof)):
  the outriggers draped over the shell, the strap anchored inside their back ends). Plot the parts in plan and side
  view (shell grey, frame red, outrigger black, strap magenta) before rendering: the gap is obvious there.
- **Head close-ups in any pose: `head_closeups.py RIDER.blend OUT`**. Its views are set once in the rest frame
  (rider at the origin facing +x) and carried with the head: posed = helmet_shell.matrix_world @ Rz(90)^-1 (rigid
  parts' mesh coordinates are the MB rest frame). `cam07` renders through photo 07's fitted camera, cropped round
  the head. Whole rider on the bike: build_rider.py with RIDER_BIKE=blend/bike_v6.blend::kit7, the seated pose,
  and gear npz files rebuilt from main (helmet.py, kit.py regenerate their textures byte-identical); its
  rider.blend is already packed, compressing it saves little (86 to 85 MB).

## Goggle round 4: joint fit on five goggle-alone photos (2026-11-13, goggle.py, goggle_views.py)
- **Fit the shape and all the cameras together, and pin the cameras with landmarks.** Silhouette-only cameras slid
  sideways about 20 mm (the icon landed 22 to 34 mm off centre) and the shape grew lopsided to follow. Four
  hand-picked points fixed it: the Leatt icon (top band front edge, s 0), the nose arch's top (s 0) and both
  tear-off stud heads. Their model points come from the shape (goggle.photo_landmarks), so they also hold it.
- **Read what the photos say about depth before fitting the outline**: the Velocity's lens is recessed (the frame's
  front face stands 8.8 mm proud of it; round 3 had 1.5 mm). Free the globals (lens plan a, A; lip) or the fit
  bends the outline to make up for them. The height origin is free in a photo fit (a common z shift costs nothing):
  fix it on the helmet (PLACE) and re-check his nose, since a recessed lens sits further back on his face.
- **Masks lie in clear-lens photos**: the frame's inner walls and the frame-coloured nose guard show through the
  lens. Use a white-frame render at the same camera (Leatt's 39278 shares the Pinata ISO's) to keep only the faces
  seen directly, mask the nose guard with ignore polygons, and use a photo whose frame and outriggers are the same
  colour (white) as a silhouette only.
- **CMA on 30+ control points needs a leash**: without it the steps crossed, the band went negative and the lens
  edge zigzagged. Penalise the lens edge leaving the outline (1.5 mm minimum), self-crossings and spikes under
  35 deg, clip the band to 1 to 16 mm; then hand-clean the result and refine with a small sigma (0.4).
- **Crease terms need named facets**: give each band face a crease ring (RING_MID at mid_t, offset mid_w) and fit
  its position; the logo then lies on the two facets either side of it, not on a flat chord through them.
- Result: outline medians 1.3 to 2.2 mm, creases 0.5 to 1.5 mm, IoU 0.92 to 0.95 (round 3: 1.5 to 3.1 mm, IoU
  0.86 to 0.91). At 0.5 photo scale (2 to 3 px per mm) 1.5 mm is near the resolution: a 1 mm target needs full
  resolution, an unseen side photographed, and the vent sawtooth and nose ribs modelled.
- goggle_views.py renders the free goggle at every fitted camera: the backdrop through Light Path "Is Camera Ray"
  (strength 5.0 renders Leatt's grey, about 234 under AgX) while a dim world lights the goggle.
- The flat 7 mm nose-guard drop hung below a shorter arch's legs: scale it to the arch (0 at the legs).

## Goggle round 5: full-resolution fit on nine photos (2026-11-13, goggle.py, ledger goggle.md)
- **Fit edges, not masks, at full resolution**: a Gauss-Newton ICP (model edge pixels matched to photo edge pixels
  of the same orientation, Huber weights, a trust cap on each step) with one normal offset per outline sample on
  top of the control points took the outline medians from 1.3 to 2.2 mm to 0.2 to 0.8 mm. At half scale (2 to 3 px
  per mm) a 1 mm target is out of reach.
- **Clear lenses show the inside**: drop photo edges more than 3 mm inside the model's lens window from the
  photo-to-model term (the nose ribs, inner walls and foam seen through it); keep every model edge.
- **Read landmarks and test numbers off what is built**: once offsets move the outline, the bare control points
  are no longer the frame (photo_landmarks put the nose arch's top 10 mm off in iso45 until it read the built
  outline). The same for tests: measure the built outline (test_goggle.edge_z).
- **The photos give the shape, never the size**: with the camera distance fixed and the focal length free, the fit
  shrank the goggle 5.5 % (every f grew 4 to 8 %) with nothing to stop it. Check an absolute reference after every
  fit: the 45 mm strap beside the outrigger (measured at the outrigger's depth) and the calibrated kit side views.
  They disagree here by 12 %: the size is a question for Damien (measure the frame).
- **A fit without landmark terms lets the cameras slide** (tear-off studs 1.5 to 5 mm off afterwards): refit the
  cameras with the landmarks (shape fixed) after the shape fit, refit the shape with those cameras frozen
  (fit5.py FREEZE), then refit the landmark cameras once more and remeasure.
- **A sibling model is not the same part**: the Velocity 4.5 render fits its outline to 0.4 mm with a camera that
  puts its nose arch 10 mm and its studs 4 to 5 mm off the 5.5's, and no camera fits both. When the outline fits
  and the landmarks never do, the part differs there: keep its outline, drop its landmarks, say so.
- **Offsets of a fitted outline loop at its sharp corners**: per-sample offsets give the outline sharp inward
  corners, and growing it (the lens edge 3 mm under the frame) made small loops there that triangulated as
  see-through wedges (white "teeth" at the nose arch in the Blender render, invisible in the numeric errors).
  Cut the loops (goggle.untangle) and test every grown loop for self-crossings; look at the Blender renders
  close up, not only the error table.
- **Never re-centre the goggle on the helmet without the clearance checks**: lowering round 5's smaller frame
  2.5 mm to centre it on the side views put the lens's lower corners into the shell's eyeport edge and his nose
  bridge into the frame. Check the lens against the shell and the skin against frame and lens (scratch
  shell_diag.py: winding numbers) for each candidate place before writing PLACE.
- **Colour on him: compare against a white reference in linear light, then switch things off.** The frame / shell
  ratio per channel in his photo and in the render of the same view says whether the albedo is wrong; rendering
  with the frame's specular off (and the Standard view) isolates the albedo. Here the albedo matched (0.416 vs
  0.37 to 0.42 in red) and the washed-out raspberry came from the soft studio's white sheen on a glossy frame
  (+0.05 of the shell in every channel); his photos are daylight. Do not retune an albedo to fix the lighting.
- Sort a product's back or front photos by camera: scale each silhouette to the same area, centre it and compare
  IoU pairwise (0.96 to 0.98 shared rig, 0.92 to 0.95 its own angle).

## Goggle round 6: fair by construction (2026-11-13, goggle.py, test_goggle.py, ledger goggle.md section 8)
- **Look at a 1:1 crop before calling a surface done.** Round 5's numbers were good and its 1100 px sheets looked
  fine; at native resolution the frame read as crumpled, melted plastic. Per-sample outline offsets and
  per-control-point section values let every sample pull the surface on its own (overfitting): the error table
  cannot see it, a crop and a raking light can (goggle_views.py rakeT / rakeB / rakeL / rakeR).
- **A moulded part's freedoms are smooth curves**: every crease, edge and section value is a low-order curve along
  the part (goggle.bspline_half: a uniform cubic B-spline over the half loop, mirrored at the centre line so it is C2
  across it; 24 coefficients for the outline offsets, 16 for the fields), corners come from the control polygon and
  its fillets (the offsets held near 0 at the control points), and the fit carries a bending penalty (second
  differences of the coefficients). Same lesson as the bike's side panel (bike-modelling decision 37).
- **Measure fairness, and test it so it fails on the bad mesh** (test_goggle.frame_fairness, between corners only:
  fillet samples and tooth steps left out): along each ring the change of turning angle sample to sample (dturn)
  and the ripple off a local quadratic through 9 samples; across each face strip the normal's kink against its
  neighbours and its wave off a running mean. Round 5 / round 6: dturn 9.1 / 0.5 deg, ripple 75 / 9.4 um, kink
  3.0 / 0.6 deg, wave 6.0 / 0.5 deg.
- **A fairness test that skips corners cannot see a fold at one**: after the fit, the 1:1 crop still showed a pinch
  at the nose arch's apex, where the face narrows to 1 mm but the rim and chamfer rings sat 4.2 mm out from the lens
  edge, so they ran past the outer edge and the face folded back. Place rings across a face as fractions of its
  width, or cap fixed widths by it (frame_rings: rim and chamfer at most 0.85 of the width), and test the order
  across the face (test_round6_front_face_does_not_fold: consecutive steps across the face turn by under 90 deg;
  the fold read 111 to 117 deg, the designed edges 67 at most).
- **Write fitted numbers with enough digits**: GP at 4 decimals (0.1 mm) quantises smooth coefficients into steps
  that show as ripple; round 6 writes 5 (10 um).
- **Weak bending lets a field fold**: at a third of the bending weight one field ran into its neighbour (the top
  surface's back edge onto the outline edge: a sliver face, kink 90 deg). Keep ordered fields apart coefficient-wise
  (enough for a shared B-spline basis: the curve is a convex mix of its coefficients).
- **Hold weakly seen fields near their evidence, not just smooth**: with the bending penalty alone the section
  fields that the photos see only edge on (lip, rim, depth, the face crease's mid_t / mid_w) drifted in a few
  iterations (lip 3 mm, the crease to its limit, depth 9 mm at the top centre) and broke the shape and side-profile
  tests. A ridge of every field to round 5's values, converted and lightly smoothed (fit6 XREF / LAMX), keeps what
  the photos do pin and lets the rest stay put.
- **Freeze the landmark views' cameras from the start**: the ICP has no landmark term, so with those cameras free the
  shape and cameras slide together and the landmarks walk off (phr posts 3.5 mm). Starting from the last
  landmark-fitted cameras with FREEZE on iso55, phy and phr avoids the refit-and-refit-again loop.
- **A p90 can be held up by something that is not modelled**: phr's photo-to-model p90 sits on the far outrigger,
  swung open in that photo and closed in the model; round 5's overfit bulged the frame's far pillar towards it and
  scored better. Split the p90 by where its pixels lie (scratch p90parts.py) before trading fairness for it. A p90
  over a small pixel set is fragile too: iso55's photo-to-model crease p90 (275 pixels) rests on 28 of them.
- **Huber at 3 mm, not 1, when p90 must not get worse**: at 1 mm the tails weigh almost nothing and a smooth fit
  trades them for medians; at 3 mm the p90s held. Apply the hard limits to the start as well as to each step, or a
  start outside them stalls the fit at iteration 0.
- **Gloss from the photo, measured**: inside the frame's mask, the highlights' edge width (25 to 75 % of the way to
  their top along the gradient), their area above 2.5 x the median, and the white (min of R, G, B) part's median as
  haze. Roughness 0.4 gave 4.0 px edges against Leatt's 2.4; 0.05 gives 2.5 with the studio's lights at 1 m (2 m
  lights spread every highlight over 15 % of the frame). A clear coat over a rough base does not help: the base
  still hazes every face.
- **Daylight for his outdoor photos** (head_closeups.py light "daylight"): a 0.53 deg sun lamp plus Blender 5.2's
  multiple-scattering sky with its own disc off; the sky's strength from the clear-sky diffuse fraction (about 12 %
  of the global light at a high sun) and its measured light on a horizontal plane at strength 1 (14.9 at sun
  elevations 60 to 75 deg); a ground colour below the horizon (albedo times the light on it over pi). Blender's sky
  convention, checked with a lamp and the sky on a matte sphere: sun_elevation = asin(d.z), sun_rotation =
  atan2(d.x, d.y). Aim the sun per view in the camera's frame from the photo's own shadows and shading, and set the
  exposure from a white reference (his shell), as his phone did. AgX compresses the highlights, so the linear ratio
  undershoots: +1.3 EV left his white shell at 0.45 to 0.51 (linear) against the photos' 0.84 to 0.86; +2.0 gives
  0.55 to 0.59 with the frame and sky still holding colour (+2.6: washed out).

## Goggle round 7: Leatt's details at 1:1 (2026-11-14, goggle.py, test_goggle.py, ledger goggle.md section 9)
- **Model every part the photo's silhouette contains before fitting outlines near it.** The nose arch fitted as a
  pointed V for three rounds because the photos' arch outline includes the black nose guard and the foam, which the
  model lacked: the frame bent to cover them. With the guard modelled (a closed rubber shell, NG_KEYS), the arch
  came out round-topped. A landmark can carry the same error: NOTCH had been picked on the lens edge's top
  (z -31.7 mm), not the frame's arch top (-38.2 to -39.1).
- **A capped ICP ignores what starts too far away**: arch photo points more than the cap (8 mm) from the start got
  zero weight and the fit narrowed the arch further. Move the start within the cap (by hand, from back-projected
  points) before fitting.
- **Hidden parts get no gradient from a silhouette fit**: the far outrigger behind the pillar in phr never moved.
  Check such parts by projecting them (all vertices, hidden or not) and say plainly what the photos cannot pin.
- **Crease width, measured**: across each designed crease, the 10 to 90 % width of the shading step at 1:1 (probe
  points on the photo), against the photo's own blur (a silhouette edge's width); predicted width =
  hypot(0.8 x the crease's projected span, blur). Leatt's creases turn in 1.2 to 2.4 px (0.2 to 0.4 mm): a 0.1 mm
  support ring each side of every ring and a 0.1 mm land at the top crease, so shading is flat inside each facet
  and turns only at the crease. Round 6's 0.35 mm support rings and 45 deg chamfer read as soft, inflated plastic.
  A fixed 45 deg land on a crease whose facets are nearly coplanar draws a false dark line (the arch's face): let
  the land follow the facet behind it where that facet is shallower than 45 deg.
- **A control point that does not turn needs a token fillet**: fillet_closed gave it d = 0, two identical points
  and a NaN normal downstream (the foam's march). Such a point is free to slide along its line without changing the
  outline, which makes it a handle on how two outlines pair up (next point).
- **Rings ruled between two outlines pair them by sample index**: where the lens edge's corner sits at another
  height than the outer edge's control point, the rulings sweep along the face and every offset ring wobbles (the
  pillar's chamfer failed fairness at 33 um ripple; the crease bent 0.5 mm). Moving the collinear side_end to the
  lens edge's corner height (outline unchanged to 60 um) made the rulings run across the pillar: ripple 7 um.
- **Re-check a jointly fitted part once the rest has settled**: the nose guard's sweep, fitted at 10.2 mm while the
  arch was still being reshaped, left the backdrop showing inside the finished arch's far leg in phr, phy and phw
  (Leatt's guard fills it). A one-key sweep through the error table on the finished frame (scratch ngsweep.py) put
  it at 3 mm: the fit views' outline p90s fell 1.0 mm in sum. Look at the 1:1 crops of every part, not only the
  part you changed last. Test such a fix in the views that showed it: the guard's front-view test passed at 10.2 mm;
  rasterising the frame and guard with PIL at each photo camera and counting the arch's uncovered pixels
  (test_round7_nose_guard_fills_the_arch_in_the_photos, about 1 s) catches it, and the test asserts the old value
  fails so the check is known to be live.
- **A worn soft part gives way to the face**: the nose guard's back sheet cut 10 skin vertices beside his nose
  bridge; on him it comes forward by up to 7 mm where needed (goggle.guard_clear), like the nose ribs.
- **Validation cameras are refitted to the final shape before the table**: frg and chee left at round 6's cameras
  read 0.3 mm worse in median for the camera, not the shape.
- **Check the ledger before calling a photo held out**: the white ISO was already a round 4 source (creases, teeth,
  ribs at iso55's camera), and the MY27 kit Blue_Red views were the placement, scale, top lip and outrigger sources
  of rounds 3 to 5. Grep the ledger for the file's SKU before the check; say so in the report rather than claim a
  clean hold-out.
- **On-helmet camera fits in the goggle frame**: fit the camera to the helmet's silhouette with the mesh taken into
  the GOGGLE frame by the head transform (helmet.build's Rt), so az and el read like the goggle-alone cameras and the
  grid start works; render by moving the mesh so the camera's target is the origin (goggle_views looks at it).
  Fitted to our shell (not Leatt's to the mm) such a camera carries several mm of error: read the goggle's position
  from the side views (az +-96 deg), not the oblique one (the front iso left view put the frame 13 to 15 mm off, of
  which about 6 mm is real).
- **A part's material: check every colourway before believing a description.** The "dark ribbed rubber" in the
  brief is the comb behind the lens, and it is frame plastic: yellow in the Neon Yellow photo, red in the Royal,
  pink in the Pinata, white-grey in the White, black in the exploded view. The dark matte part below the arch is the
  guard.
- **A see-through lens in Cycles** (goggle_views GOGGLE_VIEWS_LENS_VLT): a Principled transmission tints at every
  face and stops the lights' rays, so a double lens (four faces) at a 150 grey tint left 0.3^4 of the light and hid
  everything behind it. Use a Transparent BSDF (tint VLT^(1/4) per face, shadow rays pass) under a Fresnel-weighted
  Glossy. On a back face the Fresnel node uses 1/IOR and, since the see-through does not bend the ray, reflects
  totally past 42 deg: the lens turned into a flat grey mirror where the camera looked through it obliquely. Feed
  back faces a Fresnel at IOR 1/1.5 (Geometry Backfacing). Under AgX a 58 % lens looks paler than in Leatt's
  renders (the bright backdrop behind it is compressed), and Leatt's goggle-alone renders show black behind the
  lens (most likely the far strap, which runs straight back behind the goggle in them) where our free goggle (no
  strap) shows the backdrop. Compare the frame and the comb, not the lens's tone.

## Goggle round 8: the goggle on the helmet (2026-11-14, goggle.py, test_goggle.py, ledger goggle.md section 10)
- **A band over a convex shell is walked across the surface, never a straight chord.** Round 7's 45 mm strap was one
  ruled band: each cross-section a chord, which sagged up to 2.5 mm into the shell (dark blobs in the back view).
  goggle.strap_layout cuts the centre line with a plane, walks each section 45 mm along the shell and offsets every
  layer along the shell's normal (silicone, fabric, edges). Test the signed distance of every vertex AND face centre:
  a rigid 22 mm slide bar cleared at its vertices while its bottom face's centre sat 0.22 mm inside (the chord's
  sag; SLIDE_SAG lifts it). Keep a negative control in the test: the old builder, given the same ends, must fail.
- **His own gear's photos before a stylist's kit photo.** Leatt's MY27 kit views are an empty helmet: the strap
  placed 22 mm higher at the back than his 07 shows, the goggle sitting deeper in the eyeport (no face pushes it
  out). Fit how gear is worn on his photos and Leatt's photos of his SKU; use kit views for shapes and sizes, and say
  which won when they disagree.
- **When size sources disagree, let the body decide.** On the helmet Leatt's views read the goggle 4 % larger, the
  goggle-alone strap up to 6 % smaller. Build the body and test each candidate (scratch kcheck.py: lens vertices in
  the shell, frame in his skin): x 1.02 was the limit, x 1.04 put the lens into the eyeport at every place. Report
  the numbers, pick the largest that fits, keep the question open for the real goggle.
- **Before tuning a hidden part to show, check that it can.** At the silhouette point take the projection's
  derivatives (px per mm in x and y) and ask how far the part must move; if no direction within its reach gets
  there, the parameter is the wrong one (Leatt's far outrigger in iso55 and phr needs a hinge further out, not a
  bigger turn). Check a variant actually changes the mesh before reading its result: a key that is not in GP was set
  as a module attribute and changed nothing; part ids come from gt.PARTS, not a local list.
- **Measure against an in-photo reference at the same depth, with the foreshortening taken out.** The slides read
  24 x 54 mm from a global mm/px and centres that included the grip tab; against the strap beside them (217 px =
  44.3 mm projected) and the strap's 18 deg turn there, 22 x 52 mm, bodies 82 mm apart.
- **Notes under .claude/ go in through a script in Bash** (python open/write), not the Edit tool: an Edit there hung
  an agent for hours.
- **Render a fitted camera before using it.** A camera fitted to an outline alone (his 08: no landmark shows) can
  match the silhouette from the wrong side: the render showed the shell's shaded side where his photo shows its lit
  top. Add a landmark or a prior, or say the view is unusable.

## Goggle round 9: slides, woven strap, hinged outriggers (2026-11-15, goggle.py, goggle_strap_art.py, ledger goggle.md section 11)
- Strap hardware is modelled from the 1:1 back view (MY27 kit back, 0.21 mm/px): flat moulded frames (slabs bent to
  the strap's curve, rounded corners, soft edges), never rods or spheres. Thread the strap as Leatt does (under the
  end bars, the tail up out of the left slot, doubled to the right slide, folded round its bars) and give the folds
  height (3 mm) so the back light shades them. With no photo of a colourway's slides, use the brief's rule and say so.
- Woven elastic: a detail tile (goggle_strap_art.weave_tile: red relief, green albedo factor, Non-Color) repeated
  along u over the print, multiplied in where a mask is white, bumped after the print's normal map. The tile is
  measured (loops 0.65 x 0.45 mm, jacquard 1.9 mm, 19 mm a tile). Turn the denoiser off for fabric close-ups
  (GOGGLE_VIEWS_DENOISE=0): at low samples it smooths the weave away.
- u is s / s_total along the strap on the shell, so STRAP_LEN_UV and the detail repeat must follow the built strap:
  any change that moves the strap's ends (the outriggers) changes its length (618.8 to 645.0 mm in round 9). Rebuild,
  read info["length_mm"], update both, regenerate the textures (`goggle.py --free` rewrites them every run). Measure
  the tile on the printed face's centre line (length over u span); the edges differ by 2 to 3 % because the strap
  wraps a cone-like shell, and a median of per-edge ratios is biased by the stations' density in the bends.
- A layer that leaves the surface (a fold, a roll, a tail coming up out of a slot) needs its own u along its own
  face: mapped by the strap beneath, the tail's rolls stretched the weave up to 4.2 times on their flanks. Test
  every centre edge's face length per u (within 5 %), not only the total.
- Keep goggle_strap's vertex layout (four rows: outer bottom, outer top, inner top, inner bottom edge, one per
  station): test_helmet.py (another agent's file) reads the strap's width from rows 0 and 1. Round 9 broke it by
  building the side faces with a grid helper; the end caps now live on goggle_strap_band.
- One grain level does not fit both strap photos: the MY27 jacquard reads more grain than ours (0.26 against 0.16),
  the Pinata kit photo less (0.14 against 0.19). The Pinata print also renders dull (saturation 0.65 against 0.92):
  it is sampled from Leatt's render and shown under AgX. Calibrate the print against the kit photo, not the ISO.
- Outriggers hinge on the frame's widest point with the OUTER face's front edge on the hinge (with the inner face
  there the plate stands 5 mm beyond the frame in every front photo). 30 mm long (46 read far too wide).
- Free goggles: each Leatt photo lays the strap its own way, so fit each plate's turn per photo and side. The IoU sees
  only the far plate (the strap's cut hides the near plate's back end): set the near plate by where the strap leaves
  it (project the plate's back edge through the fitted camera: iso55 and phr both 0 deg). Measure the far plate by
  the silhouette's edge, not by dark pixels beyond the pink (part of Leatt's black there is the frame's side).
- goggle_views.py per-camera "lights" ([x, y, z, W] per key): the back view needs a key from his right and behind;
  the front rig lights folds flat. The studio's lights are placed only in studio mode: daylight() removes them and
  touching them raises "StructRNA of type Object has been removed".
- Comparison sheets: composite cut-out PNGs (palette transparency) onto Leatt's 236 grey before cropping, or they
  show green. Read his photo 07 at its own resolution too: the 4x render shows weave the motion-blurred pan cannot.
- Blender 5.2.0 and 5.2.3 render the same view pixel identical (Cycles CPU, daylight): one 5.2.0 view is enough.
- Build the goggle from Leatt's goggle photos; do not tune it to the helmet shell's eyeport edge, which the
  helmet agent found 35 to 40 mm too far forward (the brow about 20 mm, decision 44; a joint round moves both).
  Keep the worn-fit tests passing on the current shell and list in the ledger which numbers are worn on it
  (twist, anchor, strap length and so STRAP_LEN_UV, strap fit, clearances, the Pinata plate run).

## Goggle round 10: grain, plate outline, chassis band, comb (2026-11-15, goggle.py, goggle_strap_art.py, ledger goggle.md section 12)
- Fabric detail in Cycles shimmers (no mip-maps): build the tile from the photos' power spectrum (only the waves the
  photos show, nothing finer than about 2.5 px at the closest view), cap the albedo (0.9) and fade the tile by the
  pixel's footprint with a driver on the camera's pixel angle. Test shimmer as two frames (new seed, camera moved 3 mm)
  with and without the tile, the second frame registered back by the no-tile pair's sub-pixel shift (whipcmp.py):
  the ratio should be about 1.
- A band-limited weave from two pure waves reads as long parallel ripples when seen at 4x: the measured spectrum
  has width, so the waves' phase must wander enough (more than 1 rad over 0.8 mm) to break the rows into the
  photo's short twill. Look at the strap at 4x as well as at 1:1 before calling it done.
- A shape's outline from photos: fit its edges where the photo shows them (plcmp.py: edge rms per view) and keep
  the full error table as the check; a better local edge can cost the front views 0.001 of IoU, say so.
- What a dark band in a photo is: compare colourways (black in White, Black and Pinata alike means a separate black
  part), look for what shows through it, then name the ring gaps that cover those pixels (ringvis.py) before
  modelling. Read slots off per-row and per-column luminance profiles, map rows through the part's own surface.
- Shallow pockets must not be glossy inside: a 1.5 mm pocket with a specular floor reflects the studio and reads
  brighter than the face around it; give the inside no specular (spec 0) for a slot's darkness. Check a pocket
  stays in the moulding and off the lens (cross-section inside test, lens offset; slotchk.py).
- A lean seen the same way on both sides of a symmetric part, from one side only, is depth: work out how far a
  point shifts per mm deeper through each camera (combdepth.py) and fit the depth lean where the views agree before
  reading the fan. Check the depth is possible (what lies behind it) before building it; say when it is not.
- The comb's outline is a general (s, z) polygon now (rib_outline, rib_fillet, rib_dense): densify long edges to 0.25
  mm before sheet()'s Delaunay; cut it on him by a level line (contourpy) rather than per column.
- New tests that call a function main does not have still fail on main, but prefer checks through functions both
  have (build_nose_ribs, outrigger_grids, build_frame) so the failure message shows the old numbers.
- Doc patch scripts: find both ends of a slice inside the one section (index(end, start)) and assert the slice
  is not empty. str.replace('', x) puts x between every character (round 10 turned the ledger into 77 MB
  that way; undone with replace(x, '')). Check git diff --stat after every doc patch.

## Goggle round 11: parts inside parts, twill, raised LEATT, chassis clips (2026-11-15, goggle.py, goggle_strap_art.py, ledger goggle.md section 13, decision 49)
- **Test that parts do not run into each other** (test_goggle.goggle_overlaps): weld each part by position, split it
  into connected pieces, require every piece closed (an open or shared edge is a fault), then sample points on part A
  and test them inside part B by ray parity (both directions along one random ray, both odd). A block added inside a
  pocket must be a closed tube inset 0.05 mm from the pocket's walls, or the test reports open edges. Round 10 had 14
  faults (the comb 0.3 mm into the inner lens, the bridge folded round the lens) that no render showed.
- **Inside tests on a traced outline**: a triangle's edge midpoint lying on the outline reads in or out at random;
  nudge midpoints towards the centroid before the test. A ray that grazes a wall counts twice: skip faces along it.
- **Texels are not square**: the strap tile is 0.157 mm along and 0.117 across a texel, so a box sized in texels
  stretched the LEATT 1.34 times (162 mm against 120). Place and measure prints in mm.
- **A weave seen in a photo through a known render**: measure the photo's two families (period, angle) in px, render
  our own known tile in the same view, and use that render to map tile mm to image px (the view's Jacobian there);
  solve the tile's waves from it. Check the sign along the strap's +u: the first solve came out mirrored.
- **Long regular ripples come from coherent waves**: band-limited noise round each wave vector (a Gaussian at +-k in
  the FFT) coherent over 1.5 to 2 periods reads as a soft twill at 4x; a peak holding over 0.6 of the band's power
  reads as ripples (the photo about 0.35).
- **Raised prints are geometry**: Leatt's strap lettering is a layer with crisp walls; a blurred relief in the print
  reads flat and soft at 4x. Contour the mark's alpha, triangulate its top, give it square walls sunk into the fabric.
- **Solve an albedo from a test render**: render at a trial value, read the linear factor (render / albedo), divide
  the photo's tone by it. The print's 236 clipped at 254; 160 rendered 178 (1.27x), so 203 renders 225 as Leatt's.
- **Gloss black reads as its specular**: rgb 14 rendered 37 against Leatt's 19; lowering spec (0.1) and albedo (8)
  got 20 with crisp edges kept. Faces that lean towards the top light (the comb, 22 deg) mirror it at rough 0.05: give
  them their own satin (rough 0.7, spec 0.2).
- **Short features on a coarse run**: whole segments 1.1 to 1.8 mm apart quantised a 3 mm tab to 1.2 mm; interpolate
  along the run to the exact length.
- **Mask renders with the lens out of the way**: goggle_views needs goggle_lens to exist, so move its vertices 50 m
  away in the npz to see what is behind it; never delete it.
- **A fix the worn fit blocks is reported, not forced**: the comb's lean moved the bridge 7 mm back, and on him his
  nose ridge has 3.2 mm where the stack needs 5.8; the worn build notches over his nose and the rest is decision 47's.
- **Check against the latest main before reporting**: main moved during the round (helmet round 3). A trial
  merge (git merge-tree, then the changed files laid over a scratch copy, LFS smudged by `git cat-file --filters`)
  failed the worn overlap test: the new shell moved his nose 3.2 mm back and uncovered a comb/plate clash his nose
  had hidden. A part whose shape switches between two rules (the comb's back held by the plate or free) must be
  continuous across the switch, or the sheet's grid smears the jump into its neighbour; ease it (a cone dilation
  of the difference) rather than move a neighbour that other fits hang on.

## Goggle round 12: strap print in mm, plate hinge, side section, matte mouldings (2026-11-15, goggle.py, goggle_strap_art.py, ledger goggle.md section 15, decision 53)
- **Lay a print in mm from each end, not as a fraction of the length**: u = s / s_total stretched the print by the
  built strap's length ratio, so every worn refit moved the colour changes. strap_u keeps true mm over the first and
  last thirds (where the print changes) and takes up the length difference over the even middle third.
- **Sample a print by a part from the view that sees it best**: the goggle ISO saw the strap's first 30 mm turning
  away (its distances came from the strap's height per column); Leatt's kit iso-right sees it flat. Find the view's mm
  per px from the strap's own width and the built strap's projection, check it on a known length (the T end).
- **Shape or place: render the part placed as the photo's empty helmet has it** (comparison only, PLACE untouched):
  12.6 mm lower and 3.5 mm back our plate read wider still (745 to 870 px against 762 to 840), so the plate's shape
  was at fault. A hinge moved inboard needs a larger free turn to keep the photo's back edge (55 to 64, 65 to 76.5).
- **Read a hidden end through several cameras at once**: 1 mm along the lens normal moves the far end 3.9 to 5.3 px,
  1 mm along the surface 0.15 to 0.5; all three views agreeing put Leatt's lens end 3 to 4 mm further back (a moulded
  curl), not further in.
- **A curl needs room to stay fair**: curling the lens back over 75 to 97 mm rippled the lower band's edge 45 um and
  turned it 2.4 deg a sample (bounds 10 um, 1 deg); a smootherstep over 60 to 99 mm gives 7 um and 0.8 deg.
- **A see-through part seen at grazing incidence shows its reflection, not what is behind it**: the lens curled
  back from 60 mm lay at 81 to 87 deg to the iso55 view over s 72 to 95, mirrored the black wall beside it and read
  dark 12 px early. Trace the incidence (scratch refl12.py) before blaming a material; start the curl late where the
  view sees it (75 mm over the pillar's height, eased to 60 along the bands' edges for fairness), and test the
  incidence (under 80 deg).
- **Keep fitted landmarks where they were when their base moves**: the posts' stud heads are fitted in every photo;
  when the lens under them curled back, a longer stem kept the head on its landmark (moving it failed the landmark
  test by 3.2 mm).
- **Everything grown from an edge must follow the edge when it moves**: the lenses grow their groove from the frame's
  lens edge; when the foot moved out 1.85 mm on the pillars, the lens grown its full groove from it ran 0.9 mm into
  the plate's inner face (the plate turned straight back). Keep the hidden edge where it was (the groove less the
  move, at least 0.6 mm), and check the plates at every turn they can take (0, worn 18.75, free 64 and 76.5).
- **A taller upright face can mirror the key light**: the chassis wall, stood up on the pillars, faced the studio
  key's mirror direction on the lower far pillar: a white patch L 228 against Leatt's 17. Mouldings read matte (spec 0).
- **Classify a wrong tone by the part buffer before changing a material**: the light rim above the comb's tongues was
  the face foam's top (sheen 0.6 glowing at grazing view), not the bridge round them. Foam is matte (sheen 0).
- **A piece standing beyond the silhouette in only some views is often a moving part**: Leatt's black piece beyond
  the frame in phr (two windows, a post on its edge) has the plates' colour in every colourway: the outrigger's front
  wrapping the lens post, the strap seen through its windows (the teal dots in the slots). Modelling it needs the
  strap threaded through it, which is the worn fit's (reported, not forced).

## Boots: Leatt Moto 6.5 White (2026-11-13, `boots.py`, ledger research/rider-ledger/boots.md)
- Which boot a Leatt view shows: work it out from the camera, not the caption. 02 (outer side, buckles, toe
  right) and 03 (inner side, toe left) are both the RIGHT boot; in 06 (soles, toes up) the right boot is the
  image's left one; in 05 (back) the right boot is the right one. Camera on the boot's outer side, toe to the right
  = right boot.
- Never read positions off a displayed image: my first readings of 02 were off by 500 px (the view is scaled).
  Grid crops with pixel labels (`grid.py`-style) or masks by script only.
- Leatt's studio white is retouched: parts of the white boot are exactly the background grey (236, 236, 236), so
  colour or gradient masks bite into the outline (02's heel cup lost 45 mm). Fill such bites from the other side's
  photo in a known band, and check every mask drawn on the photo.
- 02 and 03 are not mirror images of one ortho view: 03's shaft leans 2.5 deg further forward. Use one photo as
  the outline and shear the other when projecting from it.
- Size from his foot: MakeHuman's foot 277 mm > US 9's 27.5 cm, so US 10; sole length = chart foot + 19 mm toe room
  (Gaerne's rule) + walls = 330 mm; that length scales the side photo (0.286 mm/px). Leatt publishes no shaft
  height or sole length.
- His leg against Leatt's empty boot: the calf is 127 mm wide where the closed, empty shaft is 106 mm, and his
  shank leans 6 deg inward in the rest pose (A stance): centre the shaft's sections on his leg and open them for
  the calf (the worn shaft's panels open); his ball needed a 2.3 deg yaw (Leatt's last curves outward) and the
  boot a 2 deg toe-down pitch (heel drop) for his toes to fit the low toe box.
- Shell shape that worked (after CSG unions of sections wobbled): an "inflated side outline". Every point inside
  the side outline carries the shell's half-width there, rounded toward the outline (superellipse over the row's
  depth in the shaft, over 22 mm on the foot). The outline is the photo's back, front and instep lines each a
  robust B-spline that ignores points standing out (buckles, keepers, plates, the spine are parts), not the raw
  mask (the raw outline gave drapes and ripples). Meshed with surface nets (numpy, 2.5 mm, faces flipped outward:
  check orientation numerically, Cycles hides it).
- Graphics by projecting each photo onto the faces that look at it, as PAINT (black where dark, red where red,
  white elsewhere) plus a high-pass normal map, never the photo itself (its shading would be baked). The mirrored
  left boot uses the same UVs with every logo box flipped in place; find the boxes as dark-pixel bounding boxes,
  my hand boxes missed two logos.
- The sole's lugs from photo 06: the moulding's fine texture (local high-pass energy) marks lugs, peg zone and
  logos; the smooth grey between them is the recessed base. Each sole's bottom texture is Leatt's own sole of that
  side (the left's LEATT reads right).
- Clearance in a pose without Blender: skin and boot both linear-blend skinned on a sagittal knee and ankle
  rotation; take each posed skin point back through the boot's blend exactly (per point, the blend is affine:
  invert it, re-evaluate the weights, repeat) and look it up in the shell's field. A plain fixed-point iteration
  diverged at 60 deg of knee.
- Check renders: from +x the camera sees the LEFT boot first; hide the other boot (and the body for soles).

## Gloves (2026-11-13, `gloves.py`, Leatt 2.5 X-Flow Black, ledger research/rider-ledger/gloves.md)
- Leatt's glove size chart is not on the product JSON: the page HTML links
  `us.leatt.com/cdn/shop/files/GloveMen_SizingChart_04-02-2026.jpg` (circumference at the knuckles, hand length).
  MakeHuman's hand at 1.85 m: knuckle circumference 21.9 cm, hand length 21.4 cm (long: 11.6 % of stature).
- Build gear on skin from the skin itself: the glove is the body's hand patch (distal of a clean edge ring) plus
  rings cast from the bone axis, one Catmull-Clark step (the body renders with subsurf 1, so this IS the rendered
  skin), then offset. Keep every gear vertex as a sparse combination of body vertices: its skin weights are then
  the same combination, exact. The body mesh is exactly mirror-symmetric but its weights are not (0.17 apart on the
  hands): build the right side from the left's topology but with the right hand's own weights.
- MakeHuman's nail folds and joint creases show through a 1 mm offset. Bridge them: Laplacian smoothing with the
  height over the skin clamped to [offset, offset + 1.5 mm] (unclamped, the palm lifted 5.5 mm over its hollow).
- UVs like the real pattern pieces (hand back, palm, edges planar along their normals; each phalanx a cylinder
  about its bone, seam mid-palm; tip caps; cuff a cylinder): about isometric, so patterns drawn in mm stay true.
  A cylinder over a bent finger overlaps itself at the joints: one island per phalanx. Paint every texel from its
  3D point (rasterise the UV triangles with PIL, barycentrics, interpolate positions, normals and weights): chart
  seams then never show, and panel boundaries are smooth curves (weight-blended per-bone palmar directions), not
  face edges.
- build_rider's gear material has one roughness and colour-image + normal-map inputs only: put construction in the
  normal map; a smooth overlay among bumpy mesh reads glossier by itself. Black fabric turned mid grey with sheen
  0.3 under a white world: sheen 0.1, roughness 0.7.
- Leatt's views: work out which glove each photo shows (thumb side + palm facing): MY26 back/palm and MY27 back are
  the RIGHT glove, MY27 "other angle" the LEFT. The two gloves carry the same graphic in the hand's own frame (mirror
  images: hatches lean the other way), but every word and logo reads right on both: mirror letters only, inside
  their own box. The photo maps onto his hand's back at 0.178 mm/px (two independent scales agreed).
- Printing a photo's graphic by thresholding it directly gives blotches (mesh texture, lighting): redraw shapes
  measured on the photo rectified to the hand, and take only clean letter shapes from it (the large holes enclosed
  by the white core; place them rigidly, not row by row, or the slanting edge shears them).
- Check renders: `gloves.py check` on build_rider's saved rider.blend (no studio views needed): cameras from the
  posed hand's own joints, a camera-only white background (Light Path) for Leatt's product angles with the body
  hidden, clearances from evaluated meshes with the hide_body Mask switched off (or the hidden skin is missing).
- Seated pose (pose.py + aim_pose, 2026-11-13): the grip's axis crosses the hand only 6 mm palmar of the bones,
  so the grip passes through the palm (skin 14 mm inside it). A power grip needs the axis about 36 mm palmar (palm
  skin 20 + glove 1 + grip radius 14.8), across the distal palm at about 25 deg to the knuckle line (right now).


## Jersey and pant: Leatt 5.5 Tiger Pink (kit.py, 2026-11-13)
- Cloth = his own body faces, cut along smooth cut surfaces (boundary vertices slid along their edges onto the
  cut), subdivided, then draped: curvature flow (the normal part of the umbrella Laplacian) plus a collision step
  along the skin's normals with a clearance per vertex. Curvature flow alone is body paint (pecs, belly, ballooned
  knees). Loose cloth needs ENVELOPES: per-slice convex hull round an axis (trunk: vertical; each leg: hip to
  ankle), hung with a fall rate (jersey 0.35 m/m off the chest, pant leg 0.08: straight legs). Keep the trunk's
  envelope out of the crotch: a radial push from a vertical axis tore a hole there.
- Ease from the chart: a convex girth grows 2 pi per metre of offset, so clearance = (garment - his girth) / 2 pi.
  Taking ease from the sides shrinks the girth unless the rest is scaled up (a girth test caught it).
- Draping drifts the openings: project the edge back onto its cut surface (Newton on the cut function) and hold it
  for the last relax. Turned facings: place the inner row 1.5 t under the LOCAL surface (k-nearest average); the
  nearest single vertex poked out and crumpled the neckline.
- Two layers (jersey tucked under the waistband): order the clearances (jersey 2.5 mm, band 11 mm) and clamp the
  tucked part from both sides, else curvature flow bridges the spine groove outside the pant; give the tucked part
  the pant's weights. Face-material regions (I.K.S panels) stair-step: snap the seam's neighbours onto the field's
  zero first. Weight smoothing 6 passes on the jersey, 2 on the pant (it follows the kneecap).
- Sizes: measure him where the garment is worn. The pant band's height came from Leatt's on-model rise (22 cm);
  my first band (18 cm rise) put his band girth at 90 cm (XL); at the right height it is 84 cm (L / US34).
- Print: one UV chart per pattern piece (LSCM; numpy 2 refuses 2D cross products, use the determinant), texels
  painted from their rasterised 3D rest position, so the layout never decides where a graphic lands. Leatt's
  frontal on-model photos (long lens) project well onto front and back panels; flat product shots are 3/4 on forms.
  Mask the studio background (border-connected near-white, or the PNG alpha) and fill from the nearest garment
  pixel, and map across arms and legs by the photo's silhouette (normalised), never in metres: the soft edge
  otherwise smears white along the sleeves. In the pant photos the gloves are runs of the silhouette rows: take
  the leg runs nearest the middle; find the crotch row from the alpha. Logos the photos see edge-on (the outer
  thigh LEATT) are printed flat from a side canvas.
- Tests in a pose without Blender: numpy linear blend skinning (bone turns about their heads, children follow).
  "No skin through the cloth away from the openings" must skip 4 rings from the open edge (facing, fold, edge).
- The Bash tool's worktree guard refuses any command containing the letters g-i-t (even in "digits"): put Python
  patches in a file.

## Jersey: his number, name and sponsors (round 2, 2026-11-13, kit.py "Damien's additions")
- **Read his photos upright**: rotate each crop so his body stands vertical (PIL rotate about a centre, enlarged
  7x, unsharp mask) and read positions on a labelled grid, converting back to photo pixels by script. Rotated, 09
  and 08 showed the front sponsors under the yoke either side of the centre chevron; round 1 had read 09 sideways
  as "a column on the side panel".
- **The photos' names are the bike's side**, not his: he is twisted in a whip. Each of 09 and 08 sees one side of
  his chest nearer (patch widths disagree by up to 30 %): combine both (geometric mean), never trust one.
- **Ruler on the cloth**: Leatt's chest LEATT is already on the model at known places. Fit it to his photo by
  normalised cross-correlation of Leatt's logo mask with his light letters: affine coarse to fine (blur 2.5, 1.5,
  0.8 px), then a little perspective with a penalty (a free homography collapses to a sliver: NCC is blind to
  scale). Check the outline overlay. The fitted plane extrapolates badly above and below the logo (the chest turns
  35 deg toward the collar; photos from below): use it near the logo, and local ratios (patch to letter height,
  to logo length) plus the official artwork's aspect for sizes.
- **Official logos, where they are**: BikeWise and USN: the og:image of their own Shopify sites; Motul: the inline
  SVG in motul.com's header (white `fill` on a `#ed1c24` box in its CSS); Pirelli: pirelli.com's og image;
  Cycleworx Suspension (Randburg) has no site: `graph.facebook.com/<page>/picture?width=1000` returns its profile
  logo while the page itself answers 400 (cycleworx.co.za is a different firm, a bicycle shop). Files and URLs in
  `reference/sponsors/README.md`. A small SVG path filler (M L H V C S Q Z, even-odd) rasterises vector logos.
- **His 114 is his own art**: lift the white glyph components from his plate art (largest three in the number's
  field; drop the bolt hole and logos), keep its keylines; outline by a distance transform.
- **Print like sublimation**: the back in unrolled coordinates (arc length across each horizontal section from the
  spine, up each vertical from z 1.45), so the number wraps the curved back and crosses the raglan seams in one
  piece; small front patches on their tangent plane. Building the unroll: keep only the outer back (cloth round
  the front of the neck also faces back at the same (x, z); y above the side seam), one point per 3 mm cell (seams
  carry duplicate vertices: Delaunay slivers made a 20 cm jump), median-filter, and integrate up from shoulder-blade
  height (from the hem the armpits' steep cloth sheared the letters at the sides).
- **Sharper print without new UVs**: an overlay part = the jersey faces under the graphics, 0.1 mm out, with the
  jersey vertices' own weights; UVs = the jersey's UVs scaled and moved per island, never rotated (tangent frames
  agree, so the jersey's normal map can be copied); the background sampled from the jersey's own print at the same
  cloth point. Check it by rendering with and without the overlay and differencing: 0.3 mm lift drew 2 px contact-
  shadow lines along the island edges. build_rider's gear materials take no alpha, so a cut-out decal is not an
  option.
- **A word cut by a fold is not the whole word**: in 06 the name ran into a fold of the jersey at the collar,
  so round 2 took DAMI for DAMIEN and set the whole name over the number's left half. Damien: it is centred.
  Read which letters are visible, then scale by the font's own ink widths (DAMIEN / DAMI). Off-centre graphics on
  a twisted rider are usually the twist: ask before printing something asymmetric.
- His name replaced Leatt's back LEATT (06 shows none beside it): erase it from Leatt's photo before projecting
  (normalised Gaussian fill).

## Coordinating the gear rounds (coordinator's notes, 2026-11-15)
- Never `cd` into an agent's worktree from the coordinating session: the session's working directory follows the
  shell and later relative paths resolve inside the worktree. Use absolute paths and `git -C <worktree>`.
- Agents must not use the Edit or Write tools on files under `.claude/`: a permission prompt nobody saw hung the
  helmet agent for 3.5 h. Write skill notes with a python script through Bash.
- Number the PROJECT.md decisions before launching parallel agents (each brief names its own number); two agents
  both took 42 once.
- Read every sheet at 1:1 (crop the panels side by side) before merging. Sheet-size thumbnails hid round 8's strap
  slides (round rods where Leatt's are flat moulded frames) and the helmet's oversized black grip-panel area.
- Check a comparison's camera before reading it: a scratch refit of his photo 08 (fitted to the helmet's outline
  alone) settled on the wrong side of the helmet; the render showed the shaded underside where his photo shows the
  lit top. Leave such sheets out of the checkpoint. head_closeups.py's views p07, p08 and p09 (matched by eye) and
  cam07 (fitted with the bike, research/rider-cameras.json) see his photos from the right side.
- Review gear at his own photo angles (07, 08, 09) as well as Leatt's: the helmet's black grip panel, painted
  through a front-iso camera 14 to 17 mm off at the brow, read as a large dark area under the strap in his 07 and
  09, where his photos show magenta. Leatt's iso-left at sheet size looked acceptable.
- Held-out on-helmet views (Leatt's MY27 kit photos) found worn-fit defects that goggle-alone views cannot: the
  strap through the shell, its height, the outriggers' thickness.
- Run the rider tests as `python3 -m pytest -q .` in scripts/rider: the bare `pytest` on PATH runs the system
  Python without numpy, and all six files fail to collect (exit 2).
- A fitted camera can hide a wrong shape. The front-iso cameras' 14 to 17 mm error at the brow was the brow itself,
  20.6 mm too far forward (the brow badge triangulated from iso-left and iso-right agrees within 0.4 mm). When one
  family of cameras disagrees, triangulate a landmark from two views before refitting a camera. (The 20.6 mm itself
  turned out to be the cameras': see the correction below.)
- An opening traced in a side photo can be the soft parts behind it: the eyeport's side edge was traced along the
  cheek pads' notch, 35 to 40 mm ahead of the shell's cut edge (Leatt's iso-left shows the cut edge). The black trim
  paint then covered shell that is really opening. Leatt's side studio photo is also not square (8 to 11 deg behind).
- Coupled parts need one owner: the eyeport edge, the brow, the helmet's place on his head and the goggle's worn fit
  move together (the corrected edge failed three goggle tests). Brief agents to stop and report when a fix needs
  another agent's file (the helmet agent did); then plan a joint round with one agent owning both scripts.
- The render look: rider sheets rendered plain AgX (exposure 0, world 0.8) and read pale in every comparison (helmet
  teal, magenta; the strap a third less saturated than both photos). The bike learned the same: Standard view for
  studio comparisons, AgX - Punchy at -0.6 for the scene (decision 46 makes the rider follow it).
- Fine relief textures read as glitter: the woven strap's grain (taken from the MY27 jacquard) speckled the Pinata
  strap in his 07 at 4x. Take each product's grain from its own photo, and check at whip distance across two frames
  for shimmer (Cycles has no mip-maps).
- Main moves while parallel rounds run. Goggle round 11's new overlap test failed on main after helmet round 3
  (the helmet sat 3.9 mm lower, which moved his nose 3.2 mm back and the comb met the plate). The agent caught it by
  fetching main and running the whole suite on a trial merge before reporting. Brief every agent to do that.
- A crop lined up on a feature can hide a layout offset: the strap LEATT sheet at 4x was aligned on the T's end, but
  the unaligned 1:1 crop through the same camera shows our strap print about 80 px further along than Leatt's (his
  yellow by the outrigger, ours magenta). Read the unaligned crop too; the strap's layout on the helmet is worn fit.
- Say which way a part leans in the brief: round 11 leaned the comb's tongues back (depth), while Leatt's phr and
  iso55 show them fanned square to a strongly curved arch (image plane); ours stand nearly upright on a flatter arch.
- Correction (helmet round 4): the brow's "20.6 mm too far forward" was itself an error of round 3's single-photo
  cameras. Solved together (helmet_ba.py, 12 cameras), the front landmarks agree with the model within 1 to 5 mm, and
  TF 172's 350 mm length is a bounding box at another height, not the same 20 mm. Pairwise triangulation through
  separately fitted cameras can invent a shape error as easily as hide one; trust the joint solve.
- An empty helmet is not a worn one. Leatt's studio iso-right has the strap rising over the chevron panel and the
  goggle about 12 mm lower and 11 mm further back; on his head (his 07, 09) the strap runs under the panel. Where the
  two disagree his own photos lead; say in the checkpoint README which studio sheets differ for that reason, and
  separate shape from place (render the part where the studio photo has it) before calling a part too wide.
- Parts of one colour merge at viewing distance: the grip panels, the port trim and the empty helmet interior are
  all black, so the front reads as one big black blob at 0.4x even after the cut edge moved 16 to 23 mm. Fixing an
  edge does not fix the read; each part needs its own tone, relief and the things behind it (liner, cheek pads).
- Check every merged decision row has its four cells (#, date, decision, source): joint phase 1's row came without
  the Source cell; brief agents with the column list.
- Give offsets in a brief from the solve, not by eye: "the goggle about 12 mm lower and 11 mm further back" on
  Leatt's empty helmet was 12.6 mm and 3.5 mm through the solved camera (goggle round 12). Separating shape from
  place then showed the plate too wide at either place: shape.
- A part's tone at 1:1 can be its neighbour's material: the comb's "light rim" (150 to 180 against 75 to 95) was
  mostly the face foam's sheen behind it; with the foam matte the rim reads 97 against Leatt's 87.
- A colour gap against his daylight photos has several causes; measure each before fixing any. The coordinator's
  test (scratchpad look/, decision 54): AgX in any look puts the jersey magenta's green at 128 where his photos
  have 22 to 44 (Khronos PBR Neutral and Standard keep it at about 15); the jersey's specular (rough 0.58: the sun's
  lobe spread wide) adds 37 to the magenta's green, 60 to 75 to the lime's blue and lifts its black from 30 to 90;
  and his phone's tone curve crushes darks to 12 to 25 where ours read 47 to 88. The look, the materials and the
  phone's curve each need their own fix.
- Fit a look on pixel-aligned pairs of trusted surfaces only (scene look round 1, decision 54): his fitted cameras
  render the photo's crop at 4x, box-averaged onto the photo's pixels; mask to the helmet's white shell and print and
  the bike's red and blacks (materials measured in studio), never the jersey (its material is a suspect). Hold one
  photo out. Mean dE of the class medians went 21.1 to 12.7 with the new look.
- His phone exposes each shot (08 sits 0.6 to 0.9 EV over the look's EV, 07 0.2 to 1.0 under): judge a comparison
  sheet at the photo's own exposure, read off a known white (the shell), not only at the global look's.
- A constant tuned under an old view transform hides the transform's error: the bike's RED (208, 10, 22) was tuned
  under AgX; under the fitted look it reads 218, 42, 38 against his 189, 47, 49. Re-derive such constants when the
  look changes, and brief every copy together (kit_canvas.RED with build_bike.RED and test_kit).
- Two rounds adding PROJECT.md decision rows conflict at the same spot: keep both, in numeric order, 4 cells each.

## Helmet round 2: the face port and a fair shell (2026-11-15, helmet.py, test_helmet.py, ledger helmet.md section 5, decision 44)

- **A side photo's notch is not the shell's edge.** In Royal_Left the face port's notch stops at the cheek pads
  (u 750, with a dark fabric band to u 793); the shell's own edge (the rubber trim's inner edge) is 35 to 40 mm
  further back, where Leatt's iso-left photo (no goggle) shows it. Cast picked edge points through the fitted camera
  onto the width field (`raw_width`, defined past the cut) to get them in the helmet frame. A paint polygon drawn on
  the photo's whole opening then lands on any shell that should not be there: that was the big flat black area.
- **Side photos are not square.** Through the iso cameras the side screw and the grip panel corner land 18 to 24 mm
  behind their Royal_Left places on both sides (the camera stands about 10 deg behind the side; the back LEATT's
  first letters show round the back). Do not take near-side features' y from a side view without that correction.
- **Check a camera with landmarks before blaming it.** A landmark-constrained camera (screw, panel corner, badge)
  can fit every landmark and still be wrong: iso-left at az 52 asked for a front 143 to 160 mm wide where the back
  view caps the shell at 130. Cross-check what a camera implies against the other views before adopting it.
- **Triangulate centre features from two views.** The brow badge's rays from iso-left and iso-right meet within
  0.4 mm (x -2 mm): the brow is 20.6 mm behind the model's. Moving it moves the head fit (fit_on_head keeps the brow
  32 mm ahead of the forehead), the helmet 12 mm forward on his head and the goggle off his face: a change that
  needs the goggle re-placed is stopped and reported, not made.
- **Fair by construction for width fields.** Distances to a rim sampled every 3 mm scallop by up to 0.6 mm at 2 mm
  from it, and x ~ sqrt(d) there turns that into ridges 20 mm either side of the centre line; tables read with
  straight lines step the slope at every knot (bands in reflections); smoothing that averages over the query points
  depends on how they are spaced. Use C2 smoothing splines for traced rims, distances to the segments of a 0.25 mm
  polyline, and smooth on a fixed grid (over the uncut domain) read back by a bicubic spline. For a sparse table,
  fit the spline to the straight-line table sampled every 1 mm, never through its knots alone: through Q_Y's knots
  it rang 9 % low in a 260 mm flat run (the chin bar 6 mm narrow). Departures measured only at the knots hid it;
  measure them between knots, and compare the mesh with main's at a few points. Test it on the mesh as rendered: the
  normal turn along each edge against its neighbours' median (`test_shell_is_fair_at_the_crown_back`, 120 /m;
  main 190).
- **The port edge carries the goggle.** Leatt's iso-right photo has the goggle's outriggers over the port's trim.
  Round 2's port (helmet.PORT "iso", right for the iso-left photo) left them 21 to 23 mm ahead of the edge: the
  strap bridged the opening (its silicone side showed in every view with the goggle) and three goggle tests failed.
  Before moving any shell edge the goggle sits on, measure the outriggers against it in the helmet frame and run
  test_goggle; if the goggle has to move, keep the old edge in the build and report it.
- **A lower port edge meets the cheeks.** Moving the port's lower rear corner down 10 to 15 mm put four cheek
  vertices inside the solid at T_MIN 18 mm; the cheek pads fill that corner (T_MIN_PORT "iso" 14 mm).
- **Cache on the object, not by id().** A dict keyed by id(prof) can hand a new Profile the field of a dead one
  (ids are reused); helmet.smoothed_width keeps its spline on the profile.

## Helmet round 3 phase A: photos solved together, shell rebuilt, moulded vents (2026-11-15, helmet.py, helmet_ba.py, helmet_detail.py, ledger helmet.md section 6, decision 46)

- **Stripes in a clear coat are normals first.** The crown stem's purple and white ladder was the coat mirroring
  vertex normals 3 to 8 deg off the surface (fans meshed from unevenly graded rings), not print. Compare Blender's
  angle-weighted normals with the analytic surface before touching the texture (`test_crown_shading_follows_the_surface`).
- **Lamps in the coat bleach the print.** A pale stem or salmon teal in a comparison render can be the studio's
  lamps mirrored in the clear coat or AgX's highlight roll-off: judge inks in the Standard view with the lamps kept
  out of the coat, then check the scene look (AgX - Punchy -0.6, shared with the bike) separately.
- **Solve all the photos together.** Cameras fitted one at a time to the outline (helmet.CAMS) each match their own
  silhouette and still disagree by 20 to 35 mm on the crown: the print traced through the top camera puts the crown
  vents at y 16 mm, Royal_Left (the frame's own gauge) sees them at y 37, and the back camera sees the painted vent
  137 px above the photo's. Before trusting any print or part placed through one camera, project it into a second
  view. `helmet_ba.py` solves the eleven cameras with shared landmarks and outlines; `research/helmet-ba.json`
  keeps them (load with `helmet_ba.solved_cameras()`).
- **Bundle adjustment of long-lens photos.** An outline fixes a long-lens camera's scale but hardly its distance, so
  landmarks drifted 16 to 29 mm inside the shell: hold the ones on a measured part of the shell on it (1.5 mm), finish
  with plain least squares after the robust (soft-l1) rounds (soft-l1 alone ignored the constraint), and divide each
  reading's sigma by the cosine of the view's incidence. Read the per-landmark residuals, not only the total: two
  landmarks (crown vent, rear badge) at 43 to 52 px rms meant no rigid shape fits them on the shell.
- **Measure a shell by bands through the solved cameras.** The outline offset per 10 mm of height (back views) and
  20 mm of length (top view), median per band, showed main 1 to 3 mm narrow below z -50 and 1.3 to 3.6 mm wide at the
  shoulder; refit W_Z and Q_Y to it with a held-out view (MY27 back) as the check (`helmet_ba.outline_bands`).
- **Published dimensions need their reference.** Leatt's Technical File 172 (in the Moto 8.5 kit PDF on
  pim.leatt.com) gives shell and EPS W x L x H per size: width and height match ours within 1 and 3 mm, the length
  is 20 mm under ours (chin bar to back), so it is measured to another reference; do not fit to it blind.
- **Moulded detail from photo px through the print's camera.** Trace the feature in the photo, cast it onto the
  shell through the same camera the print was traced through, so part and print agree; measure its size through the
  solved cameras. Snap a frame's outer edge back onto the shell (a tangent offset sank 1 mm into the concave lower
  back). Do not paint what is built: the painted lattice doubled the built one wherever the casts differ.
- **A recess on a closed shell.** A slot sunk into the shell reads as a lip rising to a rounded crest at the slot's
  edge with a dark inner wall; a raised ring with a flat top reads as a bezel (tried on the rear slots). Round 4:
  under the clear coat any raised edge, even 0.2 mm proud, shows a bright line at 3x and a dark edge a black
  outline; while the shell stays closed, draw the slot as the print's dark plus its wire mesh, nothing raised.
- **Grazing features.** The rear lower vents are seen at a 0.13 to 0.43 cosine from every camera that sees them:
  sizes along them agree (59 and 60 mm), across them not (10 and 17 mm). Measure such features in two views and
  quote the spread; the print traced there is unreliable too.

## Helmet round 4: crown, print, visor, vents, rear pieces (2026-11-15, helmet.py, helmet_art.py, helmet_ba.py, helmet_detail.py, ledger helmet.md section 7, decision 50)

- **Free the gauge camera to test the profile.** Royal_Left held as the gauge hid that the old iso cameras were off:
  freed, with its outline in the solve, it sits 1.4 to 2.3 deg off the side axis (not 8 to 11) and the profile fits at
  2.5 px. Then read the worst landmarks again before blaming the shape: the 43 to 52 px were a badge held on a surface
  it is not on and a vent read at its front end in some views and its centre in others. Read one feature point in
  every view.
- **Every camera needs a landmark at each end.** The top camera had landmarks only on the crown and stretched 45 mm
  past the visor's tip; a `visor_tip` landmark held it (reduced chi-square 2.50 to 2.02).
- **Photos can disagree with every rigid shell.** The top photo puts the crown 10 to 12 mm further forward than the
  side photos. Measure the conflict in mm, record it, let the solve share it out; do not chase it with the shape, and
  do not take a brief's offset measured through older cameras as given (the visor's "20 mm back" was not there in the
  solved Royal and MY27 cameras, which keep the edge where it was).
- **Compare silhouettes by numbers.** On a white background a white helmet's outline vanishes in crops: compare the
  photo's mask edges row by row with the model's through the solved camera, in mm (the visor's plan: main 10 to 18 mm
  wide near the tip, unseen in the crops).
- **A raised part at a grazing angle shows its top.** The back camera sees the rear lower piece at a cosine of 0.42, so
  a top 2 mm proud lands 8.3 px from its foot: place the foot so the top's projection lands on the photo's point
  (iterate three times).
- **Crisp moulded plates: separate vertices per band.** A plate whose top and walls share vertices shades as a tube
  (averaged normals). Give the top, a 0.2 mm chamfer and the wall their own vertices; check the share of vertices
  joining faces more than 20 deg apart (rear piece: main 69 %, now 3.6 %).
- **Outlines with acute corners: fit lines, not morphology.** A morphological opening rounds and eats a
  parallelogram's acute corners; fit the hull lines to the photo's outline and round the corners at a chosen radius
  (`helmet_art.round_quad`), then grow the rim as an even offset.
- **Crop every edge of a changed part at 1:1 in the view that shows it.** The visor's plan was fitted at its front
  and sides; its rear edge, never traced in the top photo, ran straight across where Leatt's has a tongue and a corner
  37.5 mm ahead of it (seen only in the checkpoint's 1:1 top crop). Trace the outline all round before calling a
  part done.
- **End a grid on an outline by remeshing a band.** Build the grid finer, find where its fine columns cross the
  outline, and run each output column from its place on a fixed station to the outline's point at the same share of
  its length (`helmet.visor_rear_edge`). Sliding each column to its own crossing shears the band into folded quads
  where columns run along the outline.
- **Symmetric art cast side by side through one camera shows the camera's error.** The visor's chevron columns,
  each cast from its own side of the top photo, landed 5 mm from mirror places once the top camera was re-solved:
  the mirror of one cast missed the other column by 14 px in the photo. Check the mirror gap of every per-side cast
  (the test does), and when it grows, move each side half way to the other's mirror in the photo rather than
  trusting one side.
- **One view owns the print round a part.** A view that sees a white part edge-on draws its edge as a spike over the
  next ink; give the view that sees it best the ownership inside a polygon (`helmet_art.BACK_ZONE`).
- **Bounding-box lengths mix heights.** Our 369.7 mm length joined the chin's front (z -80) and the back's bulge (z
  -35); per height it is at most 359.6. Compare a published length per level and against the EPS (287 against our
  brow-to-back 288.8) before moving anything.

## Joint front fit, phase 1 (decision 47): lessons
- His photos are cameras in the helmet frame (`his_cameras.py`, `research/his-photo-cameras.json`): fit to the
  helmet's measured landmarks first, then the print's colour (Lab a*, b*). Views set by eye can face the wrong way
  (main's p08 saw his face from below; the photo sees the crown from above). The colour term needs its own weight
  (score = -2 NCC - 0.5 cover + 0.02 chi): averaging it with the landmarks halved it.
- A pick cast through a single-photo camera can sit 16 to 18 mm off once the cameras are solved together: re-cast
  every photo pick through helmet.PRINT_CAMS when the cameras change (round 2's port edge did).
- In Leatt's iso photos the port's edge is the crest where the outer surface turns in (grip panel's triangles on one
  side, the trim's ribbed roll on the other); the side photo's notch is the cheek pads, 16 to 23 mm further forward.
- Place the helmet from the liner: the EPS length (TF 172) less his head's, shared front and back, plus the wall.
  The goggle rides his face: when the helmet moves on his head, move goggle.PLACE back by the same so the lens keeps
  its place on his face (lens centre 56 mm ahead of his eyes; at 61 the foam stood 8 mm off his face).
- A strap laid across a surface's free edge folds: land it where its whole width lies on the shell (the edge test
  needs a depth bound, or the far side's edge counts).
- Re-measure every worn fit through the cameras fitted to the helmet's own points (his_cameras, PRINT_CAMS), not
  through a camera fitted to the part being placed: round 8's strap plane, fitted through a camera fitted to the
  goggle, stood 37 mm above his 07's strap (rms 39 mm), running over the chevron panel his photo shows above it. A
  camera-free check: read where the part lies against the print (his 07: the strap just under the chevron panel's
  lower stripe). The plane scan is about 1 s a plane (scratch planescan.py).
- A test of a strap's landing against an edge compares each point across the strap with the edge at its own height:
  a leaning cross-section fails a band-wide max even when every point is 4.6 mm clear.
- Steep faces in a top-projected atlas island stretch 1 / |n_z| times: give them their own side island.
- Grey white: before touching materials, render the spot flat (emission, Standard, 0 EV). If it reads the photo's
  value, the light is the cause (the studio's off-axis lights leave up-facing faces at about half the light).

## Joint front fit, phase 2 (decision 51): lessons (helmet.py, helmet_detail.py, helmet_art.py, ledger helmet.md section 9)
- Know which camera to trust where: Pinata iso-left stands 13 mm off at the chin and 8 to 10 mm at the brow; MY27
  front-iso-left and Pinata iso-right agree within 3 mm at the chin. Fit the chin to those two. A pick cast through
  helmet.PRINT_CAMS can land 30 px off in the BA view camera at the brow's corner: read small parts (the brow tag) at
  3x beside the render through the view's own camera.
- Snap to the closest point on the triangles (helmet_detail.ExactShell), not the nearest vertex's tangent plane,
  where the shell folds (the brow into the trim's roll): the tangent plane sank the brow's wires 1.7 mm under the
  shell. Measure heights the same way in tests (test_helmet.surface_height): the nearest vertex read 1.5 mm under the
  chin's pieces. Keep it mirror exact: snap the point's image on his left and mirror back (the triangles' diagonals
  are not mirrored).
- A half outline mirrored into one loop across the centre line: resample it along its straight closing edges before
  snapping, or the trace's own centre segment cuts a notch (16 mm wide, 7 mm deep in the brow vent).
- Inks set in 3D (helmet_art.mouth_ink) live in the trace's force_labels: changing them needs `trace` (about 4 min),
  then his_cameras.py (about 5 min: the print's element frames move; 09's colour NCC fell to 0.40). Apply them once
  more on the drawn texels: thin atlas slivers plus the draw's island-edge fill dragged the chin cap's black 7 mm low.
- A crisp moulded edge needs its own vertices per strip and a narrow chamfer: a shared edge strip with smooth shading
  reads as a soft bump. The visor's lip: the top drawn in 0.6 mm, the chamfer catches the highlight line, the edge
  face below is the dark band.
- A grid closed to one point (the visor's pole) has zero-length ring steps: tangents there are zero and normals NaN.
  Mask them before normalising.
- Rounding a traced polygon's corners pulls its extents in (r / sin(half angle) - r at each corner): push each corner
  out along its bisector first (helmet_detail.round_corners), so the outline still meets the read corners.
- A test that compares the build with the same px it was built from proves nothing: test a property the photo shows
  (a straight edge, a material, a height on the shell) instead.
- Compare a part with a reference edge at each point's own height: the pads' front read 6 mm off on the notch's
  slope with a band-wide window, and was within -4 to +3 mm point by point.
