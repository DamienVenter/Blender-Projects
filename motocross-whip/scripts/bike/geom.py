"""Small mesh toolkit (numpy only) used to build the bike's parts outside Blender.

A Mesh holds vertices (n, 3) in metres (bike frame: x forward, y left, z up, origin on the ground under the rear
axle), quad/triangle faces and one material name per face. Parts are generated here, written to a file and
assembled in Blender by build_bike.py, so every dimension can be checked by plain Python tests.
"""
import math

import numpy as np


class Mesh:
    def __init__(self):
        self.V = []
        self.F = []
        self.M = []
        self.uv = {}                       # face index -> list of (u, v) per corner (optional)

    def add(self, other):
        o = len(self.V)
        self.V += list(map(tuple, np.asarray(other.V, float)))
        base = len(self.F)
        self.F += [tuple(i + o for i in f) for f in other.F]
        self.M += list(other.M)
        for k, v in other.uv.items():
            self.uv[base + k] = v
        return self

    def verts(self, P):
        o = len(self.V)
        self.V += [tuple(map(float, p)) for p in np.asarray(P, float)]
        return o

    def face(self, idx, mat):
        self.F.append(tuple(int(i) for i in idx))
        self.M.append(mat)

    def transform(self, R=None, t=None):
        V = np.asarray(self.V, float)
        if R is not None:
            V = V @ np.asarray(R, float).T
        if t is not None:
            V = V + np.asarray(t, float)
        self.V = list(map(tuple, V))
        return self

    def bounds(self):
        V = np.asarray(self.V, float)
        return V.min(axis=0), V.max(axis=0)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def frame_z(d):
    """Rotation whose third column is the unit vector d (first column as horizontal as possible)."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(ref, d)
    x /= np.linalg.norm(x)
    y = np.cross(d, x)
    return np.column_stack([x, y, d])


def grid(mesh, rings, mat, closed_u=True, cap0=False, cap1=False, mats=None):
    """Quads between consecutive rings (list of (n, 3) arrays with the same n). closed_u: rings are loops."""
    rings = [np.asarray(r, float) for r in rings]
    n = len(rings[0])
    base = [mesh.verts(r) for r in rings]
    for k in range(len(rings) - 1):
        m = mat if mats is None else mats[k]
        for i in range(n if closed_u else n - 1):
            j = (i + 1) % n
            mesh.face((base[k] + i, base[k] + j, base[k + 1] + j, base[k + 1] + i), m)
    for cap, k, rev in ((cap0, 0, True), (cap1, len(rings) - 1, False)):
        if cap:
            c = mesh.verts([rings[k].mean(axis=0)])
            for i in range(n):
                j = (i + 1) % n
                tri = (base[k] + i, base[k] + j, c)
                mesh.face(tri[::-1] if rev else tri, mat)
    return mesh


def lathe(profile, seg, mat, closed=False, phase=0.0):
    """Revolve a profile of (r, y) points about the Y axis (wheels, hubs, discs). Returns a Mesh."""
    m = Mesh()
    rings = []
    for r, y in profile:
        a = phase + np.linspace(0, 2 * math.pi, seg, endpoint=False)
        rings.append(np.stack([r * np.cos(a), np.full(seg, y), r * np.sin(a)], axis=1))
    return grid(m, rings if not closed else rings + [rings[0]], mat)


def tube(path, radius, seg, mat, cap0=True, cap1=True, section=None):
    """Sweep a circle (or SECTION: (seg, 2) local shape, scaled by RADIUS at each point) along PATH (k, 3).
    radius may be a scalar or a per-point array or (k, 2) for an elliptical section (a, b)."""
    P = np.asarray(path, float)
    k = len(P)
    r = np.broadcast_to(np.asarray(radius, float), (k,) + np.shape(radius)[1:] if np.ndim(radius) > 1 else (k,))
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    # parallel transport frame
    n0 = np.cross(T[0], [0, 0, 1.0]) if abs(T[0][2]) < 0.95 else np.cross(T[0], [1.0, 0, 0])
    n0 /= np.linalg.norm(n0)
    N = [n0]
    for i in range(1, k):
        v = N[-1] - np.dot(N[-1], T[i]) * T[i]
        N.append(v / np.linalg.norm(v))
    a = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    shape = np.stack([np.cos(a), np.sin(a)], axis=1) if section is None else np.asarray(section, float)
    rings = []
    for i in range(k):
        B = np.cross(T[i], N[i])
        ri = r[i]
        sa, sb = (ri[0], ri[1]) if np.ndim(ri) else (ri, ri)
        rings.append(P[i] + np.outer(shape[:, 0] * sa, N[i]) + np.outer(shape[:, 1] * sb, B))
    return grid(Mesh(), rings, mat, cap0=cap0, cap1=cap1)


def box(center, size, mat, R=None):
    m = Mesh()
    sx, sy, sz = np.asarray(size, float) / 2
    c = np.array([[-sx, -sy, -sz], [sx, -sy, -sz], [sx, sy, -sz], [-sx, sy, -sz],
                  [-sx, -sy, sz], [sx, -sy, sz], [sx, sy, sz], [-sx, sy, sz]])
    if R is not None:
        c = c @ np.asarray(R).T
    o = m.verts(c + np.asarray(center, float))
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        m.face([o + i for i in f], mat)
    return m


def rounded_rect(w, h, r, n=4):
    """Closed 2D loop (counter-clockwise) of a rounded rectangle w x h with corner radius r."""
    r = min(r, w / 2 - 1e-6, h / 2 - 1e-6)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


def resample(poly, step):
    """Closed polygon resampled at about STEP spacing."""
    P = np.asarray(poly, float)
    Q = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(int(s[-1] / step), 8)
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])], axis=1)


def smooth_poly(poly, k=2):
    """Moving-average smoothing of a closed polygon (removes pixel steps from traced outlines)."""
    P = np.asarray(poly, float)
    for _ in range(k):
        P = (np.roll(P, 1, axis=0) + 2 * P + np.roll(P, -1, axis=0)) / 4
    return P


def inside(poly, pts):
    """Point-in-polygon (even-odd) for many points."""
    P = np.asarray(poly, float)
    x, y = pts[:, 0], pts[:, 1]
    res = np.zeros(len(pts), bool)
    j = len(P) - 1
    for i in range(len(P)):
        xi, yi = P[i]
        xj, yj = P[j]
        cond = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        res ^= cond
        j = i
    return res


def panel(outline_xz, y_of, thickness, mat, step=0.012, edge_mat=None, flip=False):
    """Thin shell panel: a side outline (x, z) meshed with an interior grid, pushed out to y = y_of(x, z), given a
    thickness toward the bike's centre. Triangulated with scipy Delaunay (run outside Blender)."""
    from scipy.spatial import Delaunay
    B = resample(smooth_poly(outline_xz), step * 0.6)
    lo, hi = B.min(axis=0), B.max(axis=0)
    gx, gz = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    G = np.stack([gx.ravel(), gz.ravel()], axis=1)
    G = G[inside(B, G)]
    # keep interior grid points away from the boundary (no slivers)
    if len(G):
        d = np.min(np.linalg.norm(G[:, None, :] - B[None, :, :], axis=2), axis=1)
        G = G[d > 0.5 * step]
    P2 = np.vstack([B, G])
    tri = Delaunay(P2).simplices
    c = P2[tri].mean(axis=1)
    tri = tri[inside(B, c)]
    nb = len(B)
    m = Mesh()
    ys = np.array([y_of(x, z) for x, z in P2])
    sgn = np.sign(ys.mean()) if abs(ys.mean()) > 1e-9 else 1.0
    outer = np.stack([P2[:, 0], ys, P2[:, 1]], axis=1)
    inner = outer.copy()
    inner[:, 1] -= sgn * thickness
    o1 = m.verts(outer)
    o2 = m.verts(inner)
    for t in tri:
        a, b, cc = t
        f = (a, b, cc) if (sgn > 0) != flip else (a, cc, b)
        m.face([o1 + i for i in f], mat)
        m.face([o2 + i for i in f[::-1]], mat)
    em = edge_mat or mat
    for i in range(nb):                                   # rim around the outline
        j = (i + 1) % nb
        f = (o1 + i, o1 + j, o2 + j, o2 + i)
        m.face(f if (sgn > 0) != flip else f[::-1], em)
    return m


def loft_sections(stations, section_fn, mat, cap0=True, cap1=True):
    """Loft along a list of stations (any values); section_fn(s) returns an (n, 3) ring."""
    rings = [section_fn(s) for s in stations]
    return grid(Mesh(), rings, mat, cap0=cap0, cap1=cap1)


def plate2d(outer, holes, thickness, mat, to3d, step=0.008, side_mat=None, rings=()):
    """Solid plate from a 2D shape with holes (outer and each hole: closed (n, 2) loops, metres), extruded by
    THICKNESS along the local normal. to3d(u, v, w) maps local 2D (u, v) and offset w (-t/2..t/2) to 3D.
    Triangulated with scipy Delaunay; triangles kept inside the outer loop and outside every hole.
    rings: distances inside the outer loop at which rows of vertices follow the outline (for a surface that rolls
    or steps near its edge: an axis-aligned grid alone gives a frilled edge there)."""
    from scipy.spatial import Delaunay, cKDTree
    loops = [resample(outer, step * 0.7)] + [resample(h, step * 0.5) for h in holes]
    B = np.vstack(loops)
    R = np.zeros((0, 2))
    if len(rings):
        L = loops[0]
        t = np.roll(L, -1, axis=0) - np.roll(L, 1, axis=0)
        n = np.stack([t[:, 1], -t[:, 0]], axis=1)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        if inside(L, (L + 0.3 * step * n)[::5]).mean() < 0.5:        # make the normals point into the shape
            n = -n
        tree = cKDTree(B)
        rows = []
        for d in rings:
            Q = L + d * n
            ok = inside(L, Q) & (tree.query(Q)[0] > 0.8 * d)        # not across a thin tip or a concave corner
            for h in loops[1:]:
                ok &= ~inside(h, Q)
            Q = Q[ok]
            if len(rows) and len(Q):                                 # thin out where rows crowd (concave bends)
                Q = Q[cKDTree(np.vstack(rows)).query(Q)[0] > 0.45 * step]
            if len(Q) > 1:
                keep = [0]
                for i in range(1, len(Q)):
                    if np.hypot(*(Q[i] - Q[keep[-1]])) > 0.45 * step:
                        keep.append(i)
                Q = Q[keep]
            rows.append(Q)
        R = np.vstack(rows) if rows else R
    lo, hi = loops[0].min(axis=0), loops[0].max(axis=0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    G = np.stack([gx.ravel(), gy.ravel()], axis=1)
    ok = inside(loops[0], G)
    for h in loops[1:]:
        ok &= ~inside(h, G)
    G = G[ok]
    if len(G):
        d = np.min(np.linalg.norm(G[:, None, :] - B[None, :, :], axis=2), axis=1)
        G = G[d > (0.45 * step if not len(rings) else max(rings) + 0.5 * step)]
    B_all = np.vstack([B, R])
    P = np.vstack([B_all, G])
    tri = Delaunay(P).simplices
    c = P[tri].mean(axis=1)
    keep = inside(loops[0], c)
    for h in loops[1:]:
        keep &= ~inside(h, c)
    tri = tri[keep]
    m = Mesh()
    top = m.verts([to3d(u, v, thickness / 2) for u, v in P])
    bot = m.verts([to3d(u, v, -thickness / 2) for u, v in P])
    for a, b, cc in tri:
        m.face((top + a, top + b, top + cc), mat)
        m.face((bot + a, bot + cc, bot + b), mat)
    sm = side_mat or mat
    o = 0
    for k, L in enumerate(loops):
        n = len(L)
        for i in range(n):
            j = (i + 1) % n
            f = (top + o + i, bot + o + i, bot + o + j, top + o + j)
            m.face(f if k == 0 else f[::-1], sm)
        o += n
    return m


def circle(r, n=32, cx=0.0, cy=0.0):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def slot(c, ang, length, width, n=8):
    """Stadium-shaped slot centred at c, along angle ang."""
    d = np.array([math.cos(ang), math.sin(ang)])
    nrm = np.array([-d[1], d[0]])
    pts = []
    for s0, a0 in ((length / 2, -math.pi / 2), (-length / 2, math.pi / 2)):
        for a in np.linspace(a0, a0 + math.pi, n):
            pts.append(np.asarray(c) + d * s0 + (d * math.cos(a) + nrm * math.sin(a)) * width / 2)
    return np.array(pts)


def prism(outline, y0, y1, mat, step=0.012):
    """Solid extrusion of a side outline (x, z) between y0 and y1 (caps meshed with an interior grid)."""
    w = abs(y1 - y0)
    yc = (y0 + y1) / 2
    return plate2d(outline, [], w, mat, lambda u, v, t: (u, yc + t, v), step=step)
