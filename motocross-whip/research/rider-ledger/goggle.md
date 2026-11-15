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
| Recessed lens | round 7: top band 9.2 to 10.9 mm, pillars 3.9 to 4.5, lower band 7.3 to 7.7 (section 9). Round 6: the frame's front face stands proud of the lens front by 9.2 to 9.5 mm at the top band (7.3 at the fin root), 6.6 to 6.9 mm at the side pillars and lower corners, 8.5 to 9.3 mm at the cheeks and nose (round 6: GP lip a smooth field, values at the control points; round 5: one per control point, 6.7 to 10.1; round 4: 8.8 everywhere; round 3: 1.5) | round 6 fit (section 8), held near round 5's: the photos' inner walls between the frame face and the lens; at most 9.2 at the top centre (the side views) |
| Outline offsets | between the control points the outer edge and the lens edge bow off their polygons by a smooth normal offset (round 6: GP out_dk, open_dk, cubic B-splines of 24 coefficients a half, near 0 at the control points): median 0.06 / 0.05 mm, at most 1.45 / 1.32 mm (round 5: one offset per sample, 197 a half, median 1.6 / 1.5, up to 7.0 / 9.7 mm: the overfit that read as crumpled) | round 6 fit (section 8) |
| Top band, pillars, lower band as built | round 7: section 9 (test_velocity55_shape_from_leatts_photos lists the built values). Round 6: top band 10.7 mm over the lens at the centre, 9.5 mm at s 50; side pillar's face 9.6 mm wide at the end; lower band 12.3 mm under the lens at s 80; lowest -55.2 mm at s 49.0; nose arch apex -31.7 mm, 23.4 mm above the legs (round 5: 10.6, 9.2, 7.7, 12.5, -55.1 at s 49.5, -33.4 and 21.2; the apex 1.7 mm higher brings the NOTCH landmark in iso55 from 1.7 to 0.5 mm) | round 6 fit, measured on the built outlines (control points plus offsets); the round 4 rows below give the control points only |
| Vent teeth | the top band's lens edge steps down at the vents: two teeth, |s| 43.6 to 59 mm (drop 0 to 1.5 mm) and 59 to 79.5 mm (1.7 to 1.4 mm) (GP teeth, goggle.tooth_drop; round 5: 0 to 0.9 and 1.1 to 1.9; round 6 eases each step over 0.4 mm) | Leatt's ISO renders (iso55, white 39278): steps at |s| 43.6, 59 and 79.5 mm on the near side, back-projected; drops fitted. The sawtooth's individual steps (1 to 2 mm) are only partly reproduced |
| Nose ribs | a comb on the nose bridge behind the lens: centre finger (tip z -16.4 mm), a finger each side at s 10.3 mm (tip -17.9), an outer lobe each side (s 16.7 to 29.0 mm, top -18.7 to -21.5) with a closed slot (s 21.7, z -29.1 to -22.5), open slots between down to z -25; in frame colour, the bridge round it black within |s| 30 mm; front face 0.3 mm in front of the bridge's nearest point; clipped to clear his nose by 0.5 mm on him | iso55 (pink and white) back-projected with the round 5 camera (ribs_bp.py), the pattern centred on s 0; seen through the clear lens in phr. Depth NOT pinned: the exploded view agrees in height only 8.5 mm back and never in s, every slot reads sheared (a bridge sloping back): question for Damien. From behind (phyb) the model shows the ribs in frame colour through the nose opening where the photo shows only dark foam and shadow: what covers their back is not pinned either |
| Top band | out top_c +48.4, step_hi (s 38.9) +42.5, step_lo (s 43.9) +44.2, fin_root (s 89.8) +35.6; open +35.0 at the centre, +32.2 past the step: 13.4 mm deep at the centre, 12 mm at the step; the centre raised 4.2 mm, the lens edge stepped 2.7 mm | round 4 fit |
| Side pillars | top_corner (100.6, +32.6), side_top (107.2, +24.9), side_end (114.0, -4.3) against open s 89.5 to 92.9: the face 11 to 23 mm wide | round 4 fit |
| Lower band, cheeks | bot_corner (101.3, -43.4), cheek (64.4, -55.0), cheek_step (51.1, -60.9, the lowest point), leg_out (36.0, -58.1); open -34.0 to -48.3: 9 to 13 mm under the lens | round 4 fit |
| Beak and nose arch | round 7: a round-topped arch, top -37.9 mm, feet z -49.8 at s 12.5 (section 9). Round 4: tab_tip (26.6, -58.6), notch_side (12.7, -56.0), arch_step (9.5, -46.1), notch_apex (0, -34.5): the arch 21 mm high from the tab tips; pointed (1.2 to 1.5 mm fillets) | round 4 fit (NOTCH landmark: 1.7 mm in iso55, 4.6 mm in iso45) |
| Cross-section | round 7: section 9 (a wide flat front face, a 0.1 mm crease land, the inner wall leaning out). Round 4: front rim 2.5 to 3.0 mm, chamfer 0.7 to 1.9 mm, fillets as round 3; band (the face's fall back to the outline edge) 1.4 to 10.5 mm, the face's crease (ring RING_MID) at mid_t 0.29 to 0.59 of the face, mid_w -2.2 to +1.4 mm off the straight face (round 6: smooth fields, values at the control points; round 4: band 1 to 12, mid_t 0.19 to 0.66, mid_w -2.5 to +1.3) | round 4 fit (crease chamfer in iso55, phy, phr), round 5 and 6 refits |
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
| Outriggers | start behind the frame's tall side faces (more than 12 mm behind the lens front, the pink face shows ahead), 30 mm long, 5 mm thick (round 8, section 10; rounds 1 to 7: 8), turned out 24 deg towards the strap (round 4: 22), 59 mm high at the strap; black gloss (round 6: rough 0.05, no coat, section 8); white official LEATT at its own aspect, letter tops towards the strap | ISO (59 mm = 1.3 x the 45 mm strap beside it), the Pinata kit photo (right side); round 5 fit (GP or_*: or_turn 0.44, the far edge seen in iso55, phy, phw, the back view) |
| Nose guard | round 7: a closed black rubber shell 2.5 mm thick filling the arch from behind its top (z -37.5 mm) to -54.6 mm, 17 mm half-wide at the bottom, its sides sweeping back 3 mm; on him it gives way to his nose (section 9; rounds 4 to 6: a flap from half-way up the arch's legs) | phy, phr (bottom edge z -55.1 to -56.1, about 34 mm wide), the exploded view (smooth, no ribs); fitted on the silhouettes |
| Foam | a 13 mm band inside the face opening, along the lens normal to his face, 0.5 mm off the skin, 1.5 to 30 mm, 14 mm where no skin is in reach; the frame's back beyond it stays bare (nose channel) | EST (triple-layer); clearance (march tolerance 2.5 mm, no skin vertex inside) |
| Outriggers on the helmet | the free plate above (Leatt's ISO, goggle alone) starts inside the eyeport opening and its back 35 % would sink 22 to 41 mm into the shell; worn, the strap pulls it onto the shell: each row lifted outwards (x only, front edge fixed on the frame) to clear the shell by 1.5 mm behind the eyeport's edge, bending out at most 60 deg (55 left the top corner 2 mm inside); the strap's end sits 10 mm inside the outrigger's back end, mid height and mid thickness, so the strap leaves the outrigger and lies on the shell | Damien 2026-11-13 ("not properly connected to it's strap"), his 07 and 09, Leatt's MY27 kit views (strap from the outrigger straight onto the shell); goggle.outrigger_grids, test_outriggers_rest_on_the_shell_and_hold_the_strap |
| Strap | round 8: goggle.build_strap, laid on the shell (section 10; rounds 1 to 7 helmet.py's ruled band); 45 mm, its two white logos Leatt's official slanted LEATT at 70 % of the strap height | Leatt features, his 07, reference/leatt-gear/leatt-wordmark-slanted_official_leatt-us_1200x300.png |

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
Decided (coordinator, round 7 brief): AgX stays for every render, it is the project's look. The base colour is
verified under the Standard view (frame / shell red 0.36 to 0.38 against his 0.37 to 0.42) and stays 150/0/58; AgX
shifts that ratio to 0.66 to 0.69 at +2 EV in daylight (0.58 to 0.59 in the studio), which is the look, not an error.

## 9. Round 7: Leatt's details at 1:1
Why: the coordinator's 1:1 review of round 6 (sheets 08, 09, 11 against iso55 and phr): the silhouette is close
(IoU 0.97) but the frame reads as soft, inflated plastic where Leatt's is crisp and faceted. Seven points, in the
order they show. Scale at the goggle: iso55 and the white ISO 0.177 mm per px, phr 0.21.

### The nose arch
| | Leatt (evidence) | Round 6 | Round 7 |
|---|---|---|---|
| Top | z -38.2 to -39.1 mm: the frame's arch top back-projected at the front face in iso55, phy, phr and the white ISO; landmark NOTCH re-picked there (iso55 px 1506, 1160) | -31.7: the lens edge's top, taken for the arch top since round 4 (NOTCH sat on it) | -37.9 |
| Round top | phy 0.2 mm below the top at s 2.0 mm, iso55 0.8 at s 3.2 (a 46 deg V drops 2.0 and 3.3) | a pointed 54 deg apex, fillet 1.5 mm | 0.4 at 2.0, 1.2 at 3.2 |
| Legs | lean 46 to 51 deg from horizontal; phy's mid leg z -45.0 at s 7.8 | V legs | 51 deg; z -44.3 at 7.8 |
| Feet | s 12 to 13 mm, z -49.3 to -49.7 (FOOT landmarks, iso55, phy, phr) | about 6 mm lower | z -49.8 at s 12.5 |
| Ears | a small corner at the lens edge's top of each leg (EAR landmarks; iso55 px 1451, 1128 and 1551, 1122) | none | ring c at notch_side, both sides |
Why rounds 4 to 6 drew a V: the photos' arch outline is the frame plus the black nose guard and foam inside it, and
with no guard in the model the fit bent the frame over them. The round 7 fit (scratch fit7.py, runs F1 to P1)
still narrowed the arch: photo points more than the 8 mm cap from the start got no weight. The arch's control points
were moved by hand to the back-projected points (arch_step at s 2.6 mm, z -37.85, fillet 2.4 mm) and the fit run
from there. Not as briefed: no photo shows near-vertical legs; they lean 46 to 51 deg, and that is what is built.

### Creases (the crisp look)
Each designed crease measured at 1:1 (scratch probe.py): the 10 to 90 % width of the shading step across it, against
the photo's own blur (a silhouette edge's width: white ISO 0.85 px, iso55 1.4). The model's turn runs between the
support rings either side of the crease; projected with the photo's camera and blurred alike, its width is
hypot(0.8 x the projected span, blur) (test_round7_creases_are_as_crisp_as_leatts: every probe within 1 px, mean
within 0.6).
| Probe (photo px) | Leatt | Round 7 (0.1 mm) | Round 6 (0.35 mm) |
|---|---|---|---|
| white ISO, top band's upper crease (1250, 732) | 2.2 | 1.6 | 3.5 |
| white ISO, same crease (1150, 744) | 2.1 | 1.7 | 3.6 |
| white ISO, top band's lens edge (1250, 768) | 2.0 | 1.1 | 2.6 |
| iso55, upper crease (1250, 728) | 1.9 | 2.0 | 3.7 |
| iso55, upper crease (1150, 740) | 1.2 | 2.0 | 3.7 |
| iso55, lens edge (1250, 765) | 1.3 | 1.6 | 2.8 |
| iso55, lens edge (1150, 771) | 1.6 | 1.6 | 2.8 |
Built: goggle.CREASE_R 0.1 mm support rings at every ring (smooth shading stays flat inside each facet and turns
only there), and a 0.1 mm land at the top crease (GP chamfer) in place of round 6's 0.7 to 2.0 mm 45 deg chamfer.
The land drops at 45 deg only where the outer facet behind the crease falls back that steeply or more; where that
facet is nearly flat (the lower band and the arch, band under 1 mm) it lies on the facet. The first round 7 build
dropped it everywhere and drew a thin dark, kinked line across the arch's face, which Leatt's shows plain.
phw and phr read alike (0.8 to 2.5 px) but their cameras are less sure at that scale: not in the test. The white
ISO reads a little softer than the model at the lens edge (2.0 against 1.1 px); iso55 alone bounds the radius at
0.1 mm or less (its blur hides anything finer), so the white ISO's probes are a check, not the source. Note: the
white ISO was a round 4 source (creases, teeth, ribs at iso55's camera, section "Cameras"), so it is not a clean
hold-out.

### Section (GP fields, values at the control points; round 6 in brackets)
| Field | Round 7 | Evidence |
|---|---|---|
| lip, front face proud of the lens | top band 9.2 to 10.9 mm, pillars 3.9 to 4.5 (6.6: a fit limit, not evidence), lower band 7.3 to 7.7 | fit; the post heads stand in front of the pillar face in iso55 and phr |
| rim, the flat front face | 6.5 mm on the top band, 4.9 to 5.8 elsewhere (2.4 to 3.0) | fit on the creases (iso55, phy, phr, expl) |
| chamfer, the top crease's land | 0.1 mm (0.7 to 2.0 at 45 deg) | crease widths above |
| bevel, the inner wall's lean out from the lens edge | 0 on the top band, 1.6 to 2.7 on the pillars, 0.2 to 0.8 on the lower band beside the nose (new) | fit; the lit foot (below) |
| band, the outer facet's lean back to the outline edge | 2.1 to 4.2 on the top band, 5.7 to 6.4 on the pillars, 0.4 to 2.4 on the lower band (pillars 8.5 to 11.7) | fit |

### Pillars
Leatt's are straight bands with a clean step to the outrigger (iso55, phr). Round 6's outer edge bowed 6.3 mm off its
chord and its outer facet leaned back 8.5 to 11.7 mm. Round 7, over the pillar's middle three quarters (z +13.9 to
-30.2 mm): the outer edge 0.015 mm off its chord; the fields along it near linear (lip 3.9 to 4.5 mm, 0.29 off a
line; bevel 1.9 to 3.1, 0.43; rim 5.0, 0.04; band 5.8 to 6.6, 0.12; test_round7_side_pillars_are_straight, bound
0.3 and 0.5 mm). side_top, side_end and bot_corner are collinear; side_end now sits at the lens edge's pillar corner
height (z -17.13 mm, was -3.75), so the rulings between the lens edge and the outer edge run across the pillar, not
up it (the outline moves under 0.06 mm; before, the crease and chamfer wobbled 0.5 mm there and failed fairness:
ripple 33 um). The outriggers' depth is now taken at their own centre height (z -5.2 mm; 15.395 against 15.396 mm).

### The lower band's foot
Leatt's lower band either side of the arch juts forward with a lit near-horizontal top face and a sharp crease
(iso55, white ISO). Built: the band stands 7.3 to 7.7 mm proud of the lens there, its top face (the inner wall from
the lens edge) leaning out by 0.2 to 0.8 mm, so it faces up, and meets the front face at a CREASE_R crease.

### Top band, tab and notches
A flat front face 6.5 mm wide, the crisp upper crease (0.1 mm land), the top surface behind it. The raised tab with
the Leatt icon: the top silhouette steps up at s -32.0 mm (iso55, +11 px), -32.0 (phy, +6 px), -29.9 (phw, +6 px)
and in the white ISO (+9 to 10 px, 1.6 to 1.8 mm); its far end reads at +22.7 to +38.8 (phr, phw, phy, where the
step faces away), so it is mirrored from the near end. Built: goggle.TAB_S 31 mm, TAB_H 1.7 mm, a 2 mm ramp each
end, behind the front face's crease (the crease does not move); the ICON landmark sits on it. The white ISO's
1.6 to 1.8 mm is one of the four sources of the height. The notches: the tab's two steps, and the lens edge's
sawtooth at s 43.6, 59 and 79.5 mm (teeth, refitted: 0 to 0.3 mm and 2.0 to 1.5 mm drops; round 6 0 to 1.5 and
1.7 to 1.4). The smaller 1 to 2 mm steps between them are still not modelled: at 0.18 mm per px they are 6 to 11 px
in iso55 and the white ISO, too few edge pixels to fit apart from the teeth.

### The far side in phr
The far pillar now reads as a thin sliver: 14 px wide at mid-height against Leatt's 16 (round 6: a thick rounded
bulge). Not matched: the far outrigger. In phr it stands 50 to 65 px beyond the pillar, swung open on the strap; the
model's is closed behind the pillar. The silhouette fit gets no gradient from a hidden part, and phw and phy show it
at other angles (a free plate on the strap: its angle varies photo to photo), so round 5's outrigger is kept.

### The nose guard (new) and the ribs
Leatt's exploded view shows the guard as a smooth faceted rubber block with no ribs; the ribbed part is the comb on
the nose bridge behind the lens (five elements: a centre finger, a finger and an outer lobe each side, modelled since
round 5, section 1). In phy and phr the guard fills the arch and hangs below it, its bottom edge back-projecting to
z -55.1 to -56.1 mm, about 34 mm wide. Built (goggle.build_nose_guard, GP ng, fitted with the shape on the
silhouettes): a closed rubber shell 2.5 mm thick from z -37.5 (behind the arch's top) to -54.6 mm, 17 mm half-wide at
the bottom with 3 mm round corners, a rounded nose ridge whose sides sweep back 3 mm. On him the rubber gives way to
his nose: where its back would cut his skin it comes forward (goggle.guard_clear; up to 7 mm at the top corners
beside the bridge of his nose; test_frame_and_lens_clear_his_face now includes it). The guard shows below and
inside the arch in every view (dark, matte, smooth, as in phy, phr and phw). The sweep was fitted at 10.2 mm with
the frame still moving; on the finished frame its far side left the backdrop showing inside the arch's far leg in
phr, phy and phw, where Leatt's guard fills the arch. Set on the finished frame by the error table (scratch
ngsweep.py, repo cameras), outline p90s model to photo / photo to model:
| Sweep | iso55 | phy | phr | phw | ink | ind | iso45 | phyb |
|---|---|---|---|---|---|---|---|---|
| 10.2 mm | 4.14 / 3.48 | 3.54 / 3.01 | 3.16 / 3.54 | 1.43 / 1.43 | 1.50 / 1.42 | 1.65 / 1.56 | 2.28 / 2.29 | 1.87 / 1.77 |
| 6 mm | 4.20 / 3.42 | 3.44 / 2.98 | 3.04 / 3.49 | 1.35 / 1.49 | 1.24 / 1.39 | 1.45 / 1.65 | | |
| 3 mm (built) | 4.26 / 3.43 | 3.32 / 2.89 | 3.01 / 3.41 | 1.30 / 1.43 | 1.14 / 1.27 | 1.45 / 1.70 | 2.03 / 2.59 | 1.87 / 1.96 |
| 0 | 4.26 / 3.45 | 3.29 / 2.84 | 2.89 / 3.33 | 1.30 / 1.43 | 1.14 / 1.27 | 1.51 / 1.73 | 1.98 / 2.75 | 1.87 / 1.97 |
The sum over these views falls 1.0 mm from 10.2 to 3 mm and 0.05 more to 0; 3 mm keeps a nose ridge (the exploded
view's guard is a faceted nose cover, not a flat plate). The validation views were not used (frg, chee also improve).
Test: test_round7_nose_guard_fills_the_arch_in_the_photos projects the frame and the guard with the iso55, phy, phr
and phw cameras and counts the arch's opening (its front and back edges between the feet) left uncovered: 0 px
from 6 mm down to 0; at 10.2 mm 95, 37, 56 and 59 px (iso45 112, phyb 31; scratch guardcover.py).

The ribbed part (the brief's point 7) is the comb, and it is frame plastic, not rubber: it takes the frame's colour
in every photo that shows it (yellow in phy, red in phr and on the kit helmet, pink in iso55, white-grey in the white
ISO, black in the exploded view). His purple mirror hides it (Damien asked for a mirror his eyes do not show
through), so on him it never shows. Behind Leatt's see-through lenses (goggle_views GOGGLE_VIEWS_LENS_VLT: Light
Grey 58 % for the white ISO, Iriz Purple 78 % for iso55, Clear 83 % for phr, the VLTs in Leatt's colourway names)
it shows where Leatt's does (checkpoint 07). phr at 4x (scratch comb_phr_z4): Leatt's gaps between the tongues
start at px 1365, 1399, 1429 and about 1450, the model's at 1360, 1397, 1425 and 1455 (1 to 1.5 mm at 3.9 px per
mm); the tips at y 1006 to 1019 against 1005 to 1015. iso55: tips at 1038, 1035, 1048 against 1043, 1036, 1040.
Not matched:
- Leatt's gaps lean, more the further out (phr 10 to 35 deg from upright, iso55 and the white ISO 23 to 40 deg);
  ours read upright. Round 5 put the shear down to the bridge sloping back (goggle.py's comb note) and kept a flat,
  lens-parallel comb. Every photo that shows the comb sees it from his right (az -38 to -52 deg; the exploded view,
  from his left, shows it black on black), so a fan cannot be told apart from a slope and a wrap round the nose.
- Leatt's outer lobe is split from the first finger by a slanted slot open at its outer end and sits lower (its top
  about 25 px, 6 mm, below the finger's in phr): seven tongues (two lobes, five fingers) where ours has five (two
  lobes, three fingers). The three middle fingers match; our closed slot sits where Leatt's open one is.
- Leatt's tips are rounder (corner radius near a third of the width; ours 1.8 mm on 7.6 to 8.1 mm).
Left for a later round: it shows only behind a see-through lens.

### Fairness (test_goggle.frame_fairness; round 6 in brackets)
| Measure | Round 7 | Where |
|---|---|---|
| dturn | 0.81 deg (0.50) | the back face's inner edge |
| ripple | 7.0 um (9.4) | the front face's inner edge |
| kink | 0.49 deg (0.57) | crease / edge face |
| wave | 0.17 deg (0.50) | crease / edge face |
| fold | 45.3 deg (66.5) | the pillar's top corner |

### Round 7 errors (final geometry and cameras, full resolution; scratch errtab.py; round 6 in brackets)
| View | Outline model to photo | Photo to model | Creases m to p | Creases p to m | IoU |
|---|---|---|---|---|---|
| iso55 | 0.89 / 4.26 (0.64 / 4.01) | 1.03 / 3.43 (0.89 / 3.36) | 1.24 / 3.74 (1.19 / 3.26) | 0.56 / 1.60 (0.53 / 2.05) | 0.968 (0.974) |
| phy | 0.81 / 3.32 (0.81 / 3.96) | 1.01 / 2.89 (1.01 / 3.03) | 1.01 / 3.84 (1.01 / 3.73) | 0.57 / 1.99 (0.61 / 1.62) | 0.966 (0.965) |
| phr | 0.76 / 3.01 (0.96 / 4.33) | 1.20 / 3.41 (1.22 / 3.87) | 0.96 / 2.90 (1.29 / 3.85) | 0.96 / 2.19 (0.68 / 1.87) | 0.923 (0.927) |
| iso45 | 0.46 / 2.03 (0.49 / 1.98) | 0.49 / 2.59 (0.49 / 2.45) | | | 0.970 (0.970) |
| phw | 0.60 / 1.30 (0.60 / 1.27) | 0.64 / 1.43 (0.60 / 1.29) | | | 0.978 (0.978) |
| expl | 1.20 / 4.59 (1.30 / 5.51) | 1.20 / 4.12 (1.30 / 4.74) | 0.99 / 3.22 (1.21 / 3.35) | 1.20 / 3.36 (1.41 / 3.99) | 0.870 (0.872) |
| phyb | 0.49 / 1.87 (0.44 / 1.52) | 0.49 / 1.96 (0.44 / 1.52) | | | 0.971 (0.975) |
| ink | 0.42 / 1.14 (0.42 / 1.26) | 0.42 / 1.27 (0.42 / 1.26) | | | 0.981 (0.982) |
| ind | 0.43 / 1.45 (0.43 / 1.44) | 0.43 / 1.70 (0.43 / 1.50) | | | 0.978 (0.981) |
| frg (validation) | 0.31 / 1.11 (0.44 / 1.09) | 0.31 / 1.27 (0.44 / 1.09) | | | 0.982 (0.983) |
| chee (validation) | 0.45 / 1.32 (0.32 / 1.30) | 0.45 / 1.37 (0.32 / 1.31) | | | 0.981 (0.982) |
| white ISO (held out, camera only) | 0.89 / 4.07 | 0.89 / 2.86 | 1.25 / 3.37 | 0.75 / 1.77 | 0.964 |
With the guard's 3 mm sweep (the nose guard section; before it, scratch err2.json). Better than round 6: phr
(outline p90 4.33 / 3.87 to 3.01 / 3.41, creases model to photo 3.85 to 2.90), expl (every number), phy's outline
p90s (3.96 / 3.03 to 3.32 / 2.89), ink's model-to-photo p90, iso55's photo-to-model crease p90 (2.05 to 1.60).
Worse: iso55's outline median (+0.25 mm), p90 (+0.25) and IoU (0.974 to 0.968) and its crease p90 model to photo
(+0.48); the photo-to-model crease p90s of phy and phr (+0.37, +0.32); the silhouette p90s of phyb (+0.35, +0.44),
ind's and iso45's photo to model (+0.20, +0.14) and phw's (+0.14); the validation views by 0.02 to 0.18 mm. Where
(scratch heat.py maps, iso55 and chee, before the sweep change): the arch and the guard inside and below it (the
guard is a few smooth planes, the photos' a moulded rubber part; in chee the guard's left foot and the arch's right
leg), in iso55 also the near lower band's lens edge and the far end of the top band. The others are not mapped.
Round 6 had the arch bent over the guard, which scored better on the silhouettes for the wrong reason. frg and chee:
cameras refitted to the finished shape only (fitcam, as round 6). Landmarks: test_landmarks_in_leatts_photos.
Blender 5.2.0 (Damien's) renders the final model as 5.2.3 does: iso55 studio and the white ISO with its see-through
lens at half resolution, mean absolute difference 0.36 and 0.38 of 255, p99 3.0 and 4.0 (sampling noise).

### Cameras
iso55, phy and phr frozen at round 5's landmark fit (as round 6); iso45, phw, expl, ind, ink, phyb fitted with the
shape; frg and chee refitted to the finished shape; the white ISO (wiso) fitted to the finished shape only:
-50.83, 0.13, -0.64 deg, 1.464 m, f 8263 px, u0 502.6, v0 -16.5 px (iso55's own: -50.90, -0.34, -1.15, 1.465,
8260, 505.7, -18.5: the same camera, as Leatt's file names say). research/goggle-cameras.json.

### Held-out checks (cameras only)
Neither set is a clean hold-out, and the brief took both as unused: the white ISO was a round 4 source (creases,
teeth, ribs) and one of the four tab-height sources this round; the MY27 8.5 kit Blue_Red views _2 and _3 were the
placement, scale and top lip sources of rounds 3 to 5 and all four the outriggers-on-the-shell and frame-lettering
sources (sections 1 and 2). Neither moved the shape this round.

White ISO (white frame, Light Grey 58 % lens: Leatt SKU 8024070390, sold as "White / Light Grey 58%", e.g.
johnstonsmoto.co.nz/products/le8024070390): its error row is in the table above, in line with iso55 (the same
camera). Rendered white (236, 236, 232), studio light, a see-through 58 % lens; 1:1 beside r6 and r7 (checkpoint
03). The creases read as Leatt's: thin lines on the arch, the foot and the top band where r6 rolled. The far end
of the top band does not: Leatt's sweeps up and rounds over with a lit top, ours steps down at the teeth. The comb shows
through the lens (above). Not compared: the lens's tone (under AgX a 58 % lens looks paler than in Leatt's render,
the bright backdrop seen through it compressed) and what shows behind it (black in Leatt's, most likely its far
strap, which runs straight back behind the goggle there; the backdrop in ours, as the free goggle has no strap). The see-through lens: each of the four lens faces a
Fresnel reflection over a grey see-through, Fresnel taken from outside on both faces (on a back face the Fresnel
node's own inside view gave total reflection past 42 deg and the lens turned into a grey mirror; a Principled
transmission tints at every face and stops the lights' rays: a 150 grey tint left 0.3^4 of the light).

On the helmet (kit views _1 to _4; scratch hcam2.py fits each camera to the helmet's silhouette in the GOGGLE frame,
IoU on the helmet 0.927 front iso left, 0.925 left, 0.927 right, 0.939 back; sheets in checkpoint 08 to 11).
Measured from Leatt's red frame pixels against the model frame's projection (scratch onhelmet_meas.py):
| View | Frame front | Frame top | Frame bottom |
|---|---|---|---|
| left (az 96 deg, 3.8 px per mm) | model 31 px (8.2 mm) ahead | 11 px (2.9 mm) higher | not read (the red runs into the helmet's) |
| right (az -96 deg, 3.9 px per mm) | model 35 px (9.0 mm) ahead | 4 px (1.0 mm) higher | 19 px (4.9 mm) higher |
- Front: the placement has stood 3.9 mm ahead of these views' top lip (y -149 mm) since round 4, because further back
  put his nose bridge into the recessed lens (section 1); at these cameras, fitted to our shell (not Leatt's to the
  mm), it reads 8 to 9 mm. The front iso left view shows the frame 60 to 70 px (13 to 15 mm) to the image left of
  Leatt's; the forward offset explains about 6 mm of that (az 44 deg), the rest is that camera's fit, so it is not
  used for position.
- Bottom: the frame is 100 mm tall where these views read about 106 (the open scale question, section 1).
- How it sits: in both, the frame fills the eyeport, the top band just under the eyeport's brow, the lower band on
  the chin bar's ledge, the outriggers out on the shell behind the eyeport's edge.
- Outriggers: Leatt's plate shows 17 mm wide in the right view, ours 23 mm: ours turns out less once worn, or is
  longer. Not changed (round 5's fit; section 2).
- Strap (back view; helmet.py's, not changed here): ours runs about 23 mm lower on the shell than Leatt's (the strap's
  centre 62 % down the helmet's image height against 54 %), and the shell pokes 1.5 to 1.9 mm through it near
  x +-45 mm, the same with round 6's goggle (scratch strapchk.py); Leatt's has its adjuster slides at the back,
  ours none. For the helmet agent.

## 10. Round 8: the goggle on the helmet (decision 43)
Fixed in the brief's order. Sources first his own gear: his photos 07, 08, 09 (2026-11-12) and Leatt's photos of his
SKUs (the Pinata Teal goggle ISO 8026000150, our iso55; the Pinata Teal kit iso-right of his helmet and goggle);
Leatt's MY27 Blue_Red kit views second (another goggle colourway and outrigger, on an empty helmet). The helmet's
scale everywhere: the 45 mm strap in Leatt's MY27 side view (helmet.py, 0.2484 mm/px), confirmed by his bike's
1483 mm wheelbase in his 07 (0.443 against 0.437 px/mm). Cameras: scratch cams8.json (round 7's four kit cameras,
the Pinata iso-right and his 07, 08, 09, all in the round 7 GOGGLE frame).

### Strap: on the shell, never through it
Round 7's strap (helmet.build_strap) was one ruled band: each cross-section a straight chord 45 mm across, which
sags into the convex shell. Measured over its whole underside (scratch clearmap.py, 19 points across every
section) the shell came up to 2.5 mm through it, worst at the lower half 30 mm either side of the back centre (the
two dark blobs in the back view). goggle.build_strap now lays it on the shell: the centre line where a plane cuts
the shell (strap_layout), each cross-section walked across the surface (45 mm along the shell, not a chord), every
layer offset along the shell's normal: the silicone band (5 mm wide, 0.6 mm, Leatt features: research doc section
4; no photo shows the strap's inside) 0.7 mm off the shell, the 2 mm fabric on it (its inner face 1.3 mm off),
woven selvedges, the doubled run under the right slide, the two slides. Clearance (signed distance of every vertex
and face centre, HELMET frame): band 0.70 mm, edges 1.29, slides 1.86 at the vertices, every face centre over
0.5 mm; round 7's -2.5 mm. test_round8_strap_lies_on_the_shell_with_clearance asks 0.5 mm everywhere and asserts
that round 7's builder, given the same ends, fails it (min below -1 mm). Map: checkpoint 2026-11-13_goggle-r8, 09.

### Strap: its height on the shell
Fitted on his gear first (scratch strapfit2.py: the strap's upper and lower edges picked in the photo, cast through
each fitted camera onto the shell, the model's edges at a plane z0 + tan(rise) y scored as rms mm): his 07 (near
side-on, the strap visible from the outrigger to the back edge) and the Pinata iso-right. His 09's camera is not
used: its fitted roll leaves the goggle 17 deg off his photo's. Plane chosen: centre z -13.5 mm at y -58 behind the
outrigger, rising 3 deg towards the back (STRAP_PLANE); rms his 07 4.5 mm, Pinata 0.3; MY27 left 7.2, right 5.7,
back 15.8. Centre heights on his left side (mm): y -80: -13.8, y 0: -10.2, y 60: -7.3, y 120: -4.2; the back
centre z -2.8 at y 146 (round 7: -14.8, falling towards the back; MY27's back view about +19.6). So the back is
12 mm higher than round 7's and still about 22 mm under MY27's: MY27's strap rises 6 to 10 deg (best fit) on an
empty helmet with a stylist's placement; his 07 puts his own lower, and his 07 wins. The brief's "23 mm too low"
was measured against MY27.

### Strap: the adjuster slides
Leatt's MY27 back view at its strap's scale (217 px across the strap, which projects 44.3 of its 45 mm there:
0.204 mm/px). Each slide body 103 x 252 px; there the strap runs 18 deg out of the image plane (cos 0.952) and its
width 0.986: 22 x 52 mm (SLIDE_L, SLIDE_H). Bodies' centres 402 px apart (x +-41 mm, SLIDE_X), inner ends 302 px
(62 mm). The left slide (his left) a ladder with an embossed LEATT on its outer bar (the LEATT not modelled), the
right one with a triangular grip tab and 3 x 3 dots on its outer end (40 px: 8 mm, TAB); the strap's tail doubled
under the right slide and 30 px (6 mm, DOUBLE_IN) past its inner end. Bars 2.5 mm proud of the doubled strap; the
straight 22 mm crossbars lifted 1.2 mm for the chord's sag over the shell's back (SLIDE_SAG; without it their
bottom faces' centres sat 0.22 mm inside the shell). test_round8_strap_width_slides_and_silicone.

### Outriggers
Which one he has: a black plate with a white vertical LEATT, on both of Leatt's photos of his SKU (the Pinata Teal
goggle ISO 8026000150, both sides; the Pinata kit iso-right, his right). His 07, 08 and 09 are too small to read it
(the goggle about 45 px tall: 2.3 mm a pixel; his 07 shows a dark band behind the frame, his 09 a narrow dark band).
MY27's grey angled outrigger (the kit photos) is another colourway's part and not his. Kept: the plate.
- Thickness 8 to 5 mm (OR_T): the plate's back edge in the Pinata iso-right is 10 px at 4.5 px/mm, seen at 0.53
  (the camera 32 deg off the face's normal): 4.2 mm. Worn, its outer face now stands 6.4 mm off the shell behind the eyeport (round
  7: 9.4); the inner face rests 1.5 mm off it (OR_GAP).
- Width in side view: round 7's plate read 23 mm wide in the MY27 views, Leatt's MY27 part 17 (another outrigger).
  The plate is the same 30 mm long; round 7's strap started beyond it at mid height, round 8's starts in its slot
  (strap_ends, 10 mm inside the back end), so the plate shows 18 mm (left view) and 19 mm (right) between the frame's
  back edge and the strap at mid height (the built parts projected through the two kit cameras at 3.85 px/mm).
- Still not Leatt's: in the Pinata iso-right ours shows its face about 1.6 times as wide as Leatt's plate (110
  against 65 px): worn, ours bends out over the eyeport's edge onto the shell (round 3's mount, OR_BEND), so it faces
  that camera more; that camera also carries the 17 mm front bias.
- Free-goggle error table (scratch errtab.py, round 7 in brackets): the 5 mm plate moves only the model-to-photo
  outline p90s, where the front and side views see the plate's edge: iso55 4.21 (4.26), phy 3.44 (3.32), phr 3.02
  (3.01), phw 1.35 (1.30), expl 4.61 (4.59), ink 1.34 (1.14), frg 1.31 (1.11), chee 1.43 (1.32); medians within
  0.02 mm, photo-to-model and creases unchanged, IoU within 0.001. Kept: the 4.2 mm is his own SKU's plate, worn; the
  free photos' plates are swung to a different angle in every photo (section 9), and round 5 fitted the 8 mm
  footprint with that angle.
- The far one in iso55 and phr (goggle alone): Leatt's stands up to 44 px (iso55) and 42 to 51 px (phr) beyond the
  far pillar over a quarter of the frame's height (scratch farvis2.py); ours shows none, at round 5's turn and at
  every turn tried (or_turn 0.4 to 1.6) and with the plate swung open about its front edge up to 57 deg. Why: the
  far silhouette is the frame's widest point (x 103.7, y 28.2 mm, GOGGLE frame), and the plate's front edge sits
  7.4 mm inside it and 17 mm behind; seen from 45 to 51 deg off the front, a plate from there would have to point
  forward of sideways to show. So Leatt's plate is hinged further out than ours (about at the frame's widest
  point), as an outrigger that pivots on the frame would be. Not changed this round: moving the hinge moves the worn
  plate and the strap's ends, which his 07 and the Pinata iso-right now fit; left for a later round with the
  error table (insensitive to the outriggers: or_turn 0.6 to 0.8 and OR_T 5 mm move it 0.1 to 0.3 mm).

### Position on the eyeport (not moved)
The kit views read our frame 8 to 9 mm ahead of Leatt's (section 9). Checked: (1) the kit helmet is empty: with no
face behind it the goggle sits deeper in the eyeport; on him his face holds it out. (2) Moving it back 0.5 mm
(ty -0.1463, scratch kcheck.py) puts his nose bridge into the frame; it is already at its limit. (3) His 07 (near
side-on) shows no clear offset at 2.3 mm a pixel. (4) The Pinata iso-right camera carries a known 17 mm front bias
(helmet.py) and is not used for position. Fore-aft stays (ty -0.1468).

### Scale
| Source | Reads | Note |
|---|---|---|
| MY27 right view (az -96, 3.9 px/mm, on the helmet's scale) | Leatt's frame 3.9 mm taller than our 100 (top 1.0 mm above ours, bottom 4.9 below) | camera fitted to our shell; "about 106" in the brief was approximate |
| MY27 left view | top 2.9 mm above Leatt's, bottom not readable | |
| Pinata iso-right (his helmet and goggle, 4.5 px/mm) | 1 to 6 mm taller; width ratio 1.08 | camera's 17 mm front bias makes it read large |
| Goggle-alone photos, Leatt's 45 mm strap beside the outrigger | ours 0 to 6 % too large (section 7) | strap measured at the outrigger's depth |
| His photos 07, 08, 09 | cannot tell (2.3 mm a pixel, 4 % is 2 px) | |
| His face and the eyeport (scratch kcheck.py, body built) | x 1.01 clear; x 1.02 clear with the goggle 0.5 mm higher; x 1.03 touches his skin; x 1.04 puts 8 to 28 lens vertices into the shell's eyeport edge at every place tried (ty -0.1478 to -0.1488, tz -4 to -5.5 mm) | the physical limit |
The sources disagree (on the helmet +4 %, alone up to -6 %). Picked: x 1.02 about the lens front (PLACE's fourth
number), 0.5 mm higher (tz -0.0035): the most our helmet and his face take, and half the on-helmet readings' gap.
Frame 211.8 x 103.7 mm (round 7: 207.7 x 101.7); centre line, HELMET frame: top z 43.4 (41.9; Leatt's side views
+41 to +43.5), beak bottom -60.8 (-60.3; theirs -64.6 to -66), top lip y -153.1 (-153.0; theirs -149). The
side-profile test's top lip bound goes from 4 to 4.5 mm for that 0.1 mm (the scale brings it forward). Question for
Damien (open since round 5): his goggle's outer width and its height at the centre would pin it.

### The comb in the white ISO (low priority)
It reads dark grey through the Light Grey 58 % lens (the finger tops 66 to 75 of 255), but so does the white frame's
own inner band and pillar behind the same lens (66 to 96), against 236 to 250 outside: a white part in the goggle's
shade behind a 58 % lens. With the clear lens (phr, red) and the light Iriz (iso55, pink) the comb is frame-coloured.
"Frame plastic in every colourway" stands.

### Round 8 checks
- Tests: all 82 rider tests pass (80 on main plus the two round 8 strap tests). Changed with reasons: the side
  profile's top lip bound 4 to 4.5 mm (the scale, above); the outriggers' anchor test reads the faces at the
  anchor's own row (the 5 mm plate bends out along its length more than its thickness).
- Sheets (checkpoint 2026-11-13_goggle-r8): Leatt | round 7 | round 8 at 1:1 at the four MY27 kit cameras and the
  Pinata iso-right, round 7 re-rendered with main's helmet texture (decision 42), studio light; his photos 07 and 09
  in daylight, their box at 4x (the photo upsampled). His 08's camera in this round's scratch fit (cams8.json) is not
  usable: fitted to the helmet's outline alone (no landmark shows), it settled on a view from the wrong side (the
  render sees the shell's shaded side where his photo shows its lit top), so its sheet was left out of the
  checkpoint (sheet number 07 is unused). head_closeups.py's camera for 08 (research/rider-cameras.json, fitted with
  the bike) sees the right side and is the one to use. His 09's roll leaves the goggle 17 deg off. His 07 is the one
  of his photos that measures the strap.
- Blender 5.2.0 (Damien's) renders the worn goggle at the left kit camera and the free goggle at iso55 as 5.2.3
  does: half resolution against 5.2.3's full resolution downsampled, mean absolute difference 0.73 and 0.37 of 255
  (after a 3 px blur 0.46, p99 6: sampling noise at 48 samples).

## 11. Round 9: slides, woven strap, hinged outriggers (decision 45)
Fixed in the brief's order. Sources: Leatt's MY27 Blue/Red kit back view at 1:1 (0.214 mm/px along the strap, 0.207
across: round 8's 0.204 mm/px with the strap turned 18 deg out of the image plane), the Forge back 8024070250 and the
Neon Yellow back 8022010380 for the parts, Leatt's 5.5 back photos on their shop for the slide colours (29 images,
scratch dl/full), the Pinata Teal goggle ISO 8026000150 (iso55) and kit iso-right, his photo 07.

### Slides (goggle.slide_parts; constants SLIDE_*, TAB_*)
Each slide is a flat moulded frame (2.2 mm, SLIDE_T) with rounded outer corners (1.8 mm, 8 px) and soft edges (0.6 mm
round: the highlight along every bar), bent to the strap's curve; 22 x 52 mm outside as round 8. Rails 3.8 mm above
and below the strap (15 to 17 px show past its edges), their inner corners square where the bars meet them.
- How the strap threads: the strap comes from the left outrigger under the left slide's end bars (hidden, not
  built), the tail comes up out of the slot beside the left slide's centre bar (a quarter round over 1.6 mm,
  TAIL_FOLD), passes under that bar and runs doubled over the strap to the right slide, folds round its left end bar
  and centre bar and goes into the slot beside its outer bar.
- The left slide: one centre bar (x 772 to 797 px: 5.3 mm) with an embossed LEATT (14 mm long, 3 mm letters, a normal
  map) that stands 4.0 mm off the strap (SLIDE_CBAR_T) over the tail: its wall catches the light and the tail beside
  it lies in its shadow (x 797 px), as in the photo.
- The right slide: end bars 3.6 mm (17 px), a centre bar, and the grip tab on its outer bar (x 1240 to 1280, y 885
  to 1010 px: TAB_POLY), sloped at the top, with Leatt's triangle (x 1238 to 1278, y 890 to 935 px) above a groove
  and a staggered field of dimples (10 px pitch).
- The doubled tail (goggle.build_tail): from the left slide to the right slide's outer bar; two folds round the
  right slide's bars standing 3.0 mm over the tail (ROLL_H), each a parabola across (the photo's folds brighten
  steadily, 93 to 154 of 255 lit from his right; an ellipse's flat top rendered flat), rounded over 2 mm at the
  strap's edges.
- Colour: no photo shows the Pinata Teal's slides. In Leatt's back photos they are moulded in a colour of the strap's
  design: the strap's base on Forge (white), Fuel (teal) and Neon Yellow (cyan), its edge colour on MY27 Blue/Red and
  Royal (navy), black or an accent on the others. By the brief's rule (Forge: the strap's base; MY27: its edges) and
  with no edge colour on the Pinata strap: the print's base colour where the slides sit, the median of
  goggle_strap_print.jpg's middle band over the u the slides cover (scratch slidecol.py): 112/159/138 (top band
  123/165/145, bottom 91/151/125). The MY27 comparison renders use navy 30/42/70 (sRGB; AgX desaturates bright blues).
- Test: test_round9_slides_are_moulded_frames (top faces cover 38 % of the left slide's outline and 66 % of the
  right one's; the left centre bar over the tail stands higher off the shell than any bar of the right slide).

### The line across the strap (item 3)
Leatt's is a soft fold, not a step: a crease where the doubled run starts under the right slide (x 1115 px) and the
gap between the two folds, dark lines 2 to 4 px wide (0.4 to 0.8 mm). Modelled as the fabric pressed down to a quarter
of its thickness over 0.4 mm (CREASE_W, CREASE_DEPTH), sampled at 25 points within 1.2 mm of each crease.

### Woven elastic (goggle_strap_art.py; textures goggle_strap_print.jpg, _print_n.png, _weave.png, _mask.png)
Measured in the MY27 back view at 1:1 (scratch fabstat.py, acfcmp.py): knit loops about 0.65 x 0.45 mm (the grain 3 x
2 px), a jacquard repeat of 1.9 mm along (autocorrelation peak at 9 px), the albedo spread 15 to 24 % of the mean in
the blue body; woven selvedges 5.2 mm (25 of the strap's 217 px at each edge; the brief's "about 4 mm"), finer knit
with light flecks on navy and a faint diagonal rib.
- Built as a detail tile 19 mm along by the strap's width at 24 texels a mm (29 loops, 10 jacquard repeats), repeated
  along the strap (repeat 645 / 19): its red channel the relief (1.4 mm range, a bump node at strength 0.3), its green
  the albedo factor (body mottle 0.75, the selvedges' dark ground and flecks normalised to a mean of 1), multiplied
  into the print where the mask is white (not on the LEATT). At the print's 6.6 texels a mm the renders' grain was
  1.5 px wide at 1:1 against the photo's 0.9; with the tile it matches in the body.
- The print's normal map keeps only the seam, the edges' 0.35 mm round-over and the raised LEATT (0.8 mm, a silicone
  print: its walls show in the Pinata kit iso-right).
- The strap's centre line on the shell is now 645.0 mm (round 8: 618.8; the hinged outriggers put its ends 13 mm
  further forward): STRAP_LEN_UV and the repeat follow it. Its printed face, 3.3 mm out, is 648.4 mm along the centre
  line, so a tile reads 19.1 mm there (test_round9_woven_strap_scale: the centre line's length over its u span); the
  strap wraps a cone-like shell, so its edges run 662.9 and 630.5 mm (19.4 and 18.6 mm a tile), as an elastic
  stretched round it would. A median of every edge's ratio read 19.36 (the stations are densest where it bends).
- The doubled tail's u followed the strap beneath it, so up out of the slot and over the rolls its face ran up to 4.2
  times as far as its u (p90 3.1, scratch tilecheck.py): the weave stretched on the folds' flanks. Its u now follows
  its own centre line (goggle.build_tail); every centre edge of the main run and the tail is within 5 % of 19 mm a
  tile (main 0.976 to 1.032 of it), the test's new bound.
- The band's side faces (goggle_strap) keep round 8's four rows of vertices (outer bottom, outer top, inner top,
  inner bottom edge, one per station): test_helmet's width check reads the strap's width from them (45 mm). Its
  ends are caps on goggle_strap_band.
- MY27 back at 1:1 (box renders without the denoiser, which smooths the weave away at low samples): luminance sd /
  mean at the high pass body 0.164 against the photo's 0.256, selvedges 0.328 against 0.564. Still flatter than
  Leatt's.
- The Pinata strap in the kit iso-right (scratch grain.py: its coloured pixels, the luminance's sd over a 3 px blur
  over the mean, and the HSV saturation): the photo's grain 0.137 and saturation 0.92, ours 0.188 and 0.65 (the print
  texture itself 0.79); Leatt's goggle ISO 0.106 and 0.84. A trial at MOTTLE 0.5 read 0.159 and 0.65: the mottle is
  part of the grain, none of the dullness. The same measure on the MY27 back (box 716,864 to 1016,1004): photo
  0.216 and 0.93, ours 0.155 and 0.61. So the two photos pull apart on grain: the MY27 jacquard (two yarn colours)
  wants more, the Pinata sublimation print less. MOTTLE stays 0.75 (the brief's MY27 measure). Both agree on the
  colour: our strap renders a third less saturated than either photo (0.61 to 0.65 against 0.92 to 0.93), round 8's
  strap too: the print is sampled from photos and shown under AgX, which desaturates bright colours. A later round
  should calibrate the print through the renderer (render, measure, correct). In his photo 07 at its own
  resolution the strap reads as round 8's, a little darker; at 4x the weave shows as a fine speckle the blurred
  photo cannot show.
- The back view's light (camera "lights" in goggle_views.py): a key from his right and behind (-1.8, 0.9, 1.0 m,
  260 W), a fill from his left (1.8, 0, 1.0, 160 W), a dim top (50 W). The front studio rig lit the tail's folds flat
  and a rig symmetric about the strap shaded both folds alike; a plain grey material showed the geometry was right.
- The Pinata print against Leatt's two photos of it: sampled from the goggle ISO (the docstring of
  goggle_strap_art.py); in the kit iso-right the same hues run in the same order back from the outrigger (orange and
  yellow, pink, purple, pink round the LEATT, yellow, teal) but that view cannot place them along the strap: its
  camera's 17 mm front bias maps the outrigger and frame onto the strap's first 40 mm (scratch printmap.py,
  printunwrap.py).

### Outriggers hinged on the frame's widest point (item 4)
Each plate now hinges on the frame's widest point at the outriggers' centre height (x 103.8, y 28.4 mm, GOGGLE
frame), its outer face's front edge on that line, 30 mm long (OR_LEN, Leatt ISO), turned about the hinge.
- Hinge side: with the inner face's front edge on the hinge, the plate stood 5 mm beyond the frame's side in the
  front photos at any turn (outline p90 1.3 to 1.4 mm became 3.6 to 3.9); with the outer face's, it hides behind it.
- Length: 46 mm (to round 8's back end) showed the plate 197 px wide between strap and frame in the Pinata iso-right;
  30 mm shows 122 to 129 (round 8 156, Leatt 69).
- Free, the plates swing: each Leatt photo lays the strap its own way, so the error table fits each photo's turn per
  side (scratch errtab9.py: the best silhouette IoU at half resolution over -10 to 75 deg). Far plates: iso55 55 deg,
  phy 55, phr 65; the front and back photos -10 (hidden behind the frame). OR_FREE_TURN 55 (his SKU's ISO). The IoU
  cannot see a near plate (the strap's cut hides its back end), so its turn is set by where the strap leaves it
  (scratch nearplate.py, the plate's back edge through the fitted camera): iso55 0 deg (822 px against the strap's
  exit at 826, goggle_strap_art.ISO_X_EDGE; at 55 deg it read 777 and the plate 175 px wide against Leatt's 85), phr
  0 deg (930 against 930). Far
  silhouette edge against Leatt's (scratch farvis3.py, median per row): iso55 round 8 -9 px, round 9 -3; phr round 8
  -43 px, round 9 at 65 deg -6. Section 10's farvis2.py compared Leatt's dark pixels beyond the pink with our
  outrigger beyond our frame; part of Leatt's black block there is the frame's own black side, so the silhouette
  edge is the measure.
- Not matched (1:1 crops): in iso55 Leatt's far side is a dark band 48 px wide (x 1657 to 1705) with two clip slots
  above and below the lens post, seen from inside; ours shows the pink frame's side there and the plate as a 12 px
  edge (1690 to 1702). Leatt's near plate tapers, its top edge rising towards the frame and its back corners
  chamfered; ours is a rectangle.
- Worn, the strap pulls each plate in until its inner face rests on the shell (OR_GAP 1.5 mm): the shell widens
  upwards, so the plate twists, its turn growing linearly from 0 deg at the bottom row to 13.0 at the top, each row
  the smallest that clears. Anchor (the strap's end) x 103.6, y 48.5, z -4.8 mm (round 8: 104.4, 64.3, -4.8).
- Strap fit at the same plane (scratch strapfit2.py, rms mm, round 8 in brackets): his 07 4.2 (4.5), his 09 8.0
  (8.9), Pinata iso-right 1.9 (0.3), MY27 left 6.2 (7.2), right 5.6 (5.7), back 15.0 (15.8).
- Clearance off the shell (every vertex and face centre): band 0.60 mm, edges 1.29, slides 3.14, outriggers 1.46.

### Error table (free goggle, full resolution; outline and crease mm, model to photo / photo to model, median/p90)
| View | Turn +1/-1 | Outline round 8 | Outline round 9 | IoU 8 | IoU 9 |
|---|---|---|---|---|---|
| iso55 | 55/0 | 0.89/4.21 1.03/3.43 | 0.89/4.26 0.89/3.89 | 0.968 | 0.973 |
| phy | 55/0 | 0.83/3.44 1.01/2.89 | 0.90/4.09 1.01/3.33 | 0.966 | 0.969 |
| phr | 65/0 | 0.76/3.02 1.20/3.41 | 0.76/3.12 1.07/2.64 | 0.923 | 0.957 |
| iso45 | (none) | 0.46/2.03 0.49/2.59 | 0.46/2.03 0.49/2.59 | 0.970 | 0.970 |
| phw | -10/-10 | 0.60/1.35 0.64/1.43 | 0.64/1.43 0.64/1.49 | 0.978 | 0.976 |
| expl | 0/65 | 1.20/4.61 1.20/4.10 | 1.07/4.73 1.07/4.09 | 0.871 | 0.892 |
| phyb | -10/-10 | 0.49/1.87 0.49/1.96 | 0.49/1.97 0.49/1.97 | 0.971 | 0.973 |
| ink | -10/-10 | 0.42/1.34 0.42/1.27 | 0.42/1.29 0.42/1.46 | 0.981 | 0.980 |
| ind | -10/-10 | 0.43/1.45 0.43/1.70 | 0.48/1.65 0.48/1.73 | 0.978 | 0.976 |
| frg | -10/-10 | 0.31/1.31 0.31/1.27 | 0.44/1.38 0.44/1.38 | 0.982 | 0.980 |
| chee | -10/-10 | 0.45/1.43 0.45/1.37 | 0.45/1.44 0.45/1.58 | 0.980 | 0.979 |
Creases: iso55 1.19/3.31 0.53/1.60 (round 8 1.24/3.74 0.56/1.60), phy 1.01/3.72 0.81/3.84 (1.01/3.84 0.57/1.99),
phr 0.96/2.94 0.96/2.21 (0.96/2.90 0.96/2.17), expl 0.99/3.27 1.29/3.88 (0.99/3.23 1.20/3.36). The views that see
the far plate gain (phr IoU 0.923 to 0.957, expl 0.871 to 0.892); the front views lose up to 0.002 of IoU and
0.13 mm of median (frg): at -10 deg the plates' front edges still stand on the silhouette.

### The plate face in the Pinata iso-right (item 5)
Measured as the run of outrigger pixels between the strap and the frame (scratch platew.py, the worn build
z-buffered through the fitted camera): round 8 156 px, round 9 122 to 129, Leatt 69. Round 8's plate bent out over
the eyeport's edge (OR_BEND) and faced the camera; round 9's is flat and twisted on its hinge, 30 mm long, and still
1.8 times as wide as Leatt's. Not resolved: the plate seen at about 4 px a mm along it is 30 mm in full; Leatt's
reads 17 to 18 mm between strap and frame, and the same plate in Leatt's goggle ISO reads 85 px (about 20 mm, near
side). Either Leatt's strap end covers the plate's back 10 mm (ours enters it at mid thickness) or the camera's 17 mm
front bias stretches ours: a question for a later round. A lead from iso55 at 1:1 with the near plate straight back:
its back edge sits where Leatt's does (822 against 826 px) but Leatt's pink side face starts at 920 px and covers the
plate's front, ours at 963: the plate shows 141 px against 90. So the excess is at the front, where Leatt's frame
side overlaps the plate (its hinge inboard of the side face), not at the strap end.

### The comb (item 6)
Not done this round (items 1 to 5 first, as the brief asks). Done in round 10 (section 12).

### What depends on the helmet's eyeport edge
The coordinator, during this round: the helmet agent (decision 44) found the shell's eyeport side edge 35 to 40 mm
too far forward and the brow about 20 mm; a later joint round moves the helmet front and the goggle's worn fit
together. Nothing in round 9 is tuned to the current port edge (round 8's bend over it, OR_BEND, runs only with
OR_HINGE False; the hinged plate is flat, its rows only turned). Built from Leatt's goggle photos alone, so they hold: the hinge on the frame's widest point (x 103.8, y 28.4
mm), the plate's 30 mm (OR_LEN, Leatt ISO), the free turns, the free error table and its far edge measures, the
iso55 lead for item 5 (frame side against plate front), the slides, the crease, the weave and the tail's folds.
Worn on the current shell, so they move with it: the plates' twist (0 to 13 deg, each row turned in until it clears
the shell by OR_GAP), the anchor (x 103.6, y 48.5, z -4.8 mm), the strap's length (645.0 mm) and so STRAP_LEN_UV,
the weave's repeat and the print's mm along the strap (test_round9_woven_strap_scale fails if the strap grows by
more than about 7 mm or shrinks by 13, which forces the update), the slides' stations along the strap, the strap fit rms (his 07 4.2,
Pinata 1.9, MY27 views), the clearances, and the plate face's run in the Pinata iso-right (122 to 129 px against
Leatt's 69). The worn-fit tests pass on the current shell; they are not a target for the port edge.

### Checkpoint and checks
renders/checkpoints/2026-11-15_goggle-r9/: Leatt (or his photo) | round 8 | round 9, the same photo pixels, at 1:1
unless noted: 01 MY27 back (slides, fabric, crease; the back light rig, the MY27 print and navy slides), 02a iso55 and
02b phr (free goggle, near plates 0 deg, far 55 and 65), 03 the Pinata iso-right (its camera's 17 mm front bias
shifts ours right), 04 his photo 07 in daylight at 4x (rendered at 4x; the photo is a motion-blurred pan, so the
renders show detail it cannot). No Forge back-strap sheet: no camera is fitted to that photo and the free goggle carries no
strap. The comb sheet is not made (item 6 not done).
Blender 5.2.0 (Damien's) against 5.2.3: his 07 in daylight at 2x, 32 samples, pixel identical (mean difference 0.00).
build_rider.gear_material in 5.2.0 builds the strap's material with the weave tile (print, normal map, tile, mask),
the slides' with their normal map and kit.py's bump material as before. 03 and 04 were rendered before the tail's u
and the selvedges' vertex order changed; 03 rendered again from the final build differs by 0.06 of 255 on average.
goggle_views.py no longer places the studio's lights in daylight (daylight removes them: round 9's per-camera light
rig crashed the daylight views).

## 12. Round 10: grain, plate outline, chassis band, comb (decision 48)
Done in the brief's order. The worn fit (the helmet front, PLACE, the plates' worn twist, the strap layout, the plate's
worn width) is decision 47's and not touched here; the plate's new outline moves the worn plate's top twist from 13.0
to 12.25 deg by itself (outrigger_grids rests it on the shell, scratch wornturn.py). Look: decision 46 (Standard for
the studio sheets, AgX - Punchy 0.6 EV down in daylight). Sources: Leatt's goggle ISO renders (White 8024070390,
Pinata 8026000150, Black, Neon Yellow, Forge), the Royal Clear front photo (phr), the exploded view, the Pinata kit
iso-right, the MY27 back view.

### Strap grain (item 1; goggle_strap_art.py, goggle_views.py)
Round 9's tile read as glitter: fibre flecks 0.1 mm and an albedo factor of 0.15 to 2.2 (40 % of the brightest print's
texels reflected more than all the light), loop rows 0.45 mm apart (2 px in the Pinata view). Both photos' power
spectra (scratch psd2d.py) hold two families of diagonal waves and nothing finer: MY27 back 3.48 px (0.745 mm) at 68
and 109 deg to the strap, the Pinata 2.9 to 3.9 px at 44 and 136 deg. The tile is now those two waves (a crosshatch,
WAVE_MM 0.745, 9 periods along the 19 mm tile), its phase wandering 1 rad over 0.8 mm, plus a coarse relief of the
loops' clusters (blue channel); albedo factor 0.35 to 1.3, the shader capping the albedo at 0.9 and fading the tile by
the pixel's footprint on the strap (a driver on the camera's pixel angle: full crosshatch to 0.25 mm a pixel, none
from 0.45 mm; the coarse relief from 0.5 to 1.0 mm). Cycles has no mip-maps, so this is what stops the shimmer. Bump
strength 0.35.
| Check | Round 9 | Round 10 | Leatt |
|---|---|---|---|
| Pinata grain at 1:1 (scratch grain.py, strap only) | 0.157 | 0.130 (MOTTLE 0.35) | 0.125 to 0.147 |
| Tile power under 0.5 mm, relief / albedo | 17 % / 30 % | under 3 % / 6 % | |
| Whip distance (2.7 mm a px, 128 samples, OIDN): strap's registered frame difference, weave over no weave | 1.72 | 1.00 | |
| The same at the near camera | | 1.05 | |
The whip test: two frames, seed 1 and seed 2 with the camera moved 3 mm, with and without the tile, the second frame
shifted back by the image's own sub-pixel offset (measured on the no-weave pair), the strap's mask from a mask render
(scratch whip.sh, whipcmp.py). Test: test_round10_strap_weave_band_limited (fails on main: 0.17 and 0.30).

### The plate's outline (item 2; GP or_*, OR_CHAMFER, OR_FRONT_CUT, or_u)
Leatt's plate in his goggle photos tapers and its corners are cut; round 9's ran 63.5 mm at the frame to 58.7 at the
back with square corners. Fitted on the plate's top and bottom edges in iso55 (near plate, 0 deg) and phr (far, 65 deg)
(scratch plcmp.py: Leatt minus ours, rms), with the full error table over ten views as the check (errvar.py):
or_back_h 55.1 mm (58.7), or_top_in 1.3 (3.2), or_bot_in 1.6 (3.5), or_back_dz 1.45 (0.6); the back corners cut at 45
deg, 2 mm at the top and 3 mm at the bottom (OR_CHAMFER), the front corners cut back 1.9 mm (OR_FRONT_CUT, so the
front edge stays where round 9's showed it). The plate is 63.5 mm tall at the frame and 50.1 at its back. or_u puts a
column of the grid on each cut's start, so the cuts are straight.
| Edge rms, mm (top / bottom) | Round 9 | Round 10 |
|---|---|---|
| iso55 | 1.73 / 2.65 | 1.08 / 1.52 |
| phr | 1.31 / 1.29 | 0.53 / 1.00 |
Error table (free goggle, outline p90 model to photo / photo to model, IoU; round 9 in brackets): iso55 IoU 0.9750
(0.9732); phy 4.05 / 3.39, 0.9704 (4.09 / 3.33, 0.9690); phr 0.9586 (0.9569); expl 4.53 / 4.08, 0.8921 (4.73 / 4.09,
0.8925); phyb 2.02 / 1.97, 0.9723 (1.97 / 1.97, 0.9733); the front views lose a little: phw 1.49 / 1.63, 0.9750 (1.43
/ 1.49, 0.9759), ink 1.42 / 1.69, 0.9787 (1.29 / 1.46, 0.9795), ind 1.77 / 1.94, 0.9748 (1.65 / 1.73, 0.9756), frg
1.47 / 1.53, 0.9796 (1.38 / 1.38, 0.9804), chee 1.51 / 1.60, 0.9783 (1.44 / 1.58, 0.9791). Turning the free plates in
the front views to -5 or -15 deg instead of -10 does not win it back (phw / ink 1.51 / 1.71 and 1.45 / 1.69 at -5).
Not matched: Leatt's top edge rises more steeply into a black rim along the frame top; his frame's side face covers
the plate's front (920 px in iso55 against our 955). Test: test_round10_plate_tapers_with_chamfered_back_corners
(fails on main: 63.5 and 58.7 mm).

### The frame's side where the plate meets it (item 3; CHASSIS_*, build_frame, chassis_slots)
What it is: in Leatt's ISO the band from the lens's far edge to the silhouette (iso55 x 1655 to 1703 px, y 790 to 1150)
is black in the White, Black and Pinata colourways alike, takes the plates' colour where the plates are coloured (the
Neon Yellow's purple chassis rim in phy, the Forge's grey back) and shows the strap through its two slots (teal in
the Pinata ISO, green in phy, teal in phr); on the near side a black rim runs on from the plates' edges along the
frame. It is the chassis that carries the plates and the strap's clips, not the coloured shell. Built: the frame's
ring gaps a (the bevel up from the lens), b, l, m and n (the lens's seat and the plate behind it) are goggle_chassis
(black, glossy) where the lens edge's |s| is 85 mm or more. The slots, measured in the white ISO by per-row and
per-column luminance (scratch slotprof.py) and mapped through gap a's middle (slotz.py): y 835 to 903 and 1025 to
1094 px, lens edge z 19.4 to 6.5 and -15.9 to -28.5 mm; across, x 1673 to 1696 px, the whole width of gap a; near
black inside (L 1 to 3 against the face's 18 to 23). Each is a pocket 1.5 mm deep cut into gap a between 0.12 and
0.92 of its width: side walls and floor goggle_slot (no specular: as glossy chassis the shallow pocket read 41 to 54,
brighter than the face; now 4 to 10 against the face's 36), the end walls chassis. Square to the face the floor ran
0.17 mm into the lens's groove and parallel to the lens it came within 0.24 mm of the front rim's face, so half its
part along the lens normal is taken off: the floor is 0.20 mm or more above the lens front and 0.66 mm or more inside
the moulding (scratch slotchk.py). Each pocket face has its own vertices (sharp edges under smooth shading).
Not matched: our band reads brighter (36 against 18 to 23) and narrower: Leatt's has a flat face 34 px wide with a lit
outer rim, ours the bevel and the crease; inside Leatt's slots a clip tab and the strap show, ours are empty. phr:
Leatt shows red 1600 to 1615 px, a gap, then black 1625 to 1680; ours the seat (1597 to 1611) and the bevel (1612 to
1630). Test: test_round10_chassis_band_has_two_clip_slots_a_side (fails on main: no slots).

### The comb (item 4; RIB_*, rib_outline, rib_fillet, rib_cut, build_nose_ribs)
Leatt's gaps back-projected onto the comb's front face (scratch combbp.py; ds/dz from upright, s his left):
| Gap | phr s mm (top to bottom) | z mm | ds/dz | iso55 s mm | z mm | ds/dz |
|---|---|---|---|---|---|---|
| lobe / finger, his right | -26.8 to -21.6 | -23.9 to -29.0 | -1.05 | -27.6 to -24.3 | -24.8 to -27.3 | -1.30 |
| two fingers, his right | -17.0 to -11.1 | -18.3 to -24.8 | -0.91 | -19.4 to -12.2 | -18.7 to -25.2 | -1.16 |
| centre finger, his right | -5.8 to -2.2 | -16.7 to -24.4 | -0.49 | -9.2 to -3.5 | -16.7 to -24.8 | -0.77 |
| centre finger, his left | 4.9 to 5.6 | -19.4 to -24.4 | -0.08 | 1.8 to 3.5 | -18.9 to -23.9 | -0.44 |
All lean the same way on both sides: a common shear plus an outward fan. Seen from his right, depth reads as a shift
(1 mm deeper reads 0.75 to 1.15 mm further to his right in phr, 0.94 to 1.45 in iso55; scratch combdepth.py). With the
tongues leaning back towards his nose by T mm a mm above z -29 mm, the centre finger's two sides lean alike at T 0.35
in phr and 0.45 in iso55 (combfit.py), and the two views then agree on the fan: 0.15 to 0.27 at the centre finger,
0.64 to 0.78 at the next gap, 0.80 to 0.99 at the outer one (T 0.35 to 0.45). Each view's gaps centred on s 0 by
the centre finger's pair need 3.8 mm (phr) and 2.1 mm (iso55) of offset: the cameras' calibration at the nose, as
round 5's 3.6 mm. phr at 3x (scratch z_combphr.png) shows seven tongues: a lobe 16 mm wide whose top falls outward,
two fingers and the centre finger; the gap between lobe and finger is a wedge open at its top (the finger's side
nearly upright, 0.18; the lobe's leaning 0.81; px 1333,1023 to 1348,1060 and 1326,1037). Built from T 0.40 (RIB_GAPS,
RIB_TOPS, RIB_LOBE_TOP): gaps with round bottoms at |s| 3.9, 13.0 and 25.4 mm (z -24.6, -25.0, -28.4), leaning 0.20,
0.67 and 0.18 / 0.81, 2.4, 2.4 and 1.2 mm wide; tops -16.4 (centre), -16.7 to -17.1, -18.5 to -20.2, the lobe -23.5
to -23.9 out to |s| 33 then falling to -28.6 at 41 mm; tip corners 2.4 mm round (Leatt's about a third of a finger's
width; round 9 1.8). The closed slots are gone (Leatt's open wedge is where they were). On him the comb is cut 0.5 mm
short of his skin as before, now as the level line of the outline's signed distance and rib_clear's columns
(contourpy), so leaning slots cut cleanly.
Not built: the depth lean itself. The frame's nose bridge lies 0.3 mm behind the comb's front (bridge_depth 2.5 mm
at the centre), so tips 5 mm deeper would sink behind it; Leatt's dark bridge shows above and behind his tongues, so
his bridge sits deeper than ours. Until the bridge is checked, our gaps read 15 to 20 deg less lean than Leatt's on
his right side and lean outward on his left where Leatt's read upright (phr) or inward (iso55). Also not matched:
Leatt's far-side tongue tops read 2.7 to 6.7 mm lower than the near side's in phr (C -16.7 against E -19.4, B
-18.3 against F -25), which a symmetric comb cannot show; the comb still runs through the inner lens (2.8 to 3.4 mm
deep) at |s| over 8 mm, as since round 5. Test: test_round10_comb_has_seven_leaning_tongues (fails on main: five
tongues at z -24 mm); test_round5_offsets_teeth_and_nose_ribs's comb checks now use RIB_TOPS and no longer expect the closed slots.

### Checkpoint and checks
renders/checkpoints/2026-11-15_goggle-r10/: 01a the Pinata strap at 4x (on the helmet, 128 samples, Standard), 01b
and 01c the grain at whip distance (round 9 and round 10: two frames each, with and without the tile, the
registered differences x4; 128 samples, daylight look), 02 the plate in iso55 at 1:1, 03 the chassis band in iso55
at 2x (Leatt White and Pinata, round 9, round 10), 04a and 04b the comb through Leatt's see-through lenses (phr
Clear 83 %, iso55 Iriz 78 %) at 2x. Items 2 to 4: free goggle, 64 samples, OIDN, decision 46 Standard.
Seen at 4x, the new weave reads as long parallel diagonal ripples, more regular than the photo's soft twill: the
phase wander (1 rad over 0.8 mm) is too little to break them up at that zoom.
Blender 5.2.0 (Damien's) against 5.2.3: the free goggle in iso55 (slots, chassis, comb, plate), 16 samples, pixel
identical (mean difference 0.00).
Item 4's second half, the vent sawtooth's 1 to 2 mm steps, not done this round (the comb took the time).
Item 5 (the Forge back-strap sheet) not done: no camera is fitted to that photo.

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
