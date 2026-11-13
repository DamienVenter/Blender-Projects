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
| 03 `damien-bike-2026-11-10/03_right-side-shroud-seat-frame.jpg` | the LEFT panel from behind (the file name is wrong: chain, chain slider and shift lever are on the bike's left; intake and LEATT at the front edge): black band, keylines, black splatter band, LEATT's light edge |
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
| silver flake | front piece (Honda's black front rectangle), cover A's front tail, ahead of the first 1 | a dark base packed with bright flakes: smooth noise (5 px, 1.45 mm, plus a 2 px grain) mapped to 8/11/18/70/250 at 10/35/50/65/90 percent of the area (`SILVER_Q`, `FLAKE`); red ink over it (LEATT, splatter) lets the flake through, 0.55 to 1.0 of the red by the flake's brightness. Through 02's camera (render box x 327..362, y 683..716 against the 114 at 441..470, 720..786): p10/p50/p90 0.24/0.56/0.88 of the white | 02 (shade), box x 388..457, y 660..723 beside the 114's white (499..527, 604..688): p10/p50/p90 30/91/149 against the white's median 151, 0.20/0.60/0.98; a dark base packed with bright flakes; the red LEATT shows the flake through it. Reads navy in the sun (06, 07). Tries through 02's camera: grey 170 +-52, 0.62/0.82/0.89 of the white (too light, too flat); 4 px flakes at 10/26/120/228/250, 0.41/0.79/0.96; 6 px at 8/12/30/160/245, 0.27/0.69/0.93. The render and the camera average light in linear terms, so a few bright flakes lift the median: the base must be darker than the photo's median suggests |
| red zone | behind the front piece's rear edge (template corners (1225, 975), (1108, 1232)), below the cut; at (2064, 774) the cut drops down cover B's rear edge | red flake (198, 22, 30) +-30 | 02, 03: red flake with black splatter; 02: the rear of cover A is black to its edge |
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

## Material
`build_bike.principled` takes a base colour image only (livery_L/R: roughness 0.34, coat 0.08 everywhere). A gloss
or roughness map from the kit is not supported, so the black laminate is not glossier than the flake and the flake
does not sparkle. Proposal (not done): a second kit output, side_L_rough.png, from the same zones (black 0.12,
silver and red flake 0.30 with per-flake variation, the white print 0.25), read by an optional roughness image in
principled() for livery_L/R.

## Checks
- `test_kit.py`: the committed artwork is exactly the script's output; both side entries point at the script; every
  lettering placement has a positive determinant on both sides and the right one sits at the mirrored place; the
  right art's PSALM 91 matches the word drawn afresh (IoU > 0.9) and not the left art flipped (IoU < 0.6); the
  114's white closes by under 0.2 percent (no crack lines) and is three digits; no red slits in side_L/side_R.
- Renders through photo angles (bike_v7, `renders/checkpoints/2026-11-13_side-panels/`; all sheets in the scratch
  folder): 07 through the side close-up sp07 (camera (0.45, 3.6, 1.05) to (0.43, 0.15, 0.80), 110 mm); 02 through
  build_bike's dv02_left_front; 03 through a camera fitted to photo 03: nine landmarks read by eye (bolt hole,
  intake front tip and low corner, the name's three corners, P's foot, the left grip's end, the bar pad), seven
  unknowns, residuals 2 to 20 px: axle-line frame position (-1.129, 1.041, 1.218), looking along
  (0.877, -0.450, -0.171), up (0.191, -0.001, 0.982), 49.6 mm on the 1600 px side (so photo 03 is a 2x crop of the
  phone's frame). The panel points fit; the bar is a guess (the bars may be turned).
- Layout through 07: PSALM 91 to 114 height ratio 0.67 in the render, 0.68 in the photo. Through 03: PSALM 91 over
  the intake, the 1s under it, LEATT on the flake, hole and name in the red zone, all in place.
- Not a crack: the plate's 1s have a thin black notch under the flag (the plate's own design, `art/plate.png`);
  on the right panel it runs through the rear 1 next to the panel's rear bolt.
