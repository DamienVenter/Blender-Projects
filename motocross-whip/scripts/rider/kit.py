"""Damien's kit: Leatt Moto 5.5 UltraWeld jersey and Moto 5.5 I.K.S pant, Tiger Pink, 2026, on his body.

python3 kit.py BODY.npz OUT.npz [--no-tex] [--tex-dir DIR]
    (body.py's output; writes a gear npz for build_rider.py RIDER_GEAR, the textures into textures/rider or DIR)

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

    def __init__(self, name, exclude=(), median=5, inks=None):
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
        self.bad = bad
        self.inks = inks                           # 4 x 3 map onto the reference's inks (ink_map), or None

    def lin(self, u, v):
        """Linear colour on the reference's inks."""
        c = to_lin(self.sample(u, v))
        return c if self.inks is None else c @ self.inks[:3] + self.inks[3]

    def seen(self, u, v):
        """1 where (u, v) is the garment in the photo, 0 where it was filled (background, excluded boxes)."""
        H, W = self.bad.shape
        i = np.clip(np.round(v).astype(int), 0, H - 1)
        j = np.clip(np.round(u).astype(int), 0, W - 1)
        return (~self.bad[i, j]).astype(float)

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
# Leatt US's front flat (1920 px, PHOTO: its alpha's runs per row): the sleeves' centres at y 950 and 1500 (x 496
# and 531 on the image's left, 1380 and 1464 on its right: the form is turned a little), the line through them from
# the shoulder (y 470) to the cuff's end; 216 px across at y 950, 173 at 1300, 143 at 1550. The back three-quarter
# flat (1600 px, PHOTO: its runs per row and the side panel's seam): his left sleeve from behind, centres at y 750,
# 1250 and 1450 (x 433, 366, 331), 194, 128 and 97 px across. Half widths 0.85 of half the sleeve's, as before.
J_ARMS.update({("flat", "R"): ((467, 470), (543, 1640)), ("flat", "L"): ((1307, 470), (1485, 1565)),
               ("b34", "L"): ((489, 330), (327, 1480))})
J_ARM_CX = {"front": 800.0, "back": 800.0, "flat": 940.0, "b34": 800.0}   # px, the photo's body centre
J_ARM_TAB = {"flat": ((0.0, 0.2, 0.41, 0.72, 0.93, 1.0), (95, 95, 92, 74, 61, 58)),
             "b34": ((0.0, 0.2, 0.37, 0.80, 0.97, 1.0), (90, 88, 82, 54, 41, 40))}
J_ARM_HALF = ((0.0, 0.2, 0.6, 1.0), (68, 72, 60, 48))   # px: 0.85 of half the sleeve's width (PHOTO front), so
                                                        # the silhouette's soft edge is never sampled


SIDE_REF = os.path.join("jersey", "jersey55_tigerpink_back-flat-34_nz-distributor_LE5026000201-1_1600.jpg")
# the side panel in Leatt's back three-quarter flat (PHOTO, 1600 px): its top under the arm at y 600, the hem at
# 1450; per row its front seam (beside the sleeve) and back seam (where the black back panel starts)
SIDE_ROWS = ((1.35, 600.0), (HEM_Z, 1450.0))
SIDE_EDGES = ((600.0, 800.0, 1450.0), (545.0, 530.0, 530.0), (615.0, 640.0, 648.0))


def side_panel(pos):
    """The mesh side panels' texels (MESH_PANEL: either side of the side seam, under the arm)."""
    return ((np.abs(pos[..., 1] - Y_SIDE) < MESH_PANEL[0]) & (np.abs(pos[..., 0]) > MESH_PANEL[1])
            & (pos[..., 2] < MESH_PANEL[2]))


def side_photo_uv(P):
    """A side panel point in the back three-quarter flat: rows by height, across from the front seam to the back."""
    (z0, y0), (z1, y1) = SIDE_ROWS
    v = y0 + (P[:, 2] - z0) * (y1 - y0) / (z1 - z0)
    a = np.clip((P[:, 1] - Y_SIDE + MESH_PANEL[0]) / (2 * MESH_PANEL[0]), 0, 1)
    xf = np.interp(v, SIDE_EDGES[0], SIDE_EDGES[1])
    xb = np.interp(v, SIDE_EDGES[0], SIDE_EDGES[2])
    return xf + a * (xb - xf), v


# The side panels' zebra (round 3b): traced with the trunk's charts their lime and teal bands came out as
# fragments and white specks (the cut's 3 cm window on a strip 70 to 118 px wide, and the front chart's near-white
# guard on the grey-teal tops). They are traced on the back three-quarter flat itself, inside the panel's outline
# (SIDE_EDGES, 4 px over), with the sleeves' options (FP_FLAT_SLEEVE) at its pixel (rows: 0.47 m over 850 px),
# and laid over the trunk's print as they are (the panel is its own piece, cut at its seams)
SIDE_TEXEL = (1.35 - HEM_Z) / 850     # m per px down the side panel in the back three-quarter flat (SIDE_ROWS)


def side_panel_art(ps, inks, gain, white):
    """The side panel's zebra traced on the back three-quarter flat (photo space): a sampler (u, v) -> linear
    colour on the front flat's inks, times gain (flat_layers' output, as flat_print's)."""
    from scipy import ndimage
    H, W = ps.bad.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    xf = np.interp(yy, SIDE_EDGES[0], SIDE_EDGES[1])
    xb = np.interp(yy, SIDE_EDGES[0], SIDE_EDGES[2])
    inside = ((yy >= SIDE_EDGES[0][0] - 10) & (yy <= SIDE_EDGES[0][-1] + 10) & (xx >= xf - 4) & (xx <= xb + 4)
              & ~ps.bad)
    ys, xs = np.nonzero(inside)
    y0, x0 = ys.min(), xs.min()
    sl = (slice(y0, ys.max() + 1), slice(x0, xs.max() + 1))
    sel = inside[sl]
    col = np.clip((to_lin(ps.a[sl]) @ inks[:3] + inks[3]) * gain, 0, 1)
    o, _, _ = flat_layers(col, sel.astype(float), sel, SIDE_TEXEL, white, sel, **FP_FLAT_SLEEVE)
    return art_sampler(o, sel, y0, x0)


def art_sampler(o, sel, y0, x0):
    """Bilinear lookup (u, v photo px) into artwork traced on a photo's crop (rows from y0, columns from x0); outside
    its outline `sel` the nearest traced pixel."""
    from scipy import ndimage
    _, (iy, ix) = ndimage.distance_transform_edt(~sel, return_indices=True)
    o = o[iy, ix]

    def sample(u, v):
        return np.stack([ndimage.map_coordinates(o[..., k], [v - y0, u - x0], order=1, mode="nearest")
                         for k in range(3)], -1)
    return sample


# Leatt US's front pant photo (round 3c, fix 2): the Waistlock (strap, buckle and tab, modelled in 3D) and the
# jersey hanging over the waistband's top in the middle (down to its hem's white threads) hide the pant. Rounds 3b
# and main excluded a box round them (470..1010, 140..330) and took each texel there from the nearest traced pixel:
# teal blocks stepping down the waistband beside the buckle (sheet 05); round 3 a grey rectangle. Their outlines
# (photo px, PHOTO) are traced as the rest with the print plain there (the black ground: what the photo does not
# see is not traced), so the stripes the photo sees end cleanly at the outline; beside the buckle the waistband is
# plain black in the photo itself
PF_HIDDEN = (
    [(578, 168), (640, 186), (672, 200), (686, 214), (760, 236), (868, 262), (890, 252), (1008, 256), (1014, 366),
     (992, 370), (893, 342), (862, 322), (642, 288), (562, 274), (552, 240), (556, 190)],             # the Waistlock
    [(650, 100), (668, 200), (700, 214), (760, 232), (840, 248), (900, 251), (1000, 249), (1040, 249), (1115, 242),
     (1145, 239), (1250, 204), (1300, 170), (1340, 128), (1365, 100)])                             # the jersey over it


def polygons_mask(shape, polys, grow=4):
    """Pixels inside any of the polygons (x, y px), grown by `grow` px (their edges' shadows and threads)."""
    from matplotlib.path import Path as MPath
    from scipy import ndimage
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    pts = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1)
    m = np.zeros(H * W, bool)
    for p in polys:
        m |= MPath(p).contains_points(pts)
    return ndimage.binary_dilation(m.reshape(H, W), iterations=grow)


def pant_photo_art(ph, rows, gain, white, hidden=(), fade_rows=None):
    """A pant photo traced in its own pixels (pixel size from its rows: waist top to boot top): samplers (u, v) ->
    the zebra's linear colour on the flat's inks (FP_PANT_PHOTO, without the white elements) and the white
    elements' coverage (traced at FP_PANT's 0.8 mm: the stamps' letters and their 1.2 mm lines; at the zebra's
    2 mm the letters came out blobby and the lines were lost, their light smeared into the black ground). hidden:
    outlines of what covers the pant in the photo (PF_HIDDEN): plain ground there. fade_rows: the shins' airbrushed
    fades (PANT_FADE_ROWS), traced as FP_FADE."""
    from scipy import ndimage
    sel = ~ph.bad
    ys, xs = np.nonzero(sel)
    sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    fade = None
    if fade_rows is not None:
        f0, f1, soft = fade_rows
        yy = np.arange(ys.min(), ys.max() + 1, dtype=float)
        fy = smoothstep(f0 - soft, f0, yy) * (1 - smoothstep(f1, f1 + soft, yy))
        fade = np.repeat(fy[:, None], xs.max() + 1 - xs.min(), 1)
    texel = (rows[0][1] - rows[2][1]) / (rows[2][0] - rows[0][0])
    col = np.clip(to_lin(ph.a[sl]) * gain, 0, 1)
    q = sel[sl].astype(float)
    plain = None
    if len(hidden):
        plain = polygons_mask(ph.bad.shape, hidden)[sl] & sel[sl]
        # the photo's own black there, as seen ground: as unseen texels their ground came from the few boundary
        # texels in reach (the stripes' anti-aliased tips: teal blotches along the outline)
        d = ph.a[sl]
        blk = sel[sl] & ~plain & (d.max(-1) < 0.2) & (d.max(-1) - d.min(-1) < 0.05)
        col[plain] = np.median(col[blk], 0)
    _, _, aw = flat_layers(col, q, sel[sl], texel, white, sel[sl], cover=plain, **FP_PANT)
    near = ndimage.binary_dilation(aw > 0.02, iterations=max(1, int(round(0.0015 / texel))))
    o, _, _ = flat_layers(col, q * ~near, sel[sl], texel, white, sel[sl], whites=False, plain=plain, cover=plain,
                          fade=fade, fade_span=PANT_FADE_SPAN, **dict(FP_PANT_PHOTO, qfloor=0.0))
    return (art_sampler(o, sel[sl], ys.min(), xs.min()),
            art_sampler(np.repeat(aw[..., None], 3, -1), sel[sl], ys.min(), xs.min()))


# the trunk between the arms in Leatt's on-model photos (PHOTO: the gap or the seam between arm and side panel, rows
# under the shoulders): what maps outside is the model's arm, not his side
J_TORSO = {"front": (550.0, 1050.0, 420.0), "back": (490.0, 1070.0, 380.0)}   # x from, x to, from row


def torso_seen(u, v, view):
    x0, x1, y0 = J_TORSO[view]
    return ((u > x0) & (u < x1)) | (v < y0)


def jersey_photo_uv(body, P, view):
    if view == "front":
        return JF_C + JF_KX * P[:, 0], JF_V0 + JF_KZ * (NECK_FRONT - P[:, 2])
    return JB_C - JB_KX * P[:, 0], JB_V0 + JB_KZ * (NECK_BACK - P[:, 2])


def arm_facing(body, s, P):
    """Round each segment of the arm (upper arm, forearm): the cosine of a point's angle from the segment's front,
    and that front per point. (One axis from shoulder to cuff, as rounds 1 and 2 had, runs in front of the upper
    arm when the forearm reaches forward: its front half was painted from the back photo.)"""
    S, E, W, f, o = arm_frame(body, s)
    cos, fr = np.zeros(len(P)), np.zeros((len(P), 3))
    upper = ((P - S) @ (E - S)) < np.dot(E - S, E - S)
    for A, B, sel in ((S, E, upper), (E, W, ~upper)):
        d = (B - A) / np.linalg.norm(B - A)
        fs = np.array([0, -1.0, 0]) - d * (-d[1])
        fs /= np.linalg.norm(fs)
        r = (P[sel] - A) - np.outer((P[sel] - A) @ d, d)
        cos[sel] = (r @ fs) / np.maximum(np.linalg.norm(r, axis=1), 1e-6)
        fr[sel] = fs
    return cos, fr


def sleeve_photo_uv(body, P, s, view, photo_s=None, phase=None):
    """A sleeve point in one of the photos: along the arm (shoulder point to cuff, upper arm then forearm) and
    across it (outward from the arm's line, the photo's arm seen square on). photo_s: the photo's other sleeve
    instead (outward to outward: the point's mirror image across his middle). phase: knots (the sleeve's t, the
    photo's t) where the photo's print runs at another place along the arm (SLEEVE_PHASE). Returns the photo's
    pixel and the sleeve's own t."""
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
    tp = t if phase is None else np.interp(t, phase[0], phase[1])
    tab = J_ARM_TAB.get(view, J_ARM_HALF)
    half = np.interp(tp, tab[0], tab[1])
    (u0, v0), (u1, v1) = J_ARMS[(view, photo_s or s)]
    A, B = np.array([u0, v0], float), np.array([u1, v1], float)
    dd = (B - A) / np.linalg.norm(B - A)
    out_px = np.array([dd[1], -dd[0]])                              # across the photo's arm, away from the body
    if np.dot(out_px, (A + B) / 2 - [J_ARM_CX[view], (v0 + v1) / 2]) < 0:
        out_px = -out_px
    q = A + tp[:, None] * (B - A) + (lat * half)[:, None] * out_px
    return q[:, 0], q[:, 1], t


# Pant photo landmarks (PHOTO, Leatt US on-model 1920 px): rows of the waist top, crotch and boot top; the
# pant's silhouette in each row (alpha) gives the across position, mapped onto his pant's silhouette.
# the big LEATT on his left thigh: centre above the knee joint (m), its angle from the outer side toward the front
# (deg), its length (m). PHOTO Leatt US front on-model: rows 790 to 1260 (knee+5 to +31 cm on PF_ROWS), across the
# leg's run at 0.83 to 0.98 of its width from the inner edge (row 1100: x 1377 to 1437 in 1022 to 1443): on a round
# thigh 37 to 84 deg from the front, its centre 62 deg from the front, 28 from the side (rounds 1 and 2 put it on
# the side line: Leatt's front view then saw it edge-on, it sees 60 px of it); the back photo does not see it
THIGH_LOGO = (0.19, 28.0, 0.26)
PF_ROWS = ((205, WAIST_FRONT), (None, 0.862), (1670, PANT_CUFF_Z + 0.005))   # crotch row: from alpha
# Round 4: the back photo's middle row is where its legs part (the first open row, 909), not its crotch: from
# behind, the thighs touch under the seat. Mapped to the crotch's height (main) it pushed the back's leg print up:
# the back of the knee's mesh panel (row 1240) to z 0.64, 11 cm over his knee joint; the shins' fade tops (1275) to
# 0.61, the front's (1300) at 0.56; the outer thigh's lime (ending at 1010) to 0.79, the front's (1050) at 0.70 and
# his 07's at the thigh LEATT's middle, 0.19 m over the knee joint (0.72). The two photos share one frame: 1460 and
# 1465 rows from the waist top to the boot top, the back's 15 to 20 rows higher (190 and 1650 to 205 and 1670). In
# the front's rows the back's split (909 + 17.5) is at z 0.768; its legs then run 0.55 mm a row, the front's 0.55
PB_SPLIT_Z = 0.768
PB_ROWS = ((190, WAIST_BACK), (None, PB_SPLIT_Z), (1650, PANT_CUFF_Z + 0.005))   # split row: from alpha


# Round 3b: the photos' silhouette runs, row by row, jittered by a few px (the alpha's edge, the gloves beside the
# thighs): every vertical stripe came out jagged (the shins' magenta read as jagged marks). The runs' ends are
# smoothed down the photo (a 15 row median, then 15 rows' mean), each regime (the whole pant, the two legs) apart.
# And the photos see a leg's outer side at a slant: past PANT_MIRROR from the front its last pixels were stretched
# round the side (or left plain, round 3). There the print is the photo's own seen from PANT_MIRROR back toward the
# front, mirrored (an estimate: Leatt's zebra wraps round the thigh to the knee, his 07 and Leatt's three-quarter
# photos; the bands meet themselves in a chevron on the line, as the print's own chevrons)
PANT_MIRROR = np.radians(60.0)
PANT_RUN_SMOOTH = 15     # rows
# Round 4: over the hips the mirror took its angle across the whole pant (one round section 44 cm wide), under the
# legs' split across each leg (22 cm): at the split its source on the outer side jumped from 11 to 5.5 cm inside the
# edge, a step across the outer thigh (main, sheet 07's side view). The angle now comes from each side's own section
# (the leg; over the hips the half pant, which the leg's section is at the split), and the two regimes' photo
# positions are blended over PANT_SPLIT_BLEND each way of the split
PANT_SPLIT_BLEND = 0.02  # m
# Round 4: the outseam. The pant's front and back halves took their own photo's print up to the seam, and the two
# photos' bands met there out of phase: a step all down the outer side (sheet 07's side view; main: 0.80 and 0.64 of
# the points along the left and right outseams agree across it, every 2 mm from 0.36 to 1.03 m). Each photo's print
# is mapped from a point's x and height alone, so either runs on past the seam continuously (folding where x turns,
# as at the photo's own edge). Round each outer side the two now meet along the least-cost line between
# PANT_SEAM_SPAN from the front (the leg's own angle, pant_charts'): its cost per cell is where one print has a band
# and the other not (a band: brightest display channel over 0.3 to 0.5; the black ink is 0.07, the fills' greys
# under 0.3), and half where both have bands of other colours (over 0.25 of a channel); plus PANT_SEAM_PRIOR per
# degree off the seam (where both agree it stays on the seam) and PANT_SEAM_TURN per step aside; anti-aliased over
# PANT_SEAM_SOFT. Each photo's white elements go only where its print does: the front's own thigh LEATT (taken out
# for the official one, painted black) punched black holes into the back's print run on over the front half
PANT_SEAM_SPAN = np.radians((50.0, 150.0))
PANT_SEAM_CELL = (0.002, np.radians(1.0))     # m of height, angle
PANT_SEAM_PRIOR = 0.004
PANT_SEAM_TURN = 0.02
PANT_SEAM_SOFT = np.radians(0.6)


def pant_runs(alpha, view, crotch_y):
    """Per photo row, the pant's run (above the crotch: the whole pant) or each leg's (below): {key: (a, b)} arrays
    over the rows, nan where none, smoothed down the photo (PANT_RUN_SMOOTH)."""
    from scipy import ndimage
    H, W = alpha.shape
    cx = W / 2
    out = {k: np.full((H, 2), np.nan) for k in ("all", "L", "R")}
    for y in range(H):
        xs = np.nonzero(alpha[y])[0]
        if len(xs) < 10:
            continue
        runs = [(q[0], q[-1]) for q in np.split(xs, np.nonzero(np.diff(xs) > 3)[0] + 1) if len(q) > 40]
        near = [q for q in runs if q[1] - q[0] > 120 and abs((q[0] + q[1]) / 2 - cx) < 500]
        if y < crotch_y:                                     # the whole pant: its runs near the middle, merged
            if near:
                out["all"][y] = (min(q[0] for q in near), max(q[1] for q in near))
        elif len(near) >= 2:
            near = sorted(near, key=lambda q: q[0])
            # front: his right leg on the image's left; back: his left leg on the image's left
            a, b = ("R", "L") if view == "front" else ("L", "R")
            out[a][y], out[b][y] = near[0], near[-1]
    for k, (y0, y1) in (("all", (0, crotch_y)), ("L", (crotch_y, H)), ("R", (crotch_y, H))):
        r = out[k][y0:y1]
        ok = ~np.isnan(r[:, 0])
        if ok.sum() < 2:
            continue
        idx = np.arange(len(r))
        for j in range(2):
            f = np.interp(idx, idx[ok], r[ok, j])
            f = ndimage.uniform_filter1d(ndimage.median_filter(f, PANT_RUN_SMOOTH, mode="nearest"),
                                         PANT_RUN_SMOOTH, mode="nearest")
            r[:, j] = np.where((idx >= idx[ok][0]) & (idx <= idx[ok][-1]), f, np.nan)   # gaps inside filled
    return out


def side_mirror(t, hi, lo, th0=PANT_MIRROR):
    """Across a leg seen square on (t: 0 .. 1), past th0 from the front toward the high and/or low side: the
    point's mirror image about th0 (in the angle round the leg, sin = 2 t - 1)."""
    th = np.arcsin(np.clip(2 * t - 1, -1, 1))
    if hi:
        th = np.where(th > th0, 2 * th0 - th, th)
    if lo:
        th = np.where(th < -th0, -2 * th0 - th, th)
    return (np.sin(th) + 1) / 2


def pant_photo_uv(pants, P, view, alpha, sil3d, mirror=True):
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
    runs = pant_runs(alpha, view, cy)
    zq, xq = P[:, 2], P[:, 0]
    w = smoothstep(rows[1][1] - PANT_SPLIT_BLEND, rows[1][1] + PANT_SPLIT_BLEND, zq)    # 1: the whole pant's rows
    for s in "LR":
        mm = (xq > 0) if s == "L" else (xq <= 0)
        sa, sl = sil3d["all"], sil3d[s]
        xm = xq
        if mirror:                       # the outer side, round the side's own section (the leg; the half pant)
            a0, a1 = np.interp(zq, sl[0], sl[1]), np.interp(zq, sl[0], sl[2])
            ts = side_mirror((xq - a0) / np.maximum(a1 - a0, 1e-6), s == "L", s == "R")
            xm = a0 + ts * (a1 - a0)
        us = []
        for whole in (True, False):                          # each regime, its rows clamped to its side of the split
            row = np.minimum(vi, cy - 1) if whole else np.maximum(vi, cy)
            span = runs["all"][row] if whole else runs[s][row]
            sec = sa if whole else sl
            xl, xr = np.interp(zq, sec[0], sec[1]), np.interp(zq, sec[0], sec[2])
            t = (xm - xl) / np.maximum(xr - xl, 1e-6)
            if view == "back":
                t = 1 - t
            us.append(span[:, 0] + t * (span[:, 1] - span[:, 0]))
        uw, ul = np.where(np.isnan(us[0]), us[1], us[0]), np.where(np.isnan(us[1]), us[0], us[1])
        uu = np.where(vi < cy, uw, ul) if PANT_SPLIT_BLEND <= 0 else uw * w + ul * (1 - w)
        ok = mm & ~np.isnan(uu)
        u[ok] = uu[ok]
    return u, v


def pant_seam_path(cost, z, al):
    """The line round an outer side where the two photos' prints meet (PANT_SEAM_*): per row of height, its angle.
    cost, z, al: per texel (the prints' difference, its height, its angle from the front). Returns (rows' z, angle)."""
    dz, da = PANT_SEAM_CELL
    zr = np.arange(z.min(), z.max() + dz, dz)
    ar = np.arange(PANT_SEAM_SPAN[0], PANT_SEAM_SPAN[1] + 1e-9, da)
    iz = np.clip(((z - zr[0]) / dz).astype(int), 0, len(zr) - 1)
    ia = np.round((al - ar[0]) / da).astype(int)
    ok = (ia >= 0) & (ia < len(ar))
    S, N = np.zeros((len(zr), len(ar))), np.zeros((len(zr), len(ar)))
    np.add.at(S, (iz[ok], ia[ok]), cost[ok])
    np.add.at(N, (iz[ok], ia[ok]), 1)
    C = np.where(N > 0, S / np.maximum(N, 1), 0.5) + PANT_SEAM_PRIOR * np.abs(np.degrees(ar) - 90)[None, :]
    D = C[0].copy()
    back = np.zeros(C.shape, int)
    cols = np.arange(len(ar))
    for i in range(1, len(zr)):                     # each row from the one below: straight on, or one cell aside
        cand = np.stack([D, np.r_[np.inf, D[:-1]] + PANT_SEAM_TURN, np.r_[D[1:], np.inf] + PANT_SEAM_TURN])
        k = cand.argmin(0)
        back[i] = k
        D = cand[k, cols] + C[i]
    j = int(D.argmin())
    path = np.zeros(len(zr), int)
    for i in range(len(zr) - 1, -1, -1):
        path[i] = j
        j = j - 1 if back[i, j] == 1 else j + 1 if back[i, j] == 2 else j
    return zr + dz / 2, ar[path]


def pant_seam_weight(pants, P, ch, zf, zb):
    """Per texel, how much of the back photo's print it takes: its own half's photo, except round the outer sides,
    where the two meet along pant_seam_path. zf, zb: the two prints there (linear)."""
    wb = np.isin(ch, (1, 3)).astype(float)
    df, db = to_srgb(zf), to_srgb(zb)
    bf, bb = smoothstep(0.3, 0.5, df.max(-1)), smoothstep(0.3, 0.5, db.max(-1))
    cost = np.abs(bf - bb) + 0.5 * bf * bb * np.clip(np.abs(df - db).max(-1) / 0.25, 0, 1)
    for s, sg in (("L", 1), ("R", -1)):
        env = pants["lenv"][s]
        _, _, th, _ = env.local(P)
        al = th * np.sign(env.e2[0]) * sg              # round the outer side from the front (0) to the back (pi)
        m = (P[:, 0] * sg > 0) & (al > 0)
        zr, ap = pant_seam_path(cost[m], P[m, 2], al[m])
        a = np.interp(P[m, 2], zr, ap)
        wb[m] = smoothstep(a - PANT_SEAM_SOFT, a + PANT_SEAM_SOFT, al[m])
    return wb


def pant_silhouette(V, crotch_z, Q):
    """His pant's front-view silhouette per height: (z, x_left, x_right) per leg below the crotch and whole above,
    from the mesh's cross-section at each height (its edges crossing it: continuous in height; round 3b, the
    vertices within 6 mm of each height jumped by up to 70 mm between heights 5 mm apart, and every stripe mapped
    through it came out serrated)."""
    zs = np.arange(PANT_CUFF_Z, WAIST_BACK + 0.005, 0.005)
    E, _ = edges_of(Q)
    a, b = V[E[:, 0]], V[E[:, 1]]
    out = {}
    for key in ("L", "R", "all"):
        lo, hi = [], []
        for z in zs:
            c = (np.minimum(a[:, 2], b[:, 2]) <= z) & (np.maximum(a[:, 2], b[:, 2]) > z)
            t = (z - a[c, 2]) / (b[c, 2] - a[c, 2])
            x = a[c, 0] + t * (b[c, 0] - a[c, 0])
            x = x[x > 0] if key == "L" else x[x <= 0] if key == "R" else x
            lo.append(x.min() if len(x) else np.nan)
            hi.append(x.max() if len(x) else np.nan)
        lo, hi = np.array(lo), np.array(hi)
        ok = ~np.isnan(lo)
        out[key] = (zs[ok], lo[ok], hi[ok])
    return out


# ================================================================ graphics: the clean flat print (decision 52)
# The base print is flat artwork, as the helmet's (helmet_art.py): Leatt's photos give the shapes only. Per chart
# (one pattern piece), the stripes and the white elements are level sets of fields traced from the photos, cut at
# their half-way contour and anti-aliased over one texel (crisp at any distance); the inks are classes whose colour
# is a smooth field (the stripes' lime-to-teal gradient, the yoke's magenta fading to black) averaged from the texels
# the photo sees square on (each texel weighs cos^2 of its view angle, so grazing sides take their colour from their
# neighbours, not from the photo's shaded edge); white is one ink. The photos' colours are first mapped onto the inks
# of Leatt US's front flat, the colour reference (ledger "Round 3"): the NZ distributor's on-model photos show the same
# inks paler (magenta with 4 times the green, teal with 7 times the red).
FLAT_REF = os.path.join("jersey", "jersey55_tigerpink_front-flat_leatt-us_5026000200_1920.png")
JF_REF = os.path.join("jersey", "jersey55_tigerpink_front-on-model_nz-distributor_LE5026000201-2_1600.jpg")
JB_REF = os.path.join("jersey", "jersey55_tigerpink_back-on-model_nz-distributor_LE5026000201-3_1600.jpg")
PF_REF = os.path.join("pants", "pant55iks_tigerpink_front-on-model_leatt-us_5026000320_1920.png")
PB_REF = os.path.join("pants", "pant55iks_tigerpink_back-on-model_leatt-us_5026000320_1920.png")
# where each ink is measured, (x0, y0, x1, y1) px (PHOTO; boxes checked on overlays): a flat part of the yoke, the
# chest LEATT, the chest's lime stripes and the black between them, the teal stripes low on the front
INK_BOXES = {
    FLAT_REF: {"magenta": (800, 300, 1250, 500), "white": (850, 540, 1250, 650), "lime": (750, 800, 1250, 1000),
               "teal": (750, 1200, 1250, 1450), "black": (750, 800, 1250, 1000)},
    JF_REF: {"magenta": (620, 370, 980, 470), "white": (610, 495, 1015, 600), "lime": (650, 720, 950, 860),
             "teal": (600, 1000, 1000, 1100), "black": (650, 740, 950, 900)},
    # the back: the yoke panel's flat middle and the black over the right shoulder blade (its shoulder LEATT clips
    # at 255: the back is exposed about 1.37 times the front)
    JB_REF: {"magenta": (700, 560, 900, 720), "black": (380, 480, 500, 640)},
}
JB_STRIPES = (250, 1350, 600, 1000, 25)   # PHOTO x0, x1, y0, y1, band rows: the back's stripes (back_map)
FP_FEATURE = 0.0004      # m, the traced fields' smoothing (the on-model photos' pixel: 0.66 mm, after a 5 px median)
FP_RANGE = 0.030         # m, the window for the stripes' local light and dark levels (stripes 12 to 25 mm wide)
FP_STRIPE_FIELD = 0.012  # m, the stripes' colour field (the airbrush gradients run over 50 to 300 mm)
FP_GROUND_FIELD = 0.0006  # m, the ground's colour field (keeps the yoke panel's cut edge, takes out the mesh)
FP_FILL = (0.02, 0.06, 0.18)   # m, wider fields filling where the photo saw nothing square on
FP_WHITE_CUT = 0.55      # white: min channel less 0.6 x chroma (display) over this; grey stripes reach 0.47
FP_STRIPE_CUT = 0.5      # the stripes: half-way between the local dark and light levels
FP_WHITE_MIN = 3e-6      # m2: smaller white specks are the photos' perforations reading light (holes 2.5 mm2; the
                         # FIVE.FIVE letters are 15 to 20 mm2 of ink)
FP_SPECK = 4e-5          # m2: stripe islands and gaps smaller than this are noise (the stripes' smallest tips: 1 cm2)
# the sleeves: two photos meet along their top and underarm lines and the arms are seen turned: bigger specks are
# noise there (stripes 2 cm wide), and white under 20 mm2 is the piping's broken trace (the sleeve's LEATT letters
# and brain icon are 100 mm2 and more); their ground (the magenta to black fade, the black) has no cut edge, and
# a field over 0.6 mm kept the photos' fold shading as grey blotches 2 to 5 cm across: over 20 mm (Leatt's airbrush
# fades run over 50 to 300 mm). The back panel likewise (its magenta fades at every edge, NZ back photo); the
# front keeps 0.6 mm for the yoke's cut edge over the chest
# The sleeves' upper bands and the side panels' are grey-teal (display about 0.39, 0.47, 0.49: min channel less
# 0.6 chroma 0.33): over the default 0.3 they counted as a white element's edge and were dropped, leaving the
# sleeves near black (round 3, reviewed); only over 0.5 there (the white cut is 0.55)
FP_SLEEVE = {"white_min": 2e-4, "speck": 1.5e-4, "ground": 0.02, "near_white": 0.95, "span": (0.05, 0.1),
             "fs_min": 0.10, "rng": 0.015}
# the sleeves' white elements: his left sleeve's line (510 mm2 on the raster); the elbow icon and the forearm LEATTs
# are printed from the official files (sleeve_marks), so the traced whites are the line's alone: pieces under
# 200 mm2 dropped (round 3b review: white specks, 24 to 91 mm2, among them the line's jog at the elbow, which the
# photos see at a slant and traced as fragments; drawn since round 4: SLEEVE_LINE)
# The sleeves' zebra (round 3b): traced on the raster the upper arm's bands came out as fragments (they fade from
# grey into the black toward the shoulder, under 0.25 of contrast, so the cut fell on the photos' noise; and a
# 3 cm window took its light level from the next band or the trunk's lime). It is traced first on Leatt US's front
# flat itself, inside each sleeve's outline (J_ARMS), where the sleeve is seen square on: an 11 px median takes out
# the perforations (dots 4 to 5 px, 15 px apart), a 3 mm field and a 1.5 cm window follow the fade, a contrast of
# 0.05 to 0.1 is pattern and under 0.10 of green light is the black; the white elements are left to the raster
# (all views). The raster then cuts that clean artwork again with the same options (FP_SLEEVE: near_white 0.95,
# the white elements themselves still guard their edges)
FLAT_TEXEL = 0.275 / 395  # m per px of Leatt US's front flat (its chest LEATT: 395 px for his 0.275 m, FRONT)
FLAT_MEDIAN = 11          # px
# Which of the flat's sleeves each of his sleeves takes its zebra from. The flat lays his left sleeve turned in,
# over the trunk's side (its outline takes in the lime side panel and the yoke) and sees its upper arm at a slant:
# traced there its grey bands came out as blobs. His right sleeve lies square on, its bands whole from the shoulder
# to the cuff; his left takes it mirrored (an estimate: the bands' colours run the same down both sleeves in the
# flat and the back photos, grey, teal, lime; their exact shapes on his left sleeve differ)
SLEEVE_ZEBRA_FROM = {"L": "R", "R": "R"}
# Round 4 (decision 58): checked along the front line (sleeve_profile: the light bands' t, shoulder point 0 to cuff
# end 1, the elbow at 0.50), both front views put his left's bands further down the arm than his right's: Leatt
# US's flat its teal at 0.480 against 0.445, its green at 0.705 against 0.665, the cuff's lime from 0.845 against
# 0.840; Leatt NZ's on-model front 0.430, 0.490, 0.590 and 0.765 against 0.375, 0.455, 0.555 and 0.730. (The bands
# arch up round the arm away from the front line, so the flat's turned-in left would see them higher, not lower.)
# Behind, Leatt NZ's back three-quarter flat puts his left's at 0.475, 0.725 and 0.810, the mirror (the right's
# front) at 0.445, 0.660 and 0.775. His left takes the right's print 0.035 further down the arm from the upper arm
# to the forearm (the front views' middle bands: 0.035 to 0.040), none over the raglan part and at the cuff's
# lime; its shapes stay the right's mirrored (an estimate). Per sleeve: knots, its own t and the flat's
SLEEVE_PHASE = {"L": ((0.0, 0.15, 0.35, 0.80, 0.86, 1.0), (0.0, 0.15, 0.315, 0.765, 0.86, 1.0))}
FP_FLAT_SLEEVE = {"white_min": 1.0, "speck": 1.5e-4, "ground": 0.02, "near_white": 0.6, "span": (0.05, 0.1),
                  "feature": 0.003, "fs_min": 0.10, "rng": 0.015}
FP_BACK = {"ground": 0.02, "near_white": 0.5}
# The top chevrons' arms under FIVE.FIVE fade from lime into the black band (Leatt's airbrush; front flat and NZ
# front photo): cut at 0.5 their ends were ragged (round 3). In this box (|x|, z from, z to; m, the front, from the
# texture's centre column: the yoke ends at z 1.35, the band 1.30 to 1.345, the top chevron's point 1.27 to 1.30)
# the cut is at 0.2, where the fade is near the black, and the stripe's colour is the photo's own fade over 5 mm
FP_FADE = {"cut": 0.2, "field": 0.005, "box": (0.17, 1.285, 1.345), "soft": 0.008}   # soft: m, the box's edges
#                                                                             blend over this (no step in the cut)
# The trunk's lower sides (round 3c, fix 2): in the NZ front photo the jersey blouses over the pant's Waistlock and
# its stripes zigzag in the folds at 1 to 3 cm (photo rows 950 to 1130 beside the side seams); traced at 0.4 mm they
# came out as steps beside his right hip (sheet 05, main to 3b). There the stripes' field is smoothed over 8 mm
# (the bands are 12 to 25 mm wide; Leatt's flat shows them as smooth curves down to the hem): fully below z_lo,
# blended in up to z_hi, from |x| x0 to x1 (the front's middle keeps the photo's own edges)
FP_HEM = {"feature": 0.008, "z": (WAIST_FRONT + 0.08, WAIST_FRONT + 0.12), "x": (0.10, 0.13)}
# the pant: the black zebra over teal, lime and magenta (chroma is stripe); Leatt US's on-model pant
# photos show folds on the black and airbrushed fades: stripe specks under 1.5 cm2 dropped, the ground's colour
# averaged over 3 mm (its fades run over 100 mm and more); their teal is paler than the jersey flat's (min channel
# less 0.6 chroma up to 0.40, PHOTO), so only over 0.5 counts as a white element's edge
# and its shins' stripes are seen at 60 to 80 deg and fade to purple: their colour from themselves (weights at
# least 0.1, from 0.6 of the way into the stripe), not from the thighs' lime 10 cm up
# Round 3b: traced on his pant's texels the outer thighs (past 83 deg from the photos) were plain black, though his
# 07 and Leatt's photos show the zebra wrapping round them to the knee, and the shins' magenta, seen at 60 to 80
# deg and fading to purple, came out as jagged vertical marks. Each photo is traced first in its own pixels (0.5 mm,
# where the legs are seen square on; the options below with a 2 mm field, which follows the shins' sweeping
# stripes) and the texels take that artwork as it is: to the outseam, the photo's edge stretched round the side
# (an estimate where the photo sees the side at a slant)
FP_PANT = {"speck": 1.5e-4, "feature": 0.0008, "ground": 0.003, "near_white": 0.5, "light": "chroma",
           "qfloor": 0.1, "s_in": 0.6}
FP_PANT_PHOTO = dict(FP_PANT, feature=0.002)
# Round 4: the shins' magenta strokes run up into airbrushed fades (magenta through purple to the black) that sweep
# out to the knee panel's seam (PHOTO Leatt US on-model: back rows 1275 to 1400, front 1300 to 1560; Leatt's flats
# the same). Cut at 0.5 the trace kept only their magenta: blunt tops at the fade's start, the purple a blur above
# (main, sheet 01). In these rows (photo px: from, to, soft) the cut is FP_FADE's 0.2 and the stroke's colour is the
# photo's own fade over 5 mm, as the jersey's chevron tops: a clean gradient over the traced shape
PANT_FADE_ROWS = {"front": (1290, 1570, 25), "back": (1250, 1420, 25)}
# and there the stroke's chroma falls to 0.10 at its top (back photo row 1290) over the black's 0.03 to 0.05: the
# 3 cm window's span (0.07 to 0.15 near the top) is under the 0.25 that counts as pattern elsewhere, so the cut there
# was the absolute one, and the purple's top 4 cm was ground. In the fades, a span from 0.05 to 0.10 is pattern
PANT_FADE_SPAN = (0.05, 0.10)


def to_lin(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def ink_class(name, a):
    """The pixels of one ink (display values 0..1)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if name == "magenta":
        return (r > 0.43) & (g < 0.45 * r) & (b > 0.3 * r)
    if name == "lime":
        return (g > 0.47) & (r > 0.55 * g) & (b < 0.55 * g)
    if name == "teal":
        return (g > 0.39) & (b > 0.6 * g) & (r < 0.75 * g)
    if name == "black":
        return a.max(-1) < 0.275
    if name == "white":
        return (a.min(-1) > 0.667) & (a.max(-1) - a.min(-1) < 0.176)
    raise ValueError(name)


INK_SOFT = 0.1    # ink_weight's ramp each side of an ink_class bound (display levels / 255, or a ratio)


def ink_weight(name, a):
    """ink_class softened (display values 0..1): each of its bounds ramped over INK_SOFT either side, so the weight
    runs smoothly from 1 well inside the class to 0 well outside it."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    def s(m):                                                           # m > 0 inside the bound
        return smoothstep(-INK_SOFT, INK_SOFT, m)
    rr, gg = np.maximum(r, 1e-6), np.maximum(g, 1e-6)
    if name == "magenta":
        return s(r - 0.43) * s(0.45 - g / rr) * s(b / rr - 0.3)
    if name == "lime":
        return s(g - 0.47) * s(r / gg - 0.55) * s(0.55 - b / gg)
    if name == "teal":
        return s(g - 0.39) * s(b / gg - 0.6) * s(0.75 - r / gg)
    if name == "black":
        return s(0.275 - a.max(-1))
    raise ValueError(name)


def photo_inks(name):
    """A photo's inks (linear RGB): per class in its box, the median of the brighter half of its pixels (the black:
    of all of them), so the shading and the edges' blends do not count."""
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(REF, name)).convert("RGB")).astype(float) / 255
    out = {}
    for k, (x0, y0, x1, y1) in INK_BOXES[name].items():
        px = a[y0:y1, x0:x1].reshape(-1, 3)
        px = px[ink_class(k, px)]
        if k != "black":
            L = px.mean(1)
            px = px[L >= np.median(L)]
        out[k] = to_lin(np.median(px, 0))
    return out


# Materials round 1, phase B (decision 61; research/scene-look.md "The kit's inks (phase B)"): the textures carry
# Leatt US's front flat's inks (photo_inks times gain, white INK_WHITE). Fitted jointly to Leatt's flats under Standard
# (each ink's colour against the white, at the flat's luminance) and his photos 07, 08 and 09 at PHOTO_EV (each
# ink's diffuse body), at the prints' grey layer (MATERIALS: sheen 0, Specular IOR Level 0.25), the inks' albedos
# move by these factors per channel (linear light). The black: his darks (the specular that lifted them is halved);
# the flat's own black, 0.009 of its white, is under what any dielectric reflects of an even light (Fresnel 0.04 at
# IOR 1.5): Leatt's photograph, not the cloth. The magenta: its green out and its blue down (his pinks: green 1 to 21
# of 255, redder than ours). The lime and the teal stay: his 07 and 09 disagree on them (their lightness a stop
# apart) and their fitted change was within a few levels
INK_FACTORS = {"black": (2.76, 2.76, 2.76), "magenta": (1.03, 0.02, 0.86)}


def palette_inks(factors=None):
    """The textures' inks before the palette and after it (linear RGB): white, black, magenta, lime, teal."""
    f = INK_FACTORS if factors is None else factors
    flat = photo_inks(FLAT_REF)
    white = to_lin(np.array(INK_WHITE) / 255)
    gain = white.mean() / flat["white"].mean()
    src = {k: white if k == "white" else flat[k] * gain for k in ("white", "black", "magenta", "lime", "teal")}
    return src, {k: v * np.asarray(f.get(k, (1.0, 1.0, 1.0)), float) for k, v in src.items()}


def ink_palette(rgb, factors=None):
    """Display values in and out (last axis RGB): the inks' factors laid on the texture as the fit laid them on the
    inks' classes in his photos and Leatt's flats. In linear light a texel of a chromatic ink's class (ink_weight:
    ink_class softened) takes that ink's factors as a product, so the magenta's whole class (its traced shades, the
    back yoke's green 25 and the front's 14, and its fades) loses its green as the ink does; a texel of the black's
    class takes the black's lift (its fitted colour less its own) as a sum, so the black's shades and its blends with
    the white at the cut edges keep their steps. Each ink lands on its fitted colour (its own class whole, the others'
    none); colours of no class (the whites, the sleeves' grey-teal bands, the light pinks at the logos' edges) stay.
    Barycentric palettes (each colour placed among black, white and the two inks next to it by hue, one affine map per
    wedge) were tried and dropped: the traced shades kept their green as a white or lime part (the back yoke 18
    levels over the front), and the teal, almost opposite the magenta round the grey axis (177 deg), made the
    teal-magenta wedge near singular (light pinks lost their green whole; 1-level steps jumped 100 levels).
    Elementwise: the same bytes on any thread count."""
    src, dst = palette_inks(factors)
    f = INK_FACTORS if factors is None else factors
    shape = np.shape(rgb)
    a = np.clip(np.reshape(rgb, (-1, 3)).astype(float), 0, 1)
    x = to_lin(a)
    inks = [k for k in ("magenta", "lime", "teal") if k in f]
    w = np.stack([ink_weight(k, a) for k in inks], 1) if inks else np.zeros((len(a), 0))
    w = w / np.maximum(w.sum(1, keepdims=True), 1.0)                       # where two classes' ramps meet
    F = np.ones_like(x)
    for j, k in enumerate(inks):
        F = F + w[:, j:j + 1] * (np.asarray(f[k], float) - 1.0)
    out = x * F
    if "black" in f:
        out = out + ink_weight("black", a)[:, None] * (dst["black"] - src["black"])
    return to_srgb(out).reshape(shape)


# The stripes are one airbrushed gradient, lime under the yoke to teal at the hem, not two inks: the boxes' "teal" is
# the hem's on the flat (rows 1200-1450) but 20 cm higher on the NZ photo (tucked in under the pant), so a map
# fitted to the boxes sent the NZ photo's lower stripes past the flat's teal (R 0, B 208 against 55-93, 178-181).
# GRAD_* (PHOTO, both front views): the stripe/black profile down the centre (16 cm wide band) from the chest LEATT
# in each, scaled by the LEATT's length (0.275 m), matched by correlation (0.97: the flat runs 1.20 times as long as
# the on-model jersey, bloused over the body); the brighter half of the stripe pixels per 24-row band 0.10 to 0.40 m
# under the LEATT, 24 cm wide, on both, are the pairs the NZ photos' map is fitted to (with the boxes' magenta and
# white, each weighing as 4 pairs).
GRAD_LEATT = {JF_REF: (590, 480, 1030, 610), FLAT_REF: (840, 520, 1280, 640)}   # search boxes for the LEATT, px
GRAD_Z = np.arange(0.10, 0.41, 0.02)    # m under the LEATT's bottom (on the NZ photo)
GRAD_INK_WEIGHT = 4


def _stripe_px(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (g > 0.40) & (a.min(-1) < 0.6) & (r < 1.1 * g) & (g - 0.5 * (r + b) > 0.08)


def gradient_pairs(src_name=JF_REF, dst_name=FLAT_REF):
    """The stripes' gradient matched row by row between two front views (GRAD_*): linear colours (src, dst)."""
    from PIL import Image
    from scipy import ndimage
    ims = {}
    for name, med in ((src_name, 5), (dst_name, 3)):
        im = Image.open(os.path.join(REF, name)).convert("RGBA")
        a = np.asarray(im).astype(float) / 255
        rgb = np.stack([ndimage.median_filter(a[..., k], med) for k in range(3)], -1)
        x0, y0, x1, y1 = GRAD_LEATT[name]
        w = (rgb[y0:y1, x0:x1].min(-1) > 0.7) & (np.ptp(rgb[y0:y1, x0:x1], -1) < 0.2)
        ys, xs = np.nonzero(w)
        ims[name] = (rgb, a[..., 3] > 0.5, y0 + ys.max(), (2 * x0 + xs.min() + xs.max()) / 2,
                     (xs.max() - xs.min()) / 0.275)                 # image, alpha, LEATT bottom, centre, px per m
    zs = np.arange(0.0, 0.45, 0.002)

    def profile(name):
        rgb, al, bot, c, s = ims[name]
        out = np.full(len(zs), np.nan)
        for i, z in enumerate(zs):
            r = int(bot + z * s)
            if r < rgb.shape[0]:
                out[i] = _stripe_px(rgb[r, int(c - 0.08 * s):int(c + 0.08 * s)]).mean()
        return out
    ps, pd = profile(src_name), profile(dst_name)
    best = (-2, 1.0, 0.0)
    for k in np.arange(0.85, 1.25, 0.005):                           # dst z = k src z + o
        for o in np.arange(-0.06, 0.06, 0.002):
            zd = k * zs + o
            ok = ~np.isnan(ps) & (zd >= 0) & (zd <= zs[-1])
            if ok.sum() >= 100:
                cc = np.corrcoef(ps[ok], np.interp(zd[ok], zs, np.nan_to_num(pd)))[0, 1]
                best = max(best, (cc, k, o))
    _, k, o = best
    pairs = []
    for z in GRAD_Z:
        cols = []
        for name, zz in ((src_name, z), (dst_name, k * z + o)):
            rgb, al, bot, c, s = ims[name]
            r, x0, x1 = int(bot + zz * s), int(c - 0.12 * s), int(c + 0.12 * s)
            blk = rgb[r - 12:r + 12, x0:x1]
            px = blk[_stripe_px(blk) & al[r - 12:r + 12, x0:x1]]
            if len(px) < 80:
                break
            L = px.mean(1)
            cols.append(to_lin(np.median(px[L >= np.median(L)], 0)))
        if len(cols) == 2:
            pairs.append(cols)
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])


def ink_map(src_name, dst_name=FLAT_REF):
    """The map (4 x 3, linear RGB: a 3 x 3 matrix and the offset) taking one photo's inks onto the reference's: the
    black onto the black exactly, the matrix fitted to the other inks in relative error per channel (least
    squares in linear light would favour the light inks and leave the darks wrong). For the NZ front view, the
    stripes' gradient pairs (gradient_pairs) stand for the lime and teal boxes."""
    s, d = photo_inks(src_name), photo_inks(dst_name)
    if src_name in GRAD_LEATT and dst_name in GRAD_LEATT:
        gs, gd = gradient_pairs(src_name, dst_name)
        keys = ["magenta", "white"] * GRAD_INK_WEIGHT
        A = np.array([s[k] for k in keys] + list(gs)) - s["black"]
        B = np.array([d[k] for k in keys] + list(gd)) - d["black"]
    else:
        keys = [k for k in sorted(s) if k != "black"]
        A = np.array([s[k] - s["black"] for k in keys])
        B = np.array([d[k] - d["black"] for k in keys])
    M3 = np.zeros((3, 3))
    for j in range(3):
        wgt = 1.0 / (B[:, j] + d["black"][j] + 0.02)
        M3[:, j] = np.linalg.lstsq(A * wgt[:, None], B[:, j] * wgt, rcond=None)[0]
    return np.vstack([M3, d["black"] - s["black"] @ M3])


def back_map(base, dst_name=FLAT_REF):
    """The NZ back photo's map: the front's (base) refitted so the back's yoke magenta and black land on the flat's
    while its stripes keep what the front's map gives them. The back photo is brighter (its magenta (230, 47, 149)
    against the front's (202, 30, 125), its white clipped): through the front's map its yoke read (255, 40, 157)
    against the flat's (225, 11, 134), and his photo 06 shows his back's magenta as deep as his front's."""
    from PIL import Image
    s, d = photo_inks(JB_REF), photo_inks(dst_name)
    a = np.asarray(Image.open(os.path.join(REF, JB_REF)).convert("RGB")).astype(float) / 255
    x0, x1, y0, y1, step = JB_STRIPES
    S = []
    for y in range(y0, y1, step):
        px = a[y:y + step, x0:x1].reshape(-1, 3)
        px = px[_stripe_px(px)]
        if len(px) > 200:
            L = px.mean(1)
            S.append(to_lin(np.median(px[L >= np.median(L)], 0)))
    S = np.array(S)
    A = np.array([s["magenta"]] * GRAD_INK_WEIGHT + list(S)) - s["black"]
    B = np.array([d["magenta"]] * GRAD_INK_WEIGHT + list(S @ base[:3] + base[3])) - d["black"]
    M3 = np.zeros((3, 3))
    for j in range(3):
        wgt = 1.0 / (B[:, j] + d["black"][j] + 0.02)
        M3[:, j] = np.linalg.lstsq(A * wgt[:, None], B[:, j] * wgt, rcond=None)[0]
    return np.vstack([M3, d["black"] - s["black"] @ M3])


def nc_blur(val, w, sigma):
    """Normalised convolution: the w-weighted Gaussian mean of val (sigma in texels) and the local weight; the wide
    ones on a coarser grid. val (H, W) or (H, W, 3), w (H, W)."""
    from scipy import ndimage
    H, W = w.shape
    k = max(1, int(sigma / 4))
    vw = val * (w[..., None] if val.ndim == 3 else w)
    ww = w
    if k > 1:
        Hp, Wp = -(-H // k) * k, -(-W // k) * k

        def down(x):
            x = np.pad(x, [(0, Hp - H), (0, Wp - W)] + [(0, 0)] * (x.ndim - 2))
            return x.reshape(Hp // k, k, Wp // k, k, *x.shape[2:]).mean((1, 3))
        vw, ww = down(vw), down(ww)
    s = sigma / k
    num = ndimage.gaussian_filter(vw, (s, s, 0) if vw.ndim == 3 else s, mode="constant")
    den = ndimage.gaussian_filter(ww, s, mode="constant")
    if k > 1:
        yy, xx = np.meshgrid((np.arange(H) + 0.5) / k - 0.5, (np.arange(W) + 0.5) / k - 0.5, indexing="ij")

        def up(x):
            if x.ndim == 3:
                return np.stack([ndimage.map_coordinates(x[..., i], [yy, xx], order=1, mode="nearest")
                                 for i in range(x.shape[2])], -1)
            return ndimage.map_coordinates(x, [yy, xx], order=1, mode="nearest")
        num, den = up(num), up(den)
    out = num / np.maximum(den, 1e-9)[..., None] if num.ndim == 3 else num / np.maximum(den, 1e-9)
    return out, den


def nc_fill(val, w, sigmas, lo=0.004, hi=0.03):
    """val's weighted mean at the first scale; where that scale had little weight round a texel, the next wider."""
    res = [nc_blur(val, w, s) for s in sigmas]
    out = res[-1][0]
    for o, c in res[-2::-1]:
        a = smoothstep(lo, hi, c)
        out = o * a[..., None] + out * (1 - a[..., None]) if o.ndim == 3 else o * a + out * (1 - a)
    return out


def clean_cut(f, t, sel, min_in, min_out):
    """The field f with the specks of its cut {f > t} taken out: islands smaller than min_in texels pushed under the
    cut, holes smaller than min_out over it (the photos' noise, a perforation reading light, a fold's highlight)."""
    from scipy import ndimage
    f = f.copy()
    for inside, mn, val in ((True, min_in, t - 0.5), (False, min_out, t + 0.5)):
        b = ((f > t) if inside else (f <= t)) & sel
        lab, n = ndimage.label(b)
        if not n:
            continue
        size = ndimage.sum(b, lab, np.arange(1, n + 1))
        small = np.isin(lab, np.nonzero(size < mn)[0] + 1)
        small = ndimage.binary_dilation(small, iterations=2) & ~(b & ~small)   # with its rim, not its neighbours
        f[small] = np.minimum(f[small], val) if inside else np.maximum(f[small], val)
    return f


def aa_cut(f, t):
    """Coverage of {f > t} per texel, anti-aliased over one texel by the field's slope."""
    gy, gx = np.gradient(f)
    return np.clip(0.5 + (f - t) / np.maximum(np.hypot(gx, gy), 1e-6), 0, 1)


def flat_layers(col, q, sel, texel, white, shapes=None, white_min=None, speck=None, feature=None, ground=None,
                near_white=0.3, light="green", qfloor=0.0, s_in=0.85, fade=None, rng=FP_RANGE, span=(0.25, 0.4),
                fs_min=0.0, whites=True, plain=None, smooth=None, cover=None, fade_span=None):
    """The flat print of one chart (arrays cropped to it): col the photos' colour (linear, on the reference's inks),
    q the view weight (0 unseen .. 1 square on), sel the chart's texels, texel its size in m, white the white ink,
    shapes where the photo's shapes count (elsewhere plain ground: what a photo does not see is not traced).
    plain: where the print is ground only (no stripes; the white elements stay, and the photo's stripes there do not
    colour the ground). smooth: (weight, feature in m): the stripes' field smoothed over that feature where the
    weight is 1 (the cloth's folds in the photo, FP_HEM). cover: where something covers the garment in the photo
    (PF_HIDDEN; plain there): its colour does not blur into the stripes round it. fade_span: in the fades, the span
    that counts as pattern (PANT_FADE_SPAN). Returns the colour (linear; with the white elements laid over it unless
    whites is False) and the stripe and white coverages."""
    from scipy import ndimage
    w0 = sel.astype(float)
    d = to_srgb(col)
    G = d[..., 1]
    fw = d.min(-1) - 0.6 * (d.max(-1) - d.min(-1))                   # white: light and grey
    # the stripes (grey, teal, green, lime): green light; the magenta and purple grounds count as dark as the black
    # (the jersey); on the pant the black zebra lies over every ink (teal, lime, magenta): their chroma (the folds'
    # grey highlights on the black have none)
    if light == "green":
        fs = np.clip(G - 0.7 * np.maximum(d[..., 0] - G, 0) - 0.7 * np.maximum(d[..., 2] - G, 0), 0, 1)
    else:
        fs = d.max(-1) - d.min(-1)
    sf = (FP_FEATURE if feature is None else feature) / texel
    wb0 = w0 if cover is None else w0 * ~cover
    fw = nc_blur(fw, wb0, sf)[0]
    fs_raw = fs
    fs = nc_blur(fs, wb0, sf)[0]
    if cover is not None:
        fw, fs = np.where(cover, 0.0, fw), np.where(cover, 0.0, fs)
    if smooth is not None and np.any(smooth[0] > 0):
        fs = fs * (1 - smooth[0]) + nc_blur(fs_raw, w0, smooth[1] / texel)[0] * smooth[0]
    if shapes is not None:
        off = sel & ~shapes
        fw = np.where(off, np.minimum(fw, 0.0), fw)
        fs = np.where(off, 0.0, fs)
    white_min = FP_WHITE_MIN if white_min is None else white_min
    speck = FP_SPECK if speck is None else speck
    fw = clean_cut(fw, FP_WHITE_CUT, sel, white_min / texel ** 2, FP_WHITE_MIN / texel ** 2)
    aw = aa_cut(fw, FP_WHITE_CUT) * sel
    # the stripes, cut half-way between the local dark and light levels; never next to the white elements (their
    # blended edges would read as stripe)
    near_w = ndimage.binary_dilation((fw > near_white) | (aw > 0.5), iterations=max(1, int(round(0.0015 / texel))))
    r = max(3, int(round(rng / texel)))
    okf = sel & ~near_w
    lo = ndimage.minimum_filter(np.where(okf, fs, 9.0), r)
    hi = ndimage.maximum_filter(np.where(okf, fs, -9.0), r)
    ok = okf & (lo < 5) & (hi > -5)
    lo = nc_blur(np.where(ok, lo, 0.0), ok.astype(float), r / 2)[0]
    hi = nc_blur(np.where(ok, hi, 0.0), ok.astype(float), r / 2)[0]
    span_k = span
    span = hi - lo
    # no pattern round a texel (span under 0.25: a dark gradient's grey against the black; the back's flanks beside
    # the magenta panel, PHOTO back on-model): an absolute cut, so plain grounds stay plain and solid cuffs solid
    if fade is not None and fade_span is not None:
        k = smoothstep(span_k[0] + (fade_span[0] - span_k[0]) * fade, span_k[1] + (fade_span[1] - span_k[1]) * fade,
                       span)
    else:
        k = smoothstep(span_k[0], span_k[1], span)
    s = k * (fs - lo) / np.maximum(span, 1e-3) + (1 - k) * (fs - 0.12) / 0.3
    s = np.where(near_w, -1.0, s)
    s = np.where(fs < fs_min, np.minimum(s, 0.0), s)                 # too dark to be a stripe (a fade's black end)
    s0 = s                                                           # the ground's own cut, unshifted
    if fade is not None:
        # airbrushed ends (FP_FADE; fade: 0 to 1): cut low, where the fade is near the black, so the cut's edge
        # does not show
        s = s + (FP_STRIPE_CUT - FP_FADE["cut"]) * fade
    s = clean_cut(s, FP_STRIPE_CUT, sel, speck / texel ** 2, speck / texel ** 2)
    a_s = aa_cut(s, FP_STRIPE_CUT) * sel * (1 - aw)
    if plain is not None:
        a_s = a_s * ~plain
    # the inks' colour fields
    clean = (aw < 0.01) & sel & (True if shapes is None else shapes)
    qw = np.maximum(q ** 2, qfloor)
    ws = qw * ((s > s_in) & clean)
    # the ground by the unshifted cut (round 3b: the fade's shifted cut left the band no ground, filled from the
    # yoke: magenta blotches under FIVE.FIVE)
    wb = qw * ((s0 < 0.15) & (s < FP_STRIPE_CUT) & clean)
    Cs = nc_fill(col, ws, [FP_STRIPE_FIELD / texel] + [f / texel for f in FP_FILL])
    if fade is not None:
        # and coloured by the photo's own fade (lime to black), smoothed: a clean gradient over the traced shape
        wf_ = qw * ((s > FP_STRIPE_CUT) & clean & (fade > 0))
        Cf = nc_fill(col, wf_, [FP_FADE["field"] / texel] + [f / texel for f in FP_FILL])
        Cs = Cs * (1 - fade[..., None]) + Cf * fade[..., None]
    Cb = nc_fill(col, wb, [(FP_GROUND_FIELD if ground is None else ground) / texel] + [f / texel for f in FP_FILL])
    out = Cb * (1 - a_s)[..., None] + Cs * a_s[..., None]
    if whites:
        out = out * (1 - aw)[..., None] + np.asarray(white) * aw[..., None]
    return np.minimum(out, np.asarray(white)), a_s, aw            # no ink lighter than the white


def flat_print(lin, q, chm, charts, texel, gain, white, shapes=None, opts=None, fade=None, plain=None,
               smooth=None):
    """The flat print over the given charts: lin the photos' colours (linear, on the reference's inks), q the view
    weights, shapes where the photos' shapes count, plain where the print is ground only. Returns display values."""
    lin = lin * gain
    out = np.zeros_like(lin)
    for c in charts:
        m = chm == c
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = max(ys.min() - 8, 0), ys.max() + 9, max(xs.min() - 8, 0), xs.max() + 9
        sl = (slice(y0, y1), slice(x0, x1))
        o, _, _ = flat_layers(np.clip(lin[sl], 0, 1), q[sl], m[sl], texel, white,
                              None if shapes is None else shapes[sl], fade=None if fade is None else fade[sl],
                              plain=None if plain is None else plain[sl],
                              smooth=None if smooth is None else (smooth[0][sl], smooth[1]), **(opts or {}).get(c, {}))
        out[sl][m[sl]] = o[m[sl]]
    return to_srgb(out)


def flat_sleeve_art(gain, white):
    """Each sleeve's zebra traced on Leatt US's front flat itself (FP_FLAT_SLEEVE): a Photo of the flat whose pixels
    inside each sleeve's outline are the traced artwork (display), the white elements and the sleeve's lit edge
    (over 0.6 white, dilated 2 mm) filled from the ground round them."""
    from scipy import ndimage
    pl = Photo(FLAT_REF, median=FLAT_MEDIAN)
    a = pl.a.copy()
    H, W = pl.bad.shape
    yy, xx = np.mgrid[0:H, 0:W]
    tab = J_ARM_TAB["flat"]
    for s in sorted(set(SLEEVE_ZEBRA_FROM.values())):
        (u0, v0), (u1, v1) = J_ARMS[("flat", s)]
        A, B = np.array([u0, v0], float), np.array([u1, v1], float)
        L = np.linalg.norm(B - A)
        dd = (B - A) / L
        t = ((xx - A[0]) * dd[0] + (yy - A[1]) * dd[1]) / L
        lat = (xx - A[0]) * dd[1] - (yy - A[1]) * dd[0]
        inside = (t > -0.05) & (t < 1.05) & (np.abs(lat) < np.interp(t, tab[0], tab[1]) * 1.05) & ~pl.bad
        ys, xs = np.nonzero(inside)
        sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
        sel = inside[sl]
        d = a[sl]
        fw = d.min(-1) - 0.6 * (d.max(-1) - d.min(-1))
        sh = ~ndimage.binary_dilation(fw > FP_FLAT_SLEEVE["near_white"], iterations=int(round(0.002 / FLAT_TEXEL)))
        col = np.clip(to_lin(d) * gain, 0, 1)
        o, _, _ = flat_layers(col, sel.astype(float), sel, FLAT_TEXEL, white, sh & sel, **FP_FLAT_SLEEVE)
        a[sl] = np.where(sel[..., None], to_srgb(o / gain), a[sl])
    pl.a = a
    return pl


def sleeve_unroll(body, s, P):
    """A sleeve point unrolled about its arm: the angle round the segment's axis (upper arm, forearm; from its
    front, his outward side positive), the distance from that axis and the distance along the arm from the shoulder
    point (the segments as arm_facing and sleeve_photo_uv split them)."""
    S, E, W, f, o = arm_frame(body, s)
    L1 = np.linalg.norm(E - S)
    ang, rad, along = np.zeros(len(P)), np.zeros(len(P)), np.zeros(len(P))
    upper = ((P - S) @ (E - S)) < np.dot(E - S, E - S)
    for A, B, sel, a0 in ((S, E, upper, 0.0), (E, W, ~upper, L1)):
        d = (B - A) / np.linalg.norm(B - A)
        fs = np.array([0, -1.0, 0]) - d * (-d[1])
        fs /= np.linalg.norm(fs)
        os_ = o - d * np.dot(o, d) - fs * np.dot(o, fs)
        os_ /= np.linalg.norm(os_)
        r = (P[sel] - A) - np.outer((P[sel] - A) @ d, d)
        ang[sel] = np.arctan2(r @ os_, r @ fs)
        rad[sel] = np.linalg.norm(r, axis=1)
        along[sel] = a0 + (P[sel] - A) @ d
    return ang, rad, along


FP_SLEEVE_WRAP = 0.04    # m, the unrolled sleeve's raster runs on this far past its back line, both ways
# Leatt's marks on the sleeves, printed from its official files (round 3b): the photos see them at a slant, and
# traced from them they came out as a blob (his right forearm's LEATT) and specks (his left forearm's icon). Each:
# sleeve, t along the arm (sleeve_photo_uv's: shoulder point 0, cuff end 1), the angle round the arm from its front
# toward its outside (deg), width (m), art.
# - R, LEATT: Leatt US's front flat, ink rows 1204 to 1409 on the sleeve's line from row 470 to 1640 (t 0.627 to
#   0.802: centre 0.715; long 0.175 of his arm's 0.503 m, 88 mm), its centre 83 px outward of the line where the
#   sleeve's half is 87 px (lat 0.95: 72 deg); reading down the arm, its letters' tops toward the front. Leatt NZ's
#   back photo sees four of its letters at the right forearm's outer edge, 100 px (63 mm).
# - L, icon: Leatt NZ's back three-quarter flat (round 4, decision 58; it sees the elbow square, at 1:1), the
#   triangle's runs at rows 873 to 922 (t 0.473 to 0.515: centre 0.494) and 178 to 207 deg (b34's mapping: centre
#   192), just past the line's jog toward the arm's inside, its point that way (its flat side along the arm, the
#   line's stub pointing at its upper corner). Round 3b had it at t 0.56, 112 deg, apex up the arm, from Leatt NZ's
#   back on-model photo, which sees it at the arm's outer edge (lat 0.93): that photo sees the line there too, so
#   its arm is turned some 50 deg and its angles at that edge do not hold. 19 mm (b34: 21 mm along the arm).
# - L, LEATT: under the end of the line's run down the forearm, its letters' baseline beside the line (the back
#   three-quarter flat: the letters' runs at rows 1032 to 1136, t 0.618 to 0.706, 104 to 135 deg, the line's end at
#   t 0.623, 133 deg; Leatt NZ's side panel close-up, 1:1: the line ends 15 px over the LEATT's top, 28 px past its
#   baseline edge; the front three-quarter on-model: the line ends at its top corner). Half the right's length
#   (0.088 of the arm against the right's 0.175 in the front flat: 44 mm). Its top at the line's end, its centre
#   9 mm from the line (the letters' half height 5.5 mm, 2 mm clear of the line's edge): t 0.663, 123 deg. Round 3b
#   had the right's place mirrored (t 0.715, 72 deg, 88 mm: an estimate). Reading up the arm, its letters' tops
#   toward the front (both photos: the letters run toward the elbow), so it reads from outside as the right's does.
SLEEVE_MARKS = (("R", 0.715, 72.0, 0.088, "leatt"), ("L", 0.663, 123.0, 0.044, "leatt"),
                ("L", 0.494, 192.0, 0.019, "icon"))
SLEEVE_MARK_KEEP = 0.012        # m round each mark where the photos' traced whites are dropped


def sleeve_marks(body, pos, nrm, chm):
    """The sleeve marks (SLEEVE_MARKS) laid out: per mark its canvas (the official art, white), the texels it prints
    on, and a test for the points round it where traced whites are dropped (a LEATT: all round the arm over its
    span, as the photos' slanted views of it land anywhere round the forearm; the icon: round the icon)."""
    out = []
    for s, t, ang, w, kind in SLEEVE_MARKS:
        S, E, W, f, o = arm_frame(body, s)
        L1, L2 = np.linalg.norm(E - S), np.linalg.norm(W - E)
        al = t * (L1 + L2)
        A, d = (S + (E - S) * al / L1, (E - S) / L1) if al < L1 else (E + (W - E) * (al - L1) / L2, (W - E) / L2)
        fd = f - d * np.dot(f, d)
        fd /= np.linalg.norm(fd)
        od = o - d * np.dot(o, d) - fd * np.dot(o, fd)
        od /= np.linalg.norm(od)
        th = np.radians(ang)
        n = np.cos(th) * fd + np.sin(th) * od                       # out of the arm, at the mark
        base = 2 if s == "L" else 4
        m = (chm == base) | (chm == base + 1)
        P = pos[m]
        ring = P[np.abs((P - A) @ d) < 0.004]
        rr = (ring - A) - np.outer((ring - A) @ d, d)
        C = ring[np.argmax((rr @ n) / np.linalg.norm(rr, axis=1))]  # the cloth's point in that direction
        if kind == "leatt":
            art = official_wordmark()
            a = d if s == "R" else -d                               # down the right arm, up the left
            b = np.sin(th) * fd - np.cos(th) * od                   # tops to the front
        else:
            art = leatt_icon()
            b = -np.sin(th) * fd + np.cos(th) * od                  # its point round the arm, toward the larger angle
            a = np.cross(b, n)
        assert np.dot(np.cross(a, b), n) > 0.99                     # seen from outside, not mirrored
        h = w * art.shape[0] / art.shape[1]
        cv = Canvas(C, a, b, w + 0.01, h + 0.01, ppm=4000)
        cv.stamp(art, 0.0, 0.0, w, color=INK_WHITE)

        def near(Q, C=C, a=a, b=b, n=n, w=w, h=h, k=SLEEVE_MARK_KEEP):
            q = Q - C
            return (np.abs(q @ a) < w / 2 + k) & (np.abs(q @ b) < h / 2 + k) & (q @ n > -0.02)
        zone = m & near(pos, k=0.004) & ((nrm @ n) > 0.2)
        if kind == "leatt":
            def keep(Q, A=A, d=d, w=w, sg=1 if s == "L" else -1, k=SLEEVE_MARK_KEEP):
                q = Q - A
                al = q @ d
                rad = np.linalg.norm(q - np.outer(al, d), axis=1)
                return (np.abs(al) < w / 2 + k) & (rad < 0.10) & (Q[:, 0] * sg > 0.1)
        else:
            keep = near
        out.append(dict(s=s, kind=kind, C=C, n=n, a=a, b=b, w=w, h=h, canvas=cv, zone=zone, near=near, keep=keep))
    return out


# His left sleeve's line past the elbow (round 4, decision 58). Traced, the photos gave the line from the shoulder
# down to t 0.445 at 158 to 164 deg (texture: 3.2 mm across at half its white, its core 2 mm) and the rest as specks
# (dropped since round 3b). Leatt NZ's back three-quarter flat sees the rest at 1:1 (its white runs per row, placed
# by sleeve_photo_uv's b34 mapping): the line comes down to a junction at row 860 (t 0.463, 164 deg); a stub runs on
# 6 px toward the icon (t 0.468, 171 deg); the line jogs out across the arm to row 900 (t 0.503, 128 deg) and runs
# down the forearm to row 1040 (t 0.623, 133 deg), its end beside the LEATT's top (Leatt NZ's side panel close-up
# and the front three-quarter on-model photo see the same run and end). Drawn, not traced: per path, its points
# (t along the arm, deg round it from the front, outward positive), from inside the traced line's end (t 0.42 at its
# own 161.3 deg); straight between them in t and angle. Width as the traced line's (the photos': 2 mm). It is
# drawn on the texels themselves along the arm's axis rounded over the elbow (sleeve_bent): his elbow is bent 46 deg
# and the jog lies on its point, where the unrolled raster's distance along (sleeve_unroll's, the straight segments)
# maps 4 cm of cloth twice (2 r tan 23 deg at the sleeve's 5 cm): drawn there, the jog came out twice
SLEEVE_LINE = {"L": (((0.420, 161.3), (0.463, 164.0), (0.503, 128.0), (0.623, 133.0)),
                     ((0.463, 164.0), (0.468, 171.0)))}
SLEEVE_LINE_W = 0.0030         # m, full white across (the traced line: 0.91 or more over 2 mm, half white at 3.2 mm)
SLEEVE_LINE_SOFT = 0.0012      # m, its edge's ramp (the traced line's: 0.91 to 0.2 over 1.25 mm)


def sleeve_rho(rad, along):
    """A sleeve's median radius along its arm (1 cm bins, smoothed over 5) as a function of the distance along, and
    the bins' values."""
    from scipy import ndimage
    k = np.floor(along / 0.01).astype(int)
    k -= k.min()
    med = np.array([np.median(rad[k == i]) if (k == i).any() else np.nan for i in range(k.max() + 1)])
    ok = ~np.isnan(med)
    med = np.interp(np.arange(len(med)), np.nonzero(ok)[0], med[ok])
    med = ndimage.uniform_filter1d(med, 5, mode="nearest")
    a0 = np.floor(along.min() / 0.01) * 0.01

    def rho(al):
        return np.interp((al - a0) / 0.01 - 0.5, np.arange(len(med)), med)
    return rho, med


SLEEVE_BEND_R = 0.08           # m, the arm's axis rounded over the elbow on this radius (over the sleeve's 5 to 6 cm
                               # there, so each point of it has one nearest axis point)


def sleeve_bent(body, s, P):
    """A sleeve point against the arm's axis rounded over the elbow (a circle of SLEEVE_BEND_R from the upper arm's
    segment into the forearm's): the angle round the axis (as sleeve_unroll's: from the front, his outward side
    positive), the distance from it and the distance along it from the shoulder point, the bend's arc counted as the
    length of the straight segments it replaces (outside the bend, sleeve_unroll's own)."""
    S, E, W, f, o = arm_frame(body, s)
    L1, L2 = np.linalg.norm(E - S), np.linalg.norm(W - E)
    d1, d2 = (E - S) / L1, (W - E) / L2
    beta = np.arccos(np.clip(d1 @ d2, -1.0, 1.0))
    k = SLEEVE_BEND_R * np.tan(beta / 2)
    T1, T2 = E - d1 * k, E + d2 * k
    inn = d2 - d1 * (d1 @ d2)
    inn /= np.linalg.norm(inn)                                   # toward the bend's inside, at T1
    C = T1 + inn * SLEEVE_BEND_R
    v = P - C
    phi = np.clip(np.arctan2(v @ d1, v @ -inn), 0.0, beta)       # round the bend from T1 toward T2
    a1, a2 = (P - S) @ d1, (P - T2) @ d2
    seg1, seg2 = a1 <= L1 - k, a2 >= 0
    arc = ~seg1 & ~seg2
    A = np.where(seg1[:, None], S + np.outer(a1, d1), T2 + np.outer(a2, d2))
    tau = np.where(seg1[:, None], d1, d2)
    A[arc] = C + SLEEVE_BEND_R * (np.outer(np.cos(phi[arc]), -inn) + np.outer(np.sin(phi[arc]), d1))
    tau[arc] = np.outer(np.sin(phi[arc]), inn) + np.outer(np.cos(phi[arc]), d1)
    along = np.where(seg1, a1, np.where(seg2, L1 + k + a2, L1 - k + phi / max(beta, 1e-9) * 2 * k))
    fs = np.array([0, -1.0, 0]) - tau * (-tau[:, 1:2])
    fs /= np.linalg.norm(fs, axis=1, keepdims=True)
    os_ = o - tau * (tau @ o)[:, None] - fs * (fs @ o)[:, None]
    os_ /= np.linalg.norm(os_, axis=1, keepdims=True)
    r = P - A
    return np.arctan2(np.sum(r * os_, 1), np.sum(r * fs, 1)), np.linalg.norm(r, axis=1), along


def sleeve_line_points(body, s, rho, step=0.00025):
    """SLEEVE_LINE's paths where sleeve_line_coords lays the sleeve out (x round the arm at its median radius rho, y
    along the arm; m) as points `step` apart, straight between the path's points in t and angle."""
    S, E, W, f, o = arm_frame(body, s)
    Lr = np.linalg.norm(E - S) + np.linalg.norm(W - E)
    pts = []
    for path in SLEEVE_LINE.get(s, ()):
        for (t0, a0), (t1, a1) in zip(path[:-1], path[1:]):
            n = max(int(np.hypot((t1 - t0) * Lr, np.radians(a1 - a0) * rho(t0 * Lr)) / step), 1)
            u = np.linspace(0, 1, n + 1)
            al = (t0 + u * (t1 - t0)) * Lr
            pts.append(np.stack([np.radians(a0 + u * (a1 - a0)) * rho(al), al], 1))
    return np.concatenate(pts) if pts else np.zeros((0, 2))


def sleeve_line_coords(body, s, P):
    """Sleeve points where SLEEVE_LINE is laid out: x round the arm at its median radius, y along it (m; sleeve_bent),
    and that radius as a function of the distance along."""
    ang, rad, along = sleeve_bent(body, s, P)
    rho, _ = sleeve_rho(rad, along)
    return np.stack([ang * rho(along), along], 1), rho


def sleeve_line_dist(body, s, P):
    """How far sleeve points (all of one sleeve's texels: its radius along the arm is their median) are from
    SLEEVE_LINE (m), as sleeve_print draws it."""
    xy, rho = sleeve_line_coords(body, s, P)
    d, _ = cKDTree(sleeve_line_points(body, s, rho)).query(xy)
    return d


SLEEVE_WHITE_Q = 0.02          # the sleeves' white elements only where a photo saw the texel (view weight over this)
SLEEVE_MIRROR = (0.04, 0.10)   # m along the arm from the shoulder point: the back half mirrors the front from here
                               # (above it, the raglan part's magenta fade, from the trunk's own back view)


def sleeve_print(lin, q, chm, pos, body, texel, gain, white, shapes, zlin=None, keep_out=None):
    """The flat print of both halves of each sleeve at once (decision 52, round 3): per chart, the halves' stripes
    were cut and coloured apart and stepped along the sleeve's top and underarm lines (59 and 35 of 255 at the
    median). The sleeve is unrolled about its arm onto one raster (round = angle times the sleeve's median radius
    at that distance along, wrapped past the back line), traced and cut there by flat_layers, and read back.
    zlin: the zebra's source (the traced flat, flat_sleeve_art), the white elements from `lin` (every view) except
    where keep_out(points) holds (Leatt's marks, printed from the official files: sleeve_marks).
    Returns {chart: display colours of its texels}."""
    from scipy import ndimage
    out = {}
    zlin = lin if zlin is None else zlin
    ink_black = photo_inks(FLAT_REF)["black"] * gain
    for s, base in (("L", 2), ("R", 4)):
        m = (chm == base) | (chm == base + 1)
        P = pos[m]
        ang, rad, along = sleeve_unroll(body, s, P)
        rho, med = sleeve_rho(rad, along)
        x, y = ang * rho(along), along
        tree = cKDTree(np.stack([x, y], 1))
        R = np.pi * med.max() + FP_SLEEVE_WRAP
        nx, ny = int(np.ceil(2 * R / texel)) + 1, int(np.ceil((y.max() - y.min()) / texel)) + 9
        gx = -R + np.arange(nx) * texel
        gy = y.min() - 4 * texel + np.arange(ny) * texel
        GX, GY = np.meshgrid(gx, gy)
        rr = rho(GY)
        ga = GX / rr
        ga = (ga + np.pi) % (2 * np.pi) - np.pi                       # wrapped round the arm
        inside = np.abs(GX) <= np.pi * rr + FP_SLEEVE_WRAP
        dist, idx = tree.query(np.stack([ga * rr, GY], -1).reshape(-1, 2), distance_upper_bound=2.5 * texel)
        hit = (np.isfinite(dist) & inside.ravel()).reshape(ny, nx)
        idx = np.where(hit.ravel(), idx, 0).reshape(ny, nx)
        src = np.nonzero(m)
        col = np.clip(lin[src][idx] * gain, 0, 1) * hit[..., None]
        qq = q[src][idx] * hit
        sh = shapes[src][idx] & hit
        # the white elements (his left sleeve's line and forearm LEATT, the icons) from every view, where one sees
        # them (round 3b: where none does, the photos' fill streaks read as white bars, 190 to 1730 mm2)
        _, _, aw = flat_layers(col, qq, hit, texel, white, sh & (qq > SLEEVE_WHITE_Q), **FP_SLEEVE)
        if keep_out is not None:
            aw = aw * ~(keep_out(pos[m][idx].reshape(-1, 3)).reshape(aw.shape) & hit)
        # and what is left under white_min goes (round 3b, sheet 11: the 95 mm2 end of the left LEATT's traced
        # streak outside its band, 46 deg from the front; thin grey scratches on the top line over his left elbow,
        # where the line runs on toward the icon, traced as the cut's faint fringe: ridges just under the cut, the
        # texture's white measure peaking 0.33 to 0.53)
        lab, n = ndimage.label(aw > 0.02, np.ones((3, 3)))
        if n:
            area = ndimage.sum(aw, lab, np.arange(1, n + 1)) * texel ** 2
            aw = aw * ~np.isin(lab, np.nonzero(area < FP_SLEEVE["white_min"])[0] + 1)
        # the zebra (round 3b): the traced flat (flat_sleeve_art; the back views see the sleeve's back at grazing
        # angles and their bands' phase differs from the flat's, so their stripes came out as fragments). Below the
        # raglan part the back half is the front half mirrored about the top and underarm lines (continuous there;
        # Leatt's bands wrap round the arm: an estimate where the flat does not see, checked against the back photos)
        col = np.clip(zlin[src][idx] * gain, 0, 1) * hit[..., None]
        mi = np.abs(ga) > np.pi / 2
        gm = np.where(ga > 0, np.pi - ga, -np.pi - ga)
        cxm = np.clip(np.round((gm * rr + R) / texel).astype(int), 0, nx - 1)
        cym = np.repeat(np.arange(ny)[:, None], nx, 1)
        wm = mi * smoothstep(SLEEVE_MIRROR[0], SLEEVE_MIRROR[1], GY) * hit[cym, cxm]
        cm_ = col[cym, cxm]
        dm = to_srgb(cm_)
        cm_ = np.where((dm.min(-1) - 0.6 * np.ptp(dm, -1) > 0.5)[..., None], ink_black, cm_)   # no mirrored whites
        col = col * (1 - wm[..., None]) + cm_ * wm[..., None]
        qq = qq * (1 - wm) + qq[cym, cxm] * wm
        sh = np.where(wm > 0.5, sh[cym, cxm], sh)
        # over the raglan part plain ground (the magenta fading into the black, every photo): the trunk's views there
        # carry the photo model's sleeve stripes past the seam (fragments, round 3b review). Plain, not unseen: the
        # ground keeps those views' colour, the yoke's magenta over the shoulder fading into the sleeve's black at
        # the shoulder point (Leatt US's front flat, the NZ on-model front and back). Round 3b took the shapes off
        # there instead, and its ground was filled from the black sleeve below: the shoulders' tops and the upper
        # back's corners read black, the yoke's magenta 0.52 to 0.56 of the front view's row at the shoulders where
        # the flat's is 0.99 (round 3c review, sheets 05, 06, 11)
        rag = GY <= SLEEVE_MIRROR[1]
        o, _, _ = flat_layers(col, qq, hit, texel, white, sh, whites=False, plain=rag, **FP_SLEEVE)
        o0 = np.where(hit[..., None], o, 0.0)
        o = o * (1 - aw)[..., None] + np.asarray(white) * aw[..., None]
        o = np.where(hit[..., None], o, 0.0)
        # back onto the texels: each at its own place on the raster (the cut's edge stays within a texel)
        cx, cy = (x + R) / texel, (y - gy[0]) / texel
        val = np.stack([ndimage.map_coordinates(o[..., i], [cy, cx], order=1, mode="nearest") for i in range(3)], -1)
        wgt = ndimage.map_coordinates(hit.astype(float), [cy, cx], order=1, mode="nearest")
        val = val / np.maximum(wgt, 1e-6)[:, None]
        # the forearm's cloth behind the elbow's plane (his elbows bent 46 deg) reads the upper arm's last 3.6 cm on
        # the raster: no traced whites there (round 4: the left line's traced tip came out again beside its stub)
        S_, E_ = arm_frame(body, s)[:2]
        dup = (((P - S_) @ (E_ - S_)) >= np.dot(E_ - S_, E_ - S_)) & (along < np.linalg.norm(E_ - S_))
        if dup.any():
            v0 = np.stack([ndimage.map_coordinates(o0[..., i], [cy[dup], cx[dup]], order=1, mode="nearest")
                           for i in range(3)], -1)
            val[dup] = v0 / np.maximum(wgt[dup], 1e-6)[:, None]
        # his left sleeve's line past the elbow, drawn on the texels (SLEEVE_LINE: the photos' slanted views traced
        # it as specks; the raster maps the bent elbow's back twice)
        if s in SLEEVE_LINE:
            cov = np.clip((SLEEVE_LINE_W / 2 - sleeve_line_dist(body, s, P)) / SLEEVE_LINE_SOFT + 0.5, 0, 1)
            val = val * (1 - cov[:, None]) + np.asarray(white) * cov[:, None]
        res = to_srgb(val)
        cm = chm[m]
        for c in (base, base + 1):
            out[c] = (np.nonzero(chm == c), res[cm == c])
    return out


RAGLAN_LEVEL = 0.06      # m, how far into the sleeve its colour is drawn to the trunk's at the raglan seam


def level_raglan(img, pos, chm, V, Q, chart, reach=RAGLAN_LEVEL):
    """The sleeves' ground drawn to the trunk's colour at the raglan seams (display colours in, out): the trunk takes
    its colour from further in (its photos' sleeves show past the seam), the sleeve's raglan part from the photo
    right at the shoulder, shaded where it turns away: a step along the seam (27 of 255 on the yoke beside the
    collar, and the seam's zigzag of faces drawn by it). Each seam point's step (the medians within 1 cm each side,
    in linear light, averaged over 2 cm of seam) is added to the sleeve's texels of that ink (within 0.16 of its
    median, display), fading over `reach`."""
    lin = to_lin(img)
    trunk = (chm == 0) | (chm == 1)
    sleeve = chm >= 2
    tt = cKDTree(pos[trunk])
    st = cKDTree(pos[sleeve])
    T, S_ = lin[trunk], lin[sleeve]
    pts = seam_points(V, Q, chart, {(0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5)}, step=0.005)
    d, ref, ok = np.zeros((len(pts), 3)), np.zeros((len(pts), 3)), np.zeros(len(pts), bool)
    for i, p in enumerate(pts):
        a, b = tt.query_ball_point(p, 0.01), st.query_ball_point(p, 0.01)
        if len(a) >= 5 and len(b) >= 5:
            ref[i] = np.median(S_[b], 0)
            d[i] = np.median(T[a], 0) - ref[i]
            ok[i] = True
    pts, d, ref = pts[ok], d[ok], ref[ok]
    pt = cKDTree(pts)
    nb = pt.query_ball_point(pts, 0.02)
    d = np.array([d[j].mean(0) for j in nb])
    ref = np.array([ref[j].mean(0) for j in nb])
    dist, k = pt.query(pos[sleeve])
    fade = 1 - smoothstep(0.0, reach, dist)
    sim = np.clip(1 - np.abs(to_srgb(S_) - to_srgb(ref[k])).max(1) / 0.16, 0, 1)
    out = lin.copy()
    out[sleeve] = np.clip(S_ + d[k] * (fade * sim)[:, None], 0, 1)
    return to_srgb(out)


# ================================================================ graphics: stamps and Damien's additions
def leatt_icon(up=8):
    """Leatt's three-piece triangle from its official file (reference/leatt-gear: us.leatt.com's favicon, 100 px),
    the registered sign dropped, upsampled `up` times and re-thresholded (straight edges, round corners), cropped."""
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(os.path.join(REF, "leatt-icon-triangle_official-favicon_leatt-us_100x100.png"))
                   .convert("RGBA"))[..., 3].astype(np.float32) / 255
    lab, n = ndimage.label(a > 0.5)
    sizes = ndimage.sum(a > 0.5, lab, range(1, n + 1))
    a = a * ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(sizes > 500)[0]), iterations=2)
    a = ndimage.gaussian_filter(np.where(ndimage.zoom(a, up, order=3) > 0.5, 1.0, 0.0), up * 0.35)
    ys, xs = np.nonzero(a > 0.5)
    return np.ascontiguousarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]).astype(np.float32)


def official_wordmark():
    """Leatt's slanted LEATT from its official file (reference/leatt-gear, README: us.leatt.com's header logo) as an
    alpha mask cropped to the letters (646 x 161 px: 4.0 long per height)."""
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(REF, "leatt-wordmark-slanted_official_leatt-us_1200x300.png"))
                   .convert("RGBA"))[..., 3].astype(float) / 255
    ys, xs = np.nonzero(a > 0.5)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


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
INK_WHITE, INK_DARK_06 = (246, 245, 250), (34, 24, 44)   # PHOTO 06: white digits, dark purple-grey outline
# the outline is a dark ink on the black ground: it moves as the black does (phase B, INK_FACTORS, x 2.76 in linear
# light) and keeps its place against it, lighter and purple, 1.35 times the ground's luminance as in PHOTO 06
# (through ink_palette it would take the black's lift as a sum, 49, 43, 59: 1.13 times): 59, 44, 75
INK_DARK = tuple(int(round(float(v) * 255))
                 for v in to_srgb(to_lin(np.array(INK_DARK_06) / 255) * np.array(INK_FACTORS["black"])))
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
         "motul": (-0.057, 1.286, 0.064), "cworx": (0.064, 1.313, 0.077),
         # Leatt's triangle icon beside the chest LEATT (Leatt's print, laid with the patches so it prints at 0.1 mm:
         # its 3 mm strokes do not survive the flat print's trace of the photo at 0.8 mm). PHOTO NZ front on-model:
         # white ink x 984-1019, y 457-488 px: centre (0.133, 1.423) in the photo's frame, 24.4 mm across, times
         # 1.137 where the chest turns (the frame's stretch there, BODY: normal (0.44, -0.81, 0.39)): 27.7 mm;
         # Leatt US's front flat sees it square on: 37 x 38 px (the favicon's aspect, 1.0) beside a 395 px LEATT,
         # 0.094 of the LEATT's 0.275 m on him: 25.8 mm; the geometric mean, 26.7 mm. Its stroke is 0.14 of its
         # width as the official favicon's 0.13 (distance transform), so the favicon is the printed art
         "icon": (0.133, 1.423, 0.0267),
         # Leatt's FIVE.FIVE under the yoke (round 3b: traced at 0.8 mm a texel its 2 mm strokes read as dots).
         # PHOTO NZ front on-model: the letters' ink x 717 to 897, rows 626 to 637 (centre 807, 631; the yoke's edge
         # at row 612 above it): (0.005, 1.343) in the photo's frame. Width from Leatt US's front flat, which sees it
         # square on: ink 184 px beside the 395 px chest LEATT, 0.466 of its 0.275 m: 0.1281 m (cap height 11.5 px:
         # 8.0 mm) (FIVEFIVE)
         "fivefive": (0.005, 1.343, 0.1281)}
# FIVE.FIVE's letters in Leatt US's front flat (PHOTO, 1920 px; light ink over 0.45 on the black band): each
# glyph's ink centre (x, px), the ink's span and the cap height; the typeface is not resolved by the photo (11 px
# capitals): Inter SemiBold stands in (an estimate: its F, V and E are 0.55, 0.73 and 0.6 of the cap height wide
# as the photo's 6, 8 and 6.5 px, its stem 0.16 as the photo's 2 px)
FIVEFIVE = {"text": "FIVE.FIVE", "x": (986.5, 1008.5, 1028.5, 1052.5, 1074.5, 1095.5, 1118.0, 1140.5, 1165.0),
            "span": (984.0, 1168.0), "cap": 11.5,
            "font": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"}
FIVEFIVE_PHOTO = (705, 617, 910, 645)   # px in the NZ front on-model photo: FIVE.FIVE's box, erased from the trace
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


def fivefive_art():
    """FIVE.FIVE (FIVEFIVE): each glyph at its measured centre on a common baseline, white ink; premultiplied RGBA
    cropped to the ink's span across (FRONT's width: the F's left to the E's right)."""
    from PIL import Image, ImageDraw, ImageFont
    cap = 160                                                  # art px of the cap height
    k = cap / FIVEFIVE["cap"]                                  # art px per flat px
    f = ImageFont.truetype(FIVEFIVE["font"], int(round(cap / 0.727)))   # Inter's cap height: 0.727 em
    x0, x1 = FIVEFIVE["span"]
    pad = int(cap * 0.3)
    W, H = int(round((x1 - x0) * k)) + 2 * pad, cap + 2 * pad
    m = np.zeros((H, W), np.float32)
    for ch, xc in zip(FIVEFIVE["text"], FIVEFIVE["x"]):
        g = Image.new("L", (2 * cap, 2 * cap), 0)
        ImageDraw.Draw(g).text((cap // 2, cap + cap // 2), ch, font=f, fill=255, anchor="ls")
        a = np.asarray(g).astype(np.float32) / 255
        ys, xs = np.nonzero(a > 0.5)
        cx = (xs.min() + xs.max()) / 2
        dx = int(round(pad + (xc - x0) * k - cx))
        dy = (pad + cap) - (cap + cap // 2)                     # the baseline at the cap's foot
        ya, yb = max(0, -dy), min(a.shape[0], H - dy)
        xa, xb = max(0, -dx), min(a.shape[1], W - dx)
        m[ya + dy:yb + dy, xa + dx:xb + dx] = np.maximum(m[ya + dy:yb + dy, xa + dx:xb + dx], a[ya:yb, xa:xb])
    rgba = np.dstack([np.array(INK_WHITE, np.float32) / 255 * m[..., None], m]).astype(np.float32)
    xs = np.nonzero((m > 0.02).any(0))[0]
    return rgba[:, xs.min():xs.max() + 1]


def erase_light(photo, box, thr=0.45, dark=0.35, sigma=4):
    """Fill the light marks (min channel over thr) in a box of a photo from the dark print round them."""
    from scipy import ndimage
    u0, v0, u1, v1 = box
    a = photo.a
    m = np.zeros(a.shape[:2], bool)
    m[v0:v1, u0:u1] = a[v0:v1, u0:u1].min(2) > thr
    m = ndimage.binary_dilation(m, iterations=3)
    keep = (~m & (a.max(2) < dark)).astype(float)
    num = np.stack([ndimage.gaussian_filter(a[..., k] * keep, sigma) for k in range(3)], 2)
    den = ndimage.gaussian_filter(keep, sigma)[..., None]
    a[m] = (num / np.maximum(den, 1e-6))[m]


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
    # Leatt's icon: the official favicon's three pieces (the registered sign dropped), white ink
    m = leatt_icon()
    arts["icon"] = np.dstack([np.array(INK_WHITE, np.float32) / 255 * m[..., None], m]).astype(np.float32)
    arts["fivefive"] = fivefive_art()
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
    owner, depth = np.full(len(Q), -1), np.full(len(Q), -np.inf)
    for j, pr in enumerate(prints):
        s, t, ok = pr.st(c.reshape(-1, 3), N[Q].reshape(-1, 3))
        hit = (ok & pr.inside(s, t, margin)).reshape(-1, 4).any(1)
        texel = np.where(hit, np.minimum(texel, pr.texel), texel)
        sc, tc, _ = pr.st(c.mean(1), N[Q].mean(1))
        d = np.minimum(pr.art.w / 2 - np.abs(sc), pr.art.h / 2 - np.abs(tc))   # the face's centre inside its box
        better = hit & (d > depth)
        owner, depth = np.where(better, j, owner), np.where(better, d, depth)
    F = np.nonzero(np.isfinite(texel))[0]
    # islands: faces of one chart and one print (the one whose box the face's centre lies deepest in) joined by
    # shared vertices (round 3b: one island per print, so each takes its own texel and the islands pack closer;
    # FIVE.FIVE had joined the chest's USN and Cycleworx into one 0.30 m island: 0.192 mm a texel against 0.166)
    inc = sparse.coo_matrix((np.ones(4 * len(F)), (np.repeat(np.arange(len(F)), 4), Q[F].ravel())),
                            (len(F), len(V))).tocsr()
    adj = (inc @ inc.T).tocoo()
    same = (chart[F][adj.row] == chart[F][adj.col]) & (owner[F][adj.row] == owner[F][adj.col])
    g = sparse.coo_matrix((np.ones(same.sum()), (adj.row[same], adj.col[same])), (len(F), len(F)))
    n_isl, lab = connected_components(g, directed=False)
    isl = []
    for i in range(n_isl):
        f = F[lab == i]
        uv = UV[f].reshape(-1, 2)
        lo, hi = uv.min(0), uv.max(0)
        k = 1.0 / (scale * texel[f].min())               # atlas px per jersey-UV unit (scale: UV units per metre)
        isl.append([lo, hi, k, f])
    # skyline packing into the atlas (shrink every island together until they fit; round 3's shelves: 0.60 of
    # PRINT_TEXEL where the skyline reaches 0.61)
    shrink = 1.0
    while True:
        org = skyline_pack([(hi - lo) * k * shrink for lo, hi, k, _ in isl], ATLAS_RES, pad=6)
        if org is not None:
            break
        shrink *= 0.98
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


def skyline_pack(sizes, res, pad):
    """Rectangles (w, h in px) into a res square, tallest first, each at the lowest then leftmost place on the
    skyline (the packed tops' outline) where it fits. Returns {index: (x, y) of its origin inside its pad} or None."""
    order = sorted(range(len(sizes)), key=lambda i: (-sizes[i][1], -sizes[i][0]))
    sky = [[0, 0, res]]                                   # segments: x, top, width
    org = {}
    for i in order:
        w, h = (int(np.ceil(v)) + 2 * pad for v in sizes[i])
        best = None
        for x, _, _ in sky:
            if x + w <= res:
                y = max(sy for sx, sy, sw in sky if sx < x + w and sx + sw > x)
                if y + h <= res and (best is None or (y, x) < best):
                    best = (y, x)
        if best is None:
            return None
        y, x = best
        org[i] = (x + pad, y + pad)
        new = [[x, y + h, w]]
        for sx, sy, sw in sky:
            if sx < x:
                new.append([sx, sy, min(sw, x - sx)])
            if sx + sw > x + w:
                new.append([max(sx, x + w), sy, sx + sw - max(sx, x + w)])
        new.sort()
        sky = [new[0]]
        for seg in new[1:]:
            if seg[1] == sky[-1][1] and sky[-1][0] + sky[-1][2] == seg[0]:
                sky[-1][2] += seg[2]
            else:
                sky.append(seg)
    return org


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


# The lower back's perforations (round 3c, fix 3: his 06 leads; Damien not asked back yet, so still an estimate).
# His 06 at 1:1, each strong dot mapped through the camera fitted on the 114 (cam06) onto the posed jersey and back
# to the rest pose: a rectangular grid (not staggered), 4 rows 13.7 mm apart (z 1.154 to 1.195 at the middle; the
# review's "about 5" counts 4 here), columns 19.4 mm apart, seen from x -0.136 to 0.116 (taken as +-0.136: 15 a
# row). Leatt NZ's back three-quarter flat shows the same field: 4 rows 26.7 px apart (11.9 mm) in a rectangular
# grid (the same x in each row), holes 5 to 7 px across (2 to 3 mm), dark there (nothing under them). Each 06 dot's
# light over the black, summed over 3x3 px, is 1.17 px^2 of the 114's white (R 0.82, G 1.19, B 1.26: cooler than
# the white; 2.9 mm a photo px there: about 10 mm^2 of white); round 3b's 1.8 mm dots in (146, 165, 197) give
# 0.9 mm^2, faint specks. So the holes show a light base layer in the 06 dots' colour against the white (0.65, 0.94,
# 1.0 of INK_WHITE, linear) over r 1.8 mm: bigger than the flat's holes, which 06 cannot resolve (its dots blur
# over 3x3 px); the light through them is what it measures. The same measure on a daylight render of the 06 window
# (kit.md, Round 3c; the window's camera is re-aimed, so each frame is measured on its own): 1.19 px^2 at r 1.9 mm
# against the photo's 1.09, so r 1.8 mm (measured: 1.08)
LB_HOLES = {"z_top": 1.195, "rows": 4, "dz": 0.0137, "pitch": 0.0194, "half_width": 0.136, "r": 0.0018,
            "tone": (203, 238, 250)}


def lower_back_holes(P, N):
    """The lower back's hole centres (LB_HOLES): a rectangular grid on the back-facing cloth points P."""
    back = (N[:, 1] > 0.3) & (np.abs(P[:, 0]) < LB_HOLES["half_width"] + 0.02)
    Q = P[back]
    tree = cKDTree(Q[:, [0, 2]])
    C = []
    for k in range(LB_HOLES["rows"]):
        z = LB_HOLES["z_top"] - k * LB_HOLES["dz"]
        for x in np.arange(-LB_HOLES["half_width"], LB_HOLES["half_width"] + 1e-9, LB_HOLES["pitch"]):
            d, i = tree.query([x, z])
            if d < 0.003:
                C.append(Q[i])
    return np.array(C)


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
    """The Tiger Pink print on the jersey's charts, as flat artwork (decision 52): Leatt's photos give the shapes
    (front and back panels from the NZ on-model views, mapped onto the flat's inks; each sleeve's front from Leatt
    US's front flat, its back from the back views; the side panels from the back three-quarter flat), each texel
    weighted by how squarely its photo saw it; flat_print traces the stripes and white elements, cuts them crisp and
    fills each ink's colour field. Then Damien's additions (`prints`); the relief: raglan, side and underarm seams,
    238 laser-cut holes, riding folds. Returns the hole count and the print-free colour, the holes' darkening and
    the normal map (for the print overlay)."""
    pos, nrm, chm = raster(UV, V, N, Q, chart)
    mask = chm >= 0
    img = np.zeros(pos.shape)                                  # linear, on the front flat's inks
    q = np.zeros(pos.shape[:2])                                # how squarely the photo saw each texel
    nz = ink_map(JF_REF)                                       # the NZ distributor's photos onto the flat's inks
    pf = Photo(JF_REF, exclude=[(560, 0, 1060, 345), (160, 1290, 470, 1600), (1130, 1290, 1440, 1600)], inks=nz)
    pb = Photo(JB_REF, exclude=[(600, 0, 1000, 266), (900, 60, 1120, 330), (120, 1330, 420, 1600),
                                (1180, 1330, 1460, 1600)], inks=back_map(nz))   # the back photo is brighter
    pl = Photo(FLAT_REF, median=3)                             # the flat itself: the sleeves' fronts
    white = to_lin(np.array(INK_WHITE) / 255)
    gain = white.mean() / photo_inks(FLAT_REF)["white"].mean()
    plz = flat_sleeve_art(gain, white)                         # and its sleeves' zebra, traced (round 3b)
    ps = Photo(SIDE_REF, inks=nz)                              # the back three-quarter flat: the side panels
    if prints:
        erase_back_logo(pb)                                  # his name is printed there instead (Damien's additions)
        erase_light(pf, FIVEFIVE_PHOTO)                      # printed sharper with the prints (round 3b)
    for c, view in ((0, "front"), (1, "back")):
        m = chm == c
        Pm = pos[m].copy()
        Pm[:, 2] -= np.clip(0.02 - neck_cut(Pm), 0, None)
        u, v = jersey_photo_uv(body, Pm, view)
        ph = pf if view == "front" else pb
        img[m] = ph.lin(u, v)
        q[m] = np.clip(nrm[m][:, 1] * (-1 if view == "front" else 1), 0, 1) * ph.seen(u, v) * torso_seen(u, v, view)
    # the sleeves: the front half from Leatt US's front flat (the whole sleeve square on, evenly lit; the on-model
    # photos see the arms turned and shaded), the back half from the back on-model photo, the raglan part over the
    # shoulder from the trunk's views; blended over the sleeve's top and underarm lines
    zimg = np.zeros(pos.shape)
    for s, base in (("L", 2), ("R", 4)):
        m = (chm == base) | (chm == base + 1)
        P = pos[m]
        cosf, fseg = arm_facing(body, s, P)
        wf = smoothstep(-0.15, 0.15, cosf)                    # a narrow blend: the two photos' stripes differ
        uf, vf, t = sleeve_photo_uv(body, P, s, "flat")
        bview, pbk = ("b34", ps) if s == "L" else ("back", pb)   # his left sleeve's back: the back 3/4 flat
        ub, vb, _ = sleeve_photo_uv(body, P, s, bview)
        ws = smoothstep(0.02, 0.14, t)[:, None]               # the raglan part over the shoulder: the trunk's views
        uF, vF = jersey_photo_uv(body, P, "front")
        uB, vB = jersey_photo_uv(body, P, "back")
        cf = pl.lin(uf, vf) * ws + pf.lin(uF, vF) * (1 - ws)
        cb = pbk.lin(ub, vb) * ws + pb.lin(uB, vB) * (1 - ws)
        img[m] = cf * wf[:, None] + cb * (1 - wf[:, None])
        # the zebra's source: below the raglan part the traced flat all round (sleeve_print mirrors its back half)
        wz = (1 - (1 - wf[:, None]) * (1 - ws))
        uz, vz, _ = sleeve_photo_uv(body, P, s, "flat", photo_s=SLEEVE_ZEBRA_FROM[s], phase=SLEEVE_PHASE.get(s))
        zimg[m] = (plz.lin(uz, vz) * ws + pf.lin(uF, vF) * (1 - ws)) * wz + cb * (1 - wz)
        nf = (nrm[m] * fseg).sum(1)                          # the photos see the hanging arm square to its front
        ws = ws[:, 0]
        sf = pl.seen(uf, vf) * ws + pf.seen(uF, vF) * (1 - ws)
        sb = pbk.seen(ub, vb) * ws + pb.seen(uB, vB) * (1 - ws)
        q[m] = wf * np.clip(nf, 0, 1) * sf + (1 - wf) * np.clip(-nf, 0, 1) * sb
    # the trunk's views near the raglan seams: the photo's model and his differ by a few cm there, so the photos'
    # sleeves show past the seam (their stripes read as blotches on his upper back): no shapes from the trunk's
    # photos within 3.5 cm of the seam above the armpit, its colour from further in
    shapes = mask.copy()
    trunk = (chm == 0) | (chm == 1)
    P = pos[trunk]
    r = np.maximum(raglan(body, P, 1), raglan(body, P, -1))
    hi = P[:, 2] > RAGLAN_PIT[2] - 0.01
    q[trunk] *= np.where(hi, smoothstep(-0.005, -0.035, r), 1.0)
    # and the trunk's sides: past 75 deg the photos' shapes are smears
    shapes[trunk] = ((q[trunk] > 0.02) | ~hi) & (q[trunk] > 0.25)
    # the side panels (the mesh under the arms): Leatt's back three-quarter flat sees his left one square on, with
    # no arm over it; the right one is its mirror image
    side = side_panel(pos) & trunk
    u, v = side_photo_uv(pos[side])
    img[side] = ps.lin(u, v)
    q[side] = ps.seen(u, v)
    shapes[side] = True
    # the clean flat print (decision 52): shapes traced, inks on the front flat's
    texel = 1.0 / (scale * TEX_RES)
    src = img
    bx, bz0, bz1 = FP_FADE["box"]
    sw = FP_FADE["soft"]
    z = pos[..., 2]
    fade = ((chm == 0) * smoothstep(bx, bx - sw, np.abs(pos[..., 0])) * smoothstep(bz0 - sw / 2, bz0 + sw / 2, z)
            * smoothstep(bz1 + sw / 2, bz1 - sw / 2, z))
    # the back panel is plain, its magenta fading into the black (PHOTO back on-model, back three-quarter flat):
    # the zebra at the back's flanks in the back views is the side panels', seen at a slant (round 3b: traced on the
    # back chart past the panels' seams, it came out as lime and teal fragments, sheets 01, 06 and 09)
    plain = (chm == 1) & ~side
    hem = ((chm == 0) * smoothstep(FP_HEM["z"][1], FP_HEM["z"][0], z)
           * smoothstep(FP_HEM["x"][0], FP_HEM["x"][1], np.abs(pos[..., 0])))
    img = flat_print(src, q, chm, (0, 1), texel, gain, white, shapes, opts={1: FP_BACK}, fade=fade, plain=plain,
                     smooth=(hem, FP_HEM["feature"]))
    marks = sleeve_marks(body, pos, nrm, chm)
    keep = lambda P: np.any([mk["keep"](P) for mk in marks], 0)   # noqa: E731
    for c, (ix, v) in sleeve_print(src, q, chm, pos, body, texel, gain, white, shapes, zimg, keep).items():
        img[ix] = v                                            # each sleeve's halves as one print
    us, vs = side_photo_uv(pos[side])
    img[side] = to_srgb(side_panel_art(ps, nz, gain, white)(us, vs))   # the side panels' own trace (round 3b)
    img = level_raglan(img, pos, chm, V, Q, chart)
    for mk in marks:                                           # Leatt's sleeve marks, from the official files
        img = mk["canvas"].apply(img, pos, mk["zone"])
    # the inks' palette (phase B, decision 61): Leatt's print and marks, not Damien's additions laid next
    img[mask] = ink_palette(img[mask])
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
    lb = lower_back_holes(P, Nn)
    C = np.concatenate(holes + [lb])
    hp, dark = perforations(pos, mask, np.concatenate(holes))
    h += hp
    img *= dark[..., None]
    hp, _ = perforations(pos, mask, lb, r=LB_HOLES["r"])
    h += hp
    # what shows through the lower back's holes: a light base layer (his 06), not the dark of the others
    d, _ = cKDTree(lb).query(pos[mask])
    inside = np.zeros(pos.shape[:2])
    inside[mask] = smoothstep(LB_HOLES["r"] * 1.3, LB_HOLES["r"] * 0.7, d)
    img = img * (1 - inside[..., None]) + np.array(LB_HOLES["tone"]) / 255 * inside[..., None]   # display
    dark = np.where(inside > 0, 1.0, dark)
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
    """The pant's print, as flat artwork (decision 52): Leatt US's on-model front and back photos give the shapes
    leg by leg, each photo row's pant silhouette laid onto his pant's silhouette at the matching height (waist top,
    crotch, boot top rows); flat_print cuts the black zebra over the teal, lime and magenta crisp; the big LEATT on
    the left thigh from Leatt's official wordmark file. Relief:
    centre, in- and outseams, the I.K.S panels' and the rear yoke's seams, the waistband's stitching, 250
    laser-cut holes, the creases riding puts behind the knees and across the hips."""
    pos, nrm, chm = raster(UV, V, N, Q, chart)
    mask = chm >= 0
    img = np.zeros(pos.shape)
    # Leatt US's photos, as the jersey's front flat: their lime and black are the flat's within 5 levels (ledger
    # "Round 3"), so no ink map
    pf = Photo(PF_REF)                                    # the Waistlock and the jersey over it: PF_HIDDEN
    pb = Photo(PB_REF)
    crotch = V[np.abs(V[:, 0]) < 0.01][:, 2].min()
    sil = pant_silhouette(V, crotch, Q)
    white = to_lin(np.array(INK_WHITE) / 255)
    gain = white.mean() / photo_inks(FLAT_REF)["white"].mean()
    # the clean flat print (decision 52), traced on each photo itself (round 3b, FP_PANT_PHOTO); both photos' prints
    # everywhere, each half taking its own photo's but round the outer sides, where they meet along the line where
    # they agree (round 4: PANT_SEAM_SPAN)
    P, ch = pos[mask], chm[mask]
    zeb, wa = {}, {}
    for view, ph, rows, hid in (("front", pf, PF_ROWS, PF_HIDDEN), ("back", pb, PB_ROWS, ())):
        art, wa[view] = pant_photo_art(ph, rows, gain, white, hid, PANT_FADE_ROWS[view])
        zeb[view] = art(*pant_photo_uv(pants, P, view, ph.alpha, sil))
    wb = pant_seam_weight(pants, P, ch, zeb["front"], zeb["back"])[:, None]
    col = zeb["front"] * (1 - wb) + zeb["back"] * wb
    for cs, view, ph in (((0, 2), "front", pf), ((1, 3), "back", pb)):
        m = np.isin(ch, cs)
        un, v = pant_photo_uv(pants, P[m], view, ph.alpha, sil, mirror=False)   # white elements: never mirrored
        a = np.clip(wa[view](un, v)[:, :1], 0, 1) * (wb[m] if view == "back" else 1 - wb[m])   # where its print is
        col[m] = col[m] * (1 - a) + white * a
    img[mask] = to_srgb(col)
    # the big LEATT on the outer left thigh, printed flat from a view square to it (PHOTO: Leatt front on-model,
    # front three-quarter and back flat): reading up from the knee, letter tops to the front. The photo's own,
    # stretched over the side, is taken out first (its white and a 2 mm rim to the black ink: the print fills it)
    K = body.j("lowerleg01.L")
    zc = K[2] + THIGH_LOGO[0]
    ring = (V[:, 0] > 0.02) & (np.abs(V[:, 2] - zc) < 0.01)
    C = np.array([(V[ring, 0].min() + V[ring, 0].max()) / 2, (V[ring, 1].min() + V[ring, 1].max()) / 2, zc])
    t = np.radians(THIGH_LOGO[1])
    d = np.array([np.cos(t), -np.sin(t), 0.0])                     # out from the thigh's centre, to the logo
    side = Canvas(C + 0.4 * d, (np.sin(t), np.cos(t), 0.0), (0, 0, 1), 0.2, 0.40)
    side.stamp(official_wordmark(), 0.0, 0.0, THIGH_LOGO[2], rot=90, color=INK_WHITE)
    zone = mask & (pos[..., 0] > 0.02) & (((pos - C) @ d) > 0) & ((nrm @ d) > 0.2) & \
        (np.abs(pos[..., 2] - zc) < THIGH_LOGO[2] / 2 + 0.04)
    c = img
    whiteish = (c.min(-1) > 0.5) & (c.max(-1) - c.min(-1) < 0.25) & zone
    from scipy import ndimage
    whiteish = ndimage.binary_dilation(whiteish, iterations=max(1, int(round(0.002 * scale * TEX_RES)))) & zone
    img[whiteish] = np.array([18, 17, 20]) / 255                  # the pant's black (PHOTO, ledger "Round 3")
    img = side.apply(img, pos, zone)
    iks = mask.copy()
    iks[mask] = iks_field(pants, body, pos[mask]) > 0
    img[iks] = (0.085, 0.085, 0.09)                                  # the black I.K.S panels
    # the inks' palette (phase B, decision 61), the texels under the panels too: the print's faces filter them at the
    # panels' edges (the panels themselves are pant_iks)
    img[mask] = ink_palette(img[mask])
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


# Materials (ledger "Materials"): sublimated polyester knit; the breathable mesh side panels rougher. The prints'
# grey layer (phase B, decision 61; research/scene-look.md "The kit's inks (phase B)"): sheen 0 and Specular IOR
# Level 0.25 (half the default's reflection), fitted with the inks' palette (INK_FACTORS) to Leatt's flats under
# Standard and his photos at PHOTO_EV: main's sheen and full specular put a grey veil over the magenta (green 0.048 of
# the white under Standard against the flat's 0.004; 54 to 74 of 255 in his photos against 5 to 21); the I.K.S panels black leather and ripstop (a fine relief); the Waistlock's Hypalon-rubber
# strap, its textile tab, the moulded plastic buckle.
MATERIALS = {
    "jersey_print": {"image": "jersey_color.png", "normal": "jersey_normal.png", "rough": 0.58, "sheen": 0.0,
                     "spec": 0.25},
    "jersey_mesh": {"image": "jersey_color.png", "normal": "jersey_normal.png", "rough": 0.74, "sheen": 0.0,
                    "spec": 0.25},
    # the print overlay over Damien's additions: the same cloth, its own sharper atlas
    "jersey_print_hd": {"image": "jersey_print_color.png", "normal": "jersey_print_normal.png", "rough": 0.58,
                        "sheen": 0.0, "spec": 0.25},
    "jersey_print_hd_mesh": {"image": "jersey_print_color.png", "normal": "jersey_print_normal.png", "rough": 0.74,
                             "sheen": 0.0, "spec": 0.25},
    "pant_print": {"image": "pants_color.png", "normal": "pants_normal.png", "rough": 0.56, "sheen": 0.0,
                   "spec": 0.25},
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


# ---------------------------------------------------------------- one build, one result (decision 61)
# OpenBLAS splits a dot product over 10,000 long across its threads and adds the parts, so the sum's last bits
# depend on the thread count (OMP_NUM_THREADS, OPENBLAS_NUM_THREADS; by default the CPUs). scipy's lsqr takes such
# dots (np.linalg.norm) in lscm on the jersey's front chart: its UVs moved by an ulp, every chart's place with them,
# and jersey_color.png's texels by up to 2.5e-5 of a level before the cast (4.07 of its 4.19 million texels). 12 of
# its values lie within 1e-6 of a rounding boundary, so a rule at the cast cannot hold them: on 2 threads texel
# [725, 1753]'s blue came out 120.99999999 + 0.5 (120) against 121.00000016 on 4 (121; 1 thread 121.00000074). The
# build runs on one BLAS thread (blas_threads), whatever the environment says: the same bytes on every run with this
# numpy and scipy (another CPU can take other OpenBLAS kernels). Another BLAS (MKL, Accelerate) is not pinned:
# test_kit_rider's rebuild on another thread count catches it.

def _openblas():
    """The OpenBLAS libraries this process has loaded (numpy's and scipy's wheels each bundle one), as (get, set)
    ctypes functions of their thread count; none on another BLAS or without /proc."""
    import ctypes
    try:
        with open("/proc/self/maps") as f:
            paths = sorted({ln.split()[-1] for ln in f if "openblas" in ln.lower() and "/" in ln})
    except OSError:
        return []
    out = []
    for p in paths:
        try:
            lib = ctypes.CDLL(p)
        except OSError:
            continue
        for pre, suf in (("scipy_openblas", "64_"), ("scipy_openblas", ""), ("openblas", "64_"), ("openblas", "")):
            get, put = (getattr(lib, "%s_%s_num_threads%s" % (pre, k, suf), None) for k in ("get", "set"))
            if get is not None and put is not None:
                get.restype, put.argtypes = ctypes.c_int, [ctypes.c_int]
                out.append((get, put))
                break
    return out


class blas_threads:
    """with blas_threads(1): ... runs the block on n BLAS threads (every OpenBLAS loaded), then restores them."""

    def __init__(self, n=1):
        self.n, self.libs, self.was = n, [], []

    def __enter__(self):
        self.libs = _openblas()
        self.was = [get() for get, _ in self.libs]
        for _, put in self.libs:
            put(self.n)
        return len(self.libs)

    def __exit__(self, *exc):
        for (_, put), n in zip(self.libs, self.was):
            put(n)
        return False


def main(body_path, out_path, tex=True, tex_dir=None):
    """The kit's gear file (out_path) and, with tex, its textures into tex_dir (default textures/rider), on one BLAS
    thread (blas_threads: the same bytes whatever the thread count)."""
    with blas_threads(1):
        return build_kit(body_path, out_path, tex, tex_dir or TEXDIR)


def build_kit(body_path, out_path, tex, tex_dir):
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
        os.makedirs(tex_dir, exist_ok=True)
        nj, jinfo = paint_jersey(body, jersey["V"], jN, jersey["Q"], jc, jUV, jscale, tex_dir, prints)
        npn = paint_pants(body, pants, pants["V"], vnormals(pants["V"], pants["Q"]), pants["Q"], pc, pUV, pscale,
                          tex_dir)
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
    F, auv, fis, islands, shrink = print_overlay(jersey["V"], jN, jersey["Q"], jc, jUV, jscale, prints)
    print(f"print atlas: the front's prints at {PRINT_TEXEL['front'] / shrink * 1000:.3f} mm a texel")
    if tex:
        paint_print_atlas(jersey["V"], jN, jersey["Q"], F, auv, fis, islands, jscale, prints, jinfo["base"],
                          jinfo["dark"], jinfo["nm"], tex_dir)
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
    a = sys.argv
    main(a[1], a[2], "--no-tex" not in a, a[a.index("--tex-dir") + 1] if "--tex-dir" in a else None)
