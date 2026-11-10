"""Whole-bike audit in Blender: parts that cut through each other, and pieces that hang in the air.

blender -b BIKE.blend --python-exit-code 1 --python audit.py -- [OUT.json] [min_pairs]

clashes   every pair of objects whose surfaces intersect, with the number of intersecting face pairs, how deep one
          goes into the other (largest distance of a vertex of one inside the other, mm), the box round the
          intersecting faces and the deepest point (world: on the ground, not the axle-line frame). A bolt seated in a cover
          gives a handful of pairs and a millimetre or two; a caliper through a fork guard gives hundreds and centimetres.
floating  loose pieces of a mesh further than 4 mm from every other surface of the bike, other pieces of the same
          mesh included (a bolt that missed its boss).
Modifiers are applied first (solidify, bevel), so the audit sees what the render sees.
"""
import json
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
MIN_PAIRS = int(argv[1]) if len(argv) > 1 else 25
SKIP = {"cyc", "floor"}


def world_mesh(ob, dg):
    me = ob.evaluated_get(dg).to_mesh()
    M = ob.matrix_world
    V = [M @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    N = [(M.to_3x3() @ p.normal).normalized() for p in me.polygons]
    return V, F, N


def components(n, F):
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for f in F:
        r = find(f[0])
        for i in f[1:]:
            parent[find(i)] = r
    return np.array([find(i) for i in range(n)])


def main():
    dg = bpy.context.evaluated_depsgraph_get()
    obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name not in SKIP]
    data = {}
    for o in obs:
        V, F, N = world_mesh(o, dg)
        if not F:
            continue
        A = np.array([tuple(v) for v in V])
        FC = np.array([A[list(f)].mean(axis=0) for f in F])                      # face centres and radii
        FR = np.array([np.abs(A[list(f)] - c).max() for f, c in zip(F, FC)])
        data[o.name] = dict(V=V, F=F, N=N, bvh=BVHTree.FromPolygons(V, F), lo=A.min(axis=0), hi=A.max(axis=0), A=A,
                            FC=FC, FR=FR, F0=np.array([f[0] for f in F]))
    names = sorted(data)
    clashes = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            da, db = data[a], data[b]
            if (da["lo"] > db["hi"]).any() or (db["lo"] > da["hi"]).any():
                continue
            pairs = da["bvh"].overlap(db["bvh"])
            if len(pairs) < MIN_PAIRS:
                continue
            # depth: vertices of the faces involved, measured to the other surface along its normal
            depth, deepest = 0.0, None
            for src, dst, col in ((da, db, 0), (db, da, 1)):
                vs = {v for p in pairs[:4000] for v in src["F"][p[col]]}
                for vi in list(vs)[:600]:
                    hit = dst["bvh"].find_nearest(src["V"][vi])
                    if hit[0] is None:
                        continue
                    d = (src["V"][vi] - hit[0]).dot(hit[1])
                    if d < -depth:                              # behind the other surface: inside it
                        depth, deepest = -d, src["V"][vi]
            # where: the box round the intersecting faces of a, and the deepest point (root frame = world here)
            P = da["A"][sorted({v for p in pairs[:4000] for v in da["F"][p[0]]})]
            clashes.append(dict(a=a, b=b, pairs=len(pairs), depth_mm=round(depth * 1000, 1),
                                lo=[round(float(v), 3) for v in P.min(axis=0)], hi=[round(float(v), 3) for v in P.max(axis=0)],
                                deepest=[round(float(v), 3) for v in deepest] if deepest is not None else None))
    clashes.sort(key=lambda c: (-c["depth_mm"], -c["pairs"]))
    floating = []
    for a in names:
        d = data[a]
        comp = components(len(d["V"]), d["F"])
        labels, counts = np.unique(comp, return_counts=True)
        if len(labels) < 2 and len(names) < 2:
            continue
        others = [data[b]["bvh"] for b in names if b != a]
        for lab, cnt in zip(labels, counts):
            idx = np.nonzero(comp == lab)[0]
            rest = np.nonzero(comp != lab)[0]
            pts = idx[:: max(len(idx) // 40, 1)]
            best = 1e9
            for vi in pts:
                p = d["V"][vi]
                for bvh in others:
                    hit = bvh.find_nearest(p, best if best < 1e8 else 1.0)
                    if hit[0] is not None:
                        best = min(best, (p - hit[0]).length)
                if best < 0.004:
                    break
            if best >= 0.004 and len(rest):                     # other loose pieces of the same object count too:
                near = d["A"][rest]                             # distance to their SURFACE (a bolt on a big flat face
                c0, rad = d["A"][idx].mean(axis=0), np.ptp(d["A"][idx], axis=0).max()   # is far from its corners)
                fidx = np.nonzero(comp[d["F0"]] != lab)[0]
                fc = d["FC"][fidx]
                fidx = fidx[np.abs(fc - c0).max(axis=1) < rad + d["FR"][fidx] + 0.02]
                if len(fidx):
                    bvh = BVHTree.FromPolygons(d["V"], [d["F"][i] for i in fidx])
                    for vi in pts:
                        hit = bvh.find_nearest(d["V"][vi], 0.05)
                        if hit[0] is not None:
                            best = min(best, (d["V"][vi] - hit[0]).length)
            if best >= 0.004:
                c = d["A"][idx].mean(axis=0)
                floating.append(dict(part=a, verts=int(cnt), gap_mm=round(best * 1000, 1),
                                     at=[round(float(v), 3) for v in c]))
    floating.sort(key=lambda f: -f["gap_mm"])
    print("CLASHES (deepest first):")
    for c in clashes[:40]:
        print("  %-16s x %-16s %6d face pairs, %6.1f mm deep  box %s..%s deepest %s"
              % (c["a"], c["b"], c["pairs"], c["depth_mm"], c["lo"], c["hi"], c["deepest"]))
    print("FLOATING pieces:", len(floating))
    for f in floating[:40]:
        print("  %-16s %5d verts, %6.1f mm from anything, at %s" % (f["part"], f["verts"], f["gap_mm"], f["at"]))
    if OUT:
        json.dump(dict(clashes=clashes, floating=floating), open(OUT, "w"), indent=1)
    print("AUDIT DONE", len(names), "objects,", len(clashes), "clashes,", len(floating), "floating")


main()
