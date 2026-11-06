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

## Validated numbers (researched geometry: 2.51 m lip, 9.1 m radius, 43.6 deg; 4.0 m knuckle, 42 deg)
| Quantity | Simulation | Independent check |
|---|---|---|
| Lip speed | 16.03 m/s at 42.8 deg | research 16.06 m/s |
| Rotation off the lip | -38.2 deg/s | research -38 deg/s |
| Airtime | 2.23 s | research 2.27 s, Damien's clips 2.0 to 2.2 s |
| Toe speed (run-in) | 14.85 m/s (53.5 km/h) | research 16.1 (holding) to 17.7 (coasting) |
