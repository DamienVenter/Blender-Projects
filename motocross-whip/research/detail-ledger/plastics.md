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

## 3. Rear fender (partly done)

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

### Still different
- The deck's crease bands read fainter than the photo's (bright band and dark facet); crown and facet are EST.
- The panels' tails stand out as a flap with a hard rear edge in lr34 and the left pair; in the photo they wrap
  smoothly onto the fender's flank (their surface still follows the plan envelope out to 0.13..0.15).
- Underside: the photo's tunnel roof and its two ribs are not modelled; the wall under the tail keeps its flat top
  and two channels (rear pair).
- The upper mounting bolts and collars (fiche items 3, 4) are not modelled (hidden in every photo).
- The model's tip is 8 mm longer than the side photos' and 8 mm shorter than the top photo's (the mean).
- An exhaust piece of detail_chassis (62 vertices at world (0.084, -0.147, 0.882)) is now 4.7 mm from anything: it
  touched the old fender's root flare, which was not the fender (it was the panels' tails' envelope).
- test_bike's intruder test now finds the muffler (left view, 3.4 cm2 at u 2844..2910, v 886..908) inside the traced
  outline OUT 'rear_fender'. The photo has no red there: per column the last deep-red row (r - g over 150) is 907 /
  897 / 886 / 883 / 873 at u 2845 / 2860 / 2875 / 2890 / 2905, and under it the muffler, tinted pink by the red
  (e.g. (186, 120, 124) at (2875, 900)). The trace took the tinted muffler as red (the first pass noted the same
  tint at the fender's root). The old fender's flank covered it; the panel's tail now stops on the photo's edge.
  Fix proposed: the trace (outlines.py, shared output) should take the deep red only there.

## 4. Side panels (partly done)

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

### Not done (still different)
- The intake: the model has a dark triangular hole with a turned edge; the photo's is a rounded trapezoid with a
  lighter recessed lip and a dark green mesh (the filter) behind it.
- The red panel's surface is lumpy and its lower edge ragged in the close-ups (`cu10/render_cu_sidecover.png`).
- The bolt's recessed round pocket in the black part (the bolt is there: detail_plastics.panel_bolts).
- The raised airbox side cover ahead of the black part, and the crisp red/black joint.
- The tails' surface: a flap out to the plan envelope where the photo's wraps onto the fender's flank.

## 5. Mud flap and inner mudguard (not started)

## 6. Shroud small items (not started)
- Also: the red strip beside the seat's nose in the top photo (u 1960..2160, between the hem and the shroud) is not
  red in the model (component 1).
