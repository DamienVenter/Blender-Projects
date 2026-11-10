# 2026-11-10: bike v0.4, detail pass (stock Honda, no graphics)

"Find your inconsistencies. Fix them. Add detail to every tiny bit of the bike." Every assembly rebuilt in detail by
its own module (`scripts/bike/detail_*.py`, loaded by `parts.py`), shared reference points corrected, and the whole
bike audited for parts cutting each other (`audit.py`). Build: `build_bike.py ... stock bike_v3`.

| File | What it shows |
|---|---|
| `detail_vs_honda.jpg` | Honda's five studio photos beside Cycles renders from the same five cameras, with scores |
| `closeups.jpg` | Nine close-ups: shroud, engine left and right, pivot and chain, cockpit, rear wheel, front wheel, tail, seat |
| `hero_left.jpg`, `hero_right_rear.jpg` | Three-quarter renders |
| `scores.json` | Overlap with each photo: silhouette, red plastics, black and metal parts; error per region |
| `audit.json` | Every contact between parts (face pairs, depth, where) and loose pieces |
| `dimensions.json` | Model against Honda's spec sheet |

## Overlap with Honda's photos (start of the pass to end)
| View | Silhouette | Red plastics | Black parts | Metal parts |
|---|---|---|---|---|
| Left | 0.849 to 0.876 | 0.87 to 0.898 | 0.705 to 0.759 | 0.577 to 0.635 |
| Right | 0.852 to 0.865 | 0.88 to 0.891 | 0.721 to 0.750 | 0.618 to 0.654 |
| Front | 0.836 to 0.877 | 0.75 to 0.798 | | |
| Rear | 0.829 to 0.892 | 0.53 to 0.627 | | |
| Top | 0.861 to 0.873 | 0.82 to 0.861 | | |

## Against the spec sheet (mm)
| Dimension | Honda | Before | Now | Note |
|---|---|---|---|---|
| Wheelbase | 1483 | 1483 | 1483 | built in |
| Overall length | 2179 | 2161 | 2176 | tyres are 359.3 and 334.3 mm in radius at the knob tips, not 350.5 and 326.4 |
| Overall width | 827 | 866 | 827 | bars |
| Overall height | 1262 | 1269 | 1268 | highest point of the bars and their controls |
| Swingarm, pivot to axle | 585.2 | 579 | 584.5 | pivot cap cast on its own plane |
| Footpeg height | 422 | 413 | 427 | rear photo and left photo differ by 12 mm; the mean |
| Seat height | 955 | 967 | 975 | follows the photos; not explained |
| Ground clearance | 330 | 333 | 346 | lowest outline in the photos is 333 if on the centre line, 346 if the near cradle rail (modelled) |

The ground is 7.9 mm lower than before (bigger tyres), which is why seat and clearance read higher.

## Audit
38 parts, 298,510 vertices. 5 contacts, all 1.5 mm deep or less (bolts and edges seated in their mounts):
shroud decks on shrouds, fork guard on the caliper bracket, rear fender on the seat, footpegs on the frame, caliper
on the fork lug. No loose pieces. At the start of the pass: 40 clashes up to 79 mm deep and 347 loose pieces.

## Measured and estimated
- Measured from the photos: every side outline, tube diameters, bolt positions on the engine covers, spoke lacing,
  tread pitch, disc scallops, sprocket windows, chain line and chain runs, pivot, countershaft, bar ends, pad, seams
  and creases of the plastics, tyre radii.
- Estimated (hidden or seen from one side only): engine widths, intake, hose routes, frame spar plan, subframe,
  header elbow and mid pipe, muffler top under the panel, front hub, caliper shapes, rim depths of the plastics,
  hidden mounts, cable ends.

## Known faults, left for later
- Seat 20 mm and belly 16 mm above the spec sheet while length, width and swingarm agree: cause not found.
- Bar pad: Renthal's emblem and the lettering on its top are missing (graphics pass). Rims and tyres carry no lettering.
- Shroud: vent pocket has a floor and sits 14 px low, louvre gap at the lower tip closed, roof slot not modelled.
- Under the tail the inner wall is simple; the rear fender has no flange to it.
- Cylinder and head are plain castings; tank holds 4.8 L against 6.3; overflow tube stops above the skid plate.
- Chain: 112 links on the photo's chain line, free links 1.1 % long (the real count was not verified).
- Rear tread's three-pitch pattern, caliper guard, radiator cap side: not done or estimated.
- Honda's photos disagree with each other by up to 14 mm at the bar ends and 12 mm at the footpegs; means are used.
