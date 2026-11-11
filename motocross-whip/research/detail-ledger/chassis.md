# Detail ledger: chassis (detail_chassis.py), micro pass 2026-11-11

Damien's brief: every small component is a separate build, checked beside its reference photo. One section per
component: anatomy, references, numbers and sources, what was built, checks, what is still different.
Scratch images are under the agent's scratchpad `agents/micro/chassis/` (not committed).

## Shared finding (for the coordinator): the photos' rear axle is 8 mm above parts.RA
- LEFT: the 50T sprocket's five visible bolts fit a circle to 0.3 px; its centre cast on the sprocket's plane
  (y 0.095) is x -0.0008, z 0.3343. The axle's bore (dark disc, 24 px) cast on y 0.13: x -0.0007, z 0.3343.
- RIGHT: the axle's bore (17.7 px) cast on y -0.14: x 0.0002, z 0.3377.
- The swingarm's top edge in both photos is 7 to 8 mm above the model's near the axle and level with it near the
  pivot: the photo's arm turns about the pivot to an axle at z 0.334 to 0.338, not parts.RA (0.3264).
- Nothing shared was changed. Every swingarm shape below is measured relative to the photo's own axle-to-pivot
  line and built on the model's (RA to PIVOT), so it keeps its shape and turns 0.8 deg with the model. In the
  pair sheets the model's rear end therefore sits about 10 px low.

## Shared finding: the pedal and master cylinder were not on the bike
detail_wheels.py's caliper part is named `rear_brake`, and so was this module's pedal part; plugins load in order
and the wheels module (later) replaced it. Renamed here to `brake_pedal` (test added).

## 1. Rear axle ends (part `rear_axle`)
Anatomy at 30 cm: left, the axle's head, a round steel flange with two flats along the slot (they bear on the
block's rails), chamfered rim, a large bore (black inside, its mouth lit); right, a 32 mm U-nut: hexagon with both
faces chamfered (the chamfer circle shows on the face), its round locking collar on the outer face, the axle's end
standing 1.3 mm proud of the collar with a chamfer and a black 13 mm bore. The hollow shaft between them (hidden).
References: LEFT px 2925..3040 x 1575..1670; RIGHT 985..1100 x 1580..1675; REAR 1770..1850 and 2110..2210 x
1480..1600; lr34 2630..2760 x 1560..1680; rr34 1240..1360 x 1560..1680; web/axle_42301-KRN-A30_*.jpg (used axle,
same part number 2009 to 2025: round flanged head with a bore).
Numbers:
- Head: 35.8 mm round (LEFT 47.5 px along the slot), 30.6 mm across its flats (40.5 px across), 4.5 mm proud of the
  block (REAR: lit edge at y 0.1303, block face 0.1258). Bore 18.1 mm (LEFT dark disc 24 px).
- Nut: 32 mm across flats (an M22 nut kit listing: 32 mm hex for the 2022 CRF250R; RIGHT 44.5 px across flats with
  blur; REAR 53 px across corners, 36 mm). Honda part 90305-KZ4-J20 "NUT, U (22MM)": M22 thread. Hex 8.9 mm thick
  (REAR cols 2184..2197), collar 4.1 mm (2197..2203), 29 mm round (rr34 proportion, EST), axle end to y -0.1402
  (col 2205). Axle bore 13.3 mm (RIGHT dark disc 17.7 px). Shaft 22 mm (M22), its head-end bore 18.1 mm.
- Hex corners up and down (RIGHT: the vertical flats left and right).
Built: `rear_axle()`: hollow shaft, `slab2` head with flats, `hexnut` (new helper: ISO-shaped nut with 30 deg
chamfers), lathe collar and end, dark `bore` material inside both bores (30 mm deep, closed there: in the photos the
bore is black; a through hole would show the background).
Checks: v5/v6 pair sheets left, right, rear, lr34, rr34; close-ups cu_axL, cu_axR, cu_axL34 (cu1/). Tests:
`test_axle_ends_stand_out_as_in_the_rear_photo`, `test_axle_nut_is_a_32_mm_hexagon`.
Still different: the photos' steel is brighter and more mirror-like (chrome-plated look) than the model's `steel`;
the collar's diameter is EST from proportions.

## 2. Axle blocks and adjusters (part `rear_axle`)
Anatomy: square aluminium block in the slot, its face 2 mm under the casting's face; raised rails along its top and
bottom edges (the head's flats sit between them); on the LEFT block two bright tabs at the rails' rear ends; the
slot's rear end is an arc (the dark crescent behind the square block); ahead of the block the adjuster: an M8 bolt
whose dog point bears on the block, its thread, and a 12 mm lock nut against the window's front wall, all bright
plated.
References: as 1, plus LEFT 2925..2970 x 1595..1630 and RIGHT 1030..1080 x 1595..1635 (adjusters); fiche
K95CF3200 (adjusting bolt 22, nut 25, block "F-19-20").
Numbers: slot direction 13.5 deg in LEFT (edge contrast of rails and block edges, best over 6..16 deg) against the
photo's axle-to-pivot line at 14.47: built 0.97 deg below the model's arm line. Block 37.3 x 37.4 mm (LEFT edges at
-24.5 and +25 px along, rails 49.5 px apart). Slot, window and casting stand 0.8 to 1.9 mm above the axle's centre
(LEFT window +27.5/-26.5 px, RIGHT pocket +29/-24): N0 = 0.8 mm. Rails 2.2 mm wide, 0.8 high; tabs 7.5 mm long
(LEFT u 3004..3014). Slot arc radius 48 mm (crescent 4 mm on the slot line, closing at the block's corners).
Adjuster M8 x 1.25 (LEFT thread 10 px = 7.5 mm, RIGHT 8 px), nut 12 AF x 7 mm (LEFT 10 px long), dog point 6 mm.
Built: block `slab2` with an offset bore, rails and tabs; `hexnut`, `thread` (new helper: rolled ISO thread as a
helix) and a dog point.
Checks: as 1. Tests: `test_block_slides_in_its_slot`.
Still different: the bolt's head is not modelled (no photo shows it: it would sit in front of the wall, inside the
casting); the pocket's floor contour (a curved step under the bolt in LEFT) is a plain floor; the darkness in front
of the block in the close-ups is the pocket's shadow, as in the photos.

## 3. Swingarm: cast ends, arms, welds, pivot end (part `swingarm`)
Anatomy: each arm is a tall extruded box (brushed), welded at both ends: at the rear to a cast end that carries the
slot window, the adjuster's pocket, a 2 mm ledge round the slot, two rows of nine index marks (long and short in
turn, 2 mm apart) above and below the window, a U-shaped rear end; at the front to the pivot casting that closes in
to the boss inside the frame plates. TIG beads with heavy ripples round the whole section at both joints.
References: LEFT 2250..3080 x 1380..1760 and 2890..3045 x 1565..1675; RIGHT 920..1750 x 1380..1760; lr34, rr34
as above; fiche K95CF3200.
Numbers:
- Arm height (`armscan`: bright run of the side face at 28 stations in each photo, + 1 mm for the rounded edge):
  60 mm at the rear weld (s 0.05), 70 at s 0.20, 75 to 76 from s 0.26 to the front weld. The old model was 37 and
  57 mm (its outlines lost the arm's lower half). Top and bottom tables in `_T_TOP`, `_T_BOT`.
- Welds: rear s 0.046..0.061 (LEFT), 0.039..0.050 (RIGHT): centre 0.050; front 0.461..0.482 and 0.453..0.475:
  0.468. Bead 15 mm wide across the corner (LEFT 20 px, RIGHT 25 px), 2.8 mm high, ripples 2.8 mm (lr34: about 12
  across the arm's top).
- Cast end: rear end 29.4 mm behind the axle (LEFT 40.5 px, RIGHT 37.5), top 28.2 mm above (LEFT 37 px, RIGHT 39),
  bottom 25.2 below (34, 31.5), corners 11 mm. Window 40.6 mm tall, front wall 41 mm ahead of the axle (LEFT 53 px,
  RIGHT 57). Outer face y 0.128 (REAR row 1545), inner face 0.0937 (0.2 mm off the wheel's collar).
- Index marks: rows of 16 mm centred on the axle (LEFT), long 3.2 mm and short 2.0, 1 mm off the window's edge.
- Arm outer face 0.129 (REAR), 31 mm wide; tapers 2 mm to the front weld (EST); pivot casting closes to 0.110 by
  x 0.50 (the frame plates' inner faces, 0.111).
Built: `_arm_section` lofts (rounded 4 mm, LEFT highlight 3..4 px), `_weld` (half-buried ellipse with crescent
ripples of uneven height), `_cast_outline` (U end from the slot-frame lines blended onto the arm's edges),
`slab2` (new: rows of vertices round holes too, a crisp 0.6 mm window rim in a 1.5 mm-rounded casting), ledges, the
pocket floor, index marks as dark 0.7 mm lines. The chain slider and the cushion arm's lug follow the new edges.
Satin material for the castings (the brushed `alu_swingarm` streaked on cast faces).
Checks: v3 arm pairs (left, right), v5/v6 axle pairs, cu1 close-ups. Tests: `test_arm_is_the_tall_box_of_the_
photos`, `test_index_marks_two_rows_of_nine_each_side`, the old chain and tyre tests.
Still different: the arm's brushed texture is a material, not a normal map; the plan view of the arms is EST (the
top photo has them under the side panels); the inner rear face (REAR: a dark band 0.1145..0.1276) is lighting, not
modelled; the caliper bracket's stopper is not seen in any photo and is not modelled; the chain slider keeps its
old two-strip shape (not rebuilt in this pass).

## 4. Chain guide (part `chain_guide`)
Anatomy: an aluminium plate on the outside with a rounded front window and a long sloping rear slot (the chain
shows through both), three M6 flange bolts with bright washer faces, two tabs welded under the left arm (a wide
front tab, a narrow rear strut) that the plate bolts to, nuts on their inner side; behind the plate the black
plastic block: an inner wall and two wear rails round the lower run, its nose showing ahead of the plate's front
edge (a dark band 6 mm wide).
References: LEFT 2700..2930 x 1590..1790 (outline read on a 7x crop 2730..2920 x 1640..1780); lr34 2440..2700 x
1520..1780; fiche K95CF3200 (plate 11, block 10, bolts 18 and 19, nuts 23).
Numbers: outline, windows, bolt centres and tabs as pixel lists (GUIDE_PLATE, GUIDE_WIN, GUIDE_SLOTW, GUIDE_BOLTS,
GUIDE_TAB, GUIDE_STRUT), cast on the plate's plane (y 0.108) and carried from the photo's arm onto the model's (the
8 mm datum, see above) by `_photo_px`. The plate reaches from x 0.051 (over the 50T) to 0.181: the old guide (0.100 to
0.201) stood 5 cm too far forward and had no windows. Bolt heads: bright rings 12 mm across (M6 flange bolts, 8 mm
hex). Plate 3 mm (EST), tabs 4 mm (EST).
Built: `slab2` plate with two holes, tabs whose tops run into the arm's underside, `hexbolt`/`hexnut`/`thread`,
`_clip_below` (new) for the block's wall, rails kept on GUIDE_SLOT and clear of the 50T's teeth.
Checks: g2/g3 pair sheets (left, lr34), close-ups cu_guide, cu_guideb (cu2/). Tests: `test_chain_guide_is_the_
stock_plate`; `test_chain_guide_slot_takes_the_chain` refined (the chain's 21 mm width, the 50T's plane, the arc
the chain wraps).
Still different: the block's upper part (lr34: a black rounded hump above the front window) is a plain rail; the
plate's edges are a little rounder than the photo's sheared edges.

## 5. Muffler (part `exhaust`, the can only; the header was not reworked)
Anatomy: brushed aluminium can of flat facets (an octagon with soft corners), its rear cap a separate pressed
hood whose front edge runs on a slant (long on top, reaching the rear at the bottom), riveted with blind rivets
(domed heads, mandrel holes); the cap's rear face flat and leaning forward at the top, rounded into the facets; the
outlet a rolled 37 mm lip with the spark arrestor's sleeve inside it (lip, black gap, sleeve ring, black bore); the
front nose riveted to the can; the mount under the side panel.
References: RIGHT 960..1560 x 860..1280; REAR 2100..2330 x 680..920 (2x crop); rr34 1150..1700 x 700..1100.
Numbers: section (REAR cast on x 0): top z 0.901 (y -0.1015..-0.1658), outer chamfer to (-0.1916, 0.8665), outer
side to z 0.799, lower chamfer to (-0.1778, 0.769), bottom 0.765, inner corner (-0.095, 0.778)..(-0.0868, 0.792),
inner side to 0.880. Cap face leans 14.5 deg (RIGHT: from px (1040, 875) to (1000, 1030)). Outlet: lip 54.8 px =
37 mm, black ring 30.6, sleeve 25.8, bore 19.6 (REAR); centre px (2204, 783) after the lean (test: within 6 px of
(2202, 788)). Rivets: RIGHT px (1114, 924), (1079, 988), (1054.6, 1041.6) on the cap's edge, (1430.8, 1181.2) and
(1408, 1219.8) on the nose; heads 5.5 mm (6 to 7 px). Cap edge: a plane through the three cap rivets, 6 mm ahead.
Built: `_SEC` re-read as an octagon (was a rounded 15-point blob), `_muf_ring` leans the cap's end, outlet with lip,
sleeve and dark bore, rivets as domed blind rivets, the cap's edge as a 0.6 mm step all round.
Checks: m1/m2 pair sheets (right, rear, rr34). Test: `test_muffler_section_is_the_rear_photos_octagon`.
Still different: the cap's edge in REAR crosses the can 1 to 2 cm higher than the photo's (the edge is not a plane:
it is lower at the bottom); the dent along the can's top (the old pass's drop under the side panel's inner wall)
shows where the panel ends; the mount (strap, grommet, collar, bolt) is hidden under the side panel in every photo
and stays the old EST strap; the header and its clamps were not reworked in this pass.
