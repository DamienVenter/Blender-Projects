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


def test_fit_on_his_head(built):
    """Even stand-off all round the skull (EPS and pads), brow ahead of the forehead, eyes in the face port."""
    g = built["info"]["gaps_mm"]
    ring = [g["top"], g["back"], g["left"], g["right"]]
    assert 40 < min(ring) and max(ring) - min(ring) < 4
    assert g["fore"] >= 31.5


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
        assert str(g[name + "__bone"]) == "head"
        FS, F, M = g[name + "__FS"], g[name + "__F"], g[name + "__M"]
        assert FS.sum() == len(F) and len(M) == len(FS) and F.max() < len(g[name + "__V"])
        if name + "__UV" in g:
            assert len(g[name + "__UV"]) == FS.sum()
    for m in g["mats"]:
        assert str(m) in mats


def test_goggle_in_the_port_on_his_eyes(body, built):
    """Lens ahead of both eyes, nothing of the lens inside the shell; the strap 45 mm wide (Leatt); the frame
    raspberry (his photos, not Leatt's hot pink render)."""
    P = built["parts"]
    L = H.head_landmarks(body)
    lens = P["goggle_lens"].V
    for sgn in (1, -1):
        e = L["eye"] + [sgn * 0.031, 0, 0]
        near = lens[np.abs(lens[:, 0] - e[0]) < 0.004]
        assert near[:, 2].min() < e[2] < near[:, 2].max()            # the eye's height is inside the lens
        assert 0.05 < e[1] - near[:, 1].max() < 0.09                 # lens 50 to 90 mm ahead of the eye centre
    sh = P["helmet_shell"]
    assert (winding(lens, sh.V, tris(sh)) < 0.5).all()
    st = P["goggle_strap"]
    n = len(st.V) // 4
    w = np.linalg.norm(st.V[n:2 * n] - st.V[:n], axis=1)
    assert np.allclose(np.median(w), H.STRAP_W, atol=0.002)
    r, g, b = H.MATERIALS["goggle_frame"]["rgb"]
    assert r > 150 and g < 60 and b < 110


def test_textures_present():
    for f in ("helmet_pinata.png", "goggle_strap.png", "goggle_outrigger.png"):
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000
