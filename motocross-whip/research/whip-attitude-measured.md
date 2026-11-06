# Damien's whip, measured frame by frame (2026-11-06)

Why: Damien said the demo whip was "nowhere near as big as my whip". The earlier targets were eyeballed
from steep, close camera angles (clips 2 and 3), which hide how far the bike really turns. This file
replaces those estimates with a measurement.

## Method
1. Source: clip 1 shot A (`reference/user-clips/clip1_back-and-front_2026-11-06_102139.mp4`, frames 30 to 91).
   The camera is far behind the ramps (about 25 m behind the lip, about 1.5 m high, zoomed: about 1600 px
   focal length on the 478 px wide frame). From that far the picture is close to a straight-on view from
   behind, so angles in the picture are angles in the world. Shot B of the same clip (front camera at the
   bottom of the landing) and clips 2 and 3 were used as cross-checks.
2. Tool: `scripts/analysis/attitude_overlay.py`. It draws the bike (wheels, fork, frame, plastics, bars) and a
   stick rider at a trial world attitude, seen from that camera, next to the real frame. The attitude is
   adjusted until they match. What fixes each angle:
   - the in-picture angle of the axle line (bike turning about the travel direction),
   - the wheel ellipses: round = side-on, a thin line = edge-on (how flat the bike is),
   - which side of the bike the rider is on (where the seat faces),
   - the in-picture tilt of his torso (his lean).
3. Reproduce: extract frames with `ffmpeg -i clip1_*.mp4 -vsync 0 frames/f_%03d.png`, then e.g.
   `python3 attitude_overlay.py out.jpg frames 30 -25,1,1.5,1600 40 52 64` (frame numbers alone use the
   measured table; `frame:drop:yaw:pitch:roll` tries an attitude).
4. Check: the table was built from about one frame in three and then checked against the frames in between
   (`whip-attitude-measured/overlay_*.jpg`, top row real, bottom row the measured attitude). They match.

## Angles
Bike world attitude, composed about world axes: `R = Rx(drop) Rz(yaw) Ry(-pitch) Rx(roll)`.
yaw: nose to his left +. roll: lay-down, left negative. drop: whole bike turned about the travel direction
(with the bike fully sideways this is the nose dropping). Torso lean: seen from behind, head to his left negative.
Times are seconds after the rear wheel leaves the lip (clip 1 frame 30, 30 fps).

| t (s) | frame | drop | yaw | pitch | roll | torso lean | what the footage shows |
|---|---|---|---|---|---|---|---|
| 0.00 | f30 | 0 | 0 | lip | 0 | 0 | rear wheel leaves the lip |
| 0.13 | f34 | 0 | 40 | 38 | -35 | -25 | rear swinging out right, bike leaning left |
| 0.23 | f37 | 0 | 60 | 28 | -65 | -45 | diagonal, rear wheel low right as an ellipse |
| 0.33 | f40 | 0 | 90 | 5 | -90 | -65 | flat and fully sideways, wheels edge-on, rider horizontal |
| 0.43 | f43 | 0 | 90 | 0 | -90 | -70 | held flat and level |
| 0.53 | f46 | -15 | 90 | 0 | -80 | -60 | rear starts to rise, still flat |
| 0.63 | f49 | -30 | 90 | 0 | -75 | -50 | axle line 32 deg |
| 0.73 | f52 | -41 | 90 | 0 | -70 | -45 | axle line 41 deg, still mostly flat |
| 0.83 | f55 | -56 | 90 | 0 | -55 | -30 | front wheel becoming visible |
| 0.93 | f58 | -70 | 90 | 0 | -45 | -15 | front wheel ellipse about 0.6 round |
| 1.03 | f61 | -78 | 90 | 0 | -30 | -10 | hanging nose-down |
| 1.13 | f64 | -78 | 90 | 0 | -15 | -5 | side-on, front wheel nearly round |
| 1.33 | f70 | -75 | 90 | 0 | 0 | 0 | full profile, rider upright |
| 1.53 | f76 | -58 | 90 | 0 | 0 | 0 | nose coming up, still fully crossed up |
| 1.73 | f82 | -30 | 90 | 0 | 0 | 0 | axle line 29 deg |
| 1.87 | f86 | -32 | 90 | 0 | 0 | 0 | still crossed up |
| 1.97 | f89 | -32 | 90 | 0 | 0 | 0 | still crossed up as he drops toward the knuckle |
| about 2.0 to 2.15 | shot B f148 to f154 | | | | | | pulled straight in about 0.2 s |
| about 2.2 | shot B f160 | 0 | 0 | landing | 0 | 0 | touchdown, front wheel marginally first |

Source of truth for the numbers: `scripts/demo/whip_measured.py` (with the frame notes).

## What it means
- The whip is far bigger than the first estimate: the bike is **fully sideways (90 deg) and flat by 0.33 s**,
  not 55 to 60 deg. It stays crossed up at about 90 deg for 1.5 s, until he drops toward the landing.
- **His body goes with it.** His torso leans left about 70 deg at the peak (horizontal, head to the left), so
  the bike only has to turn about 55 to 85 deg relative to him. A torso held upright cannot reach the bars there.
- **The nose drop is the gyroscope, not him.** Once the bike is flat and sideways, the spinning wheels' momentum
  is no longer along the pitch axis, so the bodies must carry it: the bike stands up and its nose drops. A rigid
  hold from the peak in the simulation reproduces the measured nose drop from 0.45 to 1.0 s within a few degrees
  (7, 24, 38, 43, 50, 65 deg against 8, 25, 37, 50, 65, 76). His input is to stop it at about 78 deg, bring the
  nose back up to about 30 deg while still fully crossed up, and pull it straight in the last 0.2 s.
- Airtime: he is still crossed up at 2.0 s just before he disappears behind the knuckle, so touchdown is
  about 2.2 s, the same as the KOTW simulation (2.23 s). No time stretch is needed.

## Uncertainty
- About plus or minus 10 deg on the in-picture angles, more (plus or minus 20 deg) on the ellipse-based
  side-on amount; WhatsApp video, 478 px wide, motion blur.
- The camera behind cannot see the bike tipping toward or away from it. The simulation leaves that angle to
  physics (see `scripts/demo/sim.py`, `unseen_axis`).
- Shot B (front) may be a different attempt; its straighten timing (0.2 s before touchdown) is used for the
  duration only.
