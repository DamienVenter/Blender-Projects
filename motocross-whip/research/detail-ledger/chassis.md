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

## 8. Rear brake pedal and master cylinder (part `brake_pedal`)
Anatomy: a cast aluminium pedal: a round boss on an M8 socket screw, the arm rising in an arc over the pivot and
sweeping down past the clutch cover to a folding serrated tip on a pin; behind the pivot a short lever to the push
rod's clevis (cheeks, pin, split pin), the push rod with its lock nut, a rubber boot of three convolutions, the
cylinder body, the reservoir cast on top with a black cap and two screws, two mounting bosses bolted to a tab on
the frame plate's rear edge, the banjo on the body's rear with the hose's first bend, the return spring.
References: RIGHT 1560..1980 x 1260..1600 and a 3.25x crop 1680..1990 x 1420..1620; fiche K95CF1500, K95CF2900.
Numbers: pedal line (11 points, PEDAL_LINE) and its width (21 mm at the arc, 14 at the tip, PEDAL_W) read square to
the line; boss 25 mm (17 px radius); socket head 13 mm (18.5 px); tip 32 x 22 mm, five teeth (RIGHT px 1932..1975 x
1508..1537); y of the arm and tip from the old pass's top-photo reading (arm -0.1445..-0.161, tip -0.161..-0.193).
Master cylinder from RIGHT px: boot's foot (1640, 1452), reservoir top (1615, 1290), clevis pin (1640, 1505), banjo
(1595, 1345), mounting bolts (1655, 1318) and (1652, 1382), all cast on the cylinder's line y -0.1345 (EST: 6.5 mm
further out than before, clear of the swingarm's front casting, which the photo shows wide up to the frame plate).
Built: new `rear_brake()` (part `brake_pedal`), `_toe()`. The part's own long hose was removed: detail_wheels.py's
`rear_brake` already draws the hose from the caliper's banjo along the arm to (0.47, -0.086, 0.515) by the
cylinder; this part's hose now only leaves the banjo and turns down to meet it there. (Who owns the hose: the brief
gives it to this module; the coordinator should keep one of the two.)
Checks: p1/p2 pair sheets (right). Audit before this pass: the cylinder's clevis cut the swingarm 3.2 mm and the two
hoses crossed (3.3 mm): both addressed here; re-audit at the end.
Still different: the cylinder body is a plain cylinder (the photo's casting has a flat face with cast lettering and
ribs); the photo's reservoir is narrower front to back; the pedal's arm is a swept rounded bar, the photo's has a flat
face with a ridge; the pedal stop bolt and the brake light switch (none on this bike) are not modelled.

## 6. Shock (part `shock`): partly
Anatomy (fiche K95CF3300 and Dirt Rider 07-08, 09): body with the upper eye (bearing and two seals), the
reservoir cast across the head to the right with its end cap, circlip (22) and the two-stage compression adjuster
(a 14 mm hexagon with a slotted screw in it), the thread for the rings, lock ring (7) and preload ring (6) each with
eight notches, the spring (closed and ground ends), the shaft, the bump rubber (11), the lower spring seat (25) with
its stopper ring (24), the bright stepped bottom cup with grooves (Dirt Rider 09), the clevis with the rebound
adjuster's slotted screw and a cut arrow mark, upper and lower bolts with washers and nuts.
References: RIGHT 1580..1800 x 1050..1640 (the reservoir's cap through the frame at px (1727, 1096)); LEFT 2200..
2450 x 1050..1640 (coils behind the plate); Dirt Rider 07-08 (cap), 09 (cup and clevis, "S" and arrow).
Numbers: the cap cast on y -0.075: (0.546, 0.730), 19 mm behind the shock's axis: the reservoir lies across the
bike (it was parallel to the body, behind it). Cap 34 mm (45 px). The rest as before (EST from the real part: 481
mm eye to eye, 50 mm body, 8.25 coils of 12 mm wire on a 71 mm mean diameter).
Built: new `shock()`.
Checks: close-up cu_link (cu3/) for the cup and clevis; cu_res shows only the cap's edge (the side panel hides it,
as in every photo). Audit: the clevis's nut and the connecting rods (2 mm) fixed by a 14 mm nut with its flats up.
Still different / not done: the "S" letter is not cut (only the arrow's shaft); the body's colour and the spring's
colour are EST (the photos show only dark coils); no close-up matches Dirt Rider 09's exact angle.

## 7. Pro-Link (part `linkage`): partly
Anatomy (Dirt Rider 09, right side): two forged connecting rods, each a dog-bone with round eyes and an I-section
(flanges along both edges, the web between them), joined by a bridge; the cast cushion arm (a triangle with three
bosses); M14 bolts with flange heads on the left, washers, U-nuts and two threads of the bolt's end on the right;
the shock's clevis bolt just under the rods.
References: Dirt Rider 09; LEFT px (2469,1552) (2386,1607) (2471,1617) (2298,1558); RIGHT px (1524,1551)
(1611,1606) (1524,1608) (1702,1557) (the old pass's pivot readings, kept).
Numbers: rods 18 mm deep (0.55 of the eye, Dirt Rider 09), eyes 31.6 mm, web 4.8 mm, flanges 9.2 mm; nuts 22 mm on
T and B (0.73 of the eye in Dirt Rider 09: M14), 17 mm on F (M10: clear of the frame's lower cross member), 14 mm
on the shock's bolts.
Built: `_dogbone`, `_pivot_bolt` (new), the rods replace the old one-piece triangular plates (which wrongly took in
the shock's bolt).
Checks: close-up cu_link (cu3/). Audit: F's nut cut the frame's lower cross member 8 mm with M14 hardware: M10 there.
Still different: the cushion arm keeps its old plain triangle (no recessed web: a raised rim clashed with the
clevis ears and was taken out); the grease nipples (none seen) and the seals at the bosses are not modelled.

## 9. Footpegs: not started in this pass (the old pass's cage pegs, spring and pin stand).
## 10. Subframe and frame rear: not started in this pass. Noted on the way: the right photo's frame below the pivot
(the lower spar and its large opening, RIGHT 1560..1980 x 1260..1600) differs from the model's plate there.

## Audit and tests at the end of this pass
Whole-bike audit (audit.py, 25 mm) on the merged build of this worktree, chassis parts only:
- brake_pedal x rear_brake 2.8 mm: the hose's splice by the cylinder (this part's banjo bend meets detail_wheels'
  hose end): one hose drawn by two modules, to be given to one owner.
- frame x swingarm 1.9 mm: the pivot casting reached into the pivot bolt (r 8.5): ended short of it afterwards
  (s = ARM_L - 11.2 mm); not re-audited.
- frame x linkage 0.8, frame x shock 0.4, footpegs x frame 1.0 mm (footpegs' is from before this pass).
- The cap rivet found floating (the photo's rivet lies over the model's lower can top) is placed on the can's
  outer flank nearest the camera's ray since.
Before the fixes the audit had: link nut into the frame's lower cross member 8.0 mm, cylinder's tab into the frame
plate 3.4 mm, guide tabs into the arm 3.2 mm, rods against the shock's clevis nut 2.0 mm: all fixed.
Module: 140,510 vertices (budget 200,000).


# Round 2 (2026-11-11, after the coordinator's review)

## 5. Muffler, again: the lumps, the cap as a pressed part, brushed finish, the mount
Cause of the lumps (found in the code): the old section table's top line changed slope five times (-0.32, -0.67,
-0.30, -0.67, -1.14), a 20 mm dent was pressed into the inner top for the side panel's lip (x 0.09..0.235), and the
section morphed from the octagon into a circle over the can's front 11 cm. Fixed at the source: the can is now the
octagon on two straight lines (RIGHT: the lower edge is straight from x 0.029 to 0.301 within 4 mm of the old table;
the top line parallel to it, 108 mm above: LEFT row 878 and REAR's 0.901 disagree by 11 mm and the top splits it),
straight in plan (TOP and REAR lines). The octagon's inner chamfer already clears the panel's lip by 3 to 9 mm, so
no dent. The morph into the circle is only in the nose (x 0.296..0.350), a separate part with its own 0.6 mm step.
The end cap is a separate pressed part: its flat leaning face, an 18 mm roll (rr34, REAR), its sides out to its
front edge, cut per vertex on the plane through the three cap rivets (the photo's seam line from px (1125, 895) to
(1048, 1060) lies within 3 to 7 mm of it), then a 0.6 mm step down to the can.
Brushed finish: textures/stock/brushed_n.png (`brushed_map()`, numpy: streaks along u, 0.08 m per repeat), UVs
along the can's length on the can, cap and nose (`_uv_grid`), a plane map on the cap's face (REAR: level lines).
Mount (the coordinator's audit: a piece floated once the new rear fender dropped its root bulge): two brackets
welded on the can's inner flank up to a tab square to the right subframe rail's underside, an 8 mm rubber bush, a
steel collar and an M8 flange bolt up into the rail; the stack 4 mm inboard on the rail, clear of the panel's lip.
Checks: m3, m4, r2a, r2b pair sheets (right, rear, rr34).
Still different: the rear view's cap edge crosses the bottom 1 to 2 cm higher than the photo's; the brushing does
not show at the studio photos' scale (it does in close-ups).

## 3. Swingarm, again: the "coil" in front of the pedal
It is the right arm's front weld bead (RIGHT px 1587..1618 x 1420..1512: a weld there too), drawn 2.8 mm tall with
deep regular ripples in a bright material: it read as a spring. Now 2.0 mm, shallower uneven ripples, duller.

## 8. Brake hose joint
This module's hose now starts inside a crimped joint sleeve at detail_wheels' hose end (0.470, -0.086, 0.515),
heading (0.574, 0.078, 0.815) (the end of their run, measured on their mesh), and loops up and back round the
cylinder's inner side into the banjo: the two hoses meet end to end inside the sleeve's bore (0.5 mm clear).

## 9. Footpegs (partly)
Detail 475839 and RIGHT: the pegs are black with the teeth's tips worn bright, and the side rails are deep at the
root and shallow at the tip (a triangle from behind). Now `peg_black` (CLASS black) with `peg_edge` crests, rails
21 mm deep at the root to 8 mm at the tip. Not done: the cast cage's own shape (open cells, the brace's section),
the hinge bracket's shape.

## Round 2 follow-ups
- The can's height now falls straight, 18 mm per 100 mm (MUF_TAPER), from 108 mm at the cap: with the plastics
  agent's side panel the straight can stood 20.8 mm into the panel over the nose (x 0.26..0.32, hidden part). A
  straight taper keeps every facet flat (the old bend under the panel was the kink).
- Brake hose: detail_wheels now ends its run at (0.452, -0.100, 0.505) heading (0.826, 0.032, 0.562); this part's
  hose starts there inside the joint sleeve and loops up round the cylinder's inner side into the banjo.
- test_bike.test_nothing_shows_through_the_plastics, with the plastics agent's branch merged locally: a 3.2 cm2 hole
  in the left view inside the plastics' outline. With the round-1 can in the same build the can fills it (and is
  flagged as an intruder, 3.8 cm2); with main's plastics and the new can there is no hole: a gap in the new
  plastics, not in the can.
- Not done in round 2: 10 (the frame casting round the pivot: ribs, pockets, bosses and its window), the rest of
  6 (the "S" mark, a Dirt Rider 09 angle check) and 7 (the cushion arm's recessed web), the subframe rails.


# Round 3 (2026-11-11, third chassis agent; scratch images under `agents/micro/chassis3/`)

## 10. Frame rear (part `frame`): the cast pivot section, both sides
Anatomy at 30 cm: each side is an extruded spar (brushed along its length) whose rounded end is a tongue welded
into the rear casting with a U-shaped TIG bead (10 mm wide, rippled, its top run going on along the spar's top
edge under the upper mount's ear); the casting (matte, fine sand-cast grain, lighter than the spar: photo grey 192
to 205 against the spar's 165) runs down as one leg, its front edge a large concave C round the engine (softly
rounded, about 7 mm), its rear edge crisper (4 mm); round the pivot a boss 52 mm across, 2 mm proud, with a cast
fold where it meets the C; RIGHT: the pivot's 21 mm nut sits in a 31.8 mm counterbore (a dark ring round it), the
bolt's end 16 mm with a 7 mm bore; LEFT: the bolt's head sits in a hexagonal recess 27.7 mm across flats (corners
fore and aft) with a dark 1.4 mm gap round it, its face darker than the casting, a 10.6 mm bore; RIGHT: two tabs
behind the leg with round bosses (24 px) for the master cylinder's M6 flange bolts, a '>' of two small ribs from each
boss into the leg, a square pocket between them; below the pivot the casting splits round a shallow triangular
pocket with a lit rib on its upper side into the footpeg pad (raised) and a front branch down to the cradle rail,
which it meets at a second bead; the chain roller's bolt on the right's lower rear.
References: RIGHT 1450..2150 x 850..1680 (r_frame), 3x crops r_fz1 (1620..1900 x 1150..1470), r_low3 (1600..1900 x
1250..1620), r_weld, r_mc, r_pocket; LEFT l_frame, l_low (2060..2360 x 1400..1620), l_weld, l_pocket (6x), l_shift
(5x); piv2 (6x of both pivots with intensity rows/columns); REAR rear_frame; equalised crops r_leg_eq, l_leg_eq.
Numbers: outline = OUT2 'frame' (LEFT, it fits the right photo's leg within 4 px, o1_right) + the footpeg bracket +
each side's own lower section (LOW_PX) + the right's tabs (TAB_PX), cast on the plate's mid plane and joined by a
0.5 mm raster union softened 1 mm (cast fillets). The two photos' lower sections agree within 10 mm (the bottom of
the cradle weld: LEFT z 0.348, RIGHT 0.358; each side keeps its own). U bead lines TONGUE_PX (x 0.578..0.72, z 0.674
..0.81). Pivot ends in PIV_* (piv2 profiles: right row 1432 and column 1751, left row 1433 and column 2249). Tab
bolts RIGHT (1645, 1338), (1652, 1402): the round-2 master cylinder bolts at (1655, 1318), (1652, 1382) were 15 mm
high and stood on a 2 mm plate stuck on the leg, removed. Tabs 4.5 mm thick (EST). Edge radii 7 / 4 mm, tabs 1.2.
Built: `_Cast` (a height field over the side outline: outer face at _spar_y with blended edge radii, the boss, the
footpeg pad (+4 mm, carrying the pedal's pivot), tab bosses, the pocket; inner face 26 mm in, reaching in round the
cradle rail's end), `_union_outline`, `_frame_welds` (`_bead`: open rippled bead on a face), `_pivot_ends`,
`_tab_bolts`, `_cast_ribs` (smooth beads), `cast_map` -> textures/stock/cast_n.png (grain 0.3 mm over a 1 to 2 mm
orange peel), materials frame_cast (grain, strength 0.3), frame_spar (brushed map along the spar), steel_dark.
Master cylinder (brake_pedal) re-read to sit inboard of the tabs: bore column 20.5 mm (r_mc: u 1620..1647) with its
front flat 5.5 mm ahead of the axis where it passes under the tabs, the reservoir as a second column 18 mm behind
(19 mm, u 1597..1622) with a round black cap and screw, the banjo's black fitting and bolt on the bore's top, two lugs
behind the tabs; the return spring moved out to y -0.1425 (the lower section now reaches under it).
Checks: o2 outline overlays (left, right); f2/f4/f8 pair sheets right 1600..2000 x 950..1620, left 2000..2400 x
950..1620 and the brief's box; close-ups cu1..cu6 (cu_pl, cu_pr at the pivots, cu_wl the left U bead, cu_mc).
Three cycles: (1) torn white shards round the pocket, pad and chevrons: not the bevel (frame bevel now 0.1 mm), not
the UVs (one side projection now), not the normal map (off: still there) but narrow ridges and steep steps in the
height field on a 2.5 mm Delaunay mesh; the ribs became swept beads, the pad and pocket gentler (8 mm and 5 mm
ramps), the edge radius blended between neighbouring outline points; (2) the left head read proud and bright: now
flat-topped, 1 mm under the face, darker; (3) a saw tooth along the spar's top edge where the bead runs on the edge
(spar and casting finishes alternating): faces under the bead take the spar's finish.
Tests: `test_frame_rear_casting_follows_both_photos`, `test_pivot_ends_are_the_photos_nut_and_recessed_head`,
`test_master_cylinder_clears_the_frame_tabs`.
Still different: the leg's section is flat with rounded edges (the photo's front face may be slightly crowned; no
photo shows the section); the upper ear's own bead (between the ear and the spar, LEFT 2147..2187 x 990..1017) is
the U's top run continued, not a separate bead; the engine hanger plates belong to detail_engine.py (they sit on the
frame's inner face; in both photos their plates and bolt heads are OUTSIDE the spar, over its lower bead: reported).
Shared: detail_engine's shift shaft SHIFT (0.609, 0.403) is EST; LEFT l_shift shows the lever's clamp centred at
about (2185, 1505), z 0.425 cast on the plate: its clamp now cuts the frame's front branch 2.4 mm.

## 2. Muffler cap and nose (part `exhaust`), round 3
Rear profile (RIGHT, the rear-most pixel of each row, cast on y -0.14, scratch r_cap): the cap's face is upright at
x -0.0072 from z 0.866 to 0.838, a knee of about 50 mm radius (x -0.0047 at 0.820, -0.0027 at 0.811), then one 45
deg facet (0.0111, 0.793), (0.0199, 0.784), (0.0309, 0.775) to the can's underside at (0.0465, 0.765); the top corner
rolls over about 25 mm. Round 2 leaned the whole face 14.5 deg on one line (13 mm too far back at the top) and the
18 mm roll met the bottom as a crease. Now `_cap_x(z)` shapes the face (12 rings, fine enough for the knee), the roll
shrinks from 18 mm to 2 mm where the cap's seam meets the lower facet at the bottom (as in the photo), every cap
vertex takes the can's section at its own station (the cap's sides follow the can's sloping lines). Outlet square to
the upright face. Three rivets seen from behind (REAR rear_cap: lower corners (2142, 870), (2268, 870), bottom (2205,
898)) placed where the rear camera's ray meets the cap.
Nose (RIGHT r_nose, cast on the can's flank y -0.17): the can's front edge is slanted, (0.3176, 0.6373) at the bottom
to (0.3411, 0.6875) under the side panel (round 2: square at x 0.296, 2 to 4.5 cm behind); the nose is a separate
pressed cone of darker satin steel (header_steel) from 4 mm under the can's edge to the inlet's weld ring at x 0.371,
level for its first third, then turning into the pipe tangentially.
Brushed finish: brushed_n.png had a 2 deg spread of normals across its lines (y std 0.038; x quantised to 0): now
k 0.16, std 0.099 (about 6 deg); UVs along the can (u = x) and level on the cap's face (checked in cu_capr at 30 cm:
the streaks read). The cap's roll keeps the can's map (the face's plane map streaked it sideways).
The octagon's corner smoothing stays at 6 samples: 3 made the outer top corner stand 12 mm over LEFT row 878 (test).
Checks: cu6 (cu_cap from behind beside rear_cap, cu_nose beside r_nose, cu_capr from the right at 30 cm), f8 pairs
right 960..1560 x 860..1280 and rear 2100..2330 x 680..920.
Still different: from behind the knee still reads as a darker band in the studio render where the photo's cap is
evenly lit (muffler roughness raised 0.26 to 0.36 for it; not re-rendered); the photo's octagon has longer upper
chamfers on the inner side; the nose's pressed facets (a crease in the photo) are a smooth morph; in the right view
the plastics agent's side panel hangs over the can's upper half (theirs).

## Round 3 audit (audit.py 25 mm, merged with main's plastics), chassis parts
engine x frame 1.9 mm at (0.601, 0.134, 0.412): detail_engine's EST shift clamp over the frame's front branch (LEFT
l_shift: the clamp is centred near (2185, 1505), z 0.425; SHIFT is at 0.403); footpegs x frame 1.0 (the hinge pin's
washer seated on the pad); exhaust x frame 0.9; brake_pedal x frame 0.8 (cylinder lug behind the tab); frame x
linkage 0.8; cables x frame 0.5; frame x shock 0.4; brake_pedal x rear_brake 0.0 (the hose joint, end to end). No
floating pieces (the first audit found the lower cross member loose: the right plate's tab thinning had spread over
the whole lower section; fixed). Module 196,794 vertices (budget 260,000).

## 2b. The coordinator's lr34 evidence (plastics s_r16_lr34): looked at, not resolved
The photo's cap and the can's inner face look about twice as wide as the model's and its can more level. The model's
can axis projected into lr34 (lr34_axis: its cap centre lands on the photo's outlet at (2921, 862)) runs 96 px under
the middle of the photo's can at u 2565. Against a yaw toward the left rear: TOP (calibrated) has the outer flank
converging inboard toward the front (-0.194 at x 0.05, -0.180 at x 0.175), and the RIGHT pair (f8_right_0) has both
of the can's edges on the photo's. lr34 is fitted to the model and least constrained for far-side parts. Not changed;
to settle it: fit lr34 with right-side landmarks (outlet, cap corners, nose seam) or read the inner flank in REAR and
TOP together. The inner face's weld beads and stamped text (HONDA, certification block): not started.

## Coordinator's items (round 3)
- Brake hose joint: this part's hose now starts exactly at the wheels hose's end, leaving it along that run's own last
  direction (0.718, -0.182, 0.672), both read off detail_wheels' built mesh (`_wheels_hose`), inside a 16 mm crimped
  sleeve centred on the joint; no stub forward past it. The banjo moved with the reservoir column (r_mc).
- Hose guide clip on the right arm's top (RIGHT 7x crop 1370..1450 x 1428..1480, r_clip; rr34 1595..1630 x 1370..
  1400): a black band 12 mm along the hose over a ribbed base 31 mm long (three ribs), cast with detail_wheels'
  `_cal_px` to x 0.281..0.312 (band 0.287..0.299). In the photos the hose rides on the clip's base about 9 mm over
  the arm; the wheels module lays it 1.2 mm over the arm, so the base is two cheeks either side of the hose with the
  band arching over (0.3 mm clear of the hose). Part `swingarm`. Check: cu4/render_cu_clip.png.


# Round 4 (2026-11-11, fourth chassis agent; scratch images under `agents/micro/chassis4/`)

## 1. Rear master cylinder body (part `brake_pedal`): one casting
Anatomy at 30 cm (fiche K95CF1500: body 2, cap 4, plate 6, diaphragm 7, screws 14, boot 3, push rod 8, nut 15, clevis
10, banjo bolt 12 and washers 13, mounting bolts 11): one grey sand-cast body of two upright columns joined by a web,
a deep narrow valley between them; the reservoir column (rear, oval 20 x 24.5 mm) with a wider head under the cap; a
dark smoky cap with two cross-recessed pan screws at diagonal corners over a thin plate; on the column's rear a round
pad with the sight window (a lit rim, the grey lens 1 to 1.5 mm in, a light retaining ring of three arcs), the cast
word LOWER beside it on the outer face; the bore column (front, 21 mm) with NISSIN cast along it (6 mm letters reading
down, tops forward), two lugs on its outer side under the frame's tabs (the bolts come from outside); above the valley
the neck (14 mm) carrying the banjo: washer, black eye, washer, 12 mm hex bolt; from the eye a bright 4.7 mm pipe rises
into the hose's black sleeve, the hose hooking over forward and down inboard; under the reservoir the web with a round
cast emblem (an N in a ring) and two dots on its rear face; the lower column, its bell skirt, a plain black boot (no
convolutions in any photo), the push rod, its lock nut on the clevis, the clevis as rectangular outlines from the side
AND from behind (a box of narrow bars: upper box, waist, lower box round the pin), the pin with its split pin outboard.
References: RIGHT 4x..8x crops mc1 (1580..1700 x 1270..1530), mc2, mc3 (1575..1665 x 1280..1440), mc5 (the hose's
hook), mc7 (rod and clevis), sa1 (the swingarm's front); rr34 mc4, mc9; REAR mc6 (2130..2210 x 1085..1265), mc8 (the
clevis from behind); rf34 (mc_views); fiche K95CF1500.
Numbers (all in MC_* with their pixels): x, z from RIGHT cast on the casting's mid plane y -0.1211; y from REAR cast on
each feature's own x (the rear photo reads 13 px, 10 mm, lower than RIGHT here, as at the footpegs: its rows unused).
Head 0.4335..0.4610 x -0.1341..-0.1067, z 0.567..0.579; cap to 0.5852; reservoir 20 x 24.5 mm, foot z 0.519; bore
column r 10.5 at x 0.4728; neck r 6.85 on the bore's 7 deg axis (boot centre u 1641 to neck u 1627); skirt 28 x 25.6
mm; window pad face x 0.4370, centre (y -0.1238, z 0.537), ring 17.3 mm; screws at (0.4374, -0.1250) and (0.4541,
-0.1124); boot 18.7 mm to z 0.465; clevis 14.4 mm, pin RIGHT (1648, 1505).
Where it is: the round-3 axis (y -0.1345, EST) put the body's centre on the tabs' face. REAR puts the boot at y -0.1211
(cols 2150..2175), the push rod at col 2160, the clevis's legs at -0.112 and -0.130, the casting -0.108..-0.134: a
body bolted inboard of the tabs (inner face 0.1325), its lugs 0.6 mm off them. Test: `test_master_cylinder_is_one_
casting_where_the_photos_have_it` (one watertight surface, RIGHT and REAR readings, nothing outboard of the tabs).
Built: `_mc_sdf` (smooth union of prisms and cylinders, fillets 1.2 to 3 mm, the lens recess cut) meshed by
`_surface_nets` (new: naive surface nets, Newton steps onto the surface; 1.2 mm grid, 11.8k vertices); `_uv_cast` (UVs
per face by its normal's axis, each direction in its own region of the map); `mc_map` -> textures/stock/mc_n.png
(sand-cast grain and the raised marks: NISSIN, LOWER, the emblem, the dots); `_pill` (cap and plate), `_pan_screw`
(cross recess cut through the head); materials rmc_cast, rmc_lid, rmc_lens, rmc_ring (renamed from mc_*: detail_front.py's front master cylinder uses mc_cast).
Shared change (this module's swingarm): REAR and rr34 put the clevis, rod and skirt where the swingarm's pivot casting
was (outer face 0.122 at x 0.48). rr34 mc9 shows the arm's box ending at its front weld and nothing of the arm outboard
ahead of it; RIGHT sa1 shows a darker face turning in right after the weld (u 1615..1635). `_arm_yo` now steps in to
0.107 between s 0.468 and 0.482 (x 0.452..0.465); side views unchanged.
Checks (three cycles): m1 pairs right, rear, rr34; cu1 close-ups (cu_mca beside rr34 mc4, cu_mcr from the right); m3
right; m4 right and rear (m4_both). Fixed on the way: a boxy single body (rr34: two round columns) -> bore column as a
cylinder and the web set back; grain relief 0.035 mm read as crinkle paint -> 0.016; LOWER ran off the column; the
pipe stood 1 cm too tall and its ferrule bright where the photo is black; the clevis a plain plate -> bar box; screws
3.2 mm tall; non-manifold cells under the upper lug (wider fillet).
Still different: the grain and lettering are a normal map (they do not change the silhouette, correct at 30 cm); the
studio render's step-in face of the swingarm is lit where the photo's is mid grey; the REAR model sits 13 px high (the
rear camera's known offset, not the part); detail_wheels' hose passes outboard of the web in RIGHT (v 1400..1414,
ending at u 1626) where their run ends inboard (y -0.100): theirs, reported.

## 2. Frame rear, depth (part `frame`): the boss's rim round the pivot, the leg's turned faces
Anatomy (RIGHT, LEFT, the Honda detail photo 475836 in directional light): the leg's outer face is crowned, not flat:
it turns away over its last 1 to 2 cm toward the C round the engine (dark there in the detail photo, a highlight line
at the edge in the studio photos) and less toward the rear edge; round the pivot a boss about 68 mm across whose fold
is a raised rim, a C cut open by the leg's front edge, the face inside it reading recessed; no channel along the
front rim (looked for: none in any profile).
References: RIGHT fr1 (1640..1900 x 1080..1600, 2x), fr2 and LEFT fl2 (equalised 3.2x, 1660..1830 / 2170..2340 x
1180..1480); intensity rows 1260..1460 and columns 1700, 1720 of both photos; detail 475836 (d836, d836_leg, rows 1300,
1500, 1700).
Numbers: boss fold at 34 mm from the pivot (RIGHT column 1700 lit at v 1415..1440, 40 mm; row 1420 lit at u 1700..
1710; LEFT row 1440 the boss face lit to u 2296, 36.6 mm, dropping there): BOSS_R 0.026 -> 0.034, the face 1.5 mm
proud, the rim 0.8 mm over it, 3.5 mm half width (BOSS_RIM). Turned faces (TURN): 2.5 mm at the front edge, 1 mm at
the rear, over 18 mm (the detail photo, the leg 208 px = 50 mm wide: 125 -> 181 over the first 10 mm from the front
edge, even 200 beyond); not on the spar above the U bead, the tabs, the footpeg pad or the pedal's seat.
Built: `_Cast.turn` (blended by the edge radius, front 7 mm to rear 4 mm), the rim in `_Cast.feat`, rows of vertices
at the rim (`extra`). Test: `test_frame_leg_turns_away_and_the_pivot_boss_has_its_rim`.
Checks: f1 pairs right 1640..1900 x 1150..1600 and left 2100..2360 (f1_both), f2 tighter pairs (f2_both), close-ups
cu2 (cu_fl beside d836_leg, cu_fr).
Engine hanger plates: not in this module's frame. They are detail_engine.py's head hangers (`_hanger`: "plate seated on
the inner face of the frame's plate") and the engine's plates at x 0.667..0.711, z 0.68..0.735, |y| 0.098..0.102 (part
`engine`), on the frame's inner face; the photos have them outside: theirs to move. Note for them: detail_engine copies
this module's boss radius (PIVOT_BOSS_R = 0.026): it is 0.034 now.
Still different: in the studio render the right side's turned front reads darker where the photo has a highlight
line along the edge (the left side matches): the render's light, not the shape (the same face on the left is lit);
the leg's section in between is EST (no photo shows it end on).

## 3. Subframe (part `subframe`): investigated, not built (partly)
What the photos show of it (every other stretch is under the seat, the side panels or the rear fender: REAR shows only
the inner fender, TOP the seat): the lower rails' front mounts. fiche K95CF3900 part 7: two upper box rails from cast
front lugs (bolts 15) to the tail, the lower rails from the tail down and forward to the lower mounts (bolts 21), a
cross brace and a bracket (8, bolt 14) near the front of the right upper rail.
- LEFT (sf_left, s0_left 2240..2440 x 1120..1300): a cast lug with a ribbed end comes out from under the airbox panel
  (u 2355, v 1200: x 0.484, z 0.656 on y 0.141) down to ONE flange bolt on the leg's rear edge at (2305, 1250): x
  0.521, z 0.618, 4.3 mm behind the model's outline; a second bolt above it (2290, 1185: x 0.534, z 0.667) is the
  frame's own. The model's hidden bracket foot is at the same x, z (0.521, 0.603) but inboard (y 0.1105).
- RIGHT (sf_right, s0_right 1600..1800 x 1080..1260, rr34 sf_rr34): a lug from under the panel (1670, 1110: x 0.507,
  z 0.726) down to a plate with TWO flange bolts at (1690, 1165) and (1740, 1165): z 0.684, x 0.521 and 0.559. The
  front bolt lies on the model's frame outline, the rear one 31 mm behind it: the model's frame is short there (the
  photo's casting reaches back under the plate).
- Not built: from the plates outside the frame (|y| 0.14) to the rails (0.08 to 0.09) the lugs pass under the side
  panel, whose skins in the model fill |y| 0.082..0.107 down to z 0.63 there (the plastics agent's part, being
  reworked now); and the right plate needs the frame's outline extended 31 mm. Both need the coordinator: the frame's
  outline (this module) and the panel's inner skin (plastics) together. The rails, welds and the seat and airbox mounts
  are hidden in every photo (EST as before).

## 4. Shock, the rest (part `shock`)
Anatomy added: the spring's closed AND ground ends (flat bearing faces tapering over about half a turn), seated on
the preload ring's face and the lower seat; the rebound scale stamped in the clevis's right ear just under the
bottom cup (Dirt Rider 09, crop 560..1000 x 280..560: "S", a curved double-headed arrow, an index line).
Numbers: S 7 mm tall (25 px against the ear's 110 px = 33 mm), arrow 8.4 mm wide, line 6.5 mm; grooves 0.7 mm. The
spring's wire centres on the seats' faces (s 0.137 and 0.371 from the top eye), ground flat there (it stood 6 mm
past each seat's plane before, its round wire on the ring's corner).
Checks: cu3 close-ups (cu_dr9 and cu_dr9b at about Dirt Rider 09's angle, cu_smark2 on the ear beside the photo's crop:
cu3_s). The first marks were metallic "groove" 0.3 mm proud and read light: now black (`bore`) 0.1 mm proud.
Test: `test_shock_spring_ends_are_ground_on_their_seats_and_the_clevis_is_stamped`.
Still different: in Dirt Rider 09 the ear's face is a straight-sided block about 25 mm wide (the model's ears are a
rounded hull 33 mm wide); the bike there sits at another point of its travel, so the connecting rods pass 25 mm lower
across the clevis than in the studio pose (where they hide the marks); the spring's colour stays EST (dark).

## 5. Pro-Link, the rest (part `linkage`): the cushion arm's pocketed faces
Anatomy (Dirt Rider 09): the cast cushion arm's faces are recessed inside a lit rim that runs round its edges and
round each boss, the floor smooth and darker, the lightening hole with its own rim; the nuts with bright washer faces,
the bolts' ends with a dark centre mark.
Built: `_arm_sdf` (the hull of the three bosses, 24 mm, edges rounded 2.5 mm, the hole, both faces pocketed 2 mm deep
inside a 4.5 mm rim, 2.5 mm round the bosses) meshed by `_surface_nets` at 1.5 mm (9.6k vertices); the round-2 reason
for leaving it plain (a raised rim clashed with the clevis's ears) is gone: the pocket is cut in, the faces stay at
|y| 0.012 inside the ears (0.01255). First cycle: the rim's crease rounded 1.2 mm on a 1.5 mm grid came out serrated
(cu3_b); now 1.8 / 2.0 mm (cu3_c).
Numbers: pocket 1.75k mm2 a face (the arm 6.0k), EST depth (the rim's shadow is about a third of its width in the
photo). Test: `test_cushion_arm_faces_are_pocketed_inside_their_rims`.
Checks: cu3 close-ups cu_dr9, cu_dr9b (side on), cu3_c.
Still different / not done: the casting marks (ejector-pin rings about 3 mm, below the 1.5 mm grid) and the bolts'
end marks are not modelled; the bolt heads and nuts stand as in round 2 (flange heads left, washer, nut and two
threads right, as Dirt Rider 09).

## 6. Footpegs, the rest (part `footpegs`)
Anatomy (detail 475839 crop d839_peg: the left peg from the front; RIGHT and LEFT see the pegs end on, p1 pairs): a
black cast cage: a toothed top rail round the outline (about ten sharp teeth along the front rail with flat valleys,
a tall tooth on each tip corner, the tip end square with small corners); under each side rail a diagonal strut from
the tip down to the hinge's foot with an open triangle between (the old side rails were solid bands 21 mm deep at the
root); end on the cage narrows downward to the hinge; the hinge: ears, pin with head and washer, split pin, return
spring (as before).
Position (the brief: "lower and further back in f8_right_2"): measured on the tip's own plane (y 0.248), the photos'
teeth stand HIGHER than the model's, not lower: RIGHT corner teeth v 1520 (z 0.431), the others about 1527 (0.424);
LEFT rows 1522..1530 (0.421..0.427); the model's tip was at 0.420 (from REAR 0.416, which reads 10 mm low here, see
component 1). Fore and aft: RIGHT u 1708..1778 (x 0.535..0.587), LEFT 0.531..0.583: the model's 0.529..0.583 stays.
In f8_right_2 the photo's black mass reaches lower because of the hinge bracket and the cage's V of braces under the
rail, which the model lacked. PEG_TIP z 0.420 -> 0.424 (root unchanged: SPEC 422 mm on the ground).
Numbers: teeth every 9 mm (PEG_TEETH), 4 mm tall, the corner teeth 5 mm over the rest; rail 8 mm deep, 24 mm at the
hinge end (PEG_RAIL); struts 4.5 x 5.5 mm.
Checks: p1 pairs (before), cu4 close-up cu_peg beside d839_peg (cu4_peg), p2 right pair. Test:
`test_footpeg_tips_are_where_the_rear_photo_has_them` now checks REAR at row 1294 - 13 (the rear camera's offset) and
the corner teeth on RIGHT v 1520 and LEFT v 1522.
Still different: the photo's hinge bracket is a large black casting with the pin's round head on top (d839_peg); the
model's hinge is two plain ears; the photo's teeth are sharper spikes.

## 7. Muffler, the rest (part `exhaust`), and the coordinator's height check
The can's height (coordinator: the plastics agent saw the can low in RIGHT and lr34). Measured in RIGHT column by
column (metal run between the red panel or the background and the background below), cast on y -0.13:
- bottom edge: photo against model, u 1040..1400 every 40 px: 1058/1057, 1078/1076, 1097/1095, 1116/1114, 1135/1133,
  1155/1152, 1174/1170, 1211/1208, 1230/1226: within 1 to 4 px, unchanged.
- top edge against the background: u 1000 z 0.8949 (model 0.8950), u 1050 0.8914 (0.8711), u 1105 0.8841 (0.8433);
  under the side panel's lower edge (lower bounds: the top is hidden above them) u 1120..1280, x 0.094..0.213: 0.8696,
  0.8595, 0.8395, 0.8225, 0.8055 against the model's 0.8359, 0.8157, 0.7957, 0.7756, 0.7555.
So it was really low: the round-2 taper (18 mm per 100 mm, there to clear the panel) put the top 20 mm low at x
0.042, 41 mm at 0.083 and at least 34 to 50 mm under the panel. In the photo the top runs back from the cap at 8 deg
while the bottom falls at 26: the height grows from 108 mm at the cap to 136 mm at x 0.083 (REAR's section is 136 mm
tall, 0.765..0.901: the can's deepest part), then the top runs parallel to the bottom (MUF_GROW). Past x 0.215 the
top is behind the panel's black lower part in every photo: it bends down to stay 3 mm under the panel's underside
(_MUF_TOPMAX, from the plastics' mesh in main; a straight 136 mm top stood 6 to 27 mm into it from x 0.25). Checks:
p2_can before, q2_can after (q2_all): the gap under the panel at the rear is gone. A vertex check of the side panels,
subframe, fender, flap, mudguard and panel bolts against the can's section: none inside.
The dark band across the cap's knee from behind (p2_rear, cu4 cu_mufb): it is in the studio render, not in the close-up
(cu_mufb, even): the knee (RIGHT's profile, round 3) turns the face from the backdrop to the floor and passes the
render studio's darker horizon; Honda's cyclorama has none. Geometry kept; not fixed (a render-light difference).
Inner face (lr34 lr_can 2380..3020 x 700..1000, 1.5x): a stamped label (a block of about eight lines of small text,
HONDA under it) between the bracket's weld and the cap's seam, a TIG seam weld along the face's lower part, the mount
bracket a pressed plate with its bolt at the top and a rippled weld along its foot.
Built: `_can_label` gives the inner flank's faces over x 0.070..0.215 the material muffler_txt and UVs on its map
(muf_txt_n.png, `muf_txt_map`: the brushing and the label stamped 0.15 mm deep along the can's slope; the small text
is unreadable in every photo, so it is drawn as word-length strokes, no invented words), and a seam weld bead (5 mm,
ripples 2.2 mm) along the octagon's inner lower corner from x 0.06 to 0.30. Check: cu4 cu_mufi beside lr_can (q2_all).
lr34 caveat: it is fitted to the model and least sure for the far side (round 3): positions there were taken relative
to the can's own lines.
Still different: the mount is still the round-2 pair of straps (the photo's is one pressed plate with a foot weld,
hidden in RIGHT; not rebuilt); the photo's label covers more of the face; its seam weld is bigger and sits a little
higher on the face.

## Round 4 audit and totals
Audit (audit.py, 25 mm; main merged: plastics rounds 1 to 3, cockpit rounds 2 to 3) on the first full build: frame x
linkage reported 27.5 mm over long faces of the lower cross member (r 13, 27.8 mm behind F) against the link's frame
boss (r 15): the boss now 14.5; brake_pedal x frame 1.6 mm: the pedal's lever, swung inboard to the rod's new line
(y -0.121), passed 2 mm inside the plate's face near its rear edge: it now stays outside the face (0.137) over the
plate and swings in behind its edge. Final audit (audit5): chassis lines footpegs x frame 1.0 (the hinge pin's washer
seated on the pad), exhaust x frame 0.9, frame x shock 0.4, brake_pedal x frame 0.2 (the pedal's boss on the pad),
engine x frame 0.5 (detail_engine's shift clamp); no floating pieces. Module 228,641 vertices (budget 260,000). The materials mc_* were renamed rmc_*: the cockpit's
front master cylinder (detail_front.py) defines mc_cast with other values (parts.build would raise).


# Round 5 (2026-11-12, fifth chassis agent; scratch images under `agents/micro/chassis5/`)
Damien: "Find more inconsistencies, especially with the shape of everything, and fix them. Like the exhaust." His
photos: `damien-bike-2026-11-10/` 01..05 and `damien-bike-2026-11-12/` 06..10.

## 0. Exhaust, against his photos and Honda's (part `exhaust`)
Anatomy at 30 cm (fiche K95CF2700; RIGHT, detail 475834, Dirt Rider 02, rf34, rr34, lr34, LEFT, FRONT; Damien 08, 02,
07): the header (5) from the port down in front of the engine, a U whose far leg rises inboard to the port and whose
near leg climbs back to a TIG ring, the long run over the clutch cover, a second ring where a 12 mm cone opens it into
a socket; a band clamp (14, bolt 17, nut 21) over the socket's slotted end: a pressed band with rolled rims, a hinge
knuckle with its pin on top, two ears under it and an M8 flange bolt across them, head outboard; the muffler's inlet
pipe (3/11) slides in, with a soft bell just behind the band, turns in behind the frame's leg, rises behind the side
panel and is welded into the can's nose. No spring hooks on this bike (RIGHT, 475834 and Damien's 08 all show the
band). The can: flat facets, a long rippled seam weld mid-height on its inner face, a stamped label block above the
weld and the maker's line under it, the cap riveted (three blind rivets on each side of its seam), a pressed mount
plate welded along the top of the inner face and bolted across the bike into the subframe's lower rail.
Finish (Damien): the whole header heat-browned, dark rust at the head and round the U, copper and bronze along the
run, lighter bronze on the socket and band, dark rust on the inlet pipe (08, 02, 07). Honda's showroom bike is silver.
References: RIGHT 1380..2340 x 1100..1500 (route crops g_right1..4, r0z, r1z, r2: the tube's projected edges drawn
over the photo by tools/route.py), FRONT 1720..2000 x 1040..1300, TOP 1880..2160 x 900..1060, rr34, rf34 (e0 sheets),
lr34 2380..3020 x 700..1060 (lr_can), LEFT 2400..3000 x 820..1260, detail 475834 crop 1850..2500 x 1250..1700
(d834_joint), Damien 08 crops d08_header, d08_joint, d08_u, 07 d07_can, d07_header.
Differences found (model before, e0 sheets) and what was done:
1. Front U: far leg 9 to 15 mm too far forward (RIGHT far leg front edge u 2283..2290 at v 1300..1390, model 2305),
   bottom 15 mm too far back (RIGHT lowest edge v 1466 at u 2265..2280, front corner (2302, 1440)): points 4..10 moved
   (the near leg and its outer edge in FRONT, u 1786..1800 from v 1160 to 1240, were right and stay). Test.
2. Long run 3 to 6 mm low where it turns down (RIGHT u 2100: centre v 1279 against 1283; u 2150: 1301 against 1309):
   raised; at u 2000 its edges match the photo's (1236..1284, 38 mm). Test.
3. Joint: one thin EST clamp ring. Now the socket (RIGHT u 1870..1890: edges v 1208..1272 against black, 47 to 48.6
   mm: R_SOCK 23.5 mm) after a 12 mm cone from the ring (WELDS[1], px (1916, 1242) cast on y -0.124: z 0.6222), the
   band at RIGHT px (1846, 1240) (x 0.637, z 0.623 on y -0.112), its bolt at px (1846, 1290), knuckle px (1852, 1196);
   the inlet pipe's bell (RIGHT u 1815..1830, 475834). Test.
4. Inlet pipe 15 to 35 mm low: it showed under the side panel's lower edge and through the frame's window, where no
   photo has any of it (RIGHT rowscan cols 1510..1640: nothing below v 1218..1249; rr34, rf34 the same). New line from
   the nose's end ring (RIGHT col 1490: lit lower part to v 1226, z 0.635: MUF_INLET z 0.6441 -> 0.6565) rising under
   the panel, then dipping behind the frame's leg under the subframe's lower rail (EST). Test (every column).
5. Colour: Honda silver -> Damien's heat colours: `heat_maps()` writes textures/stock/header_heat.png (colour along
   the pipe, u = arc length / 1.32 m, blotches, heat bands) and header_heat_n.png (scale); header_heat, header_weld,
   header_clamp materials. Photo 08 samples: run lit (150..153, 122..125, 94..98), shade (118, 87, 62); U (64, 48, 36)
   shade, (110, 72, 44) lit; inlet pipe (92, 61, 35); band (172, 150, 114).
6. Welds: smooth turned rings -> rippled TIG beads 7.5 mm wide (the first try, 5.5 mm and matte, read as O-rings).
7. Can, inner face (LEFT, lr34): the seam weld sat on the inner lower corner; lr34 runs it 56 to 60 mm over the lower
   line, parallel to it (cast (0.324, 0.685) to (0.051, 0.825) on y -0.08), LEFT 67 px: MUF_SEAM 0.058, 8.5 mm wide.
   The label block moved above the weld (x 0.078..0.146, 66..100 mm over the lower line), HONDA (5 mm) and a second
   word as strokes under the weld. Three inner cap rivets added (LEFT px (2850, 928), (2877, 982), (2895, 1027): on the
   outer rivets' plane within 2 mm). Test.
8. Mount: round 2's EST straps and a tab under the rail -> a pressed plate on the inner face's top, its foot weld,
   bolt across the bike at lr34 px (2602, 858) (x 0.2365, z 0.835 on y -0.08), rubber grommet, collar, M8 flange
   bolt head inboard; the subframe's lower rail moved 3 to 9 mm out between x 0.22 and 0.30 (EST, hidden) so the plate
   bolts to its inner face. Test.
Checks: e0 -> e2 pair sheets (right, left, rr34, lr34, rf34), close-ups cu1 (cu_hj, cu_hu, cu_h08), cu2 (cu_hj,
cu_mnt, cu_capi); audit3 (exhaust x subframe 2.2 mm: the plate's rear corner under the rail's tail and the pipe at the
rail's end, both fixed after: 1.5 mm clear by vertex distance).
Still different: the can's position in lr34 (fitted to the model) and LEFT is 10 to 18 px off (far-side camera
offsets, round 3); the photo's mount plate reaches back to x 0.149 (lr34) but the plastics' red wall under the tail
(tail_under, x 0.185..0.204) stands in its plane, so it starts at x 0.206 (shared); in lr34 the model's side panel
hangs lower and hides the plate (plastics); the header diameter is 38 mm by the run's edges and the U's ring, but the
dim upper edge at u 1940 allows up to 44 mm (no clean silhouette against white); the seam weld's ripples are regular.
