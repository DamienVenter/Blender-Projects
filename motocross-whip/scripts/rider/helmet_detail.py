"""Moulded detail away from the helmet's front, as geometry (helmet round 3, decision 46): the crown's two mesh vents
(a raised white insert round a triangle lattice over the dark opening), the two rear exhaust slots' wire mesh and
the rear lower white pieces round the lower rear vents; and (joint front fit phase 2, decision 51) the eye port's
grip panels with their triangle relief, the textures of the port's trim roll and pads (helmet.strip_rings), and
the chin's mouthpiece (its black frame, dark floor and triangle lattice), the brow's mesh vents and its tag.

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


class ExactShell(Shell):
    """The shell, its snap exact: the closest point on its triangles and the normal interpolated there. The nearest
    vertex's tangent plane is close enough on the crown's even mesh, but where the brow's lower edge folds into the
    trim's roll it put the brow vents' wires 1.3 mm under their floor (phase 2)."""

    def __init__(self, Vo, Fo):
        super().__init__(Vo, Fo)
        from scipy.spatial import cKDTree
        self.ftree = cKDTree(Vo[Fo].mean(1))

    def snap(self, Q, it=2, k=12):
        """Mirror-exact: each point is snapped as its image on his left and carried back (the triangles' diagonals
        are not mirrored, and the brow's centre vent must be)."""
        Q = np.atleast_2d(Q)
        sx = np.where(Q[:, 0] < 0, -1.0, 1.0)[:, None] * [1, 0, 0] + [0, 1, 1]
        P, N = self._closest(Q * sx, k)
        on = np.abs(Q[:, 0]) < 1e-9
        P[on, 0], N[on, 0] = 0.0, 0.0
        return P * sx, N * sx / np.linalg.norm(N, axis=1)[:, None]

    def _closest(self, Q, k):
        j = self.ftree.query(Q, k)[1]
        f = self.F[j]
        a, b, c = self.V[f[..., 0]], self.V[f[..., 1]], self.V[f[..., 2]]
        p = Q[:, None, :]
        ab, ac, ap = b - a, c - a, p - a
        d00, d01, d11 = (ab * ab).sum(-1), (ab * ac).sum(-1), (ac * ac).sum(-1)
        d20, d21 = (ap * ab).sum(-1), (ap * ac).sum(-1)
        den = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        inside = (v >= 0) & (w >= 0) & (v + w <= 1)
        best, P, B, F3 = np.full(len(Q), np.inf), np.zeros_like(Q), np.zeros((len(Q), 3)), np.zeros((len(Q), 3), int)
        r = np.arange(len(Q))
        cands = [(a + v[..., None] * ab + w[..., None] * ac, inside, np.stack([1 - v - w, v, w], -1))]
        for e0, e1, i0, i1 in ((a, b, 0, 1), (b, c, 1, 2), (c, a, 2, 0)):
            e = e1 - e0
            t = np.clip(((p - e0) * e).sum(-1) / (e * e).sum(-1), 0, 1)
            bc = np.zeros(t.shape + (3,))
            bc[..., i0], bc[..., i1] = 1 - t, t
            cands.append((e0 + t[..., None] * e, np.ones_like(t, bool), bc))
        for q, ok, bc in cands:
            d = np.where(ok, np.linalg.norm(p - q, axis=-1), np.inf)
            i = np.argmin(d, 1)
            better = d[r, i] < best
            best[better] = d[r, i][better]
            P[better] = q[r, i][better]
            B[better] = bc[r, i][better]
            F3[better] = f[r, i][better]
        N = (B[..., None] * self.N[F3]).sum(1)
        return P, N / np.linalg.norm(N, axis=1)[:, None]


def resample_loop(P, step):
    """A closed polyline resampled at about step (px or m) along its length."""
    Q = np.vstack([P, P[:1]])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    n = max(8, int(round(s[-1] / step)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[[np.interp(t, s, Q[:, k]) for k in range(Q.shape[1])]].T


def round_corners(P, r, n=6):
    """A closed polygon (px) with each corner replaced by an arc of radius r tangent to its two edges (n points); each
    corner first moved out along its bisector by what the arc cuts off, so the arcs still reach the read corners."""
    P = np.asarray(P, float)
    Q = P.copy()
    for i, v in enumerate(P):
        u, w = P[i - 1] - v, P[(i + 1) % len(P)] - v
        u, w = u / np.linalg.norm(u), w / np.linalg.norm(w)
        th = 0.5 * np.arccos(np.clip(u @ w, -1, 1))
        Q[i] = v - (u + w) / np.linalg.norm(u + w) * (r / np.sin(th) - r)
    P = Q
    out = []
    for i, v in enumerate(P):
        u, w = P[i - 1] - v, P[(i + 1) % len(P)] - v
        u, w = u / np.linalg.norm(u), w / np.linalg.norm(w)
        th = 0.5 * np.arccos(np.clip(u @ w, -1, 1))
        c = v + (u + w) / np.linalg.norm(u + w) * r / np.sin(th)
        a0, a1 = v + u * r / np.tan(th) - c, v + w * r / np.tan(th) - c
        t0, t1 = np.arctan2(a0[1], a0[0]), np.arctan2(a1[1], a1[0])
        dt = (t1 - t0 + np.pi) % (2 * np.pi) - np.pi
        out += [c + r * np.array([np.cos(t0 + dt * k / (n - 1)), np.sin(t0 + dt * k / (n - 1))]) for k in range(n)]
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


def mesh_wires(P, N, shell, h, inset=0.0004, pitch=MESH_PITCH, w=MESH_W, angle=MESH_ANGLE):
    """A wire mesh across a slot's loop P on the shell: two sets of straight wires angle either side of the slot's
    long axis, pitch apart, w thick (the rear slots': MESH_ANGLE, MESH_PITCH, MESH_W), from SINK under the shell to h
    over it, ending inset inside the loop (under its wall). Returns [(V, F)]."""
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
        a = np.radians(angle) * sgn
        dv, nv = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
        for k in range(-int(R / pitch) - 1, int(R / pitch) + 2):
            s = np.linspace(-R, R, int(2 * R / 0.0002) + 1)
            pts = cen + nv * (k * pitch) + s[:, None] * dv
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
                out.append(bar(Q, NQ, w, h))
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


# ------------------------------------------------------------- the eye port's grip panels (phase 2, decision 51)
# Leatt's Pinata iso-left photo at 1:1 and 3x (px 1140 to 1320, 780 to 1060): beside the port's rear edge a moulded
# dark grey rubber panel with a triangle relief runs from the brow's corner down to the chin bar's top, between the
# port's cut edge (its crest, where the trim rolls in) and the paint. Read row by row through the solved iso-left
# camera (0.226 mm/px at the port's side): its inner edge is the port's cut edge, its outer edge the paint's edge
# (helmet_art.FORCE's port polygon, the same px). The panel stands GRIP_H proud of the shell: the paint's edge beside
# it shows a lit line 2 to 3 px wide at 1:1 (0.5 to 0.7 mm). The relief is moulded ridges (grip_relief): an
# equilateral triangle lattice with lines across the band and at 60 deg to it; its row period, 28 px down columns 1260
# and 1280 (autocorrelation, r 0.33 to 0.39), is 6.3 mm: cells 7.3 mm a side. At 2x the ridges' lit tops are 3 to 4
# px wide at 1:1 (0.7 to 0.9 mm) with a 2 px shadow beside them under the studio's high key light (0.5 mm high); some
# lattice edges are left out, so triangles merge into rhombi and trapezoids, and some triangles are filled solid
# (about 1 in 14 at 2x). Between the ridges the moulding is sandblasted: light flecks 1 px across at 2x (0.1 mm), the
# panel's normal map (grip_texture). Its tone (helmet.MATERIALS): see helmet_grip. A first version drew the lattice
# in the normal map only (lines 0.45 mm, 0.3 mm high): at 2x it read as thin dark grooves on a flat grey (p10 to p90
# 74 to 87 against the photo's 17 to 104).
GRIP_OUTER_PX = [(1350, 697), (1347, 735), (1331, 816), (1316, 897), (1300, 954), (1287, 1010), (1275, 1047),
                 (1262, 1085), (1256, 1097)]
GRIP_ROWS = (805.0, 1094.0)        # iso-left px rows, the port's side: above 805 its edge turns forward
                                   # along the brow; 1094, the chin bar's top
GRIP_H = 0.0006                    # m, the panel's top over the shell
GRIP_CELL = 0.0073                 # m, the triangles' side
GRIP_RIDGE_W = 0.0009             # m, the ridges' width
GRIP_RIDGE_H = 0.0005              # m, their height over the panel's top
GRIP_DROP = 0.12                   # the lattice's edges left out
GRIP_FILL = 0.07                   # its triangles filled solid
GRIP_GRAIN = (0.08, 0.015)         # mm: the sandblast grain's size (Gaussian sigma) and its height (rms)
GRIP_TILE = (0.008, 0.008)         # m, the grain's tile (u across the band, v along it)
GRIP_PX_MM = 16                    # texels per mm
MAT_GRIP = "helmet_grip"
MAT_GRIP_EDGE = "helmet_grip_edge"
MAT_GRIP_RIDGE = "helmet_grip_ridge"


def port_rows(shell, rows):
    """The port's rear (cut) edge on his left through the iso-left camera: per image row the rightmost crossing of
    the shell's free edges (above the lower edge, ahead of y = 0), as 3D points on the edge."""
    V, F = shell.V, shell.F
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    B = u[c == 1]
    m = V[B].mean(1)
    B = B[(m[:, 2] > -0.09) & (m[:, 1] < 0.0) & (m[:, 0] > 0)]
    q = H.cam_project(H.PRINT_CAMS["isoleft"], V)[0]
    out = []
    for r in rows:
        a, b = q[B[:, 0]], q[B[:, 1]]
        hit = np.nonzero((a[:, 1] - r) * (b[:, 1] - r) <= 0)[0]
        t = (r - a[hit, 1]) / (b[hit, 1] - a[hit, 1] + 1e-12)
        k = np.argmax(a[hit, 0] + t * (b[hit, 0] - a[hit, 0]))
        e = B[hit[k]]
        out.append(V[e[0]] + t[k] * (V[e[1]] - V[e[0]]))
    return np.array(out)


def grip_panel(shell, side=1.0):
    """A grip panel on his left (side 1) or right: a raised band on the shell between the port's cut edge and the
    paint's edge, its top in MAT_GRIP with UVs in GRIP_TILE units (the relief's normal map), its walls in
    MAT_GRIP_EDGE. Returns pieces (V, F, mats, uv)."""
    rows = np.arange(GRIP_ROWS[0], GRIP_ROWS[1] + 0.1, 5.0)
    I = port_rows(shell, rows)
    op = np.asarray(GRIP_OUTER_PX, float)
    O, _ = shell.cast("isoleft", np.c_[np.interp(rows, op[:, 1], op[:, 0]), rows], side=1.0)
    nt, ns = 8, len(rows)
    G, NG = [], []
    for t in np.linspace(0, 1, nt):
        Q, NQ = shell.snap(I + (O - I) * t)
        G.append(Q + NQ * GRIP_H)
        NG.append(NQ)
    G, NG = np.array(G), np.array(NG)                   # (nt, ns, 3): across, along
    along = np.r_[0, np.cumsum(np.linalg.norm(np.diff(G[0], axis=0), axis=1))]
    across = np.r_[np.zeros((1, ns)), np.cumsum(np.linalg.norm(np.diff(G, axis=0), axis=2), axis=0)]
    V = G.reshape(-1, 3)
    F, UV = [], []
    for k in range(nt - 1):
        for i in range(ns - 1):
            f = [k * ns + i, k * ns + i + 1, (k + 1) * ns + i + 1, (k + 1) * ns + i]
            F.append(f)
            UV.append([(across[j // ns, j % ns] / GRIP_TILE[0], along[j % ns] / GRIP_TILE[1]) for j in f])
    F = np.array(F)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    if np.sum(np.cross(b - a, c - a) * NG.reshape(-1, 3)[F[:, 0]]) < 0:
        F = F[:, ::-1]
        UV = [u[::-1] for u in UV]
    pieces = [(V, [list(f) for f in F], [MAT_GRIP] * len(F), UV)]
    pieces.append(grip_relief(G, NG, across, along))
    # walls all round, down to SINK under the shell, each with its own vertices (crisp edges)
    ring = ([(0, i) for i in range(ns)] + [(k, ns - 1) for k in range(1, nt)] +
            [(nt - 1, i) for i in range(ns - 2, -1, -1)] + [(k, 0) for k in range(nt - 2, 0, -1)])
    top = np.array([G[k, i] for k, i in ring])
    bot = np.array([G[k, i] - NG[k, i] * (GRIP_H + SINK) for k, i in ring])
    n = len(ring)
    Vw = np.vstack([top, bot])
    Fw = np.array([[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)])
    out_dir = top - top.mean(0)
    a, b, c = Vw[Fw[:, 0]], Vw[Fw[:, 1]], Vw[Fw[:, 2]]
    if np.sum(np.cross(b - a, c - a) * out_dir) < 0:
        Fw = Fw[:, ::-1]
    pieces.append((Vw, [list(f) for f in Fw], [MAT_GRIP_EDGE] * len(Fw), [[(0.5, 0.5)] * 4] * len(Fw)))
    if side < 0:
        pieces = [(V_ * [-1, 1, 1], [f[::-1] for f in F_], m_, [u[::-1] for u in uv_]) for V_, F_, m_, uv_ in pieces]
    return pieces


def lattice(w, h, cell=GRIP_CELL, seed=51):
    """The relief's equilateral triangle lattice over a band w x h (m; x across it from the port's edge, y along it
    from its top): its edges (a, b) across the band and at +-60 deg, GRIP_DROP of them left out, and the triangles
    filled solid (GRIP_FILL; their corners), seeded."""
    rng = np.random.default_rng(seed)
    hgt = cell * 3 ** 0.5 / 2
    edges, filled = [], []
    for r in range(-1, int(h / hgt) + 2):
        for c in range(-1, int(w / cell) + 2):
            p = np.array([c * cell + (cell / 2 if r % 2 else 0.0), r * hgt])
            for q in (p + [cell, 0.0], p + [cell / 2, hgt], p + [-cell / 2, hgt]):
                if rng.random() > GRIP_DROP:
                    edges.append((p, q))
            if rng.random() < GRIP_FILL:
                filled.append(np.array([p, p + [cell, 0.0], p + [cell / 2, hgt]]))
    return edges, filled


def grip_relief(G, NG, across, along):
    """The panel's triangle relief on its top G (nt across x ns along, normals NG; across, along: arc lengths, m):
    ridges GRIP_RIDGE_W wide standing GRIP_RIDGE_H, and the filled triangles at their height, kept a ridge's width
    inside the panel. One piece (V, F, mats, uv), in MAT_GRIP_RIDGE."""
    nt, ns = G.shape[:2]
    kk = np.arange(nt)
    m = GRIP_RIDGE_W

    def where(xy):
        """Points (x, y) on the band to the panel's top: P, N and whether inside its margin."""
        fi = np.interp(xy[:, 1], along, np.arange(ns))
        i0 = np.clip(np.floor(fi).astype(int), 0, ns - 2)
        w = (fi - i0)[:, None]
        P, N = [], []
        for i in (0, 1):
            col = i0 + i
            kf = np.array([np.interp(x, across[:, c], kk) for x, c in zip(xy[:, 0], col)])
            k0 = np.clip(np.floor(kf).astype(int), 0, nt - 2)
            t = (kf - k0)[:, None]
            P.append(G[k0, col] * (1 - t) + G[k0 + 1, col] * t)
            N.append(NG[k0, col] * (1 - t) + NG[k0 + 1, col] * t)
        P = P[0] * (1 - w) + P[1] * w
        N = N[0] * (1 - w) + N[1] * w
        N /= np.linalg.norm(N, axis=1)[:, None]
        width = np.interp(xy[:, 1], along, across[-1])
        ok = (xy[:, 0] > m) & (xy[:, 0] < width - m) & (xy[:, 1] > m) & (xy[:, 1] < along[-1] - m)
        return P, N, ok

    edges, filled = lattice(across[-1].max(), along[-1])
    Vs, Fs, UVs = [], [], []
    nv = 0
    for a, b in edges:
        xy = a + np.linspace(0, 1, int(np.ceil(np.linalg.norm(b - a) / 0.001)) + 1)[:, None] * (b - a)
        P, N, ok = where(xy)
        idx = np.nonzero(ok)[0]
        for run in np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1):
            if len(run) < 2:
                continue
            V, F = bar(P[run], N[run], GRIP_RIDGE_W, GRIP_RIDGE_H)
            uv = xy[run] / GRIP_TILE
            Vs.append(V)
            Fs += [[nv + j for j in f] for f in F]
            UVs += [[tuple(uv[j % len(run)]) for j in f] for f in F]
            nv += len(V)
    for tri in filled:
        P, N, ok = where(tri)
        if not ok.all():
            continue
        top, bot = P + N * GRIP_RIDGE_H, P - N * SINK
        V = np.vstack([top, bot])
        F = [[0, 1, 2]] + [[i, (i + 1) % 3, 3 + (i + 1) % 3, 3 + i] for i in range(3)]
        if np.cross(top[1] - top[0], top[2] - top[0]) @ N.mean(0) < 0:
            F = [f[::-1] for f in F]
        uv = tri / GRIP_TILE
        Vs.append(V)
        Fs += [[nv + j for j in f] for f in F]
        UVs += [[tuple(uv[j % 3]) for j in f] for f in F]
        nv += len(V)
    return np.vstack(Vs), Fs, [MAT_GRIP_RIDGE] * len(Fs), UVs


def normal_map(hf, height_mm, px_mm):
    """Tangent-space normal map (OpenGL: green up the texture's v) of a height field hf (0..1 x height_mm)."""
    z = hf * height_mm
    gy, gx = np.gradient(z, 1.0 / px_mm)
    gy = -gy                                            # image rows run down, v runs up
    n = np.dstack([-gx, -gy, np.ones_like(z)])
    n /= np.linalg.norm(n, axis=2)[..., None]
    return np.clip((n * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)


def grip_texture(path):
    """The grip panels' sandblast grain as a tileable normal map (GRIP_TILE, GRIP_PX_MM), seeded."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    W, Hh = int(round(GRIP_TILE[0] * 1000 * GRIP_PX_MM)), int(round(GRIP_TILE[1] * 1000 * GRIP_PX_MM))
    z = gaussian_filter(np.random.default_rng(51).standard_normal((Hh, W)), GRIP_GRAIN[0] * GRIP_PX_MM, mode="wrap")
    Image.fromarray(normal_map(z / z.std(), GRIP_GRAIN[1], GRIP_PX_MM)).save(path, optimize=True)


# The port's trim and the pads inside it (helmet.strip_rings): the trim's roll is black rubber ribbed across its
# length, the ribs' pitch read down the roll in Pinata iso-left at 1:1 (columns 1190 and 1200, rows 800 to 1040:
# autocorrelation peaks at 25 and 19 px, 5.6 and 4.3 mm; the stronger, r 0.41, taken); a rib 45 % of the pitch, 0.4
# mm high (its lit crest 2 px). The pads' face is a dark knit mesh: hexagonal holes 1.6 mm apart (the liner beside
# the trim at 2x, 6 to 7 px at about 0.24 mm/px), strands 50 48 52 over holes 10 10 11 (the photo's liner: holes 2 to
# 15, lit strands to 91 84 87 with their sheen; de-lit as the grip's tone), and a red stitch line 2.5 mm in from the
# seam with the roll (Pinata iso-left: red stitching along the pads' lower edges and round the chin bar inside).
ROLL_PITCH = 0.0056
ROLL_RIB_H = 0.0004
PAD_MESH = 0.0016
PAD_TILE = (6 * PAD_MESH, 36 * PAD_MESH * 3 ** 0.5)        # m: u along the port, v across from the seam
PAD_STITCH = (0.0025, 0.0031, 0.0022, 0.0010)              # m: from, to (across), dash, gap (along)


def roll_texture(path, px_mm=40):
    """One rib of the trim's roll across a ROLL_PITCH tile (u along the port), as a normal map."""
    from PIL import Image
    n = int(round(ROLL_PITCH * 1000 * px_mm))
    x = (np.arange(n) + 0.5) / n
    h = np.clip(np.cos(np.pi * (x - 0.5) / 0.45), 0, 1) ** 2 * (np.abs(x - 0.5) < 0.225)
    hf = np.tile(h, (n, 1))
    Image.fromarray(normal_map(hf, ROLL_RIB_H * 1000, px_mm)).save(path, optimize=True)


def pad_texture(path, px_mm=16):
    """The pads' knit mesh (hexagonal holes) with the red stitch line, PAD_TILE (sRGB albedo)."""
    from PIL import Image
    W, Hh = int(round(PAD_TILE[0] * 1000 * px_mm)), int(round(PAD_TILE[1] * 1000 * px_mm))
    u = (np.arange(W) + 0.5) / px_mm
    v = (np.arange(Hh) + 0.5) / px_mm
    U, V = np.meshgrid(u, v)
    p = PAD_MESH * 1000
    rh = p * 3 ** 0.5 / 2
    r = np.round(V / rh)
    du = U - (np.round((U - (r % 2) * p / 2) / p) * p + (r % 2) * p / 2)
    d = np.hypot(du, V - r * rh)
    hole = np.clip((0.55 * p / 2 - d) / 0.12 + 0.5, 0, 1)
    strand, dark = np.array([50, 48, 52], float), np.array([10, 10, 11], float)
    img = strand + (dark - strand) * hole[..., None]
    a, b, dash, gap = [x * 1000 for x in PAD_STITCH]
    on = (V >= a) & (V <= b) & ((U % (dash + gap)) < dash)
    img[on] = [190, 32, 38]
    Image.fromarray(img.astype(np.uint8)).save(path, optimize=True)


def textures(texdir, force=False):
    """The moulded front's textures (written when missing, or always with force)."""
    import os
    for name, fn in (("helmet_grip_relief.png", grip_texture), ("helmet_roll_ribs.png", roll_texture),
                     ("helmet_pad_mesh.png", pad_texture)):
        path = os.path.join(texdir, name)
        if force or not os.path.exists(path):
            fn(path)


# ---------------------------------------------------------------- the chin's mouthpiece (phase 2, decision 51)
# A recessed shield across the chin's front: the white shell folds in at its rim (a lit white lip, 10 to 14 px in the
# Pinata photos), a black moulded wall 5 to 13 mm wide runs in to the opening, and in the opening a triangle
# lattice over a dark floor, with two rails down the middle framing its central column. Traced at
# 2.4x to 3x with grids (scratch gridcrop.py) on Leatt's MY27 front-iso-left and Pinata iso-right photos, whose solved
# cameras (research/helmet-ba.json) see the chin's outline within 5 mm, cast onto the shell and averaged: the two
# agree within 3 mm. (Pinata iso-left, whose chin outline stands 13 mm off, read the lower sides 10 to 15 mm narrow
# and is not used.) In the chin's front plane (x, z in mm), his left half from the centre line at the top round to
# it at the bottom; his right half is the mirror. Its bottom is flat (iso-right at 4x: the frame's lower edge level
# for 25 px, 6 mm, each side of the centre line). The rim: the white paint's edge; the opening: where the wall meets
# the lattice (MY27: the wall's inner edge line; iso-right: the lattice's edge).
MOUTH_RIM = [(0.0, -92.5), (5.0, -92.7), (11.0, -93.4), (17.5, -94.8), (26.0, -98.5), (33.0, -102.0), (40.0, -105.0),
             (45.0, -107.5), (48.5, -110.0), (50.2, -113.0), (50.4, -116.0), (50.0, -119.5), (49.2, -123.5),
             (47.5, -128.0), (44.8, -133.0), (41.5, -138.0), (37.8, -142.8), (31.4, -150.1), (25.0, -156.0),
             (20.5, -161.0), (16.5, -165.5), (11.0, -168.6), (5.0, -169.5), (0.0, -169.6)]
MOUTH_OPEN = [(0.0, -98.0), (8.0, -99.0), (15.0, -100.5), (24.0, -104.5), (32.0, -109.5), (36.5, -113.0),
              (37.8, -116.5), (37.8, -120.0), (37.0, -124.3), (33.0, -133.0), (27.0, -141.5), (19.5, -150.8),
              (13.5, -158.0), (10.0, -162.5), (6.0, -164.8), (0.0, -165.3)]
# The column's rails, their centre lines at the opening's top and bottom (x, z mm; MY27 read them 37 mm apart at the
# top and 19 at the bottom, iso-right 31 and 14: their means, centred, as each camera puts the centre line 5 to 8 mm
# to one side there)
MOUTH_RAIL = [(17.0, -100.0), (8.5, -164.5)]
MOUTH_FRAME_H = 0.0020            # the wall's top over the shell (the lattice stays under it: inside the recess)
MOUTH_FLOOR_H = 0.0004
MOUTH_CELL = 0.0070               # the column's triangles (their rows 26 to 30 px apart at 0.23 mm/px)
MOUTH_BAR_W, MOUTH_BAR_H = 0.0010, 0.0014
MOUTH_RAIL_W, MOUTH_RAIL_H = 0.0030, 0.0018
MAT_FRAME = "helmet_frame_black"


def cast_any(shell, view, uv):
    """Cast photo points onto the shell, his left side first, else his right; the misses dropped."""
    out_P, out_N = [], []
    for p in np.atleast_2d(uv):
        for s in (1.0, -1.0):
            try:
                P, N = shell.cast(view, p[None], side=s)
            except ValueError:
                continue
            out_P.append(P[0])
            out_N.append(N[0])
            break
    return np.array(out_P), np.array(out_N)


def cast_dir(shell, P0, d):
    """Points P0 moved along d onto the shell (first hit), with the shell's normals there."""
    V, F = shell.V, shell.F
    v0 = V[F[:, 0]]
    e1, e2 = V[F[:, 1]] - v0, V[F[:, 2]] - v0
    p = np.cross(d, e2)
    det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    P, N = [], []
    for C in P0:
        t0 = C - v0
        u = (t0 * p).sum(1) * inv
        q = np.cross(t0, e1)
        w = (q @ d) * inv
        t = (e2 * q).sum(1) * inv
        hit = ok & (u >= 0) & (w >= 0) & (u + w <= 1) & (t > 0)
        j = np.argmin(np.where(hit, t, np.inf))
        f = F[j]
        P.append(C + t[j] * d)
        n = (1 - u[j] - w[j]) * shell.N[f[0]] + u[j] * shell.N[f[1]] + w[j] * shell.N[f[2]]
        N.append(n / np.linalg.norm(n))
    return np.array(P), np.array(N)


def sym_loop(shell, px):
    """A closed loop on the shell, symmetric about the centre plane, from its left half traced in iso-left px (an
    open line from the centre line round to the centre line; its ends are carried across to the centre plane). Read
    as a closed loop, its closing segment down the traced centre (which the iso-left camera puts 8 to 10 mm off the
    model's at the brow) cut a notch 16 mm wide into the brow vent's lower edge."""
    uv = H.resample_open(np.asarray(px, float), 3.0)
    P, _ = cast_any(shell, "isoleft", uv)
    P = P[P[:, 0] > 0.002]
    ends = [P[0] * [0, 1, 1], P[-1] * [0, 1, 1]]
    L = np.vstack([ends[0], P, ends[1], (P * [-1, 1, 1])[::-1]])
    return shell.snap(resample_loop(L, 0.0015))        # points along the straight edges carried to the centre too


def front_cast(shell, xz):
    """Points of the chin's front plane (x, z in m) on the shell, cast along +y from ahead of it, and the shell's
    normals there."""
    xz = np.atleast_2d(xz)
    y0 = shell.V[:, 1].min() - 0.05
    return cast_dir(shell, np.c_[xz[:, 0], np.full(len(xz), y0), xz[:, 1]], np.array([0.0, 1.0, 0.0]))


def mouth_xz(half, m=48):
    """The closed loop (x, z in m) of a half outline in mm (his left, from the centre line at the top round to it at
    the bottom): resampled to m points by length and mirrored (2 m - 2 points)."""
    h = np.asarray(half, float) / 1000.0
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(h, axis=0), axis=1))]
    t = np.linspace(0, s[-1], m)
    h = np.c_[np.interp(t, s, h[:, 0]), np.interp(t, s, h[:, 1])]
    return np.vstack([h, (h[1:-1] * [-1, 1])[::-1]])


def mouth_lattice(shell, open_xz):
    """The opening's lattice in the chin's front plane, cast onto the shell: across bars on every row of the
    triangles from edge to edge, the two diagonal families, and the column's two rails over them. Mirror symmetric by
    construction. Pieces (V, F, mats)."""
    from matplotlib.path import Path
    inside = Path(open_xz).contains_points
    (xt, zt), (xb, zb) = np.asarray(MOUTH_RAIL) / 1000.0

    def xr(z):                                          # the rail's centre line at height z
        return xt + (xb - xt) * (z - zt) / (zb - zt)

    xs = np.linspace(0.0, open_xz[:, 0].max(), 600)

    def xo(z):                                          # the opening's edge on his left at height z
        m = inside(np.c_[xs, np.full(len(xs), z)])
        return xs[m].max() if m.any() else 0.0

    a = MOUTH_CELL
    h = a * 3 ** 0.5 / 2
    z0, z1 = open_xz[:, 1].min(), open_xz[:, 1].max()
    rows = z1 - h * (np.arange(int((z1 - z0) / h) + 1) + 0.5)
    rows = rows[rows > z0 + 0.001]
    inset = 0.0005
    lines = []                                          # (polyline x z, width, height, mirrored too)

    def runs(p, ok, w, hh, mirror):
        idx = np.nonzero(ok)[0]
        for r in np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1):
            if len(r) >= 3:
                lines.append((p[r], w, hh, mirror))

    for z in rows:                                      # across: symmetric of themselves
        e = xo(z) - inset
        if e > 0.003:
            p = np.c_[np.linspace(-e, e, max(3, int(2 * e / 0.0015))), np.full(max(3, int(2 * e / 0.0015)), z)]
            runs(p, np.ones(len(p), bool), MOUTH_BAR_W, MOUTH_BAR_H, False)
    t = np.linspace(z0, z1, int((z1 - z0) / 0.00075))   # the 60 deg lines (and their mirror, 120 deg)
    for n in range(-14, 15):
        p = np.c_[n * a + (t - rows[0]) / 3 ** 0.5, t]
        runs(p, inside(p), MOUTH_BAR_W, MOUTH_BAR_H, True)
    z = np.linspace(z1, z0, 90)                         # the rails
    p = np.c_[xr(z), z]
    runs(p, inside(p), MOUTH_RAIL_W, MOUTH_RAIL_H, True)
    out = []
    for p, w, hh, mirror in lines:
        S3, NS = front_cast(shell, p)
        Vb, Fb = bar(S3, NS, w, hh)
        mat = MAT_FRAME if w == MOUTH_RAIL_W else MAT_MESH
        out.append((Vb, [list(f) for f in Fb], [mat] * len(Fb)))
        if mirror:
            out.append((Vb * [-1, 1, 1], [list(f)[::-1] for f in Fb], [mat] * len(Fb)))
    return out


def mouthpiece(shell):
    """The mouthpiece: its wall (MAT_FRAME, the outer wall in MAT: the white paint folding in at the rim), the dark
    floor (MAT_DARK), the lattice (MAT_MESH) and the column's rails (MAT_FRAME). Pieces (V, F, mats)."""
    open_xz = mouth_xz(MOUTH_OPEN)
    Q, NQ = front_cast(shell, mouth_xz(MOUTH_RIM))
    P, N = front_cast(shell, open_xz)
    V, F = plate(P, N, Q, NQ, MOUTH_FRAME_H)
    n = len(P)
    out = [(V, [list(f) for f in F], [MAT_FRAME] * (4 * n) + [MAT] * n)]
    Vc, Fc = cap(P, N, MOUTH_FLOOR_H, shell)
    out.append((Vc, [list(f) for f in Fc], [MAT_DARK] * len(Fc)))
    return out + mouth_lattice(shell, open_xz)


def vent_pieces(shell, P, N, rim_w, rim_h, rim_mat=MAT_FRAME, mesh=None):
    """A vent's rim (rim_mat), dark floor (MAT_DARK) and wire mesh (MAT_MESH; mesh: its pitch, wire width and angle,
    else the rear slots') round its loop P on the shell."""
    Q, NQ = shell.snap(P + outward(P, N) * rim_w)
    V, F = plate(P, N, Q, NQ, rim_h)
    out = [(V, F, [rim_mat] * len(F))]
    Vc, Fc = cap(P, N, MOUTH_FLOOR_H, shell)
    out.append((Vc, Fc, [MAT_DARK] * len(Fc)))
    kw = dict(zip(("pitch", "w", "angle"), mesh)) if mesh else {}
    return out + [(Vm, Fm, [MAT_MESH] * len(Fm)) for Vm, Fm in mesh_wires(P, N, shell, rim_h * 0.5, **kw)]


# The chin bar's side vent each side: a slanting slot under a square wire mesh in a wall of the shell's white
# (Pinata iso-left: the wall lit along its back edge, 10 to 15 px) round a dark floor. Traced at 3x with a grid on
# Leatt's MY27 front-iso-left photo and cast onto the shell through its solved camera: the slot's centroid then lies
# 2.5 mm from the chin_vent landmark solved from five photos (research/helmet-ba.json). (Pinata iso-left, whose
# camera puts the chin 13 mm off, reads it 9 mm further forward: not used.) Its outline as (y, z) mm on his left side,
# cast across (-x) onto the shell; his right is the mirror. The mesh: wires 3.2 mm apart (MY27: 13 to 15 px at 0.23
# mm/px), 0.6 mm thick (3 px), 45 deg either side of the slot's long axis.
SIDE_VENT_YZ = [(-161.8, -125.6), (-155.1, -123.9), (-148.9, -122.5), (-150.4, -125.3), (-153.1, -129.8),
                (-156.7, -135.7), (-160.3, -141.6), (-163.6, -146.4), (-167.4, -147.0), (-169.3, -144.7),
                (-168.8, -138.4), (-167.4, -132.3), (-165.4, -127.7)]
SIDE_VENT_RIM_W, SIDE_VENT_RIM_H = 0.0015, 0.0010
SIDE_MESH = (0.0032, 0.0006, 45.0)                  # pitch, wire width, angle


def side_vents(shell):
    """The chin bar's side vents, his left as traced and his right its mirror. Pieces (V, F, mats)."""
    yz = resample_loop(np.asarray(SIDE_VENT_YZ, float) / 1000.0, 0.0015)
    x0 = shell.V[:, 0].max() + 0.05
    P, N = cast_dir(shell, np.c_[np.full(len(yz), x0), yz], np.array([-1.0, 0.0, 0.0]))
    pieces = vent_pieces(shell, P, N, SIDE_VENT_RIM_W, SIDE_VENT_RIM_H, rim_mat=MAT, mesh=SIDE_MESH)
    return mirror(pieces, 1.0) + mirror(pieces, -1.0)


# ---------------------------------------------------------------- the brow's vents and tag (phase 2, decision 51)
# Traced on Leatt's Pinata iso-left photo at 2x and 3x with grids (scratch gridcrop.py; 0.21 to 0.23 mm/px there):
# under the visor the brow's black moulding carries two mesh vents a side. The centre one runs across the centre line
# (its left half traced from the brow's centre, px 663 there through the solved camera, to the diagonal divider at
# 760 to 780), the side one past the divider is a band slanting down to the brow's corner (845 to 992). Dark openings
# under a fine wire mesh (the rear slots' mesh_wires), framed by the moulding's own rim: 1.5 mm, standing 1 mm (its
# lit edge 4 to 5 px at 3x). The brow tag at the brow's corner: the Leatt triangle in a light grey rim (the photo's
# silver outline, lit to 184 188 194; its dark grey centre 46 44 45), 1 mm proud (first read 20 to 25 px high:
# the rim's top corner is at 690 px, under the brow's lower edge; read again at 3x beside the render). At 3x the
# photo's silver rim is about 10 px wide of the outline's 57 across (its dark centre 0.55 of the outline) and its
# corners are rounded about 4 px (the first build: sharp corners, a rim half as wide).
BROW_VENTS_PX = [
    [(663, 625), (720, 630), (765, 638), (782, 655), (762, 668), (700, 665), (663, 664)],      # centre: its left half
    [(843, 652), (880, 657), (920, 664), (960, 676), (988, 690), (992, 704), (960, 697), (920, 686), (880, 676),
     (850, 670)]]
BROW_RIM_W, BROW_RIM_H = 0.0015, 0.0010
BROW_TAG_PX = [(1083, 690), (1112, 729), (1060, 734)]        # its rim's corners (3x)
BROW_TAG_ROUND, BROW_TAG_IN = 4.0, 0.55     # corner radius px (about 1 mm); the dark centre's size against the outline
BROW_TAG_H = 0.0010
MAT_TAG = "helmet_tag_rim"


def brow_vents(shell):
    """The brow's mesh vents: the centre one (traced across the centre line) and the side one each side, and the
    brow tag each side. Pieces (V, F, mats)."""
    shell = ExactShell(shell.V, shell.F)
    out = []
    P, N = sym_loop(shell, BROW_VENTS_PX[0])
    out += mirror(vent_pieces(shell, P, N, BROW_RIM_W, BROW_RIM_H), 1.0)
    side = []
    for px in BROW_VENTS_PX[1:]:
        uv = resample_loop(np.asarray(px, float), 2.0)
        P, N = shell.cast("isoleft", uv, side=1.0)
        side += vent_pieces(shell, P, N, BROW_RIM_W, BROW_RIM_H)
    uv = resample_loop(round_corners(BROW_TAG_PX, BROW_TAG_ROUND), 1.5)
    P, N = shell.cast("isoleft", uv, side=1.0)
    c = P.mean(0)
    Pi, Ni = shell.snap(c + (P - c) * BROW_TAG_IN)
    V, F = plate(Pi, Ni, P, N, BROW_TAG_H)
    side.append((V, F, [MAT_TAG] * len(F)))
    Vc, Fc = cap(Pi, Ni, BROW_TAG_H, shell)
    side.append((Vc, Fc, [MAT_DARK] * len(Fc)))
    return out + mirror(side, 1.0) + mirror(side, -1.0)


def build(Vo, Fo, part=None):
    """The detail as one Part (helmet frame): the crown vents in MAT_INSERT, the rear lower pieces in MAT, their
    slots' floor in MAT_DARK, the slots' wire mesh in MAT_MESH, the grip panels in MAT_GRIP (top, UVs for its
    grain), MAT_GRIP_RIDGE (the relief) and MAT_GRIP_EDGE (walls), the chin's mouthpiece in MAT_FRAME (its outer wall in
    MAT) with its floor in MAT_DARK and its lattice in MAT_MESH, the chin bar's side vents (wall MAT, floor MAT_DARK,
    mesh MAT_MESH), the brow's vents (rim MAT_FRAME, floor MAT_DARK, mesh MAT_MESH) and tag
    (MAT_TAG round a MAT_DARK centre)."""
    shell = Shell(Vo, Fo)
    part = part or H.Part(PART)
    pieces = []
    for side in (1.0, -1.0):
        pieces += [(V, [list(f) for f in F], [MAT_INSERT] * len(F)) for V, F in crown_vent(shell, side)]
        pieces += rear_slot(shell, side)
        pieces += low_piece(shell, side)
    for V, F, mats in pieces:
        part.add(V, F, mats)
    for side in (1.0, -1.0):                            # the grip panels, with their relief's UVs
        for V, F, mats, uv in grip_panel(shell, side):
            part.add(V, F, mats, uv)
    for V, F, mats in mouthpiece(shell) + side_vents(shell) + brow_vents(shell):
        part.add(V, [list(f) for f in F], mats)
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
