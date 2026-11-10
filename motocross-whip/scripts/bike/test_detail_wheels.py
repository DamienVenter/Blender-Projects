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


def _radii(mesh, centre, mat=None):
    V = np.asarray(mesh.V)
    if mat is not None:
        idx = sorted({i for f, m in zip(mesh.F, mesh.M) if m == mat for i in f})
        V = V[idx]
    return np.hypot(V[:, 0] - centre[0], V[:, 2] - centre[2]), V


def test_parts_and_budget(built):
    assert set(built) == {"front_wheel", "rear_wheel", "drive", "rear_brake"}
    assert set(dw.REPLACES) == {"front_wheel", "rear_wheel", "drive"} and dw.FRONT_END == {"front_wheel"}
    assert sum(len(m.V) for m in built.values()) <= 130000
    for m in built.values():
        assert all(0 <= i < len(m.V) for f in m.F for i in f) and len(m.F) == len(m.M)


def test_tyre_diameters(built):
    # knob tips on the measured radii; knobbly tyres stand up to 4.5 % over their size codes' nominal diameters
    # (SPEC 80/100-21: 693.4 mm, 100/90-19: 662.6 mm; here 718.6 and 668.6)
    for name, c, R, nominal in (("front_wheel", parts.FA, parts.R_FRONT, 0.6934), ("rear_wheel", parts.RA, parts.R_REAR, 0.6626)):
        r, _ = _radii(built[name], c, "rubber")
        assert abs(r.max() - R) < 0.0008, name
        assert -0.01 < 2 * r.max() / nominal - 1 < 0.045, name


def test_tyre_widths(built):
    # FRONT rows 1900..2000: 137 px; REAR rows 1750..1975: 139 px (88 to 92 mm through the cameras)
    for name, spec in (("front_wheel", dw.FRONT), ("rear_wheel", dw.REAR)):
        _, V = _radii(built[name], (0, 0, 0), "rubber")
        assert abs((V[:, 1].max() - V[:, 1].min()) - spec["width"]) < 0.003, name
        assert abs(V[:, 1].max() + V[:, 1].min()) < 0.001, name


def test_rims(built):
    # SPEC 21 x 1.60 and 19 x 1.85: bead seat diameter and width between the flanges, in the rim's section
    for name, c, spec, d_in, w_in in (("front_wheel", parts.FA, dw.FRONT, 21, 1.60), ("rear_wheel", parts.RA, dw.REAR, 19, 1.85)):
        prof = np.array(dw.rim_profile(spec))
        assert abs(spec["rb"] * 2 / IN - d_in) < 1e-6 and abs(spec["hw"] * 2 / IN - w_in) < 1e-6
        seat = prof[np.isclose(prof[:, 0], spec["rb"])]
        assert len(seat) == 2 and abs(abs(seat[:, 1]).max() * 2 - w_in * IN) < 1e-6
        r, _ = _radii(built[name], c, "rim")
        assert abs(r.min() - spec["r_in"]) < 0.0005 and abs(r.max() - (spec["rb"] + spec["hf"])) < 0.0005


def test_spokes():
    for spec, rh, yl, yr in ((dw.FRONT, dw.FRONT_HUB_R, 0.0305, -0.0365), (dw.REAR, dw.REAR_HUB_R, 0.046, -0.040)):
        sp = dw.spoke_lines(spec, rh, yl, yr)
        assert len(sp) == 36
        rim = sorted(round(math.degrees(math.atan2(p1[2], p1[0])) % 360, 3) for _, p1, _, _ in sp)
        assert np.allclose(np.diff(rim), 10.0, atol=1e-3)                 # one nipple every 10 deg
        assert all(abs(np.hypot(p0[0], p0[2]) - rh) < 1e-9 and abs(np.hypot(p1[0], p1[2]) - spec["r_in"]) < 1e-9
                   for p0, p1, _, _ in sp)
        assert sum(1 for p0, _, _, _ in sp if p0[1] > 0) == 18


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
    pins, th_a, th_b, bottom, _, low_pitch = dw.chain_path()
    n = len(pins)
    assert n % 2 == 0 and 108 <= n <= 120
    d = np.linalg.norm(np.diff(np.vstack([pins, pins[:1]]), axis=0), axis=1)
    assert abs(parts.P520 - 0.015875) < 1e-9
    assert np.all(abs(d / parts.P520 - 1) < 0.011)                         # SPEC #520 pitch; bottom run closed up 0.9 %
    free_bottom = len(bottom) - 1
    assert np.sum(abs(d - parts.P520) < 1e-7) == n - free_bottom           # every other link exactly one pitch
    c1, c2 = np.array([parts.CS[0], parts.CS[2]]), np.array([parts.RA[0], parts.RA[2]])
    on_r = np.isclose(np.linalg.norm(pins - c2, axis=1), parts.sprocket_r(50), atol=1e-7)
    on_f = np.isclose(np.linalg.norm(pins - c1, axis=1), parts.sprocket_r(13), atol=1e-7)
    assert on_r.sum() >= 26 and on_f.sum() >= 6                             # wrapped half way round both sprockets
    # every seated pin lies in a tooth seat of its sprocket
    for on, c, nt, th in ((on_r, c2, 50, th_a), (on_f, c1, 13, th_b)):
        ang = np.arctan2(pins[on, 1] - c[1], pins[on, 0] - c[0])
        k = (ang - th) / (2 * math.pi / nt)
        assert np.allclose(k, np.round(k), atol=1e-6)


def test_wheelbase_and_ground(built):
    assert abs((parts.FA[0] - parts.RA[0]) - 1.483) < 1e-9                  # SPEC wheelbase
    for name, c in (("front_wheel", parts.FA), ("rear_wheel", parts.RA)):
        r, V = _radii(built[name], c, "hub")
        assert abs(V[:, 0].mean() - c[0]) < 0.002 and abs(V[:, 2].mean() - c[2]) < 0.002
    # on the ground: the bike stands nose-up by GROUND_PITCH about the rear axle, lifted by GROUND_DROP
    for name in ("front_wheel", "rear_wheel"):
        z = parts.to_ground(built[name].V)[:, 2]
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
