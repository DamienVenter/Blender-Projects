"""The gear against his photos (decision 59): his phone's lift of the darks in the daylight look
(scene_look.DARK_LIFT, PHOTO_TINT; research/scene-look.md "The darks"), its fit (look_fit.py darks) and the gear's
measurement (look_fit.py gear: the colour gates, the regions, the albedo and grey-layer fit)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import look_fit as F  # noqa: E402
import scene_look as S  # noqa: E402

RED = [2.18, 0.082, 0.086]            # the bike's red, render linear (scene_look_checks.swatch_chart)
WHITE = [4.12, 4.74, 5.84]            # the helmet's white shell, render linear


def test_the_daylight_look_lifts_its_darks_and_leaves_the_rest(monkeypatch):
    """A black reads DARK_LIFT (about 17 levels, his matte darks' lift over ours) in the daylight look only; the
    white shell (lit and in shade) and the bike's red in sun move under a level (the red in deep shade, a quarter
    of that light, gains 8 levels in G and B: a dark colour's weak channels lift with the darks)."""
    z = np.zeros(3)
    assert 10 < S.DARK_LIFT * 255 < 25
    assert np.allclose(S.display(z, "daylight") * 255, S.DARK_LIFT * 255)
    assert S.display(z, "scene").max() == 0 and S.display(z, "studio").max() == 0
    xs = [np.asarray(RED), np.asarray(WHITE), np.asarray(WHITE) * 0.5]
    now = [S.display(x, "daylight") for x in xs]
    monkeypatch.setattr(S, "DARK_LIFT", 0.0)
    before = [S.display(x, "daylight") for x in xs]
    for a, b in zip(now, before):
        assert np.all(np.abs(a - b) * 255 < 1.0), (a * 255, b * 255)


def test_his_07_has_its_own_tint_of_its_darks():
    """07's darks read blue whatever they are (the tyres' rubber and the helmet's black print, neutral in Leatt's
    studio): its tint, for views of that photo only; 08 and 09 the lift alone."""
    assert set(S.PHOTO_TINT) <= set(S.PHOTO_EV)
    assert S.photo_tint("p07") == S.photo_tint("cam07") == S.PHOTO_TINT["07"]
    assert S.photo_tint("p08") is None and S.photo_tint("p09") is None and S.photo_tint("front") is None
    d = S.display(np.zeros(3), "daylight", S.PHOTO_EV["07"], S.photo_tint("cam07")) * 255
    assert d[2] - d[0] > 15, d
    assert S.dark_lift("scene", S.PHOTO_TINT["07"]) is None


def test_the_darks_fit_finds_a_known_lift_and_tint(monkeypatch):
    """look_fit.dark_fit on neutral darks made through a known lift and 07 tint gives them back."""
    rng = np.random.default_rng(59)
    truth = np.array([0.05, -0.01, 0.01, 0.08])
    monkeypatch.setattr(S, "DARK_LIFT", 0.0)
    sets = {}
    for v, c in F.DARKS_FIT + (("cam07", "glove"),):
        lin = rng.uniform(5e-4, 0.03, (400, 1)) * np.ones(3)
        d = S.display(lin, "daylight", S.photo_ev(v))
        o = truth[0] + (truth[1:] if S.photo_tint(v) is not None else 0.0)
        sets[(v, c)] = (S.lift(d, o), lin)
    out = F.dark_fit(sets)
    assert abs(out["lift"] - truth[0]) < 0.003, out["lift"]
    assert np.allclose(out["tint07"], truth[1:], atol=0.004), out["tint07"]
    assert out["mean_fitted_fit"] < 0.5 and out["mean_held_fit"] < 0.5


def test_the_gear_gates_pick_the_kits_colours():
    """Each gate passes its own colour of the kit (his photos' medians) and none of the others."""
    px = np.asarray([[245, 68, 169], [111, 168, 59], [57, 112, 114], [28, 37, 49], [236, 239, 242], [128, 128, 128]],
                    float) / 255.0
    for i, kind in enumerate(("magenta", "lime", "teal", "dark", "white")):
        want = [j == i for j in range(len(px))]
        assert F.gear_gate(px, kind).tolist() == want, kind


def test_a_photos_tint_does_not_move_the_renders_pixels_out_of_the_gate(monkeypatch):
    """Under a strong blue tint (round 1's first, fitted on the black print alone, was 0.13 in B) the render's
    deepest darks are too saturated for the dark gate; gear_region gates the render without the photo's tint, so
    they stay in (the tint is the photo's, not the material's)."""
    monkeypatch.setitem(S.PHOTO_TINT, "07", (0.0, 0.02, 0.15))
    cls = np.full((60, 60), "none", dtype=object)
    cls[20:40, 20:40] = "jersey_dark"
    lin = np.full((60, 60, 3), 3e-4)
    photo = np.tile(np.asarray([28, 37, 49], float) / 255.0, (60, 60, 1))
    d = dict(cls=cls, lin=lin, photo=photo, light=lin * 50.0, alb=np.full((60, 60, 3), 0.012))
    tinted = S.display(lin[cls == "jersey_dark"], "daylight", S.PHOTO_EV["07"], S.photo_tint("cam07"))
    assert not F.gear_gate(tinted, "dark").any()
    ph, lin_c, light, alb = F.gear_region(d, "cam07", "jersey_dark")
    assert len(lin_c) == 400 and len(ph) > 2000


def test_the_gear_fit_finds_a_known_albedo_at_its_grey_layer():
    """gear_fit on classes made with a known albedo and scale k of the grey layer (sheen, coat) gives the albedo back
    at that k: a dark with a large grey layer, a colour with a small one. And the body's numbers alone cannot tell
    k: the dark made at k 0.6 fits as closely at k 2 with a smaller albedo (k is the studio photos' to say)."""
    rng = np.random.default_rng(7)
    n = 3000
    look = lambda x: S.display(x, "daylight")                                 # noqa: E731
    for a_true, k_true, g, a_now in (([0.02, 0.025, 0.03], 0.5, 0.03, 0.012), ([0.30, 0.04, 0.15], 1.0, 0.02, 0.2)):
        light = rng.uniform(0.2, 3.0, (n, 1)) * np.ones(3)
        alb = np.full((n, 3), a_now)
        G = rng.uniform(0.0, g, (n, 1)) * np.ones(3)
        photo = look(light * np.asarray(a_true) + k_true * G)
        r = F.gear_fit(light * alb + G, light, alb, photo[F.body(photo)], look)
        assert np.allclose(r["k"][str(k_true)]["albedo"], a_true, rtol=0.05), r
        if k_true == 0.5:
            assert np.abs(r["k"]["2.0"]["resid"][:3]).max() < 1.5, r["k"]["2.0"]
            assert np.all(np.asarray(r["k"]["2.0"]["albedo"]) < 0.8 * np.asarray(a_true)), r["k"]["2.0"]


def test_the_boots_white_is_his_scuffed_white():
    """His 08 sees the boot and the helmet's white shell both in sun: the boot at 0.93 of the shell (linear, the lit
    quartiles; research/scene-look.md "The boots' white"). boots.WHITE (the shell's paint) and boot_white are that
    on the helmet's white, and the shell's textures carry it (main's 236, 239, 242 was 1.10 of the shell)."""
    import boots
    import helmet_art
    from PIL import Image
    lum = lambda c: float(S.eotf(np.asarray(c, float) / 255.0) @ np.asarray(S.LUMA))          # noqa: E731
    assert 0.90 < lum(boots.WHITE) / lum(helmet_art.WHITE) < 0.96
    assert list(boots.MATERIALS["boot_white"]["rgb"]) == [int(v) for v in boots.WHITE]
    for f in ("boot_out_R.jpg", "boot_out_R_worn.jpg", "boot_back_L.jpg"):
        a = np.asarray(Image.open(os.path.join(boots.TEXDIR, f)).convert("RGB")).reshape(-1, 3).astype(float)
        assert np.all(np.abs(np.median(a[a.mean(1) > 150], 0) - boots.WHITE) <= 3), f
