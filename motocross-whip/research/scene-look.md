# Scene look (decision 54): fitted to his phone's photos

Round 1, 2026-11-15. The look every render of the bike and the rider goes through, fitted on pixel-aligned pairs of
our daylight renders and his photos 07, 08 and 09. Module: `scripts/common/scene_look.py`; fit, report, red and
sheets: `scripts/common/look_fit.py`; Blender check: `scripts/common/look_apply.py`; tests:
`scripts/common/scene_look_checks.py` through `scripts/rider/test_scene_look.py` and `scripts/bike/test_scene_look.py`.

## The look

| step | what | value | source |
|---|---|---|---|
| 1 | gains (white balance, exposure) | log2: EV 0.102, R +0.234, G 0, B -0.302 (gains 1.262, 1.073, 0.871) | WB: the white shell, below; EV and the curve: the fit, below |
| 2 | tone curve on max(R, G, B), the three channels scaled by T(M)/M (hue and channel ratios kept) | T(u) = m u^P / (1 + u^P), P 2.59, m so that T(8) = 1 | the fit |
| 3 | view | Standard (the sRGB curve, clipped) | |
| "scene" kind | studio-lit views (build_bike, build_rider, rake, head_closeups' studio) | neutral gains 2^(EV + 0.832) | 0.18 linear at 69, where decision 46's AgX - Punchy -0.6 put it (look_apply.py, Blender 5.2.3) |
| "studio" kind | Leatt's and Honda's studio comparisons | Standard at the caller's exposure | decisions 44 and 46, unchanged |

Steps 1 and 2 are a compositor node group ("scene_look": math nodes) set on `scene.compositing_node_group`; the
view's curve mapping cannot do step 2: it works per channel, and its film-like mode still sends the smallest channel
through the curve. Renders show it; the viewport shows it with Viewport Shading's Compositor on Camera or Always.

Grey ramps (G channel, 8-bit; Blender 5.2.3 through look_apply.py, equal to `display()` within a level):
- "scene", linear 0.02, 0.045, 0.09, 0.18, 0.36, 0.8, 1.6: **1, 6, 26, 69, 143, 225, 250** (decision 46: 4, 19,
  41, 69, 103, 146, 179). More contrast: his photos crush the darks (the coordinator's measures, LOOK1 brief: darks
  12 to 29 in his photos against 47 to 88 in ours).
- "daylight", linear 0.062, 0.123, 0.244, 0.486, 0.966, 1.92, 3.82, 7.59: 4, 20, 55, 120, 193, 228, 236, 237 (R
  reaches 255: a render-neutral grey reads warm, as the phone balances the rig's blue sky light away).

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
light included. **Not applied**: `kit_canvas.RED` paints the same plastic in the kit textures (side panels, fenders,
the inner faces' plain plastic sits next to them), `test_kit.py` checks it, and textures are not this round's; RED
in build_bike.py alone would put two reds side by side. Both should move together, with the Honda studio views
(Standard) checked against Honda's photos, in a bike round.

## The kit, gloves and boots (not fixable by the look; the jersey agent owns kit.py)

The pose is not fitted, so no pixel pairs: colour-gated regions instead. Render: every pixel of the class; photo:
the pixels in the garment's render mask dilated 20 px (25 in cam07), helmet, goggle and bike taken out; the same
colour gate on both (pink hue 315 to 352, lime 55 to 110, teal 150 to 205, dark value under 0.3, white saturation
under 0.2 and value over 0.6). L*, C*, hue of the median; q10 / q90 the L* of the 10 % and 90 % luminance
quantiles (shade side, lit side).

| view | class | his photo | scene look | reading |
|---|---|---|---|---|
| p08 | jersey pink | 151, 2, 49; L32 C58 h18; q 12-29 | 164, 54, 101; L40 C49 h357; q 24-39 | too pale, lifted shade, too blue |
| p09 | jersey pink | 200, 6, 100; L43 C70 h3; q 11-36 | 220, 77, 132; L54 C60 h0; q 40-51 | too pale, lifted shade |
| p09 | jersey lime | 146, 177, 50; L68 C64; q 38-84 | 202, 230, 66; L87 C78; q 81-88 | too light, flat (shade lifted) |
| cam07 (07's exposure) | jersey lime | 116, 172, 44; L64; q 45-80 | 172, 201, 63; L77; q 59-84 | too light |
| cam07 (07's exposure) | jersey teal | 61, 122, 130; L48 h211 | 141, 191, 167; L73 h163 | too light, too green |
| cam07 (07's exposure) | pant pink | 186, 23, 113; L42 C66; q 13-40 | 215, 74, 130; L53 C60; q 43-48 | too pale, lifted shade |
| cam07 (07's exposure) | pant lime | 120, 178, 33; L66; q 39-70 | 147, 195, 59; L73; q 66-82 | too light, flat |
| cam07 (EV) | jersey / pant dark | 30, 38, 52 / 31, 37, 52; L15 h274-280 C10 | 52, 46, 44 / 48, 45, 45; L19-20 C1-3 warm | neutral where his are navy |
| cam07 (EV) | gloves (dark) | 34, 39, 53; L16 h281 | 43, 40, 36; L16 warm | right level, missing the blue |
| p09 | gloves | 31, 41, 50; L16 | 16, 17, 17; L5 | too dark (p09's region is small, 184 px) |
| cam07 (07's exposure) | boots (white) | 180, 186, 184; L75; q 65-84 | 244, 237, 225; L94; q 86-97 | too light and warm |

Readings:
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
- Tests (`test_scene_look.py` in rider and bike): the swatch chart, the module's numbers (T(8) = 1, 0.18 at 69 under
  "scene", ratios kept, gains = EV + WB), and each script's look calls (AST: imports scene_look, calls
  scene_look.apply with the kinds in the named functions, no "AgX - Punchy" left there). On main: collection error
  without the module; with the module copied in, rider 3 failed (build_rider, head_closeups, goggle_views do not
  import scene_look), bike 2 failed (build_bike, rake).

## Commands

```
# pairs (renders with SCENE_LOOK=linear SCENE_LOOK_INDEX=index.json through head_closeups.py, see "Pairs")
python3 scripts/common/look_fit.py pairs pairs_his.npz p07=head_p07.exr p08=head_p08.exr p09=head_p09.exr --index index.json
python3 scripts/common/look_fit.py fit pairs_his.npz --work WORK --out fit.json
python3 scripts/common/look_fit.py report pairs_his.npz --work WORK --out report.json
python3 scripts/common/look_fit.py bike head_cam07.exr index.json 208,10,22 --work WORK --out bike_red.json --ev7 -1.038
python3 scripts/common/look_fit.py sheet p09 head_p09.exr p09.jpg
python3 scripts/common/look_fit.py sheet cam07 head_cam07.exr cam07.jpg --scale 1 --region 215,112,1110,780 --vertical
```
