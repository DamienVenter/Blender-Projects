# Goggle round 13 (decision 57)

Leatt | main (8c75de2) | round 13 per item. Free goggle renders: 16 samples, goggle_views.py's studio look, Leatt's
see-through lens VLT (iso55 0.78, the white ISO 0.7, others 0.83), the plates turned 64 deg (iso55, the white ISO,
the Forge front) and 76.5 (phr) as in round 12. Worn renders: Leatt's Pinata kit iso-right through
helmet.PRINT_CAMS, 16 samples. His photos 07 and 09: origin/main's head_closeups.py p07 and p09 in the scene look's
daylight rig (decision 55, scripts/common/day_rig.py) on rider blends built with main's and round 13's gear, 16
samples, the photo's crop at 4x. Ledger: research/rider-ledger/goggle.md section 16.

## Crops
- 01a, 01b (item 1): the strap carrier at the far end in the Pinata ISO and the white ISO at 3x. Its outer edge at
  1699 to 1705 px (Leatt 1703 to 1705, main's frame end 1692 to 1696), the windows at rows 837 to 906 and 1025 to
  1091 (830 to 900, 1025 to 1092), the strap's teal in the lower window at 1681 to 1685 (1679 to 1683). Ours stops
  2 to 3 mm short at the top and bottom (where our frame's corners reach its back), and its clear post stands 17 to
  20 px beyond the edge at rows 958 to 972, where Leatt's CAD shows none.
- 01c, 01d (item 1): phr (his Royal) and the Forge front at 3x. Leatt's C stands beyond the frame's end, 13 mm wide,
  with the post out of its outer edge and the plate hidden behind it; ours stands inboard, and our far plate's
  printed face shows where Leatt's C is. Not fitted: iso55 and phr see the far end from nearly the same side and
  disagree on the C.
- 01e (item 1): the near end in iso55 at 3x. The near carrier sits behind the lens; through our see-through lens it
  reads as a dark strip at 1000 to 1040 px (Leatt's CAD lens shows a faint band at 985 to 1000 only).
- 01f: iso55 at 1:1, unaligned.
- 02a (item 2): the plate in the Pinata iso-right at 2x: Leatt (an empty helmet); main and round 13 at PLACE (his
  placement); round 13 rebuilt at the empty helmet's placement (12.6 mm lower, 3.5 mm back; comparison only), with
  and without the strap. Where the strap's print meets the plate, rows 860 / 980: Leatt 764 / 751 px (leaning left,
  -10.8 px a 100 rows), main 764 / 787 (+19.3), round 13 757 / 749 (-6.5; the plate turns as one). At the empty
  placement the plate needs no turn and its back edge (the mesh) stands at 760 / 752, but the strap, its path solved
  there, leaves the straight-back plate outwards and covers its back 25 px (the print's edge at 785 / 777).
- 02b, 02c (item 2): the plate's outline over his photos 07 and 09 at 12x (main's twist, round 13 rigid, rigid moved
  3 and 6 mm): 0.41 and 0.51 px a mm, the two differ by 1 to 2 px, under the cameras' landmark rms (2.2, 8 px).
- 03 (item 3): the far end in iso55 at 4x: the silhouette now the carrier's edge. The lens's end (its bow at rows
  840 and 1090) is unchanged from main.
- 04a, 04b (item 4): the vent teeth at 5x in the white ISO and the Pinata ISO with a 10 px grid. Main runs flat at
  768 to 769 px from 1095 to 1225 in the white ISO; round 13 within 3 px of Leatt's edge from 1100 to 1320 px. Its
  steps are eased: Leatt's step at |s| 48.5 mm is crisp (6 px), ours a ramp over about 20 px.
- 04c (item 4): the three views' drops by |s| (each less its band line), their median, main and round 13: rms 0.20
  mm against the median over 47 to 71 mm (main 0.77). Grey: where the views disagree (the tooth's end face meets the
  band at 75, 77 or 78 mm); built to the median.
- 05 (item 5): the comb's rim in phr at 4x: the face foam's specular 0.1, rim L p50 86 (Leatt 87, main 97), peak 94
  (Leatt 93, main 99) with the run's backdrop-blended top pixel left out.
- 06a to 06d: his photos 07 and 09: the head at half the render's scale and the goggle at the render's scale (4x his
  photo), main and round 13. In 07 the near carrier shows at the frame's front end; through its windows, above the
  strap's end, the sky shows (the gap between the carrier and the frame is open at its outer edge): 1 to 2 px at his
  photo's own scale.

## Still not right
- phr's C (13 mm wide, beyond the frame's end) and the Forge front's; the back views' loop (phyb) not built.
- The carrier's clear post shows beyond the ISO renders' edge (17 to 20 px); phr and the Forge front show a post.
- The windows show the sky from the side (06b); the near carrier shows through the see-through lens (01e).
- At the empty helmet's placement the strap covers the plate's back (02a): the plate rests by the shell only, not by
  the strap's pull.
- The lens's end bows at iso55 rows 840 and 1090 (main the same).
- Outline p90 with the strap's end in place: iso55 4.08, phy 3.84, phr 3.95, wiso 4.25 mm (main 4.13, 3.72, 4.32,
  3.96; round 11 phy 3.44, phr 3.89): phy and wiso above main.
- The Forge back-strap sheet (item 6) not done.

## Checks
- Blender 5.2.0 (Damien's): the free iso55 view of the round 13 goggle rendered in 5.2.0 and in 5.2.3 is pixel
  identical (mean difference 0.000, max 0).
- New tests, each failing on main 8c75de2: test_round13_strap_carrier_round_the_lens_post and
  test_round13_carrier_stands_off_the_frame_flat (main has no carrier), test_round13_worn_plate_turns_as_one_and_leans_as_leatts
  (main leans +3.3 px a 100 rows), test_round13_vent_teeth_follow_the_joint_read (main rms 0.77 mm against 0.35),
  test_round13_face_foam_has_no_grazing_gloss (main's foam sets no specular, the default 0.5). Changed:
  test_round5_offsets_teeth_and_nose_ribs (the new steps), the worn rest's turn bound 20.25 +- 0.5 deg (measured on
  phase 2's shell, the search's 0.25 deg step).
- The whole rider suite in one run on the final tree (21023ae): 151 passed in 22 min 21 s, exit code 0.
- Trial merge with origin/main 73e41ef (decision 58; PROJECT.md's rows in the order 55, 57, 58): the whole rider
  suite in one run, 169 passed in 21 min 7 s, exit code 0.
