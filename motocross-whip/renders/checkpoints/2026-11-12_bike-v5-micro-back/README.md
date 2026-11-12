# Bike v0.5: micro-detail pass, back of the bike (2026-11-12)

Damien (2026-11-11): "Take a closer look at the more minor details, especially at the back of the bike, and perfect
them ... as if each tiny little component is a separate build all on its own."

Each component was its own build: anatomy, references, numbers, model, then a check with `pair.py` (Honda's photo
beside the model through the same calibrated camera) and close-ups beside the detail photos. The record of every
component (what was measured, from which pixels, what is still different) is in `research/detail-ledger/`
(`wheels.md`, `chassis.md`, `plastics.md`, `front.md`).

## The sheets here (Honda's photo left, the model right, same camera)
- `01_left_rear_wheel.jpg`, `02_right_rear_wheel.jpg`: tyre knob by knob, sidewall marks, rim decals, 32 spokes,
  sprocket windows, chain plates, axle block, chain guide, rear disc holes, caliper and guard.
- `03_right_muffler.jpg`, `05_rear_end.jpg`: the can (octagonal, pressed cap and nose, brushed), raised to the photo.
- `04_right_pivot_pedal_peg.jpg`: frame casting, pivot nut, master cylinder casting, pedal, peg.
- `06_rr34_rear_end.jpg`, `07_lr34_seat_fender.jpg`, `08_top_seat_fender.jpg`: seat, fender, side panels.

## Numbers
- Silhouette overlap with Honda's photos (`scores.json`): left 0.886, right 0.877, front 0.891, rear 0.903,
  top 0.886 (v0.4: 0.876, 0.865, 0.877, 0.892, 0.873).
- Length 2178 mm (Honda 2179), width 827 (827), bar top 1256 and hand controls 1274 (Honda 1262), seat 978 and belly
  346 (Honda 955 and 330: the photo bike stands high).
- 43 parts, 890,012 vertices. Audit (`audit.json`): deepest contact 1.0 mm (peg on frame), nothing floating.
  129 tests pass.

## Still different (next rounds)
- Where the seat's tail, the rear fender and the side panel meet: lumps and a step the photo does not have.
- Brake pedal pivot (a hex socket bolt in the photo), the peg's open cage and hinge bracket, the frame's MC tab
  edge, the header's colour (silver with a heat tint near the bend, not bronze all along), the subframe tubes.
- The rear axle sits 5 to 11 mm higher in Honda's photos than the model's datum (studio sag): kept, see the skill.

Blend: `blend/bike_v5.blend` (textures packed; reopened in Blender 5.2.0). Viewer: version 7 of the bike viewer.
