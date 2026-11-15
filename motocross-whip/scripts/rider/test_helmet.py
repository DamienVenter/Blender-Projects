"""Tests of Damien's helmet and goggle (helmet.py). Needs tools/fetch_makehuman.sh.

python3 -m pytest -q test_rider.py test_helmet.py
"""
import json
import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as B      # noqa: E402
import helmet as H    # noqa: E402


@pytest.fixture(scope="module")
def body():
    d = B.build()
    return {k: d[k] for k in d}


@pytest.fixture(scope="module")
def built(body, tmp_path_factory):
    parts, info, (R, t) = H.build(body)
    path = str(tmp_path_factory.mktemp("helmet") / "helmet.npz")
    H.write_npz(path, parts, H.extras(body, parts, (R, t)))
    return dict(parts={P.name: P for P in parts}, info=info, R=R, t=t, path=path)


def tris(P):
    out = []
    for f in P.F:
        for i in range(1, len(f) - 1):
            out.append([f[0], f[i], f[i + 1]])
    return np.array(out)


def winding(points, V, T, chunk=256):
    """Generalised winding number of each point w.r.t. a closed triangle mesh (1 inside, 0 outside)."""
    A, Bv, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    out = np.zeros(len(points))
    for s in range(0, len(points), chunk):
        p = points[s:s + chunk, None, :]
        a, b, c = A[None] - p, Bv[None] - p, C[None] - p
        la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
        num = np.einsum("ijk,ijk->ij", a, np.cross(b, c))
        den = la * lb * lc + np.einsum("ijk,ijk->ij", a, b) * lc + np.einsum("ijk,ijk->ij", b, c) * la + \
            np.einsum("ijk,ijk->ij", c, a) * lb
        out[s:s + chunk] = np.arctan2(num, den).sum(1) / (2 * np.pi)
    return out


def test_size_from_his_head(body):
    """Leatt sizes by head girth; his 59.2 cm head is a size L (59 to 60 cm)."""
    c = H.head_circumference(body)
    assert 0.585 < c < 0.600
    assert H.size_for(c) == "L"


def test_shell_dimensions_from_leatt_photos(built):
    """Outer shell to the strap-scaled photos: width 255 to 262 mm (back view), shell length chin to back
    365 to 372 mm, overall length with the visor (side view, 371 mm) within 4 mm."""
    Vo, Fo, prof = H.shell_outer()
    assert 0.255 < 2 * Vo[:, 0].max() < 0.262
    assert 0.362 < np.ptp(Vo[:, 1]) < 0.372
    vis = H.visor_surface(prof)
    total = max(Vo[:, 1].max(), vis[..., 1].max()) - min(Vo[:, 1].min(), vis[..., 1].min())
    assert abs(total - 1494 * H.S) < 0.004


def test_shell_is_closed_and_symmetric(built):
    P = built["parts"]["helmet_shell"]
    E = {}
    for f in P.F:
        for a, b in zip(f, np.roll(f, -1)):
            k = (min(a, b), max(a, b))
            E[k] = E.get(k, 0) + 1
    assert all(v == 2 for v in E.values())
    D = {}
    for f in P.F:
        for a, b in zip(f, np.roll(f, -1)):
            D[(a, b)] = D.get((a, b), 0) + 1
    assert all(v == 1 and D.get((b, a)) == 1 for (a, b), v in D.items())        # consistently wound
    V = (P.V - built["t"]) @ built["R"]                 # back in the helmet frame
    m = V.copy(); m[:, 0] *= -1
    from scipy.spatial import cKDTree
    assert cKDTree(V).query(m)[0].max() < 1e-6


def normal_turn_variation(V, F, region):
    """Normal turn along each edge (|n_i - n_j| / |v_i - v_j|, 1/m) less the median over the edges round its two
    vertices: a ridge or a scallop stands out, a fair surface stays near zero."""
    N = H.normals(V, F)
    E = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
    E = E[region[E[:, 0]] & region[E[:, 1]]]
    k = np.linalg.norm(N[E[:, 0]] - N[E[:, 1]], axis=1) / np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    inc = {}
    for e, (a, b) in enumerate(E):
        inc.setdefault(a, []).append(e)
        inc.setdefault(b, []).append(e)
    med = np.array([np.median(k[inc[a] + inc[b]]) for a, b in E])
    return E, k - med


def test_shell_is_fair_at_the_crown_back():
    """Round 2 (decision 44): main's crown back carried ridges 20 mm either side of the centre line (the width
    field's distance to a 3 mm sampled rim) and slope steps at the width tables' knots, seen as banded, spiky
    reflections in Leatt's back view (px 860 to 1060). Behind y = 30 mm and above z = -130 mm, 8 mm or more from
    the free edges, no edge's normal turn may stand more than 120 /m above its neighbours' (main: 190 /m)."""
    from scipy.spatial import cKDTree
    V, F, _ = H.shell_outer()
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    free = cKDTree(V[np.unique(u[c == 1])]).query(V)[0] > 0.008
    E, dk = normal_turn_variation(V, F, (V[:, 1] > 0.03) & (V[:, 2] > -0.13) & free)
    assert len(E) > 5000
    worst = V[E[np.argmax(dk)]].mean(0) * 1000
    assert dk.max() < 120.0, f"normal turn {dk.max():.0f} /m above its neighbours at {np.round(worst)} mm"



def test_shell_outline_through_the_solved_cameras():
    """Round 3 (decision 46): the shell's outline in Leatt's back views (Pinata, V25 white, MY27) and top view, through
    the cameras solved together with the shared landmarks (research/helmet-ba.json, helmet_ba.py). Each 10 mm band of
    height (back views) and 20 mm band of length (top view) lies within 1.5 mm of the photo's outline, median over
    the band. Main (round 2 tables): 1 to 3 mm too narrow below z = -50 mm and 1.3 to 3.6 mm too wide from z = -40 to
    +10 mm, 3.6 mm worst (V25 white)."""
    import helmet_ba as BA
    bands = BA.outline_bands()
    assert set(bands) == set(BA.BAND_VIEWS) and all(len(b) >= 8 for b in bands.values())
    for v, b in bands.items():
        z, off = max(b.items(), key=lambda kv: abs(kv[1]))
        assert abs(off) < 1.5, f"{v}: the outline {off:+.1f} mm off the photo's at band {z} mm"

def test_vents_are_moulded_away_from_the_front(built):
    """Round 3 (decision 46): main's crown vents were flat painted triangles; Leatt's top photo shows a raised white
    insert round a triangle lattice over the dark opening. The rear exhaust slots carry a wire mesh (round 4) and the
    lower rear vents a raised white piece drawn to a point (helmet_detail.py, from the photos' px through the print's
    cameras). The part is mirror symmetric and stands on the shell (no more than its height above it, no more than
    SINK under it); the crown rims stand 1.5 mm proud; each vent with its lattice (10 bars or more) lies inside its
    insert's outline in the top photo (within 5 px); the lower piece runs 40 mm or more down the shell."""
    from scipy.spatial import cKDTree
    import helmet_art as A
    import helmet_detail as D
    from matplotlib.path import Path
    assert "helmet_vents" in built["parts"], "no moulded vents (main: painted only)"
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]                 # back in the helmet frame
    assert cKDTree(V).query(V * [-1, 1, 1])[0].max() < 1e-6
    assert set(P.M) == {D.MAT, D.MAT_INSERT, D.MAT_DARK, D.MAT_MESH, D.MAT_GRIP, D.MAT_GRIP_EDGE, D.MAT_GRIP_RIDGE}
    Vo, Fo, _ = H.shell_outer()
    No = H.normals(Vo, Fo)
    j = cKDTree(Vo).query(V)[1]
    h = np.sum((V - Vo[j]) * No[j], 1)                  # height above the shell
    assert h.min() > -D.SINK - 0.0004 and h.max() < D.LOW_PIECE_H + 0.0002
    ins = np.zeros(len(V), bool)
    for f, m in zip(P.F, P.M):
        if m == D.MAT_INSERT:
            ins[f] = True
    crown = ins & (V[:, 0] < 0)                         # the vent on his right, as in the top photo
    assert abs(h[crown].max() - D.CROWN_RIM_H) < 0.0002
    uv = H.cam_project(H.PRINT_CAMS["top"], V[crown])[0]
    q = np.asarray(A.CROWN_VENT["insert"], float)        # the insert's outline: four corners, traced by eye
    seg = [(q[i], q[(i + 1) % 4]) for i in range(4)]
    d = np.min([np.linalg.norm(uv - (a + np.clip((uv - a) @ (b - a) / ((b - a) @ (b - a)), 0, 1)[:, None] * (b - a)),
                               axis=1) for a, b in seg], 0)
    assert np.all(Path(q).contains_points(uv) | (d < 5.0))    # outside it by 5 px (1.2 mm) at most
    assert len(D.lattice_lines(A.CROWN_VENT)) >= 10
    low = ~ins & (V[:, 2] < -0.03)
    assert np.ptp(V[low & (V[:, 0] > 0), 2]) > 0.04      # the lower piece runs 40 mm or more down the shell

def test_crown_vent_outline_and_lattice():
    """Round 4 (decision 50): Leatt's crown vent (top photo at 3x) is a rounded parallelogram in a thin, even
    surround, over a lattice of near-equilateral triangles. Main's insert and opening were two quads traced by eye:
    the surround 6 to 12 px wide by side (1.5 to 3 mm), the opening's corners sharp, the lattice's cells 21 and 25 px
    a side 108 deg apart. Now (top photo px, 0.248 mm/px at the vent): every side's surround 8 px within 1 px, the
    opening's opposite sides within 8 deg of parallel, its corners rounded (no turn over 30 deg between outline
    points 2 px apart), the cells' three sides within 3 % of one length and 120 deg apart within 3 deg."""
    import helmet_art as A
    import helmet_detail as D
    v = A.CROWN_VENT
    op, ins = (np.asarray(v[k], float) for k in ("opening", "insert"))
    for i in range(4):
        a, b = op[i], op[(i + 1) % 4]
        t = (b - a) / np.linalg.norm(b - a)
        gap = abs((0.5 * (ins[i] + ins[(i + 1) % 4]) - 0.5 * (a + b)) @ np.array([-t[1], t[0]]))
        assert abs(gap - 8.0) < 1.0, f"side {i}: the surround {gap:.1f} px wide"
    d = np.roll(op, -1, 0) - op
    ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    for i in (0, 1):
        assert abs((ang[i] - ang[i + 2]) % 360 - 180) < 8.0, f"sides {i}, {i + 2} not parallel"
    o = D.resample_loop(A.vent_outline("opening"), 2.0)
    e = np.roll(o, -1, 0) - o
    th = np.arctan2(e[:, 1], e[:, 0])
    turn = np.degrees(np.abs((np.diff(np.r_[th, th[:1]]) + np.pi) % (2 * np.pi) - np.pi))
    assert turn.max() < 30.0, f"a corner turns {turn.max():.0f} deg at once"
    a, b = np.asarray(v["a"], float), np.asarray(v["b"], float)
    sides = np.linalg.norm([a, b, a + b], axis=1)
    assert np.ptp(sides) / sides.mean() < 0.03, f"cell sides {np.round(sides, 1)} px"
    cell = np.degrees(np.arccos(a @ b / (sides[0] * sides[1])))
    assert abs(cell - 120.0) < 3.0, f"cell sides {cell:.1f} deg apart"


def test_rear_pieces_soft_slot_edge_flat_plate_point_and_mesh(built):
    """Round 4 (decision 50), from Leatt's back photos at 2x to 4x (Pinata, V25 white, Royal). The rear exhaust
    slot's edge rolls softly into the slot, with no rim: main stood a lip 1.0 mm proud that read as a bright rim (and
    so did 0.4 and 0.2 mm, rendered at 3x); now nothing of the slot stands over the shell but its mesh, under 0.5 mm.
    The rear lower piece is a flat plate with crisp edges, drawn to a point:
    its top within 0.25 mm of 2 mm over the shell; its shading broken at its edges (each band its own vertices:
    away from the point, under 10 % of its vertices join faces more than 20 deg apart; main's round loop 69 %); its
    top's point through the back camera within 3 px of the photo's (481.5, 1594.5). Both slots carry a wire mesh
    (main: none)."""
    from scipy.spatial import cKDTree
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]                 # back in the helmet frame
    Vo, Fo, _ = H.shell_outer()
    No = H.normals(Vo, Fo)
    j = cKDTree(Vo).query(V)[1]
    h = np.sum((V - Vo[j]) * No[j], 1)                  # height above the shell
    mats = list(P.M)
    left = V[:, 0] > 0
    slot = left & (V[:, 1] > 0.08) & (V[:, 2] > 0.03) & (V[:, 2] < 0.10)
    low = left & (V[:, 2] < -0.03)

    def faces(mat, region):
        return [list(f) for f, m in zip(P.F, mats) if m == mat and region[list(f)].all()]
    sv = np.unique(np.concatenate([list(f) for f in P.F]))
    sv = sv[slot[sv]]
    assert len(sv) > 100 and h[sv].max() < 0.0005, f"the slot's edge {1000 * h[sv].max():.2f} mm over the shell"
    fl = faces(D.MAT, low)
    pv = np.unique(np.concatenate(fl))
    fn = np.array([np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]) for f in fl])
    fn /= np.linalg.norm(fn, axis=1)[:, None]
    top = np.array([fn[i] @ No[j[f]].mean(0) > math.cos(math.radians(20)) for i, f in enumerate(fl)])
    tv = np.unique(np.concatenate([fl[i] for i in np.nonzero(top)[0]]))
    assert np.ptp(h[tv]) < 0.00025 and abs(h[tv].mean() - 0.002) < 0.00025, "the plate's top is not flat at 2 mm"
    tip = pv[np.argmin(V[pv, 2])]
    by_v = {}
    for i, f in enumerate(fl):
        for k in f:
            by_v.setdefault(k, []).append(i)
    spread = [np.degrees(np.arccos(np.clip((fn[fi] @ fn[fi].T).min(), -1, 1))) for k, fi in by_v.items()
              if np.linalg.norm(V[k] - V[tip]) > 0.004]
    assert np.mean(np.array(spread) > 20.0) < 0.10, "the plate's edges are shaded round"
    uv = H.cam_project(H.PRINT_CAMS["back"], V[tip][None])[0][0]
    assert np.linalg.norm(uv - [481.5, 1594.5]) < 3.0, f"the point at {np.round(uv, 1)} px in Leatt's back photo"
    for region in (slot, low):
        assert len(faces(D.MAT_MESH, region)) > 100, "no wire mesh in a slot"


def shading_normals(V, F):
    """Vertex normals as Blender's smooth shading makes them: face normals weighted by the corner angles."""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    fn /= np.linalg.norm(fn, axis=1)[:, None]
    vn = np.zeros_like(V)
    for k in range(3):
        a, b, c = V[F[:, k]], V[F[:, (k + 1) % 3]], V[F[:, (k + 2) % 3]]
        e1, e2 = b - a, c - a
        ang = np.arccos(np.clip(np.sum(e1 * e2, 1) / (np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1)), -1, 1))
        np.add.at(vn, F[:, k], fn * ang[:, None])
    return vn / np.linalg.norm(vn, axis=1)[:, None]


def test_crown_shading_follows_the_surface():
    """Round 3 (decision 46): a purple and white ladder of clear-coat reflections ran along the print's stem in
    the top view. Main's first vertices off the crown's centre line stood 7 or 14 mm out by turns (rings graded by
    the brow's roundness, thinned against the 3 mm outline samples): one strip of fan triangles across the crown,
    its shading normals 3 to 8 deg off the width field's own. Within 35 mm of the centre line over the crown, every
    shading normal must lie within 1.5 deg of the surface's."""
    V, F, prof = H.shell_outer()
    sel = (V[:, 2] > 0.08) & (np.abs(V[:, 0]) > 0.0005) & (np.abs(V[:, 0]) < 0.035) & prof.inside(V[:, 1:])
    N = shading_normals(V, F)[sel]
    P, h = V[sel], 1e-6
    dy = (H.half_width(prof, P[:, 1] + h, P[:, 2]) - H.half_width(prof, P[:, 1] - h, P[:, 2])) / (2 * h)
    dz = (H.half_width(prof, P[:, 1], P[:, 2] + h) - H.half_width(prof, P[:, 1], P[:, 2] - h)) / (2 * h)
    Na = np.c_[np.sign(P[:, 0]), -dy, -dz]
    Na /= np.linalg.norm(Na, axis=1)[:, None]
    N *= np.sign(np.median(np.sum(N * Na, 1)))
    err = np.degrees(np.arccos(np.clip(np.sum(N * Na, 1), -1, 1)))
    assert sel.sum() > 300
    worst = P[np.argmax(err)] * 1000
    assert err.max() < 1.5, f"shading normal {err.max():.1f} deg off the surface's at {np.round(worst)} mm"


def port_edge_px(view, rows, port=None):
    """The face port's rear edge on the near side through one of Leatt's cameras: the loop's rightmost crossing
    of each image row (iso-left: the helmet's left side, its back to the right)."""
    V, F, _ = H.shell_outer(H.Profile(port=port))
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    B = u[c == 1]
    # the port's loop: free edges above the lower edge (z > -0.09 m at their mid points) and ahead of y = 0
    m = V[B].mean(1)
    B = B[(m[:, 2] > -0.09) & (m[:, 1] < 0.0) & (m[:, 0] > 0)]
    q = H.cam_project(H.PRINT_CAMS[view], V)[0]
    out = []
    for r in rows:
        a, b = q[B[:, 0]], q[B[:, 1]]
        hit = (a[:, 1] - r) * (b[:, 1] - r) <= 0
        t = (r - a[hit, 1]) / (b[hit, 1] - a[hit, 1] + 1e-12)
        out.append(float(np.max(a[hit, 0] + t * (b[hit, 0] - a[hit, 0]))))
    return np.array(out)


def test_face_port_edge_on_leatt_iso_left():
    """The shell's port edge (the rubber trim's inner edge) where Leatt's Pinata iso-left photo shows it, picked on a
    1:1 crop at rows 830 to 1040: x 1195, 1193, 1189, 1183 px, seen through the solved iso-left camera (decision 47;
    round 2 checked it through its own single-photo camera, which put the edge 16 to 18 mm too far back). The built
    port (helmet.PORT): main's followed the side photo's notch (the cheek pads), 16 to 23 mm ahead, and the print's
    black trim and grip panel spread over the shell there."""
    rows = [830, 900, 970, 1040]
    err = port_edge_px("isoleft", rows) - np.array([1195.0, 1193.0, 1189.0, 1183.0])
    assert np.all(np.abs(err) < 12.0), f"port edge off Leatt's iso-left by {np.round(err, 1)} px"


def test_visor_top_line_on_the_royal_side_photo():
    """Joint front fit phase 2 (decision 51): the visor's top silhouette in Leatt's Royal side photo through the
    solved Royal camera (research/helmet-ba.json), every 8 px column along the visor where the crown does not stand
    above it: within 6 px (1.5 mm) on average, rms under 8 px. Main (round 4's tables): 21.6 px high on average (rms
    22.3): the tip 15 px high and the arch's fall to the side edges too slow, so the near wing, lifted by
    perspective, stood above the photo's line. Fitted (VISOR_TOP, VISOR_ARCH) on Royal and MY27 left together."""
    import helmet_ba as BA
    cam = BA.solved_cameras()["royal_left"]
    m = BA.photo_mask("royal_left")
    Vo, Fo, prof = H.shell_outer()
    G = H.visor_surface(prof)
    nr, nc, _ = G.shape
    T, Cc = np.meshgrid(np.linspace(0, nr - 1, nr * 3), np.linspace(0, nc - 1, nc * 4), indexing="ij")
    uv = BA.project(cam, H.grid_at(G, Cc.ravel(), T.ravel()))
    us = BA.project(cam, Vo[Fo].mean(1))
    res = []
    for x in range(int(uv[:, 0].min()) + 6, int(uv[:, 0].max()) - 6, 8):
        sel = np.abs(uv[:, 0] - x) < 4
        ss = np.abs(us[:, 0] - x) < 4
        if not sel.any() or (ss.any() and us[ss, 1].min() < uv[sel, 1].min() - 2):
            continue                                    # the crown stands above the visor here
        top = min(np.nonzero(m[:, xx])[0].min() for xx in range(x - 3, x + 4) if m[:, xx].any())
        res.append(uv[sel, 1].min() - top)
    r = np.array(res)
    assert len(r) >= 40
    assert abs(r.mean()) < 6.0 and np.sqrt(np.mean(r ** 2)) < 8.0, \
        f"visor top {r.mean():+.1f} px off Royal's on average (rms {np.sqrt(np.mean(r ** 2)):.1f})"


def test_trim_rolls_into_the_port(body):
    """Phase 2 (decision 51): the port's rubber trim rolls into the opening. In Leatt's iso photos the trim's band at
    the port's side, from its crest to where it meets the liner, reads 9 to 14 mm wide (the coordinator's 1:1 review;
    Pinata iso-left at 2x: the roll turns at the crest and runs about 15 mm in). Through the solved iso-left camera
    the roll's projected width at the port's side (|z| < 40 mm, x > 50 mm; crest to its seam with the pads, item 2)
    has its median within 9 to 14 mm, and the rolled edge keeps 1.5 mm off his skin. Main: 4.4 to 7.7 mm (a 4 mm
    round strip), median 6.2."""
    from scipy.spatial import cKDTree
    Vo, Fo, prof = H.shell_outer()
    R, tr, _ = H.fit_on_head(body, Vo, Fo, prof)
    skin = (body["V"][H.head_skin(body)] - tr) @ R
    _, _, strips = H.shell_solid(Vo, Fo, skin)
    cam = H.PRINT_CAMS["isoleft"]
    w, near = [], np.inf
    for loop, rings in strips:
        if rings[0][:, 1].max() > 0.0:
            continue                                    # the rear slots' strips
        O = rings[0]
        for k in np.nonzero((O[:, 0] > 0.05) & (O[:, 1] > -0.08) & (np.abs(O[:, 2]) < 0.04))[0]:
            q, d = H.cam_project(cam, np.array([r[k] for r in rings[:H.RIM_RINGS]]))
            w.append((q[:, 0].max() - q[:, 0].min()) / (cam["f"] / d.mean() / 1000))
        near = min(near, cKDTree(skin).query(np.vstack(rings))[0].min())
    w = np.array(w)
    assert len(w) >= 5
    assert 9.0 <= np.median(w) <= 14.0, \
        f"trim band {w.min():.1f} to {w.max():.1f} mm (median {np.median(w):.1f})"
    assert near > 0.0015, f"the trim's roll {1000 * near:.1f} mm off his skin"


def test_grip_panels_moulded_beside_the_port(built):
    """Phase 2 (decision 51): beside the port's rear edges, from the brow's corner to the chin bar's top, a moulded
    grip panel on each side (Leatt's Pinata iso photos): its own dark grey (95 92 97, de-lit from the photo; neither
    the trim's black nor the print), standing GRIP_H proud of the shell, 18 to 36 mm wide (the photo through the
    solved iso-left camera: 20 to 35 mm), its top carrying the sandblast grain's UVs, and on it the triangle relief
    moulded as ridges GRIP_RIDGE_H high over the whole panel (cells 7.3 mm). Main: no panel (the print's black and the trim)."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    top = [k for k, m in enumerate(P.M) if m == D.MAT_GRIP]
    assert top and any(m == D.MAT_GRIP_EDGE for m in P.M)
    Vt = V[np.unique(np.concatenate([P.F[k] for k in top]))]
    for s in (1, -1):
        S = Vt[Vt[:, 0] * s > 0]
        assert len(S) > 100
        for z in np.arange(-0.055, -0.0, 0.01):
            row = S[np.abs(S[:, 2] - z) < 0.002]
            assert len(row) and 0.018 < np.ptp(row[:, 1]) < 0.036, f"panel {1000 * np.ptp(row[:, 1]):.0f} mm at z {z}"
    uv = np.array([u for k in top for u in P.UV[k]])
    assert np.ptp(uv[:, 1]) > 2.0                        # the relief repeats along the panel
    g = H.MATERIALS[D.MAT_GRIP]
    assert g["rgb"] == [95, 92, 97] and os.path.exists(os.path.join(H.TEXDIR, g["normal"]))
    Vo, Fo, _ = H.shell_outer()
    Q, NQ = D.Shell(Vo, Fo).snap(Vt)
    h = np.sum((Vt - Q) * NQ, 1)                          # the top's height over the shell
    assert abs(np.median(h) - D.GRIP_H) < 0.0002 and h.min() > 0.0, f"panel top {1000 * np.median(h):.2f} mm proud"
    rid = [k for k, m in enumerate(P.M) if m == D.MAT_GRIP_RIDGE]
    Vr = V[np.unique(np.concatenate([P.F[k] for k in rid]))]
    Q, NQ = D.Shell(Vo, Fo).snap(Vr)
    hr = np.sum((Vr - Q) * NQ, 1)
    top = hr[hr > D.GRIP_H + 0.5 * D.GRIP_RIDGE_H]
    assert abs(np.median(top) - D.GRIP_H - D.GRIP_RIDGE_H) < 0.0002, f"ridges {1000 * np.median(top):.2f} mm proud"
    for s in (1, -1):                                    # over the whole panel, each side
        R = Vr[(Vr[:, 0] * s > 0) & (hr > D.GRIP_H + 0.5 * D.GRIP_RIDGE_H)]
        assert len(R) > 400 and np.ptp(R[:, 1]) > 0.015 and np.ptp(R[:, 2]) > 0.05


def test_pads_fill_the_port_to_the_side_notch(body):
    """Phase 2 (decision 51): past the trim's roll (TRIM_DEPTH from the crest) the port's rolled edge is the comfort
    liner's pad face (knit mesh, red stitching: helmet_pad). Leatt's Royal side photo shows the cheek pads filling the
    port ahead of the shell's cut edge as far as its notch (FACE_PORT as traced): at every 5 mm of height from z -45
    to 0 mm the pads' front on his left stands within 5 mm of the notch's line (main: the cut edge's trim alone, 12 to
    24 mm behind it), the pads keep 1.5 mm off his skin, and the goggle's lens stays clear (test above)."""
    from scipy.spatial import cKDTree
    Vo, Fo, prof = H.shell_outer()
    R, tr, _ = H.fit_on_head(body, Vo, Fo, prof)
    skin = (body["V"][H.head_skin(body)] - tr) @ R
    _, _, strips = H.shell_solid(Vo, Fo, skin)
    port = [np.array(rings) for loop, rings in strips if rings[0][:, 1].max() < 0.0]
    assert len(port) == 1
    pts = port[0].reshape(-1, 3)
    S = H.px2h(H.FACE_PORT[7:21])                         # the notch's chin bar top and rear edge (y, z)
    notch = S[np.argsort(S[:, 1])]
    for z in np.arange(-0.045, 0.001, 0.005):
        sel = pts[(pts[:, 0] > 0.03) & (np.abs(pts[:, 2] - z) < 0.002)]
        y_notch = np.interp(z, notch[:, 1], notch[:, 0])
        front = sel[:, 1][sel[:, 1] > y_notch - 0.02].min()
        assert abs(front - y_notch) < 0.005, f"pads' front {1000 * (front - y_notch):+.1f} mm off the notch at z {z}"
    near = cKDTree(skin).query(pts)[0].min()
    assert near > 0.0015, f"pads {1000 * near:.1f} mm off his skin"
    # the pads' face is smooth round the port: its bow at mid depth changes by under 2.5 mm between neighbouring
    # edge points (3.5 mm apart; the first version's per-ray reach jumped 10 to 15 mm at the notch's corners)
    pad = port[0][H.RIM_RINGS - 1:]
    bow = np.linalg.norm(pad[len(pad) // 2] - (pad[0] + pad[-1]) / 2, axis=1)
    assert np.abs(np.diff(np.r_[bow, bow[:1]])).max() < 0.0025, f"pad bow steps {1000 * np.abs(np.diff(bow)).max():.1f} mm"
    assert H.MATERIALS["helmet_pad"]["image"] == "helmet_pad_mesh.png"
    assert "normal" in H.MATERIALS["helmet_roll"]


def test_chin_bar_outline_on_the_royal_side_photo():
    """Phase 2 (decision 51): the chin bar's outline in Leatt's Royal side photo through the solved Royal camera
    (signed distance to the photo's silhouette, mm at the point's depth): the chin front (the centre plane's rim,
    CHIN_FRONT's points 3 to 21: the chin's face, its nose and the bar's top front edge) and the chin bar's lower
    edge from u 510 to 900 px (the near side's free edge) lie within 2 mm of the photo's outline (the fit takes the
    three side photos' mean; at the mouthpiece's step they spread by 4 mm). Main: the chin
    front 2.8 to 6.1 mm outside it (the bar stood forward and its top edge high), the chin bar's lower edge 1 to 2.5
    mm below it. MY27's left and right photos read the same within 2 mm (decision 51). Behind the ear the side
    photos put the lower edge 2 to 3 mm higher still, but the back views' width at z = -130 mm holds it there (the
    outline test above): left for the next solve."""
    import helmet_ba as BA
    cam = BA.solved_cameras()["royal_left"]
    F = BA.sdf("royal_left")

    def off(X):
        return BA.sample(F, BA.project(cam, X)) * ((X - cam["C"]) @ cam["R"][2]) / cam["f"] * 1000

    YZ = H.px2h(H.CHIN_FRONT)[3:22]
    chin = off(np.c_[np.zeros(len(YZ)), YZ])
    Vo, Fo, _ = H.shell_outer()
    E = np.sort(np.vstack([Fo[:, [0, 1]], Fo[:, [1, 2]], Fo[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    b = Vo[np.unique(u[c == 1])]
    y0, y1 = H.px2h([(510, 1500), (900, 1500)])[:, 0]
    low = off(b[(b[:, 0] > 0.02) & (b[:, 2] < -0.09) & (b[:, 1] > y0) & (b[:, 1] < y1)])
    assert len(low) >= 10
    assert np.abs(chin).max() < 2.0, f"chin front up to {chin[np.argmax(np.abs(chin))]:+.1f} mm off Royal's outline"
    assert np.abs(low).max() < 2.0, f"lower edge up to {low[np.argmax(np.abs(low))]:+.1f} mm off Royal's outline"


def test_fit_on_his_head(built):
    """The helmet on his head from the liner build-up (decision 47): Leatt TF 172's EPS length (M/L 287 mm) less his
    head's, shared front and back, plus the wall, is the shell's stand-off at his forehead, back and crown (main: 39.0,
    47.9 and 48.2 mm from two rules, the brow 40 mm above his eyes and 32 mm ahead of his forehead); the sides at
    least that (the cheek pads and the EPS's flare); the port's top edge at least 7 deg above his eyes (ECE 22.06
    6.15.3.2, passed in the file's test report)."""
    info = built["info"]
    g, T = info["gaps_mm"], info["build_up_mm"]
    assert 36.0 < T < 41.0
    for k in ("top", "fore", "back"):
        assert abs(g[k] - T) < 2.5, (k, g[k], T)
    assert min(g["left"], g["right"]) > T and abs(g["left"] - g["right"]) < 0.5
    assert info["up_clearance_deg"] >= 7.0


CHAIN = ("neck01", "neck02", "neck03", "head")


def deform_head(body, pitch_deg):
    """His skin with the head pitched down by pitch_deg relative to the trunk, shared equally by the three neck
    bones and the head (cervical flexion), by linear blend skinning of the rest mesh. Returns the skin, and the
    head bone's rigid motion (R, j, d): p -> R (p - j) + j + d."""
    names = list(body["bones"])
    parents = list(body["parents"])
    heads = body["heads"]
    Ra = H.rot_x(math.radians(pitch_deg / len(CHAIN)))
    M = {}                                               # bone -> (R, d): p -> R p + d
    R, d = np.eye(3), np.zeros(3)
    for n in CHAIN:
        j = heads[names.index(n)]
        jw = R @ j + d                                    # the joint where the chain has carried it
        R, d = Ra @ R, Ra @ (d - jw) + jw + 0 * j
        M[n] = (R.copy(), d.copy())
    under = {"head"}
    grow = True
    while grow:
        new = {n for n, p in zip(names, parents) if p in under} - under
        grow = bool(new)
        under |= new
    for n in under:
        M[n] = M["head"]
    V = body["V"]
    out = np.zeros_like(V)
    tot = np.zeros(len(V))
    for bi, n in enumerate(names):
        sel = body["w_bone"] == bi
        vi, w = body["w_vert"][sel], body["w_val"][sel]
        Rb, db = M.get(n, (np.eye(3), np.zeros(3)))
        np.add.at(out, vi, w[:, None] * (V[vi] @ Rb.T + db))
        np.add.at(tot, vi, w)
    out /= tot[:, None]
    return out, M["head"]


@pytest.mark.parametrize("pitch", [0.0, 20.0])
def test_no_skin_inside_the_shell(body, built, pitch):
    """No skin vertex inside the shell's solid (shell, EPS, liner), at rest and with the head pitched down 20 deg
    as when riding (shared by the neck and head; the helmet rides the head bone, chest and shoulders do not).
    Pitching the head bone alone by 20 deg brings the chin bar's lower inner rim 6 vertices into his throat."""
    P = built["parts"]["helmet_shell"]
    Vs, (R, d) = deform_head(body, pitch)
    Vh = P.V @ R.T + d
    lo, hi = Vh.min(0) - 0.01, Vh.max(0) + 0.01
    near = np.all((Vs > lo) & (Vs < hi), axis=1)
    w = winding(Vs[near], Vh, tris(P))
    assert (w < 0.5).all(), f"{(w >= 0.5).sum()} skin vertices inside the shell"


def test_npz_loads_for_build_rider(built):
    g = np.load(built["path"])
    mats = json.loads(str(g["materials"]))
    for name in g["names"]:
        name = str(name)
        assert str(g[name + "__bone"]) in ("head", "eye.L", "eye.R")        # his eyes ride their eye bones
        FS, F, M = g[name + "__FS"], g[name + "__F"], g[name + "__M"]
        assert FS.sum() == len(F) and len(M) == len(FS) and F.max() < len(g[name + "__V"])
        if name + "__UV" in g:
            assert len(g[name + "__UV"]) == FS.sum()
    for m in g["mats"]:
        assert str(m) in mats


def test_visor_wings_have_side_islands():
    """Decision 47: the visor's print came out in horizontal steps on its steep wings (the side LEATT smeared in the
    Royal 1:1 crop): all of the visor was one top-projected island (V), whose texels stretch 1 / |n_z| times on a
    steep face (up to 97 there, 17 at the 99th percentile). Each visor face now goes to the island of its normal's
    largest component (VL and VR by (y, z) for the wings, VF and VB by (x, z) for faces turned forward or back): its
    texels stretch under 2 times at the 99.5th percentile and under 5 at most (three twisted triangles at the rear
    corner), the left wing's faces lie in VL whatever the grid's winding, and the islands overlap no other."""
    Vo, Fo, prof = H.shell_outer()
    G = H.visor_surface(prof)
    nr, nc, _ = G.shape
    V = G.reshape(-1, 3)
    F = np.array(H.grid_faces(nr, nc))
    UV, isl = H.atlas_uvs(V, F, visor=True)
    T = np.vstack([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])
    UVt = np.vstack([UV[:, [0, 1, 2]], UV[:, [0, 2, 3]]]) * H.TEX / H.ATLAS_K      # m in the atlas
    a3 = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
    e1, e2 = UVt[:, 1] - UVt[:, 0], UVt[:, 2] - UVt[:, 0]
    a2 = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    ok = a3 > 1e-10
    stretch = a3[ok] / np.maximum(a2[ok], 1e-14)
    assert np.percentile(stretch, 99.5) < 2.0 and stretch.max() < 5.0, \
        f"visor texels stretch {np.percentile(stretch, 99.5):.1f} (99.5 %), {stretch.max():.1f} times"
    for flip in (False, True):
        isl_f = H.atlas_uvs(V, np.array(H.grid_faces(nr, nc, 0, flip)), visor=True)[1]
        assert (V[F[isl_f == "VL"]][..., 0] > 0).all() and (V[F[isl_f == "VR"]][..., 0] < 0).all()
    boxes = {}
    uv_o, isl_o = H.atlas_uvs(Vo, Fo)
    for U, I in ((uv_o, isl_o), (UV, isl)):
        for n in np.unique(I):
            q = U[I == n].reshape(-1, 2) * H.TEX
            boxes[n] = (q.min(0), q.max(0))
    assert {"VL", "VR"} <= set(boxes)
    for a in boxes:
        for b in boxes:
            if a < b:
                lo, hi = np.maximum(boxes[a][0], boxes[b][0]), np.minimum(boxes[a][1], boxes[b][1])
                assert (hi - lo < 0).any(), (a, b)


def test_gear_frame_places_the_helmet_frame(built):
    """The gear npz carries the helmet frame's placement (helmet_shell__frame, p_MB = F p_H; build_rider keeps it as
    the shell's gear_frame) so views fitted in the helmet frame ride the shell (head_closeups.py's p07 to p09)."""
    g = np.load(built["path"])
    F = g["helmet_shell__frame"]
    Vo = H.shell_outer()[0]
    assert F.shape == (4, 4) and np.allclose(F[3], [0, 0, 0, 1])
    assert np.allclose(Vo[:50] @ F[:3, :3].T + F[:3, 3], built["parts"]["helmet_shell"].V[:50], atol=1e-9)


def test_his_photo_cameras_fitted_to_the_helmet():
    """Decision 47: his photos 07, 08 and 09 as cameras in the helmet frame (his_cameras.py,
    research/his-photo-cameras.json), fitted to the helmet's measured points (landmarks, print centres, chevrons)
    and its print's colour; head_closeups.py's p07, p08, p09 are these cameras. 08 sees the crown from ahead and
    above (his head pitched far down in the whip); main's p08, set by eye, saw his face from below."""
    import his_cameras as HC
    cams = HC.load()
    pts = HC.points()
    for k, rms_max, ncc_min in (("07", 4.0, 0.35), ("08", 6.0, 0.7), ("09", 10.0, 0.4)):
        c = cams[k]
        X = np.array([pts[n] for n in HC.READINGS[k]])
        read = np.array([v[:2] for v in HC.READINGS[k].values()], float)
        rms = np.sqrt(np.mean(np.sum((HC.project(c, X) - read) ** 2, axis=1)))
        assert rms < rms_max, f"{k}: landmarks {rms:.1f} px off"
        assert abs(rms - c["landmark_rms_px"]) < 0.5 and c["colour_ncc"] > ncc_min, k
        assert np.allclose(np.asarray(c["R"]) @ np.asarray(c["R"]).T, np.eye(3), atol=1e-6)
    v = {k: np.asarray(cams[k]["to_camera"]) for k in cams}
    assert v["07"][0] > 0.9                                    # his left side, near side-on
    assert v["08"][2] > 0.5 and v["08"][1] < -0.5               # ahead and above: the crown faces the camera
    assert v["09"][0] > 0.4 and v["09"][1] < -0.4 and v["09"][2] > 0.3
    src = open(os.path.join(HERE, "head_closeups.py")).read()
    assert "his-photo-cameras.json" in src and '"p08": ((' not in src


def test_goggle_in_the_port_on_his_eyes(body, built):
    """Lens ahead of both eyes, nothing of the lens inside the shell; the strap 45 mm wide (Leatt); the frame
    raspberry (his photos, not Leatt's hot pink render). More in test_goggle.py."""
    P = built["parts"]
    L = H.head_landmarks(body)
    lens = P["goggle_lens"].V
    for sgn in (1, -1):
        e = L["eye"] + [sgn * 0.031, 0, 0]
        near = lens[np.abs(lens[:, 0] - e[0]) < 0.004]
        assert near[:, 2].min() < e[2] < near[:, 2].max()            # the eye's height is inside the lens
        assert 0.035 < e[1] - near[:, 1].max() < 0.09                # lens back 35 to 90 mm ahead of the eye centre
    sh = P["helmet_shell"]
    assert (winding(lens, sh.V, tris(sh)) < 0.5).all()
    st = P["goggle_strap"]
    n = len(st.V) // 4
    w = np.linalg.norm(st.V[n:2 * n] - st.V[:n], axis=1)
    assert np.allclose(np.median(w), H.STRAP_W, atol=0.002)
    import goggle as G
    r, g, b = G.MATERIALS["goggle_frame"]["rgb"]
    assert r > 120 and g < 60 and b < 110


def test_textures_present():
    for f in ("helmet_pinata.png", "goggle_strap.png", "goggle_outrigger.png"):
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000


# ---------------------------------------------------------------- the Pinata art (helmet_art.py)
SMALL = 1024                                            # the tests draw and read the art at 1024 texels (0.93 mm)


def shrink(img, n=SMALL):
    s = img.shape[0] // n
    return img.reshape(n, s, n, s, 3).mean((1, 3))


@pytest.fixture(scope="module")
def art(tmp_path_factory):
    """The art drawn twice at 1024 texels by the script, and the delivered 4096 texture shrunk to 1024."""
    from PIL import Image
    import helmet_art as A
    Image.MAX_IMAGE_PIXELS = None
    d = tmp_path_factory.mktemp("art")
    drawn = []
    for k in range(2):
        p = str(d / f"art{k}.png")
        A.draw(p, tex=SMALL, log=lambda *a: None)
        drawn.append(np.asarray(Image.open(p).convert("RGB")).astype(np.float32))
    tex = np.asarray(Image.open(os.path.join(H.TEXDIR, "helmet_pinata.png")).convert("RGB")).astype(np.float32)
    r, c, P, N, S = A.texels(SMALL)
    cov = np.zeros((SMALL, SMALL), bool)
    cov[r, c] = True
    return dict(A=A, drawn=drawn, tex=tex, small=shrink(tex), cov=cov)


def test_art_drawn_deterministically(art):
    """The print is drawn by script from helmet_art.json and helmet_art_field.png (no photo pixels, no randomness):
    two draws are identical, and the delivered texture is that drawing at 4096 texels."""
    a, b = art["drawn"]
    assert np.array_equal(a, b)
    assert art["tex"].shape == (H.TEX, H.TEX, 3)
    cov = art["cov"]
    d = np.abs(art["small"] - a)[cov].mean(1)
    assert np.mean(d) < 3.0 and np.percentile(d, 90) < 6.0        # only the finer edges of the 4096 drawing differ


def test_no_studio_light_in_the_flat_print(art):
    """Lighting comes only from Blender: inside the white base and the black areas (3 texels from any edge) the
    print is flat. The luminance spread there is under 4 levels (the old projection of the studio photos: 40) and
    under 5 % of those texels have a local (7 x 7 texel, 6.5 mm) luminance deviation over 2 (the old: 29 %)."""
    from scipy import ndimage
    a = art["small"]
    L = a @ [0.2126, 0.7152, 0.0722]
    m1, m2 = ndimage.uniform_filter(L, 7), ndimage.uniform_filter(L * L, 7)
    sd = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    core = ndimage.binary_erosion(art["cov"], iterations=3)
    spread = a.max(-1) - a.min(-1)
    for name, ink in (("white", (a.min(-1) > 190) & (spread < 25)), ("black", (a.max(-1) < 60))):
        inner = ndimage.binary_erosion(ink & core, np.ones((3, 3)), iterations=3)
        assert inner.sum() > 5000, name
        lo, hi = np.percentile(L[inner], [0.5, 99.5])
        assert hi - lo < 4.0, (name, lo, hi)
        assert (sd[inner] > 2.0).mean() < 0.05, name


def test_brow_badge_carries_one_leatt(art):
    """The brow badge is part of the art (helmet.py no longer paints goggle.paint_brow_badge over it): purple, with
    one white LEATT from Leatt's own file, 34.6 mm wide and centred, its white area that of one wordmark."""
    import inspect
    A = art["A"]
    assert "paint_brow_badge(" not in inspect.getsource(H)
    tex = art["tex"]
    r, c, P, N, S = A.texels(H.TEX)
    px = tex[r, c]
    brow = A.brow_zone(P, N) & (S == 0)
    from matplotlib.path import Path
    inside = brow & Path(A.badge_outline()).contains_points(P[:, [0, 2]])
    white = inside & (px.min(1) > 200)
    purple = inside & (np.abs(px - A.BADGE_RGB).sum(1) < 30)
    assert purple.sum() > 3 * white.sum()
    x = P[white, 0]
    assert abs(0.5 * (x.min() + x.max())) < 0.0015
    assert abs(np.ptp(x) - A.BADGE_LOGO["width"]) < 0.002
    m = A.wordmark_mask()
    w = A.BADGE_LOGO["width"]
    area = m.mean() * w * w * m.shape[0] / m.shape[1]           # one wordmark (m^2, in x and z)
    measured = white.sum() / H.ATLAS_K ** 2                      # front island: one texel is 1 / ATLAS_K in x and z
    assert 0.8 < measured / area < 1.25


def test_paint_is_a_gloss_clear_over_flat_print():
    """helmet_paint: the print under a full clear coat (IOR 1.5, glossy). The print/coat interface reflects next to
    nothing, so the base has no specular of its own (Blender 5.2 does not remove it under a coat by itself)."""
    m = H.MATERIALS["helmet_paint"]
    assert m["coat"] == 1.0 and m["spec"] == 0.0 and m["coat_rough"] <= 0.05


def test_art_data_complete():
    """helmet_art.json: the five inks, polygons for each, the element frames (Leatt's files, the labels) and the
    traced colour of the elements that take one."""
    import helmet_art as A
    d = json.load(open(A.DATA))
    assert set(d["inks"]) == set(A.INKS) and all(len(d["polygons"][k]) > 0 for k in A.INKS)
    names = {f["name"] for f in d["frames"]}
    for n in ("back_leatt", "back_icon", "side_icon", "side_icon_R", "visor_side_leatt", "visor_side_leatt_R",
              "turbine", "dot_label", "size_label", "emergency", "emergency_R", "chin_text", "chin_text_R",
              "visor_chevrons", "visor_chevrons_R"):
        assert n in names, n
    assert any(n.startswith("eight") for n in names)
    assert "visor_leatt" not in names                     # the visor's LEATT band is traced (its file did not fit)
    assert len(d["element_rgb"]["back_icon"]) == 3


def test_crown_vent_openings_drawn_dark(art):
    """Round 3 (decision 46): with the lattice built (helmet_detail.py), the print under it is the dark opening only:
    main also painted the bars, a second lattice offset from the built one wherever the two cameras' casts differ.
    The opening (shrunk 20 % to its centre, top photo px) is dark (every channel under 60) at 97 % of its texels."""
    from matplotlib.path import Path
    A = art["A"]
    r, c, P, N, S = A.texels(SMALL)
    v = A.CROWN_VENT
    sel = np.nonzero((S == 0) & (P[:, 2] > 0.05) & (N[:, 2] > 0.3) & (P[:, 0] < 0))[0]
    uv, vis, cos = A.view_lookup(v["view"], P[sel], N[sel], P[sel])
    op = np.asarray(v["opening"], float)
    op = op.mean(0) + 0.8 * (op - op.mean(0))
    k = sel[Path(op).contains_points(uv) & vis]
    assert len(k) > 100
    dark = art["drawn"][0][r[k], c[k]].max(1) < 60
    assert dark.mean() > 0.97, f"{100 * (1 - dark.mean()):.0f} % of the opening painted light (bars)"

def test_print_round_the_rear_lower_piece(art):
    """Round 4 (decision 50): the print round the rear lower pieces is the back photo's (helmet_art.BACK_ZONE): main
    took it from the iso-left view, which laid the white piece's edge out as a white spike over the black beside it
    (back photo px 500 to 540, 1495 to 1520). Through the solved back camera, the drawn print matches the photo at
    points picked on it at 2x: black right of the piece and under its point, white on its outer side."""
    A = art["A"]
    img = art["drawn"][0]
    r, c, P, N, S = A.texels(SMALL)
    sel = np.nonzero((S == 0) & (P[:, 0] > 0) & (P[:, 2] < -0.03))[0]
    uv, vis, cos = A.view_lookup("back", P[sel], N[sel], P[sel])
    ok = vis & (cos > 0.1)
    for (x, y), ink in (((505, 1500), "black"), ((520, 1505), "black"), ((530, 1515), "black"),
                        ((515, 1560), "black"), ((545, 1470), "black"), ((445, 1500), "white"),
                        ((450, 1450), "white")):
        k = sel[ok & (np.hypot(uv[:, 0] - x, uv[:, 1] - y) < 3.0)]
        assert len(k) > 0, (x, y)
        px = np.median(img[r[k], c[k]], 0)
        assert (px.max() < 60) if ink == "black" else (px.min() > 190), f"({x}, {y}) should be {ink}: {px}"


def test_visor_plan_on_the_top_photo():
    """Round 4 (decision 50): the visor's outline in Leatt's top photo through the solved top camera
    (research/helmet-ba.json), whose solve now holds the visor's tip on the centre line (helmet_ba.CENTRES,
    visor_tip, read in Royal's side view, the top view and MY27's two sides; main's top camera, without a landmark at
    the front, stretched 45 mm there). From 5 mm behind the tip back to y = -110 mm, both edges of each station's
    top surface lie within 3.5 mm of the photo's outline (the mask's outermost pixel on that row). Main: 15 to 18 mm
    too wide 8 mm behind the tip, 10 to 11 mm at 15 mm, 1.5 to 5.6 mm along its sides."""
    import helmet_ba as BA
    Vo, Fo, prof = H.shell_outer()
    G = H.visor_surface(prof)
    m = BA.photo_mask("pin_top")
    cam = BA.solved_cameras()["pin_top"]
    n = 0
    for row in G:
        if not -0.214 < row[0, 1] < -0.110:
            continue
        uv = BA.project(cam, row)
        for j, sgn in ((np.argmin(uv[:, 0]), -1.0), (np.argmax(uv[:, 0]), 1.0)):
            on = np.nonzero(m[int(np.clip(round(uv[j, 1]), 0, m.shape[0] - 1))])[0]
            assert len(on), f"visor edge at y {1000 * row[j, 1]:.0f} mm beyond the photo's helmet (row {uv[j, 1]:.0f})"
            edge = on.max() if sgn > 0 else on.min()
            off = sgn * (uv[j, 0] - edge) * ((row[j] - cam["C"]) @ cam["R"][2]) / cam["f"]
            assert abs(off) < 0.0035, f"visor edge {1000 * off:+.1f} mm off the photo's at y {1000 * row[j, 1]:.0f} mm"
            n += 1
    assert n >= 20
    assert "pin_top" in BA.CENTRES["visor_tip"]


# the visor's rear edge in Leatt's top photo (pin_top px, its lit line read on 3x crops, both sides): the tongue, the
# steep and gentle runs forward along the crown, and the wing's edge back up (its corner, read less surely, left out)
VISOR_REAR_TOP_PX = [
    (940, 805), (900, 805), (870, 805), (850, 807), (840, 810), (833, 815), (825, 826), (815, 840), (805, 854),
    (795, 868), (785, 881), (778, 890), (772, 895), (750, 902), (725, 910), (700, 918), (675, 926), (650, 935),
    (625, 943), (600, 952), (588, 958), (575, 952), (562, 938), (550, 925), (537, 910), (525, 898), (512, 885),
    (500, 872), (975, 808), (1010, 809), (1050, 810), (1075, 812), (1083, 815), (1095, 826), (1105, 840),
    (1115, 855), (1125, 870), (1135, 885), (1142, 896), (1150, 900), (1175, 908), (1200, 916), (1225, 925),
    (1250, 934), (1275, 942), (1300, 952), (1335, 965), (1350, 952), (1375, 930), (1400, 905), (1420, 885),
    (1430, 873)]


def test_visor_rear_edge_on_the_top_photo(built):
    """Round 4 (decision 50): the visor's rear edge in plan is Leatt's: a tongue over the crown's centre, the edge
    running forward along the crown to a corner 37.5 mm ahead of it, ahead of the vents, then back up the wing. Through
    the solved top camera, with the tongue's end put on the photo's (the top photo puts the crown 10 to 12 mm ahead of
    the side views, which place the tongue), every point read on the photo's edge lies within 8 px (1.9 mm) of the
    model's, median under 3 px (main: 467 px, median 205; its rear row ran straight across and gathered into a point
    at the centre). Over the vents' columns the edge stands at least 20 mm ahead of the vent inserts (a straight edge
    at the tongue's end: 8.3 mm), and no quad of the visor's grid is folded (its tip row, one point, aside)."""
    import helmet_ba as BA
    import helmet_detail as D
    Vo, Fo, prof = H.shell_outer()
    G = H.visor_surface(prof)
    E = G[-1]
    uv = BA.project(BA.solved_cameras()["pin_top"], E)
    c = len(E) // 2
    t = np.linspace(0, len(E) - 1, 4000)
    k = np.clip(np.floor(t).astype(int), 0, len(E) - 2)
    poly = uv[k] + (uv[k + 1] - uv[k]) * (t - k)[:, None]
    poly[:, 1] += 806.5 - uv[c, 1]                     # the tongue's end on the photo's (v 805 to 808)
    d = np.array([np.min(np.linalg.norm(poly - p, axis=1)) for p in np.array(VISOR_REAR_TOP_PX, float)])
    assert d.max() < 8.0 and np.median(d) < 3.0, f"rear edge {d.max():.1f} px off (median {np.median(d):.1f})"
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    ins = np.unique(np.concatenate([f for f, m in zip(P.F, P.M) if m == D.MAT_INSERT]))
    xs = np.abs(V[ins, 0])
    for x in np.linspace(xs.min(), xs.max(), 9):
        gap = V[ins, 1].min() - np.interp(x, np.abs(E[c:, 0]), E[c:, 1])
        assert gap > 0.020, f"visor edge {1000 * gap:.1f} mm ahead of the vents at |x| {1000 * x:.0f} mm"
    nr, nc, _ = G.shape
    Q = np.array(H.grid_faces(nr, nc))[nc - 1:]
    W = G.reshape(-1, 3)
    n1 = np.cross(W[Q[:, 1]] - W[Q[:, 0]], W[Q[:, 3]] - W[Q[:, 0]])
    n2 = np.cross(W[Q[:, 3]] - W[Q[:, 2]], W[Q[:, 1]] - W[Q[:, 2]])
    cos = np.sum(n1 * n2, 1) / (np.linalg.norm(n1, axis=1) * np.linalg.norm(n2, axis=1))
    assert cos.min() > 0.5, f"{int((cos <= 0.5).sum())} folded quads in the visor's grid"


def test_visor_chevrons_from_the_top_photo(art):
    """The visor's chevrons: seven per side, vectorised from Leatt's top photo (the stored outlines are the photo's,
    redone the same), on the visor's top at mirror places (within 3 mm), and drawn crisp: black ink, the band
    between them plain white (no traced copy beside the drawn one)."""
    A = art["A"]
    d = json.load(open(A.DATA))
    fr = {f["name"]: f for f in d["frames"] if f["name"].startswith("visor_chevrons")}
    again = A.chevron_polys()
    for name, f in fr.items():
        assert len(f["polys"]) == 7 and f["surface"] == 1
        for p, q in zip(f["polys"], again[name]):
            assert np.allclose(np.asarray(p), q, atol=0.01)
    oL, oR = (np.asarray(fr[k]["o"]) for k in ("visor_chevrons", "visor_chevrons_R"))
    assert np.linalg.norm(oL * [-1, 1, 1] - oR) < 0.003
    chevron_band_check(A, art["tex"], [f for n, f in sorted(fr.items())], d["frames"])


def test_crown_stripe_from_the_top_photo(art):
    """The crown's centre stripe as in Leatt's top photo (round 3), read through the top camera on the drawn art:
    the chevron's sides straight (purple 3 mm inside, white 3 mm outside, both sides), the white step notch at its
    lower left only (purple at the mirror place), white below its lower diagonal, dark purple at the stem and the
    chevron's top, red at its lower right."""
    A = art["A"]
    img = art["drawn"][0]
    r, c, P, N, S = A.texels(SMALL)
    sel = np.nonzero(P[:, 2] > 0.05)[0]
    uv, vis, cos = A.view_lookup("top", P[sel], N[sel], P[sel])
    ok = vis & (cos > 0.15)

    def at(x, y):
        k = sel[ok & (np.hypot(uv[:, 0] - x, uv[:, 1] - y) < 3.0)]
        assert len(k) > 0, (x, y)
        return np.median(img[r[k], c[k]], 0)

    def white(p):
        return p.min() > 190 and np.ptp(p) < 25

    def purple(p):                                      # purple to red: next to no green
        return p[1] < 60 and max(p[0], p[2]) > 50
    for y in (760, 840):
        for x in (884, 1047):
            assert purple(at(x, y)), (x, y, at(x, y))
        for x in (859, 1072):
            assert white(at(x, y)), (x, y, at(x, y))
    assert white(at(900, 915)), at(900, 915)            # the notch, his right (image left) only
    assert purple(at(1030, 915)), at(1030, 915)
    assert purple(at(1000, 980)) and white(at(1000, 1012))
    top, low, stem = at(966, 650), at(1035, 1000), at(966, 520)
    assert top[2] > top[0] and low[0] > 1.5 * low[2], (top, low)
    assert purple(stem) and stem.sum() < 250, stem


def chevron_band_check(A, tex, chev, frames):
    """Inside the drawn chevrons black; in the band round them (0.5 to 3 mm from one, not under the visor's black
    LEATT) the white print only: the share of dark texels there."""
    from scipy import ndimage
    r, c, P, N, S = A.texels(tex.shape[0])
    sel = np.nonzero(S == 1)[0]
    others = [f for f in frames if f["name"].startswith("visor_side_leatt")]
    under, _ = A.erase_mask(others, P[sel], N[sel], S[sel])
    out = []
    for f in chev:
        px = A.frame_px(f, P[sel], N[sel])
        ok = ~np.isnan(px[:, 0])
        art_a = A.poly_art(f)[..., 3]
        dist = ndimage.distance_transform_edt(art_a < 0.5) * A.px_size(f)
        a, dd = np.zeros(len(sel)), np.full(len(sel), 1.0)
        a[ok] = ndimage.map_coordinates(art_a, [px[ok, 1], px[ok, 0]], order=1, cval=0.0)
        dd[ok] = ndimage.map_coordinates(dist, [px[ok, 1], px[ok, 0]], order=0, cval=1.0)
        rgb = tex[r[sel], c[sel]]
        ink = a > 0.95
        band = ok & (a < 0.02) & (dd > 0.0005) & (dd < 0.003) & ~under
        assert ink.sum() > 200 and np.median(rgb[ink].max(1)) < 40, f["name"]
        assert band.sum() > 200, f["name"]
        out.append(float((rgb[band].max(1) < 120).mean()))
    assert max(out) < 0.01, out
    return out
