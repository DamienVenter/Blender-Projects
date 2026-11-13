"""Tests of the sticker kit pipeline (kit_mirror.py, kit_canvas.py) and of Damien's kit data (textures/damien-v1).

python3 -m pytest -q test_kit.py
"""
import json
import os

import numpy as np
import pytest
from PIL import Image

import kit_canvas
import kit_mirror

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "..", "..", "textures", "damien-v1")


def panel(W=400, H=200):
    """A black sticker on a white page."""
    a = np.full((H, W, 3), 255, np.uint8)
    a[40:160, 40:360] = (14, 14, 16)
    return a


def ell(a, x, y, s=30, t=6, colour=(250, 250, 250)):
    """An 'L' (a glyph that is not its own mirror image): stem down from (x, y), foot to the right."""
    a[y:y + s, x:x + t] = colour
    a[y + s - t:y + s, x:x + s * 2 // 3] = colour


def blob_box(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max(), ys.max()


def white(a):
    return kit_mirror.INKS["white"](a)


def test_level_word_comes_back_unmirrored_at_the_mirrored_place():
    a = panel()
    ell(a, 80, 70)
    out, st = kit_mirror.mirror_art(a, [{"ink": ["white"], "angle": 0}])
    x0, y0, x1, y1 = blob_box(white(out) & (np.arange(out.shape[1]) > 0)[None, :] & kit_mirror.part_region(out))
    # mirrored place: the L's centre moves from the left end to the right end of the sticker
    assert x0 > 260 and y0 >= 69 and y1 <= 101
    # unmirrored: the stem (6 px wide, full height) is still on the glyph's LEFT, the foot runs to the right
    stem = white(out)[y0:y1 + 1, x0:x0 + 6].mean()
    right_top = white(out)[y0:y0 + 10, x1 - 6:x1 + 1].mean()
    assert stem > 0.9 and right_top < 0.2
    # and none of the mirrored copy is left behind
    assert not white(out)[40:160, 40:200].any()


def test_slanted_word_runs_along_the_mirrored_part():
    """A word slanting down to the right on the left side slants up to the right on the right side, reading the
    right way: its writing direction becomes the mirror image of the original's."""
    a = np.full((300, 600, 3), 255, np.uint8)
    yy, xx = np.mgrid[0:300, 0:600]
    band = np.abs((yy - 80) - 0.27 * (xx - 50)) < 45                # a slanted black strip, like the swingarm
    a[band & (xx > 40) & (xx < 560)] = (14, 14, 16)
    word = (np.abs((yy - 120) - 0.27 * (xx - 200)) < 8) & (xx > 200) & (xx < 380)
    a[word] = (250, 250, 250)
    out, st = kit_mirror.mirror_art(a, [{"ink": ["white"], "on_black": True}])
    assert abs(st[0]["direction_deg"] - np.degrees(np.arctan(0.27))) < 2
    m = white(out) & kit_mirror.part_region(out)
    ys, xs = np.nonzero(m)
    slope = np.polyfit(xs, ys, 1)[0]
    assert abs(slope + 0.27) < 0.03                                  # up to the right, as the mirrored strip
    assert abs(xs.mean() - (599 - 290)) < 6                          # at the mirrored place


def test_bare_metal_and_holes_are_not_lettering():
    a = panel()
    a[40:160, 300:360] = (205, 206, 208)                             # bare aluminium end with a white slot in it
    a[90:110, 320:340] = (255, 255, 255)
    ell(a, 80, 70)
    m = kit_mirror.layer_mask(a, kit_mirror.part_region(a), {"ink": ["white"], "on_black": True})
    x0, y0, x1, y1 = blob_box(m)
    assert x1 < 130                                                 # only the L
    out, _ = kit_mirror.mirror_art(a, [{"ink": ["white"], "on_black": True}])
    # the slot stays where the flip puts it (a hole is a shape, not a word): its mirror image is in the metal end
    assert white(out)[95:105, 400 - 1 - 335:400 - 1 - 325].all()


def test_solid_logo_plate_moves_with_its_letters():
    a = panel()
    a[60:100, 60:180] = (250, 220, 20)                               # yellow plate
    a[70:90, 70:76] = (10, 10, 10)                                   # a black letter on it, left end
    out, _ = kit_mirror.mirror_art(a, [{"ink": ["yellow"], "solid": True, "angle": 0}])
    W = a.shape[1]
    # the plate sits at the mirrored place and its letter is still at the plate's LEFT end (unmirrored)
    plate = kit_mirror.INKS["yellow"](out)
    x0, y0, x1, y1 = blob_box(plate)
    assert abs(x0 - (W - 1 - 179)) <= 2 and abs(x1 - (W - 1 - 60)) <= 2
    assert out[80, x0 + 12].max() < 60                              # the letter, 10 to 16 px in from the left
    assert out[80, x1 - 12].min() > 15 and out[80, x1 - 12][0] > 180


def test_glyph_filter_drops_pinstripes():
    a = panel()
    a[50, 45:355] = (220, 20, 20)                                   # a long thin red pinstripe
    a[51, 45:355] = (220, 20, 20)
    for k in range(100):                                             # and a diagonal one
        a[45 + k, 200 + k:203 + k] = (220, 20, 20)
    a[100:130, 100:130] = (220, 20, 20)                              # a compact red logo
    m = kit_mirror.layer_mask(a, kit_mirror.part_region(a), {"ink": ["red"], "glyphs": True})
    assert m[100:130, 100:130].all() and not m[50].any() and not m[45:145, 200:305].any()


def test_sticker_band_follows_the_sticker_not_the_metal():
    art = np.full((100, 300, 3), 255, np.uint8)
    art[20:80, 10:290] = (200, 201, 203)                             # bare aluminium arm
    art[30:70, 60:240] = (14, 14, 16)                                # the black wrap on it
    art[45:55, 100:120] = (250, 250, 250)                            # white lettering on the wrap
    H, W = 100, 300
    c, r = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    ax, ay = c.astype(int), r.astype(int)
    inr = np.ones((H, W), bool)
    st = kit_canvas.sticker(art, ax, ay, inr)
    assert st[50, 110] and st[40, 150]                               # lettering and black: sticker
    assert not st[25, 150] and not st[50, 30] and not st[5, 5]       # metal and page: not
    x = c / 1000.0
    z = 1.0 - r / 1000.0
    b = kit_canvas.band(st, x, z)
    xs = np.array([q[0] for q in b])
    assert xs.min() > 0.058 and xs.max() < 0.242
    mid = b[len(b) // 2]
    assert abs(mid[1] - (1.0 - 0.0695)) < 0.003 and abs(mid[2] - (1.0 - 0.0305)) < 0.003


# ---- Damien's kit data -------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def kit():
    return json.load(open(os.path.join(KIT, "kit.json")))


def test_every_panel_has_its_art_at_the_crop_aspect(kit):
    for p in kit["panels"]:
        art = Image.open(os.path.join(KIT, p["art"]))
        assert p.get("source"), p["art"]
        if "crop" not in p and "mirror_of" not in p:                # the bar pad's face: no template crop
            continue
        u0, v0, u1, v1 = p["mirror_of"] if "mirror_of" in p else p["crop"]
        pl, pt = p.get("pad", [0, 0])
        want = ((u1 - u0) + 2 * pl) / ((v1 - v0) + 2 * pt)
        assert abs(art.width / art.height / want - 1) < 0.03, p["art"]
        assert p.get("source"), p["art"]


def test_both_sides_of_every_side_panel(kit):
    side = {(p["side"], p["part"]) for p in kit["panels"] if p["side"] in ("left", "right")}
    for s, part in side:
        assert ("left" if s == "right" else "right", part) in side, part
    for m in kit["mirror"]:
        assert os.path.exists(os.path.join(KIT, m["right"])), m["right"]


def test_textures_match_their_maps():
    maps = json.load(open(os.path.join(KIT, "maps.json")))
    s, t = maps["side"], maps["top"]
    for f in ("side_L.png", "side_R.png"):
        assert Image.open(os.path.join(KIT, f)).size == (round((s["x1"] - s["x0"]) * s["ppm"]),
                                                          round((s["z1"] - s["z0"]) * s["ppm"]))
    assert Image.open(os.path.join(KIT, "top.png")).size == (round((t["y1"] - t["y0"]) * t["ppm"]),
                                                              round((t["x1"] - t["x0"]) * t["ppm"]))
    for k in ("fender", "front_fender"):                             # painted from the top view (build_top)
        m = maps[k]
        assert Image.open(os.path.join(KIT, k + ".png")).size == (round((m["x1"] - m["x0"]) * m["ppm"]),
                                                                  round((m["y1"] - m["y0"]) * m["ppm"]))
    for f in ("plate.png", "seat.png"):
        assert os.path.exists(os.path.join(KIT, f))


def test_swingarm_wrap_band_is_on_the_arm():
    b = json.load(open(os.path.join(KIT, "bands.json")))["swingarm"]
    for side in ("left", "right"):
        xs = np.array([q[0] for q in b[side]])
        lo = np.array([q[1] for q in b[side]])
        hi = np.array([q[2] for q in b[side]])
        # from just ahead of the axle block to just behind the pivot casting, on the arm's height (axle line z 0)
        assert 0.04 < xs.min() < 0.08 and 0.48 < xs.max() < 0.55
        assert (hi > lo).all() and lo.min() > 0.30 and hi.max() < 0.50
        # the arm rises toward the pivot: so does the wrap
        assert np.polyfit(xs, (lo + hi) / 2, 1)[0] > 0.1


def test_barpad_lettering_on_the_faces_emblem_on_top():
    a = np.asarray(Image.open(os.path.join(KIT, "barpad.png")).convert("RGB")).astype(int)
    assert a.shape[:2] == (720, 840)
    B = 240
    cream = (a[..., 0] > 180) & (a[..., 1] > 160) & (a[..., 2] > 100)
    faces, top, caps = cream[2 * B:], cream[B:2 * B], cream[:B]
    assert faces.mean() > 0.15                                       # two RENTHAL lines across the face
    cols = np.nonzero(faces.any(0))[0]
    assert cols.min() < 0.12 * 840 and cols.max() > 0.88 * 840       # over most of the pad's length
    assert 0.01 < top.mean() < faces.mean()                          # the emblem, smaller, on the top
    assert caps.mean() == 0 and (a[:B, :, 0] > 180).mean() > 0.95     # red end caps (his pad is red all over)


# ---- the side panels, drawn by script (kit_sidepanel.py, decision 37) ---------------------------------------------

@pytest.fixture(scope="module")
def sidepanels():
    import kit_sidepanel
    return kit_sidepanel, {s: kit_sidepanel.build(s) for s in ("left", "right")}


def test_side_panel_art_is_the_scripts_output(sidepanels):
    """The committed artwork is exactly what kit_sidepanel.py draws (no hand edits, nothing left over from the
    image model's v1)."""
    _, art = sidepanels
    for side, f in (("left", "sidepanel_L.png"), ("right", "sidepanel_R.png")):
        a = np.asarray(Image.open(os.path.join(KIT, "art", f)).convert("RGB"))
        assert a.shape == art[side].shape == (1536, 2752, 3)
        assert np.array_equal(a, art[side]), side


def test_side_panel_entries_point_at_the_script(kit):
    for p in kit["panels"]:
        if p["part"] == "side_panels":
            assert "kit_sidepanel.py" in p["source"] and p.get("close_slits"), p["side"]


def test_side_panel_words_read_normally_on_both_sides(sidepanels):
    """Every word and logo is placed without a reflection on both sides (positive determinant), the right one at
    the mirrored place; and the right art there is the word drawn afresh, not the left art's pixels flipped."""
    K, art = sidepanels
    P = K.placements()
    rings = {"number": K.number_rings(), "psalm": K.text_rings(K.PSALM["text"])[0], "leatt": K.leatt_rings(),
             "name": K.name_rings()}
    for k, M in P.items():
        R = K.mirror_place(M, rings[k])
        assert np.linalg.det(M[:, :2]) > 0 and np.linalg.det(R[:, :2]) > 0, k
        allp = np.vstack(rings[k])
        c = (allp.min(0) + allp.max(0)) / 2                          # the source's middle lands at the mirrored place
        left, right = M[:, :2] @ c + M[:, 2], R[:, :2] @ c + R[:, 2]
        assert abs(right[0] - (K.W - left[0])) < 0.5 and abs(right[1] - left[1]) < 0.5, k
    ps = K.fill(rings["psalm"], K.mirror_place(P["psalm"], rings["psalm"])) > 0.5
    ys, xs = np.nonzero(ps)
    box = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    wr = art["right"].min(-1)[box] > 200
    wl_flipped = art["left"][:, ::-1].min(-1)[box] > 200
    iou = lambda a, b: (a & b).sum() / max((a | b).sum(), 1)
    assert iou(wr, ps[box]) > 0.9                                    # the right art shows PSALM 91 as drawn
    assert iou(wr, wl_flipped) < 0.6                                 # ... and not the left one mirrored


def test_side_panel_number_glyphs_are_whole(sidepanels):
    """The 114 has no crack lines: closing its white by 2 px adds next to nothing (the image model's v1 had dark
    ticks and slits through the 1s), and it is three digits apart from the clipping at the intake."""
    from scipy import ndimage as ndi
    K, art = sidepanels
    P = K.placements()
    num = K.fill(K.number_rings(), P["number"]) > 0.5
    words = ndi.binary_dilation(K.fill(K.text_rings(K.PSALM["text"])[0], P["psalm"]) > 0.05, iterations=3)
    ys, xs = np.nonzero(num)
    box = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    w = (art["left"].min(-1) > 200)[box] & num[box] & ~words[box]
    closed = ndi.binary_closing(w, iterations=2) & num[box]
    assert (closed & ~w).sum() < 0.002 * w.sum()
    lab, n = ndi.label(w)
    sizes = np.sort(ndi.sum(w, lab, range(1, n + 1)))[::-1]
    assert len(sizes) >= 3 and sizes[2] > 0.1 * sizes[0] and sizes[3:].sum() < 0.01 * w.sum()


def red_slits(a, box):
    """Plain plastic red texels (kit_canvas.RED) inside box in thin strokes (at most 4 texels across) cut off
    from the red round the panels and enclosing nothing: slits where the artwork failed to reach. Not counted: a
    ring (the red rim round the intake encloses the intake) and a solid patch (a bolt head in front)."""
    from scipy import ndimage as ndi
    red = (a == kit_canvas.RED).all(-1)[box]
    lab, n = ndi.label(red)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    big = np.argmax(np.bincount(lab.ravel())[1:]) + 1 if n else 0
    out = 0
    for i, s in enumerate(ndi.find_objects(lab), 1):
        if i in edge or i == big:
            continue
        m = lab[s] == i
        if ndi.binary_fill_holes(m).sum() == m.sum() and not ndi.binary_erosion(m, iterations=2).any():
            out += int(m.sum())
    return out


def test_side_textures_have_no_red_slits_through_the_side_panels():
    maps = json.load(open(os.path.join(KIT, "maps.json")))["side"]
    ppm = maps["ppm"]
    for f, side in (("side_L.png", "left"), ("side_R.png", "right")):
        a = np.asarray(Image.open(os.path.join(KIT, f)).convert("RGB"))
        # the side panels: x 0.02 .. 0.82 m, z 0.58 .. 1.03 m (template crop of kit.json)
        cols = sorted(round((maps["x1"] - x if side == "left" else x - maps["x0"]) * ppm) for x in (0.02, 0.82))
        rows = [round((maps["z1"] - z) * ppm) for z in (1.03, 0.58)]
        assert red_slits(a, (slice(*rows), slice(*cols))) == 0, f
