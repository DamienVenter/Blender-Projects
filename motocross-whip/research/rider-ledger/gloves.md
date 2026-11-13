# Gloves ledger: Leatt Moto 2.5 X-Flow, Black (module `scripts/rider/gloves.py`)

Damien's choice (2026-11-13, decision 32): the black 2.5 X-Flow seen in his photos 06, 08 and 09
(research/rider-gear-leatt.md section 5). Leatt US MY26 "Gloves Moto 2.5 X-Flow" Black 6024090150 to 154 (S to XXL),
current MY27 "Moto 2.5 X-Flow Glove" Black 6027010260 to 264 (same design). Leatt's views: `reference/leatt-gear/
gloves/` (MY26 back and palm of the RIGHT glove; MY27 "other angle" back and palm of the LEFT glove).

Every number below has its source. Frames: body.py's MB rest frame; the hand frame of `gloves.hand_frame` (origin
the wrist joint, x toward the thumb, y toward the middle finger's knuckle, z out of the palm); s = distance along the
forearm axis from the wrist joint (negative up the arm).

## 1. Shape (component 1, 2026-11-13)

### Size
| Quantity | Value | Source |
|---|---|---|
| Leatt glove chart (men) | XS 18-19 / 18.5, S 20-21 / 19, M 21-22 / 19.5, L 22-23 / 20, XL 23-24 / 20.5, XXL 24-25 / 21, XXXL 26-27 / 21.5 (cm: knuckle circumference / hand length) | `https://us.leatt.com/cdn/shop/files/GloveMen_SizingChart_04-02-2026.jpg` (the Size Guide of us.leatt.com/products/moto-2-5-x-flow-glove, fetched 2026-11-13; not saved under reference/leatt-gear/sizing, which this brief does not let me edit) |
| His knuckle circumference | 21.9 cm (21.5 to 22.2 within 5 mm of the knuckle line) | body.npz: convex hull of the cut through the index and little fingers' knuckle joints, thumb out (`hand_measures`, test) |
| His hand breadth at the knuckles | 9.5 cm | same cut |
| His distal wrist crease | hand y = +5 mm | body.npz: the palmar skin's valley along the hand's mid line (21.3 mm at y -5..0, rising from +10) |
| His hand length (flat) | 21.4 cm | crease to the middle knuckle joint 113.9 mm + middle finger bones 39.0 + 31.7 + 31.0 mm - 1.3 mm (skin short of the last bone's tail) |
| Size chosen | **L** (22-23 cm, 20 cm) | the chart's note measures the circumference only; 21.9 cm sits on the M/L line, and his long fingers (21.4 cm: XXL by length alone; 11.6 % of his stature against 10.8 % in Drillis and Contini) push to the larger. **Question for Damien.** |

The size does not change the modelled shape: the glove is his hand plus the fabric (below); a size L glove's
fingers are about 1 cm shorter than his, which a stretch-mesh glove takes up.

### Fit over the skin
| Quantity | Value | Source |
|---|---|---|
| Fabric over the hand | outer surface 1.0 mm over the skin | X-Flow mesh and NanoGrip are "ultra-thin" (Leatt features); 0.6 mm fabric + 0.4 mm ease, EST |
| Fabric bridging | spans skin grooves up to 1.5 mm deep (nail folds, joint creases) | MakeHuman's nail fold showed through the first try (close-up render); stretch fabric bridges such detail. At 40 smoothing passes unclamped the palm lifted 5.5 mm over the palm hollow: clamped |
| Fingertip room | 2 mm beyond the skin's tip, fading over 10 mm | EST (seam allowance at the tip, Leatt's photos show blunt rounded tips) |
| Cuff outer surface | 4.0 mm over the skin, ramping from 1.0 mm over s = +9 to -5 mm | goes over the jersey sleeve's end: elastic 1.2 mm + jersey under it. **Interface for the kit agent: the jersey sleeve's outer surface must stay within 2.8 mm of the skin from s = -10 mm to the cuff top (s = -27 mm), or end under the cuff.** |
| Cuff band height | 32 mm, from the wrist crease (s +5) to s = -27 mm | Leatt's photos: band 180 px; scale 0.175 mm/px (back view) and 0.182 mm/px (palm view) from the glove's knuckle breadth (his 95 mm + 2 mm fabric) over 556 and 534 px |
| Hem | top edge rolled (half-round of the 1.2 mm wall), turned in 8 mm | EST (bound cuff edge in Leatt's photos) |
| Strap | hook-and-loop, 24 mm wide, 1.6 mm thick, from 28 deg past the back's middle toward the little finger, round the thumb-side edge to 22 deg onto the palm | Leatt's photos: strap 140 of the band's 190 px tall; its free end on the thumb side (back views) with the hook patch on the palm side by the thumb (palm views) |
| White pull | 28 x 7.5 x 2.2 mm, at the strap's end on the thumb-side edge, in the strap's upper part | Leatt's back view: 160 x 40 px at 0.175 mm/px |

### Construction of the mesh
- The glove skin = the hand's own skin distal of the clean 20-vertex edge ring round the wrist (s = -18.8 mm, span
  6.4 mm), plus 4 rings cast from the forearm axis onto the skin up to the cuff top: every glove vertex is a fixed
  combination of body vertices (`C`), so its skin weights are the same combination of the body's weights (the
  right glove uses the right hand's own weights: the body's mesh is exactly symmetric, its weights are not, up to
  0.17 apart on the hands). One Catmull-Clark step (the body renders with subsurf 1, so the glove's base is the
  rendered skin), then the offset along normals, the fingertip room and the bridging.
- 15,978 vertices for both gloves (glove skin 7,373 each incl. the hem, strap 504, tab 112 per hand).
- hide_body: 1,629 vertices per hand (the hand distal of the wrist ring; the ring itself stays so the skin's edge is
  8 mm or more inside the cuff).
- UV charts like the glove's pattern pieces: hand back, palm, two edges, the webs (planar along their normals), each
  phalanx a cylinder about its bone (seam along the palm side's middle), fingertip caps, the cuff a cylinder (seam
  on the little-finger side); faces that fold in their chart get their own island. 6.6 texels/mm at 2048 px.
  Colours and relief are painted per texel from the 3D point, so chart seams do not show.
- Panels painted (smooth boundaries from weight-blended palmar directions): palm grey where the surface faces within
  62 deg of each finger bone's palmar side (fingers: Leatt's palm view shows the black stretch-mesh fourchettes
  between the fingers), 70 deg (thumb pad, facing the index finger), 80 deg (hand: the palm wraps to its edges).
  Colours (sRGB, starting values): mesh black 30, 30, 33; NanoGrip grey 152, 145, 143; elastic 24, 24, 26 (medians
  of Leatt's studio photos; to be calibrated against his daylight photos).

### Checks (component 1)
- Tests (`test_gloves.py`, 8): size and chart, offsets at rest (1.0 to 6.2 mm, median 1.4), cuff and strap
  dimensions, skin weights (normalised, each glove on its own side's bones), hide_body (under the glove, mirror),
  gear npz, UV islands (no folds, no overlaps, density within 2.6x), and the glove over its own skin with the fist
  closed as build_rider.aim_pose closes it and the wrist bent -30/0/+30 deg (numpy skinning): cuff over 3 mm
  (min 3.87), outside of the fist over 0.2 mm (min 0.27), palm-side flexion creases folding in less than 4 mm
  (min -3.49, real fabric bunches there).
- Blender (seated pose on bike_v6 kit7, `gloves.py check`): visible skin through the glove 0 (both hands).
- Renders on white like Leatt's (`check` views back_R, palm_R, back34_L, palm34_L) beside Leatt's four photos.

### Finding: the seated pose puts the grip through the palm (not the glove's to fix)
`gloves.py check` on the seated pose (pose.py seated, build_rider.aim_pose): the grip's axis crosses the hand at
(9, 92, 6) mm in the hand frame, i.e. only 6 mm palmar of the bones' plane, 25 deg to the knuckle line. Skin 14 mm
inside the 14.8 mm grip rubber (L 363 vertices, R 277), the glove 13 mm. For a power grip the axis must lie on the
palm side at palm skin (about 20 mm) + glove (1 mm) + grip radius (14.8 mm), about 36 mm palmar: the hand sits about
30 mm too close to the grip axis (aim_pose aims the wrist bone straight at the grip point, so the grip point is on
the hand's bone axis). The 25 deg angle and the crossing 92 mm from the wrist (across the distal palm) are right
for a power grip. The fingers then need more curl than (0.95, 1.05, 0.75) rad to close round it.

## 2. Construction (component 2, 2026-11-13)

Leatt's features (product page, us.leatt.com/products/moto-2-5-x-flow-glove, fetched 2026-11-13): "Fully vented
X-Flow mesh upper", "Stretch mesh FormFit finger sides", "Durable, ultra-thin NanoGrip palm", "Pre-curved, snug fit
with seamless palm", "Multi-row Coats stretch thread stitching", "Hook-and-loop adjustable closure", "Touchscreen
compatible". Shapes and places read on Leatt's MY27 back view (right glove) at 0.178 mm/px: the cuff seam (row 440)
to the knuckle line (row about 1030) is 590 px against 105 mm on his hand (crease y +5 to the knuckles y about 110),
agreeing with the 0.175 mm/px from the knuckle breadth; so the photo maps onto his hand's back as
x = -45 + (col - 520) x 0.178, y = 5 + (row - 440) x 0.178 mm (hand frame).

Everything here is in the texture (colour) and a shared tangent-space normal map (`glove_normal.png`, OpenGL
green-up, from a height field in mm): at riding distance (his photos: a glove is 60 to 100 px) none of it shows
as shape; the welded overlays are black on black.

| Feature | Model | Source |
|---|---|---|
| X-Flow mesh (back of hand and fingers) | staggered holes 0.85 mm pitch, 0.10 mm deep | Leatt's close crops (`z_cuff_back`: a fine regular knit with holes); pitch EST from 1920 px photos (about 5 px) |
| Stretch mesh (fourchettes, fingertip caps) | honeycomb, 1.5 mm cells, walls 0.12 mm | Leatt's crop of the fingertips (honeycomb caps on the back of the tips, about 12 mm long) |
| Panels | palm within 62 deg of each finger bone's palmar side, back within 55 deg of its back, fourchette between (about 10 mm wide on a 9 mm finger); thumb 70 / 65; hand: palm 80 deg, back the rest | Leatt's palm view (black strips between the fingers) and back view |
| NanoGrip palm | grey 152, 145, 143 mottled +-4.5 % (7 mm and 2.2 mm noise), suede relief 0.012 mm | Leatt's palm photos (mottled suede) |
| Cuff band | ribs round the wrist 0.75 mm pitch, 0.05 mm | Leatt's crops (`z_cuff_back`: fine ribs across the band) |
| Seams | 0.6 mm grooves, 0.18 mm deep, darker 35 % | Leatt's crops |
| FormFit stitching | dashes 1.6 mm long every 2.6 mm, 1.3 mm off the seam on the mesh side, thread grey 96, 96, 100, 0.06 mm proud | Leatt's crop of the fingers (light grey stitch dashes along the finger sides) |
| Knuckle overlays (fingers 2 to 5) | from 3 mm behind the knuckle joint along the first phalanx, 15.5 mm wide seen from the back (13 on the little finger), 30 mm long (25), the far end pointed (0.55 mm back per mm off the middle); slot vents 7.5 x 1.4 mm at 35 deg, every 5 mm | Leatt's MY27 back view crop (`z27_knuckles`) |
| Little-finger edge overlays | two, 17 mm in from the edge and 9 mm round it: y 13 to 31 mm (3 vents) and 34 to 56 mm (7 vents, 6.5 x 1.3 mm at 55 deg) | `z27_edge` (rows 480 to 600 and 600 to 720 at 0.178 mm/px) |
| Thumb overlay | along the thumb's back from 12 mm before its second joint to 65 % of its length, 16 mm wide, a row of dot vents 1.6 x 1.2 mm every 3.2 mm on its index side | `z27_thumb` |
| Overlay surface | 0.35 mm proud, 0.35 mm bevel, black 17, 17, 19, vents 0.30 mm deep | Leatt's photos (deep satin black) |
| Fabric material | roughness 0.7, sheen 0.1, one material per glove (build_rider's gear material has one roughness): the mesh's micro-relief scatters its highlight, the overlays' smooth faces keep theirs (the satin look) | Leatt's photos; the first renders with sheen 0.3 turned the black mid grey |

Areas painted (1024 px test): overlays about 5,700 mm2 (knuckles about 600 each round the finger's curve, thumb
1,300, edge pair 1,000), palm 33 to 50 % of the hand's glove. Textures: two colour maps 1.2 MB each and the normal
map 3.9 MB (2048 px PNG).

## 3. Graphics (component 3, 2026-11-13)

Which glove each Leatt view shows (thumb side and palm normal worked out per photo): MY26 back and palm, MY27 back:
the RIGHT glove; MY27 "other angle" back and palm: the LEFT glove. Both gloves carry the same band in the hand's own
frame (the gloves are mirror images: white end on the little-finger edge, halftone toward the thumb, hatches
leaning back toward the edge, so they lean "\" on the right glove's back view and "/" on the left's), but every
word reads left to right on both: LEATT starts at the edge on the right glove and ends at it on the left (MY27
crops `z_bands`, `z_hatch`, `z_hatch2`).

| Print | Model | Source |
|---|---|---|
| Knuckle band, redrawn (u = mm in from the little-finger edge in the back view, y = hand y) | core from y = 68.5 + 0.03 u to 95.0 + 0.09 u; solid to u 52, a 45 deg halftone (1.5 mm screen) fading to black at u 88; hatch strokes 1.8 mm wide every 5 mm, 9 mm long above and below the core, leaning 35 deg (toward the thumb going toward the fingers), thinning and shortening from u 25 to 75; continued 18 mm round the edge | Leatt's MY27 back view rectified onto his hand's back at 0.178 mm/px, anchored row by row to the glove's edge (`band_grid.png` in my scratch folder); the first try (thresholding the photo itself) came out blotchy from the mesh texture and the lighting |
| LEATT | the photo's own five letters: the large dark holes enclosed by the white core in rows 806 to 935, cols up to 830 (outside the glove counted as white so the L at the edge closes), smoothed 2.2 px; placed rigidly (anchored to the edge at y 82), not row by row (the slanting edge sheared them); about 50 x 20 mm; mirrored inside their box on the left glove | MY27 back view |
| Red Leatt logo | on the lower little-finger-edge overlay, photo rows 614 to 654, cols 565 to 589 (4.3 x 7 mm), red 200, 30, 40 (the photo's 149, 65, 64 is the thin outline mixed with black); mirrored in its box on the left glove | MY27 back view |
| nanoGrip label | dark rubber label 40, 40, 42 with its light grey text, on the palm by the thumb-side edge, y 11 to 35 mm (photo rows 462 to 594 at 0.182 mm/px), 0.2 mm proud; text mirrored across the label's width per row on the left glove | MY26 palm view (right glove), checked on the MY27 left-glove palm view (top right, thumb side) |
| "2.5" on the white pull | moulded figures (about 4.3 mm tall): the pull's face from the photo (cols 940 to 1048, rows 255 to 284), divided by its smooth white level, `glove_tab.png`; u flipped on the right glove so it reads on both | MY27 left-glove back view (`z_tab`) |
| Not done | the Leatt mark on the pull's palm-side end, and the small print on the pull beside "2.5" (too small to read in Leatt's views) | |

Checks: renders of both gloves from Leatt's four angles beside Leatt's photos; close-ups (knuckles, both cuffs):
LEATT and "2.5" read right on both gloves; test `test_prints_read_right_on_both_gloves`. His photos 08 and 09: the
white band with LEATT runs along the little-finger side of the fist, along the grip, in the model too; the fist
itself does not match while the pose puts the grip through the palm (section 1).
