"""Moulded detail away from the helmet's front, as geometry (helmet round 3, decision 46): the crown's two mesh vents
(a raised white insert round a triangle lattice over the dark opening), the two rear exhaust slots' moulded surround
and the rear lower white pieces round the lower rear vents. The front's detail (grip panels, the trim's roll, brow
and chin vents, chin LEATT, brow tag) waits for phase B, because the front moves.

Each outline is traced in one of Leatt's Pinata photos (px) and cast onto the shell through that photo's camera in
helmet.CAMS, the cameras the print was traced through, so the geometry stands on its own print (the painted dark
openings, the white of the rear lower pieces). Sizes are measured at 1:1 against the solved cameras of
research/helmet-ba.json (mm per px at the feature, helmet_ba.py): see the tables' comments and the ledger, section 6.
All in the HELMET frame (metres, x his left, y back, z up); the right side is the mirror of the left.
"""
import math

import numpy as np

import helmet as H

PART = "helmet_vents"
MAT = "helmet_moulded"           # the rear surrounds and lower pieces: the shell's own white under its clear coat
MAT_INSERT = "helmet_vent_insert"  # the crown vents' insert and lattice: white plastic, satin
MAT_DARK = "helmet_trim"          # the slots' depth (the trim's black, helmet.MATERIALS)
SINK = 0.0006                     # m, walls start this far under the shell's surface (no gap on a curved shell)
BEVEL = 0.0003                    # m, the moulded edges' round-over

# The crown vents: helmet_art.CROWN_VENT (top photo px, the vent on his right; the left is its mirror). Measured
# through the solved top camera (helmet_ba, 0.222 mm/px at the vent): insert 41 x 28 mm, opening 35 x 21 mm (through
# the print's top camera, helmet.CAMS: opening 35 x 23 mm, 0.232 mm/px); the rim (insert to opening) 1.2 to 3.5 mm
# wide, 2.5 mm median; lattice bars 3.5 to 4 px (0.8 to 0.9 mm), cells a = 21 px (4.7 mm) by b = 25 px (5.6 mm).
# Heights read from the iso and back photos' shading (the rim's lit top edge and its shadow on the shell, 5 to 7 px
# at 0.21 to 0.25 mm/px): rim 1.5 mm above the shell, the lattice 0.6 mm under the rim's top.
CROWN_RIM_H = 0.0015
CROWN_BAR_H = 0.0009
CROWN_BAR_W = 0.00085
CROWN_CORNER_PX = 9.0             # the insert's rounded corners (top photo px, radius about 2 mm)

# The rear exhaust slots (Pinata back photo px, his left; traced: pixels darker than 70, closed, filled). Through the
# solved back camera (0.194 mm/px at the slot): 30.5 x 6.1 mm. Leatt's back photos show the slot sunk into the
# shell, its edge rounded down into it (a lit band over its top edge, 8 to 10 px, a lit facet at its outer end): a
# lip rising 1.0 mm to a rounded crest at the slot's edge, 2.0 mm wide along the top, 1.0 mm round the rest, its
# inner wall dark (the shell is closed: the lip stands for the recess's edge).
REAR_SLOT_PX = [(796.5, 734.0), (835.0, 733.5), (839.5, 739.0), (837.5, 746.0), (827.0, 760.5), (800.0, 762.5),
                (704.0, 762.5), (698.5, 758.0), (690.5, 739.0), (696.0, 735.5)]
REAR_SLOT_H = 0.0010
REAR_SLOT_W = (0.0010, 0.0020)    # m, round the sides and bottom; along the top edge

# The rear lower white pieces round the lower rear vents (Pinata back photo px, his left; the slot traced darker than
# 80). The slot sits where the shell turns from the back to the side, seen at a grazing 0.13 to 0.43 cosine from
# both cameras that see it; through the solved cameras it is 60 x 10 mm (back, 0.202 mm/px) and 59 x 17 mm (V25
# iso-left, its own trace), z -110 to -68 mm. The white piece (Pinata: white among the black print; V25 white: its
# lit edges): a raised frame, outside the slot's outer edge 8 to 13 px in the back photo (rows 1430 to 1520), 4.4 to
# 5.8 mm on the shell, and its lower end drawn out to a point 42 px (11 mm) under the slot (px 483, 1551 to 1593).
# Height 2 mm (its lit edge and shadow in the V25 iso view). The across-slot sizes carry the grazing view's
# uncertainty (a few mm).
LOW_VENT_PX = [(465.5, 1417.0), (478.0, 1417.5), (491.0, 1420.5), (495.5, 1425.0), (497.5, 1432.0), (490.5, 1505.0),
               (484.5, 1547.0), (482.0, 1551.5), (469.5, 1525.0), (469.5, 1478.0), (466.5, 1447.0), (461.5, 1422.0),
               (461.5, 1419.0)]
LOW_PIECE_H = 0.0020
LOW_PIECE_W = 0.0045
LOW_PIECE_TIP = 0.0070            # m, the point's length under the frame's lower edge (11 mm under the slot)
LOW_FLOOR_H = 0.0003              # m, the slot's dark floor over the shell: the frame's white walls show 1.7 mm deep


def camera(view):
    C, R, f = H.cam_from(H.CAMS[view])
    return C, R, f


def rays(view, uv):
    C, R, f = camera(view)
    uv = np.atleast_2d(np.asarray(uv, float))
    d = np.c_[(uv[:, 0] - 960) / f, -(uv[:, 1] - 960) / f, np.ones(len(uv))] @ R
    return C, d / np.linalg.norm(d, axis=1)[:, None]


class Shell:
    """The outer shell for casting rays onto (one side's triangles near the feature) with smooth normals."""

    def __init__(self, Vo, Fo):
        self.V, self.F = Vo, Fo
        self.N = H.normals(Vo, Fo)
        from scipy.spatial import cKDTree
        self.tree = cKDTree(Vo)

    def snap(self, Q, it=2):
        """Points moved onto the shell (the tangent plane of the nearest vertex, twice) and their normals: a frame's
        outer edge offset along the tangent would sink into a concave stretch or float over a convex one."""
        for _ in range(it):
            j = self.tree.query(Q)[1]
            Q = Q - self.N[j] * np.sum((Q - self.V[j]) * self.N[j], 1)[:, None]
        return Q, self.N[j]

    def cast(self, view, uv, side=1.0):
        C, D = rays(view, uv)
        V, F = self.V, self.F
        sel = np.nonzero(np.sign(V[F].mean(1)[:, 0]) == side)[0]
        v0 = V[F[sel, 0]]
        e1, e2 = V[F[sel, 1]] - v0, V[F[sel, 2]] - v0
        P, N = np.zeros((len(D), 3)), np.zeros((len(D), 3))
        for k, d in enumerate(D):
            p = np.cross(d, e2)
            det = (e1 * p).sum(1)
            ok = np.abs(det) > 1e-14
            inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
            t0 = C - v0
            u = (t0 * p).sum(1) * inv
            q = np.cross(t0, e1)
            w = (q @ d) * inv
            t = (e2 * q).sum(1) * inv
            hit = ok & (u >= 0) & (w >= 0) & (u + w <= 1) & (t > 0)
            if not hit.any():
                raise ValueError("ray %d of %s misses the shell" % (k, view))
            j = np.argmin(np.where(hit, t, np.inf))
            f = F[sel[j]]
            P[k] = C + t[j] * d
            n = (1 - u[j] - w[j]) * self.N[f[0]] + u[j] * self.N[f[1]] + w[j] * self.N[f[2]]
            N[k] = n / np.linalg.norm(n)
        return P, N


def resample_loop(P, step):
    """A closed polyline resampled at about step (px or m) along its length."""
    Q = np.vstack([P, P[:1]])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    n = max(8, int(round(s[-1] / step)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[[np.interp(t, s, Q[:, k]) for k in range(Q.shape[1])]].T


def round_corners(P, r, n=4):
    """A polygon's corners rounded with radius r (same units), n points per corner."""
    out = []
    m = len(P)
    for i in range(m):
        a, b, c = P[i - 1], P[i], P[(i + 1) % m]
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        u, v = u / lu, v / lv
        ang = math.acos(np.clip(u @ v, -1, 1))
        d = min(r / math.tan(ang / 2), 0.45 * lu, 0.45 * lv)
        p0, p1 = b + u * d, b + v * d
        for t in np.linspace(0, 1, n):                  # a quadratic Bezier through the corner
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p1)
    return np.array(out)


def outward(P, N):
    """In-surface unit directions away from a closed loop's inside."""
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    o = np.cross(t, N)
    o /= np.linalg.norm(o, axis=1)[:, None]
    c = P.mean(0)
    if np.mean(np.sum(o * (P - c), 1)) < 0:
        o = -o
    return o


def loop_faces(rings, n):
    """Quads between consecutive closed rings of n points (indices into the stacked rings)."""
    F = []
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append([k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i])
    return F


def orient(V, F, N_ref, P_ref):
    """Flip all faces if their normals point into the shell on average (the top faces must face outwards)."""
    F = np.asarray(F)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    fn = np.cross(b - a, c - a)
    from scipy.spatial import cKDTree
    j = cKDTree(P_ref).query(V[F].mean(1))[1]
    return F[:, ::-1] if np.sum(np.sum(fn * N_ref[j], 1)) < 0 else F


def frame(P, N, w, h, shell, ramp=False):
    """A raised moulded frame round a closed loop on the shell: inner wall at the loop, top h above the shell, outer
    edge w (per point) outside it on the shell, both walls from SINK under the surface, edges rounded by BEVEL.
    ramp: the top falls from a rounded crest at the loop to the shell at the outer edge (a lip into a recess).
    Returns V, F and the inner wall's faces (a mask)."""
    o = outward(P, N)
    w = np.broadcast_to(np.asarray(w, float), (len(P),))[:, None]
    Q, NQ = shell.snap(P + o * w)
    b = min(BEVEL, h / 3)
    if ramp:
        M, NM = shell.snap(P + o * w * 0.45)
        rings = [P - N * SINK, P + N * (h - b), P + o * b + N * h, M + NM * (0.6 * h), Q + NQ * 0.00005,
                 Q + o * 0.0002 - NQ * SINK]
    else:
        rings = [P - N * SINK, P + N * (h - b), P + o * b + N * h, Q - o * b + NQ * h, Q + NQ * (h - b),
                 Q + o * (0.3 * h) - NQ * SINK]
    V = np.vstack(rings)
    F = loop_faces(rings, len(P))
    # the top must face out: the ring order runs inner wall -> top -> outer wall
    F = orient(V, F, N, P)
    wall = np.arange(len(F)) < len(P)
    return V, F, wall


def cap(P, N, h, shell):
    """The slot's floor: the loop's inside on the shell, h above it (rings shrinking to the centre, each on the
    shell), facing out."""
    c = P.mean(0)
    rings, norms = [], []
    for s_ in (1.0, 0.67, 0.34):
        R_, NR = shell.snap(c + (P - c) * s_)
        rings.append(R_ + NR * h)
    c0, nc = shell.snap(c[None])
    n = len(P)
    V = np.vstack(rings + [c0 + nc * h])
    F = [list(f) for f in loop_faces(rings, n)]
    F += [[3 * n, (i + 1) % n + 2 * n, i + 2 * n] for i in range(n)]
    tri = np.array([f[:3] for f in F])
    fn = np.cross(V[tri[:, 1]] - V[tri[:, 0]], V[tri[:, 2]] - V[tri[:, 0]])
    if np.sum(fn @ N.mean(0)) < 0:
        F = [f[::-1] for f in F]
    return V, F


def bar(P, N, w, h):
    """A lattice bar along a polyline on the shell: a box w wide, from SINK under the surface to h above it."""
    t = np.gradient(P, axis=0)
    s = np.cross(N, t)
    s /= np.linalg.norm(s, axis=1)[:, None]
    rings = [P - s * w / 2 - N * SINK, P - s * w / 2 + N * h, P + s * w / 2 + N * h, P + s * w / 2 - N * SINK]
    n = len(P)
    V = np.vstack(rings)
    F = []
    for k in range(3):
        for i in range(n - 1):
            F.append([k * n + i, k * n + i + 1, (k + 1) * n + i + 1, (k + 1) * n + i])
    for i in (0, n - 1):                                 # end caps
        F.append([i, n + i, 2 * n + i, 3 * n + i])
    F = np.array(F)
    a, b2, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    top = slice(n - 1, 2 * (n - 1))
    if np.sum(np.cross(b2 - a, c - a)[top] * N[:-1]) < 0:
        F = F[:, ::-1]
    return V, F


def lattice_lines(cv):
    """The crown vent's lattice bars as segments in photo px clipped to the opening: lines s = k, t = k and
    s - t = k in the cell coordinates (s, t) = M (uv - origin), M = [a b]^-1."""
    from matplotlib.path import Path
    A = np.array([cv["a"], cv["b"]], float).T
    o = np.asarray(cv["origin"], float)
    op = Path(np.asarray(cv["opening"], float))
    segs = []
    dirs = (np.array([0.0, 1.0]), np.array([1.0, 0.0]), np.array([1.0, 1.0]))
    for fam, dvec in enumerate(dirs):
        for k in range(-12, 13):
            base = np.array([k, 0.0]) if fam == 0 else (np.array([0.0, k]) if fam == 1 else np.array([k, 0.0]))
            ts = np.linspace(-15, 15, 1201)
            st = base[None] + ts[:, None] * dvec[None]
            uv = o + st @ A.T
            ins = op.contains_points(uv, radius=-1.0)
            if ins.sum() < 4:
                continue
            idx = np.nonzero(ins)[0]
            a, b = uv[idx[0]], uv[idx[-1]]
            ext = (b - a) / np.linalg.norm(b - a) * 3.0   # into the rim by 3 px each end (hidden under it)
            segs.append((a - ext, b + ext))
    return segs


def crown_vent(shell, side):
    import helmet_art as A
    cv = A.CROWN_VENT
    m = (lambda P: P) if side < 0 else (lambda P: P * [-1, 1, 1])
    ins = round_corners(np.asarray(cv["insert"], float), CROWN_CORNER_PX)
    opn = round_corners(np.asarray(cv["opening"], float), CROWN_CORNER_PX * 0.6)
    opn = resample_loop(opn, 3.0)
    # the insert's outer edge, sampled where the opening is (same count, nearest by angle about the centre)
    c = opn.mean(0)
    ins = resample_loop(ins, 1.0)
    ang_i = np.arctan2(*(ins - c).T[::-1])
    ang_o = np.arctan2(*(opn - c).T[::-1])
    j = np.argmin(np.abs(np.angle(np.exp(1j * (ang_o[:, None] - ang_i[None])))), 1)
    P, N = shell.cast(cv["view"], opn, side=-1.0)
    Pi, _ = shell.cast(cv["view"], ins[j], side=-1.0)
    o = outward(P, N)
    w = np.clip(np.sum((Pi - P) * o, 1), 0.0012, 0.0035)
    parts = [frame(P, N, w, CROWN_RIM_H, shell)[:2]]
    for a, b in lattice_lines(cv):
        n = max(3, int(np.linalg.norm(b - a) / 4.0) + 1)
        uv = a + (b - a) * np.linspace(0, 1, n)[:, None]
        Q, NQ = shell.cast(cv["view"], uv, side=-1.0)
        parts.append(bar(Q, NQ, CROWN_BAR_W, CROWN_BAR_H))
    return [(m(V), F if side < 0 else F[:, ::-1]) for V, F in parts]


def slot_frame(shell, view, px, w, h, tip=0.0, side=1.0, ramp=False, floor=None):
    """A surround round a slot traced in a photo (his left), mirrored to his right with side -1: pieces (V, F, mats)
    with the frame in MAT, its inner wall in MAT_DARK when it is a lip (ramp), and the slot's floor (floor: its
    height above the shell) in MAT_DARK."""
    uv = resample_loop(np.asarray(px, float), 3.0)
    P, N = shell.cast(view, uv, side=1.0)
    if isinstance(w, tuple):                            # (sides and bottom, top): by height within the slot
        z = (P[:, 2] - P[:, 2].min()) / np.ptp(P[:, 2])
        w = w[0] + (w[1] - w[0]) * np.clip((z - 0.6) / 0.3, 0, 1)
    w = np.broadcast_to(np.asarray(w, float), (len(P),)).copy()
    if tip:
        o = outward(P, N)
        low = np.argmin(P[:, 2])
        d = np.linalg.norm(P - P[low], axis=1)
        k = np.clip(1 - d / 0.006, 0, 1)
        k = k * k * (3 - 2 * k)
        down = -np.cross(np.cross(N[low], [0, 0, 1.0]), N[low])     # down the surface
        down /= np.linalg.norm(down)
        w = w + k * tip * np.clip(np.sum(o * down, 1), 0, 1)
    V, F, wall = frame(P, N, w, h, shell, ramp=ramp)
    out = [(V, [list(f) for f in F], [MAT_DARK if (ramp and k) else MAT for k in wall])]
    if floor is not None:
        Vc, Fc = cap(P, N, floor, shell)
        out.append((Vc, Fc, [MAT_DARK] * len(Fc)))
    if side < 0:
        out = [(V * [-1, 1, 1], [f[::-1] for f in F], m) for V, F, m in out]
    return out


def build(Vo, Fo, part=None):
    """The detail as one Part (helmet frame): the crown vents in MAT_INSERT, the rear pieces in MAT, the slots'
    depths in MAT_DARK."""
    shell = Shell(Vo, Fo)
    part = part or H.Part(PART)
    pieces = []
    for side in (1.0, -1.0):
        pieces += [(V, [list(f) for f in F], [MAT_INSERT] * len(F)) for V, F in crown_vent(shell, side)]
        pieces += slot_frame(shell, "back", REAR_SLOT_PX, REAR_SLOT_W, REAR_SLOT_H, side=side, ramp=True)
        pieces += slot_frame(shell, "back", LOW_VENT_PX, LOW_PIECE_W, LOW_PIECE_H, tip=LOW_PIECE_TIP, side=side,
                             floor=LOW_FLOOR_H)
    for V, F, mats in pieces:
        part.add(V, F, mats)
    return part


def measure():
    """The traced features' sizes through the solved cameras (research/helmet-ba.json), mm."""
    import helmet_ba as B
    import helmet_art as A
    cams = B.solved_cameras()
    Vm, Fm, _, _ = B.model_mesh()
    out = {}
    for name, view, px in (("crown vent insert", "pin_top", A.CROWN_VENT["insert"]),
                           ("crown vent opening", "pin_top", A.CROWN_VENT["opening"]),
                           ("rear exhaust slot", "pin_back", REAR_SLOT_PX),
                           ("lower rear vent slot", "pin_back", LOW_VENT_PX)):
        c = cams[view]
        P = [B.raycast(Vm, Fm, c["C"], B.ray(c, u, v)) for u, v in px]
        P = np.array([p for p in P if p is not None])
        Q = P - P.mean(0)
        vt = np.linalg.svd(Q, full_matrices=False)[2]
        e = Q @ vt[:2].T
        mmpx = np.linalg.norm(P.mean(0) - c["C"]) / c["f"] * 1000
        out[name] = (round(float(np.ptp(e[:, 0])) * 1000, 1), round(float(np.ptp(e[:, 1])) * 1000, 1),
                     np.round(P.mean(0) * 1000, 1).tolist(), round(float(mmpx), 3))
    return out


if __name__ == "__main__":
    for k, v in measure().items():
        print("%-22s %5.1f x %5.1f mm at %s mm, %.3f mm/px" % (k, v[0], v[1], v[2], v[3]))
