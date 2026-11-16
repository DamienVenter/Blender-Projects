# Goggle round 14 (decision 60)

Leatt | main (3e653c9, round 13) | round 14 per item. Free goggle renders: 16 samples, goggle_views.py's studio
look, Leatt's see-through lens VLT (iso55 0.78, the white ISO 0.7, others 0.83). Round 14's plates at each photo's
solved turn (iso55 56.1 deg, the white ISO 56.0, phr 65.4, the Forge front 54.6; the near plate at its stop, 16.0;
phyb 50), no post in any view; main's at 64 and 76.5 with its post. Worn: Leatt's Pinata kit iso-right through
helmet.PRINT_CAMS, 16 samples. His photos 07 and 09: head_closeups.py p07 and p09 in the daylight rig on rider
blends built with main's and round 14's gear, the photo's crop at 4x. Pixel positions below are against Leatt's lens
post (ours raw + 3.4 px in phr, raw - 5 in iso55). Ledger: research/rider-ledger/goggle.md section 17.

## Crops
- 01a, 01b (item 1b): the C in the Pinata ISO and the white ISO at 3x. Two windows, the strap's teal in the lower
  one, the ball pin, the satin carrier (row 960: rgb 46/36/39, slightly red, against Leatt's 48/47/48). The
  outline's end 1704 to 1705 (Leatt 1704 to 1705).
- 01c (item 1b): phr (his Royal) at 3x. Leatt, row 860: black 1595 to 1600, the red frame end 1601 to 1611, the gap
  1613 to 1626, the C 1628 to 1672. Ours: the frame's dark face 1589 to 1610, its red edge 1612 to 1614, the gap
  1616 to 1625, the C 1627 to 1652, then the plate's edge and print to 1671. Row 1060: Leatt's gap 1620 to 1627, ours 1618 to 1630; the outline's end 1677,
  ours 1674. The strap's teal shows in our gap at row 990 (1621 to 1627). Our frame end stands where Leatt's does
  but reads black (22 px) with a 2 to 3 px red edge, where Leatt's is 3 to 7 px black and 11 to 14 px red.
- 01d (item 1b): the Forge front at 3x. Its camera spreads the goggle 12 % wide (Leatt's lens posts 542 px apart,
  ours 606), so our whole far end sits about 30 px out. Refitting the camera to the lens posts (scratch
  cams_frg14b.json) left the posts 25 and -35 px off and made the outline worse (p50/p90 2.0/10.2 to 4.0/14.0 px):
  not adopted.
- 01e (item 1d, not done): the back view phyb at 2x. Leatt's strap wraps round the C (a loop) and the C's arms run
  into the frame; ours stands off the frame and the free goggle has no strap.
- 01f: iso55 at 1:1, unaligned: the C with its windows, the teal and the pin, no post. Raw, our C stands about 5 px
  further out than Leatt's (the camera's offset; against the post the outline's end matches).
- 02a (item 2): the near end in iso55 at 1:1. No dark strip through the lens. The near C's arms show over the frame's
  top and bottom at the left (Leatt's near end shows only its black edge there).
- 03a (item 3): the plate in the Pinata iso-right at 2x at the empty helmet's placement: Leatt | main (turn 0) |
  round 14 (the plate rests at its stop, 16.0 deg; the strap leaves it 1.67 deg inwards). Back edge 760.3 / 752.4 px
  at rows 860 / 980 (Leatt 764 / 751). On him the plate rests on the shell at 16.75 deg.
- 05a (item 5): the vent teeth in the white ISO at 5x: the 48.5 mm step over about 6 columns (Leatt 6).
- 06a to 06d: his photos 07 and 09 (main | round 14): no sky flecks through the near carrier in 07, as his photo.

## The far end's rebuild (item 1b)
- The pillar's face comes down 4 mm towards the curled lens (SIDE_LIP_DROP; the weight along the loop dilated and
  smoothed, DROP_DILATE, DROP_SIGMA), its bevel scaled with the wall so it keeps round 12's lean. 6 mm (the first
  rebuild) narrowed the frame to 202.7 mm (spec 205 to 218; the drop runs along the lens normal, which points
  outwards at the pillar) and left phr's frame end at 1609 to 1612; 4 mm gives 205.8 mm and the frame end at 1614 to
  1619 (Leatt 1611 to 1618). Round 10's clip slots are gone (CHASSIS_SLOTS empty): they were the C's windows.
- The C refitted on the plate with visibility in the cost (the 6 mm frame's signed distance): 1.35 px rms, 3.7 at
  most; the stop 16.0 deg (13.7 before). At 4 mm the near C still clears the frame at the stop (none of its surface
  inside at 16.0, 19 points at 15.3, 128 at 13.7); the far C was not refitted.
- The plate's anchor and length are taken from its outer face: the inner face starts CAR_INNER_CUT (6.5 mm) behind
  the C, which had moved the strap's anchor to 12.3 mm from the plate's back (the rest and weave tests caught it).
- iso55's offset (one C for the CAD and the photos): about +5 px raw, the camera's.

## The post (item 1c)
- One goggle, no post, in every view, free and worn (no switch for it any more). Damien's goggle gets none: his
  photos 07 and 09 show nothing beyond the C at that end (08 is too small to tell); Leatt's Pinata kit photos (the
  iso-right at the plate's front) and the 2022 back photo (phyb) show none; the CAD of his SKU (iso55) and the white
  ISO show none; retailers list the Velocity 5.5 Iriz's box as the goggle, a tear-off pack and a soft bag, no post
  or clip (altitude-sports.com, chromeburner.com, competitivecyclist.com). Only Leatt's Royal (phr) and Forge front
  photos show one.

## Still not right
- Outlines: model to photo p90 above main's in iso55, phy and the white ISO (table below). The misses lie in
  iso55's x 1640 to 1680 (rows 800 to 1120) and phy's x 1600 to 1680: our frame's dark face between the lens's end
  and the C (iso55 row 960: 1652 to 1669) where Leatt's shows the lens to 1655 and the C from 1658. The face covers
  the lens's last few mm in both views (it starts at 1589 in phr, Leatt's black at 1595; at 1650 to 1652 in iso55,
  Leatt's C at 1658); lowering it further (6 mm) narrowed the frame below the spec, because at the pillar the face
  is the frame's side.
- phr's frame end: right place, wrong colour (above). Colouring the face's outer half in the frame's colour (a
  trial) gave black 12 to 15 px and red 7 to 9 px, but put a 6 to 7 px pink band with specular flecks in iso55 where
  Leatt's C is: not adopted.
- Between our C and its outer edge, phr and the Forge front show the plate's edge and print (the white LEATT
  letters) where Leatt's C has its outer bar (grey 106).
- iso55: the upper window 13 px wide at row 870 (Leatt 25), with the plate's front end lit in it (Leatt's is dark);
  at row 800 the C's top face reads light (155 to 226) where Leatt's is dark (21).
- The C's arms that run into the frame at its top and bottom (Leatt's, all views) are missing.
- The C reads slightly red. In the white ISO (01b) it reads 62 at row 960 where Leatt's reads 24 (main's 26):
  Leatt's white goggle has a darker C than the Pinata (48 there under the same CAD light); ours keeps the Pinata's.
- Item 1d (phyb's strap loop) and item 6 (the Forge back-strap sheet) not done.

## Outlines
- p90, model to photo, mm: iso55 5.32, phy 5.28, phr 2.89, the white ISO 5.85. Main 3e653c9: 4.08, 3.84, 3.95, 4.25.
  Round 14 before the rebuild: 3.92, 3.51, 3.60, 3.89; the 6 mm drop: 5.68, 6.48, 2.89, 6.55.

## Checks
- Blender 5.2.0 (Damien's): iso55 through goggle_views from the final build: exit 0, pixel for pixel the same as
  5.2.3 (mean difference 0.00).
- New tests, each failing on main: test_round14_carrier_rides_on_the_plate,
  test_round14_outrigger_front_open_but_its_arms, test_round14_one_goggle_no_post, test_round14_c_stops_on_the_frame,
  test_round14_c_windows_open_to_the_strap, test_round14_strap_in_phrs_gap, test_round14_carrier_satin,
  test_round14_teeth_steps_crisp, test_round14_strap_pull_and_plate_rest_agree,
  test_round14_goggle_views_his_photos_take_their_exposure_and_tint.
