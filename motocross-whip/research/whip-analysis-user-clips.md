# Whip analysis: Damien's reference clips (2026-11-06)

Purpose: capture how Damien's whip moves, so the animation matches his style.
The bike look and kit in these clips are NOT used (per Damien). Only the motion.

## Source clips
All three: WhatsApp re-encodes, 478x850 portrait, 30 fps (clip 3 is slightly variable frame rate).
Frame numbers below are 1-based file numbers; times are presentation timestamps.

| File | Camera | Frames | Notes |
|---|---|---|---|
| `reference/user-clips/clip1_back-and-front_2026-11-06_102139.mp4` | Shot A: behind the ramps, low, left of the takeoff. Cut at about f95. Shot B: at the bottom of the landing, looking up at the knuckle | 197 | Only clip that shows the return and the landing (front view) |
| `reference/user-clips/clip2_back-close_2026-11-06_102401.mp4` | Behind and close to the ramp, looking up | 104 | Clearest view of the lay-down and peak |
| `reference/user-clips/clip3_back-wide_2026-11-06_102401k.mp4` | Behind the ramps, wider | 126 | Best for timing from lip to the landing crest |

Contact sheets (true frame numbers and timestamps) are in `reference/user-clips/sheets/`.
Regenerate with `tools/contact_sheet.sh`.

## Whip direction
Rear wheel goes out to Damien's **right**. Seen from behind the ramp, the nose swings to image-left and the tail to image-right. Seen from the landing (front), the rear wheel is on image-left.

## Timeline (t = 0 at lip departure)
Measured mainly on clip 3 (lip departure at about f29 / 0.95 s), cross-checked with clips 1 and 2.
Accuracy is about plus or minus 0.05 s (30 fps, motion blur, compression).

| Phase | t after lip (s) | What happens | Best frames |
|---|---|---|---|
| 1. Leave lip, initiate | 0.00 to 0.10 | Bike leaves the steel lip pitched up at roughly the lip angle. The whip starts immediately: bars and hips push the bike over; the rear starts to swing right. No dead time on the lip | clip3 f28 to f31, clip2 f27 to f31 |
| 2. Lay it down | 0.10 to 0.30 | Bike rolls toward flat and yaws so the rear swings out right. Rider's torso stays fairly upright and facing forward; body weight shifts left over the front | clip2 f31 to f35, clip3 f31 to f37 |
| 3. Peak flat | 0.30 to 0.50 | Bike close to horizontal (fully laid down), front fender out to Damien's left, rear high to the right. This is the "money" moment and is held, not passed through | clip2 f35 to f43, clip3 f37 to f43 |
| 4. Stand it back up | 0.50 to 0.90 | Bike rolls back to upright while staying yawed (crossed up). The nose drops; from behind the bike looks vertical with the front wheel at the bottom | clip2 f45 to f61, clip3 f46 to f58 |
| 5. Hold the cross-up | 0.90 to about 1.75 | Bike stays crossed up under the rider (seen almost in profile from both cameras) while the torso faces forward. Pitch eases from steep nose-down toward the landing slope angle | clip3 f58 to f82, clip1 front f130 to f148 |
| 6. Straighten and land | about 1.75 to 2.05 | Bike is pulled straight late, in the last moments before touchdown. It lands nearly straight with a small residual angle, front wheel marginally first, and Damien rides away down the landing | clip1 front f151 to f160 |

Estimated total airtime: about 2.0 to 2.2 s. Clip 3 loses the rider behind the landing crest at about 1.9 s after the lip, and touchdown follows shortly after.
This is consistent with a gap around 70 to 85 ft from a steel FMX ramp, so the 75 ft brief fits. To be confirmed with the physics work in `fmx-ramp-physics-whip.md`.

## Style notes (the details to reproduce)
- Initiation is instant and aggressive off the lip, not a slow build.
- The lay-down is deep: the bike gets genuinely flat at the peak.
- The return happens in two clear stages: un-roll first, un-yaw later. The bike spends a long time crossed up after standing back up. This is what makes the whip look held and stylish.
- The straighten is late and quick, just before touchdown.
- Torso and helmet stay oriented toward the direction of travel throughout; the twist happens in the hips and legs.

## Practice-site observations (not the final scene; KOTW 2025 is the target setting)
- A row of 4 or more steel FMX ramps of different sizes side by side, curved transitions, rust-brown expanded-metal decks with lighter (galvanised or painted) edge rails, black steel support frames.
- Flat wooden or steel approach boards at the base of the ramps.
- A tall dirt landing mound with a vegetated top and shoulders, light tan sandy soil, scattered green bushes.
- Bright sun, few clouds, dry grassland and large trees around.

## Open items
- Exact bike roll, yaw and pitch angles per frame: to be measured later by camera-matching our finished 3D bike to these frames (render the model over the footage and fit its orientation). Much more precise than eyeballing.
- Body and limb positions per phase (legs, which foot comes off the peg, arm extension) need higher-resolution or slow-motion footage.
