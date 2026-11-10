"""Fast checks of detail_chassis.py against the spec table (research/crf250r-2026.md) and Honda's photos.
python3 -m pytest -q test_detail_chassis.py   (a few seconds)"""
import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams               # noqa: E402
import parts              # noqa: E402
import detail_chassis as dc   # noqa: E402


@pytest.fixture(scope="module")
def V():
    return {name: np.asarray(fn().V, float) for name, fn in dc.PARTS.items()}


ground = parts.to_ground


def test_vertex_budget(V):
    assert sum(len(v) for v in V.values()) < 70000


def test_footpeg_height_is_422_mm(V):
    """SPEC: footpeg height 422 mm: top of the teeth at the peg's root, on the ground."""
    G = ground(V["footpegs"])
    for side in (1, -1):
        root = G[(G[:, 1] * side > 0.150) & (G[:, 1] * side < 0.175)]
        assert abs(root[:, 2].max() - 0.422) < 0.006, root[:, 2].max()


def test_footpeg_tips_are_where_the_rear_photo_has_them(V):
    """REAR: tips at columns 1673 and 2328, row about 1294."""
    P = V["footpegs"]
    for side, col in ((1, 1673), (-1, 2328)):
        tip = P[np.argmax(P[:, 1] * side)]
        top = P[(P[:, 1] * side > 0.235)][:, 2].max()
        u, v = cams.CAMS["rear"].project(np.array([tip[0], tip[1], top]))[0]
        assert abs(u - col) < 8 and abs(v - 1294) < 8, (u, v)


def test_ground_clearance_leaves_330_mm_under_the_cradle(V):
    """SPEC: 330 mm under the engine's guard. The cradle rails sit just above it and nothing of the frame is lower."""
    G = ground(V["frame"])
    low = G[(G[:, 0] > 0.55) & (G[:, 0] < 1.0)][:, 2].min()
    assert 0.330 <= low < 0.368, low


def test_swingarm_turns_on_the_shared_pivot_and_reaches_the_axle(V):
    """SPEC: swingarm 585.2 mm. parts.PIVOT, the pivot cap in the photos cast on the plate's plane, gives 584.5."""
    assert abs(np.linalg.norm(parts.PIVOT - parts.RA) - 0.5852) < 0.002
    S = V["swingarm"]
    nose = S[S[:, 0] > parts.PIVOT[0] + 0.010]             # pivot tube and the slider wrapped round it
    r = np.hypot(nose[:, 0] - parts.PIVOT[0], nose[:, 2] - parts.PIVOT[2])
    assert r.max() < 0.036 and len(nose) > 20
    assert S[:, 0].min() < -0.03 and abs(np.abs(S[:, 1]).max() - 0.141) < 0.004      # REAR: nut out to 0.139


def test_muffler_outlet_is_where_the_rear_photo_has_it():
    """REAR: outlet at about pixel (2202, 788)."""
    u, v = cams.CAMS["rear"].project(dc.OUTLET)[0]
    assert abs(u - 2202) < 6 and abs(v - 788) < 6, (u, v)


def test_muffler_top_reaches_the_left_photo_line(V):
    """LEFT: the muffler's top edge at the rear is at row 878 near column 2950 (it was 20 px too low before)."""
    E = V["exhaust"]
    rear = E[E[:, 0] < 0.03]
    v = cams.CAMS["left"].project(rear)[:, 1].min()
    assert abs(v - 878) < 8, v


def test_rear_tyre_has_room(V):
    """Nothing of the chassis inside the rear tyre's sweep (tyre 105 mm wide, 12 mm of air each side)."""
    for name in ("swingarm", "linkage", "shock", "exhaust", "subframe", "frame", "rear_brake"):
        P = V[name]
        near = (np.hypot(P[:, 0], P[:, 2] - parts.R_REAR) < parts.R_REAR + 0.012) & (np.abs(P[:, 1]) < 0.0525 + 0.012)
        assert not near.any(), (name, int(near.sum()))


def test_link_lengths_match_both_profile_photos():
    """Pro-Link bolts seen from both sides: link 144 mm, arm 49 and 78 mm."""
    assert abs(np.linalg.norm(dc.LINK_B - dc.F_LINK) - 0.144) < 0.004
    assert abs(np.linalg.norm(dc.LINK_T - dc.LINK_B) - 0.049) < 0.004
    assert abs(np.linalg.norm(dc.LINK_T - dc.SHOCK_A) - 0.078) < 0.004
