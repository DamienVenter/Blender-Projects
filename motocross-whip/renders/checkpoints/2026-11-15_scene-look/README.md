# Scene look round 1 (decision 54), 2026-11-15

Each sheet: his photo | AgX - Punchy -0.6 (decision 46) | the new scene look ("daylight"). Both renders come from
the same scene-linear render of the view (head_closeups.py, daylight rig, 64 samples, `SCENE_LOOK=linear`), put
through Blender with `look_apply.py`, so only the look differs. Made by `scripts/common/look_fit.py sheet`
(research/scene-look.md, "Commands").

| file | view | scale |
|---|---|---|
| 01_his-07_head.jpg | p07, his 07 cropped round his head (camera fitted to the helmet) | 2 x the photo's pixels |
| 02_his-08_head.jpg | p08 | 2 x |
| 03_his-09_head.jpg | p09 | 2 x |
| 04_his-07_bike.jpg | cam07: the bike in his 07 (research/rider-cameras.json), the look at its EV | 1 x |
| 05_his-07_bike_photo-exposure.jpg | cam07 at photo 07's own exposure (-1.04 EV, read off his white shell in 07) | 1 x |

What changed (mean dE of the class medians, white shell and black print of 07, 08, 09 plus 07's magenta, through
Blender): 21.1 with decision 46's look, 12.7 with the new one. White shell 9.5 / 23.1 / 12.1 to 4.7 / 8.9 / 5.3;
black print 22.6 / 10.7 / 18.6 to 21.7 / 3.8 / 5.8. The bike's red keeps its G and B (50, 46 against his 47, 49).

What is still not right (none of it the look's):
- The background is the rig's sky: a cream glow, where his sky is blue (and the gloss blacks reflect it).
- The rider's pose is not his (pose.py "seated"), so the bike sheet lines up only on the bike.
- Jersey and pant prints too pale and lifted (pink G 54 to 77 where his are 2 to 6), lime and teal too light, the
  darks neutral where his are navy, boots too light; the helmet's magenta short of blue. research/scene-look.md.
- The bike's red reads 218, 42, 38 at photo 07's exposure against his 189, 47, 49; RED 187, 28, 49 would match but
  waits for kit_canvas.RED to move with it.
- His phone exposes each shot (08 sits 0.6 to 0.9 EV over the look's EV, 07 0.2 to 1.0 under) and lifts the shadows
  of 07: one global look matches 08 and 09 better than 07.

Checked: the same view rendered by head_closeups.py itself with the look (p09, 32 samples) equals the linear render
put through the look to 0.6 levels mean (medians of the white shell and black print identical); the same render in
Blender 5.2.0 equals 5.2.3's in every pixel; the swatch chart through 5.2.0 and 5.2.3 within a level of the numpy
reference.
