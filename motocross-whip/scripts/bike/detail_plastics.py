"""Plastics, second pass: the parts that hang on the panels of plastics.py (plugin of parts.py).

  fork_guards     the guards over the lower fork legs: outer wall with its slots, rounded front with a ridge, inner wall
  guard_hardware  their mounting bolts and the brake hose clamp on the left guard
  tail_under      the red wall under the tail with its two channels, bosses and bolts (rear photo)
  shroud_bolts, seat_bolts, panel_bolts   the 8 body bolts (SPEC: 8 bolts, 8 mm heads, hold both shrouds, both side
                  panels and the seat), each in its collar with the boss that reaches inward to what it fixes to
  plate_details   the number plate's mounts (boss behind the bolt pocket, two pegs to the lower clamp) and hose guide
The front fender sits on the bosses of detail_front's lower clamp (its shell is under its surface: plastics.py).

Tags as in parts.py and plastics.py: LEFT/RIGHT/FRONT/REAR/TOP photo pixels, SPEC, EST.
"""
import math
import os

import numpy as np
from PIL import Image

import cams
import plastics
import parts as P
from geom import Mesh, bolt, box, grid, inside, lathe, rounded_rect, smooth_poly, tube

LEFT, FRONT, REAR, TOP = (cams.CAMS[k] for k in ("left", "front", "rear", "top"))
_UP2 = np.array([P.UP[0], P.UP[2]])
_FWD2 = np.array([-P.BACK[0], -P.BACK[2]])
_T02 = np.array([P.TUBE0[0], P.TUBE0[2]])


# ---------------------------------------------------------------- fork guards
GUARD_OUT = 0.131                      # FRONT rows 1012..1428: outer edge 131 mm off the centre line all the way down
GUARD_IN_T, GUARD_IN = [0.07, 0.30, 0.385], [0.068, 0.064, 0.058]       # FRONT: inner edge 58 mm (top) to 68 mm


def _guard_profile():
    """Front and rear edge of the guard's outer wall along the fork (t from the axle, offsets forward of the tube
    axis): the outline of the left photo (OUT 'fork_guard') cast onto the wall's plane."""
    rel = P.PO("fork_guard", GUARD_OUT) - _T02
    t, off = rel @ _UP2, rel @ _FWD2
    ts = np.linspace(t.min() + 0.003, t.max() - 0.003, 48)
    fr = np.array([off[np.abs(t - q) < 0.012].max() if (np.abs(t - q) < 0.012).any() else np.nan for q in ts])
    rr = np.array([off[np.abs(t - q) < 0.012].min() if (np.abs(t - q) < 0.012).any() else np.nan for q in ts])
    fr = plastics._gauss(np.where(np.isfinite(fr), fr, np.nanmean(fr)), 1.5)
    rr = plastics._gauss(np.where(np.isfinite(rr), rr, np.nanmean(rr)), 1.5)
    return ts, fr, np.minimum(rr, fr - 0.024)


def _guard_slots(ts):
    """The slots in the guard's outer wall: dark, elongated shapes inside its outline in the left photo, in its
    lower 60 % (LEFT, about rows 1377..1520), as polygons in (t, offset)."""
    from scipy import ndimage
    import contourpy
    px = plastics.clean_outline("left", plastics.OUT["fork_guard"], sigma=3.0)
    lo, hi = np.floor(px.min(axis=0)).astype(int), np.ceil(px.max(axis=0)).astype(int)
    im = Image.open(os.path.join(P.HERE, "..", "..", "reference", "crf250r-2026", cams.FILES["left"])).convert("RGB")
    a = np.asarray(im.crop((int(lo[0]), int(lo[1]), int(hi[0]), int(hi[1])))).astype(int)
    uu, vv = np.meshgrid(np.arange(lo[0], hi[0]), np.arange(lo[1], hi[1]))
    ins = inside(px, np.stack([uu.ravel(), vv.ravel()], axis=1).astype(float)).reshape(uu.shape)
    dark = ndimage.binary_opening(ndimage.binary_erosion(ins, iterations=6) & (a.max(axis=2) < 95), iterations=1)
    lab, n = ndimage.label(dark)
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        m = lab[sl] == k
        if not 120 < m.sum() < 2500:
            continue
        yy, xx = np.nonzero(m)
        ev = np.linalg.eigvalsh(np.cov(np.stack([xx, yy]).astype(float)))
        if ev[1] < 5.0 * ev[0]:                                # not elongated
            continue
        c = max(contourpy.contour_generator(z=np.pad(m, 2).astype(float)).lines(0.5), key=len)[:-1]
        W = LEFT.on_plane(lo[0] + sl[1].start + c[:, 0] - 2.0, lo[1] + sl[0].start + c[:, 1] - 2.0, "y", GUARD_OUT)
        rel = W[:, [0, 2]] - _T02
        q = smooth_poly(np.stack([rel @ _UP2, rel @ _FWD2], axis=1)[::2], 2)
        if q[:, 0].mean() < ts[0] + 0.6 * (ts[-1] - ts[0]):
            out.append(q)
    return out


def fork_guards():
    """Guards over the lower fork legs. FRONT (refitted camera, rows 1012..1428): outer edge 131 mm off the centre
    line all the way down, inner edge 58 mm at the top to 68 mm lower down, so each shell reaches further inboard of
    its tube than outboard. Side view from the left photo: the outer wall's front and rear edges (OUT 'fork_guard')
    and its slots. The front is rounded over 16 mm with a ridge near the outer corner (LEFT: a highlight line along
    the guard; 3 mm proud EST); the inner wall runs back to the tube's centre plane (EST). Single surface, 3 mm
    thick in Blender. The right guard is the left one mirrored."""
    ts, fr, rr = _guard_profile()
    slots = _guard_slots(ts)
    f_of = lambda t: float(np.interp(t, ts, fr))
    r_of = lambda t: float(np.interp(t, ts, rr))
    taper = lambda t: 0.004 * (1.0 - min((ts[-1] - t) / 0.03, 1.0))    # the top end closes in a little
    wall = np.array([(t, r_of(t)) for t in ts] + [(t, f_of(t) - 0.014) for t in ts[::-1]])
    holes = [h for h in slots if inside(wall, h).all() and inside(wall, h + np.array([0.0, 0.003])).all()
             and inside(wall, h - np.array([0.0, 0.003])).all()]
    m = Mesh()
    for side in (1, -1):
        def to3d(t, a, w, s=side):
            Q = P.on_tube(t) - P.BACK * a
            return (Q[0], s * (GUARD_OUT - taper(t)), Q[2])
        m.add(plastics.plate_lines(wall, holes, 0.0, "fork_guard", to3d, 0.007, single=True))
        rings = []
        for t in ts:
            f, yo = f_of(t), GUARD_OUT - taper(t)
            yi = float(np.interp(t, GUARD_IN_T, GUARD_IN)) + taper(t)
            sec = [(f - 0.016, yo - 0.0003), (f - 0.010, yo - 0.0015), (f - 0.005, yo - 0.005), (f - 0.0015, yo - 0.011),
                   (f + 0.001, yo - 0.018), (f + 0.003, yo - 0.024), (f + 0.0015, yo - 0.032), (f, yi + 0.022),
                   (f - 0.002, yi + 0.011), (f - 0.006, yi + 0.004), (f - 0.011, yi + 0.001), (f - 0.016, yi),
                   (min(max(r_of(t), 0.0), f - 0.020), yi)]
            if side < 0:
                sec = sec[::-1]
            rings.append(np.array([P.on_tube(t) - P.BACK * a + np.array([0, side * y, 0]) for a, y in sec]))
        m.add(grid(Mesh(), rings, "fork_guard", closed_u=False))
    fork_guards.slots = len(holes)
    return m


def guard_hardware():
    """LEFT: two bolt heads at each guard's lower end (grey blobs centred on px (1094, 1555) and (1132, 1578)); on
    the left guard, at its top, the brake hose clamp (grey block u 1218..1262, v 1144..1188, a second bolt head at
    (1235, 1189)) with the loop the hose runs through (EST). The right guard's bolts are the left one's mirrored."""
    m = Mesh()
    for side in (1, -1):
        for u, v in ((1094.0, 1555.0), (1132.0, 1578.0)):
            c = LEFT.on_plane(np.array([u]), np.array([v]), "y", GUARD_OUT)[0]
            c[1] = side * (GUARD_OUT + 0.0033)
            m.add(bolt(c, (0, side, 0), af=0.008, head_h=0.005, flange_d=0.013))
    c = LEFT.on_plane(np.array([1238.0]), np.array([1166.0]), "y", GUARD_OUT)[0]
    R = np.column_stack([-P.BACK, [0.0, 1.0, 0.0], P.UP])
    m.add(box(c + np.array([0, 0.0073, 0]), (0.026, 0.008, 0.032), "alu_machined", R=R))
    for u, v in ((1237.0, 1160.0), (1235.0, 1189.0)):
        b = LEFT.on_plane(np.array([u]), np.array([v]), "y", GUARD_OUT)[0]
        b[1] = GUARD_OUT + 0.0113
        m.add(bolt(b, (0, 1, 0), af=0.007, head_h=0.004, kind="cap"))
    ring = lathe([(0.008 + 0.0025 * math.cos(q), 0.0025 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 9)[:-1]],
                 20, "alu_machined", closed=True)
    ring.transform(np.column_stack([-P.BACK, P.UP, [0.0, -1.0, 0.0]]), c - P.BACK * 0.020 + np.array([0, 0.0073, 0]))
    m.add(ring)
    return m


# ---------------------------------------------------------------- under the tail
GROOVE = 0.004


def _plugin_part(name):
    """The mesh of a part as the merged modules build it (None if no module builds it)."""
    import importlib
    for mod in P.PLUGINS:
        if mod == "detail_plastics" or not os.path.exists(os.path.join(P.HERE, mod + ".py")):
            continue
        fn = getattr(importlib.import_module(mod), "PARTS", {}).get(name)
        if fn is not None:
            return fn()
    return None


def _wall_x():
    sub = _plugin_part("subframe")
    if sub is None:
        return plastics.TAIL_X0
    V = np.asarray(sub.V)
    V = V[(np.abs(V[:, 1]) < 0.085) & (V[:, 2] > 0.84) & (V[:, 2] < 0.95) & (V[:, 0] > 0.12) & (V[:, 0] < 0.30)]
    if not len(V):
        return plastics.TAIL_X0
    return float(V[:, 0].min()) - 0.002 - GROOVE - 0.0003       # wall 4 mm thick about X0, floor GROOVE ahead


def tail_under():
    """The red wall under the tail, facing back, above the inner mudguard's arch (REAR).
    Outline, rows 606..808: red from u 1872 to 2130 (128 px either side of the centre column), the arch cut out
    along the dark region (u 1964..2034 at row 736, 1949..2049 at 750, 1938..2058 at 764, 1927..2063 at 778,
    1917..2071 at 792), a tab under each bolt (left to row 800, right to 808). Two upright channels in shadow at
    u 1887..1918 and 2076..2110, rows 612..686 (4 mm deep EST). A bolt with a 20 mm washer on a boss either side of
    the arch (metal blobs 29 px wide at (1895, 766) and (2113, 775)). Left of u 1872 the red of the old stand-in
    plate was the left side panel's inner face, not this wall.
    Cast onto an upright plane that puts the channels' floors 0.3 mm behind the rear face of the subframe's rear
    cross member (detail_chassis), which the wall bolts to; without that module at x 0.20 (EST: hidden; the
    seat's base is raised over it). What it bolts to (the subframe's rear cross member) is detail_chassis's."""
    X0 = _wall_x()
    # top corners as the photo has them (row 610: red u 1898..2102, row 624: 1890..2110, rows 638..652: 1885..2129)
    px = np.array([(1898, 608), (2102, 608), (2112, 624), (2129, 640), (2130, 700), (2128, 760), (2124, 800),
                   (2100, 808), (2084, 806), (2071, 792), (2063, 778), (2058, 764), (2049, 750), (2034, 736),
                   (2018, 729), (2000, 726), (1982, 729), (1964, 736), (1949, 750), (1938, 764), (1927, 778),
                   (1917, 792), (1905, 800), (1880, 800), (1873, 760), (1872, 700), (1887, 640), (1890, 624)], float)
    # resampled before it is smoothed: smoothing the corner points themselves pulled the top edge down 24 rows
    # (17 mm) and cut both corners off (the old stand-in plate had the same fault)
    px = smooth_poly(plastics.resample(px, 4.0), 2)
    grooves = [(1887.0, 1918.0, 612.0, 686.0), (2076.0, 2110.0, 612.0, 686.0)]

    def depth(u, v):
        for u0, u1, v0, v1 in grooves:
            d = min(u - u0, u1 - u, v - v0, v1 - v)
            if d > 0:
                return GROOVE * plastics.smoothstep(d / 4.0)
        return 0.0

    def to3d(u, v, w):
        Q = REAR.on_plane(np.array([u]), np.array([v]), "x", X0)[0]
        return (Q[0] + depth(u, v) - w, Q[1], Q[2])
    lines = []
    for u0, u1, v0, v1 in grooves:
        for q in (0.0, 4.5):
            lines.append(np.array([(u0 + q, v0 + q), (u1 - q, v0 + q), (u1 - q, v1 - q), (u0 + q, v1 - q),
                                   (u0 + q, v0 + q)]))
    m = plastics.plate_lines(px, [], 0.004, "plastic_red", to3d, 10.0, lines=lines, line_step=4.0)
    for u, v in ((1895.0, 766.0), (2113.0, 775.0)):
        c = REAR.on_plane(np.array([u]), np.array([v]), "x", X0 - 0.002)[0]
        ax = np.array([-1.0, 0.0, 0.0])
        m.add(tube([c, c + ax * 0.006], 0.012, 20, "plastic_red"))
        m.add(bolt(c + ax * 0.006, ax, af=0.008, head_h=0.005, flange_d=0.020))
    return m


# ---------------------------------------------------------------- the 8 body bolts
def _fastener(c, axis, collar_mat, boss=0.0, collar_r=0.0115):
    """An 8 mm flange bolt (SPEC) in its collar, which stands on the panel's face. boss: length of a boss behind the
    panel's 3 mm shell, running inward to what the panel fixes to (not drawn: 22 mm bosses ran into the radiators
    and the subframe of the merged modules; their mounting points are not read yet)."""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    c = np.asarray(c, float)
    m = tube([c + a * 0.0008, c + a * 0.0035], np.array([collar_r, collar_r - 0.002]), 20, collar_mat)
    m.add(bolt(c + a * 0.0035, a, af=0.008, head_h=0.005, flange_d=0.013))
    if boss > 0.005:
        m.add(tube([c - a * boss, c - a * 0.0038], 0.007, 12, collar_mat))
    return m


def _px(side, u, v):
    return plastics._mpx("left" if side > 0 else "right", [(u, v)])[0]


def _normal(fn, u, v, side):
    """Outward normal of a panel's face at a pixel (fn(u, v) -> 3D point), from points 5 px either side."""
    n = np.cross(fn(u + 5.0, v) - fn(u - 5.0, v), fn(u, v + 5.0) - fn(u, v - 5.0))
    n /= np.linalg.norm(n)
    return n if n[1] * side > 0 else -n


def shroud_bolts():
    """Two a shroud. LEFT / RIGHT: a grey bolt head 15 x 18 px at (1702, 1131) and (2297, 1131), at the lower tip, into
    the radiator's bracket. TOP: a grey head at (1826, 1030) and (1826, 1219) on each top deck beside the tank,
    84 mm off the centre line."""
    m = Mesh()
    for side in (1, -1):
        u, v = _px(side, 1702.0, 1131.0)
        fn = lambda a, b, s=side: plastics.shroud_point(s, a, b)
        m.add(_fastener(fn(u, v), _normal(fn, u, v, side), "plastic_red"))
        q = TOP.on_plane(np.array([1826.0]), np.array([1219.0 if side > 0 else 1030.0]), "z", 1.0)[0]
        m.add(_fastener(plastics.deck_point(side, q[0], q[1]) + np.array([0, 0, 0.003]), (0, 0, 1), "plastic_red"))
    return m


def seat_bolts():
    """One a side, on the seam where the seat, the shroud's tail and the side panel meet. LEFT / RIGHT: a dark pocket
    34 x 32 px centred on (2172, 872) and (1827, 872)."""
    m = Mesh()
    for side in (1, -1):
        u, v = _px(side, 2172.0, 880.0)                     # 8 px under the pocket's centre: on the panel's face
        fn = lambda a, b, s=side: plastics.panel_point(s, a, b)
        if abs(plastics.shroud_point(side, u, v)[1]) > abs(fn(u, v)[1]):       # the shroud's tail lies over the panel
            fn = lambda a, b, s=side: plastics.shroud_point(s, a, b)
        # no boss drawn: this bolt goes through the shroud's tail and the panel under it into the frame
        m.add(_fastener(fn(u, v), _normal(fn, u, v, side), "plastic_red", boss=0.0, collar_r=0.013))
    return m


def panel_bolts():
    """One a side panel, in its black lower half. LEFT / RIGHT: centred on (2426, 1136) and (1572, 1136)."""
    m = Mesh()
    for side in (1, -1):
        u, v = _px(side, 2426.0, 1136.0)
        fn = lambda a, b, s=side: plastics.panel_point(s, a, b, inset=0.006)
        m.add(_fastener(fn(u, v), _normal(fn, u, v, side), "plastic_black"))
    return m


# ---------------------------------------------------------------- number plate: mounts and hose guide
def plate_details():
    """Behind the plate's bolt pocket a boss runs back to the top clamp's front face; two pegs under the slot stand
    on the lower clamp's front face, 0.3 mm short of it (both EST: hidden behind the plate; the clamps are
    detail_front's). Hose guide:
    FRONT rows 600..640, a black loop u 2081..2143 beside the plate's lower edge on the bike's left, which the brake
    hose runs through (loop 22 mm across; its tab to the plate EST)."""
    Pl = plastics._plate()
    m = Mesh()
    uc, vc = plastics.PLATE_POCKET[:2]
    # everything starts 0.5 mm behind the plate's back face (the plate is 3 mm thick): nothing cuts through it
    try:                                                   # front faces of the clamps' bridges (detail_front)
        import detail_front as DF
        top = lambda y: DF.fk(0.0173, y, (DF.FACE_UP + DF.T_UP[1]) / 2)
        low = lambda y: DF.fk(0.0253, y, DF.T_LO[0] + 0.036)
    except Exception:                                      # the first pass's clamps
        top = lambda y: P.on_tube(P.T_TOP_CLAMP) - P.BACK * 0.031 + np.array([0, y, 0])
        low = lambda y: P.on_tube(P.T_BOT_CLAMP) - P.BACK * 0.031 + np.array([0, y, 0])
    # each leaves the plate square to it and meets the clamp square to its face (a slanted end cut into both)
    stub = lambda p, q, seg: tube([p, p + Pl.back * 0.007, q - P.BACK * 0.007, q], 0.006, seg, "plastic_red")
    m.add(stub(Pl.hit(uc, vc, 0.0035), top(0.0), 12))
    for u in (1970.0, 2030.0):                             # on the flat centre panel (its edge is 47 px out here:
        p = Pl.hit(u, 598.0, 0.0035)                       # further out the folded wing cut the peg's end)
        m.add(stub(p, low(p[1]), 10))
    c = Pl.hit(2120.0, 626.0, 0.007)
    e = Pl.hit(2074.0, 600.0, 0.007)
    ring = lathe([(0.011 + 0.003 * math.cos(q), 0.003 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 9)[:-1]],
                 20, "plastic_black", closed=True)
    ring.transform(np.column_stack([np.cross(Pl.up, [0.0, 1.0, 0.0]), Pl.up, [0.0, 1.0, 0.0]]), c)
    m.add(ring)
    d = (c - e) / np.linalg.norm(c - e)
    m.add(tube([e, c - d * 0.011], 0.003, 8, "plastic_black"))
    return m


PARTS = {"fork_guards": fork_guards, "guard_hardware": guard_hardware, "tail_under": tail_under,
         "shroud_bolts": shroud_bolts, "seat_bolts": seat_bolts, "panel_bolts": panel_bolts,
         "plate_details": plate_details}
REPLACES = ("fork_guards", "fender_mounts")
FRONT_END = ("fork_guards", "guard_hardware", "plate_details")
SMOOTH = {"fork_guards": 60, "tail_under": 50}
