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
    # outriggers hinged by the frame's widest point (round 9; before, behind the side faces; round 12: OR_HINGE_IN
    # inboard of it, behind the side face), OR_LEN long, running back and out from there (free, Leatt's goggle ISO:
    # 55 deg from the widest point, 62 from the hinge inboard)
    R_ = np.vstack(rings)
    for sg, (box, end, n) in G.outrigger_frames().items():
        # round 14: the printed plate starts OR_PLATE_FRONT along it, in the C; the hinge is OR_HINGE_LEN before its
        # back end (round 9 to 13: its front end inside the frame's widest point, now the arms there)
        front, back = box[[0, 1]].mean(0), box[[2, 3]].mean(0)
        t = (back - front) / np.linalg.norm(back - front)
        hinge = back - t * G.OR_HINGE_LEN - n / np.linalg.norm(n) * G.OR_FACE_OUT   # the plate's face off it
        near = R_[np.abs(R_[:, 2] - hinge[2]) < 0.004]
        assert abs((sg * near[:, 0]).max() - sg * hinge[0] - G.OR_HINGE_IN) < 1e-4   # OR_HINGE_IN inside that point
        assert 0.030 < hinge[1] - R_[:, 1].min() < 0.045                    # 30 to 45 mm behind the frame's front
        assert abs(np.linalg.norm(back - front) - G.plate_len()) < 0.002    # round 12: OR_LEN less OR_HINGE_BACK
        turn = math.degrees(math.atan2(sg * (back[0] - front[0]), back[1] - front[1]))   # along the plate
        ft = G.OR_FREE_TURN[sg] if isinstance(G.OR_FREE_TURN, dict) else G.OR_FREE_TURN
        assert abs(turn - ft) < 0.5


def test_round5_offsets_teeth_and_nose_ribs():
    """Round 5 details: the outer edge and the lens edge bow off their control polygons by smooth normal offsets
    (round 6: cubic B-splines along each polygon's arc length, 12 to 30 coefficients a half, within 8 mm, near zero
    at the control points so the polygon carries the corners); the top band's lens edge steps down at the vent teeth
    (Leatt's ISO renders: steps at |s| 43.6, 59 and 79.5 mm, up to 2 mm, the near side only seen, mirrored; round
    13, read through three views jointly: 48.5, 58.5, 61.5, the second tooth ramping to 3 mm at 71.5 and back to
    the band by 77.5); the
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
    assert [t[0] for t in gp["teeth"]] == [0.0485, 0.0585, 0.0615, 0.0715] and gp["teeth"][-1][1] == 0.0775
    Co, Cu = G.outlines(gp)[:2]
    drop = G.outlines(gp, teeth=False)[0][:, 1] - Co[:, 1]
    s = np.abs(Co[:, 0])
    top = Co[:, 1] > 0
    assert np.abs(drop[top & ((s < 0.0485 - 0.001) | (s > 0.0775 + 0.001))]).max() < 1e-5   # steps ease 0.4 mm
    assert -1e-9 <= drop.min() and drop.max() < 0.0032 and drop[top & (s > 0.07) & (s < 0.0775)].max() > 0.001
    r = G.build_nose_ribs()
    assert abs(r.V[:, 0].min() + r.V[:, 0].max()) < 1e-6                   # symmetric
    tips = [z for z, _ in G.RIB_TOPS]                                       # the fingers' tops
    assert all(-0.019 < z < -0.016 for z in tips)
    assert r.V[:, 2].max() < edge_z(Co, 0.0, False) + 0.020                # under the frame's top band, at the nose
    # round 11: one moulding in the frame's colour, satin (Leatt's leaning tongues mirror no light)
    assert set(r.M) == {"goggle_comb"} and G.MATERIALS["goggle_comb"]["rgb"] == G.MATERIALS["goggle_frame"]["rgb"]
    assert G.MATERIALS["goggle_comb"]["rough"] >= 0.3


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
    lies inside the outrigger, between its faces, and its first ring starts there. Joint front fit (decision 47):
    with the eyeport's cut edge where Leatt's iso photos show it the plate's back end stands ahead of the side edge
    and only its top back corner reaches the shell (the brow edge). Round 13: the plate turns as one; its back end
    against Leatt's Pinata iso-right is compared where that empty helmet holds the goggle
    (test_round13_worn_plate_turns_as_one_and_leans_as_leatts; here, at his placement, it read 772 +- 15 px)."""
    Vo, Fo, prof = H.shell_outer()
    mount = G.shell_mount(prof)
    free = G.outrigger_grids()
    R, t = built["Rt"]
    S = G.h2g((np.vstack([built["parts"][n].V for n in ("goggle_strap", "goggle_strap_band")]) - t) @ R)
    for sg, (Go, Gi, anchor) in G.outrigger_grids(mount=mount).items():
        need = mount(Gi.reshape(-1, 3)).reshape(Gi.shape[:2])
        assert need[-1, -1] > 0 and need[-1].sum() < need[-1].size          # its top back corner on the shell
        gap = (np.abs(Gi[..., 0]) - need)[need > 0]
        assert G.OR_GAP - 1e-4 < gap.min() < G.OR_GAP + 0.0005              # ... resting on it, not inside
        # its hinge where the free plate's is, whatever the turn (round 14: the plate's front edge OR_PLATE_FRONT along
        # it, in the C, its outer face OR_FACE_OUT outside the hinge)
        def hinge(g):
            tt = (g[-1, :, :2] - g[0, :, :2]) / np.linalg.norm(g[-1, :, :2] - g[0, :, :2], axis=1)[:, None]
            return g[0, :, :2] - (G.OR_HINGE_LEN - G.plate_len()) * tt - sg * G.OR_FACE_OUT * np.c_[tt[:, 1], -tt[:, 0]]
        assert np.allclose(hinge(Go), hinge(free[sg][0]), atol=1e-6)
        assert np.allclose(np.linalg.norm(Go[0] - Gi[0], axis=1), G.OR_T)
        assert G.WORN_TURN[sg][0] == G.WORN_TURN[sg][1]                   # round 13: one turn, the plate rigid
        assert abs(G.WORN_TURN[sg][1] - 16.7) <= 0.5                           # measured: the turn at which the top
                                                                            # back corner clears phase 2's shell
                                                                            # (decision 51) by OR_GAP from round 14's
                                                                            # hinge (20.25 from round 12's; the
                                                                            # search steps 0.25 deg from the C's
                                                                            # stop, CAR_STOP_TURN)
        # the anchor sits between the faces near the back end, at mid height (round 8: the faces at the anchor's own
        # row; the 5 mm plate bends out along its length more than its thickness)
        j = Gi.shape[1] // 2
        i = int(np.argmin(np.linalg.norm(0.5 * (Gi + Go)[:, j] - anchor, axis=1)))
        lo, hi = sorted([abs(Gi[i, j, 0]), abs(Go[i, j, 0])])
        # (round 14: OR_ANCHOR in from the back end of the plate, now plate_len long, at its row within one)
        assert abs(i - (Gi.shape[0] - 1) * (1 - G.OR_ANCHOR / G.plate_len())) <= 1 and lo < abs(anchor[0]) < hi
        assert Gi[:, 0, 2].max() < anchor[2] < Gi[:, -1, 2].min()
        assert np.linalg.norm(Gi[-1, Gi.shape[1] // 2] - anchor) < G.OR_ANCHOR + 0.004
        # the strap starts at this side's anchor: its foremost point on this side (GOGGLE frame)
        side = S[sg * S[:, 0] > 0.05]
        end = side[np.argmin(side[:, 1])]
        assert np.linalg.norm(end[[0, 1]] - anchor[[0, 1]]) < 0.012


def test_round13_worn_plate_turns_as_one_and_leans_as_leatts():
    """Round 13 item 2 (decision 57): the worn plate's back edge (its outer face, the right plate) through Leatt's
    Pinata iso-right camera leans left going down as Leatt's does. Leatt's: where the strap's print meets the plate,
    764 px at row 860 and 751 at 980, -10.8 px a 100 rows (scratch edge13.py on the photo). Rounds 9 to 12 twisted the
    plate (the turn growing from the bottom row's need to the top's) and it leaned +3.3; rigid it leans -6.5 at any
    turn. That photo is an empty helmet: there the goggle sits 12.6 mm lower and 3.5 mm further back (round 12, the
    pink frames' best overlay), the plate meets no shell and its back edge stood at 760 / 752 px at turn 0. Round 14:
    from round 14's hinge it stands at 776 / 768 at turn 0 and 759.4 / 751.5 on the C's stop (CAR_STOP_TURN, 13.7
    deg), where the strap pulls it in to: the C's inner bar against the frame's side."""
    Vo, Fo, prof = H.shell_outer()
    cam = H.PRINT_CAMS["isoright"]

    def back_edge(grids):
        q = H.cam_project(cam, G.g2h(grids[-1][0][-1]))[0]
        o = np.argsort(q[:, 1])
        return np.interp([860.0, 980.0], q[o, 1], q[o, 0])

    u = back_edge(G.outrigger_grids(mount=G.shell_mount(prof)))
    lean = (u[1] - u[0]) / 1.2
    assert -16.0 < lean < -5.0, lean                                   # Leatt -10.8; twisted +3.3
    ty, tz, pitch, k = G._place(None)
    keep = G.PLACE
    try:
        G.PLACE = (ty + 0.0035, tz - 0.0126, pitch, k)
        u = back_edge(G.outrigger_grids(mount=G.shell_mount(prof)))
        assert G.WORN_TURN[-1] == (G.CAR_STOP_TURN, G.CAR_STOP_TURN)
        assert abs(u[0] - 764.0) < 6.0 and abs(u[1] - 751.0) < 6.0, u
        assert -16.0 < (u[1] - u[0]) / 1.2 < -5.0
    finally:
        G.PLACE = keep
        G.outrigger_grids(mount=G.shell_mount(prof))


def test_strap_crosses_the_trim_to_the_shell():
    """Decision 47: the eyeport's cut edge where Leatt's iso photos show it (helmet.PORT "iso", 16 to 23 mm behind the
    side photo's notch). The strap leaves each outrigger, crosses the trim and lands on the shell where its whole width
    lies on it: every station 45 mm wide (landing at the edge itself folded the walk across it onto the edge: 22.5 mm
    wide and 2.5 mm tall over four stations, a wedge in the iso-right render), the landing STRAP_EDGE or more behind
    the mesh's fair edge, so behind the cut edge as the photos show it (helmet.port_outline("iso"), 1.8 mm ahead of
    the mesh's) at every point across the strap, each against the edge at its own height (the strap falls towards
    the back, so its cross-section leans forward at the bottom). Main's strap landed on main's side notch, about
    15 mm ahead of it."""
    Vo, Fo, prof = H.shell_outer()
    surf = G.Surface(Vo, Fo)
    base, nrm, s, (kL, kR) = G.strap_layout(surf, G.strap_ends(G.shell_mount(prof)))
    width = np.linalg.norm(base[:, -1] - base[:, 0], axis=1)
    assert width.min() > G.STRAP_W - 0.0015, f"strap {width.min() * 1000:.1f} mm wide at station {width.argmin()}"
    a = np.array(H.port_outline("iso"))
    b = np.roll(a, -1, axis=0)

    def rear(z):
        """the cut edge's rearmost y at height z: where the outline's segments cross z"""
        dz = b[:, 1] - a[:, 1]
        t = (z - a[:, 1]) / np.where(dz != 0, dz, np.inf)
        ok = (t >= 0) & (t <= 1)
        return (a[ok, 0] + t[ok] * (b[ok, 0] - a[ok, 0])).max()

    for i in (kL, len(base) - 1 - kR):                        # the landing stations
        gap = np.array([base[i, j, 1] - rear(base[i, j, 2]) for j in range(base.shape[1])])
        assert gap.min() > 0.002, f"lands {gap.min() * 1000:+.1f} mm behind the cut edge at its height (2 mm or more)"


def test_strap_lies_where_his_07_shows_it():
    """Decision 47: his photo 07 (side-on, his left) is a camera in the helmet frame fitted to the helmet's points and
    print (research/his-photo-cameras.json, landmarks rms 2.6 px). Goggle round 8's picks of the strap's upper and
    lower edges there (photo px, between the chevron panel's lower stripe and the pink panels) against the built
    strap's edges projected through it, mm at the edge's depth: rms under 10 mm, no side off by more than 6 mm on
    average. Main's plane (-13.5 mm, rising 3 deg, fitted through a camera fitted to the goggle) put it 37 mm above
    them on average (rms 39), over the chevron panel."""
    import his_cameras
    cam = his_cameras.load()["07"]
    up = [(690, 110), (705, 104), (720, 99), (735, 91), (750, 84), (765, 78)]
    lo = [(690, 132), (705, 125), (720, 119), (735, 112), (750, 104), (765, 99)]
    Vo, Fo, prof = H.shell_outer()
    base, nrm = G.strap_layout(G.Surface(Vo, Fo), G.strap_ends(G.shell_mount(prof)))[:2]
    top = G.STRAP_CLEAR + G.SIL_H + G.STRAP_T
    off = []
    for picks, j in ((up, -1), (lo, 0)):
        E = base[:, j] + nrm[:, j] * top
        E = E[E[:, 0] > 0]                                     # his left side
        q = (E - cam["C"]) @ np.asarray(cam["R"]).T
        uv = np.c_[cam["cx"] + cam["f"] * q[:, 0] / q[:, 2], cam["cy"] - cam["f"] * q[:, 1] / q[:, 2]]
        a, b = uv[:-1], uv[1:]
        for pk in np.array(picks, float):
            t = np.clip(((pk - a) * (b - a)).sum(1) / np.maximum(((b - a) ** 2).sum(1), 1e-12), 0, 1)
            P = a + (b - a) * t[:, None]
            d = np.linalg.norm(P - pk, axis=1)
            i = int(np.argmin(d))
            off.append(d[i] * np.sign(P[i, 1] - pk[1]) * q[i, 2] * 1000.0 / cam["f"])   # mm, + below the pick
    off = np.array(off)
    rms = np.sqrt((off ** 2).mean())
    assert rms < 10.0 and abs(off[:6].mean()) < 6.0 and abs(off[6:].mean()) < 6.0, \
        f"strap edges rms {rms:.1f} mm off his 07 (upper {off[:6].mean():+.1f}, lower {off[6:].mean():+.1f} mm)"


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
    # the crosshatch full only at 2.5 px a period of its finer family (round 11's twill: 0.677 mm, 3.1 px)
    assert min(p for p, _ in SA.TWILL) / SA.FADE_FINE[0] >= 2.5


def test_round10_plate_tapers_with_chamfered_back_corners():
    """Round 10 item 2: Leatt's plate (his goggle photos, iso55 and phr) narrows from 63.5 mm at the frame to about
    50 mm at its back and its back corners are cut at 45 deg (2 mm top, 3 mm bottom); round 9's was 63.5 to 58.7 mm
    with square corners (plate edges 1.7 / 2.7 mm rms off Leatt's in iso55, now 1.1 / 1.5). Round 14: the plate
    starts in the C (OR_PLATE_FRONT), its front edge as tall as the C (CAR_Z, 61.1 mm: Leatt's C in iso55, rows 800
    to 1124 at 5.32 px a mm) less its cut corners (OR_FRONT_CUT, 45 deg)."""
    for sg, (Go, Gi, anchor) in G.outrigger_grids().items():
        h = np.linalg.norm(Go[:, -1] - Go[:, 0], axis=1) * 1000
        mid = 0.5 * (Go[:, -1] + Go[:, 0])
        back = np.linalg.norm(mid - mid[-1], axis=1) * 1000
        full = h[0] + 1000 * sum(G.OR_FRONT_CUT)
        assert abs(full - 1000 * (G.CAR_Z[1] - G.CAR_Z[0])) < 0.1 and 60.0 < full < 66.0, (sg, h[0], full)
        assert 10.0 < full - h[-1] < 16.0, (sg, full, h[-1])               # the taper and the cut corners
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
    T = np.array([[f[0], f[i], f[i + 1]] for f, m in zip(part.F, part.M) if m in ("goggle_frame", "goggle_comb")
                  for i in range(1, len(f) - 1)])        # round 11: the comb in its own satin material
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


# ---------------------------------------------------------------- round 11: parts inside parts
def solids(P):
    """A part's connected pieces, welded by position: (V, T, edges not used by exactly two triangles) each."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    V0 = np.asarray(P.V, float)
    _, idx, inv = np.unique(np.round(V0 / 1e-7).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    V, T = V0[idx], inv.ravel()[tris(P).astype(np.int64)]
    e0, e1 = np.r_[T[:, 0], T[:, 1], T[:, 2]], np.r_[T[:, 1], T[:, 2], T[:, 0]]
    lab = connected_components(coo_matrix((np.ones(len(e0)), (e0, e1)), shape=(len(V), len(V))), directed=False)[1]
    out = []
    for c in np.unique(lab[T[:, 0]]):
        Tc = T[lab[T[:, 0]] == c]
        cnt = np.unique(np.sort(np.r_[Tc[:, [0, 1]], Tc[:, [1, 2]], Tc[:, [2, 0]]], axis=1), axis=0,
                        return_counts=True)[1]
        out.append((V, Tc, int((cnt != 2).sum())))
    return out


def inside_solid(P, V, T, cell=0.001):
    """Points of P inside the closed mesh (V, T): rays both ways along one fixed random direction cross it an odd
    number of times (both must agree). The triangles are binned on a grid across the rays (winding numbers are too
    slow against the frame's 37,000 triangles)."""
    R = np.linalg.qr(np.random.default_rng(7).normal(size=(3, 3)))[0]
    P, V = P @ R, V @ R
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    t2 = np.stack([A[:, [0, 2]], B[:, [0, 2]], C[:, [0, 2]]], 1)
    lo, hi = np.floor(t2.min(1) / cell).astype(np.int64), np.floor(t2.max(1) / cell).astype(np.int64)
    nx, nz = hi[:, 0] - lo[:, 0] + 1, hi[:, 1] - lo[:, 1] + 1
    cnt = nx * nz
    tid = np.repeat(np.arange(len(T)), cnt)
    off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    kt = (lo[tid, 0] + off % nx[tid]) * (1 << 31) + (lo[tid, 1] + off // nx[tid])
    o = np.argsort(kt, kind="stable")
    kt, tid = kt[o], tid[o]
    pc = np.floor(P[:, [0, 2]] / cell).astype(np.int64)
    kp = pc[:, 0] * (1 << 31) + pc[:, 1]
    left, n = np.searchsorted(kt, kp, "left"), np.searchsorted(kt, kp, "right") - np.searchsorted(kt, kp, "left")
    pid = np.repeat(np.arange(len(P)), n)
    tt = tid[np.repeat(left, n) + (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n))]
    a = A[tt][:, [0, 2]]
    v0, v1, v2 = B[tt][:, [0, 2]] - a, C[tt][:, [0, 2]] - a, P[pid][:, [0, 2]] - a
    den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
    ok = np.abs(den) > 1e-20
    den = np.where(ok, den, 1.0)
    u = (v2[:, 0] * v1[:, 1] - v2[:, 1] * v1[:, 0]) / den
    v = (v0[:, 0] * v2[:, 1] - v0[:, 1] * v2[:, 0]) / den
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    y = A[tt][:, 1] + u * (B[tt][:, 1] - A[tt][:, 1]) + v * (C[tt][:, 1] - A[tt][:, 1])
    up = np.bincount(pid[hit & (y > P[pid][:, 1])], minlength=len(P))
    dn = np.bincount(pid[hit & (y < P[pid][:, 1])], minlength=len(P))
    return (up % 2 == 1) & (dn % 2 == 1)


def surface_samples(V, T, h, seed=0):
    """Random points on the mesh's triangles, about one per h x h, and its vertices."""
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.maximum(1, np.ceil(0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1) / (h * h))).astype(int)
    tid = np.repeat(np.arange(len(T)), n)
    r1, r2 = np.random.default_rng(seed).random((2, len(tid)))
    f = r1 + r2 > 1
    r1[f], r2[f] = 1 - r1[f], 1 - r2[f]
    return np.vstack([A[tid] + (B[tid] - A[tid]) * r1[:, None] + (C[tid] - A[tid]) * r2[:, None], V[np.unique(T)]])


def depth_below(Q, V, T, h=0.0001):
    """Each point's distance to the mesh's surface (dense samples of the triangles near the points)."""
    if not len(Q):
        return np.zeros(0)
    c = V[T].mean(1)
    sel = np.all((c > Q.min(0) - 0.016) & (c < Q.max(0) + 0.016), axis=1)
    return cKDTree(surface_samples(V, T[sel], h)).query(Q)[0]


def lens_coords(L, P):
    """(s, z, off) on the lens of points P (L.point's inverse): the lens is its plan curve swept along the tilted
    direction Rl and its normal is square to Rl, so across Rl the plan curve's nearest point gives s."""
    tt = math.tan(L.tilt)
    Rl = np.array([0.0, tt, 1.0]) / math.hypot(tt, 1.0)
    s = np.linspace(-L.S[-1], L.S[-1], int(L.S[-1] / 2e-5) * 2 + 1)
    C, N = L.point(s, np.zeros_like(s), 0.0)
    i = cKDTree(C - np.outer(C @ Rl, Rl)).query(P - np.outer(P @ Rl, Rl))[1]
    Q = P - C[i]
    off = (Q * N[i]).sum(1)
    return s[i], (Q - off[:, None] * N[i]) @ Rl / math.hypot(tt, 1.0), off


def outside_window(Co, s, z):
    """Signed distance (m) of (s, z) from the lens window's edge Co: > 0 outside the window (under the frame)."""
    from matplotlib.path import Path
    P = np.c_[s, z]
    if not len(P):
        return np.zeros(0)
    A, E = Co, np.roll(Co, -1, 0) - Co
    d = np.full(len(P), np.inf)
    for k in range(0, len(A), 64):
        a, e = A[k:k + 64], E[k:k + 64]
        u = np.clip(((P[:, None] - a[None]) * e[None]).sum(-1) / np.maximum((e * e).sum(-1), 1e-18)[None], 0, 1)
        d = np.minimum(d, np.linalg.norm(P[:, None] - a[None] - u[..., None] * e[None], axis=-1).min(1))
    return np.where(Path(Co).contains_points(P), -d, d)


# pairs of goggle parts (A, B): A's surface inside B. "none": they must not meet (0.02 mm, touching); "window": A may
# be inside B only under the frame (outside the lens window: the lens in its groove), "bridge": outside the window
# or within 0.5 mm of its edge (the comb's root in the band) or no deeper than RIB_SINK (the comb's back moulded into
# the bridge; 0.1 mm more for the two parts' tessellations), "seat": the foam
# glued on the frame's back face (shared face, tessellated apart by up to 0.5 mm where the back face twists)
GOGGLE_PAIRS = [(a, b, "none") for a, b in (
    ("noseribs", "lens_outer"), ("noseribs", "lens_inner"), ("lens_outer", "noseribs"), ("lens_inner", "noseribs"),
    ("noseribs", "foam"), ("foam", "noseribs"), ("foam", "lens_outer"), ("foam", "lens_inner"),
    ("lens_outer", "foam"), ("lens_inner", "foam"), ("lens_outer", "lens_inner"), ("lens_inner", "lens_outer"),
    ("noseguard", "lens_outer"), ("noseguard", "lens_inner"), ("lens_outer", "noseguard"),
    ("lens_inner", "noseguard"), ("noseguard", "foam"), ("foam", "noseguard"), ("noseguard", "noseribs"),
    ("noseribs", "noseguard"), ("outriggers", "lens_outer"), ("outriggers", "lens_inner"),
    ("lens_outer", "outriggers"), ("lens_inner", "outriggers"),
    # round 13: the strap carriers and the strap's ends threaded behind them
    ("carrier", "frame"), ("frame", "carrier"), ("carrier", "lens_outer"), ("carrier", "lens_inner"),
    ("lens_outer", "carrier"), ("lens_inner", "carrier"), ("carrier", "posts"), ("posts", "carrier"),
    ("strap_end", "frame"), ("frame", "strap_end"), ("strap_end", "carrier"), ("carrier", "strap_end"),
    ("strap_end", "lens_outer"), ("strap_end", "lens_inner"), ("lens_outer", "strap_end"),
    ("lens_inner", "strap_end"), ("strap_end", "posts"), ("posts", "strap_end"))] + [
    ("lens_outer", "frame", "window"), ("lens_inner", "frame", "window"), ("frame", "lens_outer", "window"),
    ("frame", "lens_inner", "window"), ("noseribs", "frame", "bridge"), ("frame", "noseribs", "bridge"),
    ("foam", "frame", "seat"), ("frame", "foam", "seat")]


def goggle_overlaps(parts, gp=None, h=0.0004):
    """Round 11: the goggle's parts (GOGGLE frame, by name) that run into each other against GOGGLE_PAIRS, and the
    parts looked inside that are not closed solids. Returns a list of faults (empty: none)."""
    gp = gp or G.GP
    L = G.LensSurface(gp)
    # the window's edge, the top band's teeth in: the frame's lens edge (round 12: its foot moved out on the pillars)
    Co = G.frame_rings(gp)[1]["Co"]
    back = getattr(G, "lens_back", lambda s, z: 0.0 * s)           # round 12: the lens's ends curl back
    comps, faults = {}, []
    for P in parts:
        key = P.name.replace("goggle_", "")
        for V, T, bad in solids(P):
            X = V[np.unique(T)]
            if key == "lens":
                s_, z_, off = lens_coords(L, X)
                k = "lens_outer" if (off + back(s_, z_)).mean() > -0.0015 else "lens_inner"
            elif key == "outriggers" and len(X) != 2 * len(G.or_u()) * G.OR_NV:
                # round 13: the strap carrier (its clear post, moulded 0.5 mm into it, unpaired); round 14: on the
                # plate, with its arms (unpaired: they reach the hinge in the frame's side)
                k = "carrier" if len(X) > 100 else "carrier_part"
            else:
                k = key
            comps.setdefault(k, []).append((V, T, bad))
    for k in ("frame", "lens_outer", "lens_inner", "noseribs", "foam", "noseguard", "outriggers", "carrier",
              "strap_end"):
        if k not in comps:
            faults.append(f"{k}: missing")
        elif sum(b for _, _, b in comps[k]):
            faults.append(f"{k}: not closed ({sum(b for _, _, b in comps[k])} open or shared edges)")
    for a, b, rule in GOGGLE_PAIRS:
        if a not in comps or b not in comps:
            continue
        Pa = np.vstack([surface_samples(V, T, h) for V, T, _ in comps[a]])
        for V, T, _ in comps[b]:
            U = V[np.unique(T)]
            Q = Pa[np.all((Pa > U.min(0) - 1e-5) & (Pa < U.max(0) + 1e-5), axis=1)]
            Q = Q[inside_solid(Q, V, T)] if len(Q) else Q
            if not len(Q):
                continue
            if rule in ("window", "bridge"):
                s, z, _ = lens_coords(L, Q)
                # inside the window by more than 0.05 mm (the comb: 0.5 mm, its 1 mm triangles across the edge)
                Q = Q[outside_window(Co, s, z) < (-0.0005 if rule == "bridge" else -0.00005)]
            dep = depth_below(Q, V, T)
            lim = dict(none=0.00002, window=0.00002, bridge=G.RIB_SINK + 0.0001, seat=0.0006)[rule]
            if len(dep) and dep.max() > lim:
                q = Q[np.argmax(dep)] * 1000
                faults.append(f"{a} in {b} ({rule}): {int((dep > lim).sum())} points, {dep.max() * 1000:.2f} mm "
                              f"deep at ({q[0]:.1f}, {q[1]:.1f}, {q[2]:.1f}) mm")
    return faults


def test_round11_goggle_parts_do_not_run_into_each_other(built):
    """Round 11 item 1: no goggle part runs into another it should not meet, on the goggle alone and on him (parts
    back in the GOGGLE frame): the comb, both lenses, the foam, the nose guard and the outriggers stay out of each
    other; the lenses enter the frame (and the chassis, part of it) only under it, in their groove; the comb enters the
    frame only at its root under the window or by RIB_SINK into the bridge behind it; the foam sits on the frame's back
    face. Every part looked inside is a closed solid. Main at round 10 failed: the comb 0.31 mm inside the inner lens
    (3,700 points, |x| 5 to 40 mm, z -49 to -17), the nose foam 0.9 mm inside the inner lens, the inner lens 1.5 mm
    inside the frame within the window (the bridge folded round it), the bridge's plate 1.4 mm inside the foam, and
    the outer lens and the comb open (6 and 92 edges)."""
    R, t = built["Rt"]
    worn = []
    for name, P in built["parts"].items():
        if name in ("goggle_frame", "goggle_lens", "goggle_noseribs", "goggle_foam", "goggle_noseguard",
                    "goggle_outriggers", "goggle_strap_end", "goggle_posts"):
            Q = H.Part(name)
            Q.V, Q.F = G.h2g((np.asarray(P.V) - t) @ R), P.F
            worn.append(Q)
    for label, parts in (("alone", G.free_parts()), ("worn", worn)):
        faults = goggle_overlaps(parts)
        assert not faults, (label, faults)


def test_round11_strap_weave_is_a_short_twill():
    """Round 11 item 2: round 10's weave read at 4x as long regular parallel ripples (in the tile's spectrum two
    families only 35 deg apart, both near the strap's across direction); Leatt's (Pinata iso-right and MY27 back at
    4x, its two families solved through the view's Jacobian) is a soft, short twill: 0.97 and 0.68 mm periods at
    -37.7 and 53.6 deg from across, each coherent over about two periods. In the tile's fine relief (its body) the
    power at 0.5 to 1.7 mm periods has two direction peaks 80 to 100 deg apart, the weaker 0.3 of the stronger or
    more; the families' coherence is three periods or less."""
    import goggle_strap_art as SA
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(H.TEXDIR, "goggle_strap_weave.png")).convert("RGB"), float) / 255.0
    ny, nx = a.shape[:2]
    body = a[int(ny * 0.3):int(ny * 0.7), :, 0]
    P = np.abs(np.fft.fft2(body - body.mean())) ** 2
    fy = np.fft.fftfreq(body.shape[0], SA.W_MM / ny)[:, None] + np.zeros((1, body.shape[1]))
    fx = np.fft.fftfreq(body.shape[1], SA.TILE_MM / nx)[None, :] + np.zeros((body.shape[0], 1))
    band = (np.hypot(fx, fy) > 0.6) & (np.hypot(fx, fy) < 2.0)
    h = np.histogram(np.degrees(np.arctan2(fy, fx))[band] % 180.0, bins=36, range=(0, 180), weights=P[band])[0]
    h = (np.roll(h, 1) + h + np.roll(h, -1)) / 3
    i1 = int(np.argmax(h))
    apart = np.abs(((np.arange(36) - i1) * 5 + 90) % 180 - 90)
    i2 = int(np.argmax(np.where(apart >= 30, h, -1.0)))
    assert 80 <= apart[i2] <= 100, (i1 * 5, i2 * 5)
    assert h[i2] >= 0.3 * h[i1], h[i2] / h[i1]
    assert len(SA.TWILL) == 2 and max(SA.TWILL_COH) <= 3.0


def test_round11_strap_leatt_is_a_raised_layer(built):
    """Round 11 item 3: Leatt's strap LEATT at 4x and 8x (Pinata iso-right) is a layer standing on the fabric, crisp
    edged, with a lit lip along its lower edges; rounds 9 and 10 painted it into the print (flat, soft-edged at 4x)
    and stretched it 1.34 times along (162 mm long against 120). Now geometry on the band: two wordmarks of
    goggle_strap_logo, each a top STRAP_LOGO_T above the fabric with walls sunk into it (on a flat strap every edge
    used once lies on the sunk bottom loops: closed down to the fabric), at the wordmark's own aspect: 30.15 mm tall
    and about 120 mm long."""
    import goggle_strap_art as SA
    s = np.arange(0, 0.646, 0.0025)
    S_, B_ = np.meshgrid(s, G.STRAP_ACROSS, indexing="ij")
    base = np.stack([S_, B_, 0 * S_], -1)
    nrm = np.zeros_like(base)
    nrm[..., 2] = 1.0
    Lp = SA.STRAP_LEN_UV * 1000.0
    boxes = [(x0 / Lp * s[-1], G.STRAP_ACROSS[0] + (1 - y0 / SA.W_MM) * G.STRAP_W, lh / 1000.0)
             for x0, y0, lh in SA.leatt_boxes()]
    p = H.Part("t")
    loops = G.strap_logo(p, base, nrm, s, 0.0027, boxes)
    assert len(loops) == 2
    for L2 in loops:
        P = np.vstack(L2)
        assert abs(np.ptp(P[:, 0]) * 1000 - 120.0) < 4.0, np.ptp(P[:, 0]) * 1000
        assert abs(np.ptp(P[:, 1]) * 1000 - 30.15) < 1.0, np.ptp(P[:, 1]) * 1000
    V = np.asarray(p.V)
    assert abs(V[:, 2].max() - (0.0027 + G.STRAP_LOGO_T)) < 1e-6 and G.STRAP_LOGO_T >= 0.0003
    _, inv = np.unique(np.round(V / 1e-8).astype(np.int64), axis=0, return_inverse=True)
    inv = inv.ravel()
    cnt = {}
    for f in p.F:
        for a_, b_ in zip(f, f[1:] + f[:1]):
            k = (min(inv[a_], inv[b_]), max(inv[a_], inv[b_]))
            cnt[k] = cnt.get(k, 0) + 1
    once = np.array([k for k, c in cnt.items() if c == 1])
    assert max(cnt.values()) == 2 and len(once)
    rep = np.zeros(inv.max() + 1, int)
    rep[inv] = np.arange(len(inv))
    assert np.allclose(V[rep[once.ravel()], 2], 0.0027 - G.STRAP_LOGO_SINK, atol=1e-7)
    band = built["parts"]["goggle_strap_band"]
    assert sum(m == "goggle_strap_logo" for m in band.M) > 10000


def test_round11_chassis_tone_and_clip_tabs():
    """Round 11 item 4: the chassis band read 37 in iso55 (L p50 of its face) against Leatt's white ISO 19, and its
    slots were empty where Leatt's show the strap clip's grey tab (L 32 to 35) at each slot's end away from the post,
    2.4 to 3 mm long, over the lens side 0.68 of the slot's width. Now a darker, less specular black (20.4 in iso55)
    and per slot a closed tab of goggle_clip: CHASSIS_CLIP_LEN long from the slot's far end, inside the pocket (below
    the mouth, above the floor)."""
    ch = G.MATERIALS["goggle_chassis"]
    assert max(ch["rgb"]) <= 10 and ch.get("spec", 0.5) <= 0.15
    fr, info = G.build_frame()
    V = np.asarray(fr.V)
    rings, _ = G.frame_rings()
    mouth = cKDTree(np.vstack([rings[0] + (rings[1] - rings[0]) * t for t in np.linspace(0, 1, 21)]))
    clip = [f for f, m in zip(fr.F, fr.M) if m == "goggle_clip"]
    P = V[sorted({i for f in clip for i in f})]
    assert len(P)
    for sg in (1, -1):
        for (z0, z1), ln in zip(G.CHASSIS_SLOTS, G.CHASSIS_CLIP_LEN):
            Q = P[(np.sign(P[:, 0]) == sg) & (P[:, 2] > z0 - 0.002) & (P[:, 2] < z1 + 0.002)]
            assert len(Q) >= 8, (sg, z0)
            far = Q[:, 2].max() if z0 > 0 else Q[:, 2].min()
            assert (far > z1 - 0.0025) if z0 > 0 else (far < z0 + 0.0025), (sg, z0, far)   # at the far end
            run = rings[0][(np.sign(rings[0][:, 0]) == sg) & (np.abs(rings[0][:, 0]) >= G.CHASSIS_S)
                           & (rings[0][:, 2] >= z0) & (rings[0][:, 2] <= z1)]
            t = run[np.argmax(run[:, 2])] - run[np.argmin(run[:, 2])]          # along the slot
            t /= np.linalg.norm(t)
            top = Q[:len(Q) // 4]                                              # its first rail (the top's edge)
            assert ln - 0.0003 < np.ptp(top @ t) < ln + 0.0001, (sg, z0, np.ptp(top @ t))
            d = mouth.query(Q)[0]
            assert d.min() > 0.00015 and d.max() < G.CHASSIS_SLOT_D + 0.0005, (d.min(), d.max())


def _hue_runs(row, mm_px, d0_px, step_mm=0.5, d_max=40.0, sign=1):
    """Hue (deg) and saturation of a print row at distances from a column, every step_mm."""
    import colorsys
    out = []
    for d in np.arange(0.0, d_max, step_mm):
        x = int(round(d0_px + sign * d / mm_px))
        c = np.median(row[:, x - 1:x + 2].reshape(-1, 3), 0) / 255.0
        h, s_, v_ = colorsys.rgb_to_hsv(*c)
        out.append((d, h * 360.0, s_))
    return out


def test_round12_strap_print_by_the_outrigger():
    """Round 12 item 1: in Pinata iso-right the print's colour changes stood 15 / 55 / 105 px from the plate where
    Leatt's stand 45 / 65 / 95 (the ISO's first 30 mm seen edge on: its yellow run a third as long, its red twice).
    Leatt's iso-right strap by the outrigger, at 0.31 mm a px: along its middle yellow to 12.7 mm, orange to 17, red to
    22.9, then magenta; along its lower fifth yellow to 16.7, orange to 23.9, red to 31.9. Read on the texture (both
    ends) from where the strap leaves the outrigger: the yellow run ends 10.5 to 15 mm (middle) and 14 to 19.5 (lower
    fifth), magenta starts 20 to 25.5 (middle) and 28 to 34 (lower fifth)."""
    import goggle_strap_art as SA
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(H.TEXDIR, "goggle_strap_print.jpg")).convert("RGB"), float)
    ny, nx = a.shape[:2]
    mm_px = SA.STRAP_LEN_UV * 1000.0 / nx
    a0 = SA.anchor_mm()

    def ends(frac):                                       # frac across from the top edge
        r = a[int(frac * ny) - 1:int(frac * ny) + 2]
        return (_hue_runs(r, mm_px, a0 / mm_px), _hue_runs(r, mm_px, nx - 1 - a0 / mm_px, sign=-1))

    def yellow_end(runs):
        return next(d for d, h, s_ in runs if d > 2.0 and not (40.0 <= h < 70.0 and s_ > 0.3))

    def magenta_start(runs):
        return next(d for d, h, s_ in runs if 295.0 <= h < 345.0 and s_ > 0.3)

    for frac, (y_lo, y_hi), (m_lo, m_hi) in ((0.5, (10.5, 15.0), (20.0, 25.5)), (0.8, (14.0, 19.5), (28.0, 34.0))):
        for runs in ends(frac):
            assert y_lo <= yellow_end(runs) <= y_hi, (frac, yellow_end(runs))
            assert m_lo <= magenta_start(runs) <= m_hi, (frac, magenta_start(runs))


def test_round12_strap_u_is_true_mm_from_each_end(built):
    """Round 12 item 1: the print is laid in mm from each end whatever length the strap is built to (the helmet
    agent refits its path; round 11's u = s / s_total stretched the print by the length's ratio): strap_u over the
    first and last thirds gives the print's true mm, the difference taken up over the back's even middle third, and
    rises all along. The built band's u by its left end is its arc length over STRAP_LEN_UV (to its height over the
    shell's curve, 4 %)."""
    import goggle_strap_art as SA
    L = SA.STRAP_LEN_UV
    for total in (0.60, 0.6436, 0.68):
        s = np.linspace(0.0, total, 601)
        u = SA.strap_u(s, total)
        assert abs(u[0]) < 1e-12 and abs(u[-1] - 1.0) < 1e-12 and np.all(np.diff(u) > 0), total
        a_, b_ = s <= total / 3, s >= 2 * total / 3
        assert np.allclose(u[a_] * L, s[a_], atol=1e-9) and np.allclose((1 - u[b_]) * L, total - s[b_], atol=1e-9)
    band = built["parts"]["goggle_strap_band"]
    V = np.asarray(band.V)
    pts = {}
    for f, m, uv in zip(band.F, band.M, band.UV):
        if m == "goggle_strap":
            for i, (uu, vv) in zip(f, uv):
                if abs(vv - 0.5) < 1e-6 and uu < 0.3:
                    pts[round(uu, 9)] = V[i]
    us = np.array(sorted(pts))
    P = np.array([pts[k] for k in us])
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    assert len(us) > 20
    assert abs((us[-1] - us[0]) * L / arc[-1] - 1.0) < 0.04, ((us[-1] - us[0]) * L, arc[-1])


def test_round12_plate_front_hides_behind_the_c():
    """Round 12 item 2: in Leatt's Pinata iso-right his plate shows 762 to 840 px and his frame's pink side 845 to 918;
    ours showed 760 to 889, over the frame's side (whose back edge projects at 845, as his), and in iso55 (free) his
    side face starts at 920 px, ours at 950. Placed as on his empty helmet (12.6 mm lower, 3.5 mm back) ours read wider
    still: shape, not place. The plate's front now hides inside the frame's side face: its hinge (the outer face's
    front edge) at least 1.5 mm inside the frame's outer side at the hinge's own height and depth, and the lens (whose
    ends curl back into the frame's sides past the hinge, item 3) stays 0.3 mm inside the plate's inner face even with
    the plate turned straight back (grown its full groove from the moved lens edge it ran 0.9 mm into the plate),
    the plate shortened by the hinge's move back (its back end, the strap's exit, stays). Round 14 (the joint fit, C
    on the plate): Leatt's C stands beyond the frame's end with the plate hidden behind it (phr, the Forge front;
    round 13's review at 1:1), so the plate starts in the C, at its outer corner, 15.5 mm along from the hinge (which
    has no part: the arms start CAR_ARM_FROM along): at the C's stop (CAR_STOP_TURN, the least turn) its front edge
    stands 5.8 mm outside the frame's side at its height and depth and is the C's height, and no lens point lies in
    the plate (the lens's ends curl into the frame's sides well ahead of it)."""
    rings, _ = G.frame_rings()
    R_ = np.vstack(rings)
    lens = np.asarray(G.build_lens().V)
    a = G.CAR_STOP_TURN
    for sg, (box, end, n) in G.outrigger_frames(turn={1: a, -1: a}).items():
        front = box[[0, 1]].mean(0)
        ring = R_[(np.abs(R_[:, 2] - front[2]) < 0.004) & (np.abs(R_[:, 1] - front[1]) < 0.0015) & (sg * R_[:, 0] > 0)]
        assert len(ring) >= 3
        assert sg * front[0] - (sg * ring[:, 0]).max() > 0.004, ((sg * ring[:, 0]).max(), sg * front[0])
        assert np.allclose(np.sort(box[[0, 1], 2]), G.CAR_Z, atol=1e-6), box[[0, 1], 2]
        t = box[2] - box[0]
        t[2] = 0.0
        t /= np.linalg.norm(t)
        along, out = (lens - box[0]) @ t, (lens - box[0]) @ (n / np.linalg.norm(n))
        assert not np.any((along > -0.001) & (out > -G.OR_T - 0.0003) & (np.abs(lens[:, 2] - front[2]) < 0.03))
        assert abs(G.OR_HINGE_LEN + G.OR_HINGE_BACK - G.OR_LEN) < 1e-9


def test_round12_side_section_lens_curls_back_and_the_wall_stands_up():
    """Round 12 item 3: Leatt's lens ends at x 1656 to 1658 px in iso55 (rows 820 to 1100) and 1597 to 1600 in phr,
    the black band beyond it 46 px wide; ours ran to 1671 to 1674 and 1612 to 1614 (its last 20 mm, nearly edge on,
    covered the band's first 17 px), and on the near side our pillar wall leaned out 32 to 37 deg off the lens normal
    and showed as a black strip (983 to 994 px) where his frame colour runs to the lens (seen from iso55 a wall there
    shows only when it leans out more than 17 deg). Now the lens's ends curl back 3 mm into the frame's sides and the
    wall stands within 17 deg of the lens normal on the pillars. Its taller wall faced the studio key's mirror
    direction on the lower far pillar (a white patch, L 228 against Leatt's 17), so the chassis is a matte moulding.
    Over the pillar's height the lens turns away late (at s 60 to 77 mm within 80 deg of the iso55 view)."""
    lens = np.asarray(G.build_lens().V)
    for view, rows, lo, hi in (("iso55", (860, 1100), 1652.0, 1662.0), ("phr", (880, 1020), 1595.0, 1605.0)):
        x = np.array(json.load(open(G.CAMERAS))[view]["x"])
        q = G.photo_project(x, lens, 1920, 1920)[0]
        for y0 in range(rows[0], rows[1], 40):
            far = q[(q[:, 1] > y0) & (q[:, 1] < y0 + 40), 0].max()
            assert lo < far < hi, (view, y0, far)
    rings, info = G.frame_rings()
    Co = info["Co"]
    N = G.LensSurface(G.GP).point(Co[:, 0], Co[:, 1], 0.0)[1]
    T = np.roll(rings[0], -1, 0) - np.roll(rings[0], 1, 0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    D = rings[1] - rings[0]                                   # gap a, the wall up from the lens, across the edge
    D -= T * np.sum(D * T, axis=1)[:, None]
    lean = np.degrees(np.arccos(np.abs(np.sum(D * N, axis=1)) / np.linalg.norm(D, axis=1)))
    pillar = (np.abs(Co[:, 0]) > 0.095) & (np.abs(Co[:, 1]) < 0.02)
    assert pillar.sum() >= 20 and lean[pillar].max() < 17.0, lean[pillar].max()
    assert G.MATERIALS["goggle_chassis"].get("spec", 0.5) == 0.0
    # over the pillar's height the curl starts late, as Leatt's lens turns away only near its end: started at 60 mm
    # there the lens at s 72 to 95 mm lay at 81 to 87 deg to the iso55 view, mirrored the black wall beside it and
    # read dark from x 1645 px (Leatt's lens colour runs to 1657); along the lower band's edge it starts at 60 (fair)
    az, el, roll, d = np.array(json.load(open(G.CAMERAS))["iso55"]["x"])[:4]
    a, e = np.radians(az), np.radians(el)
    cam = np.array([np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)]) * d
    L = G.LensSurface(G.GP)
    s, z = np.meshgrid(np.linspace(0.060, 0.077, 18), np.linspace(-0.010, 0.010, 5))
    s, z = s.ravel(), z.ravel()

    def front(ds, dz):
        return L.point(s + ds, z + dz, -G.lens_back(s + ds, z + dz))[0]
    P = front(0.0, 0.0)
    N = np.cross(front(1e-4, 0.0) - front(-1e-4, 0.0), front(0.0, 1e-4) - front(0.0, -1e-4))
    V = cam - P
    inc = np.degrees(np.arccos(np.abs(np.sum(N * V, 1)) / np.linalg.norm(N, axis=1) / np.linalg.norm(V, axis=1)))
    assert inc.max() < 80.0, inc.max()
    assert G.lens_back(0.075, -0.036) > 0.0006 and G.lens_back(0.099, 0.0) > 0.00299


def test_round12_face_foam_is_matte():
    """Round 12 item 4: the rim above the near tongues in phr (Leatt's 3 to 7 px, L 75 to 95 on its upper roll) is
    mostly the face foam's top seen past the comb (the part buffer; the bridge shows only between the tongues). At
    sheen 0.6 its roll glowed at that grazing view: rim L p50 138, the roll 150 to 200; sheen 0.2 rendered 120 and
    sheen 0 96. Polyurethane foam is matte: no sheen, rough 0.9 or more, and dark (rgb under 50)."""
    foam = G.MATERIALS["goggle_foam"]
    assert foam.get("sheen", 0.0) <= 0.05 and foam.get("rough", 0.5) >= 0.9 and max(foam["rgb"]) < 50, foam


def test_round13_vent_teeth_follow_the_joint_read():
    """Round 13 item 4: the top band's lens edge at the vents, read through three views jointly (the white ISO and the
    Pinata ISO through the iso55 camera, the yellow studio photo phy through its own; scratch saw13.py and
    sawfit13b.py): each view's drop below the band's line by the edge's |s| at 1 mm (its line through its read at |s|
    41 to 43 and 81 to 85, beyond the vents), the median of the three (the views scatter about it by rms 0.42 mm).
    The model's drop follows it over 47 to 71 mm to rms 0.35 (round 13: 0.20; main's teeth 0.77). At 79 and 80 all
    three read no drop (within 0.65 mm; main's teeth 1.5). Between 72 and 78 they disagree on where the second tooth's
    end face meets the band (the white ISO 75, iso55 77, phy 78) and nothing more is asserted."""
    read = np.array([-0.5, -0.1, 0.4, 0.4, 0.6, 0.7, 1.1, 1.2, 1.4, 1.5, 1.4, 0.9, 0.6, 1.1, 1.1, 2.0, 2.1, 2.3, 2.3,
                     2.4, 2.6, 2.6, 2.7, 2.9, 2.9])
    sg = np.arange(47.0, 72.0, 1.0)
    Co = G.outlines(G.GP)[0]
    drop = (G.outlines(G.GP, teeth=False)[0][:, 1] - Co[:, 1]) * 1000
    s = np.abs(Co[:, 0]) * 1000
    m = (Co[:, 1] > 0) & (Co[:, 0] < 0)
    o = np.argsort(s[m])
    d = np.interp(sg, s[m][o], drop[m][o])
    assert np.sqrt(np.mean((d - read) ** 2)) < 0.35, np.sqrt(np.mean((d - read) ** 2))
    assert np.interp([79.0, 80.0], s[m][o], drop[m][o]).max() < 0.5


def test_round13_face_foam_has_no_grazing_gloss():
    """Round 13 item 5: the comb's rim in phr (the face foam's top seen past the comb at a grazing view) still read
    brighter than Leatt's with no sheen: its Fresnel specular (Specular IOR Level 0.5 by default). At 0.1 the rim's
    L p50 reads 86 (Leatt 87, round 12 97) and its peak 94 (Leatt 93, round 12 99), the run's top pixel (the edge's
    blend with the backdrop) left out on both sides."""
    assert G.MATERIALS["goggle_foam"].get("spec", 0.5) <= 0.1


# ---------------------------------------------------------------- round 13: the strap carrier (decision 57)
def carrier_pieces(**kw):
    """Round 13: the far (x > 0) strap carrier, its clear post and the strap's end behind it, from the free goggle
    (GOGGLE frame): {name: (V, T, open edges)}. Round 14: on the plate, its arms (8 corners each), the post only on
    request (free_parts(post=True)), the wall behind the windows' outer part (8 corners) apart from the strap."""
    parts = {P.name: P for P in G.free_parts(**kw)}
    out = {}
    n_plate = 2 * len(G.or_u()) * G.OR_NV
    for V, T, bad in solids(parts["goggle_outriggers"]):
        X = V[np.unique(T)]
        if X[:, 0].mean() > 0.06 and len(X) != n_plate:
            k = "arm" if len(X) == 8 else "post" if len(X) < 100 else "carrier"
            out[k + ("2" if k in out else "")] = (V, T, bad)
    for V, T, bad in (solids(parts["goggle_strap_end"]) if "goggle_strap_end" in parts else []):
        X = V[np.unique(T)]
        if X[:, 0].mean() > 0:
            out["strap_wall" if len(X) == 8 else "strap_end"] = (V, T, bad)
    return out, parts


# round 14: Leatt's lens post's head (u px, measured on the photos: scratch crops14.py) in the views that see the C;
# the Forge front's camera spreads the two posts 606 px apart where the photo has 542 (12 % wide): its u are scaled
# by both posts
POST_HEAD_U = {"iso55": 1679.5, "wiso": 1678.0, "phr": 1618.5, "frg": 1656.0}
POST_HEAD_U_R = {"frg": 1114.0}


def post_relative(view):
    """Round 14: the map from a camera's u to the photo's near the far lens post: u -> s u + c."""
    x = json.load(open(G.CAMERAS))[view]["x"]
    lm = G.photo_landmarks()
    mL = G.photo_project(x, np.atleast_2d(lm["POST_L"]), 1920, 1920)[0][0, 0]
    s = 1.0
    if view in POST_HEAD_U_R:
        mR = G.photo_project(x, np.atleast_2d(lm["POST_R"]), 1920, 1920)[0][0, 0]
        s = (POST_HEAD_U[view] - POST_HEAD_U_R[view]) / (mL - mR)
    return lambda u: s * u + POST_HEAD_U[view] - s * mL


def coverage(view, V, T):
    """The pixels the triangles (V, T) cover through Leatt's photo camera (1920 x 1920, bool)."""
    from PIL import Image, ImageDraw
    q = G.photo_project(np.array(json.load(open(G.CAMERAS))[view]["x"]), V, 1920, 1920)[0]
    im = Image.new("1", (1920, 1920), 0)
    d = ImageDraw.Draw(im)
    for t in T:
        d.polygon([tuple(q[i]) for i in t], fill=1)
    return np.asarray(im, bool)


def test_round13_strap_carrier_round_the_lens_post():
    """Round 13 item 1: in Leatt's ISO renders (iso55, the Pinata, his SKU; the white ISO) the piece beyond the
    frame's far end is a C in the plates' colour: outer edge at 1703 / 1701 px over rows 840 to 1080, top 800 / 797,
    bottom 1124 / 1125, two windows at the chassis slots' heights (rows 830 to 900 and 1025 to 1092; the white ISO 832
    to 903 and 1027 to 1092), the strap dark behind them and its cut end a column of teal in the lower window (1679 to
    1683 px, rows 1040 to 1076). Main had none: the frame's black end face, 1658 to 1696. Built as part of the
    outriggers on each side, a closed solid, the strap's end threaded behind it (goggle_strap_end): through both
    cameras its outer edge within 3 px, the windows' rows within 8, its top 0 to 8 and its bottom 0 to 16 px short,
    the strap's teal within 3 px and in the lower window only. Round 14: on the plate, its u relative to Leatt's lens
    post (post_relative: the ISO camera puts our post 5 px right of his), its arms, no clear post (Leatt's CAD has
    none; test_round14_post_only_for_the_royal_and_forge); the outer edge is the silhouette of the C and the plate
    beyond it (the grey band 1701 to 1704 px outside the C's dark front face), at Leatt's half-max edge between that
    band (105, 100) and the background (235): 1704.5 and 1703 px, rows 830 to 1090 within 1 (scratch rowprof14.py).
    A vertical edge there leans 4.9 px (2.6 in the white ISO) over these 240 rows through the cameras where his
    stands upright; phr's leans 6.4 (ours 5.4) and the Forge front's -1.7 (ours 4.3): no one tilt of the C fits them
    all, so it stays upright and the 3 px holds the lean."""
    pc, parts = carrier_pieces()
    assert set(pc) == {"carrier", "arm", "arm2", "strap_end", "strap_wall"}, sorted(pc)
    assert all(b == 0 for _, _, b in pc.values()), {k: b for k, (_, _, b) in pc.items()}
    shade = [f for f, m in zip(parts["goggle_strap_end"].F, parts["goggle_strap_end"].M) if m == "goggle_strap_teal"]
    far = [(V, T) for V, T, _ in solids(parts["goggle_outriggers"]) if V[np.unique(T)][:, 0].mean() > 0.06]
    for view, edge, top, bot, wins in (("iso55", 1704.5, 800, 1124, ((830, 900), (1025, 1092))),
                                       ("wiso", 1703, 797, 1125, ((832, 903), (1027, 1092)))):
        u = post_relative(view)
        m = coverage(view, *pc["carrier"][:2])
        sil = np.any([coverage(view, V, T) for V, T in far], axis=0)
        e0 = int(round(edge - u(0.0)))                                   # Leatt's edge in the camera's px
        outer = np.array([np.nonzero(sil[r])[0].max() + 0.5 for r in range(840, 1081)])
        assert np.abs(outer - (edge - u(0.0))).max() <= 3, (view, u(outer.min()), u(outer.max()))
        col = m[:, e0 - 18]
        rows = np.nonzero(col[700:1200])[0] + 700
        assert 0 <= rows.min() - top <= 8 and 0 <= bot - rows.max() <= 16, (view, rows.min(), rows.max())
        holes = np.nonzero(np.diff(np.r_[0, (~col[rows.min():rows.max() + 1]).astype(int), 0]))[0].reshape(-1, 2)
        assert len(holes) == 2 and np.abs(holes + rows.min() - np.array(wins)).max() <= 8, (view, holes + rows.min())
        # the strap's end seen through the windows, its teal (the cut end's rows in the shade) in the lower one
        se = coverage(view, *pc["strap_end"][:2]) & ~m
        for a, b in wins:
            assert se[a + 5:b - 5, e0 - 30:e0 - 6].sum() > 100, (view, a, b)
        V = np.asarray(parts["goggle_strap_end"].V)
        T = np.array([np.asarray(f)[list(k)] for f in shade if V[f, 0].mean() > 0 for k in ((0, 1, 2), (0, 2, 3))])
        teal = coverage(view, V, T) & ~m
        ys, xs = np.nonzero(teal)
        assert abs(u(np.median(xs)) - 1681) <= 3 and wins[1][0] <= ys.min() and ys.max() <= wins[1][1], \
            (view, u(np.median(xs)), ys.min(), ys.max())


def test_round13_carrier_is_flat():
    """Round 13 item 1: the carrier is flat (Leatt's bar reads one tone top to bottom, 43; bowed with our frame's end
    its face tilted down 28 deg below the lower window and mirrored the studio's low light, 250). Its front face is one
    plane within 0.01 mm and every face's vertices are its own (the renders shade every face smooth: shared with the
    window sills, the face's normals bent at the sills' rows into white dashes, 255). Round 14: on the plate (its
    frame car_frame_plate), Leatt's top and bottom (CAR_Z: the frame's corners no longer in its way)."""
    g = G.outrigger_grids()
    F = G.car_frame_plate(g[1][0], 1)
    assert (F["zb"], F["zt"]) == G.CAR_Z
    pc, parts = carrier_pieces()
    V, T, _ = pc["carrier"]
    X = V[np.unique(T)]
    d = (X - F["R0"]) @ F["nrm"]
    front = d > d.max() - 0.0005
    assert np.ptp(d[front]) < 1e-5 and abs(d.max() - (G.CAR_OFF + G.CAR_T)) < 1e-6
    P = parts["goggle_outriggers"]
    PV = np.asarray(P.V)
    slab = lambda f: (PV[f, 0] > 0).all() and (np.abs((PV[f] - F["R0"]) @ F["nrm"] - G.CAR_OFF   # noqa: E731
                                                       - G.CAR_T / 2) < G.CAR_T / 2 + 1e-6).all()
    own = set(map(tuple, np.round(X / 1e-7).astype(np.int64)))                  # the C's, not the plate's or arms'
    mine = lambda f: all(tuple(k) in own for k in np.round(PV[f] / 1e-7).astype(np.int64))  # noqa: E731
    car = [f for f, m in zip(P.F, P.M) if m in ("goggle_outrigger", "goggle_slot") and slab(f) and mine(f)]
    idx = np.concatenate([np.asarray(f) for f in car])
    assert len(car) > 100 and len(np.unique(idx)) == len(idx)    # no vertex shared between two faces


# ---------------------------------------------------------------- round 14: the C on the plate (decision 60)
def test_round14_carrier_rides_on_the_plate():
    """Round 14 item 1: one C on the plate, the plate turned its own way in each photo (CAR_TURNS), meets Leatt's C in
    the four front views that see it: its front face's inner and outer edges, the windows' inner edge, the
    silhouette beyond it (the C or the plate at mid height) and, in phr and the Forge front, the clear post where it
    passes the C's outer corner and its tip, each relative to his lens post (post_relative); and the NEAR plate seen
    from outside in iso55 and phr (one near turn, CAR_NEAR_TURN): its back edge (830, 930.5 px at mid height) and its
    front edge, the C's outer corner (909, 986), relative to his right lens post (the cameras' landmark): within 4 px
    (the joint fit's largest residual 3.6, with the near C kept out of the frame: scratch fitc14n4.py; the cameras'
    landmark rms 4.4 to 4.5). Main's C on the frame's
    end (scratch mainres14.py): iso55 2 to 8 px off, the white ISO 2 to 8, phr 23 to 51, the Forge front 3 to 47;
    the far fit alone with round 12's hinge (this round's first build) put the near plate's front edge 20 px (iso55)
    and 11 px (phr) behind Leatt's. With one turn for all four photos (iso55's) phr's C stands 5 px or more off: the
    turn is each photo's own."""
    obs = {"iso55": dict(E1=1658.5, Win=1674, E2=1699.5, sil=1704.5),
           "wiso": dict(E1=1656.5, Win=1673, E2=1698, sil=1702.5),
           "phr": dict(E1=1630, Win=1639, E2=1657.5, sil=1675, pb=1665, pt=1700),
           "frg": dict(E1=1660.5, Win=1673, E2=1692.5, sil=1707.5, pb=1702, pt=1735)}
    cams = json.load(open(G.CAMERAS))

    def worst(turns):
        out = {}
        for view, o in obs.items():
            Go = G.outrigger_grids(dict(G.GP, or_free_turn={1: turns[view], -1: G.CAR_NEAR_TURN}))[1][0]
            F = G.car_frame_plate(Go, 1, post=True)
            z = F["zc"]
            off = float((F["E2"] - F["H"]) @ F["n"])               # the C's outer corner out from the plate's face
            pb, pn, (ln, _, _) = F["post"]
            pts = dict(E1=np.r_[F["E1"], z], Win=np.r_[F["E2"] - F["c"][:2] * G.CAR_PLATE_WIN[1], z],
                       E2=np.r_[F["E2"], z], pb=pb + pn * off, pt=pb + pn * ln)
            u = post_relative(view)
            pr = lambda X: u(G.photo_project(cams[view]["x"], np.atleast_2d(X), 1920, 1920)[0][:, 0])  # noqa: E731
            got = {k: pr(X)[0] for k, X in pts.items()}
            got["sil"] = max(got["E2"], pr(Go[:, Go.shape[1] // 2]).max())
            out[view] = {k: round(got[k] - v, 1) for k, v in o.items()}
        lm = G.photo_landmarks()
        for view, ph_r, o in (("iso55", 1076.0, dict(back=830.0, front=909.0)),
                              ("phr", 1104.0, dict(back=930.5, front=986.0))):
            Gn = G.outrigger_grids(dict(G.GP, or_free_turn={1: turns[view], -1: G.CAR_NEAR_TURN}))[-1][0]
            F = G.car_frame_plate(Gn, -1)
            m = np.array([-1.0, 1.0, 1.0])
            pr = lambda X: G.photo_project(cams[view]["x"], np.atleast_2d(X), 1920, 1920)[0][:, 0]  # noqa: E731
            sh = ph_r - pr(lm["POST_R"])[0]
            got = dict(back=pr(Gn[-1, Gn.shape[1] // 2])[0], front=pr(np.r_[F["E2"], F["zc"]] * m)[0])
            out[view + "_near"] = {k: round(got[k] + sh - v, 1) for k, v in o.items()}
        return out
    res = worst(G.CAR_TURNS)
    assert max(abs(r) for d in res.values() for r in d.values()) <= 4.0, res
    one = worst({v: G.CAR_TURNS["iso55"] for v in obs})
    assert max(abs(r) for r in one["phr"].values()) > 5.0, one["phr"]


def test_round14_outrigger_front_open_but_its_arms():
    """Round 14 item 1: between the hinge and the C the outrigger is open but for an arm at its top and bottom (phr:
    background between them at rows 837 to 867 and 1060 to 1087, the strap at mid height; the Forge front the same;
    phyb: the arms from behind). Main's printed plate ran from the hinge, its LEATT where phr shows the C. Sampled
    over its surface (0.5 mm), nothing of the far outrigger lies 5 to 15 mm along it from the hinge between the arms'
    heights, the arms are there (CAR_ARM tall at the C's top and bottom), and the plate itself starts at the C's outer
    corner (15.5 mm: round 14's joint fit, the near plate's front edge)."""
    parts = {P.name: P for P in G.free_parts()}
    box = G.outrigger_frames()[1][0]
    front, back = box[[0, 1]].mean(0), box[[2, 3]].mean(0)
    t = (back - front)[:2] / np.linalg.norm((back - front)[:2])
    hinge = back[:2] - t * G.OR_HINGE_LEN
    zb, zt = G.CAR_Z
    P = np.vstack([surface_samples(V, T, 0.0005) for V, T, _ in solids(parts["goggle_outriggers"])
                   if V[np.unique(T)][:, 0].mean() > 0.06])
    a = (P[:, :2] - hinge) @ t
    run = (a > 0.005) & (a < 0.015)
    mid = (P[:, 2] > zb + G.CAR_ARM + 0.0005) & (P[:, 2] < zt - G.CAR_ARM - 0.0005)
    assert not (run & mid).any(), (int((run & mid).sum()), np.round(P[run & mid][:3] * 1000, 1))
    assert (run & (P[:, 2] < zb + G.CAR_ARM)).sum() > 50 and (run & (P[:, 2] > zt - G.CAR_ARM)).sum() > 50
    assert abs(float((front[:2] - hinge) @ t) - G.OR_PLATE_FRONT) < 1e-6 and 0.0150 < G.OR_PLATE_FRONT < 0.0160


def test_round14_post_only_for_the_royal_and_forge():
    """Round 14 item 1: the clear post on the plate (phr: base 2.7 mm, head 4.5 mm, standing out square to the plate
    to 1700 px; the Forge front to 1735) where photos of the real goggle show it, the Royal's and the Forge's: built
    on request (free_parts(post=True); goggle.py --free ... post). Leatt's CAD of his SKU (iso55) and the white ISO
    have none, nor his Pinata kit photos or the 2022 back photo (phyb), so his goggle, free and worn, has none. Main's
    stood on the C's edge in every view, 47 px out beyond the far end in iso55 (01f)."""
    assert "goggle_post_clear" not in parts_by_name(G.free_parts())["goggle_outriggers"].M
    pc, parts = carrier_pieces(post=True)
    assert "post" in pc and pc["post"][2] == 0
    X = pc["post"][0][np.unique(pc["post"][1])]
    ln, r0, r1 = G.CAR_POST_PLATE
    assert 1.9 * r1 < np.ptp(X[:, 2]) <= 2 * r1 + 1e-6 and 0.009 < ln < 0.010 and abs(2 * r0 - 0.0027) < 1e-4


def test_round14_c_stops_on_the_frame():
    """Round 14 item 1: the C on the plate swings with it, so a plate can turn in only until its C's inner bar meets
    the frame's side (the back rim, z 13 to 23 mm). The first joint fit put the near plate at 8.7 deg with its C 2.5
    mm inside the frame (bounded at 15.5 deg, 1.2 mm); fitted with the C kept out (scratch fitc14n4.py), the near
    plate rests on that stop, 13.7 deg. Sampled over its surface (0.4 mm), the near C at CAR_STOP_TURN lies outside
    the frame and the face foam, 0.7 deg further in it does not; the free near plate is at the stop and the worn
    plates never inside it."""
    for a, clear in ((G.CAR_STOP_TURN, True), (G.CAR_STOP_TURN - 0.7, False)):
        parts = parts_by_name(G.free_parts(dict(G.GP, or_free_turn={1: G.CAR_TURNS["iso55"], -1: a})))
        car = [(V, T) for V, T, _ in solids(parts["goggle_outriggers"]) if len(V[np.unique(T)]) > 100
               and V[np.unique(T)][:, 0].mean() < -0.06 and len(V[np.unique(T)]) != 2 * len(G.or_u()) * G.OR_NV]
        P = np.vstack([surface_samples(V, T, 0.0004) for V, T in car])
        hit = np.zeros(len(P), bool)
        for name in ("goggle_frame", "goggle_foam"):
            for V, T, _ in solids(parts[name]):
                U = V[np.unique(T)]
                m = np.all((P > U.min(0) - 1e-5) & (P < U.max(0) + 1e-5), axis=1)
                if m.any():
                    hit[np.nonzero(m)[0][inside_solid(P[m], V, T)]] = True
        assert (not hit.any()) if clear else hit.sum() > 5, (a, int(hit.sum()))
    assert G.OR_FREE_TURN[-1] == G.CAR_NEAR_TURN == G.CAR_STOP_TURN
    Vo, Fo, prof = H.shell_outer()
    G.outrigger_grids(mount=G.shell_mount(prof))
    assert all(t >= G.CAR_STOP_TURN for v in G.WORN_TURN.values() for t in v), G.WORN_TURN


def parts_by_name(parts):
    return {P.name: P for P in parts}


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
    the lower band's LEATT, bare tear-off posts (no tear-offs, decision 7), nose guard, nose ribs, foam, strap, and
    (round 13) the strap's ends behind the carriers."""
    import colorsys
    r, g, b = G.MATERIALS["goggle_frame"]["rgb"]
    h = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360
    assert 330 < h < 345 and r > 120 and g < 10
    for name in ("goggle_frame", "goggle_fins", "goggle_logo", "goggle_lens", "goggle_posts", "goggle_outriggers",
                 "goggle_noseguard", "goggle_noseribs", "goggle_foam", "goggle_strap", "goggle_strap_end"):
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
    # round 11: in mm, not texels (0.157 mm along, 0.117 across: round 9's print stretched the mark 1.34 times along,
    # and in texels that read as the right aspect)
    import goggle_strap_art as SA
    mm_x, mm_y = SA.STRAP_LEN_UV * 1000.0 / w, SA.W_MM / im.shape[0]
    for half in (white[:, :w // 2], white[:, w // 2:]):
        ys, xs = np.nonzero(half)
        assert abs(np.ptp(xs) * mm_x / (np.ptp(ys) * mm_y) - a) < 0.3, np.ptp(xs) * mm_x / (np.ptp(ys) * mm_y)
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
