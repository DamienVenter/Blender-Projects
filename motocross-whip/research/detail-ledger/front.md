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

## Parts after this pass (and the whole-bike SPEC checks)
- `bars`: Fatbar, holders, pad, both grips, and the switch blocks and their leads still waiting for component 7 (solid
  blocks round the bar). `hand_controls` (new, turns with the steering): clutch perch, throttle housing, master
  cylinder. `test_bike.py` reads `bars` for the SPEC width (827: passes, the grips' rims are in it) and height (1262
  +-6 mm "to the top of the bars"): the bars now top out at the grips' flange rims, 1.2558 (6.2 mm under), while the
  measured hand controls stand 9 to 12 mm over it (throttle hood 1.274 from REAR, reservoir cap 1.271 from RIGHT, both
  cast on their own planes; Honda's photo bike stands higher than the spec sheet in other places too). No measured
  dimension was moved to pass it: the check needs the coordinator's call (see the report).
- Splitting the parts showed overlaps that one part had hidden: the reservoir reached through the bar at its inboard
  end (now a neck ahead of the bar under a box over it) and the switch leads ran through the new clamp rings (now
  under them). Audit after the split: two seats only (throttle cables 0.7 mm into their spouts, holder bush 0.0 mm).
- Module vertices: 66,479 (fork 3,920, clamps 5,000, bars 33,652, hand_controls 10,137, front_brake 4,206,
  disc_guard 3,102, cables 6,462); budget 220,000.

# Round 2 (brief FRONT2.md: nine components, each its own build)

Check images and tools for this round are in `SCRATCH2/` =
`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/front2/`
(not committed). New tools there: `tri.py` (one feature picked in two calibrated photos -> the 3D point that fits
both, printed in the grip frame), `ruler2.py` (a and u / f scales over a calibrated crop), `blobs.py` (button blob
sizes and centres in both halves of a pair sheet), `overlap.py` (face pairs that cut each other, by material, in a
built .blend), `patch.py`.

## R2-1. Switches (fiche K95CF0400: left switch 4 with its lead, holder 3; start switch 6 with its lead, holder 5)

### Anatomy
- Left switch: a black housing behind the bar, matte and finely textured. Its rear face leans back towards the rider
  and is a rounded pentagon: a big chamfer on the top-outboard corner (with a small slot in it), a straight top edge,
  the inboard side, a point at the bottom; the wells' lips form the outline at the bottom and the outboard side.
- Three round buttons in dished wells, each well with a raised lip, held apart by a ridge: blue M (engine mode,
  upper outboard), red engine stop (the larger one, inboard), green T in two circling arrows (traction control,
  bottom). Symbols are engraved. A curved rib in a groove round the stop button's outboard side.
- Two LED lenses (rounded rectangles, taller than wide) in raised bezels over the stop button.
- The top: a raised pad with an arrow mark (TOP). Collar (holder 3) round the bar; a grommet block on the front-top
  outboard corner, the lead out of its front, down in front of the bar (lf34) and along under the bar to the pad.
- Start switch (right): a black box behind the bar between the throttle housing and the master cylinder, its face
  square to the bike; a deep square guard frame whose top bar is a hood; a recessed square button with the engraved
  start symbol (a circling arrow round a lightning bolt); a bright cross-head screw under the box; a mount to a strap
  round the bar; the lead.

### References
- DR06 whole photo; crops `ref/dr06_block.jpg` (490..900 x 230..700, 2x), `dr06_red.jpg`, `dr06_green.jpg` (symbols).
- DET829 crops 1800..2800 x 1300..1950 (`d829_block.jpg`), 1980..2480 x 1360..1600 (`d829_top.jpg`: chamfer slot,
  lenses, the dark block behind the chamfer).
- DET830 1400..2000 x 1000..1700 (`d830_start.jpg`: start switch).
- REAR 1569..1773 x 154..339 at 6x with scales (`r2_rear_L.jpg`); TOP 1740..1830 x 1380..1460 at 10x
  (`top_block10.jpg`); LEFT grid (`grid_left_L.jpg`), lf34 / lr34 (`lf_lr_block.jpg`); start: REAR 2266..2354 x
  202..287 and TOP 1729..1810 x 801..881 at 10x (`start_rear.jpg`, `start_top.jpg`). Fiche `K95CF0400`.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Blue / green / red centres | a 131.1 / 130.9 / 150.7, u 16.6 / -0.1 / 7.1, then +1 mm in a | tri.py REAR + TOP (residual 1.0..1.3 px); the +1 mm from the REAR and TOP pairs (model 1.1..1.3 px outboard in both) |
| Face lean | 12.5 deg, face at f -38.6 + 0.2216 u mm | green 3.7 mm behind blue, 16.7 mm lower (tri.py); TOP pair (moved 0.8 mm back) |
| Button sizes | 9.5 mm (blue, green), 12.5 (red), 1.2 mm proud | REAR 9.1..9.6; DR06 red / blue 1.31; REAR pair blobs 89.5 / 87.0 / 113.7 px against the photo's 90.1 / 88.7 / 114.1; TOP pair blobs 58.2 / 52.6 / 69.4 against 58.8 / 55.3 / 69.7 |
| Wells | radius 8.3 (small), 9.6 (red), lip 0.4 mm, floor 2.6 mm deep | DR06 1.9 x and 1.57 x the buttons, kept 0.5 mm apart |
| LED lenses | a 145.9 / 154.3, u 26.3; 6 x 9 mm, bezel 7.6 x 10.6 | tri.py; REAR 6.5 x 10 with the bezel |
| Outline | a 122.5..164.2, u -12.2..+33.7 | REAR edges read on the face's plane (a point 25 mm behind the ruler reads 7 mm inboard: the sweep), TOP rear face a 120.9..158.7; top 1.8 mm lower after the REAR pair |
| Top pad | a 144..159, f -27..-18 | TOP cast at u 37 |
| Start frame | centre a 161.7 f -39.2 u -6.9; 18.5 x 20 mm, opening 12.5 x 13, 5 mm deep, hood +2 | tri.py REAR + TOP (0.2 px), 3 mm outboard after the pairs; REAR corners; DET830 proportions |
| Start button | 7.5 mm square, 1.8 mm proud of the recess floor, 3 mm inside the frame | DET830 (90 / 240 px of the frame) |
| Start box | 21 x 29 mm, 12 mm deep, top 8 mm over the frame | TOP pair (11.3 mm deep), REAR pair (box top over the frame) |
| Engraving | 0.25 mm, floor 20 % darker | EST (DR06: the symbols read by their shadowed walls) |

### What was built
- `switch_left()`, `switch_start()` (in `hand_controls`; the leads in `bars` through `switch_leads()`, since they run
  into the bar pad). Helpers `_hull_outline`, `_inset`, `_face_frame`, `_button` (round, UVs on its top),
  `_square_button`. The face is a 3 mm plate (plate2d) with the wells' holes and a rounded edge, 0.3 mm proud of the
  body behind it (the parting line); body rings with a rounded front; wells revolved; buttons; the stop button's rib;
  lenses in bezels; the chamfer slot; the top pad and arrow; the collar; the grommet block.
- `switch_maps()` (run by `python3 detail_front.py`) writes `textures/stock/sw_m`, `sw_stop`, `sw_tc`, `sw_start`
  (colour and normal maps, 512 px over the button). Materials `sw_m`, `sw_stop`, `sw_tc`, `sw_start` (colour map +
  normal map), `led_lens`, `sw_body` (matte, fine bump). The old solid blocks and their buttons are gone from `bars`.
- Tests: `test_left_switch_buttons_sit_on_the_rear_and_top_photos`, `test_start_switch_frame_sits_on_the_rear_and_
  top_photos`, `test_switch_buttons_carry_their_symbols`.

### Checks
- Close-ups: `chk/s1_a.jpg`, `s1_b.jpg` (first build), `s2_a.jpg` (DR06 and DET829 angles), `s2_b.jpg` (DET830).
- Pairs: `chk/p1_rear`, `p1_left`, `p1_top`, `p1_lf34` (first build), `p3_rear_1604`, `p3_top_1721`, `p3_rear_2261`,
  `p3_top_1735`, `p4_rear_start`, `p4_top_start` (after the fixes).
- Fixed after cycle 1: the lead's loop over the top (REAR shows nothing above the housing), top 1.8 mm lower, all a
  +1 mm, buttons 1.2 mm proud (they were 0.4), housing matte charcoal (it rendered as glossy black, the wells lost),
  smoky lenses. After cycle 2: the face 0.8 mm back; start frame 5 mm deep, box taller and shallower, 3 mm outboard.
- Audit: the two leads seat 0.4..0.5 mm into their grommet and box (bars / hand_controls). No floating piece.

### Still different
- LEFT and lf34 show a dark edge 42..44 mm over the bar's axis above the housing (their rays cross near a 163,
  f -17.5); REAR shows nothing there (`ref/rear_top_chk.jpg`), nor do DR06 and DET829. Left as REAR has it; the
  cause (a pose difference between the photos, or a part I could not identify) is not found.
- The photo's wells catch the light as wide grey dishes; the model's read as darker rings.
- The start switch's housing fills more of the space towards the bar in TOP than the model's narrow mount (the
  throttle boot and cables are over it there, so its shape is not readable); its bottom lip and notch (DET830) are
  not modelled. Clamp screws of the left holder: none visible in any photo, none modelled.

## R2-2. Front master cylinder, the rest of round 1's component 5 (fiche K95CF0500)

### Anatomy (added to round 1's list)
- Rear face of the reservoir: flat, satin cast, running down behind the bar; the sight window is a bright machined
  ring with a chamfer, a chrome inner ring and the dark lens; inboard of it the raised LWR with its level line under
  it, and a small round ejector-pin mark above that (DET830).
- Front face: raised NISSIN, bold italic (rf34). Outboard side: a small square pocket just under the cap (rf34).
- Holder (5): two round lobes round its flange bolts joined by a waist (DET830). Banjo bolt black (DET830).
- Lever boot: a rounded rubber pillow over the pivot lug and the lever's root (rf34). Lever: forged, flat sides with
  rounded edges (rf34, DR05 for the clutch side).

### References
- DET830 560..1560 x 950..1900 (`ref/d830_mc.jpg`); REAR 2193..2369 x 184..302 at 9x (`ref/mc_rear.jpg`); rf34
  1964..2180 x 298..428 at 8x (`ref/mc_rf34.jpg`); RIGHT (`ref/mc_right.jpg`).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Window | centre 5.7 mm inboard of the cap's centre, 19.5 mm over the bar's axis; ring 18.4 mm, chrome ring 13.8, lens 12.4 | REAR cast on the rear face's plane (x 0.9837): 18.0 over the axis, ring 19.2, lens about 13, its bottom at 8.4, on the bar's top; raised 1.5 mm and 0.8 mm smaller so the ring clears the bar (the bar's top under the face is 8.9..10.3 mm up there) |
| Rear wall | down to 0.5 mm over the bar's top, ly -18..+22.5 | the bar crosses under the reservoir 16 deg off it (`_mc_bar_axis`) |
| LWR | centre ly +18.3, 15 mm up; letters 6.3 x 2 mm, line under them | DET830 proportions to the window (0.645 of the way to the inboard edge, 4.3 mm under its centre) |
| Pin mark | ly +19.0, 22.7 mm up, 2 mm | DET830 |
| NISSIN | 32 x 5.5 mm, centre ly -4.0, 21.5 mm up, raised 0.35 | rf34 cast on the front face's plane (ly -19.9..+12.0, 18.8..24.3) |
| Pocket | 4.8 x 3.6 mm, 5.7 mm ahead of the cap's centre, 36.7 up, 1 mm deep | rf34 cast on the outboard face |
| Holder lobes | radius 9.5 round the bolts, waist 12 mm | DET830 (lobes 105 px round bolts 350 px apart = 32 mm) |
| Lever section | rounded square scaled to the old ellipse's (thick, tall) | EST from rf34 (flat sides) |

### What was built
- `master_cylinder()`: the rear wall `skirt` (its lower edge from `_mc_bar_axis`), the window rebuilt (machined ring,
  chrome ring, lens), `_decal()` patches with relief maps `mc_lwr` and `mc_nissin` (`mc_maps()`, textures
  `stock/mc_nissin_n.png`, `mc_lwr_n.png`, FreeSans Bold / Bold Oblique), the pin mark, the pocket, `_dogbone()`
  holder, the boot as `pillow()` (rounded both ends, r 6), banjo bolt `bolt_black`. `_lever()` takes `LEVER_SEC`
  (both levers).
- Test `test_master_cylinder_window_and_lettering` (window on REAR within 3 px, ring off the bar, lettering not
  mirrored).

### Checks
- Close-ups `chk/m6_a.jpg` (first: both reliefs came out mirrored; the facing reader's right is the bike's left on the
  front face), `chk/m8.jpg` (DET830 and rf34 angles, fixed). Pairs `chk/p7_mc_rear.jpg`, `p7_mc_rf34.jpg`
  (`p7s_mc.jpg`): window, holder lobes, NISSIN and the pocket land on the photo's within 1..3 px.
- Audit: round 1's window ring touched the bar (it hung 5 mm under the reservoir's wall): gone.

### Still different
- The casting is still a box on a barrel with a block web: rf34 shows the reservoir flowing into the barrel through
  a large concave fillet and a rounded body under it; not rebuilt (it needs a lofted casting, not more pieces).
- In REAR the throttle cables cross in front of the reservoir's top; in the model they pass over it (component 4).
- The boot's front opening round the lever is a plain end; the photo's wraps the lever's root.

## R2-3. Clutch lever, the rest of round 1's component 6 (fiche K95CF0400: lever 17)

### Anatomy
- Forged lever, flat sides with rounded edges; out of the boot it jogs back towards the grip in an S (the dog-leg)
  and runs on in a straight, gently curving blade to the ball (TOP, DR05, lf34).

### References
- TOP grid crop at u -19 mm (`ref/lever_top.jpg`, 5x, grid of a and f every 10 mm); DR05 whole photo
  (`ref/dr05.jpg`); lf34 1867..2151 x 330..449; FRONT (round 1's ball).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Dog-leg | up to 19.3 mm off the boot-to-ball line towards the grip, a third of the way along; 2.8 / 9.9 / 16.0 / 19.3 / 16.7 / 15.1 / 13.0 / 10.8 / 6.9 mm at 0.10..0.90 of the way | TOP centre line picks fitted through the grid (fit 0.01 mm), read relative to the photo's own boot exit (a 159.5, f 67.4) and ball (62.1, 110.6) because TOP's left bar is turned (round 1); scaled 111.5 / 106.5 to the model |
| Ball | a 55.5, f 93, u -20.5 | FRONT cast (a 55, f 92, u -20); round 1 had kept a 49.5; TOP in its own frame a 62; the lf34 pair also had the model's ball outboard |
| Section | rounded square scaled per point to 12 x 16 mm at the root, 7.2 x 10.4 at the ball | round 1's sizes; flat sides from rf34 / DR05 |

### What was built
- `clutch_lever_line()` (CP_EXIT, CP_DOGLEG), the lever spline sampled at 44 points (26 could not hold the S),
  `LEVER_SEC` for both levers. Also, from DR05 for component 1: the left holder's strap lug under the bar's front with
  its cross-head clamp screw, the grommet and the lead's drop moved inboard of the strap (a 146, where DR05 has it),
  the drop in an 8 mm rubber sleeve, the collar matte.
- Test `test_clutch_lever_dog_leg`.

### Checks
- Pairs `chk/p9_lever_top.jpg`, `p9_lever_lf34.jpg` (`p9s_lever.jpg`): the S matches TOP's in shape; the ball sat
  outboard in lf34 (moved). Close-up `chk/l10.jpg` beside DR05.
- Audit: the strap lug first cut the lead (6.5 mm), then the sleeve's curve grazed the collar (2.6 mm): both moved;
  only the leads' 0.5 mm seats remain (bars / hand_controls).

### Still different
- DR05 shows the left switch's top from the front as a taller block than the model's (as LEFT and lf34 do; REAR
  does not): see component 1.
- The blade's thickness tapers in DR05 more sharply just past the dog-leg; the model's section changes linearly.

## R2-4. Cables and hose routing - partly (band ties built; the routing itself not reworked)

### Anatomy
- Two black nylon band ties on the bar (fiche 25): a ribbed strap round the bar and what runs under it, a buckle
  under the bundle, the cut tail hanging from the buckle (DET830: about four band widths long, ribs across it).
  Left: inboard of the clutch perch round the bar and the switch lead (DR05, DR06). Right: inboard of the master
  cylinder round the bar and the brake hose (DET830).
- Cable ends and boots: the throttle cables' spouts and adjuster, the clutch adjuster, the leads' grommets (round 1
  and components 1..3 above).

### References
- DR06 1000..1440 x 100..600 (left band), DR05 (left band), DET830 100..500 x 300..950 of `ref/d830_mc.jpg` (right
  band and its tail), round 1's TOP crops for their positions.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Positions | left a 252.5, right a 280 | TOP (round 1: the bar thick out to the tie at a 250..255 left, 280 right) |
| Strap | 7 mm wide, 1.1 mm thick, ribs 0.4 mm every 0.7 mm, 1 mm clear of the bar | EST (a 7 mm tie; DR06 / DET830 ribs about a tenth of its width apart) |
| Buckle, tail | 8.2 x 6.2 x 4.8 mm; tail 28 mm, angled a little forward | DET830 proportions |

### What was built
- `_band_frame()`, `_bar_band()` (in `bars`): the strap's loop is the hull of the bar and the lead under it, built
  ring by ring in the bar's own frame (the right tie sits where the bar rises 24 deg: `tube()`'s world-up frame had
  tilted the strap 2 mm into the bar there), ribs as alternate thicker rings, buckle and tail. Material `tie_band`.
- Test `test_band_ties_hold_the_bar_and_the_lead` (the strap outside the bar's own surface everywhere, round the lead).

### Checks
- Close-ups `chk/b13.jpg` beside DR06 and DET830 (before the frame fix and the longer tail).
- Audit (front parts and neighbours, `a_s14`): no cable through any part; seats only: switch leads 0.5 mm into their
  grommet and box, throttle cables 0.7 mm into their spouts, holder bush 0.0.

### Still different / not done
- The right tie should hold the brake hose: in DET830 the hose runs from the banjo along under the bar through the
  tie; the model's hose leaves the banjo forward and crosses over the number plate (round 1's FRONT "hose" scan), so
  the tie holds only the start switch's lead. The hose's route at the bar, the clutch cable's run inboard of its
  adjuster and the throttle cables passing in front of the reservoir's top in REAR are not reworked.
- `fork_guards` / `front_brake` 1.5 mm at (1.327, 0.099, 0.698): the hose guide's grommet under the lower clamp
  against the plastics' fork guard (that part changed in main since round 1): a shared issue, left for component 6.

## Round 2 lessons (for the bike-modelling skill)
- A feature behind or ahead of a ruler's plane reads at the wrong a in an end photo: with the bar swept 16 deg, 25 mm
  of depth moves it 7 mm along the bar. Pick it in two calibrated photos and triangulate (`tri.py`).
- `geom.tube()` orients its section from the world's up: a flat strap round a tilted axis comes out twisted into it.
  Build such rings in the object's own frame.
- Relief lettering on a face: for someone facing the bike's front, their right is the bike's left; check one letter
  in a close-up before trusting a map.
- A part's UVs are all dropped by build_bike.py if Blender removes one degenerate face of it: keep UV-mapped pieces
  (buttons, decals, knurl) free of zero-area faces.

## Round 2 status
- Components 5 (fork tops), 6 (fork feet and caliper), 7 (front disc), 8 (front hub), 9 (front spoke lacing): not
  started.
- Module vertices: 82,528 (fork 3,920, clamps 5,000, bars 40,830, hand_controls 19,008, front_brake 4,206,
  disc_guard 3,102, cables 6,462); budget 220,000.

# Round 3 (brief FRONT3.md: seven components, each its own build)

Check images and tools: `SCRATCH3/` =
`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/front3/`
(not committed). New tools there: `tri2.py` (cast or triangulate a pixel about the photo's own axle: each view's
pixel is first moved by that view's offset, photo axle end minus the model's), `gpair.py` (photo and render of a
pair.py run on one labelled pixel grid, with a 50/50 overlay and the render shifted by the offset), `p1..p5.py`.

## The front axle in the side photos (a shared finding)
- The axle's ends sit 10 to 14 px behind and 5 to 10 px above FA's projection at their own y in both side photos
  (right hex socket (2948, 1606) against 2958, 1611; left nut (1050, 1605) against 1036, 1615) and 10 px above it in
  FRONT (shaft centre row 1525 against 1535). The cameras put FA (y 0) on the blueprint's wheel centre, so this is
  the side cameras' parallax at y +-0.12 (it falls to zero at the centre plane), the same effect the chassis pass
  found at the rear axle. As there: every foot and caliper feature was cast on its own plane after moving its pixel
  by the view's offset (LEFT +13.7 / -10.3, RIGHT -10.4 / -5.2, FRONT 0 / -10.3), and built about FA; in the pair
  sheets the model therefore stands 13 px ahead and 10 px under the photo there (`gpair.py ... 14,-10` overlays
  them). rf34 and lf34 are fitted to the model, so they show no offset and are not used for positions.

## R3-1. Fork feet and front caliper (fiche K95CF1100, K95CF1200)

### Anatomy
- Axle holders (both, Showa, cast, satin mid grey with a fine grain): a round socket round the inner tube's foot;
  ahead of it the axle boss, a block with a flat top and front, the front corners rounded (top 7 mm, bottom 9 mm);
  the whole foot's underside one horizontal plane; raised italic SHOWA round the socket's outboard-front side, a
  second small cast mark lower down (RIGHT "TECH"/"S", unreadable, not modelled).
- Right holder: the boss split by a horizontal slit from the axle forward, two vertical M6 hex flange bolts on its
  top (zinc), their threaded ends in the underside (FRONT: two dark dots); the axle's end flush in the boss with a
  bright head ring and a 17 mm hex socket.
- Left holder: the axle nut's side (flange nut and washer, the hollow axle end showing in it, DET831); covered in
  every photo by the disc guard's black mount; the caliper bracket's grey arm leaves the socket's rear in two
  branches to two hex flange bolts with washers (zinc), a cast triangular pocket in the upper branch.
- Caliper (Nissin, two pistons 30 / 27 mm): the outer body's two lobes over the bores with a machined D-shaped flat on
  each, raised italic NISSIN along the waist between them reading up the arc, letters' tops towards the axle; the top
  end with a round bright plug with a hex socket; the bleed screw and its black rubber cap at the top rear; the
  banjo (black) with its bolt and the hose's black steel pipe, crimp and sleeve at the rear; a black slotted plug end-on
  on the front edge; a hex bolt under the foot; the bridge over the disc's rim to the reaction half; bronze pad
  shims (RIGHT, rf34 through the spokes).
- Disc guard: two zinc socket flange bolts on black bosses (upper over the left holder, lower under the foot).
- Brake hose clamp on the left fork guard (the guide): plate, two bolts, rubber grommet round the hose.

### References
- DET831 (475831) whole (`ref/d831_small.jpg`), crops 1900..2900 x 1100..2150 (`d831_cal.jpg`: caliper) and
  1300..2100 x 1000..1900 (`d831_foot.jpg`: left foot, axle end, bolts). DR12 whole (`ref/dr12.jpg`).
- LEFT gridded 1000..1300 x 1480..1720 (`ref/g_left_cal.jpg`), RIGHT 2800..3020 x 1500..1690 (`g_right_foot.jpg`),
  FRONT 1800..1960 x 1420..1600 (`g_front_foot.jpg`), rf34 2580..2780 x 1490..1660 (`g_rf34_foot.jpg`); crops of
  lf34 and rf34 (`lf34_foot.jpg`, `rf34_foot.jpg`). Fiche K95CF1100 (24 pinch bolts, 13 centre bolt with 28),
  K95CF1200 (3, 4, 5, 14, 16).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Boss faces | outer y 106 mm, inner 72.8 (FRONT 70.5: kept 0.3 mm off the hub's end collar) | FRONT cols 1845 / 1897 cast at f 70 |
| Boss outline | top z +22, front x +29, underside z -25, slit z +2 (gap 0.8) | RIGHT cast on y -0.107: bolt seats 19.3..20.7, front 28.3..29.1; FRONT top / slit rows 1491 / 1526 |
| Underside | one horizontal plane 25 mm under the axle (socket and boss) | RIGHT socket bottom rear (f -18.7, t +2.3), FRONT front rim (27.5, -21.3): slope 0.51 = tan of the rake |
| Socket | radius 27.5 | FRONT 1820..1902 (56.8 over the silhouette's cast bulges) |
| Pinch bolts | M6 flange, 10 mm hex; x +17, abs(y) 97.5 / 79.0 | FRONT cols 1859 / 1885; x EST between the bore and the front (RIGHT +11, within its offset doubt) |
| Axle | 20 mm; right hex socket 17 mm, head ring 26.4; left nut 22 mm with washer 34 | RIGHT 19.8 mm corner to corner; FRONT shaft 29 px; LEFT nut 21..23 mm |
| SHOWA | 27 x 6 mm round the socket, centre 16 deg ahead of outboard, t 31.5 | RIGHT 2878..2914 x 1584..1600 cast on the socket |
| Caliper centre | r 116, 17.5 deg below the rearward horizontal | LEFT NISSIN (1200, 1645) on y 0.100 |
| Lobes, D-flats | bores at w +-19.5, walls r 21.5 / 20; flats r 0.66 of the wall beyond a chord 2 mm out | LEFT flats (1205, 1615) and (1190, 1672): w +23.5 / -22.3; SPEC pistons |
| Plug, bleed, banjo, slot, foot bolt | (q, w) mm: (6.6, 55.3), (22.9, 46.8), (38.3, 0.3), (-26.4, -1.1), (11.5, -45.2) | LEFT (1230,1580), (1247,1597), (1248,1660), (1167,1636), (1197,1705) |
| Bracket bolts | world (dx, dz) (-108.3, 17.2), (-75.1, -54.6); 10 mm hex, washer 16 | LEFT (1197,1578), (1154,1670); head in a 20 px washer face |
| Bracket roots | the socket's rear, f -14 / t 19 and f -30 / t 0 | LEFT (1128,1600) .. (1142,1648) |
| Body step | the top end, rear block and foot 8 mm under the lobes' face | DET831 (EST depth) |
| Guard bolts | (-8.7, 38.8), (-54.9, -33.1) | LEFT (1060,1556), (1121,1650) on y 0.134 |

### What was built
- `axle_holder(side)` (in `fork`): the socket as rings round the tube whose underside follows the horizontal plane
  (rounded 4 mm), a recess with the damper's centre bolt and slotted rebound adjuster (EST, unseen), SHOWA on
  `_decal_cyl` (relief map `stock/showa_n.png`), the boss as rounded castings (`_rplate`: any outline with holes,
  every edge rounded, a radius per vertex): right as two jaws round the bore with the slit (0.4 mm edges at the slit,
  2.4 mm elsewhere), left one piece; pinch bolts; the left lug for the guard's upper bolt; the caliper bracket's two
  branches with the pocket and bolts (part of the left casting, in `fork`). `axle()`: hollow shaft, right end with
  the hex socket and head ring, left flange nut and washer. Material `ah_cast` (satin, grain).
- `caliper()` (in `front_brake`): `_cal_outline()` (hull of lobes, ends and bosses, notched round the bracket bolts),
  the lower casting and the lobes' casting standing 8 mm proud, D-flats (`cal_spot`), NISSIN (`cal_nissin`, map
  `stock/cal_nissin_n.png`), the bridge and reaction half, pads (`pad_friction`) on bronze shims (`pad_shim`), plug,
  slotted plug, foot bolt, bleed screw and cap, banjo with washers and bolt; the hose ends in a black pipe, crimp and
  sleeve. `disc_guard`: the two bolts moved to the photo's places, on black bosses.
- The hose guide on the fork guard moved 3 mm forward (it reached 1.5 mm into the guard's front: the guard's bump at
  t 0.365..0.38 stands at f 59.7 and Blender solidifies it 3 mm).
- Tests: `test_right_axle_clamp_on_the_photos`, `test_caliper_and_bracket_bolts_on_the_left_photo`,
  `test_caliper_pads_straddle_the_disc_and_the_body_clears_it`; the axle test follows the new ends.

### Checks
- Pairs: `chk/p0_*` (round 2's foot and caliper), `p1_*` (first build), `p2_*`, `p4_left`, `p4_lf34`; overlays
  `chk/g1c_left.jpg`, `g2_left.jpg`, `g2_right.jpg` (render shifted by the offset).
- Close-ups: `chk/cu1_a.jpg` (DET831 angle), `cu1_b.jpg` (DR12, right foot), `cu2_a.jpg` (after the step).
- Fixed after cycle 1: socket 12 mm too low at the rear (the underside is horizontal, not square to the tube),
  socket 0.7 mm smaller, boss underside 3 mm higher, bracket as two branches (one hull filled the gap where the
  body's front shows), caliper rear block narrower. After cycle 2: the lobes stand 8 mm proud of the rest (one flat
  face read as a slab), bracket bolts smaller, the body notched round them.
- Audit (`a_c4`): the boss first sat 3.7 mm on the hub's collar (inner face moved), the bracket in the socket and the
  caliper (moved into the fork part, notched), the guard boss in the socket and the bracket (shortened onto the
  branch), the fork guard into the hose guide (moved). Left: guard bosses seated 0.8 mm on the lug and the branch;
  no loose piece.

### Still different
- The disc guard itself (honeycomb window, the angular black mount round the left foot and axle) is round
  dome-and-holes as before; so the left socket and its SHOWA show where the photos have the black mount. It needs its
  own build (not on this round's list).
- The caliper's casting is two stepped slabs: DET831's body has deeper sculpting between the lobes and the rear block
  (a notch under the lower lobe, the banjo boss as its own block). The bracket's upper branch is a plain hull; the
  pocket is shallow.
- The second cast mark on the right socket and any lettering on the left one are not modelled; the pinch bolts' x
  rests on room between the bore and the front (RIGHT reads 5 mm further back within its offset doubt).
- The fork guards' bolts are the plastics' (`guard_hardware`); that part also holds a hose clamp block on the guard's
  outer face where this module's guide is (one real clamp modelled twice): a shared issue.

## R3-2. Fork tops (fiche K95CF1100 cap parts 16 / 30, K95CF0700 top bridge, K95CF0900 stem nut)

### Anatomy
- The outer tube's top 5 mm above the top clamp, gold with fine turning lines.
- Showa cap: a bright turned hex with a chamfered top edge, its corners turned round inside the tube's diameter; a
  recessed black anodised top with a raised lip; on it a raised black block with chamfered edges running from the
  centre to the rim, a large slotted adjuster at its outer end and a small slotted screw near the centre; a short white
  index line on the black rim.
- Top clamp: grey satin casting; on each boss's front-outboard side a lug split along the tube's plane with two hex
  flange pinch bolts from outboard (LEFT, DET835). The steering stem nut: a large bright hex flange nut on a washer.

### References
- DET835 crops 1300..2500 x 900..1650 (`ref/d835_tops.jpg`), 1420..1700 x 960..1190 at 3x (`d835_cap.jpg`),
  2250..2520 x 1290..1430 (`d835_capR.jpg`, the right cap under the pad). LEFT gridded 1560..1720 x 500..630
  (`ref/g_left_top.jpg`). TOP (`g_top_caps.jpg`: the pad hides both caps but a rim). FRONT: the plate hides the clamp.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Pinch bolts | f 30.2, t 0.8935 / 0.9102, heads' faces about 23 mm outboard of the tube's plane | LEFT (1580, 575), (1590, 555) cast on y 0.122 (round 1 saw the same two heads) |
| Turned band | t 0.928..0.933, five grooves 0.15 mm deep every 0.8 mm | LEFT axis (round 1), DET835 lines |
| Cap hex | 47 mm across flats, corners turned to r 25.2, t 0.933..0.941, top chamfer 1.6 mm | DET835 (flats as wide as the tube); LEFT top front edge t 0.925 + lean -> 0.941 |
| Black top | 1.5 mm under the hex's top, lip r 20.5 | DET835 |
| Block | 30 x 21 mm, 4.5 mm tall, from 6 mm ahead of the centre rearwards | DET835 proportions; LEFT top t 0.947 on y 0.099; held under the pad's underside t 0.945 |
| Screws | slotted, 9 and 6 mm | DET835 |
| Stem nut | 30 mm hex flange, washer 42 mm | DET835 (0.6 of the cap's width) |

### What was built
- `fork_cap(side)` (in `fork`): hex rim as rings with per-band materials (bright hex, black top), the block as a
  rounded casting (`_rplate`), the two slotted screws, the index mark (material `mark_white`); the outer tube's
  profile carries the turned band.
- `_pinch_front()` replaces the top clamp's rear lugs (round 1, EST): the lug 26.2..37.2 mm ahead of the tube's axis
  (clear of the 51 mm tube), the slit, two M6 flange bolts; the top clamp's bosses and bridge now `alu_cast`. The
  stem nut is a `fastener()` with its washer and the stem's end.
- Test `test_fork_caps_and_top_clamp_pinch_bolts` (bolt heads on LEFT within 3 px, caps under the pad, index marks).

### Checks
- Close-ups `chk/cu4_a.jpg` (DET835 angles: the pad hides the cap from above), `cu5_a.jpg` (cap and clamp alone
  beside `d835_cap.jpg`). Pairs `chk/p8_left.jpg`, `p8_lf34.jpg`.
- Audit (`a_c8`): the first lug reached 2 mm into the tube (moved forward) and its bolt heads 4.9 mm into the number
  plate's wing (seat moved 3 mm in; the plate's wing runs 45 deg across the bolts); none left over 0.8 mm.

### Still different
- The model's number plate wing (plastics) covers the pinch bolts in LEFT where the photo's plate edge stands 25 px
  further forward and shows them: a shared issue for the plate.
- The adjuster block's direction is EST (rearwards, LEFT shows it at the cap's rear; DET835 suggests rear-outboard)
  and it is 4.5 mm tall to stay under the pad, where DET835's looks taller (its pad end sits beside the cap).
- The top clamp itself is still round 1's thin bridge with ring bosses; DET835 and LEFT show a thicker casting with a
  squared rear end (a clamp build, not on this list).

## Round 3 status
- Component 3 (cables and hose routing, rest), 4 (front disc), 5 (front hub), 6 (front spoke lacing), 7 (master
  cylinder fillets): not started.
- Module vertices: 106,962 (fork 18,219, clamps 6,961, bars 40,830, hand_controls 19,008, front_brake 12,040,
  disc_guard 3,442, cables 6,462); budget 220,000.
- Lessons: the foot's underside is world-horizontal, not square to the tube (a socket read on the wrong plane came out
  12 mm long); features at |y| 0.1 to 0.13 near the front axle need the side cameras' parallax offset (above); a
  close-up camera for the fork caps must look past the bar pad's end (the pad covers their inboard halves).
