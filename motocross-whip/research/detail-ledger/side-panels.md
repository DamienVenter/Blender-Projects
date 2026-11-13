# Detail ledger: rear side panel graphics (`scripts/bike/kit_sidepanel.py`, decision 37)

2026-11-13. Damien: the side number boards "look weird". The v1 artwork (image model, decision 31) had crack lines
and ticks through the 1s, a dark jagged wedge left of the number, stray jagged shapes on the front edge, PSALM 91
large, level and centred, a flat grey glitter upper area, and a right side with white rectangular cut-outs left by
the mirror tool. v2 draws every element by script. Check images: the agent's scratch folder
`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/bike/sidepanel/`.

## Sources
| Photo | What it shows of the panel |
|---|---|
| 07 `damien-bike-2026-11-12/07_left-side-riding-pan.jpg` (1332x888) | the whole left panel nearly square on, sunlit: every element's place and size (measured, below) |
| 02 `damien-bike-2026-11-10/02_left-side-shroud-seat-swingarm.jpg` | left panel from the front, close, shade: silver flake, black band, red rim round the intake, name, hole |
| 03 `damien-bike-2026-11-10/03_right-side-shroud-seat-frame.jpg` | the LEFT panel from behind (the file name is wrong: chain, chain slider and shift lever are on the bike's left; intake and LEATT at the front edge; kept as is, noted in that folder's README): black band, keylines, black splatter band, LEATT's light edge. The closest view of the flake: 0.88 mm per photo px up the panel, 2.2 mm along it (`tools/scale03.py`). A standard view since round 2: `dv03_left_rear` (`scripts/bike/fit_dv.py`, `research/bike-cameras-damien.json`) |
| 06 `damien-bike-2026-11-12/06_whip-from-below_rear-left.jpg` | left panel from below and behind: PSALM 91's letters, the plain black tail, the faint red grunge on the black |
| 08 | right side from below: the right panel is behind his leg. **No photo shows the right panel.** |
| `textures/damien-v1/art/plate.png` | his front plate artwork (approved kit): the 114 glyphs and the DAMIEN VENTER logo, same family as on the panels |
| `reference/leatt-gear/leatt-logo-red-with-icon_official_leatt-us_1200x848.png` | Leatt's own full logo (wordmark and triangle icon), downloaded 2026-11-13 from us.leatt.com (README row) |

## Frames
- Artwork px (2752 x 1536): kit.json's side panel crop [1832, 516, 3196, 1228] padded 27 px top and bottom,
  K = 2752 / 1364 = 2.0176 art px per template px; template px = 1700 per metre, so 1 art px = 0.29 mm.
  Left art: front at the left. Right art: the left crop mirrored (x_right = 2752 - x_left), front at the right.
- Panel geometry in art px from the v6 template (`tools/matmap.py` rasterises the side_panels faces by material;
  `tools/geom.py`): intake opening ring (18 points, `INTAKE`), top edge every 100 px (`TOP_EDGE`; rises 0.166 per
  px from x 1100 to 2100), panel bolt (1346, 1129) with a 50 px boss.
- Photo 07 to art: an affine fit to four panel landmarks (bolt, intake front tip, cover B bottom, cover A rear tip),
  rms 2.2 photo px (`tools/homog.py`, `H_p07.json`). One photo px is about 8 art px (2.3 mm): the measurement grain.
  A full homography from five points was badly skewed (too few points for 8 unknowns), so the affine was kept;
  07 is a long-lens pan, near orthographic.

## Elements (left panel; art px)
| Element | Measured (photo 07 px -> art px) | Drawn | Notes, other photos |
|---|---|---|---|
| PSALM 91 | P foot (722, 504.5) -> (1060, 617); P top (723, 492.5) -> (1065, 517); 1 top (802, 485) -> (1637, 423); 1 foot (801, 497) -> (1631, 523) | Inter Display Black, white; x 1061..1627, cap 92 (100 measured, less 8 px of blur), vertical shear 0.165 (verticals stay vertical, as in 07; the top edge's slope); baseline (1061, 623) to (1627, 530); cap line 20 px under the model's top edge | small, slanted along the top edge, above the intake (02, 03, 06, 07). Font: a heavy grotesque; the exact face is unreadable (question) |
| black band | top edge to PSALM's baseline + 16 px, from x 990 back | vector | 02: P starts just behind the silver; 03: band the height of the letters |
| 114 | 4 top-right (865, 487.5) -> (2094, 418); 4 top-left (835, 487) -> (1877, 426); first 1 foot-left (748.75, 556.25) -> (1261, 1036); second 1 foot-left (778.75, 551.25) -> (1478, 982); 4 diagonal foot (800, 539) -> (1630, 872) | the plate's three glyphs traced (rows 600..1480, cols 220..1540 of plate.png), affine plate -> art [[0.6818, 0.0157, 1066.05], [-0.1061, 0.6176, 170.85]] (residuals 13 px or less): 0.69 x 0.62 of the plate, baseline rising 8.8 deg, stems near vertical; 9 px black keyline | same family as the plate (flags on the 1s, black keylines where the digits overlap; 02, 03). The 4's counter sits about 60 px off the plate's: the panel's 4 may be drawn differently (question) |
| 114 clipping | first 1's top follows the intake's lower edge with its red rim (07, 02); 4 rises behind the intake to 80 px under the top edge | cleared 16 px round the intake (10 red rim + 6 black) and under PSALM's band ahead of the intake's rear end | |
| number foot / red zone top | (748.75, 556.25) -> (1260, 1036); (778.75, 551.9) -> (1478, 987); (827.5, 540) -> (1830, 869); (860, 530) -> (2064, 773) | cut line `CUT`; the number stops 9 px above it; red below, ragged 20 px (fractal noise) | 03: a grungy black band then red under the digits |
| silver flake | front piece (Honda's black front rectangle), cover A's front tail, ahead of the first 1 | Round 2 (`FLAKE_*`, `SPECK_*`): flake vinyl. A navy charcoal base (40, 46, 60) with worm-like specks over 32 percent of it: strokes 3.5 to 7 art px long (1.0 to 2.0 mm), 2.2 px (0.65 mm) wide, bent 0.6 rad (sd), drawn at 3x and averaged; each speck dim silver (165, 168, 178) times 0.7 to 1.0, metal and tilted (Material). Red ink over it (LEATT, splatter) lets the flake through (`INK` 0.45). Round 1 was smooth noise mapped to 8/11/18/70/250: a coarse salt and pepper at about half white | 03 (closest, 0.88 mm per px; box x 426..460, y 942..972 under LEATT): base (43, 43, 51) against the 1's white (145, 145, 151), fine worms over 0.32 of it (Otsu), 1 to 2 px, so 1 to 2 mm long and under 1 mm wide (`tools/speck.py`). 07 (sun): (28, 38, 58) against the white's (153, 179, 217), linear ratios 0.024/0.033/0.055, so an albedo near (45, 53, 66); speck share 0.33. 02 (shade): round 1's box (x 388..457, y 660..723) is on the panel's LEATT zone, not the shroud or the frame strip, but there the flake mirrors a bright sky: p10/p50/p90 0.20/0.60/0.98 of the 114's white. Metal flakes take the colour of what they reflect, so the three photos differ; round 1 matched 02's reflection with a light paint. Round 2 measures the film in 03 and 07 and lets the metal do the rest (render checks below) |
| red zone | behind the front piece's rear edge (template corners (1225, 975), (1108, 1232)), below the cut; at (2064, 774) the cut drops down cover B's rear edge | Round 2: the same pebble in red (`RED_GAP` (190, 18, 27) between light red worms `RED_SPECK` (216, 40, 47), the same strokes), the zone's mean kept at (198, 22, 30); not metal (the kit's default roughness 0.34). Round 1: red flake (198, 22, 30) +-30 noise | 03: gaps (135, 33, 44), worms (139, 44, 56); 07: (218, 55, 60) and (226, 62, 66): light red worms on the red. 02, 03: black splatter over it; 02: the rear of cover A is black to its edge |
| splatter | black drops into the red below the number; red drops over the black and silver above the cut; a red spray over the front near the first 1 (07: round LEATT and the intake's front tip) | 5200 + 2600 + 380 drops, exponential distance from the line (42, 46, 50..90 px), Pareto sizes up to 11 px, satellites round the big ones | |
| black laminate | behind the first 1's front edge (1262, 1040)..(1246, 624), up to the top edge and back to the tail | (13, 13, 15) with a faint dark red grunge print (30 percent at most) | 02, 06: dark red-brown grunge on the black above the 4 |
| LEATT | L foot (706, 535) -> (948, 877); icon apex (737, 519) -> (1170, 731); icon right end (748, 527) -> (1251, 793) | Leatt's official file, its own slant, scale 0.314 (303 px, 88 mm long), red (233, 0, 41), 3 px white edge | on the silver front piece (02, 03, 07); the light edge shows in 03 and 07 |
| name | foot-left (776, 574) -> (1461, 1172); top-left (778, 566) -> (1474, 1105); top-right (826, 559) -> (1821, 1027); foot-right (825, 567) -> (1815, 1094) | the plate's DAMIEN VENTER logo traced (rows 1440..1600, cols 520..1220, white only), 360 px long (scale 0.635), vertical shear 0.22, 5 px black outline | signature then bold italic VENTER in 02, 03 and 07, as on the plate. In 02 the signature reads like "DM"; it is the plate's DAMIEN at that size (question) |
| hole | 07: 11 photo px across round the bolt | black disc r 46 (27 mm) at the bolt | 02, 03: a clean round hole |
| intake rim | | 10 px (3 mm) of the plastic's own red round the opening, black inside | 02, 03, 07 |

## Not drawn, and why
- Small print behind the 4 near the top edge (02: a lowercase web address, about 40 photo px long, and maybe a
  tiny multicolour logo next to it; 06 shows a small light mark there): unreadable in every photo. Question.
- White swoosh stripes toward the tail: reflections of the sky in the gloss laminate. They change shape and place
  between 02 and 03 and the tail is plain black in 06.
- The red band along the lower rear edge in 03: the panel's own red plastic lip seen from below and behind
  (geometry), not the decal.

## Right side
In none of his photos. Built by the same script: zones from the mirrored geometry (glitter and splatter drawn
afresh with their own seed), every word and logo at the mirrored place and slant, its source not mirrored, so all
lettering reads left to right (kit makers' practice; test_kit checks the placements' determinants and that the
right art is not the left's pixels flipped). Consequences to show Damien: the 114 reads 1-1-4 from the rear, so
the 4 sits under the intake (its top clipped) and the 1s rise behind PSALM 91 at the rear.

## Texture fix
`kit_canvas.close_slits` (kit.json "close_slits": true on both side panel entries): the side view's raster leaves
slits inside the panel where faces meet edge-on (no part drawn) or the subframe tube leaks through, and a 60 to 1700
texel patch under the subframe and rear_inner; they kept the plain red and showed as red cracks through the 114.
Left: 369 slit texels before, 0 after (test_kit.red_slits); right: 53 before, 0 after. Other textures unchanged.

## Material (round 2: per-texel material maps)
Round 1: `build_bike.principled` took a base colour image only (roughness 0.34, coat 0.08 everywhere), so the black
laminate was no glossier than the flake and the flake was not metal. Now any kit panel may carry a material map
(kit.json `"mat"`, the artwork's size, glTF's metallic-roughness convention: G roughness, B metallic, R 255).
`kit_canvas` maps it exactly like the colour (same projection, same masks) into `<texture>_mr.png`, default
everywhere else kit.json's top-level `"material"` (roughness 0.34, metallic 0: build_bike's livery default), and
`principled` wires `<texture>_mr.png` (Non-Color, Linear) through Separate Color into Roughness (G) and Metallic (B)
when it exists, so the glTF export carries it too. Only the side panels have one so far (`kit_sidepanel.py` writes
`art/sidepanel_L_mr.png` and `_R_mr.png`); every other texture is unchanged and gets no `_mr.png`.

| Zone | Roughness | Metallic | Source / reason |
|---|---|---|---|
| default (red ink, white print, LEATT, name, rim) | 0.34 | 0 | build_bike's livery value (round 1, tuned on the studio views); "the red ink stays as it is" |
| black laminate | 0.12 | 0 | gloss vinyl laminate: 02, 03 and 07 show sharp sky reflections in it (the white swooshes, "Not drawn") |
| flake base (between the specks) | 0.40 | 0 | 03: the pebbled flake zone shows no mirror reflection where the laminate beside it does |
| flake specks | 0.25 to 0.35 by speck | 1 | metal flakes: they read light silver in shade (02, the sky reflected), dark in sun (07); per-speck brightness 0.7 to 1.0 sets each one's roughness |

Partly covered texels mix by coverage (the specks are drawn at 3x and averaged), so the map stays physical between
zones. Red ink over the flake (splatter, LEATT) takes the default: the flake still shows through its colour (02),
but the ink is a print layer over it. The number, PSALM 91 and their keylines keep the laminate's gloss (printed
under it).

Normal map (kit.json `"nrm"`, `<texture>_n.png`, same mechanism): a metal flake lying flat in the film mirrors what
the film mirrors, so a flat metallic speck still read as grey paint (render std 16 in the flake box). Real flakes lie
tilted, so neighbours catch different light: that is the sparkle. Each speck gets one tilt, Rayleigh with
`FLAKE_TILT` 12 deg per axis (EST: metal-flake coatings hold their flakes within about 20 deg of the film; median
14 deg, 9 in 10 under 26 deg; the photos cannot measure it at about 1 mm a pixel), at a random azimuth; tangent
space, OpenGL convention (128 + 127 n; flat (128, 128, 255) wherever the texel is not metal). `principled` wires
`<texture>_n.png` (Non-Color, Linear) through a Normal Map node into the base layer's Normal only; the coat keeps the
smooth surface normal (the laminate over the flakes is smooth). Render std in the sp07 flake box: 16 flat, 22.6
tilted. A check for later: a close photo of the panel in sun.

## Inner and back faces (round 2)
Round 1's `r7/render_sp03.png` showed a mirrored VENTER behind the shock: the side projection painted the right side
panel's inner skin with the same texels as its outer one. Kits are stuck on the outside, so inner and back faces of
every kit plastic now get the part's own plain plastic (the material it had before the kit assignment), by
`kit_faces.py`, called from `build_bike.kit_materials` for every kit part:
- Shells (side panels, shrouds, number plate): a kit face is an inner face when another face of the same part, within
  6 mm in front of it along the projection's direction and parallel to it (|n1 . n2| > 0.8), covers its centre. The
  normals are not trusted (not all shells are wound outward).
- Single surfaces (THIN: fenders, shroud decks, fork guards; solidified inward in Blender): per connected surface,
  the area-weighted vote of n . d says whether its normals look out; the Solidify modifier's `material_offset` puts
  the other side's material on the shell. The right fork guard's flat plate is wound inward (its outer side is the
  shell), its wrap outward; both now carry the kit outside.
- Side panels (parts2): left 7676 of 17864 kit faces are inner (2 to 3 mm inside the outer skin at the same x, z),
  right 6307 of 13205; shrouds 11326 of 21456 a side; number plate 2422 of 4852.
- The airbox cover (plastic_black grid inside the left panel's outline) is a single surface and keeps the kit as
  before. Fork guards: their inner faces are now the guard's plain plastic (fork_guard material), which may not be
  Damien's guard colour (not in any photo).

## Checks
- `test_kit.py`: the committed artwork is exactly the script's output; both side entries point at the script; every
  lettering placement has a positive determinant on both sides and the right one sits at the mirrored place; the
  right art's PSALM 91 matches the word drawn afresh (IoU > 0.9) and not the left art flipped (IoU < 0.6); the
  114's white closes by under 0.2 percent (no crack lines) and is three digits; no red slits in side_L/side_R.
- Renders through photo angles (bike_v7, `renders/checkpoints/2026-11-13_side-panels/`; all sheets in the scratch
  folder): 07 through the side close-up sp07 (camera (0.45, 3.6, 1.05) to (0.43, 0.15, 0.80), 110 mm); 02 through
  build_bike's dv02_left_front; 03 through a camera fitted to photo 03: nine landmarks read by eye (bolt hole,
  intake front tip and low corner, the name's three corners, P's foot, the left grip's end, the bar pad), seven
  unknowns. Round 1 fitted it in the scratch folder (49.6 mm, residuals 2 to 20 px). Round 2 made it a standard
  view: `fit_dv.py` fits it to the parts as built (the panels' graphics placed on the outer skin) and writes
  `research/bike-cameras-damien.json`; build_bike makes it the camera `dv03_left_rear` at the photo's 739 x 1600.
  Now: position (-1.075, 1.000, 1.225), looking along (0.878, -0.445, -0.180), up (0.194, -0.014, 0.981), 47.7 mm on
  the 1600 px side (photo 03 is a crop of the phone's frame); residuals 0.7 to 20.9 px on the panel, 24.5 and 20.1 px
  on the grip and bar pad (a guess: the bars may be turned). `test_bike.test_photo03_camera_is_fitted_to_the_current_model`
  refits it and holds the panel's residuals under 25 px (22 mm at 0.88 mm a pixel).
- Layout through 07: PSALM 91 to 114 height ratio 0.67 in the render, 0.68 in the photo. Through 03: PSALM 91 over
  the intake, the 1s under it, LEATT on the flake, hole and name in the red zone, all in place.
- Not a crack: the plate's 1s have a thin black notch under the flag (the plate's own design, `art/plate.png`);
  on the right panel it runs through the rear 1 next to the panel's rear bolt.

### Round 2 checks (2026-11-13)
- Tests (`test_kit.py`): the flake is photo 03's (speck share 0.25 to 0.40, a navy charcoal base, dim silver specks,
  median speck 0.4 to 2.5 mm2, worm-like outlines); the material map is physical (laminate gloss, only the specks
  metal, red ink at the default); the normal map tilts only the flakes (median 0.9 to 1.4 times FLAKE_TILT, no
  mean lean); side_L/R carry both maps; kit_canvas writes a map only for textures that have one; kit_faces finds a
  shell's inner skin whatever its winding, puts a single surface's kit on its outer side, and on the side panels as
  built sends back the 3 mm inner skin. `test_bike.py`: the dv03 camera refit. `test_detail_plastics.py`: the upper
  rear is fair (ledger plastics.md, decision 37 round 2). All bike tests: 166 passed, exit code 0.
- Renders of bike_v7 round 2 (Cycles, the studio): the sp07 flake box reads (90, 88, 98), 0.44 of the 114's white,
  std 22.6 (photo 07 in sun: 0.21 of the white; in the studio the metal specks mirror the grey cyc, so the zone reads
  lighter than in his photo). Through dv02: p10/p50/p90 0.33/0.52/0.71 of the white (photo 02 in shade: 0.20/0.60/0.98, the sky in
  every flake). Through dv03: 0.54 of the white (photo 03: 0.50). The studio's grey cyc is in every flake, so the
  model reads a little lighter than his tent or the sun; the film itself is photo 03's.
- Sheets (`renders/checkpoints/2026-11-13_side-panels/`, README there): photo beside model for 07, 02 and 03, both
  sides, the rear section under a raking sun (round 1 against round 2), the flake up close, the inner faces.
- `blend/bike_v7.blend` (packed) reopened in Blender 5.2.0 (`tools/reopen_check2.py`): every image packed, the
  maps Non-Color, livery_L/R wired (material map and normal map, coat normal smooth), the side panels' inner faces
  on plastic_red (10371 faces), the Solidify material offsets on the fork guards, front and rear fenders and shroud
  decks, the dv03_left_rear camera at 739 x 1600.
