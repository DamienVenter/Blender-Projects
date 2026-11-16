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
    """In-surface unit directions away from a closed loop's inside. Where neighbours coincide (a rim's offset snapped
    onto the shell's edge: the brow's centre vent touches the port's edge on the centre line) the tangent spans
    further."""
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    for k in (2, 3, 4):
        z = np.linalg.norm(t, axis=1) < 1e-9
        if not z.any():
            break
        t[z] = (np.roll(P, -k, 0) - np.roll(P, k, 0))[z]
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
    """Flip all faces if their normals point into the shell on average (the top faces must face outwards). Faces of
    one size come back as an array, of mixed sizes (quads and triangles) as lists."""
    if len({len(f) for f in F}) > 1:
        a, b, c = (V[[f[k] for f in F]] for k in range(3))
        cen = np.array([V[list(f)].mean(0) for f in F])
    else:
        F = np.asarray(F)
        a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
        cen = V[F].mean(1)
    fn = np.cross(b - a, c - a)
    from scipy.spatial import cKDTree
    j = cKDTree(P_ref).query(cen)[1]
    if np.sum(np.sum(fn * N_ref[j], 1)) >= 0:
        return F
    return F[:, ::-1] if isinstance(F, np.ndarray) else [list(f)[::-1] for f in F]


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
# it shows a lit line 2 to 3 px wide at 1:1 (0.5 to 0.7 mm). Phase 2 moulded the relief as ridges: an
# equilateral triangle lattice with lines across the band and at 60 deg to it; its row period, 28 px down columns 1260
# and 1280 (autocorrelation, r 0.33 to 0.39), is 6.3 mm: cells 7.3 mm a side. At 2x the ridges' lit tops are 3 to 4
# px wide at 1:1 (0.7 to 0.9 mm) with a 2 px shadow beside them under the studio's high key light (0.5 mm high); some
# lattice edges are left out, so triangles merge into rhombi and trapezoids, and some triangles are filled solid
# (about 1 in 14 at 2x). Between the ridges the moulding is sandblasted: light flecks 1 px across at 2x (0.1 mm), the
# panel's normal map (grip_texture). Its tone (helmet.MATERIALS): see helmet_grip. A first version drew the lattice
# in the normal map only (lines 0.45 mm, 0.3 mm high): at 2x it read as thin dark grooves on a flat grey (p10 to p90
# 74 to 87 against the photo's 17 to 104).
# Round 5 (decision 56), the coordinator's 1:1 review of 05: Leatt's panel fills the corner between the trim's roll
# and the print, from under the brow down to the chin bar, its triangles reading dark with lit ridges (iso-left p10 to
# p90 16 to 104); phase 2's was a lighter grey rectangle (56 to 90) inside the print's black (rows 805 to 1094 only).
# At 4x and 6x (Pinata iso-left, px 1215 to 1330, 850 to 1000) the relief is raised tiles, not ridges: triangles, and
# rhombi where a groove is left out, standing out of a dark net of grooves 0.6 to 0.7 mm wide (10 to 12 px at 4x;
# 0.226 mm/px at 1:1), each tile's edge a bevel lit 0.25 mm wide on the side facing the studio's key light. Its rows
# lie 24 to 25 px apart down the panel at 4x against 30 px rendered with phase 2's 7.3 mm cells (whose 28 px came
# from an autocorrelation peak of merged rows): cells 6.0 mm a side. The panel's floor now fills the print's black (helmet_art.FORCE's
# port polygon, the same px) from the port's crest to the paint's edge, and from the brow's lower edge (GRIP_TOP_PX,
# traced at 2x: where the brow's moulding folds down into the panel) to the print's edge over the chin bar
# (GRIP_BOTTOM_PX); the tiles fill the field traced on the photo: the paint's edge down to row 1010, then GRIP_FIELD_PX,
# 2 to 7 mm in from it (the smooth moulding's margin in the lower corner, as Leatt's).
GRIP_OUTER_PX = [(1350, 697), (1347, 735), (1331, 816), (1316, 897), (1300, 954), (1287, 1010), (1275, 1047),
                 (1262, 1085), (1256, 1097)]
GRIP_TOP_PX = [(1182, 797), (1230, 782), (1290, 760), (1338, 738), (1347, 735)]
GRIP_BOTTOM_PX = [(1256, 1097), (1175, 1122), (1100, 1150)]
GRIP_FIELD_PX = [(1287, 1010), (1275, 1040), (1255, 1068), (1230, 1088), (1200, 1107), (1170, 1122), (1150, 1129)]
GRIP_H = 0.0006                    # m, the panel's floor over the shell
GRIP_CELL = 0.0060                 # m, the triangles' side
GRIP_GROOVE = 0.0006               # m, the grooves between the tiles, at the floor
GRIP_BEVEL = 0.00025               # m, the tiles' bevel (45 deg)
GRIP_TILE_H = 0.0005               # m, the tiles over the floor
GRIP_MERGE = 0.12                  # the triangles merged with a neighbour into a rhombus (a groove left out)
GRIP_MIN_AREA = 2.0e-6             # m2, smaller pieces of tiles cut at the field's edge are left out
GRIP_STEP = 0.0008                 # m, the floor's mesh
GRIP_GRAIN = (0.08, 0.015)         # mm: the sandblast grain's size (Gaussian sigma) and its height (rms)
GRIP_TILE = (0.008, 0.008)         # m, the grain's tile (u across the band, v along it)
GRIP_PX_MM = 16                    # texels per mm
MAT_GRIP = "helmet_grip"           # the tiles' tops and the floor's smooth margins
MAT_GRIP_BEVEL = "helmet_grip_bevel"
MAT_GRIP_GROOVE = "helmet_grip_groove"     # the floor between the tiles
MAT_GRIP_EDGE = "helmet_grip_edge"         # the walls


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


def _cross(P, Q):
    """The first crossing of the 2D polylines P and Q: (index in P, t along that segment, index in Q, t)."""
    for i in range(len(P) - 1):
        a, r = P[i], P[i + 1] - P[i]
        for j in range(len(Q) - 1):
            c, s = Q[j], Q[j + 1] - Q[j]
            den = r[0] * s[1] - r[1] * s[0]
            if abs(den) < 1e-12:
                continue
            t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
            u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
            if 0 <= t <= 1 and 0 <= u <= 1:
                return i, t, j, u
    raise ValueError("the polylines do not cross")


def _dense(px, step=2.0):
    """An open px polyline with points about step apart (its ends kept)."""
    px = np.asarray(px, float)
    out = [px[0]]
    for a, b in zip(px[:-1], px[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out += [a + (b - a) * k / n for k in range(1, n + 1)]
    return np.array(out)


def grip_outlines(shell):
    """The panel's outline (its floor) and its tiles' field on his left, as closed 3D loops on the shell. Both start
    on the port's crest (port_rows: the shell's cut edge) where the brow's lower edge (GRIP_TOP_PX, carried on over
    the crest) meets it and run down the crest; the floor's then to the print's edge under it (GRIP_BOTTOM_PX), up the
    paint's edge (GRIP_OUTER_PX) and back along the brow's edge; the field's leaves the crest over column 1150 px and
    runs up GRIP_FIELD_PX and the paint's edge from row 1010."""
    rows = np.arange(780.0, 1146.0, 2.0)                # the crest leaves the side past row 1148
    C3 = port_rows(shell, rows)
    C = H.cam_project(H.PRINT_CAMS["isoleft"], C3)[0][:, :2]
    top = np.asarray(GRIP_TOP_PX, float)
    ext = np.vstack([top[0] + (top[0] - top[1]), top])
    i, t, _, _ = _cross(C, ext)
    T3 = C3[i] + t * (C3[i + 1] - C3[i])

    def crest_to(x):
        k = [k for k in range(i + 1, len(C) - 1) if (C[k, 0] - x) * (C[k + 1, 0] - x) <= 0 and C[k + 1, 0] < C[k, 0]][0]
        s = (x - C[k, 0]) / (C[k + 1, 0] - C[k, 0])
        return np.vstack([T3, C3[i + 1:k + 1], C3[k] + s * (C3[k + 1] - C3[k])])

    def cast(px):
        return shell.cast("isoleft", _dense(px), side=1.0)[0]

    outer = np.asarray(GRIP_OUTER_PX, float)
    up_top = top[::-1]                                   # the paint's top corner along the brow's edge to the crest
    bottom = np.asarray(GRIP_BOTTOM_PX, float)[::-1]
    floor_px = np.vstack([[bottom[0][0], bottom[0][1]], bottom[1:], outer[::-1][1:-2], up_top])
    field_px = np.vstack([np.asarray(GRIP_FIELD_PX, float)[::-1], outer[(outer[:, 1] < 1010)][::-1][:-2], up_top])
    A = np.vstack([crest_to(bottom[0][0]), cast(floor_px)])
    B = np.vstack([crest_to(GRIP_FIELD_PX[-1][0]), cast(field_px)])
    return A, B


def _area(P):
    return 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])


def _inset(P, d):
    """A closed CCW polygon moved in by d along its edges' normals (each corner along its bisector)."""
    e = np.roll(P, -1, 0) - P
    n = np.c_[-e[:, 1], e[:, 0]] / np.linalg.norm(e, axis=1)[:, None]      # inward (CCW: the left side)
    m = n + np.roll(n, 1, 0)
    m /= np.linalg.norm(m, axis=1)[:, None]
    return P + m * (d / np.sum(m * n, 1))[:, None]


def _clip(S, W):
    """The polygon S clipped to the convex CCW polygon W (Sutherland and Hodgman)."""
    out = [p for p in S]
    for a, b in zip(W, np.roll(W, -1, 0)):
        e = b - a
        side = lambda p: e[0] * (p[1] - a[1]) - e[1] * (p[0] - a[0])
        inp, out = out, []
        for k, p in enumerate(inp):
            q = inp[k - 1]
            sp, sq = side(p), side(q)
            if sp >= 0:
                if sq < 0:
                    out.append(q + (p - q) * sq / (sq - sp))
                out.append(p)
            elif sq >= 0:
                out.append(q + (p - q) * sq / (sq - sp))
        if not out:
            return np.zeros((0, 2))
    return np.array(out)


def _tidy(P, short):
    """Points closer than short to the previous one dropped (a cut tile's corners), and points on a straight line."""
    P = list(P)
    changed = True
    while changed and len(P) > 3:
        changed = False
        for k in range(len(P)):
            a, b, c = np.asarray(P[k - 1]), np.asarray(P[k]), np.asarray(P[(k + 1) % len(P)])
            u, w = b - a, c - b
            if np.linalg.norm(u) < short or abs(u[0] * w[1] - u[1] * w[0]) < 1e-3 * np.linalg.norm(u) * np.linalg.norm(w):
                del P[k]
                changed = True
                break
    return np.array(P)


def grip_tiles(field, seed=51):
    """The relief's tiles in the panel's plane (m): an equilateral triangle lattice (GRIP_CELL) over the field, some
    triangles merged with a neighbour into rhombi (GRIP_MERGE), each cell moved in by half a groove and cut to the
    field moved in by as much (the field's edge is a groove too); pieces under GRIP_MIN_AREA left out. Returns the
    tiles' outlines at the floor (CCW) and their tops (moved in by the bevel)."""
    from matplotlib.path import Path
    rng = np.random.default_rng(seed)
    c, h = GRIP_CELL, GRIP_CELL * 3 ** 0.5 / 2
    lo, hi = field.min(0), field.max(0)
    pos = lambda i, j: lo + [(i + j / 2) * c, j * h]
    cells = []
    for j in range(-1, int((hi[1] - lo[1]) / h) + 2):
        for i in range(-j // 2 - 2, int((hi[0] - lo[0]) / c) - j // 2 + 3):
            cells.append(((i, j), (i + 1, j), (i, j + 1)))
            cells.append(((i + 1, j), (i + 1, j + 1), (i, j + 1)))
    by_edge = {}
    for k, cell in enumerate(cells):
        for a, b in zip(cell, cell[1:] + cell[:1]):
            by_edge.setdefault(tuple(sorted((a, b))), []).append(k)
    merged, tiles = set(), []
    for k in rng.permutation(len(cells)):
        if k in merged:
            continue
        cell = cells[k]
        pts = set(cell)
        if rng.random() < GRIP_MERGE:
            nb = [m for a, b in zip(cell, cell[1:] + cell[:1]) for m in by_edge[tuple(sorted((a, b)))]
                  if m != k and m not in merged]
            if nb:
                m = nb[rng.integers(len(nb))]
                merged.add(m)
                pts |= set(cells[m])
        merged.add(k)
        P = np.array([pos(i, j) for i, j in pts])
        cen = P.mean(0)
        tiles.append(P[np.argsort(np.arctan2(P[:, 1] - cen[1], P[:, 0] - cen[0]))])
    F_in = _inset(field if _area(field) > 0 else field[::-1], GRIP_GROOVE / 2)
    path = Path(F_in)
    out = []
    for P in tiles:
        base = _inset(P, GRIP_GROOVE / 2)
        if not path.contains_points(base).any() and not Path(base).contains_points(F_in).any():
            continue
        if not path.contains_points(base).all() or Path(base).contains_points(F_in).any():
            base = _tidy(_clip(F_in, base), 1.5 * GRIP_BEVEL)
        if len(base) < 3 or _area(base) < GRIP_MIN_AREA:
            continue
        top = _inset(base, GRIP_BEVEL)
        e0, e1 = np.roll(base, -1, 0) - base, np.roll(top, -1, 0) - top
        if (_area(top) <= 0.25 * _area(base) or np.any(np.sum(e0 * e1, 1) <= 0)
                or not Path(base).contains_points(top).all()):
            continue
        out.append((base, top))
    return out


def grip_panel(shell, side=1.0):
    """A grip panel on his left (side 1) or right: its floor GRIP_H over the shell between the port's crest, the
    brow's edge and the paint's (grip_outlines), in MAT_GRIP outside the tiles' field and MAT_GRIP_GROOVE inside it,
    walls down into the shell (MAT_GRIP_EDGE), and the relief's tiles GRIP_TILE_H over the floor (tops MAT_GRIP,
    bevels MAT_GRIP_BEVEL, walls MAT_GRIP_EDGE). Laid out in the plane fitted to the outline (the panel is 32 by 95
    mm on a gently curved side: the shell stands within 3 mm of the plane) and carried onto the shell (ExactShell);
    UVs in GRIP_TILE units of that plane (the grain's normal map). Returns pieces (V, F, mats, uv)."""
    from matplotlib.path import Path
    from scipy.spatial import Delaunay, cKDTree
    A3, B3 = grip_outlines(shell)
    ex = ExactShell(shell.V, shell.F)
    o = A3.mean(0)
    e2, e3 = np.linalg.svd(A3 - o)[2][[0, 2]]
    if e3 @ ex.snap(o)[1][0] < 0:
        e3 = -e3
    if e2[2] < 0:
        e2 = -e2
    e1 = np.cross(e2, e3)
    flat = lambda P: np.c_[(P - o) @ e1, (P - o) @ e2]

    def lift(Q, h):
        P, N = ex.snap(o + Q[:, :1] * e1 + Q[:, 1:2] * e2)
        return P + N * h

    A, B = flat(A3), flat(B3)
    A, B = (A if _area(A) > 0 else A[::-1]), (B if _area(B) > 0 else B[::-1])
    A, B = resample_loop(A, GRIP_STEP / 3), resample_loop(B, GRIP_STEP / 3)
    pieces = []
    # the floor: the outlines' points and a grid kept off them, triangulated, cut to the outline
    rim = np.vstack([A, B[Path(A).contains_points(B) & (cKDTree(A).query(B)[0] > GRIP_STEP / 3)]])
    lo, hi = A.min(0), A.max(0)
    g = np.stack(np.meshgrid(np.arange(lo[0], hi[0], GRIP_STEP), np.arange(lo[1], hi[1], GRIP_STEP)), -1).reshape(-1, 2)
    g = g[Path(A).contains_points(g) & (cKDTree(rim).query(g)[0] > GRIP_STEP / 2)]
    Q = np.vstack([rim, g])
    T = Delaunay(Q).simplices
    cen = Q[T].mean(1)
    T = T[Path(A).contains_points(cen)]
    d = Q[T]
    u, w = d[:, 1] - d[:, 0], d[:, 2] - d[:, 0]
    flip = u[:, 0] * w[:, 1] - u[:, 1] * w[:, 0] < 0
    T[flip] = T[flip][:, ::-1]
    groove = Path(B).contains_points(Q[T].mean(1))
    pieces.append((lift(Q, GRIP_H), [list(f) for f in T],
                   [MAT_GRIP_GROOVE if k else MAT_GRIP for k in groove], [[tuple(Q[j] / GRIP_TILE) for j in f] for f in T]))
    # the walls all round, down to SINK under the shell, each with its own vertices (crisp edges)
    n = len(A)
    Vw = np.vstack([lift(A, GRIP_H), lift(A, -SINK)])
    Fw = [[n + k, n + (k + 1) % n, (k + 1) % n, k] for k in range(n)]
    pieces.append((Vw, Fw, [MAT_GRIP_EDGE] * n, [[(0.5, 0.5)] * 4] * n))
    # the tiles
    Vs, Fs, Ms, UVs, nv = [], [], [], [], 0
    for base, top in grip_tiles(B):
        m = len(base)
        cen = top.mean(0)[None]
        flat_pts = np.vstack([top, base, base, cen])
        V = np.vstack([lift(top, GRIP_H + GRIP_TILE_H), lift(base, GRIP_H + GRIP_TILE_H - GRIP_BEVEL),
                       lift(base, GRIP_H - 0.0002), lift(cen, GRIP_H + GRIP_TILE_H)])
        F = [[3 * m, k, (k + 1) % m] for k in range(m)]
        F += [[m + k, m + (k + 1) % m, (k + 1) % m, k] for k in range(m)]
        F += [[2 * m + k, 2 * m + (k + 1) % m, m + (k + 1) % m, m + k] for k in range(m)]
        Vs.append(V)
        Fs += [[nv + j for j in f] for f in F]
        Ms += [MAT_GRIP] * m + [MAT_GRIP_BEVEL] * m + [MAT_GRIP_EDGE] * m
        UVs += [[tuple(flat_pts[j] / GRIP_TILE) for j in f] for f in F]
        nv += len(V)
    pieces.append((np.vstack(Vs), Fs, Ms, UVs))
    if side < 0:
        pieces = [(V_ * [-1, 1, 1], [f[::-1] for f in F_], m_, [u[::-1] for u in uv_]) for V_, F_, m_, uv_ in pieces]
    return pieces


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
# Round 5 (decision 56): Leatt's opening is a shield (the coordinator's 1:1 review of 06a: angular, straight sides in
# every photo narrowing to a flat bottom; phase 2's was a rounded oval) and its frame a deep recessed tunnel, not a
# flat band. The rim (the white paint's edge) keeps phase 2's trace, which those photos see within 3 mm (its sides,
# straight in the photos, curve in the chin's front plane as the chin does), with its corners made sharp where the
# solved landmarks put them (helmet_ba: mouth_corner, its side corner, at x 51.0, z -113.5 mm on the shell from three
# photos; mouth_bottom, the flat bottom's corner, at x 13.1, z -168.7) and the shoulder straight. The white paint
# rolls in over a lip's first band (MOUTH_LIP[0]), then the black moulding: the lip's second band and a wall sloping in
# and back to the inner opening, MOUTH_INSET inside the rim and MOUTH_DEPTH behind it, where the lattice lies over a
# dark floor; the column's two rails stand MOUTH_RAIL_H out of it, MOUTH_RAIL_W wide (Leatt: rails 5 mm in the 1:1
# crops). The shell is cut along the rim (helmet.cut_loop, in the flat mesh's own parameters: helmet.on_mesh) and
# pushed back behind it out of sight (mouth_dent: the shell stays one closed surface, the lip starts on its cut edge).
# Round 5 (decision 56), from the 1:1 crops of Leatt's MY27 front-iso-left and Pinata iso-right through the solved
# cameras: the frame broad (iso-right's near side about 16 mm projected from the rim to the lattice, the top 7 mm,
# the bottom 6 mm; iso-left's far wall black 60 to 80 px), the lattice deep in it (the side panels' shading: MY27's
# fins 8 mm and more tall); the white roll at the rim thin (iso-right at 2.6x: the paint turns into the dark frame
# within 1 mm, no white inside it: the first build's second band, 2.5 mm back in white, read as a white strip down the
# far side). The shell is cut a second time MOUTH_EDGE outside the rim: smooth vertex normals at the rim averaged the
# surface with the dent's walls (pushed back 16.5 mm) and shaded the white beside the rim in teeth, one per triangle
# (iso-left at 2.4x); now the rim's vertices touch the surface only through that band.
MOUTH_RIM = [(0.0, -92.5), (5.0, -92.7), (11.0, -93.4), (17.5, -94.8), (26.0, -98.6), (33.0, -102.0), (40.0, -105.4),
             (46.0, -108.6), (51.0, -113.5), (50.3, -117.0), (50.0, -119.5), (49.2, -123.5), (47.5, -128.0),
             (44.8, -133.0), (41.5, -138.0), (37.8, -142.8), (31.4, -150.1), (25.0, -156.0), (20.5, -161.0),
             (13.1, -168.7), (6.0, -169.1), (0.0, -169.2)]
MOUTH_SHARP = ((51.0, -113.5), (13.1, -168.7))      # corners kept sharp (the rest smoothed once)
MOUTH_INSET = {"top": 0.0070, "side": 0.0120, "bottom": 0.0060}     # the inner opening inside the rim
MOUTH_DEPTH = 0.0110              # m, the inner opening (the lattice's plane) behind the rim
MOUTH_LIP = ((0.0008, 0.0008), (0.0012, 0.0025))   # m, the lip's two rings (in from the rim, back): white, black
MOUTH_EDGE = 0.0003               # m, the shell's second cut outside the rim (1 to 2 px at 1:1)
MOUTH_STEP = 0.0025               # m, the rim's points along it (the shell's cut and the lip's first ring)
MOUTH_TURN = 0.15                 # the front face's end at the side corner: the half width's slope along y
MOUTH_FLOOR = 0.0015              # m, the dark floor behind the lattice's plane
MOUTH_DENT = 0.0040               # m, the shell pushed back this far behind the floor inside the rim
MOUTH_CELL = 0.0070               # the column's triangles (their rows 26 to 30 px apart at 0.23 mm/px)
MOUTH_BAR_W, MOUTH_BAR_H = 0.0010, 0.0014
# The column's rails, their centre lines at the inner opening's top and bottom (x, z mm). Phase 2 read them on the
# shell's surface (MY27 37 mm apart at the top and 19 at the bottom, iso-right 31 and 14). Round 5: their front edges
# lie about 3 mm behind it (the rails' tops, MOUTH_DEPTH - MOUTH_RAIL_H), and cast there they stand wider: MY27 40 mm
# apart at z -106 to -114 and 27 at z -161, iso-right 41 at z -110 to -115 (its far bottom end hidden): 4 mm out on
# each side, the V's slope kept (the rails meet the inner opening's flat bottom at its corners, as Leatt's do)
MOUTH_RAIL = [(21.5, -100.0), (12.5, -164.0)]
MOUTH_RAIL_W, MOUTH_RAIL_H = 0.0050, 0.0080
MOUTH_FRAME_H = 0.0020            # (kept for the side vents' and brow vents' rims)
MOUTH_FLOOR_H = 0.0004
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
    uv = _resample_open_keep(np.asarray(px, float), 3.0)   # round 5: the trace's corners kept (angular vents)
    P, _ = cast_any(shell, "isoleft", uv)
    P = P[P[:, 0] > 0.002]
    ends = [P[0] * [0, 1, 1], P[-1] * [0, 1, 1]]
    L = np.vstack([ends[0], P, ends[1], (P * [-1, 1, 1])[::-1]])
    return shell.snap(_resample_closed(L, 0.0015))     # points along the straight edges carried to the centre too


def front_cast(shell, xz):
    """Points of the chin's front plane (x, z in m) on the shell, cast along +y from ahead of it, and the shell's
    normals there."""
    xz = np.atleast_2d(xz)
    y0 = shell.V[:, 1].min() - 0.05
    return cast_dir(shell, np.c_[xz[:, 0], np.full(len(xz), y0), xz[:, 1]], np.array([0.0, 1.0, 0.0]))


def mouth_rim_half():
    """His left half of the rim in the front plane (x, z in m), from the top on the centre line round to the bottom
    on it: MOUTH_RIM smoothed once but at its sharp corners and its ends, resampled every MOUTH_STEP by length with
    the corners kept as points. Returns the points and the corners' mask."""
    h = np.asarray(MOUTH_RIM, float)
    sharp = np.array([any(np.allclose(q, c) for c in MOUTH_SHARP) for q in h])
    keep = sharp.copy()
    keep[[0, -1]] = True
    sm = h.copy()
    sm[1:-1] = 0.25 * h[:-2] + 0.5 * h[1:-1] + 0.25 * h[2:]
    h = np.where(keep[:, None], h, sm)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(h, axis=0), axis=1))]
    t = np.linspace(0, s[-1], int(round(s[-1] / (1000 * MOUTH_STEP))) + 1)
    sc = s[sharp]
    t = np.sort(np.r_[t[np.abs(t[:, None] - sc[None]).min(1) > 0.4 * 1000 * MOUTH_STEP], sc])
    xz = np.c_[np.interp(t, s, h[:, 0]), np.interp(t, s, h[:, 1])] / 1000.0
    return xz, np.isin(t, sc)


_MOUTH = {}


def mouth_rim_3d(prof=None):
    """The rim's left half on the shell's surface (helmet frame, m; the analytic surface, helmet.half_width), from
    the top on the centre line round to the bottom: each front-plane point (x, z) at the y where the shell's half
    width reaches x, searched back from the chin rim. Where the front face turns into the chin bar's side before
    reaching x (the side corner: there the width creeps 1 mm in 10 mm of y, so a cast along y landed on the side,
    12 mm back), at the turn: where the width's slope along y falls under MOUTH_TURN. Returns the points and the
    corners' mask (cached)."""
    if "rim" not in _MOUTH:
        half, sharp = mouth_rim_half()
        _MOUTH["rim"] = (front_to_surface(prof or H.Profile(), half), sharp)
    return _MOUTH["rim"]


def front_to_surface(prof, half):
    """Front-plane points (x, z in m) of the rim's left half on the analytic surface (mouth_rim_3d's cast)."""
    fc = prof.fine_chin
    o = np.argsort(fc[:, 1])
    dy = 0.00005
    ys = np.arange(0.0, 0.06, dy)
    out = []
    for x, z in half:
        yc = np.interp(z, fc[o, 1], fc[o, 0])
        if x <= 0.0:
            out.append((0.0, yc, z))
            continue
        Y = yc + ys
        X = H.half_width(prof, Y, np.full(len(Y), z))
        g = np.gradient(X, dy)
        wall = np.nonzero((g < MOUTH_TURN) & (X > 0.03))[0]
        end = wall[0] if len(wall) else len(Y) - 1
        hit = np.nonzero(X[:end + 1] >= x)[0]
        if len(hit) and hit[0] > 0:
            i = hit[0]
            y = Y[i - 1] + (Y[i] - Y[i - 1]) * (x - X[i - 1]) / max(X[i] - X[i - 1], 1e-12)
        else:
            y = Y[end]
        out.append((float(H.half_width(prof, np.array([y]), np.array([z]))[0]), y, z))
    return np.array(out)


def mouth_edge_3d(prof=None):
    """The rim moved MOUTH_EDGE out of the opening along the surface (square to the rim in its tangent plane; the
    ends on the centre line moved along it): the shell's second cut (helmet.shell_outer). In the front plane the side
    corner could not move: the rim lies on the front face's turn into the side there (mouth_rim_3d). With the
    corners' mask (cached)."""
    if "edge" not in _MOUTH:
        prof = prof or H.Profile()
        R, sharp = mouth_rim_3d(prof)
        full = np.vstack([R, (R[1:-1] * [-1, 1, 1])[::-1]])
        t = (np.roll(full, -1, 0) - np.roll(full, 1, 0))[:len(R)]
        h = 1e-5
        y, z = R[:, 1], R[:, 2]
        gy = (H.half_width(prof, y + h, z) - H.half_width(prof, y - h, z)) / (2 * h)
        gz = (H.half_width(prof, y, z + h) - H.half_width(prof, y, z - h)) / (2 * h)
        o = np.cross(t, np.c_[np.ones(len(R)), -gy, -gz])
        o /= np.linalg.norm(o, axis=1)[:, None]
        n_in = inward_xz(full[:, [0, 2]])[:len(R)]
        o *= -np.sign(np.median(np.sum(o[:, [0, 2]] * n_in, 1)))
        E = R + o * MOUTH_EDGE
        ends = np.array([[0.0, R[0, 2] + MOUTH_EDGE], [0.0, R[-1, 2] - MOUTH_EDGE]])
        E[[0, -1]] = front_to_surface(prof, ends)
        _MOUTH["edge"] = (E, sharp)
    return _MOUTH["edge"]


def mouth_cut(prof=None, to_domain=None, edge=False):
    """The polygon (y, z) the shell is cut along (helmet.cut_loop): the rim's left half on the surface, from the top
    on the chin rim round to the bottom on it, closed outside the profile domain (the chin rim between its ends,
    1 mm out), so the centre line's vertices between the ends lie inside; and the rim's corners (y, z). to_domain
    carries the rim's points (x, y, z) into the domain (helmet.on_mesh: the mesh's own parameters); without it they
    are read at their (y, z). edge (with to_domain): the same for the loop MOUTH_EDGE outside it (mouth_edge_3d)."""
    if to_domain is not None or "cut" not in _MOUTH:
        prof = prof or H.Profile()
        R, sharp = mouth_edge_3d(prof) if edge else mouth_rim_3d(prof)
        if to_domain is not None:
            R = np.c_[R[:, 0], to_domain(R)]
        fc = prof.fine_chin
        t = np.gradient(fc, axis=0)
        t /= np.linalg.norm(t, axis=1)[:, None]
        out = -np.c_[-t[:, 1], t[:, 0]] * (1.0 if prof.area >= 0 else -1.0)    # out of the domain
        i0 = int(np.argmin(np.linalg.norm(fc - R[0, 1:], axis=1)))
        i1 = int(np.argmin(np.linalg.norm(fc - R[-1, 1:], axis=1)))
        idx = np.arange(i1, i0 - 1, -1) if i1 > i0 else np.arange(i1, i0 + 1)
        back = fc[idx] + out[idx] * 0.001
        poly = np.vstack([R[:, 1:], back])
        if to_domain is not None:
            return poly, R[sharp, 1:]
        _MOUTH["cut"] = (poly, R[sharp, 1:])
    return _MOUTH["cut"]


def mouth_rim_xz():
    """The rim's closed loop in the chin's front plane (x, z in m) on the surface: the left half from the top on the
    centre line round to the bottom, then the right half (its mirror) back up."""
    R = mouth_rim_3d()[0]
    return np.vstack([R[:, [0, 2]], (R[1:-1, [0, 2]] * [-1, 1])[::-1]])


def inward_xz(xz):
    """Unit normals in the front plane pointing into the closed loop xz."""
    t = np.roll(xz, -1, 0) - np.roll(xz, 1, 0)
    n = np.c_[-t[:, 1], t[:, 0]]
    n /= np.linalg.norm(n, axis=1)[:, None]
    c = xz.mean(0)
    return -n if np.mean(np.sum(n * (c - xz), 1)) < 0 else n


def mouth_inner_xz(rim):
    """The inner opening in the front plane: the rim moved in by MOUTH_INSET (top, side or bottom by the edge's
    direction), point for point."""
    n = inward_xz(rim)
    w = np.where(n[:, 1] < -0.7, MOUTH_INSET["top"], np.where(n[:, 1] > 0.7, MOUTH_INSET["bottom"],
                                                             MOUTH_INSET["side"]))
    w = np.convolve(np.r_[w[-4:], w, w[:4]], np.ones(9) / 9, mode="same")[4:-4]
    q = rim + n * w[:, None]
    for _ in range(3):                                 # untangle the corners' miters
        q = 0.25 * np.roll(q, 1, 0) + 0.5 * q + 0.25 * np.roll(q, -1, 0)
    return q


def at_depth(shell, xz, d):
    """Front-plane points cast onto the shell and moved back (+y) by d: the tunnel's points; with the shell's
    normals."""
    P, N = front_cast(shell, xz)
    return P + np.array([0.0, d, 0.0]), N


def ring_band(A, B, n):
    """Quads between two closed rings of n points each, own vertices: V, F."""
    return np.vstack([A, B]), loop_faces([A, B], n)


def mouth_lattice(shell, open_xz):
    """The opening's lattice in the lattice's plane (MOUTH_DEPTH behind the shell): across bars on every row of the
    triangles from edge to edge, the two diagonal families, and the column's two rails standing out of it. Mirror
    symmetric by construction. Pieces (V, F, mats)."""
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
        S3, NS = at_depth(shell, p, MOUTH_DEPTH)
        Vb, Fb = bar(S3, NS, w, hh)
        mat = MAT_FRAME if w == MOUTH_RAIL_W else MAT_MESH
        out.append((Vb, [list(f) for f in Fb], [mat] * len(Fb)))
        if mirror:
            out.append((Vb * [-1, 1, 1], [list(f)[::-1] for f in Fb], [mat] * len(Fb)))
    return out


def mouthpiece(shell):
    """The mouthpiece: the lip folding in from the rim (white, MAT, then black, MAT_FRAME; the shell is cut along the
    rim, helmet.cut_loop), the black wall sloping in and back to the inner opening (MAT_FRAME), the dark floor behind it (MAT_DARK), the
    lattice (MAT_MESH) and the column's rails (MAT_FRAME). Pieces (V, F, mats): the lip's bands, wall, floor, then
    the lattice's bars and rails."""
    R = mouth_rim_3d()[0]
    R0 = np.vstack([R, (R[1:-1] * [-1, 1, 1])[::-1]])  # the rim on the surface, the shell's cut edge
    rim = R0[:, [0, 2]]
    inner = mouth_inner_xz(rim)
    n = len(rim)
    nin = inward_xz(rim)
    _, NR0 = front_cast(shell, rim)
    lip = [R0]
    for d_in, d_back in MOUTH_LIP:
        L, _ = at_depth(shell, rim + nin * d_in, d_back)
        lip.append(L)
    W0 = lip[-1]
    W1, _ = at_depth(shell, inner, MOUTH_DEPTH)
    wall = [W0 + (W1 - W0) * k / 3.0 for k in range(4)]
    pieces = []
    for k in range(len(lip) - 1):                       # each lip band its own vertices: the lit fold reads crisp
        V, F = ring_band(lip[k], lip[k + 1], n)
        pieces.append((V, orient(V, F, NR0, R0), MAT if k == 0 else MAT_FRAME))
    V = np.vstack(wall)
    F = loop_faces(wall, n)
    pieces.append((V, orient(V, F, NR0, R0), MAT_FRAME))
    c = inner.mean(0)                                   # the floor: rings shrinking to the centre
    fl = [at_depth(shell, c + (inner - c) * sc, MOUTH_DEPTH + MOUTH_FLOOR)[0] for sc in (1.0, 0.67, 0.34)]
    c3 = at_depth(shell, c[None], MOUTH_DEPTH + MOUTH_FLOOR)[0]
    V = np.vstack(fl + [c3])
    F = [list(f) for f in loop_faces(fl, n)] + [[3 * n, (i + 1) % n + 2 * n, i + 2 * n] for i in range(n)]
    pieces.append((V, orient(V, F, NR0, R0), MAT_DARK))
    out = [(V, [list(f) for f in F], [m] * len(F)) for V, F, m in pieces]
    return out + mouth_lattice(shell, inner)


def mouth_dent(V, prof=None):
    """Shell vertices (helmet frame) inside the rim (in the profile domain, both halves: helmet.cut_loop's polygon;
    those on it stay), pushed back (+y) behind the tunnel's floor: the shell stays one closed surface, its faces there
    out of sight behind the lip, wall and floor. Returns the moved copy."""
    from matplotlib.path import Path
    poly = getattr(prof, "mouth_poly", None)            # the mesh's own (helmet.shell_outer), else the surface's
    poly = mouth_cut(prof)[0] if poly is None else poly
    Q = V[:, 1:]
    inside = Path(poly).contains_points(Q)
    idx = np.nonzero(inside)[0]
    d = np.full(len(idx), np.inf)
    for a, ab in zip(poly, np.roll(poly, -1, axis=0) - poly):
        tt = np.clip(((Q[idx] - a) @ ab) / max(ab @ ab, 1e-30), 0, 1)
        d = np.minimum(d, np.linalg.norm(Q[idx] - (a + tt[:, None] * ab), axis=1))
    inside[idx[d < 1e-7]] = False
    V = V.copy()
    V[inside, 1] += MOUTH_DEPTH + MOUTH_FLOOR + MOUTH_DENT
    return V


# ---------------------------------------------------------------- the chin cap's moulded LEATT (round 5, decision 56)
# Leatt's wordmark stands moulded on the chin cap's front slope, centred on the centre line, reading from the front
# with its tops towards the face: Pinata iso-left at 5x shows its letters' lit upper edges (black on black: no print),
# V25 white iso-left its soft lit tops. Cast through the solved cameras: its middle at y -192.9, z -58.1 mm
# (iso-left) and y -192.6, z -58.7 (V25); its length 43 mm (iso-left, x -20.1 to +23.0) and 35 mm (V25, whose
# camera puts it 13 mm to his left), 40 mm taken, centred (a moulding on the centre line). Raised CHIN_LEATT_H: the
# lit edges 1 to 2 px at 0.2 mm/px. The official wordmark's outlines (helmet_art.WORDMARK); the paint's black under
# its clear coat (MAT_CAP: the Pinata cap is black; MY27's is blue, V25's white).
CHIN_LEATT_C = (0.0, -0.1928, -0.0584)
CHIN_LEATT_LEN = 0.040
CHIN_LEATT_H = 0.0006
CHIN_LEATT_STEP = 0.0003          # m, outline points at most this far apart
MAT_CAP = "helmet_cap_letters"


def wordmark_loops(min_area=0.002):
    """The official wordmark's outlines in letter heights (x from its left, y down from its top), loops under
    min_area (antialiasing specks) dropped, the registered mark dropped."""
    import contourpy
    from PIL import Image
    from scipy import ndimage
    import helmet_art
    a = np.array(Image.open(helmet_art.WORDMARK).convert("RGBA"))[..., 3].astype(float) / 255.0
    m = a > 0.5
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.nonzero(sizes > 0.05 * sizes.max())[0])
    ys, xs = np.nonzero(keep)
    a = a * ndimage.binary_dilation(keep, iterations=2)
    c = np.pad(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 2)
    h = ys.max() - ys.min() + 1
    loops = []
    for ln in contourpy.contour_generator(z=c, line_type="Separate").lines(0.5):
        P = (np.asarray(ln, float) - 2.0) / h
        P = P[:-1] if np.allclose(P[0], P[-1]) else P
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        if len(P) > 3 and abs(area) > min_area:
            loops.append(P)
    return loops


def chin_wordmark(shell):
    """The raised LEATT on the chin cap: its top (Delaunay over the outline points and an inner grid, triangles kept
    whose centroid and edge midpoints lie inside) CHIN_LEATT_H over the shell, its walls down to SINK under it, each
    with its own vertices (crisp edges). Laid in the shell's tangent plane at CHIN_LEATT_C (across: x; up: towards the
    face along the slope) and cast back onto the shell along its normal there. Pieces (V, F, mats)."""
    from matplotlib.path import Path
    from scipy.spatial import Delaunay
    import types
    C0 = np.asarray(CHIN_LEATT_C, float)
    P0, N0 = shell.snap(C0[None])
    P0, N0 = P0[0], N0[0]
    ex = np.array([1.0, 0.0, 0.0]) - N0 * N0[0]
    ex /= np.linalg.norm(ex)
    ey = np.cross(N0, ex)
    ey = ey if ey[1] > 0 else -ey
    near = np.nonzero(np.linalg.norm(shell.V[shell.F].mean(1) - P0, axis=1) < 0.05)[0]
    local = types.SimpleNamespace(V=shell.V, F=shell.F[near], N=shell.N)
    loops = wordmark_loops()
    asp = max(L[:, 0].max() for L in loops)
    hgt = CHIN_LEATT_LEN / asp
    loops2 = [_resample_closed(np.c_[(L[:, 0] - asp / 2) * hgt, (0.5 - L[:, 1]) * hgt], CHIN_LEATT_STEP)
              for L in loops]

    def inside(Q):
        r = np.zeros(len(Q), bool)
        for L2 in loops2:
            r ^= Path(L2).contains_points(Q)
        return r

    def lift(Q, t):
        S = P0 + Q[:, :1] * ex + Q[:, 1:] * ey
        X, NX = cast_dir(local, S + N0 * 0.01, -N0)
        return X + NX * t

    bp = np.vstack(loops2)
    lo, hi = bp.min(0), bp.max(0)
    g = 0.0008
    gx, gy = np.meshgrid(np.arange(lo[0] + g / 2, hi[0], g), np.arange(lo[1] + g / 2, hi[1], g))
    G2 = np.c_[gx.ravel(), gy.ravel()]
    G2 = G2[inside(G2)]
    from scipy.spatial import cKDTree
    G2 = G2[cKDTree(bp).query(G2)[0] > 0.0002]
    pts = np.vstack([bp, G2])
    tri = Delaunay(pts).simplices
    T = pts[tri]
    ok = inside(T.mean(1))
    for a_, b_ in ((0, 1), (1, 2), (2, 0)):
        ok &= inside(0.45 * (T[:, a_] + T[:, b_]) + 0.1 * T.mean(1))
    tri = tri[ok]
    V = lift(pts, CHIN_LEATT_H)
    nm = np.cross(V[tri[:, 1]] - V[tri[:, 0]], V[tri[:, 2]] - V[tri[:, 0]])
    flip = (nm @ N0) < 0
    tri[flip] = tri[flip][:, ::-1]
    out = [(V, tri.tolist(), [MAT_CAP] * len(tri))]
    for L2 in loops2:
        n = len(L2)
        Vt, Vb = lift(L2, CHIN_LEATT_H), lift(L2, -SINK)
        e = np.roll(L2, -1, axis=0) - L2
        rgt = np.c_[e[:, 1], -e[:, 0]] / np.maximum(np.linalg.norm(e, axis=1), 1e-12)[:, None]
        k = int(np.argmax(np.linalg.norm(e, axis=1)))
        mid = 0.5 * (L2[k] + L2[(k + 1) % n])
        sgn = -1.0 if inside((mid + rgt[k] * 1e-5)[None])[0] else 1.0     # rgt * sgn: away from the letter
        i = np.arange(n)
        j = (i + 1) % n
        q = np.c_[i, j, n + j, n + i]
        fn = np.cross(Vt[j] - Vt[i], Vb[i] - Vt[i])
        outv = (sgn * rgt)[:, :1] * ex + (sgn * rgt)[:, 1:] * ey
        q[(fn * outv).sum(1) < 0] = q[(fn * outv).sum(1) < 0][:, ::-1]
        out.append((np.vstack([Vt, Vb]), q.tolist(), [MAT_CAP] * n))
    return out


def _resample_closed(P, step):
    """A closed loop with points at most step apart (its own points kept: corners stay sharp)."""
    out = []
    for a, b in zip(P, np.roll(P, -1, axis=0)):
        k = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out.append(a + (b - a) * (np.arange(k) / k)[:, None])
    return np.vstack(out)


def _resample_open_keep(P, step):
    """An open polyline with points at most step apart (its own points kept: corners stay sharp)."""
    out = [P[:1]]
    for a, b in zip(P[:-1], P[1:]):
        k = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out.append(a + (b - a) * (np.arange(1, k + 1) / k)[:, None])
    return np.vstack(out)


def mitred_outward(P, N, most=3.0):
    """outward(P, N) where the loop runs straight; at a corner the bisector of its two sides' normals, long enough
    that an offset along it keeps both sides parallel (a mitre: the rim's outer edge keeps the corner), at most most
    times."""
    o = outward(P, N)
    a, b = P - np.roll(P, 1, 0), np.roll(P, -1, 0) - P
    na, nb = np.cross(a, N), np.cross(b, N)
    la, lb = np.linalg.norm(na, axis=1), np.linalg.norm(nb, axis=1)
    ok = (la > 1e-9) & (lb > 1e-9)
    na, nb = na / np.maximum(la, 1e-12)[:, None], nb / np.maximum(lb, 1e-12)[:, None]
    na *= np.sign((na * o).sum(1))[:, None]
    nb *= np.sign((nb * o).sum(1))[:, None]
    m = na + nb
    m /= np.maximum(np.linalg.norm(m, axis=1), 1e-12)[:, None]
    m /= np.clip((m * na).sum(1), 1.0 / most, 1.0)[:, None]
    return np.where(ok[:, None], m, o)


def vent_pieces(shell, P, N, rim_w, rim_h, rim_mat=MAT_FRAME, mesh=None, mitre=False):
    """A vent's rim (rim_mat), dark floor (MAT_DARK) and wire mesh (MAT_MESH; mesh: its pitch, wire width and angle,
    else the rear slots') round its loop P on the shell; mitre: the rim's outer edge keeps the loop's corners."""
    Q, NQ = shell.snap(P + (mitred_outward(P, N) if mitre else outward(P, N)) * rim_w)
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
# Round 5 (decision 56; the coordinator's 1:1 review: Leatt's vents angular where ours were rounded, the tag dull with
# no recess, the brow one dark moulding where Leatt's has lit facets and a lit lower edge). Retraced at 4x with a grid
# (scratch k5d): the centre vent's mesh ends at the divider in a straight slant from (753, 631) to (785, 667), the side
# vent is a slanted parallelogram with its tip at (993, 706). The loops keep their traced corners (sampled along each
# side) and the rim's outer edge is mitred there (main: resampled through the corners and offset along the loop's
# normals, its ends rounded about 1.7 mm). The tag sits in a recess (Pinata iso-left at 5x: a dark groove about 1.5 px
# round its rim, then a lit bevel about 2 px): BROW_RECESS scales its outline about its centre for the groove's outer
# edge, the bevel's top, the surround's top and the surround's foot, where it runs into the shell (BROW_RECESS_H: the
# groove's floor and the surround's top over the shell; the tag's top 0.1 mm under the surround's), all but the tag
# and the groove in the brow's own black under the clear coat (MAT_BROW). The side vent's lower edge stays phase 2's
# (Leatt's runs 15 px lower at its left end, below the shell's port edge: our brow ends at the port 25 to 40 px, 5 to
# 8 mm, above Leatt's lit lower edge under the side vent; its lower lip band and the brow's lit facets are round 6).
BROW_VENTS_PX = [
    [(663, 625), (720, 630), (753, 631), (785, 667), (700, 665), (663, 664)],      # centre: its left half
    [(843, 652), (946, 664), (993, 706), (960, 697), (920, 686), (880, 676), (850, 670)]]
BROW_RIM_W, BROW_RIM_H = 0.0015, 0.0010
BROW_TAG_PX = [(1083, 690), (1112, 729), (1060, 734)]        # its rim's corners (3x)
BROW_TAG_ROUND, BROW_TAG_IN = 4.0, 0.55     # corner radius px (about 1 mm); the dark centre's size against the outline
BROW_TAG_H = 0.0005
BROW_RECESS = (1.10, 1.24, 1.30, 1.55)
BROW_RECESS_H = (0.00015, 0.0006)
MAT_TAG = "helmet_tag_rim"
MAT_BROW = "helmet_brow_moulding"


def brow_vents(shell):
    """The brow's mesh vents: the centre one (traced across the centre line) and the side one each side, and the
    brow tag each side. Pieces (V, F, mats)."""
    shell = ExactShell(shell.V, shell.F)
    out = []
    (P, N), *loops = brow_vent_loops(shell)
    out += mirror(vent_pieces(shell, P, N, BROW_RIM_W, BROW_RIM_H, mitre=True), 1.0)
    side = []
    for P, N in loops:
        side += vent_pieces(shell, P, N, BROW_RIM_W, BROW_RIM_H, mitre=True)
    side += brow_tag(shell)
    return out + mirror(side, 1.0) + mirror(side, -1.0)


def brow_vent_loops(shell):
    """The brow vents' loops on the shell (P, N): the centre one across the centre line, then the side one on his
    left, their traced corners kept."""
    out = [sym_loop(shell, BROW_VENTS_PX[0])]
    for px in BROW_VENTS_PX[1:]:
        out.append(shell.cast("isoleft", _resample_closed(np.asarray(px, float), 2.0), side=1.0))
    return out


def _bands(rings, N, P):
    """Quads between consecutive rings, each band with its own vertices (crisp edges), facing along N."""
    n = len(P)
    V, F = [], []
    for k, (A_, B_) in enumerate(zip(rings[:-1], rings[1:])):
        V += [A_, B_]
        F += [[i + 2 * n * k for i in f] for f in loop_faces([A_, B_], n)]
    V = np.vstack(V)
    return V, orient(V, F, N, P)


def brow_tag(shell):
    """The brow tag on his left in its recess: the rim (MAT_TAG) round its dark centre (MAT_DARK), standing on the
    groove's floor (MAT_DARK), the bevel up to the surround's top and the surround running into the shell
    (MAT_BROW). Pieces (V, F, mats)."""
    uv = resample_loop(round_corners(BROW_TAG_PX, BROW_TAG_ROUND), 1.5)
    c2 = uv.mean(0)
    P, N = shell.cast("isoleft", uv, side=1.0)
    c = P.mean(0)
    Pi, Ni = shell.snap(c + (P - c) * BROW_TAG_IN)
    out = []
    V, F = plate(Pi, Ni, P, N, BROW_TAG_H)
    out.append((V, F, [MAT_TAG] * len(F)))
    Vc, Fc = cap(Pi, Ni, BROW_TAG_H, shell)
    out.append((Vc, Fc, [MAT_DARK] * len(Fc)))
    (Pg, Ng), (Pb, Nb), (Pt, Nt), (Pf, Nf) = [shell.cast("isoleft", c2 + (uv - c2) * k, side=1.0)
                                              for k in BROW_RECESS]
    hf, ht = BROW_RECESS_H
    V, F = _bands([P + N * hf, Pg + Ng * hf], N, P)
    out.append((V, F, [MAT_DARK] * len(F)))
    V, F = _bands([Pg + Ng * hf, Pb + Nb * ht, Pt + Nt * ht, Pf - Nf * SINK], N, P)
    out.append((V, F, [MAT_BROW] * len(F)))
    return out



def build(Vo, Fo, part=None):
    """The detail as one Part (helmet frame): the crown vents in MAT_INSERT, the rear lower pieces in MAT, their
    slots' floor in MAT_DARK, the slots' wire mesh in MAT_MESH, the grip panels (floor and tiles in MAT_GRIP with UVs
    for its grain, MAT_GRIP_GROOVE between the tiles, their bevels MAT_GRIP_BEVEL, walls MAT_GRIP_EDGE), the chin's mouthpiece in MAT_FRAME (its outer wall in
    MAT) with its floor in MAT_DARK and its lattice in MAT_MESH, the chin bar's side vents (wall MAT, floor MAT_DARK,
    mesh MAT_MESH), the brow's vents (rim MAT_FRAME, floor MAT_DARK, mesh MAT_MESH) and tag (MAT_TAG round a
    MAT_DARK centre, in its recess: MAT_BROW round a MAT_DARK groove)."""
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
    for V, F, mats in mouthpiece(shell) + side_vents(shell) + brow_vents(shell) + chin_wordmark(shell):
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
