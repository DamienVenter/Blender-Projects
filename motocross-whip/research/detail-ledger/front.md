# Detail ledger: handlebar, grips, hand controls, fork ends, front wheel (`scripts/bike/detail_front.py`)

Micro-detail pass of 2026-11-11 (brief FRONT.md: thirteen separate builds, each with references, numbers, model and
check). Coordinates: axle-line frame, metres. The hand controls are written in a grip frame per side (`_Side.p(a, f,
u)`: a inboard of the grip's end face, f ahead, u up). Check images are in the agent's scratch folder
(`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/front/`,
written `SCRATCH/` below); they are not committed.

Tools written for the checks (scratch `tools/`): `gripscan.py` (grip silhouettes in the top photo cast on the bar's
plane), `gripfront.py` / `griprear.py` (edge heights per a in the end photos), `axprof.py` (photo intensity along a
line on the grip, minima = grooves), `riblines.py` (candidate rib angles drawn on a calibrated photo), `ruler.py` (a
ruler of a along each grip drawn on any calibrated photo), `cu.py` + `render_cu.sh` (close-ups aimed in the grip
frame), `mk.py` / `only.py` (swap this module's parts into a parts file; a light parts file for close-ups),
`pairs.sh`, `sbs.py`, `audit_front.sh` (the audit on the front end's parts and their neighbours, 40 s).

## 1. Grips (Honda stock, left 53165 and throttle 53140 groups)

### Anatomy (what shows at 30 cm)
- Closed end: a flat end face recessed about 0.6 mm inside a raised rim, the rim rolled over into a lip a little
  larger than the body (33.5 against 30 mm), a short smooth collar behind the lip.
- Body: true pyramids in a diamond lattice (diagonals along and round the grip), 36 round, 2.5 mm a diagonal; the
  body tapers from 30.0 mm at the end to 28.2 mm at the flange.
- Two full rings: on the palm side (top and rear) a groove 2.4 mm wide with a round bead in it that shines as a thin
  line (DR05, DR06); across the smooth underside band the ring rises into a rib that hangs below the grip's lower
  edge (DET829, DET830).
- Finger-side waffle: two ribs along the front face (+20 and -24 deg) with diamond panels between them, one rib low
  on the rear (about 205 deg), a smooth band under the grip between the lower ribs, and two partial ribs across the
  whole lower arc between the rings. The long ribs stop at the last partial rib.
- Inboard end: a wide concave fillet from the body into a 58 mm flange 3 mm thick with a rounded rim, a mould
  parting line across its outboard face (front and rear), a collar behind the flange (DR05 shows "688" moulded on
  it; the lettering is not modelled) that the switch housing wraps. The right grip ends on the throttle tube.
- Finish: satin black rubber (no texture finer than the pyramids shows in any photo); the beads smoother.

### References
- DET829 (left bar, 475829): grip crop 880..2120 x 1350..1950; zooms 1150..1750 x 1540..1900 (rings, underside
  ribs hanging below the edge), 900..1250 x 1580..1940 (end cap), 1580..1960 x 1520..1900 (fillet, flange).
- DET830 (right bar, 475830): grip 1950..3300 x 1000..1550; underside equalised 2250..3150 x 1250..1520 (rear long
  rib, partial ribs below it).
- DR05 (clutch perch): grip 740..1310 x 160..450 (front waffle, long rib, partial ribs, flange, "688" collar).
- DR06 (switches): grip 0..560 x 440..900 at 2x (pyramids, the ring as a groove with a shining bead, flange seam).
- TOP studio photo: 1730..1860 x 1440..1620 (left), 630..810 (right); ruler crops `ref/rul_top_L.jpg`, `_R.jpg`.
- FRONT studio photo: 2380..2560 x 215..290 (left), 1440..1620 (right) at 8x; REAR the same; lf34 1990..2240 x
  290..440; rr34, rf34 (rib candidates).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| End face to flange | flange disc a 119..122 mm, collar to 125.6 | TOPv widest at a 118..121 both grips; FRONTv dark run a 114..129 (flange seen edge-on) |
| Diameter over the tips | 30.0 mm at a 8, 28.2 at a 110 | FRONTv top edge falls 4.5 mm, REARv bottom 1.7 mm over that run: 2.8 mm taper, the rest is the bar's upsweep; TOPv widths 28.6 -> 27.0 and 29.6 -> 28.6 (threshold reads about 0.4 mm narrow) |
| Pyramids | 36 round, 2.47 mm diagonal along (built 2.5), 0.55 mm high | DET829 2D FFT of zone 2: both lattice families repeat every 20.4 px along the axis where 46 mm spans 380 px; round: 2.47 mm on a 29 mm grip = 36.9; height EST (DR06) |
| Ring centres | a 27.9 and 73.8 mm | mean of TOPv silhouette notches (28.5, 74.5 / 29.5, 75), TOPv dark lines on the top (27.3, 73.0 / 26.3, 72.0), FRONTv / REARv lines (25.8..31.8, 70.3..78.8) |
| Ring groove | 2.4 wide, floor 1.6 below the tips, bead r 0.5 with its top 1.0 below the tips | DR06 (bead 1.3 mm with a wall either side), TOPv dips 1.5..2.5 mm; EST |
| Partial ribs | a 51.0 and 97.5 mm | FRONTv dark lines 51.0 and 97.3 (right), DR05 48.9 / 98, DET829 about 53 / 104, TOPv front-edge step at 97 / 98 |
| Long ribs | +20, -24 (built -24 as 336) and 205 deg | FRONTv two lines 33 % and 71 % down the front face; lf34 about +28; DET830 71 % down from behind (about 200); DET829 from behind and below (about 236) |
| Smooth band | 205..336 deg, 0.75 mm under the tips | DET829 (no diamonds below the low line), FRONTv (smooth and dark below -24 deg) |
| Ribs | 1.3 mm at the root, 1.0 at the top, top 0.3 mm over the tips (1.05 over the band) | DET829 / DET830 ribs 0.5..0.9 mm below the lower edge |
| End lip | 33.5 mm, 2.8 mm long, rim face flat from r 13.5 to 15.25 | FRONTv 34.9 at a 4, REARv 34.2, TOPv 32.5..34.0 |
| Flange | 58 mm, 3 mm thick, fillet from the body over a 112..119 | lf34 pair: flange 82 px over a body of 40 (model at 28 mm: 76 px); TOPv 57.7 (narrow threshold); DET829, DR05 twice the body |
| Collar | 31.2 mm, a 122..125.6 | EST: the switch housing starts at a 122..126 (TOPv) and wraps it |
| Throttle tube under the right grip | 26 mm | EST (1.2 mm grip wall) |

### What was built
- `grips()` (new part, turns with the steering): `grip(s, right)` builds one closed rubber body from the end face to
  the bar as rings of 72 points (`_rows()`): the end face, rim and lip, the collar, three diamond fields whose rows
  sit on each field's own pitch (tips and valleys alternate; every quad is split along its valley diagonal, so the
  pyramids are exact), the two ring grooves with their beads, the fillet, flange and collar. The smooth band is the
  same rows held at one radius. On top: the long ribs (rounded section, root inside the body), the cross ribs over
  their arcs, the flange's parting lines. 11,519 vertices a grip.
- Materials `grip_rubber` (satin, rough 0.55, a faint fine bump) and `grip_bead` (rough 0.22) for the beads.
- `R_GRIP` 15.8 mm: the lip's rounded rim is where the grip reaches furthest out; overall width 826.9 mm (SPEC 827).
- The hand controls moved inboard with the longer grips (`CTRL_SHIFT` 17 mm left, 19 mm right, on all their
  points; the levers' ball ends stay): the switch housing now starts at a 126, the throttle housing at a 126. Each is
  placed again from the photos in its own component. The clutch cable's first waypoint now lies on the adjuster's
  axis (it had kinked back into its boot: bars / cables clash of 3.8 mm in the audit, now gone).
- Tests: `test_grip_diamonds_36_round_2_5_mm_along`, `test_grip_diameters_flange_and_rings`,
  `test_grips_close_onto_the_bar_and_the_throttle_tube`, the width and bar-end tests moved to the grips.

### Checks
- Pairs (32 samples): `chk/p2_lf34.jpg`, `p2_top.jpg`, `p2_front.jpg` (first build), `p3_front.jpg`, `p3_lf34.jpg`
  (rings, partials, long ribs and the hanging loops line up with the photo).
- Close-ups beside the detail photos: `chk/g1_*.jpg` (first), `g2_*.jpg`, `g3_a.jpg`, `g3_b.jpg`, `g4_a.jpg`
  (DR05, DR06), `g4_b.jpg` (DET829, DET830).
- Fixed after cycle 1: ring and partial positions (top-view reading alone was 1.5 mm out), flange 56 -> 58 mm, rib
  layout (the front long rib sits at mid-height, not under the grip). After cycle 2: the second rear rib removed
  (none in DR06 / DET829), the beads given their own smoother material.
- Audit (front parts and neighbours): no clash or loose piece on the grips.

### Still different
- TOPv shows a small notch on the front edge at a 97 where the model's partial rib stands 0.3 mm proud; at a 51 the
  photo shows none. At 0.78 mm a pixel the two cannot be told apart further; the photos agree that it is a rib under
  the grip.
- The beads shine in DR05 / DR06 (sunlight); under the studio lights of the renders they read as dark lines, as the
  rings do in Honda's studio photos.
- The rear long rib's angle rests on two uncalibrated photos (200 and 236 deg): 205 is EST between them.
- The top photo's bars are turned about 2.6 deg (left grip 13.3 deg of sweep in plan, right 18.6): the model's grip
  sits 5 mm further back at its end there; the side and end photos agree with the model.
- The "688" mould number on the collar is not modelled (hidden by the switch housing in every studio view).
