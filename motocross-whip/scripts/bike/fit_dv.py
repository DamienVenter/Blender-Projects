"""Cameras of Damien's own photos, fitted to the model, stored with the other fitted views.

python3 fit_dv.py PARTS.npz            writes research/bike-cameras-damien.json

build_bike.py makes each entry a camera (its "name"), parented to the bike's root like Honda's studio cameras, with
the photo's own size, so a render lands on the photo. Same convention as bike-cameras.json and bike-cameras-34.json
(axle-line frame: C the position, R / U / F the camera's right, up and forward axes, f the focal length in pixels of
the photo, "size" its width and height in pixels).

dv03_left_rear: photo 03 of 2026-11-10 (`03_right-side-shroud-seat-frame.jpg`, 739 x 1600). It shows the LEFT side
from behind (chain, chain slider and shift lever are on the bike's left; reference/damien-bike-2026-11-10/README.md).
Nine landmarks read by eye on gridded zooms of the photo (decision 37, 2026-11-13): the left panel bolt, six points of
the left side panel's graphics (kit_sidepanel.py art px: the intake's front tip and low corner, the name's three
corners, P's foot), the left grip's end and the bar pad (model points, EST: the bars may be turned in the photo, so
they weigh half). A side panel point's x and z come from its art px (kit.json's crop of kit_template's side view),
its y from the side panel's outer skin there. Seven unknowns: position, rotation and focal length (the photo is a
crop of the phone's frame, so the lens is free; a weak prior pulls it toward a phone's 26 mm).
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_template as kt   # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(PROJECT, "research", "bike-cameras-damien.json")
KIT = os.path.join(PROJECT, "textures", "damien-v1", "kit.json")

PHOTOS = {
    "dv03_left_rear": dict(
        file="reference/damien-bike-2026-11-10/03_right-side-shroud-seat-frame.jpg", size=(739, 1600),
        # name: (model point, photo px, weight); model point: ("bolt",), ("art", ax, ay) or ("xyz", x, y, z)
        landmarks={
            "bolt": (("bolt",), (475, 1057), 1.0),
            "intake_tip": (("art", 1246, 623), (488, 853), 1.0),
            "intake_low": (("art", 1453, 712), (531, 918), 0.7),
            "name_footleft": (("art", 1461, 1172), (483, 1076), 1.0),
            "name_topright": (("art", 1821, 1027), (530, 1063), 1.0),
            "name_footright": (("art", 1815, 1094), (530, 1080), 1.0),
            "P_foot": (("art", 1060, 617), (481, 851), 0.7),
            "bar_L": (("xyz", 0.910, 0.4135, 1.207), (22, 418), 0.5),
            "pad": (("xyz", 0.99, 0.0, 1.18), (345, 437), 0.5),
        },
        lens_prior=(26.0, 0.05)),
}


def part(d, name):
    V, S, F = d[name + "__V"].astype(float), d[name + "__S"], d[name + "__F"]
    st = np.concatenate([[0], np.cumsum(S)[:-1]])
    return V, [F[a:a + n] for a, n in zip(st, S)]


def outer_y(V, faces, x, z):
    """The largest y of the mesh's faces over (x, z): its outer skin seen from the left. A point on an opening's edge
    (the intake's tip and corner) takes the skin's largest y within a few mm round it."""
    T = np.array([(f[0], f[i], f[i + 1]) for f in faces for i in range(1, len(f) - 1)])
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = (B - A)[:, [0, 2]], (C - A)[:, [0, 2]]
    r = np.array([x, z]) - A[:, [0, 2]]
    det = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
    ok = np.abs(det) > 1e-14
    det = np.where(ok, det, 1.0)
    u = (r[:, 0] * e2[:, 1] - r[:, 1] * e2[:, 0]) / det
    v = (e1[:, 0] * r[:, 1] - e1[:, 1] * r[:, 0]) / det
    inside = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    y = A[:, 1] * (1 - u - v) + B[:, 1] * u + C[:, 1] * v
    if inside.any():
        return float(y[inside].max())
    dist = np.hypot((A[:, 0] + B[:, 0] + C[:, 0]) / 3 - x, (A[:, 2] + B[:, 2] + C[:, 2]) / 3 - z)
    for r_ in (0.003, 0.008, 0.015):
        near = dist < r_
        if near.any():
            return float(np.maximum(np.maximum(A[near, 1], B[near, 1]), C[near, 1]).max())
    raise ValueError(f"no side panel face near x {x:.3f} z {z:.3f}")


def model_points(d, spec):
    kit = json.load(open(KIT))
    p = next(q for q in kit["panels"] if q.get("art") == "art/sidepanel_L.png")
    u0, v0, u1, v1 = p["crop"]
    pl, pt = p.get("pad", [0, 0])
    k = 2752 / ((u1 - u0) + 2 * pl)                          # kit_sidepanel.W art px over the padded crop
    V, faces = part(d, "side_panels")
    keep = [f for f in faces if V[list(f), 1].mean() > 0]
    out = {}
    for name, (src, _, _) in spec.items():
        if src[0] == "bolt":
            Vb, _ = part(d, "panel_bolts")
            left = Vb[Vb[:, 1] > 0]
            out[name] = np.array([left[:, 0].mean(), left[:, 1].max(), left[:, 2].mean()])
        elif src[0] == "art":
            u, v = src[1] / k + u0 - pl, src[2] / k + v0 - pt
            x, z = kt.X1 - u / kt.PPM, kt.Z1 - v / kt.PPM
            out[name] = np.array([x, outer_y(V, keep, x, z), z])
        else:
            out[name] = np.array(src[1:], float)
    return out


def project(x, X, size):
    W, H = size
    C, R, f = x[:3], Rot.from_rotvec(x[3:6]).as_matrix(), x[6] / 36.0 * max(W, H)
    q = (np.asarray(X) - C) @ R
    return np.stack([W / 2 + f * q[..., 0] / -q[..., 2], H / 2 - f * q[..., 1] / -q[..., 2]], -1)


def look(C, T):
    f = np.asarray(T, float) - C
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    return Rot.from_matrix(np.stack([r, np.cross(r, f), -f], 1)).as_rotvec()


def fit(d, ph):
    P = model_points(d, ph["landmarks"])
    lens0, w0 = ph["lens_prior"]

    def res(x):
        out = []
        for k, (_, uv, w) in ph["landmarks"].items():
            out += list((project(x, P[k], ph["size"]) - uv) * w)
        return out + [(x[6] - lens0) * w0]
    best = None
    for C0 in ([-0.4, 0.7, 1.5], [-0.2, 0.5, 1.4], [-0.8, 0.5, 1.6], [-1.2, 0.6, 1.5], [0.0, 0.8, 1.3]):
        for lens in (26.0, 40.0, 60.0):
            r = least_squares(res, np.r_[C0, look(np.array(C0), [0.6, 0.0, 0.9]), lens])
            if best is None or r.cost < best.cost:
                best = r
    x = best.x
    R = Rot.from_rotvec(x[3:6]).as_matrix()
    W, H = ph["size"]
    resid = {k: round(float(np.linalg.norm(project(x, P[k], ph["size"]) - uv)), 1)
             for k, (_, uv, _) in ph["landmarks"].items()}
    return {"C": x[:3].tolist(), "R": R[:, 0].tolist(), "U": R[:, 1].tolist(), "F": (-R[:, 2]).tolist(),
            "f": float(x[6] / 36.0 * max(W, H)), "lens_mm": float(x[6]), "size": list(ph["size"]),
            "file": ph["file"], "residuals_px": resid,
            "landmarks": {k: [list(src), list(uv), w] for k, (src, uv, w) in ph["landmarks"].items()},
            "source": "scripts/bike/fit_dv.py (decision 37 round 2)"}


def main(parts):
    d = np.load(parts)
    out = {}
    for name, ph in PHOTOS.items():
        e = fit(d, ph)
        out[name] = dict(name=name, **e)
        print(name, "lens %.1f mm" % e["lens_mm"], "C", np.round(e["C"], 3), "F", np.round(e["F"], 3),
              "residuals px", e["residuals_px"])
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main(sys.argv[1])
