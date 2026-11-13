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
BODY_WAIST_BAND = 0.903   # m, BODY: girth under the modelled waistband (front 1.05, back 1.115; test)
BODY_INSEAM = 0.872       # m, BODY: crotch height
JERSEY_SIZE = "L"         # CHART: arm length 80-82 (his 0.80), height 178-182 (his 1.85); chest 106-112 (his 101,
                          # which alone says S/M: L keeps the sleeves and body long enough for 1.85 m)
JERSEY_CHEST = 1.12       # m, CHART top of L's chest range: a race fit stretches to it, so the garment girth
PANT_SIZE = "XL / US36"   # CHART: waist 88-93 (his 88.4 at belt height, 90.3 under the band), height 180-185 (his
                          # 185), inseam 83-85 (his 87: the cuff ends inside the boot, so it does not show)
PANT_WAIST = 0.93         # m, CHART top of XL's waist range (the Waistlock ratchet closes it on him)

# ---------------------------------------------------------------- cut lines (ledger: "Cut lines")
NECK_FRONT, NECK_SIDE, NECK_BACK = 1.515, 1.575, 1.565   # z of the "no-collar" neckline: front at the jugular
                                                         # notch (BODY 1.52), sides at the neck root, back below C7
NECK_AXIS = (0.0, -0.015)                                # x, y of the neck's axis (BODY)
CUFF_BACK = 0.012         # m, sleeve ends this far up the forearm from the wrist joint (PHOTO: glove cuff over it)
HEM_Z = 0.95              # m, the jersey's straight hem (tucked: 10 cm inside the pant at the front, PHOTO 07)
WAIST_FRONT, WAIST_BACK = 1.05, 1.115   # m, pant top: front at the iliac crest, the rear yoke higher (PHOTO)
PANT_CUFF_Z = 0.30        # m, mid-calf: halfway from knee joint (0.532) to ankle joint (0.077) (BODY, brief)

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
    A2 = np.abs(np.cross(t2[:, 1] - t2[:, 0], t2[:, 2] - t2[:, 0])).sum() / 2
    uv *= np.sqrt(A3 / A2)
    g = np.linalg.lstsq(np.c_[uv - uv.mean(0), np.ones(n)], V[:, 2], rcond=None)[0][:2]
    ang = np.arctan2(g[1], g[0]) - np.pi / 2
    R = np.array([[np.cos(-ang), -np.sin(-ang)], [np.sin(-ang), np.cos(-ang)]])
    uv = (uv - uv.mean(0)) @ R.T
    # keep orientation (not mirrored): the chart's normal side faces the viewer
    t2 = uv[T]
    if (np.cross(t2[:, 1] - t2[:, 0], t2[:, 2] - t2[:, 0]) < 0).sum() > len(T) / 2:
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


def hidden_skin(body, parts, rings=1):
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


MATERIALS = {
    "jersey_print": {"rgb": [40, 38, 46], "rough": 0.62, "sheen": 0.35},
    "pant_print": {"rgb": [40, 38, 46], "rough": 0.6, "sheen": 0.3},
    "pant_iks": {"rgb": [22, 22, 24], "rough": 0.5, "sheen": 0.1, "bump": 0.15, "bump_scale": 900.0},
    "strap": {"rgb": [18, 18, 19], "rough": 0.55},
    "strap_tab": {"rgb": [20, 20, 22], "rough": 0.8, "sheen": 0.2},
    "buckle": {"rgb": [16, 16, 17], "rough": 0.35, "coat": 0.1},
}


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
    names = ["jersey", "pants"]
    out = {"mats": np.array(mats), "materials": json.dumps(MATERIALS)}
    out.update(to_part("jersey", jV, jQ, np.full(len(jQ), mats.index("jersey_print")), jW))
    out.update(to_part("pants", pV, pQ, pM, pW))
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
