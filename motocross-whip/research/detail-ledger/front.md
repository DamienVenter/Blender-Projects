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

## 2. Handlebar (Renthal Fatbar, Honda 53100-MKE-A70)

### Anatomy
- One tube, no crossbar: 28.6 mm through the clamps and the bend, a short taper, 22.2 mm at the controls.
- Bend: straight across the clamps, a plan bend at y 0.15 sweeping the ends back 16 deg, a rise from y 0.075 that
  runs straight into the end section, the end section rising outwards (upsweep) to the bar ends.
- Knurled clamping zones on the 28.6 mm section (under the holders, inside the pad: no photo shows them).
- Open ends with a thin wall and a pressed-in plastic plug (inside the closed grips: no photo shows them).
- Finish: satin black (its upper half reflects the studio's white in FRONT and REAR); printed FATBAR logos are left
  to the graphics pass.

### References
- FRONT 2050..2420 x 205..330, REAR 1580..1950 x 195..320 (left half: rise, bend, taper); TOP ruler crops
  (`ref/rul_top_L.jpg`, `_R.jpg`); DR05 (taper at the cable tie, FATBAR logo on the thick part); d835.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Diameters | 28.6 / 22.2 mm | SPEC (Fatbar, 1-1/8 in clamp area) |
| Taper | between abs(y) 0.150 and 0.185 | TOP crops: thick out to the cable tie (a 250..255 left, 280 right), thin at the perch; DR05 |
| Upsweep | 1.85 deg, the end section straight from y 0.185 to the bar end | component 1: grip axis 3.1 mm over 96 mm (FRONT and REAR edges); the earlier pass's FRONT rise points (1.199 at y 0.186) lie on that line |
| Rise | Hermite from level at y 0.075 to the end line at 0.185 | FRONT centre z 1.189 at y 0.153 (model 1.1917) and 1.199 at 0.186 (model 1.1994) |
| Knurl zone | abs(y) 0.020..0.074, 1.0 mm diamond pitch | EST (Renthal knurls where the holders may sit: four positions over 26 mm, SPEC) |
| Ends | wall 1.6 mm, plug 1 mm inside, 4.5 mm deep | EST (hidden) |

### What was built
- `bar_path()`: plan curve unchanged (earlier TOP measurements); the height now rises from the clamps straight
  into the grips' 1.85 deg axis, which `_Side` carries too (`UPSWEEP`, its `u` vector square to the grip), so grips,
  bar end and controls share one axis.
- `_bar()`: the tube resampled 2 mm in the knurl zones and the taper (rows on the zone edges), `bar_r()` (smooth
  taper), `bar_knurl` material with a knurl normal map (`textures/stock/bar_knurl_n.png`, made by
  `python3 detail_front.py` from `knurl_map()`: four-facet pyramids at 30 deg, 8 pitches a tile) on UVs in knurl
  pitches; the open ends and plugs.
- Tests: `test_fatbar_diameters_taper_and_knurl`, `test_bar_end_runs_along_the_grip_axis`; the 827 mm and 1262 mm
  SPEC tests still pass.

### Checks
- `chk/p5_front.jpg` (first): the upsweep run across the whole bar put the rise 6 mm low (FRONT stack
  `p5_front_st.jpg`); fixed by joining the rise to the end line at y 0.185.
- `chk/p6_front_st.jpg`, `p6_rear_st.jpg` (photo above model, same grid): top edge of the bar and the turn-down to
  the clamps agree within 2 px in both views; the grip in REAR is 1 to 3 px fuller at the bottom (ribs).
- Render log: no UV warnings (the knurl UVs reach Blender). Audit: no clash on the bar.

### Still different
- The bar's lower edge cannot be read in FRONT (levers, adjuster and boot in front of it) and its upper half merges
  with the white background in both end photos: the diameters rest on SPEC, not on the photos.
- Knurl and plugs are hidden in every photo (EST extents).

## 3. Bar holders (upper 53131-K95-AG0, lower 53132-K95-AG0)

### Anatomy
- Per side (fiche K95CF0700): rubber bush (5) in the top bridge, washer (14), the lower holder (4): a machined round
  base with a turned ring, turning into a saddle under the bar; the upper holder cap (3) over the bar with two
  vertical M8 flange bolts (10) ahead of and behind the bar; under the bridge a second bush (5), washer (15) and the
  flange nut (13) on the holder's stud with a few threads showing.
- Finish: base machined bright, saddle and cap cast satin, bolts zinc, bush black rubber.

### References
- Fiche `K95CF0700_handle-pipe-top-bridge.png` (parts and counts).
- DET835 crop 1250..2550 x 700..1500 (`ref/d835_clamp.jpg`): the bases (bright machined cylinders with a ring and the
  bush at the foot) between the top clamp and the pad, a nut under the clamp's front.
- No studio photo shows any of it (the pad covers the holders in TOP, the clamp and plate hide the bases elsewhere).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Holder axes | y +-0.050 | DET835: each base midway between the fork tube's axis and the stem (pixel ratio 0.49) |
| Base | 29.6 mm, 18.5 mm tall, ring 7 mm up | DET835: 0.58 of the fork cap's width (140 px / 240 px of about 50 mm) |
| Saddle and cap | 44 mm fore-aft, 26 mm along the bar, cap 18 mm over the bar | EST (fits inside the pad, test) |
| Bolts | M8 flange, 12 mm hex, 41 mm apart | JIS head size for M8; EST spacing |
| Stud nut | M8 flange nut, 12 mm, washer 24 mm, 4 mm of thread showing | fiche (13, 15); EST sizes |

### What was built
- `_holder(yh)`: bush, washer, base (revolved, with its ring), saddle lofted from the base's circle to the rounded
  block, cap with rounded top edges, two `fastener()` flange bolts. `clamps()`: bush, washer, nut and thread under
  the bridge.
- `fastener()`: shared helper for this module (JIS hex flange with chamfered corners, plain hex, socket cap with a hex
  recess, button head, washer, exposed V thread).

### Checks
- Close-ups at DET835's angle: `chk/h7.jpg`, `h7b.jpg`, `h7c.jpg` (camera search; cables and plate in front),
  `h7d.jpg` (bars, clamps and fork only). The bases sit under the pad's middle and are hidden from 22 deg above.
- Audit: bush seated 0.5 mm in its counterbore on the top clamp (bars / clamps, depth 0.0 mm); nothing else.
- `test_bar_pad_hides_the_holders_and_their_bolts` passes with the larger holders.

### Still different
- DET835 shows about 15 mm of each base below the pad, the model hides it: the photo's pad stands higher over a
  bulkier top clamp whose top face lies well under the fork caps (the model's clamp is a thin plate with box pinch
  lugs). The clamp's shape is part of component 9 (fork tops); the holder heights follow the model's clamp.

## 4. Throttle housing (fiche K95CF0400: pipe 7, housings 11 / 12, screws 21, cables 1)

### Anatomy
- Round black body over the throttle pipe's flange right inboard of the grip's flange, a narrower collar clamping
  the bar, the parting seam of the two halves, two black M5 socket screws on the rear face (top and bottom).
- Cable hood: one thick black tube rising beside the grip's flange in a wide arc and running inboard along the top
  of the bar; a smooth tapered rubber boot over its end with a ring at the hood end, a short spout for each cable.
- The two cables leave the boot level along the top-rear of the bar; the pull cable carries a bright crimped ferrule,
  a lock nut and a black ribbed in-line adjuster; the cables part slightly round it.
- The throttle pipe shows as a thin dark ring between the grip's mouth and the housing.

### References
- DET830 (475830) crop 0..2600 x 700..1950 (`ref/d830_controls.jpg`): hood, boot, screws, ferrule and adjuster.
- rf34 1900..2120 x 280..420 and ruler crop `ref/rul_rf34_R.jpg`; REAR 2230..2420 x 170..300 (hood arc, screws,
  body height); TOP `ref/rul_top_R.jpg` (positions along the bar; the cables behind the bar, down behind the pad).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Body | a 126.3..149, radius 25 mm; collar to 156.5, radius 17.5 | TOP (black from a 122 after the flange to 156); REAR pair 360 px tall where the grip's 29 mm is 210 px |
| Hood | centre line from a 135.5 (beside the flange) up to 38 mm over the axis, radius 8.5 mm | REAR pair; hood top cast on its own x plane: z 1.2488 (model 1.2499) |
| Boot | a 163..204, 21 mm at the ring, 16 mm at the mouth | REAR pair x 220..540, DET830 |
| Screws | M5 socket, 8 mm heads, f -17.5, u +-13.5 at a 140 | DET830, REAR pair (positions within 3 px) |
| Adjuster | ferrule 32..44 mm out of the boot, nut, ribbed body 48..82 mm, 11.6 mm across the ribs | DET830 (ferrule 60 px, adjuster 180 px against the 41 mm boot's 200 px) |

### What was built
- `throttle_housing()` (in the bars part): pipe ring, revolved body and collar, seam strips, screw bosses and two
  `fastener()` socket screws (new material `bolt_black`), the hood swept along `HOOD`, its collar, the boot with its
  ring and two spouts. `throttle_paths()` now start at the spouts, run level along the top-rear of the bar, down
  behind the pad's right end close behind the top clamp and ahead of the tank, then the earlier route to the drum;
  `cables()` adds the ferrule, nut and ribbed adjuster on the pull cable.
- Test: `test_throttle_hood_top_is_the_rear_photo_s`; the SPEC 1262 mm height test now measures the bar and grips
  (the hood stands 12 mm above it in Honda's photos).

### Checks
- Pairs: `chk/p8_rf34_st.jpg`, `p8_rear_st.jpg` (hood too small and too central, boot ribbed: fixed),
  `p9_rear_st.jpg` (hood arc and screws within 2 to 3 px), `p9_rf34_st.jpg`.
- Close-ups beside DET830: `chk/t10.jpg`, `t11.jpg` (spouts and adjuster added after t10).
- Audit: the hood first reached into the grip's collar (5.8 mm), the cables kinked into the boot (2 mm) and hit the
  tank behind the pad (3.1 mm): all fixed; no clash on these parts now.

### Still different
- DET830's boot is a little fatter than the hood and its cable necks longer; the model's mouth is a plain lip with
  two short spouts.
- The housing's lower inboard lobe seen in REAR (it reaches 4 mm lower) is not modelled.
- The cable route below the pad is provisional (component 8).

## 5. Front master cylinder, Nissin (fiche K95CF0500) - partly

### Anatomy
- Cast body (satin grey): a reservoir box square to the bike on top, the barrel under it running along the bar, a
  clamp half round the bar and the holder (5) behind it with two M6 flange bolts from behind (zinc, DET830).
- Cap (4) a shade darker with its diaphragm plate's rim and two cross-head screws (19) on its long axis; printed
  warning text on it (graphics pass, not modelled).
- Rear face: round sight window (dark lens in a bright ring) and the cast LWR level mark (DET830).
- Lever (11): forged, silver, ball end; its root and the pivot lug under a black rubber boot (13) with a dome over the
  pivot bolt (15); nut (20) below; a cross-head reach adjuster seen through an oval opening in the boot's outboard
  side (RIGHT photo).
- Banjo below the barrel's inboard end: bolt (16), two washers (17), the hose fitting.

### References
- TOP zoom `ref/top_mc.jpg` (1670..1800 x 720..960, 6x, pixel ticks): cap corners and screws, clamp, boot, pivot boss.
- RIGHT `ref/right_mc.jpg` (2150..2330 x 380..500): cap top edge, boot with the adjuster opening, ball.
- FRONT `ref/ball_front.jpg`; DET830 (window, LWR, holder bolts); rf34 ruler crop (body, cap, boot, lever).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Cap | 50.3 x 34.5 mm, centre a 215.8 f 24.2, square to the bike (17 deg off the grip) | TOP corners cast at their height (the right bar agrees with the model in TOP: grip end within 2 mm) |
| Cap top | 44.5 mm over the bar's axis | RIGHT row 406.7, cols 2300..2328, cast on three planes through the cap: 44.0..45.2 (first guess 36: rf34 pair showed it low) |
| Cap screws | a 196.1 f 30.7 and a 234.5 f 14.9 (41.5 mm apart) | TOP |
| Clamp | a 182..202 | TOP |
| Lever pivot | a 164, f 48 | TOP (dome on the boot) |
| Ball centre | a 51, f 93, u -10 mm | RIGHT (2357, 471) and FRONT (1476, 268), each cast on its own plane; the earlier model had u -21 |
| Barrel | radius 11.5, axis f 27.5, a 168..246 | EST (rf34: round body under the box; clear of the bar) |
| Window | 25.6 mm ring, 18 mm lens, mid-height of the rear face | DET830 proportions |

### What was built
- `master_cylinder()` with `_mc_frame()` (the reservoir's axes, square to the bike) and `_mc_banjo()`; materials
  `mc_cast`, `mc_cap`, `glass_dark`. The front brake hose now starts at the banjo's fitting (`_hose_start`).
- Throttle cables moved 18..32 mm behind the bar's axis past the reservoir (TOP: the ferrule 30 mm behind at a 255).

### Checks
- Pairs: `chk/p12_rf34_st.jpg`, `p12_rear_st.jpg`, `p12_top.jpg` (reservoir 10 mm low: raised), `p13_right_st.jpg`
  (cap height right; ball 8 mm low: moved).
- Close-ups: `chk/m14.jpg` (DET830 and rf34 angles).
- Audit: cables leave the throttle spouts 0.7 mm into them (bars / cables, a seat); nothing else on these parts.

### Still different (why "partly")
- The cast body is a box on a cylinder: the photos show one casting with fillets between reservoir, barrel and clamp,
  and the raised NISSIN mark on the reservoir's front face; the lever boot is a block where the photo's is rounded
  over the body's outboard end.
- The LWR mark is a raised line, not lettering.

## 6. Clutch perch and lever (fiche K95CF0400: holder 14, clamp 15, bolts 20, lever 17, pivot bolt 22, nut 24, boot
16, adjuster 18 / 19)

### Anatomy
- Silver cast clamp round the bar (not black: TOP, DR05, DR06), its holder behind with two M6 flange bolts from
  behind; an arm with two ears round the lever's root; pivot bolt from above (bright head), nut and thread below.
- Black rubber boot: a sleeve over the arm and the lever's root, tapering outboard to where the lever leaves it.
- Forged silver lever, nearly level from the boot to the ball; ball end.
- Cable adjuster at the boot's inboard end: threaded sleeve, castellated lock ring, knurled black barrel; the cable
  leaves along its axis. A small hex screw with a nut on the boot's inboard end (DR05: two small nuts).

### References
- TOP zoom `ref/top_perch.jpg` (1690..1830 x 1300..1470, 5x, pixel ticks); FRONT 2280..2480 x 190..320; REAR
  1520..1720 x 180..310; DR05 (whole photo), DR06 (holder bolts from behind).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Frame for TOP readings | the photo's own left grip: end (0.9163, 0.4121), 13.34 deg sweep | gripscan.py; TOP draws the left bar 5 deg less swept than the side photos and the model, so positions are read relative to the photo's grip and placed relative to the model's |
| Clamp | a 165..193 | TOP |
| Pivot | a 174.3, f 33.3 (the model had a 195, f 36) | TOP |
| Boot | a 152..210, f 25..68, sleeve stations from u -0.026..+0.006 inboard to -0.020..-0.011 at the lever | TOP corners; FRONT pair (top edge falling to the lever) |
| Adjuster | a 202.7 f 43.9 to a 239.2 f 46.0; lock ring 16 mm, barrel 13.8 mm | TOP; DR05 proportions |
| Ball | a 49.5, f 95, u -21 (kept) | FRONT (2526, 284.5) cast on its x plane: a 55, f 92, u -20 (LEFT hides it behind the grip's end) |
| Lever height | level at u -19..-21 from the boot out | FRONT pair (the model's root had been 10 mm high) |

### What was built
- `clutch_perch()` (clamp halves, holder and bolts, ears, pivot bolt and nut, lever boss and lever, boot sleeve,
  small screw and nut, adjuster); `_clutch_adjuster()` gives the adjuster's axis; the clutch cable starts at its
  inboard end.

### Checks
- Pairs: `chk/p15_front_st.jpg`, `p15_rear_st.jpg` (boot a block and too high, lever root 10 mm high: fixed),
  `p16_front_st.jpg` (boot and lever heights agree). Close-up `chk/c16.jpg` beside DR05.
- Audit: nothing on these parts.

### Still different
- DR05's lever has a dog-leg bend just outboard of the boot; the model's blade is one smooth curve.
- The holder's rear face has a cast rectangular recess between its bolts (DR06), not modelled.
