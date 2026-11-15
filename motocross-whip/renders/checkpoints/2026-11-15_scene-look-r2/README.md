# Scene look round 2 and 2b (decision 55), 2026-11-15

Numbers and method: `research/scene-look.md`. Round 1's checkpoint: `../2026-11-15_scene-look/`. Round 2b (the red
and Honda's studio, after the review of round 2's red at 1:1) updated `his07_bike.jpg`, the Honda sheets and
`kit_seam_1to1.jpg` in place.

His photos: his photo | round 1 (decision 54's light and look) | round 2, both renders at the photo's own exposure
(read off his white shell's lit side the same way for each round). The rider's pose is not his (the blend's seated
pose), so compare colours and light, not shapes.

| file | what to look at |
|---|---|
| `his08_head.jpg` | the sky deep blue as his (was cream); the shell's shade blue-grey as his |
| `his09_head.jpg` | the same; the sky behind him at dE 1.4 |
| `his09_sky.jpg` | the sky band above his head in 09, stacked: photo, round 1, round 2 |
| `his07_bike.jpg` | his 07 with the bike at 1:1 (photo 07's pixels): photo, main (round 1), round 2 (RED 205, 41, 62), round 2b (RED 230, 46, 49); the two reds relit through the diffuse passes of one render. Round 2 reads crimson, round 2b a plain red as his |

Honda's studio photos (stock bike, studio look: Standard at -0.9, on white): Honda | main (RED 208, 10, 22, main's
studio) | round 2 (RED 205, 41, 62, main's studio) | round 2b (RED 230, 46, 49, round 2b's studio).

| file | what to look at |
|---|---|
| `honda_left.jpg`, `honda_lf34.jpg`, `honda_right.jpg` | whole views at a quarter of the photo |
| `honda_left_1to1.jpg`, `honda_lf34_1to1.jpg`, `honda_right_1to1.jpg` | the plastics at 1:1 (render pixels, half the photo's) |

Round 2b's red, on the plastic's diffuse body (the coat's highlights left out by the coordinator's gate): his 07's
hue (G = B: ours 201, 30, 30 against his 183, 41, 41, dE 12.6 / 16.4 median / lit; round 2 3.9 / 12.4 but crimson),
and Honda's views at dE 13.7 / 4.8 (left), 13.1 / 7.7 (lf34), 12.8 / 3.6 (right) against main's 15.1 / 7.2, 13.8 /
4.0, 30.1 / 11.9 (round 2: 27 to 39). Honda's studio now reflects dark as theirs does: the world reaches reflections
only through a dim dome (0.2), only the top lamp is seen in them, and the lamps turn with the camera. Not met:
lf34's lit quarter (7.7 against main's 4.0), a light Honda set for that shot alone.

Damien's kit with round 2b's red: `kit_seam_1to1.jpg`, Honda's left studio camera at the photo's full 4000 x 2250
in round 2b's studio (build_bike's own honda path, BIKE_BORDER), two boxes at 1:1 (the shroud, tank and seat; the
front fender, whose inner faces are the plain plastic): the rebuilt kit textures' red and the plain plastic are one
colour, no seam (every changed texel was round 2's red or on its blend line, `research/scene-look.md`).

Blender 5.2.0: head_closeups p09 daylight rendered in 5.2.0 and 5.2.3, identical (0 pixels differ).

Still not right: 07's darks (his phone lifts them, local tone mapping); the helmet's magenta print (the helmet's
paint); the jersey pinks' grey layer, the navy darks, the teal and the boots (the materials round, numbers in
research/scene-look.md); his 07's red at 12.6 / 16.4 (no red with his hue gets under about 12 / 16 while Honda's
views stay within main's: their red is purer, his photo has more sun on the tank); lf34's lit quarter (above); the
frame's and swingarm's highlights dimmer than Honda's (frame median G 139 against 163).
