"""Damien's 2026 Honda CRF250R, part by part, as meshes in the bike frame (metres; x forward, y left, z up; origin
on the ground under the rear axle). Plain Python (numpy/scipy): run it to write the parts file, which
build_bike.py turns into Blender objects. Every number has a source:
  SPEC  research/crf250r-2026.md (Honda spec sheets: wheelbase, rake, trail, rims, tyres, discs, fork, sprockets)
  BP    research/bike-blueprint.json (Honda studio profile photo, calibrated: axles, tyre outer diameters)
  OUT   research/bike-outlines.json (plastics traced from that photo)
  GRID  positions read off the millimetre-gridded blueprint crops (scripts/bike/gridview.py)
  TOP   widths read off the gridded studio top photo (scripts/bike/topview.py)
  DV    Damien's own photos (reference/damien-bike-2026-11-10): his parts and colours
  EST   estimated (hidden or not yet measured); to verify on his bike

python3 parts.py OUT.npz
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams                                          # noqa: E402
from geom import (Mesh, box, circle, frame_z, grid, lathe, loft_sections, panel, plate2d, prism,  # noqa: E402
                  rot_x, rot_y, rot_z, rounded_rect, slot, smooth_poly, tube)

RES = os.path.join(HERE, "..", "..", "research")
BP = json.load(open(os.path.join(RES, "bike-blueprint.json")))["left"]
OUT = json.load(open(os.path.join(RES, "bike-outlines.json")))
OUT2 = json.load(open(os.path.join(RES, "bike-outlines2.json")))      # extract.py: frame, swingarm, muffler, ...
MM = 0.001


RIGHT_VIEW = {"muffler", "header"}                  # extracted from the right profile photo (as are all "*_R")


def _world(view, o_mm, y):
    """Outline stored in the photo's linear blueprint coordinates (mm) -> true (x, z) in metres on the plane of
    lateral position Y, by casting rays through the photo's calibrated camera (cams.py)."""
    u, v = cams.linear_to_px(view, o_mm[:, 0], o_mm[:, 1])
    P = cams.CAMS[view].on_plane(u, v, "y", y)
    return P[:, [0, 2]]


def P2(name, y):
    """Outline (x, z) in metres of a part extracted from the photos' material map (tag OUT2), at lateral position Y."""
    view = "right" if name in RIGHT_VIEW or name.endswith("_R") else "left"
    return _world(view, np.array(OUT2[name], float), y)


def PO(name, y):
    """Plastics outline or top line (OUT, from the left profile photo), at lateral position Y."""
    return _world("left", np.array(OUT[name], float), y)


# ---------------------------------------------------------------- geometry of the chassis
WHEELBASE = 1.483                                   # SPEC
AXLE_Z = BP["rear_tyre_od_mm"] / 2 * MM             # 0.3264: height of both axles in the blueprint's frame. Only a datum:
# the circle the blueprint fitted to the rear tyre lies 8 mm inside the knob tips, so z = 0 is 8 mm above the ground
# Tyre radii at the knob tips. LEFT and RIGHT photos, rays from each axle over the free arc of the tyre: 95th
# percentile 359.6 and 359.7 (front), 336.9 and 338.7 (rear) at the centre plane's scale, 0.6 % less for the near
# edge of the tread; the tread drawn through both cameras fits 359.3 and 334.3 (wheels pass). Cross-checks: Honda's
# overall length 2179 = wheelbase + both radii gives 696 for the pair (here 693.6), and 80/100-21 and 100/90-19
# motocross tyres are 709 to 718 and 663 to 671 mm across
R_REAR = cams.TYRE_R_REAR                           # 0.3343
R_FRONT = cams.TYRE_R_FRONT                         # 0.3593
# The parts are built in the AXLE-LINE frame of the blueprint (both axles at z = AXLE_Z, the frame every outline
# and grid reading is in). build_bike.py then tilts the whole bike nose-up by GROUND_PITCH about the rear axle and
# lifts it by GROUND_DROP so both tyres stand on the ground (the front tyre is bigger).
RA = np.array([0.0, 0.0, AXLE_Z])                   # rear axle
FA = np.array([WHEELBASE, 0.0, AXLE_Z])             # front axle (axle-line frame)
GROUND_PITCH = math.atan2(R_FRONT - R_REAR, WHEELBASE)        # about 0.97 deg
GROUND_DROP = R_REAR - AXLE_Z                       # the ground is this far below the frame's z = 0 under the rear axle


def to_ground(P):
    """Points of the axle-line frame -> standing on the ground (z = 0 under both tyres)."""
    P = np.asarray(P, float)
    c, sn = math.cos(GROUND_PITCH), math.sin(GROUND_PITCH)
    x, z = P[:, 0] - RA[0], P[:, 2] - RA[2]
    return np.stack([RA[0] + c * x - sn * z, P[:, 1], RA[2] + GROUND_DROP + sn * x + c * z], axis=1)


# Fork tube axis measured on Honda's left profile photo: both edges of the near (left) tube fitted over 0.70..1.12 m
# give its centre line through (1209.5, 800) at 26.40 deg in the photo's blueprint coordinates; cast through the
# calibrated camera onto the tube's plane (y = +FORK_HALF) this is the true axis. It comes to about 27 deg to the
# ground: the 27 deg 33 min of the US and GS/LA/MX spec sheets, not the 28 deg 24 min listed for EU, AU and South
# Africa. The photo is followed.
# FRONT (refitted camera): at rows 900..1000 each tube runs from 108 to 176 px off the centre column: centres at
# +-99 mm, 48 mm across (50 to 53 mm in the left photo); TOP: gold tube visible out to 0.120. The 93 mm used before
# was the centre of the fork GUARDS, which sit 5 to 7 mm inboard of the tubes.
FORK_HALF = 0.099
_fl = np.array([(1209.5, 800.0), (1209.5 - 300.0 * math.tan(math.radians(26.40)), 1100.0)])
_fw = _world("left", _fl, FORK_HALF)
RAKE = math.atan2(_fw[0, 0] - _fw[1, 0], _fw[1, 1] - _fw[0, 1])          # axle-line frame
UP = np.array([-math.sin(RAKE), 0.0, math.cos(RAKE)])         # fork / steering axis, pointing up
BACK = np.array([-math.cos(RAKE), 0.0, -math.sin(RAKE)])      # perpendicular to it, pointing back
AXLE_LEAD = float((np.array([_fw[0, 0], 0.0, _fw[0, 1]]) - FA) @ BACK)      # photo: axle ahead of the tube axis
CLAMP_OFFSET = 0.022                                # SPEC (aftermarket source, L): triple clamp offset
TUBE0 = FA + AXLE_LEAD * BACK                       # fork tube axis passes here (axle height)
STEER0 = TUBE0 + CLAMP_OFFSET * BACK                # steering axis passes here


def on_tube(t, y=0.0):
    """Point on the fork tube axis t metres above the axle (along UP), at lateral position y."""
    return TUBE0 + t * UP + np.array([0, y, 0])


def t_at_z(z):
    return (z - TUBE0[2]) / UP[2]


T_BOT_CLAMP = t_at_z(0.925)                         # GRID: lower clamp at z 0.90..0.96
T_TOP_CLAMP = t_at_z(1.140)                         # GRID: top clamp at z 1.13..1.15
PIVOT = np.array([0.564, 0.0, 0.480])               # swingarm pivot bolt: its cap cast on its own plane (y 0.14) through
# the left camera. Read on the centre plane it was 18 mm low (the camera looks down on it). Pivot to axle 584.5 (SPEC 585.2)
PEG = np.array([0.556, 0.0, 0.378])                 # GRID: footpeg, read on the centre plane (the teeth, on their own plane, are
# at z 0.412 to 0.425: detail_chassis)
CHAIN_Y = 0.088                                     # chain line (left side). REAR photo: 0.086 (wheels pass) and 0.089
# (chassis pass, rows 1600..1620) for the chain's centre behind the sprocket
CS = np.array([0.633, CHAIN_Y, 0.464])              # countershaft (13T sprocket). GRID gave z 0.451 on the centre plane; on
# the chain's plane the left camera, looking down, puts it 13 mm higher. Check: centre distance to the rear axle 647.8,
# a taut loop of 114 links round 13 and 50 teeth needs 648.1 (0.3 mm of slack in the centre distance)
P520 = 0.015875                                     # SPEC: #520 chain pitch


def sprocket_r(n):
    return P520 / (2 * math.sin(math.pi / n))


# ---------------------------------------------------------------- wheels
def tyre_profile(r_bead, r_crown, half_w):
    """Carcass section (r, y), bead to bead over the crown."""
    pts = []
    for a in np.linspace(-1, 1, 25):
        y = half_w * math.sin(a * math.pi / 2) * 1.0
        # rounded section: full width at about 55 % of the section height
        r = r_bead + (r_crown - r_bead) * (math.cos(a * math.pi / 2) ** 0.55)
        pts.append((r, y * (0.62 + 0.38 * math.cos(a * math.pi / 2) ** 0.3)))
    pts[0] = (r_bead, -half_w * 0.55)
    pts[-1] = (r_bead, half_w * 0.55)
    return pts


def tyre(name, r_out, rim_d_in, section_w, pitches, knob_h):
    """Knobby tyre: carcass by lathe plus tread blocks. PITCHES knob pitches per revolution were counted on Honda's
    profile photo (Fourier analysis of the silhouette's edge: front 41, rear 46). Each pitch has a row with a centre
    pair and shoulder knobs and, half a pitch on, a row with a centre single and intermediates (Pirelli Scorpion MX32
    layout, simplified; block sizes and heights EST until the tread is modelled from the close-up photos)."""
    r_bead = rim_d_in * 0.0254 / 2 + 0.002
    r_crown = r_out - knob_h
    hw = section_w / 2
    prof = tyre_profile(r_bead, r_crown, hw)
    m = lathe(prof, 120, "rubber")
    pr = np.array(prof)
    upper = pr[np.argsort(pr[:, 1])]
    pitch_len = 2 * math.pi * r_out / pitches

    def surf(y):
        r = float(np.interp(y, upper[:, 1], upper[:, 0]))
        r1 = float(np.interp(y + 0.002, upper[:, 1], upper[:, 0]))
        return r, math.atan(-(r1 - r) / 0.002)
    for k in range(pitches):
        for half, ys in ((0.0, (-0.34, 0.34, -0.92, 0.92)), (0.5, (0.0, -0.66, 0.66))):
            a = 2 * math.pi * (k + half) / pitches
            c, sn = math.cos(a), math.sin(a)
            R = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]])
            for fy in ys:
                y = fy * hw
                r, tilt = surf(y)
                w_lat = (0.30 if abs(fy) < 0.5 else 0.24) * hw
                w_circ = (0.44 if abs(fy) < 0.8 else 0.38) * pitch_len
                kb = box((0, 0, 0), (w_circ, w_lat, knob_h + 0.004), "rubber")
                kb.transform(rot_x(-tilt))
                kb.transform(None, (0, y, r + knob_h / 2 - 0.002))
                kb.transform(R)
                m.add(kb)
    return m


def rim(bead_d_in, width_in, mat="rim"):
    rb = bead_d_in * 0.0254 / 2
    hw = width_in * 0.0254 / 2
    prof = [(rb - 0.006, -hw + 0.006), (rb - 0.004, -hw - 0.001), (rb + 0.009, -hw - 0.002), (rb + 0.010, -hw + 0.002),
            (rb + 0.001, -hw + 0.004), (rb - 0.001, -hw * 0.45), (rb - 0.009, -hw * 0.3), (rb - 0.009, hw * 0.3),
            (rb - 0.001, hw * 0.45), (rb + 0.001, hw - 0.004), (rb + 0.010, hw - 0.002), (rb + 0.009, hw + 0.002),
            (rb - 0.004, hw + 0.001), (rb - 0.006, hw - 0.006), (rb - 0.016, hw * 0.4), (rb - 0.016, -hw * 0.4)]
    return lathe(prof, 120, mat, closed=True)


def hub(half_w, flange_r, barrel_r, flange_y):
    prof = [(0.010, -half_w), (barrel_r * 0.8, -half_w), (barrel_r, -half_w + 0.006), (barrel_r, -flange_y - 0.004),
            (flange_r, -flange_y - 0.003), (flange_r, -flange_y + 0.003), (barrel_r * 0.9, -flange_y + 0.008),
            (barrel_r * 0.75, 0.0), (barrel_r * 0.9, flange_y - 0.008), (flange_r, flange_y - 0.003),
            (flange_r, flange_y + 0.003), (barrel_r, flange_y + 0.004), (barrel_r, half_w - 0.006),
            (barrel_r * 0.8, half_w), (0.010, half_w)]
    return lathe(prof, 48, "hub")


def spokes(n, hub_r, flange_y, rim_r, rim_hw, cross=3):
    """Laced spokes: n/2 per flange, each going to a rim hole CROSS x (360 / (n/2)) degrees around (3-cross)."""
    m = Mesh()
    per = n // 2
    alpha = 2 * math.pi * cross / per
    for side, fy in ((0, -flange_y), (1, flange_y)):
        for i in range(per):
            a_h = 2 * math.pi * (i + 0.5 * side) / per
            d = 1 if i % 2 == 0 else -1
            a_r = a_h + d * alpha
            ry = (-1 if side == 0 else 1) * rim_hw * 0.3
            p0 = np.array([hub_r * math.cos(a_h), fy, hub_r * math.sin(a_h)])
            p1 = np.array([rim_r * math.cos(a_r), ry, rim_r * math.sin(a_r)])
            m.add(tube([p0, p1], 0.0019, 6, "spoke", cap0=False, cap1=False))
            dn = (p1 - p0) / np.linalg.norm(p1 - p0)
            m.add(tube([p1 - dn * 0.014, p1], 0.0033, 6, "spoke"))           # nipple
    return m


def petal_disc(r_out, r_in, n_petals, y, thick=0.003):
    """Wave ('petal') disc: scalloped outer edge, ring with two rows of slots, six bolt bosses; mounted on the hub
    by a thin carrier ring (the spokes show through, as on the bike)."""
    a = np.linspace(0, 2 * math.pi, n_petals * 16, endpoint=False)
    ro = r_out - 0.0045 * (1 - np.cos(n_petals * a)) / 2
    outer = np.stack([ro * np.cos(a), ro * np.sin(a)], axis=1)
    holes = [circle(r_in, 64)]
    for k in range(n_petals * 2):
        ang = 2 * math.pi * (k + 0.5) / (n_petals * 2)
        rr = r_in + (r_out - r_in) * (0.38 if k % 2 else 0.62)
        c = (rr * math.cos(ang), rr * math.sin(ang))
        holes.append(slot(c, ang + 1.2, 0.016, 0.006))
    m = plate2d(outer, holes, thick, "disc", lambda u, v, t: (u, y + t, v), step=0.006)
    inner = [circle(0.042, 48)] + [circle(0.0055, 12, 0.060 * math.cos(2 * math.pi * k / 6),
                                          0.060 * math.sin(2 * math.pi * k / 6)) for k in range(6)]
    carrier_outer = circle(r_in + 0.004, 64)
    spokes_out = []
    m.add(plate2d(carrier_outer, [circle(r_in - 0.006, 64)], thick * 1.6, "hub",
                  lambda u, v, t: (u, y + t, v), step=0.006))
    for k in range(6):                          # six arms from the hub flange to the disc ring, with bolts
        ang = 2 * math.pi * k / 6
        d = np.array([math.cos(ang), math.sin(ang)])
        arm = tube([np.array([0.045 * d[0], y, 0.045 * d[1]]), np.array([(r_in + 0.001) * d[0], y, (r_in + 0.001) * d[1]])],
                   [(0.006, 0.003)] * 2, 8, "hub")
        m.add(arm)
        m.add(tube([np.array([0.058 * d[0], y - 0.004, 0.058 * d[1]]), np.array([0.058 * d[0], y + 0.004, 0.058 * d[1]])],
                   0.005, 6, "steel"))
    return m


def sprocket(n, y, mat="sprocket", thick=0.006):
    """Sprocket: tooth profile (rounded trapezoids at the #520 pitch radius), centre bore, lightening windows on the
    big rear sprocket."""
    r = sprocket_r(n)
    pts = []
    for i in range(n):
        a0 = 2 * math.pi * i / n
        for da, rr in ((-0.36, r - 0.0065), (-0.20, r + 0.0015), (-0.10, r + 0.0050), (0.10, r + 0.0050),
                       (0.20, r + 0.0015), (0.36, r - 0.0065)):
            a = a0 + da * 2 * math.pi / n
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    holes = [circle(0.031 if n > 20 else 0.011, 40)]
    if n > 20:
        for k in range(6):                      # six windows between six arms
            a0 = 2 * math.pi * k / 6
            win = []
            for a in np.linspace(a0 + 0.18, a0 + 2 * math.pi / 6 - 0.18, 10):
                win.append(((r - 0.020) * math.cos(a), (r - 0.020) * math.sin(a)))
            for a in np.linspace(a0 + 2 * math.pi / 6 - 0.30, a0 + 0.30, 8):
                win.append((0.058 * math.cos(a), 0.058 * math.sin(a)))
            holes.append(np.array(win))
        for k in range(6):
            a = 2 * math.pi * (k + 0.5) / 6
            holes.append(circle(0.0045, 12, 0.044 * math.cos(a), 0.044 * math.sin(a)))
    return plate2d(np.array(pts), holes, thick, mat, lambda u, v, t: (u, y + t, v), step=0.008)


def front_wheel():
    m = Mesh()
    m.add(tyre("front", R_FRONT, 21, 0.080, 41, 0.014))                 # SPEC 80/100-21, BP OD, photo pitch
    m.add(rim(21, 1.60))                                                 # SPEC 21 x 1.60, black D.I.D
    m.add(hub(0.058, 0.046, 0.030, 0.034))
    m.add(spokes(36, 0.041, 0.034, 0.2667 - 0.012, 0.0203))             # SPEC 36 spokes
    m.add(petal_disc(0.130, 0.080, 12, 0.062))                           # SPEC 260 mm, left side
    return m


def rear_wheel():
    m = Mesh()
    m.add(tyre("rear", R_REAR, 19, 0.100, 46, 0.017))                   # SPEC 100/90-19, BP OD, photo pitch
    m.add(rim(19, 1.85))                                                 # SPEC 19 x 1.85
    m.add(hub(0.070, 0.050, 0.034, 0.040))
    m.add(spokes(36, 0.045, 0.040, 0.2413 - 0.012, 0.0235))             # EST 36 (front is 36)
    m.add(petal_disc(0.120, 0.075, 12, -0.066))                          # SPEC 240 mm, right side
    m.add(sprocket(50, CHAIN_Y))                                         # SPEC 50T
    return m


# ---------------------------------------------------------------- front end (steers about the steering axis)
def fork():
    m = Mesh()
    for side in (-1, 1):
        y = side * FORK_HALF
        # outer tube (gold), from below the lower clamp to above the top clamp
        m.add(tube([on_tube(0.355, y), on_tube(T_TOP_CLAMP + 0.035, y)], 0.0255, 32, "fork_gold"))   # photos: 48..53 mm
        # inner tube (49 mm, dark coated) and the axle lug
        m.add(tube([on_tube(0.035, y), on_tube(0.40, y)], 0.0245, 32, "fork_inner", cap0=False))
        lug = tube([on_tube(-0.045, y), on_tube(0.045, y)], [(0.028, 0.030)] * 2, 24, "fork_lug")
        m.add(lug)
        # fork cap and adjuster on top
        m.add(tube([on_tube(T_TOP_CLAMP + 0.035, y), on_tube(T_TOP_CLAMP + 0.052, y)], 0.024, 24, "anod_black"))
        # dust seal / bottom of the outer tube
        m.add(tube([on_tube(0.345, y), on_tube(0.365, y)], 0.0285, 32, "rubber_black"))
    # front axle
    m.add(tube([FA + np.array([0, -0.115, 0]), FA + np.array([0, 0.115, 0])], 0.010, 16, "steel"))
    return m


def fork_guards():
    """Guards over the lower fork legs. FRONT (refitted camera, rows 1012..1428): outer edge 131 mm off the centre
    line all the way down, inner edge 58 mm at the top to 68 mm lower down, so each shell reaches further inboard of
    its tube than outboard. Front edge from the left photo's outline (OUT 'fork_guard'); the shell wraps back along
    the leg's sides."""
    m = Mesh()
    poly = PO("fork_guard", FORK_HALF + 0.03)
    rel = poly - np.array([TUBE0[0], TUBE0[2]])
    t = rel @ np.array([UP[0], UP[2]])
    off = rel @ np.array([-BACK[0], -BACK[2]])                        # forward of the tube axis
    ts = np.linspace(t.min() + 0.004, t.max() - 0.004, 34)
    fr = np.array([off[np.abs(t - tt) < 0.014].max() if (np.abs(t - tt) < 0.014).any() else 0.040 for tt in ts])
    fr = np.clip(np.convolve(np.pad(fr, 2, mode="edge"), np.ones(5) / 5, mode="valid"), 0.038, 0.075)
    y_out = 0.131
    for side in (-1, 1):
        rings = []
        for tt, f in zip(ts, fr):
            y_in = float(np.interp(tt, [0.07, 0.30, 0.385], [0.068, 0.064, 0.058]))
            top = min((ts[-1] - tt) / 0.03, 1.0)                              # the very top closes in a little
            lo, hi = y_in + 0.004 * (1 - top), y_out - 0.004 * (1 - top)
            sec = [(-0.014, lo), (0.012, lo), (f - 0.008, lo + 0.004), (f, lo + 0.012), (f, hi - 0.012),
                   (f - 0.008, hi - 0.004), (0.012, hi), (-0.014, hi)]
            if side < 0:
                sec = sec[::-1]
            rings.append(np.array([on_tube(tt) - BACK * a_ + np.array([0, side * y_, 0]) for a_, y_ in sec]))
        m.add(grid(Mesh(), rings, "fork_guard", closed_u=False))
    return m


def clamps():
    """Top and bottom triple clamps (aluminium) across both tubes and the steering stem."""
    m = Mesh()
    for t, h, mat in ((T_BOT_CLAMP, 0.045, "alu_cast"), (T_TOP_CLAMP, 0.030, "alu_machined")):
        loop = rounded_rect(0.085, 2 * FORK_HALF + 0.07, 0.035, 6)          # local (along BACK, along y)
        rings = []
        for dt in (-h / 2, h / 2):
            c = on_tube(t + dt)
            rings.append(np.array([c + BACK * (p[0] + 0.012) + np.array([0, p[1], 0]) for p in loop]))
        m.add(grid(Mesh(), rings, mat, cap0=True, cap1=True))
    # steering stem nut
    s_top = STEER0 + (T_TOP_CLAMP + 0.015) * UP
    m.add(tube([s_top, s_top + 0.018 * UP], 0.016, 6, "alu_machined"))
    return m


def bars():
    """Renthal Fatbar (28.6 mm centre, 22.2 mm at the controls), bar mounts, pad, grips, levers, perches."""
    m = Mesh()
    clamp = STEER0 + (T_TOP_CLAMP + 0.045) * UP + BACK * -0.005               # GRID: bar centre z about 1.175
    half = [(0.00, 0.000, 0.000), (0.10, -0.003, 0.004), (0.18, -0.012, 0.012), (0.24, -0.030, 0.030),
            (0.30, -0.052, 0.040), (0.36, -0.065, 0.044), (0.425, -0.073, 0.046)]       # (y, dx, dz) GRID/TOP
    for side in (-1, 1):
        P = np.array([clamp + np.array([dx, side * y, dz]) for y, dx, dz in half])
        r = np.array([0.0143, 0.0143, 0.0143, 0.0123, 0.0111, 0.0111, 0.0111])
        m.add(tube(P, r, 20, "bar_black"))
        # bar mounts (risers) under the bar
        mount = clamp + np.array([0, side * 0.04, 0]) - 0.030 * UP
        m.add(tube([mount, clamp + np.array([0, side * 0.04, 0])], 0.016, 16, "alu_machined"))
        # grip (with flange) and bar end
        g0 = P[4] + (P[5] - P[4]) * 0.2
        m.add(tube([g0, P[6] + (P[6] - P[5]) * 0.08], 0.0165, 20, "grip"))
        m.add(tube([g0 - (P[5] - P[4]) * 0.06, g0], 0.022, 20, "grip"))
        # lever perch, lever, master cylinder (right) / clutch perch (left)
        perch = P[4] + (P[3] - P[4]) * 0.4
        lever_tip = perch + np.array([0.115, side * 0.105, -0.045])
        m.add(tube([perch + np.array([0.02, 0, 0]), lever_tip], [(0.006, 0.0045)] * 2, 10, "lever"))
        m.add(box(perch + np.array([0.0, 0, 0.01]), (0.03, 0.035, 0.03), "anod_black"))
        if side < 0:
            m.add(box(perch + np.array([-0.005, 0.02, 0.03]), (0.045, 0.06, 0.03), "anod_black"))    # master cyl
    # bar pad (red Renthal, DV photo 4)
    pad = rounded_rect(0.060, 0.040, 0.015, 4)
    rings = []
    for y in np.linspace(-0.105, 0.105, 2):
        rings.append(np.array([clamp + np.array([p[0] - 0.005, y, p[1] + 0.022]) for p in pad]))
    m.add(grid(Mesh(), rings, "barpad", cap0=True, cap1=True))
    return m


def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def tank():
    """Titanium tank top visible between the shrouds (GRID x 0.79..0.96, z about 1.02), fuel cap at x 0.893."""
    m = Mesh()
    # its rear end stays under the seat's nose and the shroud decks (it showed beside the seat nose in profile)
    xs = np.linspace(0.74, 1.02, 18)
    top = np.interp(xs, [0.74, 0.79, 0.88, 0.96, 1.02], [0.950, 1.000, 1.022, 1.015, 0.96])
    hw = np.interp(xs, [0.74, 0.85, 0.95, 1.02], [0.070, 0.100, 0.090, 0.060])
    def sec(i):
        loop = rounded_rect(2 * hw[i], top[i] - 0.80, 0.045, 6)
        return np.array([(xs[i], p[0], (top[i] + 0.80) / 2 + p[1]) for p in loop])
    m.add(loft_sections(range(len(xs)), sec, "tank_ti"))
    cap = np.array([0.893, 0.0, 1.022])
    m.add(tube([cap, cap + np.array([0, 0, 0.022])], 0.036, 24, "plastic_black"))
    m.add(tube([cap + np.array([0, 0, 0.022]), cap + np.array([0, 0, 0.034])], 0.024, 12, "plastic_black"))
    return m


def radiators():
    """Twin radiators behind the shroud mouths: black cores from 70 to 176 mm off the centre line, 275 mm tall,
    leaning with the down tube; louvre slats ahead. FRONT (refitted camera) shows black from 0.130 m, where the fork
    tube stops hiding it, to 0.189; the core stops at 0.176 so that it stays inside the shroud's skin at its lower,
    rearward end (plan envelope 0.181 at x 0.95: at 0.188 it came through the shroud's side). Detailed with the
    engine."""
    m = Mesh()
    lean = rot_y(math.radians(-12))
    yc, half = 0.123, 0.053
    for side in (-1, 1):
        core = box((0, 0, 0), (0.034, 2 * half, 0.275), "radiator", lean)
        core.transform(None, (1.000, side * yc, 0.795))
        m.add(core)
        for k in range(11):                                # slats: thin blades angled outward
            zc = 0.675 + k * 0.025
            lv = box((0, 0, 0), (0.030, 2 * half - 0.005, 0.003), "louvre", lean @ rot_y(math.radians(-28)))
            lv.transform(None, (1.028 + (zc - 0.795) * math.tan(math.radians(12)), side * yc, zc))
            m.add(lv)
        for yy in (yc - half + 0.002, yc + half - 0.002):  # side tanks (black-painted here; detailed later)
            tk = box((0, 0, 0), (0.040, 0.006, 0.285), "radiator", lean)
            tk.transform(None, (1.000, side * yy, 0.795))
            m.add(tk)
    return m


def rear_inner():
    return plastics.inner_mudguard()


def fender_mounts():
    return plastics.fender_mounts()


def fender_flap():
    return plastics.fender_flap(on_tube, BACK, t_at_z)


# ---------------------------------------------------------------- frame and swingarm
def frame():
    """Twin-spar aluminium frame. The visible spar and pivot plate of each side are plates cut to the exact outline
    seen in Honda's left and right profile photos (OUT2 'frame', 'frame_R'), 26 mm thick, following the spar's path
    in plan (TOP/EST: 55 mm from the centre line near the head tube, 130 mm at the pivot plates)."""
    m = Mesh()
    m.add(tube([STEER0 + (T_BOT_CLAMP + 0.03) * UP, STEER0 + (T_TOP_CLAMP - 0.02) * UP], 0.029, 28, "alu_frame"))

    def spar_y(x, z):
        return float(np.interp(x, [0.47, 0.60, 0.75, 0.85, 0.95], [0.128, 0.132, 0.120, 0.095, 0.055]))
    for side, key in ((1, "frame"), (-1, "frame_R")):
        s_ = side
        m.add(panel(P2(key, s_ * 0.125), lambda x, z, q=s_: q * spar_y(x, z), 0.026, "alu_frame", step=0.010))
        # the spar's upper end, hidden behind the shroud, up to the head tube
        top = [(0.800, 0.108, 0.812), (0.900, 0.078, 0.885), (1.000, 0.042, 0.945)]
        m.add(tube(np.array([(x, s_ * y, z) for x, y, z in top]), [(0.014, 0.040)] * 3, 16, "alu_frame"))
        # lower cradle rail under the engine (GRID) and subframe (mostly under the side panels, EST)
        rail = [(0.950, 0.020, 0.640), (0.938, 0.040, 0.520), (0.912, 0.055, 0.425), (0.868, 0.062, 0.362),
                (0.780, 0.068, 0.345), (0.640, 0.078, 0.346), (0.570, 0.105, 0.362)]
        m.add(tube(np.array([(x, s_ * y, z) for x, y, z in rail]), 0.0135, 14, "alu_frame"))
        # subframe rails: hidden under the seat and side panels in every photo, so they are kept INSIDE the measured
        # plastics (seat half-width 0.075 to 0.088, panel envelope 0.094 at x 0.60) and end under the seat's tail.
        # Further out they came through the shroud's rear end and the fender's root (compare.py intruders).
        sub = [(0.545, 0.118, 0.650), (0.40, 0.108, 0.745), (0.25, 0.088, 0.825), (0.12, 0.066, 0.880)]
        m.add(tube(np.array([(x, s_ * y, z) for x, y, z in sub]), 0.0115, 12, "alu_frame"))
        sub2 = [(0.70, 0.074, 0.860), (0.45, 0.076, 0.900), (0.25, 0.072, 0.912), (0.12, 0.062, 0.915)]
        m.add(tube(np.array([(x, s_ * y, z) for x, y, z in sub2]), 0.010, 12, "alu_frame"))
    # down tube (single) from the head to the cradle split
    m.add(tube(np.array([(1.030, 0, 0.93), (0.990, 0, 0.78), (0.953, 0, 0.645)]), [(0.020, 0.026)] * 3, 18,
               "alu_frame"))
    m.add(tube([PIVOT + np.array([0, -0.16, 0]), PIVOT + np.array([0, 0.16, 0])], 0.011, 12, "steel"))
    for side in (-1, 1):                                  # footpeg brackets under the pivot plates (GRID)
        br = np.array([(0.585, 0.405), (0.528, 0.405), (0.532, 0.362), (0.580, 0.362)])
        m.add(panel(br, lambda x, z, q=side: q * 0.128, 0.012, "alu_cast", step=0.008))
    return m


def swingarm():
    """Each arm is a 38 mm thick box cut to the exact outline of Honda's profile photos (OUT2 'swingarm' left,
    'swingarm_R' right); the outlines stop where the arm disappears behind the wheel, so the axle block is added."""
    m = Mesh()

    def arm_y(x, z):
        return float(np.interp(x, [0.0, 0.35, 0.56], [0.125, 0.122, 0.105]))
    for side, key in ((1, "swingarm"), (-1, "swingarm_R")):
        m.add(panel(P2(key, side * 0.12), lambda x, z, q=side: q * arm_y(x, z), 0.038,
                    "swing_L" if side > 0 else "swing_R", step=0.010))
        # axle block with the adjuster slot, behind the wheel in the photos (EST)
        blk = np.array([(0.075, 0.300), (0.075, 0.352), (-0.030, 0.348), (-0.045, 0.326), (-0.030, 0.304)])
        m.add(panel(blk, lambda x, z, q=side: q * 0.125, 0.038, "alu_machined", step=0.008))
    c = PIVOT + (RA - PIVOT) * 0.16                       # cross member behind the pivot (EST)
    m.add(tube([c + np.array([0, -0.09, 0]), c + np.array([0, 0.09, 0])], [(0.024, 0.030)] * 2, 14, "alu_swingarm"))
    sl = [PIVOT + np.array([0.02, 0.112, 0.042]), PIVOT + (RA - PIVOT) * 0.30 + np.array([0, 0.118, 0.038])]
    m.add(tube(sl, [(0.014, 0.010)] * 2, 10, "plastic_black"))                     # chain slider
    m.add(tube([RA + np.array([0, -0.14, 0]), RA + np.array([0, 0.14, 0])], 0.010, 14, "steel"))
    return m


def shock():
    m = Mesh()
    # on the centre line, hidden behind the pivot plates in both profile photos (the gap behind the plates shows
    # white background at x 0.44, z 0.57: the shock is in front of it) (EST)
    top, bot = np.array([0.560, 0.0, 0.735]), np.array([0.520, 0.0, 0.405])
    d = (bot - top) / np.linalg.norm(bot - top)
    m.add(tube([top, top + d * 0.17], 0.026, 20, "shock_body"))
    m.add(tube([top + d * 0.12, bot], 0.0085, 12, "chrome"))
    # spring: helix
    n, r = 9, 0.033
    a = np.linspace(0, 2 * math.pi * n, 9 * 40)
    R = frame_z(d)
    pts = [top + d * (0.04 + 0.21 * k / len(a)) + R @ np.array([r * math.cos(t), r * math.sin(t), 0]) for k, t in
           enumerate(a)]
    m.add(tube(pts, 0.0058, 8, "spring"))
    m.add(tube([PIVOT + np.array([-0.06, 0.0, -0.105]), bot], 0.012, 10, "alu_cast"))      # linkage (EST)
    return m


# ---------------------------------------------------------------- engine and exhaust
ENGINE_OUTLINE = [(0.882, 0.760), (0.905, 0.737), (0.905, 0.655), (0.914, 0.601), (0.923, 0.565), (0.923, 0.474),
                  (0.905, 0.415), (0.869, 0.369), (0.751, 0.351), (0.638, 0.369), (0.593, 0.419), (0.584, 0.519),
                  (0.624, 0.583), (0.706, 0.610), (0.760, 0.683), (0.769, 0.737), (0.778, 0.760)]     # GRID


def engine():
    """Side outline traced off the blueprint (GRID), extruded: crankcase +-0.112 below z 0.61, cylinder and head
    +-0.072 above; covers, head cover, intake, hoses and the skid plate added on."""
    m = Mesh()
    out = np.array(ENGINE_OUTLINE)
    low = np.array([p for p in out if p[1] <= 0.62] + [(0.584, 0.61), (0.923, 0.61)])
    low = np.array(sorted(low.tolist(), key=lambda p: math.atan2(p[1] - 0.48, p[0] - 0.76)))
    up = np.array([p for p in out if p[1] >= 0.58] + [(0.70, 0.58), (0.925, 0.58)])
    up = np.array(sorted(up.tolist(), key=lambda p: math.atan2(p[1] - 0.67, p[0] - 0.84)))
    m.add(prism(low, -0.112, 0.112, "engine_case"))
    m.add(prism(up, -0.072, 0.072, "engine_case"))
    # head cover (black), on top of the head (GRID: black cover at the top of the engine)
    hc = np.array([(0.778, 0.760), (0.882, 0.760), (0.874, 0.782), (0.788, 0.782)])
    m.add(prism(hc, -0.062, 0.062, "engine_black", step=0.01))
    # generator cover (left) and clutch cover (right) (GRID: generator centre 0.769, 0.446, r 0.064)
    m.add(tube([np.array([0.769, 0.108, 0.446]), np.array([0.769, 0.138, 0.446])], 0.066, 40, "engine_cover"))
    m.add(tube([np.array([0.769, 0.138, 0.446]), np.array([0.769, 0.142, 0.446])], 0.020, 6, "engine_black"))
    m.add(tube([np.array([0.800, -0.108, 0.470]), np.array([0.800, -0.150, 0.470])], 0.098, 40, "engine_cover"))
    m.add(tube([np.array([0.880, -0.108, 0.540]), np.array([0.880, -0.135, 0.540])], 0.038, 24, "engine_cover"))  # pump
    # black ribbed electrics box behind the cylinder on the left (blue in the first difference picture: x 0.656,
    # z 0.652), tilted like the frame spar above it (GRID/EST)
    eb = box((0, 0, 0), (0.115, 0.050, 0.078), "plastic_black", rot_y(math.radians(38)))
    eb.transform(None, (0.655, 0.085, 0.645))
    m.add(eb)
    # intake: throttle body and boot toward the airbox (EST)
    m.add(tube(np.array([(0.78, 0, 0.72), (0.72, 0, 0.77), (0.63, 0, 0.81)]), 0.034, 16, "rubber_black"))
    # radiator hoses (EST)
    for side in (-1, 1):
        m.add(tube(np.array([(0.90, side * 0.02, 0.74), (0.95, side * 0.08, 0.79), (0.98, side * 0.115, 0.86)]),
                   0.012, 10, "rubber_black"))
    # skid plate (black, GRID z 0.325..0.40, x 0.62..1.00)
    sk = []
    for y in (-0.105, 0.105):
        sk.append(np.array([(x, y, z) for x, z in [(0.922, 0.425), (0.916, 0.398), (0.895, 0.368), (0.855, 0.338),
                                                    (0.700, 0.322), (0.620, 0.335)]]))       # photo front edge rows
    m.add(grid(Mesh(), sk, "plastic_black", closed_u=False))
    return m


def exhaust():
    """Header: stainless pipe along the route seen in the right photo (out of the port, a loop low at the front, back
    along the right side at z 0.593; GRID/EST). Muffler: lofted ovals whose side silhouette is the exact outline of the
    right photo (OUT2 'muffler'); width 78 % of the height (EST)."""
    m = Mesh()
    # photo rows: the pipe's front surface is at x 0.977..0.986 for z 0.46..0.55 (centre 0.964), nothing ahead of
    # 0.968 at z 0.58; it turns back on the right at z 0.52..0.55 and runs level at z 0.593 (right photo)
    header = np.array([(0.930, 0.000, 0.690), (0.956, 0.000, 0.640), (0.964, -0.004, 0.580), (0.964, -0.028, 0.512),
                       (0.950, -0.070, 0.488), (0.915, -0.115, 0.525), (0.860, -0.140, 0.572), (0.780, -0.150, 0.592),
                       (0.630, -0.152, 0.594), (0.500, -0.150, 0.615), (0.400, -0.150, 0.655)])
    from scipy.interpolate import CubicSpline
    t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(header, axis=0), axis=1))])
    hp = CubicSpline(t, header)(np.linspace(0, t[-1], 60))
    m.add(tube(hp, 0.0205, 18, "header_steel"))
    o = P2("muffler", -0.150)
    c0 = o.mean(axis=0)
    w, v = np.linalg.eigh(np.cov((o - c0).T))
    d = v[:, 1] if v[0, 1] < 0 else -v[:, 1]                 # long axis, pointing rearward
    n = np.array([-d[1], d[0]])
    if n[1] < 0:
        n = -n
    tt, pp = (o - c0) @ d, (o - c0) @ n
    st = np.linspace(tt.min() + 0.004, tt.max() - 0.004, 30)
    lo = np.array([pp[np.abs(tt - q) < 0.012].min() for q in st])
    hi = np.array([pp[np.abs(tt - q) < 0.012].max() for q in st])
    k = np.ones(5) / 5
    lo = np.convolve(np.pad(lo, 2, mode="edge"), k, mode="valid")
    hi = np.convolve(np.pad(hi, 2, mode="edge"), k, mode="valid")
    a = np.linspace(0, 2 * math.pi, 28, endpoint=False)
    rings = []
    for q, l, h in zip(st, lo, hi):
        cc = c0 + d * q + n * (l + h) / 2
        hh = max((h - l) / 2, 0.006)
        rings.append(np.array([(cc[0] + n[0] * hh * math.cos(ai), -0.150 + 0.78 * hh * math.sin(ai),
                                cc[1] + n[1] * hh * math.cos(ai)) for ai in a]))
    m.add(grid(Mesh(), rings, "muffler", cap0=True, cap1=True))
    return m


def disc_guard():
    """Stock black plastic guard over the front disc (left side): a dished cover with a hexagon-mesh window in its
    upper front and a solid lower fin (shape EST from the left photo; exact outline to follow)."""
    m = Mesh()
    outer = []
    for ang in np.linspace(0, 2 * math.pi, 72, endpoint=False):
        r = 0.137
        if -2.4 < ang - 2 * math.pi < -0.4 or -2.4 < ang < -0.4:
            r = 0.150
        outer.append((r * math.cos(ang), r * math.sin(ang)))
    holes = [circle(0.030, 24)]
    for i in range(-6, 7):
        for j in range(0, 8):
            cx = i * 0.019 + (0.0095 if j % 2 else 0.0)
            cz = 0.022 + j * 0.0165
            if 0.045 < math.hypot(cx, cz) < 0.118:
                holes.append(circle(0.0075, 6, cx, cz))
    m.add(plate2d(np.array(outer), holes, 0.004, "plastic_black", lambda u, v, t: (u, 0.080 + t, v), step=0.012))
    return m.transform(None, FA)


def cables():
    """Front brake hose (right master cylinder, in front of the plate, down the left fork guard to the caliper),
    clutch cable and the two throttle cables (loops behind the plate), following the black lines of the left photo
    (GRID landmarks; lateral routing EST)."""
    from scipy.interpolate import CubicSpline
    m = Mesh()

    def run(pts, r):
        P = np.array(pts, float)
        t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        m.add(tube(CubicSpline(t, P)(np.linspace(0, t[-1], 48)), r, 8, "cable"))
    f = lambda t, fwd, y: tuple(on_tube(t, y) - BACK * fwd)          # t up the fork, fwd ahead of the tube axis
    run([(STEER0 + (T_TOP_CLAMP + 0.07) * UP + np.array([-0.02, -0.200, 0.0])), f(T_TOP_CLAMP + 0.10, 0.085, -0.150),
         f(T_TOP_CLAMP + 0.07, 0.125, -0.050), f(T_TOP_CLAMP - 0.04, 0.105, 0.020), f(T_BOT_CLAMP + 0.05, 0.075, 0.085),
         f(0.42, 0.050, 0.128), f(0.26, 0.050, 0.130), f(0.10, 0.030, 0.115), f(0.03, -0.045, 0.090)], 0.0045)
    run([(1.000, 0.225, 1.215), (1.060, 0.160, 1.205), (1.090, 0.070, 1.130), (1.050, 0.020, 1.030),
         (0.960, -0.050, 0.900), (0.900, -0.090, 0.760), (0.860, -0.115, 0.600)], 0.004)        # clutch cable
    for dy in (-0.006, 0.006):
        run([(0.990, -0.270, 1.215), (0.950, -0.200 + dy, 1.190), (0.895, -0.100 + dy, 1.130),
             (0.870, -0.040 + dy, 1.050), (0.840, -0.010 + dy, 0.930), (0.800, 0.0 + dy, 0.800)], 0.0035)   # throttle
    return m


def drive():
    """Chain (#520 links around the 13T and 50T sprockets), front sprocket, chain roller (red, DV)."""
    m = Mesh()
    m.add(sprocket(13, 0.0, "steel").transform(None, CS))
    rf, rr = sprocket_r(13), sprocket_r(50)
    c1, c2 = np.array([CS[0], CS[2]]), np.array([RA[0], RA[2]])
    d = c2 - c1
    L = np.linalg.norm(d)
    u = d / L
    nrm = np.array([-u[1], u[0]])
    # external tangents
    ang = math.asin((rr - rf) / L)
    path = []
    def arc(c, r, a0, a1, n):
        return [c + r * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(a0, a1, n)]
    base = math.atan2(nrm[1], nrm[0])
    # top run tangent points
    t1 = c1 + rf * np.array([math.cos(base + ang), math.sin(base + ang)])
    t2 = c2 + rr * np.array([math.cos(base + ang), math.sin(base + ang)])
    b1 = c1 + rf * np.array([math.cos(base + math.pi - ang), math.sin(base + math.pi - ang)])
    b2 = c2 + rr * np.array([math.cos(base + math.pi - ang), math.sin(base + math.pi - ang)])
    loop = arc(c1, rf, base + math.pi - ang - 2 * math.pi, base + ang, 20) + [t1 + (t2 - t1) * s for s in
                                                                              np.linspace(0, 1, 40)[1:-1]]
    loop += arc(c2, rr, base + ang, base + math.pi - ang, 50) + [b2 + (b1 - b2) * s for s in np.linspace(0, 1, 40)[1:-1]]
    loop = np.array(loop)
    seg = np.linalg.norm(np.diff(np.vstack([loop, loop[:1]]), axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    nlinks = int(s[-1] / P520)
    for k in range(nlinks):
        sk = k * s[-1] / nlinks
        i = np.searchsorted(s, sk) - 1
        i = min(max(i, 0), len(loop) - 1)
        p = loop[i] + (loop[(i + 1) % len(loop)] - loop[i]) * ((sk - s[i]) / max(seg[i], 1e-9))
        q = loop[(i + 1) % len(loop)] - loop[i]
        a = math.atan2(q[1], q[0])
        plate_w = 0.0095 if k % 2 else 0.0085
        for yy in (CHAIN_Y - 0.0055, CHAIN_Y + 0.0055):
            pl = box((0, 0, 0), (P520 * 1.05, 0.0014, plate_w), "chain", rot_y(-a))
            pl.transform(None, (p[0], yy, p[1]))
            m.add(pl)
        roller = tube([np.array([p[0], CHAIN_Y - 0.005, p[1]]), np.array([p[0], CHAIN_Y + 0.005, p[1]])], 0.0035, 8,
                      "chain")
        m.add(roller)
    # red anodised chain roller below the pivot (DV photos 1, 2, 5)
    m.add(tube([np.array([0.528, CHAIN_Y - 0.012, 0.392]), np.array([0.528, CHAIN_Y + 0.012, 0.392])], 0.019, 24,
               "red_anod"))
    return m


def controls():
    m = Mesh()
    for side in (-1, 1):
        # footpeg: toothed platform (DV: silver steel pegs)
        y0, y1 = 0.135, 0.235
        m.add(box(PEG + np.array([0, side * (y0 + y1) / 2, 0]), (0.052, y1 - y0, 0.010), "steel"))
        for k in range(5):
            for xx in (-0.024, 0.024):
                tooth = box(PEG + np.array([xx, side * (y0 + 0.01 + k * 0.02), 0.008]), (0.006, 0.006, 0.010), "steel")
                m.add(tooth)
        m.add(tube([PEG + np.array([0.0, side * 0.115, -0.008]), PEG + np.array([0.0, side * 0.14, -0.008])], 0.012,
                   10, "steel"))
    # shift lever (left) and brake pedal (right) (EST)
    m.add(tube(np.array([(0.66, 0.13, 0.46), (0.66, 0.15, 0.43), (0.70, 0.17, 0.41), (0.73, 0.19, 0.41)]), 0.007, 8,
               "steel"))
    m.add(tube(np.array([(0.54, -0.125, 0.43), (0.62, -0.14, 0.40), (0.69, -0.16, 0.395), (0.72, -0.185, 0.40)]),
               0.008, 8, "steel"))
    # Pro-Link under the swingarm: pull rods from the frame to the delta link, which carries the shock's lower end
    # (positions EST from the left photo; exact parts to follow)
    delta = np.array([(0.485, 0.350), (0.405, 0.338), (0.440, 0.288)])
    m.add(panel(delta, lambda x, z: 0.018, 0.036, "alu_cast", step=0.008))
    for side in (-1, 1):
        m.add(tube([np.array([0.548, side * 0.030, 0.338]), np.array([0.440, side * 0.030, 0.296])], [(0.011, 0.007)] * 2,
                   8, "alu_cast"))
    # chain guide (black block under the swingarm, ahead of the rear sprocket) and lower chain roller
    cg = box((0, 0, 0), (0.085, 0.034, 0.070), "plastic_black", rot_y(math.radians(-13)))
    cg.transform(None, (0.130, CHAIN_Y, 0.262))
    m.add(cg)
    m.add(tube([np.array([0.455, CHAIN_Y - 0.012, 0.333]), np.array([0.455, CHAIN_Y + 0.012, 0.333])], 0.017, 16,
               "plastic_black"))
    # rear master cylinder and reservoir behind the right pivot plate (EST)
    m.add(box(np.array([0.505, -0.150, 0.470]), (0.030, 0.026, 0.085), "anod_black", rot_y(math.radians(12))))
    m.add(tube([np.array([0.500, -0.150, 0.530]), np.array([0.500, -0.150, 0.565])], 0.015, 12, "plastic_black"))
    # front caliper (left, behind the fork leg) and rear caliper (right)
    m.add(box(FA + np.array([-0.075, 0.085, 0.045]), (0.06, 0.035, 0.09), "caliper", rot_y(math.radians(-25))))
    m.add(box(RA + np.array([0.04, -0.09, -0.095]), (0.06, 0.03, 0.05), "caliper"))
    return m


import plastics                                      # noqa: E402  (measured plastics: plastics.py)

FRONT_END = {"fork": fork, "fork_guards": fork_guards, "clamps": clamps, "bars": bars,
             "number_plate": plastics.number_plate, "front_fender": plastics.front_fender, "fender_flap": fender_flap,
             "front_wheel": front_wheel, "disc_guard": disc_guard}
CHASSIS = {"frame": frame, "swingarm": swingarm, "shock": shock, "engine": engine, "exhaust": exhaust,
           "drive": drive, "controls": controls, "rear_wheel": rear_wheel, "shrouds": plastics.shrouds,
           "side_panels": plastics.side_panels, "seat": plastics.seat, "rear_fender": plastics.rear_fender,
           "tank": tank,
           "radiators": radiators, "cables": cables, "rear_inner": rear_inner,
           "shroud_decks": plastics.shroud_decks, "fender_mounts": fender_mounts, "mud_flap": plastics.mud_flap}
PIVOTS = {"front_wheel": FA, "rear_wheel": RA}         # wheels are built about their axle


# Plugins: detail modules beside this file add parts or replace parts of this file. Each defines
#   PARTS      {part name: function() -> geom.Mesh}  (axle-line frame; front-end parts with the bars straight)
#   REPLACES   names of parts of this file (or of an earlier plugin) that it replaces: dropped from the build
#   FRONT_END  names of its parts that turn with the steering
#   MATERIALS  {material name: dict(rgb=(r, g, b) 0..255, metal=, rough=, coat=, aniso=, bump=)} for new materials
#              (existing names: MATS in build_bike.py)
#   CLASS      {material name: "red" | "black"} for compare.py's material classes (default: metal)
#   THIN       names of single-surface parts to solidify 3 mm in Blender;  BEVEL {name: width m};  SMOOTH {name: deg}
# BIKE_PLUGINS=a,b limits which load (BIKE_PLUGINS=none: none), so one assembly can be worked on alone.
PLUGINS = ("detail_chassis", "detail_engine", "detail_front", "detail_wheels", "detail_plastics")


def plugins():
    import importlib
    want = os.environ.get("BIKE_PLUGINS", "all")
    mods = []
    for name in PLUGINS:
        if want == "none" or (want != "all" and name not in want.split(",")):
            continue
        if os.path.exists(os.path.join(HERE, name + ".py")):
            mods.append(importlib.import_module(name))
    return mods


def build():
    fns = {**FRONT_END, **CHASSIS}
    own = set(fns)
    front = set(FRONT_END)
    meta = {"thin": [], "bevel": {}, "smooth": {}, "materials": {}, "class": {}}
    for m in plugins():
        for old in getattr(m, "REPLACES", ()):
            fns.pop(old, None)
            front.discard(old)
            own.discard(old)
        for name, fn in m.PARTS.items():
            fns[name] = fn
            own.discard(name)
        front |= set(getattr(m, "FRONT_END", ()))
        meta["thin"] += list(getattr(m, "THIN", ()))
        meta["bevel"].update(getattr(m, "BEVEL", {}))
        meta["smooth"].update(getattr(m, "SMOOTH", {}))
        meta["materials"].update({k: dict(v) for k, v in getattr(m, "MATERIALS", {}).items()})
        meta["class"].update(getattr(m, "CLASS", {}))
    parts = {}
    for name, fn in fns.items():
        mesh = fn()
        if name in PIVOTS and name in own:               # this file's wheels are built about their axle
            mesh.transform(None, PIVOTS[name])
        parts[name] = mesh
    meta["front_end"] = sorted(front & set(parts))
    build.meta = meta
    return parts


def save(parts, path):
    data = {}
    mats = sorted({mm for p in parts.values() for mm in p.M})
    data["materials"] = np.array(mats)
    data["names"] = np.array(list(parts))
    for name, p in parts.items():
        V = np.asarray(p.V, np.float32)
        sizes = np.array([len(f) for f in p.F], np.int32)
        flat = np.array([i for f in p.F for i in f], np.int32)
        data[f"{name}__V"] = V
        data[f"{name}__S"] = sizes
        data[f"{name}__F"] = flat
        data[f"{name}__M"] = np.array([mats.index(mm) for mm in p.M], np.int16)
    data["meta"] = np.array(json.dumps(getattr(build, "meta", {"front_end": sorted(FRONT_END)})))
    data["steer_axis"] = np.vstack([STEER0, UP])
    data["ground"] = np.array([RA[0], RA[1], RA[2], GROUND_PITCH, GROUND_DROP])
    np.savez_compressed(path, **data)


if __name__ == "__main__":
    parts = build()
    save(parts, sys.argv[1])
    for name, p in parts.items():
        lo, hi = p.bounds()
        print(f"{name:13s} {len(p.V):6d} v {len(p.F):6d} f   x {lo[0]:+.3f}..{hi[0]:+.3f}  y {lo[1]:+.3f}..{hi[1]:+.3f}"
              f"  z {lo[2]:+.3f}..{hi[2]:+.3f}")
