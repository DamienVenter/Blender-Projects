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
  of the helmet (the goggle in iso-right). Studio reflections come along: a cleanup pass is still to do.
- **The big side LEATT in Leatt's iso-right and his photos is the goggle strap's print**, not the helmet's.
- Text on a strap reads correctly on both sides from outside if it runs in one direction from the left outrigger
  round the back. An outrigger face seen from the other side mirrors its UVs: give each side its own image half.
- A head pitch put on the head bone alone drives the chin bar into the throat; share it over neck01-03 and head.
- Test closure and orientation of the solid (every directed edge once each way) before trusting winding numbers.

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
