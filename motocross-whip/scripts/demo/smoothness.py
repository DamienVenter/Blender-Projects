"""Smoothness audit of an exported animation (frames.json): finds pops and jerks in every object, over the whole clip.

For each object, from its world transforms at the export rate (120 fps):
- w: angular speed (deg/s) and linear speed;
- wobble: how far one frame's angular velocity is from the mean of its two neighbours (deg/s). Smooth motion, however
  fast, changes its rate steadily, so this stays small; a pop (a joint that jumps for a frame and comes back, or a
  join where two simulations meet) shows up as a large wobble at that frame;
- the same for position (m/s): a body that jumps sideways for a frame.
Also the time step (frames must be evenly spaced).

python3 smoothness.py frames.json [N]      prints the N worst objects for each measure
"""
import json
import sys

import numpy as np


def q2R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def logm(R):
    c = max(min((np.trace(R) - 1) / 2, 1.0), -1.0)
    a = np.arccos(c)
    if a < 1e-9:
        return np.zeros(3)
    return a / (2 * np.sin(a)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])


def audit(frames_json, skip=("wheel",)):
    """{object: dict(w_max, wobble_max, wobble_t, vwobble_max, vwobble_t)} and the time step range."""
    fr = json.load(open(frames_json)) if isinstance(frames_json, str) else frames_json
    names, F = fr["objects"], fr["frames"]
    T = np.array([f["t"] for f in F]) - fr["t_off"]
    dt = np.diff(T)
    out = {}
    for j, n in enumerate(names):
        if any(s in n for s in skip):
            continue
        P = np.array([f["tf"][j][:3] for f in F])
        R = [q2R(f["tf"][j][3:]) for f in F]
        w = np.array([logm(R[i + 1] @ R[i].T) / dt[i] for i in range(len(R) - 1)])     # world angular velocity
        v = np.diff(P, axis=0) / dt[:, None]
        wob = np.degrees(np.linalg.norm(w[1:-1] - 0.5 * (w[:-2] + w[2:]), axis=1))
        vwob = np.linalg.norm(v[1:-1] - 0.5 * (v[:-2] + v[2:]), axis=1)
        tm = T[1:-2] + 0.5 * dt[1:-1]
        i, k = int(np.argmax(wob)), int(np.argmax(vwob))
        out[n] = dict(w_max=float(np.degrees(np.linalg.norm(w, axis=1)).max()), wobble_max=float(wob[i]),
                      wobble_t=float(tm[i]), vwobble_max=float(vwob[k]), vwobble_t=float(tm[k]))
    return out, (float(dt.min()), float(dt.max()))


def main():
    res, (dmin, dmax) = audit(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    print(f"time step {dmin * 1000:.3f} .. {dmax * 1000:.3f} ms")
    print(f"{'object':26s} {'max w deg/s':>11s} {'wobble deg/s':>13s} {'at t':>7s} {'pos wobble m/s':>15s} {'at t':>7s}")
    for name, r in sorted(res.items(), key=lambda kv: -kv[1]["wobble_max"])[:n]:
        print(f"{name:26s} {r['w_max']:11.0f} {r['wobble_max']:13.1f} {r['wobble_t']:+7.3f} "
              f"{r['vwobble_max']:15.3f} {r['vwobble_t']:+7.3f}")
    print("worst position wobble:")
    for name, r in sorted(res.items(), key=lambda kv: -kv[1]["vwobble_max"])[:6]:
        print(f"  {name:26s} {r['vwobble_max']:.3f} m/s at {r['vwobble_t']:+.3f}")


if __name__ == "__main__":
    main()
