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
    4 to 5 mm of each, the beak's bottom within 6 mm: these views read the frame about 104 mm tall (round 5 to 7:
    100), so it sits with the top on the views' and the bottom high. Round 8 (decision 43): x 1.02 and 0.5 mm higher,
    the most his face and the eyeport allow (ledger goggle.md section 10); the scale brings the top lip 0.2 mm
    forward, to 4.1 mm ahead of the views' (the kit helmet is empty: back from here his nose bridge meets the frame),
    so the top lip's bound is 4.5 mm."""
    V, info = frame_in_helmet_frame()
    c = V[np.abs(V[:, 0]) < 0.004]
    top = c[c[:, 2] > 0.02]
    bot = V[(np.abs(V[:, 0]) < 0.03) & (V[:, 2] < -0.04)]
    assert abs(top[:, 1].min() - (-0.149)) < 0.0045
    assert abs(top[:, 2].max() - 0.0425) < 0.004
    assert abs(bot[:, 1].min() - (-0.1565)) < 0.005
    assert abs(bot[:, 2].min() - (-0.065)) < 0.006


def edge_z(C, s, top):
    """Height (z) of an outline (n x 2, (s, z)) at s, on its upper (top) or lower half."""
    c = C[(C[:, 1] > 0) == top]
    i = np.argsort(c[:, 0])
    return np.interp(s, c[i, 0], c[i, 1])


def test_velocity55_shape_from_leatts_photos():
    """Round 5 to 7: the shape fitted with the cameras of nine goggle-alone photos (Leatt's 5.5 and 4.5 ISO renders,
    the exploded view, six studio photographs of the 5.5) at full resolution on outlines and creases (ledger
    goggle.md), measured on the outlines as built (control points plus the smooth offsets): the frame's front face
    3.9 to 10.9 mm proud of the lens front (round 7: the side pillars 3.9 to 4.5 mm, the post heads showing in front of
    them in iso55 and phr; round 6's 6.6 mm was a fit limit, not evidence), deepest at the top band; a top band 8.8 mm
    over the lens at the centre (10.5 with the tab) and 8.7 mm at s 50 mm, stepped down past the centre; the side
    pillar's face 9 to 14 mm wide at the end (inner wall, front face and outer facet); a lower band 12 mm under the
    lens at the corners, lowest (-55.3 mm) at the tab's tip either side of the nose; the nose arch's top at -37.9 mm,
    14.5 mm over the lower band at s 20 mm (round 7: rounds 4 to 6 read the lens edge's top, -31.7, for it); a flat
    front face 4 to 6.5 mm wide with a crisp crease; posts on the lens at s 86.7 mm; outriggers behind the side
    faces."""
    gp = G.GP
    u = {n: gp["out"][G.ci(n)] for n in G.CTRL}
    Co, Cu = G.outlines(gp)[:2]
    lip = G.xs_at(gp, "lip", G.cp_t(gp))                                  # at the control points
    assert 0.0035 < lip.min() and lip.max() < 0.0115                        # recessed lens
    assert lip[G.ci("top_c")] - lip[G.ci("side_end")] > 0.0015              # ... deepest at the top band
    assert 0.0080 < edge_z(Cu, 0.0, True) - edge_z(Co, 0.0, True) < 0.0115  # raised top band
    assert 0.0075 < edge_z(Cu, 0.05, True) - edge_z(Co, 0.05, True) < 0.0105
    assert edge_z(Cu, 0.0, True) - edge_z(Cu, 0.05, True) > 0.0025          # stepped centre
    end = Cu[:, 0].argmax()
    assert 0.009 < Cu[end, 0] - Co[end, 0] < 0.014                          # side pillar's face at the end
    assert 0.010 < edge_z(Co, 0.08, False) - edge_z(Cu, 0.08, False) < 0.014   # lower band at the corners
    assert -0.057 < Cu[:, 1].min() < -0.053                                 # lowest at the tab's tip
    assert abs(Cu[Cu[:, 1].argmin(), 0]) > 0.025
    notch = edge_z(Cu, 0.0, False)
    assert -0.0395 < notch < -0.0370                                        # nose arch's top
    assert 0.012 < notch - edge_z(Cu, 0.02, False) < 0.017                  # ... 14.5 mm over the lower band
    assert gp["fillet_out"][G.ci("tab_tip")] <= 0.0015 and gp["fillet_out"][G.ci("step_lo")] <= 0.001
    rings, info = G.frame_rings()
    rim = np.linalg.norm(rings[G.RING_RIM] - rings[2], axis=1)
    W = np.linalg.norm(info["Cu"] - info["Co"], axis=1)
    room = 0.85 * W >= G.xs_at(gp, "rim", info["t"]) + G.xs_at(gp, "chamfer", info["t"])   # not the arch's apex
    assert 0.0035 < rim[room].min() and rim.max() < 0.0075                 # wide flat front face, crisp crease
    # fins rise above the top band's edge as built at their tips
    f = G.build_fins()
    z_band = edge_z(Cu, G.FIN_S[1], True)
    assert 0.003 < f.V[:, 2].max() - z_band < 0.008
    ng = G.build_nose_guard()
    assert ng.V[:, 2].min() > Cu[:, 1].min() - 0.002                         # the guard stays inside the legs
    assert abs(G.post_sz()[0] - 0.0867) < 0.0005
    # outriggers hinged on the frame's widest point (round 9; before, behind the side faces), OR_LEN long, running
    # back and out from there (free, Leatt's goggle ISO: 55 deg)
    R_ = np.vstack(rings)
    for sg, (box, end, n) in G.outrigger_frames().items():
        hinge = box[[0, 1]].mean(0)                                         # the outer face's front edge
        near = R_[np.abs(R_[:, 2] - hinge[2]) < 0.004]
        assert abs(sg * hinge[0] - (sg * near[:, 0]).max()) < 1e-4          # on the frame's widest point
        assert 0.030 < hinge[1] - R_[:, 1].min() < 0.045                    # 30 to 45 mm behind the frame's front
        assert (sg * box[[4, 5], 0] < sg * hinge[0] - 0.002).all()          # its front end inside it (front photos)
        back = box[[2, 3]].mean(0)
        assert abs(np.linalg.norm(back - hinge) - G.OR_LEN) < 0.002
        turn = math.degrees(math.atan2(sg * (back[0] - hinge[0]), back[1] - hinge[1]))
        assert abs(turn - G.OR_FREE_TURN) < 0.5


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
    tips = [z for z, _ in G.RIB_TOPS]                                       # the fingers' tops
    assert all(-0.019 < z < -0.016 for z in tips)
    assert r.V[:, 2].max() < edge_z(Co, 0.0, False) + 0.020                # under the frame's top band, at the nose
    assert {"goggle_frame", "goggle_foam"} <= set(r.M)                     # round 10: no closed slots (noseguard)


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
    fillet's samples and one either side, 1.5 mm round the top band's tooth steps and, round 7, round the tab's
    ramps, are left out):
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
    corner |= (Co[:, 1] > 0) & (np.abs(np.abs(Co[:, 0]) - G.TAB_S) < 0.5 * G.TAB_RAMP + 0.0015)
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
    assert n.min() > 0.00002                    # round 7: the crease land, 0.1 mm, narrows with the face at the apex
    cos = np.einsum("kij,kij->ki", V[1:], V[:-1]) / (n[1:] * n[:-1])
    worst = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))).max()
    assert worst < 90.0, worst


def test_round7_nose_arch_has_a_round_top_and_feet():
    """Round 7: Leatt's nose arch is a round-topped opening (iso55, phy, phr, the white ISO at 1:1): its top at z
    -38.2 to -39.1 mm, rounding over |s| 1 to 7 mm, legs leaning about 46 deg down to feet at |s| 12 to 13 mm,
    z -49.3 to -49.7 (back-projected at the front face; the NOTCH and FOOT landmarks), the black nose guard below and
    between them. Rounds 4 to 6 took the lens edge's top (-31.7 mm) for the opening's top: a pointed V 23 mm tall."""
    Cu = G.outlines()[1]
    apex = edge_z(Cu, 0.0, False)
    assert -0.0395 < apex < -0.0370
    assert apex - edge_z(Cu, 0.0020, False) < 0.0005            # round: phy 0.2 mm under the top at |s| 2.0 mm,
    assert apex - edge_z(Cu, 0.0032, False) < 0.0013            # iso55 0.8 mm at 3.2 (a 46 deg V: 2 and 3.3 mm)
    leg = edge_z(Cu, 0.0078, False)
    assert abs(leg - (-0.0450)) < 0.0010                         # phy's mid-leg point
    foot = edge_z(Cu, 0.0125, False)
    assert -0.0515 < foot < -0.0480
    assert apex - foot < 0.014                                   # an arch 11 to 12 mm tall over the feet, not 23


def test_round7_nose_guard_fills_the_arch():
    """Round 7: the dark nose guard shows inside and below the arch in every Leatt photo (phy, phr: it fills the
    opening and hangs below the feet, its bottom edge back-projecting to z -55.1 to -56.1 mm, about 34 mm wide).
    The guard is a closed rubber shell: its top hidden behind the arch's top, wider than the opening at every
    height, its bottom 4 to 7 mm under the feet; it stays clear of his nose (test_frame_and_lens_clear_his_face)."""
    ng = dict(zip(G.NG_KEYS, G.GP["ng"]))
    Cu = G.outlines()[1]
    apex, foot = edge_z(Cu, 0.0, False), edge_z(Cu, 0.0125, False)
    assert ng["top_z"] > apex                                     # starts behind the arch's top
    assert -0.0575 < ng["bot_z"] < foot - 0.004                   # hangs below the feet
    assert 0.014 < ng["hw_bot"] < 0.020                           # 28 to 40 mm wide at the bottom
    g = G.build_nose_guard()
    arch = Cu[(Cu[:, 0] >= 0.0) & (Cu[:, 0] < 0.0125) & (Cu[:, 1] < -0.03)]
    arch = arch[np.argsort(arch[:, 1])]
    for z in np.linspace(foot + 0.001, apex - 0.001, 6):          # wider than the opening at every height
        open_hw = np.interp(z, arch[:, 1], arch[:, 0])
        row = g.V[np.abs(g.V[:, 2] - z) < 0.0015]
        assert len(row) and np.abs(row[:, 0]).max() > open_hw, z


def arch_backdrop_px(view, gp=None):
    """Pixels of the nose arch's opening (its front and back edges between the feet, each closed by the line between
    them, projected with the photo's camera) that neither the frame nor the nose guard covers: backdrop showing
    through the arch."""
    from PIL import Image, ImageDraw
    x = np.array(json.load(open(G.CAMERAS))[view]["x"])

    def fill(polys):
        im = Image.new("1", (1920, 1920), 0)
        d = ImageDraw.Draw(im)
        for p in polys:
            d.polygon([tuple(c) for c in p], fill=1)
        return np.asarray(im, bool)

    rings, info = G.frame_rings(gp)
    Cu = info["Cu"]
    i = np.nonzero((np.abs(Cu[:, 0]) <= 0.0125) & (Cu[:, 1] < -0.03))[0]
    i = i[np.argsort(Cu[i, 0])]
    cover = np.zeros((1920, 1920), bool)
    for part in (G.build_frame(gp)[0], G.build_nose_guard(gp)):
        q = G.photo_project(x, part.V, 1920, 1920)[0]
        cover |= fill(q[t] for t in tris(part))
    return [int((fill([G.photo_project(x, rings[k][i], 1920, 1920)[0]]) & ~cover).sum())
            for k in (G.RING_EDGE, G.RING_BACK_OUT)]


def test_round7_nose_guard_fills_the_arch_in_the_photos():
    """Round 7: in Leatt's photos from his right (iso55, phy, phr, phw) the guard fills the arch out to its far leg.
    Swept back 10.2 mm (the shape fit) its far side left 37 to 95 px of backdrop inside the arch; at 3 mm none."""
    for view in ("iso55", "phy", "phr", "phw"):
        assert max(arch_backdrop_px(view)) == 0, view
    gp = dict(G.GP, ng=list(G.GP["ng"]))
    gp["ng"][G.NG_KEYS.index("sweep")] = 0.01017
    assert min(arch_backdrop_px("phr", gp)) > 20                  # the check sees the round 7 fit's gap


def test_round7_creases_are_as_crisp_as_leatts():
    """Round 7: Leatt's facets meet in sharp lines: across each designed crease the shading turns over 1.2 to 2.4 px
    at 1:1 (10 to 90 %), the photos' own blur (their silhouettes) 0.8 to 1.5 px (white ISO and iso55, goggle.py
    CREASE_PROBES). The model's turn runs between the support rings either side of each crease (CREASE_R, and the
    crease land); projected with the photo's camera, blurred alike, it matches each probe within 1 px and on average
    within 0.6 px. Round 6's 0.35 mm support rings and 45 deg chamfer read 2.5 to 4 px: a rolled, tube-like edge."""
    cams = {k: v["x"] for k, v in json.load(open(G.CAMERAS)).items() if not k.startswith("_")}
    rings, _ = G.frame_rings()
    R = G.CREASE_R
    diffs = []
    for view, u, v, meas, (k0, k1) in G.CREASE_PROBES:
        x = np.array(cams[view])
        q = G.photo_project(x, 0.5 * (rings[k0] + rings[k1]), 1920, 1920)[0]
        i = int(np.argmin(np.hypot(q[:, 0] - u, q[:, 1] - v)))
        assert np.hypot(q[i, 0] - u, q[i, 1] - v) < 12.0, (view, u, v)      # the probe is on that crease
        a = rings[k0][i] + R * (rings[k0 - 1][i] - rings[k0][i]) / np.linalg.norm(rings[k0 - 1][i] - rings[k0][i])
        b = rings[k1][i] + R * (rings[k1 + 1][i] - rings[k1][i]) / np.linalg.norm(rings[k1 + 1][i] - rings[k1][i])
        pa, pb = G.photo_project(x, np.array([a, b]), 1920, 1920)[0]
        pred = np.hypot(0.8 * np.linalg.norm(pb - pa), G.CREASE_BLUR[view])
        diffs.append(pred - meas)
    diffs = np.array(diffs)
    assert np.abs(diffs).max() < 1.0, diffs
    assert np.abs(diffs).mean() < 0.6, diffs


def pillar_samples(gp=None):
    """The side pillar's outline samples (left), its middle 3/4 between side_top and bot_corner (clear of their
    fillets), top to bottom."""
    gp = gp or G.GP
    Co, Cu, Ci, seg, frac = G.outlines(gp)
    a, b = G.ci("side_top"), G.ci("side_end")
    z0, z1 = gp["out"][a][1], gp["out"][G.ci("bot_corner")][1]
    h = 0.125 * (z0 - z1)
    m = np.isin(seg, (a, b)) & (Cu[:, 0] > 0) & (Cu[:, 1] < z0 - h) & (Cu[:, 1] > z1 + h)
    i = np.nonzero(m)[0]
    return i[np.argsort(-Cu[i, 1])], Co, Cu


def test_round7_side_pillars_are_straight():
    """Round 7: Leatt's side pillars are straight bands with a clean step down to the outrigger (iso55, phr at 1:1);
    round 6's swelled outward at mid-height (its outer edge bowed 6.3 mm off the chord, and the outer facet leaned
    back 8.5 to 11 mm). In the front view the pillar's outer edge stays within 0.3 mm of its chord; in plan its
    section changes linearly along it (front face offset, inner wall lean, face width and outer facet within 0.5 mm
    of a straight line), so no part of it swells."""
    i, Co, Cu = pillar_samples()
    P = Cu[i]
    d = P[-1] - P[0]
    n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    assert np.abs((P - P[0]) @ n).max() < 0.0003
    t = G.outline_t(G.GP)[i]
    for k in ("lip", "bevel", "rim", "band"):
        f = G.xs_at(G.GP, k, t)
        assert np.abs(f - np.polyval(np.polyfit(t, f, 1), t)).max() < 0.0005, k


def test_round7_top_band_tab():
    """Round 7: the raised tab on the top band carrying the Leatt icon: the top silhouette steps up at s -32.0
    (iso55, phy), -29.9 (phw) and in the white ISO, by 6 to 11 px (1.6 to 1.9 mm at the white ISO's 0.177 mm per px);
    its far end faces away from those cameras and is mirrored. Behind the front face's top crease the top surface
    stands TAB_H higher inside |s| TAB_S, the front face's crease does not move."""
    assert abs(G.TAB_S - 0.031) < 0.002 and 0.0015 < G.TAB_H < 0.0020
    rings, info = G.frame_rings()
    h, G.TAB_H = G.TAB_H, 0.0
    try:
        flat, _ = G.frame_rings()
    finally:
        G.TAB_H = h
    Cu = G.outlines()[1]
    top = Cu[:, 1] > 0.02
    mid, out = top & (np.abs(Cu[:, 0]) < 0.025), top & (np.abs(Cu[:, 0]) > 0.040)
    for k in (G.RING_EDGE, G.RING_TOP):                                     # the top surface rises on the tab
        dz = rings[k][:, 2] - flat[k][:, 2]
        assert np.abs(dz[mid] - h).max() < 0.0003 and np.abs(dz[out]).max() < 1e-6
    assert np.abs(rings[G.RING_RIM] - flat[G.RING_RIM]).max() < 1e-9       # the front face's crease stays


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
    OR_GAP; the plate turns on its hinge (round 9: the frame's widest point) until it rests there; the strap's end
    lies inside the outrigger, between its faces, and its first ring starts there."""
    Vo, Fo, prof = H.shell_outer()
    mount = G.shell_mount(prof)
    free = G.outrigger_grids()
    R, t = built["Rt"]
    S = G.h2g((np.vstack([built["parts"][n].V for n in ("goggle_strap", "goggle_strap_band")]) - t) @ R)
    for sg, (Go, Gi, anchor) in G.outrigger_grids(mount=mount).items():
        need = mount(Gi.reshape(-1, 3)).reshape(Gi.shape[:2])
        assert (need[-1] > 0).all()                                         # its back end lies over the shell
        gap = (np.abs(Gi[..., 0]) - need)[need > 0]
        assert G.OR_GAP - 1e-4 < gap.min() < G.OR_GAP + 0.0005              # ... resting on it, not inside
        assert np.allclose(Go[0], free[sg][0][0])           # front edge on the hinge, whatever each row's turn
        assert np.allclose(np.linalg.norm(Go[0] - Gi[0], axis=1), G.OR_T)
        assert 0.0 <= G.WORN_TURN[sg][0] <= G.WORN_TURN[sg][1] < 20.0       # turned out, its top more (the shell
                                                                            # widens upwards)
        # the anchor sits between the faces near the back end, at mid height (round 8: the faces at the anchor's own
        # row; the 5 mm plate bends out along its length more than its thickness)
        j = Gi.shape[1] // 2
        i = int(np.argmin(np.linalg.norm(0.5 * (Gi + Go)[:, j] - anchor, axis=1)))
        lo, hi = sorted([abs(Gi[i, j, 0]), abs(Go[i, j, 0])])
        assert i >= Gi.shape[0] - 6 and lo < abs(anchor[0]) < hi
        assert Gi[:, 0, 2].max() < anchor[2] < Gi[:, -1, 2].min()
        assert np.linalg.norm(Gi[-1, Gi.shape[1] // 2] - anchor) < G.OR_ANCHOR + 0.004
        # the strap starts at this side's anchor: its foremost point on this side (GOGGLE frame)
        side = S[sg * S[:, 0] > 0.05]
        end = side[np.argmin(side[:, 1])]
        assert np.linalg.norm(end[[0, 1]] - anchor[[0, 1]]) < 0.012


STRAP_PARTS = ("goggle_strap_band", "goggle_strap", "goggle_slides")


def strap_clearance(parts, Rt, surf):
    """Signed distance (m, positive outside) from the shell's outer surface of every vertex and face centre of the
    given parts (MB frame, Rt: HELMET -> MB)."""
    R, t = Rt
    out = []
    for P in parts:
        V = (np.asarray(P.V) - t) @ R
        C = np.array([V[f].mean(0) for f in P.F])
        out.append(surf.closest(np.vstack([V, C]))[2])
    return np.concatenate(out)


def test_round8_strap_lies_on_the_shell_with_clearance(built):
    """Round 8 (decision 43): the strap lies on the shell, never through it. Round 7's strap was one ruled band whose
    chord across its 45 mm sagged into the convex shell: the shell came 1.5 to 1.9 mm through it at x +-45 mm (two
    dark blobs on the strap in the back view). Now every vertex and face centre of the strap (printed band, its
    inner face, the silicone strip, the doubled run, the woven edges) and of the two adjuster slides is at least
    0.5 mm outside the shell. The same measure on round 7's strap (helmet.build_strap) fails."""
    Vo, Fo, prof = H.shell_outer()
    surf = G.Surface(Vo, Fo)
    P = built["parts"]
    sd = strap_clearance([P[n] for n in STRAP_PARTS], built["Rt"], surf)
    assert sd.min() > 0.0005, f"strap {sd.min() * 1000:.2f} mm off the shell"
    if hasattr(H, "build_strap"):                     # round 7's strap, for the record: the shell through it
        I = (np.eye(3), np.zeros(3))
        r7 = H.build_strap(I, prof, {k: v[0] for k, v in G.strap_ends(G.shell_mount(prof)).items()})
        assert strap_clearance([r7], I, surf).min() < -0.001


def test_round8_strap_width_slides_and_silicone(built):
    """The strap is 45 mm wide measured along the shell (Leatt features) and 2 mm thick; the silicone strip inside
    is 5 mm wide (Leatt features) and rests on the shell; the two adjuster slides sit on the back, their inner ends
    62 mm apart (Leatt's MY27 back view at its strap's scale, 0.204 mm/px), each 22 mm along the strap and 52 mm
    across (103 x 252 px, foreshortening taken out), the right one (his right) with its grip tab on its outer end."""
    Vo, Fo, prof = H.shell_outer()
    surf = G.Surface(Vo, Fo)
    base, nrm, s = G.strap_layout(surf, G.strap_ends(G.shell_mount(prof)))[:3]
    seg = np.linalg.norm(np.diff(base, axis=1), axis=2).sum(1)              # across, station by station
    assert abs(np.median(seg) - 0.045) < 0.0005
    R, t = built["Rt"]
    sl = (built["parts"]["goggle_slides"].V - t) @ R
    reach = {}
    for sg in (1, -1):
        Q = sl[sg * sl[:, 0] > 0]
        assert abs(np.abs(Q[:, 0]).min() - 0.0305) < 0.002                      # inner ends 61 to 62 mm apart
        assert 0.050 < np.ptp(Q[:, 2]) < 0.058                                 # 52 mm across, round the shell
        reach[sg] = np.abs(Q[:, 0]).max()
    assert reach[-1] - reach[1] > 0.004                    # the right one's 8 mm tab, outwards (x, round the shell)
    assert G.SIL_W == 0.005
    band = built["parts"]["goggle_strap_band"]
    sil = np.array([f for f, m in zip(band.F, band.M) if m == "goggle_silicone"])
    Vs = (band.V[np.unique(sil)] - t) @ R
    assert surf.closest(Vs)[2].min() > 0.0005 and surf.closest(Vs)[2].min() < 0.001


def test_round9_slides_are_moulded_frames(built):
    """Round 9 (decision 45): each slide is a moulded frame round open slots (MY27 back, Forge 8024070250 and Neon
    Yellow 8022010380 backs at 1:1), not a solid block: seen square to the strap its top faces cover 30 to 75 % of
    its outline (22 x 52 mm, the right one 30 with its tab), the left one (centre bar only) less than the right one
    (end bars, centre bar, grip tab);
    the left slide's centre bar stands over the doubled tail (SLIDE_CBAR_T), higher off the shell than any bar of the
    right slide, which lies on the single strap."""
    Vo, Fo, prof = H.shell_outer()
    surf = G.Surface(Vo, Fo)
    R, t = built["Rt"]
    P = built["parts"]["goggle_slides"]
    V = (np.asarray(P.V) - t) @ R
    cover, height = {}, {}
    for sg in (1, -1):
        faces = [f for f in P.F if sg * V[f][:, 0].mean() > 0]
        C = V[np.unique(np.concatenate(faces))]
        c = C.mean(0)
        n_mean = c - surf.closest(c[None])[0][0]
        n_mean /= np.linalg.norm(n_mean)
        area = 0.0
        for f in faces:
            Q = V[f]
            a = 0.5 * sum(np.cross(Q[k] - Q[0], Q[k + 1] - Q[0]) for k in range(1, len(Q) - 1))
            area += max(0.0, a @ n_mean)                                     # top faces, seen along the normal
        along = np.cross([0.0, 0.0, 1.0], n_mean)
        along /= np.linalg.norm(along)
        cover[sg] = area / (np.ptp(C @ along) * np.ptp(C[:, 2]))            # of its outline (the right one: tab too)
        height[sg] = surf.closest(C)[2].max()
    assert 0.30 < cover[1] < cover[-1] < 0.75, cover
    assert height[1] - height[-1] > 0.001, height                          # the centre bar over the tail
    assert G.SLIDE_CBAR_T > G.SLIDE_T


def test_round9_woven_strap_scale(built):
    """Round 9: the strap's weave tile repeats every TILE_MM (19 mm, the MY27 back view's jacquard measured at 1:1)
    along the built strap: its centre line's length over its u span and the material's repeat."""
    import goggle_strap_art as SA
    R, t = built["Rt"]
    P = built["parts"]["goggle_strap_band"]
    V = (np.asarray(P.V) - t) @ R
    rep = G.MATERIALS["goggle_strap"]["detail"]["repeat"][0]
    assert abs(rep - SA.STRAP_LEN_UV * 1000.0 / SA.TILE_MM) < 1e-9
    # the printed faces' centre line (v = 0.5: the main run and the doubled tail), each edge once: its length over
    # its u span. Not a median of the edges' ratios: the strap wraps a cone-like shell, so one edge runs 2.2 % longer
    # than the centre line and the other 2.8 % shorter (662.9, 648.4, 630.5 mm in round 9's build: the elastic
    # stretches unevenly), and the stations are densest where it bends. No edge stretches the weave more than 5 %:
    # the tail's u follows its own fabric up out of the slot and over the rolls (along the strap beneath, its flanks
    # stretched it up to 4.2 times)
    edges = {}
    for f, uv, m in zip(P.F, P.UV, P.M):
        if uv is None or m != "goggle_strap":
            continue
        n = len(f)
        for i in range(n):
            j = (i + 1) % n
            d_u = abs(uv[j][0] - uv[i][0])
            if d_u > 1e-6 and abs(uv[j][1] - 0.5) < 1e-6 and abs(uv[i][1] - 0.5) < 1e-6:
                edges[(min(f[i], f[j]), max(f[i], f[j]))] = (d_u, np.linalg.norm(V[f[j]] - V[f[i]]))
    du, ds = np.array(list(edges.values())).T
    assert du.sum() > 1.1                                                  # the whole run and the tail
    tile = ds.sum() / du.sum() / rep * 1000.0
    assert abs(tile - SA.TILE_MM) < 0.3, tile
    r = ds / du / SA.STRAP_LEN_UV
    assert 0.95 < r.min() and r.max() < 1.05, (r.min(), r.max())


def test_round10_strap_weave_band_limited():
    """Round 10 (decision 48): round 9's weave read as glitter (his 07 at 4x, the Pinata iso-right at 1:1, brightest
    on the teal end) and changed the strap 1.7 times as much as no weave between two frames at whip distance. The
    tile now holds nothing finer than the photos' crosshatch: in the body under 3 % of the relief's variance and
    under 6 % of the albedo's at wavelengths below 0.5 mm (round 9: 17 % and 30 %, fibre flecks and loop rows 0.45
    mm apart, 2 px in the Pinata view); the albedo factor stays within 0.3 to 1.4 (round 9: 0.15 to 2.2, so 40 % of
    the brightest print's texels reflected more than all the light); the shader caps the albedo at 0.9 and fades the
    tile by the pixel's footprint (gone by 0.5 mm a pixel: the whip view is 2.7 mm), its blue channel the coarse
    relief that stays longer."""
    import goggle_strap_art as SA
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(H.TEXDIR, "goggle_strap_weave.png")).convert("RGB"), float) / 255.0
    ny, nx = a.shape[:2]
    mm_x, mm_y = SA.TILE_MM / nx, SA.W_MM / ny
    body = a[int(ny * 0.3):int(ny * 0.7)]
    fy = np.fft.fftfreq(body.shape[0], mm_y)[:, None]
    fx = np.fft.fftfreq(body.shape[1], mm_x)[None, :]
    short = np.hypot(fx, fy) > 2.0                                     # cycles a mm: under 0.5 mm
    share = []
    for c in (0, 1):
        P = np.abs(np.fft.fft2(body[..., c] - body[..., c].mean())) ** 2
        share.append(P[short].sum() / P.sum())
    assert share[0] < 0.03 and share[1] < 0.06, share
    g = a[..., 1] * SA.ALB_MAX
    assert 0.3 <= g.min() and g.max() <= 1.4, (g.min(), g.max())
    assert body[..., 2].std() > 0.01                                   # the coarse relief
    assert SA.ALB_CAP <= 0.9
    assert SA.FADE_FINE[0] < SA.FADE_FINE[1] <= 0.5 and SA.FADE_COARSE[1] <= 1.0
    assert SA.WAVE_MM / SA.FADE_FINE[0] >= 2.5                         # the crosshatch full only at 2.5 px a period


def test_round10_plate_tapers_with_chamfered_back_corners():
    """Round 10 item 2: Leatt's plate (his goggle photos, iso55 and phr) narrows from 63.5 mm at the frame to about
    50 mm at its back and its back corners are cut at 45 deg (2 mm top, 3 mm bottom); round 9's was 63.5 to 58.7 mm
    with square corners (plate edges 1.7 / 2.7 mm rms off Leatt's in iso55, now 1.1 / 1.5)."""
    for sg, (Go, Gi, anchor) in G.outrigger_grids().items():
        h = np.linalg.norm(Go[:, -1] - Go[:, 0], axis=1) * 1000
        mid = 0.5 * (Go[:, -1] + Go[:, 0])
        back = np.linalg.norm(mid - mid[-1], axis=1) * 1000
        assert 60.0 < h[0] < 66.0, (sg, h[0])
        assert 10.0 < h[0] - h[-1] < 16.0, (sg, h[0], h[-1])               # the taper and the cut corners
        h3 = float(np.interp(3.0, back[::-1], h[::-1]))
        assert h3 - h[-1] > 4.0, (sg, h3, h[-1])                           # cut in the last 3 mm, not a taper


def test_round10_chassis_band_has_two_clip_slots_a_side():
    """Round 10 item 3: in Leatt's ISO (every colourway) the frame's side round the lens is a black band (the
    chassis that carries the plates) with two clip slots in it, above and below the post, near black inside (L 1 to
    3 against the face's 18 to 23). Round 9 drew that band in the frame's colour with no slots. Per side: chassis
    faces on the side walls, and two pockets whose floors (goggle_slot) lie within Leatt's slot heights, at least
    1.2 mm into the moulding, above the lens front and inside the frame's cross-section."""
    from matplotlib.path import Path
    fr, info = G.build_frame()
    V = np.asarray(fr.V)
    cen = {m: np.array([V[f].mean(0) for f, mm in zip(fr.F, fr.M) if mm == m]) for m in ("goggle_chassis",
                                                                                         "goggle_slot")}
    assert len(cen["goggle_chassis"]) > 100 and np.abs(cen["goggle_chassis"][:, 0]).min() > 0.06   # the sides only
    rings, _ = G.frame_rings()
    R = np.stack(rings, 1)
    L = info["L"]
    mouth = cKDTree(np.vstack([rings[0] + (rings[1] - rings[0]) * t for t in np.linspace(0, 1, 11)]))
    fl = [f for f, mm in zip(fr.F, fr.M) if mm == "goggle_slot"]
    for sg in (1, -1):
        z = np.array([V[f].mean(0)[2] for f in fl])
        x = np.array([V[f].mean(0)[0] for f in fl])
        for z0, z1 in ((0.0060, 0.0200), (-0.0290, -0.0155)):
            sel = (np.sign(x) == sg) & (z > z0) & (z < z1)
            assert sel.sum() >= 6, (sg, z0, sel.sum())
            P = V[sorted({i for f, s_ in zip(fl, sel) if s_ for i in f})]
            assert np.ptp(P[:, 2]) > 0.008                                  # 9 to 13 mm tall, as Leatt's
            P = P[mouth.query(P)[0] > 0.001]                                # the floor (not the mouth's edges)
            assert len(P) >= 8
            for p in P[::3]:
                i = int(np.argmin(np.linalg.norm(R[:, 0] - p, axis=1)))
                t = R[(i + 1) % len(R), 0] - R[i - 1, 0]
                t /= np.linalg.norm(t)
                e1 = np.cross(t, [1.0, 0.0, 0.0] if abs(t[2]) > 0.9 else [0.0, 0.0, 1.0])
                e1 /= np.linalg.norm(e1)
                e2 = np.cross(t, e1)
                assert Path(np.c_[(R[i] - p) @ e1, (R[i] - p) @ e2]).contains_point((0.0, 0.0))
    # the floors are the pockets' bottoms: 1.2 mm or more from the mouth (gap a's face), and above the lens
    fv = np.array(sorted({i for f, mm in zip(fr.F, fr.M) if mm == "goggle_slot" for i in f}))
    d = mouth.query(V[fv])[0]
    assert np.median(d[d > 0.001]) > 0.0012, np.median(d[d > 0.001])
    from scipy import optimize
    for p in V[fv[d > 0.001]][::7]:
        off = optimize.least_squares(lambda q: L.point(np.array([q[0]]), np.array([q[1]]), q[2])[0][0] - p,
                                     [np.sign(p[0]) * 0.09, p[2], 0.0]).x[2]
        assert off > 0.0001, off


def comb_runs(part, z, step=0.00005):
    """The x runs (m) the comb's sheets cover along the row z (front view: x his left, z up)."""
    V = np.asarray(part.V)
    T = np.array([[f[0], f[i], f[i + 1]] for f, m in zip(part.F, part.M) if m == "goggle_frame"
                  for i in range(1, len(f) - 1)])
    A, B, C = (V[T[:, k]][:, [0, 2]] for k in range(3))
    keep = (np.minimum(np.minimum(A[:, 1], B[:, 1]), C[:, 1]) <= z) & (np.maximum(np.maximum(A[:, 1], B[:, 1]),
                                                                                 C[:, 1]) >= z)
    A, B, C = A[keep], B[keep], C[keep]
    xs = np.arange(-0.045, 0.045, step)
    P = np.c_[xs, np.full_like(xs, z)][:, None]
    d = (B[:, 1] - C[:, 1]) * (A[:, 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (A[:, 1] - C[:, 1])
    l1 = ((B[:, 1] - C[:, 1]) * (P[..., 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (P[..., 1] - C[:, 1])) / d
    l2 = ((C[:, 1] - A[:, 1]) * (P[..., 0] - C[:, 0]) + (A[:, 0] - C[:, 0]) * (P[..., 1] - C[:, 1])) / d
    inn = ((l1 >= -1e-9) & (l2 >= -1e-9) & (l1 + l2 <= 1 + 1e-9)).any(1)
    idx = np.nonzero(inn)[0]
    return [(xs[r[0]], xs[r[-1]]) for r in np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1) if len(r)]


def test_round10_comb_has_seven_leaning_tongues():
    """Round 10 item 4: Leatt's comb (phr and iso55 through his see-through lenses, phr at 3x) has seven tongues: an
    outer lobe, two fingers a side and the centre finger, the slots between them leaning outward at the top (the
    inner pair 0.15 to 0.27, the next 0.64 to 0.73 mm a mm in both views), the lobe 5 to 6 mm lower than the finger
    beside it, behind a wedge-shaped slot open at its top. Round 9's had five upright tongues and a closed slot in
    each lobe."""
    r = G.build_nose_ribs()
    runs = comb_runs(r, -0.0240)
    assert len(runs) == 7, [(round(a * 1000, 1), round(b * 1000, 1)) for a, b in runs]
    hi = [b for a, b in runs if b > 0]                    # his left: the gaps' inner edges (each tongue's outer end)
    lo_ = [comb_runs(r, z) for z in (-0.0220, -0.0240)]
    # each gap on his left moves outward going up: compare the tongues' outer ends at z -22 and -24 mm
    ends = [sorted(b for a, b in rr if b > 0.001) for rr in lo_]
    assert len(ends[0]) >= 3 and len(ends[1]) >= 3, ends
    lean = [(ends[0][k] - ends[1][k]) / 0.002 for k in range(2)]
    assert 0.1 < lean[0] < 0.4 and 0.5 < lean[1] < 0.9, lean           # mm a mm: the inner and the next gap
    V = np.asarray(r.V)
    top = lambda a, b: V[(V[:, 0] > a) & (V[:, 0] < b), 2].max()       # noqa: E731
    finger, lobe = top(0.017, 0.026), top(0.029, 0.042)
    assert 0.004 < finger - lobe < 0.007, (finger, lobe)
    assert abs(V[:, 0].min() + V[:, 0].max()) < 1e-6 and hi                               # symmetric


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
    """No skin inside the frame, the lens, the outriggers, the nose guard (round 7) or the nose ribs (round 5: they
    give way to his nose), at rest and with the head pitched down 20 deg (the goggle rides the head bone); the face
    foam is pressed onto the skin by at most 3 mm (compressed foam)."""
    P = built["parts"]
    for pitch in (0.0, 20.0):
        Vs, (R, d) = deform_head(body, pitch)
        for name in ("goggle_frame", "goggle_lens", "goggle_outriggers", "goggle_noseguard", "goggle_noseribs"):
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
    im = np.array(Image.open(os.path.join(H.TEXDIR, G.MATERIALS["goggle_strap"]["image"])).convert("RGB")).astype(int)
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
    for f in ("goggle_outrigger.png", "goggle_eyes_brown.png", "helmet_pinata.png"):
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000
    # round 9: every image the goggle's materials name (the strap's print, its normal map, the weave tile and its
    # mask, the slides' normal map)
    names = set()
    for spec in G.MATERIALS.values():
        names |= {spec[k] for k in ("image", "normal") if spec.get(k)}
        names |= {spec["detail"][k] for k in ("image", "mask") if spec.get("detail", {}).get(k)}
    assert {"goggle_strap_print.jpg", "goggle_strap_print_n.png", "goggle_strap_weave.png", "goggle_strap_mask.png",
            "goggle_slide_n.png"} <= names
    for f in names:
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000, f
