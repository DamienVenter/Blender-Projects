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

## 3. Graphics (Pinata Teal art)
| Number | Value | Source |
|---|---|---|
| Method | Leatt's four Pinata views projected onto the shell and visor top through pinhole cameras fitted to the model's outline (chamfer both ways, half resolution; residual rms 10 to 20 px at half res), each texel from the views that see it (cos^4 weights, depth test), mirrored point for the 9 % no view sees, base white elsewhere | `paint_atlas`, CAMS |
| Atlas | `textures/rider/helmet_pinata.png`, 2048 px, 2.15 px/mm, islands by face normal (left, right, top, back, front, visor) | |
| Goggle in iso-right | hand-drawn polygon ISORIGHT_GOGGLE masks the goggle and strap out of that photo | |
| Finding | the big white LEATT on the iridescent band behind the eyeport (Leatt iso-right, his 07 and 09) is the **goggle strap's** print; the helmet's side there carries the iridescent field and white chevrons (Leatt iso-left, no goggle) | photos |
| Limits | studio reflections are baked into the art; the chin front reads too dark (the model's chin is blunter than the real one, so the black vent grille spreads); small print is 5 texels high | review sheets |

## 4. Goggle: Velocity 5.5 Iriz, Pinata Teal frame, Purple 78 %
| Number | Value | Source |
|---|---|---|
| Frame outer | 188 x 92 mm (half width 94, top 35 above the eye centres, bottom 57 below), rim 8 / 9 / 10 mm, nose cut 30 mm high, 84 mm wide | height: MY27 side view with the goggle on (386 px x 0.241 mm/px = 93 mm); width: fits the port at eye height; rims and nose: Leatt goggle iso (EST) |
| Lens | double sheet 2 mm, elliptical plan 115 / 75 mm half axes (170 deg wrap, ends 36 mm back), centre 74 mm ahead of his eye centres | Leatt features (WideVision 170 deg), EST |
| Frame depth, face foam | 20 mm, 14 mm (foam's back on his face, conforming) | EST (triple-layer foam) |
| Outriggers | 46 mm long, 50 mm tall, 7 mm thick, black, white vertical LEATT, letter tops to the frame (reads top to bottom on the right) | Leatt goggle iso, Pinata iso-right |
| Tear-off posts | bare, 5 mm, 83 mm off centre | Leatt features; decision 7 (no tear-offs) |
| Strap | 45 mm, 2 mm, 4 mm off the shell, front point from the MY27 side view, running back 5 deg down in the helmet frame as in his photo 07 (Leatt's product shot: 7 deg up); print: orange-yellow at the goggle, magenta, purple, teal round the back, white LEATT each side reading from outside | Leatt features (45 mm), MY27 view, his 07, Leatt goggle iso |
| Frame colour | sRGB 196, 28, 78 raspberry | his photos 07, 09 (Leatt's render is hot pink) |
| Lens material | transmissive, light purple; Iriz mirror wants a thin film (520 nm, IOR 1.6) that build_rider does not read yet | Leatt 78 % VLT |
| Contacts with the shell | frame 8, face foam 48, outriggers 2, strap 18, visor 45 vertices inside the shell solid (pads and trim pressed, visor seated): lens none | winding numbers, not yet driven to zero |
