# Goggle round 14 (decision 60)

Leatt | main (3e653c9, round 13) | round 14 per item. Free goggle renders: 16 samples, goggle_views.py's studio
look, Leatt's see-through lens VLT (iso55 0.78, the white ISO 0.7, others 0.83). Round 14's plates at each photo's
solved turn (iso55 56.1 deg, the white ISO 56.0, phr 65.4, the Forge front 54.6; the near plate at its stop, 16.0;
phyb 50), no post in any view; main's at 64 and 76.5 with its post. Worn: Leatt's Pinata kit iso-right through
helmet.PRINT_CAMS, 16 samples. His photos 07 and 09: head_closeups.py p07 and p09 in the daylight rig on rider
blends built with main's and round 14's gear, the photo's crop at 4x. Ledger: research/rider-ledger/goggle.md
section 17.

## Crops
- 01a, 01b (item 1b): the C in the Pinata ISO and the white ISO at 3x. The C reads again: two windows, the strap's
  teal in the lower one (1680 to 1685 px against Leatt's lens post, Leatt 1679 to 1683), the ball pin, a satin tone
  (L 40 to 43, Leatt 43; slightly red). The frame's far end was rebuilt so the C is not behind it (below).
- 01c (item 1b): phr (his Royal) at 3x. Leatt: a 7 px black band (1595 to 1602), the red frame end (1602 to 1617), the
  strap in the gap (1617 to 1630), the C (1630 to 1675). Ours, against Leatt's lens post: the black band 4 to 5 px, the
  red frame end 2 to 3 px, the gap with the strap's teal (1619 to 1621 at the gap's middle), the C from 1627 to 1630
  (its inner edge) to 1660. Beyond the C our plate's LEATT print shows where Leatt shows background.
- 01d (item 1b): the Forge front at 3x. Its camera spreads the goggle 12 % wide (Leatt's lens posts 542 px apart,
  ours 606), so our whole far end sits about 30 px out. Refitting the camera to the lens posts (scratch
  cams_frg14b.json) left the posts 25 and -35 px off and made the outline worse (p50/p90 2.0/10.2 to 4.0/14.0 px):
  not adopted. Against the posts the C's place holds.
- 01e (item 1d, not done): the back view phyb at 2x. Leatt's strap wraps round the C (a loop) and the C's arms run
  into the frame; ours stands off the frame and the free goggle has no strap.
- 01f: iso55 at 1:1, unaligned: the C with its windows, the teal and the pin, no post, no featureless slab.
- 02a (item 2): the near end in iso55 at 1:1. No dark strip through the lens. The near C's arms show over the frame's
  top and bottom at the left (Leatt's near end shows only its black edge there).
- 03a (item 3): the plate in the Pinata iso-right at 2x at the empty helmet's placement: Leatt | main (turn 0) |
  round 14 (the plate rests at its stop, 16.0 deg; the strap leaves it 1.74 deg inwards). Back edge 760.4 / 752.6 px
  at rows 860 / 980 (Leatt 764 / 751). On him the plate rests on the shell at 16.75 deg.
- 05a (item 5): the vent teeth in the white ISO at 5x: the 48.5 mm step over about 6 columns (Leatt 6).
- 06a to 06d: his photos 07 and 09 (main | round 14): no sky flecks through the near carrier in 07, as his photo.

## The far end's rebuild (item 1b)
- SIDE_LIP_DROP 6 mm: the frame's face on the pillars comes down towards the curled lens, its bevel shrinking with
  the wall (round 12's lean kept, so no black strip on the near side). Round 10's clip slots are gone
  (CHASSIS_SLOTS empty): they were the C's windows.
- The C refitted on the plate against the new frame's signed distance (visibility in the cost): 1.35 px rms, 3.7 at
  most (the Forge front's inner edge), the near C 0.28 mm clear of the frame; the stop 16.0 deg (13.7 before).
- iso55's offset (one C for the CAD and the photos): our raw iso55 sits about +5 px from Leatt's (the camera's;
  against the lens post the C is within 1 to 2 px of Leatt's).

## The post (item 1c)
- One goggle, no post, in every view, free and worn (no switch for it any more). Damien's goggle gets none: his
  photos 07 and 09 show nothing beyond the C at that end (08 is too small to tell); Leatt's Pinata kit photos (the
  iso-right at the plate's front) and the 2022 back photo (phyb) show none; the CAD of his SKU (iso55) and the white
  ISO show none; retailers list the Velocity 5.5 Iriz's box as the goggle, a tear-off pack and a soft bag, no post
  or clip (altitude-sports.com, chromeburner.com, competitivecyclist.com). Only Leatt's Royal (phr) and Forge front
  photos show one.

## Still not right
- Outlines: the drop raised the model-to-photo p90 in iso55, phy and the white ISO (table below). The cause: a 6 px
  band of frame between our lens end and the C on mid rows, about 8 mm from Leatt's outline. Without the drop the
  C is hidden again (below about 6.6 mm of drop), and above about 2.5 mm the metric rises: no drop gives both.
  The cameras disagree here too: against the posts our lens end is 8 px too long in phr and 8 px too short in iso55.
- phr: the red frame end is 2 to 3 px (Leatt 15), and the plate's print shows beyond the C (phr, the Forge front).
- The C's arms that run into the frame at its top and bottom (Leatt's, all views; the exploded view moulds the C on
  the frame) are missing: background shows there in iso55 and phr.
- The C has a slight red tint.
- Item 1d (phyb's strap loop) and item 6 (the Forge back-strap sheet) not done.

## Outlines
- p90, model to photo, mm (main 3e653c9 in brackets): iso55 5.68 (4.08), phy 6.48 (3.84), phr 2.89 (3.95), the
  white ISO 6.55 (4.25). Round 14 before the rebuild: 3.92, 3.51, 3.60, 3.89.

## Checks
- Blender 5.2.0 (Damien's): iso55 through goggle_views from the final build: exit 0, pixel for pixel the same as
  5.2.3 (mean difference 0.00).
- New tests, each failing on main: test_round14_carrier_rides_on_the_plate,
  test_round14_outrigger_front_open_but_its_arms, test_round14_one_goggle_no_post, test_round14_c_stops_on_the_frame,
  test_round14_c_windows_open_to_the_strap, test_round14_strap_in_phrs_gap, test_round14_carrier_satin,
  test_round14_teeth_steps_crisp, test_round14_strap_pull_and_plate_rest_agree,
  test_round14_goggle_views_his_photos_take_their_exposure_and_tint.
