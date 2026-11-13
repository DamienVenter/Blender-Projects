"""Riding poses on Damien's CRF250R: the contact targets from the bike model, as a pose file for build_rider.py.

python3 pose.py PARTS.npz NAME OUT.json        NAME: seated, standing (more to come)

All targets are in the bike's ground frame (x forward, y left, z up, the ground at z = 0; parts.to_ground), which is
the world frame the bike stands in. build_rider.py turns them into bone rotations (aim_pose):
  pelvis      the midpoint of his hip joints; pelvis_pitch: the pelvis tipped forward (deg, about y);
              pelvis_roll: the right hip dropped (deg; a foot down on the right)
  spine_lean  the trunk's forward lean from vertical (deg), shared over the five spine bones
  head_pitch  the head and neck tipped down (deg) from the trunk's line, to look ahead
  hands       per side: the grip point the hand closes on (grip axis, 60 mm in from the bar end, where the palm's
              centre sits: Damien's 2.5 X-Flow gloves are short-cuffed, the grip is 130 mm long)
  balls       per side: the point under the ball of the foot (the boot sole's tread on the peg's top, 25 mm sole)
  knee_pole, elbow_pole   the directions the knees and elbows bend toward (unit vectors, ground frame)
Sources: grips (detail_front._Side, 0.06 m in), peg tops (footpegs part, top z of each peg), seat top (seat part,
highest point within 30 mm of the centre line), all from the bike model; body lengths from body.py.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BIKE = os.path.join(HERE, "..", "bike")
sys.path.insert(0, BIKE)

BOOT_SOLE = 0.020            # m under the ball of the foot: the 6.5 boot model, sole and insole (boots.py; 27 at the heel)
GRIP_IN = 0.06               # m from the bar end along the grip to the palm's centre


def contacts(parts_npz):
    import parts
    import detail_front as df
    d = np.load(parts_npz)
    G = parts.to_ground
    P = d["footpegs__V"].astype(float)
    pegs = {}
    for side, s in (("L", 1), ("R", -1)):
        Q = P[P[:, 1] * s > 0]
        pegs[side] = G(np.array([[Q[:, 0].mean(), Q[:, 1].mean(), Q[:, 2].max()]]))[0]
    grips = {side: G(np.array([df._Side(s).p(GRIP_IN, 0, 0)]))[0] for side, s in (("L", 1), ("R", -1))}
    S = G(d["seat__V"].astype(float))
    S = S[np.abs(S[:, 1]) < 0.03]
    xs = np.arange(0.30, 0.80, 0.01)
    seat = np.array([[x, 0.0, S[np.abs(S[:, 0] - x) < 0.006, 2].max()] for x in xs
                     if (np.abs(S[:, 0] - x) < 0.006).any()])
    return dict(pegs=pegs, grips=grips, seat=seat)


def seat_top(c, x):
    s = c["seat"]
    return float(np.interp(x, s[:, 0], s[:, 2]))


def pose(c, name):
    """A named pose from the contacts. Numbers: rider position on the seat from his photo 05 (seated, left side)
    and common riding technique (seated: trunk 20 deg forward; standing attack: hips over the pegs, trunk 40 deg)."""
    pegs, grips = c["pegs"], c["grips"]
    balls = {k: (v + np.array([0.0, 0.0, BOOT_SOLE])).tolist() for k, v in pegs.items()}
    if name == "seated":
        # riding seated, as his photo 07 (2026-11-12, panning, left side): trunk about 28 deg forward, elbows up
        # and out, head forward over the bars (by eye: that photo's camera cannot be fitted from the visible bike
        # points while the suspension sags under him)
        x = 0.58                                          # hip joints over the seat's lowest point (photo 05)
        pelvis = [x, 0.0, seat_top(c, x) + 0.095]         # sit bones about 95 mm below the hip joints when seated
        out = dict(pelvis=pelvis, pelvis_pitch=20.0, spine_lean=34.0, head_pitch=4.0,
                   elbow_pole=[-0.15, 0.75, 0.25])           # a straight back, the head carried up (photo 07)
    elif name == "photo05":
        # his photo 05 (2026-11-10, stopped in the pits, seated, left side): upright trunk, left boot on the left
        # peg, right boot on the ground on the far side. The right sole's place: the photo's camera (fitted to six
        # bike landmarks, 5.3 px rms; cam05 in research/rider-cameras.json) cast onto the ground from the middle of
        # the sole's lower edge (photo pixel 335, 1139): (0.30, -0.43, 0); the ball of the foot about 50 mm ahead.
        # to plant that foot flat he slides his hips right and drops the right hip, the trunk upright over them
        x = 0.62
        pelvis = [x, -0.07, seat_top(c, x) + 0.095]
        out = dict(pelvis=pelvis, pelvis_pitch=2.0, pelvis_roll=9.0, spine_lean=3.0, head_pitch=2.0)
        balls = dict(balls, R=[0.35, -0.43, BOOT_SOLE])
    elif name == "standing":
        x = 0.47                                          # hips back over the pegs' line, knees bent about 50 deg:
        pelvis = [x, 0.0, 1.25]                           # hip joints about 0.8 m above the balls of the feet
        out = dict(pelvis=pelvis, pelvis_pitch=35.0, spine_lean=42.0, head_pitch=10.0,
                   elbow_pole=[-0.1, 0.8, 0.35])
    else:
        raise ValueError(name)
    out.setdefault("elbow_pole", [-0.3, 0.6, -0.4])
    out.update(hands={k: v.tolist() for k, v in grips.items()}, balls=balls, knee_pole=[0.85, 0.15, 0.2])
    return out


if __name__ == "__main__":
    c = contacts(sys.argv[1])
    p = pose(c, sys.argv[2])
    p["name"] = sys.argv[2]
    json.dump(p, open(sys.argv[3], "w"), indent=1)
    print(json.dumps(p))
