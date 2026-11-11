# Detail ledger: wheels, tyres, final drive, rear brake (`scripts/bike/detail_wheels.py`)

Micro-detail pass of 2026-11-11 (brief: one component at a time, each with references, numbers, model and check).
Coordinates: axle-line frame, metres. Check images are in the agent's scratch folder
(`/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/agents/micro/wheels/`,
written `SCRATCH/` below); they are not committed.

Tools written for the checks (scratch): `edge.py` (per-row outline of photo and model in a `pair.py` box, the
difference in pixels), `sbs.py` (images side by side), `cu.sh` (close-ups), `chk_tyre.py` (tyre mesh numbers).

## 1. Rear tyre tread (Pirelli Scorpion MX32 Mid Soft 100/90-19)

### Anatomy (what shows at 30 cm)
- Carcass crown and shoulders under the knobs; groove floor between rows.
- 46 rows round the tyre. Per row: a centre knob across the crown split along the centre line by a V slit (full
  length, part depth: the halves join below it); an intermediate knob each side in the same row, its outer-leading
  corner cut at a slant; half a pitch on, a shoulder knob each side (plain tapered block); a low pad joining the
  row's three in-row knobs (a faint arc on the floor between rows, longest at the centre).
- Knob walls drafted (narrower top), top edges rounded, corners rounded in plan, a fillet at each knob's root.
- Mould vent hairs ("spews"): thin whiskers at the knobs' top corners (DR13: one at each corner of the shoulder
  knobs, pointing up) and on the shoulder knobs' outer faces (475832).
- Finish: black rubber with a dull sheen where lit (studio photos); new-tyre purple bloom in DR13 (outdoor sun) and
  a red centre line in 475832 (outdoor press bike) are not on the studio bike: left off (REAR and lr34 show
  neither).

### References
- REAR studio photo 475598: rows 1440..2040, cols 1880..2120 (whole tread from behind); zoom rows 1560..1700 cols
  1920..2080 (one row: centre knob 44 px = 28 mm at the top with its slit, intermediates, shoulders half a pitch
  on, the floor arcs).
- LEFT studio photo 475600: polar scan of the outline round the rear axle (scan_left.npy: tall plateaus every 7.8
  deg = 46 rows, 4.2 deg wide; low plateaus half a pitch on); zoom cols 3250..3400 rows 1480..1680 and cols
  3300..3400 rows 1500..1620 (one pitch side-on: the in-row knob's outer face 25 px = 19.5 mm long, the row 29 px =
  22 mm, the shoulder's face 25 px).
- RIGHT studio photo 475596: the same scan (46 rows).
- lr34 475599 cols 3060..3260 rows 1560..1760 and rr34 475597: shoulder and intermediate knobs seen from outside.
- 475832 (rear tyre and chain): crops 1100..2300 x 800..1900 and 1300..2600 x 1700..2732; slit zoom 1380..1880 x
  1050..1450 (the slit is a V groove; the halves join below; vent hairs on the knob edges).
- DR13 (Dirt Rider rear rim and tyre): shoulder knobs side-on (plain tapered blocks, four spews on each top).
- Pirelli's product images (web/README.md): flat view of the tread (plan shapes: intermediates with a slanted outer
  end; their shoulders have a notch that the stock tyre does not have), the rear from behind.

### Numbers and sources
| Item | Value | Source |
|---|---|---|
| Rows round the tyre | 46 | LEFT and RIGHT polar scans, 7.83 deg a row |
| Tip radius | 334.3 mm | shared `R_REAR` (both side photos) |
| Groove floor (crown) | 317.8 mm (knob 16.5) | side scans: floor 317..319 |
| Centre knob | 22 x 30 mm at the root, 28 mm wide at the top | REAR 44 px at the top; LEFT zoom row length 22 mm |
| Centre slit | 1.5 mm at its floor, 9 mm above the carcass; about 5 mm at the top (V) | REAR zoom (dark wedge 8 px wide at the top); 475832 (halves join below) |
| Intermediate | t 16.5..31.5 mm, 19 mm long, corner cut 6.5 x 5.5 mm | REAR cols 1947..1977 (y 15..34 mm), LEFT zoom 19.5 mm |
| Tip envelope | R at the crown, R - 9 mm at t 31.5 mm | `edge.py` on LEFT: nothing passes the centre tips (perspective: +0.28 px per mm of y, 1.28 px per mm of radius) |
| Shoulder | t 28..47 mm, 16 mm long, inner top corner r 317.5, outer end 12 mm high | REAR cols 1929..1959 (y 26..45.5); LEFT low plateau col 3365 |
| Tyre width | 92.2 mm | shared measurement 91.5 (REAR rows 1750..1975), test +-3 mm |
| Draft | 4 deg centre, 5 deg others; slit walls 7.5 deg | EST (moulded rubber) |
| Edge round, root fillet | 0.9 mm, 1.0 mm | EST (MICRO.md: rubber 0.5 to 1 mm) |
| Pad | 1.2 mm high, 24 mm long at the edges, 33 at the centre | REAR floor arcs; EST height |
| Vent hairs | 0.45 mm thick, 2.5..5 mm long | 475832, DR13; EST size |

### What was built
- `carcass()`: the carcass as one whole grid (no holes); `Knob` maps a knob's plan (s along the tread, t across the
  section, z height) onto the wheel with a lean between radial and the surface normal; `_knob()` builds any knob
  from a plan polygon: drafted walls (per-vertex draft for the slit), root flare sunk 0.8 mm into the carcass,
  quarter-round top edge, Delaunay top cap; `rear_tread()` lays the rows; `_spews_at()` / `_spew()` the hairs.
- Rear tyre 89.5k vertices (was about 20k).

### Checks
- `SCRATCH/p_left4.jpg` + `p_left4.jpg.d/edge.png`: LEFT outline, model minus photo: median 2 px, the tall and the
  low plateaus within 1 to 3 px (first try was +8 px: the intermediates stood too tall).
- `SCRATCH/p_right4.jpg` + edge: RIGHT outline 4 to 5 px further out than the photo on both plateaus (the right
  photo's tyre is about 4 mm smaller than the left's; the shared radius is their mean).
- `SCRATCH/p_rear5.jpg`, `p_lr5.jpg`, `p_rr5.jpg`: rear, rear-left and rear-right three-quarter pairs.
- `SCRATCH/r5/render_cu_832.png` beside 475832, `SCRATCH/r5/render_cu_dr13.png` beside DR13.

### Still different, and why
- In the REAR photo the rows stand 66.5 px apart near the tyre's rear-most point (rows 1527..1931, cols 1980..2020);
  the model through the same camera puts them 70 px apart. The side scans fix the row count at 46 (angles do not
  depend on scale), so the REAR camera's scale at the rear tyre is about 6 % high: by the same ratio the tyre would
  be about 97 mm wide instead of 91.5, and the front tyre shows the same 6 % in the FRONT photo. Not changed here
  (the shared width, swingarm faces and chain line were all measured through that camera): reported to the
  coordinator.
- lr34: the model's tyre and rim sit about 13 px left of the photo's (camera, not shape: rim and knobs move
  together).
