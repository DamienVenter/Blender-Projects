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
| Round 4 goggle-alone photos (reference/leatt-gear/goggles/, URLs in its README): Leatt's 5.5 ISO render (Pinata Teal 39281 and the white 39278 at the same camera), the 4.5 ISO render (39260, same front frame, no outriggers, a more frontal camera), three studio photographs of the real 5.5 (Neon Yellow 8022010380, Royal Clear 8025200590, White Bronze 8025200510) | the frame's shape: five cameras fitted jointly with it (below); every one sees his right side |
| Round 5 additions (same folder): Leatt's exploded view (the bare frame from his LEFT front three-quarter, the only view of his left side), the Neon Yellow back photograph (of the 29 back views, chosen below), the Ink and Indigo front photographs (their fitted cameras put them within 1.5 deg of phw's angle: more photographs of the studio's front three-quarter, not new angles), the Forge and Cheetah front photographs (validation only: cameras fitted to the finished shape) | nine fitted views, two validation views |

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

Round 4 (the shape pass, Damien 2026-11-13: "replicate it 1 to 1"): five goggle-alone photos, one camera each in
the GOGGLE frame (research/goggle-cameras.json, goggle.py photo_project), fitted jointly with the shape (CMA-ES,
scratch scripts fitshape.py): per view (1 - IoU) x 4, the outline chamfer both ways (capped at 8 mm), the crease
chamfer both ways where the frame's faces show (iso55 through the white 39278 at the same camera, phy, phr), and
four hand-picked landmarks: ICON (the Leatt icon on the top band's front edge, s 0), NOTCH (the top of the nose
arch's front edge, s 0), POST_R and POST_L (the tear-off stud heads, 3.9 mm off the lens front). The shape's
globals (lens plan a, A; lip) were free. Masks: frame colour in the photo; the frame-coloured nose guard seen
through the clear lenses (phy, phr) ignored by polygons; the 4.5 and the white photo used as silhouettes only.
| View | az, el, roll (deg), d (m), f (px) | px/mm | Landmarks |
|---|---|---|---|
| iso55 (5.5 ISO render, Pinata and white) | -48.5, -2.0, -2.2, 1.465, 7814 | 5.3 | ICON, NOTCH, POST_R, POST_L |
| phy (Neon Yellow photo) | -51.2, -3.1, 0.4, 1.425, 6756 | 4.7 | ICON, POST_R, POST_L |
| phr (Royal Clear photo) | -42.8, -8.5, -7.0, 1.461, 5850 | 4.0 | POST_R, POST_L |
| iso45 (4.5 ISO render) | -42.3, 1.8, 1.9, 1.339, 7715 | 5.8 | ICON, NOTCH, POST_R, POST_L |
| phw (White Bronze photo) | -30.2, -5.5, -2.0, 1.419, 6195 | 4.4 | none (silhouette only) |
Without the landmarks the silhouette-only cameras slid sideways: the icon landed 22 to 34 mm off centre and the
shape grew lopsided to follow. The height origin is free in the photo fit (a common z shift of shape and cameras
costs nothing): PLACE fixes it on the helmet. Round 3's single ISO camera (az -44.6) is replaced by iso55.

## 1. Frame
| Number | Value | Source |
|---|---|---|
| Top lip front, centre line | y -149 mm (both side views) | red mask back-projected on x = 0, Blue_Red _2 and _3 |
| Frame top, centre | z +41 to +43.5 mm | same |
| Nose beak front, its bottom | y -156 to -157 mm; z -64.6 to -66 mm | same |
| Placement on the helmet | round 5: lens front centre (0, -0.1468, -0.004), pitched 5 deg top back: frame top front y -152.9, top z +41.6, beak front y -159.3, beak bottom z -59.6 mm (helmet frame; round 6's frame: -153.0, +41.3, -158.2, -59.8); the top on the side views, the beak's bottom 5.4 mm above theirs (round 4: (0, -0.147, -0.004)) | the side views' -149 / +41 to +43.5 / -156 to -157 / -64.6 to -66; round 5's frame is 100 mm tall where they read about 106 (see "Scale"). Centring it on their top and bottom (z -0.0065) put the lens's lower corners 1 to 2 mm into the shell's eyeport edge (26 vertices) and his nose bridge into the frame and lens; -0.005 still did (8 lens vertices, 3 + 1 skin), -0.004 clears both (scratch shell_diag.py). y -0.143 matched them best in round 4 but put his nose bridge 3 mm into the recessed lens |
| Height overall (top to beak) | 100.0 mm built (round 5: 100.2; round 4: 109.8) | round 6 fit: the built outer edge at s 0 is +44.8, the lowest point -55.2 at the cheek step (s 49.0 mm; round 5: +45.1, -55.1 at s 49.5). See "Scale" below |
| Ends | 35.2 mm behind the lens front at the side end (round 5: 37.6) | round 6 fit (the side end's control point on round 5's lens plan); side views: red stops 25 to 32 mm behind the lip |
| Lens plan | ellipse a 134.8, A 93.9 mm (round 4: 137.7, 89.8; round 3: 118, 72) | round 5 fit, free global; kept in round 6 |
| Width | 206.2 mm outer (round 5: 205.2; round 4: 212.6; round 3: 197) | round 6 fit; the size is not pinned (see "Scale") |
| Outlines | GP in goggle.py, 15 control points a half (goggle.CTRL: top_c, step_hi, step_lo, fin_root, top_corner, side_top, side_end, bot_corner, cheek, cheek_step, leg_out, tab_tip, notch_side, arch_step, notch_apex), out (frame edge) and open (the lens's visible edge, the foot of the frame's inner wall); inner (face side opening) round 2's, 4 mm higher (PLACE moved the goggle 4 mm down) | round 4 joint fit, hand-cleaned (crossed steps, a zigzag at the side, an undercut leg) and refined |
| Recessed lens | the frame's front face stands proud of the lens front by 9.2 to 9.5 mm at the top band (7.3 at the fin root), 6.6 to 6.9 mm at the side pillars and lower corners, 8.5 to 9.3 mm at the cheeks and nose (round 6: GP lip a smooth field, values at the control points; round 5: one per control point, 6.7 to 10.1; round 4: 8.8 everywhere; round 3: 1.5) | round 6 fit (section 8), held near round 5's: the photos' inner walls between the frame face and the lens; at most 9.2 at the top centre (the side views) |
| Outline offsets | between the control points the outer edge and the lens edge bow off their polygons by a smooth normal offset (round 6: GP out_dk, open_dk, cubic B-splines of 24 coefficients a half, near 0 at the control points): median 0.06 / 0.05 mm, at most 1.45 / 1.32 mm (round 5: one offset per sample, 197 a half, median 1.6 / 1.5, up to 7.0 / 9.7 mm: the overfit that read as crumpled) | round 6 fit (section 8) |
| Top band, pillars, lower band as built | round 6: top band 10.7 mm over the lens at the centre, 9.5 mm at s 50; side pillar's face 9.6 mm wide at the end; lower band 12.3 mm under the lens at s 80; lowest -55.2 mm at s 49.0; nose arch apex -31.7 mm, 23.4 mm above the legs (round 5: 10.6, 9.2, 7.7, 12.5, -55.1 at s 49.5, -33.4 and 21.2; the apex 1.7 mm higher brings the NOTCH landmark in iso55 from 1.7 to 0.5 mm) | round 6 fit, measured on the built outlines (control points plus offsets); the round 4 rows below give the control points only |
| Vent teeth | the top band's lens edge steps down at the vents: two teeth, |s| 43.6 to 59 mm (drop 0 to 1.5 mm) and 59 to 79.5 mm (1.7 to 1.4 mm) (GP teeth, goggle.tooth_drop; round 5: 0 to 0.9 and 1.1 to 1.9; round 6 eases each step over 0.4 mm) | Leatt's ISO renders (iso55, white 39278): steps at |s| 43.6, 59 and 79.5 mm on the near side, back-projected; drops fitted. The sawtooth's individual steps (1 to 2 mm) are only partly reproduced |
| Nose ribs | a comb on the nose bridge behind the lens: centre finger (tip z -16.4 mm), a finger each side at s 10.3 mm (tip -17.9), an outer lobe each side (s 16.7 to 29.0 mm, top -18.7 to -21.5) with a closed slot (s 21.7, z -29.1 to -22.5), open slots between down to z -25; in frame colour, the bridge round it black within |s| 30 mm; front face 0.3 mm in front of the bridge's nearest point; clipped to clear his nose by 0.5 mm on him | iso55 (pink and white) back-projected with the round 5 camera (ribs_bp.py), the pattern centred on s 0; seen through the clear lens in phr. Depth NOT pinned: the exploded view agrees in height only 8.5 mm back and never in s, every slot reads sheared (a bridge sloping back): question for Damien. From behind (phyb) the model shows the ribs in frame colour through the nose opening where the photo shows only dark foam and shadow: what covers their back is not pinned either |
| Top band | out top_c +48.4, step_hi (s 38.9) +42.5, step_lo (s 43.9) +44.2, fin_root (s 89.8) +35.6; open +35.0 at the centre, +32.2 past the step: 13.4 mm deep at the centre, 12 mm at the step; the centre raised 4.2 mm, the lens edge stepped 2.7 mm | round 4 fit |
| Side pillars | top_corner (100.6, +32.6), side_top (107.2, +24.9), side_end (114.0, -4.3) against open s 89.5 to 92.9: the face 11 to 23 mm wide | round 4 fit |
| Lower band, cheeks | bot_corner (101.3, -43.4), cheek (64.4, -55.0), cheek_step (51.1, -60.9, the lowest point), leg_out (36.0, -58.1); open -34.0 to -48.3: 9 to 13 mm under the lens | round 4 fit |
| Beak and nose arch | tab_tip (26.6, -58.6), notch_side (12.7, -56.0), arch_step (9.5, -46.1), notch_apex (0, -34.5): the arch 21 mm high from the tab tips; pointed (1.2 to 1.5 mm fillets) | round 4 fit (NOTCH landmark: 1.7 mm in iso55, 4.6 mm in iso45) |
| Cross-section | front rim 2.5 to 3.0 mm, chamfer 0.7 to 1.9 mm, fillets as round 3; band (the face's fall back to the outline edge) 1.4 to 10.5 mm, the face's crease (ring RING_MID) at mid_t 0.29 to 0.59 of the face, mid_w -2.2 to +1.4 mm off the straight face (round 6: smooth fields, values at the control points; round 4: band 1 to 12, mid_t 0.19 to 0.66, mid_w -2.5 to +1.3) | round 4 fit (crease chamfer in iso55, phy, phr), round 5 and 6 refits |
| Fins | at the top band's ends, s 90 to 99 mm, rising 5 mm above the band, 3.5 mm thick, tip leaning out | ISO, right end (8 x 5 mm) |
| Nose | the face side's opening rises to z -10 mm (round 3: -14; PLACE 4 mm lower); frame 5 mm deep at the notch side, 2.5 mm at the arch step and apex (the bridge over his nose, behind the recessed lens); foam leaves the bridge and runs on the opening's edge | exploded view; clearance test (at 5 mm his nose bridge was 2 to 5 mm inside the frame) |
| Depth | 23 mm top to 16 mm bottom, 9.5 mm at the tabs, 5.6 to 2.2 mm over the nose (round 6's smooth field; round 4: 24, 16, 10, 5 / 2.5) | EST (exploded view proportions), clearance |
| Top vents | three slots a side, 16 mm long, in the vent row behind the step | exploded view |
| LEATT on the frame | official slanted LEATT, white, 4 mm high, on the lower band at his left cheek (s 53 mm); none on his right band; none on the nose bridge | MY27 front-iso-left and left side views show it at his left cheek; the right side view and the Pinata ISO (his right) show the right band plain; the ISO's nose bridge faces carry no lettering |
| Colour | sRGB 150/0/58 (hue 337 deg), rough 0.05 (round 6, gloss measured: section 8; round 5: 0.4) | his 08 and 09 under daylight: frame median 165/20/54, hue 346 deg (Leatt's studio magenta is bluer, not used). AgX moves reds about +9 deg towards orange and caps saturation near 0.61: the base 150/0/58 renders at hue 347 deg in his 09 view |

## 2. Lens, posts, outriggers, nose guard, foam, strap
| Number | Value | Source |
|---|---|---|
| Double lens | outer 1.2 mm, gap 1.6 mm, inner 0.6 mm; its front 8.8 mm behind the frame's front face (round 4); its edge the lens window grown 3 mm under the frame, with the loops that growth makes at the window's sharp inward corners cut out (round 5: they had left see-through wedges at the nose arch's steps; test_lens_fills_the_window) | EST (Leatt: double lens); round 4 fit |
| Mirror | metallic 0.94, purple base 90/30/125, thin film 430 nm IOR 1.33, rough 0.03 | Damien (purple, eyes hidden); lens swatch renders (deep purple square on, blue-pink at grazing) |
| Tear-off posts | bare: 4.5 mm boss, 2.4 mm stud, 3.4 mm head (centre 3.9 mm off the lens front), at s 86.7 mm, z -1.2 mm on the lens (round 4: 87.5, -1.5) | round 5: refitted on round 5's lens with the cameras fixed (POST_R, POST_L landmarks in iso55, phy, phr: 0.5 to 1.0 mm; 0.2 to 1.8 mm at round 4's place); decision 7 (no tear-offs) |
| Outriggers | start behind the frame's tall side faces (more than 12 mm behind the lens front, the pink face shows ahead), 30 mm long, 8 mm thick, turned out 24 deg towards the strap (round 4: 22), 59 mm high at the strap; black gloss (round 6: rough 0.05, no coat, section 8); white official LEATT at its own aspect, letter tops towards the strap | ISO (59 mm = 1.3 x the 45 mm strap beside it), the Pinata kit photo (right side); round 5 fit (GP or_*: or_turn 0.44, the far edge seen in iso55, phy, phw, the back view) |
| Nose guard | black flap from half-way up the arch's legs, 7 mm under the apex, its drop scaled to the arch (0 at the legs) | ISO, exploded view; round 4 (the flat 7 mm drop hung below the shorter legs) |
| Foam | a 13 mm band inside the face opening, along the lens normal to his face, 0.5 mm off the skin, 1.5 to 30 mm, 14 mm where no skin is in reach; the frame's back beyond it stays bare (nose channel) | EST (triple-layer); clearance (march tolerance 2.5 mm, no skin vertex inside) |
| Outriggers on the helmet | the free plate above (Leatt's ISO, goggle alone) starts inside the eyeport opening and its back 35 % would sink 22 to 41 mm into the shell; worn, the strap pulls it onto the shell: each row lifted outwards (x only, front edge fixed on the frame) to clear the shell by 1.5 mm behind the eyeport's edge, bending out at most 60 deg (55 left the top corner 2 mm inside); the strap's end sits 10 mm inside the outrigger's back end, mid height and mid thickness, so the strap leaves the outrigger and lies on the shell | Damien 2026-11-13 ("not properly connected to it's strap"), his 07 and 09, Leatt's MY27 kit views (strap from the outrigger straight onto the shell); goggle.outrigger_grids, test_outriggers_rest_on_the_shell_and_hold_the_strap |
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

## 6. Round 4 errors (goggle-alone photos, final geometry, Blender 5.2.0 renders beside them)
| View | Outline model to photo, median / p90 | Photo to model | Creases model to photo / photo to model, medians | IoU | Landmarks |
|---|---|---|---|---|---|
| iso55 | 1.50 / 5.2 mm | 1.59 / 5.2 mm | 1.50 / 0.53 mm | 0.950 | ICON 3.2, NOTCH 1.7, POST_R 0.3, POST_L 0.3 mm |
| phy | 1.33 / 5.2 mm | 2.11 / 6.3 mm | 1.27 / 0.84 mm | 0.945 | ICON 0.2, POST_R 1.1, POST_L 0.1 mm |
| phr | 1.50 / 6.0 mm | 2.23 / 7.6 mm | 1.50 / 0.71 mm | 0.915 | POST_R 0.1, POST_L 0.7 mm |
| iso45 (silhouette) | 1.43 / 5.8 mm | 1.43 / 5.9 mm | | 0.931 | ICON 1.1, NOTCH 4.6, POST_R 0.3, POST_L 0.8 mm |
| phw (silhouette) | 1.30 / 4.1 mm | 1.30 / 4.1 mm | | 0.947 | |
Medians at 0.5 photo scale (2 to 3 px per mm): 1.5 mm is close to the fit's resolution there. Round 3 at its one
ISO camera: 1.5 / 1.9 mm, IoU 0.917. The 1 mm target is not reached. Still different: the vent sawtooth on the top
band's lower edge (s 25 to 66 mm, near side) and the nose bridge's ribs (seen through clear lenses) are not
modelled; the far (left) side, the top and the bottom are never seen in any photo (mirrored from the right); the
outrigger's far edge and the outline at the lower near corner (phr) miss by 5 to 8 mm at p90.

## 7. Round 5 (full resolution, nine views)
Method (scratch scripts fit5.py, errtab.py, camlm5.py): a Gauss-Newton ICP over the shape and the nine cameras
(distance fixed, focal length free): model outline and crease pixels at full photo resolution matched to the photo
edge pixel of the same orientation nearest along the normal, Huber weights, residuals capped at 6 mm, a trust cap on
each step, ridge terms on the offsets. Free: the control points, a lip per control point, the cross-section
values, the outrigger values, the two teeth's drops, and one normal offset per outline sample (out_dn, open_dn).
Clear lenses: photo edges more than 3 mm inside the model's lens window are left out of the photo-to-model term
(the nose ribs, inner walls and foam seen through the lens); every model edge counts. The ICP has no landmark term,
so the sequence was: fit B (shape and nine cameras); the landmark views' cameras (iso55, phy, phr) refitted with the
shape fixed (silhouette, outline and landmarks); fit C (shape and the other six cameras, those three frozen; it
stopped after 4 iterations with no further progress); the tear-off posts refitted on the final lens with every
camera fixed (POST_S, POST_Z). The two validation views (Forge, Cheetah) got cameras fitted to the shape only and
never entered the fit.
Back views: the 29 "Back" photographs sorted by camera (silhouettes scaled to the same area, IoU pairwise): the MY24
ones pair up at 0.96 to 0.98 (shared rigs), the 2022, 2023 and 2025 ones only 0.92 to 0.95 (each its own angle);
one is used, the Neon Yellow (phy's goggle). Front views: the other front photographs (Ink, Indigo, Forge, Cheetah)
turned out to share the studio's front three-quarter rig (fitted az -38 to -45, el -1.6 to -4.4 deg, within 2 to 5
deg of phw and phr): they add photographs, not angles. The only new angles in round 5 are the exploded view (his left,
24 deg from above) and the back view.

### Round 5 errors (final geometry and cameras, full resolution; scratch errtab.py, work/r5/err_final3.log)
Outline: the frame's silhouette edge plus the lens window edge; crease: the frame face's edges inside the outline.
Model to photo / photo to model, median / p90 in mm at the goggle. Round 4 at the same measure in brackets.
| View | Outline model to photo | Photo to model | Creases m to p / p to m | IoU | Landmarks (mm) |
|---|---|---|---|---|---|
| iso55 | 0.73 / 3.8 (1.51 / 5.6) | 0.89 / 3.4 (1.60 / 5.3) | 1.29 / 3.4, 0.40 / 1.1 | 0.972 (0.950) | ICON 0.55, NOTCH 1.66, POST_R 0.85, POST_L 1.03 |
| phy | 0.81 / 4.0 (1.48 / 5.6) | 1.01 / 3.1 (1.79 / 5.6) | 1.21 / 4.1, 0.45 / 1.3 | 0.962 (0.946) | ICON 1.33, POST_R 0.93, POST_L 0.65 |
| phr | 0.96 / 3.7 (1.50 / 6.0) | 1.20 / 3.5 (2.01 / 6.7) | 1.22 / 3.6, 0.54 / 1.9 | 0.930 (0.916) | POST_R 0.67, POST_L 0.54 |
| iso45 (4.5, silhouette) | 0.37 / 1.8 (1.56 / 5.7) | 0.46 / 2.3 (1.55 / 5.8) | | 0.972 (0.930) | not the 5.5's frame: NOTCH 9.9, POSTs 4.5 to 5.5 (left out) |
| phw (silhouette) | 0.43 / 1.6 (1.15 / 4.2) | 0.43 / 1.5 (1.15 / 4.0) | | 0.978 (0.947) | |
| expl (exploded view) | 1.57 / 6.4 | 1.55 / 5.2 | 1.10 / 3.4, 1.23 / 3.7 | 0.854 | |
| phyb (back) | 0.44 / 1.6 | 0.44 / 1.6 | | 0.975 | |
| ink | 0.30 / 2.1 | 0.21 / 1.3 | | 0.982 | |
| ind | 0.30 / 1.7 | 0.30 / 1.5 | | 0.981 | |
| frg (validation) | 0.44 / 1.4 | 0.44 / 1.3 | | 0.979 | |
| chee (validation) | 0.80 / 3.3 | 0.70 / 2.2 | | 0.966 | |
Targets (median 1 mm, p90 3 mm) met in the silhouette views (iso45, phw, phyb, ink, ind, frg) and on outline
medians in iso55, phy, phr; not met: outline p90 3.1 to 4.0 mm in iso55, phy, phr, chee; crease medians 1.2 to 1.3 mm
model to photo in iso55, phy, phr (the model's face crease against a soft photo crease, p90 3.4 to 4.1); and the
exploded view everywhere (1.1 to 1.6 mm, p90 3.4 to 6.4). Where the p90s sit (overlays in the checkpoint sheets):
the far (his left) outrigger and side pillar, seen edge on in every front view and never square on; the vent
sawtooth (two ramps, not five steps); and in expl the far outrigger, which stands upright in that photo (unworn) and
is ignored, plus the frame's back edge and top vents, which no other photo shows.

### Round 5 cameras (research/goggle-cameras.json; az, el, roll in deg, d in m, f in px, on 1920 x 1920 photos)
| View | az | el | roll | d | f | mm per px |
|---|---|---|---|---|---|---|
| iso55 | -50.9 | -0.3 | -1.2 | 1.46 | 8260 | 0.177 |
| phy | -52.1 | -3.1 | -0.3 | 1.43 | 7050 | 0.202 |
| phr | -44.4 | -1.6 | -1.2 | 1.46 | 6086 | 0.240 |
| iso45 | -49.6 | -1.6 | -1.3 | 1.34 | 8190 | 0.163 |
| phw | -39.4 | -2.2 | 1.7 | 1.42 | 6670 | 0.213 |
| expl | 50.6 | 24.0 | -0.5 | 1.32 | 5362 | 0.246 |
| phyb | -145.0 | 1.0 | -1.2 | 1.40 | 6399 | 0.218 |
| ink | -40.9 | -2.0 | 0.4 | 1.48 | 7026 | 0.211 |
| ind | -39.7 | -1.6 | -1.3 | 1.39 | 6469 | 0.215 |
| frg | -38.2 | -4.4 | -1.9 | 1.49 | 6803 | 0.219 |
| chee | -44.8 | -1.7 | -0.2 | 1.45 | 6514 | 0.222 |
d is held fixed in the joint fit (round 4's for its five views; for the new ones the value of their first camera
fit, where perspective pins it only weakly); f carries the scale (see "Scale").

### Scale (not pinned)
The photos fix the shape, not its size: with the distance fixed and the focal length free the fit shrank the goggle
5.5 % (every focal length grew 4 to 8 %; width 212.6 to 205.2 mm, height 109.8 to 100.2 mm). Two absolute
references disagree by 12 %: Leatt's 45 mm strap (research doc section 4), measured beside the outrigger at the
outrigger's depth, reads 45.2 (Indigo), 45.8 (phr), 47.8 (phy, iso55) and 48.2 mm (phw) at the fitted size, so the
strap asks for a goggle up to 6 % smaller; the calibrated kit side views (top +41 to +43.5, beak bottom -64.6 to
-66 mm) ask for one about 6 % taller. The fitted size sits between them and is kept. PLACE keeps round 4's height:
the frame's top on the side views' (+41.6 against +41 to +43.5 mm), its beak bottom 5.4 mm above theirs; centred
on them instead, the lens's lower corners went into the shell's eyeport edge and his nose bridge into the frame
(placement row above), so the side-profile test allows 6 mm at the beak bottom until the size is pinned. Question
for Damien: the frame's outer width and its height at the centre.

### Frame colour on him (round 5 check, his 08 and 09)
Frame and white shell medians in the same image (colour.py: band polygons on the frame, the lit half of the shell),
linear; the frame / shell ratio per channel cancels the white balance and exposure:
| Image | Frame sRGB | Shell sRGB | Frame / shell (linear R, G, B) |
|---|---|---|---|
| his 08 (daylight) | 147, 28, 49 | 229, 238, 243 | 0.372, 0.014, 0.034 |
| his 09 (daylight) | 160, 10, 48 | 235, 239, 244 | 0.423, 0.004, 0.033 |
| render 08 as built (AgX, studio) | 173, 73, 95 | 200 | 0.72, 0.114, 0.19 |
| render 09 as built | 158, 57, 79 | 188, 189, 192 | 0.680, 0.080, 0.148 |
| render 09, Standard view | 162, 56, 83 | 231 to 243 | 0.452, 0.049, 0.097 |
| render 09, frame specular off (AgX) | 153, 2, 55 | 188, 189, 192 | 0.633, 0.001, 0.072 |
| render 09, frame specular off, Standard view | 156, 0, 61 | 231, 233, 243 | 0.416, 0.000, 0.052 |
The albedo is right: rendered with its specular off and no tone curve the frame / shell ratio is 0.416 / 0 / 0.052
against his photos' 0.37 to 0.42 / 0.004 to 0.014 / 0.033 (the albedo's own ratio to the shell texture's 226/229/235:
0.40 / 0 / 0.051). The washed-out raspberry in the renders is the studio: the frame's specular reflection of the soft
studio (two 2.5 m area lights, a 0.9 grey world at 0.8, a light floor) lifts every channel by about 0.05 of the shell
(green 0.004 to 0.014 in his photos, 0.08 in the render), which takes the saturation from 0.81 to 0.94 (his) to 0.64;
AgX then raises the frame against the bright shell (red 0.42 to 0.68). Roughness 0.15 or 0.25, a dimmer world (0.2)
and AgX Punchy (with +0.4 exposure: 141/45/67) do not remove it; a sun-and-blue-sky test still reflected the sky
(0.415 / 0.040 / 0.101). The albedo stays 150/0/58; a daylight-like lighting of the close-ups would match his photos
(a render-wide choice, not the goggle's: put to Damien). Sheet: renders/checkpoints/2026-11-13_goggle-r5/ (in git at
405ea54; replaced by round 6's checkpoint, which repeats the check under daylight: section 8).

## 8. Round 6: fair by construction
Why: round 5's error table was good and its 1100 px sheets looked right, but a 1:1 crop of iso55 (box 900, 660 to
1720, 1280) showed crumpled, melted plastic: wobbling creases, dents and ripples on the top band, the near pillar,
the lower band and the beak. Leatt's photo shows an injection-moulded part: flat or gently curved faces, creases in
straight lines or smooth arcs, clean highlights. Cause: overfitting. One normal offset per outline sample and one
section value per control point let every sample pull the surface on its own. Same defect and fix as the bike's
side panel (bike-modelling decision 37).

### Representation (goggle.py)
| Freedom | Round 5 | Round 6 |
|---|---|---|
| Outer edge and lens edge between the corners | one normal offset per sample, 197 a half (out_dn, open_dn), median 1.6 / 1.5 mm, up to 7.0 / 9.7 mm | a uniform cubic B-spline over each polygon's own arc length, mirrored at the centre line so it is C2 across it (goggle.bspline_half), 24 coefficients a half (out_dk, open_dk), held near 0 at the control points so the polygon and its fillets carry the corners: median 0.06 / 0.05 mm, up to 1.45 / 1.32 mm |
| Section fields (depth, rim, chamfer, band, top, mid_t, mid_w, lip) | one value per control point, straight lines between | the same kind of B-spline over the outer edge's arc length (outline_t), 16 coefficients a half |
| Corners, lens plan, outriggers, fillets | fitted | round 5's, kept |
| GP digits | 4 decimals (0.1 mm) | 5 (10 um; mid_t, a fraction, 4): 0.1 mm steps in smooth coefficients read as ripple |

### Fit (scratch fit6.py, built on fit5.py)
Round 5's full-resolution ICP over the same nine views, plus:
- a bending penalty: the second differences of every coefficient run (the mirrored ends included), weight 0.08 per
  mm (per 0.1 for mid_t);
- the outline offsets at the control points held near 0 (weight 1 per mm);
- a ridge of every section field to round 5's values converted to the B-splines (weight 0.3 per mm): the photos see
  the recess, the rim, the depth and the face's crease nearly edge on and pin them weakly. Without it they drifted
  in a few iterations (the lip 3 mm, the crease to its limit, the depth 9 mm at the top centre);
- the landmark views' cameras (iso55, phy, phr) frozen at round 5's landmark fit: the ICP has no landmark term, and
  with them free the shape and the cameras slid together (phr's posts 3.5 mm off);
- residual weights Huber at 3 mm (the first round 6 fits: 1 mm, which let the p90s grow), residuals capped at 8 mm;
- hard limits on the start and after each step: the top surface's back edge at least 0.3 mm behind the outline edge
  (at a third of the bending weight they met: a sliver face, kink 90 deg), fillets 0.4 to 8 mm, vent drops at most
  2.4 mm, the lip at least 6.6 mm and at most 9.2 mm at the top centre (Leatt's side views: top front y -149 mm, the
  frame already 4 mm ahead of them; see "Scale").
Start: round 5 converted (its offsets and fields projected onto the B-splines, fairness 1.3 deg / 28 um / 1.2 deg /
0.7 deg) with round 5's final cameras. Fits F8 (8 iterations at Huber 1), F10 (6 at Huber 3), F13 (4 with the lip
limit) in scratch work/r6. The other six cameras were fitted with the shape; frg and chee (validation) were refitted
to the final shape only (fitcam).

### The nose arch's apex (found in the 1:1 crops after the fit)
At the apex the face between the lens edge and the outer edge narrows to 1.0 mm (1.0 to 4.6 mm for |s| < 4.5 mm),
less than the rim plus the chamfer (4.2 mm). The rings sat at those fixed distances from the lens edge, so the rim
and chamfer rings ran past the outer edge and the face folded back: a pinch at the apex in the 1:1 crop and under
the raking light, which frame_fairness does not see (it leaves the corners out). frame_rings now shrinks the rim and
the chamfer with the face, to 0.85 of its width (7 samples). The outlines do not change; the error table moved by at
most 0.1 mm (below). test_round6_front_face_does_not_fold: each step across the face turns from the one before by
under 90 deg (round 5: 111 deg, the first round 6 build: 117 deg, both at the apex; now 67 deg at most, a designed
edge). Still different from Leatt's photo there: its arch's underside is a round arc (about 5 mm radius at the top,
read off iso55 at 0.18 mm per px) under a flat top with two small ears at the lens; ours is pointed (the outer
edge's 54 deg apex corner, fillet 1.5 mm, round 4's), and under a side light the beak's two halves meet in a straight
valley. A larger fillet does not round it: a quadratic fillet at a 54 deg corner has a radius of 0.24 x its length at
the apex (1.4 mm at 6 mm; the side allows 7), and fillets of 3, 4.5 and 6 mm (the control point raised to keep the
apex and the NOTCH landmark where they are) moved the error table by under 0.1 mm (scratch apexvar.py). A round arch
needs the arch's control points refitted: left for a later round.

### Fairness (test_goggle.frame_fairness; bounds 1 deg, 10 um, 1 deg, 2 deg)
| Measure | Round 5 | Round 6 | Where (round 6) |
|---|---|---|---|
| dturn: change of turning angle sample to sample along a ring | 9.07 deg | 0.50 deg | the face's crease |
| ripple: off the local quadratic through 9 samples | 74.9 um | 9.4 um | the chamfer at the near pillar's lower half (the lens edge's offset there) |
| kink: a face normal against its neighbours' mean | 3.04 deg | 0.57 deg | chamfer / crease face |
| wave: a face normal against its running mean | 6.02 deg | 0.50 deg | crease / edge face |
| fold: a step across the front face against the one before (test_round6_front_face_does_not_fold, bound 90 deg) | 110.6 deg | 66.5 deg | the top band's crease near the centre (a designed edge) |

### Round 6 errors (final geometry and cameras, full resolution; scratch errtab.py, work/r6/final7_err.log)
Same measure as round 5 (model to photo / photo to model, median / p90 in mm at the goggle); round 5 in brackets.
| View | Outline model to photo | Photo to model | Creases m to p | Creases p to m | IoU |
|---|---|---|---|---|---|
| iso55 | 0.64 / 4.01 (0.73 / 3.84) | 0.89 / 3.36 (0.89 / 3.39) | 1.19 / 3.26 (1.29 / 3.42) | 0.53 / 2.05 (0.40 / 1.08) | 0.974 (0.972) |
| phy | 0.81 / 3.96 (0.81 / 3.97) | 1.01 / 3.03 (1.01 / 3.14) | 1.01 / 3.73 (1.21 / 4.09) | 0.61 / 1.62 (0.45 / 1.28) | 0.965 (0.962) |
| phr | 0.96 / 4.33 (0.96 / 3.73) | 1.22 / 3.87 (1.20 / 3.54) | 1.29 / 3.85 (1.22 / 3.63) | 0.68 / 1.87 (0.54 / 1.92) | 0.927 (0.930) |
| iso45 (4.5, silhouette) | 0.49 / 1.98 (0.37 / 1.83) | 0.49 / 2.45 (0.46 / 2.34) | | | 0.970 (0.972) |
| phw (silhouette) | 0.60 / 1.27 (0.43 / 1.62) | 0.60 / 1.29 (0.43 / 1.49) | | | 0.978 (0.978) |
| expl | 1.30 / 5.51 (1.57 / 6.38) | 1.30 / 4.74 (1.55 / 5.20) | 1.21 / 3.35 (1.10 / 3.44) | 1.41 / 3.99 (1.23 / 3.68) | 0.872 (0.854) |
| phyb | 0.44 / 1.52 (0.44 / 1.57) | 0.44 / 1.52 (0.44 / 1.59) | | | 0.975 (0.975) |
| ink | 0.42 / 1.26 (0.30 / 2.08) | 0.42 / 1.26 (0.21 / 1.34) | | | 0.982 (0.982) |
| ind | 0.43 / 1.44 (0.30 / 1.73) | 0.43 / 1.50 (0.30 / 1.51) | | | 0.981 (0.981) |
| frg (validation) | 0.44 / 1.09 (0.44 / 1.35) | 0.44 / 1.09 (0.44 / 1.28) | | | 0.983 (0.979) |
| chee (validation) | 0.32 / 1.30 (0.80 / 3.25) | 0.32 / 1.31 (0.70 / 2.19) | | | 0.982 (0.966) |
Better: every p90 in expl, phw, phyb, ink, ind and both validation views (chee 3.3 to 1.3 mm), the crease medians in
iso55 and phy. Worse (the smooth curve no longer bends into every photo edge):
- iso55: outline p90 model to photo +0.17 mm; crease p90 photo to model 1.08 to 2.05 mm, on a small set (275 photo
  crease pixels: the p90 is 28 of them, on two short marks, the near pillar's lower inner corner and the far beak
  leg);
- phy: crease p90 photo to model +0.34 mm;
- phr: outline p90 3.73 / 3.54 to 4.33 / 3.87 mm. The far outrigger stands open in that photo and closed on the
  model (both rounds); without it (photo x 1640 on) photo to model is 2.64 (round 5) against 2.82 mm. New: 97 px at
  the near pillar (x 1007 to 1023, y 901 to 1010) 4.2 mm off, where round 5's free offsets followed a photo edge;
- iso45: medians +0.03 to 0.12 mm, p90 +0.11 to 0.15 mm (the 4.5's frame, not the 5.5's);
- silhouette medians in phw, ink, ind 0.30 to 0.43 up to 0.42 to 0.60 mm (p90s better);
- expl creases +0.11 to 0.31 mm.
A camera refit of iso55 and phr on the round 6 shape (scratch camlm5.py, with landmarks) gave better landmarks but
mixed p90s (iso55 3.84 / 3.48, phr 4.57 / 3.99): not kept. Landmarks (round 6 cameras): iso55 ICON 0.88, NOTCH 0.53
(round 5: 1.66), POST_R 0.85, POST_L 1.03; phy ICON 1.51, POSTs 0.93, 0.65; phr POSTs 0.67, 0.54 mm.

### Round 6 cameras (research/goggle-cameras.json; as round 5's table)
| View | az | el | roll | d | f | mm per px |
|---|---|---|---|---|---|---|
| iso55, phy, phr | round 5's (frozen) | | | | | |
| iso45 | -49.7 | -1.3 | -1.0 | 1.34 | 8217 | 0.163 |
| phw | -39.0 | -2.0 | 2.0 | 1.42 | 6690 | 0.212 |
| expl | 50.2 | 24.1 | -0.2 | 1.32 | 5463 | 0.241 |
| phyb | -145.0 | 0.7 | -0.9 | 1.40 | 6410 | 0.218 |
| ink | -40.8 | -1.7 | 0.7 | 1.48 | 7048 | 0.210 |
| ind | -39.5 | -1.3 | -0.9 | 1.39 | 6485 | 0.215 |
| frg (validation) | -39.4 | -3.3 | -1.2 | 1.49 | 6816 | 0.218 |
| chee (validation) | -40.6 | -2.0 | 0.4 | 1.46 | 6506 | 0.225 |

### Raking light (goggle_views.py, light rakeT, rakeB, rakeL, rakeR)
After the bike's rake.py: the studio lights off, the ambient at 12 %, a 0.5 deg sun 20 deg in front of the lens's
front plane from above, below, his left or his right, AgX Punchy; every dent shows as a streak. Round 5 (same
materials): the top band's face streaked at the control points and its step edge zigzagged, the near pillar waved,
the lower band showed facets and the beak's legs crumpled. Round 6: even gradients along each face, creases straight
or in even arcs, the apex's pinch gone after the fix above. Left: the beak's two halves meet in a straight valley at
its pointed apex (above), and in expl the top's back edge follows the depth field in long, even bows. Sheets in the
round 6 checkpoint (iso55: above, his right, below; expl: above, his left, below; 1:1).

### Gloss (round 6; scratch gloss.py, iso55 at full resolution)
On the frame's pixels: the highlights' edge width (25 to 75 % of their rise, px), the area brighter than 2.5 x the
median luminance, the haze (the white part's median over the median luminance: sheen spread over every face) and
the peak (p99.5 over the median).
| Render | Edge | Area | Haze | Peak |
|---|---|---|---|---|
| Leatt's photo | 2.4 px | 0.1 % | 0.089 | 2.01 |
| round 5: rough 0.4, studio lights 2 m | 4.0 | 4.6 | 0.396 | 5.52 |
| rough 0.4, lights 5 m | 2.8 | 2.2 | 0.493 | 5.92 |
| rough 0.3 under a clear coat, lights 2 m | 3.1 | 16.1 | 0.371 | 5.94 |
| rough 0.2, 2 m | 3.5 | 15.7 | 0.230 | 6.58 |
| rough 0.1, 2 m | 3.2 | 15.4 | 0.198 | 6.74 |
| rough 0.05, 2 m | 3.0 | 15.2 | 0.194 | 6.76 |
| rough 0.05, 5 m | 3.1 | 3.0 | 0.542 | 5.79 |
| rough 0.05, 1 m (kept) | 2.5 | 4.4 | 0.198 | 6.59 |
| rough 0.05, 0.5 m | 2.5 | 3.8 | 0.202 | 6.58 |
The edge width is set by the roughness and the lights' size together: Leatt's 2.4 px edges need a near-mirror
finish lit by small sources; round 5's rough 0.4 gave 4.0 px, a semi-matte look. Kept: frame rough 0.05, and
goggle_views' studio lights 1 m square (GOGGLE_VIEWS_LIGHT_SIZE). The area, peak and haze stay above the photo's:
Leatt's studio is not ours (fewer, dimmer reflections; our dim world spreads a sheen), so they rank the variants but
are not matched. Outriggers (gloss black): Leatt's near outrigger reads 23 sRGB on its face with thin crisp edge
highlights; rough 0.25 under a coat (round 5) rendered 46 (a grey sheen), rough 0.1 bare 36, rough 0.05 bare 36 with
crisp edges (the rest is our backdrop's reflection): kept rough 0.05, no coat. Its white print reads 255 in the
photo and 172 in the render (it faces away from our key light). The lens was checked by eye only: Leatt's photo has
the Pinata colourway's lens, not his purple mirror, so its material stays (round 4).

### Daylight for his photos (head_closeups.py, light "daylight")
His photos 07, 08 and 09 are outdoor shots from one session under a clear sky with a high sun. The studio's grey
reflections on the glossy frame were the washed-out raspberry of section 7's check. The daylight option: a sun lamp
and Blender 5.2's multiple-scattering sky (its own sun disc off, the lamp is the sun) over a flat ground colour; AgX.
The default stays the studio (the helmet graphics work uses it); Leatt's product shots keep goggle_views' studio.
| Number | Value | Source |
|---|---|---|
| Sun direction per view, in the camera frame: phi across the image (0 right, 90 up), theta off the line back to the camera | 07: (90, 106.7) deg; 08: (85, 130); 09: (81, 130). World elevation: 07 78.0 deg, 08 73.2, 09 70.0 | 07: the bike's shadow lies right under it, a little towards the camera (sun about 78 deg high, just beyond the bike); the view's camera looks up 4.7 deg, so theta = 90 + (90 - 78) + 4.7 (102, for a level camera, put the sun at 82.7 deg); 08, 09: the luminance gradient on his white shell points to image up (85, 81 deg); theta swept 115 to 145 deg, 130 matches the shell's lit / shaded ratio |
| Sun lamp | 4 W/m2, disc 0.53 deg | the sun's angular diameter |
| Sky strength | 0.136 x 4 x cos 15 deg / 14.9 | a clear sky at a high sun gives about 12 % of the light on the ground as diffuse (clear-sky models): 0.136 of the sun's on a horizontal plane; Blender's multiple-scattering sky at strength 1 puts 14.9 on it at sun elevations 60 to 75 deg (measured) |
| Ground | albedo 0.41, 0.40, 0.36, lit by the sun and sky (Lambert) | his 07: the lit pavement over his white shell's top, x 0.8 |
| Exposure | +2.0 EV | his phone exposes for him: his white shell's lit half has median linear luminance 0.84 (08) and 0.86 (09). AgX compresses: the render's lit shell 0.45 / 0.51 at +1.3 EV, 0.55 / 0.59 at +2.0, 0.62 / 0.66 at +2.6, where the frame and the sky wash out |

### Frame colour under daylight (round 6, his 08 and 09)
Section 7's measure (scratch colour.py: frame and lit-shell medians, the frame / shell ratio cancels white balance
and exposure) on head_closeups.py renders of the round 6 rider (frame rough 0.05):
| Image | Frame sRGB | Shell sRGB | Frame / shell (linear R, G, B) |
|---|---|---|---|
| his 08 | 147, 28, 49 | 229, 238, 243 | 0.372, 0.014, 0.034 |
| his 09 | 160, 10, 48 | 235, 239, 244 | 0.423, 0.004, 0.033 |
| render 08, daylight, AgX +2 EV | 164, 71, 99 | 194, 196, 198 | 0.688, 0.114, 0.221 |
| render 09, daylight, AgX +2 EV | 167, 69, 95 | 201, 202, 204 | 0.662, 0.101, 0.190 |
| render 08, daylight, Standard view (scratch copy of the script) | | | 0.384, 0.056, 0.118 |
| render 09, daylight, Standard view | | | 0.357, 0.050, 0.089 |
| render 08, studio, AgX | 154, 52, 74 | 197, 199, 201 | 0.579, 0.060, 0.117 |
| render 09, studio, AgX | 133, 45, 63 | 169, 171, 174 | 0.591, 0.064, 0.117 |
Through a linear view the frame's red against the white shell matches his photos (0.36 to 0.38 against 0.37 to
0.42): the albedo 150/0/58 stays. Two things still separate the renders from his photos. AgX (the render-wide view,
kept as briefed) lifts a bright, saturated red against a near-white shell (red 0.66 to 0.69 at +2 EV: the frame reads
pinker and lighter, more than in the studio, where it is lit less against the shell) and pales the sky. And the
glossy frame reflects the blue sky and the bright ground (green 0.05 and blue 0.09 to 0.12 of the shell, against
0.004 to 0.014 and 0.033 in his photos; his phone's colour processing likely removes most of it). Sheet:
renders/checkpoints/2026-11-13_goggle-r6/07_frame_colour_daylight_his_08_09.jpg (the Standard panels are the 0 EV
render scaled by +1.5 EV in linear, exact for that view below white). Whether his photo comparisons should go
through the Standard view (or AgX Punchy) is a render-wide choice, not the goggle's: put to the coordinator.

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
