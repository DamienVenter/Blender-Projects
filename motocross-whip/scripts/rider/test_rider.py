"""Tests of the rider's body (body.py, mhdata.py). Needs tools/fetch_makehuman.sh.

python3 -m pytest -q test_rider.py
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as B    # noqa: E402
import mhdata as mh  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return B.build()


def test_default_shape_reproduces_makehumans_skeleton():
    """Our macro rules and joint strategies give MakeHuman's own default joints (rig file) within 2 mm."""
    base = mh.Base()
    rig = mh.rig()
    J = mh.joint_positions(base, mh.to_mb(mh.shape(base, mh.DEFAULT_MACRO)), rig)
    err = max(max(np.abs(J[k][0] - rig[k]["head"]["default_position"]).max(),
                  np.abs(J[k][1] - rig[k]["tail"]["default_position"]).max()) for k in rig)
    assert err < 0.002


def test_stature_and_mass_are_his(built):
    V = built["V"]
    assert abs(np.ptp(V[:, 2]) - 1.85) < 0.001 and abs(V[:, 2].min()) < 1e-9          # 185 cm, soles on z = 0
    FS, F = built["FS"], built["F"]
    starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
    tris = np.array([[F[s], F[s + i], F[s + i + 1]] for s, n in zip(starts, FS) for i in range(1, n - 1)])
    a, b, c = V[tris[:, 0]], V[tris[:, 1]], V[tris[:, 2]]
    vol = abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6 * 1000
    assert abs((vol - B.GAS) * B.TISSUE_DENSITY - 80.0) < 0.1                          # 80 kg body


def test_skin_is_closed(built):
    FS, F = built["FS"], built["F"]
    starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
    edges = {}
    for s, n in zip(starts, FS):
        f = F[s:s + n]
        for i in range(n):
            e = (min(f[i], f[(i + 1) % n]), max(f[i], f[(i + 1) % n]))
            edges[e] = edges.get(e, 0) + 1
    assert all(k == 2 for k in edges.values())                                         # the volume is exact


def test_every_vertex_is_skinned(built):
    n = len(built["V"])
    tot = np.bincount(built["w_vert"], weights=built["w_val"], minlength=n)
    assert (tot > 0.5).all() and (tot < 1.5).all()


def test_proportions_against_drillis_contini(built):
    """Leg and arm against Drillis and Contini (1966) fractions of stature, within 6 % (arm: acromion to
    fingertip, 0.44 H; MakeHuman puts the elbow joint high, so the segment split differs, not the reach)."""
    n = list(built["bones"])
    H, T = built["heads"], built["tails"]
    j = lambda b: H[n.index(b)]
    S = 1.85
    assert abs(np.linalg.norm(j("lowerleg01.L") - j("upperleg01.L")) / (0.245 * S) - 1) < 0.06    # thigh
    assert abs(np.linalg.norm(j("foot.L") - j("lowerleg01.L")) / (0.246 * S) - 1) < 0.06          # shank
    assert abs(j("upperleg01.L")[2] / (0.530 * S) - 1) < 0.06                                       # hip height
    V = built["V"]
    left = V[V[:, 0] > 0.10]
    tip = T[n.index("finger3-3.L")]
    shoulder_top = left[(left[:, 0] < 0.20) & (np.abs(left[:, 1] - j("upperarm01.L")[1]) < 0.04)]
    ac = shoulder_top[np.argmax(shoulder_top[:, 2])]
    assert abs(np.linalg.norm(tip - ac) / (0.44 * S) - 1) < 0.06


PARTS = os.environ.get("BIKE_PARTS", "/tmp/claude-0/-home-user-blender-projects/4c1715c0-4e6f-517a-aa9d-c16103ac023a/scratchpad/int9/b.npz")


@pytest.mark.skipif(not os.path.exists(PARTS), reason="needs a bike parts file (parts.py OUT.npz; BIKE_PARTS)")
def test_pose_contacts_are_the_bikes():
    """Grips and pegs mirror each other; seat top about 0.98 m (CRF250R spec 965 mm unladen, our model 0.979 at the
    seat's low point); peg tops about 0.45 m; every pose keeps the hands and feet on them."""
    import pose
    c = pose.contacts(PARTS)
    for k in ("grips", "pegs"):
        L, R = np.array(c[k]["L"]), np.array(c[k]["R"])
        assert np.allclose(L * [1, -1, 1], R, atol=1e-4)                                   # 0.1 mm
    assert 0.96 < pose.seat_top(c, 0.55) < 1.0 and 0.42 < c["pegs"]["L"][2] < 0.47
    for name in ("seated", "standing", "photo05"):
        p = pose.pose(c, name)
        assert np.allclose(p["hands"]["L"], c["grips"]["L"])
        assert p["pelvis"][2] > pose.seat_top(c, p["pelvis"][0]) + 0.09                   # never into the seat
