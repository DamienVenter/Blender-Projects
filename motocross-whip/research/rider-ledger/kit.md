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
| Sleeves | each half from its view: along the arm from the shoulder point to the cuff end, across normalised to the photo arm's half width (68, 72, 60, 48 px at 0, 0.2, 0.6, 1.0 of the arm: 0.85 of the silhouette so its soft edge is never sampled); the two halves blended over the sleeve's top line; the raglan part over the shoulder takes the trunk's views | PHOTO |
| Pant | Leatt US on-model front and back (1920 px, alpha): rows waist top (205 front, 190 back), crotch (first open row in the alpha), boot top (1670, 1650); across, each photo row's silhouette laid onto his pant's silhouette at the same height, leg by leg | PHOTO |
| Big LEATT, outer left thigh | printed flat from a side view (the photos see it edge-on): length 0.26 m, centre 0.19 m above the knee joint, reading up from the knee, letter tops to the front; the wordmark cut from the jersey chest in the front photo (x 606-1018, y 492-603) | PHOTO (Leatt front on-model, back flat; his 07 seated: reads knee to hip) |
| I.K.S panels in the print | black (0.085) inside the panel field, so the material seam and the print agree | PHOTO |
| Laser-cut holes | jersey 238 (Leatt's number): 50 on each upper sleeve front, 40 on each side panel, two rows of 29 across the lower back; pant 250: 60 on each front thigh, 25 each side of the rear yoke, 40 behind each knee. 1.8 mm holes, darkened and dented | Leatt features, PHOTO (fields' places) |
| 114 | white, dark outline 5 mm, 0.20 m high, centre z 1.33, slanted 12 deg | PHOTO 06 |
| Name | **placeholder**: region x -0.13 to 0.13, z 1.445 to 1.49 on the back, left empty (unreadable in his photos) | PHOTO 06; question for Damien |
| BIKE WISE | white box 50 x 44 mm, black outline and text, centre (-0.098, 1.428): above the chest logo's LE | PHOTO 09 |
| Pirelli | yellow patch 46 x 22 mm with red PIRELLI, centre (0.163, 1.372): past the logo's end, under the brain icon | PHOTO 09 |
| USN column | his right side panel, top z 1.30, 42 mm pitch: blue USN badge, then a red/white and a blue/white badge (unreadable: placeholders) | PHOTO 09; question for Damien |
| Relief (normal maps) | seams: 4 mm wide, 0.6 mm groove, stitch dents 3 mm off it (jersey raglan, side and underarm seams; pant centre, in-, outseams, I.K.S panels, rear yoke V z = 1.025 + 0.30 abs(x), waistband edge 40 mm down); folds: inner elbows, belly, shoulder blades (jersey), behind the knees and across the hips (pant) | PHOTO, EST |

Known limits: the projected print carries the photos' soft lighting and is softer than Leatt's real print; the
side panels and the outer shins are seen at grazing angles by the front and back photos and look smeared close up.

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
