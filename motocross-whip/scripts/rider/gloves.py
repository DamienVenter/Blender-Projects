"""Damien's gloves: Leatt Moto 2.5 X-Flow, Black, size L (MY26 6024090152 / MY27 6027010262). Both hands.

python3 gloves.py BODY.npz OUT.npz          build both gloves (gear npz for build_rider.py) and their textures
python3 gloves.py preview BODY.npz OUT.png  flat matplotlib views of the left glove (no Blender)

Numbers and their sources: research/rider-ledger/gloves.md. Frames: body.py's MB rest frame (metres, z up, facing
-y, his left at +x). Each hand has a local frame (hand_frame): origin at the wrist joint, x toward the thumb, y toward
the fingers (wrist joint to the middle finger's knuckle), z out of the palm; the forearm axis runs from the forearm's
joint toward the wrist and s is the distance along it from the wrist joint (negative up the forearm).

How the glove is made (as the real one is): the glove is the hand's own skin pushed out (the hand patch of the body
mesh distal of the clean edge ring round the wrist, plus rings up the forearm to the cuff's top), subdivided once by
Catmull-Clark and offset along its normals: 1.0 mm over the hand (X-Flow mesh and NanoGrip are thin), 2 mm more room
at the fingertips, rising over the wrist to the cuff that goes over the jersey sleeve. Every glove vertex is a fixed
linear combination of body vertices, so its skin weights are the same combination of the body's weights: the glove
closes round the grip with the hand. The right glove is the left one's mirror (the body is exactly symmetric; its own
vertices and weights are used). Panels (back, palm, finger sides, tips, cuff) are UV charts projected along their
own direction, about isometric, so textures drawn in millimetres stay true; colours and relief are painted per texel
from 3D positions, so seams between charts do not show.
"""
import json
import math
import os
import sys

import numpy as np
try:
    from scipy import sparse
except ImportError:                          # Blender's Python (check mode needs no scipy)
    sparse = None

HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.join(HERE, "..", "..", "textures", "rider")

# ---- numbers (sources in research/rider-ledger/gloves.md) -------------------------------------------------------
SIZE = "L"                      # Leatt glove chart: L = knuckle circumference 22-23 cm, hand length 20 cm
CHART = {"XS": (18, 19, 18.5), "S": (20, 21, 19), "M": (21, 22, 19.5), "L": (22, 23, 20), "XL": (23, 24, 20.5),
         "XXL": (24, 25, 21), "XXXL": (26, 27, 21.5)}          # cm: circumference min, max; length (Leatt, 2026)
CREASE_Y = 0.005                # m: distal wrist crease, hand-local y (palmar skin valley, measured on body.npz)
CUFF_BAND = 0.032               # m: cuff band height (Leatt photos: 180 px at 0.175-0.182 mm/px by knuckle breadth)
CUFF_TOP = CREASE_Y - CUFF_BAND  # s of the cuff's top edge (-27 mm)
OFF_HAND = 0.0010               # m: glove outer surface over the skin on the hand (fabric 0.6 mm + 0.4 mm ease)
OFF_CUFF = 0.0040               # m: cuff outer surface over the skin (jersey sleeve end under it, elastic 1.2 mm)
CUFF_WALL = 0.0012              # m: cuff elastic thickness (the hem shows it)
HEM = 0.008                     # m: turned-in hem depth inside the cuff
TIP_ROOM = 0.002                # m: glove fingertip beyond the skin's tip (seam allowance and room)
BRIDGE_MAX = 0.0015             # m: fabric spans skin grooves up to this deep (nail folds, joint creases)
STRAP_W = 0.024                 # m: hook-and-loop strap width (Leatt photos: 140 of 190 px of the band)
STRAP_T = 0.0016                # m: strap thickness
TAB = (0.028, 0.0075, 0.0022)   # m: white pull: length round the wrist, height, thickness (photo: 160 x 40 px)
TEX = 2048                      # texture size (px)


# ---- body ---------------------------------------------------------------------------------------------------------
def load_body(path):
    d = np.load(path)
    names = [str(n) for n in d["bones"]]
    V = d["V"].astype(float)
    W = sparse.csr_matrix((d["w_val"], (d["w_vert"], d["w_bone"])), shape=(len(V), len(names)))
    return dict(V=V, F=d["F"].reshape(-1, 4), names=names, J=dict(zip(names, d["heads"])),
                T=dict(zip(names, d["tails"])), W=W, d=d)


def hand_frame(B, side="L"):
    """Origin (wrist joint), rows of R: x thumbward, y fingerward, z palmar; forearm axis (distal unit vector)."""
    J, T = B["J"], B["T"]
    o = J[f"wrist.{side}"]
    f = J[f"finger3-1.{side}"] - o
    f /= np.linalg.norm(f)
    t = J[f"finger2-1.{side}"] - J[f"finger5-1.{side}"]
    t -= f * (t @ f)
    t /= np.linalg.norm(t)
    n = np.cross(f, t) if side == "L" else np.cross(t, f)
    fa = T[f"lowerarm02.{side}"] - J[f"lowerarm02.{side}"]
    fa /= np.linalg.norm(fa)
    return o, np.stack([t, f, n]), fa


def mirror_index(V):
    from scipy.spatial import cKDTree
    d, i = cKDTree(V).query(V * [-1, 1, 1])
    assert d.max() < 1e-7, "body not symmetric"
    return i


def hand_bone_groups(names, side):
    """Bone index -> segment: 0 hand (wrist, metacarpals and the thumb's first bone, which carries the thenar
    mound), 1 thumb, 2 index, 3 middle, 4 ring, 5 little, 6 forearm."""
    g = {}
    for i, n in enumerate(names):
        if not n.endswith("." + side):
            continue
        if n.startswith("finger1-1"):
            g[i] = 0
        elif n.startswith("finger"):
            g[i] = int(n[6])
        elif n.startswith("metacarpal") or n.startswith("wrist"):
            g[i] = 0
        elif n.startswith("lowerarm"):
            g[i] = 6
    return g


# ---- mesh tools ---------------------------------------------------------------------------------------------------
def edges_of(F):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 3]], F[:, [3, 0]]])
    return E


def boundary_loops(F):
    """Ordered boundary loops (lists of vertex ids, following the faces' winding)."""
    E = edges_of(F)
    key = {}
    for a, b in E:
        key[(a, b)] = True
    nxt = {a: b for a, b in E if (b, a) not in key}
    loops, seen = [], set()
    for a in list(nxt):
        if a in seen:
            continue
        loop = [a]
        seen.add(a)
        b = nxt[a]
        while b != a:
            loop.append(b)
            seen.add(b)
            b = nxt[b]
        loops.append(loop)
    return loops


def catmull_clark(F, nv):
    """One Catmull-Clark step on a quad mesh with boundaries. Returns (S, F2): new points = S @ old points
    (S sparse, (nv + ne + nf) x nv), F2 the new quads (winding kept). Boundary: cubic B-spline rule."""
    nf = len(F)
    E = edges_of(F)
    es = np.sort(E, axis=1)
    ue, inv = np.unique(es, axis=0, return_inverse=True)
    inv = inv.ravel()
    ne = len(ue)
    fe = inv.reshape(4, nf).T                                        # face -> its 4 edge ids (ab, bc, cd, da)
    efaces = [[] for _ in range(ne)]
    for k, e in enumerate(inv):
        efaces[e].append(k % nf)
    nfe = np.array([len(x) for x in efaces])
    rows, cols, vals = [], [], []

    def put(r, c, v):
        rows.extend(np.atleast_1d(r).tolist())
        cols.extend(np.atleast_1d(c).tolist())
        vals.extend(np.atleast_1d(v).tolist())
    # face points
    FPr = nv + ne + np.arange(nf)
    for k in range(4):
        put(FPr, F[:, k], np.full(nf, 0.25))
    # face point matrix as its own sparse (for reuse)
    FP = sparse.csr_matrix((np.full(4 * nf, 0.25), (np.repeat(np.arange(nf), 4), F.ravel())), shape=(nf, nv))
    # edge points
    for e in range(ne):
        a, b = ue[e]
        if nfe[e] == 2:
            put([nv + e] * 2, [a, b], [0.25, 0.25])
            for fi in efaces[e]:
                put([nv + e] * 4, F[fi], [0.0625] * 4)
        else:
            put([nv + e] * 2, [a, b], [0.5, 0.5])
    # vertex points
    vfaces = [[] for _ in range(nv)]
    for fi in range(nf):
        for v in F[fi]:
            vfaces[v].append(fi)
    vedges = [[] for _ in range(nv)]
    for e in range(ne):
        vedges[ue[e][0]].append(e)
        vedges[ue[e][1]].append(e)
    used = np.zeros(nv, bool)
    used[F.ravel()] = True
    for v in range(nv):
        if not used[v]:
            put(v, v, 1.0)
            continue
        bnd = [e for e in vedges[v] if nfe[e] == 1]
        if bnd:
            nb = [ue[e][0] if ue[e][1] == v else ue[e][1] for e in bnd]
            put([v] * 3, [v] + nb[:2], [0.75, 0.125, 0.125])
            continue
        n = len(vedges[v])
        # Q: mean of face points; R: mean of edge midpoints; P
        for fi in vfaces[v]:
            put([v] * 4, F[fi], [0.25 / len(vfaces[v]) / n] * 4)
        for e in vedges[v]:
            put([v] * 2, ue[e], [2.0 * 0.5 / len(vedges[v]) / n] * 2)
        put(v, v, (n - 3.0) / n)
    S = sparse.csr_matrix((vals, (rows, cols)), shape=(nv + ne + nf, nv))
    S.sum_duplicates()
    F2 = []
    for fi in range(nf):
        a, b, c, d = F[fi]
        eab, ebc, ecd, eda = nv + fe[fi]
        fp = nv + ne + fi
        F2 += [(a, eab, fp, eda), (b, ebc, fp, eab), (c, ecd, fp, ebc), (d, eda, fp, ecd)]
    return S, np.array(F2)


def vertex_normals(V, F):
    n = np.zeros_like(V)
    for tri in ((0, 1, 2), (0, 2, 3)):
        a, b, c = V[F[:, tri[0]]], V[F[:, tri[1]]], V[F[:, tri[2]]]
        fn = np.cross(b - a, c - a)
        for k in tri:
            np.add.at(n, F[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def ray_hits(O, D, V, T):
    """Nearest positive hit of rays (O, D) with triangles T (indices into V): (t, tri, u, v) per ray."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = b - a, c - a
    out = []
    for o, d in zip(O, D):
        p = np.cross(d, e2)
        det = np.einsum("ij,ij->i", e1, p)
        ok = np.abs(det) > 1e-14
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        s = o - a
        u = np.einsum("ij,ij->i", s, p) * inv
        q = np.cross(s, e1)
        v = (q @ d) * inv
        t = np.einsum("ij,ij->i", e2, q) * inv
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 0)
        if not hit.any():
            out.append((np.inf, -1, 0.0, 0.0))
            continue
        k = np.nonzero(hit)[0][np.argmin(t[hit])]
        out.append((t[k], k, u[k], v[k]))
    return out


def tris_of(F):
    return np.concatenate([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ---- the glove surface --------------------------------------------------------------------------------------------
def wrist_ring(B, side):
    """The clean 20-vertex edge ring round the wrist (s about -19 mm): the glove's patch of the body ends there."""
    o, R, fa = hand_frame(B, side)
    V, F = B["V"], B["F"]
    s = (V - o) @ fa
    g = hand_bone_groups(B["names"], side)
    arm = np.asarray(B["W"][:, list(g)].sum(1)).ravel() > 0.5          # hand and forearm skin of this side
    near = arm & (np.linalg.norm(V - o, axis=1) < 0.3)
    keep = (s[F] > -0.028).all(1) & near[F].all(1)
    loops = boundary_loops(F[keep])
    loops = [l for l in loops if abs(np.mean(s[l]) + 0.019) < 0.006]
    assert len(loops) == 1 and len(loops[0]) == 20, [len(l) for l in loops]
    return np.nonzero(keep)[0], loops[0]


def control_mesh(B, side="L"):
    """Control cage of the glove skin as A (sparse, n x body vertices): points = A @ body V. Patch faces of the body
    distal of the wrist ring, then rings up the forearm to the cuff's top (points on the skin by rays from the
    forearm axis, as barycentric combinations of body vertices). Returns A, faces, ring loops (cuff, ordered)."""
    o, R, fa = hand_frame(B, side)
    V = B["V"]
    fids, ring = wrist_ring(B, side)
    F = B["F"][fids]
    ids = np.unique(F)
    loc = -np.ones(len(V), int)
    loc[ids] = np.arange(len(ids))
    Fl = loc[F]
    ringl = loc[ring]
    # forearm triangles to cast on
    s = (V - o) @ fa
    r = np.linalg.norm((V - o) - np.outer(s, fa), axis=1)
    arm = (s > -0.08) & (s < 0.0) & (r < 0.06)
    Ft = B["F"][arm[B["F"]].all(1)]
    Tt = tris_of(Ft)
    e1 = np.cross(fa, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(fa, e1)
    rel = V[ring] - o
    sr = rel @ fa
    th = np.arctan2(rel @ e2, rel @ e1)
    K = 4                                                    # rings from the wrist ring to the top
    rows, cols, vals = [], [], []
    for i, b in enumerate(ids):
        rows.append(i), cols.append(b), vals.append(1.0)
    n = len(ids)
    rings = [ringl]
    for k in range(1, K + 1):
        sk = sr + (CUFF_TOP - sr) * k / K
        O = o + np.outer(sk, fa)
        D = np.outer(np.cos(th), e1) + np.outer(np.sin(th), e2)
        cur = []
        for (t, tri, u, v), oo, dd in zip(ray_hits(O, D, V, Tt), O, D):
            assert tri >= 0, "cuff ray missed the forearm"
            a, b_, c = Tt[tri]
            rows += [n] * 3
            cols += [a, b_, c]
            vals += [1 - u - v, u, v]
            cur.append(n)
            n += 1
        rings.append(np.array(cur))
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(n, len(V)))
    # quads between rings, wound like the patch (the patch's boundary loop runs with its faces' winding)
    P = A @ V
    quads = []
    for k in range(K):
        a, b = rings[k], rings[k + 1]
        for i in range(len(a)):
            j = (i + 1) % len(a)
            quads.append((a[j], a[i], b[i], b[j]))
    quads = np.array(quads)
    allF = np.vstack([Fl, quads])
    # the body's skin faces outward: check the cage does too (normals away from the bones)
    nrm = vertex_normals(P, allF)
    c = P[quads].mean(1)
    rad = (c - o) - np.outer((c - o) @ fa, fa)
    if (np.einsum("ij,ij->i", nrm[quads[:, 0]], rad) < 0).mean() > 0.5:
        raise RuntimeError("cuff winding")
    return A, allF, rings, ids


def glove_surface(B, side="L"):
    """The glove's outer skin: control cage, one Catmull-Clark step, offset. Returns dict with P (points), F (quads),
    C (sparse: points before offset = C @ body V), loops of the cuff top."""
    o, R, fa = hand_frame(B, side)
    A, F0, rings, ids = control_mesh(B, side)
    S, F1 = catmull_clark(F0, A.shape[0])
    C = (S @ A).tocsr()
    P = C @ B["V"]
    N = vertex_normals(P, F1)
    s = (P - o) @ fa
    L = (P - o) @ R.T
    # offset: hand -> cuff over the wrist crease
    off = OFF_HAND + (OFF_CUFF - OFF_HAND) * smoothstep(CREASE_Y + 0.004, CREASE_Y - 0.010, s)
    Q = P + N * off[:, None]
    # fingertip room: along each finger's last bone, fading over 10 mm from the tip
    Wv = C @ B["W"]
    names = B["names"]
    room = np.zeros(len(P))
    for fgr in range(1, 6):
        b = names.index(f"finger{fgr}-3.{side}")
        h, t = B["J"][f"finger{fgr}-3.{side}"], B["T"][f"finger{fgr}-3.{side}"]
        ax = (t - h) / np.linalg.norm(t - h)
        w = np.asarray(Wv[:, b].todense()).ravel()
        w = w / w.max()
        tipd = (P - h) @ ax
        tip = np.max(tipd[w > 0.5])
        g = np.clip(w, 0, 1) * smoothstep(tip - 0.010, tip, tipd)
        Q += np.outer(g * TIP_ROOM, ax)
        room += g * TIP_ROOM * np.maximum(np.einsum("ij,j->i", N, ax), 0.0)
    loops = boundary_loops(F1)
    top = [l for l in loops if np.mean(s[l]) < CUFF_TOP + 0.003]
    assert len(top) == 1
    Q = bridge(Q, F1, P, N, off + room, np.array(top[0]))
    return dict(P=Q, P0=P, F=F1, C=C, N=vertex_normals(Q, F1), top=np.array(top[0]), s=s, L=L)


def bridge(Q, F, P, N, off, fixed, iters=40, lam=0.5):
    """Fabric does not follow small skin detail (fingernails, knuckle creases, tendons): Laplacian smoothing of the
    glove, then every vertex pushed back out to at least its offset above the skin (signed distance along the skin
    normal of its own source point and its neighbours'). Boundary vertices stay."""
    n = len(Q)
    E = edges_of(F)
    A = sparse.csr_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()
    keep = np.zeros(n, bool)
    keep[fixed] = True
    for _ in range(iters):
        avg = (A @ Q) / deg[:, None]
        Qn = Q + lam * (avg - Q)
        Qn[keep] = Q[keep]
        d = np.einsum("ij,ij->i", Qn - P, N)                         # height over its own skin point
        Q = Qn + N * (np.clip(d, off, off + BRIDGE_MAX) - d)[:, None]
    # and over its neighbours' skin points (a vertex over a crease can sit nearer a neighbour's skin than its own)
    for _ in range(3):
        need = np.zeros(n)
        for a, b in ((E[:, 0], E[:, 1]), (E[:, 1], E[:, 0])):
            d = np.einsum("ij,ij->i", Q[a] - P[b], N[b])
            np.maximum.at(need, a, np.maximum(off[b] - d, 0.0))
        Q = Q + N * need[:, None]
    return Q


# ---- segments and UV charts ---------------------------------------------------------------------------------------
def segment_weights(B, side, Wv):
    """Per vertex: its skin weight summed per segment (hand_bone_groups), (n, 7)."""
    g = hand_bone_groups(B["names"], side)
    M = np.zeros((len(B["names"]), 7))
    for b, k in g.items():
        M[b, k] = 1
    S = np.asarray(Wv @ M)
    return S / np.maximum(S.sum(1, keepdims=True), 1e-9)


def segments(B, side, Wv):
    """Dominant segment per vertex."""
    return segment_weights(B, side, Wv).argmax(1)


def spine(B, side, k):
    """A finger's (or the thumb's) joint chain, proximal to tip: the cylinder its chart is unwrapped about."""
    first = 2 if k == 1 else 1
    pts = [B["J"][f"finger{k}-{j}.{side}"] for j in range(first, 4)] + [B["T"][f"finger{k}-3.{side}"]]
    return np.array(pts)


def on_spine(X, S):
    """Closest point parameter (arc length from the first joint) and the segment index of points X on polyline S."""
    best = np.full(len(X), np.inf)
    par = np.zeros(len(X))
    idx = np.zeros(len(X), int)
    acc = 0.0
    for j in range(len(S) - 1):
        a, b = S[j], S[j + 1]
        L = np.linalg.norm(b - a)
        t = np.clip((X - a) @ (b - a) / L ** 2, 0, 1)
        d = np.linalg.norm(X - (a + np.outer(t, b - a)), axis=1)
        m = d < best
        best[m], par[m], idx[m] = d[m], acc + t[m] * L, j
        acc += L
    return par, idx


def cyl_uv(X, Xc, centre, axis, e1, e2, radius, cut):
    """Cylindrical unwrap of face corners X (nf, 4, 3) about a line: u = angle from CUT x radius (each face's corners
    kept together across the seam, about the face centre Xc), v = distance along the axis."""
    th = np.arctan2((X - centre) @ e2, (X - centre) @ e1)
    th0 = np.arctan2((Xc - centre) @ e2, (Xc - centre) @ e1)
    thc = (th0 - cut) % (2 * np.pi)
    th = thc[:, None] + (th - th0[:, None] + np.pi) % (2 * np.pi) - np.pi
    return np.stack([th * radius, (X - centre) @ axis], -1)


def charts(B, side, G):
    """UV charts, like the real glove's pattern pieces: the hand's back, palm and edges (planar, along their
    normals), each finger and the thumb unwrapped as a cylinder about its joint chain (seam along the palm side's
    middle) with a cap at the tip, the cuff as one cylinder (seam on the little-finger side). Returns face-corner
    coordinates in metres in each chart's plane and the chart id per face."""
    P, F = G["P"], G["F"]
    o, R, fa = hand_frame(B, side)
    Wv = G["C"] @ B["W"]
    seg_v = segments(B, side, Wv)
    fc = P[F].mean(1)
    fn = np.cross(P[F[:, 2]] - P[F[:, 0]], P[F[:, 3]] - P[F[:, 1]])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True)
    seg = np.array([np.bincount(seg_v[f], minlength=7).argmax() for f in F])
    s_face = (fc - o) @ fa
    seg[s_face < CREASE_Y - 0.002] = 6                              # the cuff band
    seg[(seg == 6) & (s_face >= CREASE_Y - 0.002)] = 0
    UV = np.zeros((len(F), 4, 2))
    chart = np.zeros(len(F), int)
    X = P[F]
    # hand: back, palm, thumb-side edge, little-finger-side edge, distal (the webs)
    m = seg == 0
    x, y, z = R
    c = np.stack([-fn[m] @ z, fn[m] @ z, fn[m] @ x, -fn[m] @ x, fn[m] @ y], 1).argmax(1)
    axes = [(x, y), (-x, y), (z, y), (-z, y), (x, z)]
    idx = np.nonzero(m)[0]
    for k in range(5):
        mm = idx[c == k]
        u, v = axes[k]
        UV[mm] = np.stack([(X[mm] - o) @ u, (X[mm] - o) @ v], -1)
        chart[mm] = k
    # fingers and thumb: cylinders about the joint chain, tip caps
    for k in range(1, 6):
        m = np.nonzero(seg == k)[0]
        S = spine(B, side, k)
        par, j = on_spine(fc[m], S)
        a_tip = S[-1] - S[-2]
        a_tip /= np.linalg.norm(a_tip)
        Ltot = sum(np.linalg.norm(S[i + 1] - S[i]) for i in range(len(S) - 1))
        tip = (fn[m] @ a_tip > 0.55) & (par > Ltot - 0.012)
        a = S[-1] - S[0]
        a /= np.linalg.norm(a)
        p = z - a * (z @ a)
        if k == 1:                                                   # the thumb's pad faces the index finger
            p = -x - a * (-x @ a)
        p /= np.linalg.norm(p)
        q = np.cross(a, p)
        r = np.median(np.linalg.norm((fc[m] - S[0]) - np.outer((fc[m] - S[0]) @ a, a), axis=1))
        body = m[~tip]
        # per face: the spine point and local axis it sits on, so the curl does not shear the unwrap
        par_b, jb = on_spine(fc[body], S)
        for jj in range(len(S) - 1):
            mm = body[jb == jj]
            if not len(mm):
                continue
            aj = S[jj + 1] - S[jj]
            Lj = np.linalg.norm(aj)
            aj /= Lj
            pj = p - aj * (p @ aj)
            pj /= np.linalg.norm(pj)
            qj = np.cross(aj, pj)
            UV[mm] = cyl_uv(X[mm], fc[mm], S[jj], aj, pj, qj, r, 0.0)
            chart[mm] = 100 + 10 * k + jj                            # one island per phalanx: no overlap at a bend
        mt = m[tip]
        UV[mt] = np.stack([(X[mt] - S[-1]) @ q, (X[mt] - S[-1]) @ p], -1)
        chart[mt] = 20 + k
    # cuff
    m = np.nonzero(seg == 6)[0]
    e1 = x - fa * (x @ fa)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(fa, e1)
    UV[m] = cyl_uv(X[m], fc[m], o, fa, e1, e2, 0.029, math.pi)      # seam at -x: the little-finger side
    chart[m] = 30
    # a face that projects folded (its UV winding against its chart's) becomes its own island, flat along its normal
    a, b = UV[:, 2] - UV[:, 0], UV[:, 3] - UV[:, 1]
    area = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
    nxt = 10000
    for c in np.unique(chart):
        m = chart == c
        sgn = np.sign(area[m].sum())
        for i in np.nonzero(m & (np.sign(area) != sgn))[0]:
            e1 = X[i, 1] - X[i, 0]
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(fn[i], e1)
            UV[i] = np.stack([(X[i] - fc[i]) @ e1, (X[i] - fc[i]) @ e2], -1)
            chart[i] = nxt
            nxt += 1
    return UV, chart


def islands(F, chart):
    """Connected components of faces within each chart (sharing an edge)."""
    from scipy.sparse.csgraph import connected_components
    E = edges_of(F)
    nf = len(F)
    fid = np.tile(np.arange(nf), 4)
    es = np.sort(E, axis=1)
    order = np.lexsort((es[:, 1], es[:, 0]))
    es, fid = es[order], fid[order]
    same = (es[1:] == es[:-1]).all(1)
    a, b = fid[:-1][same], fid[1:][same]
    ok = chart[a] == chart[b]
    g = sparse.coo_matrix((np.ones(ok.sum()), (a[ok], b[ok])), shape=(nf, nf))
    return connected_components(g, directed=False)[1]


def pack(UV, isl, size=TEX, pad=6):
    """Shelf-pack islands (UV in metres) into [0, 1]^2 at one scale (texels per metre) as large as fits."""
    ids = np.unique(isl)
    boxes = []
    for i in ids:
        Q = UV[isl == i].reshape(-1, 2)
        lo, hi = Q.min(0), Q.max(0)
        boxes.append((i, lo, hi - lo))
    area = sum(w * h for _, _, (w, h) in boxes)
    k = math.sqrt(0.80 * size * size / area)
    while True:
        place = {}
        x = y = rowh = 0
        ok = True
        for i, lo, (w, h) in sorted(boxes, key=lambda b: -b[2][1]):
            W_, H_ = w * k + 2 * pad, h * k + 2 * pad
            if x + W_ > size:
                x, y, rowh = 0, y + rowh, 0
            if y + H_ > size:
                ok = False
                break
            place[i] = (x + pad - lo[0] * k, y + pad - lo[1] * k)
            x += W_
            rowh = max(rowh, H_)
        if ok:
            break
        k *= 0.97
    out = np.zeros_like(UV)
    for i, (ox, oy) in place.items():
        m = isl == i
        out[m, :, 0] = (UV[m, :, 0] * k + ox) / size
        out[m, :, 1] = 1.0 - (UV[m, :, 1] * k + oy) / size
    return out, k


# ---- texture painting ---------------------------------------------------------------------------------------------
def raster(UV, size=TEX):
    """Triangle id per texel (-1 empty) and barycentrics, for face-corner UVs of quads (split 0-1-2, 0-2-3)."""
    from PIL import Image, ImageDraw
    T = np.concatenate([UV[:, [0, 1, 2]], UV[:, [0, 2, 3]]])           # (2nf, 3, 2)
    px = np.stack([T[..., 0] * size, (1 - T[..., 1]) * size], -1)
    img = Image.new("RGB", (size, size), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for i, t in enumerate(px):
        dr.polygon([tuple(p) for p in t], fill=(i & 255, (i >> 8) & 255, (i >> 16) & 255))
    a = np.asarray(img).astype(np.int64)
    tid = a[..., 0] + (a[..., 1] << 8) + (a[..., 2] << 16)
    tid[tid == 0xFFFFFF] = -1
    yy, xx = np.nonzero(tid >= 0)
    t = tid[yy, xx]
    P = np.stack([xx + 0.5, yy + 0.5], -1)
    A, Bp, Cp = px[t, 0], px[t, 1], px[t, 2]
    v0, v1, v2 = Bp - A, Cp - A, P - A
    den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    b1 = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
    b2 = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
    bc = np.clip(np.stack([1 - b1 - b2, b1, b2], -1), 0, 1)
    bc /= bc.sum(1, keepdims=True)
    return tid, (yy, xx, t, bc)


def dilate(img, filled, n=12):
    """Spread island texels into empty space (no dark seams when the texture is filtered)."""
    from scipy import ndimage
    d, (iy, ix) = ndimage.distance_transform_edt(~filled, return_indices=True)
    out = img[iy, ix]
    return out


def texel_geometry(G, UV, tex=TEX):
    """Per texel: hand-local position, hand-local normal, segment, face id."""
    F = G["F"]
    tid, (yy, xx, t, bc) = raster(UV, tex)
    nf = len(F)
    fi = t % nf
    tri = np.where(t < nf, 0, 1)
    corners = np.where(tri[:, None] == 0, np.array([0, 1, 2]), np.array([0, 2, 3]))
    vids = F[fi[:, None], corners]
    X = np.einsum("ij,ijk->ik", bc, G["L"][vids])
    N = np.einsum("ij,ijk->ik", bc, G["NL"][vids])
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return dict(yy=yy, xx=xx, face=fi, X=X, N=N, tid=tid, bc=bc, vids=vids)


def palm_fields(B, side, G):
    """Per glove vertex (hand-local): the palmar direction of the bones it rides on (weight-blended: each finger
    bone's own palmar side, the thumb's pad toward the fingers) and the cosine of the palm panel's half-width there
    (fingers 62 deg: the stretch-mesh fourchettes show between the fingers in Leatt's palm view; thumb 70; hand 80:
    the palm wraps to the hand's edges)."""
    o, R, fa = hand_frame(B, side)
    z, x = R[2], R[0]
    names = B["names"]
    Pb = np.zeros((len(names), 3))
    Cb = np.zeros(len(names))
    g = hand_bone_groups(names, side)
    for b, k in g.items():
        n = names[b]
        a = B["T"][n] - B["J"][n]
        a /= np.linalg.norm(a)
        if k == 1:
            target = B["J"][f"finger2-2.{side}"] - B["J"][n]
            p = target - a * (target @ a)
            p = p / np.linalg.norm(p) + 0.4 * (z - a * (z @ a))
            lim = 70.0
        elif k in (2, 3, 4, 5):
            p, lim = z - a * (z @ a), 62.0
        else:
            p, lim = z, 80.0
        Pb[b] = p / np.linalg.norm(p)
        Cb[b] = math.cos(math.radians(lim))
    Wv = G["C"] @ B["W"]
    pv = np.asarray(Wv @ Pb)
    cv = np.asarray(Wv @ Cb).ravel() / np.maximum(np.asarray(Wv.sum(1)).ravel(), 1e-9)
    return pv @ R.T, cv


def interp(TG, G, A):
    """Per-vertex field A (n, ...) interpolated at the texels."""
    return np.einsum("ij,ij...->i...", TG["bc"], A[TG["vids"]])


def paint_panels(G, TG, side):
    """Base colours: X-Flow mesh black on the back and the finger sides, NanoGrip light grey on the palm, the finger
    fronts and the thumb's pad, black ribbed elastic on the cuff band. Returns colours and the palm mask."""
    X, N = TG["X"], TG["N"]
    pv = interp(TG, G, G["palm_dir"])
    pv /= np.linalg.norm(pv, axis=1, keepdims=True)
    cv = interp(TG, G, G["palm_cos"])
    col = np.zeros((len(X), 3))
    col[:] = BLACK_MESH
    palm = (np.einsum("ij,ij->i", N, pv) > cv) & (X[:, 1] > CREASE_Y)
    col[palm] = GREY_PALM
    col[X[:, 1] < CREASE_Y] = BLACK_ELASTIC
    return col, palm


BLACK_MESH = np.array([30, 30, 33]) / 255.0          # sRGB, Leatt's studio photo of the back (median of the mesh)
GREY_PALM = np.array([152, 145, 143]) / 255.0         # NanoGrip palm, Leatt's palm photo (median)
BLACK_ELASTIC = np.array([24, 24, 26]) / 255.0


# ---- strap and pull tab -------------------------------------------------------------------------------------------
def strap_parts(B, side, G):
    """The hook-and-loop strap over the cuff band's back, round the thumb-side edge onto the palm, and its white
    pull at the end: thin shells laid on the glove's cuff (rays from the forearm axis), skinned from the glove."""
    o, R, fa = hand_frame(B, side)
    P, F = G["P"], G["F"]
    Tt = tris_of(F)
    n_g = len(P)
    e1 = R[0] - fa * (R[0] @ fa)                     # thumbward, across the wrist
    e1 /= np.linalg.norm(e1)
    e2 = R[2] - fa * (R[2] @ fa)                     # palmar
    e2 /= np.linalg.norm(e2)

    def on_cuff(th, s, lift):
        """Points on the glove's cuff at angle th (0 = thumb side, +pi/2 = palm, -pi/2 = back) and s, lifted; and
        each point as a combination of glove vertices (for its skin weights)."""
        O = o + np.outer(s, fa)
        D = np.outer(np.cos(th), e1) + np.outer(np.sin(th), e2)
        hits = ray_hits(O, D, P, Tt)
        pts, rows, cols, vals = [], [], [], []
        for i, ((t, tri, u, v), oo, dd) in enumerate(zip(hits, O, D)):
            a, b, c = Tt[tri]
            nrm = np.cross(P[b] - P[a], P[c] - P[a])
            nrm /= np.linalg.norm(nrm)
            pts.append(oo + dd * t + nrm * lift)
            rows += [i] * 3
            cols += [a, b, c]
            vals += [1 - u - v, u, v]
        return np.array(pts), sparse.csr_matrix((vals, (rows, cols)), shape=(len(pts), n_g))

    parts = {}
    # strap: from 30 % across the back (from the little-finger side) round the thumb edge to 10 mm onto the palm
    rr = 0.031
    th0, th1 = -math.radians(118), math.radians(22)
    s0, s1 = CUFF_TOP + 0.002, CUFF_TOP + 0.002 + STRAP_W
    nu, nv = 36, 7
    TH = np.linspace(th0, th1, nu)
    SS = np.linspace(s0, s1, nv)
    grid_top, grid_bot, W_ = [], [], []
    for sv in SS:
        p_top, w = on_cuff(TH, np.full(nu, sv), STRAP_T)
        p_bot, _ = on_cuff(TH, np.full(nu, sv), 0.0001)
        grid_top.append(p_top)
        grid_bot.append(p_bot)
        W_.append(w)
    parts["strap"] = shell_from_grids(np.array(grid_top), np.array(grid_bot), sparse.vstack(W_ + W_).tocsr())
    # pull tab: white, over the strap's free end at the thumb-side edge, in the strap's upper part
    L_, H_, T_ = TAB
    th_b = th1 + 0.004 / rr
    th_a = th_b - L_ / rr
    TH = np.linspace(th_a, th_b, 14)
    SS = np.linspace(s0 + 0.003, s0 + 0.003 + H_, 4)
    gt, gb, W_ = [], [], []
    for sv in SS:
        p_top, w = on_cuff(TH, np.full(len(TH), sv), STRAP_T + T_)
        p_bot, _ = on_cuff(TH, np.full(len(TH), sv), STRAP_T * 0.6)
        gt.append(p_top)
        gb.append(p_bot)
        W_.append(w)
    parts["tab"] = shell_from_grids(np.array(gt), np.array(gb), sparse.vstack(W_ + W_).tocsr())
    return parts


def shell_from_grids(top, bot, W):
    """Closed slab between two (nv, nu, 3) grids: top faces up, bottom down, four side walls. W: each vertex as a
    combination of glove vertices, in the order top then bottom."""
    nv, nu, _ = top.shape
    V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
    o = nv * nu
    idx = lambda i, j: i * nu + j
    F = []
    for i in range(nv - 1):
        for j in range(nu - 1):
            F.append((idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j)))
            F.append((o + idx(i, j), o + idx(i + 1, j), o + idx(i + 1, j + 1), o + idx(i, j + 1)))
    for j in range(nu - 1):                                          # first and last rows
        F.append((idx(0, j + 1), idx(0, j), o + idx(0, j), o + idx(0, j + 1)))
        F.append((idx(nv - 1, j), idx(nv - 1, j + 1), o + idx(nv - 1, j + 1), o + idx(nv - 1, j)))
    for i in range(nv - 1):                                          # first and last columns
        F.append((idx(i, 0), idx(i + 1, 0), o + idx(i + 1, 0), o + idx(i, 0)))
        F.append((idx(i + 1, nu - 1), idx(i, nu - 1), o + idx(i, nu - 1), o + idx(i + 1, nu - 1)))
    F = np.array(F)
    # orient: top faces' normals away from the bottom
    n = np.cross(V[F[0, 1]] - V[F[0, 0]], V[F[0, 3]] - V[F[0, 0]])
    if n @ (top[0, 0] - bot[0, 0]) < 0:
        F = F[:, ::-1]
    return dict(V=V, F=F, W=W)


# ---- hem ----------------------------------------------------------------------------------------------------------
def hem(G):
    """The cuff's top edge rolled over and turned in: a half-round rim and an inner wall HEM deep, from the outer
    surface's top rows offset inward by the elastic's thickness."""
    P, F, N = G["P"], G["F"], G["N"]
    top = G["top"]
    # rows below the top loop by topology: next row = neighbours of the current row not yet used, in order
    adj = {}
    for f in F:
        for i in range(4):
            a, b = f[i], f[(i + 1) % 4]
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
    rows = [list(top)]
    used = set(top)
    while True:
        prev = rows[-1]
        nxt = []
        for v in prev:
            c = [u for u in adj[v] if u not in used]
            if len(c) != 1:
                break
            nxt.append(c[0])
        if len(nxt) != len(prev):
            break
        rows.append(nxt)
        used.update(nxt)
        depth = G["s"][nxt].mean() - G["s"][top].mean()
        if depth > HEM:
            break
    rows = [np.array(r) for r in rows]
    V, W = [], []
    rings = []
    # rim: half-round of radius CUFF_WALL/2 over the top
    t0 = P[rows[0]]
    n0 = N[rows[0]]
    up = -np.outer(np.ones(len(t0)), G["fa"])
    for ang in np.linspace(0, math.pi, 5)[1:]:
        c = t0 - n0 * CUFF_WALL / 2
        rings.append(c + n0 * math.cos(ang) * CUFF_WALL / 2 + up * math.sin(ang) * CUFF_WALL / 2)
    for r in rows[1:]:
        rings.append(P[r] - N[r] * CUFF_WALL)
    srcs = [rows[0]] * 4 + rows[1:]
    out_rings = [rows[0]]
    nV = len(P)
    newV = []
    for k, ring in enumerate(rings):
        out_rings.append(np.arange(nV, nV + len(ring)))
        newV.append(ring)
        nV += len(ring)
    Fh = []
    for k in range(len(out_rings) - 1):                  # the outer faces hold top[i] -> top[i+1]: run against it
        a, b = out_rings[k], out_rings[k + 1]
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            Fh.append((a[j], a[i], b[i], b[j]))
    Fh = np.array(Fh)
    return np.concatenate(newV), Fh, np.concatenate(srcs)


# ---- assemble -----------------------------------------------------------------------------------------------------
def weights_list(Wsp, keep=4, tol=0.01):
    """Sparse (n x bones) -> (vert, bone, weight) arrays: at most KEEP bones per vertex, renormalised."""
    Wd = Wsp.tocsr()
    wv, wb, ww = [], [], []
    for i in range(Wd.shape[0]):
        row = Wd.getrow(i)
        b, w = row.indices, row.data
        o = np.argsort(-w)[:keep]
        b, w = b[o], w[o]
        k = w > tol
        b, w = b[k], w[k] / w[k].sum()
        wv += [i] * len(b)
        wb += b.tolist()
        ww += w.tolist()
    return np.array(wv), np.array(wb), np.array(ww)


def build_side(B, side="L"):
    """Everything for the left glove (the right one is mirrored from it by mirror_side)."""
    o, R, fa = hand_frame(B, side)
    G = glove_surface(B, side)
    G["fa"] = fa
    G["NL"] = G["N"] @ R.T
    Wv = G["C"] @ B["W"]
    seg_v = segments(B, side, Wv)
    G["seg_face"] = np.array([np.bincount(seg_v[f], minlength=7).argmax() for f in G["F"]])
    G["palm_dir"], G["palm_cos"] = palm_fields(B, side, G)
    UV, chart = charts(B, side, G)
    isl = islands(G["F"], chart)
    G["isl"] = isl
    UVp, k = pack(UV, isl)
    G["UV"], G["texel_per_m"] = UVp, k
    # hem (inner side of the cuff) and strap
    Vh, Fh, src = hem(G)
    G["hem"] = (Vh, Fh, src)
    G["straps"] = strap_parts(B, side, G)
    G["Wv"] = Wv
    return G


def hide_ids(B, G, side):
    """Body vertices under the glove: distal of the wrist ring (the ring itself stays: the skin ends under the cuff,
    10 mm inside its top edge)."""
    fids, ring = wrist_ring(B, side)
    ids = np.unique(B["F"][fids])
    return np.setdiff1d(ids, ring)


def to_parts(B, G, side="L", mirror=None):
    """Gear parts for one side, built from the left glove G. For the right side (mirror: the body's mirror vertex
    index) the shapes are mirrored and the skin weights are the right hand's own: every glove vertex is the same
    combination of the mirrored body vertices."""
    C = G["C"]
    if side == "R":
        Pm = sparse.csr_matrix((np.ones(len(mirror)), (np.arange(len(mirror)), mirror)), shape=(len(mirror),) * 2)
        C = (C @ Pm).tocsr()
    Wg = (C @ B["W"]).tocsr()                                         # glove vertices' weights
    P = G["P"]
    F = G["F"]
    Vh, Fh, src = G["hem"]
    Vall = np.concatenate([P, Vh])
    Wall = sparse.vstack([Wg, Wg[src]]).tocsr()
    Fall = np.vstack([F, Fh])
    UV = np.concatenate([G["UV"], np.zeros((len(Fh), 4, 2))])
    M = np.concatenate([np.zeros(len(F), int), np.ones(len(Fh), int)])
    parts = {"glove": (Vall, Fall, M, UV, Wall, [f"glove_fabric_{side}", "glove_elastic"])}
    for k, mat in (("strap", "glove_strap"), ("tab", "glove_tab")):
        st = G["straps"][k]
        parts["glove_" + k] = (st["V"], st["F"], np.zeros(len(st["F"]), int), None, (st["W"] @ Wg).tocsr(), [mat])
    out = {}
    for name, (V, Fp, Mp, UVp, Wp, mt) in parts.items():
        if side == "R":
            V, Fp = V * [-1, 1, 1], Fp[:, ::-1]
            UVp = UVp[:, ::-1] if UVp is not None else None
        out[f"{name}_{side}"] = (V, Fp, Mp, UVp, Wp, mt)
    return out


MATERIALS = {
    # fabric: X-Flow mesh, stretch mesh and NanoGrip in one texture; elastic, webbing, TPR pull (Leatt photos)
    "glove_fabric_L": dict(image="glove_L_color.png", rough=0.78, sheen=0.35),
    "glove_fabric_R": dict(image="glove_R_color.png", rough=0.78, sheen=0.35),
    "glove_elastic": dict(rgb=[24, 24, 26], rough=0.8, sheen=0.3),
    "glove_strap": dict(rgb=[22, 22, 24], rough=0.72, sheen=0.25),
    "glove_tab": dict(rgb=[236, 236, 234], rough=0.45),
}


def write_textures(B, G, out_dir):
    TG = texel_geometry(G, G["UV"])
    filled = TG["tid"] >= 0
    for side in ("L", "R"):
        col, palm = paint_panels(G, TG, side)
        img = np.zeros((TEX, TEX, 3))
        img[TG["yy"], TG["xx"]] = col
        img = dilate(img, filled)
        from PIL import Image
        Image.fromarray((np.clip(img, 0, 1) * 255).round().astype(np.uint8)).save(
            os.path.join(out_dir, f"glove_{side}_color.png"), optimize=True)
    return TG


def build(body_path, out_path, textures=True):
    B = load_body(body_path)
    G = build_side(B, "L")
    mirror = mirror_index(B["V"])
    parts = {}
    parts.update(to_parts(B, G, "L"))
    parts.update(to_parts(B, G, "R", mirror))
    if textures:
        os.makedirs(TEXDIR, exist_ok=True)
        write_textures(B, G, TEXDIR)
    hide_L = hide_ids(B, G, "L")
    hide = np.concatenate([hide_L, mirror[hide_L]])
    mats = sorted({m for p in parts.values() for m in p[5]})
    out = dict(names=np.array(list(parts)), mats=np.array(mats), materials=json.dumps(MATERIALS),
               hide_body=hide)
    nv = 0
    for name, (V, F, M, UV, W, mt) in parts.items():
        out[name + "__V"] = V.astype(np.float32)
        out[name + "__F"] = F.ravel().astype(np.int32)
        out[name + "__FS"] = np.full(len(F), 4, np.int32)
        out[name + "__M"] = np.array([mats.index(mt[i]) for i in M], np.int32)
        if UV is not None:
            out[name + "__UV"] = UV.reshape(-1, 2).astype(np.float32)
        wv, wb, ww = weights_list(W)
        out[name + "__wv"], out[name + "__wb"], out[name + "__ww"] = wv, wb, ww.astype(np.float32)
        nv += len(V)
    out["meta"] = json.dumps(dict(size=SIZE, texel_per_mm=G["texel_per_m"] / 1000.0, vertices=nv))
    np.savez_compressed(out_path, **out)
    return out, G, B


def preview(body_path, out_png):
    """Flat views of the left glove (back, palm, thumb side) over the body's hand, and the UV islands."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    B = load_body(body_path)
    G = build_side(B, "L")
    o, R, fa = hand_frame(B, "L")
    L = (G["P"] - o) @ R.T
    Vh, Fh, _ = G["hem"]
    Lh = (Vh - o) @ R.T
    fig, axs = plt.subplots(1, 4, figsize=(28, 9))
    TG = texel_geometry(G, G["UV"], 1024)
    col, _ = paint_panels(G, TG, "L")
    fcol = np.zeros((len(G["F"]), 3))
    np.add.at(fcol, TG["face"], col)
    cnt = np.bincount(TG["face"], minlength=len(G["F"]))[:, None]
    fcol = np.where(cnt > 0, fcol / np.maximum(cnt, 1), 0.5)
    for ax, (i, j, k, sgn, title) in zip(axs, [(0, 1, 2, -1, "back (from -z)"), (0, 1, 2, 1, "palm (from +z)"),
                                               (2, 1, 0, 1, "thumb side (from +x)")]):
        depth = L[G["F"]][:, :, k].mean(1) * sgn
        order = np.argsort(depth)
        ax.add_collection(PolyCollection(L[G["F"]][order][:, :, [i, j]], facecolors=fcol[order] * 0.85 + 0.1,
                                         edgecolor="k", linewidth=0.1))
        ax.add_collection(PolyCollection(Lh[Fh - len(G["P"])][:, :, [i, j]] if False else [], facecolor="r"))
        for nm, st in G["straps"].items():
            Ls = (st["V"] - o) @ R.T
            ax.add_collection(PolyCollection(Ls[st["F"]][:, :, [i, j]], facecolor="w" if nm == "tab" else "0.3",
                                             edgecolor="0.5", linewidth=0.1))
        ax.set_aspect("equal")
        ax.set_xlim(-0.1, 0.1) if i == 0 else ax.set_xlim(-0.07, 0.07)
        ax.set_ylim(-0.05, 0.23)
        if sgn < 0 and i == 0:
            ax.invert_xaxis()
        ax.set_title(title)
        ax.grid(True, lw=0.3)
    UV = G["UV"]
    axs[3].add_collection(PolyCollection(UV, facecolors=fcol, edgecolor="r", linewidth=0.05))
    axs[3].set_xlim(0, 1)
    axs[3].set_ylim(0, 1)
    axs[3].set_aspect("equal")
    axs[3].set_title("UV islands (%.1f texels/mm at %d px)" % (G["texel_per_m"] / 1000, TEX))
    plt.tight_layout()
    plt.savefig(out_png, dpi=60)


# ---- measures and a numpy pose (tests) ----------------------------------------------------------------------------
def hand_measures(B, side="L", glove=None):
    """Leatt's two glove-chart measures on his hand (or, with GLOVE, over the glove): circumference round the
    knuckles (convex hull of the cut through the index and little fingers' knuckle joints, thumb left out, as a tape
    lies) and hand length (distal wrist crease to the middle fingertip with the hand flat: palm along the hand axis
    plus the middle finger's three bones, less the 1.3 mm the skin stops short of the last bone's tail)."""
    from scipy.spatial import ConvexHull
    o, R, fa = hand_frame(B, side)
    if glove is None:
        P, F = B["V"], B["F"]
        keep = np.linalg.norm(P - o, axis=1) < 0.25
    else:
        P, F = glove["P"], glove["F"]
        keep = np.ones(len(P), bool)
    L = (P - o) @ R.T
    a = (B["J"][f"finger2-1.{side}"] - o) @ R.T
    b = (B["J"][f"finger5-1.{side}"] - o) @ R.T
    slope = (a[1] - b[1]) / (a[0] - b[0])
    g = L[:, 1] - (a[1] + (L[:, 0] - a[0]) * slope)
    pts = []
    for e in ((0, 1), (1, 2), (2, 3), (3, 0)):
        i, j = F[:, e[0]], F[:, e[1]]
        m = (g[i] * g[j] < 0) & keep[i] & keep[j]
        t = g[i][m] / (g[i][m] - g[j][m])
        pts.append(L[i][m] + (L[j][m] - L[i][m]) * t[:, None])
    Q = np.concatenate(pts)
    Q = Q[(np.abs(Q[:, 2]) < 0.06) & (Q[:, 0] > -0.08) & (Q[:, 0] < a[0] + 0.015)]
    circ = ConvexHull(Q[:, [0, 2]]).area
    bones = sum(np.linalg.norm(B["T"][f"finger3-{k}.{side}"] - B["J"][f"finger3-{k}.{side}"]) for k in (1, 2, 3))
    length = ((B["J"][f"finger3-1.{side}"] - o) @ R[1] - CREASE_Y) + bones - 0.0013
    return dict(circumference_cm=circ * 100, length_cm=length * 100)


CURL = {1: (0.35, 0.35, 0.35), 2: (0.95, 1.05, 0.75), 3: (0.95, 1.05, 0.75), 4: (0.95, 1.05, 0.75),
        5: (0.95, 1.05, 0.75)}          # rad per bone, as build_rider.aim_pose closes the hand on the grip


def pose_hand(B, G, side="L", wrist_deg=0.0, curl=CURL):
    """The hand posed in numpy: the wrist bent WRIST_DEG about the knuckle-line axis at the wrist joint (+ = toward
    the palm), each finger bone turned palmward about (its axis x palm normal) by CURL. Skin (all body vertices)
    and glove (G's points) by linear blend skinning with their own weights (the glove's as written to the npz).
    Returns (posed body V, posed glove points)."""
    o, R, fa = hand_frame(B, side)
    names = B["names"]
    parents = [str(p) for p in B["d"]["parents"]]
    z = R[2]

    def rot(axis, ang):
        axis = axis / np.linalg.norm(axis)
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K

    local = {}
    local[f"wrist.{side}"] = (rot(R[0], math.radians(wrist_deg) * (1 if side == "L" else -1)), o)
    for k, angs in curl.items():
        for j, ang in zip((1, 2, 3), angs):
            n = f"finger{k}-{j}.{side}"
            a = B["T"][n] - B["J"][n]
            ax = np.cross(a, z) if side == "L" else np.cross(z, a)
            local[n] = (rot(ax, ang), B["J"][n])
    M = {}

    def world(n):
        if n in M:
            return M[n]
        p = parents[names.index(n)]
        Mp = world(p) if p else (np.eye(3), np.zeros(3))
        if n in local:
            Rl, c = local[n]
            Ml = (Rl, c - Rl @ c)
        else:
            Ml = (np.eye(3), np.zeros(3))
        M[n] = (Mp[0] @ Ml[0], Mp[0] @ Ml[1] + Mp[1])
        return M[n]
    for n in names:
        world(n)

    def lbs(P, W):
        W = W.tocsc()
        out = np.zeros_like(P)
        tot = np.asarray(W.sum(1)).ravel()
        for b in range(W.shape[1]):
            col = W.getcol(b)
            if col.nnz == 0:
                continue
            Rb, tb = M[names[b]]
            idx = col.indices
            out[idx] += col.data[:, None] * (P[idx] @ Rb.T + tb)
        out += P * (1 - tot)[:, None]
        return out
    Vp = lbs(B["V"], B["W"])
    wv, wb, ww = weights_list(G["C"] @ B["W"])
    Wg = sparse.csr_matrix((ww, (wv, wb)), shape=(len(G["P"]), len(names)))
    return Vp, lbs(G["P"], Wg)


def heights(G, Vp, Pg):
    """Each posed glove point's height over its own posed skin point (the Catmull-Clark skin it was made from),
    along that skin's normal."""
    P0 = G["C"] @ Vp
    N = vertex_normals(P0, G["F"])
    return np.einsum("ij,ij->i", Pg - P0, N)


# ---- Blender: close-ups and clearances on a built rider (build_rider.py's rider.blend) -----------------------------
# blender -b RIDER.blend --python-exit-code 1 --python gloves.py -- check OUT_DIR VIEWS
#   VIEWS: comma list of <name>_<L|R>; names: back, palm (Leatt's back-hand and palm views: the glove hanging fingers
#   down, seen square to the back or palm, cuff at the top), back34 and palm34 (Leatt's other-angle views, turned 35
#   deg toward the little finger / thumb), grip08 (his photo 08: the right fist from below, in front and outboard),
#   grip09 (photo 09: the fist from below and in front), top (from above and behind, the rider's own view).
#   Prints the clearances as JSON (CLEARANCE ...) and writes OUT_DIR/glove_<view>.png.
#   RIDER_SAMPLES (default 16), GLOVE_RES (default 900).
CAMS = {
    # (direction from the hand to the camera in the hand frame (x thumb, y finger, z palm), image up, lens mm, dist)
    "back": ((0.0, 0.0, -1.0), (0.0, -1.0, 0.0), 90, 0.95),
    "palm": ((0.0, 0.0, 1.0), (0.0, -1.0, 0.0), 90, 0.95),
    "back34": ((0.30, 0.15, -0.94), (0.0, -1.0, 0.0), 90, 0.95),
    "palm34": ((-0.25, 0.10, 0.96), (0.0, -1.0, 0.0), 90, 0.95),
    # close-ups (not Leatt views): fingertips from the back and from the side, knuckles, cuff and strap
    "tips": ((0.0, 0.45, -0.89), (0.0, -1.0, 0.0), 90, 0.42, 0.07),
    "knuckles": ((0.0, -0.2, -0.98), (0.0, -1.0, 0.0), 90, 0.40, 0.02),
    "cuff": ((0.75, -0.25, -0.6), (0.0, -1.0, 0.0), 90, 0.38, -0.055),
}


def grip_wrap(skin, glove, grip, wrist, frame=None):
    """The hand on a grip (all world points, numpy): the grip is a cylinder (axis by PCA of its rubber's vertices,
    radius the upper quartile of their distances over its middle 80 %). Skin and glove vertices inside it (mm deep),
    how far round it the glove wraps (degrees of the circumference with glove within 4 mm of the rubber), and with
    FRAME (wrist, x thumb, y finger, z palm) where the grip's axis crosses the hand, in the hand's frame (mm), the
    angle between the axis and the knuckle line (x), and the palm skin's height there."""
    c = grip.mean(0)
    u = np.linalg.svd(grip - c)[2][0]
    t = (grip - c) @ u
    mid = np.abs(t - np.median(t)) < 0.4 * np.ptp(t)
    r = np.linalg.norm((grip - c) - np.outer(t, u), axis=1)
    R0 = float(np.percentile(r[mid], 75))                       # the rubber's outside (its bore is inside too)
    lo, hi = t[mid].min(), t[mid].max()
    e1 = np.cross(u, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    out = dict(grip_radius_mm=round(R0 * 1000, 1), grip_length_mm=round(float(np.ptp(t)) * 1000, 1))
    for nm, P in (("skin", skin), ("glove", glove)):
        P = P[np.linalg.norm(P - wrist, axis=1) < 0.3]
        tp = (P - c) @ u
        rp = np.linalg.norm((P - c) - np.outer(tp, u), axis=1)
        inn = (tp > lo) & (tp < hi) & (rp < R0)
        out[nm + "_inside"] = int(inn.sum())
        out[nm + "_deepest_mm"] = round(float((R0 - rp[inn]).max()) * 1000, 1) if inn.any() else 0.0
        if nm == "glove":
            band = (tp > lo) & (tp < hi) & (rp >= R0 - 0.002) & (rp < R0 + 0.004)
            ang = np.degrees(np.arctan2((P[band] - c) @ e2, (P[band] - c) @ e1)) % 360
            out["wrap_deg"] = int(10 * len(np.unique((ang // 10).astype(int))))
    if frame is not None:
        o, x, y, z = (np.asarray(a, float) for a in frame)
        pc = o + y * 0.07                                      # middle of the palm
        k = (pc - c) @ u
        a = c + u * k                                          # the axis' point nearest the palm's middle
        loc = np.array([(a - o) @ x, (a - o) @ y, (a - o) @ z])
        S = (skin - o) @ np.stack([x, y, z]).T
        near = (np.abs(S[:, 0] - loc[0]) < 0.01) & (np.abs(S[:, 1] - loc[1]) < 0.01)
        out["axis_in_hand_mm"] = [round(float(v) * 1000, 1) for v in loc]
        out["axis_vs_knuckle_line_deg"] = round(float(np.degrees(np.arccos(abs(u @ x)))), 1)
        out["palm_skin_z_mm"] = round(float(S[near, 2].max()) * 1000, 1) if near.any() else None
    return out


def _blender_check(argv):
    import bpy
    from mathutils import Vector, Matrix
    from mathutils.bvhtree import BVHTree
    out_dir, views = argv[0], [v for v in argv[1].split(",") if v]
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    rig = bpy.data.objects["rider_rig"]
    dg = bpy.context.evaluated_depsgraph_get()

    def bone_world(n, tail=False):
        pb = rig.pose.bones[n]
        return rig.matrix_world @ (pb.tail if tail else pb.head)

    def frame(side):
        o = bone_world(f"wrist.{side}")
        f = (bone_world(f"finger3-1.{side}") - o).normalized()
        t = bone_world(f"finger2-1.{side}") - bone_world(f"finger5-1.{side}")
        t = (t - f * t.dot(f)).normalized()
        n = f.cross(t) if side == "L" else t.cross(f)
        c = (bone_world(f"metacarpal2.{side}", True) + o) / 2 + f * 0.035
        return c, t, f, n

    def mesh_world(ob):
        e = ob.evaluated_get(dg)
        me = e.to_mesh()
        M = e.matrix_world
        V = [M @ v.co for v in me.vertices]
        P = [tuple(p.vertices) for p in me.polygons]
        mats = [p.material_index for p in me.polygons]
        names = [m.name if m else "" for m in me.materials]
        e.to_mesh_clear()
        return V, P, mats, names

    res = {}
    # clearances
    bars = bpy.data.objects.get("bars")
    body = bpy.data.objects["rider_body"]
    mask = body.modifiers.get("covered")
    if mask:                                                    # the whole skin, also what the glove hides
        mask.show_viewport = False
        dg.update()
    BV, BP, _, _ = mesh_world(body)
    if mask:
        mask.show_viewport = True
        dg.update()
    bvh_skin = BVHTree.FromPolygons(BV, BP)
    for side in ("L", "R"):
        gl = bpy.data.objects.get(f"glove_{side}")
        if gl is None:
            continue
        GV, GP, GM, GN = mesh_world(gl)
        fab = [p for p, m in zip(GP, GM) if GN[m].startswith("glove_fabric")]
        bvh_g = BVHTree.FromPolygons(GV, fab)
        # skin outside the glove: skin vertices within 6 mm of the fabric whose nearest fabric point faces them
        c, t, f, n = frame(side)
        o = bone_world(f"wrist.{side}")
        fa = (bone_world(f"lowerarm02.{side}", True) - bone_world(f"lowerarm02.{side}")).normalized()
        # each skin vertex against the glove over it: the same digit (0 = hand); a fingertip pressed into the palm
        # (the pose closing the fist through itself) is counted apart, as the pose's, not the glove's
        def digit(obj, vi):
            gs = [g for g in obj.data.vertices[vi].groups if obj.vertex_groups[g.group].name != "covered"]
            if not gs:
                return -1
            n_ = obj.vertex_groups[max(gs, key=lambda x: x.weight).group].name
            return int(n_[6]) if n_.startswith("finger") and not n_.startswith("finger1-1") else 0
        nb = len(body.data.vertices)
        worst, count, self_x = 0.0, 0, 0
        cov = body.vertex_groups.get("covered")
        covered = set()
        if cov is not None:
            covered = {i for i, vv in enumerate(body.data.vertices) if any(g.group == cov.index for g in vv.groups)}
        vis_worst, vis_count = 0.0, 0
        for i, v in enumerate(BV[:nb]):                         # subsurf keeps the cage's vertices first
            if (v - o).length > 0.3 or (v - o).dot(fa) < CUFF_TOP + 0.004:
                continue
            hit = bvh_g.find_nearest(v, 0.006)
            if hit[0] is None:
                continue
            d = (v - hit[0]).dot(hit[1])
            if d > 0:
                gface = fab[hit[2]]
                if digit(body, i) != digit(gl, gface[0]) and gface[0] < len(gl.data.vertices):
                    self_x += 1
                    continue
                count += 1
                worst = max(worst, d)
                if i not in covered:
                    vis_count += 1
                    vis_worst = max(vis_worst, d)
                if os.environ.get("GLOVE_DEBUG"):
                    loc = v - o
                    print("OUT", side, digit(body, i), round(d * 1000, 1), [round(loc.dot(a) * 1000) for a in (t, f, n)],
                          [obj_g.name for obj_g in body.vertex_groups if any(
                              g.group == obj_g.index and g.weight > 0.2 for g in body.data.vertices[i].groups)])
        res[f"skin_out_{side}"] = dict(visible=vis_count, visible_worst_mm=round(vis_worst * 1000, 2),
                                       hidden=count - vis_count, hidden_worst_mm=round(worst * 1000, 2),
                                       pose_self_intersections=self_x)
        if bars is not None:
            BVb, BPb, BMb, BNb = mesh_world(bars)
            gname = "grip_rubber" if side == "L" else "grip_r"
            gv = sorted({i for p, m in zip(BPb, BMb) if BNb[m] == gname for i in p})
            res[f"grip_{side}"] = grip_wrap(np.array([list(BV[i]) for i in range(len(BV))]),
                                            np.array([list(v) for v in GV]),
                                            np.array([list(BVb[i]) for i in gv]), o,
                                            (o, t, f, n))
    print("CLEARANCE", json.dumps(res))
    # lights and render settings: a white studio like Leatt's product shots
    sc.render.engine = "CYCLES"
    sc.cycles.samples = int(os.environ.get("RIDER_SAMPLES", "16"))
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.0
    res_px = int(os.environ.get("GLOVE_RES", "900"))
    sc.render.resolution_x = sc.render.resolution_y = res_px
    w = bpy.data.worlds.new("glove_world")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]                                 # what lights the scene
    seen = nt.nodes.new("ShaderNodeBackground")                 # what the camera sees behind the glove
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(seen.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs["Surface"])
    body.hide_render = False
    for v in views:
        name, side = v.rsplit("_", 1)
        c, t, f, n = frame(side)
        for ob in [o for o in sc.objects if o.name.startswith("gl_cam") or o.name.startswith("gl_lamp")]:
            bpy.data.objects.remove(ob, do_unlink=True)
        if name in CAMS:                                        # Leatt's product shots: the glove alone on white
            d, up, lens, dist = CAMS[name][:4]
            c = c + f * (CAMS[name][4] if len(CAMS[name]) > 4 else 0.0)
            dw = (t * d[0] + f * d[1] + n * d[2]).normalized()
            upw = (t * up[0] + f * up[1] + n * up[2]).normalized()
            bg.inputs["Color"].default_value = (1, 1, 1, 1)
            bg.inputs["Strength"].default_value = 0.35
            seen.inputs["Color"].default_value = (1, 1, 1, 1)
            seen.inputs["Strength"].default_value = 1.0
            body.hide_render = True
        else:
            body.hide_render = False
            # riding views (world frame of the bike: x forward, y left, z up). His photos 08 and 09 are shot from far
            # below in a whip with the bike rolled over: the bar end is at the top of the picture, the fist seen
            # from in front (09) or from below and in front (08). Image up = outboard along the bar.
            outb = Vector((0, 1 if side == "L" else -1, 0))
            if name == "grip08":
                dw = Vector((0.45, 0, -0.85)) - outb * 0.25
            else:
                dw = Vector((0.85, 0, -0.45)) - outb * 0.15
            dw.normalize()
            upw = outb - dw * outb.dot(dw)
            lens, dist = 70, 0.55
            bg.inputs["Color"].default_value = (0.62, 0.72, 0.85, 1)       # daylight sky as in his photos
            bg.inputs["Strength"].default_value = 0.6
            seen.inputs["Color"].default_value = (0.36, 0.50, 0.70, 1)
            seen.inputs["Strength"].default_value = 1.0
        cam = bpy.data.objects.new("gl_cam", bpy.data.cameras.new("gl_cam"))
        cam.data.lens = lens
        cam.data.clip_start = 0.02
        pos = c + dw * dist
        zc = (pos - c).normalized()
        xc = upw.cross(zc).normalized()
        yc = zc.cross(xc)
        cam.matrix_world = Matrix((list(xc) + [0], list(yc) + [0], list(zc) + [0], [0, 0, 0, 1])).transposed()
        cam.matrix_world.translation = pos
        sc.collection.objects.link(cam)
        sc.camera = cam
        for k, (off, en, size) in enumerate((((0.4, 0.6, 1.0), 22.0, 0.6), ((-0.7, 0.2, 0.6), 9.0, 0.8),
                                             ((0.0, -0.8, -0.3), 6.0, 1.0))):
            L = bpy.data.lights.new(f"gl_lamp{k}", "AREA")
            L.energy, L.size = en, size
            lo = bpy.data.objects.new(f"gl_lamp{k}", L)
            lp = c + (xc * off[0] + yc * off[1] + zc * (1.0 + off[2])) * 0.9
            lo.location = lp
            lo.rotation_euler = (c - lp).to_track_quat("-Z", "Y").to_euler()
            sc.collection.objects.link(lo)
        sc.render.filepath = os.path.join(out_dir, f"glove_{v}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


REF = os.path.join(HERE, "..", "..", "reference")
LEATT = {   # Leatt's views of the Black 2.5 X-Flow (reference/leatt-gear/gloves) and which glove each shows
    "back_R": "leatt-gear/gloves/glove25xflow_black-my26_backhand_leatt-us_6024090150_1920.jpg",
    "palm_R": "leatt-gear/gloves/glove25xflow_black-my26_palm_leatt-us_6024090150_1920.jpg",
    "back34_L": "leatt-gear/gloves/glove25xflow_black-my27_backhand-other-angle_leatt-us_6027010260_1920.jpg",
    "palm34_L": "leatt-gear/gloves/glove25xflow_black-my27_palm-other-angle_leatt-us_6027010260_1920.jpg",
    # his photos (crops round each glove, pixel boxes in the original files)
    "grip09_L": ("damien-bike-2026-11-12/09_whip-from-below_left-front.jpg", (890, 530, 1040, 680)),
    "grip09_R": ("damien-bike-2026-11-12/09_whip-from-below_left-front.jpg", (1000, 215, 1120, 335)),
    "grip08_R": ("damien-bike-2026-11-12/08_whip-from-below_right-side.jpg", (945, 360, 1065, 480)),
}


def sheet(out_path, render_dir, views, size=640):
    """Reference beside render for each view, one row each."""
    from PIL import Image, ImageDraw
    rows = []
    for v in views:
        ref = LEATT[v]
        if isinstance(ref, tuple):
            im = Image.open(os.path.join(REF, ref[0])).convert("RGB").crop(ref[1])
            label = f"{os.path.basename(ref[0])[:2]} crop {ref[1]}"
        else:
            im = Image.open(os.path.join(REF, ref)).convert("RGB")
            label = os.path.basename(ref)[:40]
        im = im.resize((size, size), Image.LANCZOS)
        rd = Image.open(os.path.join(render_dir, f"glove_{v}.png")).convert("RGB").resize((size, size), Image.LANCZOS)
        row = Image.new("RGB", (2 * size + 10, size + 24), "white")
        row.paste(im, (0, 24))
        row.paste(rd, (size + 10, 24))
        d = ImageDraw.Draw(row)
        d.text((4, 4), label, fill=(0, 0, 0))
        d.text((size + 14, 4), f"model: {v}", fill=(0, 0, 0))
        rows.append(row)
    out = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), "white")
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(out_path, quality=90)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "sheet":
        sheet(a[1], a[2], a[3].split(","))
        raise SystemExit(0)
    if "bpy" in sys.modules or "--" in sys.argv:
        import bpy  # noqa: F401
        a = sys.argv[sys.argv.index("--") + 1:]
        if a[0] == "check":
            _blender_check(a[1:])
        raise SystemExit(0)
    if a and a[0] == "preview":
        preview(a[1], a[2])
        raise SystemExit(0)
    out, G, B = build(a[0], a[1])
    print(json.loads(str(out["meta"])))
