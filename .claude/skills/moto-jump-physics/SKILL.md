---
name: moto-jump-physics
description: Physics of motocross / FMX jumps and whips as simulated in this repo (ramp, lip, flight, whip, landing). Use before changing motocross-whip/scripts/demo or simulating any jump.
---

# Motocross jump and whip physics: what we learned

Code: `motocross-whip/scripts/demo/` (`params.py` holds every number with its source).
Tests: `python3 -m pytest -q test_physics.py` must pass before any render.

## Model
- Ground (`ground.py`): bike rigid body + rider point mass on leg spring-dampers; massless wheels on a
  fork (slides along the rake) and a swingarm (arc). Contact via the wheel-centre offset curve
  (morphological dilation of the profile by the tyre radius): exact for concave transitions and the lip edge.
- Air (`air.py`): bike + rider as two rigid bodies + spinning wheels. Total angular momentum about the
  system CoM is conserved exactly; the CoM flies ballistically with drag.
- Whip (`sim.py`, `air.run_control`): CLOSED-LOOP rider. Each step the rider picks how fast to twist the bike
  relative to his body and how much throttle/brake to give the rear wheel (weighted least squares: follow
  Damien's whip, keep the torso facing forward, stay in reach, be neutral by touchdown). Conservation of
  angular momentum (gyro included) then fixes both rotations. Outer optimiser picks only the lip inputs:
  yaw kick, roll kick, takeoff rotation change (lip pull on the bars) and the whip amplitude.

## Lessons (each cost real time)
1. **The rider's legs decide the lip rotation.** A passive, springy rider (zeta 0.5) stores energy crouching
   into the transition and shoves the rear into the ramp as the front leaves: -86 deg/s nose-down. A skilled
   rider absorbs (overdamped legs, zeta about 1.8): -42 deg/s. Real jumps need about -37 deg/s.
2. **Throttle up the face sets the rotation.** Drive force at the rear contact (below the CoM) pitches the nose
   up. Solve the steady face throttle so the bike's natural rotation lands it at the slope angle (result:
   1332 N, part throttle, about 18 kW).
3. **Gyroscope makes the whip.** With the wheels spinning (about 62 kg m^2/s), laying the bike down to the LEFT
   swings the rear to the RIGHT by itself (test `test_gyro_whip_direction`). Straightening needs the opposite.
   Throttle in the air spins up the rear wheel and pitches the nose up; a brake tap pitches it down.
4. **Whip formulations that FAILED, and why.**
   - Open-loop forward (25 rider-input knots, generic optimiser): tumbling (rider roll 178 deg).
   - Inverse (prescribe the bike, solve the rider): the gyro reaction of laying the bike down is far larger
     than the rider's inertia can absorb, so the rider spins (170 deg off the bike).
   - Open-loop forward with sensible shapes: once the input stops, the system keeps precessing.
   - What works: closed-loop rider (feedback), like a real rider who watches the landing.
5. **Laying the bike flat pitches everything nose-down faster** (wheel momentum leaves the pitch axis). A whip
   needs a gentler takeoff rotation than a straight jump. Throttle on the face only shifts it about 4 deg/s
   (power limited); the rider lifting on the bars at the lip shifts it about 1.8 deg/s per 100 N (cap 1000 N).
6. **Hips must be a physical DOF.** Solving the hip shift instantly from the rider's orientation creates an
   algebraic loop (hip rate feeds the rider's spin): 1000 m/s hip rates. Rate-limit it (80 ms, 2 m/s, 0.45 m).
7. **Rigid rider pivoting at the pegs cannot reach the bars when the bike is flat** (1.1 to 1.6 m overreach).
   Real riders shift their hips over the bike; model it.
8. **Euler angles wrap.** Reading pitch from a rotation matrix (asin) hides a 180 deg over-rotation behind a
   plausible -39 deg. Track continuous pitch by accumulating small rotations.
9. **Pure-radius FMX ramps load about 4 g steady** (6 to 7 g transients at the toe) and push a stock-sprung bike
   near the bottom of its travel. Model the linkage rising rate, fork air volume and bottoming cone.
10. `numpy.cross` on 3-vectors costs 60 % of an inner loop; use a hand-written cross.

## Getting Damien's FULL whip (session 2026-11-06, after "the demo whip was nowhere near as big")
- Never let the optimiser shrink the whip to make the physics easy. Fix the peak at Damien's size and find
  the inputs and body motion that achieve it; if it fails, the MODEL is missing something real.
- What was missing, in order of impact:
  1. **A spine.** A rigid torso leaves the low hand 0.5 m short of the grip when the bike is flat. Real
     riders side-bend, twist and flex (about 35, 45, 30 deg). Model it with the hips in the posture solver,
     and put the upper body's mass swing into the momentum balance (it rotates with the RIDER, not the bike).
  2. **Track only where the whip is defined.** Firm tracking for the lay-down/peak and the last 0.5 s
     before touchdown; light touch in between. Holding a crossed-up bike precesses the whole system into
     a roll (wheel momentum gains a component along the travel direction): about 60 deg/s at 60 deg yaw.
     Real riders let the gyroscope bring the bike back instead of fighting it.
  3. **Define the peak in world angles** (how footage shows it). Composing the whip on top of the jump's
     own rotation over-flattens the apparent lean past -100 deg.
  4. **Pitch at the peak is part of the look.** A flat whip seen from behind is flat AND level: the nose
     drops fast during the lay-down (the gyro pushes it) to about level at the peak, then slowly to the
     landing angle. A steady nose-down pitch target leaves the bike laid over but nose-up 35 deg: it reads
     as a diagonal, not a whip. The extra nose-down from the flat phase must be paid for with a gentler
     takeoff rotation (lip pull).
  5. **Render exactly what was scored.** One code path (`Pipeline.fly`) for the optimiser and the recorded
     flight; a regression test checks they match.
- Momentum budget: any roll or yaw momentum given at the lip is still there at touchdown (wheels hold it
  only while the bike is crossed up or laid over). Lip kicks must be small or cancelled by body motion.

## Damien's MEASURED whip (2026-11-06, research/whip-attitude-measured.md)
- Real size: bike fully sideways (90 deg) and flat by 0.33 s after the lip, held to 0.45 s; the nose then drops
  until the bike hangs nose-down (about 78 deg in the picture) at 1.0 s; nose back up to about 30 deg while still
  fully crossed up until about 2.0 s; pulled straight in the last 0.2 s. His torso leans left about 70 deg at
  the peak (goes WITH the bike) and is upright by 1.0 s.
- The nose drop is the gyroscope: once the bike is flat and sideways, the wheels' momentum leaves the pitch axis
  and the bodies must carry it. A rigid hold from the peak reproduces his nose drop to within a few degrees for
  0.45 to 1.0 s. His own input is stopping it, lifting the nose and the late straighten.
- Tracking every axis of a measured attitude makes the rider tumble: the bike is heavier than the rider, so
  every degree forced on the bike spins him further the other way. Track only what the camera saw (bike: turn in
  the picture and side-on amount; torso: lean) and solve the hidden angles (bike tipping toward the camera, torso
  turn and pitch) so momentum is conserved: `sim.Pipeline.target_fn`, knots `HID_T`.
- The lip kick: the system leaves the lip already rolling left with the bike (he rolls with it), so the kick is
  shared by rider and bike (`KICK_BIKE_ONLY = False`); `run_control(kick_bike_only=True)` exists for comparison,
  with the exact angular momentum of two bodies rotating differently.
- Relative bike-to-rider rotation needed: about 55 to 85 deg (REL_MAX raised from 75 to 95 deg; the limb-by-limb
  reach check is the real limit). A torso held upright cannot reach the bars when the bike is flat and sideways.
- Holding the cross-up: the jump's nose-down spin must live somewhere once the wheel axis has left the pitch
  axis. If nothing holds the torso pitch, the light rider absorbs it and goes over the bars (head below the bike
  by 1.5 s). Hold the torso pitch firmly (`lg_w_torso_pitch`); then the bike carries it, crossed up a bit less
  than 90 deg (60 deg still looks side-on from behind: wheel roundness 0.87) with the throttle open, so the wheels
  hold part of it.
- An exact inverse (prescribe every visible angle, solve the hidden ones from L = const) blows up: noise in the
  measured angles becomes impossible spin rates when differentiated. Fit within the measurement error instead.
- Judge flights by drawing them over the real frames (`attitude_overlay.py --sim flight.npz`), not by numbers.
- Search: CMA-ES (`pip install cma`) in coordinates normalised to each input's range; Nelder-Mead stalls on this
  many-input, many-valley problem. The landscape is chaotic (tiny input changes flip clean and tumbling), so use
  a population, several hundred evaluations, and restart from the best with a smaller step.

## Replica of the measured whip and smooth animation (2026-11-09)
- Damien asked for his whip replicated EXACTLY. `replicate.py`: bike attitude = two-phone 3D measurement through
  a quaternion spline (knots 0.10 s: inside the measurement noise, half the jerk of 0.07 s); physics for run-in,
  ramp, takeoff, CoM flight, suspension, landing; rider lean as filmed, the unseen body angles solved for reach
  and momentum. Momentum mismatch is REPORTED (about 75 kg m2/s RMS): the two-body rider cannot reproduce it.
- He starts the whip on the lip. Use ONE attitude curve through the lip (ramp attitude until 0.1 s before, the
  measured lip attitude at it) and pivot about the rear tyre contact. Two pieces joined at the lip rock the bike.
- Sources of "choppy" motion found and fixed (audit every object's angular velocity and acceleration from
  frames.json, `max ang acc` and p99):
  1. Closed-loop controller corrections and step changes in its phase weights: the bike wobbles.
  2. Elbow IK flips when the pole lines up with the arm: use the previous frame's joint as the pole.
  3. Limb twist flips when the limb lines up with its reference axis: parallel-transport the twist.
  4. IK snap at full extension (square root): soft IK eases the reach over the last 4 %.
  5. Uneven keys at the ground-to-air and air-to-ground joins (1 ms apart): resample all objects to whole frames.
  6. Head look target switching: blend the target, smooth the head rotation.
  7. Hip shift dropping to zero at touchdown: carry it and blend it out over 0.15 s.

## Validated numbers (researched geometry: 2.51 m lip, 9.1 m radius, 43.6 deg; 4.0 m knuckle, 42 deg)
| Quantity | Simulation | Independent check |
|---|---|---|
| Lip speed | 16.03 m/s at 42.8 deg | research 16.06 m/s |
| Rotation off the lip | -38.2 deg/s | research -38 deg/s |
| Airtime | 2.23 s | research 2.27 s, Damien's clips 2.0 to 2.2 s |
| Toe speed (run-in) | 14.85 m/s (53.5 km/h) | research 16.1 (holding) to 17.7 (coasting) |
