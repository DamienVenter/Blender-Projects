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

def surface_height(V, Vo, Fo, k=12):
    """Signed distance of points V from the shell (Vo, Fo), + outside: to the closest point on the k triangles
    whose centroids lie nearest (exact on the triangle, not the nearest vertex's tangent plane, which on the chin's
    coarser triangles read 1.5 mm under a piece that stands on the surface)."""
    from scipy.spatial import cKDTree
    A, B, C = Vo[Fo[:, 0]], Vo[Fo[:, 1]], Vo[Fo[:, 2]]
    Nf = np.cross(B - A, C - A)
    Nf /= np.linalg.norm(Nf, axis=1)[:, None]
    j = cKDTree((A + B + C) / 3).query(V, k)[1]
    a, b, c = A[j], B[j], C[j]
    p = V[:, None, :]
    ab, ac, ap = b - a, c - a, p - a
    d00, d01, d11 = (ab * ab).sum(-1), (ab * ac).sum(-1), (ac * ac).sum(-1)
    d20, d21 = (ap * ab).sum(-1), (ap * ac).sum(-1)
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    best = np.full(V.shape[0], np.inf)
    h = np.zeros(V.shape[0])
    cand = [a + v[..., None] * ab + w[..., None] * ac]                    # inside the triangle
    ok = [(v >= 0) & (w >= 0) & (v + w <= 1)]
    for e0, e1 in ((a, b), (b, c), (c, a)):                              # its edges
        e = e1 - e0
        t = np.clip(((p - e0) * e).sum(-1) / (e * e).sum(-1), 0, 1)
        cand.append(e0 + t[..., None] * e)
        ok.append(np.ones_like(t, bool))
    for q, m in zip(cand, ok):
        d = np.where(m, np.linalg.norm(p - q, axis=-1), np.inf)
        i = np.argmin(d, 1)
        r = np.arange(len(V))
        better = d[r, i] < best
        best[better] = d[r, i][better]
        h[better] = ((V - q[r, i]) * Nf[j[r, i]]).sum(1)[better]
    return h


def test_vents_are_moulded_away_from_the_front(built):
    """Round 3 (decision 46): main's crown vents were flat painted triangles; Leatt's top photo shows a raised white
    insert round a triangle lattice over the dark opening. The rear exhaust slots carry a wire mesh (round 4) and the
    lower rear vents a raised white piece drawn to a point (helmet_detail.py, from the photos' px through the print's
    cameras). The part is mirror symmetric (but the chin's moulded LEATT) and stands on the shell (no more than its
    height above it, no more than SINK under it; round 5: but the mouthpiece's tunnel inside its rim, recessed up to
    16.5 mm: test_mouthpiece_shield_and_tunnel); the crown rims stand 1.5 mm proud; each vent with its lattice (10
    bars or more) lies inside its insert's outline in the top photo (within 5 px); the lower piece runs 40 mm or more
    down the shell."""
    from scipy.spatial import cKDTree
    import helmet_art as A
    import helmet_detail as D
    from matplotlib.path import Path
    assert "helmet_vents" in built["parts"], "no moulded vents (main: painted only)"
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]                 # back in the helmet frame
    cap = np.zeros(len(V), bool)                        # round 5: the chin's LEATT reads one way (not mirrored)
    for f, m in zip(P.F, P.M):
        if m == D.MAT_CAP:
            cap[f] = True
    assert cKDTree(V[~cap]).query(V[~cap] * [-1, 1, 1])[0].max() < 1e-6
    assert set(P.M) == {D.MAT, D.MAT_INSERT, D.MAT_DARK, D.MAT_MESH, D.MAT_GRIP, D.MAT_GRIP_EDGE, D.MAT_GRIP_BEVEL,
                        D.MAT_GRIP_GROOVE, D.MAT_FRAME, D.MAT_TAG, D.MAT_CAP, D.MAT_BROW}
    Vo, Fo, _ = H.shell_outer()
    h = surface_height(V, Vo, Fo)                       # height above the shell
    rim = D.mouth_rim_xz()
    tunnel = Path(rim + D.inward_xz(rim) * 0.0002).contains_points(V[:, [0, 2]]) & (V[:, 1] < -0.15)
    assert tunnel.sum() > 100 and h[~tunnel].min() > -D.SINK - 0.0004 and h.max() < D.LOW_PIECE_H + 0.0002
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
    low = ~ins & (V[:, 2] < -0.03) & (V[:, 1] > 0.0)      # the rear lower piece (not the chin's vents)
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
    low = left & (V[:, 2] < -0.03) & (V[:, 1] > 0.0)      # the rear lower piece (not the chin's vents)

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


def _royal_px(X):
    """Helmet-frame points through Royal_Left's solved camera (research/helmet-ba.json), px."""
    import json
    cam = json.load(open(H.BA_JSON))["cameras"]["royal_left"]
    q = (np.atleast_2d(X) - np.array(cam["C"])) @ np.array(cam["R"]).T
    return np.c_[cam["cx"] + cam["f"] * q[:, 0] / q[:, 2], cam["cy"] - cam["f"] * q[:, 1] / q[:, 2]]


def test_visor_lip_runs_on_leatts_in_royal():
    """Round 5 (decision 56): VISOR_LOW is Leatt's lip traced in Royal's px; through the solved Royal camera the
    wing's lip (the top grid's left edge) lies on it within 1 px from u 760 back to the rear corner (u 1075) and
    within 12 px at u 700 (main: 50 to 57 px above it, 12 to 14 mm: px2h read the side view at the centre plane,
    the wing stands 100 mm nearer the camera). Ahead of u 660 the peak keeps phase 2's fit (main's lip there)."""
    Vo, Fo, prof = H.shell_outer()
    G = H.visor_surface(prof)
    uv = _royal_px(G[:, -1])
    lip = np.asarray(H.VISOR_LOW, float)
    off = uv[:, 1] - np.interp(uv[:, 0], lip[:, 0], lip[:, 1])
    m = (uv[:, 0] > 760) & (uv[:, 0] < 1075)
    assert m.sum() > 10 and np.abs(off[m]).max() < 1.0, f"lip {off[m].min():+.0f} to {off[m].max():+.0f} px off"
    k = np.argmin(np.abs(uv[:, 0] - 700))
    assert abs(off[k]) < 12.0, f"lip {off[k]:+.0f} px off at u 700"


def test_visor_wings_have_windows(built):
    """Round 5 (decision 56): the coordinator's 1:1 review of 01: Leatt's wing is open, a slanted window with rounded
    corners in a lit lip (Royal at 2x; the iso views see the background through the far wing); main's was closed.
    The visor's top (helmet_paint: its face and the lip's chamfer) is bounded by three loops, the outline and a
    window each side, mirror images; the left window through the solved Royal camera lies within 3 px of
    VISOR_WINDOW_PX's sides and covers 85 % or more of its area (its corners rounded VISOR_WINDOW_R); the visor
    stays closed (every edge used twice)."""
    from matplotlib.path import Path
    P = built["parts"]["helmet_visor"]
    V = (P.V - built["t"]) @ built["R"]
    _, inv = np.unique(np.round(V, 9), axis=0, return_inverse=True)
    inv = inv.ravel()
    E = {}
    for f in P.F:
        g = [inv[i] for i in f]
        for a, b in zip(g, g[1:] + g[:1]):
            if a != b:
                E[(min(a, b), max(a, b))] = E.get((min(a, b), max(a, b)), 0) + 1
    assert min(E.values()) >= 2, "the visor is open"
    top = []
    for f, m in zip(P.F, P.M):
        g = [int(inv[i]) for i in f]
        g = [v for k, v in enumerate(g) if v != g[k - 1]]  # the tip's row welds into one point
        if m == "helmet_paint" and len(set(g)) >= 3:
            top.append(g)
    Vu = np.zeros((inv.max() + 1, 3))
    Vu[inv] = V
    loops = sorted(H.boundary_loops(top), key=lambda L: np.ptp(Vu[L], 0).sum())      # the windows, then the outline
    assert len(loops) == 3, f"{len(loops)} loops round the visor's top (main: 1)"
    win = [Vu[L] for L in loops[:2]]
    left = win[0] if win[0][:, 0].mean() > 0 else win[1]
    right = win[1] if win[0][:, 0].mean() > 0 else win[0]
    assert np.abs(np.sort(left[:, 1]) - np.sort(right[:, 1])).max() < 1e-6
    q = _royal_px(left)
    W = np.asarray(H.VISOR_WINDOW_PX, float)
    d = np.full(len(q), np.inf)
    for a, b in zip(W, np.roll(W, -1, 0)):
        t = np.clip(((q - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        d = np.minimum(d, np.linalg.norm(q - (a + t[:, None] * (b - a)), axis=1))
    assert d.max() < 3.0, f"window {d.max():.1f} px off Leatt's"
    area = lambda X: 0.5 * abs(np.dot(X[:, 0], np.roll(X[:, 1], -1)) - np.dot(X[:, 1], np.roll(X[:, 0], -1)))
    assert area(q) > 0.85 * area(W), f"window {100 * area(q) / area(W):.0f} % of Leatt's"
    assert Path(W).contains_points(q).mean() > 0.5


def test_visor_window_is_clear(built):
    """Round 5 (decision 56): through the solved Royal camera, rays through the left window 12 px (3 mm) or more
    inside VISOR_WINDOW_PX's sides miss the left wing (nearer the sides its wall shows, 10 px wide along the top edge
    as Leatt's lit band there). Slivers along the outline had turned two of its points' normals over (83 and 85 deg)
    and the wall stood into the opening in two spikes 3 mm tall: 3 rays hit them (Royal at 5x)."""
    import json
    from matplotlib.path import Path
    P = built["parts"]["helmet_visor"]
    V = (P.V - built["t"]) @ built["R"]
    T = np.array([[f[0], f[k], f[k + 1]] for f in P.F for k in range(1, len(f) - 1)])
    T = T[(V[T][:, :, 0] > 0).all(1)]
    cam = json.load(open(H.BA_JSON))["cameras"]["royal_left"]
    C, Rc, f, cx, cy = np.array(cam["C"]), np.array(cam["R"]), cam["f"], cam["cx"], cam["cy"]
    W = np.asarray(H.VISOR_WINDOW_PX, float)
    uu, vv = np.meshgrid(np.arange(650, 930, 2.0), np.arange(470, 670, 2.0))
    Q = np.c_[uu.ravel(), vv.ravel()]
    Q = Q[Path(W).contains_points(Q)]
    d = np.full(len(Q), np.inf)
    for a, b in zip(W, np.roll(W, -1, 0)):
        t = np.clip(((Q - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        d = np.minimum(d, np.linalg.norm(Q - (a + t[:, None] * (b - a)), axis=1))
    Q = Q[d > 12.0]
    A = V[T[:, 0]]
    e1, e2, s = V[T[:, 1]] - A, V[T[:, 2]] - A, C - A
    q = np.cross(s, e1)
    hits = []
    for u, v in Q:                                     # Moller-Trumbore against every face of the left wing
        D = Rc.T @ np.array([(u - cx) / f, -(v - cy) / f, 1.0])
        p = np.cross(D, e2)
        det = np.sum(e1 * p, 1)
        ok = np.abs(det) > 1e-15
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        a, b, t = np.sum(s * p, 1) * inv, (q @ D) * inv, np.sum(e2 * q, 1) * inv
        if np.any(ok & (a >= 0) & (b >= 0) & (a + b <= 1) & (t > 0)):
            hits.append((u, v))
    assert len(Q) > 1000 and not hits, f"{len(hits)} of {len(Q)} rays through the window hit the wing: {hits[:4]}"


def test_grip_panels_moulded_beside_the_port(built):
    """Phase 2 (decision 51): beside the port's rear edges, from the brow's corner to the chin bar's top, a moulded
    grip panel on each side (Leatt's Pinata iso photos): its own dark grey (round 5: 80 77 82, the field's median 68
    in the photo under the Standard view; neither the trim's black nor the print), its floor standing GRIP_H proud
    of the shell (round 5: the tiles over it), 18 to 36 mm wide (the photo through the solved iso-left camera: 20 to
    35 mm), carrying the sandblast grain's UVs. Main: no panel (the print's black and the trim)."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    Vo, Fo, _ = H.shell_outer()
    h = surface_height(V, Vo, Fo)
    grip = [k for k, m in enumerate(P.M) if m in (D.MAT_GRIP, D.MAT_GRIP_GROOVE)]
    assert grip and any(m == D.MAT_GRIP_EDGE for m in P.M)
    gv = np.unique(np.concatenate([P.F[k] for k in grip]))
    fl = gv[h[gv] < D.GRIP_H + 0.0001]                   # the floor (the tiles stand over it)
    assert abs(np.median(h[fl]) - D.GRIP_H) < 0.0001 and h[fl].min() > 0.0, f"floor {1000 * np.median(h[fl]):.2f} mm"
    for s in (1, -1):
        S = V[fl][V[fl][:, 0] * s > 0]
        assert len(S) > 1000
        for z in np.arange(-0.055, -0.0, 0.01):
            row = S[np.abs(S[:, 2] - z) < 0.002]
            assert len(row) and 0.018 < np.ptp(row[:, 1]) < 0.036, f"panel {1000 * np.ptp(row[:, 1]):.0f} mm at z {z}"
    uv = np.array([u for k in grip for u in P.UV[k]])
    assert np.ptp(uv[:, 1]) > 2.0                        # the grain repeats along the panel
    g = H.MATERIALS[D.MAT_GRIP]
    assert g["rgb"] == [80, 77, 82] and os.path.exists(os.path.join(H.TEXDIR, g["normal"]))


def test_grip_panel_fills_the_corner_with_tiles(built):
    """Round 5 (decision 56): the coordinator's 1:1 review of 05: Leatt's panel fills the corner between the trim's
    roll and the print from under the brow down to the chin bar, its relief raised tiles (triangles, and rhombi
    where a groove is left out) in a dark net of grooves with lit bevels (Pinata iso-left at 6x); phase 2's was a
    band over rows 805 to 1094 with ridges, the print's black round it. Through the solved iso-left camera the
    panel's floor reaches the brow's edge at the paint (row 745 or above beyond x 1320 px; main 805) and the print's
    edge over the chin bar (below row 1135; main 1094), and on every row from 800 to 1090 runs out to within 8 px of
    the paint's edge (GRIP_OUTER_PX). The tiles stand GRIP_TILE_H over the floor, 80 to 160 a side (built: 114),
    rhombi among them (8 % or more four-cornered; built: 20 %), their tops 38 to 55 % of the field (grooves 0.6 mm
    and bevels 0.25 mm round 6.0 mm cells; built: 45 %), and the floor between them is the grooves' dark
    (MAT_GRIP_GROOVE) over the whole field."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    Vo, Fo, _ = H.shell_outer()
    h = surface_height(V, Vo, Fo)
    floor = [f for f, m in zip(P.F, P.M) if m in (D.MAT_GRIP, D.MAT_GRIP_GROOVE) and h[f].max() < D.GRIP_H + 1e-4]
    fv = np.unique(np.concatenate(floor))
    fv = fv[V[fv, 0] > 0]
    q = H.cam_project(H.PRINT_CAMS["isoleft"], V[fv])[0]
    top_row = q[q[:, 0] > 1320, 1].min()
    assert top_row < 745, f"the panel's top at the paint: row {top_row:.0f}"
    assert q[:, 1].max() > 1135, f"the panel's bottom: row {q[:, 1].max():.0f}"
    op = np.asarray(D.GRIP_OUTER_PX, float)
    for r in range(800, 1091, 10):
        gap = np.interp(r, op[:, 1], op[:, 0]) - q[np.abs(q[:, 1] - r) < 2.0, 0].max()
        assert gap < 8.0, f"row {r}: the panel ends {gap:.0f} px short of the paint"
    area = lambda F: sum(0.5 * np.linalg.norm(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])) for f in F)
    top = [f for f, m in zip(P.F, P.M) if m == D.MAT_GRIP and h[f].min() > D.GRIP_H + 0.5 * D.GRIP_TILE_H]
    tv = np.unique(np.concatenate(top))
    assert abs(np.median(h[tv]) - D.GRIP_H - D.GRIP_TILE_H) < 0.00005, f"tiles {1000 * np.median(h[tv]):.2f} mm proud"
    for s in (1, -1):
        T = [f for f in top if V[f[0], 0] * s > 0]
        cnt = np.bincount(np.concatenate(T))
        corners = cnt[cnt >= 3]                          # each tile's top is a fan round its centre
        assert 80 <= len(corners) <= 160, f"{len(corners)} tiles"
        assert np.mean(corners == 4) > 0.08, f"{100 * np.mean(corners == 4):.0f} % four-cornered"
        G = [f for f, m in zip(P.F, P.M) if m == D.MAT_GRIP_GROOVE and V[f[0], 0] * s > 0]
        r = area(T) / area(G)
        assert 0.38 < r < 0.55, f"tile tops {100 * r:.0f} % of the field"


def test_pads_fill_the_port_to_the_side_notch(body):
    """Phase 2 (decision 51): past the trim's roll (TRIM_DEPTH from the crest) the port's rolled edge is the comfort
    liner's pad face (knit mesh, red stitching: helmet_pad). Leatt's Royal side photo shows the cheek pads filling the
    port ahead of the shell's cut edge as far as its notch (FACE_PORT as traced): at every 5 mm of height from z -45
    to 0 mm the pads' front on his left stands within 5 mm of the notch's line, each point against the line at its own
    height (main: the cut edge's trim alone, 17 to 29 mm behind it; read at the band's centre height instead, the
    line's slope at the chin bar's top, 1.4 mm in y per mm, put a point 2 mm low 6 mm ahead), the pads keep 1.5 mm
    off his skin, and the goggle's lens stays clear (test above)."""
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
        d = sel[:, 1] - np.interp(sel[:, 2], notch[:, 1], notch[:, 0])
        front = d[d > -0.02].min()
        assert abs(front) < 0.005, f"pads' front {1000 * front:+.1f} mm off the notch at z {z}"
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


def outline_mm(view, Vo, Fo):
    """The shell's outline vertices in a Leatt photo through its solved camera (edges between a face turned to the
    camera and one turned away, on the projected outline) and their signed distance to the photo's silhouette (mm
    at the vertex's depth, + = outside it)."""
    import helmet_ba as BA
    from PIL import Image, ImageDraw
    from scipy import ndimage
    cam = BA.solved_cameras()[view]
    FC = Vo[Fo].mean(1)
    FN = np.cross(Vo[Fo[:, 1]] - Vo[Fo[:, 0]], Vo[Fo[:, 2]] - Vo[Fo[:, 0]])
    face = np.sign(((cam["C"] - FC) * FN).sum(1))
    E = np.sort(np.vstack([Fo[:, [0, 1]], Fo[:, [1, 2]], Fo[:, [2, 0]]]), 1)
    fid = np.tile(np.arange(len(Fo)), 3)
    key = E[:, 0] * (len(Vo) + 1) + E[:, 1]
    o = np.argsort(key)
    E, fid, key = E[o], fid[o], key[o]
    a = np.nonzero(key[1:] == key[:-1])[0]
    idx = np.unique(E[a[face[fid[a]] != face[fid[a + 1]]]].ravel())
    uv = BA.project(cam, Vo)
    im = Image.new("L", (960, 960), 0)
    d = ImageDraw.Draw(im)
    for f in Fo:
        d.polygon([tuple(uv[i] / 2) for i in f], fill=255)
    m = np.asarray(im) > 0
    dist = ndimage.distance_transform_edt(~(m & ~ndimage.binary_erosion(m)))
    q = uv[idx] / 2
    ok = (q[:, 0] > 0) & (q[:, 0] < 959) & (q[:, 1] > 0) & (q[:, 1] < 959)
    ok[ok] = dist[q[ok, 1].astype(int), q[ok, 0].astype(int)] < 1.5
    idx = idx[ok]
    depth = (Vo[idx] - cam["C"]) @ cam["R"][2]
    return Vo[idx], BA.sample(BA.sdf(view), uv[idx]) * depth / cam["f"] * 1000


def test_chin_front_on_the_iso_photos():
    """Phase 2 (decision 51): the chin's front in plan. Through the solved cameras (research/helmet-ba.json) the chin
    bar's outline ahead of y -0.12 m and below z -0.06 m has its median within 4 mm of Leatt's in MY27 front-iso-left
    (the camera that sees the front best) and within 8 mm in Pinata iso-right; the side vent's landmark (chin_vent,
    solved from five photos) lies within 1.5 mm of the shell. Main: the V too sharp at its front, its outline -14.4
    and -15.6 mm inside Leatt's (now +3.1 and -4.2), the landmark +0.8 mm (now 0.0). (Pinata iso-left reads -12.4 mm,
    main -18.9: that camera's whole outline sits 10 to 15 mm off, its back as far outside.)"""
    Vo, Fo, _ = H.shell_outer()
    for view, lim in (("my27_isoleft", 4.0), ("pin_isoright", 8.0)):
        P, mm = outline_mm(view, Vo, Fo)
        chin = (P[:, 1] < -0.12) & (P[:, 2] < -0.06)
        assert chin.sum() >= 20
        assert abs(np.median(mm[chin])) < lim, f"{view}: chin outline {np.median(mm[chin]):+.1f} mm off Leatt's"
    X = np.array(json.load(open(H.BA_JSON))["landmarks"]["chin_vent"]["X"])
    No = H.normals(Vo, Fo)
    j = np.argmin(((Vo - X) ** 2).sum(1))
    off = (X - Vo[j]) @ No[j]
    assert abs(off) < 0.0015, f"chin_vent landmark {1000 * off:+.1f} mm off the shell"


def test_iso_left_camera_refit():
    """Round 5 (decision 56): Pinata iso-left's camera (the print's and the front details' camera, helmet.PRINT_CAMS)
    refitted with the other cameras held (helmet_ba.refit): its chin outline's median within 5 mm of Leatt's, like
    MY27 front-iso-left (+3.1) and iso-right (-4.2) (main -12.4, now -4.5); the mouthpiece's side corner, placed by
    those two cameras alone, seen within 1.5 mm of where Pinata iso-left shows it (main 2.8 mm, now 0.7); the brow
    badge's reading within 8 px (main 17.3 px, now 5.7); and the brow tag's reading at the centre of its rim's three
    corners (helmet_detail.BROW_TAG_PX, read at 3x), within 3 px (main's reading, the light triangle's centroid, 15.8
    px off)."""
    import helmet_ba as BA
    import helmet_detail as D
    from scipy.optimize import least_squares
    Vo, Fo, _ = H.shell_outer()
    P, mm = outline_mm("pin_isoleft", Vo, Fo)
    chin = (P[:, 1] < -0.12) & (P[:, 2] < -0.06)
    assert chin.sum() >= 20
    assert abs(np.median(mm[chin])) < 5.0, f"pin_isoleft: chin outline {np.median(mm[chin]):+.1f} mm off Leatt's"
    cams = BA.solved_cameras()
    assert "mouth_corner" in BA.PAIRS, "no mouthpiece landmarks (main)"
    obs = [(v, s, o) for s in ("L", "R") for v, o in BA.PAIRS["mouth_corner"][s].items() if v != "pin_isoleft"]

    def r(x):
        return np.concatenate([(BA.project(cams[v], (x * ([1, 1, 1] if s == "L" else [-1, 1, 1]))[None])[0] -
                                o[:2]) / o[2] for v, s, o in obs])
    X = least_squares(r, np.array([0.05, -0.2, -0.11]), method="lm").x
    c = cams["pin_isoleft"]
    e = BA.project(c, X[None])[0] - BA.PAIRS["mouth_corner"]["L"]["pin_isoleft"][:2]
    mm_px = ((X - c["C"]) @ c["R"][2]) / c["f"] * 1000
    assert np.linalg.norm(e) * mm_px < 1.5, f"mouth corner {np.linalg.norm(e) * mm_px:.1f} mm off in pin_isoleft"
    ba = json.load(open(H.BA_JSON))
    Xb = np.array(ba["landmarks"]["brow_badge"]["X"])
    eb = BA.project(c, Xb[None])[0] - BA.CENTRES["brow_badge"]["pin_isoleft"][:2]
    assert np.linalg.norm(eb) < 8.0, f"brow badge {np.linalg.norm(eb):.1f} px off in pin_isoleft"
    tag = np.mean(D.BROW_TAG_PX, 0)
    rd = BA.PAIRS["eyeport_triangle"]["L"]["pin_isoleft"]
    assert np.linalg.norm(tag - rd[:2]) < 3.0, f"brow tag reading {np.linalg.norm(tag - rd[:2]):.1f} px off its rim"


def test_mouthpiece_and_side_vents(built):
    """Phase 2 (decision 51): the chin's mouthpiece (helmet_detail.MOUTH_RIM, MOUTH_OPEN: traced on Leatt's MY27
    front-iso-left and Pinata iso-right photos and cast through their solved cameras) is a black moulded wall from
    the white rim in to the opening, a triangle lattice across the whole opening with two rails framing its central
    column, over a dark floor; and the chin bar's side vents a wire mesh in a white wall. On the built part: the wall in
    MAT_FRAME reaches 48 mm or more each side of the centre line at z -116 mm (the shield's corners) and 35 mm or
    more at z -142 mm (its lower sides; the first trace through the Pinata iso-left camera made a diamond, 28 mm
    there), from z -92 to -170 mm (round 5: from the lip's inner edge, 2 mm in); 30 or more lattice bars (cells 7 mm
    a side), all inside the opening, the rails standing less than the tunnel's depth; the side vents' floor centred
    within 5 mm of the chin_vent landmark, with 30 or more wires. Main: none of it (print)."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    fr = [k for k, m in enumerate(P.M) if m == D.MAT_FRAME]
    assert fr, "no mouthpiece (main: the print's black)"
    Vf = V[np.unique(np.concatenate([P.F[k] for k in fr]))]
    Vf = Vf[(Vf[:, 1] < -0.18) & (Vf[:, 2] < -0.085)]
    for z, w in ((-0.116, 0.048), (-0.142, 0.035)):
        row = Vf[np.abs(Vf[:, 2] - z) < 0.0015]
        assert row[:, 0].max() > w and row[:, 0].min() < -w, f"mouthpiece {1000 * row[:, 0].max():.1f} mm at z {z}"
    assert -0.098 < Vf[:, 2].max() < -0.090 and -0.173 < Vf[:, 2].min() < -0.164
    Vo, Fo, _ = H.shell_outer()
    shell = D.Shell(Vo, Fo)
    pieces = D.mouthpiece(shell)
    bars = [p for p in pieces if p[2][0] == D.MAT_MESH]
    assert len(bars) >= 30
    rails = [p for p in pieces[4:] if p[2][0] == D.MAT_FRAME]             # round 5: lip bands, wall, floor first
    assert len(rails) == 2 and np.allclose(rails[0][0], rails[1][0] * [-1, 1, 1])
    Vb = np.vstack([p[0] for p in bars])
    assert Vb[:, 2].max() < -0.095 and Vb[:, 2].min() > -0.168           # inside the opening
    assert D.MOUTH_BAR_H < D.MOUTH_RAIL_H < D.MOUTH_DEPTH                # the rails stand in the tunnel
    side = D.side_vents(shell)
    floor = [p[0] for p in side if p[2][0] == D.MAT_DARK]
    wires = [p for p in side if p[2][0] == D.MAT_MESH]
    X = np.array(json.load(open(H.BA_JSON))["landmarks"]["chin_vent"]["X"])
    c = floor[0].mean(0)
    assert np.linalg.norm(c - X) < 0.005, f"side vent {1000 * np.linalg.norm(c - X):.1f} mm off the landmark"
    assert len(wires) >= 30 and all(p[2][0] == D.MAT for p in side[:1])


def front_y(Vo, Fo, xz):
    """The undented shell's front surface y at front-plane points (x, z), cast along +y."""
    import helmet_detail as D
    return D.front_cast(D.Shell(Vo, Fo), xz)[0][:, 1]


def test_mouthpiece_shield_and_tunnel(built):
    """Round 5 (decision 56): the coordinator's 1:1 review of 06a: Leatt's mouthpiece is a shield (straight sides
    narrowing to a flat bottom, angular corners) and a deep recessed tunnel with wide rails; phase 2's an oval band
    lying on the shell with 3 mm rails. Its rim's corners sit on the landmarks solved from the photos (helmet_ba:
    mouth_corner and mouth_bottom, their feet on the shell) within 1.5 mm and turn 30 deg or more at one point; its
    bottom is flat (the rim within 0.6 mm in z inside the bottom corner); the lattice lies 8 mm or more behind the
    shell's surface; the shell inside the rim is pushed back out of the tunnel (no vertex of its outer surface within
    12 mm behind it 1 mm or more inside the rim; the liner, 8.8 mm behind it at the opening's top corners, still
    crosses the tunnel there: round 6); the rails' front faces 4.5 to 5.8 mm wide (Leatt about 5 mm at 1:1; main
    3 mm), their centre lines 19 to 22 mm off the centre line at z -110 mm and 14 to 16.5 at z -145, above the
    shield's flat bottom (Leatt's fins cast 3 mm behind the surface, where their front edges lie: MY27 40 mm apart at
    the top and 27 at the bottom, iso-right 41 at the top; main 15.7 and 9.0, read on the surface)."""
    import helmet_detail as D
    from matplotlib.path import Path
    R, sharp = D.mouth_rim_3d()
    ba = json.load(open(H.BA_JSON))["landmarks"]
    Vo, Fo, _ = H.shell_outer()
    No = H.normals(Vo, Fo)
    for name, c in zip(("mouth_corner", "mouth_bottom"), R[sharp]):
        X = np.array(ba[name]["X"])
        j = np.argmin(((Vo - X) ** 2).sum(1))
        foot = X - ((X - Vo[j]) @ No[j]) * No[j]
        assert np.linalg.norm(c - foot) < 0.0015, f"{name}: rim corner {1000 * np.linalg.norm(c - foot):.1f} mm off"
    xz = R[:, [0, 2]]
    for i in np.nonzero(sharp)[0]:
        a, b = xz[i] - xz[i - 1], xz[i + 1] - xz[i]
        turn = np.degrees(np.arccos(a @ b / np.linalg.norm(a) / np.linalg.norm(b)))
        assert turn > 30.0, f"rim corner at {np.round(1000 * xz[i], 1)} mm turns {turn:.0f} deg"
    bottom = xz[np.nonzero(sharp)[0][1]:]                # from the bottom corner to the centre line
    assert np.ptp(bottom[:, 1]) < 0.0006, f"bottom not flat: {1000 * np.ptp(bottom[:, 1]):.1f} mm"
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    mesh = np.unique(np.concatenate([P.F[k] for k, m in enumerate(P.M) if m == D.MAT_MESH]))
    Vm = V[mesh][(V[mesh][:, 1] < -0.15) & (np.abs(V[mesh][:, 0]) < 0.05) & (V[mesh][:, 2] < -0.09)]
    assert len(Vm) > 100, "no lattice"
    back = Vm[:, 1] - front_y(Vo, Fo, Vm[:, [0, 2]])
    assert back.min() > 0.008, f"lattice {1000 * back.min():.1f} mm behind the surface (main: on it)"
    rim = D.mouth_rim_xz()
    inner = Path(rim + D.inward_xz(rim) * 0.001)
    S = built["parts"]["helmet_shell"]
    Vs = ((S.V - built["t"]) @ built["R"])[:len(Vo)]      # the outer surface (the part's first vertices)
    Vs = Vs[inner.contains_points(Vs[:, [0, 2]]) & (Vs[:, 1] < -0.15)]
    gap = Vs[:, 1] - front_y(Vo, Fo, Vs[:, [0, 2]])
    assert (gap < 0.012).sum() == 0, f"{(gap < 0.012).sum()} shell vertices in the tunnel (main: the print)"
    pieces = D.mouthpiece(D.Shell(Vo, Fo))
    rails = [p for p in pieces[4:] if p[2][0] == D.MAT_FRAME]
    Vr = np.asarray(rails[0][0])
    depth = Vr[:, 1] - front_y(Vo, Fo, Vr[:, [0, 2]])
    top = Vr[depth < depth.min() + 0.0005]               # its front face (the walls flare along the shell's normals)
    zm = np.median(top[:, 2])
    w = np.ptp(top[np.abs(top[:, 2] - zm) < 0.0005, 0])
    assert 0.0045 < w < 0.0058, f"rail {1000 * w:.1f} mm wide"
    for z, lo, hi in ((-0.110, 0.019, 0.022), (-0.145, 0.014, 0.0165)):
        row = np.abs(Vr[np.abs(Vr[:, 2] - z) < 0.001, 0])
        assert len(row) > 4, f"no rail at z {1000 * z:.0f} mm"
        c = 0.5 * (row.min() + row.max())
        assert lo < c < hi, f"rail centre {1000 * c:.1f} mm off the centre line at z {1000 * z:.0f} mm"


def angle_normals(V, F):
    """Vertex normals weighted by the corners' angles (Blender's smooth shading)."""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1), 1e-30)[:, None]
    vn = np.zeros_like(V)
    for k in range(3):
        a, b = V[F[:, (k + 1) % 3]] - V[F[:, k]], V[F[:, (k + 2) % 3]] - V[F[:, k]]
        cosw = np.sum(a * b, 1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-30)
        np.add.at(vn, F[:, k], fn * np.arccos(np.clip(cosw, -1, 1))[:, None])
    return vn / np.maximum(np.linalg.norm(vn, axis=1), 1e-30)[:, None], fn


def test_mouth_rim_shading_clean(built):
    """Round 5 (decision 56): the shell's faces inside the mouthpiece's rim are pushed back 16.5 mm behind it
    (helmet_detail.mouth_dent) and share the rim's vertices with the faces outside, so the rim's smooth normals
    (weighted by the corners' angles, as Blender's) took in the dent's walls and shaded the white beside the rim in
    teeth, one per triangle (round 5's first build, iso-left at 2.4x). The shell is cut again MOUTH_EDGE outside the
    rim (helmet.shell_outer, helmet_detail.mouth_edge_3d): the faces outside the rim whose vertex normals the dent
    turns more than 15 deg (against the undented shell's: the chin bar's bottom fold, 7 mm under the rim, turns its
    own 48 deg) lie within 1 mm of it (the first build: the rim's whole first row, 2 to 4 mm; now 0.3 mm along the
    rim, 0.95 mm beside the shield's bottom corners, where the side profile's domain, nearly edge-on at the chin's
    front, puts a cut vertex 0.7 mm off the rim's curve)."""
    import helmet_detail as D
    from scipy.spatial import cKDTree
    S = built["parts"]["helmet_shell"]
    V = (S.V - built["t"]) @ built["R"]
    F = np.array([f for f, m in zip(S.F, S.M) if m == "helmet_paint"])
    Vo, Fo, _ = H.shell_outer()
    assert np.array_equal(F, Fo)
    V = V[:len(Vo)]                                     # the outer surface (the part's first vertices)
    vn, _ = angle_normals(V, F)
    vo, _ = angle_normals(Vo, F)                        # the undented shell's
    R = D.mouth_rim_3d()[0]
    R = np.vstack([R, (R[1:-1] * [-1, 1, 1])[::-1]])
    ts = np.linspace(0, 1, 41)[:-1]
    Rf = np.vstack([R[i] + (np.roll(R, -1, 0)[i] - R[i]) * t for i in range(len(R)) for t in ts])
    d = cKDTree(Rf).query(V)[0]
    out = (np.abs(V - Vo).sum(1) < 1e-7)[F].all(1) & (d[F].min(1) < 0.010)      # undented (to the frame's rounding)
    tilt = np.degrees(np.arccos(np.clip(np.einsum("fkj,fkj->fk", vn[F], vo[F]), -1, 1))).max(1)
    bad = out & (tilt > 15.0)
    far = 1000 * d[F[bad]].max() if bad.any() else 0.0
    assert out.sum() > 200 and far < 1.0, f"faces shaded off the surface reach {far:.1f} mm from the rim"


def test_chin_front_mesh_follows_the_surface():
    """Round 5 (decision 56): the chin's front had no vertices between the centre line and 25 to 35 mm out (the blunt
    nose's width rises 28 mm within 1.2 mm of the chin rim in the profile, the domain's exclusion there), so its
    triangles ran 30 mm across and lay up to 5 mm off the surface: the crumpled bottom corner and the lumpy shading at
    1:1. Now (helmet.layer_strip, the cut in the mesh's own parameters): no edge of the chin's front longer than 8 mm
    (main 35.5), its triangles' centres within 0.5 mm of the surface at the 99th percentile and 1.5 mm at most (main
    3.8 and 4.9), and no two neighbouring triangles anywhere on the shell turned more than 60 deg against each
    other (a fold; the first drafts left them at the mouthpiece's bottom corner)."""
    V, F, prof = H.shell_outer()
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    c = V[E].mean(1)
    m = (c[:, 1] < -0.18) & (c[:, 2] < -0.09) & (c[:, 2] > -0.17) & (np.abs(c[:, 0]) < 0.055)
    assert m.sum() > 500 and L[m].max() < 0.008, f"chin front edge {1000 * L[m].max():.1f} mm"
    cen = V[F].mean(1)
    left = (cen[:, 0] > 0) & (cen[:, 1] < -0.15) & (cen[:, 2] < -0.05)
    cen = cen[left]
    dch = H.rim_dist(prof.ftree_chin, prof.fine_chin, cen[:, 1:])[0]
    cen = cen[dch > 5e-5]                              # beside the rim the width is read across its 3 mm chords
    h = 2e-6
    gy = (H.half_width(prof, cen[:, 1] + h, cen[:, 2]) - H.half_width(prof, cen[:, 1] - h, cen[:, 2])) / (2 * h)
    gz = (H.half_width(prof, cen[:, 1], cen[:, 2] + h) - H.half_width(prof, cen[:, 1], cen[:, 2] - h)) / (2 * h)
    dev = np.abs(H.half_width(prof, cen[:, 1], cen[:, 2]) - cen[:, 0]) / np.sqrt(1 + gy ** 2 + gz ** 2)
    assert np.percentile(dev, 99) < 0.0005 and dev.max() < 0.0015, \
        f"chin front off the surface: p99 {1000 * np.percentile(dev, 99):.2f}, max {1000 * dev.max():.2f} mm"
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n /= np.linalg.norm(n, axis=1)[:, None]
    faces = {}
    for i, f in enumerate(F):
        for k in range(3):
            faces.setdefault((min(f[k], f[(k + 1) % 3]), max(f[k], f[(k + 1) % 3])), []).append(i)
    pairs = np.array([v for v in faces.values() if len(v) == 2])
    dots = (n[pairs[:, 0]] * n[pairs[:, 1]]).sum(1)
    worst = V[F[pairs[np.argmin(dots), 0]]].mean(0)
    assert dots.min() > 0.5, f"fold of {np.degrees(np.arccos(dots.min())):.0f} deg at {np.round(1000 * worst, 1)} mm"


def test_chin_wordmark(built):
    """Round 5 (decision 56): the raised LEATT on the chin cap above the mouthpiece (Leatt's iso-left and V25 white
    photos: about 40 mm long, centred, z -58 mm; helmet_detail.CHIN_LEATT_C), in the print's black ink under the clear
    coat: its faces centred on the centre line within 1 mm, 38 to 42 mm across, standing 0.4 to 0.7 mm out of the
    shell. Main: none (the print's)."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    cap = [k for k, m in enumerate(P.M) if m == D.MAT_CAP]
    assert cap, "no chin LEATT (main)"
    V = (P.V - built["t"]) @ built["R"]
    Vc = V[np.unique(np.concatenate([P.F[k] for k in cap]))]
    assert abs(Vc[:, 0].max() + Vc[:, 0].min()) / 2 < 0.001
    assert 0.038 < np.ptp(Vc[:, 0]) < 0.042, f"LEATT {1000 * np.ptp(Vc[:, 0]):.1f} mm across"
    assert -0.062 < Vc[:, 2].min() and Vc[:, 2].max() < -0.054
    Vo, Fo, _ = H.shell_outer()
    from scipy.spatial import cKDTree
    No = H.normals(Vo, Fo)
    j = cKDTree(Vo).query(Vc)[1]
    h = ((Vc - Vo[j]) * No[j]).sum(1)
    top = h[h > 0.0002]
    assert 0.0004 < np.median(top) < 0.0007, f"LEATT stands {1000 * np.median(top):.2f} mm"


def test_brow_vents_and_tag(built):
    """Phase 2 (decision 51): under the visor the brow's black moulding carries two mesh vents a side (Leatt's Pinata
    iso-left photo at 2x and 3x: the centre one across the centre line, past its divider the side one slanting to the
    brow's corner; their px cast through the print's iso-left camera) and the brow tag at the corner (the Leatt
    triangle in a light grey rim). On the built part: the tag rim in MAT_TAG each side; the centre vent's lower edge
    runs straight across the centre line (within 1.5 mm of its height 12 mm to each side: read as a closed loop, the
    trace's own centre segment cut a notch 16 mm wide and 7 mm deep into it); 20 or more wire pieces, none of them
    more than 1 mm under the shell (snapped to the nearest vertex's tangent plane, the wires sank 1.7 mm where the
    brow's edge folds into the trim's roll, under their own floor). Main: none of it (the print's black)."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    tag = [k for k, m in enumerate(P.M) if m == D.MAT_TAG]
    assert tag, "no brow tag (main: print only)"
    Vt = V[np.unique(np.concatenate([P.F[k] for k in tag]))]
    assert (Vt[:, 0] > 0.09).any() and (Vt[:, 0] < -0.09).any()
    Vo, Fo, _ = H.shell_outer()
    shell = D.Shell(Vo, Fo)
    L, _ = D.sym_loop(shell, D.BROW_VENTS_PX[0])
    low = L[L[:, 2] < np.median(L[:, 2])]
    mid = low[np.abs(low[:, 0]) < 0.004, 2]
    side = low[np.abs(np.abs(low[:, 0]) - 0.012) < 0.002, 2]
    assert len(mid) and len(side) and abs(mid.mean() - side.mean()) < 0.0015, "notch in the brow vent's lower edge"
    wires = [p for p in D.brow_vents(shell) if p[2][0] == D.MAT_MESH]
    assert len(wires) >= 20
    h = surface_height(np.vstack([p[0] for p in wires]), Vo, Fo)
    assert h.min() > -D.SINK - 0.0004, f"brow wires {1000 * h.min():.2f} mm under the shell"


def _turns(P):
    """The turn at each point of a closed loop, deg."""
    a, b = P - np.roll(P, 1, 0), np.roll(P, -1, 0) - P
    c = np.sum(a * b, 1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def test_brow_vents_keep_their_corners():
    """Round 5 (decision 56; the coordinator's 1:1 review: Leatt's brow vents are angular, ours rounded). Retraced at
    4x, the centre vent ends at its divider in a straight slant and the side vent is a slanted parallelogram tipped
    at (993, 706) px; their loops keep the traced corners. On the shell the centre loop turns 140 deg or more at the
    slant's lower corner each side, the side loop 140 deg or more at its tip, each at one point (now 151 and 153;
    main: corners rounded about 4 px and resampled through, its sharpest turns 101 and 120 deg)."""
    import helmet_detail as D
    Vo, Fo, _ = H.shell_outer()
    (P, _), (Q, _) = D.brow_vent_loops(D.ExactShell(Vo, Fo))
    t = _turns(P)
    t = np.sort(t[np.isfinite(t)])[::-1]
    assert t[1] >= 140.0, f"the centre vent's corners turn {t[0]:.0f} and {t[1]:.0f} deg"
    t = _turns(Q)
    assert np.nanmax(t) >= 140.0, f"the side vent's tip turns {np.nanmax(t):.0f} deg"


def test_brow_tag_sits_in_its_recess(built):
    """Round 5 (decision 56; the 1:1 review: Leatt's tag sits in a recess, ours stood on the plain moulding).
    Pinata iso-left at 5x: round the tag's rim a dark groove about 1.5 px, then a lit bevel about 2 px up to the
    brow's surface. Round each tag a groove (MAT_DARK) 0.25 mm or less over the shell, the brow's own moulding
    (MAT_BROW) round it up to a surround standing above the tag's top (main: no recess; the tag 1 mm proud)."""
    import helmet_detail as D
    P = built["parts"]["helmet_vents"]
    V = (P.V - built["t"]) @ built["R"]
    Vo, Fo, _ = H.shell_outer()
    assert hasattr(D, "MAT_BROW") and D.MAT_BROW in P.M, "no recess round the tag (main: none)"
    vs = {m: np.unique(np.concatenate([f for f, mm in zip(P.F, P.M) if mm == m])) for m in (D.MAT_TAG, D.MAT_DARK,
                                                                                            D.MAT_BROW)}
    for sgn in (1.0, -1.0):
        tag = vs[D.MAT_TAG][sgn * V[vs[D.MAT_TAG], 0] > 0]
        lo, hi = V[tag].min(0) - 0.003, V[tag].max(0) + 0.003
        near = lambda k: k[np.all((V[k] > lo) & (V[k] < hi), 1)]
        bro, dark = near(vs[D.MAT_BROW]), near(vs[D.MAT_DARK])
        assert len(bro) and len(dark)
        h = lambda k: surface_height(V[k], Vo, Fo)
        assert h(dark).min() < 0.00025, f"groove {1000 * h(dark).min():.2f} mm over the shell"
        assert h(tag).max() < h(bro).max(), f"tag {1000 * h(tag).max():.2f} mm, surround {1000 * h(bro).max():.2f}"
        assert np.all(V[bro].min(0)[[1, 2]] < V[tag].min(0)[[1, 2]]) and np.all(V[bro].max(0)[[1, 2]] >
                                                                                 V[tag].max(0)[[1, 2]])


def test_visor_rear_lip_is_crisp(built):
    """Phase 2 (decision 51; round 4's review item A): Leatt's visor ends in a crisp lip (its thickness a dark band
    under the lit top, a thin highlight along its top edge: Pinata iso-left at 2x), main's in a soft bump: its edge
    strip shared the top's vertices, and smooth shading rounded the edge over. The edge strip has its own vertices
    (none of the top's is used by another face) and a chamfer VISOR_LIP wide runs between the top and the edge face:
    the top's outline lies VISOR_LIP inside the edge face's top."""
    P = built["parts"]["helmet_visor"]
    top = {i for f, m in zip(P.F, P.M) if m == "helmet_paint" for i in f}
    rest = {i for f, m in zip(P.F, P.M) if m != "helmet_paint" for i in f}
    assert top and rest and not (top & rest), f"{len(top & rest)} of the top's vertices shared with the edge strip"
    Vt, Ft, _, _ = P.top
    edge = np.array(sorted({i for f, m in zip(P.F, P.M) if m == "visor_under" for i in f}))
    from scipy.spatial import cKDTree
    rim = np.unique(H.boundary_loops([list(f) for f in Ft])[0])
    d = cKDTree(((P.V - built["t"]) @ built["R"])[edge]).query(Vt[rim])[0]
    assert 0.5 * H.VISOR_LIP < np.median(d) < 2.0 * H.VISOR_LIP, f"chamfer {1000 * np.median(d):.2f} mm"


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
    above (his head pitched far down in the whip); main's p08, set by eye, saw his face from below. 09's colour match
    is 0.40 since the print was retraced on phase 2's front (its chin and visor changed; 0.43 before): its floor is
    0.38."""
    import his_cameras as HC
    cams = HC.load()
    pts = HC.points()
    for k, rms_max, ncc_min in (("07", 4.0, 0.35), ("08", 6.0, 0.7), ("09", 10.0, 0.38)):
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


def test_mouthpiece_rim_corners_clean(art):
    """Round 5 (decision 56): the coordinator's 1:1 review of 06a: the rim's top corner had a jagged white-and-black
    edge. At the rim's side corners the front face turns into the chin bar's side (helmet_detail.mouth_rim_3d), and the
    side's texels just behind them lay inside the rim's outline in the front plane (within 0.2 to 0.7 mm of it) and
    took the opening's black: a flag 2 mm out of the rim, 1 to 3 mm behind the corner (iso-left at 2.4x, cast through
    its camera). Now the black is inside the shell's cut in its own parameters (helmet_art.mouth_ink). Within 5 mm of
    the mouth_corner landmark (helmet_ba, solved from three photos) and 0.8 mm or more behind it, 98 % of the texels
    are white."""
    A = art["A"]
    img = art["drawn"][0]
    r, c, P, N, S = A.texels(SMALL)
    X = np.array(json.load(open(H.BA_JSON))["landmarks"]["mouth_corner"]["X"])
    near = (S == 0) & (P[:, 0] > 0) & (np.linalg.norm(P - X, axis=1) < 0.005)
    yc = P[near][np.argmin(np.linalg.norm(P[near] - X, axis=1)), 1]
    side = near & (P[:, 1] > yc + 0.0008)
    assert side.sum() > 10
    px = img[r[side], c[side]]
    ok = px.min(1) > 190
    assert ok.mean() > 0.98, \
        f"{100 * (1 - ok.mean()):.0f} % of the {side.sum()} texels behind the rim's corner not white"


def test_mouthpiece_print_white_round_its_rim(art):
    """Phase 2 (decision 51): the print round the mouthpiece and the side vents is the white paint, inside them the
    black: the Pinata iso-left camera, which owns the chin's front, laid Leatt's black 10 to 15 mm off there and it
    ran past the rim as teeth (main: 8 % of the band round the rim not white). In the band 1.5 to 7 mm outside the rim
    on the chin's front (|x| under 45 mm: beside the rim's upper corners stand the MX.26 labels, as in Leatt's photos;
    above the chin's lower edge) and round the side vents, 98 % of the texels are white (every channel over 190);
    inside the opening shrunk 20 %, 98 % black. The chin cap's edge (helmet_art.CHIN_CAP, across the chin's front
    within 40 mm of the centre line) is as clean: from 2 to 8 mm under it 98 % white, from 2 to 5 mm over it 98 %
    black (main: 24 % under it not white; the atlas's slivers there had hung its black 7 mm under it). The 3D inks
    are set in the trace and again on the drawn texels (helmet_art.mouth_ink)."""
    from matplotlib.path import Path
    from scipy.spatial import cKDTree
    import helmet_detail as D
    A = art["A"]
    img = art["drawn"][0]
    r, c, P, N, S = A.texels(SMALL)
    rim = D.mouth_rim_xz()
    front = (S == 0) & (P[:, 1] < -0.12)
    xz = P[:, [0, 2]]
    d = cKDTree(rim).query(xz)[0]
    band = front & ~Path(rim).contains_points(xz) & (d > 0.0015) & (d < 0.007)
    band &= (np.abs(P[:, 0]) < 0.045) & (P[:, 2] > -0.172)  # not the labels beside its corners, nor the lower trim
    op = D.mouth_inner_xz(rim)
    inner = front & Path(op.mean(0) + 0.8 * (op - op.mean(0))).contains_points(xz)
    sv = D.resample_loop(np.asarray(D.SIDE_VENT_YZ, float) / 1000.0, 0.0005)
    yz = P[:, [1, 2]]
    sd = (S == 0) & (np.abs(P[:, 0]) > 0.035) & (P[:, 1] < -0.12)
    ds = cKDTree(sv).query(yz)[0]
    sband = sd & ~Path(sv).contains_points(yz) & (ds > 0.0015) & (ds < 0.004)
    cap = np.asarray(A.CHIN_CAP) / 1000.0
    zc = np.interp(np.abs(P[:, 0]), cap[:, 0], cap[:, 1])
    face = (S == 0) & (P[:, 1] < A.CHIN_CAP_Y) & (np.abs(P[:, 0]) < 0.04)
    below = face & (P[:, 2] < zc - 0.002) & (P[:, 2] > zc - 0.008)
    above = face & (P[:, 2] > zc + 0.002) & (P[:, 2] < zc + 0.005)
    for sel, ink in ((band, "white"), (sband, "white"), (inner, "black"), (below, "white"), (above, "black")):
        assert sel.sum() > 100
        px = img[r[sel], c[sel]]
        ok = px.min(1) > 190 if ink == "white" else px.max(1) < 60
        assert ok.mean() > 0.98, f"{100 * (1 - ok.mean()):.0f} % of the {ink} texels not {ink}"
