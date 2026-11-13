"""Damien's body: MakeHuman's base mesh shaped to his measurements, with the default skeleton and skin weights.

python3 body.py OUT.npz        (needs tools/fetch_makehuman.sh)

Sources (PROJECT.md decisions 7, 21, 32):
  stature 1.85 m, body mass 80 kg (Damien); male; build "lean and athletic" (Damien, 2026-11-13); age not given:
  25 years (MakeHuman's young adult, age 0.5); race mix and proportions at MakeHuman's neutral defaults (no
  evidence either way; the face is behind the helmet and goggles).
  Mass to volume: tissue density 1.065 kg/L for a lean man of about 15 % body fat (Siri: fat % = 495 / D - 450),
  plus about 3.1 L of gas (lungs at functional residual capacity about 3.0 L for a 1.85 m man, gut 0.1 L) that the
  closed skin surface also encloses: 80 / 1.065 + 3.1 = 78.2 L.
The height slider is solved for the stature (top of the head to the sole) and the weight slider for the volume.
MakeHuman's average-weight man at 1.85 m is slim (72.9 L: 68 kg, BMI 20) and more muscle makes the body tighter,
not bigger, so his 80 kg (BMI 23.4) needs the weight slider near 0.7 whatever the muscle; muscle 0.75 gives the
lean athletic definition (the "maxmuscle" end is a bodybuilder).

Output (MB frame of mhdata: metres, z up, facing -y, left at +x):
  V (n, 3), faces as a flat index list with sizes (FS), face-corner UVs (UV), the skeleton (bone names, heads,
  tails, rolls, parents) and skin weights (per bone: vertex ids and weights), plus the settings and the checks.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mhdata as mh  # noqa: E402

STATURE = 1.85                      # m, Damien
MASS = 80.0                         # kg, Damien (gear is separate: about 8.5 kg)
TISSUE_DENSITY = 1.065              # kg/L, about 15 % fat (Siri)
GAS = 3.1                           # L inside the skin: lungs at FRC about 3.0, gut about 0.1
VOLUME = MASS / TISSUE_DENSITY + GAS
MUSCLE = 0.75                       # lean and athletic (Damien)


def damien_macro(height, weight):
    m = dict(mh.DEFAULT_MACRO, gender=1.0, age=0.5, muscle=MUSCLE, height=height, weight=weight)
    m["race"] = dict(mh.DEFAULT_MACRO["race"])
    return m


class Body:
    def __init__(self):
        self.base = mh.Base()
        F, T = self.base.faces("body")
        self.F, self.T = F, T
        self.tris = np.array([[f[0], f[i], f[i + 1]] for f in F for i in range(1, len(f) - 1)])
        self.bv = self.base.group_verts("body")

    def mesh(self, m):
        return mh.to_mb(mh.shape(self.base, m))

    def stature(self, V):
        z = V[self.bv, 2]
        return z.max() - z.min()

    def volume(self, V):
        a, b, c = V[self.tris[:, 0]], V[self.tris[:, 1]], V[self.tris[:, 2]]
        return abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6 * 1000.0        # litres

    def solve(self):
        """Height slider for the stature, weight slider for the volume (secant on each, alternating)."""
        h, w = 0.59, 0.55
        for _ in range(6):
            f = lambda hh: self.stature(self.mesh(damien_macro(hh, w))) - STATURE
            h0, h1 = h - 0.02, h + 0.02
            for _ in range(8):
                f0, f1 = f(h0), f(h1)
                if abs(f1) < 1e-5 or f1 == f0:
                    break
                h0, h1 = h1, h1 - f1 * (h1 - h0) / (f1 - f0)
            h = h1
            g = lambda ww: self.volume(self.mesh(damien_macro(h, ww))) - VOLUME
            w0, w1 = w - 0.03, w + 0.03
            for _ in range(8):
                g0, g1 = g(w0), g(w1)
                if abs(g1) < 1e-3 or g1 == g0:
                    break
                w0, w1 = w1, w1 - g1 * (w1 - w0) / (g1 - g0)
            w = w1
        return h, w


def build():
    body = Body()
    h, w = body.solve()
    m = damien_macro(h, w)
    V = body.mesh(m)
    V[:, 2] -= V[body.bv, 2].min()                              # soles on z = 0
    rig = mh.rig()
    J = mh.joint_positions(body.base, V, rig)
    names = list(rig)
    W = mh.weights()
    keep = np.zeros(len(V), bool)
    keep[body.bv] = True
    remap = -np.ones(len(V), int)                               # body vertices only, renumbered
    remap[body.bv] = np.arange(len(body.bv))
    F = [[remap[i] for i in f] for f in body.F]
    UV = np.array([body.base.VT[t] for tt in body.T for t in tt])
    wid, wv, wb = [], [], []
    for bi, n in enumerate(names):
        for vi, x in W.get(n, []):
            if keep[vi]:
                wid.append(remap[vi])
                wv.append(x)
                wb.append(bi)
    checks = dict(stature=float(body.stature(V)), volume_l=float(body.volume(V)), mass_kg=float(
        (body.volume(V) - GAS) * TISSUE_DENSITY), height_slider=float(h), weight_slider=float(w), muscle=MUSCLE)
    return dict(V=V[body.bv], FS=np.array([len(f) for f in F]), F=np.concatenate(F), UV=UV,
                bones=np.array(names), heads=np.array([J[n][0] for n in names]),
                tails=np.array([J[n][1] for n in names]), rolls=np.array([rig[n].get("roll", 0.0) for n in names]),
                parents=np.array([rig[n]["parent"] or "" for n in names]),
                connect=np.array([bool(rig[n].get("use_connect", False)) for n in names]),
                w_vert=np.array(wid), w_val=np.array(wv), w_bone=np.array(wb),
                meta=json.dumps(dict(macro=m, checks=checks)))


if __name__ == "__main__":
    d = build()
    np.savez_compressed(sys.argv[1], **d)
    print(json.loads(str(d["meta"]))["checks"])
