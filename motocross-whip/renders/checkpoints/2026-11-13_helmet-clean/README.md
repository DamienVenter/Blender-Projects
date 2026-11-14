# 2026-11-13: helmet graphics, a clean flat print (decision 42)

The Pinata Teal art is drawn by `scripts/rider/helmet_art.py` (traced in Leatt's four photos, logos from Leatt's own
files, labels drawn), lighting only from Blender. "Before" is the earlier texture projected from the photos (its
studio reflections baked in), "now" is the drawn print with the clear-coat paint (helmet.MATERIALS). Ledger:
`research/rider-ledger/helmet.md` section 3.

| File | What it shows |
|---|---|
| `01_leatt_views_photo_before_now.jpg` | Leatt's iso-left, iso-right (with goggle), back and top photos beside renders through the cameras fitted to them (helmet.CAMS), 1920 px renders shown at 720 |
| `02_leatt_1to1_crops_photo_before_now.jpg` | Seven 480 px crops at the photos' own pixels (1:1): brow badge and visor chevrons, side band and EIGHT POINT FIVE, chin lettering, side icon and emergency label, visor chevrons and LEATT band, crown vents and 360 Turbine, back band and icon, back LEATT with the DOT print and size sticker |
| `03_his_photos_07_08_09_before_now.jpg` | His photos 07, 08 and 09 (the helmet is 240 to 280 px there, enlarged to 560) beside close-ups of the rider blend at the matched views (`head_closeups.py` p07, p08, p09) |

Renders: Cycles, 24 samples at 1920 for Leatt's views, 48 for his. The rider blend for the close-ups is
`blend/rider_v2.blend` with the new image and paint values swapped in and reopened in Blender 5.2.0
(`rider_v2.blend` itself is not rebuilt in this step).
