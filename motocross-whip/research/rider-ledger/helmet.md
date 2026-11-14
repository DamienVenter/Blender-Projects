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
| Visor chevrons x7 a side | **vectorised from the top photo**, where they are seen square-on (4 px per mm): dark components (below 90 on white) of 1200 to 2000 px in the columns x 1220-1480 (his left) and 440-700 (his right), y 950-1540; each outline at half contrast between its own black core and the white ring round it (sub-pixel contour, Douglas-Peucker 0.6 px), black ink, projected onto the visor through the top camera; the traced black under them erased 3 mm round | 7 a side, centres x +-78.7 mm, columns 102.7 and 101.2 mm long, each about 10 x 21 mm | top |
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
