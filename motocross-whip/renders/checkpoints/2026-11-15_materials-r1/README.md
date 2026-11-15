# Gear materials round 1, phase A (decision 59), 2026-11-15

Numbers and method: `research/scene-look.md` ("The gear, materials round 1") and the ledgers
(`research/rider-ledger/gloves.md`, `boots.md`, `kit.md`). Commands: `look_fit.py darks`, `look_fit.py gear`,
`look_fit.py boot_white`.

His photos: his photo | main | this round, at the photo's pixels (scaled up by an integer), both renders through
`scene_look.display` at the photo's PHOTO_EV. Main = round 2's daylight look; this round = the same plus his phone's
lift of the darks (DARK_LIFT 0.0668) and, for 07, its tint (PHOTO_TINT["07"]). The rider's pose is the blend's seated
pose, not his: compare colours, not shapes.

| file | what to look at |
|---|---|
| `01_darks_cam07_rider.jpg` | the jersey's, pant's and glove's black: navy-grey and lighter as his (dE 2.7, 1.6, 2.3; main 13.3, 12.4, 14.2) |
| `02_darks_cam07_tyre.jpg` | the rear tyre, a neutral the look was fitted on: dE 6.1 (main 11.9) |
| `03_darks_p07_p08_p09.jpg` | the head views: the helmet's black print (07 8.7, 08 5.2; main 15.1, 8.2) and the jersey's black (6.2, 6.5, 6.1; main 7.9, 7.1, 8.7) |
| `04_boots_cam07.jpg` | the boot in 07 (renders cropped where the seated pose puts it): main's white 213, 222, 228 (dE 14.7 with this round's look), this round 207, 215, 221 (dE 12.3), his 176, 184, 181 |

07's boot hangs in the bike's shade beside the engine; ours is lifted toward the sky by the seated pose. Its white is
set where the boot and the helmet's white shell are both in sun (his 08: 0.93 of the shell), not here.

Maker's studio photos: Leatt | ours, under Standard on white (`gloves.py check`'s studio light).

| file | what to look at |
|---|---|
| `05_boot_leatt02.jpg` | Leatt 02, main, this round: the right boot alone, rest pose, orthographic, placed by `boots.P02`; one exposure for both renders (-0.67 EV, main's lit white at Leatt's). Hue: Leatt C 0.4, main 1.8, this round 2.0 (a clean white, dE under 2); this round's level 0.86 of main's (the paint 219, 222, 224 against 236, 239, 242). Ours carries the wear layer (dust at the welt); Leatt's is new |
| `06_glove_leatt.jpg` | Leatt my26 back and my27 three-quarter back beside ours (main's check renders: the gloves' materials are kept, so main = this round). Leatt's dark / white 0.025, ours 0.055: Leatt's black point, as the kit's |

Blender 5.2.0: the boot view above reopened from this round's 5.2.3 blend and rendered in 5.2.0 matches 5.2.3 to the
level (max difference 0); the swatch chart through the new compositor (lift and 07's tint) is within a level of
`scene_look.display` (black 16, 20, 35).
