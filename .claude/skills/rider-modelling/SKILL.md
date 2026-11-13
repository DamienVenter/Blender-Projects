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
