"""Damien's helmet and goggle: Leatt Moto 8.5 Composite (V26 kit, Pinata Teal) and Velocity 5.5 Iriz goggle.

python3 helmet.py BODY.npz OUT.npz          (body.py writes BODY.npz; OUT.npz is a gear file for build_rider.py)

Everything is built here in the HELMET frame (metres, x to the wearer's left, y backwards, z up: the axes of body.py's
MB frame) and placed on his head by one rigid transform found from his head mesh (fit_on_head). The parts ride the
"head" bone rigidly.

Sources (research/rider-ledger/helmet.md has every number with its source):
  PROFILE   the shell's side outline traced from Leatt's near-orthographic left view of the same 8.5 shell
            (V25 "Royal", 1025100220: Leatt_Helmet_Moto_8.5_Royal_Left_1025100220.png on us.leatt.com, product
            helmet-kit-moto-8-5-composite-with-5-5-goggle-sale), in its pixels (u right = backwards, v down).
  SCALE     the 45 mm goggle strap (Leatt Velocity 5.5 spec) measured in Leatt's MY27 side and back views of the
            same shell with the goggle on (31509_Helmet_Kit_Moto_8.5_White_2/_3_1027000260.jpg), the left view
            registered onto that side view by a similarity fit (residual 18 px), camera taken 1.5 m away.
  WIDTHS    back-view half widths (Royal_Back, scaled the same way) and the plan (Pinata Teal top view).
"""
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import Delaunay, cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.normpath(os.path.join(HERE, "..", "..", "textures", "rider"))

# ---------------------------------------------------------------- scale and profile (Leatt Royal_Left pixels)
STRAP = 0.045                      # m, Velocity 5.5 strap width (Leatt feature list)
STRAP_PX_MY27_SIDE = 186.7         # strap width across its run in the MY27 side view (194 px tall at 15.8 deg)
ROYAL_TO_MY27 = 0.9481             # similarity fit of the Royal_Left outline onto the MY27 side view
PERSPECTIVE = 1.087                # strap on the side surface 0.13 m nearer a camera 1.5 m away than the centre plane
S = STRAP / STRAP_PX_MY27_SIDE * ROYAL_TO_MY27 * PERSPECTIVE      # m per Royal_Left pixel = 0.248 mm
U0, V0 = 1100.0, 900.0             # helmet-frame origin in Royal_Left pixels (near the ear)

# Traced outline, Royal_Left pixels, in order round the shell (front at small u). RIM stretches are on the
# centre plane (the surface's two halves meet there); FREE stretches are cut edges (lower edge, face port).
CROWN_UNDER_VISOR = [            # shell crown hidden under the visor: estimated (visor stands 0 mm off the crown at
    (539, 703), (533, 660), (533, 615), (540, 572), (556, 530),   # u 1135, 13 mm at u 886, 21 mm at u 726)
    (582, 490), (620, 455), (668, 430), (725, 413), (800, 399), (886, 390), (966, 384), (1045, 379), (1124, 377)]
CROWN_BACK = [
    (1194, 380), (1218, 385), (1241, 389), (1265, 395), (1288, 400), (1311, 405), (1335, 412), (1358, 418),
    (1381, 424), (1404, 430), (1427, 436), (1450, 442), (1473, 450), (1496, 457), (1519, 464), (1542, 471),
    (1562, 484), (1577, 503), (1584, 524), (1581, 547), (1580, 571), (1588, 593), (1597, 615), (1606, 637),
    (1615, 659), (1624, 681), (1633, 703), (1641, 726), (1649, 748), (1655, 771), (1662, 794), (1668, 817),
    (1674, 841), (1679, 864), (1683, 888), (1688, 911), (1691, 935), (1695, 959), (1697, 982), (1699, 1006),
    (1699, 1030), (1696, 1054), (1689, 1076), (1681, 1098), (1674, 1121), (1670, 1144), (1668, 1168),
    (1665, 1192), (1658, 1214), (1649, 1235), (1637, 1256), (1625, 1276), (1613, 1297), (1602, 1319),
    (1589, 1336), (1573, 1354), (1557, 1372), (1540, 1389), (1522, 1404), (1497, 1414)]
LOWER_EDGE = [
    (1497, 1414), (1458, 1422), (1419, 1432), (1380, 1437), (1340, 1440), (1300, 1443), (1260, 1446),
    (1220, 1449), (1181, 1452), (1141, 1455), (1101, 1459), (1061, 1463), (1022, 1471), (983, 1478),
    (943, 1486), (904, 1493), (865, 1500), (825, 1507), (786, 1514), (747, 1522), (707, 1529), (668, 1537),
    (629, 1544), (590, 1550), (550, 1555), (510, 1561), (471, 1569), (432, 1578), (393, 1585), (353, 1591),
    (314, 1596), (294, 1598)]
CHIN_FRONT = [
    (294, 1598), (272, 1593), (257, 1578), (252, 1550), (249, 1516), (247, 1484), (244, 1453), (241, 1421),
    (239, 1389), (240, 1357), (243, 1330), (236, 1300), (224, 1272), (213, 1245), (210, 1228), (221, 1210),
    (238, 1192), (259, 1168), (281, 1145), (305, 1124), (334, 1110), (364, 1100), (378, 1098)]
FACE_PORT = [                    # chin bar top, the port's side edge (inner edge of the trim), brow edge
    (378, 1098), (386, 1111), (396, 1124), (410, 1131), (441, 1139), (473, 1142), (505, 1144), (536, 1146),
    (566, 1135), (592, 1116), (621, 1104), (652, 1096), (683, 1090), (708, 1071), (726, 1045), (735, 1015),
    (740, 983), (742, 951), (744, 919), (746, 887), (750, 860), (746, 842), (731, 835), (704, 819), (676, 806),
    (649, 788), (625, 768), (597, 752), (569, 738), (548, 724), (539, 703)]


def px2h(P):
    """Royal_Left pixels -> helmet frame (y, z) in metres."""
    P = np.asarray(P, float)
    return np.c_[(P[:, 0] - U0) * S, -(P[:, 1] - V0) * S]


def resample_open(P, step):
    P = np.asarray(P, float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, s[-1], max(int(round(s[-1] / step)), 2) + 1)
    return np.c_[np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])]


def smooth_open(P, k=2):
    """Moving average that keeps the end points (removes 1 px tracing steps)."""
    P = np.array(P, float)
    for _ in range(k):
        Q = P.copy()
        Q[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
        P = Q
    return P


class Profile:
    """The side outline in the helmet frame: two rims (crown and back; chin front) and the free edges."""

    def __init__(self, step=0.003):
        crown = np.vstack([CROWN_UNDER_VISOR, CROWN_BACK])
        self.rim_crown = resample_open(smooth_open(px2h(crown), 3), step)
        self.lower = resample_open(smooth_open(px2h(LOWER_EDGE), 2), step)
        self.rim_chin = resample_open(smooth_open(px2h(CHIN_FRONT), 2), step)
        self.port = resample_open(smooth_open(px2h(FACE_PORT), 2), step)
        # closed domain outline, counter-clockwise in (y, z)? order: brow -> crown -> back -> lower -> chin -> port
        self.outline = np.vstack([self.rim_crown, self.lower[1:], self.rim_chin[1:], self.port[1:-1]])
        self.tree_crown = cKDTree(self.rim_crown)
        self.tree_chin = cKDTree(self.rim_chin)
        o = self.outline
        self.area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])

    def inside(self, P):
        o = self.outline
        x, y = P[:, 0], P[:, 1]
        res = np.zeros(len(P), bool)
        j = len(o) - 1
        for i in range(len(o)):
            xi, yi = o[i]
            xj, yj = o[j]
            res ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
            j = i
        return res


# ---------------------------------------------------------------- half width over the profile
L_CROWN, P_CROWN = 0.1239, 1.933  # roundness of the crown and back (m, superellipse power): fitted with W_Z, Q_Y
L_CHIN, P_CHIN = 0.120, 1.5        # the chin bar narrows to a blunt V in plan (estimated from the iso views)
# Half width by height (back view) and plan factor by y (top view), fitted together with L_CROWN and P_CROWN to
# Leatt's back view (Royal_Back, camera 13.5 deg above, 0.2046 mm/px) and top view (Pinata Teal top, 0.247
# mm/px) by least squares with a smoothness penalty: residuals 7.7 px (1.6 mm) back, 9.3 px (2.3 mm) top. The
# fit's 7 % dip at z = 0 (a 1.5 % waist in the back photo, rows 880 to 960) is evened out by hand to 0.1300.
W_Z = np.array([[-0.20, 0.1115], [-0.16, 0.1155], [-0.12, 0.1197], [-0.08, 0.1287], [-0.04, 0.1347],
                [0.00, 0.1300], [0.04, 0.1304], [0.08, 0.1322], [0.12, 0.1342], [0.16, 0.1362]])
Q_Y = np.array([[-0.30, 0.9126], [-0.04, 0.9126], [0.00, 0.9755], [0.04, 0.9413], [0.08, 0.9447],
                [0.12, 1.0228], [0.16, 1.1211]])


def falloff(t, p):
    t = np.clip(t, 0.0, 1.0)
    return (1.0 - (1.0 - t) ** p) ** (1.0 / p)


L_BROW, P_BROW = 0.075, 2.0         # the brow and forehead are broad and flat with rounded corners (iso views)
Y_BROW = (-0.10, 0.00)             # the crown rim blends from the brow's roundness to the crown's over this y range
SMOOTH_SIGMA = 0.010               # m, Gaussian smoothing of the width field away from the rims (no creases)


def rim_shape(prof):
    """Roundness length and power at each crown rim sample (brow in front, crown and back behind)."""
    y = prof.rim_crown[:, 0]
    k = np.clip((y - Y_BROW[0]) / (Y_BROW[1] - Y_BROW[0]), 0, 1)
    k = k * k * (3 - 2 * k)
    return L_BROW + (L_CROWN - L_BROW) * k, P_BROW + (P_CROWN - P_BROW) * k


def half_width(prof, Y, Z, smooth=True):
    """Half width x of the outer surface over the profile domain (both halves are +-x)."""
    P = np.c_[Y, Z]
    dc, ic = prof.tree_crown.query(P)
    dh = prof.tree_chin.query(P)[0]
    Lc, Pc = rim_shape(prof)
    w = np.interp(Z, W_Z[:, 0], W_Z[:, 1]) * np.interp(Y, Q_Y[:, 0], Q_Y[:, 1])
    X = w * falloff(dc / Lc[ic], Pc[ic]) * falloff(dh / L_CHIN, P_CHIN)
    if not smooth:
        return X
    # the nearest-rim distance has creases where the nearest rim point jumps: average them out away from the rims
    d = np.minimum(dc, dh)
    tree = cKDTree(P)
    far = np.nonzero(d > 0.008)[0]
    Xs = X.copy()
    for i, nb in zip(far, tree.query_ball_point(P[far], 2.5 * SMOOTH_SIGMA)):
        nb = np.asarray(nb)
        wts = np.exp(-np.sum((P[nb] - P[i]) ** 2, 1) / (2 * SMOOTH_SIGMA ** 2))
        Xs[i] = np.sum(wts * X[nb]) / np.sum(wts)
    k = np.clip((d - 0.008) / 0.020, 0, 1)
    return X + (Xs - X) * k * k * (3 - 2 * k)


def ring_offsets(L, p, n):
    """Distances from a rim where the falloff rises in equal steps (even spacing across the 3D surface)."""
    s = np.arange(1, n + 1) / n
    return L * (1.0 - (1.0 - s ** p) ** (1.0 / p))


def domain_points(prof, h=0.005, nring=14):
    """Points of the profile domain: the outline itself, rings graded towards the rims, an interior grid."""
    pts = [prof.outline]
    for rim, L, p in ((prof.rim_crown, L_BROW, P_BROW), (prof.rim_chin, L_CHIN, P_CHIN)):
        t = np.gradient(rim, axis=0)
        t /= np.linalg.norm(t, axis=1)[:, None]
        n = np.c_[-t[:, 1], t[:, 0]]
        if prof.area < 0:
            n = -n
        for d in ring_offsets(L, p, nring)[:-3]:
            step = max(0.003, min(h, d * 0.9))
            r = resample_open(rim + n * d, step)
            pts.append(r)
    lo, hi = prof.outline.min(0), prof.outline.max(0)
    gy, gz = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
    gy = gy + (np.arange(gy.shape[0])[:, None] % 2) * h / 2
    pts.append(np.c_[gy.ravel(), gz.ravel()])
    P = np.vstack(pts)
    n_out = len(prof.outline)
    keep = np.ones(len(P), bool)
    keep[n_out:] = prof.inside(P[n_out:])
    # nothing closer than 1.2 mm to the outline (other than the outline itself)
    d_out = cKDTree(prof.outline).query(P)[0]
    keep[n_out:] &= d_out[n_out:] > 0.0012
    P = P[keep]
    # thin out points closer than a local spacing (greedy, rings first)
    tree = cKDTree(P)
    alive = np.ones(len(P), bool)
    dc = np.minimum(prof.tree_crown.query(P)[0], prof.tree_chin.query(P)[0])
    rad = np.clip(dc * 0.35, 0.0008, h * 0.6)
    for i in range(n_out, len(P)):
        if not alive[i]:
            continue
        for j in tree.query_ball_point(P[i], rad[i]):
            if j > i and j >= n_out:
                alive[j] = False
    return P[alive]


def mesh_domain(prof, P):
    tri = Delaunay(P).simplices
    c = P[tri].mean(1)
    tri = tri[prof.inside(c)]
    # orientation: counter-clockwise in (y, z)
    a, b, cc = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (cc[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (cc[:, 0] - a[:, 0])
    tri[cr < 0] = tri[cr < 0][:, ::-1]
    return tri[np.abs(cr) > 1e-9]                   # slivers along nearly straight outline corners


def shell_outer(prof=None):
    """Outer surface of the shell, both halves, one vertex on the centre plane for each rim point."""
    prof = prof or Profile()
    P = domain_points(prof)
    T = mesh_domain(prof, P)
    X = half_width(prof, P[:, 0], P[:, 1])
    rim_mask = np.minimum(prof.tree_crown.query(P)[0], prof.tree_chin.query(P)[0]) < 1e-7
    X[rim_mask] = 0.0
    n = len(P)
    VL = np.c_[X, P]                                       # left half (x > 0)
    VR = np.c_[-X, P]
    # right half reuses the rim vertices
    idx_r = np.arange(n) + n
    idx_r[rim_mask] = np.nonzero(rim_mask)[0]
    V = np.vstack([VL, VR])
    # left half seen from +x: (y, z) counter-clockwise -> normal +x when ordered (y, z) ccw. Check below.
    FL = T.copy()
    FR = idx_r[T][:, ::-1]
    F = np.vstack([FL, FR])
    used = np.unique(F)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    return V[used], remap[F], prof


def normals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]


# ---------------------------------------------------------------- parts, rims, inner surface
class Part:
    """Vertices, triangles/quads, a material name per face, optional face-corner UVs."""

    def __init__(self, name, bone="head"):
        self.name, self.bone = name, bone
        self.V = np.zeros((0, 3))
        self.F, self.M, self.UV = [], [], []

    def add(self, V, F, mat, uv=None):
        o = len(self.V)
        self.V = np.vstack([self.V, V])
        for k, f in enumerate(F):
            self.F.append([int(i) + o for i in f])
            self.M.append(mat if isinstance(mat, str) else mat[k])
            self.UV.append(None if uv is None else uv[k])
        return o


def boundary_loops(F):
    """Closed loops of edges used by one face only, as vertex lists in the faces' winding order."""
    cnt = {}
    for f in F:
        for a, b in zip(f, np.roll(f, -1)):
            k = (min(a, b), max(a, b))
            cnt[k] = cnt.get(k, 0) + 1
    nxt = {}
    for f in F:
        for a, b in zip(f, np.roll(f, -1)):
            if cnt[(min(a, b), max(a, b))] == 1:
                nxt[int(a)] = int(b)
    loops, seen = [], set()
    for s in nxt:
        if s in seen:
            continue
        loop, v = [], s
        while v not in seen:
            seen.add(v)
            loop.append(v)
            v = nxt[v]
        loops.append(np.array(loop))
    return loops


def smooth_field(F, n, val, it=10, keep=None):
    """Laplacian smoothing of a per-vertex scalar over the mesh's edges."""
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=n).astype(float)
    v = val.copy()
    for _ in range(it):
        acc = np.bincount(E[:, 0], weights=v[E[:, 1]], minlength=n)
        v = 0.5 * v + 0.5 * acc / np.maximum(deg, 1)
        if keep is not None:
            v[keep] = val[keep]
    return v


# ---------------------------------------------------------------- his head size and Leatt's chart
SIZES = [("XS", 0.53, 0.54), ("S", 0.55, 0.56), ("M", 0.57, 0.58), ("L", 0.59, 0.60), ("XL", 0.61, 0.62),
         ("XXL", 0.63, 0.64)]          # Leatt helmet moto size chart, head circumference (m)


def head_circumference(body):
    """Tape round his head above the brows and over the back of the skull: the largest convex girth of the
    skin over planes through the head between the brows and the crown, tilted -10 to +10 deg (front low)."""
    from scipy.spatial import ConvexHull
    V, FS, F = body["V"], body["FS"], body["F"]
    starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
    tri = np.array([[F[s0], F[s0 + i], F[s0 + i + 1]] for s0, n in zip(starts, FS) for i in range(1, n - 1)])
    names = list(body["bones"])
    eye = body["heads"][names.index("eye.L")]
    best = 0.0
    for z0 in np.arange(eye[2] + 0.015, eye[2] + 0.05, 0.0025):
        for tilt in np.radians(np.arange(-10, 10.1, 2)):
            n = np.array([0.0, math.sin(tilt), math.cos(tilt)])
            sd = (V - np.array([0.0, eye[1], z0])) @ n
            pts = []
            for i, j in ((0, 1), (1, 2), (2, 0)):
                si, sj = sd[tri[:, i]], sd[tri[:, j]]
                m = si * sj < 0
                tt = si[m] / (si[m] - sj[m])
                pts.append(V[tri[m, i]] + (V[tri[m, j]] - V[tri[m, i]]) * tt[:, None])
            P = np.concatenate(pts)
            P = P[np.abs(P[:, 0]) < 0.12]
            P = P[P[:, 2] > eye[2] - 0.03]
            if np.ptp(P[:, 0]) > 0.165:                 # the plane caught the ears: not a head girth
                continue
            e1 = np.array([1.0, 0, 0]); e2 = np.cross(n, e1)
            best = max(best, ConvexHull(np.c_[P @ e1, P @ e2]).area)
    return best


def size_for(circ):
    """Leatt size for a head girth: the size whose range holds it, else the nearest range (ties: larger)."""
    d = [(max(lo - circ, circ - hi, 0.0), -i, name) for i, (name, lo, hi) in enumerate(SIZES)]
    return min(d)[2]


# ---------------------------------------------------------------- his head and the fit
GAP = 0.002                        # m between his skin and the comfort liner's surface (pads touch the head)
T_MIN, T_MAX = 0.018, 0.040        # m, shell + EPS + pads at their thinnest (chin bar) and fullest (crown)
EYE_TO_BROW = 0.040                # m, face port's top edge above his eye centres (goggle centred on them)
FORE_MIN = 0.032                   # m, the brow (outer) at least this far ahead of his forehead


def head_skin(body, bones=("head", "jaw", "neck03", "neck02", "neck01")):
    """Skin vertices mostly carried by the head, jaw and neck (rest frame) and those of the head alone."""
    names = list(body["bones"])
    V = body["V"]
    tot = np.zeros(len(V))
    for b in bones:
        bi = names.index(b)
        sel = body["w_bone"] == bi
        np.add.at(tot, body["w_vert"][sel], body["w_val"][sel])
    for b in [n for n in names if n.startswith(("eye", "special", "tongue", "jaw", "levator", "orbicularis",
                                                    "oris", "temporalis", "risorius", "nose", "cheek"))]:
        bi = names.index(b)
        sel = body["w_bone"] == bi
        np.add.at(tot, body["w_vert"][sel], body["w_val"][sel])
    return np.nonzero(tot > 0.5)[0]


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def brow_point(prof):
    """Centre-line end of the face port's top edge (helmet frame)."""
    p = prof.port[-1]
    return np.array([0.0, p[0], p[1]])


def head_landmarks(body):
    """His head's landmarks (rest frame): eye centres' midpoint, vertex (top), back, sides, forehead."""
    names = list(body["bones"])
    eye = 0.5 * (body["heads"][names.index("eye.L")] + body["heads"][names.index("eye.R")])
    Hd = body["V"][head_skin(body, ("head",))]
    sk = Hd[Hd[:, 2] > eye[2] + 0.03]
    fore = Hd[(Hd[:, 2] > eye[2] + 0.025) & (np.abs(Hd[:, 0]) < 0.01)]
    return dict(eye=eye, top=Hd[np.argmax(Hd[:, 2])], back=sk[np.argmax(sk[:, 1])], left=sk[np.argmax(sk[:, 0])],
                right=sk[np.argmin(sk[:, 0])], fore=fore[np.argmin(fore[:, 1])])


def fit_on_head(body, Vo, Fo, prof):
    """Place the helmet on his head: the face port's top edge EYE_TO_BROW above his eye centres on the centre
    line (the goggle then sits centred on his eyes in the port); pitch and fore-aft shift chosen so the shell
    stands off his skull evenly at the top, back and sides (equal EPS and padding all round) with the forehead
    at least FORE_MIN behind the brow. Returns R, t (p_MB = R p_H + t) and the gaps."""
    L = head_landmarks(body)
    C = np.vstack([Vo, Vo[Fo].mean(1)])
    tree = cKDTree(C)
    b = brow_point(prof)

    def place(th, dy):
        R = rot_x(th)
        return R, np.array([0.0, L["eye"][1] + dy, L["eye"][2] + EYE_TO_BROW]) - R @ b

    def gaps(th, dy):
        R, t = place(th, dy)
        return {k: tree.query((L[k] - t) @ R)[0] for k in ("top", "back", "left", "right", "fore")}

    best = None
    for th in np.radians(np.arange(0.0, 25.01, 0.5)):
        for dy in np.arange(-0.070, -0.0199, 0.001):
            g = gaps(th, dy)
            ring = np.array([g["top"], g["back"], g["left"], g["right"]])
            cost = ring.std() + 10 * max(0.0, FORE_MIN - g["fore"])
            if best is None or cost < best[0]:
                best = (cost, th, dy, g)
    R, t = place(best[1], best[2])
    return R, t, dict(pitch_deg=round(math.degrees(best[1]), 2), brow_ahead_of_eye_mm=round(-best[2] * 1000, 1),
                      gaps_mm={k: round(float(v) * 1000, 1) for k, v in best[3].items()})


def shell_solid(Vo, Fo, skin_H):
    """Outer surface, inner (comfort liner) surface and the rolled edges joining them, in the helmet frame.
    skin_H: his head and neck skin in the helmet frame. The liner surface lies GAP off the skin where the skin is
    near (pads) and T_MAX inside the shell elsewhere, never thinner than T_MIN. Returns the inner surface, the
    thickness and the rim strips (one per free edge: face port, lower edge) as lists of rings."""
    n = len(Vo)
    N = normals(Vo, Fo)
    d = cKDTree(skin_H).query(Vo)[0]
    t = np.clip(d - GAP, T_MIN, T_MAX)
    t = np.minimum(smooth_field(Fo, n, t, 12), np.maximum(d - GAP, T_MIN))
    Vi = Vo - N * t[:, None]
    strips = []
    for loop in boundary_loops(Fo):
        O, I = Vo[loop], Vi[loop]
        tang = np.roll(O, -1, 0) - np.roll(O, 1, 0)
        tang /= np.linalg.norm(tang, axis=1)[:, None]
        out = np.cross(tang, N[loop])                      # in the surface, away from it (winding order)
        out /= np.linalg.norm(out, axis=1)[:, None]
        rings = []
        for k, sv in enumerate(np.linspace(0, 1, 6)):
            bulge = RIM_R * np.sin(np.pi * sv) + RIM_R * 0.6 * np.sin(np.pi * min(sv * 3, 1)) * (sv < 0.34)
            rings.append(O + (I - O) * sv + out * bulge[..., None] if np.ndim(bulge) else O + (I - O) * sv + out * bulge)
        strips.append((loop, rings))
    return Vi, t, strips


RIM_R = 0.004                      # m, the rubber trim's roll beyond the cut edge


# ---------------------------------------------------------------- visor
# Royal_Left pixels: top line (centre line) and lower edge (the visor's side edge seen from the side), tip at u 220,
# rear end on the crown at u 1135 (its rear edge runs down to the side corner at u 1075, v 662).
VISOR_TOP = [(220, 334), (257, 323), (297, 322), (337, 322), (407, 321), (487, 322), (567, 323), (647, 326),
             (726, 329), (806, 334), (886, 340), (966, 347), (1045, 358), (1100, 366), (1135, 372)]
VISOR_LOW = [(220, 334), (277, 377), (346, 416), (416, 454), (487, 491), (558, 528), (610, 600), (660, 660),
             (720, 712), (760, 722), (900, 692), (1000, 675), (1075, 662), (1110, 540), (1135, 380)]
# plan half width of the visor (Pinata Teal top view, 0.247 mm/px), by Royal_Left u
VISOR_PLAN = [(220, 0.0), (236, 0.0356), (276, 0.0652), (315, 0.0745), (395, 0.0800), (474, 0.0860),
              (554, 0.0921), (634, 0.0988), (713, 0.1058), (793, 0.1162), (872, 0.1212), (912, 0.1225),
              (1000, 0.090), (1075, 0.050), (1135, 0.0)]      # behind u 912 the visor lies on the shell
VISOR_T = 0.0035                   # m, visor thickness (moulded ABS)
VISOR_GAP = 0.004                  # m, clear of the shell where it lies over it


def visor_surface(prof, nu=56, nphi=41):
    """Top surface of the visor as a grid (stations from the tip back to the rear, arch across)."""
    top = px2h(VISOR_TOP)
    low = px2h(VISOR_LOW)
    plan = np.array(VISOR_PLAN, float)
    us = np.r_[np.linspace(220, 330, 12), np.linspace(330, 1135, nu - 12)[1:]]
    ys = (us - U0) * S
    zt = np.interp(ys, top[:, 0], top[:, 1])
    zl = np.interp(ys, low[:, 0], low[:, 1])
    a = np.interp(us, plan[:, 0], plan[:, 1])
    phi = np.linspace(-1, 1, nphi)
    G = np.zeros((len(us), nphi, 3))
    for i, (y, z0, z1, ai) in enumerate(zip(ys, zt, zl, a)):
        c = 1 - np.cos(phi * np.pi / 2)
        z = z0 - (z0 - z1) * c ** 1.3
        x = ai * np.sin(phi * np.pi / 2)
        G[i] = np.c_[x, np.full(nphi, y), z]
    # lie over the shell where the shell is under it: never closer than VISOR_GAP
    flat = G.reshape(-1, 3)
    ins = prof.inside(flat[:, 1:])
    hw = np.zeros(len(flat))
    hw[ins] = half_width(prof, flat[ins, 1], flat[ins, 2], smooth=False)
    side = np.sign(flat[:, 0]) + (flat[:, 0] == 0)
    need = ins & (np.abs(flat[:, 0]) < hw + VISOR_GAP)
    flat[need, 0] = side[need] * (hw[need] + VISOR_GAP)
    return flat.reshape(G.shape)


def grid_faces(nr, nc, off=0, flip=False):
    F = []
    for i in range(nr - 1):
        for j in range(nc - 1):
            q = [off + i * nc + j, off + i * nc + j + 1, off + (i + 1) * nc + j + 1, off + (i + 1) * nc + j]
            F.append(q[::-1] if flip else q)
    return F


def thicken_grid(G, t, mat_top, mat_under, mat_edge, part):
    """A grid surface made solid: top, underside offset by t along its normals, edge strips all round."""
    nr, nc, _ = G.shape
    V = G.reshape(-1, 3)
    Ft = np.array(grid_faces(nr, nc))
    tris = np.vstack([Ft[:, [0, 1, 2]], Ft[:, [0, 2, 3]]])
    N = normals(V, tris)
    # top faces point up/out: orient by the centre of the grid
    c = V.mean(0)
    flip = np.mean(np.sum(N * (V - c), 1)) < 0
    if flip:
        N = -N
    Vu = V - N * t
    o1 = part.add(V, grid_faces(nr, nc, 0, flip), mat_top)
    o2 = part.add(Vu, grid_faces(nr, nc, 0, not flip), mat_under)
    ring = ([(0, j) for j in range(nc)] + [(i, nc - 1) for i in range(1, nr)] +
            [(nr - 1, j) for j in range(nc - 2, -1, -1)] + [(i, 0) for i in range(nr - 2, 0, -1)])
    idx = [i * nc + j for i, j in ring]
    F = []
    for k in range(len(idx)):
        a, b = idx[k], idx[(k + 1) % len(idx)]
        q = [o1 + a, o1 + b, o2 + b, o2 + a]
        F.append(q if not flip else q[::-1])
    part.add(np.zeros((0, 3)), [], mat_edge)
    for f in F:
        part.F.append(f); part.M.append(mat_edge); part.UV.append(None)
    return o1


def build(body):
    Vo, Fo, prof = shell_outer()
    R, tr, info = fit_on_head(body, Vo, Fo, prof)
    skin = body["V"][head_skin(body)]
    skin_H = (skin - tr) @ R
    Vi, thick, strips = shell_solid(Vo, Fo, skin_H)
    shell = Part("helmet_shell")
    shell.add(Vo, Fo, "helmet_white")
    o_in = shell.add(Vi, Fo[:, ::-1], "helmet_liner")
    for loop, rings in strips:
        m = len(loop)
        ids = [loop] + [shell.add(r, [], "helmet_trim") + np.arange(m) for r in rings[1:-1]] + [o_in + loop]
        F = []
        for k in range(len(ids) - 1):
            for i in range(m):
                j = (i + 1) % m
                F.append([ids[k][i], ids[k + 1][i], ids[k + 1][j], ids[k][j]])
        o = len(shell.V)
        for f in F:
            shell.F.append(f); shell.M.append("helmet_trim"); shell.UV.append(None)
    visor = Part("helmet_visor")
    thicken_grid(visor_surface(prof), VISOR_T, "helmet_white", "visor_under", "visor_under", visor)
    parts = [shell, visor]
    for P in parts:
        P.V = P.V @ R.T + tr
    info.update(shell_thickness_mm=[round(float(thick.min()) * 1000, 1), round(float(thick.max()) * 1000, 1)])
    return parts, info, (R, tr)


def hidden_skin(body, Rt, prof=None):
    """His scalp and the skin the shell covers completely (hide_body): head skin inside the shell, more than
    40 mm above its lower edge and more than 30 mm behind the face port's side edge, so nothing that can be seen
    through the port or from below is hidden."""
    prof = prof or Profile()
    R, t = Rt
    idx = head_skin(body)
    q = (body["V"][idx] - t) @ R
    ins = prof.inside(q[:, 1:])
    hw = np.zeros(len(q))
    hw[ins] = half_width(prof, q[ins, 1], q[ins, 2], smooth=False)
    low = np.interp(q[:, 1], prof.lower[::-1, 0], prof.lower[::-1, 1])
    port_back = prof.port[:, 0].max()
    keep = ins & (np.abs(q[:, 0]) < hw - 0.005) & (q[:, 2] > low + 0.040) & (q[:, 1] > port_back + 0.030)
    return idx[keep]


def extras(body, parts, Rt):
    return dict(hide_body=hidden_skin(body, Rt))


MATERIALS = {
    "helmet_white": dict(rgb=[226, 229, 235], rough=0.22, coat=1.0),
    "helmet_trim": dict(rgb=[18, 18, 20], rough=0.65),
    "helmet_liner": dict(rgb=[34, 34, 38], rough=0.9, sheen=0.4),
    "visor_under": dict(rgb=[214, 217, 222], rough=0.45),
}


def write_npz(path, parts, extra=None):
    mats = sorted({m for P in parts for m in P.M})
    out = dict(names=np.array([P.name for P in parts]), mats=np.array(mats),
               materials=json.dumps({m: MATERIALS[m] for m in mats}))
    for P in parts:
        FS = np.array([len(f) for f in P.F])
        out[P.name + "__V"] = P.V.astype(np.float64)
        out[P.name + "__F"] = np.concatenate([np.asarray(f) for f in P.F]).astype(np.int64)
        out[P.name + "__FS"] = FS
        out[P.name + "__M"] = np.array([mats.index(m) for m in P.M])
        out[P.name + "__bone"] = np.array(P.bone)
        if all(u is not None for u in P.UV):
            out[P.name + "__UV"] = np.concatenate([np.asarray(u, float) for u in P.UV])
    if extra:
        out.update(extra)
    np.savez_compressed(path, **out)


if __name__ == "__main__":
    body = np.load(sys.argv[1])
    parts, info, Rt = build(body)
    write_npz(sys.argv[2], parts, extras(body, parts, Rt))
    print(json.dumps(info), sum(len(P.V) for P in parts), "vertices")
