"""Tests of Damien's goggle, his eyes and the helmet's brow badge (goggle.py, built through helmet.py).

python3 -m pytest -q test_rider.py test_helmet.py test_goggle.py
"""
import json
import math
import os
import sys

import numpy as np
import pytest
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as B          # noqa: E402
import helmet as H        # noqa: E402
import goggle as G        # noqa: E402
from test_helmet import winding, tris, deform_head   # noqa: E402


@pytest.fixture(scope="module")
def body():
    d = B.build()
    return {k: d[k] for k in d}


@pytest.fixture(scope="module")
def built(body, tmp_path_factory):
    parts, info, Rt = H.build(body)
    path = str(tmp_path_factory.mktemp("goggle") / "helmet.npz")
    H.write_npz(path, parts, H.extras(body, parts, Rt))
    return dict(parts={P.name: P for P in parts}, info=info, Rt=Rt, path=path)


def frame_in_helmet_frame():
    rings, info = G.frame_rings()
    return G.g2h(np.vstack(rings)), info


def test_side_profile_from_leatts_side_views():
    """Leatt's MY27 kit side views (left and right, cameras fitted to the shell), red frame back-projected onto the
    centre plane: top lip front at y -149 mm, top at z +41 to +43.5 mm, the beak's front at y -156 to -157 mm, its
    bottom (the tabs either side of the nose notch) at z -64.6 to -66 mm (helmet frame). The built frame within
    4 to 5 mm of each, the beak's bottom within 6 mm: round 5's frame is 100 mm tall at the centre where these views
    read about 106 (the goggle-alone photos fix its shape, not its size; a lower place puts the lens into the
    shell's eyeport edge and his nose into the frame), so it sits at round 4's height with the top on the views'
    (41.6 mm) and the bottom 5.4 mm high until Damien's own goggle pins the size (ledger goggle.md, "Scale")."""
    V, info = frame_in_helmet_frame()
    c = V[np.abs(V[:, 0]) < 0.004]
    top = c[c[:, 2] > 0.02]
    bot = V[(np.abs(V[:, 0]) < 0.03) & (V[:, 2] < -0.04)]
    assert abs(top[:, 1].min() - (-0.149)) < 0.004
    assert abs(top[:, 2].max() - 0.0425) < 0.004
    assert abs(bot[:, 1].min() - (-0.1565)) < 0.005
    assert abs(bot[:, 2].min() - (-0.065)) < 0.006


def edge_z(C, s, top):
    """Height (z) of an outline (n x 2, (s, z)) at s, on its upper (top) or lower half."""
    c = C[(C[:, 1] > 0) == top]
    i = np.argsort(c[:, 0])
    return np.interp(s, c[i, 0], c[i, 1])


def test_velocity55_shape_from_leatts_photos():
    """Round 5: the shape fitted with the cameras of nine goggle-alone photos (Leatt's 5.5 and 4.5 ISO renders, the
    exploded view, six studio photographs of the 5.5) at full resolution on outlines and creases (ledger goggle.md),
    measured on the outlines as built (control points plus the smooth offsets, round 6): the lens recessed 7 to 10 mm
    behind the frame's front face (deepest at the top band and the cheeks, least at the side pillars); a top band
    about 10.6 mm over the lens at the centre and 9.2 mm at s 50 mm, the frame stepped down past the centre; the
    side pillar's face 7 to 10 mm wide at the end (round 4's 23 mm read too chunky); a lower band 12 to 13 mm under
    the lens at the corners, lowest (-55 mm) at the cheek step; the beak's legs either side of a nose arch 23 mm
    high (apex -31.7 mm: round 6's fair fit raised it 1.7 mm from round 5's -33.4, and the NOTCH landmark in iso55,
    which the fit does not see, came from 1.7 to 0.5 mm); crisp edges; posts on the lens at s 86.7 mm; outriggers
    behind the side faces."""
    gp = G.GP
    u = {n: gp["out"][G.ci(n)] for n in G.CTRL}
    Co, Cu = G.outlines(gp)[:2]
    lip = G.xs_at(gp, "lip", G.cp_t(gp))                                  # at the control points
    assert 0.0065 < lip.min() and lip.max() < 0.0105                        # recessed lens
    assert lip[G.ci("top_c")] - lip[G.ci("side_end")] > 0.0015              # ... deepest at the top band
    assert 0.0095 < edge_z(Cu, 0.0, True) - edge_z(Co, 0.0, True) < 0.012   # raised top band
    assert 0.008 < edge_z(Cu, 0.05, True) - edge_z(Co, 0.05, True) < 0.0105
    assert edge_z(Cu, 0.0, True) - edge_z(Cu, 0.05, True) > 0.0025          # stepped centre
    end = Cu[:, 0].argmax()
    assert 0.005 < Cu[end, 0] - Co[end, 0] < 0.010                          # side pillar's face at the end
    assert 0.010 < edge_z(Co, 0.08, False) - edge_z(Cu, 0.08, False) < 0.014   # lower band at the corners
    assert -0.057 < Cu[:, 1].min() < -0.053                                 # lowest at the cheeks
    assert abs(Cu[Cu[:, 1].argmin(), 0]) > 0.035
    notch = edge_z(Cu, 0.0, False)
    assert -0.033 < notch < -0.030                                          # nose arch apex
    assert 0.021 < notch - edge_z(Cu, 0.02, False) < 0.025                  # ... 23 mm above the legs
    assert gp["fillet_out"][G.ci("tab_tip")] <= 0.0015 and gp["fillet_out"][G.ci("step_lo")] <= 0.001
    rings, info = G.frame_rings()
    rim = np.linalg.norm(rings[G.RING_RIM] - rings[2], axis=1)
    W = np.linalg.norm(info["Cu"] - info["Co"], axis=1)
    room = 0.85 * W >= G.xs_at(gp, "rim", info["t"]) + G.xs_at(gp, "chamfer", info["t"])   # not the arch's apex
    assert 0.0018 < rim[room].min() and rim.max() < 0.0035                 # flat front rim, crisp chamfer behind
    # fins rise above the top band's edge as built at their tips
    f = G.build_fins()
    z_band = edge_z(Cu, G.FIN_S[1], True)
    assert 0.003 < f.V[:, 2].max() - z_band < 0.008
    ng = G.build_nose_guard()
    assert ng.V[:, 2].min() > Cu[:, 1].min() - 0.002                         # the guard stays inside the legs
    assert abs(G.post_sz()[0] - 0.0867) < 0.0005
    # outriggers behind the side faces
    L = info["L"]
    for sg, (box, end, n) in G.outrigger_frames().items():
        front = box[[0, 1]].mean(0)
        P, N = L.point(sg * u["top_corner"][0], front[2], 0.0)
        assert (P - front) @ N > 0.012                                      # more than 12 mm behind the lens front


def test_round5_offsets_teeth_and_nose_ribs():
    """Round 5 details: the outer edge and the lens edge bow off their control polygons by smooth normal offsets
    (round 6: cubic B-splines along each polygon's arc length, 12 to 30 coefficients a half, within 8 mm, near zero
    at the control points so the polygon carries the corners); the top band's lens edge steps down at the vent teeth
    (Leatt's ISO renders: steps at |s| 43.6, 59 and 79.5 mm, up to 2 mm, the near side only seen, mirrored); the
    comb of ribs over the nose bridge (seen through the clear lenses, phr): symmetric, its finger tips 16 to 19 mm
    below the lens centre, inside the nose arch, in frame colour with its slots."""
    gp = G.GP
    per = G.loop_per(gp)
    cum = np.r_[0, np.cumsum(per[:len(gp["out"]) - 1])].astype(int)
    for key, base in (("out_dk", "out"), ("open_dk", "open")):
        assert 12 <= len(gp[key]) <= 30
        Cb = G.fillet_closed(G.full_loop(gp[base]), per, G.loop_values(gp["fillet_" + base]))[0]
        dn = G.bspline_half(gp[key], G.loop_t(Cb, G.half_samples(gp, per)))
        assert np.abs(dn).max() < 0.008 and np.abs(dn[cum]).max() < 0.0005
    assert [t[0] for t in gp["teeth"]] == [0.0436, 0.059] and gp["teeth"][-1][1] == 0.0795
    Co, Cu = G.outlines(gp)[:2]
    drop = G.outlines(gp, teeth=False)[0][:, 1] - Co[:, 1]
    s = np.abs(Co[:, 0])
    top = Co[:, 1] > 0
    assert np.abs(drop[top & ((s < 0.0436 - 0.001) | (s > 0.0795 + 0.001))]).max() < 1e-5   # steps ease 0.4 mm
    assert -1e-9 <= drop.min() and drop.max() < 0.0025 and drop[top & (s > 0.07) & (s < 0.0795)].max() > 0.001
    r = G.build_nose_ribs()
    assert abs(r.V[:, 0].min() + r.V[:, 0].max()) < 1e-6                   # symmetric
    tips = [z for s_, w, z in G.RIB_FINGERS]
    assert all(-0.019 < z < -0.016 for z in tips)
    assert r.V[:, 2].max() < edge_z(Cu, 0.0, False) + 0.020                # under the frame's top band, at the nose
    assert {"goggle_frame", "goggle_foam", "goggle_noseguard"} <= set(r.M)


def crossings(P):
    """Crossings between the non-adjacent edges of a closed (s, z) loop."""
    A, B = P, np.roll(P, -1, 0)

    def orient(p, q, r):
        return np.sign((q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0]))
    a1, a2, b1, b2 = A[:, None], B[:, None], A[None], B[None]
    X = (orient(a1, a2, b1) * orient(a1, a2, b2) < 0) & (orient(b1, b2, a1) * orient(b1, b2, a2) < 0)
    i, j = np.nonzero(np.triu(X, 2))
    return int((j - i < len(P) - 1).sum())


def test_lens_fills_the_window():
    """The lens's edge (the window grown 3 mm under the frame) never crosses itself and holds the whole window: the
    first round 5 build left see-through wedges in the lens at the nose arch's steps, where the grown outline looped
    (seen white in the iso55 render)."""
    from matplotlib.path import Path
    poly = G.lens_region(G.GP, G.LENS_GROOVE)
    assert crossings(poly) == 0
    Co = G.outlines(G.GP, teeth=False)[0]
    assert Path(poly).contains_points(Co).all()


RING_NAMES = ("lens", "lip", "rim in", "rim out", "chamfer", "crease", "edge", "top", "step", "vent 1", "vent 2",
              "wall back", "back in", "stack", "behind")


def frame_fairness(gp=None):
    """Round 6 fairness of the frame (goggle.frame_rings), inside each run of loop samples between its corners (a
    fillet's samples and one either side, and 1.5 mm round the top band's tooth steps, are left out):
      along every ring (an edge or crease running round the frame): dturn, the change of the turning angle from one
        sample to the next (deg), and ripple, how far a point lies off the least-squares quadratic through the 9
        samples round it (um);
      across every face strip between two rings: kink, how far the face normal leaves the mean of its two
        neighbours along the loop (deg), and wave, how far it leaves its running mean (Gaussian of 4 samples, deg).
    Returns {measure: (worst value, ring or face)}."""
    from scipy.ndimage import gaussian_filter1d
    gp = gp or G.GP
    rings, info = G.frame_rings(gp)
    seg, frac = info["seg"], info["frac"]
    per = np.asarray(G.loop_per(gp))
    n1 = np.maximum(np.minimum(per // 4, 3), 1)
    k = np.rint(frac * per[seg]).astype(int)
    corner = (k < n1[seg]) | (k > per[seg] - n1[seg] - 1)
    Co = G.outlines(gp, teeth=False)[0]
    for t in gp.get("teeth", []):
        for e in t[:2]:
            corner |= (Co[:, 1] > 0) & (np.abs(np.abs(Co[:, 0]) - e) < 0.0015)
    ok = ~(corner | np.roll(corner, 1) | np.roll(corner, -1))
    start, runs, cur = int(np.argmin(ok)), [], []
    for j in range(1, len(ok) + 1):
        i = (start + j) % len(ok)
        if ok[i]:
            cur.append(i)
        elif cur:
            runs.append(np.array(cur))
            cur = []
    runs = [r for r in runs + ([np.array(cur)] if cur else []) if len(r) >= 9]
    x = np.arange(-4, 5, dtype=float)
    V = np.stack([np.ones_like(x), x, x * x], 1)
    off_quad = (np.eye(9) - V @ np.linalg.pinv(V))[4]                     # a point minus its local quadratic

    def ang(a, b):
        a = a / np.linalg.norm(a, axis=-1)[..., None]
        b = b / np.linalg.norm(b, axis=-1)[..., None]
        return np.degrees(np.arccos(np.clip((a * b).sum(-1), -1.0, 1.0)))
    worst = {m: (0.0, "") for m in ("dturn", "ripple", "kink", "wave")}

    def note(m, v, where):
        if v > worst[m][0]:
            worst[m] = (float(v), where)
    for name, P in zip(RING_NAMES, rings):
        for r in runs:
            Q = P[r]
            d = np.diff(Q, axis=0)
            note("dturn", np.abs(np.diff(ang(d[:-1], d[1:]))).max(), name)
            win = np.lib.stride_tricks.sliding_window_view(Q, 9, axis=0)    # (n - 8, 3, 9)
            note("ripple", np.linalg.norm(win @ off_quad, axis=1).max() * 1e6, name)
    for k in range(len(rings) - 2):                                        # the plate behind the lens edge (m-n)
        A, B = rings[k], rings[k + 1]                                      # folds where the opening crosses it
        if np.linalg.norm(B - A, axis=1).min() < 1e-5:
            continue
        face = RING_NAMES[k] + " / " + RING_NAMES[k + 1]
        for r in runs:
            a, b = A[r], B[r]
            n = np.cross(np.gradient(a, axis=0) + np.gradient(b, axis=0), b - a)
            n /= np.linalg.norm(n, axis=1)[:, None]
            note("kink", ang(n[:-2] + n[2:], n[1:-1]).max(), face)
            if len(r) > 18:
                mean = gaussian_filter1d(n, 4.0, axis=0, mode="nearest")
                note("wave", ang(n, mean)[8:-8].max(), face)
    return worst


def test_round6_frame_is_fair():
    """Round 6: the frame reads as an injection-moulded part at 1:1, flat or gently curved faces between crisp creases
    that run straight or in smooth arcs (Leatt's iso55 render), not crumpled. Every edge and crease is a smooth
    curve (frame_fairness): its turning angle changes by under 1 deg from one sample to the next and no point lies
    more than 10 um off the quadratic through its neighbours; across every face the normal leaves the mean of its
    neighbours by under 1 deg and its running mean by under 2 deg. Round 5's frame (one free offset per outline
    sample, rounded to 0.1 mm, and cross-section values per control point joined by straight lines) failed every
    bound: dturn 9.1 deg (the lens edge at the near pillar's lower corner), ripple 75 um (the step ring on the top
    band), kink 3.0 deg and wave 6.0 deg (the outer wall at the top band's step). Round 6's: dturn 0.5 deg, ripple
    9.4 um (the chamfer at the near pillar's lower half), kink 0.6 deg, wave 0.5 deg. The outlines' offsets never
    fold them (no self-crossing)."""
    w = frame_fairness()
    assert w["dturn"][0] < 1.0, w["dturn"]
    assert w["ripple"][0] < 10.0, w["ripple"]
    assert w["kink"][0] < 1.0, w["kink"]
    assert w["wave"][0] < 2.0, w["wave"]
    Co, Cu = G.outlines()[:2]
    assert crossings(Cu) == 0 and crossings(G.outlines(teeth=False)[0]) == 0


def test_round6_front_face_does_not_fold():
    """Round 6: across the frame's front face the rings run from the lens edge out (rim, chamfer, crease, band edge)
    without folding back: at every sample, each step across the face turns from the one before by under 90 deg (the
    designed edges turn up to 67 deg). frame_fairness leaves the corners out, and at the nose arch's apex, a corner,
    the face narrows to 1 mm, under the rim plus chamfer (4.2 mm): round 5 and the first round 6 build folded there
    (111 and 117 deg; a pinch at the apex in the 1:1 crops and the raking light). frame_rings now shrinks the rim and
    the chamfer with the face where it is that narrow."""
    rings, info = G.frame_rings()
    R = np.array([rings[k] for k in (2, G.RING_RIM, G.RING_CHAMFER, G.RING_MID, G.RING_EDGE)])
    V = np.diff(R, axis=0)                                                  # steps across the face
    n = np.linalg.norm(V, axis=2)
    assert n.min() > 0.0001
    cos = np.einsum("kij,kij->ki", V[1:], V[:-1]) / (n[1:] * n[:-1])
    worst = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))).max()
    assert worst < 90.0, worst


def test_landmarks_in_leatts_photos():
    """Every goggle-alone photo's camera (research/goggle-cameras.json) puts the model's landmarks where the photo
    shows them: the tear-off studs within 1.5 mm, the icon and the nose arch's top within 5 mm, half of all within
    1.5 mm (mm at the goggle). The Velocity 4.5 render (iso45) is left out since round 5: the camera that fits its
    outline to 0.4 mm (median) puts its nose arch 10 mm and its studs 4 to 5 mm off, and no camera fits both, so
    the 4.5's frame is not the 5.5's at the nose and the ends (no outriggers); its outline still counts in the fit
    (ledger goggle.md, round 5)."""
    spec = json.load(open(G.CAMERAS))
    P3 = G.photo_landmarks()
    errs, posts = [], []
    for name, v in spec.items():
        if name.startswith("_"):
            continue
        assert os.path.exists(os.path.join(HERE, "..", "..", v["photo"]))
        keys = list(v["landmarks"])
        if not keys or name == "iso45":
            continue
        uv, depth = G.photo_project(v["x"], np.array([P3[k] for k in keys]), v["W"], v["H"])
        assert (depth > 0).all()
        mm = v["x"][3] / v["x"][4] * 1000.0
        for k, p in zip(keys, uv):
            e = np.linalg.norm(p - v["landmarks"][k]) * mm
            errs.append(e)
            (posts if k.startswith("POST") else []).append(e)
            assert e < 5.0, (name, k, e)
    assert max(posts) < 1.5 and np.median(errs) < 1.5


def test_outriggers_rest_on_the_shell_and_hold_the_strap(built):
    """On the helmet the outriggers lie on the shell and the strap comes out of their back ends (Damien 2026-11-13:
    "The actual goggles is not properly connected to it's strap"; round 3 had them 22 to 41 mm inside the shell
    with the strap starting 30 to 40 mm further out). Behind the eyeport's edge the inner face clears the shell by
    OR_GAP; the plate stays fixed on the frame at its front edge; the strap's end lies inside the outrigger, between
    its faces, and its first ring starts there."""
    Vo, Fo, prof = H.shell_outer()
    mount = G.shell_mount(prof)
    free = G.outrigger_grids()
    R, t = built["Rt"]
    strap = built["parts"]["goggle_strap"].V
    m = len(strap) // 4
    first = G.h2g((np.vstack([strap[:1], strap[m:m + 1]]) - t) @ R)        # the strap's first ring, GOGGLE frame
    for sg, (Go, Gi, anchor) in G.outrigger_grids(mount=mount).items():
        need = mount(Gi.reshape(-1, 3)).reshape(Gi.shape[:2])
        back = need[-4:] > 0
        assert back.all()                                                   # its back lies over the shell
        gap = np.abs(Gi[..., 0]) - need
        assert gap[-4:][back].min() > G.OR_GAP - 1e-4                       # ... resting on it, not inside
        assert np.allclose(Gi[0], free[sg][1][0]) and np.allclose(Go[0], free[sg][0][0])   # front edge on the frame
        # the anchor sits between the faces near the back end, at mid height
        i = -2
        lo, hi = sorted([abs(Gi[i, :, 0]).mean(), abs(Go[i, :, 0]).mean()])
        assert lo < abs(anchor[0]) < hi
        assert Gi[:, 0, 2].max() < anchor[2] < Gi[:, -1, 2].min()
        assert np.linalg.norm(Gi[-1, Gi.shape[1] // 2] - anchor) < G.OR_ANCHOR + 0.004
        # the strap starts at this side's anchor (left side first in the strap's rows)
        if sg > 0:
            mid = first.mean(0)
            assert np.linalg.norm(mid[[0, 1]] - anchor[[0, 1]]) < 0.012


def test_frame_width_and_wrap():
    """Outer frame 205 to 218 mm across (round 4 fit 212.6, round 5 fit 205.8: the photos fix the shape, not the size;
    Leatt's 45 mm strap beside the outrigger reads 45 to 48 mm at round 5's size, the calibrated kit side views ask
    for a frame about 6 % taller: ledger goggle.md, "Scale"; round 3's 197 came from the kit photos' biased
    cameras), its ends 24 to 40 mm behind the lens front (the side views: red
    stops 25 to 32 mm behind the lip; the 170 deg WideVision lens wraps back round the face)."""
    V, info = frame_in_helmet_frame()
    assert 0.205 < np.ptp(V[:, 0]) < 0.218
    L = info["L"]
    s_end = max(p[0] for p in G.GP["out"])
    P_end = L.point(s_end, 0.0, 0.0)[0]
    assert 0.024 < P_end[1] < 0.040


def test_frame_and_lens_clear_his_face(body, built):
    """No skin inside the frame, the lens, the outriggers or the nose ribs (round 5: they give way to his nose), at
    rest and with the head pitched down 20 deg (the goggle rides the head bone); the face foam is pressed onto the
    skin by at most 3 mm (compressed foam)."""
    P = built["parts"]
    for pitch in (0.0, 20.0):
        Vs, (R, d) = deform_head(body, pitch)
        for name in ("goggle_frame", "goggle_lens", "goggle_outriggers", "goggle_noseribs"):
            Vh = P[name].V @ R.T + d
            lo, hi = Vh.min(0) - 0.005, Vh.max(0) + 0.005
            near = np.all((Vs > lo) & (Vs < hi), axis=1)
            w = winding(Vs[near], Vh, tris(P[name]))
            assert (np.abs(w) < 0.5).all(), f"{name}: {(np.abs(w) >= 0.5).sum()} skin vertices inside at {pitch}"
        Vf = P["goggle_foam"].V @ R.T + d
        lo, hi = Vf.min(0) - 0.005, Vf.max(0) + 0.005
        near = np.nonzero(np.all((Vs > lo) & (Vs < hi), axis=1))[0]
        w = winding(Vs[near], Vf, tris(P["goggle_foam"]))
        inside = near[np.abs(w) >= 0.5]
        if len(inside):
            assert cKDTree(Vf).query(Vs[inside])[0].max() < 0.003


def test_eyes_in_his_sockets(body, built):
    """Eyeballs on the eye bones, centred where MakeHuman's eye proxy puts them (helper sphere), radius 0.955 x
    the helper's; the lids close round them: the lid opening's rim (skin within 2.5 mm of the eyeball and in front
    of its centre) lies on the eyeball within 1.5 mm, and the cornea stays behind the lens by more than 20 mm."""
    P = built["parts"]
    names = list(body["bones"])
    for s in ("L", "R"):
        e = P["eye_ball_" + s]
        assert e.bone == "eye." + s
        c, r = G.eye_geometry(body)[s]
        head = body["heads"][names.index("eye." + s)]
        assert np.linalg.norm(c - head) < 0.002
        d = np.linalg.norm(e.V - c, axis=1)
        assert abs(np.median(d) - r) < 0.0005 and abs(r - 0.0158) < 0.0005
        skin = body["V"]
        ds = np.linalg.norm(skin - c, axis=1) - r
        rim = skin[(np.abs(ds) < 0.0025) & (skin[:, 1] < c[1] - 0.010)]
        assert len(rim) > 10
        assert np.abs(np.linalg.norm(rim - c, axis=1) - r).max() < 0.0025
        apex = e.V[np.argmin(e.V[:, 1])]
        lens = P["goggle_lens"].V
        near = lens[(np.abs(lens[:, 0] - apex[0]) < 0.005) & (np.abs(lens[:, 2] - apex[2]) < 0.005)]
        assert apex[1] - near[:, 1].max() > 0.020


def test_brown_eyes_and_the_lens_hides_them():
    """Brown irises (Damien); the lens is a purple mirror (mostly metallic, purple base, interference film) and
    what it lets through is tinted dark purple: his eyes do not show from outside."""
    from PIL import Image
    im = np.array(Image.open(os.path.join(H.TEXDIR, "goggle_eyes_brown.png")).convert("RGB")).astype(float)
    n = im.shape[0]
    ring = im[n // 2 - 30:n // 2 + 30, n // 2 + 34:n // 2 + 44].reshape(-1, 3).mean(0)   # in the iris, off the pupil
    assert ring[0] > ring[1] > ring[2] and ring[0] < 170
    m = G.MATERIALS["goggle_lens_mirror"]
    r, g, b = m["rgb"]
    assert m["metal"] >= 0.9 and b > r > g and "thin_film" in m
    assert G.MATERIALS["eye_ball"]["coat"] > 0.5                           # wet


def test_frame_colour_and_parts(built):
    """Red-pink frame: his 08 and 09 measure hue 346 deg (median 165/20/54); the base is set bluer (337 deg) so the
    render (AgX shifts reds towards orange) measures 347 deg in his 09 view. Black outriggers with their LEATT, fins,
    the lower band's LEATT, bare tear-off posts (no tear-offs, decision 7), nose guard, nose ribs, foam, strap."""
    import colorsys
    r, g, b = G.MATERIALS["goggle_frame"]["rgb"]
    h = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360
    assert 330 < h < 345 and r > 120 and g < 10
    for name in ("goggle_frame", "goggle_fins", "goggle_logo", "goggle_lens", "goggle_posts", "goggle_outriggers",
                 "goggle_noseguard", "goggle_noseribs", "goggle_foam", "goggle_strap"):
        assert name in built["parts"]
    assert "goggle_vent" in built["parts"]["goggle_frame"].M


def test_leatt_wordmark_is_the_official_slanted_one():
    """Strap, outriggers and the lower band carry Leatt's official slanted LEATT (reference file from Leatt's own
    site), at its own aspect (about 4.0 long per height): the strap's two white logos, the lower band's logo at his
    left cheek (MY27 front-iso and left side views), 4 mm high."""
    from PIL import Image
    a = G.wordmark_aspect()
    assert 3.8 < a < 4.2
    im = np.array(Image.open(os.path.join(H.TEXDIR, "goggle_strap.png")).convert("RGB")).astype(int)
    white = im.min(-1) > 235
    w = im.shape[1]
    for half in (white[:, :w // 2], white[:, w // 2:]):
        ys, xs = np.nonzero(half)
        assert abs(np.ptp(xs) / np.ptp(ys) - a) < 0.3
    lg = G.build_frame_logo()
    V = G.g2h(lg.V)
    assert (V[:, 0] > 0.03).all()                                           # his left cheek
    # length and letter height along its own axes (the band slopes down at the cheek: round 4)
    C = V - V.mean(0)
    ax = np.linalg.svd(C, full_matrices=False)[2]
    ext = np.ptp(C @ ax.T, 0)
    assert G.LOGO_H - 0.0015 < ext[1] < G.LOGO_H + 0.002 and abs(ext[0] / G.LOGO_H - a) < 0.8


def test_outrigger_text_reads_from_outside():
    """Each outrigger's half carries LEATT with the letter tops towards the strap; the left half is the right half
    mirrored across its height (the left face's UVs are mirrored seen from outside)."""
    from PIL import Image
    p = os.path.join(os.path.dirname(H.TEXDIR), "rider", "goggle_outrigger.png")
    im = np.array(Image.open(p).convert("L")).astype(float) > 128
    w = im.shape[1] // 2
    left, right = im[:, :w], im[:, w:]
    assert (left == right[:, ::-1]).mean() > 0.99
    rows = np.nonzero(right.any(1))[0]
    assert rows.mean() < im.shape[0] * 0.6                       # tops towards v = 1 (image top, the strap)


def test_one_leatt_on_the_brow_badge():
    """The brow badge is painted once, centred, purple with one white LEATT (Leatt's photos, his 09): the purple
    texels of the brow lie inside the badge (centred on x = 0, 56 mm wide at the bottom) and the white letters
    span 34.6 mm."""
    from PIL import Image
    Vo, Fo, prof = H.shell_outer()
    UV, isl = H.atlas_uvs(Vo, Fo)
    N = H.normals(Vo, Fo)
    idx, Pts, Nn = H.rasterize(UV * H.TEX, Vo[Fo], N[Fo])
    img = np.array(Image.open(os.path.join(H.TEXDIR, "helmet_pinata.png")).convert("RGB")).astype(int)
    row, col = H.TEX - 1 - np.clip(idx[:, 1], 0, H.TEX - 1), np.clip(idx[:, 0], 0, H.TEX - 1)
    px = img[row, col]
    brow = (Pts[:, 1] < -0.09) & (Nn[:, 1] < 0) & (np.abs(Pts[:, 0]) < 0.09) & (Pts[:, 2] > 0.066) & (Pts[:, 2] < 0.1)
    purple = brow & (np.abs(px - G.BADGE_RGB).sum(1) < 30)
    x = Pts[purple, 0]
    assert abs(0.5 * (x.min() + x.max())) < 0.0015 and 0.050 < np.ptp(x) < 0.058
    white = brow & (px.min(1) > 236) & (np.abs(Pts[:, 0]) < 0.03) & (Pts[:, 2] > G.BADGE_Z[0]) & (Pts[:, 2] < G.BADGE_Z[1])
    xw = Pts[white, 0]
    assert abs(np.ptp(xw) - G.BADGE_LOGO["width"]) < 0.003


def test_npz_loads_with_eye_bones(built, body):
    g = np.load(built["path"])
    names = list(body["bones"])
    mats = json.loads(str(g["materials"]))
    for name in g["names"]:
        name = str(name)
        assert str(g[name + "__bone"]) in names
        FS, F, M = g[name + "__FS"], g[name + "__F"], g[name + "__M"]
        assert FS.sum() == len(F) and len(M) == len(FS) and F.max() < len(g[name + "__V"])
    for m in g["mats"]:
        assert str(m) in mats


def test_textures_present():
    for f in ("goggle_strap.png", "goggle_outrigger.png", "goggle_eyes_brown.png", "helmet_pinata.png"):
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000
