# 2026-11-15: helmet round 2 (decision 44)

Ledger: `research/rider-ledger/helmet.md` section 5. Every sheet is Leatt's photo (or his) beside renders through
the cameras fitted to it; Leatt's views at the photos' own pixels (1:1, 560 px crops).

| File | What it shows |
|---|---|
| `01_pin-isoleft_port-panel_leatt_main_r2.jpg` | Pinata iso-left, port trim and grip panel: the built port is main's, so the big black area is still there (see 06) |
| `02_pin-isoright_goggle_leatt_main_r2.jpg` | Pinata iso-right with the goggle: unchanged, the goggle sits over the shell as before |
| `03_pin-back_band_leatt_main_r2.jpg` | Back band: main's facet shading and ridges either side of the centre line are gone (fair shell) |
| `04_pin-top_crown-back_leatt_main_r2.jpg` | Top, crown back: smoother; the centre stem between the turbine and the chevron is a purple and white ladder (main: white, the photo: purple), still wrong |
| `05_my27-front-isoleft_leatt_main_r2.jpg` | MY27 front iso-left (another colourway; shape and goggle only): brow still about 20 mm forward |
| `06_iso-port-held-back_isoleft_leatt_main_iso.jpg` | **The cause, found**: round 2's port edge where Leatt's photo has it (-5 to +4 px; main 185 to 221 px ahead) and the black reduced to the trim and panel |
| `07_iso-port-held-back_isoright-goggle_leatt_main_iso.jpg` | **Why it is not built**: with that edge the goggle's outriggers stand 21 to 23 mm ahead of it and the strap bridges the opening (its silicone side shows) |
| `08_his-photos-07-08-09_daylight_main_r2_iso.jpg` | His photos 07, 08, 09 (the helmet 240 to 280 px there, enlarged to 560) beside daylight close-ups (`head_closeups.py` p07, p08, p09): main, round 2, and the iso port |

Renders: Cycles 16 samples, Blender 5.2.3; Leatt's views at 1920 px through helmet.CAMS (unchanged this round),
his views 1200 px. Blender 5.2.0 check: the round 2 rider blend reopened in 5.2.0 renders p07 identically to 5.2.3 (mean difference 0.0 of 255).

Tests (scripts/rider, all six rider files): 84 passed, exit code 0 (goggle strap at least 0.55 mm off the shell; main 0.60). With `PORT = "iso"` three goggle tests fail (outriggers off the shell, strap through it). New: `test_shell_is_fair_at_the_crown_back` and
`test_face_port_edge_on_leatt_iso_left`, both failing on main (190 /m against 120; main's port 185 to 221 px off).
