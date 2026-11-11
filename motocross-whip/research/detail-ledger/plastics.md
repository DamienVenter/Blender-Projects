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
  too wide seat. It is the shroud's bolt plate running back under the seat: `DECK_END_U` 1950 to 2120 (x 0.665);
  the plate there lies 3 to 6 mm under the hem and 9 mm under the base. Top red score 0.861 before, 0.874 after.

### Still different
- The tail tip is buried in the rear fender's root (fender hump over x 0.064..0.109: audit 4.2 mm), and from
  behind the seat's base shows under the fender's tip (rear red score 0.627 to 0.597, floor 0.62): component 3.
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
