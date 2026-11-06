"""Rider body model: anthropometry, neutral attack pose, mass properties, IK.

Segment lengths: Drillis and Contini (1966) fractions of standing height H.
Segment masses and centre-of-mass ratios: Winter, Biomechanics and Motor
Control of Human Movement (4th ed.), table 4.1.

Rider frame: origin at the peg midpoint (between the two foot contacts),
x forward, y left, z up. In the neutral pose the rider frame coincides with
the bike frame (translated to the pegs).
"""
import numpy as np
import params as P

H = P.RIDER_HEIGHT
BODY = P.RIDER_MASS

# Lengths (m)
L_THIGH = 0.245 * H            # hip joint to knee
L_SHANK = 0.246 * H            # knee to ankle
L_UPPER_ARM = 0.186 * H        # shoulder to elbow
L_FOREARM = 0.146 * H          # elbow to wrist
L_HAND_GRIP = 0.045 * H        # wrist to grip centre (about 40 % of hand length)
L_TRUNK = 0.288 * H            # hip-joint centre to shoulder-joint centre
HIP_HALF = 0.096 * H / 2 * 1.0 # hip joint half separation (0.096 H between joint centres)
SHOULDER_HALF = 0.205 * H / 2  # shoulder joint half separation
L_NECK_HEAD = 0.137 * H        # shoulder line to head centre (helmet centre)
SCAPULA_REACH = 0.08           # extra reach from the shoulder blade sliding forward (protraction), EST
ANKLE_ABOVE_PEG = 0.10         # boot sole + ankle height above the ball of foot on the peg
ANKLE_BEHIND_PEG = 0.14        # ankle joint behind the ball of the foot

# Gear (kg) added to segments: total about 8.5 kg (EST)
GEAR = {"head": 1.40, "trunk": 2.50, "hand": 0.10, "thigh": 0.30, "foot": 1.90}

# Neutral attack pose (rider frame). Tuned so knee flexion is about 55 degrees
# and elbow flexion about 85 degrees, typical standing attack position.
TRUNK_LEAN_DEG = 42.0          # trunk forward of rider-frame vertical
PELVIS = np.array([-0.10, 0.0, 0.88])


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def two_bone(root, target, l1, l2, pole):
    """Analytic two-bone IK. Returns (mid_joint, end, reached)."""
    d = target - root
    dist = np.linalg.norm(d)
    reached = dist <= (l1 + l2) * 0.999
    dist_c = np.clip(dist, abs(l1 - l2) + 1e-4, (l1 + l2) * 0.999)
    u = d / max(dist, 1e-9)
    a = (l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * dist_c)
    h = np.sqrt(max(l1 * l1 - a * a, 0.0))
    p = pole - root
    perp = _unit(p - np.dot(p, u) * u)
    mid = root + u * a + perp * h
    end = root + u * dist_c
    return mid, end, reached


def neutral_landmarks(peg_half=P.FOOTPEG_HALF_SPAN, grip_rel=None, grip_half=P.GRIP_HALF_SPAN):
    """Joint positions of the neutral pose in the rider frame."""
    if grip_rel is None:
        grip_rel = np.array([P.GRIP[0] - P.FOOTPEG[0], 0.0, P.GRIP[1] - P.FOOTPEG[1]])
    lean = np.radians(TRUNK_LEAN_DEG)
    trunk_dir = np.array([np.sin(lean), 0.0, np.cos(lean)])
    lm = {"pelvis": PELVIS.copy()}
    lm["shoulder_mid"] = PELVIS + trunk_dir * L_TRUNK
    head_dir = _unit(trunk_dir + np.array([0.0, 0.0, 1.2]))
    lm["head"] = lm["shoulder_mid"] + head_dir * L_NECK_HEAD
    for side, s in (("l", 1.0), ("r", -1.0)):
        hip = PELVIS + np.array([0.0, s * HIP_HALF, 0.0])
        ball = np.array([0.0, s * peg_half, 0.0])
        ankle = ball + np.array([-ANKLE_BEHIND_PEG, -s * 0.01, ANKLE_ABOVE_PEG])
        knee, ankle_r, _ = two_bone(hip, ankle, L_THIGH, L_SHANK,
                                    hip + np.array([0.6, s * 0.15, 0.0]))
        sh = lm["shoulder_mid"] + np.array([0.0, s * SHOULDER_HALF, 0.0])
        grip = grip_rel + np.array([0.0, s * grip_half, 0.0])
        elbow, wrist, _ = two_bone(sh, grip, L_UPPER_ARM, L_FOREARM + L_HAND_GRIP,
                                   sh + np.array([-0.2, s * 0.5, 0.1]))
        lm.update({f"hip_{side}": hip, f"knee_{side}": knee, f"ankle_{side}": ankle_r,
                   f"ball_{side}": ball, f"shoulder_{side}": sh, f"elbow_{side}": elbow,
                   f"grip_{side}": grip})
    return lm


def segments(lm):
    """(name, mass_kg, com_position, rod_axis_vector, radius) in the rider frame."""
    m = lambda frac, g=0.0: frac * BODY + g
    segs = [
        ("trunk", m(0.497, GEAR["trunk"]), lm["pelvis"] + 0.50 * (lm["shoulder_mid"] - lm["pelvis"]),
         lm["shoulder_mid"] - lm["pelvis"], 0.15),
        ("head_neck", m(0.081, GEAR["head"]), lm["head"], np.array([0, 0, 0.25]), 0.13),
    ]
    for s in ("l", "r"):
        segs += [
            (f"thigh_{s}", m(0.100, GEAR["thigh"]), lm[f"hip_{s}"] + 0.433 * (lm[f"knee_{s}"] - lm[f"hip_{s}"]),
             lm[f"knee_{s}"] - lm[f"hip_{s}"], 0.075),
            (f"shank_{s}", m(0.0465), lm[f"knee_{s}"] + 0.433 * (lm[f"ankle_{s}"] - lm[f"knee_{s}"]),
             lm[f"ankle_{s}"] - lm[f"knee_{s}"], 0.05),
            (f"foot_{s}", m(0.0145, GEAR["foot"]), 0.5 * (lm[f"ankle_{s}"] + lm[f"ball_{s}"]),
             lm[f"ball_{s}"] - lm[f"ankle_{s}"], 0.05),
            (f"upper_arm_{s}", m(0.028), lm[f"shoulder_{s}"] + 0.436 * (lm[f"elbow_{s}"] - lm[f"shoulder_{s}"]),
             lm[f"elbow_{s}"] - lm[f"shoulder_{s}"], 0.045),
            (f"forearm_{s}", m(0.016), lm[f"elbow_{s}"] + 0.43 * (lm[f"grip_{s}"] - lm[f"elbow_{s}"]),
             lm[f"grip_{s}"] - lm[f"elbow_{s}"], 0.04),
            (f"hand_{s}", m(0.006, GEAR["hand"]), lm[f"grip_{s}"], np.array([0, 0, 0.1]), 0.04),
        ]
    return segs


def mass_properties(lm=None):
    """Total mass, CoM (rider frame) and inertia tensor about the CoM (rider frame)."""
    if lm is None:
        lm = neutral_landmarks()
    segs = segments(lm)
    M = sum(s[1] for s in segs)
    com = sum(s[1] * s[2] for s in segs) / M
    I = np.zeros((3, 3))
    for _, mi, ci, axis, r in segs:
        d = ci - com
        I += mi * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
        Lr = np.linalg.norm(axis)
        a = axis / Lr
        i_par = 0.5 * mi * r * r                       # solid cylinder about its axis
        i_perp = mi * (3 * r * r + Lr * Lr) / 12.0     # about a perpendicular axis
        I += i_perp * np.eye(3) + (i_par - i_perp) * np.outer(a, a)
    return M, com, I


if __name__ == "__main__":
    lm = neutral_landmarks()
    M, com, I = mass_properties(lm)
    print(f"rider+gear mass {M:.2f} kg  CoM {np.round(com, 3)} m (rider frame)")
    print("inertia diag (kg m^2):", np.round(np.diag(I), 2))
    for s in ("l", "r"):
        kv = lm[f"hip_{s}"] - lm[f"knee_{s}"]; sv = lm[f"ankle_{s}"] - lm[f"knee_{s}"]
        ev = lm[f"shoulder_{s}"] - lm[f"elbow_{s}"]; fv = lm[f"grip_{s}"] - lm[f"elbow_{s}"]
        kf = 180 - np.degrees(np.arccos(np.dot(kv, sv) / np.linalg.norm(kv) / np.linalg.norm(sv)))
        ef = 180 - np.degrees(np.arccos(np.dot(ev, fv) / np.linalg.norm(ev) / np.linalg.norm(fv)))
        print(f"side {s}: knee flexion {kf:.0f} deg, elbow flexion {ef:.0f} deg")
