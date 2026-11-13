# Ledger: goggle, eyes, brow badge (`scripts/rider/goggle.py`, built through `helmet.py`)

Leatt Velocity 5.5 Iriz, Pinata Teal frame and strap (8026000150; research doc section 4) with the lens Damien
asked for on 2026-11-13: a purple mirror his eyes do not show through, and his brown eyes behind it. Frames:
HELMET = helmet.py's (x his left, y back, z up, m); GOGGLE = the same axes, origin at the lens front centre.

## Sources
| Source | Use |
|---|---|
| Leatt US product JSON, every goggle-velocity-5-5-* handle (70 images) | the same five angles in every colourway: ISO, "Front" (= ISO angle), Back, Exploded, lens; no front, top or side view of the goggle alone; no dimensions but the 45 mm strap and the 48 mm Roll-Off film |
| MY27 Moto 8.5 kit, Blue_Red (31505 _1 front-iso-left, _2 left, _3 right, _4 back; "Velocity 5.5 goggles are included") | the goggle on the same shell from four sides: the measured views (saved in reference/leatt-gear/goggles/) |
| Pinata Teal 8.5 kit iso-right with goggle (reference/leatt-gear/helmet/) | frame colour, outrigger lettering, badge colour, fourth calibrated view |
| Leatt exploded view, Forge back view | frame anatomy: top vents, nose bridge, flexible nose guard, foam, outrigger block |
| His photos 07, 08, 09 (2026-11-12) | frame colour, strap print and its place, the brow badge (one LEATT) |
| MakeHuman CC0 high-poly eye proxy (system assets, mhclo) fitted on his mesh | where the eyeballs sit in his sockets |

## Cameras (fitted in the helmet frame to the shell + visor silhouette, port zone ignored, chamfer both ways)
| View | az, el, roll (deg), d (m), f (px) | chamfer at 960 px |
|---|---|---|
| Blue_Red _2 (left) | 94.7, -2.6, -8.8, 1.408, 5280 | 8.9 px |
| Blue_Red _3 (right) | -101.2, -3.6, 6.2, 1.403, 5516 | 8.4 px |
| Blue_Red _1 (front-iso-left) | 39.7, 9.4, -0.2, 1.413, 6136 | 9.7 px |
| Blue_Red _4 (back) | -182.3, 9.5, 0.8, 1.259, 5283 | 10.1 px |
| Pinata iso-right (refit) | -62.3, 8.8, 9.4, 1.422, 5826 | 8.9 px |
The front-iso cameras carry a lateral bias at the goggle of 20 to 60 mm (the badge measured in two of them came out
+7.7 and -30.2 mm off centre): the shell's estimated brow and chin bias them. The side views are near-orthographic
and agree with each other within 2 mm: the goggle's numbers come from them; the front-iso views gave the outline's
shape only (back-projected onto a frontal plane), and a silhouette optimisation over all four views degenerated.

## 1. Frame
| Number | Value | Source |
|---|---|---|
| Top lip front, centre line | y -149 mm (both side views) | red mask back-projected on x = 0, Blue_Red _2 and _3 |
| Frame top, centre | z +41 to +43.5 mm | same |
| Nose beak front, its bottom | y -156 to -157 mm; z -64.6 to -66 mm | same |
| Placement on the helmet | lens front centre (0, -0.149, 0.0), pitched 5 deg top back | the lip and the beak (front face 3.5 mm ahead of the lens, tilt from their 7 mm offset) |
| Height overall (top to beak) | 104 mm (out[0] to out[8]) | side views (107 mm incl. the moulding) |
| Ends | red stops 25 to 32 mm behind the lip at the top corners | side views (outrigger beyond) |
| Lens plan | ellipse a 118, A 72 mm: ends about 31 mm back at x 97 mm | side views' end depth; 170 deg WideVision |
| Width | 197 mm outer | front-iso back-projections averaged left and right (cancels their common lateral bias) |
| Outlines (open, out) | GP in goggle.py, 9 control points a half, straight runs with 5 to 12 mm fillets | front-iso back-projections, Leatt ISO and br1 crops; a smooth spline read as a generic goggle |
| Nose | the lens opening rises to z -14 mm (a 19 mm arch); the bridge hangs to -62 mm in front of the nose; frame only 6 mm deep there; foam leaves the bridge and runs on the opening's edge | Leatt ISO, br1, exploded view; clearance test (the first foam sat on his nose tip) |
| Front face | flat to a crease at 45 % of its width, the outer facet 3.5 mm back; 0.8 mm edges with support rings | Leatt ISO, kit photos (the bezel shaded like a tube without support rings) |
| Depth | 24 mm top to 16 mm bottom, 6 mm over the nose | EST (exploded view proportions) |
| Top vents | three slots a side, 16 mm long, mid band of the top | exploded view |
| Colour | sRGB 132/0/44, rough 0.45 | photos: Pinata kit frame median 209/0/61, his 09 190/8/88; the white studio and AgX lift the base (200/6/70 rendered 188/85/97) |

## 2. Lens, posts, outriggers, nose guard, foam, strap
| Number | Value | Source |
|---|---|---|
| Double lens | outer 1.2 mm, gap 1.6 mm, inner 0.6 mm; 3 mm under the frame lip | EST (Leatt: double lens) |
| Mirror | metallic 0.94, purple base 90/30/125, thin film 430 nm IOR 1.33, rough 0.03 | Damien (purple, eyes hidden); lens swatch renders (deep purple square on, blue-pink at grazing) |
| Tear-off posts | bare: 4.5 mm boss, 2.4 mm stud, 3.4 mm head, 14 mm in from the opening's ends, 3 mm high | Leatt photos; decision 7 (no tear-offs) |
| Outriggers | 30 mm long, 8 mm thick, frame height at the frame to 52 mm at the strap; black gloss; white LEATT, letter tops towards the strap (reads bottom to top on his right, top to bottom on his left) | Leatt ISO and the Pinata kit photo (right side) |
| Nose guard | black flap 11 mm under the bridge | exploded view |
| Foam | along the lens normal to his face, 0.5 to 30 mm, 1.2 mm off the skin, 14 mm where no skin is in reach | EST (triple-layer); clearance |
| Strap | helmet.py's (45 mm, path and print unchanged), now starting at the new outriggers | Leatt features, his 07 |

## 3. Eyes
| Number | Value | Source |
|---|---|---|
| Eyeball | sphere radius 0.955 x the helper-eye sphere (15.8 mm), centre 0.032 x behind its centre | MakeHuman eye proxy fitted by its mhclo on his mesh (lids close round it there) |
| Iris, pupil, cornea | 11.8 mm, 3.6 mm, cornea bulge radius 7.8 mm | adult means (anatomy) |
| Colour | brown, painted by script (fibres, amber collarette, dark limbus) | Damien ("I got brown eyes") |
| Rig | eye.L, eye.R bones, gaze straight ahead | MakeHuman skeleton |
| Cornea to inner lens | 35 mm | result |

## 4. Brow badge
| Number | Value | Source |
|---|---|---|
| Badge | trapezoid z 76.5 to 93 mm, half widths 28 (bottom) and 18.5 mm (top), 3 mm top corners, purple 79/39/180, white LEATT 34.6 x 8.3 mm | back-projected through Blue_Red _1 (white badge) and the Pinata iso-right, each centred on itself (their offsets +7.7 / -30.2 mm come from the shell's brow standing about 16 mm ahead of the real one) |
| Vents | slanted slots inner edge x 31 to 37 mm, outer 62 to 63 mm, z 72 to 91 mm | Pinata iso-right, back-projected |
| Why doubled | the two side views' projections of the badge land 19 mm either side of centre (same depth error) | measured above |
