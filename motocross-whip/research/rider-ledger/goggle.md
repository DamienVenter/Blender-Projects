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

Round 3 (shape pass): Leatt's Velocity 5.5 Pinata Teal ISO (goggle alone on grey,
`goggle-velocity55-iriz_pinatateal-purple78_iso_..._1920.jpg`) got its own camera, fitted in the GOGGLE frame to
the model goggle's silhouette (strap cut at x 835 px; IoU + edge chamfer both ways; grid, then Powell at 240 and
480 px, refined on the final geometry): az -44.6, el -4.8, roll -9.0 deg, d 1.472 m, f 7809 px (1920), 5.3 px/mm
at the goggle. It sees his right side. Elevation is weakly held (el fixed at +8 costs only slightly more): heights
read from it are good to about 1 mm, depths less so. Every round-3 number marked "ISO" is a photo pixel
back-projected through this camera onto the model's lens surface (s along the lens, z up) or onto its offset
surfaces.

## 1. Frame
| Number | Value | Source |
|---|---|---|
| Top lip front, centre line | y -149 mm (both side views) | red mask back-projected on x = 0, Blue_Red _2 and _3 |
| Frame top, centre | z +41 to +43.5 mm | same |
| Nose beak front, its bottom | y -156 to -157 mm; z -64.6 to -66 mm | same |
| Placement on the helmet | lens front centre (0, -0.149, 0.0), pitched 5 deg top back | the lip and the beak (front face 3.5 mm ahead of the lens, tilt from their 7 mm offset) |
| Height overall (top to beak) | 108 mm (out[0] +42 to the tab tips -66); the built frame measures 109.6 mm (helmet.py report) | side views (107 mm incl. the moulding), ISO |
| Ends | red stops 25 to 32 mm behind the lip at the top corners | side views (outrigger beyond) |
| Lens plan | ellipse a 118, A 72 mm: ends about 31 mm back at x 97 mm | side views' end depth; 170 deg WideVision |
| Width | 197 mm outer | front-iso back-projections averaged left and right (cancels their common lateral bias) |
| Outlines | GP in goggle.py, 11 control points a half (top centre, top, fin root, top end corner, side end, bottom end corner, cheek, cheek step, beak tab tip, notch side, notch apex), three outlines: out (frame edge), open (lens visible edge), inner (face side opening) | round 3: ISO back-projected, out and open per control point; inner kept from round 2 (his nose) |
| Frame top, lens top (centre) | out +42 mm, open +33 mm: a 9 mm top band over a lens that fills the front | ISO (lens top +31 to +36 along the band), side views (+41 to +43.5) |
| Side end | out s 107 mm, open s 102 mm: a 5 mm rim at the ends | ISO |
| Beak | tab tips at s 21 mm, z -66 mm; notch apex z -43 mm, pointed (1.2 to 1.5 mm fillets); cheek step at s 42 mm, z -56 mm, its 2 mm 45 deg facet | ISO (the tabs and notch), side views (tab bottom -64.6 to -66) |
| Cross-section | front rim 3 mm (2.5 at the ends), 1.5 mm proud of the lens; 0.8 mm chamfer (2 mm at the cheeks); band face rising back to the outline edge 8 to 10 mm behind the rim (top, side faces), 3 to 4 mm at the cheeks and beak; top surface back to a 1.5 mm step, then the vent row and the outer wall | ISO (the rim, the flat top band and its step, the tall flat side faces); round 2's rounded tube was the main miss |
| Fins | at the top band's ends, s 90 to 99 mm, rising 5 mm above the band, 3.5 mm thick, tip leaning out | ISO, right end (8 x 5 mm) |
| Nose | the face side's opening rises to z -14 mm; frame 6 mm deep at the notch side, 5 mm at the apex (his nose tip sits 5.6 mm behind the lens front there); foam leaves the bridge and runs on the opening's edge | ISO, exploded view; clearance test |
| Depth | 24 mm top to 16 mm bottom, 10 mm at the tabs, 6 / 5 mm over the nose | EST (exploded view proportions), clearance |
| Top vents | three slots a side, 16 mm long, in the vent row behind the step | exploded view |
| LEATT on the frame | official slanted LEATT, white, 4 mm high, on the lower band at his left cheek (s 53 mm); none on his right band; none on the nose bridge | MY27 front-iso-left and left side views show it at his left cheek; the right side view and the Pinata ISO (his right) show the right band plain; the ISO's nose bridge faces carry no lettering |
| Colour | sRGB 150/0/58 (hue 337 deg), rough 0.4 | his 08 and 09 under daylight: frame median 165/20/54, hue 346 deg (Leatt's studio magenta is bluer, not used). AgX moves reds about +9 deg towards orange and caps saturation near 0.61: the base 150/0/58 renders at hue 347 deg in his 09 view |

## 2. Lens, posts, outriggers, nose guard, foam, strap
| Number | Value | Source |
|---|---|---|
| Double lens | outer 1.2 mm, gap 1.6 mm, inner 0.6 mm; 3 mm under the frame lip | EST (Leatt: double lens) |
| Mirror | metallic 0.94, purple base 90/30/125, thin film 430 nm IOR 1.33, rough 0.03 | Damien (purple, eyes hidden); lens swatch renders (deep purple square on, blue-pink at grazing) |
| Tear-off posts | bare: 4.5 mm boss, 2.4 mm stud, 3.4 mm head, 17 mm in from the lens's visible ends, 2 mm high | ISO back-projected (17 mm, z +0.4 to +3.6 mm); decision 7 (no tear-offs) |
| Outriggers | start behind the frame's tall side faces (more than 12 mm behind the lens front, the pink face shows ahead), 30 mm long, 8 mm thick, turned out 22 deg towards the strap, 59 mm high at the strap; black gloss; white official LEATT at its own aspect, letter tops towards the strap | ISO (59 mm = 1.3 x the 45 mm strap beside it), the Pinata kit photo (right side) |
| Nose guard | black flap 7 mm under the notch, inside the tabs | ISO, exploded view |
| Foam | a 13 mm band inside the face opening, along the lens normal to his face, 0.5 mm off the skin, 1.5 to 30 mm, 14 mm where no skin is in reach; the frame's back beyond it stays bare (nose channel) | EST (triple-layer); clearance (march tolerance 2.5 mm, no skin vertex inside) |
| Strap | helmet.py's (45 mm, path unchanged), its two white logos now Leatt's official slanted LEATT at 70 % of the strap height | Leatt features, his 07, reference/leatt-gear/leatt-wordmark-slanted_official_leatt-us_1200x300.png |

## 5. Round 3 outline errors (final geometry)
| View | Model to photo, median / p90 | Photo to model, median / p90 | Note |
|---|---|---|---|
| Leatt ISO (goggle alone, own camera) | 1.5 / 4.6 mm | 1.9 / 5.4 mm | IoU 0.917; the largest misses: the outrigger's far edge and the beak's facets |
| MY27 front-iso-left, raw / aligned | 4.4 / 19.7, 2.4 / 9.6 mm | 4.5 / 10.4, 2.6 / 7.9 mm | aligned: shift 16.1, 0.0 mm, scale 0.94 (camera bias) |
| MY27 left side, raw / aligned | 9.9 / 25.1, 7.5 / 24.4 mm | 3.7 / 9.9, 2.7 / 6.8 mm | the Blue/Red frame's side faces are not red: model to photo is inflated there |
| MY27 right side, raw / aligned | 4.7 / 20.8, 3.3 / 17.9 mm | 4.6 / 10.6, 4.4 / 9.5 mm | shift -16.2, -6.2 mm |
| Pinata kit iso-right, raw / aligned | 4.8 / 20.1, 2.4 / 13.0 mm | 5.0 / 10.4, 3.0 / 9.9 mm | shift -30.1, -4.2 mm |
Kit errors are edge to edge (model frame's visible edges, z-buffered against the helmet, against the photo's red
frame edges, inner and outer), photo edges over 15 mm from any model edge left out as clutter (strap stripe).

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
