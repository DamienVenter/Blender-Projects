# Scene look (decisions 54 and 55): fitted to his phone's photos

Round 1 (decision 54) and round 2 (decision 55), 2026-11-15. The look every render of the bike and the rider goes
through, fitted on pixel-aligned pairs of our daylight renders and his photos 07, 08 and 09. Module:
`scripts/common/scene_look.py`; the daylight rig: `scripts/common/day_rig.py`; fit, report, red and sheets:
`scripts/common/look_fit.py`; Blender check: `scripts/common/look_apply.py`; tests:
`scripts/common/scene_look_checks.py` through `scripts/rider/test_scene_look.py` and `scripts/bike/test_scene_look.py`,
`scripts/rider/test_day_rig.py`.

Round 2 in short: his sky (deep blue) replaces the cream glow, the look is refit on that light, each comparison with
one of his photos is shown at that photo's own exposure, the bike's plastic red is his 07's, and the gear is measured
again for the materials round. Sections marked (round 2) replace round 1's numbers; round 1's stay below them where
they explain a choice.

## The look

| step | what | value (round 2; round 1) | source |
|---|---|---|---|
| 1 | gains (white balance, exposure) | log2: EV -0.847, R +0.107, G 0, B -0.165 (round 1: EV 0.102, R +0.234, B -0.302) | WB: the white shell, below; EV and the curve: the fit, below |
| 2 | tone curve on max(R, G, B), the three channels scaled by T(M)/M (hue and channel ratios kept) | T(u) = m u^P / (1 + u^P), P 2.21 (round 1: 2.59), m so that T(8) = 1 | the fit |
| 3 | view | Standard (the sRGB curve, clipped) | |
| "scene" kind | studio-lit views (build_bike, build_rider, rake, head_closeups' studio) | neutral gains 2^(EV + 1.514) (round 1: EV + 0.832) | 0.18 linear at 69, where decision 46's AgX - Punchy -0.6 put it (look_apply.py, Blender 5.2.3) |
| "studio" kind | Leatt's and Honda's studio comparisons | Standard at the caller's exposure | decisions 44 and 46, unchanged |
| PHOTO_EV | a view of one of his photos (head_closeups p07, p08, p09, cam07) | daylight at EV + 07 -0.045, 08 -0.147, 09 -0.649 | "Each photo's exposure", below (round 2) |

Steps 1 and 2 are a compositor node group ("scene_look": math nodes) set on `scene.compositing_node_group`; the
view's curve mapping cannot do step 2: it works per channel, and its film-like mode still sends the smallest channel
through the curve. Renders show it; the viewport shows it with Viewport Shading's Compositor on Camera or Always.

Grey ramps (G channel, 8-bit; Blender 5.2.3 through look_apply.py, equal to `display()` within a level):
- "scene", linear 0.02, 0.045, 0.09, 0.18, 0.36, 0.8, 1.6: **2, 10, 31, 69, 131, 209, 243** (round 1: 1, 6, 26,
  69, 143, 225, 250; decision 46: 4, 19, 41, 69, 103, 146, 179). More contrast than decision 46: his photos crush
  the darks (the coordinator's measures, LOOK1 brief: darks 12 to 29 in his photos against 47 to 88 in ours).
- "daylight", linear 0.062, 0.123, 0.244, 0.486, 0.966, 1.92, 3.82, 7.59: 2, 10, 30, 68, 128, 194, 232, 244 (round
  1: 4, 20, 55, 120, 193, 228, 236, 237; R reaches 255: a render-neutral grey reads warm, as the phone balances the
  rig's blue sky light away).

## The daylight rig (round 2, `day_rig.py`)

One module builds the daylight world for every daylight render: `head_closeups.daylight` and
`goggle_views.daylight` call `day_rig.build`, their `day_sun` calls `day_rig.aim`. build_bike.py, rake.py and
build_rider.py have no daylight scene (studio only), so none uses it yet.

| part | value | source |
|---|---|---|
| sun lamp | 4 x 2^3.4 = 42.2 W/m2, white, 0.53 deg disc | decision 46's DAY_GAIN (the look's exposure is referred to it) |
| sky | Blender's multiple-scattering sky, air, aerosols, ozone 1, altitude 100 m (the default clear atmosphere), its own sun disc off | the fit below |
| sky strength | 42.2 sin(78 deg) / 141.03 = 0.293 | as bright against the lamp as against its own sun: its disc gives a level white plane luminance 141.03 at strength 1 with the sun 78 deg high (1024 samples) |
| sun height for his photos | 78 deg | his 07's bike shadow (one session, minutes apart) |
| ground | albedo 0.41, 0.40, 0.36, lit by the sun and the sky (E1 table: the sky's irradiance on a level plane by sun height, measured in Blender, `day_rig.py -- e1`) | his 07's pavement over his white shell's top x 0.8 (decision 46) |
| light groups | lamp "sun", world "sky" | Combined_sun and Combined_sky passes in linear renders (not denoised) |

His photos' cameras ride the posed helmet, so the blend's seated pose had set the sun's height to 67, 12.7 and 36.3
deg in p07, p08 and p09. `aim(..., elevation)` now turns the world (a Vector Rotate on the sky's and the ground's
coordinates) so the sun stands 78 deg high, with no camera roll and the lower of the two pitches that do it: p07 4.7
deg (the look-up of cam07's camera, fitted to the bike independently), p08 28.7, p09 30.5. With the camera 12 m from
his head that puts the head about 6 m above the camera; the other root (about 51 deg) would put it above the whip's
apex (centre of mass 9.65 m, fmx-ramp-physics-whip.md). Checked in Blender: the turned rig against the unturned rig
seen by the turned camera, p95 relative difference under 0.001 (test_day_rig.py).

Learned in Blender 5.2.3: the multiple-scattering sky has no Vector input while its sun disc is on (the socket
disappears and links are ignored), so the disc is off and the lamp is the sun; `sky_ground_albedo` has no effect on
that sky (0.1, 0.3 and 0.6 gave the same light to 4 digits).

The fit (each configuration with the white balance refit and each photo at its lit exposure; shade = the white
shell's pixels in the bottom quartile of Combined_sun, lit = the top quartile; sky09 = the sky behind him in 09):

| configuration | shade dE | lit dE | sky 09 dE |
|---|---|---|---|
| decision 54's sky (round 1, at each photo's exposure) | 8.2 / 36.4 / 35.9, mean 26.8 | 2.7 / 6.1 / 6.6 | cream, not blue |
| **default atmosphere, white sun, strength 0.293 (shipped)** | **6.2** (07 5.7, 08 5.8, 09 7.2) | 3.8 | **1.4** |
| the same, strength 0.159 (the shade's own best) | 5.7 | | 17.4 |
| the model's own sun colour (1.13, 0.98, 0.79 at 78 deg) | 7.6 | 3.1 | |
| aerosols 0, 0.5, 2, 4; air 0.5, 2; ozone 0, 3; altitude 1500 m; ground albedo 0.1, 0.6 | 6.0 to 7.8 | | up to 17 off |

The shade stays at about 6 dE whatever the atmosphere: 07's shade is 4.1 L* darker in ours (his phone lifts it),
09's 6.9 b* less blue. The sky behind him in 08 is further off than 09's (8.5 dE).

## Pairs

- **His 07, 08, 09**: `head_closeups.py` p07, p08, p09 (cameras fitted to the helmet, `research/his-photo-cameras.json`,
  decision 47), daylight rig unchanged (sun 4 x 2^3.4, DAY_SUN per view), 64 samples, `SCENE_LOOK=linear`
  (multilayer float EXR with Diffuse Color, Depth and Material Index passes; `SCENE_LOOK_INDEX` writes the material
  table). Rider: build_rider.py on main's gear (helmet, kit `--no-tex`, gloves, boots) with the bike
  (`RIDER_BIKE=blend/bike_v7.blend::bike_v7`) in pose.py's "seated" pose (his photo 05's seat position; not fitted
  to 07, 08 or 09). The render is 4 x the photo's crop, so 4 x 4 blocks lie on photo pixels.
- **The bike in his 07** (cam07): `research/rider-cameras.json`'s camera fitted to photo 07, the whole frame at 2 x,
  p07's sun setting (head_closeups with its photo crop opened to the frame, a scratch wrapper). Camera rms up to about
  15 px on the bike, and the rider's pose is not his, so only colour statistics are used there (the red, the kit).
- **Masks**: a photo pixel is kept when its render block is one material and one albedo class, eroded by about the
  camera's rms (p07 3, p08 5, p09 8, cam07 8 px). Classes from the Diffuse Color pass (`look_fit.classify`).
- **Used in the fit**: the helmet's white shell and its black print (all three photos); magenta print as a check
  (p07 only, 167 px). Dropped: the goggle frame (8 px in p07, off its thin part in p08), the sky (a cream glow round
  the sun in our rig, deep blue in his photos: the rig's sky, not the look), the bike's red and black and the boots
  (pose and the 15 px rms; RED was tuned under the old look).

Pixels per class (p07 / p08 / p09): white 1426 / 1312 / 919, black 432 / 269 / 33, magenta 167 / - / -.

Round 2's pairs: the same renders and masks with day_rig's light (the sky turned to his sun's height), plus the
Diffuse Direct and Indirect passes (to relight a surface with another albedo: lin + light x (new - old), exact but
for interreflection) and the sun and sky light groups; the same pixel counts. cam07 was given p07's sun (90, 106.7):
cam07 has no DAY_SUN entry in head_closeups.py and takes DAY_SUN_OTHER (90, 110).

## The fit

Objective per (view, class): CIELAB of the median colour and L* of the 25 % and 75 % luminance quantiles, render
against photo, each group the same weight, soft L1 at 10 dE (`look_fit.fit`). A per-pixel loss preferred spread over
colour (AgX: pixels better, medians 21 to 30 dE) and was dropped.

White balance from the white shell (neutral paint): log2(photo linear / render linear), R and B against G, median
over the photos: R +0.234, B -0.302. A free white balance went blue (+0.2 on B) to fit the black print's sky
reflection and turned neutral greys blue.

His phone exposes every shot itself, so the shipped procedure fits **one exposure per photo** and the curve P
shared; EV is their mean. With one shared exposure the curve went to P 4.0 to make up the difference; each photo
alone gives P 2.23 (07), 2.85 (08), 2.39 (09). Per-photo exposures (log2, over EV): 07 -0.21, 08 +0.64, 09 -0.43
(white and black); from the white shell alone 07 -1.04, 08 +0.91, 09 -0.60.

Candidates, fitted on white, magenta and black of all three photos and with each photo held out (mean dE of the
class medians; before = decision 46's look on the same pairs, through Blender):

| model | params (all three) | fitted | held p07 | held p08 | held p09 |
|---|---|---|---|---|---|
| before (AgX - Punchy -0.6) | | 21.1 | 27.8 | 16.9 | 15.3 |
| Standard, exposure | ev -1.56 | 20.8 | 24.9 | 20.3 | 16.3 |
| Standard, exposure, WB | | 20.7 | 26.8 | 21.2 | 21.4 |
| PBR Neutral, WB, saturation | sat 1.34 | 15.7 | 28.8 | 16.2 | 16.1 |
| AgX - Punchy, WB, saturation (compositor) | sat 2.02 | 18.6 | 30.8 | 21.4 | 17.7 |
| curve per channel, free WB | wb +0.21, P 3.81 | 6.3 | 14.6 | 6.2 | 9.8 |
| curve per channel, free WB, saturation | sat 1.07 | 6.3 | 23.2 | 13.0 | 9.9 |
| curve on max(RGB), free WB | P 3.73 | 12.1 | 19.8 | 10.4 | 5.7 |
| **shipped**: max(RGB), WB from the shell, exposure per photo | EV 0.102, P 2.59 | 12.7 (own exposures 11.8) | 22.7 (own 23.1) | 10.9 (own 6.1) | 10.3 (own 7.6) |

The free-WB per-channel curve scores best on these three classes only by fitting the black and the magenta errors
with blue; it also crushed the weak channels of saturated colours (the bike's red to G 7 where his 07 shows 47,
below), which the max(RGB) curve keeps (G 50). The first version of this module (commit 060976e: the per-channel
curve in the view's curve mapping, P 2.52, a shared exposure) scored 14.8 fitted, 25.8 / 13.6 / 11.0 held out.
The fold holding out p09 fits P on 07 and 08 alone and runs to the bound (6.0): two photos with two classes do not
pin P with free exposures; the other folds give 2.52 and 2.41.

### Round 2's refit (the new light, round 1's pipeline unchanged: `look_fit.py fit`)

Before = decision 46's look on round 2's pairs; mean dE of the class medians, through the module (own exposure: each
photo at its fitted exposure).

| fold | params | fitted dE | held-out dE | own exposure |
|---|---|---|---|---|
| all three (shipped) | EV -0.847, WB R +0.107 B -0.165, P 2.21; per-photo -0.24 / -1.08 / -1.22 | 22.0 -> **13.3** | | 10.9 |
| hold p07 | P 2.20 | 17.9 -> 3.0 | 27.5 -> 27.4 | 20.9 |
| hold p08 | P 2.15 | 23.0 -> 16.6 | 19.6 -> **6.8** | 4.9 |
| hold p09 | P 2.28 | 24.4 -> 16.7 | 16.2 -> **7.4** | 4.5 |

Round 1 for comparison: fitted 12.7; held out 22.7 / 10.9 / 10.3; own 23.1 / 6.1 / 7.6. P is now stable across the
folds (2.15 to 2.28; round 1 ran to the bound in one fold), and 08 and 09 held out improve by 4 and 3 dE: the light
was what the curve was making up for. 07 held out stays at 27: its own exposure and lifted darks (below). The white
balance halves (R +0.234 to +0.107, B -0.302 to -0.165): the blue sky now gives the shade its blue.

### Before and after, per class, through Blender (`look_fit.py report`; the module's look at EV, no per-photo exposure)

| view | class | n | photo | AgX - Punchy -0.6 | dE | scene look | dE |
|---|---|---|---|---|---|---|---|
| p07 | white | 1426 | 237, 242, 242 | 212, 216, 222 | 9.5 | 254, 249, 248 | 4.7 |
| p07 | magenta | 167 | 238, 32, 173 | 166, 89, 120 | 51.3 | 217, 89, 130 | 38.9 |
| p07 | black | 432 | 46, 50, 70 | 91, 91, 90 | 22.6 | 75, 69, 60 | 21.7 |
| p08 | white | 1312 | 214, 229, 235 | 152, 166, 180 | 23.1 | 192, 206, 220 | 8.9 |
| p08 | black | 269 | 19, 22, 23 | 36, 44, 47 | 10.7 | 14, 13, 13 | 3.8 |
| p09 | white | 919 | 219, 220, 228 | 180, 189, 199 | 12.1 | 228, 235, 243 | 5.3 |
| p09 | black | 33 | 30, 30, 28 | 71, 70, 68 | 18.6 | 44, 39, 34 | 5.8 |
| | **mean** | | | | **21.1** | | **12.7** |

Round 2 (round 2's light; before = decision 46's look on it):

| view | class | n | photo | AgX - Punchy -0.6 | dE | scene look | dE (round 1) |
|---|---|---|---|---|---|---|---|
| p07 | white | 1426 | 237, 242, 242 | 213, 217, 221 | 8.9 | 236, 239, 246 | 3.8 (4.7) |
| p07 | magenta | 167 | 238, 32, 173 | 167, 91, 123 | 51.2 | 147, 67, 94 | 53.4 (38.9) |
| p07 | black | 432 | 46, 50, 70 | 91, 92, 92 | 22.5 | 39, 38, 36 | 16.4 (21.7) |
| p08 | white | 1312 | 214, 229, 235 | 202, 207, 212 | 7.9 | 222, 229, 235 | 2.8 (8.9) |
| p08 | black | 269 | 19, 22, 23 | 89, 90, 92 | 31.2 | 37, 36, 35 | 7.6 (3.8) |
| p09 | white | 919 | 219, 220, 228 | 205, 208, 212 | 5.0 | 227, 233, 234 | 5.8 (5.3) |
| p09 | black | 33 | 30, 30, 28 | 90, 91, 90 | 27.4 | 38, 37, 34 | 3.6 (5.8) |
| | **mean** | | | | **22.0** | | **13.3 (12.7)** |

The magenta print is darker than round 1 (147, 67, 94): the helmet agent's paint (its albedo, a fluorescent ink?),
not the look. Without it the mean is 6.7 (round 1 8.4).

## Each photo's exposure (round 2)

His phone exposes each shot itself, so a render compared with one of his photos is shown at that photo's exposure:
`scene_look.PHOTO_EV`, used by head_closeups' p07, p08, p09 and cam07 (`scene_look.photo_ev(view)`); the scene and
the animation keep the one look. Read off his white shell's lit side: the white-shell pixels whose Combined_sun is in
the top quartile, the exposure (over EV) at which our median G through the look meets the photo's.

| photo | white px | lit px | photo lit median | PHOTO_EV | at it: lit dE | shade dE | white dE | black dE |
|---|---|---|---|---|---|---|---|---|
| 07 | 1426 | 357 | 244, 246, 244 | -0.045 | 3.3 | 4.3 | 3.7 | 16.6 |
| 08 | 1312 | 328 | 225, 234, 240 | -0.147 | 1.5 | 6.1 | 2.9 | 5.9 |
| 09 | 919 | 230 | 233, 221, 231 | -0.649 | 6.3 | 7.1 | 5.7 | 4.9 |

Round 1's light needed -1.12, -0.80 and -1.38 for the same shell (its sky lit the shade warm).

What still differs: **07's darks**. At its exposure the white matches (3.7) but the black print reads 38, 37, 35
where his photo has 46, 50, 70: lifted and blue. His phone lifted that shot's shadows (local tone mapping; a global
look cannot do it while keeping 08 and 09), and its black also mirrors the deep blue sky. Left as it is. 09's lit
white is pink in his photo (233, 221, 231), neutral in ours.

What the look cannot reach here (not the look's to fix):
- **Magenta print** (helmet agent): 217, 89, 130 against 238, 32, 173. Its albedo (0.288, 0, 0.092 linear) has
  too little blue against red (the photo needs B/R about 0.6, ours 0.32), and its rendered G (0.22 linear, all of it
  grey reflection over a zero-G albedo) shows once the curve keeps channel ratios (the per-channel curve crushed it
  to 44, the photo has 32); possibly a fluorescent ink.
- **Black print in p07**: blue in his photo (46, 50, 70: the deep blue sky in a gloss print), neutral to warm in
  ours: the rig's sky is a cream glow near the sun and its ground is warm.
- **Photo 07's contrast**: from its white shell, photo 07 sits 1.04 stops under EV, yet its darks (black print,
  dark kit) are L* 7 to 16 where ours fall to L* 3 to 4 at that exposure: his phone lifted the shadows of that shot
  (local tone mapping) or our sky fills the shade too little. A global look cannot do both.

## The bike's red (`look_fit.py bike`, photo 07, cam07)

Plain red surfaces of our render (albedo RED 208, 10, 22 in the Diffuse Color pass, 0.955 of it under the clear
coat's Fresnel loss) against his photo's red pixels round the bike (15 px), the same red gate on both (hue within 15
deg of red, saturation over 0.5, value over 0.3); lit = the top quartile by luma Y' (the red channel clips, so
quartiles by value are ill-defined). 13268 photo pixels, 13907 render pixels.

| | median | lit | dE median / lit |
|---|---|---|---|
| his photo 07 | 189, 47, 49 | 245, 94, 105 | |
| AgX - Punchy -0.6 | 205, 59, 47 | 212, 98, 89 | 8.3 / 15.3 |
| per-channel curve (first version) | 247, 7, 5 | 251, 69, 51 | G and B crushed |
| scene look at EV | 248, 50, 46 | 251, 83, 73 | 26.5 / 17.5 |
| scene look at photo 07's exposure (-1.04, its white shell) | 218, 42, 38 | 233, 78, 69 | 16.9 / 14.7 |
| **RED 187, 28, 49** at photo 07's exposure | 199, 51, 59 | 226, 86, 88 | **4.1 / 6.9** |

The albedo solve: each plain red pixel is lin = albedo x E x e + S, E its diffuse light, e the light's colour (white
shell's lin over its albedo in this render: 1, 1.072, 1.163), S a grey reflection (the coat and the specular,
median 0.072); a new albedo relights every pixel and is fitted (median and lit, CIELAB) through the look at photo
07's exposure, then checked through Blender rounded to 8 bits.

Does it move towards the photo's own colour (240, 50, 60)? In its ratios, yes: G/R 0.005 to 0.023 (photo 0.037),
B/R 0.013 to 0.062 (photo 0.052, a little past). In level, R goes down (208 to 187): the photo's 240 is a lit mean,
light included. Not applied in round 1 (kit_canvas.RED paints the same plastic in the kit textures).

### Round 2: one red, his 07's (applied)

`build_bike.RED`, `kit_canvas.RED` and `kit_sidepanel.PLASTIC_RED` are one plastic and stay one value (test_kit.py).
Fitted as in round 1 but with round 2's light and look, photo 07 at its own exposure (-0.045), every plain red pixel
relit through the diffuse passes (`look_fit.py bike`), checked through Blender:

| | median | lit | dE median / lit |
|---|---|---|---|
| his photo 07 (13268 px) | 189, 47, 49 | 245, 94, 105 | |
| RED 208, 10, 22 (13907 px) | 205, 42, 41 | 223, 79, 76 | 10.4 / 10.4 |
| **RED 205, 41, 62** | 203, 52, 60 | 226, 88, 91 | **5.0 / 6.6** |

Honda's studio photos under the studio look (Standard at -0.9, build_bike.STUDIO; the stock bike rendered at half
the photos' 4000 x 2250, `look_fit.py honda`; plain red eroded 2 px, about 71 700 px per view):

| view | Honda's photo median / lit | RED 208, 10, 22 dE | RED 205, 41, 62 dE | Honda's own fit | its dE |
|---|---|---|---|---|---|
| left | 244, 24, 38 / 249, 90, 97 | 15.0 / 3.5 | 29.5 / 10.1 | 230, 1, 3 | 6.6 / 3.8 |
| lf34 | 238, 27, 39 / 246, 88, 95 | 13.4 / 7.2 | 27.1 / 4.7 | 210, 2, 7 | 10.5 / 9.8 |
| right | 244, 24, 38 / 246, 90, 96 | 30.1 / 11.2 | 39.8 / 16.5 | 251, 1, 4 | 12.5 / 9.4 |

One albedo cannot fit both, and the reasons:
- **Our studio set-up veils the red**: in the studio renders 91 to 94 % of the plain red's G is reflection (the clear
  coat and the specular mirroring the studio dome and lamps), G 54 to 57 on its own after the look, where Honda's
  photo median has G 24. No albedo gets below that: Honda's own fit runs G and B to 1 to 7 and still reads G 55 to
  58. In his 07 the same split leaves G 4.9 of reflection: the street mirrors far less than our dome.
- **Honda's red is purer**: decoded to linear, Honda's photo medians have G/R 1.0 to 1.3 % and B/R 2.1 to 2.4 %,
  his 07's 5.6 % and 6.0 % (the albedos: old RED 0.5 % and 1.3 %, his fit 3.6 % and 7.9 %). Honda's product photos
  are graded and lit for a saturated red; his plastics are a used bike's in street light through a phone.

His photos lead for the scene (brief), so RED = 205, 41, 62. Honda's studio views now read crimson-pink against
Honda's red (dE 27 to 40 median). A red for the STOCK livery alone (the shape work against Honda's photos) or a
studio set-up with less reflection would close that; asked in the round's report, not done.

The kit textures were rebuilt from their scripts with the new red (kit_template.py, kit_sidepanel.py, kit_canvas.py;
no hand edits): every changed texel was the old red (exactly) or an anti-aliased blend of it, moved along the same
blend line (`kit_diff`: 0 texels off it). The rebuild also carries panel-edge changes from parts.py since the
textures were last built (commit 298c20a): 114 texels on fender.png, 140 to 488 on the side textures and their
material maps, 1 on side_L_n.png, the same with the old red.

### The kit's printed colours in his 07 (round 2)

The side panel's printed colours (kit_sidepanel.py), ours against his photo 07 at its exposure. Our side panel sits
about 22 px above the photo's in cam07 and the rider's boot hides its LEATT logo, so photo boxes (photo 07 px, picked
on a 6x crop) are compared with our whole class (livery_L texels by albedo, x over 640):

| colour | photo pixels | photo median / lit | ours median / lit | dE | reading | change |
|---|---|---|---|---|---|---|
| red zone (RED 198, 22, 30 as RED_GAP and RED_SPECK worms) | x 730..847, y 555..600, 2974 px | 215, 47, 44 / 223, 62, 67 | 230, 60, 69 / 234, 63, 72 | 9.5 / 3.7 | 4.6 L* lighter and 6 deg pinker; the albedo fit runs blue to 0 and stops at 5.7 dE: what is left is the coat's sky reflection and the panel's light, not the ink | none |
| LEATT logo (LEATT_RED 233, 0, 41) | x 705..747, y 520..537, 89 px | 182, 78, 99 | hidden by the boot in ours | | 89 photo px mix the red, its light edge and the navy flake: not measurable at 1 mm a pixel | none (the official logo file's red) |
| black laminate (BLACK 13, 13, 15) round the number | ours dilated 6 px, 554 px | 11, 13, 19 / 47, 49, 61 | 36, 36, 36 / 51, 53, 61 | 11.0 / 3.4 | lit side right; the median is the gloss film mirroring our bright uniform ground where his street is darker: the environment, not the albedo (0.004 linear already) | none |
| number white (WHITE 247, 247, 245) | x 748..850, y 503..555, 2349 px | 165, 192, 228 | 247, 248, 242 | 41 | his number is in shade (sky blue), ours in sun: the pose and the sun's azimuth, not the print | none |
| plastic rim (PLASTIC_RED) | | | | | 10 art px, the plastic's red | the new RED |

So none is clearly off; only PLASTIC_RED moves (it is the plastic).

## The kit, gloves and boots (round 2; not fixable by the look: kit.py, gloves.py, boots.py are the jersey agent's)

The pose is not fitted, so no pixel pairs: colour-gated regions instead. Render: every pixel of the class; photo:
the pixels in the garment's render mask dilated 20 px (25 in cam07), helmet, goggle and bike taken out; the same
colour gate on both (pink hue 315 to 352, lime 55 to 110, teal 150 to 205, dark value under 0.3 and saturation under
0.6, white saturation under 0.2 and value over 0.6). L*, C*, hue of the median; q the L* of the 10 % and 90 %
luminance quantiles (shade side, lit side). Round 2's light, each photo at its own exposure (PHOTO_EV).

What the material should do: each class pixel is split into its diffuse part D (Diffuse Direct + Indirect times the
Diffuse Color) and the rest G (specular, sheen, coat: Combined - D); one albedo a for the class and a scale k of the
rest, lin' = D a / albedo + k G, are fitted so that the median (CIELAB) and the q10 and q90 L* meet the photo's
(scratch gear2.py). k is what the grey layer should be: 0 none, 1 as now. "rest" = G's share of the pixel's light now.

| view | class (px photo / ours) | his photo | ours | dE | albedo now -> fitted (8-bit) | rest, k | after the fit |
|---|---|---|---|---|---|---|---|
| p08 | jersey pink (7876 / 4974) | 151, 2, 49; L32 C58 h18; q 12-29 | 200, 66, 121; L49 C57 h358; q 36-45 | 26.6 | 180, 31, 111 -> 150, 19, 56 | 25 %, 0 | 154, 18, 53; q 18-22 |
| p09 | jersey pink (5117 / 4085) | 200, 6, 100; L43 C70 h3; q 11-36 | 161, 53, 96; L40 C48 h359; q 26-38 | 22.3 | 180, 30, 109 -> 220, 15, 120 | 26 %, 0 | 198, 11, 100; q 23-25 |
| cam07 | pant pink (1663 / 361) | 186, 23, 113; L42 C66; q 13-40 | 202, 73, 138; L51 C58; q 41-47 | 12.8 | 171, 33, 117 -> 159, 0, 100 | 26 %, 0.20 | 183, 25, 112; q 25-29 |
| cam07 | jersey lime (700 / 420) | 116, 172, 44; L64 h124; q 45-80 | 160, 196, 64; L74 h117; q 58-82 | 12.8 | 178, 217, 43 -> 138, 196, 40 | 8 %, 0.55 | 124, 178, 52 |
| p09 | jersey lime (98 / 530) | 146, 177, 50; L68; q 38-84 | 168, 190, 51; L73; q 63-77 | 8.1 | 204, 233, 48 -> 163, 205, 0 | 5 %, 1.86 | 141, 171, 54 |
| cam07 | pant lime (1404 / 98) | 120, 178, 33; L66; q 39-70 | 133, 185, 58; L70; q 63-78 | 6.8 | 100, 150, 32 -> 86, 129, 24 | 32 %, 0 | 130, 189, 46 |
| cam07 | jersey teal (2295 / 201) | 61, 122, 130; L48 h211; q 30-78 | 131, 190, 175; L73 h176; q 60-86 | 28.2 | 117, 184, 168 -> 84, 147, 161 | 9 %, 0.54 | 82, 133, 136; h202 |
| cam07 | jersey dark (4147 / 4414) | 30, 38, 52; L15 C10 h274 | 24, 23, 24; L8 C1 | 12.3 | 38, 37, 46 -> 10, 45, 82 | 64 %, 0.84 | 26, 35, 49; C10 h272 |
| cam07 | pant dark (6056 / 10373) | 31, 37, 52; L15 C11 h280 | 23, 23, 24; L8 C1 | 12.0 | 38, 37, 43 -> 2, 36, 70 | 68 %, 0.38 | 11, 20, 35 |
| p07 / p08 / p09 | jersey dark | 16, 23, 29 / 39, 30, 39 / 27, 26, 38 | 25, 24, 24 / 26, 26, 28 / 11, 12, 13 | 6.0 / 7.0 / 10.8 | -> 0, 18, 51 / 57, 1, 48 / 18, 0, 77 | 61 to 66 %, 1.3 to 1.9 | |
| cam07 | gloves (807 / 904) | 34, 39, 53; L16 C10 h281 | 19, 19, 19; L6 | 14.3 | 35, 35, 37 -> 35, 48, 80 | 66 %, 1.08 | 38, 42, 57 |
| p09 | gloves (184 / 414) | 31, 41, 50; L16 | 8, 8, 8; L2 | 15.6 | 37, 37, 39 -> 19, 59, 87 | 63 %, 2.18 | 32, 41, 50 |
| cam07 | boots (3876 / 7256) | 180, 186, 184; L75; q 65-84 | 231, 237, 235; L93; q 84-98 | 18.1 | 230, 234, 237 -> 150, 157, 162 | 5 %, 1.26 | 177, 185, 186 |

What each material should do (for the materials round; the numbers above):
- **jersey_print pink** (kit.py: rough 0.58, sheen 0.18): drop the grey layer: sheen 0 and Specular IOR Level near 0
  (k = 0 in both photos; it is a quarter of the pink's light now, and it is what lifts G to 53 to 66 where his has 2
  to 6). Albedo G 31 to about 15 to 19; R and B between the two photos' fits (150, 56 in 08 where the chest is in
  shade; 220, 120 in 09): 08 and 09 disagree by about 1.2 stops, so keep R and B and change G and the gloss first.
  Roughness: not measurable from these medians; keep.
- **pant_print pink** (rough 0.56, sheen 0.16): the grey layer to a fifth (k 0.20: sheen about 0.03, Specular IOR
  Level about 0.1), albedo 171, 33, 117 -> 159, 0, 100.
- **lime** (jersey and pant): darker albedo, R 178 -> 138 (jersey), 100 -> 86 (pant), G 217 -> 196, 150 -> 129; the
  grey layer is only 5 to 8 % of the jersey lime (keep) and 32 % of the pant lime (k 0: sheen off with the pink).
- **jersey teal**: darker and bluer, 117, 184, 168 -> 84, 147, 161 (hue 176 -> 202, his 211); gloss as now (9 %).
- **darks** (jersey, pant): his are navy (C* 10, hue 272 to 280) where ours are neutral: a navy dye, about 10, 45, 82
  (jersey) and 2, 36, 70 (pant) from cam07's large regions (4147 and 6056 px), against 38, 37, 46 and 38, 37, 43 now.
  The grey layer is two thirds of their light: keep it (k 0.4 to 1.9 across views, no clear direction).
- **gloves** (gloves.py glove_fabric: rough 0.7, sheen 0.1): navy too, 35, 35, 37 -> 35, 48, 80 (cam07, 807 px), the
  sheen as now to twice (k 1.08 in cam07, 2.18 in p09's 184 px).
- **boots** (boots.py boot_white: 236, 239, 242, rough 0.38, coat 0.15): L* 93 against his 75. An albedo of about
  150, 157, 162 would match, but his boots in 07 face down and away and the pose is not fitted: check with a photo of
  the boot side in sun before going grey (scuffed off-white is likely, 150 is not white).
- Spread: after the fit the pinks' shade-to-lit spread stays narrower than his (q 18-22 against 12-29): folds and the
  unfitted pose, not the material.

Round 1's readings (decision 54's sky), kept for the record:
- **Jersey and pant prints (pink, lime) are too pale and too lifted**: the pink's G 54 to 77 where his are 2 to 6 is
  a grey layer over the dye, and its shade quantile sits 12 to 30 L* over his. That is the print's own specular
  (rough 0.58, sheen 0.18 in kit.py "jersey_print"; pant_print rough 0.56, sheen 0.16): the coordinator measured
  255/93/211 with it and 255/40/179 with sheen and Specular IOR Level 0 (photo 233/22/123). **Too glossy** is the
  first cause; the pink also reads bluer (hue 357 to 0 against 3 to 18).
- **Teal too light and too green**, lime too light: the albedos, after the gloss.
- **Darks (jersey, pant, gloves)**: his read navy (h 274 to 281, C* 10); ours neutral. Part of it is our cream sky
  in a sheen; the dye may be navy rather than black.
- **Boots**: L* 94 against 75 at photo 07's exposure: the boot white (236, 239, 242, coat 0.15) is brighter than his
  boots read in that shot.

## Checks

- `display()` against Blender (look_apply.py, emission plane, one sample): max 1 level, mean 0.0004 levels over a
  768-swatch chart (greys 0.001 to 30, the red, magenta, white and black as rendered, random colours), daylight at 0,
  scene at +1.5, studio at -0.9.
- In the scripts: head_closeups.py p09 daylight with the look (32 samples) against the 64-sample linear render put
  through `display()`: 0.6 levels mean, white shell 228, 236, 243 against 228, 235, 243, black print the same.
  Rendered again in **Blender 5.2.0** (CPU compositor): one pixel one level off 5.2.3's render, the rest equal; the swatch chart through 5.2.0 within a
  level for daylight, scene and studio.
- Tests (`test_scene_look.py` in rider and bike): the swatch chart, the module's numbers (T(8) = 1, 0.18 at 69 under
  "scene", ratios kept, gains = EV + WB), and each script's look calls (AST: imports scene_look, calls
  scene_look.apply with the kinds in the named functions, no "AgX - Punchy" left there). On main: collection error
  without the module; with the module copied in, rider 3 failed (build_rider, head_closeups, goggle_views do not
  import scene_look), bike 2 failed (build_bike, rake).
- Round 2, in the script: head_closeups.py p09 daylight (day_rig, the sky turned, PHOTO_EV; 32 samples) against the
  64-sample linear render through `display()` at PHOTO_EV: 0.62 levels mean, the sky behind him 104, 136, 173 in
  both. Rendered again in **Blender 5.2.0**: identical to 5.2.3 (0 pixels differ). Both print a driver's Math Domain
  Error on loading the rider blend, as main's script does.
- Round 2's tests, each failing on main: `test_day_rig.py` (collection error without day_rig.py; with it copied in,
  the 3 script tests fail and the module's 6 pass), `test_scene_look.py`'s two exposure tests, `test_kit.py`'s one
  red.

## Commands

```
# pairs (renders with SCENE_LOOK=linear SCENE_LOOK_INDEX=index.json through head_closeups.py, see "Pairs")
python3 scripts/common/look_fit.py pairs pairs_his.npz p07=head_p07.exr p08=head_p08.exr p09=head_p09.exr --index index.json
python3 scripts/common/look_fit.py fit pairs_his.npz --work WORK --out fit.json
python3 scripts/common/look_fit.py report pairs_his.npz --work WORK --out report.json
python3 scripts/common/look_fit.py bike head_cam07.exr index.json 208,10,22 --out bike_red.json    # --ev7: PHOTO_EV["07"]
# Honda's studio views: build_bike.py stock with SCENE_LOOK=linear BIKE_STUDIO_RES=2000,1125, views honda_left etc.
python3 scripts/common/look_fit.py honda left render_honda_left.exr index.json 208,10,22 --out honda_red_left.json
blender -b --factory-startup --python scripts/common/day_rig.py -- e1      # the E1 table
blender -b --factory-startup --python scripts/common/day_rig.py -- turn    # the turned sky's check
python3 scripts/common/look_fit.py sheet p09 head_p09.exr p09.jpg
python3 scripts/common/look_fit.py sheet cam07 head_cam07.exr cam07.jpg --scale 1 --region 215,112,1110,780 --vertical
```
