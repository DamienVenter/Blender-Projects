# Ledger: jersey and pant (Leatt Moto 5.5 UltraWeld jersey, Moto 5.5 I.K.S pant, Tiger Pink, 2026)

Module `scripts/rider/kit.py` (`python3 kit.py BODY.npz OUT.npz`), tests `scripts/rider/test_kit_rider.py`.
Identification and every Leatt source: `research/rider-gear-leatt.md` sections 1 and 2. Tags: BODY (measured on
body.npz), CHART (Leatt size charts, `reference/leatt-gear/sizing/`), PHOTO (Leatt's photos or his), EST (estimate).

## Sizes

| What | Value | Source |
|---|---|---|
| His chest | 100.8 cm (convex girth at nipple height, z 1.36) | BODY |
| His natural waist | 80.5 cm (narrowest, z 1.18) | BODY |
| His waist at belt height | 88.4 cm (z 1.06, where Leatt's chart figure draws the tape) | BODY, CHART figure |
| His girth under the modelled waistband | 84.4 cm (band tilted, front 1.09, back 1.15) | BODY (test) |
| His inseam | 87.2 cm (crotch height) | BODY |
| His arm length (back neck, shoulder, elbow, wrist) | about 80 cm | BODY |
| Jersey | **L** (5026000202): arm 80-82 and height 178-182 fit; chest 106-112 is above his 101, which alone says S/M. L keeps the body and sleeves long enough for 1.85 m; worn with 5 to 11 cm of ease | CHART |
| Jersey girth at his chest | 112 cm (top of L: a race fit is cut to stretch to it) | CHART; test 112 +- 3 |
| Pant | **L / US34 / EU52** (5026000323): waist 83-88 (his 84.4 under the band, where the pant is worn; 88.4 at belt height). Height 178-182 and inseam 81-83 are short of his 185 and 87: the leg is cut to his body here and the cuff ends inside the boot, so nothing shows. (First pass said XL from the belt-height girth with a lower band; the band moved up to Leatt's rise, see Cut lines) | CHART |

## Cut lines

| What | Value | Source |
|---|---|---|
| Neckline ("no-collar") | z 1.515 at the front (jugular notch 1.52), 1.575 at the sides (neck root), 1.565 at the back (below C7 at 1.59), smooth in the angle round the neck | BODY, PHOTO (flat front, collar close-up) |
| Sleeve end | 12 mm up the forearm from the wrist joint: the glove's short cuff covers it | BODY, PHOTO (front on-model) |
| Jersey hem | straight, z 0.97: tucked, 12 cm inside the pant at the front | PHOTO (his 07: waistband and strap visible, jersey bloused over) |
| Pant top | z 1.09 at the front, 1.15 at the back (raised rear yoke): Leatt's front on-model photo has a rise of 499 px waist to crotch, 22 cm at its 2200 px/m; a first pass at 1.05 gave 18 cm | PHOTO (front and back on-model), BODY |
| Pant cuff | **z 0.355, level**: inside the Leatt 6.5's gaiter (its top 400 mm at the front, 423 at the back; white shell top 360 to 409), in the 330 to 380 band the boots build gives. Checked in renders of both riding poses with boots.npz: no cuff outside the boot | boots build (coordinator), renders |

## Ease (clearance of the cloth from the skin)

| Where | Value | Source |
|---|---|---|
| Jersey chest | 1.8 cm mean = (112 - 100.8) / 2 pi; less under the arms (x 0.5), more front and back so the girth holds | CHART, BODY |
| Jersey fall | 0.35 m in per m down from the chest and shoulder blades; 0.9 from the chest up to the collarbones | PHOTO (Leatt on-model), EST |
| Jersey shoulders, neckline | 3 mm | PHOTO (fabric on the shoulders in every view) |
| Sleeves | 14 mm upper arm and elbow, closing to 4 mm at the cuff | PHOTO (close cuffs) |
| Jersey blouse over the waistband | 6 mm, then held 2.5 to 4 mm off the skin under the pant | PHOTO 07 |
| Pant waistband | 11 mm: tucked jersey 2.5 mm, its cloth, a 4 mm band with its facing | EST (Waistlock webbing in the band) |
| Pant seat | 12 mm over the convex hull (the seat bridges the gluteal fold) | EST |
| Pant thigh | 16 mm; the leg then falls nearly straight (0.08 m per m) to the knee | PHOTO (Leatt on-model: straight legs) |
| Pant knee | 20 mm at the front (brace shell room), pre-curved panel 10 mm forward | EST, PHOTO (front and side views) |
| Pant calf | 12 mm, closing to 7 mm at the cuff (goes inside the boot) | EST |

## Construction modelled

| Part | Value | Source |
|---|---|---|
| Edges | turned in: jersey 1.5 mm thick, facings 12 mm (neck), 20 mm (cuffs), 15 mm (hem); pant cuffs 2 mm / 25 mm; waistband 4 mm / 40 mm | EST, PHOTO (collar close-up, waistband close-up) |
| Fly | YKK Vislon zip under a placket: 36 mm wide, 170 mm long, 2 mm proud, centre 10 mm to his right | PHOTO (front close-up), Leatt features |
| I.K.S panels | inner knee, 20 cm above to 13 cm below the knee joint, inner 150 deg; vertices snapped onto the seam | PHOTO (front flat, inner-knee close-up) |
| Waistlock buckle | 26 x 33 x 8 mm, on a textile backing, low on his right hip (x -0.150) 22 mm under the waist top | PHOTO (front on-model 1920 px at 0.47 mm/px from the hip width) |
| Waistlock strap | 16 mm wide, 2.5 mm thick, teeth every 5 mm (0.32 strap widths), 1.2 mm high, sloping down across the front | PHOTO (Tech1 close-up), EST (tooth height) |
| Strap tab | 61 x 47 x 1.5 mm, just right of the fly (x -0.020), 47 mm under the waist top | PHOTO |

## Method notes
- Body region cut along smooth surfaces, boundary slid onto them; subdivided once; draped by curvature flow with
  collision, plus "envelopes" (per-slice convex hulls of the trunk and each leg, hung with a fall rate) for the
  loose parts; openings projected back onto their cut lines and held for the last relax.
- Seams run straight: the vertices beside each pattern seam (raglan, side, sleeve split, centre, leg sides) are
  slid onto the seam's plane before the charts are cut (the face edges' stair-steps showed in the seam relief).
- hide_body: every skin vertex of the cut patch except its edge ring (the cloth's edge was slid past that ring, so
  the mask's hole ends under the cloth). Keeping one more ring visible left skin behind the knee (0.44 m, above the
  boot) poking through the pant in the seated test pose.
- Weights: nearest skin vertex, smoothed (jersey 6 passes, pant 2 so the cloth follows the kneecap); the tucked
  jersey takes the pant's weights so the two move together; facings copy their edge vertex.
- Riding test poses (test file): hips 60 and knees 60 deg, ankles 30, head 20 down, arms forward 45 with elbows 60;
  and seated (hips and knees 90). Result: no visible skin through the cloth away from the openings; the only
  masked skin standing more than 6 cm from the cloth is 4 to 7 vertices at the kneecap (LBS).

## Graphics (component 3)

Textures `textures/rider/jersey_color.png`, `jersey_normal.png`, `pants_color.png`, `pants_normal.png`, 2048 px,
0.8 mm per texel (both garments at one texel density: 0.61 texture units per metre for the jersey).

| What | How, numbers | Source |
|---|---|---|
| UV charts | one per pattern piece: jersey front, back (split at the side seam y -0.005), each sleeve's front and back half (split by the plane through each arm segment's axis), raglan seam from (0.088, -0.072, 1.522) front and (0.078, 0.052, 1.556) back to the armpit (0.178, -0.005, 1.362); pant legs' front and back halves (leg frame), left and right; least-squares conformal maps, shelf packed | PHOTO (raglan seam in the flat front and collar close-up), BODY |
| Jersey front and back | Leatt's on-model photos (1600 px) projected: front neckline at (800, 290), 1513 px/m across, rows from the neckline to the pant top (1130); back neckline (790, 258), 1580 px/m, pant top 1040. Photos median-filtered 5 px (takes out the micro-mesh dots), studio background and the helmet, neck and hands masked and filled from the nearest garment pixel | PHOTO |
| Sleeves | each half from its view: along the arm from the shoulder point to the cuff end, across normalised to the photo arm's half width (68, 72, 60, 48 px at 0, 0.2, 0.6, 1.0 of the arm: 0.85 of the silhouette so its soft edge is never sampled); the two halves blended over the sleeve's top line; the raglan part over the shoulder takes the trunk's views. Round 3: the front half from Leatt US's front flat, his left sleeve's back from the back 3/4 flat; the whole sleeve printed as one (section "Round 3") | PHOTO |
| Pant | Leatt US on-model front and back (1920 px, alpha): rows waist top (205 front, 190 back), crotch (first open row in the alpha), boot top (1670, 1650); across, each photo row's silhouette laid onto his pant's silhouette at the same height, leg by leg | PHOTO |
| Big LEATT, outer left thigh | printed flat from a canvas square to it: length 0.26 m, centre 0.19 m above the knee joint, reading up from the knee, letter tops to the front; round 3: turned 28 deg from the side toward the front (rounds 1 and 2: on the side line, where Leatt's front view would see it edge-on; it sees 60 px of it), the official wordmark (us.leatt.com's header logo) instead of the chest's trace | PHOTO (Leatt US front on-model rows 790 to 1260: 0.83 to 0.98 across the leg, centre 62 deg from the front; back flat; his 07 seated: reads knee to hip), official file |
| I.K.S panels in the print | black (0.085) inside the panel field, so the material seam and the print agree | PHOTO |
| Laser-cut holes | jersey 238 (Leatt's number): 50 on each upper sleeve front, 40 on each side panel, two rows of 29 across the lower back; pant 250: 60 on each front thigh, 25 each side of the rear yoke, 40 behind each knee. 1.8 mm holes, darkened and dented | Leatt features, PHOTO (fields' places) |
| Damien's additions | round 2 (2026-11-13): see the section "Damien's additions" below | |
| Relief (normal maps) | seams: 4 mm wide, 0.6 mm groove, stitch dents 3 mm off it (jersey raglan, side and underarm seams; pant centre, in-, outseams, I.K.S panels, rear yoke V z = 1.025 + 0.30 abs(x), waistband edge 40 mm down); folds: inner elbows, belly, shoulder blades (jersey), behind the knees and across the hips (pant) | PHOTO, EST |

## Damien's additions (round 2, 2026-11-13: an exact replica of his number, name and sponsors)

Damien: "Same with the number on my jersey and the sponsors on the front of my jersey"; "We got sponsors: BikeWise
(SA), Cycleworx Suspension, USN, Motul. Get the logos online and verify"; name DAMIEN. Measured on his photos turned
upright and enlarged (06 back; 09 and 08 chest, measured against Leatt's chest LEATT, which the model already
carries at known places; 07: nothing on the left side). Code: kit.py "graphics: Damien's additions".

| What | Value | Source |
|---|---|---|
| 114 glyphs | lifted from his plate art `textures/damien-v1/art/plate.png` (the three white glyph components, x 256-1497, y 635-1424; the bolt hole and small logo dropped), its black keyline where the 4 overlaps the second 1 and the slashes kept dark; italic lean tan 0.23 (13 deg) as on the plate | his bike art, PHOTO 06 (same glyphs) |
| 114 colours | white (246, 245, 250), outline dark purple-grey (34, 24, 44), 4.5 mm (0.024 of its height) | PHOTO 06 (glyph lilac-white, outline median (77, 50, 86) blurred, darker at its core) |
| 114 size | 0.300 m across with the outline on the flat back panel, so 0.196 m high (the plate's aspect 1.57) | PHOTO 06: 0.59 of his deltoid breadth as seen (410 / 700 px upright), 0.49 m (BODY: shoulder joints x 0.195 plus 5 cm) = 0.29 m, plus 3 % for the wrap |
| 114 place | centred on the spine; its top 0.37 of its height (73 mm along the back) under the back collar's centre: centre z 1.412, top about 1.51 | PHOTO 06 (collar 400, top 475, height 205 px upright) |
| Name | DAMIEN, Inter Display Black stretched to length and leaned 13 deg like the 114, white with a 2.2 mm dark outline; letters 29 mm with the outline (0.146 of the number's height); 0.89 number widths (0.267 m) long, centred over the number; its bottom 0.05 H over the number's top | Damien 2026-11-13 (spelling; "perfectly centered": 06's angle makes it look off-centre). Length: PHOTO 06 shows DAMI over 0.585 W (name 410-650 px, number 445-855 px, upright) in front of a fold of the jersey at the collar, EN beyond it; times the ink width of DAMIEN / DAMI in the font (1 / 0.658). Round 2 had taken DAMI for the whole name, over the left half. The typeface is not resolvable in 06: wide bold capitals with an outline |
| Leatt's back LEATT | erased from the projected back print (filled from the print round it): his name sits in its place and 06 shows no Leatt logo beside it | PHOTO 06, Leatt back on-model (logo at 478-648, 310-388 px) |
| How the back is printed | in "unrolled" back coordinates: arc length across each horizontal section from the spine and up each vertical section from z 1.45, on the jersey's back surface (as sublimation prints the flat panel): the 114's ends wrap the back (its normal turns 17 deg at x 0.10 and 44 deg at 0.15, z 1.33) and run on over the raglan seams without a break | BODY (jersey mesh) |
| Front layout | BikeWise above the LE of the chest LEATT (his right), Pirelli above the brain icon (his left); under the pink yoke and FIVE.FIVE, either side of the green centre chevron: USN with Motul under it (his right), Cycleworx (his left). Not a column on the side panel (round 1 misread 09) | PHOTO 09, 08 (upright crops, same layout in both) |
| Logos | the official files in `reference/sponsors/` (README: URLs, and each checked against 08 and 09: shape, colours, layout) | brands' own sites; Cycleworx Suspension's own Facebook page |
| Front sizes, places | centre (x, z) in the frame of Leatt's front photo (as the print) and width: BikeWise (-0.091, 1.447) 95 mm (logo plus a 4 % white margin, 1.75:1); Pirelli (0.102, 1.446) 80 x 24.7 mm (its own box, 3.24:1); USN (-0.063, 1.320) 80 mm with a 1.6 mm white contour; Motul (-0.057, 1.286) 64 x 17.5 mm (white on its red box, the SVG's viewBox); Cycleworx (0.064, 1.313) 77 mm with a 1.6 mm white contour | PHOTO 09 and 08: the LEATT fitted to each photo (affine, then a little perspective; outline overlays in the review), corners read on 7x upright crops and mapped back; the two photos disagree on widths by up to 30 % (each sees one side of his chest nearer), so the values are the geometric means of the two photos' local ratios (patch to letter height and to logo length) with the official aspect, and the places are the patches' edges next to the logo (BikeWise bottom 0.22 letter heights over the L, Pirelli bottom at the brain's top, its right edge at the brain's right; USN top 13 to 16 mm under FIVE.FIVE) |
| Front printing | on each patch's tangent plane at its centre (under 1 mm off over 5 cm of chest), so a patch keeps its size where the chest turns (35 deg at z 1.44) and runs on over the raglan seam (BikeWise and Pirelli touch it) | BODY |
| Print overlay | the jersey faces under the additions (747), copied 0.1 mm out with the jersey vertices' own weights; its UVs are the jersey's scaled and moved per island (never rotated: tangent frames and normal map agree), atlas `jersey_print_color.png` / `_normal.png` 2048 px at 0.10 mm (sponsors), 0.15 mm (name), 0.25 mm (114) per texel; the base round the graphics sampled from the jersey's own print and normal map at the same cloth point. 0.3 mm left a contact-shadow line at the island edges in renders; 0.1 mm does not | EST, renders |
| Not printed | a light band with dark lettering under Cycleworx in 08 (as wide as CWORX, 0.8 of its height; small in 09), not legible | PHOTO 08, 09; Damien 2026-11-13: the logos as printed are right, leave it off |

Patch sizes (BikeWise box, Pirelli patch) stay estimates: Damien 2026-11-13 "You estimate it".

Known limits (round 2; round 3 replaced the projected print by a flat one, see "Round 3"): the projected print
carried the photos' soft lighting; the side panels and the outer shins are seen at grazing angles by the front and
back photos.

## Round 3 (decision 52, 2026-11-15): a crisp print, true colours, his number and sponsors at 1:1

Code: kit.py "graphics: the clean flat print (decision 52)", tests in test_kit_rider.py. Checkpoint
`renders/checkpoints/2026-11-15_jersey3/`. Round 3b (below) replaced the sleeves' and side panels' zebra, the pant's
trace, FIVE.FIVE, the chevrons' faded tops and the lower back's holes; the rows here are round 3's.

### The print, element by element

| Element | How, numbers | Source |
|---|---|---|
| Colour reference | Leatt US's front flat (1920 px, evenly lit): each ink is the median of the brighter half of its class in a box (`INK_BOXES`): magenta (225, 11, 134), lime (174, 226, 35), teal (55, 196, 177), black (21, 21, 24), white (232, 227, 240). The NZ distributor's on-model photos show the same inks paler: (202, 30, 125), (198, 235, 75), (140, 211, 162), (34, 34, 34) | PHOTO |
| Ink map | the NZ photos (front, back, back 3/4 flat) onto the flat's inks: 3 x 3 plus offset, black onto black exactly, fitted in relative error to magenta and white (each weighing as 4 pairs) and 16 pairs along the stripes' gradient: the stripe/black profile down the centre of each front view from the chest LEATT (scaled by its 0.275 m), matched by correlation (0.97; the flat runs 1.205 times as long as the on-model jersey), the brighter half of the stripe pixels per band 0.10 to 0.40 m under the LEATT. Residual on the gradient: median 18, max 27 of 255. A map fitted to four boxes (round 3's first) had 28 and 93: its "teal" box is the hem on the flat but 20 cm higher on the on-model photo (the hem is tucked in), so the lower stripes went to R 0, B 208. The NZ back photo is brighter (its yoke magenta (230, 47, 149) against the front's (202, 30, 125), its shoulder LEATT clipped at 255): through the front's map its yoke read (255, 40, 157). Its own map (`back_map`): the front's refitted so its magenta (box 700, 560, 900, 720) and black (380, 480, 500, 640) land on the flat's, while its stripes (the 11 bands of 25 rows between rows 600 and 1000 that hold over 200 stripe pixels) keep what the front's map gives them (moved median 3, max 6 of 255): back yoke against front yoke in the texture (median of the magenta faces' colours) 28 to 11 of 255 (main 41) | PHOTO (both front views; the back view; his 06: his back's magenta as deep as his front's) |
| White elements | white = min channel less 0.6 chroma, over 0.55 (the grey stripes reach 0.47), smoothed over 0.4 mm, cut and anti-aliased over one texel (0.8 mm); white specks under 3 mm2 dropped (the photos' perforations: holes 2.5 mm2; FIVE.FIVE's letters are 15 to 20 mm2), on the sleeves under 20 mm2 (the piping's broken trace; the sleeve's LEATT and icon are 100 mm2 and more) | PHOTO |
| Zebra stripes, centre chevron | green light (G less 0.7 of R and B over it) cut half-way between the local dark and light levels in a 3 cm window (stripes 12 to 25 mm wide); where that span is under 0.25 there is no pattern (plain grounds, solid cuffs) and the cut is absolute (0.12 plus 0.15); islands and gaps under 0.4 cm2 dropped (the stripes' smallest tips are 1 cm2), on the sleeves under 1.5 cm2 | PHOTO NZ front and back on-model (trunk), Leatt US front flat (sleeve fronts), back views (sleeve backs), back 3/4 flat (side panels) |
| Ink colours | each ink a smooth field: stripes over 12 mm (the airbrush gradient lime to teal runs over 50 to 300 mm), the ground over 0.6 mm on the front (keeps the yoke's cut edge over the chest) and over 20 mm on the sleeves and the back (their magenta fades at every edge; at 0.6 mm the photos' fold shading stayed as grey blotches 2 to 5 cm across), wider fields (2, 6, 18 cm) where the photo saw nothing square on; every texel weighs cos^2 of its photo's view angle | PHOTO |
| Yoke | magenta ground fading to black over the shoulders and down the back: the ground field from the NZ front and back photos on the flat's inks; at the raglan seams the sleeve's ground is drawn to the trunk's (each seam point's step from the medians within 1 cm each side, averaged over 2 cm of seam, fading over 6 cm, on texels of that ink only): step 37 to 2 of 255 (median over the yoke's seam edges; main 2) | PHOTO (front flat: one ink over the seam) |
| Sleeves | each sleeve printed as one piece: unrolled about its arm (angle round the upper arm's or forearm's axis times the sleeve's median radius per cm along, wrapped 4 cm past the back line), traced and cut there, each texel read back from its own place. The step along the top line (a UV cut only) went from 51 (per-chart cuts, round 3's first) to 5 of 255 (main 0, a photo blend). His left sleeve carries Leatt's thin white line from the back LEATT down the arm to the icon at the elbow, and the forearm LEATT (back 3/4 flat) | PHOTO, BODY |
| FIVE.FIVE | the white trace (letters 15 to 20 mm2 survive the speck rule); at 0.8 mm per texel each letter is 4 to 5 texels high and reads as dots at 1:1 | PHOTO |
| Chest icon | Leatt's triangle printed from the official favicon (us.leatt.com, 100 px, upsampled 8 times and re-thresholded), 26.7 mm, centre (0.133, 1.423) in the front photo's frame: the geometric mean of the NZ photo's 27.7 mm (24.4 mm seen, times 1.137 where the chest turns) and the flat's 25.8 mm (37 px beside a 395 px LEATT); the trace had lost its 3 mm strokes | PHOTO, official file |
| Perforations | modelled holes as before (238 jersey, 250 pant; 1.8 mm, darkened), not printed | Leatt features |
| Cuffs | lime, solid: from the flat's sleeve fronts (the absolute cut keeps solid areas solid) | PHOTO |
| Pant panels | the black zebra over teal, lime and magenta: the stripes are the chroma; specks under 1.5 cm2 dropped, the ground over 3 mm, white edges only over 0.5 (the pant's teal is paler: up to 0.40), the shins' stripes coloured from themselves (weights at least 0.1, from 0.6 of the way into the stripe; they are seen at 60 to 80 deg); past 83 deg (the legs' outer sides) plain ground. The rows above the crotch take the whole pant: Leatt's back photo opens a 5 px gap at its centre 120 rows above the crotch, and round 2 took the first run there (the model's glove) | PHOTO Leatt US on-model pant |
| Thigh LEATT | the official wordmark, 0.26 m, 28 deg from the side toward the front (row "Big LEATT" above) | PHOTO, official file |

### Colours, measured (Standard view against Leatt's studio photos; daylight against his)

Each ink's core (median of the brighter half of its class in a box; the black of all of it), display sRGB, and
in brackets its ratio to the white beside it in linear light (R, G, B), which takes out the exposure. Renders: the
front (jf) and back (jb) studio views, Standard at -1.6 (nothing clips) or -1.0; daylight is AgX - Punchy -0.6.
Script: the checkpoint's 08 sheet.

| Ink | Leatt US flat | NZ on-model | main, Standard -1.6 | round 3, Standard -1.6 |
|---|---|---|---|---|
| magenta | 225, 11, 134 (0.93, 0.004, 0.27) | 202, 30, 125 (0.75, 0.017, 0.24) | 175, 58, 112 (0.72, 0.075, 0.25) | 209, 53, 127 (0.89, 0.050, 0.29) |
| lime | 174, 226, 35 (0.53, 0.99, 0.02) | 198, 235, 75 (0.71, 1.12, 0.08) | 146, 189, 80 (0.48, 0.90, 0.12) | 122, 184, 51 (0.27, 0.68, 0.04) |
| teal | 55, 196, 177 (0.05, 0.72, 0.51) | 140, 211, 162 (0.33, 0.87, 0.42) | 96, 157, 145 (0.20, 0.60, 0.44) | 94, 156, 147 (0.16, 0.47, 0.39) |
| black | 21, 21, 24 (0.009, 0.010, 0.010) | 34, 34, 34 (0.020) | 49, 49, 50 (0.051, 0.054, 0.049) | 45, 45, 47 (0.037, 0.037, 0.038) |
| back magenta (Standard -1.0) | | 230, 47, 149 (the NZ back photo; its white clips) | 221, 69, 152 (0.89, 0.074, 0.37) | 221, 56, 139 (0.89, 0.049, 0.30) |

- Magenta, front and back: green per white 0.075 to 0.050 (flat 0.004, his 09 0.005, his 06 0.014); the rest of
  the green is the cloth's sheen in the render (the texture's front yoke is 226, 14, 132; its back 231, 25, 140).
- Lime and teal: the render's boxes see the chest's chevrons and the stripes above the pant, the middle of the
  airbrushed gradient (lime to green to teal), while the flat's boxes are the chest's brightest lime and the hem's
  teal: these two rows are not like for like. The texture's stripes against the flat's at the same height (the
  gradient pairs): median 18, max 27 of 255; the texture's lime 166, 221, 18 (flat 174, 226, 35).
- Daylight (AgX - Punchy -0.6) against his photos: magenta 189, 85, 151 (0.80, 0.14, 0.43) round 3, 170, 75, 138
  (0.67, 0.11, 0.37) main, his 09 217, 8, 111 (1.03, 0.005, 0.22), his 08 175, 22, 72. The look lifts the
  magenta's green per white from 0.050 (Standard) to 0.14: the look's, not the kit's (not changed).

### His number and sponsors at 1:1

Cameras fitted to his photos 06, 09 and 08 by the print (symmetric chamfer between the posed model's projected
white print and the photo's white mask, a grid over azimuth, elevation and roll, then CMA; an anchor on the name's
centroid in 06 and the L of LEATT in 09 and 08, as a 180 deg turn fits the 114 as well): 06 f 1342 px, 0.90 px
residual; 09 f 2087 px, 2.43 px; 08 f 1590 px, 2.26 px. Windows of each photo are rendered through the same camera
turned onto the window, enlarged 4 times (06) and 8 times (09, 08), and turned upright: photo | main | round 3.

| What | Photo | Round 3 | Verdict |
|---|---|---|---|
| 114 box (06, 4x upright) | 414 x 278 px | 401 x 294 px | width within 3 %, height 6 % over |
| 1s' stems (4x) | 77, 58 px | 70, 51 px | within 2 photo px (06 is blurred over 1 to 2 px) |
| gaps 1-1, 1-4 (4x) | 29, 8 px | 24, 10 px | within 1.3 photo px |
| glyph centroids | | | within 1 px of the fit |
| the 4's counter (4x) | 39 px tall | 89 px | 06's 4 is crossed by a fold and smeared on its right by the shoulder: the plate art (the same glyphs) stays the source |
| DAMIEN | DAMI over the fold | the same | as round 2 |
| BikeWise (09, 08) | | centre +2, -17 mm; -8, -8 mm | long side within 4 to 7 % in both; short side +30 % in 09, -5 % in 08 (the model's chest faces each camera differently from his): kept |
| Pirelli | 74 mm (09), 108 to 112 mm (08) long | 80 mm; centre -12, -9; -11, -14 mm | the photos disagree: 80 mm kept. Its colours in 08 (red letters (143, 2, 38) on (245, 152, 58)) are the official red on yellow in daylight |
| USN | | -16, -35 mm; +20, +6 mm | the lower patches move in opposite directions in the two photos (his chest turned, the jersey pulled over the pant): not moved |
| Motul | hidden in 08 | -30, -40 mm (09) | as USN |
| Cycleworx | | -20, -18 mm; +24, -16 mm | as USN |
| chest icon | under Pirelli at its right | the same place; 09's camera does not see it on the model (the chest turns away sooner than his) | |

Offsets are round 3 minus the photo, along the photo's axes, at 3.69 (09) and 3.21 (08) mm per photo px.

### Not seen, estimated

- The lower back under the magenta fade: his 06 shows about 5 staggered rows of light dots there; Leatt's back
  on-model photo shows 2 rows about 13 mm apart near the pant, its back flat an upper field of 4 rows and a lower
  tail field of 4 rows (light: lit through). The model has 2 rows 60 mm apart (z 1.155 and 1.215). What shows
  through the holes (skin, a base layer) is Damien's to say: asked.
- The top two chevrons under FIVE.FIVE fade from black to lime in Leatt's print (an airbrushed end); the trace
  cuts them where they cross the cut level, so their tops are ragged. Keeping them as fades from the photo
  brought back the photo's mottle (tried, not kept).
- The sleeves' backs, the underarms and the pant's outer sides are seen at grazing angles by every photo: the
  sleeves' stripes there are the photos' shapes, smoothed (some read as soft grey bands on the black), and the
  pant's outer sides are plain black.
- AgX - Punchy (the daylight look) desaturates the magenta (render (189, 85, 151) against his 09's (217, 8, 111));
  the look is not the kit's.

## Round 3b (decision 52, 2026-11-15): the 1:1 review's six fixes

The coordinator's review of round 3 at 1:1 (JERSEY3b) kept the inks in the Standard view, the cut trunk print, the
logos, the 114 and DAMIEN, and the fitted cameras; the sleeves had regressed and six things needed finishing. Each
fix has a test in test_kit_rider.py that fails on round 3 (c543ac7) and on main and passes here (numbers below in
that order). Code: kit.py's "round 3b" comments. Checkpoint: a round 3b column in the sheets of
`renders/checkpoints/2026-11-15_jersey3/` and sheet 11, each sleeve all round at 1:1.

| Fix | How, numbers | Test: round 3, main, round 3b | Source |
|---|---|---|---|
| 1. Sleeve fronts | Round 3's cause: the upper arm's grey-teal bands (display about 0.39, 0.47, 0.49: min channel less 0.6 chroma 0.33) were over the white elements' edge guard (0.3) and dropped, so the sleeves read near black. Each sleeve's zebra is now traced first on Leatt US's front flat itself, inside the sleeve's outline, where the sleeve is seen square on (0.70 mm a px: the chest LEATT's 395 px for 0.275 m; an 11 px median takes out the perforations, dots 4 to 5 px, 15 px apart; a 3 mm field and a 1.5 cm window follow the fade; contrast 0.05 to 0.1 is pattern, under 0.10 of green light is the black), then cut again on the sleeve's unrolled raster (edge guard 0.95). His left sleeve takes the flat's right one mirrored: the flat lays his left turned in, over the trunk's side, its upper arm at a slant (traced there the grey bands came out as blobs) | band texels against the flat, IoU on each sleeve's upper arm and forearm, over 0.75: 0.27 (his left upper arm), 0.21 to 0.36, 0.85 to 0.88 | PHOTO Leatt US front flat |
| 2. Sleeve backs | Below the raglan part each sleeve's back half is its front half mirrored about the top and underarm lines, so the bands run on across both lines (the back views see the sleeves' backs at grazing angles, their bands' phase differs from the flat's, and traced they gave the review's fragments). Over the raglan part (4 to 10 cm from the shoulder point) plain ground, the magenta fading into the black (the trunk's views there carried the photo model's sleeve stripes past the seam). White elements only where a photo saw the texel (view weight over 0.02), pieces under 200 mm2 dropped (the specks were 24 to 91 mm2; his left sleeve's line is 510 mm2) | white specks under 20 mm2 on the sleeves' backs: 0, 3 (his left), 0 | PHOTO NZ back, back 3/4 flat |
| 2. Sleeve marks | The forearm LEATTs and his left elbow icon printed from Leatt's official files (`SLEEVE_MARKS`): the right LEATT on the flat at ink rows 1204 to 1409 of the sleeve's line from row 470 to 1640 (t 0.715 along the arm, 88 mm long), 83 px outward where the half sleeve is 87 px (72 deg from the front toward the outside), letters' tops to the front; the icon from the NZ back photo (t 0.56, 112 deg, 19 mm, apex up the arm). The photos' traced whites are dropped all round the arm over each LEATT's span and 12 mm beyond (traced, the left LEATT landed in three places: a 1086 mm2 streak at 44 deg, 340 mm2 of letters at 109 deg), and what is left of the white coverage in pieces under 200 mm2 goes after that (build 9 had kept an 81 mm2 end of that streak outside the band and 14 specks of 1 to 2 mm2, thin grey scratches, on the top line over his left elbow) | the white over each LEATT's span against the stamp, IoU over 0.8: 0.27 and 0.13, 0.00 and 0.03, 0.99 and 0.99. Unstamped white pieces under 200 mm2 on the sleeves: 25, 14, none | PHOTO front flat, NZ back; us.leatt.com wordmark and favicon |
| 2. Side panels and back | The side panels traced on Leatt NZ's back three-quarter flat itself, inside the panel's outline (`SIDE_EDGES`, 0.55 mm a px down the panel), with the sleeves' options, and laid over the trunk's print as their own piece (cut at its seams). The back panel outside them is ground only (`plain`: the stripes zeroed, the white elements kept): the photo model's stripes there were the lime and teal fragments | stripe ink on the back's flanks beside the panels (z hem + 3 cm to 1.30 m), under 0.02: 0.222, 0.21, 0.001 | PHOTO NZ back 3/4 flat, back on-model |
| 3. Pant | Each Leatt on-model photo is traced in its own pixels (0.5 mm, where the legs are seen square on; a 2 mm field follows the shins' sweeping stripes; the white elements at 0.8 mm) and the texels take that artwork. The legs' outline comes from the mesh's cross-section at each height (round 3 took the vertices within 6 mm of a height: up to 70 mm jumps between heights 5 mm apart, and every stripe mapped through it came out serrated), the photo's runs smoothed down 15 rows (median, then mean). Past 60 deg from the front (`PANT_MIRROR`) the print is the photo's own seen from 60 deg back toward the front, mirrored: the bands meet themselves in a chevron on the outseam (round 3 left past 83 deg plain) | stripe ink within 18 deg of each leg's side, 30 to 42 cm above the knee joint, over 0.3: 0.09 and 0.09, 0.36 and 0.53, 0.43 and 0.53. The shins' magenta changed by a 3 mm closing and opening, under 0.11: 0.126 and 0.116, 0.18 and 0.17, 0.099 and 0.053 | PHOTO Leatt US on-model front and back; his 07 |
| 4. Lower back holes | `LB_HOLES`: 5 staggered rows from z 1.197 down, 12.4 mm apart, 14.3 mm pitch, 0.176 m wide (63 holes of 1.8 mm), and what shows through them a light base layer, (146, 165, 197) display. Leatt NZ's back three-quarter flat at 1:1 shows 4 staggered rows under the magenta fade, 27.7 px apart (12.4 mm at its 2237 px per m down the garment), 13 holes a row over 293 px (24 px apart, foreshortened: 14.3 mm for an equilateral stagger); his 06 shows about 5 rows: one more on top. The tone: the brightest tenth of the dots' peaks in his 06 (daylight; the 1 to 2 px dots are blurred into the black). Round 3's two rows at z 1.155 and 1.215 are gone (the jersey's holes: 243; Leatt says 238) | dots in the tone (within 0.1), per row over 0.6 of 12.3: none, 8 in one row, 13 12 13 12 13 | PHOTO NZ back 3/4 flat, his 06; estimate (Damien has not answered) |
| 5. Chevron fade | In a box over the top chevrons' tops under FIVE.FIVE (`FP_FADE`: \|x\| under 0.17 m, z 1.285 to 1.345) the stripe is cut at 0.2, where the fade is near the black, not 0.5, and coloured by the photo's own fade (lime to black) smoothed over 5 mm: a clean gradient over the traced shape. The box's edges blend over 8 mm; the band's ground follows the unshifted cut (the shifted one left the band no ground: magenta blotches under FIVE.FIVE) | of the band's green texels, the share at mid brightness, over 0.4: 0.28 (a cut edge), 0.55 (the projected photo), 0.53 | PHOTO front flat, NZ front |
| 6. FIVE.FIVE | Set on the print overlay with Damien's additions (`FRONT["fivefive"]`, `FIVEFIVE`): each glyph at its ink centre measured on the front flat (184 px of ink beside the 395 px chest LEATT: 0.128 m wide; cap height 11.5 px: 8.0 mm), centred at (0.005, 1.343) from the NZ front photo (ink x 717 to 897, rows 626 to 637, under the yoke's edge at row 612); erased from the trace there (box 705, 617 to 910, 645 of that photo). The photo's 11 px capitals do not resolve Leatt's face: Inter SemiBold stands in (its F, V and E are 0.55, 0.73 and 0.6 of the cap height wide as the photo's 6, 8 and 6.5 px, its stem 0.16 as the photo's 2 px). The atlas is now packed by skyline: the front's prints at 0.162 mm a texel with the extra island | the overlay's faces over FIVE.FIVE, median texel under 0.17 mm: none (traced into the 0.8 mm texture: 10 texels to a capital), none, 0.164 mm (49 texels) | PHOTO front flat, NZ front; estimate (typeface) |

The cut test (`test_print_is_cut_not_blurred`) now measures Leatt's own airbrushed ends apart: the sleeves' last
30 %, where the flat fades the bands into the lime cuff (0.26 of its right sleeve's lime at mid brightness, 0.48 to
0.64 at 0.80 to 0.90 of its length), and the fade box of fix 5. There under 0.30 (round 3b 0.265); the rest of the
jersey under 0.10 (round 3 0.147, main 0.162, round 3b 0.090); the pant under 0.25 (0.139, 0.51, 0.058).

### Colours (round 3b)

The inks are round 3's, as the review kept them (sheet 08, the same boxes): at Standard -1.6 magenta 208, 53, 127
(0.88, 0.050, 0.29), lime 122, 184, 51 (0.27, 0.68, 0.04), black 45, 45, 47 (0.037), the back's magenta at -1.0
221, 56, 139 (0.89, 0.049, 0.30): within 1 of 255 of round 3's. Teal 97, 160, 151 (0.17, 0.50, 0.42), round 3's
94, 156, 147. In daylight (AgX - Punchy -0.6) the magenta reads 189, 85, 150 (round 3 189, 85, 151; his 09
217, 8, 111): the look's, which the coordinator checks; not changed here.

### Not seen, estimated (round 3b; replaces round 3's list)

- His left sleeve's zebra: the flat's right sleeve mirrored. The flat and the back photos run the same colours down
  both sleeves (grey, teal, lime); the exact shapes on his left differ. His 07 sees his left sleeve riding (sheet 04).
- Both sleeves' backs and underarms: their fronts mirrored about the top and underarm lines.
- His left forearm LEATT: the right one's place mirrored (t 0.715, 72 deg); read up the arm, its tops to the front
  (Leatt NZ's back three-quarter flat and front three-quarter photo see it at a slant).
- The jog of his left sleeve's line at the elbow (Leatt's back three-quarter photo): not drawn; traced, it gave
  fragments.
- The pant's outer sides past 60 deg: the photos' print mirrored. There the zebra reaches about 20 cm above the knee
  joint and the knee panel below it is black, as in Leatt's photos; the review reads his 07's zebra down to the knee.
  The front and back halves meet on the outseam with a step in the bands' phase (each half is its own photo's print
  mirrored; seen square on in sheet 07's side view, hardly in the riding view of sheet 04).
- The lower back's holes: rows, pitch and the base layer's tone (Damien has not answered).
- FIVE.FIVE's typeface: Inter SemiBold.
- The daylight look (AgX - Punchy) desaturates the magenta: the scene's, checked by the coordinator, not changed.

## Round 3c (decision 52, 2026-11-15): the 1:1 review of round 3b

The coordinator's review of round 3b (JERSEY3c) kept the sleeve fronts with the flat's bands and no white fragments
on the sleeves' backs or side panels, the forearm LEATTs and the elbow icon, FIVE.FIVE as letters, the chevron tops'
gradient, the shins' clean strokes, the lower back's dot rows (an estimate) and the outer thigh's zebra; it found one
regression and three smaller faults. Each fix has a test in test_kit_rider.py that fails on round 3b (56b403a) and
on main and passes here (numbers below: main, round 3b, round 3c). Code: kit.py's "round 3c" comments. Checkpoint: a
round 3c column in place of round 3b's in `renders/checkpoints/2026-11-15_jersey3/`.

| Fix | How, numbers | Test: main, round 3b, round 3c | Source |
|---|---|---|---|
| 1. The yoke's magenta (regression) | Round 3b's cause: `sleeve_print` left the sleeves' raglan part (within 0.10 m of the shoulder point along the arm) out of the traced shapes, so it was "unseen" and its ground came from the black sleeve: the magenta stopped short of the raglan seams and its edge was a soft halo inside the trunk (the review's measure on sheet 05: 200 px across the chest's widest row against round 3's 354, main 248). The raglan part is now traced as plain ground (`plain`), its colour the views' own: the trunk's photos at the seam blended into Leatt US's front flat's sleeve top by 0.14 of the arm, where the flat carries the magenta over the shoulder and fades it into the sleeve's black. Where no photo sees the shoulder's top square on, that fade is the flat's (an estimate) | seen square on, the magenta's share of the garment's width at each 1 cm row, over 0.85: chest (z 1.48 to 1.54) 0.70 to 0.86, 0.45 to 0.56, 0.92 to 1.00 (round 3 0.94 to 1.00); upper back (1.55 to 1.59) 0.68 to 0.79, 0.53 to 0.64, 0.99 to 1.00. Leatt's flat 0.99 at the shoulders, the NZ front 0.97, the NZ back 0.92 | PHOTO Leatt US front flat, NZ front and back, back 3/4 flat; his 06 |
| 2. The waistband and the hem beside the Waistlock | The pant: Leatt US's front photo was traced with a box round the Waistlock excluded (470 to 1010, 140 to 330 px) and each texel there took the nearest traced pixel: teal blocks stepping down the waistband (main and round 3b; round 3 a grey rectangle). Now the Waistlock's outline (strap, buckle, tab) and the jersey hanging over the waistband's top in the middle (down to its hem's white threads) are drawn in photo px (`PF_HIDDEN`) and traced with the rest, plain there in the photo's own black (median of its black pixels, taken as seen ground: as unseen texels their ground came from the stripes' anti-aliased tips, teal blotches along the outline), and kept out of the stripes' field (`cover`), so the stripes the photo sees end cleanly at the outline. Beside the buckle on his right hip the photo's waistband is plain black itself. The jersey: in the NZ front photo the jersey blouses over the Waistlock and its stripes zigzag in the folds at 1 to 3 cm beside the side seams (rows 950 to 1130), traced as steps above his right hip; there (`FP_HEM`: z under 1.17 m, blended out by 1.21, \|x\| from 0.10 to 0.13 m) the stripes' field is smoothed over 8 mm (bands 12 to 25 mm wide; Leatt's flat shows smooth curves down to the hem) | on the pant's stripe ink (chroma over 0.2) within 8 cm of its top, x -0.20 to -0.02: what an 8 mm closing and opening changes, under 0.10: 0.140, 0.126, 0.068, and the share of its outline along the texture's axes (the blocks' sides), under 0.10: 0.14, 0.15, 0.06. On the jersey's front 1 to 10 cm over the pant's top, x -0.22 to -0.10, the 3 mm measure (the shins'), under 0.045: 0.063, 0.052, 0.032 | PHOTO Leatt US front on-model pant, NZ front on-model jersey, front flat |
| 3. The lower back's dots | Measured in his 06 at 1:1: each strong dot (top-hat over 0.10, peak over 0.28) mapped through the camera fitted on the 114 (cam06, 0.9 px) onto the posed jersey and back to the rest pose. A rectangular grid (not staggered): 4 rows 13.7 mm apart (z 1.154 to 1.195 at the middle, tilted about 5 deg by the pose's error), columns 19.4 mm apart in x (about 20 mm along the cloth), seen from x -0.136 to 0.116, taken as +-0.136 (15 a row, 60 holes). The review counted about 5 rows; the mapping and the autocorrelation of the dots give 4, and Leatt NZ's back three-quarter flat shows the same field as 4 rows 26.7 px apart (11.9 mm), the same x in every row (round 3b read it as staggered), holes 5 to 7 px across (2 to 3 mm), dark there. Contrast: each 06 dot's light over the black, summed over 3x3 px, is 1.17 px2 of the 114's white beside it (R 0.82, G 1.19, B 1.26: cooler than the white); at 2.9 mm a photo px, about 10 mm2 of white per dot. Round 3b's 0.9 mm holes in (146, 165, 197) give 1.7 mm2 in the texture: the faint specks. `LB_HOLES` now: z 1.195 down, 13.7 by 19.4 mm, r 1.8 mm, the base layer's tone (203, 238, 250) display (the 06 dots against the white, linear 0.65, 0.94, 1.0 of INK_WHITE). The same measure on a daylight render of the 06 window (its camera re-aimed, so each frame is measured on its own, the polygons registered by phase correlation): 1.19 px2 (R 0.92, G 1.30, B 1.36) at r 1.9 mm against the photo's 1.09 (0.82, 1.19, 1.26), so r 1.8 mm: 1.08 (0.84, 1.17, 1.23), 5.0 px between neighbours as in the photo. The holes are bigger than the flat's: 06 cannot resolve them (its dots blur over 3x3 px), and the light through them is what it measures | light dots in the tone (within 0.1) in each of the 4 rows over 0.8 of 15, on a rectangular grid (median offset from the top row's columns under a quarter pitch), each dot's light over 6 mm2 of white: none in the tone, none (round 3b's own tone: 1.7 mm2, staggered), 15 15 15 15 at 9.2 mm2 | his 06 (cam06, posed mesh), PHOTO NZ back 3/4 flat; estimate (Damien has not answered) |
| 4. Shins on Leatt's diagonal | Open (the review allows it when 1 to 3 run long): Leatt US's back on-model sweeps the shins' magenta strokes on a diagonal with airbrushed upper ends; ours are clean but vertical. Not changed in this round | none | PHOTO Leatt US back on-model |

The renders of his photos' windows (sheets 01 to 04, 09, 10) now go through decision 54's scene look, its
"daylight" kind (head_closeups' sun and sky, the compositor's gains and max-RGB tone curve) instead of AgX - Punchy;
main is rendered again the same way beside round 3c. The inks stay as the Standard-view measurement gives them (round
3c's at Standard -1.6 are round 3's: magenta 209 53 127, lime 122 184 51, teal 94 157 148); in the daylight kind the
front view's inks come out lighter than his photos' (teal 161 253 236 against his 09's 102 171 162, the magenta's
green 0.07 of the white against 0.01): the jersey's material (gloss, sheen, the pink's lift, the navy darks) is a
later round. Blender 5.2.0: the front view at Standard -1.0 within 1 of 255 of 5.2.3's (99.5 % of pixels
identical), and the saved scene reopens with its jersey and pant images (2048 px).

### Not seen, estimated (round 3c; adds to round 3b's list)

- The yoke's fade onto the raglan part over the shoulder's top: Leatt's flat's, where no photo sees it square on.
- The waistband under the Waistlock and under the jersey's overhang in Leatt US's front photo: plain black.
- The jersey's lower sides above the hips: the NZ photo's stripes smoothed over 8 mm (its folds taken out).
- The lower back's holes: 4 rows of 15 by his 06; their size (r 1.8 mm) and the base layer's tone (203, 238, 250)
  matched to the light 06 measures, not seen directly.
- The shins' strokes: vertical; Leatt's back photo sweeps them on a diagonal (open).

## Materials (component 4)

| Material | Values | Source |
|---|---|---|
| jersey_print | print texture and normal map, roughness 0.58, sheen 0.18 (0.40 hazed the print pale in the check sheets) | EST (sublimated polyester knit) |
| jersey_mesh | the side panels (35 cm high, 9 cm wide about the side seam): same print, roughness 0.74, sheen 0.10 | Leatt features (breathability mesh), PHOTO side-panel close-up |
| pant_print | print texture and normal map, roughness 0.56, sheen 0.16 | EST (Twisted Yarn micro mesh, 4-way stretch) |
| pant_iks | near-black (22, 22, 24), roughness 0.46, coat 0.05, fine bump (ripstop and leather grain) | PHOTO inner-knee close-up |
| strap | black Hypalon rubber (18, 18, 19), roughness 0.62 | PHOTO Tech1 |
| strap_tab | black textile, roughness 0.85, sheen 0.3 | PHOTO |
| buckle | black moulded plastic, roughness 0.32, coat 0.15 | PHOTO Tech1 |
