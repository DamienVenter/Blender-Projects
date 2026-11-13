# Rear side panels drawn by script, round 2 (2026-11-13, decision 37)

Damien: the side number boards "look weird"; he wants an exact replica. Round 1 drew every element by script
(`scripts/bike/kit_sidepanel.py`). Round 2 fixed what round 1's own renders showed: the panels' upper rear was
crumpled under gloss, the flake was a coarse bright salt and pepper, the kit had no gloss or metal, and the inner
skin showed the livery mirrored. The record (what was measured, from which pixels, what is still different) is in
`research/detail-ledger/side-panels.md` and, for the shape, `research/detail-ledger/plastics.md`.

## The sheets here (his photo left, bike_v7 right)
- `01_left_photo07_vs_model.jpg`: photo 07 (riding, sun) beside the side close-up sp07: layout, the flake, the
  laminate's gloss.
- `02_left_photo02_vs_model.jpg`: photo 02 (front left, shade) beside build_bike's view dv02_left_front (an angle
  set by eye, not fitted).
- `03_left_photo03_vs_model.jpg`, `03b_photo03_whole_view.jpg`: photo 03 (the LEFT panel from behind; the file name
  says right) beside the new standard view dv03_left_rear, fitted to the photo (`fit_dv.py`).
- `04_left_and_right_model.jpg`: both sides; no photo shows the right panel, so its layout is the left one mirrored
  with every word reading normally.
- `05_rear_section_raking_light.jpg`: the upper rear (behind the 4, over the can, to the fender) under a sun grazing
  the face from behind, panels in plain gloss red (`scripts/bike/rake.py`): round 1 against round 2 on both sides,
  then round 2 through photos 03 and 02 and with the kit.
- `06_flake_photo03_vs_model.jpg`: the flake up close, pixels kept: photo 03 (about 1 mm a pixel), round 1, round 2
  (navy charcoal base, fine worm-like metal specks, each tilted so it sparkles).
- `07_inner_faces_round1_vs_round2.jpg`: behind the shock: round 1 showed the right panel's inner skin with a mirrored
  VENTER; round 2 gives every kit plastic's inner and back faces its plain plastic.

## Numbers
- Upper rear fairness (`test_detail_plastics.test_decision37_panel_upper_rear_is_fair`): normal waves 9.2 and 8.8 deg
  to 3.5 and 4.0 (bound 5), kinks 4.1 and 5.5 deg to 0.29 and 0.36 (bound 1), mesh normals 16 and 39 deg off the
  surface to 7.8 and 6.7 (bound 10). Overlap scores with Honda's photos within 0.002 of before (top silhouette
  0.8860 to 0.8864, the rest the same or nearly).
- Flake (photo 03): base (43, 43, 51) against the white's (145, 145, 151), specks over 32 percent, 1 to 2 mm long.
  Renders, as a share of the 114's white: sp07 0.44 (photo 07 in sun 0.21), dv02 median 0.52 (photo 02 in shade 0.60),
  dv03 0.54 (photo 03 0.50). The flake is metal, so it shows what it reflects: the studio's grey cyc reads lighter
  than the sun on photo 07.
- All bike tests: 166 passed.

Blend: `blend/bike_v7.blend` (textures packed; reopened in Blender 5.2.0).
