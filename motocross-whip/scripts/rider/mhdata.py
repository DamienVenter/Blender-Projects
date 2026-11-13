"""MakeHuman data (CC0) read directly: the base mesh, shape targets, macro modifiers and the default skeleton.

The data comes from MPFB 2.0.18 (tools/fetch_makehuman.sh puts it in $MH_DATA, default
~/.cache/makehuman/mpfb-2.0.18/data). MPFB's code is not used; the macro rules below follow MakeHuman's published
scheme (data/targets/macrodetails/macro.json): every macro slider is split into the two neighbouring named levels
with linear weights, and the shape is the base mesh plus the weighted sum of
  macrodetails/<race>-<gender>-<age>                                         (race mix x gender x age)
  macrodetails/universal-<gender>-<age>-<muscle>-<weight>
  macrodetails/height/<gender>-<age>-<muscle>-<weight>-<min|max>height
  macrodetails/proportions/<gender>-<age>-<muscle>-<weight>-<uncommon|ideal>proportions
(the breast targets apply to female shapes only).

Frames. MakeHuman's own: decimetres, y up, the body faces +z, its left side at +x. MB ("MPFB Blender", the frame
of the rig file's numbers): metres, z up, facing -y, left at +x: MB = 0.1 * (x, -z, y). The rider is built in MB
and turned to the bike's frame (x forward, y left, z up) by one rotation of +90 deg about z (rider.py).
"""
import gzip
import json
import os

import numpy as np

DATA = os.environ.get("MH_DATA", os.path.join(os.path.expanduser("~"), ".cache", "makehuman", "mpfb-2.0.18"))
DATA = os.path.join(DATA, "data") if os.path.isdir(os.path.join(DATA, "data")) else DATA

DEFAULT_MACRO = dict(gender=0.5, age=0.5, muscle=0.5, weight=0.5, proportions=0.5, height=0.5, cupsize=0.5,
                     firmness=0.5, race=dict(african=1 / 3, asian=1 / 3, caucasian=1 / 3))


def path(*p):
    f = os.path.join(DATA, *p)
    if not os.path.exists(f):
        raise FileNotFoundError(f"{f}: run tools/fetch_makehuman.sh (MakeHuman data, CC0)")
    return f


class Base:
    """base.obj: every vertex (the body and the helper geometry share one vertex list, as the targets index it),
    UVs, and faces by group ('body', 'helper-*', 'joint-*')."""

    def __init__(self):
        V, VT, groups = [], [], {}
        g = None
        for line in open(path("3dobjs", "base.obj")):
            if line.startswith("v "):
                V.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("vt "):
                VT.append([float(x) for x in line.split()[1:3]])
            elif line.startswith("g "):
                g = line.split()[1]
                groups.setdefault(g, [])
            elif line.startswith("f "):
                tok = [t.split("/") for t in line.split()[1:]]
                groups[g].append(([int(t[0]) - 1 for t in tok], [int(t[1]) - 1 if len(t) > 1 and t[1] else -1
                                                                   for t in tok]))
        self.V = np.array(V)
        self.VT = np.array(VT)
        self.groups = groups

    def faces(self, group="body"):
        return [f for f, _ in self.groups[group]], [t for _, t in self.groups[group]]

    def group_verts(self, group):
        return np.unique(np.concatenate([np.array(f) for f, _ in self.groups[group]]))


_CACHE = {}


def target(name):
    """A target: (vertex indices, offsets in MakeHuman's frame). Empty targets (the average shape) are allowed."""
    if name in _CACHE:
        return _CACHE[name]
    idx, d = [], []
    for line in gzip.open(path("targets", name + ".target.gz"), "rt"):
        s = line.split()
        if len(s) == 4 and not line.startswith("#"):
            idx.append(int(s[0]))
            d.append([float(x) for x in s[1:]])
    out = (np.array(idx, int), np.array(d).reshape(-1, 3))
    _CACHE[name] = out
    return out


def _components(macro, name, value):
    out = []
    for p in macro["macrotargets"][name]["parts"]:
        lo, hi = p["lowest"], p["highest"]
        if lo < value < hi:
            t = (value - lo) / (hi - lo)
            if p["low"]:
                out.append((p["low"], 1 - t))
            if p["high"]:
                out.append((p["high"], t))
    return out


def macro_stack(m, cutoff=0.01):
    """The weighted targets of a macro setting (dict like DEFAULT_MACRO), as MakeHuman combines them."""
    macro = json.load(open(path("targets", "macrodetails", "macro.json")))
    c = {k: _components(macro, k, m[k]) for k in ("gender", "age", "muscle", "weight", "proportions", "height")}
    out = []
    for race, rw in m["race"].items():
        if rw > 1e-4:
            for a, wa in c["age"]:
                for g, wg in c["gender"]:
                    if rw * wg * wa > cutoff:
                        out.append((f"macrodetails/{race}-{g}-{a}", rw * wg * wa))
    for g, wg in c["gender"]:
        for a, wa in c["age"]:
            for mu, wm in c["muscle"]:
                for we, ww in c["weight"]:
                    w = wg * wa * wm * ww
                    if w > cutoff:
                        out.append((f"macrodetails/universal-{g}-{a}-{mu}-{we}", w))
                    for h, wh in c["height"]:
                        if w * wh > cutoff:
                            out.append((f"macrodetails/height/{g}-{a}-{mu}-{we}-{h}", w * wh))
                    for pr, wp in c["proportions"]:
                        if w * wp > cutoff and a != "baby":
                            out.append((f"macrodetails/proportions/{g}-{a}-{mu}-{we}-{pr}", w * wp))
    cf = {k: _components(macro, k, m[k]) for k in ("cupsize", "firmness")}
    for g, wg in c["gender"]:
        if g != "female":
            continue
        for a, wa in c["age"]:
            for mu, wm in c["muscle"]:
                for we, ww in c["weight"]:
                    for cu, wc in cf["cupsize"]:
                        for fi, wf in cf["firmness"]:
                            w = wg * wa * wm * ww * wc * wf
                            n = f"breast/{g}-{a}-{mu}-{we}-{cu}-{fi}"
                            if w > cutoff and "averagecup-averagefirmness" not in n and a != "baby":
                                out.append((n, w))
    return out


def shape(base, m, extra=()):
    """Vertices (MakeHuman frame) for macro setting m plus extra (target name, weight) pairs."""
    V = base.V.copy()
    for name, w in list(macro_stack(m)) + list(extra):
        idx, d = target(name)
        if len(idx):
            V[idx] += w * d
    return V


def to_mb(V):
    """MakeHuman frame -> MB frame (metres, z up, facing -y, left at +x)."""
    V = np.asarray(V, float)
    return 0.1 * np.stack([V[:, 0], -V[:, 2], V[:, 1]], axis=1)


def rig(name="default"):
    return json.load(open(path("rigs", "standard", f"rig.{name}.json")))


def weights(name="default"):
    return json.load(open(path("rigs", "standard", f"weights.{name}.json")))["weights"]


def joint_positions(base, Vmb, rigdef):
    """Head and tail of every bone (MB frame) from the shaped mesh: CUBE = centre of the joint helper cube,
    VERTEX = one vertex, MEAN = the mean of a few vertices (MakeHuman's rule)."""
    cubes = {}

    def point(spec):
        s = spec["strategy"]
        if s == "CUBE":
            n = spec["cube_name"]
            if n not in cubes:
                cubes[n] = Vmb[base.group_verts("joint-" + n if not n.startswith("joint-") else n)].mean(0)
            return cubes[n]
        if s == "VERTEX":
            return Vmb[spec["vertex_index"]]
        if s == "MEAN":
            return Vmb[spec["vertex_indices"]].mean(0)
        raise ValueError(s)
    return {b: (point(v["head"]), point(v["tail"])) for b, v in rigdef.items()}
