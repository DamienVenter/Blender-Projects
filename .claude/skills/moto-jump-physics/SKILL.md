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
- Whip (`sim.py`): INVERSE formulation. Prescribe the bike's motion (Damien's whip from footage), solve the
  rider's rotation from conservation, optimise only the real inputs (lip yaw/roll kick, lay-down depth,
  rear-wheel throttle/brake) so the rider stays within reach and faces forward.

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
4. **Do not drive the whip forward with a generic optimiser.** 25 rider-input knots plus gyro coupling produced
   tumbling solutions (rider roll 178 deg). The inverse formulation with 6 physical parameters is well posed.
5. **Euler angles wrap.** Reading pitch from a rotation matrix (asin) hides a 180 deg over-rotation behind a
   plausible -39 deg. Track continuous pitch by accumulating small rotations.
6. **Pure-radius FMX ramps load about 4 g steady** (6 to 7 g transients at the toe) and push a stock-sprung bike
   near the bottom of its travel. Model the linkage rising rate, fork air volume and bottoming cone.
7. `numpy.cross` on 3-vectors costs 60 % of an inner loop; use a hand-written cross.

## Validated numbers (researched geometry: 2.51 m lip, 9.1 m radius, 43.6 deg; 4.0 m knuckle, 42 deg)
| Quantity | Simulation | Independent check |
|---|---|---|
| Lip speed | 16.03 m/s at 42.8 deg | research 16.06 m/s |
| Rotation off the lip | -38.2 deg/s | research -38 deg/s |
| Airtime | 2.23 s | research 2.27 s, Damien's clips 2.0 to 2.2 s |
| Toe speed (run-in) | 14.85 m/s (53.5 km/h) | research 16.1 (holding) to 17.7 (coasting) |
