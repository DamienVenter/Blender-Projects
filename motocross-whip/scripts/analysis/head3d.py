"""Damien's head (helmet centre) in 3D relative to the bike, from the two phones (clips 2 and 3, one jump).

Each phone pans with the rider, so what is measured is the helmet's pixel offset from the red plastics' bbox
centre (helmet.py, bikebox.py). For a trial head position the same offset is predicted with the calibrated
cameras (cams_clips23.json) and the bike attitude solved from the same frames (fit_clips23.json): project the
head and the red parts (fit3d.red_points), take the red parts' bbox centre. Two views give four equations for the
three coordinates; all frames are solved together with a light smoothness prior (so frames where one phone lost
the helmet still get a value, held by the other phone and their neighbours).

python3 head3d.py HELM_C2.json HELM_C3.json OUT.json
OUT: {frame: {"t": s after the lip (Damien's clock), "head_bike": [x fwd, y left, z up] of the helmet centre
from the red plastics' centroid in the bike frame (m), "resid_px": [...]}}
"""
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "demo"))
from fit3d import red_points                      # noqa: E402
from attitude_overlay import trajectory          # noqa: E402

R3D = os.path.join(HERE, "..", "..", "research", "whip-attitude-3d")
W, H = 478, 850
SIG_PX = {"clip2": 3.0, "clip3": 2.5}            # helmet centre reading (px): about a quarter of its radius
SIG_SMOOTH = 0.03                                # m, second difference between frames 1/30 s apart


def size_focal(view, frames=range(33, 57)):
    """Focal length (px) at which the bike's red plastics come out the size they are in the phone's frames
    (median over the frames where the bike is tracked well). The attitude fit only uses angles, so its focal lengths
    (cams_clips23.json "f") were never checked for scale; every pixel distance (the helmet) needs this one."""
    from attitude_overlay import trajectory
    cams = json.load(open(os.path.join(R3D, "cams_clips23.json")))
    fit = json.load(open(os.path.join(R3D, "fit_clips23.json")))
    box = json.load(open(os.path.join(R3D, f"box_c{view[-1]}.json")))
    pts, _ = red_points()
    m = pts.mean(axis=0)
    ts, pbs = trajectory()
    cam, f = np.array(cams[view]["cam"]), float(cams[view]["f"])
    ratios = []
    for fr in frames:
        if str(fr) not in fit or box[str(fr)][4] < 40:
            continue
        t = (fr - cams["lip_frame"]) / 30.0
        pos = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
        uv = project(cam, pos, f, pos + (np.array(fit[str(fr)]["R"]) @ (pts - m).T).T)
        size = np.percentile(uv, 98, axis=0) - np.percentile(uv, 2, axis=0)
        ratios.append(np.hypot(*box[str(fr)][2:4]) / np.hypot(*size))
    return f * float(np.median(ratios))


def zoom_track(view, f_first=30, f_last=87, min_px=None, start=0.13):
    """The phone's focal length frame by frame (it zooms: clip 2 goes from about 1300 to 1840 px between 0.3 and
    0.8 s), from the bike's red plastics' size in each frame against the model at the fit's focal length. Frames
    where little red shows (off the lip, in the trees; late clip 3) are left out; the track is a smoothing spline
    held flat before START and after the last good frame. Returns (t, f) every 1/30 s from 0 to the last frame."""
    from scipy.interpolate import UnivariateSpline
    from attitude_overlay import trajectory
    cams = json.load(open(os.path.join(R3D, "cams_clips23.json")))
    fit = json.load(open(os.path.join(R3D, "fit_clips23.json")))
    box = json.load(open(os.path.join(R3D, f"box_c{view[-1]}.json")))
    pts, _ = red_points()
    m = pts.mean(axis=0)
    ts, pbs = trajectory()
    cam, f = np.array(cams[view]["cam"]), float(cams[view]["f"])
    min_px = min_px if min_px is not None else (400 if view == "clip2" else 140)
    T, Fv = [], []
    for fr in range(f_first, f_last + 1):
        if str(fr) not in fit or str(fr) not in box or box[str(fr)][4] < min_px:
            continue
        t = (fr - cams["lip_frame"]) / 30.0
        if t < start:
            continue
        pos = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
        uv = project(cam, pos, f, pos + (np.array(fit[str(fr)]["R"]) @ (pts - m).T).T)
        size = np.percentile(uv, 98, axis=0) - np.percentile(uv, 2, axis=0)
        T.append(t)
        Fv.append(np.hypot(*box[str(fr)][2:4]) / np.hypot(*size) * f)
    T, Fv = np.array(T), np.array(Fv)
    spl = UnivariateSpline(T, Fv, k=3, s=len(T) * (0.03 * np.median(Fv)) ** 2)
    grid = np.arange(0.0, (f_last - cams["lip_frame"]) / 30.0 + 1e-9, 1 / 30)
    return grid, np.array([float(spl(min(max(t, T[0]), T[-1]))) for t in grid])


def project(cam, look, f, P):
    fwd = look - cam
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    d = P - cam
    z = d @ fwd
    return np.stack([W / 2 + f * (d @ right) / z, H / 2 - f * (d @ up) / z], axis=-1)


def main():
    helm = {"clip2": json.load(open(sys.argv[1])), "clip3": json.load(open(sys.argv[2]))}
    out_path = sys.argv[3]
    cams = json.load(open(os.path.join(R3D, "cams_clips23.json")))
    fit = json.load(open(os.path.join(R3D, "fit_clips23.json")))
    pts, _ = red_points()
    m_red = pts.mean(axis=0)
    ts, pbs = trajectory()
    lip = cams["lip_frame"]
    frames = [f for f in sorted(map(int, fit)) if str(f) in helm["clip2"] or str(f) in helm["clip3"]]
    frames = [f for f in frames if any(helm[v].get(str(f), [0, 0, 0, 0])[3] for v in helm)]
    frames = list(range(frames[0], frames[-1] + 1))
    data = []
    for f in frames:
        t = (f - lip) / 30.0
        pos = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
        RA = np.array(fit[str(f)]["R"]) if str(f) in fit else None
        views = []
        for v in ("clip2", "clip3"):
            h = helm[v].get(str(f))
            if h and h[3] and RA is not None:
                cam, fl = np.array(cams[v]["cam"]), cams[v]["f_size"]
                red = project(cam, pos, fl, pos + (RA @ (pts - m_red).T).T)
                lo, hi = np.percentile(red, 2, axis=0), np.percentile(red, 98, axis=0)
                views.append((v, cam, fl, 0.5 * (lo + hi), np.array(h[:2])))
        data.append((f, t, pos, RA, views))

    n = len(data)

    def resid(x):
        X = x.reshape(n, 3)
        r = []
        for i, (f, t, pos, RA, views) in enumerate(data):
            for v, cam, fl, redc, meas in views:
                r += list((project(cam, pos, fl, pos + X[i]) - redc - meas) / SIG_PX[v])
        r += list((np.diff(X, 2, axis=0) / SIG_SMOOTH).ravel())
        return np.array(r)

    x0 = np.tile([-0.3, 0.0, 0.6], n)
    sol = least_squares(resid, x0, x_scale=0.3)
    X = sol.x.reshape(n, 3)
    res = {}
    for i, (f, t, pos, RA, views) in enumerate(data):
        rp = [float(np.linalg.norm(project(cam, pos, fl, pos + X[i]) - redc - meas)) for v, cam, fl, redc, meas in views]
        hb = (RA.T @ X[i]).tolist() if RA is not None else None
        res[f] = {"t": t, "head_world": X[i].tolist(), "head_bike": hb, "views": [v[0] for v in views],
                  "resid_px": [round(e, 2) for e in rp]}
        print(f"f{f} t {t:.2f} views {','.join(v[0][-1] for v in views):4s} head_bike "
              f"{np.round(hb, 2) if hb else None} resid px {res[f]['resid_px']}")
    json.dump(res, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
