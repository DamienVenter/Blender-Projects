# 2026-11-10: bike v0.3, plastics pass (stock Honda, no graphics)

Chunk 1 of the exact-shape pass ("start with the plastics"). Built by `scripts/bike/plastics.py` through the
calibrated cameras of `scripts/bike/cams.py`; `build_bike.py ... stock bike_v2`.

| File | What it shows |
|---|---|
| `plastics_vs_honda.jpg` | Honda's five studio photos beside Cycles renders from the same five cameras, with scores |
| `flat_check.jpg` | The same five views in flat material colours (what `compare.py` scores) |
| `closeups.jpg` | Close-ups of the shroud's leading edge and the tail (surface quality) |
| `hero_left.jpg`, `hero_right_rear.jpg` | Three-quarter renders |
| `scores.json` | Overlap with each photo: whole silhouette and red plastics; error per region for the profiles |
| `dimensions.json` | Model against Honda's spec sheet |

## Scores (overlap with Honda's photos, red plastics; start of the pass to end)
| View | Start | End | Whole silhouette |
|---|---|---|---|
| Left | 0.78 | 0.87 | 0.85 |
| Right | 0.80 | 0.88 | 0.85 |
| Front | 0.52 | 0.75 | 0.84 |
| Rear | 0.40 | 0.53 | 0.83 |
| Top | 0.76 | 0.82 | 0.86 |

## Against the spec sheet (mm)
| Dimension | Honda | Model | Note |
|---|---|---|---|
| Wheelbase | 1483 | 1483 | built in |
| Overall length | 2179 | 2161 | tyre to tyre; wheelbase plus both measured tyre radii is 2160: Honda's extra 18 mm is unexplained |
| Overall height | 1262 | 1269 | top of the bars |
| Seat height | 955 | 967 | follows the studio photo, which shows the suspension extended |
| Ground clearance | 330 | 333 | |
| Overall width | 827 | 866 | FAULT: bars too wide in the model; fix with the bars pass (test is marked xfail) |

## Measured and tied to the photos now
Shrouds (profile outline, plan width 0.200 m agreeing between top and front photos, rounded shoulder, top decks,
two-layer leading edge), side panels and black lower panels (profile outlines, plan width), seat, rear fender (top
line, flanks, plan, flare into the panels), front fender (arched section proved from three photos, plateau, rear
flap between the fork legs), number plate (front photo), fork guards (inboard of the tubes), inner mudguard and mud
flap (rear and left photos), radiators inside the shrouds.

## Still crude in the plastics (second pass)
- No creases or feature lines on any panel; side panel cross-sections are estimated (the rear photo cannot show them).
- Under the tail: the red walls with the two bolts are one flat plate at an estimated x.
- Number plate: no raised centre panel, no hose guide (its right half is mirrored from the left).
- Shroud: the inner wall and the skin are one stepped surface; the gap between them at the lower tip is closed.
- Seat: plain loft, same red as the plastics.
- The side panel's rear edge is a straight cut at the fender root.

## Not plastics, seen during this pass
Bars 39 mm too wide; fork tubes measure 48 to 53 mm where 60 was assumed (now 51); lower triple clamp is a plain
bar; muffler top too low against the left photo; engine, frame cradle and subframe are still first-pass shapes.
