"""Damien's kit: Leatt Moto 5.5 UltraWeld jersey and Moto 5.5 I.K.S pant, Tiger Pink, 2026, on his body.

python3 kit.py BODY.npz OUT.npz [--no-tex]      (body.py's output; writes a gear npz for build_rider.py RIDER_GEAR)

Sources: research/rider-gear-leatt.md sections 1 and 2 (identification, construction, size charts), Leatt's photos
in reference/leatt-gear/jersey and pants, his photos reference/damien-bike-2026-11-12/06 to 10. Every number is in
the ledger research/rider-ledger/kit.md with its source; the tags below say where each comes from:
  BODY  measured on body.npz (MakeHuman shaped to 1.85 m, 80 kg)
  CHART Leatt's adult size charts (reference/leatt-gear/sizing)
  PHOTO read off Leatt's product photos or his photos
  EST   an estimate from common motocross gear, stated in the ledger

How a garment is made (both garments):
  1. the body faces of the garment's region are cut out of the rest-pose body along smooth cut surfaces (neckline,
     cuffs, hem, waist), the boundary vertices slid onto the cut along their edges;
  2. the patch is subdivided once and draped: curvature flow (the normal part of the umbrella Laplacian) pulls the
     cloth taut and bridges the body's hollows, a collision step pushes it out to a clearance per region (the ease
     from Leatt's size chart against his own girths);
  3. skin weights from the nearest skin vertex, smoothed over the garment; hide_body lists the skin it covers;
  4. UV charts (front/back panels, sleeve halves, leg halves) flattened by least-squares conformal maps and packed
     at one texel density; textures are painted per texel from the 3D rest-pose position of the cloth (kit_tex.py
     style functions below), so a graphic is placed by where it is on him, not by the UV layout.
"""
import json
import os
import sys

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import lsqr
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.join(HERE, "..", "..", "textures", "rider")

# ---------------------------------------------------------------- sizes (ledger: "Sizes")
BODY_CHEST = 1.008        # m, BODY: convex girth at nipple height (z 1.36)
BODY_WAIST_NATURAL = 0.805  # m, BODY: narrowest torso girth (z 1.18)
BODY_WAIST_BELT = 0.884   # m, BODY: horizontal girth at belt height (z 1.06), where Leatt's chart figure measures
BODY_WAIST_BAND = 0.844   # m, BODY: girth under the modelled waistband (front 1.09, back 1.15; test)
BODY_INSEAM = 0.872       # m, BODY: crotch height
JERSEY_SIZE = "L"         # CHART: arm length 80-82 (his 0.80), height 178-182 (his 1.85); chest 106-112 (his 101,
                          # which alone says S/M: L keeps the sleeves and body long enough for 1.85 m)
JERSEY_CHEST = 1.12       # m, CHART top of L's chest range: a race fit stretches to it, so the garment girth
PANT_SIZE = "L / US34"    # CHART: waist 83-88 (his 84.4 under the band, where the pant is worn); height 178-182
                          # and inseam 81-83 are short of his 185 and 87: the cuff ends higher, inside the boot
PANT_WAIST = 0.88         # m, CHART top of L's waist range (the Waistlock ratchet closes it on him)

# ---------------------------------------------------------------- cut lines (ledger: "Cut lines")
NECK_FRONT, NECK_SIDE, NECK_BACK = 1.515, 1.575, 1.565   # z of the "no-collar" neckline: front at the jugular
                                                         # notch (BODY 1.52), sides at the neck root, back below C7
NECK_AXIS = (0.0, -0.015)                                # x, y of the neck's axis (BODY)
CUFF_BACK = 0.012         # m, sleeve ends this far up the forearm from the wrist joint (PHOTO: glove cuff over it)
HEM_Z = 0.97              # m, the jersey's straight hem (tucked: 12 cm inside the pant at the front, PHOTO 07)
WAIST_FRONT, WAIST_BACK = 1.09, 1.15    # m, pant top: front 22 cm over his crotch (PHOTO: Leatt front
                                        # on-model, rise 499 px at 2200 px/m), the rear yoke higher
PANT_CUFF_Z = 0.355       # m: inside the 6.5 boot's gaiter (top 400 front to 423 back), the band 330-380 (boots build)

# ---------------------------------------------------------------- clearances (ledger: "Ease")
C_SKIN = 0.003            # m, fabric on skin where it is pulled tight (shoulders, cuffs)
C_JERSEY_CHEST = (JERSEY_CHEST - BODY_CHEST) / (2 * np.pi)   # 1.8 cm: a convex girth grows 2 pi per metre of offset
C_TUCK = 0.0025           # m, the tucked jersey under the pant
C_PANT_WAIST = 0.011      # m, waistband over the tucked jersey: jersey 2.5 mm, its cloth, the band's 4 mm and
                          # its facing (EST: a 4 mm double-layer band with the Waistlock's webbing inside)
C_PANT_SEAT = 0.012
C_PANT_THIGH = 0.016
C_PANT_CALF = 0.012
C_PANT_CUFF = 0.007       # m, cuff goes inside the boot
C_PANT_KNEE = 0.020       # m, at the front of the knee: a brace shell (EST 15 to 25 mm); the sides get the straight
                          # fall of the leg from the thigh
PANT_KNEE_CURVE = 0.010   # m, the pre-curved knee panel stands this far forward (PHOTO: Leatt front and side views)
PANT_FALL = 0.08          # m per m: the pant leg falls nearly straight from the thigh (PHOTO: Leatt on-model)
JERSEY_FALL = 0.35        # m per m: the jersey falls off the chest and shoulder blades (PHOTO: Leatt on-model)
JERSEY_SPAN_UP = 0.9      # m per m: from the chest up to the collarbones the cloth runs straight
JERSEY_BLOUSE = 0.006     # m, the tucked jersey's fullness over the waistband (PHOTO 07)


# ================================================================ mesh helpers
def vnormals(V, Q):
    n = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
    N = np.zeros_like(V)
    for k in range(Q.shape[1]):
        np.add.at(N, Q[:, k], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def edges_of(Q):
    E = np.sort(np.stack([Q, np.roll(Q, -1, 1)], 2).reshape(-1, 2), 1)
    return np.unique(E, axis=0, return_inverse=True)


def adjacency(n, Q):
    E, _ = edges_of(Q)
    A = sparse.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), (n, n)).tocsr()
    A.data[:] = 1.0
    return A


def boundary_edges(Q):
    E = np.sort(np.stack([Q, np.roll(Q, -1, 1)], 2).reshape(-1, 2), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    return u[c == 1]


def subdivide(V, Q):
    """Each quad into four (edge midpoints and face centre). Returns V2, Q2 and P, the sparse map from old vertex
    data to new (V2 = P @ V) so any per-vertex attribute follows."""
    n = len(V)
    E, inv = edges_of(Q)
    ne, nq = len(E), len(Q)
    rows = [np.arange(n), np.repeat(n + np.arange(ne), 2), np.repeat(n + ne + np.arange(nq), 4)]
    cols = [np.arange(n), E.ravel(), Q.ravel()]
    vals = [np.ones(n), np.full(2 * ne, 0.5), np.full(4 * nq, 0.25)]
    P = sparse.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                          (n + ne + nq, n)).tocsr()
    e = inv.reshape(-1, 4) + n
    c = n + ne + np.arange(nq)
    Q2 = np.concatenate([np.stack([Q[:, k], e[:, k], c, e[:, k - 1]], 1) for k in range(4)])
    return P @ V, Q2, P


def compact(V, Q):
    used = np.unique(Q)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    return V[used], remap[Q], used


# ================================================================ the body
class Body:
    def __init__(self, path):
        d = np.load(path)
        self.d = d
        self.V = d["V"].astype(float)
        self.Q = d["F"].reshape(-1, 4)
        self.names = [str(n) for n in d["bones"]]
        self.heads, self.tails = d["heads"], d["tails"]
        n, nb = len(self.V), len(self.names)
        self.W = sparse.coo_matrix((d["w_val"], (d["w_vert"], d["w_bone"])), (n, nb)).tocsr()
        self.N = vnormals(self.V, self.Q)
        # a dense collision proxy: the body subdivided once (about 7 mm between samples)
        V2, Q2, P2 = subdivide(self.V, self.Q)
        self.PV, self.PN = V2, vnormals(V2, Q2)
        self.tree = cKDTree(self.PV)
        self.vtree = cKDTree(self.V)
        self.bgroup = group_of_bones(self.names)
        self.grp = self.bgroup[np.asarray(self.W.argmax(1)).ravel()]
        self.pgrp = np.asarray((P2 @ np.eye(len(GROUPS))[self.grp]).argmax(1)).ravel()

    def j(self, name, tail=False):
        return (self.tails if tail else self.heads)[self.names.index(name)].astype(float)

    def bone_ids(self, *keys):
        return [i for i, n in enumerate(self.names) if any(k in n for k in keys)]


# ================================================================ cutting a region out of the body
def cut_patch(body, f):
    """Faces of the body whose four corners have f > 0; boundary vertices slid onto f = 0 along their edges to
    outside neighbours. Returns V, Q (renumbered) and the body vertex index of every patch vertex."""
    V, Q = body.V, body.Q
    fv = f(V)
    keep = (fv[Q] > 0).all(1)
    Qk = Q[keep]
    Vp = V.copy()
    E = np.sort(np.stack([Q, np.roll(Q, -1, 1)], 2).reshape(-1, 2), 1)
    E = np.unique(E, axis=0)
    bnd = np.unique(boundary_edges(Qk))
    isb = np.zeros(len(V), bool)
    isb[bnd] = True
    acc = np.zeros_like(V)
    cnt = np.zeros(len(V))
    for a, b in ((0, 1), (1, 0)):
        ia, ib = E[:, a], E[:, b]
        m = isb[ia] & (fv[ib] <= 0) & (fv[ia] > 0)
        t = fv[ia[m]] / (fv[ia[m]] - fv[ib[m]])
        np.add.at(acc, ia[m], V[ia[m]] + (V[ib[m]] - V[ia[m]]) * t[:, None])
        np.add.at(cnt, ia[m], 1)
    m = cnt > 0
    Vp[m] = acc[m] / cnt[m, None]
    Vc, Qc, used = compact(Vp, Qk)
    return Vc, Qc, used


# ================================================================ body part groups and hanging envelopes
GROUPS = ("torso", "armL", "armR", "legL", "legR")


def group_of_bones(names):
    g = np.zeros(len(names), int)
    for i, n in enumerate(names):
        if any(k in n for k in ("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "shoulder01")):
            g[i] = 1 if n.endswith(".L") else 2
        elif any(k in n for k in ("upperleg", "lowerleg", "foot", "toe")):
            g[i] = 3 if n.endswith(".L") else 4
    return g


class Envelope:
    """Loose cloth round a limb or the trunk, seen in slices across an axis: each slice's convex hull (a tape
    measure round it bridges every hollow), then hung: below a bulge the cloth falls at most k metres inward per
    metre down the axis (a straight fall from the chest, the seat, the thigh)."""

    def __init__(self, pts, origin, axis, ref, h0, h1, k, dh=0.01, nth=120, k_up=None):
        a = np.asarray(axis, float)
        self.a = a / np.linalg.norm(a)
        r = np.asarray(ref, float) - self.a * np.dot(ref, self.a)
        self.e1 = r / np.linalg.norm(r)
        self.e2 = np.cross(self.a, self.e1)
        self.o = np.asarray(origin, float)
        self.h0, self.dh, self.nth = h0, dh, nth
        self.hs = np.arange(h0, h1 + dh / 2, dh)
        q = pts - self.o
        h, x, y = q @ self.a, q @ self.e1, q @ self.e2
        th = np.linspace(-np.pi, np.pi, nth, endpoint=False)
        d = np.stack([np.cos(th), np.sin(th)], 1)
        R = np.full((len(self.hs), nth), np.nan)
        from scipy.spatial import ConvexHull
        for i, hc in enumerate(self.hs):
            m = np.abs(h - hc) < dh * 0.75
            if m.sum() < 8:
                continue
            P = np.stack([x[m], y[m]], 1)
            try:
                hull = P[ConvexHull(P).vertices]
            except Exception:
                continue
            A, B = hull, np.roll(hull, -1, 0)
            E = B - A
            # ray t*d hits edge A + s E: t = cross(A, E) / cross(d, E), s = cross(A, d) / cross(d, E)
            den = d[:, None, 0] * E[None, :, 1] - d[:, None, 1] * E[None, :, 0]
            with np.errstate(divide="ignore", invalid="ignore"):
                t = (A[None, :, 0] * E[None, :, 1] - A[None, :, 1] * E[None, :, 0]) / den
                s = (A[None, :, 0] * d[:, None, 1] - A[None, :, 1] * d[:, None, 0]) / den
            ok = (s >= -1e-9) & (s <= 1 + 1e-9) & (t > 0)
            if not ok.any(1).all():
                continue                                    # the axis is outside this slice: skip it
            R[i] = np.where(ok, t, np.inf).min(1)
        good = ~np.isnan(R).all(1)
        for j in range(nth):
            R[:, j] = np.interp(self.hs, self.hs[good], R[good, j])
        R0 = R.copy()
        for i in range(len(self.hs) - 2, -1, -1):           # hang: from the top slice down
            R[i] = np.maximum(R[i], R[i + 1] - k * dh)
        if k_up is not None:                                # and spanning up (the cloth from a bulge to a
            for i in range(1, len(self.hs)):                # shoulder above it is a straight run)
                R[i] = np.maximum(R[i], np.minimum(R[i - 1] - k_up * dh, R[i] + 0.03))
        self.R = R
        self.R0 = R0

    def local(self, P):
        q = P - self.o
        h = q @ self.a
        x, y = q @ self.e1, q @ self.e2
        return h, np.hypot(x, y), np.arctan2(y, x), q - h[:, None] * self.a

    def radius(self, h, th):
        fi = np.clip((h - self.h0) / self.dh, 0, len(self.hs) - 1.001)
        i = fi.astype(int)
        t = fi - i
        fj = (th + np.pi) / (2 * np.pi) * self.nth
        j = np.floor(fj).astype(int) % self.nth
        u = fj - np.floor(fj)
        j1 = (j + 1) % self.nth
        r0 = self.R[i, j] * (1 - u) + self.R[i, j1] * u
        r1 = self.R[i + 1, j] * (1 - u) + self.R[i + 1, j1] * u
        return r0 * (1 - t) + r1 * t

    def push(self, P, extra, mask):
        """Move the masked points radially out to the envelope plus extra (m)."""
        h, r, th, perp = self.local(P[mask])
        want = self.radius(h, th) + extra[mask]
        inside = (h >= self.hs[0]) & (h <= self.hs[-1]) & (r < want)
        Q = P[mask]
        Q[inside] = (self.o + h[inside, None] * self.a + perp[inside] / np.maximum(r[inside, None], 1e-9)
                     * want[inside, None])
        P = P.copy()
        P[mask] = Q
        return P


# ================================================================ draping
def drape(body, V, Q, clear, iters=80, lam=0.45, mu=0.15, proxy=None, fixed=None, envelopes=(), cmax=None):
    """Curvature flow (normal part of the umbrella Laplacian, lam) with a little tangential smoothing (mu), then a
    collision step: every vertex at least clear (m, per vertex) out from the body along the body's normal; then
    the envelopes (Envelope, extra clearance, vertex mask) push the loose parts out."""
    PV, PN, tree = proxy if proxy is not None else (body.PV, body.PN, body.tree)
    A = adjacency(len(V), Q)
    deg = np.asarray(A.sum(1)).ravel()
    bverts = np.unique(boundary_edges(Q))
    isb = np.zeros(len(V), bool)
    isb[bverts] = True
    # boundary vertices smooth only along their boundary loop
    BE = boundary_edges(Q)
    B = sparse.coo_matrix((np.ones(2 * len(BE)), (np.r_[BE[:, 0], BE[:, 1]], np.r_[BE[:, 1], BE[:, 0]])),
                          (len(V), len(V))).tocsr()
    bdeg = np.maximum(np.asarray(B.sum(1)).ravel(), 1)
    V = V.copy()
    for it in range(iters):
        N = vnormals(V, Q)
        L = (A @ V) / deg[:, None] - V
        Lb = (B @ V) / bdeg[:, None] - V
        Ln = (L * N).sum(1, keepdims=True) * N
        step = lam * Ln + mu * (L - Ln)
        step[isb] = 0.5 * Lb[isb]
        if fixed is not None:
            step[fixed] = 0
        V += step
        for env, extra, mask in envelopes:
            V = env.push(V, extra, mask)
        _, i = tree.query(V)
        s = ((V - PV[i]) * PN[i]).sum(1)
        V += np.maximum(clear - s, 0)[:, None] * PN[i]
        if cmax is not None:                                   # held down onto the skin (a tucked hem)
            V -= np.maximum(s - cmax, 0)[:, None] * PN[i]
    return V


def clearance_to(body, V):
    _, i = body.tree.query(V)
    return ((V - body.PV[i]) * body.PN[i]).sum(1)


# ================================================================ skinning
def skin_weights(body, V, Q, smooth=6, top=4, src=None):
    """Weights of the nearest skin vertex, smoothed over the garment, the largest four kept and normalised."""
    if src is None:
        _, i = body.vtree.query(V)
        W = body.W[i].toarray()
    else:
        W = src
    A = adjacency(len(V), Q)
    A = A + sparse.identity(len(V))
    A = sparse.diags(1.0 / np.asarray(A.sum(1)).ravel()) @ A
    for _ in range(smooth):
        W = A @ W
    order = np.argsort(-W, 1)
    W[np.arange(len(V))[:, None], order[:, top:]] = 0
    W /= W.sum(1, keepdims=True)
    return W


def weights_triplets(W, tol=1e-4):
    v, b = np.nonzero(W > tol)
    w = W[v, b]
    s = np.bincount(v, w, len(W))
    return v.astype(np.int32), b.astype(np.int32), (w / s[v]).astype(np.float32)


# ================================================================ UVs: least-squares conformal charts
def cross2(a, b):
    return a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]


def lscm(V, T):
    """Conformal flattening of one disk-like chart (V, triangles T). Pins the two vertices farthest apart."""
    n = len(V)
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1 = p1 - p0
    nrm = np.cross(e1, p2 - p0)
    area = np.linalg.norm(nrm, axis=1) / 2
    ok = area > 1e-12
    T, p0, p1, p2, e1, nrm, area = T[ok], p0[ok], p1[ok], p2[ok], e1[ok], nrm[ok], area[ok]
    ex = e1 / np.linalg.norm(e1, axis=1, keepdims=True)
    ey = np.cross(nrm / np.linalg.norm(nrm, axis=1, keepdims=True), ex)
    xs = np.stack([np.zeros(len(T)), (e1 * ex).sum(1), ((p2 - p0) * ex).sum(1)], 1)
    ys = np.stack([np.zeros(len(T)), np.zeros(len(T)), ((p2 - p0) * ey).sum(1)], 1)
    s = 1 / np.sqrt(2 * area)
    Wr = np.stack([xs[:, 2] - xs[:, 1], xs[:, 0] - xs[:, 2], xs[:, 1] - xs[:, 0]], 1) * s[:, None]
    Wi = np.stack([ys[:, 2] - ys[:, 1], ys[:, 0] - ys[:, 2], ys[:, 1] - ys[:, 0]], 1) * s[:, None]
    m = len(T)
    r = np.repeat(np.arange(m), 3)
    c = T.ravel()
    # complex equation sum W_j (u_j + i v_j) = 0 -> real rows: Wr u - Wi v ; imag rows: Wi u + Wr v
    Mr = sparse.coo_matrix((Wr.ravel(), (r, c)), (m, n)).tocsr()
    Mi = sparse.coo_matrix((Wi.ravel(), (r, c)), (m, n)).tocsr()
    A = sparse.bmat([[Mr, -Mi], [Mi, Mr]]).tocsr()
    # pins: farthest pair (approx.)
    a = np.argmax(np.linalg.norm(V - V.mean(0), axis=1))
    b = np.argmax(np.linalg.norm(V - V[a], axis=1))
    d = np.linalg.norm(V[b] - V[a])
    pins = {a: (0.0, 0.0), b: (d, 0.0)}
    free = np.ones(2 * n, bool)
    x = np.zeros(2 * n)
    for k, (u, v) in pins.items():
        free[k], free[n + k] = False, False
        x[k], x[n + k] = u, v
    rhs = -A[:, ~free] @ x[~free]
    sol = lsqr(A[:, free], rhs, atol=1e-12, btol=1e-12, iter_lim=20000)[0]
    x[free] = sol
    uv = np.stack([x[:n], x[n:]], 1)
    # scale to true size (area-weighted) and turn the chart upright: its 3D "up" (z) along +v
    A3 = area.sum()
    t2 = uv[T]
    A2 = np.abs(cross2(t2[:, 1] - t2[:, 0], t2[:, 2] - t2[:, 0])).sum() / 2
    uv *= np.sqrt(A3 / A2)
    g = np.linalg.lstsq(np.c_[uv - uv.mean(0), np.ones(n)], V[:, 2], rcond=None)[0][:2]
    ang = np.arctan2(g[1], g[0]) - np.pi / 2
    R = np.array([[np.cos(-ang), -np.sin(-ang)], [np.sin(-ang), np.cos(-ang)]])
    uv = (uv - uv.mean(0)) @ R.T
    # keep orientation (not mirrored): the chart's normal side faces the viewer
    t2 = uv[T]
    if (cross2(t2[:, 1] - t2[:, 0], t2[:, 2] - t2[:, 0]) < 0).sum() > len(T) / 2:
        uv[:, 0] *= -1
    return uv


def chart_uvs(V, Q, chart, margin=0.012):
    """Per-corner UVs for quads Q with a chart id per quad: each chart flattened, all at the same scale, packed on
    shelves into the unit square. Returns UV (len(Q) x 4 x 2) and the scale (texture units per metre)."""
    charts = []
    for c in np.unique(chart):
        q = Q[chart == c]
        used, local = np.unique(q, return_inverse=True)
        local = local.reshape(-1, 4)
        T = np.concatenate([local[:, [0, 1, 2]], local[:, [0, 2, 3]]])
        uv = lscm(V[used], T)
        uv -= uv.min(0)
        charts.append((c, used, local, uv))
    # shelf packing by height
    order = sorted(range(len(charts)), key=lambda k: -charts[k][3][:, 1].max())
    total = sum(ch[3].max(0).prod() for ch in charts)

    def place(width):
        x = y = shelf = 0.0
        pos = {}
        for k in order:
            w, h = charts[k][3].max(0) + margin
            if x + w > width:
                x, y, shelf = 0.0, y + shelf, 0.0
            pos[k] = (x, y)
            x += w
            shelf = max(shelf, h)
        return pos, y + shelf

    best = None
    for width in np.sqrt(total) * np.linspace(1.0, 2.2, 40):
        pos, height = place(width)
        side = max(width, height)
        if best is None or side < best[0]:
            best = (side, pos)
    side, pos = best
    UV = np.zeros((len(Q), 4, 2))
    for k, (c, used, local, uv) in enumerate(charts):
        UV[chart == c] = (uv[local] + np.array(pos[k]) + margin / 2) / side
    return UV, 1.0 / side


# ================================================================ the garments
def neck_cut(p):
    """> 0 below the neckline (z of the cut by the angle round the neck's axis: front, sides, back)."""
    th = np.arctan2(p[:, 0] - NECK_AXIS[0], -(p[:, 1] - NECK_AXIS[1]))       # 0 at the front
    b = (NECK_BACK - NECK_FRONT) / -2
    a_c = (NECK_FRONT + NECK_BACK) / 2
    a = (a_c + NECK_SIDE) / 2
    c = a_c - a
    return a + b * np.cos(th) + c * np.cos(2 * th) - p[:, 2]


def arm_axes(body, s):
    S, E, W = body.j(f"upperarm01.{s}"), body.j(f"lowerarm01.{s}"), body.j(f"wrist.{s}")
    return S, E, W


def jersey_region(body):
    cuffs = []
    for s in "LR":
        S, E, W = arm_axes(body, s)
        n = (W - E) / np.linalg.norm(W - E)
        cuffs.append((W - n * CUFF_BACK, n))

    def f(p):
        v = np.minimum(neck_cut(p), p[:, 2] - HEM_Z)
        for c, n in cuffs:
            v = np.minimum(v, ((c - p) * n).sum(1))
        return v
    return f


def pant_region(body):
    def waist(p):
        back = np.clip((p[:, 1] + 0.10) / 0.18, 0, 1)                      # 0 at the front, 1 at the back
        back = back * back * (3 - 2 * back)
        return WAIST_FRONT + (WAIST_BACK - WAIST_FRONT) * back

    def f(p):
        return np.minimum(np.minimum(waist(p) - p[:, 2], p[:, 2] - PANT_CUFF_Z), 0.33 - np.abs(p[:, 0]))
    return f, waist


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


TORSO_ORIGIN = (0.0, -0.03, 0.0)    # the trunk's vertical axis (BODY: midway between chest and back at z 1.1)


def torso_envelope(body, z0, z1, k, k_up=None):
    m = (body.pgrp == 0) & (body.PV[:, 2] > z0 - 0.02) & (body.PV[:, 2] < z1 + 0.02)
    return Envelope(body.PV[m], TORSO_ORIGIN, (0, 0, 1), (0, -1, 0), z0, z1, k, k_up=k_up)


def leg_envelope(body, s, h_low, k):
    H, A = body.j(f"upperleg01.{s}"), body.j(f"foot.{s}")
    m = body.pgrp == (3 if s == "L" else 4)
    return Envelope(body.PV[m], H, H - A, (0, -1, 0), h_low, -0.03, k)


def two_stage(body, V, Q, src, clear_fn, env_fn, iters=(70, 30), cmax_fn=None, cut=None):
    """Drape the coarse patch, subdivide it, drape again (fast convergence over long spans)."""
    g = body.grp[src]
    c = clear_fn(V, g)
    cm = cmax_fn(V) if cmax_fn else None
    V = drape(body, V, Q, c, iters=iters[0], envelopes=env_fn(V, g), cmax=cm)
    V, Q, P = subdivide(V, Q)
    g = np.asarray((P @ np.eye(len(GROUPS))[g]).argmax(1)).ravel()
    c = clear_fn(V, g)
    cm = cmax_fn(V) if cmax_fn else None
    V = drape(body, V, Q, c, iters=iters[1], envelopes=env_fn(V, g), cmax=cm)
    V = drape(body, V, Q, c, iters=25, lam=0.0, mu=0.0, envelopes=env_fn(V, g), cmax=cm)   # even the edges
    if cut is not None:                         # the openings back onto their cut lines, then held there
        b = np.unique(boundary_edges(Q))
        for _ in range(4):
            p = V[b]
            f0 = cut(p)
            gr = np.stack([(cut(p + e) - f0) / 1e-4 for e in np.eye(3) * 1e-4], 1)
            V[b] = p - (f0 / np.maximum((gr * gr).sum(1), 1e-9))[:, None] * gr
        fx = np.zeros(len(V), bool)
        fx[b] = True
        V = drape(body, V, Q, c, iters=8, envelopes=env_fn(V, g), cmax=cm, fixed=fx)
    else:
        V = drape(body, V, Q, c, iters=6, envelopes=env_fn(V, g), cmax=cm)
    return V, Q, P, g, c


def build_pants(body):
    f, waist = pant_region(body)
    V, Q, src = cut_patch(body, f)
    knee = {s: body.j(f"lowerleg01.{s}") for s in "LR"}
    hip = {s: body.j(f"upperleg01.{s}") for s in "LR"}
    tenv = torso_envelope(body, 0.90, 1.13, 0.30)
    lenv = {s: leg_envelope(body, s, knee[s][2] - hip[s][2] - 0.14, PANT_FALL) for s in "LR"}

    def clear_fn(V, g):
        # skin clearance (collision) by region: waistband, seat, thigh, knee (brace room), calf, cuff
        z = V[:, 2]
        c = np.full(len(V), C_SKIN + 0.002)
        for s in "LR":
            K = knee[s]
            leg = g == (3 if s == "L" else 4)
            front = smoothstep(0.03, -0.05, V[:, 1] - K[1])
            kb = (1 - smoothstep(0.05, 0.16, np.abs(z - K[2]))) * front
            cc = C_PANT_THIGH + (C_PANT_KNEE - C_PANT_THIGH) * kb
            calf = smoothstep(0.08, 0.20, K[2] - z)
            cc = cc * (1 - calf) + C_PANT_CALF * calf
            cc = cc + (C_PANT_CUFF - cc) * smoothstep(PANT_CUFF_Z + 0.07, PANT_CUFF_Z + 0.01, z)
            c = np.where(leg, cc, c)
        return c

    def env_fn(V, g):
        z = V[:, 2]
        wz = waist(V)
        ex = C_PANT_SEAT + (C_PANT_WAIST - C_PANT_SEAT) * smoothstep(wz - 0.07, wz - 0.01, z)
        out = [(tenv, ex, (g == 0) & (z > 0.935))]
        for s in "LR":
            K = knee[s]
            front = smoothstep(0.03, -0.05, V[:, 1] - K[1])
            kb = np.exp(-0.5 * ((z - K[2]) / 0.08) ** 2) * front                # pre-curved knee: the front
            exl = C_PANT_THIGH - 0.004 + PANT_KNEE_CURVE * kb
            out.append((lenv[s], exl, (g == (3 if s == "L" else 4)) & (z > K[2] - 0.12)))
        return out

    V, Q, P, g, c = two_stage(body, V, Q, src, clear_fn, env_fn, cut=f)
    return dict(V=V, Q=Q, src=src, P=P, clear=c, grp=g, lenv=lenv, tenv=tenv)


def build_jersey(body, pants=None):
    f = jersey_region(body)
    V, Q, src = cut_patch(body, f)
    _, waist = pant_region(body)
    tenv = torso_envelope(body, 0.92, 1.50, JERSEY_FALL, k_up=JERSEY_SPAN_UP)

    def clear_fn(V, g):
        z = V[:, 2]
        wz = waist(V)
        c = np.full(len(V), C_SKIN)
        c = np.where(z < wz + 0.035, C_TUCK, c)
        for s, gi in (("L", 1), ("R", 2)):
            S, E, W = arm_axes(body, s)
            n = (W - E) / np.linalg.norm(W - E)
            t = ((V - E) * n).sum(1) / np.linalg.norm(W - E)              # 0 at the elbow, 1 at the wrist
            ca = 0.014 + (C_SKIN + 0.001 - 0.014) * smoothstep(0.5, 0.95, t)
            c = np.where(g == gi, ca, c)
        return c

    def env_fn(V, g):
        z = V[:, 2]
        wz = waist(V)
        th = np.arctan2(V[:, 0], -(V[:, 1] - TORSO_ORIGIN[1]))
        sa = 0.5 * smoothstep(1.30, 1.39, z)                       # less ease under the arms, more front and
        ex = C_JERSEY_CHEST * (1 - sa * np.abs(np.sin(th))) / (1 - 2 * sa / np.pi)   # back: the girth is kept
        ex = ex + (C_SKIN - ex) * smoothstep(1.40, 1.50, z)                                   # on the shoulders
        ex = ex + JERSEY_BLOUSE * np.exp(-0.5 * ((z - (wz + 0.07)) / 0.035) ** 2)            # over the waistband
        return [(tenv, ex, (g == 0) & (z > wz + 0.035))]

    def cmax_fn(V):
        wz = waist(V)
        return np.where(V[:, 2] < wz + 0.01, C_TUCK + 0.0015, np.inf)

    V, Q, P, g, c = two_stage(body, V, Q, src, clear_fn, env_fn, cmax_fn=cmax_fn, cut=f)
    return dict(V=V, Q=Q, src=src, P=P, clear=c, grp=g)


def boundary_directed(Q):
    """Boundary edges in the winding of their face (a -> b)."""
    D = np.stack([Q, np.roll(Q, -1, 1)], 2).reshape(-1, 2)
    key = {tuple(e) for e in D.tolist()}
    return np.array([e for e in D.tolist() if (e[1], e[0]) not in key])


def add_rolls(V, Q, spec):
    """Finished edges: every opening's edge turns inward (thickness t) and runs back inside the garment as a facing
    (width w), so an edge seen side-on has the cloth's thickness and a cuff seen end-on shows its inside.
    spec(points) -> (t, w) per boundary vertex. Returns V, Q, parent (each new vertex's garment vertex)."""
    N = vnormals(V, Q)
    BE = boundary_directed(Q)
    bv = np.unique(BE)
    t, w = spec(V[bv])
    tree = cKDTree(V)
    # inward direction along the surface: towards the centroid of the vertex's faces
    cen = np.zeros_like(V)
    cnt = np.zeros(len(V))
    fc = V[Q].mean(1)
    for k in range(4):
        np.add.at(cen, Q[:, k], fc)
        np.add.at(cnt, Q[:, k], 1)
    d = cen[bv] / cnt[bv, None] - V[bv]
    n = N[bv]
    d -= n * (d * n).sum(1, keepdims=True)
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    a1 = V[bv] - n * t[:, None]
    a2 = V[bv] + d * w[:, None]
    for _ in range(3):                         # onto the garment's inside, 1.5 t under its local surface
        dd, j = tree.query(a2, k=4)
        ww = 1 / (dd + 1e-5)
        ww /= ww.sum(1, keepdims=True)
        q = (V[j] * ww[..., None]).sum(1)
        nq = (N[j] * ww[..., None]).sum(1)
        nq /= np.linalg.norm(nq, axis=1, keepdims=True)
        a2 = a2 - nq * (((a2 - q) * nq).sum(1) + 1.5 * t)[:, None]
    nb = len(bv)
    idx1 = len(V) + np.arange(nb)
    idx2 = len(V) + nb + np.arange(nb)
    m1 = -np.ones(len(V), int)
    m2 = -np.ones(len(V), int)
    m1[bv], m2[bv] = idx1, idx2
    Qn = [np.stack([BE[:, 1], BE[:, 0], m1[BE[:, 0]], m1[BE[:, 1]]], 1),
          np.stack([m1[BE[:, 1]], m1[BE[:, 0]], m2[BE[:, 0]], m2[BE[:, 1]]], 1)]
    V2 = np.concatenate([V, a1, a2])
    parent = np.concatenate([np.arange(len(V)), bv, bv])
    return V2, np.concatenate([Q] + Qn), parent


# ================================================================ the Waistlock (pant front)
# PHOTO: Leatt front on-model (1920 px, 0.47 mm/px from the pant's hip width there against his 0.39 m) and the
# Tech1 close-up: a black ratchet buckle low on the right hip, a toothed strap running across the front, down to a
# black textile tab just right of the fly with an X-box stitch.
WL_BUCKLE = (0.026, 0.033, 0.008)     # m, width along the waist, height, thickness (PHOTO 55 x 70 px)
WL_STRAP_W, WL_STRAP_T = 0.016, 0.0025
WL_TOOTH_PITCH, WL_TOOTH_H = 0.005, 0.0012   # PHOTO Tech1: a tooth every 0.32 strap widths; EST height
WL_TAB = (0.061, 0.047, 0.0015)       # m (PHOTO 130 x 100 px)
WL_X_BUCKLE, WL_X_TAB = -0.150, -0.020   # m, his right is -x (PHOTO: buckle 378 px, tab 75 px right of the fly)
WL_DROP = (0.022, 0.047)              # m below the waist top: at the buckle, at the tab (PHOTO)


def front_point(V, N, x, z, r=0.012):
    """The garment's outer surface seen from the front at (x, z): weighted nearest front-facing vertices."""
    m = (N[:, 1] < -0.15) & (V[:, 1] < 0.02)
    P = V[m]
    d2 = (P[:, 0] - x) ** 2 + (P[:, 2] - z) ** 2
    k = np.argsort(d2)[:6]
    w = 1 / (np.sqrt(d2[k]) + 1e-4)
    p = (P[k] * w[:, None]).sum(0) / w.sum()
    n = (N[m][k] * w[:, None]).sum(0)
    return p, n / np.linalg.norm(n)


def loft(rings, cap=True):
    """Quads between closed rings (k, n, 3) plus fan caps; returns V, faces (list)."""
    R = np.asarray(rings, float)
    k, n = R.shape[:2]
    V = list(R.reshape(-1, 3))
    F = []
    for a in range(k - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append((a * n + i, a * n + j, (a + 1) * n + j, (a + 1) * n + i))
    if cap:
        for a, rev in ((0, True), (k - 1, False)):
            c = len(V)
            V.append(R[a].mean(0))
            for i in range(n):
                f = (a * n + i, a * n + (i + 1) % n, c)
                F.append(f[::-1] if rev else f)
    return np.array(V), F


def rrect(w, h, r, n=4):
    r = min(r, w / 2 - 1e-6, h / 2 - 1e-6)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = np.radians(a0 + 90 * k / n)
            pts.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    return np.array(pts)


def block_on(p, n, t_dir, size, bevel, lift=0.0005):
    """A rounded, bevelled block standing on the surface at p (normal n), its width along t_dir."""
    w, h, th = size
    n = n / np.linalg.norm(n)
    t = t_dir - n * np.dot(t_dir, n)
    t /= np.linalg.norm(t)
    b = np.cross(n, t)
    rings = []
    for z, ins in ((0.0, bevel * 0.3), (bevel * 0.5, 0.0), (th - bevel, 0.0), (th, bevel)):
        o = rrect(w - 2 * ins, h - 2 * ins, min(w, h) * 0.18)
        rings.append(p + n * (z + lift) + o[:, :1] * t + o[:, 1:] * b)
    return loft(rings)


def waistlock(pants_V, pants_N, waist_top):
    parts = {}
    # strap path: from under the buckle's far edge to the tab, sloping down across the front
    xs = np.linspace(WL_X_BUCKLE + WL_BUCKLE[0] * 0.3, WL_X_TAB - WL_TAB[0] * 0.2, 60)
    u = (xs - xs[0]) / (xs[-1] - xs[0])
    pts, nrm = [], []
    for x, s in zip(xs, u):
        zt = waist_top(np.array([[x, -0.12, 0]]))[0]
        p, n = front_point(pants_V, pants_N, x, zt - (WL_DROP[0] + (WL_DROP[1] - WL_DROP[0]) * s))
        pts.append(p)
        nrm.append(n)
    P = np.array(pts)
    Nn = np.array(nrm)
    # smooth the path and resample by arc length at a fine step for the teeth
    for _ in range(4):
        P[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    ss = np.arange(0, L[-1], WL_TOOTH_PITCH / 6)
    P = np.stack([np.interp(ss, L, P[:, i]) for i in range(3)], 1)
    Nn = np.stack([np.interp(ss, L, Nn[:, i]) for i in range(3)], 1)
    Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    B = np.cross(Nn, T)
    saw = (ss % WL_TOOTH_PITCH) / WL_TOOTH_PITCH                         # ramps: the ratchet's teeth
    tooth = np.where(ss > L[-1] * 0.08, WL_TOOTH_H * np.clip(saw * 1.25, 0, 1), 0.0)
    hw, t0 = WL_STRAP_W / 2, WL_STRAP_T
    sec = []
    for i in range(len(P)):
        o, n, b = P[i] + Nn[i] * 0.0008, Nn[i], B[i]
        top = t0 + tooth[i]
        sec.append([o - b * hw, o + b * hw, o + b * hw + n * t0, o + b * hw * 0.72 + n * top,
                    o - b * hw * 0.72 + n * top, o - b * hw + n * t0])
    parts["pant_strap"] = loft(sec) + (["strap"],)
    # buckle on its own textile backing, and the tab at the strap's end
    zt = waist_top(np.array([[WL_X_BUCKLE, -0.12, 0]]))[0]
    pb, nb = front_point(pants_V, pants_N, WL_X_BUCKLE, zt - WL_DROP[0] + 0.004)
    tb = np.array([1.0, 0, -0.25])
    V1, F1 = block_on(pb, nb, tb, (WL_BUCKLE[0] + 0.008, WL_BUCKLE[1] + 0.006, 0.0015), 0.0005, lift=0.0003)
    V2, F2 = block_on(pb, nb, tb, WL_BUCKLE, 0.0025, lift=0.0018)
    zt = waist_top(np.array([[WL_X_TAB, -0.12, 0]]))[0]
    pt, nt = front_point(pants_V, pants_N, WL_X_TAB, zt - WL_DROP[1])
    V3, F3 = block_on(pt, nt, np.array([1.0, 0, -0.12]), WL_TAB, 0.0006, lift=0.0003)
    V = np.concatenate([V1, V2, V3])
    F = F1 + [tuple(i + len(V1) for i in f) for f in F2] + [tuple(i + len(V1) + len(V2) for i in f) for f in F3]
    M = [0] * len(F1) + [1] * len(F2) + [0] * len(F3)
    parts["pant_buckle"] = (V, F, ["strap_tab", "buckle"], M)
    return parts


def hidden_skin(body, parts, rings=0):
    """Body vertices under the garments, less `rings` rings from each garment opening."""
    n = len(body.V)
    cov = np.zeros(n, bool)
    for g in parts:
        m = np.zeros(n, bool)
        m[g["src"]] = True
        A = adjacency(n, body.Q)
        inner = m.copy()
        Qm = body.Q[m[body.Q].all(1)]
        bnd = np.unique(boundary_edges(Qm))
        edge = np.zeros(n, bool)
        edge[bnd] = True
        for _ in range(rings):
            edge = edge | (A @ edge.astype(float) > 0)
        inner &= ~edge
        cov |= inner
    return np.nonzero(cov)[0]


# ================================================================ graphics: UV charts
REF = os.path.join(HERE, "..", "..", "reference", "leatt-gear")
TEX_RES = 2048
# raglan seam, his left side (mirror for the right): from the neckline at the front and back down to the armpit
# (PHOTO: Leatt flat front and collar close-up, the seam from the neckline's side to the underarm; BODY points)
RAGLAN_FRONT, RAGLAN_BACK, RAGLAN_PIT = (0.088, -0.072, 1.522), (0.078, 0.052, 1.556), (0.178, -0.005, 1.362)
Y_SIDE = -0.005           # the side seam's plane (BODY: mid-depth of the chest under the arm)


def raglan(body, P, sg):
    a, b, c = (np.array(p) * [sg, 1, 1] for p in (RAGLAN_FRONT, RAGLAN_BACK, RAGLAN_PIT))
    n = np.cross(b - a, c - a)
    if np.dot(body.j(f"wrist.{'L' if sg > 0 else 'R'}") - a, n) < 0:
        n = -n
    return (P - a) @ (n / np.linalg.norm(n))                         # > 0 on the sleeve's side


def arm_frame(body, s):
    """Shoulder point, elbow, cuff end and the unit 'front' and 'outward' directions across the arm."""
    S, E, W = body.j(f"upperarm01.{s}"), body.j(f"lowerarm01.{s}"), body.j(f"wrist.{s}")
    W = W - (W - E) / np.linalg.norm(W - E) * CUFF_BACK
    d = (W - S) / np.linalg.norm(W - S)
    f = np.array([0, -1.0, 0]) - d * (-d[1])
    f /= np.linalg.norm(f)
    o = np.cross(f, d) * (1 if s == "L" else -1)
    if o[0] * (1 if s == "L" else -1) < 0:
        o = -o
    return S, E, W, f, o


def snap_to_field(V, Q, f, sel):
    """Slide the vertices beside a seam (field f = 0) onto it, so the seam runs straight across the faces instead
    of stair-stepping along their edges. sel: vertices allowed to move."""
    V = V.copy()
    fv = f(V)
    E, _ = edges_of(Q)
    cross = (np.sign(fv[E[:, 0]]) != np.sign(fv[E[:, 1]])) & sel[E[:, 0]] & sel[E[:, 1]]
    cand = np.unique(np.where(np.abs(fv[E[cross, 0]]) < np.abs(fv[E[cross, 1]]), E[cross, 0], E[cross, 1]))
    for _ in range(3):
        p = V[cand]
        f0 = f(p)
        gr = np.stack([(f(p + e) - f0) / 1e-4 for e in np.eye(3) * 1e-4], 1)
        V[cand] = p - (f0 / np.maximum((gr * gr).sum(1), 1e-9))[:, None] * gr
    return V


def straight_seams_jersey(body, V, Q):
    """Raglan seams, side seams and the sleeves' split lines made straight."""
    for s, sg in (("L", 1), ("R", -1)):
        V = snap_to_field(V, Q, lambda P: raglan(body, P, sg), (V[:, 0] * sg > 0.04) & (V[:, 2] > RAGLAN_PIT[2] - 0.03))
        V = snap_to_field(V, Q, lambda P: arm_front(body, s, P), (V[:, 0] * sg > 0.1) & (raglan(body, V, sg) > 0.005))
    torso = (raglan(body, V, 1) < -0.005) & (raglan(body, V, -1) < -0.005)
    return snap_to_field(V, Q, lambda P: P[:, 1] - Y_SIDE, torso & (np.abs(V[:, 0]) > 0.08))


def straight_seams_pants(pants, V, Q):
    V = snap_to_field(V, Q, lambda P: P[:, 0], np.ones(len(V), bool))
    for s, sg in (("L", 1), ("R", -1)):
        env = pants["lenv"][s]
        V = snap_to_field(V, Q, lambda P: (P - env.o) @ env.e1, V[:, 0] * sg > 0.01)
    return V


def jersey_charts(body, V, Q):
    """0 front, 1 back, 2/3 left sleeve front/back, 4/5 right sleeve front/back (one chart per pattern piece,
    the sleeves halved along their top line)."""
    c = V[Q].mean(1)
    ch = np.where(c[:, 1] < Y_SIDE, 0, 1)
    for s, sg, k in (("L", 1, 2), ("R", -1, 4)):
        sl = (raglan(body, c, sg) > 0) & (c[:, 0] * sg > 0)
        ch = np.where(sl, np.where(arm_front(body, s, c) > 0, k, k + 1), ch)
    return ch


def arm_front(body, s, P):
    """> 0 in front of the arm: the plane through each segment's axis (upper arm, forearm) square to the front."""
    S, E, W, f, o = arm_frame(body, s)
    out = np.zeros(len(P))
    for A, B, m in ((S, E, ((P - S) @ (E - S)) < np.dot(E - S, E - S)), (E, W, None)):
        d = (B - A) / np.linalg.norm(B - A)
        fs = np.array([0, -1.0, 0]) - d * (-d[1])
        fs /= np.linalg.norm(fs)
        v = (P - A) @ fs
        out = np.where(m, v, out) if m is not None else np.where(((P - S) @ (E - S)) >= np.dot(E - S, E - S), v, out)
    return out


def pant_charts(pants, V, Q):
    c = V[Q].mean(1)
    ch = np.zeros(len(Q), int)
    for s, k in (("L", 0), ("R", 2)):
        h, r, th, _ = pants["lenv"][s].local(c)
        side = c[:, 0] > 0 if s == "L" else c[:, 0] <= 0
        ch = np.where(side, np.where(np.abs(th) < np.pi / 2, k, k + 1), ch)
    return ch


def corner_uvs(Q_all, n_main, UVmain, parent):
    """UVs for every face corner: the main faces' own, the turned edges' from their edge vertex."""
    per_v = {}
    for f, uv in zip(Q_all[:n_main], UVmain):
        for v, t in zip(f, uv):
            per_v.setdefault(int(v), t)
    out = np.zeros((len(Q_all), 4, 2))
    out[:n_main] = UVmain
    for i in range(n_main, len(Q_all)):
        out[i] = [per_v[int(parent[v])] for v in Q_all[i]]
    return out


def raster(UV, V, N, Q, chart, res=TEX_RES):
    """Texel maps from the charts: rest-pose position, normal and chart of the cloth at every texel centre (v up:
    row 0 is v = 0, flipped when saved)."""
    pos = np.zeros((res, res, 3))
    nrm = np.zeros((res, res, 3))
    chm = -np.ones((res, res), int)
    T = np.concatenate([np.stack([Q[:, 0], Q[:, 1], Q[:, 2]], 1), np.stack([Q[:, 0], Q[:, 2], Q[:, 3]], 1)])
    TU = np.concatenate([UV[:, [0, 1, 2]], UV[:, [0, 2, 3]]]) * res - 0.5
    TC = np.concatenate([chart, chart])
    for t in range(len(T)):
        a, b, c = TU[t]
        x0, x1 = int(np.floor(min(a[0], b[0], c[0]))), int(np.ceil(max(a[0], b[0], c[0])))
        y0, y1 = int(np.floor(min(a[1], b[1], c[1]))), int(np.ceil(max(a[1], b[1], c[1])))
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, res - 1), min(y1, res - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not m.any():
            continue
        W3 = np.stack([w0[m], w1[m], w2[m]], 1)
        yy, xx = gy[m], gx[m]
        pos[yy, xx] = W3 @ V[T[t]]
        nrm[yy, xx] = W3 @ N[T[t]]
        chm[yy, xx] = TC[t]
    nrm /= np.maximum(np.linalg.norm(nrm, axis=2, keepdims=True), 1e-9)
    return pos, nrm, chm


def dilate(img, mask, px=12):
    """Fill the texels outside the charts from the nearest painted texel (no seams when filtered)."""
    from scipy import ndimage
    d, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
    out = img[iy, ix]
    keep = d > px
    out[keep] = img[mask].mean(0)
    return out


# ================================================================ graphics: photos
class Photo:
    """One of Leatt's photos, denoised (a 5 px median takes out the micro-mesh's dots, keeps the print's edges),
    sampled bilinearly. exclude: boxes (x0, y0, x1, y1) that are not the garment (helmet, hands), filled from the
    nearest garment pixel."""

    def __init__(self, name, exclude=(), median=5):
        from PIL import Image
        from scipy import ndimage
        im = Image.open(os.path.join(REF, name))
        self.alpha = None
        if im.mode in ("P", "RGBA", "LA"):
            im = im.convert("RGBA")
            self.alpha = np.asarray(im)[..., 3] > 128
        a = np.asarray(im.convert("RGB")).astype(float) / 255
        a = np.stack([ndimage.median_filter(a[..., k], size=median) for k in range(3)], 2)
        if self.alpha is None:                     # a white studio background: near-white touching the border
            lab, _ = ndimage.label(a.min(2) > 0.90)
            edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
            bad = np.isin(lab, edge[edge > 0])
            bad = ndimage.binary_dilation(bad, iterations=3)
        else:
            bad = ~ndimage.binary_erosion(self.alpha, iterations=2)
        for x0, y0, x1, y1 in exclude:
            bad[y0:y1, x0:x1] = True
        if bad.any():
            _, (iy, ix) = ndimage.distance_transform_edt(bad, return_indices=True)
            a = a[iy, ix]
        self.a = a

    def sample(self, u, v):
        H, W = self.a.shape[:2]
        u = np.clip(u, 0, W - 1.001)
        v = np.clip(v, 0, H - 1.001)
        i, j = v.astype(int), u.astype(int)
        fy, fx = (v - i)[:, None], (u - j)[:, None]
        A = self.a
        return (A[i, j] * (1 - fx) * (1 - fy) + A[i, j + 1] * fx * (1 - fy) + A[i + 1, j] * (1 - fx) * fy
                + A[i + 1, j + 1] * fx * fy)


# Jersey photo landmarks (PHOTO, Leatt on-model 1600 px; ledger "Graphics"): front: neckline centre (800, 290),
# torso 575 px across at the chest for his 0.38 m; the pant top (centre) at 1130. Back: neckline (790, 258),
# torso 613 px across, the pant top at 1040. The rows are fitted to his neckline and pant top.
JF_C, JF_V0, JF_KX = 800.0, 290.0, 1513.0
JB_C, JB_V0, JB_KX = 790.0, 258.0, 1580.0
JF_KZ = (1130 - 290) / (NECK_FRONT - WAIST_FRONT)
JB_KZ = (1040 - 258) / (NECK_BACK - WAIST_BACK)
# sleeves (PHOTO): shoulder point and cuff end of each arm in each photo, pixels
J_ARMS = {("front", "R"): ((400, 370), (350, 1300)), ("front", "L"): ((1205, 370), (1255, 1300)),
          ("back", "L"): ((427, 400), (293, 1324)), ("back", "R"): ((1156, 409), (1271, 1324))}
J_ARM_HALF = ((0.0, 0.2, 0.6, 1.0), (68, 72, 60, 48))   # px: 0.85 of half the sleeve's width (PHOTO front), so
                                                        # the silhouette's soft edge is never sampled


def jersey_photo_uv(body, P, view):
    if view == "front":
        return JF_C + JF_KX * P[:, 0], JF_V0 + JF_KZ * (NECK_FRONT - P[:, 2])
    return JB_C - JB_KX * P[:, 0], JB_V0 + JB_KZ * (NECK_BACK - P[:, 2])


def sleeve_photo_uv(body, P, s, view):
    """A sleeve point in one of the photos: along the arm (shoulder point to cuff, upper arm then forearm) and
    across it (outward from the arm's line, the photo's arm seen square on)."""
    S, E, W, f, o = arm_frame(body, s)
    L1, L2 = np.linalg.norm(E - S), np.linalg.norm(W - E)
    d1, d2 = (E - S) / L1, (W - E) / L2
    o1 = o - d1 * np.dot(o, d1)
    o2 = o - d2 * np.dot(o, d2)
    o1, o2 = o1 / np.linalg.norm(o1), o2 / np.linalg.norm(o2)
    t1 = (P - S) @ d1
    upper = t1 < L1
    t = np.where(upper, t1, L1 + np.clip((P - E) @ d2, 0, None)) / (L1 + L2)
    lat = np.where(upper, (P - S) @ o1, (P - E) @ o2)
    rad = np.where(upper, np.linalg.norm((P - S) - np.outer(t1, d1), axis=1),
                   np.linalg.norm((P - E) - np.outer((P - E) @ d2, d2), axis=1))
    lat = lat / np.maximum(rad, 1e-6)                                   # -1 .. 1 across the arm seen square on
    half = np.interp(t, J_ARM_HALF[0], J_ARM_HALF[1])
    (u0, v0), (u1, v1) = J_ARMS[(view, s)]
    A, B = np.array([u0, v0], float), np.array([u1, v1], float)
    dd = (B - A) / np.linalg.norm(B - A)
    out_px = np.array([dd[1], -dd[0]])                              # across the photo's arm, away from the body
    if np.dot(out_px, (A + B) / 2 - [800.0, (v0 + v1) / 2]) < 0:
        out_px = -out_px
    q = A + t[:, None] * (B - A) + (lat * half)[:, None] * out_px
    return q[:, 0], q[:, 1], t


# Pant photo landmarks (PHOTO, Leatt US on-model 1920 px): rows of the waist top, crotch and boot top; the
# pant's silhouette in each row (alpha) gives the across position, mapped onto his pant's silhouette.
THIGH_LOGO = (0.19, -0.005, 0.26)   # m: centre above the knee joint, y, length (PHOTO: knee+5 to +31 cm)
PF_ROWS = ((205, WAIST_FRONT), (None, 0.862), (1670, PANT_CUFF_Z + 0.005))   # crotch row: from alpha
PB_ROWS = ((190, WAIST_BACK), (None, 0.862), (1650, PANT_CUFF_Z + 0.005))


def pant_photo_uv(pants, P, view, alpha, sil3d):
    rows = list(PF_ROWS if view == "front" else PB_ROWS)
    r0 = np.nonzero(alpha[400])[0]
    cx0 = int(np.median(r0))
    cy = 400 + int(np.argmax(~alpha[400:1200, cx0 - 4:cx0 + 5].any(1)))   # the photo's crotch: first open row
    rows[1] = (cy, rows[1][1])
    ys = np.array([r[0] for r in rows], float)
    zs = np.array([r[1] for r in rows], float)
    v = np.interp(-P[:, 2], -zs, ys)
    u = np.zeros(len(P))
    vi = np.clip(v.astype(int), 0, alpha.shape[0] - 1)
    crotch_y = cy
    for y in np.unique(vi):
        m = vi == y
        r = alpha[y]
        xs = np.nonzero(r)[0]
        if len(xs) < 10:
            continue
        runs = [(q[0], q[-1]) for q in np.split(xs, np.nonzero(np.diff(xs) > 3)[0] + 1) if len(q) > 40]
        if not runs:
            continue
        cx = alpha.shape[1] / 2
        if y < crotch_y:                                     # the whole pant: the run nearest the middle
            run = min(runs, key=lambda q: abs((q[0] + q[1]) / 2 - cx) if q[0] <= cx <= q[1] else 1e9)
            spans = {"L": run, "R": run}
        else:
            legs = sorted([q for q in runs if q[1] - q[0] > 120 and abs((q[0] + q[1]) / 2 - cx) < 500],
                          key=lambda q: q[0])
            if len(legs) < 2:
                continue
            left_img, right_img = legs[0], legs[-1]
            # front: his right leg on the image's left; back: his left leg on the image's left
            spans = {"R": left_img, "L": right_img} if view == "front" else {"L": left_img, "R": right_img}
        zq = P[m, 2]
        xq = P[m, 0]
        for s in "LR":
            mm = (xq > 0) if s == "L" else (xq <= 0)
            if not mm.any():
                continue
            xl = np.interp(zq[mm], sil3d[s][0], sil3d[s][1])
            xr = np.interp(zq[mm], sil3d[s][0], sil3d[s][2])
            if y < crotch_y:
                xl = np.interp(zq[mm], sil3d["all"][0], sil3d["all"][1])
                xr = np.interp(zq[mm], sil3d["all"][0], sil3d["all"][2])
            t = (xq[mm] - xl) / np.maximum(xr - xl, 1e-6)
            if view == "back":
                t = 1 - t
            a, b = spans[s]
            idx = np.nonzero(m)[0][mm]
            u[idx] = a + t * (b - a)
    return u, v


def pant_silhouette(V, crotch_z):
    """His pant's front-view silhouette per height: (z, x_left, x_right) per leg below the crotch and whole above."""
    zs = np.arange(PANT_CUFF_Z, WAIST_BACK + 0.005, 0.005)
    out = {}
    for key, sel in (("L", V[:, 0] > 0), ("R", V[:, 0] <= 0), ("all", np.ones(len(V), bool))):
        lo, hi = [], []
        for z in zs:
            m = sel & (np.abs(V[:, 2] - z) < 0.006)
            if key != "all" and z < crotch_z:
                pass
            lo.append(V[m, 0].min() if m.any() else np.nan)
            hi.append(V[m, 0].max() if m.any() else np.nan)
        lo, hi = np.array(lo), np.array(hi)
        ok = ~np.isnan(lo)
        out[key] = (zs[ok], lo[ok], hi[ok])
    return out


# ================================================================ graphics: stamps and Damien's additions
def logo_stamps():
    """Leatt's wordmark and brain icon as alpha masks, cut from the chest of the front on-model photo (PHOTO:
    LEATT at x 610-1015, y 495-600; the brain at x 975-1020, y 452-492), white on pink."""
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(REF, "jersey", "jersey55_tigerpink_front-on-model_nz-distributor_"
                                                    "LE5026000201-2_1600.jpg")).convert("RGB")).astype(float) / 255

    def cut(x0, y0, x1, y1):
        c = a[y0:y1, x0:x1]
        w = smoothstep(0.55, 0.8, c.min(2)) * smoothstep(0.35, 0.15, c.max(2) - c.min(2))
        return w
    return cut(606, 492, 1018, 603), cut(972, 450, 1023, 494)


def font(size, bold=True, italic=False):
    from PIL import ImageFont
    for f in (("/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf" if italic else
               "/usr/share/fonts/opentype/inter/Inter-Bold.otf"), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


class Canvas:
    """A flat drawing in metres, laid on the cloth by a parallel projection: axes (a, b) are 3D unit vectors of
    the canvas's right and up; a texel at P takes the canvas's pixel at ((P - o).a, (P - o).b)."""

    def __init__(self, o, a, b, w, h, ppm=2000):
        from PIL import Image
        self.o, self.a, self.b = np.asarray(o, float), np.asarray(a, float), np.asarray(b, float)
        self.w, self.h, self.ppm = w, h, ppm
        self.W, self.H = int(w * ppm), int(h * ppm)
        self.rgb = Image.new("RGB", (self.W, self.H), (0, 0, 0))
        self.alpha = Image.new("L", (self.W, self.H), 0)

    def px(self, x, y):                                          # canvas metres (from its centre) to pixels
        return (self.W / 2 + x * self.ppm, self.H / 2 - y * self.ppm)

    def text(self, x, y, s, size_m, fill, outline=None, outline_m=0.0, italic=False, spacing=0.0, anchor="mm",
             shear=0.0):
        from PIL import Image, ImageDraw
        if shear:                                   # slanted lettering: drawn upright on a layer, then sheared
            lay = Canvas(self.o, self.a, self.b, self.w, self.h, self.ppm)
            lay.text(x, y, s, size_m, fill, outline, outline_m, italic, spacing, anchor)
            cx, cy = self.px(x, y)
            M = (1, shear, -shear * cy, 0, 1, 0)
            r = lay.rgb.transform(lay.rgb.size, Image.AFFINE, M, resample=Image.BICUBIC)
            al = lay.alpha.transform(lay.alpha.size, Image.AFFINE, M, resample=Image.BICUBIC)
            self.rgb.paste(r, (0, 0), al)
            self.alpha.paste(Image.fromarray(np.maximum(np.asarray(self.alpha), np.asarray(al))))
            return
        f = font(int(size_m * self.ppm * 1.3), italic=italic)
        for img, col in ((self.rgb, fill), (self.alpha, 255)):
            d = ImageDraw.Draw(img)
            kw = {}
            if outline is not None:
                kw = dict(stroke_width=int(outline_m * self.ppm), stroke_fill=(outline if img is self.rgb else 255))
            if spacing:
                X = x - (len(s) - 1) * spacing / 2
                for ch in s:
                    d.text(self.px(X, y), ch, font=f, fill=col, anchor=anchor, **kw)
                    X += spacing
            else:
                d.text(self.px(x, y), s, font=f, fill=col, anchor=anchor, **kw)

    def rect(self, x0, y0, x1, y1, fill, r=0.0, outline=None, width_m=0.0):
        from PIL import ImageDraw
        for img, col, oc in ((self.rgb, fill, outline), (self.alpha, 255, 255 if outline else None)):
            d = ImageDraw.Draw(img)
            p0, p1 = self.px(x0, y1), self.px(x1, y0)
            d.rounded_rectangle([p0, p1], radius=int(r * self.ppm), fill=col, outline=oc,
                                width=max(1, int(width_m * self.ppm)) if outline else 0)

    def stamp(self, mask, x, y, w_m, rot=0, color=(255, 255, 255)):
        from PIL import Image
        m = Image.fromarray((mask * 255).astype(np.uint8))
        h_m = w_m * mask.shape[0] / mask.shape[1]
        m = m.resize((max(1, int(w_m * self.ppm)), max(1, int(h_m * self.ppm))), Image.LANCZOS).rotate(rot, expand=True)
        cx, cy = self.px(x, y)
        box = (int(cx - m.width / 2), int(cy - m.height / 2))
        self.rgb.paste(Image.new("RGB", m.size, color), box, m)
        a = self.alpha.crop((box[0], box[1], box[0] + m.width, box[1] + m.height))
        self.alpha.paste(Image.fromarray(np.maximum(np.asarray(a), np.asarray(m))), box)

    def apply(self, img, pos, mask):
        q = pos[mask] - self.o
        x, y = q @ self.a, q @ self.b
        u, v = self.px(x, y)
        ok = (u >= 0) & (u < self.W - 1) & (v >= 0) & (v < self.H - 1)
        A = np.asarray(self.alpha).astype(float) / 255
        C = np.asarray(self.rgb).astype(float) / 255
        idx = np.nonzero(mask)
        ii, jj = idx[0][ok], idx[1][ok]
        ui, vi = u[ok].astype(int), v[ok].astype(int)
        al = A[vi, ui][:, None]
        img[ii, jj] = img[ii, jj] * (1 - al) + C[vi, ui] * al
        return img


# ================================================================ graphics: Damien's additions (his own print)
# Ledger "Damien's additions". Not Leatt's print: his number and name on the back (PHOTO 06), his sponsors on the
# front (PHOTO 09 and 08; 07 shows nothing on the left side). Every graphic is lifted from his own bike art or from
# the sponsors' official files (reference/sponsors, README there: URLs and the check against his photos), never
# retyped in a font; only the name is set in a font (his photos do not resolve its lettering).
ART = os.path.join(HERE, "..", "..", "textures", "damien-v1", "art")
SPONSORS = os.path.join(HERE, "..", "..", "reference", "sponsors")
INK_WHITE, INK_DARK = (246, 245, 250), (34, 24, 44)   # PHOTO 06: white digits, dark purple-grey outline
NUMBER_W = 0.300         # m, the 114 with its outline across the flat back panel (PHOTO 06: 0.59 of his 0.49 m
                         # deltoid breadth as seen = 0.29 m; plus 3 % for the back's wrap)
NUMBER_OUTLINE = 0.0045  # m (PHOTO 06: 0.024 of the number's height)
NUMBER_TOP = 0.37        # the back collar's centre to the number's top, in number heights (PHOTO 06)
NAME = "DAMIEN"          # Damien (2026-11-13)
NAME_FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
NAME_SEEN = ("DAMI", 0.585)   # PHOTO 06: the first four letters in front of a fold of the jersey at the collar
                              # span 0.585 number widths (EN shows past the fold); the whole name is longer
NAME_LEN = 0.89          # the whole name in number widths: 0.585 x ink width of DAMIEN / DAMI in NAME_FONT (0.658)
NAME_LEFT, NAME_RIGHT = -NAME_LEN / 2, NAME_LEN / 2   # centred over the number (Damien 2026-11-13: "perfectly
                                                      # centered", 06's camera angle and the fold shift it)
NAME_H = 0.146           # letter height with the outline, in number heights (PHOTO 06)
NAME_GAP = 0.05          # the name's bottom above the number's top, in number heights (PHOTO 06)
NAME_OUTLINE = 0.0022    # m
GLYPH_SLANT = 0.23       # tan of the italic lean of the 114 on his plate art (stems: 114 px over 500); the name too
# front patches: centre (x, z) on the front (Leatt's photo frame, as the print) and width with any contour, m;
# heights follow the official artwork (PHOTO 09 and 08 against the chest LEATT, then the photo-matched renders)
FRONT = {"bikewise": (-0.091, 1.447, 0.095), "pirelli": (0.102, 1.446, 0.080), "usn": (-0.063, 1.320, 0.080),
         "motul": (-0.057, 1.286, 0.064), "cworx": (0.064, 1.313, 0.077)}
CONTOUR = 0.0016         # m, white contour round the USN and Cycleworx inks on the black jersey (PHOTO 08)
PRINT_LIFT = 0.0001      # m, the print overlay over the cloth (0.3 mm left a contact-shadow line at its edges)
PRINT_TEXEL = {"number": 0.25e-3, "name": 0.15e-3, "front": 0.10e-3}   # m per texel of the print atlas
ATLAS_RES = 2048


class Art:
    """A flat graphic: premultiplied RGBA (float, rows top down), w metres wide; sampled at (s, t) metres from its
    centre (s to the reader's right, t up), box-filtered to the texel size it is printed at."""

    def __init__(self, rgba, w):
        self.rgba = np.ascontiguousarray(rgba, np.float32)
        H, W = self.rgba.shape[:2]
        self.w, self.h = w, w * H / W
        self.levels = {}

    def level(self, texel):
        from PIL import Image
        H, W = self.rgba.shape[:2]
        n = int(np.clip(round(self.w / texel), 4, W))
        if n not in self.levels:
            m = max(2, int(round(H * n / W)))
            self.levels[n] = self.rgba if n == W else np.stack(
                [np.asarray(Image.fromarray(self.rgba[..., k]).resize((n, m), Image.BOX)) for k in range(4)], 2)
        return self.levels[n]

    def sample(self, s, t, texel):
        from scipy import ndimage
        A = self.level(texel)
        H, W = A.shape[:2]
        u = (s / self.w + 0.5) * W - 0.5
        v = (0.5 - t / self.h) * H - 0.5
        return np.stack([ndimage.map_coordinates(A[..., k], [v, u], order=1, mode="constant", cval=0.0)
                         for k in range(4)], 1)


def contoured(rgba, px, colour):
    """Premultiplied RGBA with a contour px wide in `colour` round its ink (padded to fit)."""
    from scipy import ndimage
    p = int(np.ceil(px)) + 4
    a = np.pad(rgba, ((p, p), (p, p), (0, 0)))
    d = ndimage.distance_transform_edt(a[..., 3] < 0.5)
    ring = smoothstep(px + 0.7, px - 0.7, d)
    out = a.copy()
    out[..., 3] = np.maximum(a[..., 3], ring)
    out[..., :3] += np.array(colour, np.float32) / 255 * (out[..., 3] - a[..., 3])[..., None]
    return out


def ink(mask, colour):
    return np.dstack([mask[..., None] * (np.array(colour, np.float32) / 255), mask]).astype(np.float32)


def number_art():
    """His 114 lifted from his plate art (the cleanest of his bike's 114s): the three white glyphs (the plate's bolt
    hole and small logo dropped), anti-aliased by the art's own edges; the plate's black keyline where the 4 overlaps
    the second 1 and the slashes stay dark; a dark outline round the whole (PHOTO 06)."""
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(os.path.join(ART, "plate.png")).convert("RGB")).astype(np.float32) / 255
    zone = np.zeros(a.shape[:2], bool)
    zone[600:1480, 220:1540] = True                      # the number's field on the plate
    hard = (a.min(2) > 0.6) & zone
    lab, n = ndimage.label(hard)
    size = ndimage.sum(hard, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.argsort(-size)[:3])       # 1, 1, 4
    near = ndimage.binary_dilation(keep, iterations=2) & ~ndimage.binary_dilation(hard & ~keep, iterations=3)
    soft = smoothstep(0.35, 0.8, a.min(2)) * near
    ys, xs = np.nonzero(keep)
    px = (xs.max() - xs.min() + 1) / (NUMBER_W - 2 * NUMBER_OUTLINE)     # art pixels per metre
    p = int(NUMBER_OUTLINE * px) + 4
    m = soft[ys.min() - p:ys.max() + 1 + p, xs.min() - p:xs.max() + 1 + p]
    rgba = contoured(ink(m, INK_WHITE)[p:-p, p:-p], NUMBER_OUTLINE * px, INK_DARK)
    return Art(rgba, rgba.shape[1] / px)


def name_art(number):
    """DAMIEN in heavy capitals stretched to the measured length, leaned like his 114, white with the number's dark
    outline (PHOTO 06: wide bold capitals with an outline; the photo does not resolve the typeface)."""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(NAME_FONT, 600)
    l, t, r, b = f.getbbox(NAME)
    im = Image.new("L", (r - l + 40, b - t + 40), 0)
    ImageDraw.Draw(im).text((20 - l, 20 - t), NAME, font=f, fill=255)
    m = np.asarray(im).astype(np.float32) / 255
    ys, xs = np.nonzero(m > 0.5)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H = NAME_H * number.h                                # letter height with the outline, m
    L = (NAME_RIGHT - NAME_LEFT) * number.w              # length with the outline, m
    px = (m.shape[0] - 1) / (H - 2 * NAME_OUTLINE)       # art pixels per metre (letters' height fixed)
    w_up = (L - 2 * NAME_OUTLINE) * px - GLYPH_SLANT * m.shape[0]   # upright width, so the leaned name has length L
    im = Image.fromarray(m).resize((int(round(w_up)), m.shape[0]), Image.LANCZOS)
    h, sh = im.height, int(np.ceil(GLYPH_SLANT * im.height))
    im = im.transform((im.width + sh, h), Image.AFFINE, (1, GLYPH_SLANT, -GLYPH_SLANT * h, 0, 1, 0), Image.BICUBIC)
    rgba = contoured(ink(np.clip(np.asarray(im), 0, 1), INK_WHITE), NAME_OUTLINE * px, INK_DARK)
    return Art(rgba, rgba.shape[1] / px)


def svg_mask(path, scale):
    """A minimal SVG path filler (M L H V C S Q Z, absolute and relative; curves flattened; even-odd): the mask of
    every <path> in the file at `scale` pixels per SVG unit."""
    import re
    from PIL import Image, ImageDraw
    s = open(path).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
    W, H = int(np.ceil(vb[2] * scale)), int(np.ceil(vb[3] * scale))
    acc = np.zeros((H, W), bool)
    for d in re.findall(r'<path[^>]* d="([^"]+)"', s):
        toks = re.findall(r"[MmLlHhVvCcSsQqZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", d)
        polys, cur, start, last_c, cmd, i = [], [], np.zeros(2), None, None, 0
        pos = np.zeros(2)

        def num(k):
            return np.array([float(toks[i + j]) for j in range(k)])
        while i < len(toks):
            if toks[i].isalpha():
                cmd = toks[i]
                i += 1
                if cmd in "Zz":
                    if cur:
                        polys.append(cur)
                    cur, pos = [], start.copy()
                    continue
            rel = cmd.islower()
            c = cmd.upper()
            if c == "M":
                p = num(2) + (pos if rel else 0)
                i += 2
                if cur:
                    polys.append(cur)
                cur, pos, start = [p], p, p.copy()
                cmd = "l" if rel else "L"
            elif c in "LHV":
                if c == "L":
                    p = num(2) + (pos if rel else 0)
                    i += 2
                elif c == "H":
                    p = np.array([float(toks[i]) + (pos[0] if rel else 0), pos[1]])
                    i += 1
                else:
                    p = np.array([pos[0], float(toks[i]) + (pos[1] if rel else 0)])
                    i += 1
                cur.append(p)
                pos = p
            elif c in "CSQ":
                k = {"C": 6, "S": 4, "Q": 4}[c]
                q = num(k).reshape(-1, 2) + (pos if rel else 0)
                i += k
                if c == "S":
                    c1 = 2 * pos - last_c if last_c is not None else pos
                    q = np.vstack([c1, q])
                ctrl = np.vstack([pos, q])
                tt = np.linspace(0, 1, 17)[1:, None]
                if len(ctrl) == 4:
                    pts = ((1 - tt) ** 3 * ctrl[0] + 3 * (1 - tt) ** 2 * tt * ctrl[1] + 3 * (1 - tt) * tt ** 2
                           * ctrl[2] + tt ** 3 * ctrl[3])
                else:
                    pts = (1 - tt) ** 2 * ctrl[0] + 2 * (1 - tt) * tt * ctrl[1] + tt ** 2 * ctrl[2]
                cur.extend(list(pts))
                last_c = ctrl[-2]
                pos = ctrl[-1]
                continue
            last_c = None
        if cur:
            polys.append(cur)
        for poly in polys:
            if len(poly) < 3:
                continue
            im = Image.new("1", (W, H), 0)
            ImageDraw.Draw(im).polygon([tuple((p - vb[:2]) * scale) for p in poly], fill=1)
            acc ^= np.asarray(im)
    return acc


def logo(name):
    from PIL import Image
    return np.asarray(Image.open(os.path.join(SPONSORS, name)).convert("RGBA")).astype(np.float32) / 255


def front_arts():
    """The sponsors' official artwork (reference/sponsors) as printed on his jersey (PHOTO 09 and 08)."""
    from PIL import Image
    arts = {}
    # BikeWise: the logo (black on white, red sprocket) on its white box, a white margin of 4 % of its width
    a = logo("bikewise_logo.png")
    ys, xs = np.nonzero(a[..., :3].max(2) < 0.6)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    p = int(0.04 * a.shape[1])
    a = np.pad(a, ((p, p), (p, p), (0, 0)), constant_values=1.0)
    arts["bikewise"] = a
    # Pirelli: its yellow box with the red long-P PIRELLI, exactly the box
    a = logo("pirelli_logo.png")
    ys, xs = np.nonzero((a[..., 0] > 0.8) & (a[..., 1] > 0.7) & (a[..., 2] < 0.3))
    arts["pirelli"] = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # USN: navy atom and letters (the registered sign included), a white contour on the black jersey
    a = logo("usn_logo.png")
    a[..., :3] *= a[..., 3:]
    ys, xs = np.nonzero(a[..., 3] > 0.05)
    arts["usn"] = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # Motul: the site's white wordmark on its red box (#ed1c24), the box being the SVG's viewBox
    m = svg_mask(os.path.join(SPONSORS, "motul_logo.svg"), 12).astype(np.float32)
    m = np.asarray(Image.fromarray(m).resize((m.shape[1] // 2, m.shape[0] // 2), Image.BOX))   # 2x2 anti-aliasing
    red = np.array([0xED, 0x1C, 0x24], np.float32) / 255
    arts["motul"] = np.dstack([red * (1 - m[..., None]) + m[..., None], np.ones_like(m)])
    # Cycleworx Suspension: the JPEG cleaned to its three inks (red C and slash, blue W, black ORX and SUSPENSION)
    a = logo("cycleworx_suspension_logo.jpg")[..., :3]
    cov = smoothstep(0.12, 0.82, 1 - a.min(2))
    mix = (a - (1 - cov[..., None])) / np.maximum(cov[..., None], 1e-3)        # the ink under the white
    redm = (mix[..., 0] > 0.5) & (mix[..., 2] < 0.5)
    blum = (mix[..., 2] > 0.5) & (mix[..., 0] < 0.5)
    col = np.where(redm[..., None], [254 / 255, 0, 2 / 255], np.where(blum[..., None], [0, 0, 254 / 255], [0.02] * 3))
    ys, xs = np.nonzero(cov > 0.5)
    sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    arts["cworx"] = np.dstack([col[sl] * cov[sl][..., None], cov[sl]]).astype(np.float32)
    out = {}
    for k, a in arts.items():
        x, z, w = FRONT[k]
        if k in ("usn", "cworx"):                       # contour on the jersey's black
            px = a.shape[1] / (w - 2 * CONTOUR)
            a = contoured(a, CONTOUR * px, (255, 255, 255))
        out[k] = Art(a, w)
    return out


class BackUnroll:
    """The back as it is printed, flat: s = arc length across the back's horizontal sections from the spine, t = arc
    length up its vertical sections, on the jersey's back-facing surface y(x, z). Sublimation prints the flat panel,
    so a graphic laid out in (s, t) wraps the curved back (and runs on over the raglan seams) as the real print."""

    def __init__(self, V, N):
        from scipy import ndimage
        from scipy.integrate import cumulative_trapezoid
        from scipy.interpolate import RegularGridInterpolator, griddata
        sel = (N[:, 1] > 0.05) & (np.abs(V[:, 0]) < 0.24) & (V[:, 2] > 1.05) & (V[:, 1] > Y_SIDE + 0.02)
        xs, zs = np.arange(-0.24, 0.2401, 0.002), np.arange(1.06, 1.6201, 0.002)
        X, Z = np.meshgrid(xs, zs, indexing="ij")
        # the outer back only: cloth round the front of the neck also faces back at the same (x, z), and the cut
        # seams carry duplicate vertices (Delaunay slivers): one point per 3 mm cell, the one furthest back
        P = V[sel]
        key = np.round(P[:, [0, 2]] / 0.003).astype(int)
        o = np.lexsort((-P[:, 1], key[:, 1], key[:, 0]))
        _, first = np.unique(key[o], axis=0, return_index=True)
        pts, ys = P[o[first]][:, [0, 2]], P[o[first]][:, 1]
        Y = griddata(pts, ys, (X, Z), method="linear")
        Y = np.where(np.isnan(Y), griddata(pts, ys, (X, Z), method="nearest"), Y)
        Y = ndimage.median_filter(Y, size=3)
        gx = np.sqrt(1 + np.clip(np.gradient(Y, xs, axis=0), -4, 4) ** 2)
        gz = np.sqrt(1 + np.clip(np.gradient(Y, zs, axis=1), -4, 4) ** 2)
        S = cumulative_trapezoid(gx, xs, axis=0, initial=0)
        S -= S[np.argmin(np.abs(xs))][None]
        T = cumulative_trapezoid(gz, zs, axis=1, initial=0)
        T -= T[:, np.argmin(np.abs(zs - 1.45))][:, None]    # from shoulder-blade height: from the hem, the armpits'
                                                             # steep cloth offset the columns at the sides
        self.s = RegularGridInterpolator((xs, zs), S, bounds_error=False, fill_value=np.nan)
        self.t = RegularGridInterpolator((xs, zs), T, bounds_error=False, fill_value=np.nan)
        self.y = RegularGridInterpolator((xs, zs), Y, bounds_error=False, fill_value=np.nan)

    def __call__(self, P):
        q = P[:, [0, 2]]
        return self.s(q), self.t(q)


class Print:
    """One graphic placed on the jersey. back: laid out on the unrolled back (reader's right = his right); front: on
    the tangent plane at its centre (small patches: under 1 mm off over 5 cm of chest)."""

    def __init__(self, art, kind, P0, texel, unroll=None, N0=None):
        self.art, self.kind, self.P0, self.texel, self.unroll = art, kind, np.asarray(P0, float), texel, unroll
        if kind == "back":
            s0, t0 = unroll(self.P0[None])
            self.s0, self.t0 = float(s0[0]), float(t0[0])
        else:
            self.N0 = N0 / np.linalg.norm(N0)
            up = np.array([0, 0, 1.0]) - self.N0[2] * self.N0
            self.U = up / np.linalg.norm(up)
            self.R = np.cross(-self.N0, self.U)          # front: +x, his left, is the reader's right

    def st(self, P, Nn):
        if self.kind == "back":
            s, t = self.unroll(P)
            s, t = -(s - self.s0), t - self.t0          # seen from behind his right (-x) is the reader's right
            ok = (Nn[:, 1] > 0.05) & np.isfinite(s) & np.isfinite(t)
            return np.nan_to_num(s), np.nan_to_num(t), ok
        d = P - self.P0
        return d @ self.R, d @ self.U, (Nn @ self.N0) > 0.4

    def inside(self, s, t, margin=0.0):
        return (np.abs(s) <= self.art.w / 2 + margin) & (np.abs(t) <= self.art.h / 2 + margin)


def damien_prints(V, N):
    """His number, name and sponsors as Print objects on this jersey (rest pose)."""
    un = BackUnroll(V, N)
    num = number_art()
    # the number's top lies NUMBER_TOP of its height below the back collar's centre, measured along the back
    collar = np.array([0.0, float(un.y([[0.0, NECK_BACK]])[0]), NECK_BACK])
    t_c = float(un.t([[0.0, NECK_BACK]])[0])
    zs = np.arange(1.2, NECK_BACK, 0.0005)
    tz = un.t(np.c_[np.zeros_like(zs), zs])
    z_of_t = lambda t: float(np.interp(t, tz, zs))
    zc = z_of_t(t_c - (NUMBER_TOP + 0.5) * num.h)
    prints = [Print(num, "back", [0.0, float(un.y([[0.0, zc]])[0]), zc], PRINT_TEXEL["number"], un)]
    name = name_art(num)
    # the name's centre: along the back from the number's centre (s to his left is negative for the reader)
    s_c = (NAME_LEFT + NAME_RIGHT) / 2 * num.w
    t_n = t_c - NUMBER_TOP * num.h + (NAME_GAP + NAME_H / 2) * num.h
    xs = np.arange(-0.2, 0.2, 0.0005)
    zn = z_of_t(t_n)
    sx = un.s(np.c_[xs, np.full_like(xs, zn)])
    xn = float(np.interp(-s_c, sx, xs))                  # reader's s = -(his s): a negative s_c lies at +x (his left)
    prints.append(Print(name, "back", [xn, float(un.y([[xn, zn]])[0]), zn], PRINT_TEXEL["name"], un))
    front = (N[:, 1] < -0.05) & (V[:, 1] < 0)
    tree = cKDTree(V[front][:, [0, 2]])
    for k, art in front_arts().items():
        x, z, _ = FRONT[k]
        d, i = tree.query([x, z], k=6)
        w = 1 / np.maximum(d, 1e-4)
        y = float((V[front][i, 1] * w).sum() / w.sum())
        n0 = (N[front][i] * w[:, None]).sum(0)
        prints.append(Print(art, "front", [x, y, z], PRINT_TEXEL["front"], N0=n0))
    prints[0].name, prints[1].name = "number", "name"
    for p, k in zip(prints[2:], FRONT):
        p.name = k
    return prints


LEATT_BACK_LOGO = (478, 310, 648, 388)   # px in Leatt's back on-model photo: the LEATT on the upper left back, where
                                         # his name is printed instead (PHOTO 06: no Leatt logo beside the name)


def erase_back_logo(photo):
    """Fill Leatt's back LEATT (white letters) from the print round it (normalised Gaussian convolution)."""
    from scipy import ndimage
    u0, v0, u1, v1 = LEATT_BACK_LOGO
    a = photo.a
    m = np.zeros(a.shape[:2], bool)
    m[v0:v1, u0:u1] = a[v0:v1, u0:u1].min(2) > 0.6
    m = ndimage.binary_dilation(m, iterations=4)
    keep = (~m).astype(float)
    num = np.stack([ndimage.gaussian_filter(a[..., k] * keep, 10) for k in range(3)], 2)
    den = ndimage.gaussian_filter(keep, 10)[..., None]
    a[m] = (num / np.maximum(den, 1e-6))[m]


def lay_prints(img, pos, nrm, mask, prints, texel=None):
    """Print the graphics over img (rest-pose texel positions pos, normals nrm) where mask: each texel takes the art
    at its (s, t), box-filtered to the texel size."""
    P, Nn = pos[mask], nrm[mask]
    C = img[mask]
    for pr in prints:
        s, t, ok = pr.st(P, Nn)
        tx = texel or pr.texel
        ok &= pr.inside(s, t, tx)
        if not ok.any():
            continue
        a = pr.art.sample(s[ok], t[ok], tx)
        C[ok] = C[ok] * (1 - a[:, 3:]) + a[:, :3]
    img[mask] = C
    return img


def print_overlay(V, N, Q, chart, UV, scale, prints, margin=0.004):
    """The print overlay: the jersey faces under Damien's additions, copied PRINT_LIFT out along the normals, with
    UVs that are the jersey's own scaled and moved per island (never rotated: the tangent frames, and so the normal
    map, agree) into a ATLAS_RES atlas at PRINT_TEXEL. Returns the faces, per-corner atlas UVs, island per face, and
    the islands (chart, jersey-UV origin, scale k = atlas pixels per jersey-UV unit, atlas origin)."""
    from scipy.sparse.csgraph import connected_components
    c = V[Q]
    texel = np.full(len(Q), np.inf)
    for pr in prints:
        s, t, ok = pr.st(c.reshape(-1, 3), N[Q].reshape(-1, 3))
        hit = (ok & pr.inside(s, t, margin)).reshape(-1, 4).any(1)
        texel = np.where(hit, np.minimum(texel, pr.texel), texel)
    F = np.nonzero(np.isfinite(texel))[0]
    # islands: faces of one chart joined by shared vertices
    inc = sparse.coo_matrix((np.ones(4 * len(F)), (np.repeat(np.arange(len(F)), 4), Q[F].ravel())),
                            (len(F), len(V))).tocsr()
    adj = (inc @ inc.T).tocoo()
    same = chart[F][adj.row] == chart[F][adj.col]
    g = sparse.coo_matrix((np.ones(same.sum()), (adj.row[same], adj.col[same])), (len(F), len(F)))
    n_isl, lab = connected_components(g, directed=False)
    isl = []
    for i in range(n_isl):
        f = F[lab == i]
        uv = UV[f].reshape(-1, 2)
        lo, hi = uv.min(0), uv.max(0)
        k = 1.0 / (scale * texel[f].min())               # atlas px per jersey-UV unit (scale: UV units per metre)
        isl.append([lo, hi, k, f])
    # shelf packing into the atlas (shrink every island together until they fit)
    pad, shrink = 6, 1.0
    while True:
        order = sorted(range(n_isl), key=lambda i: -(isl[i][1][1] - isl[i][0][1]) * isl[i][2])
        x = y = rowh = 0
        org, ok = {}, True
        for i in order:
            lo, hi, k, _ = isl[i]
            w, h = (hi - lo) * k * shrink + 2 * pad
            if x + w > ATLAS_RES:
                x, y, rowh = 0, y + rowh, 0
            if y + h > ATLAS_RES or w > ATLAS_RES:
                ok = False
                break
            org[i] = (x + pad, y + pad)
            x, rowh = x + w, max(rowh, h)
        if ok:
            break
        shrink *= 0.93
    fis = np.zeros(len(Q), int) - 1
    out_uv = np.zeros((len(F), 4, 2))
    islands = []
    for i in range(n_isl):
        lo, hi, k, f = isl[i]
        k *= shrink
        islands.append((lo, k, np.array(org[i], float)))
        fis[f] = i
    for j, f in enumerate(F):
        lo, k, o = islands[fis[f]]
        out_uv[j] = ((UV[f] - lo) * k + o) / ATLAS_RES
    return F, out_uv, fis[F], islands, shrink


def bilinear(img, u, v):
    """Sample an image stored with row 0 at v = 0 (as painted, before the flip on saving) at UVs."""
    R = img.shape[0]
    x, y = np.clip(u * R - 0.5, 0, R - 1.001), np.clip(v * R - 0.5, 0, R - 1.001)
    i, j = y.astype(int), x.astype(int)
    fy, fx = (y - i)[:, None], (x - j)[:, None]
    I = img.reshape(R, R, -1)
    out = (I[i, j] * (1 - fx) * (1 - fy) + I[i, j + 1] * fx * (1 - fy) + I[i + 1, j] * (1 - fx) * fy
           + I[i + 1, j + 1] * fx * fy)
    return out.reshape((len(u),) + img.shape[2:])


def paint_print_atlas(V, N, Q, F, auv, fis, islands, scale, prints, base, dark, nm, out_dir):
    """The overlay's atlas: per texel the jersey's own print and normal map sampled at the same cloth point (so the
    overlay matches the cloth round it), then Damien's graphics at the atlas's resolution."""
    pos, nrm, isl = raster(auv, V, N, Q[F], fis, res=ATLAS_RES)
    m = isl >= 0
    col = np.zeros(pos.shape)
    nrmm = np.tile(np.array([0, 0, 1.0]), pos.shape[:2] + (1,))
    iy, ix = np.nonzero(m)
    I = isl[m]
    lo = np.array([islands[i][0] for i in range(len(islands))])[I]
    k = np.array([islands[i][1] for i in range(len(islands))])[I]
    o = np.array([islands[i][2] for i in range(len(islands))])[I]
    juv = lo + (np.c_[ix + 0.5, iy + 0.5] - o) / k[:, None]
    col[m] = bilinear(base, juv[:, 0], juv[:, 1])
    dk = bilinear(dark[..., None], juv[:, 0], juv[:, 1])
    n = bilinear(nm, juv[:, 0], juv[:, 1])
    nrmm[m] = n / np.linalg.norm(n, axis=1, keepdims=True)
    for i in range(len(islands)):
        lay_prints(col, pos, nrm, isl == i, prints, texel=1.0 / (scale * islands[i][1]))
    col[m] *= dk
    save_png(col, os.path.join(out_dir, "jersey_print_color.png"), m)
    save_png((nrmm + 1) / 2, os.path.join(out_dir, "jersey_print_normal.png"), m)


# ================================================================ graphics: relief (normal map)
def seam_points(V, Q, chart, pairs, step=0.002):
    """Points every 2 mm along the edges where faces of the given chart pairs meet (real seams)."""
    D = np.stack([Q, np.roll(Q, -1, 1)], 2).reshape(-1, 2)
    fc = np.repeat(chart, 4)
    key = {}
    for e, c in zip(map(tuple, np.sort(D, 1)), fc):
        key.setdefault(e, set()).add(int(c))
    pts = []
    for (a, b), cs in key.items():
        if len(cs) == 2 and tuple(sorted(cs)) in pairs:
            n = max(1, int(np.linalg.norm(V[a] - V[b]) / step))
            t = np.linspace(0, 1, n + 1)[:, None]
            pts.append(V[a] * (1 - t) + V[b] * t)
    return np.concatenate(pts) if pts else np.zeros((0, 3))


def seam_height(pos, mask, pts, width=0.004, depth=0.0006, stitch=0.003):
    """A stitched seam: a groove with a row of stitch dents either side."""
    h = np.zeros(pos.shape[:2])
    if not len(pts):
        return h
    d, i = cKDTree(pts).query(pos[mask])
    g = -depth * np.exp(-0.5 * (d / (width / 2)) ** 2)
    # stitches: dents every 3 mm along the seam, 3 mm off it
    along = (pts[i] @ np.array([0.37, 0.53, 0.76])) / stitch
    st = (np.abs(d - 0.003) < 0.0006) & ((along % 1) < 0.55)
    g -= 0.00025 * st
    h[mask] = g
    return h


def perforations(pos, mask, centres, r=0.0009, depth=0.0008):
    """Laser-cut holes: dents of radius r at the given 3D centres. Returns height and a darkening factor."""
    h = np.zeros(pos.shape[:2])
    dark = np.ones(pos.shape[:2])
    if not len(centres):
        return h, dark
    d, _ = cKDTree(centres).query(pos[mask])
    inside = smoothstep(r * 1.3, r * 0.7, d)
    h[mask] = -depth * inside
    dark[mask] = 1 - 0.75 * inside
    return h, dark


def hole_field(P, N, sel, pitch, count, rng=None):
    """count hole centres on the cloth points P (rest pose) inside a selection, on a staggered grid of pitch."""
    Q = P[sel]
    if not len(Q):
        return np.zeros((0, 3))
    key = np.floor(Q[:, [0, 2]] / pitch).astype(int)
    key[:, 0] += (key[:, 1] % 2)
    _, first = np.unique(key, axis=0, return_index=True)
    C = Q[first]
    if len(C) > count:
        C = C[np.linspace(0, len(C) - 1, count).astype(int)]
    return C


def normal_map(height, scale_m_per_px, mask):
    """Tangent-space normal map (OpenGL convention: green = +v) from a height field in metres."""
    from scipy import ndimage
    h = ndimage.gaussian_filter(height, 0.6)
    gy, gx = np.gradient(h, scale_m_per_px)
    n = np.stack([-gx, -gy, np.ones_like(h)], 2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    n[~mask] = (0, 0, 1)
    return n


def folds(pos, mask, specs):
    """Wrinkles where the riding pose bends the cloth: each spec (centre, axis along the fold lines, across
    direction, radius, wavelength, amplitude): ridges across `across`, fading out over `radius`."""
    h = np.zeros(pos.shape[:2])
    P = pos[mask]
    acc = np.zeros(len(P))
    for c, along, across, rad, lam, amp in specs:
        q = P - np.asarray(c)
        r = np.linalg.norm(q, axis=1)
        w = np.exp(-0.5 * (r / rad) ** 2)
        phase = (q @ np.asarray(across)) / lam + 0.15 * np.sin((q @ np.asarray(along)) / (lam * 3))
        acc += amp * w * (np.abs(np.sin(np.pi * phase)) ** 3 - 0.3)
    h[mask] = acc
    return h


def save_png(img, path, mask=None):
    from PIL import Image
    a = np.clip(img, 0, 1)
    if mask is not None:
        a = dilate(a, mask)
    Image.fromarray((np.flipud(a) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def paint_jersey(body, V, N, Q, chart, UV, scale, out_dir, prints=()):
    """The Tiger Pink print on the jersey's charts: Leatt's on-model photos projected (front panel from the front
    view, back panel from the back view, each sleeve half from its view, blended over the sleeve's top line),
    then Damien's additions (`prints`); the relief: raglan, side and underarm seams, 238 laser-cut holes, riding
    folds. Returns the hole count and the print-free colour, the holes' darkening and the normal map (for the print
    overlay)."""
    pos, nrm, chm = raster(UV, V, N, Q, chart)
    mask = chm >= 0
    img = np.zeros(pos.shape)
    pf = Photo(os.path.join("jersey", "jersey55_tigerpink_front-on-model_nz-distributor_LE5026000201-2_1600.jpg"),
               exclude=[(560, 0, 1060, 345), (160, 1290, 470, 1600), (1130, 1290, 1440, 1600)])
    pb = Photo(os.path.join("jersey", "jersey55_tigerpink_back-on-model_nz-distributor_LE5026000201-3_1600.jpg"),
               exclude=[(600, 0, 1000, 266), (900, 60, 1120, 330), (120, 1330, 420, 1600), (1180, 1330, 1460, 1600)])
    if prints:
        erase_back_logo(pb)                                  # his name is printed there instead (Damien's additions)
    for c, view in ((0, "front"), (1, "back")):
        m = chm == c
        Pm = pos[m].copy()
        Pm[:, 2] -= np.clip(0.02 - neck_cut(Pm), 0, None)
        u, v = jersey_photo_uv(body, Pm, view)
        img[m] = (pf if view == "front" else pb).sample(u, v)
    for s, base in (("L", 2), ("R", 4)):
        m = (chm == base) | (chm == base + 1)
        P = pos[m]
        S, E, W, f, o = arm_frame(body, s)
        ax = W - S
        ax /= np.linalg.norm(ax)
        rr = P - S - ((P - S) @ ax)[:, None] * ax
        wf = smoothstep(-0.35, 0.35, (rr @ f) / np.maximum(np.linalg.norm(rr, axis=1), 1e-6))
        uf, vf, t = sleeve_photo_uv(body, P, s, "front")
        ub, vb, _ = sleeve_photo_uv(body, P, s, "back")
        cf = pf.sample(uf, vf)
        cb = pb.sample(ub, vb)
        ws = smoothstep(0.02, 0.14, t)[:, None]               # the raglan part over the shoulder: the trunk's views
        cf = cf * ws + pf.sample(*jersey_photo_uv(body, P, "front")) * (1 - ws)
        cb = cb * ws + pb.sample(*jersey_photo_uv(body, P, "back")) * (1 - ws)
        img[m] = cf * wf[:, None] + cb * (1 - wf[:, None])
    # Damien's additions (also printed sharper on the print overlay, which takes `base` round them)
    base = img.copy()
    img = lay_prints(img, pos, nrm, mask, prints, texel=1.0 / (scale * TEX_RES))
    # relief
    h = np.zeros(pos.shape[:2])
    seams = seam_points(V, Q, chart, {(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (0, 4), (0, 5), (1, 4), (1, 5)})
    under = []
    for s, k in (("L", 2), ("R", 4)):
        S, E, W, f, o = arm_frame(body, s)
        sp = seam_points(V, Q, chart, {(k, k + 1)})
        if len(sp):
            under.append(sp[((sp - S) @ o) < 0])                    # the underarm line only (not the top line)
    h += seam_height(pos, mask, np.concatenate([seams] + under))
    # laser-cut perforations (Leatt: 238): upper sleeves at the front, side panels, two rows across the lower back
    P, Nn = pos[mask], nrm[mask]
    holes = []
    for s, sg in (("L", 1), ("R", -1)):
        S, E, W, f, o = arm_frame(body, s)
        t = ((P - S) @ (E - S)) / np.linalg.norm(E - S) ** 2
        sel = (P[:, 0] * sg > 0.15) & (t > 0.05) & (t < 0.75) & (((P - S) @ f) > 0.01)
        holes.append(hole_field(P, Nn, sel, 0.011, 50))
        sel = (P[:, 0] * sg > 0.12) & (np.abs(P[:, 1] - Y_SIDE) < 0.03) & (P[:, 2] > 1.12) & (P[:, 2] < 1.33)
        holes.append(hole_field(P, Nn, sel, 0.012, 40))
    for zr in (1.155, 1.215):
        sel = (Nn[:, 1] > 0.6) & (np.abs(P[:, 2] - zr) < 0.004) & (np.abs(P[:, 0]) < 0.14)
        holes.append(hole_field(P, Nn, sel, 0.0095, 29))
    C = np.concatenate(holes)
    hp, dark = perforations(pos, mask, C)
    h += hp
    img *= dark[..., None]
    # folds where riding bends the jersey: inner elbows, the belly over the bent hips, the shoulder blades reaching
    spec = [((0, -0.135, 1.13), (1, 0, 0), (0, 0, 1), 0.07, 0.022, 0.0009)]
    for s, sg in (("L", 1), ("R", -1)):
        S, E, W, f, o = arm_frame(body, s)
        d = (W - E) / np.linalg.norm(W - E)
        spec.append((E + f * 0.03, np.cross(d, f), d, 0.045, 0.016, 0.0010))
        spec.append(((0.11 * sg, 0.09, 1.40), (0, 0, 1), (sg * 0.7, 0, -0.7), 0.06, 0.03, 0.0006))
    h += folds(pos, mask, spec)
    nm = normal_map(h, 1.0 / (scale * TEX_RES), mask)
    save_png(img, os.path.join(out_dir, "jersey_color.png"), mask)
    save_png((nm + 1) / 2, os.path.join(out_dir, "jersey_normal.png"), mask)
    return len(C), dict(base=base, dark=dark, nm=nm)



def paint_pants(body, pants, V, N, Q, chart, UV, scale, out_dir):
    """The pant's print: Leatt US's on-model front and back photos projected leg by leg, each photo row's pant
    silhouette laid onto his pant's silhouette at the matching height (waist top, crotch, boot top rows). Relief:
    centre, in- and outseams, the I.K.S panels' and the rear yoke's seams, the waistband's stitching, 250
    laser-cut holes, the creases riding puts behind the knees and across the hips."""
    pos, nrm, chm = raster(UV, V, N, Q, chart)
    mask = chm >= 0
    img = np.zeros(pos.shape)
    pf = Photo(os.path.join("pants", "pant55iks_tigerpink_front-on-model_leatt-us_5026000320_1920.png"),
               exclude=[(470, 140, 1010, 330)])                       # the Waistlock (modelled in 3D)
    pb = Photo(os.path.join("pants", "pant55iks_tigerpink_back-on-model_leatt-us_5026000320_1920.png"))
    crotch = V[np.abs(V[:, 0]) < 0.01][:, 2].min()
    sil = pant_silhouette(V, crotch)
    for cs, view, ph in (((0, 2), "front", pf), ((1, 3), "back", pb)):
        m = np.isin(chm, cs)
        u, v = pant_photo_uv(pants, pos[m], view, ph.alpha, sil)
        img[m] = ph.sample(u, v)
    # the big LEATT on the outer left thigh: the photos see it edge-on, so it is printed flat from a side view
    # (PHOTO: Leatt front on-model and back flat, his 07): reading up from the knee, letter tops to the front
    word, _ = logo_stamps()
    K = body.j("lowerleg01.L")
    zc = K[2] + THIGH_LOGO[0]
    side = Canvas((0.4, THIGH_LOGO[1], zc), (0, 1, 0), (0, 0, 1), 0.2, 0.40)
    side.stamp(word, 0.0, 0.0, THIGH_LOGO[2], rot=90)
    zone = mask & (pos[..., 0] > 0.10) & (nrm[..., 0] > 0.35) & (np.abs(pos[..., 2] - zc) < THIGH_LOGO[2] / 2 + 0.04)
    c = img[zone]
    whiteish = smoothstep(0.45, 0.7, c.min(1)) * smoothstep(0.25, 0.1, c.max(1) - c.min(1))
    img[zone] = c * (1 - whiteish[:, None]) + np.array([0.11, 0.105, 0.13]) * whiteish[:, None]
    img = side.apply(img, pos, zone)
    iks = mask.copy()
    iks[mask] = iks_field(pants, body, pos[mask]) > 0
    img[iks] = (0.085, 0.085, 0.09)                                  # the black I.K.S panels
    # relief
    h = np.zeros(pos.shape[:2])
    seams = [seam_points(V, Q, chart, {(0, 2), (1, 3), (0, 1), (2, 3), (0, 3), (1, 2)})]
    P, Nn = pos[mask], nrm[mask]
    _, wtop = pant_region(body)
    wt = wtop(P)
    yz = WAIST_BACK - 0.125 + 0.30 * np.abs(P[:, 0])                  # the rear yoke's V (PHOTO back views)
    seams.append(P[(Nn[:, 1] > 0.4) & (np.abs(P[:, 2] - yz) < 0.0015) & (np.abs(P[:, 0]) < 0.17)])
    seams.append(P[np.abs(P[:, 2] - (wt - 0.040)) < 0.0012])          # the waistband's lower edge
    fi = iks_field(pants, body, P)
    seams.append(P[(np.abs(fi) < 0.0015)])
    h += seam_height(pos, mask, np.concatenate(seams))
    holes = []
    for s, sg in (("L", 1), ("R", -1)):
        K = body.j(f"lowerleg01.{s}")
        sel = (P[:, 0] * sg > 0.05) & (Nn[:, 1] < -0.6) & (P[:, 2] > K[2] + 0.20) & (P[:, 2] < K[2] + 0.33)
        holes.append(hole_field(P, Nn, sel, 0.012, 60))
        sel = (P[:, 0] * sg > 0.03) & (Nn[:, 1] > 0.5) & (np.abs(P[:, 2] - (yz + 0.02)) < 0.012) & (P[:, 0] * sg < 0.15)
        holes.append(hole_field(P, Nn, sel, 0.011, 25))
        sel = (P[:, 0] * sg > 0.05) & (Nn[:, 1] > 0.6) & (np.abs(P[:, 2] - (K[2] + 0.04)) < 0.04)
        holes.append(hole_field(P, Nn, sel, 0.011, 40))
    C = np.concatenate(holes)
    hp, dark = perforations(pos, mask, C)
    h += hp
    img *= dark[..., None]
    spec = []
    for s, sg in (("L", 1), ("R", -1)):
        K = body.j(f"lowerleg01.{s}")
        spec.append((K + np.array([0, 0.06, 0]), (1, 0, 0), (0, 0, 1), 0.05, 0.018, 0.0012))   # behind the knee
        spec.append(((0.10 * sg, -0.11, 0.90), (1, 0, 0), (0, 0.3, 1), 0.06, 0.025, 0.0008))  # across the hip
    h += folds(pos, mask, spec)
    nm = normal_map(h, 1.0 / (scale * TEX_RES), mask)
    save_png(img, os.path.join(out_dir, "pants_color.png"), mask)
    save_png((nm + 1) / 2, os.path.join(out_dir, "pants_normal.png"), mask)
    return len(C)


# ================================================================ posing (for the clearance tests)
def rot(axis, deg):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    t = np.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K


def bone_matrices(body, pose):
    """pose: {bone: (axis, degrees)} turns about the bone's head in the rest frame, children follow. Returns a
    4x4 per bone (linear blend skinning, as Blender's Armature modifier without volume preservation)."""
    names = body.names
    parents = [str(p) for p in body.d["parents"]]
    M = {}

    def get(i):
        n = names[i]
        if n in M:
            return M[n]
        p = parents[i]
        Mp = get(names.index(p)) if p else np.eye(4)
        L = np.eye(4)
        if n in pose:
            R = rot(*pose[n])
            h = body.heads[i]
            L[:3, :3] = R
            L[:3, 3] = h - R @ h
        M[n] = Mp @ L
        return M[n]
    return np.array([get(i) for i in range(len(names))])


def lbs(V, W, Ms):
    """Pose vertices V with weights W (n x bones, dense or sparse) by bone matrices Ms."""
    W = W.toarray() if sparse.issparse(W) else W
    Vh = np.c_[V, np.ones(len(V))]
    out = np.zeros((len(V), 3))
    for b in np.nonzero(W.any(0))[0]:
        out += W[:, b:b + 1] * (Vh @ Ms[b].T)[:, :3]
    return out


def riding_pose(body, seated=False):
    """The test pose of the brief: knees and ankles bent, head pitched down 20 deg; arms reaching forward with the
    elbows bent. Seated: hips and knees at 90 deg (on the seat). Axes in the rest frame (his left is +x)."""
    X = (1, 0, 0)
    hip, knee = (-90, 90) if seated else (-60, 60)
    pose = {"neck01": (X, 10), "head": (X, 10)}
    for s, sg in (("L", 1), ("R", -1)):
        pose[f"upperleg01.{s}"] = (X, hip)
        pose[f"lowerleg01.{s}"] = (X, knee)
        pose[f"foot.{s}"] = (X, -30 if not seated else 0)
        S, E, Wr = body.j(f"upperarm01.{s}"), body.j(f"lowerarm01.{s}"), body.j(f"wrist.{s}")
        pose[f"upperarm01.{s}"] = (X, -45)                                   # reach forward
        ax = np.cross(E - S, Wr - E)
        pose[f"lowerarm01.{s}"] = (ax, 60)                                   # elbow bend in the arm's plane
    return pose


def to_part(name, V, faces, mat_index, W, smooth=True, UV=None):
    faces = [tuple(f) for f in faces]
    out = {name + "__V": np.asarray(V, np.float32),
           name + "__F": np.array([i for f in faces for i in f], np.int32),
           name + "__FS": np.array([len(f) for f in faces], np.int32),
           name + "__M": np.asarray(mat_index, np.int32), name + "__smooth": np.int32(1 if smooth else 0)}
    if UV is not None:
        out[name + "__UV"] = np.asarray(UV, np.float32).reshape(-1, 2)
    out[name + "__wv"], out[name + "__wb"], out[name + "__ww"] = weights_triplets(W)
    return out


# Materials (ledger "Materials"): sublimated polyester knit with a soft sheen; the breathable mesh side panels
# rougher and duller; the I.K.S panels black leather and ripstop (a fine relief); the Waistlock's Hypalon-rubber
# strap, its textile tab, the moulded plastic buckle.
MATERIALS = {
    "jersey_print": {"image": "jersey_color.png", "normal": "jersey_normal.png", "rough": 0.58, "sheen": 0.18},
    "jersey_mesh": {"image": "jersey_color.png", "normal": "jersey_normal.png", "rough": 0.74, "sheen": 0.1},
    # the print overlay over Damien's additions: the same cloth, its own sharper atlas
    "jersey_print_hd": {"image": "jersey_print_color.png", "normal": "jersey_print_normal.png", "rough": 0.58,
                        "sheen": 0.18},
    "jersey_print_hd_mesh": {"image": "jersey_print_color.png", "normal": "jersey_print_normal.png", "rough": 0.74,
                             "sheen": 0.1},
    "pant_print": {"image": "pants_color.png", "normal": "pants_normal.png", "rough": 0.56, "sheen": 0.16},
    "pant_iks": {"rgb": [22, 22, 24], "rough": 0.46, "sheen": 0.12, "coat": 0.05, "bump": 0.22, "bump_scale": 1400.0},
    "strap": {"rgb": [18, 18, 19], "rough": 0.62},
    "strap_tab": {"rgb": [20, 20, 22], "rough": 0.85, "sheen": 0.3},
    "buckle": {"rgb": [16, 16, 17], "rough": 0.32, "coat": 0.15},
}
MESH_PANEL = (0.045, 0.12, 1.35)   # m: half width about the side seam, |x| beyond, top z (PHOTO side-panel close-up)


def jersey_mesh_faces(V, Q):
    c = V[Q].mean(1)
    return (np.abs(c[:, 1] - Y_SIDE) < MESH_PANEL[0]) & (np.abs(c[:, 0]) > MESH_PANEL[1]) & (c[:, 2] < MESH_PANEL[2])


def iks_field(pants, body, P):
    """> 0 inside an I.K.S inner-knee panel, in metres to its seam (PHOTO: Leatt front flat and the inner-knee
    close-up: black leather and ripstop on the inner side, from 20 cm above the knee joint to 13 cm below it, over
    the inner 150 deg)."""
    out = np.full(len(P), -1.0)
    for s, med in (("L", -np.pi / 2), ("R", np.pi / 2)):
        env = pants["lenv"][s]
        h, r, th, _ = env.local(P)
        hk = np.dot(body.j(f"lowerleg01.{s}") - env.o, env.a)
        dth = np.abs((th - med + np.pi) % (2 * np.pi) - np.pi)
        f = np.minimum((np.radians(IKS_HALF_ANGLE) - dth) * r, np.minimum(h - (hk - IKS_BELOW), hk + IKS_ABOVE - h))
        side = P[:, 0] * (1 if s == "L" else -1) > 0.02
        out = np.where(side, np.maximum(out, f), out)
    return out


def knee_panels(pants, body):
    """Snap the vertices next to each panel's seam onto it (so the leather's edge is a clean line, not the faces'
    stair-steps), then the faces inside."""
    V, Q = pants["V"].copy(), pants["Q"]
    fv = iks_field(pants, body, V)
    E, _ = edges_of(Q)
    cross = np.sign(fv[E[:, 0]]) != np.sign(fv[E[:, 1]])
    cand = np.unique(np.where(np.abs(fv[E[cross, 0]]) < np.abs(fv[E[cross, 1]]), E[cross, 0], E[cross, 1]))
    for _ in range(4):
        p = V[cand]
        f0 = iks_field(pants, body, p)
        gr = np.stack([(iks_field(pants, body, p + e) - f0) / 1e-4 for e in np.eye(3) * 1e-4], 1)
        V[cand] = p - (f0 / np.maximum((gr * gr).sum(1), 1e-9))[:, None] * gr
    pants["V"] = V
    return iks_field(pants, body, V[Q].mean(1)) > 0


IKS_HALF_ANGLE, IKS_ABOVE, IKS_BELOW = 75.0, 0.20, 0.13
FLY_X, FLY_W, FLY_LEN, FLY_T = -0.010, 0.036, 0.17, 0.002   # m: YKK fly under a placket (PHOTO front close-up)


def fly_placket(V, N, waist_top):
    """The fly's placket: a strip standing 2 mm proud down the centre front from the waistband."""
    zt = waist_top(V)
    across = 1 - smoothstep(FLY_W / 2 - 0.006, FLY_W / 2, np.abs(V[:, 0] - FLY_X))
    down = smoothstep(zt - FLY_LEN, zt - FLY_LEN + 0.02, V[:, 2])
    m = (V[:, 1] < -0.04) & (N[:, 1] < -0.3)
    return V + (FLY_T * across * down * m)[:, None] * N


def roll_spec_jersey(P):
    t = np.full(len(P), 0.0015)
    w = np.where(P[:, 2] > 1.45, 0.012, np.where(P[:, 2] < 1.05, 0.015, 0.020))    # neck, hem, cuffs
    return t, w


def roll_spec_pants(P):
    top = P[:, 2] > 0.8
    return np.where(top, 0.004, 0.002), np.where(top, 0.040, 0.025)               # waistband, cuffs


def main(body_path, out_path, tex=True):
    body = Body(body_path)
    _, waist_top = pant_region(body)
    pants = build_pants(body)
    jersey = build_jersey(body, pants)
    jersey["V"] = straight_seams_jersey(body, jersey["V"], jersey["Q"])
    pants["V"] = straight_seams_pants(pants, pants["V"], pants["Q"])
    # pants: fly, knee panels, finished edges, weights
    pants["V"] = fly_placket(pants["V"], vnormals(pants["V"], pants["Q"]), waist_top)
    iks = knee_panels(pants, body)
    pV, pQ, ppar = add_rolls(pants["V"], pants["Q"], roll_spec_pants)
    pW0 = skin_weights(body, pants["V"], pants["Q"], smooth=2)         # light: the cloth follows the kneecap
    pW = pW0[ppar]
    mats = list(MATERIALS)
    pM = np.r_[np.where(iks, mats.index("pant_iks"), mats.index("pant_print")),
               np.full(len(pQ) - len(pants["Q"]), mats.index("pant_print"))]
    # jersey: finished edges; the tucked part moves with the pant over it
    W0 = skin_weights(body, jersey["V"], jersey["Q"])
    _, k = cKDTree(pants["V"]).query(jersey["V"])
    s = smoothstep(waist_top(jersey["V"]) + 0.05, waist_top(jersey["V"]), jersey["V"][:, 2])[:, None]
    Wp = pW0[k]
    W0 = W0 * (1 - s) + Wp * s
    jV, jQ, jpar = add_rolls(jersey["V"], jersey["Q"], roll_spec_jersey)
    jW = W0[jpar]
    # UV charts (one per pattern piece) and the print
    jc = jersey_charts(body, jersey["V"], jersey["Q"])
    jUV, jscale = chart_uvs(jersey["V"], jersey["Q"], jc)
    pc = pant_charts(pants, pants["V"], pants["Q"])
    pUV, pscale = chart_uvs(pants["V"], pants["Q"], pc)
    jN = vnormals(jersey["V"], jersey["Q"])
    prints = damien_prints(jersey["V"], jN)                        # his number, name and sponsors
    if tex:
        os.makedirs(TEXDIR, exist_ok=True)
        nj, jinfo = paint_jersey(body, jersey["V"], jN, jersey["Q"], jc, jUV, jscale, TEXDIR, prints)
        npn = paint_pants(body, pants, pants["V"], vnormals(pants["V"], pants["Q"]), pants["Q"], pc, pUV, pscale,
                          TEXDIR)
        print("laser-cut holes: jersey", nj, "pant", npn)
    names = ["jersey", "pants"]
    out = {"mats": np.array(mats), "materials": json.dumps(MATERIALS)}
    jM = np.full(len(jQ), mats.index("jersey_print"))
    jM[:len(jersey["Q"])][jersey_mesh_faces(jersey["V"], jersey["Q"])] = mats.index("jersey_mesh")
    out.update(to_part("jersey", jV, jQ, jM, jW,
                       UV=corner_uvs(jQ, len(jersey["Q"]), jUV, jpar)))
    out.update(to_part("pants", pV, pQ, pM, pW, UV=corner_uvs(pQ, len(pants["Q"]), pUV, ppar)))
    out["tex_scale"] = np.array([jscale, pscale])                   # texture units per metre (jersey, pant)
    # Damien's additions, sharper: the print overlay rides the jersey (its vertices' own weights)
    F, auv, fis, islands, _ = print_overlay(jersey["V"], jN, jersey["Q"], jc, jUV, jscale, prints)
    if tex:
        paint_print_atlas(jersey["V"], jN, jersey["Q"], F, auv, fis, islands, jscale, prints, jinfo["base"],
                          jinfo["dark"], jinfo["nm"], TEXDIR)
    used, inv = np.unique(jersey["Q"][F], return_inverse=True)
    oM = np.where(jersey_mesh_faces(jersey["V"], jersey["Q"])[F], mats.index("jersey_print_hd_mesh"),
                  mats.index("jersey_print_hd"))
    out.update(to_part("jersey_print", jersey["V"][used] + PRINT_LIFT * jN[used], inv.reshape(-1, 4), oM, W0[used],
                       UV=auv))
    names.append("jersey_print")
    out["prints"] = json.dumps({p.name: dict(kind=p.kind, P0=p.P0.round(5).tolist(), w=round(p.art.w, 5),
                                             h=round(p.art.h, 5)) for p in prints})
    # the Waistlock rides the pant's waist (weights of the pant under it)
    ptree = cKDTree(pants["V"])
    for name, item in waistlock(pants["V"], vnormals(pants["V"], pants["Q"]), waist_top).items():
        V, F, ml = item[0], item[1], item[2]
        M = item[3] if len(item) > 3 else [0] * len(F)
        _, k = ptree.query(V)
        out.update(to_part(name, V, F, [mats.index(ml[i]) for i in M], pW0[k], smooth=(name != "pant_strap")))
        names.append(name)
    out["names"] = np.array(names)
    out["hide_body"] = hidden_skin(body, [jersey, pants]).astype(np.int32)
    np.savez_compressed(out_path, **out)
    print("jersey", len(jV), "verts; pants", len(pV), "verts; hidden skin", len(out["hide_body"]))
    return body, jersey, pants


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--no-tex" not in sys.argv)
