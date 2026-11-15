"""Checks of the scene look (decision 54), shared by the rider's and the bike's test suites (test_scene_look.py in
each): Blender renders a swatch chart as scene_look.display() says it should, the module's own numbers hold, and the
scripts set their look through scene_look.apply() instead of their own view settings."""
import ast
import os
import shutil
import subprocess
import tempfile

import numpy as np

import scene_look as S

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_LOOK = "AgX - Punchy"            # decision 46's look, set by hand in every script before the module


def swatch_chart():
    """Scene-linear test colours, 12 x 32: a grey ramp 0.001 .. 30 (2^-10 .. 2^4.9), the bike's red and the helmet's
    magenta and white as the daylight renders carry them (look_fit pairs: medians of the render's linear values),
    and random colours over five decades, saturated and pale."""
    rng = np.random.default_rng(54)
    a = np.zeros((12, 32, 3))
    a[0] = np.geomspace(1e-3, 30.0, 32)[:, None]
    for j, c in enumerate([(2.18, 0.082, 0.086), (1.08, 0.224, 0.50), (4.12, 4.74, 5.84), (0.29, 0.29, 0.286)]):
        a[1, 8 * j:8 * j + 8] = np.array(c) * np.geomspace(0.25, 4.0, 8)[:, None]
    c = rng.uniform(0.0, 1.0, (10, 32, 3)) ** 3
    a[2:] = np.exp(rng.uniform(np.log(1e-3), np.log(30.0), (10, 32, 1))) * c / np.maximum(c.max(-1, keepdims=True), 1e-6)
    return a.astype(np.float32)


def blender_render(a, kind, ev):
    """The chart through look_apply.py (an emission plane, one sample per pixel: each pixel its texel) with
    scene_look.apply(scene, kind, ev); 8-bit RGB."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as d:
        np.save(os.path.join(d, "in.npy"), a)
        r = subprocess.run(["blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python",
                            os.path.join(HERE, "look_apply.py"), "--", os.path.join(d, "in.npy"),
                            os.path.join(d, "out.png"), kind, str(ev)], capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
        line = [x for x in r.stdout.splitlines() if x.startswith("LOOK_APPLY")]
        return np.asarray(Image.open(os.path.join(d, "out.png")).convert("RGB")).astype(float), line[0]


def check_swatches(kinds=(("daylight", 0.0), ("scene", 1.5), ("studio", -0.9))):
    """Blender's output within one level of display() on every swatch, for each kind."""
    if not shutil.which("blender"):
        import pytest
        pytest.skip("needs Blender (tools/setup_blender.sh)")
    a = swatch_chart()
    for kind, ev in kinds:
        out, line = blender_render(a, kind, ev)
        ref = np.round(S.display(a, kind, ev) * 255.0)
        d = np.abs(out - ref)
        assert d.max() <= 1.0, "%s %s: Blender differs from display() by up to %d levels (%s)" % (kind, ev, d.max(), line)
        assert ("compositor gains" in line) == (kind != "studio"), line


def check_numbers():
    """The look's own claims: T(XMAX) = 1 and T rising; mid grey 0.18 at 69 under "scene" (decision 46's level);
    the hue kept (the gained channels' ratios survive the tone curve); white balance and exposure in the gains."""
    u = np.geomspace(1e-4, S.XMAX, 200)
    t = S.tone(u)
    assert abs(float(S.tone(S.XMAX)) - 1.0) < 1e-12 and np.all(np.diff(t) > 0)
    assert round(float(S.display(np.full(3, 0.18), "scene")[1] * 255)) == 69
    x = np.array([2.18, 0.082, 0.086])                     # the bike's red, render linear
    g = np.asarray(S.GAINS) * x
    y = S.eotf(S.display(x, "daylight"))
    assert np.allclose(y / y[0], g / g[0], rtol=0.02), (y / y[0], g / g[0])
    assert np.allclose(np.log2(S.GAINS), S.EV + np.asarray(S.WB))
    assert S.gains_of("scene") == (2.0 ** (S.EV + S.EV_SCENE),) * 3


def _calls(node):
    """(kind, has ev) of every scene_look.apply(scene, "kind", ...) call under an AST node."""
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "apply" and \
                isinstance(n.func.value, ast.Name) and n.func.value.id == "scene_look":
            k = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else None
            out.append(k)
    return out


def check_script(path, functions):
    """A script imports scene_look and, in each named function (None: the module's top level), sets its look with
    scene_look.apply for each kind listed, and no longer names decision 46's look itself."""
    src = open(path).read()
    tree = ast.parse(src)
    assert any(isinstance(n, ast.Import) and any(a.name == "scene_look" for a in n.names) for n in ast.walk(tree)), \
        "%s does not import scene_look" % os.path.basename(path)
    for name, kinds in functions.items():
        node = tree if name is None else next(
            (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)
        assert node is not None, "%s has no function %s" % (os.path.basename(path), name)
        calls = _calls(node)
        for k in kinds:
            assert k in calls, "%s.%s does not call scene_look.apply(scene, %r)" % (os.path.basename(path), name, k)
        consts = [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert OLD_LOOK not in consts, "%s.%s still sets %s itself" % (os.path.basename(path), name, OLD_LOOK)
