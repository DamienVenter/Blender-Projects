"""Fast checks of detail_wheels.py against the spec table (research/crf250r-2026.md) and the photo measurements.

python3 -m pytest -q test_detail_wheels.py
"""
import math

import numpy as np
import pytest

import detail_wheels as dw
import parts

IN = 0.0254


@pytest.fixture(scope="module")
def built():
    return {name: fn() for name, fn in dw.PARTS.items()}


TYRE = ("tyre", "rubber")             # the tyre's moulded rubber (vent hairs are "tyre_spew")


def _radii(mesh, centre, mat=None):
    V = np.asarray(mesh.V)
    if mat is not None:
        mats = (mat,) if isinstance(mat, str) else mat
        idx = sorted({i for f, m in zip(mesh.F, mesh.M) if m in mats for i in f})
        V = V[idx]
    return np.hypot(V[:, 0] - centre[0], V[:, 2] - centre[2]), V


def test_parts_and_budget(built):
    assert set(built) == {"front_wheel", "rear_wheel", "drive", "rear_brake"}
    assert set(dw.REPLACES) == {"front_wheel", "rear_wheel", "drive"} and dw.FRONT_END == {"front_wheel"}
    assert sum(len(m.V) for m in built.values()) <= 450000             # the micro-detail brief's budget
    for m in built.values():
        assert all(0 <= i < len(m.V) for f in m.F for i in f) and len(m.F) == len(m.M)


def test_tyre_diameters(built):
    # knob tips on the shared radii (LEFT / RIGHT circle fits). The front stands 3.6 % over its size code's nominal
    # 693.4 mm in Honda's photos, the rear 0.9 % over 662.6 mm.
    for name, c, R, nominal in (("front_wheel", parts.FA, parts.R_FRONT, 0.6934), ("rear_wheel", parts.RA, parts.R_REAR, 0.6626)):
        r, _ = _radii(built[name], c, TYRE)
        assert abs(r.max() - R) < 0.0008, name
        assert abs(2 * r.max() / nominal - 1) < 0.04, name
    # the carcass between the knobs is where the photos show the groove floor (it did not move with the tips)
    for spec in (dw.FRONT, dw.REAR):
        assert abs(spec["R"] - spec["knob"] - spec["root"]) < 0.0015


def test_tyre_widths(built):
    # FRONT rows 1900..2000: 137 px; REAR rows 1750..1975: 139 px (88 to 92 mm through the cameras)
    for name, spec in (("front_wheel", dw.FRONT), ("rear_wheel", dw.REAR)):
        _, V = _radii(built[name], (0, 0, 0), TYRE)
        assert abs((V[:, 1].max() - V[:, 1].min()) - spec["width"]) < 0.003, name
        assert abs(V[:, 1].max() + V[:, 1].min()) < 0.001, name


def test_rear_sidewall_marks():
    """Raised marks where the LEFT and RIGHT photos show them (unwrapped about the rear axle)."""
    lay = dw.REAR_WALL
    left = {(txt or kind): (lay["emblem"][0] + d0, lay["emblem"][0] + (d1 if d1 is not None else d0), r, cap)
            for kind, txt, d0, d1, r, cap in lay["items"]}
    a0, a1, r, cap = left["SCORPION  MX32"]
    assert abs(a0 - 84) < 2 and abs(a1 - 160) < 2 and abs(r - 0.2665) < 0.001 and abs(cap - 0.016) < 0.001
    a0, a1, r, cap = left["100/90-19  57M  NHS"]
    assert abs(a0 - 272) < 2 and abs(a1 - 337.5) < 2 and abs(cap - 0.0115) < 0.001
    assert lay["emblem"][1] - 2 < 97 < lay["emblem"][1] + 2                # RIGHT: the emblem before SCORPION
    polys, w = dw._text_polys("SCORPION", 0.016)
    V = np.vstack(polys)
    assert abs(V[:, 1].max() - 0.016) < 0.0006                            # cap height (O overshoots a little)
    # the marks stand MARK_H proud of the sidewall and stay below the shoulder knobs' roots (r 294)
    assert all(r + cap * (0.6 if kind == "emblem" else 1.3) < 0.290 for kind, txt, d0, d1, r, cap in lay["items"])
    assert 0.0005 <= dw.MARK_H <= 0.0012


def test_front_tread_and_wall():
    """The front MX32 pattern: 41 rows (side scans, 8.78 deg), every pitch alike, tips at R_FRONT; the size code
    80/100-21 M/C 51M MST (SPEC) where the LEFT photo shows it (267..340 deg)."""
    assert dw.FRONT["pitches"] == 41
    sec = dw.Section(dw.FRONT, dw.FRONT_SECTION)
    m, na, a0, n_t = dw.carcass(sec, 41, dw.FRONT_PHASE, 8, 0.050)
    nf = len(m.F)
    dw.front_tread(m, sec, 41, a0, dw.FRONT)
    V = np.asarray(m.V)
    knob = np.array(sorted({i for f, mt in zip(m.F[nf:], m.M[nf:]) if mt == "tyre" for i in f}))
    assert abs(np.hypot(V[knob, 0], V[knob, 2]).max() - dw.FRONT["R"]) < 1e-4
    assert len(knob) % 41 == 0
    P = V[knob].reshape(41, -1, 3)
    turn = 2 * math.pi / 41
    rot = np.array([[math.cos(turn), 0, -math.sin(turn)], [0, 1, 0], [math.sin(turn), 0, math.cos(turn)]])
    assert np.allclose(P[0] @ rot.T, P[1], atol=1e-6)
    lay = {txt: (d0, d1) for kind, txt, d0, d1, r, cap in dw.FRONT_WALL["items"] if kind == "text"}
    d0, d1 = lay["80/100-21  M/C  51M  MST"]
    e = dw.FRONT_WALL["emblem"][0]
    assert abs(e + d0 - 267) < 2 and abs(e + d1 - 340) < 2


def test_rear_tread():
    """The rear MX32 pattern (REAR_TREAD): 46 rows, each a slit centre knob, two intermediates, two shoulders half
    a pitch on, a pad; the outline the LEFT photo shows; vent hairs on the knobs."""
    q = dw.REAR_TREAD
    assert dw.REAR["pitches"] == 46                                       # LEFT / RIGHT scans: 7.83 deg a row
    sec = dw.Section(dw.REAR, dw.REAR_SECTION)
    m, na, a0, n_t = dw.carcass(sec, 46, dw.REAR_PHASE, 8, 0.054)
    nv, nf = len(m.V), len(m.F)
    dw.rear_tread(m, sec, 46, a0, dw.REAR)
    knob_f = [f for f, mt in zip(m.F[nf:], m.M[nf:]) if mt == "tyre"]
    spews = sum(1 for mt in m.M[nf:] if mt == "tyre_spew") // 12            # 12 faces a hair (3 sides, 3 rings)
    assert 46 * 4 < spews < 46 * 22
    V = np.asarray(m.V)
    knob = np.array(sorted({i for f in knob_f for i in f}))
    rk = np.hypot(V[knob, 0], V[knob, 2])
    assert abs(rk.max() - dw.REAR["R"]) < 1e-4                             # the centre knobs' tops: the tip radius
    # the centre knob's slit: at the top the halves stand 3.5 to 6 mm apart, the floor 1 to 2.5 mm wide
    c = q["centre"]
    top_gap = 2 * (c["slit_t"] + c["slit_z"] * math.tan(math.radians(c["draft"])) +
                   (dw.REAR["knob"] - c["slit_z"]) * math.tan(math.radians(c["slit_draft"])))
    assert 0.0035 < top_gap + 2 * dw.ROUND < 0.006 and 0.001 < 2 * (c["slit_t"] + c["slit_z"] * math.tan(
        math.radians(c["draft"]))) < 0.0025
    # knobs of one pitch do not touch: intermediate and shoulder half a pitch apart leave a gap at their roots
    rc = sec.at(q["shoulder"]["t0"])[1]
    gap = math.pi * rc / 46 - q["inter"]["s"] - q["shoulder"]["s"] - 2 * dw.FLARE
    assert gap > 0.0005
    # every pitch alike: the knob vertices come in 46 equal sets, one 7.83 deg turn apart
    assert len(knob) % 46 == 0
    P = V[knob].reshape(46, -1, 3)
    turn = 2 * math.pi / 46
    rot = np.array([[math.cos(turn), 0, -math.sin(turn)], [0, 1, 0], [math.sin(turn), 0, math.cos(turn)]])
    assert np.allclose(P[0] @ rot.T, P[1], atol=1e-6)


def test_rims(built):
    # SPEC 21 x 1.60 and 19 x 1.85: bead seat diameter and width between the flanges, in the rim's section
    for name, c, spec, d_in, w_in in (("front_wheel", parts.FA, dw.FRONT, 21, 1.60), ("rear_wheel", parts.RA, dw.REAR, 19, 1.85)):
        prof = np.array(dw.rim_profile(spec))
        assert abs(spec["rb"] * 2 / IN - d_in) < 1e-6 and abs(spec["hw"] * 2 / IN - w_in) < 1e-6
        seat = prof[np.isclose(prof[:, 0], spec["rb"])]
        assert len(seat) == 2 and abs(abs(seat[:, 1]).max() * 2 - w_in * IN) < 1e-6
        r, _ = _radii(built[name], c, "rim")
        # the inner face at r_in (the nipples' eyelets stand 0.6 mm proud of it)
        assert abs(r.min() - (spec["r_in"] - 0.0006)) < 0.0003 and abs(r.max() - (spec["rb"] + spec["hf"])) < 0.0005


def test_rim_print(built):
    """The decal strip lies on the side bands only, once a side, where the side photos show it, with UVs inside
    the texture; the textures exist (python3 detail_wheels.py paints them)."""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    for name, which, c in (("rear_wheel", "rear", parts.RA), ("front_wheel", "front", parts.FA)):
        assert os.path.exists(os.path.join(here, "..", "..", "textures", "stock", "rim_%s.png" % which))
        m = built[name]
        mat = "rim_print_" + which[0]
        fi = [i for i, mt in enumerate(m.M) if mt == mat]
        assert fi and all(i in m.uv for i in fi)
        uv = np.array([q for i in fi for q in m.uv[i]])
        assert uv[:, 0].min() > -0.01 and uv[:, 0].max() < 1.0 and 0.0 < uv[:, 1].min() and uv[:, 1].max() < 1.0
        V = np.asarray(m.V)
        P = V[[m.F[i][0] for i in fi]] - c
        ang = np.degrees(np.arctan2(P[:, 2], P[:, 0])) % 360
        dec = (ang < dw.RIM_DECAL[which] + 30) & (ang > dw.RIM_DECAL[which] - 3)
        assert dec.sum() > 0.25 * len(fi)                                  # the decals at 258..288 deg
        assert set(np.sign(P[:, 1])) == {-1.0, 1.0}                         # both sides
        prof = np.array(dw.rim_profile(dw.REAR if which == "rear" else dw.FRONT))
        assert abs(prof[3, 1] - prof[4, 1]) < 0.0005                        # the band is flat (decals lie flat)


def test_spokes():
    # front 36 (SPEC, counted), rear 32 (counted round the rim in both side photos), three-cross, rim holes where
    # the photos' nipples are: front 8.3 deg mod 10, rear 9.0 mod 11.25
    for spec, rh, yl, yr, n, ph in ((dw.FRONT, dw.FRONT_HUB_R, 0.0305, -0.0365, 36, 8.3),
                                    (dw.REAR, dw.REAR_HUB_R, 0.046, -0.040, 32, 9.0)):
        sp = dw.spoke_lines(spec, rh, yl, yr, phase=dw.FRONT_SPOKE0 if spec is dw.FRONT else dw.REAR_SPOKE0)
        assert len(sp) == n
        rim = sorted(round(math.degrees(math.atan2(p1[2], p1[0])) % 360, 3) for _, p1, _, _ in sp)
        assert np.allclose(np.diff(rim), 360 / n, atol=1e-3)              # one nipple every 360 / n deg
        assert abs((rim[0] - ph + 180 / n) % (360 / n) - 180 / n) < 0.6
        assert all(abs(np.hypot(p0[0], p0[2]) - rh) < 1e-9 and abs(np.hypot(p1[0], p1[2]) - spec["r_in"]) < 1e-9
                   for p0, p1, _, _ in sp)
        assert sum(1 for p0, _, _, _ in sp if p0[1] > 0) == n // 2


def test_discs(built):
    # SPEC 260 mm front (left side), 240 mm rear (right side)
    for name, c, d, side in (("front_wheel", parts.FA, 0.260, 1), ("rear_wheel", parts.RA, 0.240, -1)):
        r, V = _radii(built[name], c, "disc")
        assert abs(2 * r.max() - d) < 0.0006, name
        assert np.all(V[:, 1] * side > 0.05), name
    a = np.radians(np.arange(0, 360, 0.25))
    assert abs(dw.front_disc_r(a).max() - 0.130) < 1e-4 and abs(dw.rear_disc_r(a).max() - 0.120) < 1e-4


def test_sprockets_and_chain():
    for n in (13, 50):
        out = dw.sprocket_outline(n, 0.3)
        r = np.hypot(out[:, 0], out[:, 1])
        tips = np.sum((r > np.roll(r, 1)) & (r >= np.roll(r, -1)))
        assert tips == n
        assert abs(r.min() - (parts.sprocket_r(n) - dw.SEAT_R)) < 1e-6
    pins, th_a, th_b, bottom, e = dw.chain_path()
    n = len(pins)
    assert n % 2 == 0 and 108 <= n <= 118
    assert abs(parts.P520 - 0.015875) < 1e-9                                # SPEC #520 pitch
    # the photo's path is 112.9 pitches round: 112 links, the free runs' links 1.2 % long, the seated ones true
    d = np.linalg.norm(np.diff(np.vstack([pins, pins[:1]]), axis=0), axis=1)
    true = abs(d - parts.P520) < 1e-7
    assert true.sum() >= 32 and np.all(true | (abs(d / (parts.P520 * (1 + e)) - 1) < 0.004))
    assert 0 < e < 0.0125 and e * (~true).sum() / n < 0.01                  # under 1 % over the whole chain
    c1, c2 = np.array([parts.CS[0], parts.CS[2]]), np.array([parts.RA[0], parts.RA[2]])
    on_r = np.isclose(np.linalg.norm(pins - c2, axis=1), parts.sprocket_r(50), atol=1e-7)
    on_f = np.isclose(np.linalg.norm(pins - c1, axis=1), parts.sprocket_r(13), atol=1e-7)
    assert on_r.sum() >= 26 and on_f.sum() >= 6                             # wrapped half way round both sprockets
    for on, c, nt, th in ((on_r, c2, 50, th_a), (on_f, c1, 13, th_b)):      # every seated pin in a tooth seat
        ang = np.arctan2(pins[on, 1] - c[1], pins[on, 0] - c[0])
        k = (ang - th) / (2 * math.pi / nt)
        assert np.allclose(k, np.round(k), atol=1e-6)
    # no free pin inside a pitch circle (the chain meets and leaves the sprockets from outside)
    assert np.all(np.linalg.norm(pins - c2, axis=1) > parts.sprocket_r(50) - 1e-4)
    assert np.all(np.linalg.norm(pins - c1, axis=1) > parts.sprocket_r(13) - 1e-4)
    # the photo's path: top run on parts.chain_top, bottom run on the line (0.604, 0.428) .. (0.171, 0.270)
    top = pins[(pins[:, 0] > 0.15) & (pins[:, 0] < 0.60) & (pins[:, 1] > 0.44)]
    assert len(top) > 20 and np.all(abs(top[:, 1] - parts.chain_top(top[:, 0])) < 0.002)
    low = bottom[(bottom[:, 0] > 0.18) & (bottom[:, 0] < 0.60)]
    line = 0.270 + (low[:, 0] - 0.171) * (0.428 - 0.270) / (0.604 - 0.171)
    assert len(low) > 20 and np.all(abs(low[:, 1] - line) < 0.005)
    # the bottom run passes just over the frame's lower roller (room for a roller of 11 to 20 mm radius)
    zc = float(np.interp(dw.LOWER_ROLLER[0], bottom[::-1, 0], bottom[::-1, 1]))
    assert 0.011 < zc - 0.0073 - dw.LOWER_ROLLER[1] < 0.020


def test_wheelbase_and_ground(built):
    assert abs((parts.FA[0] - parts.RA[0]) - 1.483) < 1e-9                  # SPEC wheelbase
    for name, c in (("front_wheel", parts.FA), ("rear_wheel", parts.RA)):
        r, V = _radii(built[name], c, "hub")
        assert abs(V[:, 0].mean() - c[0]) < 0.002 and abs(V[:, 2].mean() - c[2]) < 0.002
    # on the ground (parts.to_ground: nose-up by GROUND_PITCH, the ground GROUND_DROP under the frame's z = 0)
    for name in ("front_wheel", "rear_wheel"):
        z = parts.to_ground(np.asarray(built[name].V))[:, 2]
        assert abs(z.min()) < 0.0015, name


def test_chain_line_and_clearances(built):
    V = np.asarray(built["drive"].V)
    chain = V[V[:, 1] > parts.CHAIN_Y - 0.0095]
    assert abs(0.5 * (chain[:, 1].min() + V[:, 1].max()) - parts.CHAIN_Y) < 0.012
    r, Vs = _radii(built["rear_wheel"], parts.RA, "sprocket")
    assert abs(Vs[:, 1].mean() - parts.CHAIN_Y) < 1e-4 and np.ptp(Vs[:, 1]) < 0.00635      # between the inner plates
    # brake pads clear the disc; caliper bracket clear of the hub collar
    Vb = np.asarray(built["rear_brake"].V)
    rb = np.hypot(Vb[:, 0] - parts.RA[0], Vb[:, 2] - parts.RA[2])
    near_disc = Vb[(rb < 0.121) & (rb > 0.03)]
    y0, y1 = dw.DISC_R["y"] - dw.DISC_R["t"] / 2, dw.DISC_R["y"] + dw.DISC_R["t"] / 2
    assert not np.any((near_disc[:, 1] > y0 - 0.0001) & (near_disc[:, 1] < y1 + 0.0001))
