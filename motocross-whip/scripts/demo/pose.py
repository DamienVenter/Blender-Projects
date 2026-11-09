"""Per-frame world transforms for every bike part and rider segment.

Mesh conventions (shared with build_scene.py):
- Bike parts are modelled in the bike frame (x forward, y left, z up, metres).
  frame: origin = bike-frame origin (ground under the rear axle, full extension).
  fork_lower: same origin; slides along the fork axis by the fork compression.
  front_wheel / rear_wheel: origin at the axle, spin about local +Y.
  swingarm: origin at the swingarm pivot, rotates about local +Y.
- Rider limb segments are modelled along local +Z from the proximal joint, with
  local +X toward the bending side reference. Rigid parts (pelvis, torso, head)
  are modelled in the rider frame around their own origin.
"""
import math
import numpy as np
import params as P
import bike as B
import rider as RD
import air
from air import Ry

LIMBS = {
    "thigh": (RD.L_THIGH, "hip", "knee"),
    "shank": (RD.L_SHANK, "knee", "ankle"),
    "foot": (None, "ankle", "ball"),
    "upper_arm": (RD.L_UPPER_ARM, "shoulder", "elbow"),
    "forearm": (RD.L_FOREARM + RD.L_HAND_GRIP, "elbow", "grip"),
}


def quat_from_matrix(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def frame_from_z(z_dir, x_hint):
    z = z_dir / np.linalg.norm(z_dir)
    x = x_hint - np.dot(x_hint, z) * z
    if np.linalg.norm(x) < 1e-6:
        x = np.cross(z, [0.0, 1.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.column_stack([x, y, z])


def v3(q2):
    return np.array([q2[0], 0.0, q2[1]])


class Poser:
    def __init__(self, sysm):
        self.S = sysm
        self.lm = RD.neutral_landmarks()
        self.reach_violations = 0
        self.max_overreach = 0.0
        self.prev = {}               # previous frame's elbows, knees and head: bend directions stay continuous

    def limb_frame(self, name, z_dir, x_hint):
        """Segment frame along z_dir. The twist follows the previous frame (parallel transport) and is pulled gently
        toward the anatomical hint, so a limb never spins about its own axis when it lines up with the hint."""
        key = "x_" + name
        if key in self.prev:
            z = z_dir / np.linalg.norm(z_dir)
            xp = self.prev[key] - np.dot(self.prev[key], z) * z
            xh = x_hint - np.dot(x_hint, z) * z
            if np.linalg.norm(xh) > 0.3 and np.linalg.norm(xp) > 1e-6:
                xp = xp / np.linalg.norm(xp) + 0.05 * xh / np.linalg.norm(xh)
            x_hint = xp if np.linalg.norm(xp) > 1e-6 else x_hint
        R = frame_from_z(z_dir, x_hint)
        self.prev[key] = R[:, 0]
        return R

    def bike_parts(self, RA, pb, sf, sr, spin_f, spin_r, steer=0.0):
        """pb = bike CoM (world). Returns {name: (loc, R)}, the frame point mapper and the steered
        front-end point mapper (bars, grips). The steering axis is taken as the fork axis line through
        the front axle at full extension (the 22 mm triple-clamp offset is ignored)."""
        cb = self.S.cb
        Q = v3(P.FRONT_AXLE)
        s_ax = v3(B.fork_axis())
        Rs = air.expm_so3(s_ax * steer)

        def W(q):
            return pb + RA @ (np.asarray(q, float) - cb)

        def Wf(q):                                     # point on the steered front end
            return pb + RA @ (Q + Rs @ (np.asarray(q, float) - Q) - cb)

        out = {"frame": (W([0, 0, 0]), RA)}
        out["front_end"] = (Wf([0, 0, 0]), RA @ Rs)
        out["fork_lower"] = (Wf(v3(B.fork_axis() * sf)), RA @ Rs)
        out["front_wheel"] = (Wf(v3(B.front_axle_at(sf))), RA @ Rs @ Ry(spin_f))
        out["swingarm"] = (W(v3(P.SWINGARM_PIVOT)), RA @ Ry(sr / B.SWINGARM_LEN))
        out["rear_wheel"] = (W(v3(B.rear_axle_at(sr))), RA @ Ry(spin_r))
        return out, W, Wf, RA @ Rs

    def rider_parts(self, RA, RB, W, origin, look_at, crouch=0.0, Wf=None, R_front=None, spine=None):
        """origin: world position of the rider-frame origin (peg midpoint in the neutral pose).
        crouch: extra trunk lean (rad) applied about the pelvis."""
        lm = self.lm
        lean = Ry(crouch)                             # forward lean about the pelvis (rider frame)
        if spine is not None:
            lean = air.expm_so3(np.asarray(spine, float)) @ lean   # spine bend and twist about the pelvis

        def U(p):                                     # rigid upper body point, rider frame -> world
            p = np.asarray(p, float)
            return origin + RB @ (lm["pelvis"] + lean @ (p - lm["pelvis"]))

        out = {}
        pelvis_w = origin + RB @ lm["pelvis"]
        out["pelvis"] = (pelvis_w, RB)
        out["torso"] = (pelvis_w, RB @ lean)
        J = {"pelvis": pelvis_w}
        for s in ("l", "r"):
            J[f"hip_{s}"] = origin + RB @ lm[f"hip_{s}"]
            J[f"shoulder_{s}"] = U(lm[f"shoulder_{s}"])
            J[f"ball_{s}"] = W(self.S.peg + lm[f"ball_{s}"])
            J[f"ankle_target_{s}"] = W(self.S.peg + lm[f"ankle_{s}"])
            J[f"grip_{s}"] = (Wf or W)(self.S.peg + lm[f"grip_{s}"])
        head_c = U(lm["head"])
        # head: look at the target, limited to 75 degrees from the trunk's forward axis
        fwd_trunk = RB @ lean @ np.array([1.0, 0.0, 0.0])
        look = look_at - head_c
        look /= np.linalg.norm(look)
        ang = math.acos(max(min(np.dot(look, fwd_trunk), 1.0), -1.0))
        lim = math.radians(75)
        if ang > lim:
            axis = np.cross(fwd_trunk, look)
            axis /= np.linalg.norm(axis)
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
            look = (np.eye(3) + math.sin(lim) * K + (1 - math.cos(lim)) * K @ K) @ fwd_trunk
        up = RB @ lean @ np.array([0.0, 0.0, 1.0])
        z = up - np.dot(up, look) * look
        z /= np.linalg.norm(z)
        Rh = np.column_stack([look, np.cross(z, look), z])
        if "head" in self.prev:                     # the head turns smoothly (no snap when the look target moves)
            Rh = air.expm_so3(0.25 * air.logm_so3(Rh @ self.prev["head"].T)) @ self.prev["head"]
        self.prev["head"] = Rh
        out["head"] = (head_c, Rh)
        for s, sign in (("l", 1.0), ("r", -1.0)):
            # bend direction: the default pole, or the previous frame's joint (keeps elbows and knees from flipping)
            kpole = self.prev.get(f"knee_{s}", J[f"hip_{s}"] + RA @ np.array([0.6, sign * 0.18, 0.0]))
            knee, ankle, ok1 = RD.two_bone(J[f"hip_{s}"], J[f"ankle_target_{s}"], RD.L_THIGH, RD.L_SHANK, kpole)
            self.prev[f"knee_{s}"] = knee + (knee - 0.5 * (J[f"hip_{s}"] + ankle)) * 2.0
            # shoulder blade slides toward the bar when the arm is near full stretch (up to SCAPULA_REACH)
            arm = RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP
            to_grip = J[f"grip_{s}"] - J[f"shoulder_{s}"]
            dist = np.linalg.norm(to_grip)
            slide = min(max(dist - 0.95 * arm, 0.0), RD.SCAPULA_REACH)
            J[f"shoulder_{s}"] = J[f"shoulder_{s}"] + to_grip / max(dist, 1e-9) * slide
            epole = self.prev.get(f"elbow_{s}", J[f"shoulder_{s}"] + RB @ np.array([-0.25, sign * 0.55, 0.15]))
            elbow, grip, ok2 = RD.two_bone(J[f"shoulder_{s}"], J[f"grip_{s}"], RD.L_UPPER_ARM,
                                           RD.L_FOREARM + RD.L_HAND_GRIP, epole)
            # remember the bend direction, blended with the default so it can recover after a straight arm
            default = J[f"shoulder_{s}"] + RB @ np.array([-0.25, sign * 0.55, 0.15])
            mid = 0.5 * (J[f"shoulder_{s}"] + grip)
            self.prev[f"elbow_{s}"] = 0.85 * (elbow + (elbow - mid) * 2.0) + 0.15 * default
            for ok, a, b in ((ok1, J[f"hip_{s}"], J[f"ankle_target_{s}"]), (ok2, J[f"shoulder_{s}"], J[f"grip_{s}"])):
                if not ok:
                    self.reach_violations += 1
            over_leg = np.linalg.norm(J[f"ankle_target_{s}"] - J[f"hip_{s}"]) - (RD.L_THIGH + RD.L_SHANK)
            over_arm = np.linalg.norm(J[f"grip_{s}"] - J[f"shoulder_{s}"]) - (RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP)
            self.max_overreach = max(self.max_overreach, over_leg, over_arm)
            side = RA @ np.array([0.0, sign, 0.0])
            out[f"thigh_{s}"] = (J[f"hip_{s}"], self.limb_frame(f"thigh_{s}", knee - J[f"hip_{s}"], RA @ np.array([1.0, 0, 0])))
            out[f"shank_{s}"] = (knee, self.limb_frame(f"shank_{s}", ankle - knee, RA @ np.array([1.0, 0, 0])))
            out[f"foot_{s}"] = (ankle, self.limb_frame(f"foot_{s}", J[f"ball_{s}"] - ankle, RA @ np.array([0, 0, 1.0])))
            out[f"upper_arm_{s}"] = (J[f"shoulder_{s}"], self.limb_frame(f"upper_arm_{s}", elbow - J[f"shoulder_{s}"], side))
            out[f"forearm_{s}"] = (elbow, self.limb_frame(f"forearm_{s}", grip - elbow, side))
            out[f"hand_{s}"] = (grip, RA if R_front is None else R_front)
        return out
