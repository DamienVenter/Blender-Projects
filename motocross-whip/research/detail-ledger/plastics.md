# Detail ledger: seat and rear plastics (plastics.py, detail_plastics.py)

Micro-detail pass, 2026-11-11. One section per component, in the brief's order. Pixel boxes are in the 4000x2250
studio photos unless a file is named. Check images are in the agent's scratch folder
(`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/plastics`):
`p_*` pair sheets from `pair.py` (photo left, model right), `s_*` the same stacked (photo above, model below),
`cu*/render_cu_*.png` close-ups.

## 1. Seat shape (done)

### Anatomy (what shows at 30 cm)
- Plan: a blunt nose (straight front edge, rounded corners), a waist where it sits on the tank, the full width over
  the middle, a rounded point at the tail.
- Profile: the top dips to its lowest where the rider sits and rises to a peak at the nose and to the tail; the nose
  rounds over in its last 20 mm to a short front face; the tail is a wedge (top line and hem meet) with a round tip.
- Section: crowned top, a broad shoulder falling about 21 mm to the skirt, the skirt leaning out toward the hem.
- Hem: the cover's rounded lower edge (a light line 1 to 2 px over a dark seam line 6 mm wide); a V at its lowest
  point over the joint of the shroud's tail and the side panel; the cover turns under the base.
- Base: black plastic pan, hidden; rests on the subframe's rails and clears the tank and the wall under the tail.
- Fasteners: the two seat bolts in their pockets on the seam (detail_plastics.seat_bolts, unchanged).
- Surface and colour: matte vinyl, lighter and pinker than the gloss plastics, fine pebble grain (component 2).
- Graphics: "HONDA" on both skirts (printed: left out).

### References
- TOP photo u 1900..2800, v 990..1260 (4x zoom with a 10 px grid: `grid_top_nose.jpg`, `grid_top_tail.jpg`;
  per-column scan of the matte cover: `seat_scan.jpg`).
- LEFT photo u 1930..2090 v 720..840 (nose), u 2740..2900 v 730..860 (tail) at 6x on a grid; RIGHT photo the same,
  mirrored. Whole seat: u 1900..2950, v 700..960.
- REAR photo u 1820..2180, v 480..660 (the nose seen end-on over the fender).
- rr34 photo u 1250..2100, v 560..800; lr34 u 1950..2800, v 560..860.
- Detail 475833 (left side cover): the seat's skirt and grain at the top of the frame.

### Numbers and sources
- Plan (SEAT_PLAN_PX, TOP, row 1124.5 the centre): front edge straight at u 1967.5, rows 1060..1185 (x 0.7826,
  half-width 55.8 mm); corners (1971, 1054), (1990, 1049 / 1200); full half-width 88.8 mm (99.5 px) u 2260..2620;
  tail point at u 2757.5 (x 0.0776). The 2026-11-10 table had the top at 0.088 plus 14 mm of skirt (0.102 at the
  hem): 13 mm a side too wide; its nose ran to a 15 mm point.
- Top line: the LEFT photo's silhouette, first non-white row per column, every 4 px, sub-pixel (in `_seat_lines`);
  1.5 to 2 px above the traced OUT 'seat_top'; the RIGHT photo agrees within 1 px. Lowest 0.961 at x 0.539, nose
  peak 1.002 at x 0.767 (both side cameras: 1.0021 / 1.0029). The REAR camera puts the same peak 4 mm lower
  (row 512.5 = z 0.998): the side photos are used, the rear one only for shape.
- Hem / seam (SEAT_HEM_PX = SEAM_PX): darkest run of r+g per column, every 20 px, LEFT and RIGHT (mirrored columns)
  equal within 0.5 px; lowest at the V, u 2266 row 904.5 (z 0.878 left, 0.880 right). Each side is cast through its
  own camera: the right camera puts the same rows 2.5 mm higher (left panel 2.5 mm under its hem, right panel at
  it before: 1.2 to 2.6 mm clash), so each side follows its own photo. HEM_LIFT 2.5 mm: the hem's outer point over
  the dark line's centre. HEM_R 1.2 mm (EST: the light line 1 to 2 px).
- Shoulder (SEAT_SHOULDER 21 mm, power 2.5): REAR rows 514..562 under the top, half-widths 34 / 52 / 60 / 65.5 /
  71.5 / 74.5 / 76.5 / 79.5 / 81.5 / 83.5 / 85 / 85.5 / 87 px every 4 rows (0.775 mm/px). Projected model
  vertices: rms 2.9 px (power 4: 5.7; a 20 mm round roll on a flat top: 11 px). LEFT: the "HONDA" print's top
  edge 21 mm under the silhouette (skirt starts there). TOP: the light band ends 69 mm out at u 2300, where this
  shoulder is at 29 deg.
- Nose and tail shoulders (SEAT_END_L 25 / 20 mm): LEFT, the nose falls 3 mm in its last 20 mm then 12 mm to its
  front (u 1985..1962); the tail 5 mm in its last 12.5 mm (u 2850..2866).
- Skirt lean 12 deg (SEAT_LEAN): the "HONDA" print, 43 px (34 mm) tall in the LEFT photo, is 8 px (7 mm) deep in
  the TOP photo. Nose front 3 deg (EST: upright within 2 px over its lower 10 px).
- Tail tip at least 8 mm thick (LEFT: 8 px at u 2866, rows 762..770).
- Tuck under the base 4 mm in, 2 mm up (EST, hidden); base 4 mm over the hem, 0.5 mm over the tank and the
  subframe rails (detail_chassis 'subframe'), 3 mm over the wall under the tail.

### Built
`plastics.seat_outline` (plan, 3 mm samples, 543 points), `seat_cover_z` (heights by distance to the hem: skirt,
then the shoulder of the sides, the nose and the tail combined so the nose's corners come out round, parameters
blended across the medial line), `seat()` (conforming mesh with 22 rows of vertices parallel to the hem, the
rounded hem and tuck as rings, the base as its own conforming mesh): 17,222 vertices. The side panels' top edge
follows the same hem (`seat_hem_hw`, SEAM_PX); the panels' red piece under the seat's nose is clipped under the hem
(it stood 9 mm proud of the new nose as a fin); the wall under the tail (detail_plastics.tail_under) is clipped
0.5 mm inside the panels' inner faces (the narrower hem moved them 13 mm in: 8.6 mm clash).

### Checks
- `s_3_left.jpg`, `s_2_left_nose.jpg`, `s_3_top.jpg`, `s_3_rear.jpg`, `s_3_rr34.jpg`, close-ups
  `cu7/render_cu_seatnose.png`, `cu7/render_cu_seattail.png`.
- Left: top line, nose, hem and tail tip on the photo's within 1 to 2 px. Top: plan outline on the photo's. Rear:
  the nose's dome now (was a flat block with square corners). rr34: the shoulder and skirt read as the photo's.

- Mesh density: the hem sampled every 4 mm and 14 rows of vertices (SEAT_RINGS_MM). With 3 mm and 22 rows (17,222
  vertices) 19 % of the cover's faces were under 2 px in the top view, and compare.raster draws those as one pixel:
  the base showed between the dots and the top red score fell 0.8 points. Now 10,408 vertices, 0.3 % such faces.
- The red strip beside the seat's nose (TOP u 1960..2160, between the hem and the shroud) was covered by the old,
  too wide seat. Running the shroud's bolt plate back under the seat to fill it (`DECK_END_U` 1950 to 2120) ran 3 to
  4 mm into the side panels' noses and the shrouds' skins and cost the rear view 1.6 points of red: undone. That
  strip is still not red in the model (see component 6).

### Still different
- (Fixed in component 3: the tail tip was buried in the old fender's root hump, audit 4.2 mm, and from behind the
  seat's base showed under the fender's tip.)
- The rear camera puts the nose's peak 4 mm lower than both side cameras; the model follows the side photos, so the
  dome stands 5 px high in the rear pair.

## 2. Seat cover (done)

### Anatomy
- One-piece matte vinyl cover over the top, shoulders, skirts, nose and tail; no ribs, panels, gripper zones or
  stitched seams in any photo (top photo at 4x: an even mottle with faint wrinkle lines; the profiles: plain); its
  only seam is the hem. Fine pebble grain all over. Colour: lighter and pinker than the gloss plastics, pinker still
  at grazing angles. "HONDA" printed on each skirt (graphics: out).

### References
- Detail 475833 (left side cover; the skirt's grain at the top of the frame): u 1400..2400, v 0..260 and at 6x
  u 1700..1900, v 40..180 (`det_475833_seat.jpg`, `det_grain.jpg`); its panel bolt u 1740..1940, v 1980..2240
  (`det_bolt.jpg`) for the scale.
- TOP u 2300..2500, v 1060..1160 at 8x (`grain_top.jpg`): mottled only (0.9 mm/px).
- Colours: TOP u 2200..2600 v 1080..1170, u 2300..2400 v 1026..1040 and 1206..1220; LEFT u 2300..2500 v 790..830,
  u 2600..2700 v 770..790.

### Numbers and sources
- Pebble pitch 1.3 mm: 475833, pebbles 3 to 6 px across, 6 to 8 px apart; the panel bolt's hex, 43 px for 8 mm
  (SPEC: 8 mm body bolt heads), gives 0.19 mm/px. Groove 0.22 mm and height 0.12 mm: EST.
- Colour: photo top (240, 64, 69), skirt (245, 103, 108), roll band (233, 115, 118), highlight (246, 131, 136).
  Material `seat` (detail_plastics.MATERIALS): base (202, 22, 30), roughness 0.72, sheen 0.6, the grain's normal map
  at strength 1.6. Rendered: top (238, 73, 76), skirt (243, 106, 108), roll band (248, 139, 141) (was (175, 66, 68)),
  highlight (248, 139, 141). The first pass's (176, 18, 26) rendered (208, 58, 62).

### Built
`detail_plastics.make_textures()` (`python3 detail_plastics.py textures`) writes `textures/stock/seat_grain_n.png`
(1024 px, 64 mm tile, tileable: two periodic Worley octaves, pebbles domed from their borders, heights varied cell
to cell). The cover's faces carry box-projected UVs (`plastics._box_uv`, SEAT_UV_TILE 64 mm).

### Checks
- `s_8_top.jpg`, `s_8_left.jpg` (colour), `cu10/render_cu_grain.png` (grain at 0.1 mm/px),
  `cu10/render_cu_sidecover.png` (the skirt over the side cover, 475833's angle).

### Still different
- The photo's cover shows faint wrinkle lines (top photo); not modelled.
- The livery mode's `seat.png` image is replaced by this material (the stock bike is the target).

## 3. Rear fender (partly done; round 2)

### Anatomy
- Plan: a straight taper from the root (where it meets the side panels' tails in dark seams) to a shoulder, then an
  arrow point. Profile: a thin blade rising to the point, whose end slants (top corner ahead of the lower one).
- Section: a lit, slightly crowned deck; a bright crease band; a dark facet; a light strip where the lip rolls over
  into the flank; the flank down to its lower edge. The bands converge on the point.
- Root: runs on under the seat's tail (the seat rests on it) between the side panels' tails and top edges, to the
  red wall under the tail, which is the same moulding's front leg (fiche K95CF3400: one fender, item 1).
- Fasteners (fiche K95CF3400): 2 upper bolts (item 3) with collars (4) at the front sides, 2 lower bolts (2) with
  washers (5) at the foot of the legs: the lower ones are detail_plastics.tail_under's two bolts with 20 mm washers
  (REAR, (1895, 766) and (2113, 775)). The upper pair is hidden under the seat and the panels in every photo.
- Underside (REAR): a tunnel under the blade, its roof arching up, two lighter ribs down its side walls.
- Graphics (out): the "IMPORTANT INFORMATION" label and "HONDA" near the point.

### References
- TOP u 2620..3360, v 950..1300 (`grid_top_froot.jpg`, `grid_top_ftip.jpg`, 3x to 3.5x on 10 px grids), scan of the
  red per column (`fender_scan.py`).
- LEFT u 2700..3420, v 690..900 (`grid_left_froot.jpg`, `grid_left_ftip.jpg`, `grid_left_seam.jpg`, 3.5x to 4.5x).
- REAR u 1820..2180, v 540..820 (`grid_rear_fender.jpg`, 3x). lr34 u 2550..2950, v 600..820 (`grid_lr34_froot.jpg`).
- Fiche K95CF3400 (`fiche_rear_fender.jpg`).

### Numbers and sources
- Plan (FENDER_PLAN_PX, TOP, row 1124.5): 103 px at u 2720 (x 0.112, 91.8 mm) to 63 px at the shoulder u 3128
  (x -0.252, 56 mm), then 57 / 47 / 36 / 25 / 14 / 6 px at u 3140..3186, point at u 3188.5. The old blade was
  98 mm wide behind x 0 and flared to 0.145..0.168 at the root (the side panels' tails' envelope): the root hump.
- Tip: TOP x -0.305, LEFT -0.290, RIGHT -0.287 (cast at y 0): the mean (-0.297) is used (the plan's x is stretched
  by up to 8.3 mm toward the point, FENDER_TIP_SHIFT); the old tip -0.3005 was EST.
- Top line (FENDER_TOP_PX, LEFT, first non-white row): 774 at u 2880 (6 px under the seat's tip), 763 at 3000,
  755 at 3100, 748 at 3200, 740.5 at 3340. Lower edge (FENDER_LOW_PX, last non-white row, near flank): 847 at u
  2960 (where it leaves the muffler), 831 at 3000, 804 at 3100, 782 at 3200, 754 at 3340, 751 at 3353.
- Section (TOP u 3000, half-width 78.5 px): deck to 30 px, crease band 30..45 px, dark facet to 62 px, light strip
  to the edge: FENDER_A1 0.50, FENDER_A2 0.80. Crown 3 mm, facet 8 mm, flank flare 8 deg (EST; the flare dies out
  at the root, where the flank is upright under the panels' tails).
- Root: x 0.195 (the wall's rear face), 0.5 mm under the seat's underside, 0.5 mm inside the side panels' top
  edges (they tuck in to 70..80 mm out under the hem).
- Side panels' tails (PANEL_TAIL_PX, LEFT 4x with the traced outlines drawn on it): the traced outline was cut
  upright at u 2845 (a hand-drawn seam); the panel carries on 100 px along the fender's flank to a corner at
  (2947, 811), its upper edge the top of the dark-red graphic band from (2845, 787), its rear edge down to (2897,
  876), its lower edge along the muffler's top. The fender's plan edges at the root (TOP rows 1022 / 1227) are the
  seams to these tails; the plan envelope outside them (0.13..0.15) is the tails.

### Built
`plastics._fender_lines`, `rear_fender` (loft of 100 stations, 4,300 vertices: deck, eased facet, rolled lip,
flank; the root clamped under the seat and inside the panels), `_union` + PANEL_TAIL_PX (panel tails, lapping 0.5
mm outside the fender's flank), `_seat_under` / `seat_under_z`.

### Checks
- `s_16_left.jpg`, `s_16_top.jpg`, `s_16_rear.jpg`, `s_16_lr34.jpg`; scores (red overlap): rear 0.627 before, 0.639
  after; top 0.861 / 0.858; front unchanged. Audit: no new clash (fender on the seat 0.1 mm, a seat).

### Round 2 (coordinator's review of `s_16_lr34.jpg`)
- The see-through test: the panel's tail stopped 5 to 10 px short of the photo's red. Per column the red run (fit34
  rule, r > 120, r - g > 70, r - b > 50, 3 px gaps bridged) ends 916 / 910 / 904 / 899 / 897 at u 2830 / 2840 /
  2850 / 2860 / 2870. Under it the left photo draws the muffler (the bike's far side) half-transparent: the plastic
  shows through it pink (rows 896..912 at u 2848..2890: 58 % red by the same rule, mean (195, 116, 119)) down to a
  straight band ending at row 896 as far as the can's end (u 2950), and the can's top edge and a bolt head at
  (2853, 915) are drawn over the plastic. PANEL_TAIL_PX now runs the tail on behind the can to rows 912 .. 896. The
  test's can (3.4 cm2) and, after the rear-chassis round's narrower can, its 3.2 cm2 hole are gone; left subframe
  1.9 cm2 (under 2) shows through the seam under the seat's hem.
- Seat's tail on the fender: the gap was the fender's top stepping down outside the seat's outline. A cup raised
  round the seat's tail to the hem cut through the hem between vertices (teeth): dropped. The fender's top under the
  seat now stays 2 mm under the seat's underside; the seam is tight and clean (`cu_r16/render_cu_tail.png`).
- The tails: they lap onto the fender's rolled lip (`fender_outer_y`, the fender's own section at each height, 3 mm
  clear: at 0.5 mm the panel's 7 mm faces spanning the lip's roll cut it, audit 3 to 11 mm), with one crease 12 px
  under their top edge, and taper in plan as the top photo's red outside the fender's seam: 0.148 / 0.139 / 0.134 /
  0.120 / 0.113 / 0.107 at x 0.087 / 0.074 / 0.060 / 0.047 / 0.040 / 0.033, the point at x 0.027 (TOP).
- The fender's section is shallower toward the root (LEFT: the crease line 23 px under the top line at u 3100,
  15 px at u 2890; the facet's drop down to 60 %, the lip from 10 to 3 mm), and it narrows between the panels from
  x 0.084.

### Still different
- lr34 (`s_r16_lr34.jpg`): the panel's lower rear edge ends higher than the photo's, and under the fender's front
  the wall under the tail, the subframe and the far panel's tail show where the photo has the near panel; the tail's
  top edge still wrinkles where it meets the panel's main body (x 0.085..0.125: three blends cross there), and the
  far (right) tail's top edge stands a few mm over the fender's lip near the seat's tip.
- The deck's crease bands read fainter than the photo's (bright band and dark facet); crown and facet are EST.
- Underside: the photo's tunnel roof and its two ribs are not modelled; the wall under the tail keeps its flat top
  and two channels (rear pair).
- The upper mounting bolts and collars (fiche items 3, 4) are not modelled (hidden in every photo).
- The model's tip is 8 mm longer than the side photos' and 8 mm shorter than the top photo's (the mean).

## 4. Side panels (partly done; round 2)

### Anatomy (detail 475833, LEFT, lr34)
- Red upper panel: glossy, a crease/ridge across its tail, the bead under the seat's hem, the air intake (a
  rounded trapezoid recessed with a lighter lip, the filter's dark green mesh behind it), its tail along the
  fender's flank (component 3).
- Black lower part (the airbox's side): satin black over a fine stipple, raised Y-shaped ribs (three arms 120 deg
  apart, all the same way round) on a hexagonal lattice; a recessed round pocket with the panel bolt (8 mm flange
  bolt) at its lower front; a raised smooth rectangular panel (the airbox side cover) ahead of it with a rounded
  recess.
- Joint red/black: a crisp diagonal edge.

### Done
- The black part's Y ribs and stipple: `detail_plastics.SIDE_COVER`, `textures/stock/side_cover_n.png` (1024 x 886,
  a 34.2 x 29.6 mm tile: two lattice steps each way), material `black_texture` (satin (22, 22, 24), roughness
  0.55, the map at strength 1). Numbers (475833 at 2.4x, u 1500..2000, v 1450..1800, 0.186 mm/px from the panel
  bolt's 8 mm hex, 43 px): Y centres 92 px (17.1 mm) apart, rows 83 px (15.4 mm, hexagonal 14.8) apart, arms 42 to
  52 px (8 to 10 mm) long and 7 px (1.3 mm) wide, round ended; arms laid at 115, -5, 235 deg (EST: the photo's own
  tilt not removed); rib height 0.4 mm, stipple 0.05 mm (EST). UVs on the black faces (x and z over the tile), u
  turned so (u, v, normal) is right-handed on the outer faces (mirrored, the ribs read as grooves; the same check
  turned the seat's box UVs).
- The panels' tails (component 3) and their top edge along the measured hem (component 1).
- Checks: `cu18/render_cu_tristar.png`, `cu18/render_cu_sidecover.png` (475833's angle), `tristar_sign.jpg` (the
  map against its inverse).

### Round 2
- Lumpy face: the section was a function of the distance to the traced outline (every wiggle of the trace a dent)
  and of the outline's height per 6 px column smoothed over 18 px only. Now it is a function of the column and of
  the height under the panel's top edge (the seam, then the tail's upper edge), the panel's height per column
  smoothed over 40 px, the plan envelope over 40 mm; the trace's lower and rear edges smoothed over 12 px more (the
  seam stays). `cu_r5/render_cu_panel.png`: the face is smooth, the lower edge clean.
- Intake: the backing is now the filter's screen, a dark green diamond mesh (INTAKE_MESH: strands on two diagonals
  2 mm apart, 475833 at 4x, u 2350..2650, v 600..800, about 11 px at 0.186 mm/px; green lit (18, 63, 5), in the
  shadow (8, 35, 2)), `textures/stock/intake_mesh_n.png`, material `intake_mesh` (class black, as the louvre panel
  it replaces). `cu_r17/render_cu_intake.png`.
- Bolt pocket: a 30 mm round recess, 8 mm deep (EST), in the black part (475833: the dark recess 160 px across), the
  8 mm flange bolt and a washer on its floor (the collar standing proud is gone). The bolt's shank passes through
  the pocket's floor (nesting; the audit lists it, 1.8 mm).

### Still different
- The intake's opening: the photo's is a crisper trapezoid (long straight top edge, sharp front corner); the
  model's comes from the photo's dark pixels and bulges at its lower front. Faint wrinkles beside its rear end.
- The raised airbox side cover ahead of the black part, and the crisp red/black joint.

## 5. Mud flap and inner mudguard (partly done)

### Anatomy (REAR, `s_r17_rear.jpg` photo half)
- The inner mudguard: a black arch-topped panel whose dome fills the red wall's arch, edged along its top by a thin
  rim; two black tabs with holes on each side (its mounts); at its foot a lip with two small fasteners where the mud
  flap hangs on; the flap below it curves forward over the tyre.

### Done
- `detail_plastics.mudguard_top`: through the wall's arch (rows 726..808) the model showed the subframe's rear cross
  member; now a black plate cut to the arch (the wall's own arch points) 1 mm ahead of the wall's front face and
  1.5 mm behind the cross member, with a 2.4 mm rim along its top edge (`s_r18_rear.jpg`). Audit clean.

### Not done (still different)
- The side tabs with their holes, the foot lip and its two fasteners, the flap's shape and ribs; the plate renders
  with faint vertical streaks at 24 samples (its rear face lies 1.8 mm from the cross member).

## 6. Shroud small items (not started)
- Also: the red strip beside the seat's nose in the top photo (u 1960..2160, between the hem and the shroud) is not
  red in the model (component 1).

# Round 3 (2026-11-11, PLASTICS3 brief)

Check images in `/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/plastics3`
(`s*_` stacked pair sheets, photo above; `z*_` zoomed pairs with a pixel grid; `id*` part maps: which part is in front
at each pixel of a photo's camera, `*_ov.png` the parts' borders drawn on the photo; `cu*/` close-ups).

## R3.1 Side panel rear: the tail, the crease, the lower edge over the can (done)

### Anatomy (LEFT, RIGHT, TOP, lr34, at 30 cm)
- The panel's tail is a pointed wing, not a box: under the seat's hem, then under the fender's dark crease line, a
  light facet (A, the bead's continuation) runs out to one crisp crease (a dark line with a light line 2 to 4 px
  under it: lr34's "crease and highlight line"); under it the face leans out (B, then a light band C) to the fold,
  the panel's widest line, where it turns in (D, dark) to its edge. A, the crease, C and D converge on one point at
  LEFT (2949, 805), x 0.037, on the fender's lip. Behind D's edge (u 2895..2945) the fender's flank shows, medium red
  as it is behind the panel. From u 2895 on, D's edge is the seam with that flank; ahead of it, the panel's free
  lower edge over the can.
- The fender's flank is never covered by an upright rear edge: the round 1-2 trace ran the tail on over the flank to
  an upright edge at u 2946, 35 to 55 mm out from it (the "bulky wedge" of `s_r16_lr34.jpg`).
- Over the can the lower edge is a rounded edge (a light line 1 to 2 px) on the red's last rows; under it, the can
  (pink-grey (180, 116, 118) on the left: its top reflects the panel).

### References
- LEFT u 2700..3020, v 760..1010 (`left_tail5x.jpg`, contrast stretched at 5x; `bands.py` runs per column every 5 px,
  green channel: dark g < 45, light g > 88); RIGHT mirrored, the same (`bands.py right ... m`).
- TOP u 2550..2950, v 940..1310 (`top_tail.jpg`, runs per column every 10 px).
- lr34 u 2540..2900, v 670..880 (`lr34_grid.jpg`, runs per row every 6 px); REAR u 1700..1920, v 540..820
  (`rear_ltail4x.jpg`).
- Fiche K95CF2300 (`fiche_side_l.png`): side covers 8 and 10, an inner black piece 9, a slender piece 4.

### Numbers and sources (plastics.py, next to each table)
- PANEL_TAIL_TOP_PX (A's top, rows 790.3 / 784.5 / 797.5 at u 2852 / 2890 / 2940), PANEL_TIP_PX (2949, 805),
  PANEL_CREASE_PX (836 at u 2780 to 810 at 2940), PANEL_FOLD_PX (C's lower edge, 916 at u 2760, 884.5 at 2850,
  834.5 at 2900, 813.5 at 2940; ahead of 2760 the round 2 ridge's two EST points), PANEL_SEAM_TAIL_PX (D's edge on the
  flank, 862 at u 2900 to 818.5 at 2940; RIGHT 843.5 / 832.5 / 821.5 at 2920..2940, the left's within 3 px).
- PANEL_LOW_PX, each side from its own photo (last row with r > 200 and r - g > 110): left 956.5 / 933.5 at u 2760 /
  2800; right 958.5 / 936.5 / 908.5 / 894.5 at u 2760 / 2800 / 2850 / 2870. The trace ran 10 px (left) and 25 px
  (right) under that: the coordinator's RIGHT check (box 960,860..1560,1280: the panel covered the can's top). The
  render's red-to-silver edge now lies on the photo's within 0..3 px at RIGHT u 1150..1290 (`z4_right.jpg`).
- Left, behind u 2840: the red ends at 904.5 (u 2850) and 891.5 (2870), but round 2 (the coordinator's see-through
  check) ran the tail on into the pink-grey under it, read as plastic seen through the far side's can, to 912 / 903
  at u 2850 / 2900. Kept for that check (the traced 'rear_fender' outline takes the pink as red: 4.6 cm2 of
  background without it), its corner now rounded up into D's seam (911 / 906 / 899 / 887 at u 2860 / 2880 / 2888 /
  2894). Against it: the far side's can shows its bolt head at (2853, 915), inside that strip, and nothing on the
  near side can be in front of it; to my reading the pink is the can's top reflecting the panel.
- test_bike's see-through check fails on the RIGHT: 3.5 cm2 of background at RIGHT u 1222..1252, rows 958..982,
  inside the traced 'side_panel_R' outline, which runs 20 to 25 px under the photo's red there (the photo shows the
  can). The panel follows the coordinator's request (the red-to-silver edge); the outline (outlines.py) or the
  check (test_bike.py) is a shared file.
- In plan (TOP, light facet A's outer edge): the crease at half-width 0.105..0.114 (PANEL_CREASE_Y); the panel's top
  edge at 0.095..0.101 (PANEL_SEAM_Y; used as an upper bound, the edge sits 0.8 mm clear of the fender's lip); the
  fold at the plan envelope (TOP's dark band's outer edge 0.1535 / 0.1454 / 0.1347 / 0.1222 / 0.1168 at x 0.128 /
  0.083 / 0.066 / 0.048 / 0.039, within 3 mm of width(x)). Cross-checks in lr34: the crease cast at 0.11 from its LEFT
  rows lands on the photo's highlight line ((2594, 747), (2631, 739)); the fold cast at the envelope on the photo's
  light-to-dark edge ((2600, 767), (2558, 810)).
- D's tuck at the free edge PANEL_TUCK 10 mm (EST: D is dark, 15 to 40 px tall).

### Built
`plastics._panel`: the trace is cut at PANEL_LOW_PX and ends at u 2836; the tail polygon (hem, A's top, tip, D's
seam, the lower edge) joins it. Section behind u 2790 (in full from 2830): facet A straight from the top edge to the
crease, the face convex out to the fold at the envelope, then D turning in (s^1.5) to the edge: on the fender's flank
(its face plus the 3 mm shell plus 0.5 mm) from u 2890, 10 mm inside the fold at the free edge. D's turn-in starts at
u 2730 on the main panel too (the photo's C band begins at 2750). Measured lines are smoothing splines (sigma 0.4 to
0.8 px): straight-line interpolation put a kink in the face's lean at every reading. Mesh rows along the crease and
the fold. The top edge is now a function of x only (on the fender's lip, under the seat's hem ahead): the round 2
wrinkle at x 0.085..0.125 (each vertex's own height over the lip's roll, three blends) is gone: second differences
along the top rows under 0.7 mm at 3 px (were 20 mm). Five extra rows of vertices through the tail (between the
crease and the fold, under the fold, between the fold and the edge, along the edge, in facet A): on the 9 px mesh
alone the tail came out jagged. side_panels: 11,294 vertices (was 11,162).

### Stray pieces under the tail in lr34 (each found with `idmap.py`)
- The C-shaped red piece (`s_r16_lr34.jpg` x 480..560, y 1150..1180): the RIGHT panel's tail, run on behind the can
  in round 2. Gone with the new outline (both sides).
- Red beside the can, under the fender: the right panel's inner face (as in the photo, where its lower edge meets the
  can's top at lr34 (2660, 830)..(2860, 768)).
- Red with two bolts and a black dome under the left panel: detail_plastics.tail_under (the wall under the tail) and
  mudguard_top. The photo shows a red face there too (2530..2600, 840..940): cast on the left panel's face it lands on
  the can in LEFT, so it is not the panel; it is the wall (or the right panel's inner face) seen under the panel's
  edge, beside the can's bracket. The photo hides the rest behind its can, which sits higher than the model's in lr34
  (detail_chassis: its ledger lists the lr34 evidence as not resolved). The left panel's own edge there lies on the
  photo's within 5 px in lr34 and on the red's last row in LEFT.
- Grey rails: detail_chassis 'subframe'.

### Checks
`s4_lr34.jpg`, `z3_lr34.jpg`, `z4_left.jpg`, `z4_right.jpg`, `ol1_left.jpg`, `ol2_left.jpg`, `ol2_right.jpg`,
`cu13/render_cu_taillr.png`, `cu13/render_cu_tails.png` (before: `cu1/render_cu_taillr.png`), `z8_left.jpg`,
`z8_lr34.jpg`.
Scores (b13): left 0.8814 / red 0.8956, right 0.8674 / 0.8948, front 0.8744 / 0.796, rear 0.8958 / 0.6411, top
0.8744 / 0.857 (floors held). Audit: no new clash of these parts (rear_fender on the seat 0.9 mm at x 0.11..0.13: a
seat; the fender's root now runs at its full width there). See-through (compare.intruders): left 1.6 cm2, right 3.5
cm2 (over 2: test_bike fails, above).

### Still different
- In the close-ups the tail reads as a pointed beak standing out from the fender, where the photo's glossy bands make
  it read flush; its size follows TOP's outer edge and the lr34 fold. The tip's last 10 px are coarse (four lines meet
  within 5 px on a 9 px mesh).
- The main panel's face between the intake and the tail still undulates softly in close-ups (from round 2: its lean
  follows the panel's height per column).
- The photo's crease is a crisp dark-and-light line pair; the model's is a change of angle only.

## R3.2 Rear fender, rest: the tunnel under its root, the upper bolts (partly)

### Anatomy (REAR at 3.5x, `rear_tunnel.jpg`; fiche K95CF3400)
- Seen from behind, under the blade: the tunnel's side walls (the fender's flanks, a bright highlight on their inner
  edges), then the wall under the tail (the fender's front leg): in its upper part a dome, its rim an arch from (1890,
  650) up to (2000, 600) and down to (2110, 650), dark in its outer corners; it stands on a ledge (a light line, rows
  652..656); under the ledge two upright channels in shadow (u 1890..1925 and 2075..2110, rows 657..688), each with a
  rib block under it (a lit top edge at rows 688..692, a dark face to 712); lower, the arch over the black mudguard
  and the two lower bolts on their bosses with 20 mm washers (rounds 1-2).
- Fiche: 2 upper bolts (item 3) with collars (4) through tabs at the legs' upper front corners, sideways into the
  subframe; 2 lower bolts (2) with washers (5). No tail light (stock).

### Numbers (detail_plastics.py)
WALL_DOME (2000, 652, 110, 52): centre column, the ledge's row, half-width, height; DOME_D 12 mm (EST, shading only:
nothing ahead of it until x 0.226, the seat's base above, the subframe's cross member below row 672); WALL_CHANNELS
(rows 657..688, 4 mm, as rounds 1-2's grooves, which ran at rows 612..686 across the dome); WALL_RIBS (u 1902..1922
and 2078..2098, rows 689..712, 3 mm proud, EST: their outer 12 px and 2 mm of height would be inside the fender's
root, whose flanks are pinned at 75.5 mm between the panels' top edges there: at 5 mm and full width they cut 7 mm in).

### Built
`detail_plastics.tail_under`: the depth map now holds the dome (rim rows of vertices at 1.0 / 0.8 / 0.5 of it), the
ledge (a 2.5 px step), the channels and the rib blocks; mesh 8 px with 3.5 px rows on the features. 2,352 vertices.

### Checks
`z6_rear.jpg` (rear pair), `cu13/render_cu_tunnel.png`. Audit: clean for the wall (the first rib blocks cut 7.3 mm
into the fender's root: fixed as above).

### Still different / not done
- The photo's dome reads deeper and rounder, with dark outer corners; the model's is EST in depth.
- The tunnel's side walls are the fender's plain flanks; the photo's have a rolled inner edge with a bright highlight.
- The upper bolts and collars are not modelled: hidden in every photo, and their tabs would sit on detail_chassis's
  subframe rails, which are sparse tubes at x 0.20..0.24 (rail outer face 0.068..0.097 there): no measured place.

## R3.3 Side panels, rest (intake's exact shape, raised airbox cover): not started
## R3.4 Mud flap and inner mudguard, rest: not started
## R3.5 Shroud small items: not started

# Round 4 (2026-11-11, PLASTICS4 brief)

Check images in `/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/plastics4`
(`p*_` pair sheets, photo left; `g_*` gridded crops of the photos; `cu*/` close-ups; `cmp*` close-ups beside 475833;
`tools/` the measuring scripts: `intake_contour.py`, `runs.py`, `cover_contour.py`).

## R4.1 Side panels, rest: the intake, its scoop and screen, the airbox cover, the side cover's window (done)

### Anatomy (LEFT, detail 475833, Dirt Rider 04, fiche K95CF2300 / K95CF2500, at 30 cm)
- Intake: a quadrilateral opening, its front tip sharp (4 px round), a long straight top edge, the rear end round
  (5 px), a lower-rear edge to a round lowest corner (8 px), a lower-front edge back to the tip. It sits in a scoop:
  over the top edge a facet facing up under one crisp crease (the scoop's top edge), which runs on 50 px ahead of the
  tip to a point; under the lower-rear edge the face rolls in (a bright band); under the lower-front edge one thin
  light line; a V under the lowest corner; at the rear the crease hooks down round the opening's end.
- Behind the opening: the panel's red moulding turns in, then a black rim (the airbox's) round the filter, the
  filter itself green open-cell foam (speckled pores in 475833; Dirt Rider 04 shows the stock filter, green foam).
  Rounds 1 to 3 read it as a diamond mesh.
- The black side cover (fiche 10) is a frame with a window at its front: a smooth top bar (a double line along its
  lower edge), the ribbed part behind the window (its inner edge rolled and lit). In the window the airbox's side cover
  (fiche K95CF2500 item 2): a flat satin plateau, a broad bevel round it, a dark gap; under and ahead of it the main
  frame's spar, no bar of the side cover.
- The ribs: Y shapes on a hexagonal lattice; in the studio light they read near black on the satin ground.
- RIGHT photo: no intake (plain red with a bolt at (1320, 921)), and its black cover's window is open (the shock's top
  mount shows), a triangular pocket at its foot, its bolt at (1585, 1076), not the left's mirror: not built this round.

### References
- LEFT u 2300..2640, v 860..1010 at 5x (`g_left_intake.jpg`), runs per column every 8 px (`runs.py`, 2322..2602);
  LEFT u 2080..2560, v 940..1260 (`g_left_black.jpg`), u 2170..2420, v 950..1210 and u 2130..2430, v 915..1095 at 4x,
  contrast stretched (`g_cover4x.jpg`, `g_topbar4x.jpg`); u 2380..2680, v 1150..1450 (`leg.jpg`).
- 475833: u 300..1800, v 250..2050 (`d833_cover.jpg`), u 1050..3550, v 350..1350 (`d833_intake.jpg`), edges at 2x
  (`d833_edges.jpg`), the ribs beside the bolt u 1450..2150, v 1600..2300 (`ycmp.jpg`). Dirt Rider 04 (filter).
- TOP u 2280..2640, v 1180..1300 (`top_intake.jpg`): the intake from above, a dark line 2 to 3 px under a lit facet.

### Numbers and sources (plastics.py, next to each table)
- INTAKE_PX: the red channel's contour at 120 (0.6 px blur): tip (2385.8, 938.4), rear end (2585.3, 902.3), lowest
  (2471.7, 978.3); top edge rising 0.164 px a px, lower-rear edge 0.59, lower-front 0.44. The round 2 opening
  (segmented, eroded, smoothed over 7 px) bulged at its lower front and lost the tip.
- SCOOP_PX: the crease's row (930 at u 2346 to 893 at 2582), the hook (2594..2599, 892..914), the lower band's last row
  (920.5 at 2590 to 989 at 2474), the V (2467, 988), the lower-front line (977.5 at 2458 to 938.5 at 2338), the front
  point (2334, 937). Facet 4 to 7 px, lower band 4 to 9 px, lower-front line 3 to 4 px outside the edge.
- SCOOP_D 5 / 8 mm (facet / lip; EST: steep in LEFT, 6 and 15 to 17 mm wide in 475833 seen from ahead and below);
  INTAKE_FOAM_D 10 mm behind the edge (EST: the foam is near black 23 px under the top edge in LEFT, the facet's
  shadow); the black rim 2.5 mm deep, lapping 1.5 px over the foam.
- COVER_OUT_PX (the cover's edge: the double line, rows 994.5 / 1026 / 1054.5 at u 2240 / 2290 / 2340; the gap before
  the frame's lit wall, u 2373 / 2351 at rows 1090 / 1130; the bevel's last row 1111.5 / 1147.5 at u 2240 / 2290; its
  first column 2205 / 2207 at rows 1010 / 1050), COVER_TOP_PX (the plateau: grey contour at 28 and the rows and
  columns where it ends). COVER_SET 12 mm, COVER_RISE 9 mm (EST: the bevel is lit as a steep face, its left side 95,
  its lower side 57 against the plateau's 21). WINDOW_GAP 2.5 px, WINDOW_ROLL 12 px and 6 mm (its lit band 15 to 18
  px; depth EST). TOPBAR_END_PX (2318, 990)..(2384, 1078); COVER_LOW_PX (the mud flap's top cut from the trace).
- Ribs, scale corrected: LEFT u 2400..2520, rows 1040..1110 autocorrelated: hexagonal, neighbours 12.0 / 12.1 / 12.2 px
  apart = 9.0 mm (SIDE_COVER_TILE 18 mm, two steps). Rounds 1 to 3 had 17.1 mm from 475833 with its scale taken off
  the bolt's hex as 43 px for 8 mm; the hex there is about 70 px, the pocket 257 px (31 mm, 42 px in LEFT): 0.12 mm/px,
  so the Ys are 10.4 mm apart there; the spacing-to-pocket ratio is 0.30 in LEFT and 0.34 in 475833. Arms 4.2 mm,
  1.0 mm wide (0.75 mm in 475833; 2 px dark in LEFT with their shadow), 0.25 mm high (EST). Colour map
  `side_cover_c.png`: ground (26, 26, 28), ribs (7, 7, 8) (LEFT: median (23, 24, 26), 10th percentile (5, 6, 6)).
- Foam: INTAKE_FOAM cells 1.2 mm, struts 0.22 mm, pores 0.35 mm (475833: speckles 0.4 to 0.6 mm, 1 to 2 mm apart;
  EST), `intake_foam_n.png`; colour (8, 46, 3) (LEFT lit low front (26..44, 41..65, 5..11)).

### Built
`plastics.INTAKE_PX` as the panel's hole (left only); `scoop_depth(u, v)` pushes the face in round it (a straight facet
from the crease above SCOOP_SPLIT_PX, a lip rolling in under it, t^2), with rows of vertices on the scoop's outline
(smoothed over 3 px) and 2.5 / 5.5 px outside the opening; the duct (red, then the black rim) and the foam
(`intake_foam`, UVs). `_window_left` cuts the window, the gap and the mud flap's top out of the traced side cover; the
frame's edge rolls into the window (lsurf); its top bar is `plastic_black` (smooth), the rest `black_texture`
(normal and colour maps). `_airbox_cover`: paired rounded quads (`_round_quad`, `_quad_pair`), skirt, bevel rings
(rounded both ends), plateau rings, cap. side_panels 14,792 vertices (was 11,294).

### Checks
`p1_left.jpg`, `p3_left.jpg`, `p5_left.jpg` (the cover, the ribs, the window), `p6_intake.jpg`, `p8_intake.jpg` (6x on the
intake), `cmp_cover1.jpg`, `cmp2.jpg` (close-ups beside 475833). Scores (b8 against b0, the round's start): left red
0.8921 (0.8953: the score counts the traced outline red all over, intake included, and the opening is now the
photo's full size), top red 0.8557 (0.8562), rear red 0.6427 (0.6438): the scoop's opening seen from above and behind
(TOP shows it as a dark line 2 to 3 px; with an all-black duct the top fell to 0.8547, so the duct's first part is the
panel's red). Audit: no clash of the cover, duct or foam. Also found: build_bike.srgb reads a channel value of 1 as
1.0 (the foam at (5, 32, 1) rendered bright blue): keep channels at 0 or 2 and up.

### Still different
- The photo's crease and lower lip read as crisp light lines; the model's as softer shading, with a jog in the
  reflection near u 2440..2470. The photo's crease may run further ahead faintly (475833); LEFT shows it to u 2334.
- The cover's bevels and the frame's rolled edge do not light as in the photo (left bevel 95, frame wall 130 there):
  the depths are EST and the studio lights differ.
- The red face round the intake and toward the tail still undulates softly (rounds 2 and 3).
- The right side cover (open window, pocket, bolt positions) and the right red panel's bolt: not built (see anatomy).

## R4.2 Mud flap and inner mudguard (done)

### Anatomy (REAR, LEFT, lr34, rr34, fiche K95CF3400)
- Inner mudguard, seen from behind: a shield 131 mm wide between the wall's arch and a rounded foot (lowest on the
  centre line), convex across (an upright highlight left of centre), a dark rolled lip along its foot; either side a
  flange running forward and out (lit in REAR on the left, the right one behind the can), carrying two tabs with
  holes (its mounts on the subframe's lower rails). Rounds 1 to 3 had it 170 mm wide (the flange's outer edge taken as
  the face's) and flat-sided.
- Two small round-head screws hold the flap's top to the mudguard's foot, just under the lip.
- Mud flap: hangs from the foot, an S-curve in side view (back leaning back down to the chain, then upright), its
  sides curled forward 24 to 26 mm, a fold (LEFT: a light line 6 to 8 px inside the rear edge) where the curl starts,
  smooth satin back (lr34, rr34: no ribs on its back; the fold and the curled edges are its ribs), running on behind
  the chain toward the tyre.

### References
- REAR u 1860..2140, v 780..1090 at 3x, contrast stretched (`g_rear_mud.jpg`); pairs `m0_rear.jpg`, `m1_rear.jpg`.
- LEFT u 2420..2640, v 1150..1500 (`m0_left.jpg`, `leg.jpg`), dark runs per row every 10 px (rows 1200..1460).
- lr34 u 2254..2588, v 782..1492 and rr34 u 1405..1742, v 785..1497 at 2x (`lr34_flap.jpg`, `rr34_flap.jpg`).

### Numbers and sources (plastics.py)
- MUD_HW 65.5 mm (REAR u 1913 / 2094 at rows to 940, cast at x 0.335, 0.727 mm/px: y +0.0629 / -0.0680; built
  symmetric, the photo's face is 2.5 mm right of the centre line). MUD_LOW_PX: the foot (1913, 940) .. (1950, 974) ..
  (2003.5, 999), mirrored (the right half within 4 px). Face lean 0.15 and convexity 10 mm: EST (as rounds 1 to 3).
- Flange: REAR u 1880..1913, rows 790..950 (out to y 0.087); built to MUD_Y_MAX 0.079, forward 12 mm (EST): the
  subframe's lower rails' inner faces are at y 0.083..0.086 there (at the photo's 87 mm the flange cut them 17 mm,
  audit). Tabs: holes at REAR (1903, 841) and (1892, 930) (y 0.070 / 0.078, z 0.778 / 0.713), 17 x 18 mm, holes 5 mm
  (7 px), held inside MUD_Y_MAX. Lip radius 1.5 mm (REAR: a dark line 3 to 4 px; EST).
- Screws: REAR (1947, 993), (2057, 993): y +0.038 / -0.041 (built at +-0.040), z 0.667; heads 5.5 mm (7 px), 2.5 mm
  tall (EST).
- Flap (MUD_FLAP_PX): rear / front u per row from LEFT, 2531 / 2499 at row 1220 to 2554 / 2520 at row 1390 (x 0.339 to
  0.318 at its back). Rows 1440 / 1450 reach z 0.447 at x 0.312, where the model's tyre is (the photo's axle sits
  about 8 mm higher): knobs as much as flap; the flap ends at MUD_FLAP_Z1 0.447, 7 mm over the model's tyre (rounds 1
  to 3: 0.485, at the chain). Width 55 mm a side at the top (REAR u 1928..2079 under the lip), 50 at the foot (EST).
  Fold at 78 % of the half-width, 22 % of the curl (the light line).

### Built
`plastics.inner_mudguard` (face, lip, flanges with `_thick`, tabs with holes), `_mud_flap_rings` (the back face) with
the lap behind the mudguard's foot following its convex face across (`MUD_LAP` 0.7 mm clear), `detail_plastics.rear_flap`
(the flap 3 mm thick ahead of its back; it replaces parts.py's single-surface `mud_flap`, whose Blender solidify is
set by vertex normals), `mud_hardware` (the two screws, seated on the back under their rims). rear_inner 1,568,
rear_flap 1,208, mud_hardware 124 vertices.

### Checks
`m1_rear.jpg`, `m1_left.jpg`, `m2_lr34.jpg`. Audit: no clash of these parts (on the way: the flange into the rails 17.3
mm, the flap's lap into the mudguard's sides 3.5 mm, the screws into the flap 1.0 mm: all fixed). Scores (b13): left
0.8809 / 0.8931, right 0.8689 / 0.8974, front 0.88 / 0.793, rear 0.9034 / 0.6427, top 0.879 / 0.8557.

### Still different
- REAR: the photo's left flange reads lit grey and wider (to y 0.087); the model's stops at 0.079 for the rails.
- The flap reads lighter than the photo's (in the photo it is in the mudguard's shadow, with red reflections).
- lr34: the model shows the mudguard's lower part beside the flap's top where the photo has the side cover's inner
  wall and the can (the panel's tail and the can's position: rounds 3, detail_chassis).
- The viewer's plastics toggle (viewer/bike-v0.html, PLASTICS) lists `mud_flap`, now `rear_flap` (and lacks
  `mudguard_top`, `mud_hardware`): a shared file.

## R4.3 Shroud small items (partly done: the two seats; bolts, collars and louvre edges not started)

### Done
- Shroud decks on the shrouds (audit: 1.5 mm cut). The plate's outer row was the skin's own top edge, and Blender's 3 mm
  under the plate (THIN) cut the skin's 3 mm shell along it. `DECK_SEAT` 3.2 mm: the plate now starts on the shell's
  inner face (2.5 mm: worse, 3.0 mm at the plate's rear end; 3.2 mm: no clash). TOP pair `s1_top.jpg`: no slit shows.
- Side panel bolt in its pocket (audit: 1.8 mm cut). The pocket's floor was the rim moved 8 mm in, so it followed the
  panel's slope across the 30 mm pocket and a fan closed it; the washer, square to y, cut it. Now the floor is flat
  and square to the bolt at its seat (POCKET_D under the black face at the centre) with the bolt's hole in it
  (POCKET_HOLE 3.2 mm: an M6 shank, 0.3 mm clear), and the bolt carries its shank (2.9 mm, 12 mm long) through it.
- `guard_hardware`: its brake hose clamp at the left guard's top is gone (the coordinator's request: detail_front's
  hose guide holds the hose there now); the guards' bolts stay.
- Audit after both: no clash of the plastics parts but rear_fender on the seat 0.9 mm (a seat, round 2). 12 clashes in
  all (other modules').

### Not started (seen in `s1_top.jpg`, TOP)
- The roof slots (louvre edges) in each shroud's top beside the deck: dark slits about 62 x 6 px, TOP u 1854..1916,
  rows 1011..1020 and 1227..1236; the deck's pointed front end with its gusset; the shroud bolts' hex flange heads
  (the model's read as round caps). The right side cover's own layout (open window, pocket, bolt at RIGHT (1585, 1076),
  not the left's mirror (1573, 1136)) and the right red panel's bolt at RIGHT (1320, 921).

## R4.4 Front fender and number plate small items (partly: the plate's wings; the rest not started)

### Done (the coordinator's two items, after the cockpit round 3 merge)
- The plate's wings covered the top clamp's pinch bolts and the fork caps, which LEFT shows in plain view. LEFT (and
  RIGHT, mirrored), the plate's red run per row: 33 / 44 / 47 / 47 / 45 / 38 px deep at rows 515 / 545 / 590 / 650 / 710 /
  740; the model's was 58 / 64 / 64 / 62 / 56 / 42 (its rear edge 14 to 17 px behind). Across a row the depth is the
  wings' fold over cos 27 deg: `PLATE_WING_D` 29 mm (was 45; 32 mm left the rear edge 5 px behind on average). Now
  the rear edge is within -7..+14 px row by row in both profiles (the FRONT outline's wing edge varies), the front edge
  within 3 px from row 585 down, and the pinch bolts and the cap show (`n0_left.jpg` before, `n1_left.jpg` after).
- Duplicates of the cockpit's parts removed: the fork guard's brake hose clamp (guard_hardware), and the plate's hose
  guide loop (plate_details): detail_front now has its own guide under the lower clamp with a grommet round the hose
  at the same place; this module's loop sat 12 mm off the hose's axis and cut it (audit 20.6 mm; centred on the hose,
  it still cut detail_front's guide).

### Still different / not started
- The plate's top: LEFT shows a red sliver running up from the wing's top corner to row 441 beside the bar (FRONT: the
  red above the plate's top edge beside the bar pad, measure.py 'front_plate_rt', not built since round 1); TOP, lf34
  and rf34 not checked.
- Not started: the plate's and the fender's bolts, the fender's underside ribs.

## Round 4 totals
Vertices (both modules' parts): 73,868 (budget 160k). Audit: no clash of these parts but rear_fender on the seat 0.9 mm
(a seat). Scores and tests: see the report (b20).
