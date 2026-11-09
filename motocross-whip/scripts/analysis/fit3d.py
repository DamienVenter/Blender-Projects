"""Two-camera 3D fit of the bike's attitude, every frame, from the shape of its red plastics.

Clips 2 and 3 are one jump filmed by two phones (research/whip-attitude-measured.md). In each frame the red
plastics (fenders, radiator shrouds, side panels) form an elongated blob; its principal axis angle, elongation and
spread are measured (redpca output). For a trial attitude the same red parts of the bike model are projected into
both calibrated cameras and the same three numbers computed. The attitude that matches both views is solved frame
by frame (small rotation from the previous frame, with a smoothness prior), starting at the lip where the attitude
is known.

python3 fit3d.py PCA_C2.json PCA_C3.json CAMS.json OUT.json
"""
import json
import math
import sys
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "demo"))
import air            # noqa: E402
import params as P    # noqa: E402
import bike as B      # noqa: E402


def red_points():
    """Points on the red plastics in the bike frame (x fwd, y left, z up), with area weights."""
    pts, wts = [], []
    fa = B.fork_axis()
    for s in np.linspace(-1, 1, 9):                       # front fender: above the tyre, along the fork's normal
        c = np.array([P.FRONT_AXLE[0] + fa[0] * 0.47, 0.0, P.FRONT_AXLE[1] + fa[1] * 0.47])
        d = np.array([math.cos(math.radians(-14)), 0, math.sin(math.radians(-14))])
        for y in (-0.07, 0.07):
            pts.append(c + d * 0.27 * s + np.array([0, y, 0])); wts.append(1.0)
    for x in np.linspace(0.80, 1.12, 5):                  # radiator shrouds, both sides
        for z in (0.78, 0.90, 1.00):
            for y in (-0.22, 0.22):
                pts.append(np.array([x, y, z])); wts.append(1.2)
    for x in np.linspace(-0.40, 0.55, 9):                 # side panels and rear fender
        z = 0.96 + 0.06 * (0.55 - x)
        for y in (-0.12, 0.0, 0.12):
            pts.append(np.array([x, y, z])); wts.append(0.9)
    return np.array(pts), np.array(wts)


PTS, WTS = red_points()
PTS = PTS - PTS.mean(axis=0)


def shape(RA, cam, pos, f):
    """Projected principal-axis angle (deg mod 180, image y up), elongation and spread (px) of the red parts."""
    look = pos - cam
    fwd = look / np.linalg.norm(look)
    right = np.cross(fwd, [0.0, 0.0, 1.0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    W = (RA @ PTS.T).T + pos - cam
    z = W @ fwd
    u, v = f * (W @ right) / z, f * (W @ up) / z
    w = WTS / WTS.sum()
    mu, mv = (w * u).sum(), (w * v).sum()
    C = np.array([[(w * (u - mu) ** 2).sum(), (w * (u - mu) * (v - mv)).sum()],
                  [(w * (u - mu) * (v - mv)).sum(), (w * (v - mv) ** 2).sum()]])
    ev, evec = np.linalg.eigh(C)
    vec = evec[:, 1]
    return math.degrees(math.atan2(vec[1], vec[0])) % 180.0, math.sqrt(max(ev[0], 1e-9) / ev[1]), math.sqrt(ev[1])


def wrap180(a):
    return (a + 90.0) % 180.0 - 90.0


def main():
    pca2, pca3, cams, out = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), sys.argv[4]
    sys.path.insert(0, HERE)
    from attitude_overlay import trajectory
    ts, pbs = trajectory()
    views = [(pca2, np.array(cams["clip2"]["cam"]), cams["clip2"]["f"], cams["clip2"].get("k", 1.0)),
             (pca3, np.array(cams["clip3"]["cam"]), cams["clip3"]["f"], cams["clip3"].get("k", 1.0))]
    lip = cams.get("lip_frame", 29)
    prior = None
    if cams.get("prior_table"):          # weak prior: the clip 1 measurement (breaks the one-view ambiguity only)
        import whip_measured as WM
        tab = WM.table(44.0, -40.0)
        prior = lambda tt: WM.attitude(*[float(v) for v in WM.params_at(tt, tab)[:4]])
    R = air.Ry(-math.radians(44.0))
    res = {}
    for fr in range(lip, lip + cams.get("n_frames", 60)):
        t = (fr - lip) / 30.0
        pos = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
        meas = [(v.get(str(fr)), cam, f, k) for v, cam, f, k in views]
        meas = [m for m in meas if m[0] is not None and m[0][3] >= 40]
        for tm, am in cams.get("manual_angle", []):          # angle read by eye where the red blob is too small
            if abs(tm - t) < 0.017 and not meas:
                meas = [((am, 0.1, 30.0, 99), views[1][1], views[1][2], views[1][3])]
        rt = cams.get("roundness")
        rho = float(np.interp(t, [q[0] for q in rt], [q[1] for q in rt])) if rt and rt[0][0] <= t <= rt[-1][0] else None
        if not meas:
            continue
        Rp = R

        def resid(dlt):
            Rt = air.expm_so3(dlt) @ Rp
            r = []
            for (ang, el, sd, n), cam, f, k in meas:
                a, e, s = shape(Rt, cam, pos, f)
                r += [wrap180(a - ang) / 4.0]              # angle of the plastics in the picture (reliable)
            if rho is not None:                            # wheel roundness seen by the phones (front wheel ellipse)
                for _, cam, f, k in views:
                    los = (pos - cam) / np.linalg.norm(pos - cam)
                    r += [(abs(float(Rt[:, 1] @ los)) - rho) / 0.08]
            r += list(np.degrees(dlt) / 25.0)
            if prior is not None:
                r += list(np.degrees(air.logm_so3(prior(t) @ Rt.T)) / 45.0)
            return np.array(r)
        best = None
        for g in ([0, 0, 0], [0.2, 0, 0], [-0.2, 0, 0], [0, 0.2, 0], [0, -0.2, 0], [0, 0, 0.2], [0, 0, -0.2]):
            sol = least_squares(resid, np.array(g, float), x_scale=0.2)
            if best is None or sol.cost < best.cost:
                best = sol
        R = air.expm_so3(best.x) @ Rp
        n_, y_, z_ = R[:, 0], R[:, 1], R[:, 2]
        res[fr] = {"t": t, "R": R.tolist(), "cost": float(best.cost),
                   "nose": [round(float(v), 3) for v in n_], "left": [round(float(v), 3) for v in y_],
                   "top": [round(float(v), 3) for v in z_],
                   "fit": [[round(v, 1) for v in shape(R, cam, pos, f)] for _, cam, f, k in meas],
                   "meas": [m[0][:3] for m in meas]}
        print(f"f{fr} t{t:.2f} cost {best.cost:6.2f} nose {np.round(n_, 2)} top {np.round(z_, 2)} "
              f"| fit {res[fr]['fit']} meas {res[fr]['meas']}", flush=True)
    json.dump(res, open(out, "w"))


if __name__ == "__main__":
    main()
