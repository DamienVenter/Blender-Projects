# Ledger: Damien's boots, Leatt Moto 6.5 White (scripts/rider/boots.py)

Every number in boots.py with its source. Frames: the boot is built as the RIGHT boot in its own frame (u to the
toe from the back of the sole's heel, v up from the ground line under the lugs, w to the outer side, metres), put on
his right foot, and mirrored onto the left. Leatt's views 02 (outer side) and 03 (inner side) both show the RIGHT
boot (toe right with the buckles facing: camera on its outer side); in 06 the right sole is the image's left one.
Photos are read only on grid crops (`grid.py`-style crops with pixel labels) or by script, never off a scaled view.

## Size
| Number | Value | Source |
|---|---|---|
| His foot, heel to longest toe | 277.3 mm | body.npz (right foot, y extent of vertices below 12 cm) |
| Leatt boot chart (foot length) | US 9 = 27.5 cm, US 10 = 29.0 cm | reference/leatt-gear/sizing/leatt-size-chart_boots.jpg |
| Size chosen | **US 10** (UK 9, EU 44.5, SKU 3025400143) | smallest size whose chart length covers his foot |
| Toe room | 19 mm | Gaerne's fit rule: the foot at least 3/4 in shorter than the insole (web search, Gaerne size chart) |
| Heel wall | 8 mm | EST: 3 mm TPU counter + 5 mm padding and liner |
| Toe wall | 13 mm | EST: 6 mm toe box wall and liner, 3 mm toe cap, 4 mm welt lip (photo 07) |
| **Sole length** (heel to toe cap tip) | **330 mm** | 290 + 19 + 8 + 13 |
| Photo 02 scale | 0.286 mm/px | 330 mm / 1154 px (heel x 443, toe cap tip x 1597, read on grid crops) |
| Boot height, ground to gaiter top | 424.7 mm | photo 02: ground y 1702, gaiter top y 217 |

## Photo calibrations (pixels)
| Photo | Landmarks | Source |
|---|---|---|
| 02 outer side | heel 443, toe 1597, ground 1702, top 217 | grid crops `g02ends`, `g02sole` |
| 03 inner side | heel 1467, toe 312, ground 1704, top 216 (1155 px long: same zoom as 02) | grid crop `g03ends` |
| 05 back pair | right boot = the right one; ground 1742, top 215 (0.278 mm/px by the boot's height) | grid crop `g05` |
| 06 soles | right sole: toe 275, heel 1555, heel centre x 663, forefoot centre 621.5; left sole: 266, 1547, 1284 | grid crop `g06`, dark-rubber mask rows |

03 is not an exact mirror of 02: its shaft leans about 2.5 deg further forward (back and front edges 10 to 20 mm
ahead at the top). 02 is the outline; 03 only fills 02's heel cup, which Leatt's retouch blew out to the
background's exact grey (236, 236, 236) between v 55 and 170 mm.

## Placement on his foot
| Number | Value | Source |
|---|---|---|
| His heel's back | u = 17 mm | the upper's heel 9 mm in front of the sole's heel (02) + heel wall 8 mm |
| Footbed under his heel | 27 mm | welt top at the heel 23 mm in 02 (y 1622) + 4 mm insole (EST) |
| Footbed under his ball | 20 mm | welt top at the ball 18 mm (02, y 1640) + 2 mm |
| Pitch (heel drop) | 2.0 deg toe down against his flat rest foot | the two footbed heights over 200 mm |
| Yaw | 2.3 deg | his ball's centre onto the outsole's centre at the ball (06: 10.7 mm out of the heel's centre) |
| **Sole under the ball** (for pose.py BOOT_SOLE) | **20 mm** | footbed at the ball |
| Shaft (gaiter) top above the ground | 423 mm at the back, 400 at the front | photo 02 columns (gaiter's top) |
| White shell's top above the ground | 360 to 396 mm outer side, 385 to 409 inner | first white below the black gaiter, 02 and 03 columns |

## Component 1: shell and sole
- Shell: every point of the side outline carries the shell's half-width there, rounded toward the outline
  (superellipse, exponent 2.4 in the shaft over the row's whole depth, 2.0 over 22 mm on the foot). Outline =
  photo 02's back line, shaft front line and the foot's top line, each a robust cubic spline (knots 40, 40, 25 mm)
  that discounts points standing out of it (buckles, strap keepers, plates, the spine are parts). Shaft width:
  photo 05's clean inner edge about its centre line (0 at the heel, -13.5 mm at the top), sections centred on his
  leg. Foot width: photo 06's outsole less the welt (5 mm). Meshed by surface nets on a 2.5 mm grid.
- Opened for his body: 8 mm outside his leg and foot (3 mm TPU + 5 mm foam and liner), 4 mm over the calf
  (v > 260 mm; his calf is 127 mm wide where Leatt's empty, closed shaft is about 106: the worn shaft's panels
  open) and 4 mm at the ball (a lasted upper, snug); the upper stays 1.5 mm inside the welt. The shell is
  therefore up to 20 mm wider than Leatt's photo at the top of the calf: worn, not empty.
- Outsole: photo 06's outline; black top at 21.2 mm (heel), 14.3 (arch and ball), 17.7 (u 274), 22 (toe)
  (02: y 1628, 1650, 1640, 1620). Lugs: the moulding's fine texture in 06 (texture energy > 9) marks the Leatt
  triangle lugs, the footpeg zone and the logos; the base between them 3.5 mm up (EST from 02's sole edge). Waist
  1.5 mm off the ground (02 y 1697). Toe spring 3.4 / 6.3 / 12 / 17.7 mm at u 260 / 288 / 302 / 317 (02 y 1690,
  1680, 1660, 1640). Bottom texture and normal map: each sole's own crop of photo 06 (the left boot's LEATT is
  Leatt's left sole, so it reads right).
- Welt: 6.5 mm white band (02, 10), 5 mm out of the upper, with a cord stitch of 35 deg slanted beads every 2.4 mm
  (02, 10).
- Toe cap: Zamak, 1.8 mm (EST), wraps the last 17 mm of the sole (02: x 1555), top edge 38 mm at the tip, 30 at
  the sides (02, 07); flange under the toe to 24 mm back with three screws (06: x 580, 640, 700, y 305), two
  screws on the wrap (07).

## Component 2: plates, buckles, straps, spine (partly done)
| Part | Numbers | Source |
|---|---|---|
| SlideLock badge plate | polygon (688,305) (780,285) (850,330) (852,470) (790,520) (700,470) px, 2.8 mm | 02 grid crops; thickness EST from 08 |
| Shin plate (brain logo) | 10-point polygon x 845 to 1085, y 330 to 760 px, 2.8 mm | 02 |
| Buckles 1 to 4 | (bail, lever front, keeper) px: (575,592)(762,598)(885,592); (572,905)(782,908)(918,905); (620,1215)(805,1158)(975,1105); (875,1460)(1005,1335)(1060,1280) | 02 grid crop `gbuck` |
| Lever | 13 mm wide (02: 45 px), 5.4 mm thick, raised 6.5 mm at the hinge, 3.5 at the front | 02, 09 |
| Bail | 21 x 30 mm loop of 3.6 mm wire | 02, 09 |
| Strap, keeper | 20 mm x 2 mm strap; keeper loop 29 x 8 mm | 02, 09 |
| Torsion blade | black wedge on the back, v 125 to 265 mm, 38 mm wide at its foot to 14 at its top, standing 16 to 6 mm out | 02 (x 445 to 470), 05, 11 |
Not yet: the SlideLock top closure's sliding mechanism, the four white plates under the buckles as separate
mouldings (the levers sit on 2.5 mm painted base plates), the spine's white plate.

## Component 3: graphics and gaiter
- Paint by projection: each shell face takes its colour from the photo it faces (02 outer, 03 inner, 05 back;
  front and top faces by the side of their normal). Paint = black where the photo's luminance is under 55 (blend
  to 95), red where red exceeds green and blue by 50, TPU white (236, 239, 242) elsewhere: the photo's shading is
  not baked. Normal map: high pass of the photo (2.5 px) for the moulded triangle patterns and the debossed LEATT.
- Photo 03's shaft leans 0.08 m per m further forward above v 170 mm than 02's: its projection is sheared back.
- Left boot: the right boot's paint with each logo box flipped back in place (horizontal flip; the spine's
  vertical LEATT flipped top to bottom), checked on the left boot's outer side (render d07: LEATT and 6.5 read
  right). Boxes: dark-pixel bounding boxes in 02 (SlideLock badge 676-830 x 322-410, brain logo 895-1085 x
  425-725, ankle LEATT 636-800 x 1430-1505, 6.5 1228-1355 x 1505-1558), 03 (calf panel LEATT and 6.5, brain icon
  on the ankle rubber), 05 (spine LEATT, heel 6.5, heel brain icon).
- Gaiter: black sleeve from 15 mm under the shell's lowest top edge to the gaiter's top (423 mm at the back, 400
  at the front, 02), 2 to 4.5 mm inside the outline's surface, 2.5 mm thick, red lining (photo 12), rolled top.
- Raised black rubber panels are paint plus normal map so far, not geometry.

## Component 4: articulation and wear
- Skin weights: the foot shell rides foot, the shaft lowerleg02, blended over the Dual Axis hinge (his ankle
  joint, foot bone head): from 25 mm below to 35 mm above it, and only behind 50 mm in front of it (the forefoot
  stays on the foot).
- Clearance (test): his covered skin is inside the boot at rest (min 1.1 mm) and with the knee at 60 deg and the
  ankle 15 deg up and 20 deg down (skin and boot both linearly blend skinned; posed skin taken back through the
  boot's blend exactly, per point). Posing changes the clearance by at most 2.6 mm (6 mm at 30 deg up).
- hide_body: 2412 body vertices (both feet and lower calves) inside the outline volume, 6 mm under the gaiter's top.
- Wear: dry dust (sRGB 120, 104, 86) in the shell's paint, fading out 60 mm above the welt, by seeded noise; the
  welt (206, 200, 189), cord and sole dusty, the toe cap rougher (his 2026-11-10/05, 2026-11-12/07 and 08).

## Checks
- `test_boots.py`: size, scale, height, shell against 02's outline row by row (median 1.1 mm), sole heights,
  skin inside the boot at rest and in five poses, hidden skin, gear file, mirror.
- Check sheets (photo beside render, same angle): Leatt 02, 03, 04, 05, 06; his 07 (left boot) and 08 (right boot
  from below).
