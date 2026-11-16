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

Round 2b (the coordinator's review of round 2's red at 1:1): the red is fitted on the plastic's diffuse body only,
with his hue (G = B) and Honda's studio views within main's error, and the studio for Honda's views reflects dark as
theirs does ("Round 2b" and "Honda's studio", under "The bike's red").

Materials round 1, phase A (decision 59): the darks' navy cast is his phone, not the dyes: the daylight look now
lifts the darks as his phone does (all three photos) with 07's own blue tint on top; the boots are his scuffed
white; the gloves stay; round 2's sky numbers re-measured on main's refitted cameras; the gear's measurement is a
command (`look_fit.py gear`, `look_fit.py darks`). "The gear, materials round 1", below.

## The look

| step | what | value (round 2; round 1) | source |
|---|---|---|---|
| 1 | gains (white balance, exposure) | log2: EV -0.847, R +0.107, G 0, B -0.165 (round 1: EV 0.102, R +0.234, B -0.302) | WB: the white shell, below; EV and the curve: the fit, below |
| 2 | tone curve on max(R, G, B), the three channels scaled by T(M)/M (hue and channel ratios kept) | T(u) = m u^P / (1 + u^P), P 2.21 (round 1: 2.59), m so that T(8) = 1 | the fit |
| 3 | "daylight" only: the lift of the darks, on the display values d (sRGB-encoded) by the pixel's value | d + o (1 - max d)^2 per channel, o = DARK_LIFT 0.0668 (17 levels at black; a white moves under a level) | `look_fit.py darks`, "The darks" below (decision 59) |
| 4 | view | Standard (the sRGB curve, clipped) | |
| "scene" kind | studio-lit views (build_bike, build_rider, rake, head_closeups' studio) | neutral gains 2^(EV + 1.514) (round 1: EV + 0.832) | 0.18 linear at 69, where decision 46's AgX - Punchy -0.6 put it (look_apply.py, Blender 5.2.3) |
| "studio" kind | Leatt's and Honda's studio comparisons | Standard at the caller's exposure | decisions 44 and 46, unchanged |
| PHOTO_EV | a view of one of his photos (head_closeups p07, p08, p09, cam07) | daylight at EV + 07 -0.045, 08 -0.147, 09 -0.649 | "Each photo's exposure", below (round 2) |
| PHOTO_TINT | the same views: a photo's own tint of its darks, added to o (`scene_look.photo_tint(view)`) | 07: -0.0044, +0.0123, +0.0706 (08, 09: none) | "The darks" below (decision 59) |

Steps 1 and 2 are a compositor node group ("scene_look": math nodes) set on `scene.compositing_node_group`; the
view's curve mapping cannot do step 2: it works per channel, and its film-like mode still sends the smallest channel
through the curve. Renders show it; the viewport shows it with Viewport Shading's Compositor on Camera or Always.

Grey ramps (G channel, 8-bit; Blender 5.2.3 through look_apply.py, equal to `display()` within a level):
- "scene", linear 0.02, 0.045, 0.09, 0.18, 0.36, 0.8, 1.6: **2, 10, 31, 69, 131, 209, 243** (round 1: 1, 6, 26,
  69, 143, 225, 250; decision 46: 4, 19, 41, 69, 103, 146, 179). More contrast than decision 46: his photos crush
  the darks (the coordinator's measures, LOOK1 brief: darks 12 to 29 in his photos against 47 to 88 in ours).
- "daylight", linear 0.062, 0.123, 0.244, 0.486, 0.966, 1.92, 3.82, 7.59: 2, 10, 30, 68, 128, 194, 232, 244 (round
  1: 4, 20, 55, 120, 193, 228, 236, 237; R reaches 255: a render-neutral grey reads warm, as the phone balances the
  rig's blue sky light away). With the lift (decision 59): 19, 25, 43, 77, 132, 195, 232, 244.

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

### Round 2: one red, his 07's (superseded by round 2b)

Round 2 fitted RED 205, 41, 62 to his 07 under round 2's light and look (dE 10.4 / 10.4 to 5.0 / 6.6 under round 2's
gate, hue within 15 deg of red) and rebuilt the kit textures with it. The coordinator's review at 1:1: it read
crimson (B above G in the albedo and on the bike), and Honda's studio views turned pink (dE 27 to 40 median, from 13
to 30). Its photo "lit" (245, 94, 105) held the coat's sky highlights, which the hue gate kept.

### Round 2b: the red on the plastic's diffuse body (applied)

**The gate** (the coordinator's, `look_fit.red_test`): red the largest channel, saturation over 0.5, value over 77,
G and B each under 0.45 R. The coat's pinkish highlights fail it. Applied alike to the photos and our renders.

**His 07, the bike alone.** The coordinator's reading of round 2's sheet (median 183, 51, 45, lit 221, 87, 57: an
orange-red with G at or above B) covers the whole photo panel, and 8522 of its 21378 gated pixels are the orange sign
at the top left (median 180, 73, 48). On the bike (look_fit's region: the bike's red and black parts in cam07,
dilated 15 px; 10405 px) the gate gives **183, 41, 41, lit 238, 74, 80**: G = B at the median, G/B 0.92, 0.91, 1.00,
0.93 by luma quartile. The panel below row 380 (the bike, no sign) gives 190, 43, 42 / 235, 72, 77. So the diffuse hue
of his plastic is a plain red with G about B, not an orange-red. Round 2's red had G/B 0.60 to 0.69 on the bike.

**The render's body** (`look_fit.py bike`): the plain red pixels whose gloss (Glossy Direct + Indirect times Glossy
Color) is under a fifth of the pixel (channel sums, `GLOSS_SHARE`): 9699 of 13914 in cam07, gloss share median 0.13.
A red a reads there as its diffuse light x a x 0.956 (the coat's loss), through the daylight look at photo 07's
exposure (-0.045); "all" puts the coat's reflection back (lin + light x (a - albedo)). Through Blender:

| red | body median / lit | dE body | all of it median / lit | dE all | the coat adds (all - body) |
|---|---|---|---|---|---|
| his photo 07 (bike) | 183, 41, 41 / 238, 74, 80 | | | | |
| 208, 10, 22 (main) | 182, 5, 11 / 202, 7, 16 | 14.0 / 22.7 | 187, 25, 28 / 204, 48, 50 | 8.3 / 11.0 | 5, 20, 17 |
| 205, 41, 62 (round 2) | 179, 26, 39 / 199, 34, 49 | 3.9 / 12.4 | 184, 38, 48 / 202, 59, 66 | 4.3 / 11.5 | 5, 12, 9 |
| 228, 74, 82 (the body's own fit) | 199, 50, 53 / 217, 61, 65 | 5.1 / 6.3 | 203, 57, 60 / 219, 75, 76 | 7.0 / 7.8 | 4, 7, 7 |
| 230, 45, 50 (the grid's pick) | 201, 29, 31 / 218, 36, 38 | 12.3 / 16.0 | 204, 39, 41 / 220, 58, 58 | 9.5 / 7.7 | 3, 10, 10 |
| **230, 46, 49 (round 2b, applied)** | **201, 30, 30 / 218, 37, 37** | **12.6 / 16.4** | 204, 40, 40 / 220, 59, 58 | 9.7 / 7.7 | 3, 10, 10 |

- **The environment's part**: the coat adds about 3, 10, 10 to the medians (the rig's sky and ground mirrored), G and
  B alike: a grey-blue veil, not a blue cast, and it is the environment's (his street of warm stone and pavement
  mirrors less of the sky than our open rig), not the albedo's.
- **The lit quarter's gap is light, not albedo**: our body's lit R is 218 against his 238 while its median is 201
  against his 183 (his shade-to-sun spread 1.30, ours 1.09: his 07 has more sun on the tank and fender). No red with
  his hue closes both; the body's own fit gets 6.3 by lifting G and B to 74 and 82, and Honda's views then go to 22
  to 31.

**One red for both.** A grid of 288 reds (R 205 to 240, G 30 to 70 in steps of 5, B from G - 5 to G + 10; the look in
numpy, `scene_look.display`, within a level of Blender's), kept when his 07 body's median G is within 3 of its B (his
hue) and each Honda view (round 2b's studio, below) is at or under main's own error there (main's red in main's
studio: left 15.1 / 7.2, lf34 13.8 / 4.0, right 30.1 / 11.9). No red keeps lf34's lit quarter under 4.0 in the round
2b studio (Honda's own fit gets 8.2 there; see below), so it is ranked on the rest: the medians in all three views
and the lit quarters of left and right. **230, 45, 50** comes first on Honda (left 13.9 / 4.5, lf34 13.3 / 7.3, right
12.9 / 3.4) with his 07 body at 12.2 / 15.9; 230, 50, 50 is 0.3 better in his 07 and worse in every Honda view;
220, 40, 45 (10.5 / 16.5 in his 07) misses lf34's median (14.8). Of the 43 reds that pass, none gets his 07's body
under about 12 / 16 (median / lit): Honda's purer red and his photo's wider shade-to-sun spread set that floor.

Applied one level off it, **230, 46, 49**: the side panels' artwork holds 230, 45, 50 itself in lone anti-aliased
texels (11 a side, already there in round 2's textures), which test_kit's slit check then reads as plain plastic
showing through the print (5 a side); no texel in the panels' box holds 230, 46, 49. Checked through Blender on the
final renders (round 2b's code and red, `look_fit.py honda`, dE median / lit):

| view | Honda's photo median / lit | main (main's red and studio) | round 2 (205, 41, 62, main's studio) | **round 2b (230, 46, 49, round 2b's studio)** | main's red in round 2b's studio | Honda's own fit, main's studio | Honda's own fit, round 2b's studio |
|---|---|---|---|---|---|---|---|
| left | 243, 24, 37 / 249, 79, 87 | 15.1 / 7.2 | 28.4 / 8.5 | **13.7 / 4.8** | 11.6 / 2.7 | 229, 1, 0: 6.0 / 6.0 | 232, 0, 21: 4.4 / 5.1 |
| lf34 | 238, 25, 39 / 246, 79, 87 | 13.8 / 4.0 | 27.7 / 6.2 | **13.1 / 7.7** | 12.0 / 10.9 | 228, 0, 10: 7.5 / 7.2 | 241, 41, 47: 9.5 / 8.2 |
| right | 243, 24, 38 / 245, 87, 92 | 30.1 / 11.9 | 39.3 / 17.2 | **12.8 / 3.6** | 10.7 / 6.7 | 255, 1, 5: 11.3 / 9.4 | 230, 25, 30: 5.8 / 7.6 |

Five of the six numbers are under main's; lf34's lit quarter is not (7.7 against 4.0; see "Honda's studio", below).

Honda's red in their photos is purer and leans to B (G 24, B 37 at the median): with his hue (G = B) no red gets
Honda's medians under about 12. The two photos still disagree on purity (decoded G/R 1 % in Honda's, 2 % and more in
his 07); the red sits between them, with his hue.

The kit textures were rebuilt from their scripts with the new red (kit_template.py, kit_sidepanel.py, kit_canvas.py;
no hand edits; `kit_diff`: every changed texel was round 2's red exactly or an anti-aliased blend of it, moved along
the same blend line).

### Honda's studio (round 2b, `build_bike.studio`, the honda_* views)

**What their photos show.** For each plain red pixel of a honda_* render, the camera ray's mirror direction (the
Normal and Position passes; the camera's centre by a DLT on the Position pass, rms 0.000 px), binned by its
elevation; Honda's photo decoded to linear and box-averaged to our pixels; linear x 1000 at the studio exposure
(-0.9). Left view, 87 702 px (scratch honda_env.py):

| reflected ray's elevation (deg) | px | Honda's photo R, G, B | main's studio: the coat's gloss G | round 2b: gloss G |
|---|---|---|---|---|
| -90 to -30 | 2374 | 853, 8, 17 | 46 | 43 |
| -30 to -10 | 5238 | 853, 9, 17 | 41 | 37 |
| -10 to 0 | 36533 | 901, 9, 18 | 26 | 19 |
| 0 to 10 | 3343 | 861, 13, 22 | 33 | 15 |
| 10 to 20 | 5403 | 859, 10, 20 | 48 | 16 |
| 20 to 30 | 4840 | 913, 9, 20 | 122 | 26 |
| 30 to 45 | 10256 | 920, 9, 22 | 137 | 29 |
| 45 to 60 | 5379 | 909, 10, 22 | 108 | 41 |
| 60 to 90 | 14336 | 913, 45, 60 | 95 | 81 |

Honda's G is the albedo's and the coat's together: 8 to 13 wherever their coat looks below 60 deg, 45 overhead. Their
studio mirrors dark flags round the bike and one soft light above it. Ours mirrored a grey world (0.9 at 0.7) all
round and the key lamp from 20 to 60 deg. The light groups (two renders of the left view, A with every lamp seen in
reflections, B with none; per lamp its diffuse part B and its reflection A - B; the red's medians at strength 1,
linear x 1000): key diffuse R 1247, reflection G 11; top 389 / 2; rim 270 / 1; front 198 / 1; fill 18 / 0; the world's
reflection G 80, the veil.

**The change** (`build_bike.STUDIO`, `STUDIO_LAMPS`, `studio()`, `turn_lamps()`):
- The world is hidden from reflected rays in the honda_* views (`world.cycles_visibility.glossy`); a sphere of its
  grey seen by reflected rays only (`refl_dome`, emission 0.9 x STUDIO[3]) takes its place: the dark flags. STUDIO[3]
  = 0.2 from a scan on the left view's light groups (world 0.6 to 0.8, lamps 0.4 to 0.6, the dome 0.15 to 0.25;
  scratch studio_scan.py), checked in the real render: the frame's median G 139 against Honda's 163, the black
  plastics' 44 against 28 (the table below).
- Of the lamps only the top one is seen in reflections: Honda's overhead light.
- The lamps turn with the camera about the bike's vertical axis (`turn_lamps`): Honda's left and right photos light
  the bike alike (the plain red's linear R 896 and 899), where our fixed lamps lit the right at 548 against the left's
  802; now 769 and 761.
- Kept: the world's light 0.7, the lamps 0.5, the exposure -0.9 (STUDIO's first three). Every other view keeps the
  world in reflections and every lamp as before.

The bike's other materials, sRGB G quartiles (25, 50, 75 %) against Honda's photo:

| view, class | Honda's photo | main's studio | round 2b |
|---|---|---|---|
| left, frame (spars and castings) | 87, 163, 184 | 161, 179, 190 | 99, 139, 152 |
| left, swingarm | 176, 180, 187 | 166, 184, 197 | 144, 172, 189 |
| left, engine | 55, 104, 135 | 114, 140, 151 | 82, 113, 134 |
| left, black plastics | 22, 28, 43 | 52, 58, 62 | 40, 44, 47 |
| left, the whole bike | 28, 53, 105 | 50, 60, 115 | 39, 60, 94 |
| right, frame | 64, 163, 184 | 154, 176, 186 | 89, 135, 152 |
| right, black plastics | 22, 33, 49 | 45, 48, 50 | 40, 44, 45 |
| lf34, frame | 25, 93, 154 | 137, 168, 183 | 76, 141, 156 |
| lf34, black plastics | 19, 26, 42 | 50, 60, 63 | 40, 45, 47 |

Closer in every class but the frame's and swingarm's top quartile (their highlights).

**Tried and left out**: the floor (the shadow catcher) hidden from reflections too: the red's G 4 lower, but the
frame fell to a median 68 and the swingarm to 67 (they mirror the floor). The light-group composite predicted half the
coat's reflection the real render had (G 13 against 26 per mille with main's red): the lamps' groups in B also hold
the lamp-lit floor and bike seen in reflections. Check a studio in a real render.

**lf34's lit quarter** stays over main's (7.7 against 4.0). Honda's lf34 photo has one strong light in the coat: in
the bike's frame (front +X) the reflected rays at azimuth -60 to -30 deg and 20 to 30 deg up read G 559 per mille
(2071 px), -90 to -60 deg 105 (5888 px). Their right photo reflects that same direction too (507 px) and reads 8, so
it is no fixed studio light; turning with the camera it sits 95 deg right of the camera, where their left photo
reads 6 to 15 (scratch env_world.py). Tried with 230, 46, 49: each lamp seen in reflections in turn (the light-group
composite, which underestimates: key 13.6 / 4.4, rim 13.9 / 3.8 with the median over main's, fill 13.2 / 6.6, front
13.3 / 7.0; the key sits 18 deg off the camera and 38 up, nowhere near the highlight, and lights the left's 20 to 60
deg where Honda's is dark), and in a real render a card seen by reflections only at the highlight's direction
(1.8 x 0.6 m, 3.5 m out, 150 W): lf34 13.2 / 4.9 (it matches the highlight, 486
against 559, but also lights 30 to 45 deg up, 117 against 10), left 13.7 / 4.7 to 14.0 / 5.6 with 53 to 224 put on
about 4300 px where Honda's left reads 6 to 15. Honda lit that shot for itself; a studio that turns with the camera
cannot copy it without contradicting their left photo, and the rest of the lit quarter's gap is R (ours clips at 255,
theirs 246), the diffuse light, not the reflections. Main's grey world reached 4.0 by chance: main's red there is
12.0 / 10.9 in the round 2b studio, Honda's own fit 9.5 / 8.2. Left out; lf34's lit quarter is the one number over
main's.

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

## The gear, materials round 1 (decision 59, phase A)

Renders: main 039e0a0's rider (helmet and kit npz rebuilt from main, body, pose, gloves as round 1), his views p07,
p08, p09 and cam07 linear at 64 samples on main's refitted cameras (helmet phase 2, his-photo-cameras.json rms 2.2,
5.8, 8.0 px). Measured with `look_fit.py gear` (the colour gates and regions of round 2, the render now gated
without the photo's tint) and `look_fit.py darks`.

### The darks

Is the navy his phone or the light? Neutral blacks first: the helmet's black print (gloss over black, neutral in
Leatt's studio) and the tyres' rubber, against the white shell's shade (the light itself).

| photo | black print (pairs) | tyres | white shell, shade (the light) | reading |
|---|---|---|---|---|
| 07 | 35, 37, 56; linear B/G 2.1, in every reflection bin, also where it mirrors the warm street (43, 56, 72) | 27, 31, 39 (cam07, 41576 px); B/G 1.5 | 212, 224, 238; B/G 1.12; the cobbles in the bike's shadow 1.33 | bluer than its own light: **his phone** |
| 08 | 40, 43, 48; B/G 1.16 | neutral (his 08, the wheels' rings) | 193, 212, 220; B/G 1.10 | **the light** |
| 09 | no pairs at its camera's rms | | 185, 193, 205; B/G 1.17 | helmet blacks and gloves B - R about +7 to +20, as its shade: **the light** |

Leatt's studio shows all of them neutral (the helmet's black print; the glove black 34, 34, 35 and 39, 39, 40 in
the my27 shots; the my26 shot is cool all over, its white print 222, 227, 236 too). So no dye is navy.

The second finding is bigger: in all three photos the **matte darks read 10 to 20 levels over ours** (jersey, pant,
gloves, tyres: his 25 to 37, ours 5 to 22) while his white shell's lit and shade sides match ours. The same blacks
read darker in Leatt's studio photos than ours under Standard (the kit's black: flat 21, ours 45, kit.md round 3;
the glove below): so not the albedos. It is the phone's toe: a lift of the darks. And the rig's fill is not it: a
darker ground (DAY_RIG ground 0.2 and 0.1, p07 p08 p09 re-rendered) takes the black print to 10 to 15 (his 35 to
40) and 07's shade to dE 15.7 and 27.1 (7.6 now); it does make 08's and 09's shade bluer and closer (8.0 to 3.7,
11.4 to 2.2 at the lit side's exposure), a lead for the rig, not a fix for the darks.

The fix, in the look (`scene_look.DARK_LIFT`, `PHOTO_TINT`): the display values lifted by the pixel's value,
d + o (1 - max d)^2 per channel (max: a saturated colour's weak channels and the whites are left alone), one
neutral o for all his photos and 07's tint on top, fitted (`look_fit.py darks`, least squares on the CIELAB
medians) on the neutral blacks outside the gear: the black print in 07 and 08 (pairs) and the tyres in cam07. The
gear's darks are held out. Fit: lift 0.0668 (17.0 levels), 07's tint -0.0044, +0.0123, +0.0706.

| view | class | his | main (no lift) | dE | this round | dE |
|---|---|---|---|---|---|---|
| p07 | black print (fitted) | 35, 37, 56 | 34, 33, 31 | 15.1 | 46, 48, 57 | 8.7 |
| p08 | black print (fitted) | 40, 43, 48 | 31, 30, 28 | 8.2 | 44, 43, 41 | 5.2 |
| cam07 | tyres (fitted) | 27, 31, 39 | 5, 5, 5 | 11.9 | 20, 24, 39 | 6.1 |
| p07 | jersey dark | 22, 31, 38 | 22, 21, 21 | 7.9 | 35, 38, 50 | 6.2 |
| p08 | jersey dark | 31, 26, 35 | 20, 20, 21 | 7.1 | 34, 34, 36 | 6.5 |
| p09 | jersey dark | 25, 25, 34 | 11, 12, 12 | 8.7 | 27, 27, 28 | 6.1 |
| p09 | gloves | 30, 39, 50 | 7, 8, 8 | 15.5 | 23, 24, 24 | 10.7 |
| cam07 | jersey dark | 28, 37, 49 | 16, 16, 16 | 13.3 | 29, 33, 47 | 2.7 |
| cam07 | pant dark | 29, 35, 49 | 16, 16, 19 | 12.4 | 30, 33, 49 | 1.6 |
| cam07 | gloves | 32, 37, 50 | 14, 14, 14 | 14.2 | 28, 32, 45 | 2.3 |
| | **mean** | | fitted 11.7, held out 11.3 | | fitted 6.7, **held out 5.2** | |

07's tint fitted on the black print alone (0.0027, 0.0205, 0.1309, the first try) matched the print (dE 0.0) and
made the matte darks navy (cam07 tyres 5, 10, 37: dE 15.2; held out 13.8): the print is bluer than the matte darks
in his 07 (linear B/G 2.1 against 1.5 to 1.7). Fitting the tint on the print's colour alone and the lift on the
lightness: held out 11.4. The joint fit above is the one shipped.

What else moves (numpy, at each photo's exposure, 07 with its tint): the look's pixel pairs, white, magenta and black
per photo, mean dE 13.7 to 12.0 (the whites within 0.1; 07's magenta 42.7 to 41.9); the sky 9.8 to 10.0 (08) and
4.3 to 4.9 (09); the bike's red on his 07 (`look_fit.py bike`, cam07, the plastic's body): 247, 50, 53 at both,
dE 23.9 / 18.4 unchanged; a mid grey (display 128) gains 4 levels, a dark red's weak channels (the red at a quarter
of its light) 8. The "scene" kind (the studio-lit views) keeps decision 54's curve: whether it takes the lift too
is the coordinator's call (it changes every studio-lit render). head_closeups' day_sun does not pass 07's tint yet
(`scene_look.apply(..., tint=scene_look.photo_tint(name))`, one argument in a view script): the lift is in every
daylight render already; the checkpoints take the tint through look_fit.

What remains in the darks: 09's shade light is bluer than our rig's (his white shade B/G 1.17, ours 1.03), so 09's
gloves read 23, 24, 24 against 30, 39, 50 (dE 10.7): the rig's sky and ground (the darker ground lead above).

### Gloves (gloves.py glove_fabric: rough 0.7, sheen 0.1; texture blacks 30, 30, 33)

- Leatt's studio, the back of the hand against its own white LEATT print (each its body, under the 90th luminance
  percentile; `gloves.py check` back_R under Standard against the my26 back-hand shot): Leatt dark 31, 38, 48, white
  222, 227, 236, dark / white 0.025 (linear luminance); ours 62, 62, 63 and 240, 240, 239, 0.055. Ours is twice as
  light against its white: the same gap as the kit's black against Leatt's flats (21 against 45, kept in round 3):
  Leatt's black point, not the glove (his photos need the black lighter still). The my27 shots read the black
  neutral (34, 34, 35 and 39, 39, 40 against a 236 grey sweep), ours neutral: no navy dye.
- His photos, this round's look: cam07 32, 37, 50 against ours 28, 32, 45 (dE 2.3, main 14.2); p09 30, 39, 50
  against 23, 24, 24 (10.7, main 15.5: 09's shade light, above).
- Sheen and roughness: the body's numbers cannot tell the grey layer's scale from the albedo (`gear_fit`: a test
  class made with k 0.6 fits as closely at k 2.3 with a third of the albedo); Leatt's shots show no sheen
  highlight on the back (the weave's print spreads the dark, q90 / q50 2.2 against our 1.2, a pattern, not gloss).
- So the gloves stay as they are: their dark reads right in his 07 at this round's look, neutral as in Leatt's
  studio, and its studio gap is Leatt's processing, as the kit's.

### The boots' white (boots.py WHITE and boot_white)

Every photo of his that sees the boots, the boot's white against the helmet's white shell in the same photo (white
pixels, saturation under 0.25 and value over 0.45, in boxes round each; the lit side: the top luminance quartile,
glints over the 98th percentile out; `look_fit.py boot_white`, its BOOT_BOXES):

| photo | boot lit | helmet lit | boot / helmet (linear) | what the boot faces |
|---|---|---|---|---|
| 05 (11-10, seated) | 173, 191, 203 | 202, 220, 238 | 0.72 | its sides upright, the helmet's top up |
| 06 (from below) | 168, 168, 156 | 218, 217, 243 | 0.55 | mostly its underside; cream, dusty |
| 08 (from below) | 221, 231, 232 | 228, 238, 243 | **0.93** (R 0.932, G 0.935, B 0.900) | both in sun |
| 09 (from below) | 168, 162, 155 | 235, 238, 244 | 0.43 | its underside; cream, dusty |
| 07 (cam07) | 176, 184, 181 (shade side) | | | the sun behind the bike |

Only 08 sees both lit alike: the boot is 0.93 of the shell, a little warmer. On helmet_art.WHITE (226, 229, 235)
that is **219, 222, 224** (L* 89): a scuffed off-white, as expected, not a grey. Main's 236, 239, 242 was 1.10 of the
shell (the boot whiter than the helmet, where his are never). Leatt's studio (boot 01 to 05: a clean neutral white
on a 236 grey sweep; its exposure is the studio's, so it fixes the hue, not the level) agrees on neutral. Applied to
WHITE (the shell's paint, textures rebuilt by boots.py) and boot_white. The cam07 numbers: see the checkpoint
README (decision 59).

### Round 2's sky numbers on main's refitted cameras

`remeasure` (scratch): the white shell's pixels eroded by ERODE, lit and shade quartiles of Combined_sun, at
round 2's PHOTO_EV and at a refit by the same rule (our median G on the lit side meets his).

| photo | white / lit px | his lit | ev refit (PHOTO_EV) | lit dE | shade dE | white dE | black dE | sky dE |
|---|---|---|---|---|---|---|---|---|
| 07 | 1346 / 337 | 242, 244, 245 | -0.365 (-0.045) | 2.0 (refit 1.7) | 6.1 (7.6) | 3.0 (3.4) | 15.1 (16.2) | |
| 08 | 1912 / 478 | 229, 237, 242 | -0.150 (-0.147) | 1.4 | 8.0 | 5.0 | 8.2 | 9.8 |
| 09 | 822 / 206 | 224, 221, 232 | -0.593 (-0.649) | 3.8 (3.6) | 10.7 (11.4) | 8.1 (7.3) | | 4.3 (5.5) |

Round 2 on the old cameras: lit 3.3, 1.5, 6.3; shade 4.3, 6.1, 7.1; black 16.6, 5.9, 4.9 (09's black has no pairs
now). Mean at PHOTO_EV: lit 2.4, shade 8.3. PHOTO_EV stays: 08 and 09 refit within 0.06 stops, and 07's lit
quartile sits on the curve's shoulder (242 to 245), where a third of a stop moves G by 2 levels: the refit buys 0.3
dE on the lit side and costs 1.5 in the shade. The shade's error is the rig's blue (above), not the exposure.
(Before the lift; the lift moves the whites by under a level.)

### Commands (decision 59)

```
python3 scripts/common/look_fit.py darks darks.json p07=head_p07.exr p08=head_p08.exr p09=head_p09.exr cam07=head_cam07.exr --index index.json
python3 scripts/common/look_fit.py gear gear.json p07=head_p07.exr p08=head_p08.exr p09=head_p09.exr cam07=head_cam07.exr --index index.json [--no-tint]
python3 scripts/common/look_fit.py boot_white boot_white.json
```

## The gear, materials round 1, phase B (decision 61)

Renders: main ea66687's rider (helmet, gloves, boots, body and pose as phase A), the kit built from main's kit.py
("main") and from this round's ("phase B"), his views p07, p08, p09 and cam07 linear at 64 samples on the rig below,
through the look at PHOTO_EV with 07's tint; Leatt's views: build_rider's studio (rest pose, front and back),
linear, Standard. Every number below is measured on the renders (no relighting), on the same pixels for both.

### 07's tint in head_closeups

head_closeups.day_sun passes `tint=scene_look.photo_tint(name)`: p07 and cam07 take 07's tint, the other views
None. p07 (main's rider, main's rig): the black print 47, 46, 44 -> 46, 48, 57 (his 35, 37, 56; dE 15.3 -> 8.7),
the jersey's dark 37, 36, 36 -> 36, 39, 51 (his 32, 47, 68; 16.5 -> 8.1), the white shell unchanged (3.0).
head_closeups' own render of p07 (Blender's compositor, phase B's rider) reads the black print 44, 47, 60.
goggle_views has no per-photo exposure or tint (its look is "daylight" at 0 for every view and its cameras name no
photo): left to the goggle agent. The "scene" kind takes no lift: it renders our models under studio light, not a
phone photo (the coordinator); the animation's look is decided against his clips.

### The shade light

His white shell's shade is bluer than ours in all three photos (linear B/G 1.13, 1.10, 1.14 against 1.03, 1.03,
0.98) while the lit sides match; in the rig the shade is 78 to 87 % the ground's light (the sky 13 to 22 %). A gain
on the sky's colour fitted on 09's shade put the lit sides at 9 to 10 dE (1.4 to 3.8) and the sky behind him 10 to
16 dE further off. So day_rig.RIG's ground takes 09's shade's hue at GROUND_07's luminance (0.41, 0.40, 0.36 ->
0.379, 0.398, 0.461; not darker) and the sun 07's and 08's lit sides' hue at luminance 1 (1.004, 1.007, 0.924). Held
out: 09's gloves and the jersey's black. The darker ground stays out (it takes the black print too dark and 07's
shade worse). Main's rider, before -> after (dE; the shade's linear B/G his / before / after):

| photo | lit | shade | B/G shade | white | black print | sky | jersey dark | the rest |
|---|---|---|---|---|---|---|---|---|
| 07 | 2.0 -> 2.4 | 6.4 -> 2.3 | 1.13 / 1.03 / 1.17 | 3.0 -> 2.2 | 8.7 -> 7.0 | | 6.2 -> 7.3 | magenta 32.1 -> 31.7, lime 33.0 -> 31.7 |
| 08 | 1.4 -> 0.8 | 8.2 -> 5.7 | 1.10 / 1.03 / 1.17 | 5.0 -> 4.7 | 5.2 -> 2.9 | 10.0 -> 10.0 | 6.5 -> 6.0 | magenta 31.5 -> 36.5 |
| 09 | 3.8 -> 4.2 | 11.1 -> 6.2 | 1.14 / 0.98 / 1.13 | 8.0 -> 8.9 | | 4.9 -> 4.9 | 6.1 -> 5.2 (held out) | gloves 10.7 -> 9.9 (held out), magenta 10.6 -> 15.4, lime 8.0 -> 8.9, teal 3.8 -> 4.9 |
| cam07 | | | | | | | 2.7 -> 3.0 | pant dark 2.0 -> 2.2, gloves 2.3 -> 2.2, tyre 6.1 -> 6.3, boot 12.3 -> 13.9, pant magenta 13.6 -> 14.9, lime 16.2 -> 15.3 and 28.9 -> 29.1, teal 25.7 -> 23.2 |

08 holds or improves everywhere but its pink (the inks', below). 07's lit side goes 0.4 over (2.0 -> 2.4) and its
jersey dark 1.1 over (6.2 -> 7.3); its shade, white and black print improve. The pinks read bluer under the bluer
shade (08 31.5 -> 36.5, 09 10.6 -> 15.4): the inks are fitted on this rig.

### The kit's inks (phase B)

A print pixel is the ink's albedo under a grey layer (sheen, specular). Three renders per view of main's rider
(v0: sheen 0 and Specular IOR Level 0; vS: the sheen alone; v1: main's) make each pixel v0 m + ks (vS - v0) +
kp (v1 - vS): m the ink's albedo factor (R, G, B), ks and kp scales of main's sheen and specular. Rows: Leatt's
front flat's inks under Standard (each ink's core against the white core, compared at the flat's luminance: a
ratio, so the studio's exposure is free) and his photos (each class's diffuse body: median CIELAB, q10 and q90
L*). Each ink's factors fitted on its own rows at each (ks, kp) of a grid; the criterion the sum of the classes'
mean dE.

- The grey layer: the criterion's minimum is flat along kp; the smallest change in it is **sheen 0, Specular IOR
  Level 0.25** (ks 0, kp 0.5) on jersey_print, jersey_mesh, jersey_print_hd, jersey_print_hd_mesh and pant_print.
  Main's veil: the magenta's green 0.048 of the white under Standard (the flat's 0.004), 54 to 74 of 255 in his
  photos (his 1 to 21).
- The black under Standard, layer by layer (its ratio to the white core; jersey and pant, front and back): the grey
  layer off 0.008 to 0.010 (the flat 0.0098), the sheen alone 0.015 to 0.018, main's 0.043 to 0.049. Main's black
  under Standard was our specular and sheen mirroring the studio's even white world, not Leatt's black point (phase
  A's reading above; kit.md and gloves.md corrected): a flat-lay photo is lit so the cloth's reflection misses the
  camera.
- The inks' factors (kit.INK_FACTORS, linear): **black x 2.76** (his darks, with the specular that lifted them
  halved), **magenta (1.03, 0.02, 0.86)** (its green out, its blue down: his pinks' green is 1 to 21, redder than
  ours). The lime and the teal stay: his 07 and 09 put their lightness a stop apart (07's a stop darker than ours,
  09's and the flat's as ours) and their fitted change was a few levels.
- The palette (kit.ink_palette) lays the factors on the textures as the fit laid them on the classes: a texel of a
  chromatic ink's class (ink_class softened over 0.1 either side of each bound: kit.ink_weight) takes the ink's
  factors as a product, a texel of the black's class the black's lift (its fitted colour less its own) as a sum.
  The inks land exactly; the black's blends with the white within 6.4 of 255; colours of no class stay (the
  sleeves' grey-teal bands, light pinks); a 1-level step moves no colour more than 5.2 levels. Dropped: barycentric
  palettes among the inks (the back yoke kept green 25 against the front's 6; the teal, 177 deg from the magenta
  round the grey axis, made a near-singular wedge: light pinks lost their green, 1-level steps jumped 100 levels).
  The pant texture's texels under the I.K.S panels now take it too (painted after it, they stayed at 22 beside the
  print's 42, a dark rim where the print's faces filter them); the panels themselves are pant_iks (22, 22, 24,
  leather and ripstop, not a print), unchanged.
  Damien's additions keep their own colours; their outline ink takes the black's factor (INK_DARK 59, 44, 75: 1.35
  times the ground's luminance, as in PHOTO 06).
- The textures, on the charts: jersey black 23, 21, 29 -> 42, 41, 48; pant black 22, 22, 25 -> 42, 42, 47; jersey
  magenta 213, 37, 132 -> 215, 1, 122; pant magenta 188, 41, 130 -> 188, 2, 121; the front yoke 226, 14, 132 ->
  229, 0, 123, its back 231, 25, 140 -> 234, 1, 131; the lime and the teal unchanged.

Leatt's flats under Standard (each ink's ratio to the white core; dE, at the flat's luminance in brackets):

| view | ink | flat | main | dE | phase B | dE |
|---|---|---|---|---|---|---|
| front, jersey | magenta | 0.933, 0.004, 0.274 | 0.868, 0.048, 0.296 | 10.7 (12.5) | 0.891, 0.018, 0.244 | 6.3 (6.2) |
| back, jersey | magenta | | 0.923, 0.045, 0.309 | 8.5 (11.0) | 0.950, 0.017, 0.256 | 5.2 (5.9) |
| front, jersey | lime | 0.525, 0.990, 0.019 | 0.340, 0.570, 0.037 | 30.0 (10.3) | 0.333, 0.571, 0.023 | 26.9 (5.6) |
| front, pant | lime | | 0.619, 1.060, 0.073 | 8.7 (10.6) | 0.609, 1.064, 0.048 | 4.8 (6.2) |
| front, jersey | black | 0.009, 0.010, 0.010 | 0.041, 0.042, 0.046 | 15.7 | 0.035, 0.036, 0.043 | 13.9 |
| front, pant | black | | 0.046, 0.046, 0.048 | 16.9 | 0.041, 0.041, 0.046 | 15.3 |
| back, jersey | black | | 0.048, 0.048, 0.050 | 17.3 | 0.040, 0.040, 0.046 | 15.2 |
| back, pant | black | | 0.045, 0.044, 0.047 | 16.4 | 0.039, 0.038, 0.045 | 14.8 |

His photos (the diffuse body's median; dE of the CIELAB medians):

| view | class | his | main | dE | phase B | dE |
|---|---|---|---|---|---|---|
| p09 | jersey pink | 191, 5, 91 | 189, 54, 120 | 15.4 | 191, 34, 109 | 8.9 |
| cam07 | pant pink | 178, 21, 114 | 189, 74, 148 | 14.9 | 189, 44, 133 | 6.6 |
| p08 | jersey pink | 147, 1, 46 | 217, 62, 140 | 36.5 | 217, 39, 126 | 33.9 |
| p07 | jersey pink | 245, 68, 169 | 166, 66, 119 | 31.7 | 165, 38, 106 | 27.9 |
| p07 | jersey dark | 22, 31, 38 | 35, 39, 53 | 7.3 | 30, 34, 49 | 7.1 |
| p08 | jersey dark | 31, 26, 35 | 35, 35, 39 | 6.0 | 31, 32, 36 | 4.6 |
| p09 | jersey dark | 25, 25, 34 | 27, 28, 30 | 5.2 | 24, 25, 28 | 4.6 |
| cam07 | jersey dark | 28, 37, 49 | 30, 34, 49 | 3.0 | 26, 30, 46 | 4.6 |
| cam07 | pant dark | 29, 35, 49 | 28, 33, 50 | 2.2 | 26, 30, 47 | 3.3 |
| p09 | jersey teal | 56, 92, 97 | 69, 99, 109 | 4.9 | 62, 94, 103 | 3.3 |
| cam07 | jersey teal | 57, 113, 114 | 76, 159, 135 | 23.2 | 64, 152, 127 | 22.9 |
| p07 | jersey lime | 111, 168, 59 | 169, 234, 70 | 31.7 | 165, 234, 51 | 35.9 |
| p09 | jersey lime | 145, 174, 47 | 135, 184, 48 | 8.9 | 134, 183, 32 | 11.4 |
| cam07 | jersey lime | 114, 168, 41 | 155, 206, 63 | 15.3 | 152, 205, 44 | 18.4 |
| cam07 | pant lime | 117, 169, 35 | 204, 249, 113 | 29.1 | 197, 248, 91 | 29.7 |

- Rule 1 (one material for both references): on Leatt's flats every ink comes closer (magenta 10.7 and 8.5 -> 6.3
  and 5.2, lime 30.0 and 8.7 -> 26.9 and 4.8, the black's ratio 0.041 to 0.048 -> 0.035 to 0.041): within round 3's
  error. The black x 2.76 is his photos'; under Standard the halved specular more than pays for it.
- What does not fit: 08's pink (his q10 to q90 L* 11 to 20, ours 30 to 36): his exposure and light there, not the
  ink (an albedo that dark breaks 09's pink and the flat). The lime loses the blue the grey layer's sky gave it (51
  against his 59 in 07, 32 against 47 in 09): 0.6 to 4.2 dE worse; its lightness is the 07 and 09 disagreement.
  cam07's darks 3.0 -> 4.6 and 2.2 -> 3.3 (3 to 4 levels under his) while 08's and 09's come closer.
- Blender 5.2.0: p09 rendered from phase B's saved blend is identical to 5.2.3's through the look (every pixel, the
  kit's and the frame's).

### Commands (decision 61)

```
python3 scripts/rider/kit.py body.npz kit.npz        # the kit and its textures (textures/rider), bit-identical run to run
python3 -m pytest scripts/rider/test_kit_rider.py -k "phase_bs or rebuild or back_yoke"
python3 scripts/common/look_fit.py gear gear.json p07=head_p07.exr p08=head_p08.exr p09=head_p09.exr cam07=head_cam07.exr --index index.json
```

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
- Round 2b's tests, each failing on main and on round 2's scripts (2b13352): bike `test_scene_look.py`'s studio
  reflects dark (the dome at STUDIO[3] at most a third of the world's light, only the top lamp seen), the world shown
  to reflections through the dome in Honda's views only, the lamps turning with Honda's camera, and the red gate
  leaving out the coat's highlights; `test_kit.py`'s red (230, 46, 49, G within 5 of B, no texture holding 208, 10,
  22 or 205, 41, 62); rider `test_day_rig.py`'s three on the view lines: cam07 takes p07's sun
  (head_closeups.DAY_SUN), cam07 turns the sky to his sun's height with his photos' views (SUN_HEIGHT_VIEWS), and
  goggle_views' photo views get the sun's height through day_rig.
- Round 2b's red through Blender on the final renders: his 07 (`look_fit.py bike`, cam07 relit) and Honda's three
  views (`look_fit.py honda` on renders of round 2b's code and red), the tables above. Kit textures rebuilt from their
  scripts with 230, 46, 49: every texel that changed from round 2's was round 2's red exactly or on its blend line
  (642 and 640 blend texels on the side textures, 1923 and 1928 in the side panel art, off the line by at most 1).

## Commands

```
# pairs (renders with SCENE_LOOK=linear SCENE_LOOK_INDEX=index.json through head_closeups.py, see "Pairs")
python3 scripts/common/look_fit.py pairs pairs_his.npz p07=head_p07.exr p08=head_p08.exr p09=head_p09.exr --index index.json
python3 scripts/common/look_fit.py fit pairs_his.npz --work WORK --out fit.json
python3 scripts/common/look_fit.py report pairs_his.npz --work WORK --out report.json
python3 scripts/common/look_fit.py bike head_cam07.exr index.json "208,10,22;205,41,62" --also "r2b=230,46,49" --out bike_red.json    # REDS: the reds the render holds; --ev7: PHOTO_EV["07"]
# Honda's studio views: build_bike.py stock with SCENE_LOOK=linear BIKE_STUDIO_RES=2000,1125, views honda_left etc.
# (BIKE_STUDIO="w,l,e,r" and BIKE_STUDIO_LAMPS='{"key": [1, 1]}' to test other studios)
python3 scripts/common/look_fit.py honda left render_honda_left.exr index.json 230,46,49 --ev -0.9 --also "main=208,10,22" --out honda_red_left.json
blender -b --factory-startup --python scripts/common/day_rig.py -- e1      # the E1 table
blender -b --factory-startup --python scripts/common/day_rig.py -- turn    # the turned sky's check
python3 scripts/common/look_fit.py sheet p09 head_p09.exr p09.jpg
python3 scripts/common/look_fit.py sheet cam07 head_cam07.exr cam07.jpg --scale 1 --region 215,112,1110,780 --vertical
```
