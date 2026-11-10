"""Fast checks of detail_engine.py against the spec table, the photo measurements and the audit's rules.
python3 -m pytest -q test_detail_engine.py        (python3 test_detail_engine.py lists the loose pieces)"""
import numpy as np
from scipy.spatial import cKDTree

import detail_engine as d
import plastics

MESH = {name: fn() for name, fn in d.PARTS.items()}


def pieces(mesh):
    """Loose pieces of a mesh (connected through shared vertices): list of vertex index arrays."""
    parent = np.arange(len(mesh.V))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for f in mesh.F:
        r = find(f[0])
        for i in f[1:]:
            parent[find(i)] = r
    root = np.array([find(i) for i in range(len(mesh.V))])
    return [np.flatnonzero(root == r) for r in np.unique(root)]


def floating(mesh, tol=0.004):
    """audit.py's rule inside one object: a loose piece with no vertex of another piece within TOL."""
    V = np.asarray(mesh.V, float)
    out = []
    for idx in pieces(mesh):
        rest = np.ones(len(V), bool)
        rest[idx] = False
        gap = cKDTree(V[rest]).query(V[idx])[0].min() if rest.any() else 9.0
        if gap >= tol:
            out.append((round(float(gap) * 1000, 1), len(idx), np.round(V[idx].mean(axis=0), 3).tolist()))
    return sorted(out, reverse=True)


def volume(mesh):
    V = np.asarray(mesh.V, float)
    return abs(sum(np.dot(V[f[0]], np.cross(V[f[i]], V[f[i + 1]])) for f in mesh.F for i in range(1, len(f) - 1)) / 6)


def test_vertex_budget():
    assert sum(len(m.V) for m in MESH.values()) <= 80000


def test_spec_bore_and_throttle():
    assert d.BORE == 0.079 and d.TB_BORE == 0.044                       # SPEC 79.0 mm bore, 44 mm throttle bore
    assert d.CYL_Y[1] - d.CYL_Y[0] >= d.BORE + 0.030                    # room for the liner and the water jacket
    assert 0.060 <= d.H_HEAD - d.H_BASE <= 0.085                        # SPEC stroke 50.9: a cylinder 60..85 mm tall
    assert abs(np.degrees(d.LEAN) - 14.0) < 0.01                        # photo; SPEC 9 deg (reported)


def test_bolt_counts_from_the_photos():
    assert (len(d.L_COVER_BOLTS), len(d.CLUTCH_BOLTS), len(d.PUMP_BOLTS), len(d.FILTER_BOLTS)) == (8, 6, 4, 2)


def test_exhaust_port():
    assert abs(d.PORT[1]) < 1e-9 and 0.88 < d.PORT[0] < 0.92 and 0.59 < d.PORT[2] < 0.65
    assert d.PORT_DIR[0] > 0.9 and d.PORT_DIR[2] < 0


def test_tank_capacity_and_visible_top():
    litres = volume(d.tank_hull()) * 1000
    assert 4.0 <= litres <= 7.5, litres                                 # SPEC 6.3 L (see the report)
    b, hw, zl, zu, zs, zt, yp = d.tank_section(d.CAP[0])
    assert 0.045 <= yp <= d.TANK_GAP                                    # TOP: titanium shows to 0.053..0.060
    assert zt - zs > 0.02 and abs(d.CAP[0] - 0.883) < 0.003 and abs(d.CAP[1]) < 0.005


def test_tank_clears_the_frame():
    """detail_chassis.py's spars: the lobe hangs 2 mm inside them, the body rests 2 mm above them."""
    for x in np.linspace(0.745, 0.975, 40):
        b, hw, zl, zu, zs, zt, yp = d.tank_section(x)
        yin, top = d._spar(x)
        assert b <= yin - 0.002
        assert zu >= top + 0.002 or hw <= yin - 0.002


def test_radiators_inside_the_shroud_plan():
    m = MESH["radiators"]
    V = np.asarray(m.V, float)
    mat = np.array(m.M)
    used = np.zeros(len(V), bool)
    for f, mm in zip(m.F, mat):
        if mm in ("radiator", "alu_cast", "louvre"):
            used[list(f)] = True
    for side in (1, -1):
        plan = plastics._shroud_plan(side)
        P = V[used & (V[:, 1] * side > 0.07) & (V[:, 2] >= 0.70)]
        lim = np.array([float(plan(float(x))) for x in P[:, 0]]) - 0.008
        assert (np.abs(P[:, 1]) <= lim + 1e-4).all(), float((np.abs(P[:, 1]) - lim).max())
    assert V[used][:, 2].max() < 0.925                                  # under the shroud decks (z 0.93 at x 1.06)


def test_nothing_hangs_far_from_its_seat():
    """Coarse and fast (vertex to vertex): a bolt that misses its boss by a centimetre. audit.py measures the real
    4 mm rule to surfaces."""
    for name, m in MESH.items():
        assert not floating(m, 0.012), (name, floating(m, 0.012)[:5])


def test_no_zero_area_faces():
    for name, m in MESH.items():
        V = np.asarray(m.V, float)
        for f in m.F:
            p = V[list(f)]
            assert max(np.linalg.norm(np.cross(p[k] - p[0], p[k + 1] - p[0])) for k in range(1, len(p) - 1)) > 1e-12, name


def test_sprocket_pocket():
    """The left case, the shift shaft and the guard go round detail_wheels.py's sprocket and chain."""
    from parts import CS, chain_top
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        for r in (0.0, 0.020, 0.0417):
            assert d.case_face(CS[0] + r * np.cos(a), CS[2] + r * np.sin(a), True) <= CS[1] - d.CHAIN_HALF - 0.002
    for x in (0.596, 0.604, 0.612):
        assert d.case_face(x, float(chain_top(x)), True) <= CS[1] - d.CHAIN_HALF - 0.002
        assert d.case_face(x, 0.428 + 0.3649 * (x - 0.604), True) <= CS[1] - d.CHAIN_HALF - 0.002
    assert d.GUARD_Y[0] >= CS[1] + d.CHAIN_HALF + 0.002
    assert np.hypot(d.SHIFT[0] - CS[0], d.SHIFT[2] - CS[2]) > 0.0417 + 0.0065 + 0.004


def test_inside_the_frame_plates():
    """No engine vertex within 2 mm of the frame's plates (outline, pivot boss, bracket): the frame is measured."""
    V = np.asarray(MESH["engine"].V, float)
    fin = np.array([d.frame_in(x) for x in V[:, 0]])
    k = np.flatnonzero((np.abs(V[:, 1]) > fin - 0.002) & (np.abs(V[:, 1]) < fin + d.T_FR + 0.002) & (V[:, 0] < 0.82))
    hanger = (V[:, 0] > 0.66) & (V[:, 0] < 0.75) & (V[:, 2] > 0.62) & (V[:, 2] < 0.78) & (np.abs(V[:, 1]) < fin - 0.0003)
    bad = [V[i] for i in k if not hanger[i] and d.under_frame(V[i, 0], V[i, 2], 0.002)]   # the head hangers seat on it
    assert not bad, (len(bad), np.round(bad[0], 3))


def test_cable_anchors():
    assert 0.10 < d.CLUTCH_ARM_END[1] < 0.125 and d.THROTTLE_DRUM[1] < -0.03


if __name__ == "__main__":
    for name, m in MESH.items():
        print(name, len(m.V), "verts;", len(pieces(m)), "pieces; floating:", floating(m)[:14])
    print("tank litres", round(volume(d.tank_hull()) * 1000, 2), "section at cap", np.round(d.tank_section(d.CAP[0]), 3))
