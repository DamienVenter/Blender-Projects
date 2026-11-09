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

## Simulation against the measurement (2026-11-06)
The simulated flight (`scripts/demo/sim.py`, best of a CMA-ES search, then refined in the pipeline) drawn over
the same frames: `renders/checkpoints/2026-11-06_measured-whip/overlay_vs_clip_*.jpg`.

| | simulation | Damien |
|---|---|---|
| Flat and fully sideways | about 0.5 s | 0.33 s |
| Nose dropped to hanging | about 1.0 s, about 62 deg in the picture | 1.0 s, 78 deg |
| Crossed up side-on until | about 1.9 s (crossed about 55 deg: wheel roundness 0.8) | about 2.0 s (roundness about 1) |
| Nose angle while crossed up, 1.5 to 1.9 s | 45 to 50 deg | 58 to 30 deg |
| Torso lean | left about 30 deg at the peak; right up to about 50 deg just before the straighten | left about 70 deg at the peak, upright from 1.1 s |
| Head | above the hips the whole flight | same |
| Touchdown | yaw -0.5, lean -1.1, pitch -48 on the 42 deg slope (front first) | nearly straight, front marginally first |

Overall match from his camera: 30 deg RMS (features scaled by measurement precision), torso lean 16 deg RMS.

Rider controls the search chose: rear wheel braked to a stop just after the lip, then revved to the limiter while
crossed up; bars up to 5 deg; 1000 N lift on the bars at the lip (the cap).

What is still different and why (open questions for Damien):
- The lay-down is about 0.1 to 0.15 s late. Faster needs a bigger roll kick off the lip, which then over-rotates
  the rider later in this model.
- His nose comes back up to 30 deg while still fully crossed up; the simulation holds about 50 deg. The physical
  levers are the throttle (revving the rear wheel while crossed up lifts the nose), the bars, and body motion
  this rider model does not have (a leg off the peg, hips off the seat beyond 0.45 m).
- His torso goes much further over with the bike (70 deg) than the simulation's (30 deg), and he is upright again
  by 1.1 s. Leaning that far needs more roll from the lip than this model can then stop.

## 3D from two phones (2026-11-09)
Damien: "Whip is still too small ... my bike is way more sideways. Think 3D ... Replicate it exactly."

Clips 2 and 3 are the same jump filmed by two phones at once (poses match frame for frame, lip at frame 29 in
both). Two lines of sight give the true 3D attitude, including the tilt toward or away from the camera that one
view cannot see.

Method (`scripts/analysis/`):
1. Cameras: both phones are behind and LEFT of the jump line (calibrated on the frames on the ramp, where the
   bike's attitude is known: at the lip the bike appears tilted about 30 deg left in clip 2, which only a camera
   about 2.5 m left of the line gives). Clip 3: (-16, 4, 1.5) m from the lip, about 1200 px focal; clip 2:
   (-6, 2.5, 1.0) m, about 1300 px (zoomed, from the bike's pixel length at the flat peak).
2. Every frame: the bike's red plastics are segmented (`bikebox.py`, `redpca.py`); their principal axis gives the
   bike's angle in the picture in each phone to about 1 deg (both phones agree within 5 deg).
3. Wheel roundness (front wheel ellipse) read off close crops: edge-on at the peak, opening from 0.53 s, full
   profile (both wheels round in both phones) from 1.2 s. The plastics' length is NOT used: the rider's body
   covers the middle of the bike, which made an early solve wrong.
4. `fit3d.py` solves the attitude per frame from both phones' angles plus the roundness (smoothness prior, weak
   prior from the clip 1 table). Result: `whip-attitude-3d/fit_clips23.json`. Checked by drawing the solved bike
   from each phone's position next to the real frames (`twoview.py`): it matches through the whole flight.

| t (s) | what the two phones show (3D solve) |
|---|---|
| 0.00 | already turning on the lip: about 27 deg of yaw at the lip frame |
| 0.27 to 0.30 | flat and about 80 deg sideways; laid PAST flat (about 107 deg, seat facing back and down) |
| 0.33 to 0.47 | held flat; rear starts rising (picture angle 6, 16, 27 deg) |
| 0.53 to 1.07 | nose drops (37, 57, 69, 77 deg in the picture) while the bike rolls up into profile (roundness 0.25 to 0.9) |
| 1.07 to 1.2 | hanging nose-down about 78 deg, full profile |
| 1.2 to 1.95 | full profile (crossed up about 90 deg to the cameras); nose comes back up: 72, 60, 50, 43, 37, 32 deg |
| after 1.95 | straightened in the last about 0.2 s (clip 1), touchdown about 2.2 s |

## Differences between Damien's whip and the previous demo (checkpoint 2026-11-06)
| | Damien (3D) | previous demo |
|---|---|---|
| Initiation | on the lip, bike already 20 to 27 deg turned | after takeoff |
| Flat and sideways | by 0.27 to 0.30 s, laid past flat (about 107 deg) | about 0.5 s, laid about 75 deg |
| Sideways at the peak | about 80 deg | 65 to 75 deg |
| Nose drop | to about 78 deg in the picture by 1.0 s | about 62 deg |
| Cross-up | full profile 1.1 to 1.95 s (90 deg to the cameras) | about 55 deg (roundness 0.8) |
| Nose while crossed up | back up to about 32 deg by 1.8 s | 45 to 50 deg |
| Torso | leans about 70 deg with the bike at the peak, upright from 1.1 s | about 30 deg, then leaning 50 deg the other way |
| Motion | smooth | jerky: controller corrections, elbow IK flips, uneven keys at the takeoff and landing joins |

## Replica (scripts/demo/replicate.py)
The bike's attitude in the air is the 3D measurement through a smooth quaternion spline (knots every 0.10 s:
within 3.2 deg RMS of the measurement, inside its noise). The whip starts on the lip: in the last 0.25 s on the ramp
the ramp simulation's attitude is bent onto the measured lip attitude (23 deg away) and its turn rate; the bike turns
about its centre of mass (the rear end steps out), moves opposite the rider's body, and the ramp holds the rear tyre
up (and the front, while it is still on the ramp), so it leaves the lip about 20 cm higher than a straight bike and settles onto the physics path over 0.8 s.
Run-in, ramp, takeoff, centre-of-mass flight,
suspension and landing are the physics simulation. The rider's lean is as filmed; his torso turn and pitch, hip
shift, spine and rear-wheel speed are solved to keep hands and feet on the bike (worst gap under 1 cm) and the
angular momentum as constant as possible.

Physics check: along the measured motion my two-body rider model cannot conserve angular momentum: mismatch about
69 kg m2/s RMS against 78 at the lip (2026-11-09 solve; the calculation is verified on a simulated flight: constant
to 1 to 2).
The real body does more than the model has (legs and arms moving mass, hips sliding further, throttle and brake
used harder). Closing that gap needs a fuller body model; it is an open item, not hidden.

### Smoothness audit of the replica (2026-11-09, scripts/demo/smoothness.py)
Damien: "your movement is super choppy". The first audit only looked at rotations in the air. Over the whole clip,
rotations and positions, the delivered replica had: arm pops of 3150 deg/s 0.1 s before the lip (the torso
switched attitude), a 33 cm one-frame jump of the whole bike and rider at the lip (the bike pivoted about the rear
tyre on the ramp, dragging it 34 cm sideways, then the flight started back on the physics path), the rear tyre
16 cm inside the lip edge for two frames, a head flip after touchdown (the look target ended up behind him),
an arm stutter at full stretch, rate flips at every filmed-lean reading, and a frozen last frame. After the fixes
(skill moto-jump-physics, smoothness list) the worst frame-to-frame wobble anywhere is about 175 deg/s on the arms
during the flick itself (the bike turns at 745 deg/s there) and no part jumps (largest 1.1 m/s, a forearm).

### His body from the two phones (2026-11-09)
The bike matched; his body did not. A strip of his frames against the replica showed him laid flat along the bike
from the lip (head down by the front fender, legs out behind) while the replica sat upright until about 0.35 s.

- Helmet tracked in every frame of both phones (`scripts/analysis/helmet.py`; `whip-attitude-3d/helmet_c2.json`,
  `helmet_c3.json`): clip 2 on 46 of 48 frames (0 to 1.57 s), clip 3 to frame 70 (it loses the helmet against the
  body after that). Offsets are from the red plastics' bbox centre (the phones pan).
- Scale check: the attitude fit only used angles, so its focal lengths had never been checked for size. Making the
  bike's red plastics come out their measured size frame by frame shows the clip 2 phone ZOOMING: about 1230 px
  off the lip to 1870 px at 1.0 s (the fit's 900 was half); clip 3 holds about 1340 to 1430 px. Stored as
  `f_track` in `cams_clips23.json` (`head3d.zoom_track`); every pixel distance uses it, and the replica's matched
  cameras zoom the same way (the replica was framed smaller than his phones and the comparison drifted).
- Free 3D triangulation of the helmet is not reliable here: the phones stand only about 14 deg apart, so depth
  along the travel direction is weak (the answer jumped between two solutions).
- The replica's helmet, placed where its body puts it, is off his by 31 px across and 52 px up the picture (RMS)
  in clip 2 and 15 and 33 px in clip 3: at the lip his head is far lower (crouched over the bars) and through
  0.4 s it stays low along the bike (`head_compare.py`, chart in the checkpoint).
- Fitting the replica's body to it (`replicate.Replicator.head_pixels`, 6 px) failed: the solve stretched the legs
  to 154 % and doubled the momentum mismatch. The measurement is not yet good enough to drive it: the bike's size
  in his frames drifts 1.5x to 2x against the model over the flight (his clip 2 phone zooms; the zoom track now
  follows it, but the fit was done before that), and off the lip the red plastics are half hidden in the trees, so the anchor is biased. The fit
  is switched off (`FIT_HELMET`); the helmet error is reported. Next: per-frame scale from the bike's own size,
  a second body point (hips or boots) and an anchor on the wheels.
