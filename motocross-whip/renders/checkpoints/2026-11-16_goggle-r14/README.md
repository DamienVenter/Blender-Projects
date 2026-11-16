# Goggle round 14 (decision 60)

Leatt | main (3e653c9, round 13) | round 14 per item. Free goggle renders: 16 samples, goggle_views.py's studio
look, Leatt's see-through lens VLT (iso55 0.78, the white ISO 0.7, others 0.83). Round 14's plates at each photo's
solved turn (iso55 and the white ISO 56.0 deg, phr 65.2, the Forge front 54.4; the near plate 13.7), the post in phr
and the Forge front only; main's at 64 and 76.5. Worn: Leatt's Pinata kit iso-right through helmet.PRINT_CAMS, 16
samples. His photos 07 and 09: head_closeups.py p07 and p09 in the daylight rig on rider blends built with main's
and round 14's gear (both before decisions 59 and 61, so one look), the photo's crop at 4x. Ledger:
research/rider-ledger/goggle.md section 17.

## Crops
- 01a, 01b (item 1): the C in the Pinata ISO and the white ISO at 3x. One C on the plate fits the four views'
  landmarks at 1.25 px rms (each view against Leatt's lens posts), but it is not what you see here: its face lies
  13.7 to 18.6 mm behind the frame's black chassis wall (round 12's 6.9 mm pillar wall) up to its outer corner. The
  two "windows" are the frame's clip slots (round 10), the C reads L 16 to 28 (Leatt 43) and round 13's teal in the
  lower window is gone. Only the C's outer bar shows, to 1706 px at row 820 and 1715 at row 1090 (Leatt 1704 to
  1705): our plate's back end leans out about 5 px going down.
- 01c (item 1): phr (his Royal) at 3x. Leatt: a 7 px black band (1595 to 1602), the red frame end (1602 to 1617),
  the strap in the gap (1617 to 1630), then the C (1630 to 1675, windows 1638 to 1658), the post out of its outer
  edge to 1698. Ours: the chassis wall with slots over 1600 to 1648, a thin red strip, then the C, our plate's print
  beside it, the post to about 1701. The wall stands where Leatt's frame end, gap and C are.
- 01d (item 1): the Forge front at 3x. Its camera (fitted to the outline only, round 6) spreads the goggle 12 % wide
  (Leatt's lens posts 542 px apart, ours 606): our whole far end sits about 30 px out (the C to 1738 px against 1708,
  the post's tip 1778 against 1735, our far lens post 1683 against 1656). Against the posts the C's place holds; the
  chassis wall covers it as in phr.
- 01e (item 1): the back view phyb at 2x. Not in the fit. Leatt's strap wraps round the C (a loop); ours is a solid
  block, and the free goggle has no strap.
- 01f: iso55 at 1:1, unaligned. No post in the CAD view now (round 13's stood 17 to 20 px out); the far end's dark
  band is the chassis wall.
- 02a (item 2): the near end in iso55 at 1:1. Main's dark strip through the lens at 1000 to 1040 px is gone (the
  near C on the plate sits behind the frame's near end).
- 03a (item 3): the plate in the Pinata iso-right at 2x at the empty helmet's placement: Leatt | round 14 with the
  plate at its stop (13.7 deg, the strap's span 2.11 deg outwards) | round 14 with the strap's rest (14.98 deg, in
  line). The plate's back edge 758 / 751 px at rows 860 / 980 (Leatt 764 / 751); the strap's print still ends square
  at about 761 px over the plate's back (3 to 10 px) and lies lower than Leatt's. The two turns look nearly alike.
- 05a (item 5): the vent teeth in the white ISO at 5x: the 48.5 mm step over about 6 columns (1290 to 1296 px; Leatt
  6, main 1282 to 1300).
- 06a to 06d: his photos 07 and 09 (main | round 14). In 07 main shows the sky through the near carrier's windows (the
  blue flecks); round 14 shows none (rays through them meet the outrigger and the strap's slot), as his photo. The
  black spot at the C is the lens post.

## Still not right
- Item 1: the C on the plate is hidden behind the frame's far-end chassis wall in iso55, the white ISO and the Forge
  front (and its inner quarter in phr). Refitted with visibility the fit needs the pivot inside the frame (rms 4.01
  px, at most 8.9, phr's turn 14.1 deg): no goggle. The photos show no such wall; the next step is the frame's far
  end to the photos, then the C refitted with visibility. In the CAD views this round is a step back from round 13
  (windows and teal).
- Item 3: the strap shows over the plate's back by 3 to 10 px and lies lower than Leatt's at the empty placement.
- Item 4: the lens end's bow at iso55 rows 840 and 1090 is the chassis wall seen through the lens's grazing end
  (Leatt's corners show his frame there); not changed.
- Item 6 (the Forge back-strap sheet) not done.

## Outlines
- p90, model to photo, mm (main 3e653c9 in brackets): iso55 3.92 (4.08), phy 3.51 (3.84), phr 3.60 (3.95), the white
  ISO 3.89 (4.25).

## Checks
- Blender 5.2.0 (Damien's): goggle_views' daylight, the iso55 camera as iso55 and as a view named p07 (8 samples):
  both render (exit 0); p07's darks +17.8 in blue (07's tint 0.0706); a view not named after his photos gets 0 EV
  and no tint, the look daylight() already set.
- New tests, each failing on main: test_round14_carrier_rides_on_the_plate, test_round14_outrigger_front_open_but_its_arms,
  test_round14_post_only_for_the_royal_and_forge, test_round14_c_stops_on_the_frame, test_round14_teeth_steps_crisp,
  test_round14_strap_pull_and_plate_rest_agree, test_round14_goggle_views_his_photos_take_their_exposure_and_tint.
