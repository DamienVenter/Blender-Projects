# Detail ledger: wheels, tyres, final drive, rear brake (`scripts/bike/detail_wheels.py`)

Micro-detail pass of 2026-11-11 (brief: one component at a time, each with references, numbers, model and check).
Coordinates: axle-line frame, metres. Check images are in the agent's scratch folder
(`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/wheels/`,
written `SCRATCH/` below); they are not committed.

Tools written for the checks (scratch): `edge.py` (per-row outline of photo and model in a `pair.py` box, the
difference in pixels), `sbs.py` (images side by side), `cu.sh` (close-ups), `chk_tyre.py` (tyre mesh numbers).

## 1. Rear tyre tread (Pirelli Scorpion MX32 Mid Soft 100/90-19)

### Anatomy (what shows at 30 cm)
- Carcass crown and shoulders under the knobs; groove floor between rows.
- 46 rows round the tyre. Per row: a centre knob across the crown split along the centre line by a V slit (full
  length, part depth: the halves join below it); an intermediate knob each side in the same row, its outer-leading
  corner cut at a slant; half a pitch on, a shoulder knob each side (plain tapered block); a low pad joining the
  row's three in-row knobs (a faint arc on the floor between rows, longest at the centre).
- Knob walls drafted (narrower top), top edges rounded, corners rounded in plan, a fillet at each knob's root.
- Mould vent hairs ("spews"): thin whiskers at the knobs' top corners (DR13: one at each corner of the shoulder
  knobs, pointing up) and on the shoulder knobs' outer faces (475832).
- Finish: black rubber with a dull sheen where lit (studio photos); new-tyre purple bloom in DR13 (outdoor sun) and
  a red centre line in 475832 (outdoor press bike) are not on the studio bike: left off (REAR and lr34 show
  neither).

### References
- REAR studio photo 475598: rows 1440..2040, cols 1880..2120 (whole tread from behind); zoom rows 1560..1700 cols
  1920..2080 (one row: centre knob 44 px = 28 mm at the top with its slit, intermediates, shoulders half a pitch
  on, the floor arcs).
- LEFT studio photo 475600: polar scan of the outline round the rear axle (scan_left.npy: tall plateaus every 7.8
  deg = 46 rows, 4.2 deg wide; low plateaus half a pitch on); zoom cols 3250..3400 rows 1480..1680 and cols
  3300..3400 rows 1500..1620 (one pitch side-on: the in-row knob's outer face 25 px = 19.5 mm long, the row 29 px =
  22 mm, the shoulder's face 25 px).
- RIGHT studio photo 475596: the same scan (46 rows).
- lr34 475599 cols 3060..3260 rows 1560..1760 and rr34 475597: shoulder and intermediate knobs seen from outside.
- 475832 (rear tyre and chain): crops 1100..2300 x 800..1900 and 1300..2600 x 1700..2732; slit zoom 1380..1880 x
  1050..1450 (the slit is a V groove; the halves join below; vent hairs on the knob edges).
- DR13 (Dirt Rider rear rim and tyre): shoulder knobs side-on (plain tapered blocks, four spews on each top).
- Pirelli's product images (web/README.md): flat view of the tread (plan shapes: intermediates with a slanted outer
  end; their shoulders have a notch that the stock tyre does not have), the rear from behind.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Rows round the tyre | 46 | LEFT and RIGHT polar scans, 7.83 deg a row |
| Tip radius | 334.3 mm | shared `R_REAR` (both side photos) |
| Groove floor (crown) | 317.8 mm (knob 16.5) | side scans: floor 317..319 |
| Centre knob | 22 x 30 mm at the root, 28 mm wide at the top | REAR 44 px at the top; LEFT zoom row length 22 mm |
| Centre slit | 1.5 mm at its floor, 9 mm above the carcass; about 5 mm at the top (V) | REAR zoom (dark wedge 8 px wide at the top); 475832 (halves join below) |
| Intermediate | t 16.5..31.5 mm, 19 mm long, corner cut 6.5 x 5.5 mm | REAR cols 1947..1977 (y 15..34 mm), LEFT zoom 19.5 mm |
| Tip envelope | R at the crown, R - 9 mm at t 31.5 mm | `edge.py` on LEFT: nothing passes the centre tips (perspective: +0.28 px per mm of y, 1.28 px per mm of radius) |
| Shoulder | t 28..47 mm, 16 mm long, inner top corner r 317.5, outer end 12 mm high | REAR cols 1929..1959 (y 26..45.5); LEFT low plateau col 3365 |
| Tyre width | 92.2 mm | shared measurement 91.5 (REAR rows 1750..1975), test +-3 mm |
| Draft | 4 deg centre, 5 deg others; slit walls 7.5 deg | EST (moulded rubber) |
| Edge round, root fillet | 0.9 mm, 1.0 mm | EST (MICRO.md: rubber 0.5 to 1 mm) |
| Pad | 1.2 mm high, 24 mm long at the edges, 33 at the centre | REAR floor arcs; EST height |
| Vent hairs | 0.45 mm thick, 2.5..5 mm long | 475832, DR13; EST size |

### What was built
- `carcass()`: the carcass as one whole grid (no holes); `Knob` maps a knob's plan (s along the tread, t across the
  section, z height) onto the wheel with a lean between radial and the surface normal; `_knob()` builds any knob
  from a plan polygon: drafted walls (per-vertex draft for the slit), root flare sunk 0.8 mm into the carcass,
  quarter-round top edge, Delaunay top cap; `rear_tread()` lays the rows; `_spews_at()` / `_spew()` the hairs.
- Rear tyre 89.5k vertices (was about 20k).

### Checks
- `SCRATCH/p_left4.jpg` + `p_left4.jpg.d/edge.png`: LEFT outline, model minus photo: median 2 px, the tall and the
  low plateaus within 1 to 3 px (first try was +8 px: the intermediates stood too tall).
- `SCRATCH/p_right4.jpg` + edge: RIGHT outline 4 to 5 px further out than the photo on both plateaus (the right
  photo's tyre is about 4 mm smaller than the left's; the shared radius is their mean).
- `SCRATCH/p_rear5.jpg`, `p_lr5.jpg`, `p_rr5.jpg`: rear, rear-left and rear-right three-quarter pairs.
- `SCRATCH/r5/render_cu_832.png` beside 475832, `SCRATCH/r5/render_cu_dr13.png` beside DR13.

### Still different, and why
- In the REAR photo the rows stand 66.5 px apart near the tyre's rear-most point (rows 1527..1931, cols 1980..2020);
  the model through the same camera puts them 70 px apart. The side scans fix the row count at 46 (angles do not
  depend on scale), so the REAR camera's scale at the rear tyre is about 6 % high: by the same ratio the tyre would
  be about 97 mm wide instead of 91.5, and the front tyre shows the same 6 % in the FRONT photo. Not changed here
  (the shared width, swingarm faces and chain line were all measured through that camera): reported to the
  coordinator.
- lr34: the model's tyre and rim sit about 13 px left of the photo's (camera, not shape: rim and knobs move
  together).

## 2. Rear tyre sidewall

### Anatomy
- Raised marks, tops outward, reading clockwise seen from their own side: Pirelli's Scorpion emblem (a scorpion
  seen from above, about 16 mm), SCORPION MX32, MID SOFT in a box, the PIRELLI word (long P) in a frame, the size
  code 100/90-19 57M NHS, a small PIRELLI box, a rotation arrow.
- The rim line (a fine rib just above the rim flange); vent hairs in a row under the shoulder knobs.
- Mould parting line: not seen in any photo at this scale; not modelled.

### References
- LEFT and RIGHT studio photos unwrapped about the rear axle (`unwrap.py`, then `uwcmp.py`: photo above model):
  LEFT: SCORPION MX32 84..160 deg (caps 16 mm, baseline r 266.5), size code 272..337.5 deg (caps 11.5 mm, baseline
  r 259); RIGHT: SCORPION MX from 95 deg down to 27 (it reads the other way round on the right wall), emblem at
  94..97 deg, a small box at 138..148 deg.
- DR13: the emblem (scorpion) beside SCORPION, the PIRELLI word near the rim in a raised frame, the long P, vent
  hairs as short dark ticks under the knobs.
- Pirelli's side view (web/pirelli-mx32ms-wheel-side): the order of the marks round the wall.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| SCORPION MX32 | 84..160 deg left, 91..15 deg right, caps 16 mm at r 266.5 | LEFT / RIGHT unwraps |
| Size code | 272..337.5 deg left, caps 11.5 mm at r 259 | LEFT unwrap |
| Emblem | 78 deg left, 97 deg right, 16 mm | RIGHT unwrap; DR13 |
| MID SOFT box, PIRELLI word, small box, arrow | offsets from the emblem as in Pirelli's side view | EST (Pirelli picture; LEFT shows a faint mark where the PIRELLI word falls) |
| Mark height | 0.8 mm proud, 0.3 mm sunk | EST |
| Rim line | rib 1.2 x 0.6 mm, 4 mm above the flange | EST (DR13 shows the line) |
| Vent hairs | one a pitch at r 288.5 | DR13 |

### What was built
`_text_polys` (DejaVu Sans Bold Oblique outlines, bundled with matplotlib), `_raised` (any even-odd outline set
raised from a surface: Delaunay top, walls facing out), `_arc_map` (text on an arc of the sidewall), `_emblem`,
`sidewall()` with `REAR_WALL`. About 47k vertices for both walls.

### Checks
- `SCRATCH/uw_sw3.png` (LEFT, 60..345 deg) and `SCRATCH/uw_sw4.png` (RIGHT, 0..150 deg): photo unwrap above the
  model's; the text spans and heights agree to about 2 deg and 1 mm.
- `SCRATCH/r7/render_cu_size.png`, `render_cu_emb.png`: close-ups (size code upside down at the bottom as on a real
  tyre; emblem before SCORPION as in DR13).

### Still different, and why
- Pirelli's own letter shapes (a custom heavy italic) are not available: DejaVu Sans Bold Oblique is a near
  substitute; the long P is drawn as a bar over the word.
- The MID SOFT box, the big PIRELLI word, the small box and the arrow sit where Pirelli's layout puts them (hidden
  or too faint in Honda's photos to place better).

## 3. Front tyre tread and sidewall (Pirelli Scorpion MX32 Mid Soft 80/100-21)

### Anatomy
- 41 rows. Per row: a centre knob split by a V slit (like the rear's), its trailing edge rising toward the slit
  (arrow-shaped halves); a shoulder knob each side in the same row; half a pitch on, an arrowhead knob each side
  pointing out with a V notch in its inner side. Drafted walls, rounded edges, root fillets, vent hairs.
- Sidewall: emblem, SCORPION MX32, MID SOFT box, PIRELLI word, size code "80/100-21 M/C 51M MST", small box,
  arrow, rim line, vent hairs (as the rear).

### References
- LEFT / RIGHT polar scans about the front axle (`SCRATCH/scan_front.png`): tall plateaus r 359 every 8.78 deg
  (41 rows), 3.8 deg wide; low plateaus r 354 half a pitch on; floor 347..348.
- FRONT studio photo rows 1380..1560 cols 1930..2070 zoomed (`SCRATCH/front_mid.jpg`): the centre pair, the
  shoulder knobs in the row, the arrowheads between rows.
- LEFT / RIGHT unwraps of the front sidewall (`SCRATCH/uw_front.png`, `uw_fsw.png`, `uw_f.png`).
- 475831: "80/100" in large letters beside the rim; Pirelli's flat view of the front tread (web/).

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Rows | 41 | side scans |
| Centre knob | 22 mm long, 40 mm across at the root (38 at the top), slit 3.7 mm at the top, V 2.5 mm | FRONT cols 1969..2030; scan plateau 3.8 deg |
| Shoulder knob | y 30..44 mm, 17 mm long | FRONT cols 1930..1952 |
| Arrowhead knob | 22 mm long, t 16.5..40 mm | FRONT zoom, pair p_ff2 |
| Tip envelope | R - 11 mm (t / 31.5 mm)^2 | `edge.py` LEFT and RIGHT |
| Size code | 267..340 deg left, caps 12.5 mm at r 293 | LEFT unwrap (475831 reads about 14 mm by the nipples' size) |
| SCORPION MX32 | 69..156 deg left, 100..13 deg right, caps 17 mm | LEFT / RIGHT unwraps |

### Checks
- `SCRATCH/p_fl2.jpg.d/edge.png` and `p_fr2.jpg.d/edge.png`: LEFT and RIGHT outlines, model 2 to 3 px outside the
  photo's on the tall plateaus (both photos alike: the shared radius), low plateaus within 2 px, rows in phase.
- `SCRATCH/p_ff3.jpg`: FRONT pair (tread from ahead). `SCRATCH/r10/render_cu_831.png` beside 475831.
- `SCRATCH/uw_fsw.png`: RIGHT sidewall unwrap, photo above model (MX32 in place, emblem moved to 105 deg after it).

### Still different, and why
- The rows in the FRONT photo stand about 6 % closer than the model's through the front camera: the same scale
  question as the rear (section 1), reported.
- 475831 shows the size code on another part of the wall: the wheel turns between photos; the studio photos place
  the marks.

## 4. Rims (D.I.D DirtStar, black anodised, 21 x 1.60 and 19 x 1.85)

### Anatomy
- Section: flat inner face (the spoke bed, nipples come through it), rounded corner, flat side band (the decals'
  ground), rounded flange lip, bead seats on the WM contour with a small hump, drop-centre well (hidden by the tyre).
- Decals once on each side of each rim: white "D.I.D" (bold slab-serif block letters) and "DirtStar" (outlined
  italic small caps, a star in the A), tops toward the tyre, reading clockwise seen from that side.
- Dark print "D.I.D JAPAN 76-08 10" and the size (475831: black on the black band).
- Finish: black anodised aluminium (satin; a dielectric film, so a plain, not metallic, gloss).

### References
- DR13 (decals, lip, band, nipple seats); 475831 (dark print); LEFT / RIGHT unwraps (decal places, both rims);
  LEFT pairs `SCRATCH/p_rim4.jpg`, `p_rim6.jpg`, RIGHT `p_rim5.jpg`.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Bead seat diameter, width | 21 x 1.60 in, 19 x 1.85 in | SPEC (test_rims) |
| Inner face radius | 256 front, 229 rear | LEFT / RIGHT radial scans (unchanged) |
| Flange top | rb + 11 / 10.5 mm | SPEC WM contour (unchanged) |
| Flange thickness, band plane | 3.5 mm: rim 54 mm over the bands (rear), 48 (front) | EST |
| Decal place | 258..286 deg rear, 260..288 front, both sides (right side reads back down) | LEFT / RIGHT unwraps |
| Decal size | letters 12 mm (D.I.D squeezed to 2.7 : 1), DirtStar caps 11 / 8.5 mm, 117 mm end to end | LEFT pair: letters 70 % of the band; DR13 |
| Texture | strip 400 x 25 mm, 4096 x 256 px (10 px a mm) | painted by `rim_texture()` (`python3 detail_wheels.py`) |

### What was built
`rim_profile` (new section), `_rim` (band faces inside the decal strip get `rim_print_r` / `rim_print_f` and their
own UVs), `rim_texture` (PIL, fonts bundled with matplotlib) -> `textures/stock/rim_rear.png`, `rim_front.png`;
the `rim` material overridden to a plain satin black (no other module uses it).

### Checks
- `SCRATCH/p_rim6.jpg`: LEFT pair at the rear decal (upside down at the bottom, DirtStar left of D.I.D, as the
  photo). `SCRATCH/r13/render_cu_dec.png`: close-up (decal and the tyre's size code both upside down there).
  (One wrong turn on the way: a v flip from a misread thumbnail mirrored the letters; the close-up settled it.)

### Still different, and why
- The rim joint (a weld line across the band) is not visible in any photo: not modelled.
- D.I.D's own letter shapes are approximated with DejaVu Serif Bold, squeezed.

## 5. Spokes and nipples

### Anatomy
- Count and lacing per wheel; each spoke: round head on the far face of the hub flange, J-bend through the flange
  (rounded), straight spoke, a few mm of rolled thread, then the nipple: hex flats with a chamfered end, a round
  collar, a raised eyelet round the hole on the rim's inner face.

### References and numbers
- Both side photos, the rims' inner ring unwrapped (r_in - 9..20 mm, plane y 0; `SCRATCH/uw_stems.png`), nipples
  found as dark comb teeth on white and fitted with a comb of n teeth (vector strength):
  - front: n 36 fits (0.67 / 0.71), phase 8.3 deg mod 10, rms 1.4..1.6 deg. The model's rim holes (hub holes at
    18.5 + k 20, three-cross 60 deg) land at 8.5 mod 10: unchanged.
  - rear: n 36 does not fit (0.16 / 0.04); n 32 does (0.58 / 0.43); 17 nipples over 179 deg in the LEFT photo's clear
    arc, 19 over 200 deg in the RIGHT: the rear wheel has 32 spokes (it was 36, EST). Rim holes at 9.0 + k 11.25
    deg, three-cross = 3 x 720 / 32 = 67.5 deg. The uneven gaps (about 10 and 13.5 deg) come from the nipples
    leaning along their spokes (leading and trailing alternate).
- Nipple: 6 mm across the flats, 8.5 mm of hex, 4 mm round collar, chamfered end; eyelet 8.4 mm across, 0.6 mm
  proud; 3 mm of thread at 0.8 mm pitch beyond the nipple: EST from DR13 (nipple flats against the rim and spokes).
- Spoke 3.8 mm (unchanged, EST), head 6.6 mm across, 1.8 mm thick (EST).

### Checks
- `SCRATCH/uw_sp1.png`: LEFT photo inner ring (30..330 deg) above the model's: every nipple within about 0.6 deg,
  valve and rim lock in place.
- `SCRATCH/r14/render_cu_nip.png` beside DR13 (`SCRATCH/r14.jpg`): nipple proportions corrected after this look
  (collar a third, hex two thirds).

### Still different
- The spokes are straight-gauge 3.8 mm (real ones may be butted, thicker at the hub end: not measurable here).
- A small dark lump sits on the rear rim's inner face at 172 deg in the LEFT photo (8 mm); not identified, not
  modelled.

## 6. Rim locks and valves

### References and numbers
- Same unwraps: rear valve (black stem with a domed cap) at 84.8 deg, rear rim lock (grey threaded stud) at 308.2
  deg; front valve 53.8 deg, front rim lock 252.5 deg (both photos agree). The model had them at 115 / 295 (rear)
  and 245 / 65 (front: valve and lock swapped).
- DR13: rim lock = washer, hex nut on a flange, the stud's thread showing past the nut.
- Built: M8 stud with 10 mm of 1.25 mm-pitch thread (rings), 16 mm washer, 12 mm flange nut; TR4 valve: knurled
  nut 11.6 mm, stem 7.8 mm, black cap with a domed end (sizes EST, standard parts).

### Checks
- `SCRATCH/uw_sp1.png` (places), `SCRATCH/r14/render_cu_lock.png` beside DR13.

### Still different
- The valve's own thread and the cap's knurling are not modelled (too fine to see in any photo).

## 7. Rear hub (partly)

### Anatomy
- Cast barrel with two spoke flanges, the sprocket flange (six lobes under the bolts) and the disc flange (four
  lobes), seals and collars each side; seen in the LEFT photo through the sprocket's bore: a dark grey casting with
  twelve tear-shaped radial ribs on its end face.

### References and numbers
- LEFT photo rectified onto the sprocket plane (`SCRATCH/spr_plan.png`, 0.25 mm a px) and unwrapped
  (`SCRATCH/spr_polar.png`). Colour: hub end RGB 96 / 99 / 102 against the bare sprocket's 150 / 153 / 157, so the
  hub is a darker cast finish (`hub_cast`, both hub lathe and its flanges).
- Ribs: twelve, r 36..54.5 mm, 3 mm wide inside, 8 mm outside, 2.6 mm high (EST from the photo's bumps).

### Checks
- `SCRATCH/p_spr1.jpg` (LEFT pair, the box of the coordinator's example).

### Round 2 (coordinator's review: "light, high-contrast tear marks on a dark disc; the photo shows a dark cast hub
with subtle ribs and a lighter machined ring")
- Ribs lowered to 1.3 mm with 40 deg walls and a 1 mm round (subtle bumps); the cast finish made diffuse (metal
  0.6, rough 0.62) and darker (82 / 84 / 88, after `SCRATCH/p_spr3.jpg` read lighter than the photo); the end face's
  outer chamfer and the sprocket spigot (r 56..60.5 mm) are `hub_machined`, the lighter turned ring of the photo.

### Not done
- Spoke-flange hole chamfers, the barrel's own casting shape (hidden by spokes and discs in every photo), the
  seals' lips.

## 8. Rear sprocket 50T

### Anatomy
- 50 teeth on the #520 pitch circle, chamfered tips; a bore ring with six bolt bosses; a truss of straight struts:
  six big windows between the bolts (standing on the bore ring, narrowing outward) and six smaller ones above the
  bolts (hanging from the tooth ring, narrowing inward); six socket-head bolts with nuts behind.

### References and numbers
- LEFT photo unwrapped about the axle on the sprocket plane (`SCRATCH/spr_polar.png`): window A between bolts from
  r 74 (38 deg wide) to r 96 (20 deg); window B above each bolt from r 108.5 (25 deg) to r 90.5 (11 deg). The bolt
  heads fit a circle 6.4 mm off the model's axle (x -2.9, z +5.7 mm on the sprocket plane, r 78): the radii are
  read from that centre. `SCRATCH/spr_overlay.png`: the model's windows drawn on the rectified photo, every window
  in place.
- The old model's slots over the bolts and three 7 mm holes between them are not in the photo: removed.
- Teeth: the top 3 mm taper to 55 % of the 5.8 mm width (EST, the usual chamfer of an ANSI #520 sprocket).
- Finish: bare aluminium, RGB 150..157 in the photo (material darkened from 170, which rendered white).

### Checks
- `SCRATCH/spr_overlay.png`; `SCRATCH/p_spr1.jpg` (LEFT pair).

### Still different, and why
- The photo's sprocket sits 6.4 mm from the model's axle (above): the model keeps the shared axle (`parts.RA`);
  reported.
- Stamped marks (tooth count, part number) are not visible in any photo: not modelled.
- Round 2: the twelve windows now have a 0.7 mm 45 deg chamfer on both faces (`_plate(..., chamfer=)`), the
  bright edge the LEFT photo shows round each window (`SCRATCH/p_spr3.jpg`).

## 9. Chain, D.I.D 520

### Anatomy
- 112 links (path from the LEFT photo, unchanged): outer and inner plates, figure-of-eight with round ends and a
  waist; pins riveted, their heads a rim with a dark peening dimple; rollers between the inner plates. Plain grey
  steel, no O-rings showing between the plates (the photo shows the plates touching).

### References and numbers
- LEFT pair zoom (`SCRATCH/chainz.jpg`: photo, old model, 475832): grey plates, figure-of-eight outlines, pin heads
  as rings with dark centres; the old model had dark plates and white pin dots (the opposite).
- #520: pitch 15.875 mm, roller 10.16 mm, pin 5.2 mm (unchanged, SPEC); plate height 15 mm, waist 0.8 of it
  (ANSI #50 / 520 plate proportions; EST for the waist), inner and outer plates alike.

### What was built
`_plate_outline` (9 points on each end arc, 3 on each waist), `_chain` rewritten for any outline size, 10-sided pins
with dimpled heads, materials `chain` (grey steel) and `chain_pin`.

### Checks
- `SCRATCH/chainz2.jpg`: LEFT photo against the model, same camera, the top run over the sprocket.

### Still different
- The connecting link (clip or riveted) cannot be found in any photo: not modelled.
- D.I.D's printed plate marks are too small to read in any photo: not modelled.

## 10. Rear disc, 240 mm wave disc (round 2)

### Anatomy
- Eight petals round the edge (flat arc, steep drop, flat bottom, ramp back), the braking band r 89.5..120 with
  three staggered rows of drilled holes (chamfered), four arms down to bolt bosses, four socket-head bolts.

### References and numbers
- RIGHT photo rectified onto the disc plane (y -0.070) and unwrapped about the disc's own centre (`SCRATCH/
  disc_polar_c.png`): the four bolt heads fit a circle of r 72.1 centred 8.4 mm above the model's axle (x -0.4, z
  +8.4 mm: the hub-parts offset the coordinator also found; the model keeps RA). Edge traced per degree
  (`SCRATCH/disc_edge.png`), the model's edge fitted to it (`SCRATCH/disc_fit.png`): petals start at 63.5 + 45 k
  deg, plateau 21 deg at r 120 (SPEC 240 mm), drop 4.5 deg to r 109.5, 6 deg flat, 13.5 deg ramp; median
  |model - photo| 1.1 mm (the trace is cut by spokes in places). The old outline (four 15 mm scallops, 28 ripples)
  is not in the photo.
- Inner edge: r 89.5 between the bolts, arms 15 deg wide at r 80, 30 deg at the band, bosses to r 63; bolts on r 71
  at 86 + 90 k deg (the photo: 84, 179, 263, 339 about its own centre).
- Holes: the old three rows of 28 (6 mm) kept, now 12-sided with a 0.4 mm chamfer; their exact places not mapped.

### Checks
- `SCRATCH/disc_plan2_s.png` (model outline on the rectified photo), `SCRATCH/p_disc1.jpg` (RIGHT pair).

### Still different
- The hole pattern is the old one (rows of 28), not hole-for-hole the photo's.

## 11. Rear caliper (partly)

### Done
- The stock black caliper guard (RIGHT and rr34 photos, `SCRATCH/cal_ref.jpg`): a skeletal triangle over the
  caliper's outer face with a triangular window and two black socket bolts; corners cast onto its plane (GUARD).

### Not done, and what the check shows (`SCRATCH/p_cal1.jpg`, RIGHT pair)
- The bracket is a broad silver plate outboard of the disc reaching up to the caliper: the photo shows the disc's
  holes there, so the real bracket is a slimmer arm, lower and mostly behind the swingarm.
- The caliper sits about 15 deg lower in the photo (the guard's window, over the piston, at about 50 deg from the
  axle, not 65) and the guard should cover it; the hose arrives level from the front with a black clamp on the
  banjo. Pad pin with its plug, the bronze-coloured plug and the bleed nipple's cap are not checked.
- These need the caliper moved and the bracket rebuilt, then an audit against the swingarm (detail_chassis), which
  did not fit in this pass.

### Round 3 (rebuilt; check images in `SCRATCH3/` = `.../scratchpad/agents/micro/wheels3/`)
Anatomy (fiche K95CF1700 for the counts): bracket 7 (axle eye, slim cast arm, bore for the slide pin, the bracket's
own pin), pad retainer 4 (inside, not seen), caliper body 6 (outboard half round the piston housing, bridge over the
disc's edge, inboard finger), two pads 1 (steel backing with an ear on the pad pin, sintered lining), pad pin 8 under
its hex plug, bleed screw 11 with rubber cap 12, slide pin 5 with its boot 16, the bracket's pin under the ribbed boot
15, banjo with two sealing washers and its bolt, the hose with a black clamp ring and a crimped black sleeve, guard 10
on two black socket bolts 17. Finish: body dark cast aluminium, the piston housing's end lighter (turned), bronze pad
ears, black guard, sleeve and boots.

References: RIGHT 7x crop 1044..1192 x 1462..1560 contrast-stretched (`gz_r2.png`), 6x crops `gz_r1.jpg`,
`gz_hose2.jpg`, 2.4x `gz_hose.jpg`; rr34 7x crop 1290..1440 x 1410..1540 (`gz_rr1.jpg`); REAR 7x crop 2070..2200 x
1350..1470 (`gz_rear1.jpg`); outdoor right side 476001 crop 1200..1560 x 1640..1960 (`o476_cal.jpg`); fiche
K95CF1700 (`fiche_cal.png`).

Numbers (RIGHT pixel, cast on its plane y, then carried from the photo's hub to the model's by a turn about the
swingarm pivot: the RIGHT disc bolt circle puts the photo's hub 8.4 mm above parts.RA; y from the REAR photo at
1.435 px a mm about the disc):
| Item | Place (x, z about RA, mm) | Source |
|---|---|---|
| Piston housing end | 75, 82 (47.5 deg, r 111), r 20.5 | RIGHT (1115, 1519): lower arc through (1097, 1540), (1115, 1545.5), (1133, 1537) |
| Slide pin 5 head | 111, 79 (r 137, outside the disc) | RIGHT (1160.8, 1524.2), 23 mm round |
| Bracket pin and boot 15 | 55, 59, y -0.096..-0.122 | RIGHT (1086.7, 1550); REAR cylinder u 2141..2180, ribbed end 2169..2179 |
| Pad pin and plug | 67, 108; pin y -0.052..-0.100, plug to -0.109 | RIGHT hex (1105, 1484); REAR bar v 1360..1369 u 2081..2161 |
| Pads | backing at y -0.058..-0.062 and -0.078..-0.082 | REAR u 2083..2089 and 2114..2120 (bronze ears on top) |
| Bleed screw and cap | 84, 108 to 91, 118 | RIGHT (1128, 1483) to (1136, 1472) |
| Banjo | 106, 99 | RIGHT (1155, 1497), under the guard's lower bar |
| Guard bolts | 124, 117 and 38, 75 | RIGHT (1176.7, 1475.8) and (1063.3, 1530.8) |
| Guard | outline and two windows: 26 + 5 + 9 RIGHT pixels, y -0.118..-0.131, front end folded in 6 mm | RIGHT pair p_cal1; rr34; REAR black box to u 2195 |
| Hose | 9 mm, level from the banjo, sleeve 11 mm x 27 mm, onto the arm's top | RIGHT gz_hose2 u 1185..1210; gz_hose |
| Bracket | eye y -0.0935..-0.0858 (between collar and arm), arm rib inboard to y -0.079 | REAR arm u 2115..2137; outline EST round the pins |

Built: `_slab` (any outline extruded with every edge rounded, holes allowed, caps without flat slivers via
`_off_hull`), `_turned` (closed capped lathe), `_ribbed` (boots), `caliper_points()` (the pixels above through
`_cal_px`), `rear_brake()` and `_caliper_guard()` rewritten. The hose is held 1 mm over the swingarm's top
(`ARM_TOP`, ray cast on the built swingarm) and tapers to the pedal part's 4.2 mm at `HOSE_END`. 23.8k vertices.

Checks: RIGHT `p_cal1.jpg` (first build: guard far too broad), `p_cal2.jpg`, `p_cal4.jpg`; rr34 `p_calrr1.jpg`,
`p_calrr3.jpg`, `p_calrr4.jpg`; REAR `p_calb1.jpg`, `p_calb3.jpg`, `p_calb4.jpg`; all three in `p_cal4_all.jpg`.
Audit `aud4.log`: no clash with the swingarm, wheel or disc; brake_pedal x rear_brake 3.9 mm at the hose joint (below).

Still different, and why:
- The whole assembly sits about 8 mm lower than in the photos: the hub parts are built about parts.RA (decided).
- The body's cast form (where it is not seen past the guard) and the bracket's outline are EST round measured
  points; the guard's windows are read from a dark-on-dark region (2 px uncertain).
- REAR: the photo's guard box ends 12 px further out (8 mm); the REAR camera reads distances from the centre plane
  about 6 % large (section 1), which is most of it.
- The hose joint: the pedal part's hose (detail_chassis) comes down to `HOSE_END` and runs on 20 mm forward past it
  to (0.468, -0.088, 0.513); this hose turns back along the arm there, so the two overlap 3.9 mm at the joint (a
  joint, not a clash through a solid). Fix in detail_chassis: end its hose at `HOSE_END`, its last control point
  behind and below it (about (0.440, -0.100, 0.497)).
- The hose guide clip on the swingarm's top (RIGHT u 1385..1425, v 1445..1475) is not modelled (on the chassis
  agent's swingarm).

## 12. Front hub, front disc 260 mm and front spokes: not started
(The front spokes and nipples got the component 5 work: count 36 confirmed, new nipples, eyelets and threads; the
front valve and rim lock moved to their measured places. The front hub keeps its old light finish and the front
disc its old outline.)
