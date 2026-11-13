"""Damien's goggle and eyes: Leatt Velocity 5.5 Iriz (Pinata Teal frame and strap) with a purple mirror lens, and
his brown eyes behind it. Built by helmet.py (build calls build_goggle and eyes); helmet.py's CLI writes the npz.

Frames: GOGGLE frame = metres, x to the wearer's left, y backwards, z up (the axes of body.py's MB frame), origin
at the midpoint of his eye centres; the goggle is placed on his face by a translation only (the shapes are measured
square to the face). HELMET frame: helmet.py's.

Sources (research/rider-ledger/goggle.md has every number with its source):
  SHAPE     Leatt's MY27 Moto 8.5 kit photos with the Velocity 5.5 on (us.leatt.com moto-8-5-helmet-kit,
            31505_..._Blue_Red_1/2/4_1027000180.jpg, saved in reference/leatt-gear/goggles/) through pinhole cameras
            fitted to the helmet shell's silhouette (fitted in helmet.py's helmet frame): the goggle's front outline
            back-projected onto its front surface, the side profile from the side views; the Pinata Teal ISO view
            and Leatt's exploded view for the facets, vents and nose bridge.
  SCALE     the helmet (its own 45 mm strap scale, helmet.py).
  EYES      MakeHuman's CC0 high-poly eye proxy fitted by its mhclo onto his shaped mesh puts the eyeball (radius
            0.955 x and centre 0.03 x the helper-eye sphere's radius behind its centre) where the lids close round
            it; here it is rebuilt by script on the same sphere, iris and cornea anatomical (iris 11.8 mm, pupil
            3.6 mm in daylight, cornea radius 7.8 mm).
"""
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import helmet as H      # noqa: E402
import mhdata as mh     # noqa: E402

TEXDIR = H.TEXDIR


# ---------------------------------------------------------------- eyes
EYE_R_OVER_HELPER = 0.9554         # MakeHuman eye proxy (CC0 high-poly, mhclo-fitted on his mesh): eyeball radius
EYE_BACK_OVER_HELPER = 0.0317      # ... and its centre behind the helper-eye sphere's centre, both / helper radius
IRIS_R = 0.0059                    # m, iris radius (adult mean 11.7 to 11.8 mm diameter)
PUPIL_R = 0.0018                   # m, pupil radius in daylight (3 to 4 mm)
CORNEA_RC = 0.0078                 # m, anterior corneal radius of curvature (adult mean 7.8 mm)
EYE_THETA_MAX = math.radians(120)  # the cap kept (the rest lies deep in the socket)
EYE_TEX = 512


def helper_sphere(body, side):
    """Centre and radius of MakeHuman's helper-eye sphere on his shaped mesh (MB rest frame)."""
    meta = json.loads(str(body["meta"]))
    base = mh.Base()
    V = mh.to_mb(mh.shape(base, meta["macro"]))
    V[:, 2] -= V[base.group_verts("body"), 2].min()
    P = V[base.group_verts(f"helper-{side}-eye")]
    A = np.c_[2 * P, np.ones(len(P))]
    s = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    return s[:3], float(np.sqrt(s[3] + s[:3] @ s[:3]))


def eye_geometry(body):
    """Eyeball centre and radius per side ('L', 'R'), gaze along -y (ahead)."""
    out = {}
    for s, side in (("L", "l"), ("R", "r")):
        c, r = helper_sphere(body, side)
        out[s] = (c + np.array([0.0, EYE_BACK_OVER_HELPER * r, 0.0]), EYE_R_OVER_HELPER * r)
    return out


EYE_UV_POW = 0.6                   # polar map r = 0.5 (theta / EYE_THETA_MAX) ** 0.6: more texels on the iris


def eye_texture(path, n=EYE_TEX, R=0.0158):
    """Brown eye (Damien), polar map: texel at radius r from the centre -> angle from the gaze axis
    theta = (r / 0.5) ** (1 / EYE_UV_POW) * EYE_THETA_MAX, round it phi. Pupil, iris with radial fibres, an amber
    collarette and a dark limbal ring, sclera off-white with a few faint vessels towards the back. By script."""
    from PIL import Image, ImageDraw
    rng = np.random.default_rng(114)
    u, v = np.meshgrid((np.arange(n) + 0.5) / n * 2 - 1, (np.arange(n) + 0.5) / n * 2 - 1)
    th = np.hypot(u, v) ** (1 / EYE_UV_POW) * EYE_THETA_MAX
    ph = np.arctan2(v, u)
    rho = R * np.sin(np.minimum(th, np.pi / 2))                     # radius in the eye's frontal projection
    k = np.arange(1, 90)
    amp = rng.normal(0, 1, len(k)) / np.sqrt(k)
    pha = rng.uniform(0, 2 * np.pi, len(k))
    fib = np.zeros_like(ph)
    for a, kk, p in zip(amp, k, pha):
        fib += a * np.cos(kk * ph + p)
    fib = fib / np.abs(fib).max()
    t = np.clip((rho - PUPIL_R) / (IRIS_R - PUPIL_R), 0, 1)            # 0 at the pupil edge, 1 at the limbus
    dark = np.array([58, 32, 18.0])                                   # brown iris (sRGB)
    mid = np.array([104, 60, 28.0])
    amber = np.array([150, 98, 44.0])
    iris = dark + (mid - dark) * (0.5 + 0.5 * fib[..., None]) * (1 - 0.6 * t[..., None])
    coll = np.exp(-((t - 0.28) / 0.08) ** 2)[..., None]               # collarette ring
    iris = iris + (amber - iris) * 0.55 * coll * (0.6 + 0.4 * fib[..., None])
    limb = np.clip((t - 0.82) / 0.18, 0, 1)[..., None]
    iris = iris * (1 - 0.55 * limb)
    sclera = np.array([236, 230, 222.0]) * np.ones_like(iris)
    vm = Image.new("L", (n, n), 0)                                    # a few thin, wandering vessels
    dv = ImageDraw.Draw(vm)
    for _ in range(16):
        t_, p_ = math.radians(118), rng.uniform(0, 2 * np.pi)
        pts = []
        while t_ > math.radians(rng.uniform(48, 75)):
            r_ = 0.5 * (t_ / EYE_THETA_MAX) ** EYE_UV_POW
            pts.append(((0.5 + r_ * math.cos(p_)) * n, (0.5 + r_ * math.sin(p_)) * n))
            t_ -= math.radians(3)
            p_ += rng.normal(0, 0.05)
        dv.line(pts, fill=int(rng.uniform(60, 140)), width=1)
    vein = np.array(vm, float) / 255.0
    back = np.clip((th - math.radians(45)) / math.radians(50), 0, 1)
    sclera = sclera + (np.array([200, 120, 110.0]) - sclera) * (vein * 0.5)[..., None]
    sclera = sclera * (1 - 0.15 * back[..., None])
    img = np.where((rho < PUPIL_R)[..., None], np.array([10, 8, 7.0]), iris)
    lim = np.clip((rho - IRIS_R) / 0.0004, 0, 1)[..., None] * (th < np.pi / 2)[..., None] + (th >= np.pi / 2)[..., None]
    img = img * (1 - lim) + sclera * lim
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)


def _frame(gaze):
    g = gaze / np.linalg.norm(gaze)
    a = np.cross(g, [0, 0, 1.0])
    a /= np.linalg.norm(a)
    b = np.cross(a, g)
    return g, a, b


def build_eyes(body, nth=40, nph=64):
    """Eyeballs and corneas, each riding its eye bone (eye.L / eye.R) rigidly."""
    parts = []
    geo = eye_geometry(body)
    for s in ("L", "R"):
        c, R = geo[s]
        g, a, b = _frame(np.array([0.0, -1.0, 0.0]))
        ball = H.Part("eye_ball_" + s, bone="eye." + s)
        ths = np.r_[np.linspace(0, math.asin(IRIS_R / R), 14)[1:], np.linspace(math.asin(IRIS_R / R), EYE_THETA_MAX, nth)[1:]]
        phs = np.linspace(0, 2 * np.pi, nph, endpoint=False)
        # the cornea's bulge: over the iris the surface follows a sphere of radius CORNEA_RC meeting the eyeball
        # at the limbus (a separate refracting dome over a painted iris looked like a glass bead)
        axial = math.sqrt(R * R - IRIS_R * IRIS_R)
        sc = axial - math.sqrt(CORNEA_RC ** 2 - IRIS_R ** 2)

        def radius(th):
            return max(R, sc * math.cos(th) + math.sqrt(max(CORNEA_RC ** 2 - (sc * math.sin(th)) ** 2, 0.0)))
        apex = ball.add((c + g * radius(0.0))[None], [], "eye_ball")
        rings = []
        for th in ths:
            P = c + radius(th) * (np.cos(th) * g + np.sin(th) * (np.cos(phs)[:, None] * a + np.sin(phs)[:, None] * b))
            rings.append(ball.add(P, [], "eye_ball") + np.arange(nph))

        def uvp(th, ph):
            r = (th / EYE_THETA_MAX) ** EYE_UV_POW * 0.5
            return (0.5 + r * math.cos(ph), 0.5 + r * math.sin(ph))
        for j in range(nph):
            k = (j + 1) % nph
            ball.F.append([apex, rings[0][j], rings[0][k]]); ball.M.append("eye_ball")
            ball.UV.append([uvp(0, 0), uvp(ths[0], phs[j]), uvp(ths[0], phs[j] + 2 * np.pi / nph)])
        for i in range(len(ths) - 1):
            for j in range(nph):
                k = (j + 1) % nph
                phk = phs[j] + 2 * np.pi / nph
                ball.F.append([rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]]); ball.M.append("eye_ball")
                ball.UV.append([uvp(ths[i], phs[j]), uvp(ths[i + 1], phs[j]), uvp(ths[i + 1], phk), uvp(ths[i], phk)])
        parts.append(ball)
    return parts, dict(eye_radius_mm=round(geo["L"][1] * 1000, 2),
                       eye_centres=[np.round(geo[s][0], 4).tolist() for s in ("L", "R")])


# ---------------------------------------------------------------- the goggle's shape (GOGGLE frame, metres)
# The lens front is a cylinder: plan an ellipse y = A (1 - sqrt(1 - (x / a)^2)) (origin at its front centre),
# rulings tilted back by TILT at the top. Points on it are named by (s, z): s the arc length along the plan from
# the centre (+ to his left), z the height. Outlines are closed curves in (s, z) from control points on the left
# half (top centre, round the left end, the bottom, up the nose arch to the bottom centre), mirrored for the right.
# GP holds every fitted number (measured in Leatt's calibrated photos: see the ledger).
GP = dict(
    a=0.118, A=0.072, tilt=0.0,
    # lens opening (the frame front face's inner edge), half outline (s, z) in m
    open=[(0, 0.029), (0.045, 0.030), (0.080, 0.028), (0.091, 0.020), (0.094, -0.006), (0.090, -0.032),
          (0.066, -0.038), (0.028, -0.032), (0, -0.014)],
    # frame outer edge (front face), half outline; the bottom centre is the bridge over the nose (it hangs lower)
    out=[(0, 0.042), (0.045, 0.043), (0.085, 0.040), (0.104, 0.032), (0.107, -0.006), (0.102, -0.046),
         (0.072, -0.052), (0.028, -0.050), (0, -0.062)],
    # frame depth behind the lens front at each control point (front face to the back face); shallow over the nose
    depth=[0.024, 0.024, 0.022, 0.020, 0.018, 0.016, 0.016, 0.012, 0.006],
    t_front=0.0035,        # front face ahead of the lens front
    taper=0.004,           # the outer wall leans out this much going back
    back_in=0.006,         # back face width (the foam's seat), measured inward from the outer wall's back
)
VENT_ROWS = (0.25, 0.75)           # the top vents' slots run between these fractions of the outer wall's depth
CREASE, FACET_DROP = 0.45, 0.0035  # front face: crease at 45 % of its width, outer facet sloping back 3.5 mm
# rings round the frame's cross-section: a lens, b lip, c face, d crease, e face edge, e' wall top, e1, e2 (vent
# rows), f wall back, g back face, h inner wall
RING_VENT, RING_BACK_OUT, RING_BACK_IN = 6, 8, 9
LENS_T, LENS_GAP, LENS_IN_T = 0.0012, 0.0016, 0.0006     # outer lens, foam spacer gap, inner lens (m)
LENS_GROOVE = 0.003                                     # the lens runs this far under the frame's front lip


class LensSurface:
    def __init__(self, gp=None):
        gp = gp or GP
        self.a, self.A, self.tilt = gp["a"], gp["A"], gp["tilt"]
        x = np.linspace(0, self.a * 0.995, 4000)
        y = self.A * (1 - np.sqrt(1 - (x / self.a) ** 2))
        self.X, self.Y = x, y
        self.S = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]

    def point(self, s, z, off=0.0):
        """Points on the lens front surface (off > 0: in front of it along its normal)."""
        s, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float))
        sg = np.where(s < 0, -1.0, 1.0)
        x = np.interp(np.abs(s), self.S, self.X)
        y = np.interp(np.abs(s), self.S, self.Y)
        dx = np.gradient(self.X)
        dy = np.gradient(self.Y)
        ds = np.hypot(dx, dy)
        tx = np.interp(np.abs(s), self.S, dx / ds)
        ty = np.interp(np.abs(s), self.S, dy / ds)
        T = np.stack([tx, ty * sg, np.zeros_like(tx)], -1)            # plan tangent, d/ds
        tt = math.tan(self.tilt)
        Rl = np.array([0.0, tt, 1.0]) / math.hypot(tt, 1.0)
        N = np.cross(T, Rl)
        N /= np.linalg.norm(N, axis=-1)[..., None]
        P = np.stack([sg * x, y + z * tt, z], -1)
        return P + N * np.asarray(off)[..., None] if np.ndim(off) else P + N * off, N


def catmull_closed(P, per=12):
    """Closed centripetal Catmull-Rom through P (k x 2), per samples per segment; returns samples and, for each,
    the index of the control point that starts its segment and the fraction along it."""
    P = np.asarray(P, float)
    k = len(P)
    out, seg, frac = [], [], []
    for i in range(k):
        p0, p1, p2, p3 = P[(i - 1) % k], P[i], P[(i + 1) % k], P[(i + 2) % k]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-9) ** 0.5
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-9) ** 0.5
        t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-9) ** 0.5
        for j in range(per):
            u = j / per
            t = t1 + (t2 - t1) * u
            A1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            A2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            A3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
            B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
            out.append((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2)
            seg.append(i)
            frac.append(u)
    return np.array(out), np.array(seg), np.array(frac)


def full_loop(half):
    """Half outline (top centre ... bottom centre, s >= 0) -> closed loop: the left half, then the right half
    (mirrored) back up to the top: anticlockwise seen from the front (x left, z up)."""
    h = np.asarray(half, float)
    right = h[1:-1][::-1] * [-1, 1]
    return np.vstack([h, right])


def loop_values(vals):
    v = np.asarray(vals, float)
    return np.r_[v, v[1:-1][::-1]]


def outward2d(C):
    """Unit outward normals of a closed (s, z) loop (anticlockwise seen from the front: s grows to his left)."""
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    n = np.c_[t[:, 1], -t[:, 0]]
    area = 0.5 * np.sum(C[:, 0] * np.roll(C[:, 1], -1) - np.roll(C[:, 0], -1) * C[:, 1])
    return n if area > 0 else -n


def frame_rings(gp=None, per=12):
    """The frame as rings (closed loops of 3D points, GOGGLE frame) round its cross-section: lens contact, front
    lip, front face, outer wall, back face, inner wall."""
    gp = gp or GP
    L = LensSurface(gp)
    Co, seg, frac = catmull_closed(full_loop(gp["open"]), per)
    Cu, _, _ = catmull_closed(full_loop(gp["out"]), per)
    D = loop_values(gp["depth"])
    d = D[seg] + (D[(seg + 1) % len(D)] - D[seg]) * frac
    no, nu = outward2d(Co), outward2d(Cu)
    tf, r = gp["t_front"], 0.0008
    rings = []

    def ring(C, off):
        return L.point(C[:, 0], C[:, 1], off)[0]
    # the front face is two facets (Leatt ISO, kit photos): flat from the lip to a crease at CREASE of its width,
    # then sloping back FACET_DROP to the outer edge
    crease = Co + (Cu - Co) * CREASE
    rings.append(ring(Co, 0.0003))                                  # a: against the lens front
    rings.append(ring(Co, tf - r))                                  # b: lip wall
    rings.append(ring(Co + no * r, tf))                             # c: front face, inner edge
    rings.append(ring(crease, tf))                                  # d: the crease
    rings.append(ring(Cu - nu * r, tf - FACET_DROP))                # e: front face, outer edge
    rings.append(ring(Cu, tf - FACET_DROP - r))                     # e': outer wall top
    back_out = Cu + nu * gp["taper"]
    top_off = tf - FACET_DROP - r
    for f_ in VENT_ROWS:                                            # e1, e2: vent rows on the outer wall
        rings.append(ring(Cu + nu * gp["taper"] * f_, top_off - (top_off + d) * f_))
    rings.append(ring(back_out, -d))                                # f: outer wall back
    rings.append(ring(back_out - nu * gp["back_in"], -d))           # g: back face inner edge
    rings.append(ring(Co + no * 0.001, -(LENS_T + LENS_GAP + LENS_IN_T + 0.0005)))   # h: inner wall at the lens back
    return rings, dict(Co=Co, Cu=Cu, depth=d, L=L)


# top vents: slots across the top of the frame, s ranges on each side (Leatt exploded view: three angled slots a
# side either side of the moulded logo), and the loop index ranges they apply to
VENTS_S = [(0.008, 0.024), (0.030, 0.046), (0.052, 0.068)]


def ring_faces(part, rings, mats, uv=None):
    """Quads between consecutive closed rings (the last ring joins the first). mats: per ring gap, a material
    name or a per-segment list."""
    m = len(rings[0])
    ids = [part.add(r, [], "x") + np.arange(m) for r in rings]
    for k in range(len(rings)):
        A_, B_ = ids[k], ids[(k + 1) % len(rings)]
        mk = mats[k]
        for i in range(m):
            j = (i + 1) % m
            part.F.append([A_[i], A_[j], B_[j], B_[i]])
            part.M.append(mk if isinstance(mk, str) else mk[i])
            part.UV.append([(0.0, 0.0)] * 4)
    return ids


def build_frame(gp=None):
    gp = gp or GP
    rings, info = frame_rings(gp)
    Co = info["Co"]
    m = len(Co)
    # vents: segments of the outer wall's middle band on the top (|s| in a vent range, above the top corners)
    Cu = info["Cu"]
    top = Cu[:, 1] > np.max(Cu[:, 1]) - 0.010
    vent = np.array(["goggle_frame"] * m, dtype=object)
    for s0, s1 in VENTS_S:
        sel = top & (np.abs(Cu[:, 0]) >= s0) & (np.abs(Cu[:, 0]) <= s1)
        vent[sel] = "goggle_vent"
    mats = ["goggle_frame"] * len(rings)
    mats[RING_VENT] = list(vent)                 # between e1 and e2
    mats[-1] = "goggle_frame"                    # h -> a: hidden in the lens groove
    # support rings 0.35 mm either side of every edge: smooth shading then turns only at the edges, and the wide
    # faces read flat (without them the bezel shaded like a tube)
    R2, M2 = [], []
    K = len(rings)
    for k in range(K):
        A_, B_ = rings[k], rings[(k + 1) % K]
        gap = np.linalg.norm(B_ - A_, axis=1)[:, None]
        f_ = np.clip(0.00035 / np.maximum(gap, 1e-6), 0, 0.3)
        R2 += [A_, A_ + (B_ - A_) * f_, B_ + (A_ - B_) * f_]
        M2 += [mats[k]] * 3
    fr = H.Part("goggle_frame")
    ring_faces(fr, R2, M2)
    return fr, info


def lens_region(gp, grow):
    """Lens outline in (s, z): the opening grown by grow (under the frame's lip)."""
    Co, _, _ = catmull_closed(full_loop(gp["open"]), 12)
    return Co + outward2d(Co) * grow


def sheet(L, poly, off, h=0.004):
    """Triangulated region of the lens surface inside poly ((s, z) loop) at offset off: vertices, triangles
    (anticlockwise seen from the front), and the boundary vertex count (the first len(poly))."""
    from scipy.spatial import Delaunay
    lo, hi = poly.min(0), poly.max(0)
    gs, gz = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
    gs = gs + (np.arange(gs.shape[0])[:, None] % 2) * h / 2
    pts = np.c_[gs.ravel(), gz.ravel()]
    o = H.Profile.__new__(H.Profile)
    o.outline = poly
    keep = H.Profile.inside(o, pts) & (cKDTree(poly).query(pts)[0] > 0.4 * h)
    P2 = np.vstack([poly, pts[keep]])
    T = Delaunay(P2).simplices
    T = T[H.Profile.inside(o, P2[T].mean(1))]
    a, b, c = P2[T[:, 0]], P2[T[:, 1]], P2[T[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T[cr < 0] = T[cr < 0][:, ::-1]
    # (s, z) anticlockwise with s to his left = clockwise seen from the front (x left): flip to face forward
    T = T[:, ::-1]
    V = L.point(P2[:, 0], P2[:, 1], off)[0]
    return V, T, len(poly)


def closed_sheet(part, L, poly, off_front, off_back, mat_front, mat_back, mat_edge):
    """A lens sheet as a closed solid: front, back (the same triangulation further back) and the edge strip."""
    Vf, T, nb = sheet(L, poly, off_front)
    Vb = sheet(L, poly, off_back)[0]
    of = part.add(Vf, [list(t) for t in T], mat_front, [[(0.0, 0.0)] * 3 for _ in T])
    ob = part.add(Vb, [list(t[::-1]) for t in T], mat_back, [[(0.0, 0.0)] * 3 for _ in T])
    for i in range(nb):
        j = (i + 1) % nb
        part.F.append([of + j, of + i, ob + i, ob + j]); part.M.append(mat_edge); part.UV.append([(0.0, 0.0)] * 4)
    return of, ob


def build_lens(gp=None):
    """The double lens: the outer (mirror coated on its front) in the frame's groove, the thin inner lens behind it
    on the foam spacer."""
    gp = gp or GP
    L = LensSurface(gp)
    lens = H.Part("goggle_lens")
    poly = lens_region(gp, LENS_GROOVE)
    closed_sheet(lens, L, poly, 0.0, -LENS_T, "goggle_lens_mirror", "goggle_lens_clear", "goggle_lens_clear")
    poly_in = lens_region(gp, LENS_GROOVE - 0.0015)
    closed_sheet(lens, L, poly_in, -(LENS_T + LENS_GAP), -(LENS_T + LENS_GAP + LENS_IN_T),
                 "goggle_lens_clear", "goggle_lens_clear", "goggle_lens_clear")
    return lens


POST_S_IN, POST_Z = 0.014, 0.003    # tear-off posts: this far in from the opening's end, this high (Leatt photos)


def build_posts(gp=None):
    """Bare tear-off posts (Damien runs no tear-offs): a square boss on the lens and a round stud with a head."""
    gp = gp or GP
    L = LensSurface(gp)
    s_end = max(p[0] for p in gp["open"])
    posts = H.Part("goggle_posts")
    for sg in (1, -1):
        s0 = sg * (s_end - POST_S_IN)
        P0, N0 = L.point(s0, POST_Z, 0.0)
        P1, _ = L.point(s0 + 0.001, POST_Z, 0.0)
        t = (P1 - P0) / np.linalg.norm(P1 - P0)
        up = np.cross(N0, t)
        up /= np.linalg.norm(up)
        # square boss 4.5 x 4.5 x 1.5 mm
        box = []
        for h, (a, b) in ((0, (-1, -1)), (0, (1, -1)), (0, (1, 1)), (0, (-1, 1)),
                          (1, (-1, -1)), (1, (1, -1)), (1, (1, 1)), (1, (-1, 1))):
            box.append(P0 + t * a * 0.00225 + up * b * 0.00225 + N0 * (0.0015 * h - 0.0002))
        quads = [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        posts.add(np.array(box), quads, "goggle_post", [[(0.0, 0.0)] * 4] * 6)
        # stud 2.4 mm across, 2.5 mm long, head 3.4 mm
        k = 12
        ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
        rings = []
        for rr, hh in ((0.0012, 0.0013), (0.0012, 0.0033), (0.0017, 0.0036), (0.0017, 0.0042), (0.0008, 0.0045)):
            rings.append(P0 + N0 * hh + rr * (np.cos(ang)[:, None] * t + np.sin(ang)[:, None] * up))
        ids = [posts.add(r, [], "goggle_post") + np.arange(k) for r in rings]
        for a_, b_ in zip(ids[:-1], ids[1:]):
            for i in range(k):
                j = (i + 1) % k
                posts.F.append([a_[i], a_[j], b_[j], b_[i]]); posts.M.append("goggle_post")
                posts.UV.append([(0.0, 0.0)] * 4)
        tip = posts.add((P0 + N0 * 0.0046)[None], [], "goggle_post")
        for i in range(k):
            j = (i + 1) % k
            posts.F.append([ids[-1][i], ids[-1][j], tip]); posts.M.append("goggle_post"); posts.UV.append([(0.0, 0.0)] * 3)
    return posts


OR_LEN, OR_T, OR_BACK_H = 0.030, 0.008, 0.052     # outrigger: length behind the frame, thickness, height at the
                                                 # strap slot (45 mm strap + 3.5 mm each side); Leatt ISO, kit photos


def outrigger_frames(gp=None):
    """Each outrigger's corners (GOGGLE frame): it continues the frame's side end backwards along the plan's
    tangent there. Returns {side: (8 x 3 corners, strap end point, outward normal)}."""
    gp = gp or GP
    L = LensSurface(gp)
    out = {}
    s_end = max(p[0] for p in gp["out"])
    zt = gp["out"][3][1] - 0.003
    zb = gp["out"][5][1] + 0.003
    zc = 0.5 * (zt + zb)
    for sg in (1, -1):
        s0 = sg * (s_end - 0.006)
        P0, N0 = L.point(s0, zc, 0.0)
        P1, _ = L.point(s0 + sg * 0.001, zc, 0.0)
        t = (P1 - P0) / np.linalg.norm(P1 - P0)                    # along the plan, round the end (backwards)
        t[2] = 0.0
        t /= np.linalg.norm(t)
        n = np.array([N0[0], N0[1], 0.0])
        n /= np.linalg.norm(n)
        C = []
        for u, h in ((0, zt), (0, zb), (1, zc - OR_BACK_H / 2), (1, zc + OR_BACK_H / 2)):
            C.append(P0 + t * OR_LEN * u + np.array([0, 0, h - zc]))
        C = np.array(C)
        box = np.vstack([C + n * (gp["t_front"] - 0.0005), C + n * (gp["t_front"] - 0.0005 - OR_T)])
        out[sg] = (box, P0 + t * (OR_LEN - 0.004) + n * (gp["t_front"] - 0.0005 - OR_T / 2), n)
    return out


def build_outriggers(gp=None):
    """Black outriggers, white vertical LEATT on the outer face (letter tops towards the strap; Leatt's ISO view
    and the Pinata kit photo, right side), one image half per side."""
    o = H.Part("goggle_outriggers")
    for sg, (box, end, n) in outrigger_frames(gp).items():
        # corners: 0 front-top, 1 front-bottom, 2 back-bottom, 3 back-top (outer), 4..7 inner
        quads = [[0, 1, 2, 3], [7, 6, 5, 4], [4, 5, 1, 0], [3, 2, 6, 7], [4, 0, 3, 7], [1, 5, 6, 2]]
        if sg < 0:
            quads = [q[::-1] for q in quads]
        uvs = [[(0.5, 0.5)] * 4 for _ in quads]
        # outer face: u = height (0 bottom .. 1 top) in its image half, v = along the outrigger (0 front .. 1 back)
        h0, h1 = (0.0, 0.5) if sg > 0 else (0.5, 1.0)
        c = {0: (h1, 0.0), 1: (h0, 0.0), 2: (h0, 1.0), 3: (h1, 1.0)}
        q = quads[0]
        uvs[0] = [c[i] for i in q]
        o.add(box, quads, "goggle_outrigger", uvs)
    return o


def outrigger_texture(path, w=256, h=512):
    """Image halves (left half: his left outrigger), each u across the outrigger's height (0 bottom .. 1 top within
    the half), v along it (0 at the frame, 1 at the strap). Letter tops towards the strap on both sides (Leatt ISO
    and the Pinata kit photo, right side): on the right it reads bottom to top, on the left top to bottom (the left
    face's (u, v) is mirrored seen from outside, so its half is drawn mirrored and reads right there)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (2 * w, h), (14, 14, 16))
    d = ImageDraw.Draw(im)
    polys, lw = H.logo_polys(0.0, 0.0, 1.0)
    L_ = 0.78 * w                                             # text length in px (along u)
    ch = 0.42 * h                                             # cap height in px (along v)
    sx = L_ / lw
    for half in (0, 1):
        for p in polys:
            pts = []
            for px, py in p:
                if half == 1:
                    u = w + (w - L_) / 2 + px * sx            # right: reads up (+u)
                else:
                    u = (w + L_) / 2 - px * sx                # left: reads down (-u)
                v = 0.47 * h + (py - 0.5) * ch               # letter tops towards +v (the strap)
                pts.append((u, h - v))                        # image rows run down, v runs up
            d.polygon(pts, fill=(236, 236, 238))
    im.save(path)


NOSE_GUARD_DROP = 0.011            # the flexible nose guard hangs this far under the frame's nose arch


def build_nose_guard(gp=None):
    """The black flexible nose guard under the nose arch (Leatt exploded view)."""
    gp = gp or GP
    L = LensSurface(gp)
    Cu, seg, frac = catmull_closed(full_loop(gp["out"]), 12)
    n = len(gp["out"])
    # the arch: from half-way between the left bottom corner and the nose foot (controls 6, 7), over the nose
    # (control 8, the bottom centre) to the mirror point on the right (full-loop segments 6 .. 9)
    idx = np.nonzero(((seg == n - 3) & (frac >= 0.5)) | (seg == n - 2) | (seg == n - 1) |
                     ((seg == n) & (frac <= 0.5)))[0]
    C = Cu[idx]
    rings = []
    for drop, off in ((0.0, -0.002), (NOSE_GUARD_DROP * 0.6, -0.006), (NOSE_GUARD_DROP, -0.012)):
        P = L.point(C[:, 0], C[:, 1] - drop, off)[0]
        rings.append(P)
    g = H.Part("goggle_noseguard")
    m = len(C)
    ids = [g.add(r, [], "goggle_noseguard") + np.arange(m) for r in rings]
    for a_, b_ in zip(ids[:-1], ids[1:]):
        for i in range(m - 1):
            g.F.append([a_[i], a_[i + 1], b_[i + 1], b_[i]]); g.M.append("goggle_noseguard"); g.UV.append([(0.0, 0.0)] * 4)
    return g


# ---------------------------------------------------------------- placement, face foam, assembly
# Where the goggle sits on Leatt's helmet (HELMET frame): its lens front centre at (0, ty, tz), pitched by PITCH
# (top back), fitted with the shape in the four kit photos. On Damien the helmet sits on his head (helmet.py
# fit_on_head) and the goggle keeps this place in it; the foam fills to his face.
PLACE = (-0.149, 0.0, 5.0)
FOAM_MIN, FOAM_MAX, FOAM_DEFAULT = 0.0015, 0.030, 0.014  # triple-layer foam, compressed against the face


def g2h(V, pl=None):
    ty, tz, pitch = pl or PLACE
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    return np.asarray(V) @ Rg.T + np.array([0.0, ty, tz])


def h2g(V, pl=None):
    ty, tz, pitch = pl or PLACE
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    return (np.asarray(V) - np.array([0.0, ty, tz])) @ Rg


def march_to_skin(P, D, tree, step=0.0005, reach=FOAM_MAX + 0.01, tol=0.0015):
    """Distance along D from each P to the first skin point within tol of the ray (nan if none within reach)."""
    out = np.full(len(P), np.nan)
    for t_ in np.arange(0.0, reach, step):
        todo = np.isnan(out)
        if not todo.any():
            break
        d, _ = tree.query(P[todo] + D[todo] * t_)
        hit = d < tol
        idx = np.nonzero(todo)[0][hit]
        out[idx] = t_
    return out


def build_foam(rings, info, skin_G):
    """Face foam from the frame's back face to his face along the lens's inward normal, conforming (compressed to
    0.5 mm off the skin), never thinner than FOAM_MIN; where no skin is in reach (the ends past the temples) it
    keeps FOAM_DEFAULT."""
    L = info["L"]
    Cu, Co = info["Cu"], info["Co"]
    f, g = rings[RING_BACK_OUT], rings[RING_BACK_IN]
    # over the nose the foam leaves the bridge and runs along the lens opening's edge (the nose sits under the
    # bridge, in the nose guard: Leatt exploded view): its outer edge closes onto its inner edge there
    s_foot = GP["out"][-2][0]
    t = np.clip(1 - np.abs(Cu[:, 0]) / s_foot, 0, 1) * (Cu[:, 1] < 0)
    w = (t * t * (3 - 2 * t))[:, None] ** 0.5
    f = f + (g + (f - g) * 0.25 - f) * w
    tree = cKDTree(skin_G)
    out = []
    for R_, C in ((f, Cu), (g, Co)):
        N = L.point(C[:, 0], C[:, 1], 0.0)[1]
        d = march_to_skin(R_, -N, tree)
        d = np.where(np.isnan(d), FOAM_DEFAULT, d - 0.0012)
        d = np.clip(d, FOAM_MIN, FOAM_MAX)
        for _ in range(4):                                          # round the loop: no steps between samples
            d = np.minimum(d, (np.roll(d, 1) + 2 * d + np.roll(d, -1)) / 4 + 0.0005)
        out.append(R_ - N * d[:, None])
    foam = H.Part("goggle_foam")
    ring_faces(foam, [f, out[0], out[1], g], ["goggle_foam", "goggle_foam", "goggle_foam", "goggle_foam"])
    return foam, out


def build_goggle(body, Rt, prof):
    """The goggle on his head (MB rest frame), riding the head bone: frame, double lens, bare tear-off posts,
    outriggers, nose guard, face foam and the strap; his eyes behind it."""
    R, t = Rt
    fr, info = build_frame()
    rings, _ = frame_rings()
    skin = body["V"][H.head_skin(body, ("head",))]
    skin_G = h2g((skin - t) @ R)
    foam, foam_back = build_foam(rings, info, skin_G)
    parts = [fr, build_lens(), build_posts(), build_outriggers(), build_nose_guard(), foam]
    ends = {sg: g2h(e[None])[0] @ R.T + t for sg, (box, e, n) in outrigger_frames().items()}
    for P in parts:
        P.V = g2h(P.V) @ R.T + t
    strap = H.build_strap(Rt, prof, ends)
    eyes, einfo = build_eyes(body)
    L = info["L"]
    ctr = g2h(L.point(0.0, 0.0, 0.0)[0][None])[0] @ R.T + t
    eye = H.head_landmarks(body)["eye"]
    info_out = dict(lens_centre_ahead_of_eye_mm=round(float(eye[1] - ctr[1]) * 1000, 1),
                    lens_centre_above_eye_mm=round(float(ctr[2] - eye[2]) * 1000, 1),
                    foam_mm=[round(float(np.linalg.norm(foam_back[0] - rings[RING_BACK_OUT], axis=1).min()) * 1000, 1),
                             round(float(np.linalg.norm(foam_back[0] - rings[RING_BACK_OUT], axis=1).max()) * 1000, 1)],
                    frame_width_mm=round(float(np.ptp(g2h(np.vstack(rings))[:, 0])) * 1000, 1),
                    frame_height_mm=round(float(np.ptp(np.vstack(rings)[:, 2])) * 1000, 1), **einfo)
    return parts + [strap] + eyes, info_out


# ---------------------------------------------------------------- the helmet's brow badge (repainted by script)
# helmet.py's projection put the purple badge on the atlas twice ("LEATT LEATT") with four brow vents: the
# model's brow under the visor stands about 16 mm ahead of the real one, so Leatt's two side views (iso-left,
# iso-right) project it 19 mm apart either way. The badge and its two vents are measured on the shell by casting
# the rays of Leatt's MY27 front-iso-left (white badge, 31505 _1) and Pinata iso-right (purple badge) photos through
# their fitted cameras; each view's outline is centred on its own badge (the depth error shifts the whole outline)
# and the two are averaged; HELMET frame (x, z), m. The brow is then repainted once, centred on x = 0.
BADGE_Z = (0.0765, 0.0930)          # bottom and top of the badge
BADGE_HW = (0.0280, 0.0185)         # half widths at the bottom and the top (a trapezoid, top corners rounded)
BADGE_CORNER = 0.003
BADGE_LOGO = dict(width=0.0346, height=0.0083, zc=0.0848)   # white LEATT: 62 % of the bottom width, 50 % high
BADGE_RGB = (79, 39, 180)           # Pinata iso-right photo, median of the badge
VENT_QUAD = [(-0.0633, 0.0717), (-0.0368, 0.0797), (-0.0313, 0.0912), (-0.0624, 0.0775)]   # his right; mirrored
BROW_BOX = (0.096, 0.064, 0.101)    # |x| and z range repainted (plain brow in Leatt's photos)


def leatt_logo(width, height, cx, cy, shear=0.25):
    """The LEATT logotype (logo_polys) scaled to a box (width x height) centred at (cx, cy), y up, reading +x."""
    polys, lw = H.logo_polys(0.0, 0.0, 1.0, shear)
    sx, sy = width / lw, height
    return [[(cx + (px - lw / 2) * sx, cy + (py - 0.5) * sy) for px, py in p] for p in polys]


def badge_outline(n=8):
    (z0, z1), (w0, w1), r = BADGE_Z, BADGE_HW, BADGE_CORNER
    pts = [(-w0, z0), (w0, z0)]
    k = (w1 - w0) / (z1 - z0)
    # right side up to the corner, rounded corner, top, left corner, left side
    for sgn in (1, -1):
        c = (sgn * (w1 - r), z1 - r)
        arc = np.linspace(0, math.pi / 2, n) if sgn > 0 else np.linspace(math.pi / 2, math.pi, n)
        seg = [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in arc]
        pts += seg
    return np.array(pts)


def paint_brow_badge(path):
    """Repaint the brow of helmet_pinata.png: plain brow white, the two vents (dark mesh, lighter rim), the purple
    badge with one white LEATT. Every texel is coloured from its own 3D point on the shell."""
    from matplotlib.path import Path
    from PIL import Image
    Vo, Fo, prof = H.shell_outer()
    UV, isl = H.atlas_uvs(Vo, Fo)
    N = H.normals(Vo, Fo)
    idx, P, Nn = H.rasterize(UV * H.TEX, Vo[Fo], N[Fo])
    img = np.array(Image.open(path).convert("RGB")).astype(float)
    row, col = H.TEX - 1 - np.clip(idx[:, 1], 0, H.TEX - 1), np.clip(idx[:, 0], 0, H.TEX - 1)
    front = (P[:, 1] < -0.09) & (Nn[:, 1] < 0)
    box = front & (np.abs(P[:, 0]) < BROW_BOX[0]) & (P[:, 2] > BROW_BOX[1]) & (P[:, 2] < BROW_BOX[2])
    ring = front & (np.abs(P[:, 0]) < BROW_BOX[0] + 0.012) & (P[:, 2] > BROW_BOX[1]) & (P[:, 2] < BROW_BOX[2]) & ~box
    base = np.median(img[row[ring], col[ring]], 0) if ring.sum() > 20 else np.array(H.BASE_WHITE, float)
    xz = P[:, [0, 2]]
    col_ = np.tile(base, (len(P), 1))
    for sgn in (1, -1):                                              # vents: mesh, lighter moulded rim
        q = np.array(VENT_QUAD) * [sgn, 1]
        inside = Path(q).contains_points(xz)
        qc = q.mean(0)
        rim = Path(qc + (q - qc) * 1.12).contains_points(xz) & ~inside
        u = (xz[:, 0] + xz[:, 1]) / 0.0016
        v = (xz[:, 0] - xz[:, 1]) / 0.0016
        mesh = (np.abs(u - np.round(u)) < 0.12) | (np.abs(v - np.round(v)) < 0.12)
        col_[inside] = np.where(mesh[inside, None], [92, 92, 98], [26, 26, 30])
        col_[rim] = base * 0.82
    b = Path(badge_outline()).contains_points(xz)
    col_[b] = BADGE_RGB
    lg = BADGE_LOGO
    for poly in leatt_logo(lg["width"], lg["height"], 0.0, lg["zc"]):
        col_[b & Path(np.array(poly)).contains_points(xz)] = (240, 240, 244)
    out = img.copy()
    out[row[box], col[box]] = col_[box]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)
    return dict(brow_texels=int(box.sum()), badge_texels=int((b & box).sum()), base=base.round(0).tolist())


MATERIALS = {
    "eye_ball": dict(image="goggle_eyes_brown.png", rough=0.35, coat=1.0),        # wet: a clear coat over it all
    "goggle_frame": dict(rgb=[150, 0, 45], rough=0.45),                     # raspberry: Pinata kit photo frame
                                                                            # median 209/0/61, his 09: 190/8/88
    "goggle_vent": dict(rgb=[16, 16, 18], rough=0.95),                      # foam-backed slots
    "goggle_foam": dict(rgb=[40, 40, 44], rough=0.95, sheen=0.6),
    "goggle_noseguard": dict(rgb=[30, 30, 32], rough=0.6),
    "goggle_post": dict(rgb=[20, 20, 22], rough=0.35),
    "goggle_outrigger": dict(image="goggle_outrigger.png", rough=0.25, coat=0.5),       # gloss black (kit photo)
    # purple mirror (Damien): metallic purple with an interference film, purple square on, gold-orange at grazing
    # angles (his 08, 09); the little light the mirror lets through is tinted dark purple (eyes hidden)
    "goggle_lens_mirror": dict(rgb=[90, 30, 125], metal=0.94, rough=0.03, transmission=1.0,
                               thin_film=dict(thickness_nm=430, ior=1.33)),      # swatches: deep purple square on
    "goggle_lens_clear": dict(rgb=[120, 90, 150], rough=0.02, transmission=1.0),
}
for _k in ("goggle_strap", "goggle_strap_in"):
    MATERIALS[_k] = H.MATERIALS[_k]
