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
| His girth under the modelled waistband | 90.3 cm (band tilted, front 1.05, back 1.115) | BODY (test) |
| His inseam | 87.2 cm (crotch height) | BODY |
| His arm length (back neck, shoulder, elbow, wrist) | about 80 cm | BODY |
| Jersey | **L** (5026000202): arm 80-82 and height 178-182 fit; chest 106-112 is above his 101, which alone says S/M. L keeps the body and sleeves long enough for 1.85 m; worn with 5 to 11 cm of ease | CHART |
| Jersey girth at his chest | 112 cm (top of L: a race fit is cut to stretch to it) | CHART; test 112 +- 3 |
| Pant | **XL / US36 / EU54** (5026000324): waist 88-93 (his 88.4 at belt height, 90.3 under the band), height 180-185 (his 185); inseam 83-85 is under his 87, so the cuff sits higher on the calf, inside the boot | CHART |

## Cut lines

| What | Value | Source |
|---|---|---|
| Neckline ("no-collar") | z 1.515 at the front (jugular notch 1.52), 1.575 at the sides (neck root), 1.565 at the back (below C7 at 1.59), smooth in the angle round the neck | BODY, PHOTO (flat front, collar close-up) |
| Sleeve end | 12 mm up the forearm from the wrist joint: the glove's short cuff covers it | BODY, PHOTO (front on-model) |
| Jersey hem | straight, z 0.95: tucked, 10 cm inside the pant at the front | PHOTO (his 07: waistband and strap visible, jersey bloused over) |
| Pant top | z 1.05 at the front (iliac crest), 1.115 at the back (raised rear yoke for the seated position) | BODY, PHOTO (back on-model) |
| Pant cuff | **z 0.30, level: mid-calf, halfway from the knee joint (0.532) to the ankle joint (0.077)**, about 10 cm inside a 0.40 m boot shaft | BODY, brief |

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
- Weights: nearest skin vertex, smoothed (jersey 6 passes, pant 2 so the cloth follows the kneecap); the tucked
  jersey takes the pant's weights so the two move together; facings copy their edge vertex.
- Riding test poses (test file): hips 60 and knees 60 deg, ankles 30, head 20 down, arms forward 45 with elbows 60;
  and seated (hips and knees 90). Result: no visible skin through the cloth away from the openings; the only
  masked skin standing more than 6 cm from the cloth is 4 to 7 vertices at the kneecap (LBS).
