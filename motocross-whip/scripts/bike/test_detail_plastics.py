"""Fast checks of the seat and rear plastics (plastics.py, detail_plastics.py) against the photo measurements written
next to their tables (research/detail-ledger/plastics.md).

python3 -m pytest -q test_detail_plastics.py
"""
import os

import numpy as np
import pytest
from PIL import Image

import cams
import detail_plastics as dp
import plastics as pl


@pytest.fixture(scope="module")
def seat():
    return pl.seat()


def test_seat_plan_follows_the_top_photo(seat):
    """The hem's plan (the seat's outermost line) through the top camera lands on the measured columns and rows."""
    V = np.asarray(seat.V)
    for u, hw_px in pl.SEAT_PLAN_PX:
        if not 1975 < u < 2745:                                # the nose's corners and the tail's point are
            continue                                           # rounded by the 2 mm smoothing
        x = cams.CAMS["top"].on_plane(np.array([u]), np.array([pl.SEAT_ROW]), "z", 0.96)[0][0]
        k = np.abs(V[:, 0] - x) < 0.002
        half = (V[k, 1].max() - V[k, 1].min()) / 2
        want = pl.seat_hem_hw(x)
        assert abs(half - want) < 0.0025, (u, half, want)
    xs, hw = pl._seat_plan()
    assert abs(xs[-1] - 0.7826) < 0.002 and abs(xs[0] - 0.0776) < 0.002        # nose front, tail point
    assert abs(hw.max() - 0.0888) < 0.0015                                       # 99.5 px at u 2260..2620
    assert abs(V[:, 1].max() + V[:, 1].min()) < 0.001                           # symmetric


def test_seat_top_line_on_the_left_photo(seat):
    """The seat's highest vertex at each station projects onto the photo's silhouette row within 2 px."""
    V = np.asarray(seat.V)
    L = cams.CAMS["left"]
    a = np.asarray(Image.open(os.path.join(pl.HERE, "..", "..", "reference", "crf250r-2026", cams.FILES["left"]))
                   .convert("RGB")).astype(float).min(axis=2)
    for u in (2050, 2200, 2300, 2450, 2600, 2750, 2830):
        x = L.on_plane(np.array([float(u)]), np.array([780.0]), "y", -0.025)[0][0]
        k = np.abs(V[:, 0] - x) < 0.003
        v = L.project(V[k])[:, 1].min()
        col = a[650:900, u]
        photo = 650 + int(np.argmax(col < 235.0))
        assert abs(v - photo) < 2.5, (u, v, photo)


def test_seat_hem_on_each_side_photo(seat):
    """The hem's outer points, through each side's camera, on the seam rows (SEAT_HEM_PX) less HEM_LIFT."""
    S = pl._seat_sections()
    for side, view in ((1, "left"), (-1, "right")):
        cam = cams.CAMS[view]
        k = S.B[:, 1] * side > 0.04
        P = np.column_stack([S.B[k], S.zb[k] - pl.HEM_LIFT])
        uv = cam.project(P)
        hm = np.array(pl.SEAT_HEM_PX, float)
        ul = uv[:, 0] if side > 0 else 3999.0 - uv[:, 0]
        m = (ul > 2000) & (ul < 2840)
        d = uv[m, 1] - np.interp(ul[m], hm[:, 0], hm[:, 1])
        assert np.abs(d).max() < 3.0, (view, np.abs(d).max())


def test_seat_shoulder_against_the_rear_photo(seat):
    """The nose seen from behind: half-widths under the top within 7 px of the photo's (rms under 4 px)."""
    photo = {514: 34, 518: 52, 522: 60, 526: 65.5, 530: 71.5, 534: 74.5, 538: 76.5, 542: 79.5, 546: 81.5,
             550: 83.5, 554: 85, 558: 85.5, 562: 87}
    uv = cams.CAMS["rear"].project(np.asarray(seat.V))
    top = uv[:, 1].min()
    err = []
    for v, hw in photo.items():
        k = np.abs(uv[:, 1] - (v - 513.0 + top)) < 1.0
        err.append((uv[k, 0].max() - uv[k, 0].min()) / 2 - hw)
    err = np.array(err)
    assert np.abs(err).max() < 7.0 and np.sqrt((err ** 2).mean()) < 4.0, err


def test_seat_mesh_is_clean(seat):
    V = np.asarray(seat.V)
    assert all(0 <= i < len(V) for f in seat.F for i in f) and len(seat.F) == len(seat.M)
    area = np.array([np.linalg.norm(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])) for f in seat.F])
    assert area.min() > 1e-8                                    # no zero-area faces
    assert all(len(seat.uv[i]) == len(f) for i, f in enumerate(seat.F) if i in seat.uv)
    assert sum(1 for m in seat.M if m == "seat") == len(seat.uv)   # every cover face carries its grain's UVs
    # compare.raster draws faces under 2 px as one pixel: keep the cover's top faces over that in the top view
    P = cams.CAMS["top"].project(V) / 2
    small = [(np.ceil(P[list(f)].max(0)) - np.floor(P[list(f)].min(0))).max() <= 2
             for f, m in zip(seat.F, seat.M) if m == "seat" and np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])[2] > 0]
    assert np.mean(small) < 0.02


def test_seat_grain_texture():
    """The grain's normal map exists, is tileable (its edges match) and its pebble pitch is the measured 1.3 mm."""
    path = os.path.join(dp.TEXTURES, "seat_grain_n.png")
    a = np.asarray(Image.open(path)).astype(float)
    g = dp.SEAT_GRAIN
    assert a.shape == (g["size"], g["size"], 3)
    assert abs(a[0] - a[-1]).mean() < 40 and abs(a[:, 0] - a[:, -1]).mean() < 40
    n = (a / 255.0) * 2 - 1
    assert (n[..., 2] > 0.3).all()                              # a bump map, not noise
    # pitch: the autocorrelation of the x slope falls to its first minimum at about half a pebble
    s = n[..., 0] - n[..., 0].mean()
    f = np.abs(np.fft.rfft(s, axis=1)) ** 2
    k = np.argmax(f.mean(axis=0)[1:]) + 1
    pitch_mm = g["tile"] / k
    assert 0.5 < pitch_mm < 2.0, pitch_mm
    assert dp.MATERIALS["seat"]["normal"] == "stock/seat_grain_n.png"


@pytest.fixture(scope="module")
def fender():
    return pl.rear_fender()


def test_rear_fender_plan_and_point(fender):
    """Half-widths at the top photo's columns within 2 mm; an arrow point (half-width falls 50 mm in the last 50 mm)
    and not the old round tongue (60 mm there); the tip at the mean of the top and side photos."""
    V = np.asarray(fender.V)
    px, phw, T, E = pl._fender_lines()
    for x in (-0.25, -0.20, -0.14, -0.06):
        k = np.abs(V[:, 0] - x) < 0.0035
        half = (V[k, 1].max() - V[k, 1].min()) / 2
        assert abs(half - np.interp(x, px, phw)) < 0.002, (x, half)
    assert abs(V[:, 0].min() - (-0.2971)) < 0.002
    x0 = V[:, 0].min()
    k = np.abs(V[:, 0] - (x0 + 0.025)) < 0.002
    assert (V[k, 1].max() - V[k, 1].min()) / 2 < 0.036    # the point: 25 mm from it 32 mm (TOP u 3160: 36 px)
    assert abs(V[:, 1].max() + V[:, 1].min()) < 0.001


def test_rear_fender_profile_on_the_left_photo(fender):
    """The top line and the near flank's lower edge project onto the photo's rows within 3 px."""
    V = np.asarray(fender.V)
    L = cams.CAMS["left"]
    uv = L.project(V)
    for (u, v) in pl.FENDER_TOP_PX[3:-2]:
        k = np.abs(uv[:, 0] - u) < 5.0
        assert abs(uv[k, 1].min() - v) < 3.0, (u, uv[k, 1].min(), v)
    for (u, v) in pl.FENDER_LOW_PX[2:-2]:
        k = np.abs(uv[:, 0] - u) < 5.0
        assert abs(uv[k, 1].max() - v) < 3.5, (u, uv[k, 1].max(), v)


def test_side_cover_ribs():
    """The side panels' black lower part carries UVs on every face (the Y-rib normal map), right-handed on the outer
    faces (or the ribs read as grooves); the map's rib lattice is the measured 17.1 mm pitch."""
    m = pl.side_panels()
    V = np.asarray(m.V)
    faces = [i for i, q in enumerate(m.M) if q == "black_texture"]
    assert faces and all(i in m.uv for i in faces)
    good = []
    for i in faces:
        P, uv = V[list(m.F[i])][:3], np.array(m.uv[i])[:3]
        A = np.array([uv[1] - uv[0], uv[2] - uv[0]])
        if abs(np.linalg.det(A)) < 1e-12:
            continue
        T, B = np.linalg.solve(A, np.array([P[1] - P[0], P[2] - P[0]]))
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if n[1] * P[0, 1] > 0:                                   # outer face
            good.append(np.dot(np.cross(T, B), n) > 0)
    assert np.mean(good) > 0.99
    a = np.asarray(Image.open(os.path.join(dp.TEXTURES, "side_cover_n.png")))
    assert a.shape[:2] == (dp.SIDE_COVER["size"][1], dp.SIDE_COVER["size"][0])
    h, sx, sy = dp._tristar_height()
    assert abs(h.shape[1] * sx - 2 * dp.SIDE_COVER["pitch"]) < 1e-6 and abs(sx / sy - 1.0) < 0.002
    assert 0.08 < (h > 0.05).mean() < 0.25                     # ribs cover a measured share of the surface
