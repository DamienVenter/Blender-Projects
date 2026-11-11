"""Front end in detail (plugin of parts.py): Showa 49 mm fork, triple clamps, Renthal Fatbar, hand controls, front
brake, disc cover, and the cables and hoses that leave the handlebar.

Frame: metres, x forward, y left, z up, axle-line frame of parts.py. Most of it is written in the FORK frame
fk(f, y, t): f ahead of the plane of the two tube axes, y left, t up the tubes from the axle's height (parts.on_tube).
The hand controls are written in a GRIP frame per side (_Side.p): a inboard of the bar end along the grip, f ahead of
it, u up.

Sources, tagged on every number: SPEC (research/crf250r-2026.md), LEFT / RIGHT / FRONT / TOP (Honda's studio photos
through cams.CAMS; rows, columns or the scan that gave it), DET (Honda's detail photos 475829, 475830, 475831, 475835:
what the part looks like, no dimensions), EST (real part's usual size, not visible in any photo).
Scans (scratch, reproducible with rowscan.py): class runs across the left tube at t 0.33..0.96 ("across"), along its
axis ("axis"), front photo rows 600..1020 on the tubes' plane ("front"), bar black per column of the front photo and
per row of the top photo ("bars_front", "bars_top"), the hose's black over the plate rows 230..610 ("hose").
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.spatial import ConvexHull

import cams
import parts as P
from geom import Mesh, bolt, box, circle, grid, plate2d, rounded_rect, tube
from parts import AXLE_LEAD, BACK, CLAMP_OFFSET, FA, FORK_HALF, TUBE0, UP

Y = np.array([0.0, 1.0, 0.0])
Z = np.array([0.0, 0.0, 1.0])
FWD = -BACK
RF = np.column_stack([FWD, Y, UP])                    # fork frame as a rotation (box sizes: f, y, t)
F_STEER = -CLAMP_OFFSET                               # the steering axis in the fork frame (f)

# ---------------------------------------------------------------- measured levels (t along the tubes)
T_SEAL = 0.354                                        # LEFT axis: dust seal black 0.348..0.354, gold above
T_LO = (0.662, 0.716)                                 # FRONT rows 630, 660 silver, 600 and 690 gold; LEFT axis 0.652..
T_UP = (0.884, 0.928)                                 # LEFT + RIGHT axis: silver 0.884..0.928
T_TUBE_TOP = 0.933                                    # LEFT axis: tube stands 5 mm proud of the top clamp (DET 475835)
R_BOSS_LO = 0.0325                                    # FRONT rows 630, 660: lower clamp out to |y| 0.130..0.132
R_BOSS_UP = 0.0305                                    # EST (5 mm wall): yields to the number plate, whose wing comes
#   within 31.1 mm of the tube axis ahead and outboard of the top clamp (plastics, measured)
FACE_LO = T_LO[1] - 0.001                             # lower clamp's upper face, along the steering axis
FACE_UP = T_UP[1] - 0.015                             # top clamp's underside: bridge 15 mm thick between the bosses, EST
STEM_R = 0.0145                                       # EST: the stem is the only part inside the frame's head tube
FENDER_T = 0.003                                      # build_bike.py solidifies the fender 3 mm inwards
R_INNER = 0.0245                                      # SPEC: 49 mm inner tubes
T_BAR = 0.968                                         # bar centre, EST: the holders' caps and bolts reach 27 mm above
#   it and must stay under the bar pad's measured top (PAD_T)
F_BAR = F_STEER + 0.003                               # TOP rows 1045, 1180: pad centred on x 0.988
YC = 0.152                                            # TOP rows 1270..1360: the bar is straight across out to here
R_GRIP = 0.0158                                       # where the end lip's rounded rim reaches furthest out
# The bar ends sit on cams.BAR_END: both side photos, the rear photo and the top photo agree on it.
_TXZ = (cams.BAR_END[0], cams.BAR_END[2])
_C0X = float((TUBE0 + F_BAR * FWD + T_BAR * UP)[0])
UPSWEEP = math.radians(1.85)                          # the grips rise outwards: FRONT top edge falls 4.5 mm from a 8 to
#   104, REAR top 4.6 and bottom 1.7 (axis 3.1 mm over 96 mm with the grip's 2.8 mm taper taken out; component 1)
SWEEP = 0.25                                          # plan angle of the grips: from the corner at YC to the bar end
for _ in range(4):                                    # (TOP rows 685..1585 give 0.288 = 16 deg to the photo's bar end)
    SWEEP = math.atan((_C0X - _TXZ[0]) / (cams.BAR_END[1] - R_GRIP * math.sin(SWEEP) - YC))
TIP = np.array([_TXZ[0], cams.BAR_END[1] - R_GRIP * math.sin(SWEEP), _TXZ[1]])    # grip end centre: the end face is
#   swept back, so its outer rim, not its centre, makes the 827 mm overall width (SPEC)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _outward(m):
    """Wind a closed piece so that its normals point outwards (signed volume): the audit's depth test and the
    bar pad's lettering both read the normals."""
    v = np.asarray(m.V, float)
    v = v - v.mean(axis=0)
    vol = 0.0
    for f in m.F:
        q = v[list(f)]
        for i in range(1, len(f) - 1):
            vol += float(q[0] @ np.cross(q[i], q[i + 1]))
    if vol < 0:
        m.F = [tuple(reversed(f)) for f in m.F]
    return m


def fk(f, y, t):
    """Fork frame to bike frame."""
    return TUBE0 + f * FWD + y * Y + t * UP


# Bar pad, in the fork frame: it leans with the steering axis and its section is the same along its length.
PAD_F = (-0.0545, 0.0315)     # rear face: LEFT rows 505..560 and RIGHT rows 510..560 on the end plane y +-0.106, the
#   cap's rear edge stays 53..57 mm behind the tubes' plane from t 0.947 to 0.995 (so the lean is the fork's, RAKE);
#   front face: the mirror of it about the top face's centre, and TOP u 1662..1684 (second line of lettering)
PAD_T = (0.945, 1.001)        # underside: LEFT / RIGHT axis scans (cap black from t 0.946), corners at 0.947, REAR col
#   2000 (red down to row 345, 0.941); top: FRONT cols 1960..2040 (rows 250..258, z 1.208..1.203) with TOP u 1708
PAD_SHOULDER = (0.0185, 0.013)                        # rounded shoulders, deep and high: TOP emblem band u 1708..1762,
#   lettering bands u 1684..1708 and 1762..1775, rear edge u 1775 (x 0.951); REAR col 2000 lettering rows 276..294
PAD_Y = (0.0875, 0.106)       # red body, and with the grey end caps: TOP cols 1712..1744 (red v 1025..1225, dark to
#   1001 and 1244), REAR rows 290..310 (red u 1890..2109, dark caps outside)
PAD_HALF = ((PAD_F[1] - PAD_F[0]) / 2, (PAD_T[1] - PAD_T[0]) / 2)        # 86 mm fore-aft, 56 mm tall
PAD_C = fk((PAD_F[0] + PAD_F[1]) / 2, 0, (PAD_T[0] + PAD_T[1]) / 2)      # its centre (axle-line frame)
PAD_TILT = P.RAKE                                     # lean back, radians


def pad_section():
    """The pad's section (f, t), counter-clockwise from the front lower corner."""
    (f0, f1), (t0, t1), (a, b) = PAD_F, PAD_T, PAD_SHOULDER
    ph = np.linspace(0, math.pi / 2, 7)
    front = [(f1 - a + a * math.cos(q), t1 - b + b * math.sin(q)) for q in ph]
    rear = [(f0 + a - a * math.cos(q), t1 - b + b * math.sin(q)) for q in ph[::-1]]
    return np.array([(f1 - 0.003, t0), (f1, t0 + 0.003)] + front + rear + [(f0, t0 + 0.003), (f0 + 0.003, t0)])




def fyz(f, y, z):
    """Point f ahead of the tubes' plane at lateral y and height z (front-photo readings)."""
    return fk(f, y, (z - TUBE0[2] - f * FWD[2]) / UP[2])


def rev(o, axis, prof, mat, seg=24, cap0=False, cap1=False, ref=None, arc=None, solid=False):
    """Profile [(radius, height)] turned about AXIS through O: a full turn, or the ARC (a0, a1) measured from REF
    towards axis x REF. solid: the profile is a closed loop (outer wall then inner wall, same number of points)."""
    a = unit(axis)
    if ref is None:
        ref = Z if abs(a[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = unit(ref - (ref @ a) * a)
    v = np.cross(a, u)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False) if arc is None else np.linspace(arc[0], arc[1], seg)
    ring = np.outer(np.cos(ang), u) + np.outer(np.sin(ang), v)
    rings = [np.asarray(o, float) + a * h + r * ring for r, h in prof]
    if solid:
        rings.append(rings[0])
    m = grid(Mesh(), rings, mat, closed_u=arc is None, cap0=cap0, cap1=cap1)
    if solid and arc is not None:                     # close the two ends of the arc
        k = len(prof)
        for col, flip in ((0, False), (seg - 1, True)):
            for i in range(k // 2 - 1):
                q = (i * seg + col, (i + 1) * seg + col, (k - 2 - i) * seg + col, (k - 1 - i) * seg + col)
                m.face(q[::-1] if flip else q, mat)
    return _outward(m) if (arc is None or solid) else m


def cyl(p0, p1, r, mat, seg=20, ch=0.0):
    """Capped cylinder from p0 to p1, edges chamfered by ch."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ln = np.linalg.norm(p1 - p0)
    prof = [(r - ch, 0.0), (r, ch), (r, ln - ch), (r - ch, ln)] if ch > 0 else [(r, 0.0), (r, ln)]
    return rev(p0, p1 - p0, prof, mat, seg, cap0=True, cap1=True)


def ball(c, r, mat, seg=14):
    lat = np.linspace(0.3, math.pi - 0.3, 7)
    return rev(c, Z, [(r * math.sin(a), -r * math.cos(a)) for a in lat], mat, seg, cap0=True, cap1=True)


def slab(outline, h0, h1, mat, to3d, ch=0.0015):
    """Outline (n, 2) extruded from h0 to h1 through to3d(p, q, h), edges chamfered (outline star-shaped)."""
    o = np.asarray(outline, float)
    c = o.mean(axis=0)
    ins = c + (o - c) * (1.0 - ch / np.linalg.norm(o - c, axis=1).mean())
    lev = [(ins, h0), (o, h0 + ch), (o, h1 - ch), (ins, h1)] if ch > 0 else [(o, h0), (o, h1)]
    rings = [np.array([to3d(p[0], p[1], h) for p in loop]) for loop, h in lev]
    return _outward(grid(Mesh(), rings, mat, cap0=True, cap1=True))


def pillow(outline, h0, h1, r, mat, to3d, n=4):
    """Outline (star-shaped about its centroid) extruded from h0 to h1 with both ends rounded over radius R (a
    moulded rubber boot or a soft casting): rings inset along a quarter circle at each end."""
    o = np.asarray(outline, float)
    c = o.mean(axis=0)
    rad = np.linalg.norm(o - c, axis=1).mean()
    lev = []
    for k in range(n + 1):                                   # bottom end: from the inset centre outwards
        t = (math.pi / 2) * k / n
        lev.append((r * (1 - math.sin(t)), h0 + r * (1 - math.cos(t))))
    for k in range(n, -1, -1):
        t = (math.pi / 2) * k / n
        lev.append((r * (1 - math.sin(t)), h1 - r * (1 - math.cos(t))))
    rings = [np.array([to3d(*(c + (p - c) * (1.0 - d / rad)), h) for p in o]) for d, h in lev]
    return _outward(grid(Mesh(), rings, mat, cap0=True, cap1=True))


def spline(pts, n):
    q = np.asarray(pts, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))])
    return CubicSpline(s, q)(np.linspace(0, s[-1], n))


def sweep(pts, r, mat, seg=10, n=None):
    q = np.asarray(pts, float)
    if n is None:
        n = max(8, int(np.linalg.norm(np.diff(q, axis=0), axis=1).sum() / 0.007))
    return tube(spline(q, n), r, seg, mat)


def loop_from_half(half):
    """Closed outline from its y >= 0 half ((f, y), front centre round to rear centre), corners cut twice."""
    h = np.asarray(half, float)
    full = np.vstack([h, h[-2:0:-1] * [1, -1]])
    for _ in range(2):
        nxt = np.roll(full, -1, axis=0)
        full = np.stack([0.75 * full + 0.25 * nxt, 0.25 * full + 0.75 * nxt], axis=1).reshape(-1, 2)
    return full


# ================================================================ fasteners
def _frame(axis):
    a = unit(axis)
    h = Z if abs(a[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = unit(np.cross(h, a))
    return a, u, np.cross(a, u)


def fastener(c, axis, kind="flange", af=0.010, h=None, flange_d=None, washer=None, mat="bolt", thread=0.0,
             thread_d=None, recess=None):
    """A real fastener head at C standing along AXIS (out of the surface it sits on).
    kind "flange": hex flange bolt or nut (JIS: 8 mm across flats on M5, 10 on M6, 12 on M8, 14 on M10), flange with
    its edge rounded, hex with 30 deg chamfered corners on top; "hex": plain hex with the same chamfer; "socket":
    cylindrical socket cap with a hex recess (RECESS across flats, 0.6 x the head height deep); "button": low domed
    socket head. washer: (outer d, thickness) under the head. thread: length of exposed thread beyond the head along
    AXIS (a stud through a nut), thread_d its diameter (60 deg V, 1.25 mm pitch on M8)."""
    a, u, v = _frame(axis)
    c = np.asarray(c, float)
    m = Mesh()
    z0 = 0.0
    if washer:
        wd, wt = washer
        ri = (thread_d or af * 0.7) / 2 + 0.0003
        m.add(rev(c, a, [(ri, 0.0), (wd / 2 - 0.0003, 0.0), (wd / 2, 0.0003), (wd / 2, wt - 0.0002),
                         (wd / 2 - 0.0002, wt), (ri, wt)], "steel", 24, solid=True))
        z0 = wt
    ang = np.linspace(0, 2 * math.pi, 24, endpoint=False)
    circ = np.stack([np.cos(ang), np.sin(ang)], axis=1)
    hexa = circ / np.maximum.reduce([np.abs(np.cos(ang - k * math.pi / 3)) for k in range(3)])[:, None]   # unit-apothem hex

    def ring(shape, r, z):
        return np.array([c + a * (z0 + z) + r * (q[0] * u + q[1] * v) for q in shape])
    if kind in ("flange", "hex"):
        h = h if h is not None else af * 0.62
        rings = []
        if kind == "flange":
            rf = (flange_d if flange_d else af * 1.4) / 2
            tf = min(0.0018, h * 0.28)
            rings += [ring(circ, rf - 0.0003, 0.0), ring(circ, rf, 0.0003), ring(circ, rf, tf * 0.6),
                      ring(circ, rf - 0.0004, tf), ring(circ, af / 2 * 1.05, tf)]
            zh = tf
        else:
            zh = 0.0
            rings += [ring(circ, af / 2 * 0.98, 0.0)]
        ch = af * 0.06                                                    # 30 deg corner chamfer, top and bottom
        rings += [ring(hexa, af / 2, zh + 0.0002),
                  ring(hexa, af / 2, h - ch), ring(np.where(np.linalg.norm(hexa, axis=1)[:, None] > 1.04,
                                                            hexa / np.linalg.norm(hexa, axis=1)[:, None] * 1.04,
                                                            hexa), af / 2, h - ch * 0.35),
                  ring(circ, af / 2 * 0.94, h)]
        m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    else:                                                                 # socket / button
        d = af                                                            # head diameter
        h = h if h is not None else (d * 0.62 if kind == "socket" else d * 0.3)
        rs = (recess if recess else d * 0.45) / 2
        top = [ring(circ, d / 2, 0.0), ring(circ, d / 2, h * 0.88), ring(circ, d / 2 * 0.93, h)] if kind == "socket" \
            else [ring(circ, d / 2, 0.0), ring(circ, d / 2, h * 0.25), ring(circ, d / 2 * 0.82, h * 0.8),
                  ring(circ, d / 2 * 0.62, h)]
        rings = top + [ring(hexa, rs * 1.08, h), ring(hexa, rs, h - 0.0003), ring(hexa, rs, h - h * 0.6)]
        m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    if thread > 0:
        td = thread_d or af * 0.66
        pitch = 0.00125 if td > 0.007 else 0.001
        prof = [(td / 2 - 0.0006, h + z0 - 0.001)]
        z = h + z0
        while z < h + z0 + thread - pitch:
            prof += [(td / 2, z + pitch * 0.25), (td / 2 - 0.0006, z + pitch * 0.75)]
            z += pitch
        prof += [(td / 2 - 0.0008, h + z0 + thread)]
        m.add(rev(c, a, prof, "steel", 16, cap1=True))
    return m


# ================================================================ fork
def fork():
    """Showa 49 mm coil-spring fork: gold outer tubes, chrome inner tubes, dust seals, caps with adjuster and bleed
    screw, cast axle lugs with pinch bolts (and the caliper ears on the left), axle with its nut."""
    m = Mesh()
    lug = "fork_lug"
    for side in (-1, 1):
        y = side * FORK_HALF
        o = fk(0, y, 0)
        # outer tube. LEFT across: 51 mm at t 0.50..0.76, 58 mm seal housing with two grooves at 0.36..0.385 (EST length:
        # it ends under the fork guard's neck, which is 27.5 mm inside from t 0.40);
        # FRONT rows 690..990: 46..48 mm (y 74..120); the brief's 48..53. 53 mm inside the lower clamp is EST.
        prof = [(0.0262, T_SEAL), (0.0290, 0.357), (0.0290, 0.3625), (0.0279, 0.364), (0.0279, 0.367),
                (0.0290, 0.3685), (0.0290, 0.3745), (0.0279, 0.376), (0.0279, 0.379), (0.0290, 0.3805),
                (0.0290, 0.385), (0.0252, 0.393), (0.0250, 0.397), (0.0250, 0.600), (0.0265, 0.650), (0.0265, 0.725),
                (0.0255, 0.760), (0.0255, T_TUBE_TOP - 0.0015), (0.0243, T_TUBE_TOP)]
        m.add(rev(o, UP, prof, "fork_gold", 40, cap1=True))
        # dust seal (LEFT axis: black 0.348..0.354) and inner tube (LEFT axis: bright metal 0.292..0.346)
        m.add(rev(o, UP, [(R_INNER + 0.0003, 0.3425), (0.0262, 0.345), (0.0270, 0.351), (0.0262, T_SEAL + 0.001)],
                  "rubber_black", 32))
        m.add(rev(o, UP, [(R_INNER, 0.066), (R_INNER, 0.400)], "chrome", 32))
        # fork cap (DET 475835: black cap in the tube's mouth), compression adjuster and bleed screw (EST sizes)
        m.add(rev(o, UP, [(0.0222, T_TUBE_TOP - 0.001), (0.0222, 0.9365), (0.0205, 0.938)], "anod_black", 28,
                  cap1=True))
        m.add(bolt(fk(0, y, 0.938), UP, af=0.014, head_h=0.004, flange_d=0.019, mat="alu_machined"))
        m.add(cyl(fk(0, y, 0.942), fk(0, y, 0.9432), 0.0038, "steel", 12))
        m.add(box(fk(0, y, 0.9434), (0.0066, 0.0011, 0.0006), "rubber_black", RF))            # screwdriver slot
        m.add(bolt(fk(0.013, y, 0.938), UP, af=0.0052, head_h=0.0022, mat="steel", kind="cap"))    # air bleed
        # (the socket's top is a collar for the fork guard's foot: the guard starts at t 0.053, LEFT axis red from
        # 0.056; its inboard wall is 28.0 mm from the tube axis inside, audit; the collar is 27.7)
        # axle lug: socket round the foot of the inner tube, web to the axle boss 39.6 mm ahead (parts.AXLE_LEAD),
        # chin under the axle with a slit and two pinch bolts from the front (EST layout; DET 475831 for the look)
        m.add(rev(o, UP, [(0.020, -0.022), (0.0285, -0.017), (0.031, -0.008), (0.031, 0.036), (0.0277, 0.040),
                          (0.0277, 0.064), (0.0262, 0.070), (R_INNER + 0.0002, 0.072)], lug, 32, cap0=True))
        pts = np.vstack([circle(0.025, 24, AXLE_LEAD, 0.0), [(-0.020, -0.020), (-0.026, 0.036), (0.026, 0.040), (AXLE_LEAD + 0.004, -0.0386),
                         (AXLE_LEAD - 0.012, -0.038), (AXLE_LEAD + 0.020, -0.038), (AXLE_LEAD + 0.020, -0.022)]])
        hull = pts[ConvexHull(pts).vertices]
        m.add(slab(hull, 0.078, 0.122, lug, lambda f, t, h, s=side: fk(f, s * h, t), ch=0.002))
        m.add(cyl(FA + side * 0.074 * Y, FA + side * 0.126 * Y, 0.024, lug, 28, 0.002))
        m.add(box(fk(AXLE_LEAD + 0.004, side * 0.100, -0.0295), (0.0016, 0.0446, 0.018), "rubber_black", RF))
        for dy in (-0.012, 0.012):
            m.add(bolt(fk(AXLE_LEAD + 0.020, side * 0.100 + dy, -0.030), FWD, af=0.010, flange_d=0.013))
    # caliper ears on the left lug (DET 475831: two bolts behind the leg), webs into the socket
    for f, t in CAL_EARS:
        m.add(cyl(fk(f, 0.083, t), fk(f, 0.105, t), 0.009, lug, 20, 0.0015))
        m.add(box(fk(f + 0.006, 0.094, t), (0.012, 0.022, 0.016), lug, RF))
    # axle (EST 20 mm), head on the right, nut on the left (DET 475831: hex in the centre of the disc cover)
    m.add(cyl(FA - 0.126 * Y, FA + 0.126 * Y, 0.010, "steel", 20))
    m.add(bolt(FA - 0.126 * Y, -Y, af=0.027, head_h=0.006, mat="steel", kind="cap"))
    m.add(bolt(FA + 0.126 * Y, Y, af=0.022, head_h=0.010, flange_d=0.032, mat="steel"))
    return m


CAL_EARS = ((-0.036, 0.036), (-0.040, -0.006))         # (f, t) of the caliper bracket bolts on the left lug, EST


# ================================================================ triple clamps
_FENDER = []


def _fender_skin(x, y, default=0.962):
    """Height of the front fender's outer surface at (x, y): the mesh of the fender in use (the plastics plugin's
    if it replaces it), linear between its vertices, so the bosses follow the fender."""
    try:
        if not _FENDER:
            from scipy.interpolate import LinearNDInterpolator
            fn = P.plastics.front_fender
            try:
                import detail_plastics
                fn = detail_plastics.PARTS.get("front_fender", fn)
            except Exception:
                pass
            v = np.asarray(fn().V, float)
            v = v[(v[:, 0] < 1.30) & (np.abs(v[:, 1]) < 0.065)]
            _FENDER.append(LinearNDInterpolator(v[:, :2], v[:, 2]))
        z = float(_FENDER[0](x, y))
        return z if np.isfinite(z) else default
    except Exception:
        return default


def _pinch(m, t0, t1, mat):
    """Rear pinch lug of a clamp boss with its slit and two bolts, both sides. LEFT (1516, 880): a flange bolt
    faces out at t 0.668, 31 mm behind the tube axis (lower clamp); the top clamp's are EST (the two bolt heads
    seen ahead of the top clamp at t 0.893 and 0.910 leave no room behind the number plate for a lug)."""
    tc, h = (t0 + t1) / 2, t1 - t0 - 0.004
    for side in (-1, 1):
        m.add(box(fk(-0.0375, side * FORK_HALF, tc), (0.019, 0.030, h), mat, RF))
        m.add(box(fk(-0.0375, side * FORK_HALF, tc), (0.0196, 0.0016, h + 0.0006), "rubber_black", RF))
        for t in (t0 + 0.012, t1 - 0.012):
            m.add(bolt(fk(-0.0375, side * (FORK_HALF + 0.015), t), side * Y, af=0.010, flange_d=0.014))


def _boss(side, tt, r, r_in, mat):
    """Clamp boss as a ring round the tube: the tube runs through its bore untouched."""
    ch = 0.002
    prof = [(r_in, tt[0]), (r - ch, tt[0]), (r, tt[0] + ch), (r, tt[1] - ch), (r - ch, tt[1]), (r_in, tt[1])]
    return rev(fk(0, side * FORK_HALF, 0), UP, prof, mat, 48, solid=True)


def _bridge(front, rear, r_mid):
    """Outline (f, y) of a clamp's bridge from its y >= 0 half: front edge, a notch that follows the middle of the
    boss's wall round the tube, rear edge."""
    notch = [(r_mid * math.cos(a), FORK_HALF + r_mid * math.sin(a))
             for a in np.radians([-50, -70, -90, -110, -130, -150])]
    return loop_from_half(front + notch + rear)


def clamps():
    """Lower clamp (cast, with the fender bosses and the fender nose), top clamp (machined, stem nut), steering
    stem."""
    m = Mesh()
    cast, mach = "alu_cast", "alu_machined"
    # (rear edge EST: it yields to the frame's down tube, 22 mm behind the steering axis at s 0.70)
    # ---- lower clamp: bosses FRONT rows 630..660 (|y| 0.073..0.131), LEFT across t 0.66..0.69 (36 mm ahead of the
    # axis, 55 mm behind it at the stem)
    for side in (-1, 1):
        m.add(_boss(side, T_LO, R_BOSS_LO, 0.0269, cast))
    low = _bridge([(0.024, 0.0), (0.025, 0.040), (0.024, 0.064)],
                  [(-0.036, 0.062), (-0.041, 0.040), (-0.0425, 0.015), (-0.0425, 0.0)], (0.0269 + R_BOSS_LO) / 2)
    m.add(slab(low, T_LO[0] + 0.006, FACE_LO, cast, fk, ch=0.002))
    _pinch(m, T_LO[0], T_LO[1], cast)
    m.add(cyl(fk(F_STEER, 0, T_LO[0] - 0.006), fk(F_STEER, 0, T_LO[0] + 0.008), 0.018, cast, 28, 0.002))  # stem foot
    for f, yb in ((0.010, 0.036), (-0.034, 0.034)):                # fender bosses under the clamp (EST positions)
        for side in (-1, 1):
            m.add(cyl(fk(f, side * yb, T_LO[0] - 0.002), fk(f, side * yb, T_LO[0] + 0.008), 0.0085, cast, 16, 0.001))
    # fender nose: two arms run forward under the number plate's lower edge (t 0.684) to bosses that stop 0.3 mm under the
    # fender's inner skin at x 1.236 (the fender of plastics.py starts at x 1.218 with its top at z 0.968)
    sec = rounded_rect(2.0, 1.2, 0.35, 3)
    for side in (-1, 1):
        yb, xb = side * 0.024, 1.236
        ring = [(0.0, 0.0)] + [(0.0075 * math.cos(a), 0.0075 * math.sin(a))
                               for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
        zb = min(_fender_skin(xb + dx, yb + dy) for dx, dy in ring) - FENDER_T - 0.0003     # 0.3 mm short of the skin
        skin = min(_fender_skin(x, yb + dy) for x in (1.221, 1.229, 1.240) for dy in (-0.007, 0.007))
        e = np.array([xb, yb, skin - 0.0105])                        # the arm stays 3 mm under the inner skin
        a = fk(0.078, yb, 0.670)
        m.add(tube([fk(0.016, yb, 0.670), fk(0.050, yb, 0.670), a, e + 0.007 * unit(e - a)], 0.0075, len(sec), cast,
                   section=sec))
        m.add(cyl(e - 0.003 * Z, [xb, yb, zb], 0.0075, cast, 16, 0.001))
    # ---- top clamp: LEFT / RIGHT axis silver t 0.884..0.928
    for side in (-1, 1):
        m.add(_boss(side, T_UP, R_BOSS_UP, 0.0259, mach))
    top = _bridge([(0.017, 0.0), (0.017, 0.045), (0.016, 0.066)],
                  [(-0.036, 0.066), (-0.054, 0.048), (-0.062, 0.020), (-0.063, 0.0)], (0.0259 + R_BOSS_UP) / 2)
    m.add(slab(top, FACE_UP, T_UP[1] - 0.0005, mach, fk, ch=0.002))
    _pinch(m, T_UP[0], T_UP[1], mach)
    # ---- stem: the only part between the two faces within the head tube's radius; nut and washer (EST 30 mm)
    m.add(cyl(fk(F_STEER, 0, T_LO[0] - 0.0055), fk(F_STEER, 0, T_UP[1] + 0.011), STEM_R, "steel", 24, 0.001))
    m.add(bolt(fk(F_STEER, 0, T_UP[1]), UP, af=0.030, head_h=0.008, flange_d=0.040, mat="steel"))
    for side in (-1, 1):                     # under the bridge: rubber bush (5), washer (15), nut (13) on the stud
        ax = fk(F_BAR, side * HOLDER_Y, 0.0)
        m.add(rev(ax, -UP, [(0.0065, -FACE_UP - 0.0005), (0.0140, -FACE_UP - 0.0005), (0.0143, -FACE_UP + 0.0012),
                            (0.0138, -FACE_UP + 0.0025), (0.0065, -FACE_UP + 0.0025)], "rubber_black", 32, solid=True))
        m.add(fastener(fk(F_BAR, side * HOLDER_Y, FACE_UP - 0.0025), -UP, "flange", af=0.012, h=0.008,
                       flange_d=0.017, washer=(0.024, 0.0016), mat="steel", thread=0.004, thread_d=0.008))
    return m


# ================================================================ handlebar and hand controls
CTRL_SHIFT = (0.017, 0.019)   # left and right controls moved inboard to clear the grips' flanges (TOP: switch housing
#   from a 122, throttle housing from a 122 on the right); each control is measured again in its own component


HOLDER_Y = 0.050              # lower holders' axes: DET835 (from behind and above) puts each base midway between the fork
#   tube's axis and the stem (pixel ratio 0.49 of 0.099); the pad hides the rest in every photo
HOLDER_BASE = (0.0148, 0.0185)    # base radius and height above the bush, DET835: about 0.58 of the fork cap's 50 mm
#   width (140 px against 240), its height about half its width; a turned ring 7 mm above its foot (bright line)
HOLDER_BOLT_F = 0.0205        # the cap's two bolts ahead of and behind the bar (fiche: two bolts 10 per cap), EST
#   spacing (M8 holders on a 28.6 mm bar need about 41 mm between bolt centres)


def _holder(yh):
    """One bar holder: rubber bush and washer on the top bridge, the lower holder (a machined round base turning into
    a saddle under the bar), the upper holder cap over the bar with its two M8 flange bolts (12 mm heads, JIS)."""
    m = Mesh()
    t0 = T_UP[1]
    ax = fk(F_BAR, yh, 0.0)
    m.add(rev(ax, UP, [(0.0065, t0 - 0.0005), (0.0140, t0 - 0.0005), (0.0143, t0 + 0.0012), (0.0138, t0 + 0.0025),
                       (0.0065, t0 + 0.0025)], "rubber_black", 32, solid=True))                       # bush (5)
    m.add(rev(ax, UP, [(0.0062, t0 + 0.0025), (0.0150, t0 + 0.0025), (0.0150, t0 + 0.0040), (0.0062, t0 + 0.0040)],
              "steel", 32, solid=True))                                                                # washer (14)
    rb, hb = HOLDER_BASE
    tb = t0 + 0.0040
    prof = [(rb - 0.0008, tb), (rb, tb + 0.0008), (rb, tb + 0.0065), (rb - 0.0005, tb + 0.0070),
            (rb - 0.0005, tb + 0.0078), (rb, tb + 0.0083), (rb, tb + hb - 0.002), (rb - 0.0004, tb + hb)]
    m.add(rev(ax, UP, prof, "alu_machined", 40, cap0=True, cap1=True))                                # base (4)
    # saddle: from the round base to a block 26 mm along the bar and 44 mm fore-aft, flat at the bar's centre
    sad = rounded_rect(0.044, 0.026, 0.008, 4)
    circ = circle(rb - 0.0004, len(sad))
    levels = [(tb + hb - 0.0004, 0.0), (tb + hb + 0.003, 0.65), (T_BAR - 0.006, 1.0), (T_BAR - 0.0003, 1.0)]
    rings = [np.array([fk(F_BAR + (1 - k) * q0[0] + k * q1[0], yh + (1 - k) * q0[1] + k * q1[1], t)
                       for q0, q1 in zip(circ, sad)]) for t, k in levels]
    m.add(_outward(grid(Mesh(), rings, "alu_cast", cap0=True, cap1=True)))
    # upper holder cap (3): same plan, 18 mm over the bar, rounded top edges, bolt bosses
    levels = [(T_BAR + 0.0003, 1.0, 1.0), (T_BAR + 0.0150, 1.0, 1.0), (T_BAR + 0.0180, 0.93, 0.85),
              (T_BAR + 0.0190, 0.80, 0.62)]
    rings = [np.array([fk(F_BAR + q[0] * kf, yh + q[1] * ky, t) for q in sad]) for t, kf, ky in levels]
    m.add(_outward(grid(Mesh(), rings, "alu_cast", cap0=True, cap1=True)))
    for dfb in (-HOLDER_BOLT_F, HOLDER_BOLT_F):
        p = fk(F_BAR + dfb, yh, T_BAR + 0.0150)
        m.add(fastener(p, UP, "flange", af=0.012, h=0.0062, flange_d=0.0165))
    return m


class _Side:
    """Grip frame of one side: p(a, f, u) is a metres inboard of the bar end along the grip, f ahead, u up.
    shift: added to every a (the hand controls moved inboard when the grips grew to their measured length; each
    control is placed again from the photos in its own component)."""

    def __init__(self, side, shift=0.0):
        self.side = side
        self.shift = shift
        self.T = TIP * [1, side, 1]
        dh = np.array([-math.sin(SWEEP), side * math.cos(SWEEP), 0.0])
        self.d = math.cos(UPSWEEP) * dh + math.sin(UPSWEEP) * Z                # along the grip, outwards (and up)
        self.f = np.array([math.cos(SWEEP), side * math.sin(SWEEP), 0.0])       # ahead of the grip
        self.u = -math.sin(UPSWEEP) * dh + math.cos(UPSWEEP) * Z               # up, square to the grip

    def p(self, a, f=0.0, u=0.0):
        return self.T - (a + self.shift) * self.d + f * self.f + u * self.u


# ================================================================ grips (Honda stock, 53165 / 53140 group)
# Anatomy and sources: research/detail-ledger/front.md, component 1. a is measured inboard from the end face (mm in
# the comments, metres in the code). TOPv = top studio photo, silhouette cast on the plane z = BAR_END z (gripscan.py,
# 0.78 mm a pixel); FRONTv / REARv = edge scans of the end photos on the grip's own plane; DET829 / DET830 / DR05 /
# DR06 = detail photos (counts, proportions, which features are grooves and which ribs).
G_TIP = (0.0150, 0.0141)      # outside diameter over the diamond tips 30.0 mm at a 8 and 28.2 mm at a 110: FRONTv top
#   edge falls 4.5 mm and REARv's bottom 1.7 mm over that run (so 2.8 mm of taper, the rest is the bar's upsweep),
#   TOPv widths 28.6 -> 27.0 (left) and 29.6 -> 28.6 (right) under a threshold that reads about 0.4 mm narrow
G_DEPTH = 0.00055             # pyramid height, EST: DR06 shows sharp pyramids about a third as tall as they are wide
G_PITCH = 0.00125             # half the pyramid diagonal along the axis: DET829 2D FFT of zone 2, both diagonal
#   families repeat every 20.4 px along the axis where zone 2 (46 mm) spans 380 px -> 2.47 mm a diagonal
G_ROUND = 36                  # pyramids round the grip: 2.47 mm round a 29 mm grip -> 36.9; 36 keeps the square
#   diamonds of DR06 (2.6 mm round, 2.5 along)
G_RINGS = (0.0279, 0.0738)    # full rings, centres: mean of TOPv silhouette notches (28.5, 74.5 left; 29.5, 75 right),
#   TOPv dark lines on the grip's top (27.3, 73.0; 26.3, 72.0) and FRONTv / REARv dark lines (25.8..31.8, 70.3..78.8;
#   axprof.py). A groove round the palm side with a bright bead in it (DR06, DR05); a rib across the waffle side
#   (DET829, DET830: they stand below the bottom edge there)
G_ZONES = ((0.0080, 0.0267), (0.0291, 0.0726), (0.0750, 0.1120))    # diamond fields between the end collar, the two
#   ring grooves and the flange's fillet; the pattern starts after a smooth collar behind the end lip (DET829 crop)
G_GROOVE = 0.0024             # groove width over the field edges, EST from DR06 (bead 1.3 mm, walls either side)
G_FLOOR = 0.0016              # groove floor below the tips; TOPv dips 1.5..2.5 mm at the rings
G_BEAD = (0.0005, 0.0010)     # bead radius and its top below the tips, EST: it catches the light in DR05 / DR06
G_PARTIAL = (0.0510, 0.0975)  # ribs across the waffle side between the full rings: FRONTv dark lines at a 51.0 and
#   97.3 (right grip), DR05 48.9 and 98, DET829 about 53 and 104, TOPv front-edge step at 97 (left) and 98 (right)
G_LONG = tuple(math.radians(t) for t in (20, 205, 336))   # ribs along the grip (deg from the front, up positive):
#   FRONTv shows two lines on the front face, +20 and -24 deg (33 % and 71 % down the grip), diamond panels between
#   them; lf34 (calibrated, candidate lines drawn, riblines.py) about +28. Behind, one line only, low: DET830 71 %
#   down from behind (about 200 deg), DET829 from behind and below (about 236), DR06 none on the upper rear (a second
#   rear rib at 158 deg was tried and showed in the DR06 / DET829 close-ups where the photos have none).
#   They run from the end collar to the last partial rib (DR05)
G_BAND = (math.radians(205), math.radians(336))    # smooth band under the grip between the lower ribs (DET829: no
#   diamonds below the line near the bottom; FRONTv: the face below -24 deg reads smooth and dark)
G_RIB = (0.0013, 0.0010, 0.0003)    # rib width at the root and at the top, top above the tips: DET829 / DET830 ribs
#   across the smooth band stand 5..10 px (0.5..0.9 mm) below the bottom edge (the band lies 0.75 mm under the tips)
G_LIP = 0.01675               # end lip radius (33.5 mm): FRONTv 34.9 at a 4, REARv 34.2, TOPv 32.5..34.0 at a 2..5
G_FLANGE = (0.1190, 0.1220, 0.0290)     # flange disc a0, a1 and radius: TOPv widest at a 118..121 (both), its front-
#   rear extent 57.7 mm (left, threshold reads narrow); lf34 pair: flange 82 px tall over a body of 40 (model 76 at
#   28 mm); DET829 and DR05 flange twice the body's height next to it
G_COLLAR = (0.0156, 0.1256)   # collar behind the flange (DR05 "688" moulded on it) and where the grip ends on the bar,
#   EST: the switch housing starts at a 122..126 in TOPv and wraps it
G_THROTTLE_R = 0.0130         # throttle tube under the right grip, EST (a 1.2 mm grip wall on a 26 mm pipe)


def g_tip(a):
    """Radius over the diamond tips at a (linear taper, constant over the end collar)."""
    k = (min(max(a, 0.008), 0.110) - 0.008) / 0.102
    return G_TIP[0] + (G_TIP[1] - G_TIP[0]) * k


def _rows():
    """Rings of the grip body from the end face to the bar: (a, kind, data). kind 'r': a plain ring of radius data;
    'p': a pattern row (data = row parity). Pattern rows sit on each field's own pitch so both its edges are rows."""
    out = []
    # end face: recessed disc, raised rim, rolled lip, step down to the smooth collar (DET829 crop of the end cap)
    for r, a in ((0.0110, 0.0006), (0.0118, 0.00035), (0.0126, 0.00005), (0.0135, 0.0), (0.01525, 0.0),
                 (0.0158, 0.00005), (0.01625, 0.0004), (0.0166, 0.0009), (G_LIP, 0.0015), (G_LIP, 0.0028),
                 (0.0165, 0.0036), (0.0160, 0.0042), (0.0153, 0.0046), (0.0150, 0.0050)):
        out.append((a, "r", r))
    out.append((0.0074, "r", g_tip(0.0074) - G_DEPTH))
    edges = []
    for z, (a0, a1) in enumerate(G_ZONES):
        n = int(round((a1 - a0) / G_PITCH))
        for i in range(n + 1):
            out.append((a0 + (a1 - a0) * i / n, "p", i % 2))
        if z < len(G_RINGS):                                # ring groove after this field
            c, w = G_RINGS[z], G_GROOVE / 2
            fl, bead = G_FLOOR, G_BEAD
            for a, dr in ((c - w + 0.00015, -G_DEPTH - 0.00015), (c - w + 0.0003, -fl), (c - bead[0] - 0.0001, -fl),
                          (c - bead[0] * 0.7, -bead[1] - bead[0] * 0.3), (c - bead[0] * 0.35, -bead[1] - 0.00006),
                          (c, -bead[1]), (c + bead[0] * 0.35, -bead[1] - 0.00006),
                          (c + bead[0] * 0.7, -bead[1] - bead[0] * 0.3), (c + bead[0] + 0.0001, -fl),
                          (c + w - 0.0003, -fl), (c + w - 0.00015, -G_DEPTH - 0.00015)):
                out.append((a, "b" if abs(a - c) < bead[0] * 0.8 else "r", g_tip(a) + dr))
    # fillet from the field into the flange, the flange with its rounded rim, the collar (DET829, DR05, DR06)
    a0, a1, rf = G_FLANGE
    for r, a in ((g_tip(0.1123) - G_DEPTH, 0.1123), (0.0145, 0.1142), (0.0154, 0.1158), (0.0168, 0.1172),
                 (0.0186, 0.1183), (0.0210, 0.1189), (0.0235, a0), (rf - 0.0008, a0 + 0.0002),
                 (rf - 0.0002, a0 + 0.0008), (rf, a0 + 0.0015), (rf - 0.0002, a1 - 0.0008), (rf - 0.0008, a1 - 0.0002),
                 (0.0250, a1), (0.0175, a1), (G_COLLAR[0] + 0.0004, a1 + 0.0003), (G_COLLAR[0], a1 + 0.0008),
                 (G_COLLAR[0], G_COLLAR[1] - 0.0006), (G_COLLAR[0] - 0.0006, G_COLLAR[1])):
        out.append((a, "r", r))
    return out


def grip(s, right=False):
    """Honda stock grip on one side (s: _Side): a closed rubber body from the end face to the bar (or the throttle
    tube), its diamond fields as true pyramids (36 round, 2.5 mm diagonal), two ring grooves with beads, the end lip,
    flange and collar; the underside's waffle ribs (two along it, the rings and two partial ribs across) on top."""
    mat = "grip_rubber"
    n = 2 * G_ROUND
    th = np.arange(n) * 2 * math.pi / n
    cs, sn = np.cos(th), np.sin(th)
    band = (th > G_BAND[0] + 0.01) & (th < G_BAND[1] - 0.01)
    rows = _rows()
    rows.append((G_COLLAR[1] + 0.0001, "r", G_THROTTLE_R if right else 0.0114))      # onto the pipe / the bar
    m = Mesh()
    base = []
    for a, kind, q in rows:
        if kind == "p":
            r = np.where((np.arange(n) + q) % 2 == 0, g_tip(a), g_tip(a) - G_DEPTH)
            r = np.where(band, g_tip(a) - G_DEPTH - 0.0002, r)        # the smooth band under the grip
        else:
            r = np.full(n, q)
        base.append(m.verts([s.p(a, ri * c, ri * si) for ri, c, si in zip(r, cs, sn)]))
    for k in range(len(rows) - 1):
        b0, b1 = base[k], base[k + 1]
        pat = rows[k][1] == "p" and rows[k + 1][1] == "p"
        fm = "grip_bead" if rows[k][1] == "b" and rows[k + 1][1] == "b" else mat
        for i in range(n):
            j = (i + 1) % n
            q = (b0 + i, b0 + j, b1 + j, b1 + i)
            if not pat:
                m.face(q, fm)
            elif (i + rows[k][2]) % 2 == 0:                  # corner i of row k is a tip: split along the valleys
                m.face((q[0], q[1], q[3]), mat)
                m.face((q[1], q[2], q[3]), mat)
            else:
                m.face((q[0], q[1], q[2]), mat)
                m.face((q[0], q[2], q[3]), mat)
    c = m.verts([s.p(rows[0][0])])                           # end face centre, recessed with its ring
    for i in range(n):
        m.face((base[0] + (i + 1) % n, base[0] + i, c), mat)
    m = _outward_open(m, s)
    # ---- underside waffle: ribs along at G_LONG, across at the rings and the partial ribs
    w0, w1, hgt = G_RIB
    lo = -G_FLOOR - 0.0003                                   # root below the groove floor, inside the body

    sec = [(-w0 / 2, lo), (-w0 / 2, -G_DEPTH), (-w1 / 2, hgt - 0.0003), (-w1 / 2 + 0.0002, hgt),
           (w1 / 2 - 0.0002, hgt), (w1 / 2, hgt - 0.0003), (w0 / 2, -G_DEPTH), (w0 / 2, lo)]    # (across, radial)
    for z, (a0, a1) in enumerate(G_ZONES):                   # ribs along, from the end collar to the fillet
        aa = (a0 + 0.0006 if z == 0 else G_RINGS[z - 1], G_PARTIAL[1] if z == 2 else G_RINGS[z])
        for t in G_LONG:
            e_r, e_t = np.array([math.cos(t), math.sin(t)]), np.array([-math.sin(t), math.cos(t)])
            rings = [np.array([s.p(a, *((g_tip(a) + dr) * e_r + dt * e_t)) for dt, dr in sec])
                     for a in np.linspace(aa[0], aa[1], 3)]
            m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    for c in list(G_RINGS) + list(G_PARTIAL):                # ribs across: partials over the whole lower arc (FRONTv,
        prof = [(dt, dr) for dt, dr in sec]                  # lf34, rr34), the rings' beads rise into ribs only
        t0, t1 = (G_LONG[1], G_LONG[0] + 2 * math.pi) if c in G_PARTIAL else G_BAND   # across the smooth band
        tt = np.linspace(t0 - 0.046, t1 + 0.046, 48 if c in G_PARTIAL else 30)      # over the long ribs' width
        rings = [np.array([s.p(c + da, *((g_tip(c) + dr) * np.array([math.cos(t), math.sin(t)])))
                           for da, dr in prof]) for t in tt]
        m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    # ---- mould parting line across the flange's outboard face, front and rear (DET829: a fine line at mid-height),
    # 0.4 mm wide, 0.12 mm proud of the flat face
    for t in (0.0, math.pi):
        e, e_t = np.array([math.cos(t), math.sin(t)]), np.array([-math.sin(t), math.cos(t)])
        loop = [(0.0003, -0.0002), (0.0003, 0.0002), (-0.00012, 0.0002), (-0.00012, -0.0002)]
        rings = [np.array([s.p(G_FLANGE[0] + da, *(r0 * e + dt * e_t)) for da, dt in loop])
                 for r0 in (0.0220, G_FLANGE[2] - 0.0010)]
        m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    return m


def _outward_open(m, s):
    """Wind the grip body so its normals point away from the grip's axis (checked on the widest ring)."""
    v = np.asarray(m.V, float)
    for f in m.F[:200]:
        q = v[list(f)]
        nrm = np.cross(q[1] - q[0], q[2] - q[0])
        c = q.mean(axis=0) - s.T
        radial = c - (c @ s.d) * s.d
        if np.linalg.norm(nrm) > 1e-12 and np.linalg.norm(radial) > 0.008:
            if nrm @ radial < 0:
                m.F = [tuple(reversed(f)) for f in m.F]
            break
    return m


def bar_path():
    """Centre line of the left half of the Fatbar, clamp to bar end. TOP: straight across to y 0.15, then swept
    back in one line to the bar end (bar centre x 0.980 at y 0.168, 0.969 at 0.207, 0.9165 at 0.404). FRONT cols
    2205..2340: it rises between y 0.075 and 0.225 (centre z 1.189 at y 0.153, 1.199 at 0.186); beyond it follows
    the grips' axis (UPSWEEP)."""
    c0 = fk(F_BAR, 0, T_BAR)
    k, w = math.tan(SWEEP), 0.020                                  # w: softness of the plan bend (EST)
    q = (c0[0] - TIP[0]) / k
    yc = TIP[1] - (q - w * w / (4 * q))
    ys = np.append(np.arange(0.0, TIP[1] - 0.004, 0.008), TIP[1])
    v = ys - yc
    x = c0[0] - k * (v + np.sqrt(v * v + w * w)) / 2
    m_ = math.tan(UPSWEEP) / math.cos(SWEEP)                                  # slope of the grips' axis in y
    zl = TIP[2] - (TIP[1] - ys) * m_                                       # the grips' axis, run inwards
    y1, y2 = RISE
    h = y2 - y1
    t = np.clip((ys - y1) / h, 0, 1)                                       # cubic Hermite: level at y1, on the
    z2 = TIP[2] - (TIP[1] - y2) * m_                                       # grips' axis with its slope at y2
    zr = c0[2] * (2 * t ** 3 - 3 * t ** 2 + 1) + z2 * (3 * t ** 2 - 2 * t ** 3) + m_ * h * (t ** 3 - t ** 2)
    z = np.where(ys >= y2, zl, zr)
    return np.stack([x, ys, z], axis=1)


RISE = (0.075, 0.185)         # the bar rises from the clamps and meets the grips' axis (with its upsweep) at y 0.185:
#   FRONT centre z 1.189 at y 0.153 and 1.199 at 0.186 (cols 2205..2340, earlier pass); the grips' axis is at 1.1993
#   there, so the end section is one straight 1.85 deg line from the rise to the bar end


BAR_R = (0.0143, 0.0111)      # SPEC: Renthal Fatbar, 28.6 mm in the clamps, 22.2 mm at the controls
BAR_TAPER = (0.150, 0.185)    # |y| where the taper starts and ends: TOP crops (rul_top_L / _R) and DR05, the bar is
#   thick out to the cable tie (TOP a 250..255 left, 280 right) and thin from the perch's clamp inwards; d835 the same
BAR_KNURL = (0.020, 0.074)    # knurled clamping zone each side of the centre (under the pad, hidden in every photo):
#   Renthal knurls the 28.6 mm section where the holders can sit (four positions over 26 mm, SPEC), EST extent
KNURL_PITCH = 0.0010          # knurl diamond pitch, EST (a fine straight-diamond knurl)


def bar_r(y):
    """Fatbar radius at lateral y: 28.6 mm, a smooth taper, 22.2 mm."""
    k = np.clip((np.abs(y) - BAR_TAPER[0]) / (BAR_TAPER[1] - BAR_TAPER[0]), 0, 1)
    return BAR_R[0] + (BAR_R[1] - BAR_R[0]) * k * k * (3 - 2 * k)


def knurl_map(path, n=256, tiles=8):
    """Tangent-space normal map (OpenGL, +Y up) of a straight diamond knurl: TILES pitches across N pixels, the
    pyramids' faces at 30 deg."""
    from PIL import Image
    t = (np.arange(n) + 0.5) / n * tiles
    u, v = np.meshgrid(t, t)
    a, b = (u + v) % 1.0 - 0.5, (u - v) % 1.0 - 0.5                      # distance to the two groove families
    gx = -(np.sign(a) + np.sign(b))                                      # gradient of -(|a| + |b|)
    gy = -(np.sign(a) - np.sign(b))
    k = math.tan(math.radians(30)) / 2
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(gx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    img = np.stack([nx / ln, ny / ln, nz / ln], axis=2) * 0.5 + 0.5
    Image.fromarray((img[::-1] * 255).round().astype(np.uint8)).save(path)       # row 0 is the top (v = 1)


def _block(s, a0, a1, wf, wu, mat, cf=0.0, cu=0.0, r=0.006, ch=0.0015):
    """Block clamped on the grip section from a0 to a1, wf deep and wu tall, centred (cf, cu) off the bar axis."""
    return slab(rounded_rect(wf, wu, r, 4), a0, a1, mat, lambda p, q, h: s.p(h, cf + p, cu + q), ch)


def _lever(s, pts):
    """Forged lever blade through grip-frame points (a, f, u), ball end. FRONT: ball at |y| 0.389, z 1.18;
    TOP rows 685..865 and 1405..1540: blade 52 mm ahead of the grip at |y| 0.265, 70 at 0.345, 95 at the ball
    (offsets kept relative to the grip)."""
    q = spline([s.p(a - s.shift * (1 - min(1.0, max(0.0, (a - 0.06) / 0.10))), f, u) for a, f, u in pts], 26)
    k = np.linspace(0, 1, len(q))
    rad = np.stack([np.interp(k, [0, 0.25, 1], [0.0060, 0.0042, 0.0036]),
                    np.interp(k, [0, 0.25, 1], [0.0080, 0.0068, 0.0052])], axis=1)
    m = tube(q, rad, 12, "lever", section=LEVER_SEC)
    m.add(ball(q[-1], 0.0085, "lever"))
    return m


def _wire(s, a0, f, u, loop=None):
    """Switch lead: from a housing along the underside of the bar into the bar pad (loop: the lead's own end
    points (a, f, u) from under the bar to the housing, instead of the two default ones)."""
    side = s.side
    path = bar_path() * [1, side, 1]
    y0 = abs(s.p(a0)[1])
    sel = path[(abs(path[:, 1]) > 0.070) & (abs(path[:, 1]) < y0 - 0.02)]
    rr = bar_r(sel[:, 1])
    end = [s.p(a0 + 0.012, f * 0.5, u), s.p(a0 - 0.002, f, u)] if loop is None else [s.p(*q) for q in loop]
    pts = np.vstack([sel - (rr + 0.0092)[:, None] * Z, end])          # under the bar, outside the clamp rings
    return sweep(pts, 0.0025, "cable", 8)


def _bar(path):
    """The Fatbar: plain black tube, its knurled clamping zones (own material with a knurl normal map, UVs in knurl
    pitches), the open ends with a 1.6 mm wall and a black plastic plug pressed in (both hidden by the closed grips)."""
    from scipy.interpolate import interp1d
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    marks = sorted(set([0.0, float(s[-1])] + [float(np.interp(y, path[:, 1], s)) for y in
                   (-BAR_TAPER[1], -BAR_TAPER[0], -BAR_KNURL[1], -BAR_KNURL[0], BAR_KNURL[0], BAR_KNURL[1],
                    BAR_TAPER[0], BAR_TAPER[1])]))
    ss = []                     # rows every 2 mm in the knurl zones and the taper, 6 mm elsewhere, on the zone edges
    for s0, s1 in zip(marks[:-1], marks[1:]):
        mid = abs(float(np.interp((s0 + s1) / 2, s, path[:, 1])))
        step = 0.002 if (BAR_KNURL[0] < mid < BAR_KNURL[1] or BAR_TAPER[0] < mid < BAR_TAPER[1]) else 0.006
        k = max(1, int(math.ceil((s1 - s0) / step)))
        ss += list(np.linspace(s0, s1, k + 1)[:-1])
    ss = np.array(ss + [float(s[-1])])
    P = interp1d(s, path, axis=0)(ss)
    seg = 32
    m = tube(P, bar_r(P[:, 1]), seg, "bar_black", cap0=False, cap1=False)
    circ = 2 * math.pi * BAR_R[0]
    for k in range(len(P) - 1):
        if BAR_KNURL[0] < abs(0.5 * (P[k, 1] + P[k + 1, 1])) < BAR_KNURL[1]:
            for i in range(seg):
                fi = k * seg + i
                m.M[fi] = "bar_knurl"
                u0, u1 = i * circ / seg / KNURL_PITCH / 8, (i + 1) * circ / seg / KNURL_PITCH / 8
                v0, v1 = ss[k] / KNURL_PITCH / 8, ss[k + 1] / KNURL_PITCH / 8
                m.uv[fi] = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    for end, nxt in ((P[0], P[1]), (P[-1], P[-2])):      # open ends: wall, bore, plug 1 mm inside
        ax = unit(end - nxt)
        ri = BAR_R[1] - 0.0016
        m.add(rev(end, -ax, [(BAR_R[1], 0.0), (ri + 0.0003, 0.0), (ri, 0.0003), (ri, 0.006)], "bar_black", seg))
        m.add(rev(end - 0.001 * ax, -ax, [(ri + 0.0001, 0.0), (ri + 0.0001, 0.0045), (0.0, 0.0045)], "plastic_black",
                  seg, cap0=True))
    return m


def bars():
    """Renthal Fatbar (28.6 mm in the holders, 22.2 mm at the controls), holders with their bolts, bar pad, grips,
    left: mode / traction / stop switch and clutch perch, lever and adjuster; right: throttle housing with its two
    cable elbows, start button, front master cylinder with reservoir, lever and banjo."""
    m = Mesh()
    left = bar_path()
    path = np.vstack([(left * [1, -1, 1])[::-1][:-1], left])
    path[-1] -= 0.003 * unit(path[-1] - path[-2])                           # bar ends 3 mm inside the grips' ends
    path[0] -= 0.003 * unit(path[0] - path[1])
    m.add(_bar(path))
    # ---- holders (fiche K95CF0700: upper holder 3 with two bolts 10, lower holder 4 on rubber bushes 5 above and
    # below the top bridge, washers 14 / 15, nut 13), on the rear of the bar's two clamp positions
    for side in (-1, 1):
        m.add(_holder(side * HOLDER_Y))
    # ---- bar pad (PAD_F, PAD_T, PAD_Y): red body, dark grey end caps, the bar leaving through a bore in each cap.
    # It sits over the holders and hides them and their bolts (DET 475835)
    sec = pad_section()
    cs = sec.mean(axis=0)
    ring = lambda yy, k=1.0: np.array([fk(q[0], yy, q[1]) for q in cs + (sec - cs) * k])
    y0, y1 = PAD_Y
    rings = [ring(-y1, 0.96), ring(-y1 + 0.002), ring(-y0), ring(y0), ring(y1 - 0.002), ring(y1, 0.96)]
    bore = []
    for r_ in (rings[0], rings[-1]):
        j = int(np.argmin(np.abs(path[:, 1] - r_[0][1])))
        d = (r_ - path[j]) * [1, 0, 1]
        bore.append(path[j] * [1, 0, 1] + [0, r_[0][1], 0]
                    + (bar_r(path[j, 1]) + 0.0004) * d / np.linalg.norm(d, axis=1, keepdims=True))
    m.add(_outward(grid(Mesh(), [bore[0]] + rings + [bore[1]], "barpad",
                        mats=["barpad", "pad_cap", "pad_cap", "barpad", "pad_cap", "pad_cap", "barpad"])))
    # ---- grips (component 1): part of the bars, so the bars span the SPEC 827 mm (test_bike.py)
    m.add(grip(_Side(1)))
    m.add(grip(_Side(-1), right=True))
    # ---- the switches' leads (the switches themselves are in hand_controls: round 2, component 1)
    m.add(switch_leads())
    return m


def hand_controls():
    """Switches, clutch perch and lever, throttle housing, start button, master cylinder and lever, and their leads:
    a part of their own, so the bars' part keeps the bar's SPEC height (the throttle hood and the reservoir stand
    higher in Honda's photos)."""
    m = Mesh()
    # ---- left: engine mode / stop / traction control switch on its holder, and its lead (round 2, component 1)
    m.add(switch_left())
    # ---- right: start switch on its holder, and its lead (round 2, component 1)
    m.add(switch_start())
    # ---- left: clutch perch, lever, boot, cable adjuster (component 6)
    m.add(clutch_perch())
    # ---- right: throttle housing, cable hood and boot (component 4)
    m.add(throttle_housing())
    # ---- right: Nissin master cylinder, lever, boot, banjo (component 5)
    m.add(master_cylinder())
    return m


# ---- throttle housing (fiche K95CF0400: throttle pipe 7, housing upper 11 and lower 12, screws 21)
TH_A = (0.1263, 0.1490, 0.1565)    # outboard face, step to the clamp collar, inboard face (a): TOP widest black after
#   the grip's flange from a 122, the collar round the bar to 156 (rul_top_R); rf34 the same order
TH_R = (0.0250, 0.0175)       # body and collar radii: REAR pair (p8_rear) body 360 px tall where the grip's 29 mm is
#   210 px -> 50 mm; collar EST
HOOD = [(0.1355, -0.004, 0.012), (0.1355, -0.004, 0.0245), (0.1395, -0.004, 0.0335), (0.1480, -0.004, 0.0378),
        (0.1630, -0.004, 0.0380)]  # cable hood (a, f, u): rises right beside the grip's flange in one wide arc and
#   runs inboard along the top of the bar 38 mm over its axis (REAR pair: top 46 mm over the grip's axis, the straight
#   run 38; rf34; TOP on the bar a 122..165; DET830 a thick curved black tube)
HOOD_R = 0.0085               # REAR pair: the hood about 0.6 of the grip's thickness
BOOT = (0.1630, 0.2040)       # smooth tapered boot over the cable ends, a ring at its hood end (REAR pair x 220..540,
#   DET830, rf34)
TH_SCREW = ((0.1400, -0.0175, 0.0135), (0.1400, -0.0175, -0.0135))   # the two clamp screws on the rear face, top and
#   bottom (DET830: black socket heads), M5, EST positions


def throttle_housing():
    """Honda two-cable throttle housing on the right bar: round body over the throttle pipe's flange with its parting
    seam, clamp collar, two black socket screws from behind, the cable hood rising from its top and running inboard,
    and the ribbed rubber boot from which the two cables leave (their adjuster rides on the pull cable, cables())."""
    s = _Side(-1)
    m = Mesh()
    pipe = "plastic_black"
    # throttle pipe (7) between the grip's collar and the housing (shows as a thin dark ring)
    m.add(rev(s.T, -s.d, [(G_THROTTLE_R - 0.0001, G_COLLAR[1] - 0.0006), (G_THROTTLE_R - 0.0001, TH_A[0] + 0.001)],
              pipe, 32))                                            # (inside the grip's mouth, which closes on it)
    a0, a1, a2 = TH_A
    r0, r1 = TH_R
    prof = [(G_THROTTLE_R + 0.0004, a0), (r0 - 0.003, a0), (r0 - 0.0008, a0 + 0.0004), (r0, a0 + 0.0022),
            (r0, a1 - 0.0025), (r0 - 0.001, a1 - 0.0005), (r0 - 0.0025, a1), (r1 + 0.001, a1), (r1, a1 + 0.0008),
            (r1, a2 - 0.0012), (r1 - 0.0012, a2), (BAR_R[1] + 0.0003, a2)]
    m.add(rev(s.T, -s.d, prof, "plastic_black", 48))
    # parting seam of the two halves (11 / 12): a fine groove line front and rear at mid-height, as a dark strip
    for f0 in (1, -1):
        for a_, r_ in (((a0 + 0.0025, a1 - 0.003), r0), ((a1 + 0.001, a2 - 0.0015), r1)):
            q = [s.p(x, f0 * (r_ + 0.00005), z) for x in a_ for z in (-0.0003, 0.0003)]
            mm = Mesh()
            i = mm.verts(q)
            mm.face((i, i + 1, i + 3, i + 2) if f0 > 0 else (i, i + 2, i + 3, i + 1), "rubber_black")
            m.add(mm)
    # clamp screws (21): M5 socket heads, black, on bosses
    for a_, f_, u_ in TH_SCREW:
        c = s.p(a_, f_, u_)
        ax = -s.f
        m.add(cyl(c + 0.004 * s.f, c, 0.0055, "plastic_black", 20, 0.0006))
        m.add(fastener(c, ax, "socket", af=0.0080, h=0.0045, recess=0.004, mat="bolt_black"))
    # hood: one thick curved tube, its end a collar the boot pulls over
    hp = [s.p(*q) for q in HOOD]
    m.add(sweep(hp, HOOD_R, "plastic_black", 20))
    e, ed = hp[-1], unit(hp[-1] - hp[-2])
    m.add(cyl(e - 0.002 * ed, e + 0.0015 * ed, HOOD_R + 0.0007, "plastic_black", 20, 0.0005))
    # boot: a raised ring over the hood's collar, then a smooth taper to a lip round the two cables
    L = BOOT[1] - BOOT[0]
    prof = [(HOOD_R + 0.0005, -0.0015), (HOOD_R + 0.0016, -0.0010), (HOOD_R + 0.0018, 0.0020),
            (HOOD_R + 0.0010, 0.0030), (HOOD_R + 0.0006, 0.0060), (0.0084, L * 0.55), (0.0078, L - 0.0025),
            (0.0082, L - 0.0018), (0.0082, L - 0.0006), (0.0079, L)]
    b0 = s.p(BOOT[0], HOOD[-1][1], HOOD[-1][2])
    m.add(rev(b0, -s.d, prof, "rubber_black", 24, cap1=True))
    for sg in (1, -1):                                   # a short spout for each cable (DET830)
        c0 = b0 - (L - 0.001) * s.d + sg * THR_GAP * s.f
        m.add(rev(c0, -s.d, [(0.0047, 0.0), (0.0044, 0.003), (0.0043, 0.0050), (0.0040, 0.0055)], "rubber_black", 16,
                  cap1=True))
    return m


def throttle_boot_end():
    """Centre of the boot's end, where the two cables leave it."""
    return _Side(-1).p(BOOT[1], HOOD[-1][1], HOOD[-1][2])


# ---- front master cylinder (Nissin; fiche K95CF0500: body 3, cap 4 with screws 19, holder 5 with bolts 14, lever 11,
# pivot bolt 15 and nut 20, lever boot 13, banjo bolt 16 with washers 17, hose 1)
MC_CAP = (0.2158, 0.0242, 0.0503, 0.0345, 0.0445)  # cap centre (a, f), length, width, top above the bar's axis: TOP
#   corners cast at their height, a 187..244, f 0..48 (top_mc.jpg; the right bar agrees with the model there, its end
#   within 2 mm); length 50.3, width 34.5, its long side square to the bike (17 deg off the grip); top: RIGHT photo,
#   the cap's top edge (row 406.7, cols 2300..2328) cast on three planes through the cap: 44.0..45.2 mm
MC_SCREWS = ((0.1961, 0.0307), (0.2345, 0.0149))    # the cap's two screws (TOP), 41.5 mm apart on its long axis
MC_CLAMP = (0.182, 0.202)     # clamp round the bar (TOP: grey block on the bar a 181.5..202)
MC_PIVOT = (0.164, 0.048)     # lever pivot (TOP: the round boss on the lever boot)
MC_BALL = (0.051, 0.093, -0.010)   # lever's ball centre (a, f, u): RIGHT photo (2357, 471) cast on its y plane: a 48.7,
#   f 93.4, u -11; FRONT (1476, 268) on its x plane: a 54.1, f 93.3, u -9.8
MC_BARREL = (0.0275, -0.004, 0.0115, 0.168, 0.246)   # barrel axis f, u, radius, a from / to: under the reservoir
#   (rf34: a round body under the box), clear of the bar as it sweeps forward inboard; EST radius (12.7 mm bore)


MC_WIN = (0.0057, 0.0195, 0.0092)   # sight window centre (along the cap's long side, inboard; over the bar's axis) and
#   ring radius: REAR cast on the rear face's plane (5.7, 18.0, 9.6), raised 1.5 mm and 0.4 smaller to clear the bar
MC_LWR = (0.0183, 0.0150)     # LWR mark's centre: DET830, 0.645 of the way from the window's centre to the face's inboard
#   edge, 4.3 mm under the window's centre (its rows foreshortened 0.8); 6.3 x 2 mm letters, the line under them
MC_NISSIN = (-0.0040, 0.0215)       # NISSIN's centre on the front face: rf34 cast on the front face's plane
LEVER_SEC = rounded_rect(2.0, 2.0, 0.75, 3)   # forged lever: flat sides, rounded edges (rf34, DR05), scaled per point


def _decal(c, right, up, nrm, w, h, mat):
    """A flat patch W x H centred at C, facing NRM, its UVs over the patch (raised lettering as a relief map)."""
    m = Mesh()
    xs, ys = np.linspace(-0.5, 0.5, 3), np.linspace(-0.5, 0.5, 3)
    idx = {}
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            idx[i, j] = m.verts([c + x * w * right + y * h * up])
    for i in range(2):
        for j in range(2):
            fi = len(m.F)
            m.face((idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]), mat)
            m.uv[fi] = [(xs[i] + 0.5, ys[j] + 0.5), (xs[i + 1] + 0.5, ys[j] + 0.5), (xs[i + 1] + 0.5, ys[j + 1] + 0.5),
                        (xs[i] + 0.5, ys[j + 1] + 0.5)]
    if np.cross(right, up) @ nrm < 0:
        m.F = [tuple(reversed(f)) for f in m.F]
        m.uv = {k: list(reversed(v)) for k, v in m.uv.items()}
    return m


def _dogbone(r, half, waist, n=72):
    """Star-shaped outline (p, q) of two round lobes of radius R at q = +-HALF joined by a waist WAIST wide."""
    out = []
    for t in np.linspace(0, 2 * math.pi, n, endpoint=False):
        d = np.array([math.cos(t), math.sin(t)])
        best = 0.0
        for cq in (half, -half):                       # ray from the centre against each lobe
            b = d[1] * cq
            disc = b * b - (cq * cq - r * r)
            if disc >= 0:
                best = max(best, b + math.sqrt(disc))
        tx = waist / 2 / abs(d[0]) if abs(d[0]) > 1e-9 else 1e9
        ty = half / abs(d[1]) if abs(d[1]) > 1e-9 else 1e9
        best = max(best, min(tx, ty))
        out.append(best * d)
    return np.array(out)


def _mc_bar_axis(c, lx, ly, yl):
    """The bar's axis under the reservoir at YL along the cap's long side: its (q, z) in the cap's frame."""
    s = _Side(-1)
    A = np.linspace(0.15, 0.28, 261)
    P = np.array([s.p(a) for a in A])
    q = (P - c) @ ly
    i = int(np.argmin(np.abs(q - yl)))
    return float((P[i] - c) @ lx), float(P[i][2])


def mc_maps(folder, n=512):
    """Relief maps (OpenGL normal maps) of the raised NISSIN on the reservoir's front (bold italic, 32 x 5.5 mm in a
    36 x 6.8 mm patch, rf34) and the raised LWR with its level line (DET830, in a 9 x 4.5 mm patch); 0.35 mm high."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import os
    for name, text, wmm, hmm, font, th, line in (
            ("mc_nissin", "NISSIN", 36.0, 6.8, "/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf", 5.5, False),
            ("mc_lwr", "LWR", 9.0, 4.5, "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 2.0, True)):
        W_, H_ = n, int(round(n * hmm / wmm))
        k = 4
        im = Image.new("L", (W_ * k, H_ * k), 0)
        d = ImageDraw.Draw(im)
        px_mm = W_ * k / wmm
        f = ImageFont.truetype(font, int(th * px_mm * 1.36))
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
        tw = (32.0 if name == "mc_nissin" else 6.3) * px_mm
        sx = tw / (x1 - x0)
        tmp = Image.new("L", (x1 - x0 + 8, y1 - y0 + 8), 0)
        ImageDraw.Draw(tmp).text((4 - x0, 4 - y0), text, font=f, fill=255)
        tmp = tmp.resize((int(tmp.width * sx), int(th * px_mm)), Image.LANCZOS)
        oy = (H_ * k - tmp.height) // 2 - (int(0.9 * px_mm) if line else 0)
        im.paste(tmp, ((W_ * k - tmp.width) // 2, oy))
        if line:
            d.rectangle([(W_ * k - tw * 1.15) / 2, oy + tmp.height + 0.5 * px_mm, (W_ * k + tw * 1.15) / 2,
                         oy + tmp.height + 1.2 * px_mm], fill=255)
        mask = np.asarray(im.resize((W_, H_), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6)), float) / 255.0
        h = 0.35 * mask
        gy, gx = np.gradient(h, wmm / W_)
        nx, ny, nz = -gx, gy, np.ones_like(h)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        Image.fromarray(((np.stack([nx, ny, nz], axis=2) / ln[..., None] * 0.5 + 0.5) * 255).round().astype(np.uint8)
                        ).save(os.path.join(folder, name + "_n.png"))


def _mc_frame():
    s = _Side(-1)
    ly = unit((s.p(0.2351, 0.0002) - s.p(0.1871, 0.0153)) * [1, 1, 0])     # the cap's long side, inboard
    lx = unit(np.cross(ly, Z))                                               # forward
    return s, lx, ly


def _mc_banjo():
    """Banjo on the barrel's inboard end, below: its centre, the bolt's axis, the hose fitting's end."""
    s = _Side(-1)
    c = s.p(MC_BARREL[4] - 0.006, MC_BARREL[0] + 0.002, MC_BARREL[1] - MC_BARREL[2] - 0.006)
    ax = -s.u
    return c, ax, c + 0.006 * s.f - 0.020 * s.u * 0.0 + 0.016 * unit(s.f - 0.6 * s.u)


def master_cylinder():
    """Nissin front master cylinder on the right bar: cast body with its barrel, the reservoir square to the bike
    with its cap, two screws and the diaphragm plate's rim, the sight window and its LWR level mark on the rear face,
    the clamp with its holder and two bolts from behind, the lever pivot lug with bolt and nut under the black lever
    boot, the forged lever with its ball end, the banjo with bolt, washers and the hose fitting."""
    s, lx, ly = _mc_frame()
    m = Mesh()
    cast, cap = "mc_cast", "mc_cap"
    zb = s.p(MC_CAP[0])[2]                                                   # the bar's axis at the cylinder
    ca, cf, L, W, top = MC_CAP
    c = s.p(ca, cf)
    c = np.array([c[0], c[1], zb])
    # reservoir: walls from the barrel up, rounded in plan (r 5), drafted 2 deg, the cap's rim seat
    plan = rounded_rect(L, W, 0.005, 5)
    to3 = lambda p, q, h: c + p * ly + q * lx + h * Z
    m.add(slab(plan * 0.985, 0.0135, top - 0.0035, cast, to3, ch=0.0012))      # over the bar (DET830: window above it)
    neck = np.array([(p_, q_) for p_, q_ in plan * 0.985 if q_ > -0.003] + [(-L / 2 * 0.985, -0.003), (L / 2 * 0.985, -0.003)])
    neck = neck[np.argsort(np.arctan2(neck[:, 1] - neck[:, 1].mean(), neck[:, 0]))]
    m.add(slab(neck, -0.002, 0.0145, cast, to3, ch=0.0008))                    # neck to the barrel, ahead of the bar
    # cap (4): plate with rounded edges, its diaphragm plate's rim showing as a thin step, two cross-head screws
    m.add(slab(plan, top - 0.0035, top - 0.0008, cap, to3, ch=0.0006))
    m.add(slab(plan * np.array([0.93, 0.90]), top - 0.0009, top, cap, to3, ch=0.0004))
    for a_, f_ in MC_SCREWS:
        q = s.p(a_, f_)
        q = np.array([q[0], q[1], zb + top])
        m.add(fastener(q, Z, "button", af=0.0060, h=0.0016, recess=0.0022, mat="steel"))
    # the rear wall reaches down to just over the bar round the window (DET830: the face runs down behind the bar;
    # the bar crosses under the reservoir's rear 16 deg off it, so the wall's lower edge follows the bar's top 0.5 mm up)
    qr = -(W / 2 * 0.985)
    pts = []
    for yl in np.linspace(-0.018, 0.0225, 15):
        lo = 0.004
        for qq in (qr, qr + 0.004):
            ax = _mc_bar_axis(c, lx, ly, yl)                                   # bar axis (q, z) under that ly
            d = qq - ax[0]
            if abs(d) < BAR_R[1]:
                lo = max(lo, ax[1] - zb + math.sqrt(BAR_R[1] ** 2 - d * d) + 0.0005)
        pts.append((yl, lo))
    skirt = [(yl, 0.0150) for yl, _ in pts[::-1]] + pts
    m.add(slab(skirt, qr, qr + 0.004, cast, lambda p_, h_, q_: c + p_ * ly + q_ * lx + h_ * Z, ch=0.0006))
    # sight window (DET830: a bright machined ring, a chrome inner ring, the dark lens): REAR cast on the rear face's
    # plane: centre 18.0 mm over the bar's axis and 5.7 mm inboard of the cap's centre, ring 19.2 mm, lens about 13;
    # built 19.5 mm up so the ring clears the bar's top (1.2 px in REAR)
    rear = c + (qr - 0.0001) * lx + MC_WIN[0] * ly + MC_WIN[1] * Z
    m.add(rev(rear, -lx, [(MC_WIN[2], -0.0003), (MC_WIN[2], 0.0005), (MC_WIN[2] - 0.0007, 0.0011),
                          (0.0071, 0.0011), (0.0069, 0.0005)], "alu_machined", 40))
    m.add(rev(rear, -lx, [(0.0069, 0.0005), (0.0066, 0.0008), (0.0062, 0.0008), (0.0061, 0.0002)], "chrome", 40))
    m.add(rev(rear, -lx, [(0.0062, 0.0002), (0.0, 0.0002)], "glass_dark", 40, cap1=False))
    # raised LWR with its level line, and the ejector-pin mark above it (DET830), as a relief map on the face
    m.add(_decal(c + (qr - 0.00012) * lx + MC_LWR[0] * ly + MC_LWR[1] * Z, -ly, Z, -lx, 0.0090, 0.0045, "mc_lwr"))
    m.add(cyl(c + qr * lx + 0.0190 * ly + 0.0227 * Z, c + (qr - 0.0003) * lx + 0.0190 * ly + 0.0227 * Z, 0.0010, cast,
              12))
    # raised NISSIN on the front face (rf34: bold italic, ly -19.9..+12.0, 18.8..24.3 mm over the axis)
    m.add(_decal(c + (W / 2 * 0.985 + 0.00012) * lx + MC_NISSIN[0] * ly + MC_NISSIN[1] * Z, ly, Z, lx, 0.0360, 0.0068,
                 "mc_nissin"))                         # (facing the front, the reader's right is the bike's left)
    # a small square pocket on the outboard side just under the cap (rf34 cast on that face: 4.8 x 3.6 mm, centre
    # 5.7 mm ahead of the cap's centre, 36.7 mm over the bar's axis), 1 mm deep
    pk = c - (L / 2 * 0.985 - 0.0004) * ly + 0.0057 * lx + 0.0367 * Z
    m.add(box(pk, (0.0048, 0.0010, 0.0036), "plastic_black", np.column_stack([lx, ly, Z])))
    # barrel and its end caps, the web to the clamp
    bf, bu, br, b0, b1 = MC_BARREL
    m.add(rev(s.p(b0, bf, bu), -s.d, [(br - 0.0015, 0.0), (br, 0.0015), (br, b1 - b0 - 0.002), (br - 0.002, b1 - b0)],
              cast, 32, cap0=True, cap1=True))
    # clamp: the body's front half round the bar and the holder (5) behind it, two M6 flange bolts from behind
    rb = bar_r(s.p(0.19)[1])
    for a0_, a1_ in (MC_CLAMP,):
        ring = [(rb + 0.0004, a0_), (rb + 0.0052, a0_), (rb + 0.0060, a0_ + 0.0008), (rb + 0.0060, a1_ - 0.0008),
                (rb + 0.0052, a1_), (rb + 0.0004, a1_)]
        m.add(rev(s.T, -s.d, ring, cast, 40, ref=s.f, arc=(-1.35, 1.35), solid=True))          # front half
        m.add(rev(s.T, -s.d, ring, cast, 40, ref=s.f, arc=(1.79, 4.49), solid=True))            # holder (5)
        m.add(slab(_dogbone(0.0095, 0.016, 0.0120), 0.0, 0.0060, cast,                   # holder: round lobes at the
                   lambda p_, q_, h_: s.p((a0_ + a1_) / 2 + p_, -(rb + 0.0025 + h_), q_), ch=0.0008))   # bolts (DET830)
        for u_ in (0.016, -0.016):
            m.add(fastener(s.p((a0_ + a1_) / 2, -(rb + 0.0085), u_), -s.f, "flange", af=0.010, h=0.0058,
                           flange_d=0.0135))
    m.add(_block(s, MC_CLAMP[0] + 0.001, MC_CLAMP[1] - 0.001, bf - rb - 0.004, 0.022, cast,
                 cf=(rb + bf) / 2, cu=bu * 0.5, r=0.004))
    # lever pivot lug (two ears) ahead of the barrel's outboard end, the pivot bolt (15) and nut (20)
    pa, pf = MC_PIVOT
    lug = [(pa - 0.010, bf - 0.004), (pa + 0.014, bf - 0.004), (pa + 0.012, pf + 0.004), (pa + 0.002, pf + 0.011),
           (pa - 0.008, pf + 0.008), (pa - 0.011, pf)]
    for u0, u1 in ((0.0035, 0.0105), (-0.0135, -0.0065)):
        m.add(slab(lug, u0, u1, cast, lambda a_, f_, h: s.p(a_, f_, h), ch=0.0008))
    m.add(fastener(s.p(pa, pf, 0.0105), s.u, "flange", af=0.010, h=0.005, flange_d=0.013))
    m.add(fastener(s.p(pa, pf, -0.0135), -s.u, "flange", af=0.010, h=0.0065, flange_d=0.0135, mat="steel",
                   thread=0.003, thread_d=0.006))
    # lever (11): forged blade from the pivot to the ball (FRONT ball at abs(y) 0.389, z 1.18; TOP), a boss round the
    # pivot between the ears
    m.add(cyl(s.p(pa, pf, -0.0063), s.p(pa, pf, 0.0033), 0.0092, "lever", 24, 0.0008))
    m.add(_lever(s, [(pa - 0.002, pf + 0.008, -0.002), (pa - 0.016, pf + 0.014, -0.004), (0.130, 0.067, -0.006),
                     (0.087, 0.076, -0.008), (0.062, 0.086, -0.009), MC_BALL]))
    # reach adjuster: a cross-head screw seen through an oval opening in the boot's outboard side (RIGHT photo)
    oc = s.p(0.1438, 0.047, -0.001)
    rim = [(0.0062 * math.cos(t) * 0.75, 0.0062 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
    to_o = lambda p_, q_, h: oc + p_ * s.f + q_ * s.u + h * s.d
    m.add(slab(rim, -0.0003, 0.0008, "rubber_black", to_o, ch=0.0003))
    m.add(slab([(x * 0.78, y * 0.78) for x, y in rim], 0.0008, 0.00085, "plastic_black", to_o, ch=0.0))
    m.add(fastener(oc + 0.0006 * s.d, s.d, "button", af=0.0060, h=0.0015, recess=0.0026, mat="steel"))
    # lever boot (13): black rubber hood over the lug and the lever's root, a dome over the pivot bolt (TOP: a 145..193,
    # f 9..73; rf34)
    hood = [(0.150, 0.026), (0.172, 0.022), (0.186, 0.034), (0.184, 0.058), (0.170, 0.068), (0.152, 0.070),
            (0.144, 0.058), (0.144, 0.036)]
    m.add(pillow(hood, -0.0165, 0.0150, 0.0060, "rubber_black", lambda a_, f_, h: s.p(a_, f_, h)))   # rounded (rf34)
    m.add(rev(s.p(pa, pf, 0.0150), s.u, [(0.0090, -0.001), (0.0088, 0.0015), (0.0070, 0.0035), (0.0040, 0.0045),
                                         (0.0, 0.0047)], "rubber_black", 24))
    # banjo (17 washers either side, bolt 16) and the hose fitting
    bc, bax, he = _mc_banjo()
    m.add(rev(bc - 0.0005 * bax, bax, [(0.0035, 0.0), (0.0075, 0.0), (0.0075, 0.0015), (0.0035, 0.0015)], "alu_machined",
              24, solid=True))
    m.add(cyl(bc + 0.0010 * bax, bc + 0.0110 * bax, 0.0080, "steel", 24, 0.0008))
    m.add(rev(bc + 0.0110 * bax, bax, [(0.0035, 0.0), (0.0075, 0.0), (0.0075, 0.0015), (0.0035, 0.0015)], "alu_machined",
              24, solid=True))
    m.add(fastener(bc + 0.0125 * bax, bax, "flange", af=0.012, h=0.0065, flange_d=0.0155, mat="bolt_black"))  # DET830
    m.add(cyl(bc + 0.006 * bax, he, 0.0042, "steel", 16, 0.0005))
    return m


# ---- clutch perch (fiche K95CF0400: holder 14, clamp 15 with bolts 20, lever 17, pivot bolt 22, nut 24, lever boot 16,
# cable adjuster 18 / 19). Positions read in TOP (`ref/top_perch.jpg`, 5x, pixel ticks), cast at their heights and
# measured in the photo's own left-grip frame (its end and axis from gripscan.py: the top photo draws the left bar
# 5 deg less swept than the side photos and the model, so the photo's grip is the reference, not the model's)
CP_CLAMP = (0.1650, 0.1930)   # silver clamp round the bar (TOP a 164.7..193.0)
CP_PIVOT = (0.1743, 0.0333)   # pivot bolt's head (TOP)
# black lever boot in plan: TOP corners a 154..211, f 24.7..66.2 (the sleeve's stations in clutch_perch)
CP_ADJ = ((0.2027, 0.0439), (0.2392, 0.0460))     # cable adjuster from the boot to its inboard end (TOP)
CP_SCREW = (0.2067, 0.0291)   # small hex screw and nut on the boot's inboard end (TOP, DR05: two small nuts)
CP_BALL = (0.0495, 0.095, -0.021)   # lever's ball: FRONT (2526, 284.5) cast on its x plane: a 55, f 92, u -20 (LEFT
#   hides it behind the grip's end); the earlier model's a 49.5 f 95 kept within that


def clutch_perch():
    """Clutch perch on the left bar: silver cast clamp and its holder with two flange bolts from behind (DR06), the arm
    and two ears round the lever's root, pivot bolt and nut, the forged lever, the black rubber boot over the root, the
    knurled cable adjuster with its castellated lock ring, the small screw and nut on the boot."""
    s = _Side(1)
    m = Mesh()
    cast = "mc_cast"
    a0, a1 = CP_CLAMP
    rb = bar_r(s.p(0.18)[1])
    ring = [(rb + 0.0004, a0), (rb + 0.0055, a0), (rb + 0.0063, a0 + 0.0008), (rb + 0.0063, a1 - 0.0008),
            (rb + 0.0055, a1), (rb + 0.0004, a1)]
    m.add(rev(s.T, -s.d, ring, cast, 40, ref=s.f, arc=(-1.38, 1.38), solid=True))             # clamp, front half
    m.add(rev(s.T, -s.d, ring, cast, 40, ref=s.f, arc=(1.76, 4.52), solid=True))              # holder, rear half
    m.add(_block(s, a0 + 0.001, a1 - 0.001, 0.0055, 0.048, cast, cf=-(rb + 0.0050), r=0.003))
    for u_ in (0.016, -0.016):
        m.add(fastener(s.p((a0 + a1) / 2, -(rb + 0.0077), u_), -s.f, "flange", af=0.010, h=0.0058, flange_d=0.0135))
    pa, pf = CP_PIVOT
    arm = [(a0 + 0.002, rb + 0.004), (a1 - 0.003, rb + 0.004), (pa + 0.012, pf + 0.002), (pa + 0.004, pf + 0.010),
           (pa - 0.006, pf + 0.009), (pa - 0.011, pf + 0.001), (a0 + 0.001, rb + 0.008)]
    for u0, u1 in ((0.0035, 0.0100), (-0.0130, -0.0065)):
        m.add(slab(arm, u0, u1, cast, lambda a_, f_, h: s.p(a_, f_, h), ch=0.0008))
    m.add(fastener(s.p(pa, pf, 0.0100), s.u, "flange", af=0.010, h=0.005, flange_d=0.013, mat="alu_machined"))
    m.add(fastener(s.p(pa, pf, -0.0130), -s.u, "flange", af=0.010, h=0.0065, flange_d=0.0135, mat="steel",
                   thread=0.003, thread_d=0.006))
    m.add(cyl(s.p(pa, pf, -0.0063), s.p(pa, pf, 0.0033), 0.0090, "lever", 24, 0.0008))
    m.add(_lever(s, [(pa - 0.002, pf + 0.007, -0.003), (pa - 0.016, pf + 0.015, -0.013), (0.130, 0.060, -0.019),
                     (0.087, 0.072, -0.0205), (0.062, 0.085, -0.021), CP_BALL]))     # level from the boot (FRONT pair)
    # boot over the lever's root and the arm: a sleeve tapering outboard to the lever (DR05; FRONT pair: its top falls
    # from the clamp to the lever, the lever leaves it at the ball's height)
    st = [(0.2095, (0.026, 0.062), (-0.026, 0.006)), (0.1900, (0.025, 0.066), (-0.026, 0.004)),
          (0.1700, (0.032, 0.068), (-0.025, -0.004)), (0.1560, (0.042, 0.066), (-0.022, -0.009)),
          (0.1520, (0.046, 0.063), (-0.020, -0.011))]
    rings = []
    for a_, (f0, f1), (u0, u1) in st:
        rr_ = rounded_rect(f1 - f0, u1 - u0, min(0.006, (u1 - u0) * 0.45), 4)
        rings.append(np.array([s.p(a_, (f0 + f1) / 2 + q[0], (u0 + u1) / 2 + q[1]) for q in rr_]))
    m.add(_outward(grid(Mesh(), rings, "rubber_black", cap0=True, cap1=True)))
    m.add(fastener(s.p(CP_SCREW[0], CP_SCREW[1], 0.0060), s.u, "hex", af=0.008, h=0.0045, mat="alu_machined"))
    m.add(fastener(s.p(CP_SCREW[0], CP_SCREW[1], 0.0105), s.u, "hex", af=0.008, h=0.004, mat="alu_machined",
                   thread=0.0025, thread_d=0.005))
    # cable adjuster: threaded sleeve out of the boot, castellated lock ring, knurled barrel (DR05)
    p0, ad = _clutch_adjuster(start=True)
    p1, _ = _clutch_adjuster()
    L = float(np.linalg.norm(p1 - p0))
    m.add(cyl(p0 - 0.003 * ad, p0 + 0.006 * ad, 0.0042, "alu_machined", 16, 0.0004))
    prof = [(0.0050, 0.006)]
    for i in range(6):                                               # lock ring: six castellations' ribs
        z = 0.0068 + i * 0.0011
        prof += [(0.0080, z), (0.0080, z + 0.0005), (0.0074, z + 0.0007)]
    prof += [(0.0074, 0.0136), (0.0056, 0.0142)]
    for i in range(10):                                              # knurled barrel
        z = 0.0150 + i * (L - 0.0175) / 10
        prof += [(0.0066, z), (0.0069, z + 0.0006), (0.0066, z + 0.0012)]
    prof += [(0.0062, L - 0.0010), (0.0045, L)]
    m.add(rev(p0, ad, prof, "anod_black", 24, cap1=True))
    return m


def _clutch_adjuster(start=False):
    """The adjuster's axis: its boot end (start) or its inboard end, where the cable leaves; and its direction."""
    s = _Side(1)
    q0, q1 = s.p(CP_ADJ[0][0], CP_ADJ[0][1], -0.002), s.p(CP_ADJ[1][0], CP_ADJ[1][1], -0.002)
    return (q0 if start else q1), unit(q1 - q0)


# ================================================================ switches (fiche K95CF0400: left switch 4 with its lead
# and holder 3, start switch 6 with its lead and holder 5). Anatomy, photos and readings: research/detail-ledger/
# front.md, round 2, component 1. Positions triangulated from the REAR and TOP studio photos (tri.py: one feature
# picked in both, the 3D point that fits both pixels, residual 1.0..1.3 px), in the grip frame without CTRL_SHIFT.
SW_TILT = math.atan(0.2216)   # the left switch's face leans back 12.5 deg (green sits 3.7 mm further back than blue,
#   16.7 mm lower: REAR + TOP)
SW_FACE_F = -0.0386           # face at u 0 (button tops f -38.8 + 0.2216 u mm (blue, green), red -37.7; the buttons stand
#   1.2 mm proud of the face: TOP pair, the photo's buttons show more of their sides than 0.4 mm did; then 0.8 mm back:
#   TOP pair, the model's buttons 0.7 to 1.7 px ahead of the photo's)
SW_BTN = {"m": ((0.1321, 0.0166), 0.00475, 0.0083), "tc": ((0.1319, -0.0001), 0.00475, 0.0083),
          "stop": ((0.1517, 0.0071), 0.00625, 0.0096)}  # (a, u) centre, button radius, well radius. REAR + TOP: blue
#   a 131.1 u 16.6, green 130.9 / -0.1, red 150.7 / 7.1, all 1 mm further inboard after the REAR and TOP pairs (model
#   1.1 to 1.3 px outboard in both); diameters REAR 9.1..9.6 mm (blue, green), red / blue 1.31 (DR06) -> 12.5: the REAR
#   pair's blobs 89.5 / 87.0 / 113.7 px against the photo's 90.1 / 88.7 / 114.1; wells DR06 1.9 x the small buttons,
#   1.57 x the red one (held off each other by a 0.5 mm ridge)
SW_WIN = ((0.1459, 0.0263), (0.1543, 0.0266))     # LED lenses (a, u): REAR + TOP (+1 mm as the buttons); 6 x 9 mm
#   (REAR 6.5 x 10 with the bezel, DET829 1.6 tall to 1 wide)
SW_POLY = ((0.1225, 0.0175), (0.1448, 0.0328), (0.1620, 0.0337), (0.1642, 0.0315), (0.1635, 0.0050),
           (0.1447, -0.0122))   # face outline corners (a, u): REAR edges read on the face's plane (the 16 deg sweep moves a
#   point 25 mm behind the ruler 7 mm inboard), TOP: rear face a 120.9..158.7 at f -38.5; the outline is the hull of
#   these and the three wells (DR06: the wells' lips are the outline at the bottom and the outboard side). Top: the
#   REAR pair put the first build's top edge 1.8 mm high (33.7 mm over the axis); LEFT and lf34 show a dark edge at
#   u 42..44 that REAR, DR06 and DET829 do not (ledger)
SW_FRONT = -0.0162            # body's front face behind the bar (clears the grip's collar, r 15.6), EST
SW_PAD = ((0.1515, -0.0225), (0.0145, 0.0090))    # raised pad on the top with an arrow mark: TOP (1782..1799,
#   1410..1424) cast at u 37 mm: a 143..160, f -27.7..-17.5
SW_COLLAR = (0.1262, 0.1600, 0.0172)              # collar round the bar (holder 3), EST: the block's front over the bar
#   reaches f 0 at a 150 (TOP tab cast at u 30)


def _hull_outline(pts, n=120, cut=2):
    """Convex outline through PTS (2D), corners rounded by corner cutting, resampled to N points by arc length,
    counter-clockwise."""
    p = np.asarray(pts, float)
    h = p[ConvexHull(p).vertices]
    for _ in range(cut):
        nx = np.roll(h, -1, axis=0)
        h = np.stack([0.75 * h + 0.25 * nx, 0.25 * h + 0.75 * nx], axis=1).reshape(-1, 2)
    c = np.vstack([h, h[:1]])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, c[:, 0]), np.interp(t, s, c[:, 1])], axis=1)


def _inset(o, d):
    """Convex counter-clockwise outline moved D inwards along its normals."""
    t = np.roll(o, -1, axis=0) - np.roll(o, 1, axis=0)
    n = np.stack([-t[:, 1], t[:, 0]], axis=1)
    return o + d * n / np.linalg.norm(n, axis=1, keepdims=True)


def _face_frame(s, tilt, f0):
    """A switch face leaning back by TILT: the point at projected (a, u) on it, its outward normal, up and across
    (towards the rider's right) vectors."""
    nf = -math.cos(tilt) * s.f + math.sin(tilt) * s.u
    up = math.sin(tilt) * s.f + math.cos(tilt) * s.u
    right = -s.d if s.side > 0 else s.d
    return (lambda a, u: s.p(a, f0 + math.tan(tilt) * u, u)), nf, up, right


def _button(c, nf, up, right, rb, h0, h1, mat, dome=0.0001):
    """Round push button standing from h0 to h1 along NF at C, its top edge rounded 0.6 mm; the top disc carries
    UVs over the button's diameter (the symbol's normal and colour maps), the sides the map's plain border."""
    m = Mesh()
    ang = np.linspace(0, 2 * math.pi, 48, endpoint=False)
    rad = np.outer(np.cos(ang), right) + np.outer(np.sin(ang), up)
    prof = [(rb, h0), (rb, h1 - 0.0006), (rb - 0.0002, h1 - 0.00018), (rb - 0.0006, h1)]
    prof += [(rb * k, h1 + dome * (1 - k * k)) for k in (0.8, 0.6, 0.4, 0.2)]
    base = [m.verts(c + h * nf + r * rad) for r, h in prof]
    cen = m.verts([c + (h1 + dome) * nf])
    for k in range(len(prof) - 1):
        for i in range(48):
            j = (i + 1) % 48
            fi = len(m.F)
            m.face((base[k] + i, base[k] + j, base[k + 1] + j, base[k + 1] + i), mat)
            uv = []
            for kk, ii in ((k, i), (k, j), (k + 1, j), (k + 1, i)):
                r = prof[kk][0]
                uv.append((0.5 + 0.5 * r / rb * math.cos(ang[ii]), 0.5 + 0.5 * r / rb * math.sin(ang[ii]))
                          if kk >= 3 else (0.5, 0.02))
            m.uv[fi] = uv
    for i in range(48):
        j = (i + 1) % 48
        fi = len(m.F)
        m.face((base[-1] + i, base[-1] + j, cen), mat)
        r = prof[-1][0] / rb
        m.uv[fi] = [(0.5 + 0.5 * r * math.cos(ang[i]), 0.5 + 0.5 * r * math.sin(ang[i])),
                    (0.5 + 0.5 * r * math.cos(ang[j]), 0.5 + 0.5 * r * math.sin(ang[j])), (0.5, 0.5)]
    return _outward(m)


def switch_maps(folder, n=512):
    """Colour and tangent-space normal maps (OpenGL, +Y up) of the engraved button symbols, the canvas spanning the
    button's diameter: M (engine mode, blue), the engine stop symbol (a circling arrow crossed out, red), T in two
    circling arrows (traction control, green), DR06 close-ups; the start symbol (a circling arrow round a lightning
    bolt, black) DET830. Engraved 0.25 mm, the floor darkened 20 % (it holds shadow and dust in the photos)."""
    from PIL import Image, ImageDraw, ImageFilter
    import os
    k = 4
    N = n * k

    def px(x, y):
        return ((0.5 + x) * N, (0.5 - y) * N)

    def arc(d, r, a0, a1, w, head=None):
        box = [px(-r, r), px(r, -r)]
        d.arc([box[0], box[1]], -a1, -a0, fill=255, width=int(w * N))
        if head is not None:                              # arrowhead at angle head, pointing along +-tangent
            ang, sgn = head
            t = math.radians(ang)
            c = np.array([r * math.cos(t), r * math.sin(t)])
            tg = sgn * np.array([-math.sin(t), math.cos(t)])
            nr = np.array([math.cos(t), math.sin(t)])
            pts = [c + 0.10 * tg, c - 0.02 * tg + 0.075 * nr, c - 0.02 * tg - 0.075 * nr]
            d.polygon([px(*p) for p in pts], fill=255)

    def line(d, pts, w):
        d.line([px(*p) for p in pts], fill=255, width=int(w * N), joint="curve")
        for p in (pts[0], pts[-1]):
            q = px(*p)
            rr = w * N / 2
            d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=255)

    syms = {}
    im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im)
    line(d, [(-0.19, -0.20), (-0.19, 0.20), (0.0, -0.03), (0.19, 0.20), (0.19, -0.20)], 0.10)
    syms["sw_m"] = (im, (35, 88, 190))
    im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im)
    arc(d, 0.29, 62, 292, 0.045, head=(292, 1))
    line(d, [(-0.39, 0.035), (0.37, -0.005)], 0.042)
    line(d, [(-0.16, -0.36), (0.19, 0.35)], 0.042)
    syms["sw_stop"] = (im, (205, 50, 50))
    im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im)
    line(d, [(-0.15, 0.12), (0.15, 0.12)], 0.09)
    line(d, [(0.0, 0.12), (0.0, -0.17)], 0.10)
    arc(d, 0.31, 28, 148, 0.05, head=(150, 1))
    arc(d, 0.31, 208, 328, 0.05, head=(330, 1))
    syms["sw_tc"] = (im, (32, 150, 72))
    im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im)
    arc(d, 0.27, 100, 425, 0.045)
    line(d, [(0.035, 0.17), (-0.045, 0.01), (0.045, 0.0), (-0.03, -0.17)], 0.04)
    syms["sw_start"] = (im, (26, 26, 28))
    for name, (im, rgb) in syms.items():
        mask = np.asarray(im.resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2)), float) / 255.0
        h = -0.25 * mask                                              # mm
        mm_px = 9.5 / n                                               # the canvas spans about one button (mm a pixel)
        gy, gx = np.gradient(h, mm_px)                                # rows run down the image (-v)
        nx, ny, nz = -gx, gy, np.ones_like(h)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        Image.fromarray(((np.stack([nx, ny, nz], axis=2) / ln[..., None] * 0.5 + 0.5) * 255).round().astype(np.uint8)
                        ).save(os.path.join(folder, name + "_n.png"))
        col = np.array(rgb, float)[None, None, :] * (1.0 - 0.2 * mask[..., None])
        Image.fromarray(col.round().astype(np.uint8)).save(os.path.join(folder, name + ".png"))


def switch_left():
    """Honda's left switch (engine mode M, engine stop, traction control T, two LED lenses) on its holder: a housing
    behind the bar whose rear face leans back 12.5 deg towards the rider, the three buttons in dished wells, the
    parting line between the rear shell and the body, the chamfer with its slot, the raised pad with an arrow on the
    top, the collar round the bar, the lead's grommet on the front-top corner and the lead looping over the bar's
    front into the run under the bar (lf34, LEFT)."""
    s = _Side(1)
    m = Mesh()
    hs = "sw_body"
    P, nf, up, right = _face_frame(s, SW_TILT, SW_FACE_F)
    pts = [p for p in SW_POLY]
    for (c, rb, rw) in SW_BTN.values():
        pts += [(c[0] + (rw + 0.0012) * math.cos(t), c[1] + (rw + 0.0012) * math.sin(t))
                for t in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
    face = _hull_outline(pts, 120)
    # rear shell: 3 mm plate, the wells' holes, its rear edge rounded r 1.5 (rows at 0.3, 0.8, 1.5 mm)
    from scipy.spatial import cKDTree
    dense = _hull_outline(pts, 900)
    tree = cKDTree(dense)
    holes = [circle(rw, 40, *c) for (c, rb, rw) in SW_BTN.values()]

    def to3d(a, u, w):
        d = tree.query([a, u])[0]
        r = 0.0015
        dr = r - math.sqrt(max(r * r - (r - min(d, r)) ** 2, 0.0)) if w > 0 else 0.0
        return P(a, u) + (w - 0.0015 - dr) * nf
    m.add(_outward(plate2d(face, holes, 0.003, hs, to3d, step=0.0012, rings=(0.0003, 0.0008, 0.0015))))
    # body (the front shell), 0.3 mm inside the rear shell's outline (the parting line), front edge rounded
    body = _inset(face, 0.0003)
    body[:, 0] = np.maximum(body[:, 0], 0.1228)            # inboard of the grip's flange (a 122)
    rings = []
    for f, k in ((SW_FRONT, 0.0012), (SW_FRONT - 0.0004, 0.00045), (SW_FRONT - 0.0012, 0.0)):
        rings.append(np.array([s.p(a, f, u) for a, u in _inset(body, k)]))
    rings.append(np.array([P(a, u) - 0.0025 * nf for a, u in body]))
    m.add(_outward(grid(Mesh(), rings, hs, cap0=True, cap1=True)))
    hs = "plastic_black"                                    # wells, rib, bezels: the darker gloss of REAR's rings
    # wells (a dished ring with a raised lip) and the buttons with their engraved symbols
    mats = {"m": "sw_m", "tc": "sw_tc", "stop": "sw_stop"}
    for key, (c, rb, rw) in SW_BTN.items():
        o = P(*c)
        prof = [(rw + 0.0002, -0.0030), (rw + 0.0002, -0.0002), (rw, 0.0003), (rw - 0.0006, 0.0004),
                (rw - 0.0012, 0.0), (rb + 0.0018, -0.0019), (rb + 0.0008, -0.0025), (rb + 0.0003, -0.0026)]
        m.add(rev(o, nf, prof, hs, 48, cap1=True, ref=up))
        m.add(_button(o, nf, up, right, rb, -0.0027, 0.0012, mats[key]))
    # the guard rib round the stop button's outboard side (DR06: a curved rib in a groove)
    c, rb, rw = SW_BTN["stop"]
    ang = np.linspace(math.radians(118), math.radians(232), 14)
    path = [P(c[0] + (rw + 0.0016) * math.cos(t), c[1] + (rw + 0.0016) * math.sin(t)) + 0.0002 * nf for t in ang]
    m.add(tube(np.array(path), 0.0006, 8, hs))
    # LED lenses in raised bezels (DET829: clear, rounded; REAR: blue-grey)
    for c in SW_WIN:
        o = P(*c)
        for (w_, h_, r_), z0, z1, mat in (((0.0076, 0.0106, 0.0024), -0.0005, 0.0005, hs),
                                          ((0.0060, 0.0090, 0.0018), 0.0, 0.0008, "led_lens")):
            loop = rounded_rect(w_, h_, r_, 4)
            m.add(slab(loop, z0, z1, mat, lambda x, y, h, o=o: o + x * right + y * up + h * nf, ch=0.0002))
    # chamfer slot (DET829): a dark slot 5 x 1.2 mm on the chamfer, 7 mm ahead of the face
    q0, q1 = np.array(SW_POLY[0]), np.array(SW_POLY[1])
    mid = q0 + 0.40 * (q1 - q0)
    nc = unit(s.p(mid[0], -0.030, mid[1]) - s.p(mid[0] + 0.001, -0.030, mid[1] - 0.001))   # outward on the chamfer
    along = unit(s.p(q1[0], -0.03, q1[1]) - s.p(q0[0], -0.03, q0[1]))
    ctr = s.p(mid[0], SW_FACE_F + math.tan(SW_TILT) * mid[1] + 0.007, mid[1]) + 0.0001 * nc
    m.add(box(ctr, (0.0050, 0.0012, 0.0006), "rubber_black", np.column_stack([along, s.f, np.cross(along, s.f)])))
    # raised pad on the top with its arrow mark (TOP)
    (pa, pf), (la, lf) = SW_PAD
    top = 0.0333
    m.add(slab(rounded_rect(la, lf, 0.002, 4), top - 0.0006, top + 0.0005, "sw_body",
               lambda x, y, h: s.p(pa + x, pf + y, h), ch=0.0003))
    tri_ = [(-0.003, -0.0005), (0.003, -0.0005), (0.0, 0.0035)]
    m.add(slab(tri_, top + 0.0004, top + 0.0008, "sw_body", lambda x, y, h: s.p(pa + x, pf + y, h), ch=0.0001))
    # collar round the bar and the block's upper front over it (holder 3)
    a0, a1, rc = SW_COLLAR
    rb_ = BAR_R[1] + 0.0003
    m.add(rev(s.T, -s.d, [(rb_, a0), (rc - 0.0008, a0), (rc, a0 + 0.0008), (rc, a1 - 0.0008), (rc - 0.0008, a1),
                          (rb_, a1)], hs, 48, solid=True))
    m.add(_block(s, 0.1400, 0.1600, 0.0160, 0.0185, "sw_body", cf=-0.0095, cu=0.0238, r=0.0025, ch=0.001))
    # lead: a grommet block on the front-top outboard corner (lf34: a black bracket there, the lead dropping from its
    # front in front of the bar; DET829: a dark block with a hole behind the chamfer's top), the lead out of its front,
    # down in front of the bar and into the run under the bar (TOP: its front at a 138, f 14)
    m.add(_block(s, 0.1275, 0.1395, 0.0125, 0.0180, "sw_body", cf=-0.0100, cu=0.0215, r=0.002, ch=0.0008))
    m.add(cyl(s.p(0.1335, -0.0040, 0.0245), s.p(0.1335, 0.0035, 0.0245), 0.0036, "rubber_black", 16, 0.0006))
    return m


def switch_leads():
    """The two switches' leads (in the bars' part: they run under the bar into the bar pad): the left one from its
    grommet's front over the bar's front and down into the run under the bar, the start switch's from its box's
    front under the bar; each ends 0.5 mm inside the face it enters."""
    m = Mesh()
    m.add(_wire(_Side(1), 0.160, 0.0, 0.0, loop=[(0.140, 0.006, -0.0218), (0.1365, 0.0165, -0.0150),
                                                 (0.1345, 0.0215, -0.0010), (0.1338, 0.0205, 0.0140),
                                                 (0.1335, 0.0140, 0.0235), (0.1335, 0.0060, 0.0245),
                                                 (0.1335, 0.0030, 0.0245)]))
    s = _Side(-1)
    e = s.p(*SS_C) + np.array([SS_DEPTH - 0.0004, 0.0, 0.0]) + 0.0002 * s.d - 0.0080 * Z    # 0.4 mm into the box's
    ends = []                                                                                # front face, square to it
    for p in (e + np.array([0.006, 0.0, 0.0]), e + np.array([0.003, 0.0, 0.0]), e):
        q = p - s.T
        ends.append((-(q @ s.d), q @ s.f, q @ s.u))
    m.add(_wire(s, 0.160, 0.0, 0.0, loop=[(0.172, -0.004, -0.0215), (0.1690, -0.0120, -0.0200)] + ends))
    return m


SS_C = (0.1617, -0.0392, -0.0069)   # start switch: centre of its guard frame's rear face (a, f, u, right grip frame):
#   REAR (2302.5, 256.5) + TOP (1805, 848.5), residual 0.2 px, then 3 mm outboard after the pairs (REAR 2..4 px, TOP
#   the box's middle at row 844.6, not 848.5); the face is square to the bike (TOP: its rear edge runs from a 153.7
#   f -36.7 to a 174.7 f -42.7, 16 deg off the grip)
SS_FRAME = ((0.0185, 0.0200), (0.0125, 0.0130))   # guard frame outer and opening (across, tall): REAR corners cast
#   on f -30 (a 158.3..176.7, u -17.0..+3.3: 18.4 x 20.3), triangulated 155.2..173.8 / -17.1..+3.2; the opening from
#   DET830's proportions (165 / 240 px of the frame)
SS_BTN = 0.0075               # square button, DET830: 90 / 240 px of the frame -> 6.9 mm, REAR 9.6 x 8.8 (blurred)
SS_DEPTH = 0.0120             # box from the frame's face forward: TOP pair, the box 13 px (11.3 mm) deep along x; the
#   mount reaches on to the bar
SS_MOUNT = (0.1680, 0.1810)   # the box's mount and strap round the bar (holder 5): REAR's dark block inboard of the
#   frame, cast a 182..185 at f -30 (a 175..181 nearer the bar), clear of the master cylinder's clamp (a 182)


def _square_button(c, nb, up, right, w, h0, h1, mat):
    """Rounded square push button from h0 to h1 along NB, its top's UVs over the button's width."""
    m = Mesh()
    sq = rounded_rect(w, w, w * 0.16, 4)
    prof = [(1.0, h0), (1.0, h1 - 0.0004), (0.96, h1 - 0.0001), (0.90, h1)]
    base = [m.verts([c + h * nb + k * (q[0] * right + q[1] * up) for q in sq]) for k, h in prof]
    n = len(sq)
    for kk in range(len(prof) - 1):
        for i in range(n):
            j = (i + 1) % n
            fi = len(m.F)
            m.face((base[kk] + i, base[kk] + j, base[kk + 1] + j, base[kk + 1] + i), mat)
            m.uv[fi] = [(0.5, 0.03)] * 4
    cen = m.verts([c + h1 * nb])
    k = prof[-1][0]
    for i in range(n):
        j = (i + 1) % n
        fi = len(m.F)
        m.face((base[-1] + i, base[-1] + j, cen), mat)
        m.uv[fi] = [(0.5 + k * sq[i][0] / w, 0.5 + k * sq[i][1] / w), (0.5 + k * sq[j][0] / w, 0.5 + k * sq[j][1] / w),
                    (0.5, 0.5)]
    return _outward(m)


def switch_start():
    """Start switch on the right bar, between the throttle housing and the master cylinder (DET830, REAR, TOP): a
    black box behind the bar with its face square to the bike, the raised guard frame round the recessed square
    button (start symbol), the guard's top bar standing further out as a hood, a cross-head screw under the box,
    the mount and strap round the bar (holder 5), and the lead forward under the bar."""
    s = _Side(-1)
    m = Mesh()
    hs = "sw_body"
    c = s.p(*SS_C)
    nb, up = np.array([-1.0, 0.0, 0.0]), Z.copy()             # out of the face (towards the rider), up
    right = np.cross(up, nb)                                  # the rider's right (outboard): -y
    to = lambda x, y, h: c + x * right + y * up + h * nb
    # box: from 5 mm inside the frame's face forward SS_DEPTH, rounded r 2.5, its edges 1.2 mm
    m.add(slab(rounded_rect(0.0210, 0.0290, 0.0025, 4), -SS_DEPTH, -0.0050, hs,         # its top 8 mm over the
               lambda x, y, h: to(x, y + 0.0035, h), ch=0.0012))                       # frame's (REAR pair)
    # guard frame: a square ring standing 5 mm out of the box (DET830: its walls deep round the sunken button), its top
    # bar a hood 2 mm further out
    (ow, oh), (iw, ih) = SS_FRAME
    outer, inner = rounded_rect(ow, oh, 0.0022, 4), rounded_rect(iw, ih, 0.0015, 4)
    m.add(_outward(plate2d(outer, [inner], 0.0054, hs, lambda x, y, w: to(x, y, w - 0.0025), step=0.0010)))
    m.add(slab(rounded_rect(ow, oh / 2 - ih / 2 + 0.0004, 0.0012, 3), -0.0003, 0.0020, hs,
               lambda x, y, h: to(x, y + oh / 4 + ih / 4, h), ch=0.0006))
    # the recess floor and the button with the start symbol, 3 mm inside the frame's face
    m.add(slab(rounded_rect(iw + 0.0004, ih + 0.0004, 0.0015, 3), -0.0052, -0.0046, "plastic_black", to, ch=0.0))
    m.add(_square_button(c - 0.0005 * up, nb, up, right, SS_BTN, -0.0048, -0.0030, "sw_start"))
    # cross-head screw under the box (REAR: a bright head under the frame's right half), M4, EST length
    p = to(-0.0020, -0.0108, -0.0080)
    m.add(fastener(p, -Z, "button", af=0.0070, h=0.0022, recess=0.0028, mat="steel"))
    # mount from the box's inboard front to a strap round the bar (holder 5)
    a0, a1 = SS_MOUNT
    m.add(_block(s, a0, a1, 0.0170, 0.0150, hs, cf=-0.0200, cu=-0.0040, r=0.003, ch=0.001))
    m.add(rev(s.T, -s.d, [(BAR_R[1] + 0.0003, a0 + 0.0045), (0.0140, a0 + 0.0045), (0.0145, a0 + 0.0050),
                          (0.0145, a1 - 0.0005), (0.0140, a1), (BAR_R[1] + 0.0003, a1)], hs, 40, solid=True))
    return m


THROTTLE_F = (-0.005, 0.005)                          # the two cables leave side by side over the bar, EST


def _throttle_start(k):
    return _Side(-1, CTRL_SHIFT[1]).p(0.168, THROTTLE_F[k], 0.029)


def _hose_start():
    """Where the hose leaves the banjo's fitting (master_cylinder)."""
    return _mc_banjo()[2]


# ================================================================ front brake
CAL_C = FA + np.array([-0.120, 0.0, 0.004])           # LEFT: caliper box u 1174..1252, v 1550..1654 (by eye, 10 mm)
E_Q = unit((CAL_C - FA) * [1, 0, 1])                  # radial, away from the axle (rearwards)
E_W = np.cross(Y, E_Q)                                # along the disc's rim, upwards


def cal(q, w, y):
    return CAL_C + q * E_Q + w * E_W + y * Y


def _banjo():
    return cal(0.0515, -0.012, 0.088)


def hose_path():
    """Front brake hose, master cylinder to caliper. FRONT ("hose" scan): crosses the centre line at z 1.193, over
    the plate's left half to y 0.089 at z 1.064, then straight down at y 0.088..0.090 to the guide on the fork
    guard (rows 1014..1054, y 0.097..0.108), inboard of the leg below it (y 0.047 at z 0.53). LEFT across: 64 to
    75 mm ahead of the tube axis at t 0.42..0.76. LEFT by eye (10 mm): the loop behind the leg down to the banjo."""
    b = _banjo()
    pts = [_hose_start(), fyz(0.078, -0.170, 1.208), fyz(0.088, -0.125, 1.224), fyz(0.090, -0.085, 1.222),
           fyz(0.088, -0.030, 1.208), fyz(0.086, 0.000, 1.193), fyz(0.084, 0.028, 1.1785), fyz(0.082, 0.0535, 1.150),
           fyz(0.080, 0.0685, 1.1215), fyz(0.078, 0.079, 1.0925), fyz(0.075, 0.0885, 1.064), fyz(0.072, 0.0895, 1.028),
           fk(0.072, 0.088, 0.740), fk(0.072, 0.088, 0.670), fk(0.070, 0.089, 0.550), fk(0.068, 0.092, 0.440),
           fk(0.066, 0.096, 0.385), fk(0.064, 0.080, 0.340), fk(0.062, 0.062, 0.300), fk(0.050, 0.052, 0.265),
           fk(0.020, 0.051, 0.235), fk(-0.020, 0.054, 0.213), (1.2964, 0.065, 0.4457), (1.2887, 0.078, 0.3958),
           b + 0.028 * E_W, b + 0.010 * E_W]
    return spline(pts, 230)


def front_brake():
    """Brake hose with its sleeve and two guides, Nissin two-piston caliper (30 and 27 mm, SPEC) on its bracket
    behind the left leg, pads, slide pins, bleed nipple, banjo."""
    m = Mesh()
    q = hose_path()
    m.add(tube(q, 0.0045, 10, "cable"))
    t = (q - TUBE0) @ UP
    sl = q[(t > 0.725) & (t < 0.82) & (q[:, 1] > 0.08)]              # FRONT rows 530..610: black 8 mm wide (sleeve)
    m.add(tube(sl, 0.0062, 10, "rubber_black"))
    # guide under the lower clamp (FRONT rows 610..640, LEFT (1445, 815)): stay off the left boss, rubber grommet
    m.add(box(fk(0.0475, 0.090, 0.670), (0.036, 0.003, 0.012), "steel", RF))
    m.add(cyl(fk(0.072, 0.088, 0.661), fk(0.072, 0.088, 0.679), 0.0085, "rubber_black", 16, 0.0015))
    # guide on the fork guard (FRONT rows 1014..1054; LEFT bolts (1244, 1170) and (1236, 1189))
    m.add(box(fk(0.0585, 0.108, 0.384), (0.003, 0.030, 0.026), "steel", RF))
    for tb in (0.376, 0.392):
        m.add(bolt(fk(0.060, 0.114, tb), FWD, af=0.008))
    m.add(cyl(fk(0.066, 0.096, 0.372), fk(0.066, 0.096, 0.396), 0.0085, "rubber_black", 16, 0.0015))
    # ---- caliper (DET 475831). Disc at y 0.0605..0.0635 out to r 0.130 (wheel): pads either side, bridge beyond
    c = "caliper"
    m.add(slab(rounded_rect(0.052, 0.082, 0.014, 5), 0.071, 0.099, c, lambda p, w, h: cal(0.005 + p, w, h), 0.002))
    for w, r in ((0.0195, 0.0195), (-0.0195, 0.0180)):               # 30 and 27 mm pistons
        m.add(cyl(cal(-0.004, w, 0.097), cal(-0.004, w, 0.106), r, c, 24, 0.003))
    m.add(slab(rounded_rect(0.016, 0.070, 0.005, 3), 0.046, 0.099, c, lambda p, w, h: cal(0.022 + p, w, h)))
    m.add(slab(rounded_rect(0.050, 0.060, 0.010, 4), 0.046, 0.055, c, lambda p, w, h: cal(0.006 + p, w, h)))
    for y0, y1 in ((0.0645, 0.0712), (0.0548, 0.0595)):              # pads
        m.add(slab(rounded_rect(0.034, 0.054, 0.006, 3), y0, y1, "anod_black", lambda p, w, h: cal(-0.011 + p, w, h),
                   0.0005))
    # bracket: plate from the lug's two ears to the slide pins above and below the body
    pins = [cal(0.004, 0.049, 0.0), cal(0.004, -0.049, 0.0)]
    ears = [fk(f, 0.0, t) for f, t in CAL_EARS]
    pts = np.vstack([circle(0.009, 16, p[0], p[2]) for p in ears] + [circle(0.009, 16, p[0], p[2]) for p in pins])
    hull = pts[ConvexHull(pts).vertices]
    m.add(slab(hull, 0.0745, 0.0825, c, lambda x, z, h: np.array([x, h, z]), 0.001))
    for p in ears:
        m.add(bolt([p[0], 0.105, p[2]], Y, af=0.010, flange_d=0.016))
    for p in pins:
        m.add(cyl([p[0], 0.0825, p[2]], [p[0], 0.099, p[2]], 0.0065, "rubber_black", 14, 0.001))
        m.add(bolt([p[0], 0.099, p[2]], Y, af=0.010, head_h=0.004, flange_d=0.011))
    nb = unit(0.9 * E_W + 0.3 * E_Q)                                 # bleed nipple with its rubber cap
    p0 = cal(0.020, 0.040, 0.090)
    m.add(bolt(p0, nb, af=0.008, head_h=0.004, flange_d=0.009, mat="steel"))
    m.add(cyl(p0 + 0.004 * nb, p0 + 0.011 * nb, 0.0028, "steel", 10))
    m.add(cyl(p0 + 0.008 * nb, p0 + 0.015 * nb, 0.0042, "rubber_black", 10, 0.0008))
    # banjo on the body's rear, hose entering from above through a steel stub
    b = _banjo()
    m.add(cyl(cal(0.029, -0.012, 0.088), cal(0.047, -0.012, 0.088), 0.008, c, 14, 0.001))
    m.add(cyl(cal(0.047, -0.012, 0.088), cal(0.056, -0.012, 0.088), 0.0085, "steel", 16, 0.001))
    m.add(bolt(cal(0.056, -0.012, 0.088), E_Q, af=0.012, head_h=0.006, flange_d=0.015))
    m.add(cyl(b, b + 0.024 * E_W, 0.0040, "steel", 10))
    return m


# ================================================================ disc cover
def disc_guard():
    """Black plastic cover outside the front disc (DET 475831, LEFT u 960..1110, v 1440..1600): a plate just outside
    the disc with a honeycomb window in its upper front, solid below, a fin towards the rear under the caliper, a
    hub that steps out over the axle lug to the axle nut. Open where the fork leg and the caliper are. Outline in
    axle-centred fork coordinates (g ahead, t up the fork); radii and the window's extent are EST."""
    m = Mesh()
    yp, r0, rh = 0.0865, 0.143, 0.060
    a_top = math.atan2(math.sqrt(r0 ** 2 - 0.006 ** 2), 0.006)       # edge 6 mm ahead of the fork guard's front
    a_fin = math.radians(-161.75)                                    # 135 deg below the horizontal, behind
    out = [(r0 * math.cos(a), r0 * math.sin(a)) for a in np.linspace(a_top, a_fin + math.radians(16), 64)]
    out.append((0.160 * math.cos(a_fin + math.radians(5)), 0.160 * math.sin(a_fin + math.radians(5))))   # fin tip
    out.append((0.096 * math.cos(a_fin), 0.096 * math.sin(a_fin)))
    a_in = math.atan2(-0.030, -math.sqrt(rh ** 2 - 0.030 ** 2))      # inner edge 8 mm under the lug's socket
    out += [(rh * math.cos(a), rh * math.sin(a)) for a in np.linspace(a_in, math.radians(80), 40)]
    holes = []
    pitch, rhex = 0.0135, 0.0052
    for i in range(-2, 14):
        for j in range(0, 14):
            g, t = i * pitch + (pitch / 2 if j % 2 else 0.0), j * pitch * 0.866
            if rh + 0.012 < math.hypot(g, t) < r0 - 0.012 and g > 0.026 and t > 0.012:
                holes.append(circle(rhex, 6, g, t))
    m.add(_outward(plate2d(np.array(out), holes, 0.003, "plastic_black",
                  lambda g, t, w: FA + g * FWD + t * UP + (yp + w) * Y, step=0.009)))
    arc = lambda a0, a1: (-math.radians(a1), -math.radians(a0))      # fork angles to rev's (which runs clockwise)
    # hub: cone from the plate out over the lug, face round the axle nut (3 mm wall)
    hub = [(rh, yp + 0.0015), (0.050, 0.127), (0.046, 0.1315), (0.041, 0.1335), (0.0135, 0.1335),
           (0.0135, 0.1305), (0.0395, 0.1305), (0.0435, 0.129), (0.047, 0.125), (rh - 0.003, yp - 0.0015)]
    m.add(rev(FA, Y, hub, "plastic_black", 56, ref=FWD, arc=arc(-135, 80), solid=True))
    # rim lip towards the wheel, rib on the solid part
    lip = [(r0 - 0.0005, yp + 0.0015), (r0 + 0.0025, yp + 0.0005), (r0 + 0.0025, 0.0765), (r0 + 0.0005, 0.0755),
           (r0 + 0.0005, yp - 0.0015), (r0 - 0.0005, yp - 0.0015)]
    m.add(rev(FA, Y, lip, "plastic_black", 72, ref=FWD,
              arc=arc(math.degrees(a_fin) + 16, math.degrees(a_top)), solid=True))
    rib = [(0.104, yp + 0.0014), (0.1025, yp + 0.0034), (0.0985, yp + 0.0034), (0.097, yp + 0.0014)]
    m.add(rev(FA, Y, rib, "plastic_black", 48, ref=FWD, arc=arc(-150, 2)))
    for a in (35, -75):                                              # screws on the hub face (DET: two visible)
        c = FA + 0.028 * (math.cos(math.radians(a)) * FWD + math.sin(math.radians(a)) * UP) + 0.1335 * Y
        m.add(bolt(c, Y, af=0.008))
    return m


# ================================================================ cables that run on to the frame
CLUTCH_JOIN = np.array([0.790, 0.074, 0.800])         # upper end of the cable that detail_engine draws up from the
#   clutch release arm on the LEFT crankcase cover. Its route down to the arm is detail_engine.CLUTCH_CABLE

def _engine(name):
    """A cable anchor of the engine module; None until it defines one (CLUTCH_ARM_END, THROTTLE_DRUM)."""
    try:
        import detail_engine
        v = getattr(detail_engine, name, None)
        return None if v is None else np.asarray(v, float)
    except Exception:
        return None


def throttle_end():
    """Where the throttle cables end: on top of the drum on the right of the throttle body (detail_engine: centre
    TB0 + 0.062 TB_DIR, 38 mm right of the bore's axis, radius 19 mm), lying on it 0.3 mm clear."""
    drum = _engine("THROTTLE_DRUM")
    if drum is not None:
        return drum + np.array([0.0, 0.0, 0.0038])
    try:
        import detail_engine as de
        mid = de.TB0 + 0.062 * de.TB_DIR
        return np.array([mid[0], -(de.TB_BORE / 2 + 0.016), mid[2] + 0.019 + 0.0038])
    except Exception:
        return np.array([0.7047, -0.038, 0.7618])


def clutch_path():
    """Clutch cable, perch adjuster to the engine: past the plate's left corner, across the front of the pad's left end (FRONT row 270: black at y 0.080..0.089,
    z 1.193), down behind the plate, between the
    left tube and the head, down the left of the steering head (LEFT by eye: (0.996, 1.10) to (1.019, 1.04), with
    the in-line adjuster), then under the tank's left edge to the upper end of the engine module's own cable
    (CLUTCH_JOIN), or all the way to detail_engine.CLUTCH_ARM_END once that exists."""
    a0, ad = _clutch_adjuster()
    arm = _engine("CLUTCH_ARM_END")
    w = unit(np.array([0.815, 0.074, 0.795]) - CLUTCH_JOIN)
    route = _engine("CLUTCH_CABLE")                      # the engine module's own route, from CLUTCH_JOIN to its last guide
    tail = [CLUTCH_JOIN + 0.0025 * w] if arm is None or route is None else [CLUTCH_JOIN] + [tuple(p) for p in route[1:]] + [arm]
    pts = [a0 + 0.0006 * ad, a0 + 0.016 * ad, a0 + 0.034 * ad,            # leaves along the adjuster
           (1.058, 0.118, 1.190), fk(0.041, 0.095, 0.972),
           fk(0.042, 0.072, 0.968), fk(0.043, 0.060, 0.945), fk(0.040, 0.057, 0.915), fk(0.034, 0.056, 0.880), fk(0.006, 0.052, 0.858), fk(-0.038, 0.052, 0.853),
           fk(-0.054, 0.054, 0.800), fk(-0.056, 0.056, 0.740), (1.030, 0.057, 0.904), (0.991, 0.062, 0.875),
           (0.951, 0.068, 0.849), (0.909, 0.075, 0.824), (0.866, 0.077, 0.801), (0.815, 0.074, 0.795)] + tail
    return spline(pts, 190)


def throttle_paths():
    """The two throttle cables, housing elbows to the drum. FRONT (bars_front, refitted camera): a cable crosses
    over the front of the bar pad from the throttle side, z 1.241 at y -0.18 falling to 1.200 at y 0.086, into
    the cable loop on the plate's left; then under the bar, down behind the steering head ahead of the tank and
    back under the tank to the drum. They leave the elbows along the bar, behind the master cylinder's reservoir
    (FRONT col 1710: nothing black above or ahead of the reservoir). One centre line; the pair rides either side
    of it on a frame carried along the path (always square to it, so the cables stay 7.6 mm apart), turned
    evenly along the way so that they arrive side by side across the drum."""
    end = throttle_end()
    sd = _Side(-1)
    b = throttle_boot_end()                          # out of the boot along the top-rear of the bar (TOP, DET830),
    pts = [b + 0.0055 * (-sd.d), sd.p(BOOT[1] + 0.022, -0.006, 0.0372), sd.p(0.240, -0.018, 0.0360),
           sd.p(0.255, -0.026, 0.0352), sd.p(0.282, -0.032, 0.0345),    # level out of the boot (REAR), behind the
           fk(-0.075, -0.098, 0.985),                                    # reservoir (TOP: ferrule 30 mm behind at a 255) (0.972, -0.075, 1.120),   # down behind the pad's
           (0.976, -0.040, 1.103), (0.986, -0.010, 1.045), (0.995, 0.000, 0.974),             # right end (TOP, DET835),
           (0.995, 0.003, 0.907),                                     # close behind the top clamp, ahead of the tank
           (0.996, -0.006, 0.840), (0.953, -0.019, 0.805), (0.902, -0.028, 0.784), (0.845, -0.031, 0.783),
           (0.789, -0.035, 0.781), end + np.array([0.030, 0.0, 0.004]), end]
    c = spline(pts, 260)
    t = np.gradient(c, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = [unit(sd.f - (sd.f @ t[0]) * t[0])]                         # the elbows sit one ahead of the other
    for i in range(1, len(c)):
        n.append(unit(n[-1] - (n[-1] @ t[i]) * t[i]))
    n = np.array(n)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))])
    bn = np.cross(t[-1], n[-1])
    turn = min((math.atan2(sgn * (Y @ bn), sgn * (Y @ n[-1])) for sgn in (1, -1)), key=abs)
    ang = turn * arc / arc[-1]
    n = np.cos(ang)[:, None] * n + np.sin(ang)[:, None] * np.cross(t, n)
    g = np.interp(arc, [0.0, 0.020, 0.030, 0.090, 0.120], [THR_GAP, THR_GAP, 0.0050, 0.0050, THR_GAP])[:, None]
    return [c - g * n, c + g * n]                # they part round the pull cable's adjuster (DET830)


THR_GAP = 0.0038              # the two throttle cables' centres either side of their common line (7 mm cables)
THR_ADJ = (0.032, 0.044, 0.048, 0.082)   # along the pull cable from the boot (m): crimped ferrule, lock nut, ribbed
#   adjuster body: DET830 ferrule 60 px and adjuster 180 px where the 41 mm boot is 200 px, 32 mm out of the boot


def cables():
    """Clutch cable and the two throttle cables: they start on the bar's fittings and end on the engine, so they
    do not turn with the steering. Below the steering head their control points were pushed away from the nearest
    surface of the merged model (frame, tank, radiators, engine) until the paths cleared it by 10 mm or more."""
    m = Mesh()
    q = clutch_path()
    m.add(tube(q, 0.0040, 8, "cable"))
    i = int(np.argmin(np.linalg.norm(q - fk(-0.054, 0.054, 0.800), axis=1)))
    d = unit(q[i + 1] - q[i - 1])
    m.add(cyl(q[i] - 0.016 * d, q[i] + 0.016 * d, 0.0058, "steel", 12, 0.001))          # in-line adjuster
    m.add(cyl(q[i] + 0.016 * d, q[i] + 0.030 * d, 0.0052, "rubber_black", 10, 0.001))
    for k, q in enumerate(throttle_paths()):
        m.add(tube(q, 0.0035, 8, "cable"))
        if k == 1:                                       # the pull cable's in-line adjuster (DET830)
            arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))])
            at = lambda d: np.array([np.interp(d, arc, q[:, j]) for j in range(3)])
            f0, f1, n0, a1 = THR_ADJ
            p0, p1 = at(f0), at(f1)
            m.add(cyl(p0, p1, 0.0042, "alu_machined", 16, 0.0006))                       # bright crimped ferrule
            m.add(fastener(at(f1), at(n0) - at(f1), "hex", af=0.010, h=n0 - f1, mat="anod_black"))   # lock nut
            ax = unit(at(a1) - at(n0))
            prof = [(0.0040, 0.0)]
            for i in range(7):                                                          # knurled ribs
                z = 0.003 + i * (a1 - n0 - 0.006) / 6
                prof += [(0.0053, z - 0.0012), (0.0058, z - 0.0005), (0.0058, z + 0.0005), (0.0053, z + 0.0012)]
            prof += [(0.0050, a1 - n0 - 0.001), (0.0040, a1 - n0)]
            m.add(rev(at(n0), ax, prof, "anod_black", 16))
    return m


PARTS = {"fork": fork, "clamps": clamps, "bars": bars, "hand_controls": hand_controls, "front_brake": front_brake,
         "disc_guard": disc_guard, "cables": cables}
REPLACES = ["fork", "clamps", "bars", "cables", "disc_guard"]
FRONT_END = ["fork", "clamps", "bars", "hand_controls", "front_brake", "disc_guard"]
MATERIALS = {"bar_knurl": dict(rgb=(20, 20, 22), metal=0.6, rough=0.45, normal="stock/bar_knurl_n.png",
                           normal_strength=0.8),        # the Fatbar's clamping zones (BAR_KNURL)
             "bolt_black": dict(rgb=(28, 28, 30), metal=0.8, rough=0.35),     # black-finished screws (DET830)
             "mc_cast": dict(rgb=(168, 168, 170), metal=1.0, rough=0.55),     # Nissin cast body, satin (DET830, rf34)
             "mc_cap": dict(rgb=(118, 118, 122), metal=0.7, rough=0.45),      # the cap a shade darker (TOP, rf34)
             "mc_nissin": dict(rgb=(168, 168, 170), metal=1.0, rough=0.55, normal="stock/mc_nissin_n.png"),
             "mc_lwr": dict(rgb=(168, 168, 170), metal=1.0, rough=0.55, normal="stock/mc_lwr_n.png"),
             "glass_dark": dict(rgb=(30, 24, 16), rough=0.05),                # sight lens, fluid behind it
             "btn_red": dict(rgb=(200, 22, 26), rough=0.4), "btn_blue": dict(rgb=(24, 70, 190), rough=0.4),
             "btn_green": dict(rgb=(20, 140, 60), rough=0.4), "pad_cap": dict(rgb=(58, 58, 62), rough=0.65),
             "grip_rubber": dict(rgb=(24, 24, 26), rough=0.55, bump=0.12),      # satin black rubber (DR06, DET829)
             "grip_bead": dict(rgb=(26, 26, 28), rough=0.22),       # the rings' beads shine as thin lines (DR05, DR06)
             # switch buttons: colour and engraved symbol (switch_maps); base colours from the REAR photo's lit
             # buttons (blue 45 103 194, green 40 159 86, red 207 64 65) darkened to the render's studio light
             "sw_m": dict(rgb=(35, 88, 190), rough=0.45, image="stock/sw_m.png", normal="stock/sw_m_n.png"),
             "sw_stop": dict(rgb=(205, 50, 50), rough=0.45, image="stock/sw_stop.png", normal="stock/sw_stop_n.png"),
             "sw_tc": dict(rgb=(32, 150, 72), rough=0.45, image="stock/sw_tc.png", normal="stock/sw_tc_n.png"),
             "sw_start": dict(rgb=(26, 26, 28), rough=0.5, image="stock/sw_start.png",
                              normal="stock/sw_start_n.png"),
             "led_lens": dict(rgb=(40, 52, 66), rough=0.05, spec=1.0),    # smoky lens: REAR (studio) blue-grey 90 117
             #   142 from the reflection, DR06 dark, DET829 clear over a light diffuser
             "sw_body": dict(rgb=(26, 26, 28), rough=0.62, bump=0.08)}    # textured matte switch housing (DR06)
CLASS = {"glass_dark": "black", "bolt_black": "black", "bar_knurl": "black", "btn_red": "black", "btn_blue": "black", "btn_green": "black", "pad_cap": "black", "grip_rubber": "black",
         "grip_bead": "black", "sw_m": "black", "sw_stop": "black", "sw_tc": "black", "sw_start": "black",
         "led_lens": "black", "sw_body": "black"}
SMOOTH = {"fork": 40, "clamps": 40, "bars": 40, "hand_controls": 40, "front_brake": 40, "disc_guard": 40, "cables": 60}
# bar pad's texture: "RENTHAL" on its front and rear faces, each read from its own side (FRONT and REAR photos)
UV = {"barpad": dict(centre=[float(PAD_C[0]), float(PAD_C[2])], half=list(PAD_HALF), y_half=PAD_Y[1],
                     tilt=float(PAD_TILT))}


if __name__ == "__main__":
    import os
    stock = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textures", "stock")
    knurl_map(os.path.join(stock, "bar_knurl_n.png"))
    switch_maps(stock)
    mc_maps(stock)
