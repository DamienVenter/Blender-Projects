"""Moulded detail away from the helmet's front, as geometry (helmet round 3, decision 46): the crown's two mesh vents
(a raised white insert round a triangle lattice over the dark opening), the two rear exhaust slots' wire mesh and
the rear lower white pieces round the lower rear vents. The front's detail (grip panels, the trim's roll, brow
and chin vents, chin LEATT, brow tag) waits for phase B, because the front moves.

Each outline is traced in one of Leatt's Pinata photos (px) and cast onto the shell through that photo's camera in
helmet.PRINT_CAMS (round 4: the cameras solved with all of Leatt's photos, research/helmet-ba.json), the cameras the
print is traced through, so the geometry stands on its own print (the painted dark openings, the white of the rear
lower pieces). Sizes are measured at 1:1 against those cameras (mm per px at the feature, helmet_ba.py): see the
tables' comments and the ledger, sections 6 and 7.
All in the HELMET frame (metres, x his left, y back, z up); the right side is the mirror of the left.
"""
import numpy as np

import helmet as H

PART = "helmet_vents"
MAT = "helmet_moulded"           # the rear surrounds and lower pieces: the shell's own white under its clear coat
MAT_INSERT = "helmet_vent_insert"  # the crown vents' insert and lattice: white plastic, satin
MAT_DARK = "helmet_trim"          # the slots' depth (the trim's black, helmet.MATERIALS)
MAT_MESH = "helmet_vent_mesh"     # the rear slots' wire mesh
SINK = 0.0006                     # m, walls start this far under the shell's surface (no gap on a curved shell)

# The crown vents: helmet_art.CROWN_VENT (top photo px, the vent on his right; the left is its mirror). Round 4
# (decision 50): Leatt's outline is a rounded parallelogram with a thin, even surround and its lattice near-equilateral
# triangles (helmet_art's table). Through the solved top camera (0.248 mm/px at the vent): the rim 8 px, 2.0 mm, as
# one width on the shell all round (the insert's outer edge is the opening's offset on the shell, so its corners
# round with the opening's); cells 24 px (6.0 mm) a side; bars 4.5 to 5 px wide in the photo at 3x, and the built
# bar's top plus its lit wall read 1 px wider through that camera (render at 3x, round 4): 1.0 mm. Heights read from
# the iso and back photos' shading (the rim's lit top edge and its shadow on the shell, 5 to 7 px at 0.21 to 0.25
# mm/px): rim 1.5 mm above the shell, the lattice 0.6 mm under the rim's top. The rim is a flat plate with crisp
# edges (plate()): the photo at 3x shows a flat white top, a bright line along its inner edge and a thin grey line
# at its outer edge; round 4's first build, a frame with shared vertices, shaded as a soft round tube.
CROWN_RIM_H = 0.0015
CROWN_RIM_W = 0.0020
CROWN_BAR_H = 0.0009
CROWN_BAR_W = 0.0010

# The rear exhaust slots (Pinata back photo px, his left; traced: pixels darker than 70, closed, filled). Through the
# solved back camera (0.194 mm/px at the slot): 30.5 x 6.1 mm. Leatt's back photos show the slot sunk into the
# shell, its edge rounded down into it (a lit band over its top edge, 8 to 10 px, a lit facet at its outer end), no
# rim. Round 3 stood a lip 1.0 mm proud for that edge: it read as a bright rim. Round 4 rendered it at 3x in that
# view as a lip 0.4 mm proud (crest rounded 0.3 mm, falling to the shell 1.5 to 2.5 mm away), 0.2 mm proud, and as a
# thin dark edge: under the clear coat any raised edge shows a bright line, and the dark edge a black outline. The
# shell stays closed (no recess), so the slot is the print's dark with the wire mesh in it, nothing raised round it.
REAR_SLOT_PX = [(796.5, 734.0), (835.0, 733.5), (839.5, 739.0), (837.5, 746.0), (827.0, 760.5), (800.0, 762.5),
                (704.0, 762.5), (698.5, 758.0), (690.5, 739.0), (696.0, 735.5)]
REAR_MESH_H = 0.0002              # m, the mesh's top over the shell

# The rear lower white pieces round the lower rear vents (Pinata back photo px, his left; the slot traced darker than
# 80). The slot sits where the shell turns from the back to the side, seen at a grazing 0.13 to 0.43 cosine from
# both cameras that see it; through the solved cameras it is 60 x 10 mm (back, 0.202 mm/px) and 59 x 17 mm (V25
# iso-left, its own trace), z -110 to -68 mm. The white piece (Pinata: white among the black print; V25 white: its
# lit edges): a raised frame, outside the slot's outer edge 8 to 13 px in the back photo (rows 1430 to 1520), 4.4 to
# 5.8 mm on the shell, and its lower end drawn out to a point 42 px (11 mm) under the slot (px 483, 1551 to 1593).
# Height 2 mm (its lit edge and shadow in the V25 iso view). The across-slot sizes carry the grazing view's
# uncertainty (a few mm).
# Round 4 (decision 50): Leatt's piece is a flat plate (back photos at 4x: Pinata, V25 white, Royal), main's a thick
# round loop. A flat top 2 mm over the shell with crisp edges (each face band has its own vertices, so the shading
# breaks at the edges; a 0.2 mm chamfer catches the light), 10 px wide round the slot in the back photo (the outer
# side 10 px, the top 12), its lower end two straight sides to a sharp point at px (481.5, 1594.5), 43 px under
# the slot's end. That point is the raised top's: the back camera sees the piece at a cosine of 0.42 there, and a top
# 2 mm over the shell shows 8 px to the left of its foot (round 4's first build, the foot on the photo's point:
# its top's point 8.3 px left of Leatt's at 2x), so the foot's point is placed for the top's point to land on it.
# A dark wire mesh fills the slot: two sets of wires 40 deg either side of its long axis, 1.6 mm apart (the back
# photos' mesh: 6 to 8 px between wires at 0.2 mm/px), 0.35 mm thick, its top 0.9 mm over the shell.
LOW_VENT_PX = [(465.5, 1417.0), (478.0, 1417.5), (491.0, 1420.5), (495.5, 1425.0), (497.5, 1432.0), (490.5, 1505.0),
               (484.5, 1547.0), (482.0, 1551.5), (469.5, 1525.0), (469.5, 1478.0), (466.5, 1447.0), (461.5, 1422.0),
               (461.5, 1419.0)]
LOW_PIECE_H = 0.0020
LOW_PIECE_PX = 10.0               # photo px, the plate's width round the slot
LOW_PIECE_TIP_PX = (481.5, 1594.5)
LOW_FLOOR_H = 0.0003              # m, the slot's dark floor over the shell: the frame's white walls show 1.7 mm deep
LOW_MESH_H = 0.0009
PLATE_CHAMFER = 0.0002
MESH_PITCH = 0.0016
MESH_W = 0.00035
MESH_ANGLE = 40.0                 # deg either side of the slot's long axis


def camera(view):
    C, R, f = H.cam_from(H.PRINT_CAMS[view])
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


def plate(P, N, Q, NQ, h):
    """A flat plate between a slot's loop P and its outer edge Q on the shell (point for point): a flat top h above the
    shell, inner and outer walls from SINK under it, a PLATE_CHAMFER on both top edges. Each band (inner wall,
    chamfer, top, chamfer, outer wall) has its own vertices, so smooth shading breaks at the edges: crisp, as Leatt's
    moulded piece. Returns V, F."""
    o, oq = outward(P, N), outward(Q, NQ)
    c = min(PLATE_CHAMFER, h / 4)
    bands = [(P - N * SINK, P + N * (h - c)), (P + N * (h - c), P + o * c + N * h),
             (P + o * c + N * h, Q - oq * c + NQ * h), (Q - oq * c + NQ * h, Q + NQ * (h - c)),
             (Q + NQ * (h - c), Q + oq * (0.15 * h) - NQ * SINK)]
    n = len(P)
    V, F = [], []
    for k, (A_, B_) in enumerate(bands):
        V += [A_, B_]
        F += [[i + 2 * n * k for i in f] for f in loop_faces([A_, B_], n)]
    V = np.vstack(V)
    return V, orient(V, F, N, P)


def plate_outline(px, wpx, tip):
    """A slot's outline (photo px, resampled) and, point for point, the plate's outer edge: the outline grown wpx
    along its outward normals and joined to the tip by straight sides (their convex hull), each slot point's outer
    point where its outward ray meets that edge; the slot's lowest point's is the tip itself."""
    from scipy.spatial import ConvexHull
    p = resample_loop(np.asarray(px, float), 3.0)
    t = np.roll(p, -1, 0) - np.roll(p, 1, 0)
    n2 = np.c_[t[:, 1], -t[:, 0]] / np.linalg.norm(t, axis=1)[:, None]
    if np.mean(np.sum((p - p.mean(0)) * n2, 1)) < 0:
        n2 = -n2
    allp = np.vstack([p + n2 * wpx, np.asarray(tip, float)[None]])
    hull = allp[ConvexHull(allp).vertices]
    q = np.zeros_like(p)
    for i, (pi, ni) in enumerate(zip(p, n2)):
        best = np.inf
        for a, b in zip(hull, np.roll(hull, -1, 0)):
            M = np.array([ni, a - b]).T
            if abs(np.linalg.det(M)) < 1e-9:
                continue
            s, r = np.linalg.solve(M, a - pi)
            if s > 0 and -1e-9 <= r <= 1 + 1e-9:
                best = min(best, s)
        q[i] = pi + ni * best
    q[np.argmax(p[:, 1])] = tip
    return p, q


def mesh_wires(P, N, shell, h, inset=0.0004):
    """A wire mesh across a slot's loop P on the shell: two sets of straight wires MESH_ANGLE either side of the
    slot's long axis, MESH_PITCH apart, MESH_W thick, from SINK under the shell to h over it, ending inset inside
    the loop (under its wall). Returns [(V, F)]."""
    from matplotlib.path import Path
    c = P.mean(0)
    n = N.mean(0) / np.linalg.norm(N.mean(0))
    T = (P - c) - np.outer((P - c) @ n, n)
    e1 = np.linalg.svd(T, full_matrices=False)[2][0]
    e2 = np.cross(n, e1)
    xy = np.c_[T @ e1, T @ e2]
    cen = xy.mean(0)
    shrink = Path(cen + (xy - cen) * (1 - inset / np.maximum(np.linalg.norm(xy - cen, axis=1), 1e-6))[:, None])
    out = []
    R = np.abs(xy).max() * 1.5
    for sgn in (1.0, -1.0):
        a = np.radians(MESH_ANGLE) * sgn
        dv, nv = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
        for k in range(-int(R / MESH_PITCH) - 1, int(R / MESH_PITCH) + 2):
            s = np.linspace(-R, R, int(2 * R / 0.0002) + 1)
            pts = cen + nv * (k * MESH_PITCH) + s[:, None] * dv
            ins = shrink.contains_points(pts)
            if ins.sum() < 3:
                continue
            idx = np.nonzero(ins)[0]
            runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
            for run in runs:
                if len(run) < 3:
                    continue
                m = max(2, int(np.ptp(s[run]) / 0.001) + 1)
                st = np.linspace(pts[run[0]], pts[run[-1]], m)
                Q, NQ = shell.snap(c + st[:, :1] * e1 + st[:, 1:] * e2)
                out.append(bar(Q, NQ, MESH_W, h))
    return out


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
    opn = resample_loop(A.vent_outline("opening"), 2.0)
    P, N = shell.cast(cv["view"], opn, side=-1.0)
    Q, NQ = shell.snap(P + outward(P, N) * CROWN_RIM_W)
    parts = [plate(P, N, Q, NQ, CROWN_RIM_H)]
    for a, b in lattice_lines(cv):
        n = max(3, int(np.linalg.norm(b - a) / 4.0) + 1)
        uv = a + (b - a) * np.linspace(0, 1, n)[:, None]
        Q, NQ = shell.cast(cv["view"], uv, side=-1.0)
        parts.append(bar(Q, NQ, CROWN_BAR_W, CROWN_BAR_H))
    return [(m(V), F if side < 0 else F[:, ::-1]) for V, F in parts]


def mirror(out, side):
    """Pieces (V, F, mats) of his left as they are, or mirrored to his right (side -1)."""
    if side < 0:
        return [(V * [-1, 1, 1], [list(f)[::-1] for f in F], m) for V, F, m in out]
    return [(V, [list(f) for f in F], m) for V, F, m in out]


def rear_slot(shell, side=1.0):
    """A rear exhaust slot's wire mesh (MAT_MESH) over its printed dark."""
    uv = resample_loop(np.asarray(REAR_SLOT_PX, float), 3.0)
    P, N = shell.cast("back", uv, side=1.0)
    out = [(Vm, Fm, [MAT_MESH] * len(Fm)) for Vm, Fm in mesh_wires(P, N, shell, REAR_MESH_H)]
    return mirror(out, side)


def low_piece(shell, side=1.0):
    """A rear lower piece: the flat plate (MAT) round the slot, to its point, the slot's dark floor (MAT_DARK) and
    its mesh (MAT_MESH)."""
    want = np.asarray(LOW_PIECE_TIP_PX, float)
    tip = want.copy()
    for _ in range(3):                                   # the top's point on the photo's (see LOW_PIECE_TIP_PX)
        p, q = plate_outline(LOW_VENT_PX, LOW_PIECE_PX, tip)
        k = np.argmax(p[:, 1])
        T, NT = shell.snap(shell.cast("back", q[k:k + 1], side=1.0)[0])
        tip = tip + want - H.cam_project(H.PRINT_CAMS["back"], T + NT * LOW_PIECE_H)[0][0]
    P, N = shell.cast("back", p, side=1.0)
    Q, NQ = shell.cast("back", q, side=1.0)
    Q, NQ = shell.snap(Q)
    V, F = plate(P, N, Q, NQ, LOW_PIECE_H)
    out = [(V, F, [MAT] * len(F))]
    Vc, Fc = cap(P, N, LOW_FLOOR_H, shell)
    out.append((Vc, Fc, [MAT_DARK] * len(Fc)))
    out += [(Vm, Fm, [MAT_MESH] * len(Fm)) for Vm, Fm in mesh_wires(P, N, shell, LOW_MESH_H)]
    return mirror(out, side)


def build(Vo, Fo, part=None):
    """The detail as one Part (helmet frame): the crown vents in MAT_INSERT, the rear lower pieces in MAT, their
    slots' floor in MAT_DARK, the slots' wire mesh in MAT_MESH."""
    shell = Shell(Vo, Fo)
    part = part or H.Part(PART)
    pieces = []
    for side in (1.0, -1.0):
        pieces += [(V, [list(f) for f in F], [MAT_INSERT] * len(F)) for V, F in crown_vent(shell, side)]
        pieces += rear_slot(shell, side)
        pieces += low_piece(shell, side)
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
    for name, view, px in (("crown vent insert", "pin_top", A.vent_outline("insert")),
                           ("crown vent opening", "pin_top", A.vent_outline("opening")),
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
