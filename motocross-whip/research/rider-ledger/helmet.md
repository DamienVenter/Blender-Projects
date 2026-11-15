# Ledger: helmet and goggle (`scripts/rider/helmet.py`)

Leatt Moto 8.5 Composite, V26 helmet kit, Pinata Teal (1026000250 series) with the Velocity 5.5 Iriz goggle, Pinata
Teal frame, Iriz Purple 78% lens (8026000150). Identification: `research/rider-gear-leatt.md` sections 3 and 4.
Every number below names its source. Frames: HELMET frame = metres, x to the wearer's left, y backwards, z up
(the axes of body.py's MB frame); "px" = pixels of the named photo.

## Extra Leatt views used (not saved in the repo; all from us.leatt.com product JSON, 1920 px originals)
| Use | File | Product handle |
|---|---|---|
| side profile (traced) | `Leatt_Helmet_Moto_8.5_Royal_Left_1025100220.png` | helmet-kit-moto-8-5-composite-with-5-5-goggle-sale |
| back widths | `Leatt_Helmet_Moto_8.5_Royal_Back_1025100220_9117e0ed-97d5-4155-a968-67d16b7e5392.png` | same |
| strap ruler, side | `31509_Helmet_Kit_Moto_8.5_White_2_1027000260.jpg` | moto-8-5-helmet-kit (MY27) |
| strap ruler, back | `31509_Helmet_Kit_Moto_8.5_White_3_1027000260.jpg` | same |

The V25 (1025100xxx) and MY27 (1027000xxx) 8.5 are the same shell as the V26 Pinata Teal: identical outline,
vents, eyeport and chin in the iso views (and the research doc's V25 White check). The photographed helmets are
size M (the size label on the back in the Pinata back view and the MY27 back view reads "M 57-58cm").

## Size
| Number | Value | Source |
|---|---|---|
| His head girth | 59.2 cm | body.npz: largest convex girth through the brows and the back of the skull (planes 15 to 50 mm above the eye centres, tilted -10 to +10 deg, ears excluded), `helmet.head_circumference` |
| Leatt size | **L** (59-60 cm) | Leatt helmet moto size chart (`reference/leatt-gear/sizing/leatt-size-chart_helmets-moto.jpg`) |
| Shell size | the photographed M shell | Leatt: "3 shell sizes" for 6 head sizes; split not published (search found none). Assumed two sizes per shell (XS-S, M-L, XL-XXL), so the M in Leatt's photos is the L shell. **Unconfirmed: ask Damien his size.** |

## 1. Shell
Anatomy: composite outer shell (three sizes), EPS in four densities, 360 Turbine discs, Pro-Fit pads; large face
port with a black rubber trim, textured goggle-strap grip panels beside it, chin bar with a central vent, brow vents
either side of the badge, two mesh crown vents, two rear exhaust vents under the rear spoiler step, black lower trim.

| Number | Value | Source |
|---|---|---|
| Scale of the profile photo | 0.2484 mm/px | strap 45 mm (Leatt Velocity 5.5 features) = 186.7 px across its run in MY27 side view (194 px tall at 15.8 deg); Royal_Left outline registered onto that view by a similarity fit: scale 0.9481, rotation -8.8 deg, residual 18 px; perspective 1.087 (strap on the side surface 0.13 m nearer a camera taken 1.5 m away: EST) |
| Profile (centre-line outline, free edges) | tables in helmet.py | traced from the Royal_Left alpha matte (contourpy), 4 px steps, smoothed 2 to 3 passes |
| Crown under the visor | 14 points | EST: the visor stands 0 mm off the crown at u 1135 (where its rear edge meets it), 13 mm at u 886, 21 mm at u 726, then the forehead runs down to the port's top corner |
| Back-view scale | 0.2046 mm/px | MY27 back view: strap 217 px = 45 mm, helmet 1155 px wide once its width profile is fitted to Royal_Back's (scale 0.905); perspective 1.09 (EST, as above) |
| Back-view camera | 13.5 deg above | rear exhaust vent to rear lower corner: 218 mm in the profile, 206 mm in the back view |
| Top-view scale | 0.247 mm/px | Pinata top: visor tip to back 1500 px = profile length 371 mm. Check: the visor tip lands 3 mm from the profile's |
| Width field | W_Z, Q_Y, L_CROWN 124 mm, P_CROWN 1.93 in helmet.py | least squares to the back and top silhouettes: residual 7.7 px (1.6 mm) back, 9.3 px (2.3 mm) top; a 7 % dip at z = 0 from a 1.5 % waist in the photo evened out by hand |
| Brow and chin roundness | L_BROW 75 mm p 2.0, L_CHIN 140 mm p 1.25 | EST from the iso views (broad flat brow, blunt V chin); the chin narrowed after the iso-left camera fit |
| Outer width | 257 mm (max) | result; back photo 255 to 261 mm |
| Shell length, chin to back | 368 mm | result; with the visor 371 mm = 1494 px of the profile |
| Shell height, chin bottom to crown | 303 mm | result |
| Liner surface | 2 mm off his skin where near, 40 mm inside the shell elsewhere, never under 18 mm (chin bar) | EST: shell 3 mm, EPS about 30 mm, pads; the comfort liner touches the head |
| Fit on his head | port's top edge 40 mm above his eye centres (goggle centred on the eyes); pitch 18 deg nose down from the profile photo's attitude, brow 63 mm ahead of the eye centre; shell 50.9 / 51.1 / 51.4 / 51.4 mm off the top / back / left / right of his skull, 38 mm ahead of his forehead | `fit_on_head`: even stand-off all round (the EPS and pads of a real fit) |
| Head pitched down 20 deg | no skin inside the shell when shared by neck01-03 and the head (5 deg each); pitching the head bone alone brings the chin bar's lower inner rim 6 vertices into his throat | test_helmet |
| Hidden scalp | 1141 body vertices | head skin inside the shell, 40 mm above its lower edge and 30 mm behind the port (hide_body) |

Check: silhouettes against Royal_Left (exact by construction), Royal_Back and the Pinata top view (sheets in the
agent's scratch, residuals above). Tests: `test_helmet.py` (size, dimensions, closed and symmetric shell, fit,
no skin inside the shell at rest and with the head pitched down 20 deg).

## 2. Visor, trim, vents
| Number | Value | Source |
|---|---|---|
| Visor top line and side lower edge | tables VISOR_TOP, VISOR_LOW | Royal_Left px: tip u 220, rear end on the crown u 1135, rear corner u 1075 v 662 (rear end raised 3 mm so it sits on the crown) |
| Visor plan half width | 0 at the tip, 74.5 mm at u 315, 122.5 mm at u 912 | Pinata top view, 0.247 mm/px (tip lands 3 mm from the profile's) |
| Visor thickness, clearance | 3.5 mm, top 7.5 mm off the shell where it lies on it | EST (moulded visor) |
| Eyeport trim, lower trim | black rubber rolled edge, 4 mm roll, joining shell and liner | EST; colour from the photos |
| Vents, mesh, grip panels, brow badge | painted from Leatt's photos (component 3), not modelled as openings | **not done as geometry** |
| Visor screws | not modelled | **not done** |

## 3. Graphics (Pinata Teal art): a clean flat print (2026-11-13, `scripts/rider/helmet_art.py`)
The first pass projected Leatt's photos into the atlas (`helmet.paint_atlas`, kept for comparison): studio
reflections, soft shading and doubled edges came along (luminance spread 40 levels inside the white base). Now the
photos only MEASURE the print; the texture is drawn by script (`helmet_art.py trace` once, `draw` from
`helmet_art.json` and `helmet_art_field.png`; helmet.py's CLI redraws it). Photos: the four Pinata Teal views
(`reference/leatt-gear/helmet/helmet85-kit_pinatateal_{iso-left,iso-right-with-goggle,back,top}_...png`, 1920 px).

| Number | Value | Source |
|---|---|---|
| Atlas | `textures/rider/helmet_pinata.png`, 4096 px, 4.3 texels/mm (ATLAS_K 4300 per m), same island layout as before (left, right, top, back, front, visor) | helmet.TEX, ISLANDS |
| Cameras | the fitted pinhole cameras helmet.CAMS. **Back camera refitted** with the print's centre line (stripe stem 964 to 967 px, DOT print 964 to 968: x 965.5) as a second term: az 186.6 -> 179.7 deg, roll -4.9 -> 0.04 deg, centre line rms 94.9 -> 0.6 px, outline chamfer 11.2 -> 9.0 px (half res). Before, the back LEATT was drawn 16 mm off centre | scratch refit_back.py; helmet.py comment |
| Iso cameras | centre line 66 px (iso-left) and 79 px (iso-right) beside the brow badge's centre (about 14 and 17 mm). Fitting iso-left to the badge costs 4.7 px of outline and leaves it 27 px low: the shell's estimated front, kept | photos: badge centre iso-left 638,532 px, iso-right 1275,540 px |
| Design point | each texel is traced at its mirror point on his left (x >= 0): the Pinata art is mirror-symmetric (iso-left against iso-right); words and logos are drawn afterwards, reading right on both sides | photos |
| Owner | ONE view per texel: cos^2 x VIEW_PREF (iso-right 0.6: its goggle) x MIRROR_PREF (a mirror point 0.45 except on the sides) x VISOR_PREF (on the visor's top the top view 1.0, the others 0.1: it sees the visor square-on, and through the model's visor the iso views put its chevrons 10 to 25 mm off), smoothed 6 texels. A view whose de-lit colour is lighter than the white base (any channel over 255) does not own the texel: no ink is lighter than white, so it is a reflection or the shading fit extrapolated (the iso-left view of his rear lower side, facing down, gave a saturated pink glow). A texel no view owns within 3 mm of an owned one on the same surface takes its owner and colour (the crown's rippled back slope: faces turned to the back are seen by no view). Owned: iso-left 505k, top 265k, back 223k, iso-right 89k of 2048-atlas texels; 73k unowned (under the visor, the chin's underside), 193k hand-marked | trace log (2026-11-14) |
| De-lighting | per view: second-order spherical harmonics of the normal fitted (robust) to the white base's texels, then a local white correction (blur 12 and 40 texels); reflections = brighter than the view's white + 18, or a washed pink | trace |
| White | 226, 229, 235 (helmet.BASE_WHITE): every view's white scaled to it | photos (de-lit white base) |
| Inks | black 24.5/22.4/25.0, purple 56.3/0.1/93.9, magenta 165.0/0.0/101.6 (medians of each ink's de-lit core); the iridescent band (median 158.6/121.5/75.9), purple and magenta are fitted colour fields (normalised Gaussian 3 texels inside their own region, 15 and 60 where sparse), fitted only from texels a view owns whose own colour is that ink, so the design's gradients stay gradients. (A hand-marked texel no view owns has no colour: the stripe's end on the back, masked in the back view and seen edge-on from the top, fed its garbage into the teal field as a pure white glow until this rule) | trace log, helmet_art.json |
| Pale teal | the back band's hexagon round the icon: de-lit red at least 14 below the mean of green and blue (white base: 5.7 median, 95 % under 12.5) and green minus blue above -7 (the visor's sky-blue studio reflections: -12.7 median; the hexagon: -1.7) | measured in the back view |
| Regions | class maps smoothed 2.2 texels, islands under 3 mm^2 away from an island edge refilled (glints), contours vectorised and simplified (0.8 texel): 116 black, 101 white, 41 purple, 31 magenta, 99 iridescent polygons. Drawn at 4096: an island's edge (2 texels) and fragments under 160 mm^2 take the colour of the nearest island interior on the shell (KD-tree in 3D), since atlas-space smoothing mixes in whatever lies next to them in the atlas (light teal lines on the crown's rippled back, where faces alternate between the top and back islands) | trace log |
| Hand-marked (FORCE) | iso-left px, black: chin vent (14 points round 365-629 x 1289-1629), eye port trim and grip panel (22 points round 470-1350 x 577-1150), chin cap (385-650 x 1098-1192). Their moulded texture caught the studio light as grey streaks. Back px: the stripe's end, teal 850-1060 x 440-722 with the purple stem 941-988. Visor (FORCE_VISOR), top px 1230-1480 x 960-1560, white: the visor's crease, the shadow under its raised side and the side vent's recess lit pale blue are moulded shape, not print (the chevrons in it are drawn from the photo, below) | photos |
| Not shell (NOT_SHELL) | back px: everything above the rear lip (the visor seen from behind; 14 points), the turbine disc (870-1030 x 585-690: drawn from the top view); top px: everything beyond the rear spoiler's edge (y under 378 to 540: the back band and stripe end seen edge-on, which the top camera laid across the crown as a streak) | photos |
| Stripe's end | the top view puts the turbine about 40 mm higher up the back than the back view (the shell has no rear spoiler step): the turbine follows the top view (its camera fits there), the shell below it carries the stripe's teal and purple stem down to the spoiler's foot | top and back photos |

| Element | Drawn from | Place, size, colour | Source photo |
|---|---|---|---|
| Back LEATT | Leatt's wordmark file (`reference/leatt-gear/leatt-wordmark-slanted_official_leatt-us_1200x300.png`), white | fitted in the photo (IoU 0.61) then on the shell through the back camera (IoU 0.69): 174 x 38 mm, turned -18 deg, aspect 0.86 (free, bounded 0.74 to 1.35) | back |
| Visor side LEATT x2 | same file, black, on the visor's top surface | 31 x 8 mm, turned -18 deg (IoU 0.60), mirrored to read right | iso-left |
| Visor top LEATT band | **traced**, not the file: laid on the visor the file fits badly (IoU 0.49, 0.50 with a free aspect: the visor's slope differs from the real one's) and ate the band's strips | top |
| Side icon x2 | Leatt's three-piece triangle (`leatt-icon-triangle_official-favicon_leatt-us_100x100.png`, upsampled 8x), white | 50.3 mm, IoU 0.70 | iso-left |
| Back icon | same file, its traced pale teal | 27.4 mm, IoU 0.77 | back |
| Brow badge | goggle.py's numbers (BADGE_*): purple 79/39/180 trapezoid z 76.5 to 93.0 mm, half widths 28.0 / 18.5 mm, corners 3 mm, one white LEATT from the wordmark file 34.6 mm wide at z 84.8 mm; brow vents (VENT_QUAD, mirrored) dark mesh in a moulded rim; plain white round them | iso-right (goggle.md) |
| Crown vents x2 | drawn (moulded parts): insert rim 202/206/214, opening 14/14/16 with a triangle lattice of bars 209/213/219 (cells 20.3 px along the opening's top edge, 25 px down its side, bars 0.15 of a cell) | top px 670-772 x 583-746 |
| 360 Turbine | drawn: blue disc 3/116/200, black ring of six arcs, "360°" and "TURBINE" | 19.4 mm, top-back centre line | top 922-1006 x 384-463 px |
| Emergency label x2 | drawn: black 13/7/11, red pull tab 197/0/0 with a white arrow, EMERGENCY USE ONLY / PULL RED TAB & REMOVE CHEEK PAD | 46.5 x 8.7 mm under each cheek | iso-left 1164-1347 x 1340-1440 px |
| Chin lettering x2 | drawn: navy 46/28/117 spaced italic capitals MX.26 / MOTO RACE SPEC / LEATT DEVELOPED | 46.1 x 14.1 mm, cap 3.4 mm | iso-left 695-865 x 1325-1415 px |
| DOT print | drawn white on the black lower back: bar with the wordmark knocked out, MOTO 8.5, DOT, FMVSS No. 218, CERTIFIED | 19.3 x 21.8 mm, projected through the back camera | back 915-1017 x 1540-1620 px |
| Size sticker | drawn: white 245/244/241, **L 59-60cm** (his size), 1305g±50g, ECE 22.06 | 18.4 x 16.0 mm | back 1020-1116 x 1562-1621 px (reads M 57-58cm) |
| EIGHT POINT FIVE x2 | drawn: black capitals one per cell along the top of each side band, from the front up on his left, from the back down on his right | cap 2.45 mm, pitch 8.29 mm (24 of 26 letter centres, residual 8.1 mm) | iso-left, iso-right |
| Visor chevrons x7 a side | **vectorised from the top photo**, where they are seen square-on (4 px per mm): dark components (below 90 on white) of 1200 to 2000 px in the columns x 1220-1480 (his left) and 440-700 (his right), y 950-1540; each outline at half contrast between its own black core and the white ring round it (sub-pixel contour, Douglas-Peucker 0.6 px), black ink, projected onto the visor through the top camera; the traced black under them erased 3 mm round | 7 a side, centres x +-78.7 mm, columns 102.7 and 101.2 mm long, each about 10 x 21 mm (round 4, through the solved top camera: each column moved 7 px in the photo to mirror places, centres (+-82.4, -106.6, 110.8) mm, section 7) | top |
| Side chevrons, bands, stripe | traced (regions and fields) | | all four |

| Material | Value | Source |
|---|---|---|
| helmet_paint | the print under a full clear coat: coat 1.0, coat IOR 1.5 (4 % at normal incidence), coat rough 0.03; the base has no specular of its own (Specular IOR Level 0) and rough 0.5 (no effect then) | physics: the print/coat interface (n about 1.5 both sides) reflects next to nothing. Test spheres in Blender 5.2: base specular 0.5 under coat 1 added a soft satin glow round the sharp coat highlight, so Blender does not suppress it. Leatt's studio photos show the softboxes with crisp edges (high gloss) |

Checks: renders through the four fitted cameras at the photos' own 1920 px beside Leatt's photos, full and in 1:1
crops (`renders/checkpoints/2026-11-13_helmet-clean/`), his photo views 07/08/09 (`head_closeups.py`), the texture
splatted into each view one point per texel (no pure white and no saturated texel at the stripe's end or his rear
lower side), tests in `test_helmet.py`: deterministic drawing, no studio light in the flat white and black
(luminance spread under 4 levels; the old projection 40), one LEATT on the brow badge, the visor chevrons as
vectorised from the top photo with no traced copy beside them (dark share of the 0.5 to 3 mm band round them under
1 %), the paint material, the art data.

Limits and open points:
- The front-iso camera offset (above) widens what is traced at the front centre from those views: the chin vent's
  black reads wider than in Leatt's photos. Fixing it needs the shell's brow and chin shape (outside this pass).
- The visor's LEATT band is traced on the model's visor, whose slope differs from the real one: it stretches in the
  iso views. Its chevrons are drawn from the top photo (above), so they match it there and stand slightly
  differently in the iso views (the visor's slope again).
- The stripe's end: the top and back photos put the 360 Turbine about 40 mm apart along the back (above). Below
  the drawn turbine, where the back photo shows its disc, no view measures the teal: it is the teal field of the
  print round it (smooth, paler than the photo's left side there).
- His rear lower side, just above the black lower shell: the back camera sees it more squarely and puts it on the
  black, the iso-left photo shows the magenta reaching down to the white edge. The back view wins (a black patch round
  x 80, y 66, z -110 mm); the shell's lower rear shape differs from the real one there.
- The crown's back seen from the top shows pale banded reflections: the gloss coat on the mesh's small ripples
  (they are in the old render too), geometry, not print. Likewise the light and dark spikes across the back band's
  centre in the renders (back px 860 to 1060): the shell's long thin triangles there shade in facets; the texture
  is smooth there.
- Moulded detail is drawn flat or not at all: the grip panel's triangles and the chin vent's mesh are plain black;
  the moulded LEATT on the chin cap and the small Leatt tag on the brow trim (black on black) are not drawn.
- **Questions for Damien**: his helmet size (L assumed: the sticker reads L 59-60cm with the photographed shell's
  1305g±50g); the crown under the visor is seen in no photo (plain white assumed); the back LEATT fits best 14 %
  shorter than Leatt's file (aspect 0.86), as if printed stretched round the back: right, or the model's curvature?

Finding (unchanged): the big white LEATT on the iridescent band behind the eyeport (Leatt iso-right, his 07 and 09)
is the **goggle strap's** print; the helmet's side there carries the iridescent field and white chevrons.

## 4. Goggle
Rebuilt on 2026-11-13 (round 2): `scripts/rider/goggle.py`, ledger `goggle.md` (frame, purple mirror lens, his eyes,
and the brow badge, which the projection had doubled and is now repainted by script).

## 5. Round 2 (2026-11-15, decision 44): the face port's real edge, the brow, a fair shell

Damien: the eyeport trim and grip panel read as one big flat black area, the brow sat 14 to 17 mm off in the
front-iso views, the crown back showed ridges. Checkpoint `renders/checkpoints/2026-11-15_helmet-r2/`.

### The big black area: the face port's side edge (found, fix held back)
| Number | Value | Source |
|---|---|---|
| Main's port side edge | y -88 mm (Royal_Left u 742 to 750) | FACE_PORT, traced at Royal_Left's notch. That notch is bounded by the cheek pads (u 750, a dark fabric band to u 793), not by the shell |
| The shell's own edge (rubber trim's inner edge) | iso-left photo x 1195, 1193, 1189, 1183 px at rows 830, 900, 970, 1040 | Leatt Pinata iso-left (no goggle), picked on a 1:1 crop |
| Main against that edge | 185 to 221 px left (ahead), 35 to 40 mm on the shell | test_face_port_edge_on_leatt_iso_left on main's shell |
| Why it was black | helmet_art's FORCE polygon (the photo's trim and grip panel) covers the photo's opening; main's shell stands inside that opening, so it was painted flat black | helmet_art.FORCE["isoleft"] |
| Round 2 port ("iso") | rear part cast through the iso-left camera onto the width field: chin bar top (980, 1150) to (1150, 1120), side edge (1175, 1090) to (1196, 800), brow edge (1160, 795) to (920, 772) px; edge at y -47 to -58 mm | helmet.PORT_REAR; -5 to +4 px against the photo |
| Trim ridge, panel | trim about 6 mm wide; grip panel's rear edge y -15 to -36 mm | iso-left casts |
| T_MIN with the iso port | 14 mm (18 put 4 cheek vertices inside the solid: its lower rear corner reaches 10 to 15 mm lower) | test_no_skin_inside_the_shell |
| Goggle against the iso edge | outriggers' rear 21 to 23 mm ahead of the edge (z -40 to 0 mm); main's edge is under them by 17 mm | helmet frame, outriggers from goggle.py round 8 |
| Leatt iso-right photo (with goggle) | the outriggers sit over the trim; the strap runs back over the grip panel | 1:1 crop |
| Result with the iso port | the strap bridges the opening (its silicone side shows in every goggle view, 14 free stations instead of 8); test_goggle fails three: the outriggers' backs no longer lie over the shell (Damien 2026-11-13), the strap 41.2 mm inside the shell's surface where it crosses the opening, its clearance 0.48 mm (< 0.5) | iso build, sheets 06 and 07 |

So the port edge cannot move without the goggle: **held back**, `helmet.PORT = "side"` builds main's port;
`PORT = "iso"` builds round 2's (tested at the outline level). The goggle has to sit about 22 mm further back on
the shell, which is the brow question below. Side check: through both iso cameras the side screw and the grip
panel's top rear corner land 18 to 24 mm behind their Royal_Left places (screw y -19.3 iso-left, -15.7 iso-right,
-39.7 Royal_Left; panel corner -8.5 against -26.6): Royal_Left's camera stands 8 to 11 deg behind the side (the
back LEATT's first letters show in it), so its near-side features read about 20 mm forward. The notch's fabric
band end (u 793, y -76 mm) then lands near -57 mm, where the iso photo has the edge: both photos agree.

### The brow (found, not moved)
| Number | Value | Source |
|---|---|---|
| Badge rays from iso-left and iso-right | meet within 0.4 mm at (-2.1, -118.7, 80.7) mm | helmet.CAMS, badge centre picked in both photos |
| Model's brow at that height | y -139.3 mm: 20.6 mm too far forward | Profile |
| Badge error through each camera | iso-left 81.3 px (dx -81.3, dy 13.7), iso-right 86.6 px (dx 86.6, dy 18.3): about 20 and 21 mm. Before = after (not moved) | renders against photos |
| Moving it (brow 20.6 mm back) | fit_on_head keeps the brow 32 mm (FORE_MIN) ahead of his forehead: the helmet slid 12.5 mm forward on his head, back gap 51 to 38 mm, the ring of gaps spread 0.6 to 12 mm; the goggle (placed on the helmet) went 66.4 mm ahead of his eyes (53.9), foam 14 mm off his face (5) | trial build, reverted |

Moving the brow and the port edge together is one change for the helmet, the head fit and the goggle: open
question for Damien and the goggle agent (decision 44).

### A fair shell (done)
Main's crown back had ridges 20 mm either side of the centre line (back photo px 860 to 1060). Causes and fixes:
| Cause | Fix |
|---|---|
| Distances to rims sampled every 3 mm scalloped up to 0.6 mm at 2 mm from the rim; x ~ sqrt(d) there turns that into ridges | rims faired by C2 smoothing splines (crown 0.43 mm, chin 0.25 mm from the trace), distances to the segments of a 0.25 mm polyline |
| W_Z and Q_Y read with straight lines: the slope jumps at every knot (bands in the reflections) | C2 smoothing spline over each straight-line table sampled every 1 mm (0.30 and 0.35 mm of width at most). A spline through the knots alone rang 9 % low in Q_Y's flat run (the chin bar 6 mm narrow): caught by the skin test, fixed |
| The Gaussian smoothing averaged over the query points (graded rings near the rims weighted it) | smoothed once on a fixed 2 mm grid over the uncut domain (the port does not change the surface), read back by a bicubic spline |

| Number | Main | Round 2 | Source |
|---|---|---|---|
| Normal turn above its neighbours, crown back (max) | 189.8 /m | 96.2 /m | test_shell_is_fair_at_the_crown_back (limit 120) |
| Same, 99th percentile | 27.6 /m | 21.9 /m | fair check |
| Largest left | | at the rear spoiler's S-bend (y 109, z 94, x +-50 mm): a real shape | |
| Fit gaps top / back / left / right / fore | 50.9 / 51.1 / 51.4 / 51.4 / 38.1 mm | 51.8 / 51.4 / 51.3 / 51.3 / 38.1 mm | fit_on_head |

### Not done this round
- Moulded detail as geometry (grip panel triangles, rolled trim, chin vent mesh, brow and crown vents, rear
  exhausts, moulded LEATT on the chin cap, the brow trim's Leatt tag): not started.
- Rear lower corner (about x 80, y 66, z -110 mm): Leatt's back photo has a white moulded piece at each rear lower
  corner (a dark mesh slot in it) with a magenta strip ahead of it; iso-left shows the magenta reaching that white
  edge. The model has no such piece and its texels there take the back photo's black band, so iso-left shows a
  black patch where the photo has magenta. Needs the piece (geometry or print) and one forced field for both views.
- The FORCE trim and panel polygon is unchanged (it is right once the port is).
- The top view's centre stem (between the 360 Turbine disc and the chevron, top photo x 949 to 984, y 466 to
  600) is a purple and white ladder on the fairer shell (main: white; the photo: purple). The back view sees it
  edge-on over the rear spoiler's S-bend, and its forced stem polygon catches alternate texel rows. A forced
  purple field in the top view only swapped the colours (tried, reverted): the fitted colour fields there need a
  look.

### Daylight colour check against his photos 07 and 09 (report only)
| Patch | His photo (sRGB) | Render, main's materials (sRGB) |
|---|---|---|
| White shell, lit (07 crown) | 242, 246, 249 | 223, 226, 230 (8 % darker) |
| White shell, lit (09 crown) | 240, 242, 248 | 205, 207, 210 (15 % darker) |
| Magenta print (07 side) | 207, 34, 138 (saturation 0.84) | 174, 88, 112 (0.49) |
| Magenta print (09 side, shade) | 148, 27, 96 (0.82) | 192, 94, 126 (0.51) |

The render's magenta is about half as saturated as his photos' and leans red; the white is 8 to 15 % darker. The
ink is fully saturated (166.7, 0, 102.2), so AgX's highlight desaturation and the clear coat's sky reflection take
it: to look at with the lighting (AgX look or exposure), not in the print. Medians of the brightest quarter of the
low-saturation pixels (white) and of hue 300 to 350 deg, saturation over 0.45 (magenta), in boxes on the photos'
own pixels and the 16-sample close-ups.

## 6. Round 3 phase A (2026-11-15, decision 46): the photos solved together, the shell rebuilt, moulded vents

### Stem ladder and crown stripe (done, merged as 9bba9fa and f3778be)
- The purple and white ladder on the crown-back stem was shading: the crown band was meshed as fans with normals 3
  to 8 deg off the surface, mirrored by the clear coat. A structured crown band fixes it (Blender's normals within
  1.25 deg of the surface, main 67 deg; `test_crown_shading_follows_the_surface`).
- The crown stripe (teal bands, purple stem and chevron, white margins, step notch) is drawn from Leatt's de-lit top
  photo (`helmet_art_stripe.png`); the scene look is the bike's AgX - Punchy at -0.6, daylight gain 3.4 EV.

### Bundle adjustment of Leatt's 8.5 photos (`scripts/rider/helmet_ba.py`, `research/helmet-ba.json`)
Eleven cameras (Pinata iso-left, iso-right, back, top; Royal_Left as the gauge; V25 white iso-left and back; MY27
front-iso, left, right, back) and twelve landmarks solved together with the shell's back and top outlines. Gauge:
Royal_Left is the helmet frame's own camera (only its distance is free) and the shell is mirror symmetric. Landmarks
read on 1:1 crops (disc and blob centroids to sub-pixel, the rest by eye at 3x); sigma divided by the cosine of the
view's incidence; the landmarks away from the front held on the model shell (1.5 mm), the two on the centre line on
the traced profile. Three soft-l1 rounds, then plain least squares (soft-l1 alone left the back group 16 to 29 mm
inside the shell: a long lens's outline fixes its scale, not its distance). Result: landmarks 1.69 sigma rms,
outlines 3.2 px rms, reduced chi-square 2.50. The front's outlines (iso views: 13 to 15 px off, the visor and
brow) are left out of the solve: phase B rebuilds the front from these cameras.

| Camera | Landmark readings | Landmark rms (px) | Outline rms (px) | mm per px at the origin |
|---|---|---|---|---|
| royal_left | 7 | 17.8 | - | 0.248 |
| pin_isoleft | 6 | 21.3 | - | 0.255 |
| pin_isoright | 5 | 17.2 | - | 0.247 |
| pin_back | 7 | 15.4 | 3.1 | 0.208 |
| pin_top | 6 | 22.7 | 3.1 | 0.243 |
| v25w_isoleft | 7 | 10.3 | - | 0.263 |
| v25w_back | 7 | 19.3 | 3.6 | 0.205 |
| my27_isoleft | 6 | 4.9 | - | 0.237 |
| my27_left | 6 | 30.2 | 3.8 | 0.265 |
| my27_right | 6 | 20.1 | 3.0 | 0.255 |
| my27_back | 8 | 12.4 | 2.7 | 0.228 |

Landmarks in the helmet frame (mm; x his left, y back, z up; the pair's left member), 1-sigma, the model's own
feature now (its print or part through the art view's old camera, helmet.CAMS), the difference (measured - model)
and the measured point's distance off the model shell (+ outside):

| Landmark | Measured | Sigma | Model now | Difference | Off the shell |
|---|---|---|---|---|---|
| side_screw | (124, -37, -66) | (6, 1, 1) | (125, -21, -69) | (0, -16, 3) | +2.4 |
| release_tab | (106, -87, -132) | (7, 1, 1) | (109, -67, -131) | (-3, -20, -1) | +4.0 |
| rear_slot | (38, 120, 64) | (0, 3, 1) | (37, 118, 68) | (0, 2, -4) | -0.1 |
| crown_vent | (56, 46, 100) | (1, 2, 1) | (58, 15, 115) | (-2, 32, -16) | -8.8 |
| side_vent | (86, 50, 80) | (1, 1, 1) | (96, 55, 74) | (-10, -5, 6) | -4.0 |
| low_vent | (97, 82, -80) | (2, 2, 1) | (98, 80, -78) | (-1, 1, -2) | +0.4 |
| eyeport_triangle | (113, -93, 31) | (7, 1, 1) | (112, -74, 25) | (1, -19, 6) | +8.1 |
| chin_vent | (66, -161, -126) | (9, 1, 1) | (58, -161, -125) | (8, 0, -1) | +6.2 |
| rear_badge | (0, 117, 86) | (0, 1, 1) | (1, 120, 90) | (-1, -3, -4) | -2.4 |
| dot_o | (0, 127, -99) | (0, 1, 1) | (0, 133, -89) | (0, -6, -10) | -0.1 |
| brow_badge | (0, -137, 83) | (0, 4, 4) | (33, -136, 80) | (-33, -1, 3) | -1.1 |
| visor_rear_edge | (0, 21, 115) | (0, 2, 1) | - | - | -14.1 |

Readings of the table:
- Residuals per landmark (px rms over its readings): DOT 2.5, side screw 3.6, rear slot 4.4, eye-port triangle 5.1,
  chin vent 7.1, release tab 8.3, side vent 10.5, brow badge 11.0, low vent 13.5, but rear badge 42.6 and crown vent
  51.9 (to 103 px in my27_left). No rigid, mirror-symmetric solution puts those two on the shell: either the
  crown-back surface between the outlines (seen face-on, which no outline measures) or the traced centre-line profile
  is off there, or a reading is of another feature. To settle first in phase B, before the crown print is re-traced.
- Away from the front the solve agrees with the shell: rear slot -0.1 mm, low vent +0.4, DOT -0.1, rear badge -2.4.
- The crown vent does not: 8.8 mm inside the shell and 32 mm behind the painted vent. Royal_Left alone (the gauge,
  no solve) sees the crown vent at y 36 to 38 mm, z 112 (the print: y 16, z 115) and the visor's rear edge at y 20
  (the model: 8.7). In Leatt's back photo the painted vent through the old back camera lands 137 px (28 mm) above
  the photo's vent. So the crown print (traced through the old top camera, which fits the outline but is pitched)
  sits about 20 mm too far forward and the visor ends about 12 mm short: both phase B (print re-traced through the
  solved cameras; the visor's rear edge).
- The front landmarks (side screw, release tab, eye-port triangle) are 16 to 20 mm further forward than the print:
  the front moves in phase B.

### Published figures (Leatt Technical File 172 r01, in the Moto 8.5 kit document)
Source: pim.leatt.com, Helmet Kit Moto 8.5, `07100200 R22 ALL - MOTO 8.5.pdf`. Shell (W x L x H, mm): XS/S 268 x 361
x 309, M/L 260 x 350 x 300, XL/XXL 252 x 342 x 276. EPS liner: XS/S 260 x 294 x 276, M/L 256 x 287 x 270, XL/XXL 244 x
268 x 255. Weights 1250 / 1305 / 1340 / 1430 g (+-50 g); EPS liner, moulded EVA padding, cheek pads 25 / 30 / 35 / 40
mm. The label in Leatt's photos reads M, 57-58 cm, 1305 g +-50, ECE 22.06 (one M/L shell in all the photos).
Model now: 260.8 x 369.7 x 303.3 mm (width and height within 1 and 3 mm of M/L). The length is 20 mm over the
figure; ours is chin bar to back (Royal_Left's 0.2484 mm/px strap scale), so the file's length is likely measured to
another reference (no drawing in the file). Not changed for it.
Liner build-up (phase B, decision 47): the same file's EPS envelope, M/L 256 x 287 x 270 mm inside the 260 x 350 x
300 shell, with the cheek pads' 25 to 40 mm per size, is the source; the model's shell solid runs 21.3 to 40.0 mm
between the outer surface and his head now.

### The shell rebuilt to the measurement (crown, back, back band, lower rear)
W_Z (half width by height) and Q_Y (by length) refitted to the outlines through the solved back cameras (Pinata,
V25 white; MY27 back as a check, not fitted) and the top camera. Median offset per band, model outside the photo
(+), mm:

| View | main max | main rms | round 3 max | round 3 rms |
|---|---|---|---|---|
| Pinata back (z bands 10 mm) | 3.32 | 2.11 | 1.31 | 0.47 |
| V25 white back | 3.57 | 2.19 | 1.05 | 0.53 |
| MY27 back (check) | 2.89 | 1.84 | 1.00 | 0.46 |
| Pinata top (y bands 20 mm) | 1.22 | 0.70 | 0.72 | 0.50 |

Main was 1 to 3 mm too narrow below z -50 mm and 1.3 to 3.6 mm too wide from z -40 to +10 mm. The fairness test
holds. New test `test_shell_outline_through_the_solved_cameras` (every band within 1.5 mm; main fails at 3.3 mm).
The print was re-traced and redrawn on the new shell.

### Moulded detail away from the front (`scripts/rider/helmet_detail.py`)
Traced in Leatt's Pinata photos (px) and cast onto the shell through the print's cameras (helmet.CAMS), so each
piece stands on its own print. Sizes through the solved cameras (helmet_detail.measure):
- Crown mesh vents (top photo): insert 41 x 28 mm, opening 35 x 21 mm (0.222 mm/px); rim 1.2 to 3.5 mm, raised 1.5
  mm; a triangle lattice of bars 0.85 mm wide, 0.9 mm high (0.6 under the rim), cells 4.7 x 5.6 mm, over the dark
  opening. White plastic, satin (`helmet_vent_insert`, top photo de-lit 202 to 219). The print no longer paints the
  bars (`test_crown_vent_openings_drawn_dark`: main paints 68 % of the opening light).
- Rear exhaust slots (back photo): 30.5 x 6.1 mm (0.194 mm/px). The photos show the slot sunk into the shell with
  its edge rounded down into it: a lip rising 1.0 mm to a crest at the slot (2 mm wide along the top, 1 mm round the
  rest), its inner wall dark. The shell stays closed, so the recess itself is not cut.
- Rear lower white pieces (back photo): the slot 60 x 10 mm through the solved back camera and 59 x 17 mm through V25
  iso-left (its own trace), z -110 to -68 mm; both cameras see it at a grazing 0.13 to 0.43 cosine, so the sizes
  across it carry a few mm. The white frame 4.5 mm wide (4.4 to 5.8 mm on the shell from 8 to 13 px), 2 mm high,
  drawn to a point 11 mm under the slot (42 px), the slot's floor dark 1.7 mm down.
- The frames' outer edges are put on the shell (a tangent offset sank 1 mm into the concave lower back). The goggle
  strap clears every piece by 34.7 mm.
- New test `test_vents_are_moulded_away_from_the_front` (main: no moulded vents).

### Still not right (phase A)
- The crown print and vents sit about 20 mm too far forward and the visor ends about 12 mm short (above): in the top
  view at 1:1 the visor's rear edge covers the vents' front 4 mm, where Leatt's edge is 10 mm ahead of them.
- The print round the rear lower pieces is not Leatt's (magenta and grey where the photo has the white piece's
  plate, the white band and black): traced at a grazing angle in both views. The pieces read rounder than Leatt's
  flat plate.
- The rear slots' crest reads brighter than Leatt's soft edge.
- The "moulded ridge line across the crown" of the brief is the visor's rear edge (top photo: the print crosses its
  step): phase B.

## 7. Round 4 (2026-11-15, decision 50): crown, print, visor, vents, rear pieces

Away from the front only: the brow, the face port, the chin bar, the helmet's place on his head and the goggle wait
for the joint front fit (decision 47).

### The crown: why the crown vent and the rear badge sat 43 to 52 px off the shell
- Royal_Left is now solved free (round 3 held it as the gauge). It sits 1.4 to 2.3 deg off the side axis and 3.3 to
  3.7 deg above it, not the 8 to 11 deg the old iso cameras implied, and the centre-line profile's silhouette fits its
  outline at 2.0 to 2.5 px (0.5 to 0.6 mm). The profile is right; the shell was not changed.
- The 43 to 52 px were forced readings. The rear badge was held on the profile: free, its four readings agree to 4.5
  px rms and put it 22.6 mm inside the shell. The crown vent's side views had been read at its front end: read as the
  centroid of its outline they still leave 26.9 px rms over 16 readings, the back views seeing the vent 10 to 15 mm
  lower than the side views, the solved point 9.5 mm under the shell.
- Reading of it: the crown has relief that the smooth shell has not. The silhouettes are the raised vent pods and
  the rear ledge; the vents and the central panel lie lower between them. No outline sees that surface face-on, so it
  is not measured yet (a later round, from the iso views' shading).
- The top camera had no landmark at the front: free, it stretched 185 px (45 mm) past Leatt's visor tip. New landmark
  `visor_tip` (Royal_Left, top, MY27 left and right; MY27's only along the length, its visor angle differs). Reduced
  chi-square 2.50 to 2.02; twelve cameras (Royal back added).
- Left over: the top photo puts the crown vents and the visor's rear edge 10 to 12 mm further forward than the side
  views do (Leatt's visor tip to rear edge: 216 mm in the top photo at 0.238 mm/px, 228 mm in Royal). No rigid
  mirror-symmetric shell takes both; the solve shares it out.

| Camera | Landmark rms round 3 (px) | Round 4 (px) | Outline rms round 4 (px) |
|---|---|---|---|
| royal_left | 17.8 | 9.6 | 2.5 |
| pin_isoleft | 21.3 | 8.0 | - |
| pin_isoright | 17.2 | 6.0 | - |
| pin_back | 15.4 | 13.7 | 3.7 |
| pin_top | 22.7 | 6.8 | 2.0 |
| v25w_isoleft | 10.3 | 8.6 | - |
| v25w_back | 19.3 | 14.0 | 3.5 |
| my27_isoleft | 4.9 | 6.5 | - |
| my27_left | 30.2 | 11.5 | 3.6 |
| my27_right | 20.1 | 11.6 | 3.5 |
| my27_back | 12.4 | 9.8 | 2.7 |
| royal_back | - | 11.1 | 3.3 |

Front landmarks against the model now (measured, model; mm): brow y -136.6 / -139.7, chin vent y -158.1 / -156.9,
eye-port triangle y -95.0 / -89.7, release tab y -86.3 / -85.9, side screw y -39.3 / -39.3. Round 3's 16 to 20 mm
were the old cameras.

### The print re-traced through the solved cameras
- `helmet.PRINT_CAMS` are research/helmet-ba.json's Pinata cameras; the print and the moulded parts are cast through
  them. The black blobs under each crown vent (round 3 sheet 02, main and r3) are gone: they were the old print's
  vent openings, misregistered. The built vent insert lies on its traced outline in the top photo within 2.5 px.
- The print round the rear lower pieces comes from the back camera (`helmet_art.BACK_ZONE`): the iso-left view had
  drawn the white piece's edge out as a spike over the black (back photo px 500 to 540, 1495 to 1520).
- To re-trace in the joint round, after the front moves: the brow badge, the eye port's black trim and grip panel,
  the chin (cap, vent, chin text), the side icon, the emergency labels, the visor's side LEATT (distorted now) and
  EIGHT POINT FIVE.
- The visor's chevrons, cast column by column through the solved top camera, landed 5.0 mm from mirror places
  (centres (81.3, -107.8, 112.6) and (-83.6, -105.5, 108.8) mm; main 1.9 mm). Leatt's art is symmetric: the mirror
  of either column's cast lands 14 px (3.5 mm) from the other column in the photo, and the visor's sloping side
  stretches that along the surface. The camera's error at the visor's tip and the visor's height there (4.4 mm high
  in Royal) are the likely cause, not the print. Each column's outline is now moved in the photo half way to the
  mirror of the other's cast (7.3 and 6.8 px, `proj.shift`): both at (+-82.4, -106.6, 110.8) mm, gap 0.04 mm, each
  within 2 mm of its own photo place. The joint round's visor height should bring the casts together by themselves.
- Seen, not done: the side exhaust vent is a painted black blob (Leatt: a dark slot with lit walls).

### The visor
- Rear end: the tongue's end kept at y 8.7 mm on the centre line. Through the solved cameras Royal (u 1135) and
  MY27 left (1082, 316) put it there; the top photo puts it about 10 mm further forward (above). The brief's 20 mm
  came from round 3's top and back triangulation.
- Rear edge in plan, from the top photo at 3x (both sides traced, cast through the solved top camera onto the shell
  offset by the visor's gap, mirrored and averaged; the sides agree within 1.3 mm but at the corner): a tongue over
  the crown's centre (straight to |x| 22 mm, rounded to 30), the edge then running forward along the crown, steeply
  to |x| 46 mm (22 mm ahead of the tongue's end) and gently to a corner 37.5 mm ahead at |x| 90 mm, then back up the
  wing to |x| 113 mm, 15 mm ahead (y -6.2 mm: Royal's corner at u 1075). Main's ran straight across at the tongue's
  end, 8.3 mm ahead of the vents, and its rear row gathered into one point at the centre (folded quads: the white
  sliver at the visor's rear in the top view, sheet 03). Now, with the tongue's end put on the photo's (44.6 px),
  the edge lies within 7.5 px (1.8 mm) of every traced point, median 2.3 px; over the vents' columns it stands 24.1
  mm ahead of the inserts' front (Leatt's photo: 29 to 43 mm at the vents' own columns; ours 30 to 33).
- How: the visor's grid is built 8 times finer across; where each fine column first crosses the rear edge gives the
  edge, and the band behind y -60 mm is remeshed from that station to the edge, each column going to the edge's point
  at the same share of its length. Sliding each arch column to its own crossing folded quads where the columns run
  nearly along the edge's steep part. Behind the side corner the low line now runs on at the corner's height (main
  rose to the crown for its straight edge).
- In Royal the edge's corner shows at (1005, 464), Leatt's at about (977, 452): 7 mm further forward, relative to the
  tongue, than the top photo gives. Kept to the top photo (the plan view).
- Plan from the top photo through the solved top camera, row by row against the photo's outline: main stood 15 to 18
  mm too wide 8 mm behind the tip (Leatt's tip is pointed in plan), 10 to 11 mm at 15 mm and 1.5 to 5.6 mm along
  its sides; now within 3.2 mm from 5 mm behind the tip to y -112 mm (both sides, with the camera's 1.5 mm offset to
  one side all along). The silhouette's rows near the tip agree within 6 px.
- Wings (y -103 to -56 mm): 2 to 9 mm outside the photo's outline. The shell itself stands 0.4 to 3.2 mm outside it
  there (the temples) and the wing must clear it: the wings' edges now come down to 4.5 mm off the shell (1 mm under
  the visor) from 7.5. The shell's width at the temples belongs to the joint round.
- Height: through the solved Royal camera the visor's top line stands 7 to 18 px (1.7 to 4.4 mm) above Leatt's, most
  at the tip (the tip solves at z 136.1 mm, the model's 140.6). Its angle is adjustable (MY27's sits lower still).
  Not changed: the joint round sets the visor on the front.
- Not modelled (joint round): the screw in the triangular window of each wing (Royal at (865, 615)), the window, and
  the visor's two moulded vents (printed black now).

### The crown vents' shape
- From the top photo at 3x: the opening a rounded parallelogram, hull lines top -23, right 94, bottom -21, left 100
  deg (opposite sides within 6 deg of parallel through the camera), corners 6 px (1.5 mm); one rim 8 px (2.0 mm) all
  round, the insert's outline the opening grown by 8 px. Main's two quads traced by eye gave a 6 to 12 px surround.
- The lattice fitted to the photo's bars: cells 24.1 and 24.2 px (6.0 mm) a side, 119.5 deg apart, the third side
  24.3 px (main: 21.4 and 25 px, 108 deg). Bars 1.0 mm (4.5 to 5 px at 3x).
- The rim is a flat plate with crisp edges (each band its own vertices, a 0.2 mm chamfer), 1.5 mm proud: the first
  build, shared vertices, shaded as a round tube against the photo's flat top with a bright inner edge.

### The rear exhaust slots
- Rendered at 3x in the Pinata back view: the round 3 lip 1.0 mm proud, a lip 0.4 mm proud with a 0.3 mm round, 0.2
  mm proud, and a thin dark edge. Under the clear coat every raised edge showed a bright line (the coat's reflection
  of the light backdrop on its round), the dark edge a black outline. Leatt's slot is a recess with no rim; the
  shell stays closed, so the slot is the print's dark with the wire mesh in it (two sets at 40 deg, 1.6 mm apart,
  0.35 mm wires, 0.2 mm over the shell) and nothing raised round it.

### The rear lower pieces
- A flat plate 2 mm over the shell, top flat within 0.2 mm, crisp edges (each band its own vertices, a 0.2 mm
  chamfer): away from its point 3.6 % of its vertices join faces more than 20 deg apart (main's round loop 69 %).
- Its point: the photo's point (481.5, 1594.5) is the raised top's. The back camera sees it at a cosine of 0.42, so a
  top 2 mm proud shows 8.3 px left of its foot; the foot is placed for the top's point to land on the photo's (now
  within 1 px).
- A dark wire mesh fills the slot (as above, its top 0.9 mm over the floor's shell). Mesh material 36/37/40, rough
  0.4 (the photos: near black, faint glints).
- The print round it from the back camera (above).

### The length: TF 172's 350 mm against our 369.7
- Not the same 20 mm as the brow's 20.6. Our 369.7 is a bounding box: the chin's front (y -220.8 at z -80) and the
  back's bulge (y 148.8 at z -35) at different heights. Length per height: 359.6 mm at most (z -80), 347.9 at z -95.
  No pitch gives L 350 with H 300 (pitched 12 deg: L 351.7, H 342.8).
- The brow's 20.6 mm was round 3's old cameras: through the solved ones the front landmarks agree with the model
  within 1 to 5 mm (above), and the Royal outline, chin included, fits at 2.5 px.
- The EPS figure fits the model: brow (y -140) to back (148.8) is 288.8 mm against the EPS's 287. So the file's
  shell length is likely taken at another height or reference; the shell is left as the photos give it.

### Liner numbers for the joint round (Technical File 172, M/L; nothing moved)
- Shell 260 x 350 x 300 mm, EPS 256 x 287 x 270: the shell wall about 2 mm (width) and 1 mm (length, brow to
  back, against our 288.8). EPS height 270 against the shell's 300: the shell's lower edge runs about 30 mm below
  the EPS.
- His head (size L, 592 mm round) on the model's placement (pitch 16.5 deg): skull 145.7 mm wide, 201.6 long, its
  top 85.3 mm up (shell top 129.9). EPS plus comfort padding at the EPS's widest: (256 - 145.7) / 2 = 55 mm a side;
  front and back (287 - 201.6) / 2 = 42.7 mm. At his head's widest (z 16 mm) the model's shell is 243.8 wide: 47 mm
  a side less a 2 mm wall.
- Model now: outer surface to his head 48.2 top, 47.9 back and sides, 39.0 at the forehead; solid 21.3 to 40.0 mm
  thick.
- Cheek pads 25 / 30 / 35 / 40 mm in the file, beside the weights 1250 / 1305 / 1340 / 1430 g (the label in Leatt's
  photos: M, 1305 g). If the pads follow that order the M is 30 mm and the L 35; to read from the file's table in
  the joint round before the cheeks are built.

### Tests (all fail on main)
- `test_crown_vent_outline_and_lattice`: even 8 px surround, parallel sides, rounded corners, equilateral cells (main:
  surround 10.5 px on one side).
- `test_rear_pieces_soft_slot_edge_flat_plate_point_and_mesh`: nothing of the exhaust slot over 0.5 mm, the plate's
  top flat at 2 mm, its edges crisp, its point within 3 px of the photo's, a mesh in both slots (main: the lip 1.01 mm).
- `test_print_round_the_rear_lower_piece`: black and white at seven points picked on the back photo (main: magenta
  at (505, 1500)).
- `test_visor_plan_on_the_top_photo`: the visor's edges within 3.5 mm of the top photo's outline from 5 mm behind
  its tip to y -110 mm (main: its first station falls 139 px beyond the photo's tip).
- `test_visor_rear_edge_on_the_top_photo`: the rear edge within 8 px of 52 points read on the top photo's edge
  (median under 3), at least 20 mm ahead of the vent inserts over their columns, no folded quad (main: 467 px off,
  median 205).
- `test_vents_are_moulded_away_from_the_front` takes the mesh material.

### Still not right
- The crown's relief (pods, ledge, the lower central panel) is not modelled; the crown vent's readings disagree by
  10 to 15 mm in height between the back and side views.
- The top photo and the side photos disagree by 10 to 12 mm along the crown.
- The visor stands up to 4.4 mm high at the tip through the solved Royal camera; its wings 2 to 9 mm outside the
  top photo's outline over the temples; its rear edge's corner 7 mm behind Leatt's in Royal; no window, screws or
  moulded vents.
- The crown vents' rim: Leatt's reads thinner on the side towards the centre line (5 px against 8 to 11 on the outer
  side); ours is even, as asked.
- The rear exhaust slots' edge is the print's: no moulded roll (the shell is closed).
- In the iso views the front (black eye port too high and too big, the visor low over it): the joint round.

## 8. Joint front fit, phase 1 (2026-11-15, decision 47): his views, the fit on his head, the eye port, the goggle

### His photos as cameras on the helmet (item 1; `his_cameras.py`, `research/his-photo-cameras.json`)
p07, p08 and p09 were set by eye. Each photo is now a camera in the helmet frame, fitted to the helmet's measured
points (helmet_ba's solved landmarks, the print's centres, the visor's chevrons) read on his photo, then to the
print's colour (Lab a*, b* correlation in a helmet mask; Powell on 7 parameters). `head_closeups.py` renders them
through the shell's `gear_frame` (helmet.extras writes `helmet_shell__frame`, build_rider keeps it), as the photo's
crop round his head at 4x its pixels.

| photo | camera seen from the helmet (az, el) | landmarks rms | colour NCC | px per mm | worst reading |
|---|---|---|---|---|---|
| 07 | 94.0, 1.0 deg (his left, side-on) | 2.6 px | 0.39 | 0.39 | chevron L0 4.6 px |
| 08 | -1.0, 42.0 deg (ahead and above) | 4.5 px | 0.74 | 0.46 | visor tip 7.8 px |
| 09 | 41.0, 29.0 deg (front left, above) | 8.3 px | 0.43 | 0.51 | visor tip 14.7 px |

- 08 sees the crown from ahead and 42 deg above: his head pitched far down in the whip, the sky behind. Main's p08
  saw his face from below.
- Head pitch against the torso (scratch torso.py: the rest torso, spine05 to neck01, carried by the placement and
  turned about the neck's side axis, matched to the photo's pelvis-to-neck line): 07 +2 +-5 deg chin down from
  standing (the torso 233 px long against the photo's 264). 08: not determined (the torso is end-on: 6 px of its
  180 projected). 09: -39 deg if pitch alone (-47 to -31), -65 to -10 with a turn; not determined.

### The helmet on his head from the liner (item 2; helmet.fit_on_head, build_up)
- Source: Leatt Technical File 172 r01, M/L: EPS 256 x 287 x 270 mm (W x L x H). The table's outer rows read
  reversed against the weights (XS/S 268 x 361 x 309 is the largest, XS/S 1250 g to XL/XXL 1430 g); M/L, the middle
  row, is the same either way. His head: size L, 592 mm round.
- Build-up = (EPS length - his head's length) / 2 + the shell wall: (287 - 211.8) / 2 + 0.9 = 38.5 mm (his head 211.8 mm long, forehead to back, head_landmarks) at crown,
  forehead and back (the wall: our brow-to-back 288.8 mm against the EPS's 287). The crown takes the same (EST: the
  file gives no crown figure).
- Pitch, fore-aft and height fitted to it (grid, then least squares on the three stand-offs): pitch 13.1 deg (main
  16.5), the brow 65.5 mm ahead of and 37.7 above his eyes; stand-offs top 37.6, forehead 39.9, back 39.8, sides
  46.3 mm (the cheek pads and the EPS's flare fill the sides). Main: top 48.2, back and sides 47.9, forehead 39.0,
  set by two rules (port top 40 mm above his eyes, forehead at least 32 mm behind the brow).
- Check: upward clearance from his eyes to the port's top edge 29.9 deg (ECE 22.06 6.15.3.2 asks 7).
- Cheek pads: TF 172 lists 25, 30, 35, 40 mm without a size map. A larger head takes the thinner pad, so L 30 mm and
  M 35 (EST). Not built (phase 2).
- Against his 07 and 09 (coarse, 0.39 and 0.51 px a mm): the goggle's top matches in 07 (y 117 px); its bottom reads
  7 to 10 px lower in the photo, and the chin bar about 10 px lower.

### The eye port's cut edge (item 3; helmet.PORT_REAR, PORT "iso")
- Round 2 cast its iso-left picks through that photo's own camera (CAMS); through the solved camera (PRINT_CAMS) the
  same picks land 16 to 18 mm further forward and 6 to 14 mm further in: the side edge at y -65 to -72 mm, 16 to 23 mm
  behind main's side notch (-88, the cheek pads in Royal_Left).
- The picks are the crest where the outer surface turns into the port: right of it Leatt's grip panel (triangle
  relief), left of it the trim's ribbed inward roll (iso-left 1160 to 1197 px, iso-right 710 to 760 px). Mirrored,
  the edge lands on the iso-right photo's crest within about 5 px.
- The built port is now "iso": the edge test reads -11.4, -3.1, +1.9, +5.3 px at rows 830 to 1040 (main -114 to
  -174).

### The print re-traced on the new front (item 5; helmet.ISLANDS, atlas_uvs, helmet_art.force_labels)
- The streaks in the visor's side LEATT: all of the visor was one top-projected island (V); on the steep wing a
  texel stretched about 1 / |n_z| times (texel area against surface area: 31 at the 99.5th percentile, 56 at most),
  so the print stepped in horizontal bands.
  Each visor face now goes to the island of its normal's largest component: VL and VR by (y, z) for the wings, VF and
  VB by (x, z) for faces turned forward or back, V for the rest (a quad's normal from its diagonals: the tip's first
  three corners nearly meet). Stretch now under 2 at the 99.5th percentile (three twisted triangles at the rear
  corner up to 4.5). The new islands sit in the atlas's free band (u 1214 to 3464, v 2918 to 3833 texels).
- The two blue slivers and the thin grey marks on the wing: the photos' visor rear edge line (grey) and the shell's
  blue beyond it fell on our wing, whose rear corner stands 7 mm off Leatt's. The wings are white print in every
  Pinata photo (the LEATT is drawn from the file over them): force_labels now marks them white.
- Re-traced through the solved cameras on the iso port and the new islands (brow badge, port trim, grip panels,
  chin, side icon, emergency labels, EIGHT POINT FIVE and the visor's LEATT are fitted again by the same trace):
  visor side LEATT IoU on the shell 0.56 (from 0.39 at its start), EIGHT POINT FIVE residual 2.9 mm.

### Measuring the white (item 6; report only, nothing changed)
- Leatt's top photo, the flat visor spot: 225 to 233. Ours in the studio top view 178 to 184 (visor top 163 to 181).
- Rendered flat (emission, Standard, 0 EV) the same spot reads 226 / 229 / 235: BASE_WHITE, the photo's white. The
  clear coat is not it (without it within +-3).
- Crown sides at (560, 900) and (1360, 900): ours 147 to 163 against the photo's 157 to 170 (92 %); the visor's top
  gets 55 % of the photo's linear light. The studio's lights stand off-axis round the camera, so faces turned up in
  the top view are under-lit. The light, not the material. No look settings changed.

### Tests (each fails on main)
- `test_his_photo_cameras_fitted_to_the_helmet`: rms under 4, 6, 10 px; colour NCC over 0.35, 0.7, 0.4; 07 from his
  left, 08 from ahead and above, 09 from the front left and above; head_closeups uses the file (main: no module).
- `test_gear_frame_places_the_helmet_frame`: the npz carries the helmet frame's placement (main: not in the archive).
- `test_fit_on_his_head`: build-up 36 to 41 mm, crown, forehead and back within 2.5 mm of it, the sides more and
  even, up clearance 7 deg at least (main: no build-up).
- `test_face_port_edge_on_leatt_iso_left`: through the solved camera, within 12 px of the photo's crest (main -114
  to -174 px).
- `test_visor_wings_have_side_islands`: visor texels stretch under 2 (99.5 %) and 5 (all), the islands apart (main
  30.6 and 56.2).
- goggle: `test_strap_crosses_the_trim_to_the_shell` (every station 45 mm wide, each point across the landing 2 mm
  or more behind the cut edge at its height; main 31.9 mm ahead); `test_strap_lies_where_his_07_shows_it` (the
  strap's edges under 10 mm rms off his 07 through its fitted camera; main 39.1);
  `test_outriggers_rest_on_the_shell_and_hold_the_strap` now asks the plate's back end within 15 px of Leatt's
  iso-right and only its top back corner on the shell.

### Still not right
- The visor: tip 4.4 mm high in Royal, wings 2 to 9 mm wide over the temples, rear corner 7 mm off (not moved this
  phase: item 3's visor and the trim's roll and chin bar remain).
- The trim's roll: ours RIM_R 4 mm; Leatt's ribbed inward roll reads 9 to 14 mm in the iso photos.
- His 09 camera: 8.3 px rms (visor tip 14.7 px off); 08 and 09's head pitch against the torso not determined.
- The cheek pads are not built (the side photo's notch).

### Phase 2 plan (decision 51, not started)
1. Front moulded details: grip panels with the triangle relief (iso-left 1:1: cells about 30 px, 7 to 8 mm, across; their depth to read), the
   chin vent mesh and mouthpiece, the chin LEATT, the brow vents and the brow tag.
2. Visor details: screws, the top windows (Leatt's back view), moulded vents, a crisp rear lip with its shadow line;
   reshape its tip, wings and rear corner to the solved Royal and top cameras first.
3. The crown side vents as geometry.
4. Later: the crown vent pod and a thinner rim, the rear slot's chamfered end, the rear lower slot's taper, the rear
   spoiler shelf, the lower centre panel.

