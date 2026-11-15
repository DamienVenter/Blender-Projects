"""The daylight rig shared by the rider's and the bike's daylight renders (decision 55, scripts/common/day_rig.py):
the scripts take it from the module, his photos' views get the sun's height of his 07, and Blender turns the sky as
the module says."""
import ast
import math
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.join(HERE, "..", "common")
sys.path.insert(0, COMMON)
import day_rig  # noqa: E402


def _calls(node, attr):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr and isinstance(n.func.value, ast.Name) and n.func.value.id == "day_rig"]


@pytest.mark.parametrize("script", ["head_closeups.py", "goggle_views.py"])
def test_the_daylight_scripts_take_their_rig_from_the_module(script):
    tree = ast.parse(open(os.path.join(HERE, script)).read())
    fn = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert _calls(fn["daylight"], "build"), "%s.daylight does not build day_rig's rig" % script
    assert _calls(fn["day_sun"], "aim"), "%s.day_sun does not aim day_rig's sun" % script
    consts = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "ShaderNodeTexSky" not in consts, "%s still makes a sky itself" % script
    day = {n.value for n in ast.walk(fn["daylight"]) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "SUN" not in day, "%s.daylight still makes its own sun lamp" % script


def _assigned(tree):
    return {t.id: n.value for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}


def test_his_photo_views_turn_the_sky_to_his_suns_height():
    """head_closeups gives his three photos' views and cam07 (the bike's camera on photo 07) DAY_ELEV (78 deg, photo
    07's shadow) and the other views None."""
    tree = ast.parse(open(os.path.join(HERE, "head_closeups.py")).read())
    val = _assigned(tree)
    assert ast.literal_eval(val["DAY_ELEV"]) == 78.0
    assert ast.unparse(val["SUN_HEIGHT_VIEWS"]) == "(*HIS_VIEWS, 'cam07')", ast.unparse(val["SUN_HEIGHT_VIEWS"])
    aim = _calls(next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "day_sun"), "aim")[0]
    el = aim.args[4] if len(aim.args) > 4 else None
    assert isinstance(el, ast.IfExp) and ast.unparse(el) == "DAY_ELEV if name in SUN_HEIGHT_VIEWS else None", \
        ast.unparse(aim)


def test_cam07_takes_p07s_sun():
    """cam07 is photo 07 seen by the camera fitted to the bike: p07's sun (decision 55, round 2b), not the views
    without a photo's DAY_SUN_OTHER."""
    sun = ast.literal_eval(_assigned(ast.parse(open(os.path.join(HERE, "head_closeups.py")).read()))["DAY_SUN"])
    assert sun.get("cam07") == sun["p07"] == (90.0, 106.7), sun


def test_goggle_views_photo_views_get_the_suns_height():
    """goggle_views' cameras of his photos (those carrying a "sun") turn the sky to day_rig.SUN_ELEV through
    day_sun, the others keep the GOGGLE frame's up (decision 55, round 2b)."""
    tree = ast.parse(open(os.path.join(HERE, "goggle_views.py")).read())
    fn = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    aim = _calls(fn["day_sun"], "aim")[0]
    assert [ast.unparse(a) for a in aim.args] == ["day", "cam", "*phi_theta", "elevation"], ast.unparse(aim)
    calls = [n for n in ast.walk(fn["main"]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "day_sun"]
    assert len(calls) == 1 and len(calls[0].args) == 4, [ast.unparse(c) for c in calls]
    assert ast.unparse(calls[0].args[3]) == "day_rig.SUN_ELEV if 'sun' in s else None", ast.unparse(calls[0])
    assert day_rig.SUN_ELEV == 78.0


@pytest.mark.parametrize("view,phi,theta,pitch", [("p07", 90.0, 106.7, 4.7), ("p08", 85.0, 130.0, 28.7),
                                                  ("p09", 81.0, 130.0, 30.5)])
def test_photo_up_gives_the_suns_height_without_roll(view, phi, theta, pitch):
    """The world's up for a photo: no roll, the sun 78 deg high, the lower pitch. 07's comes out at cam07's own
    (the camera fitted to the bike looks up 4.7 deg, head_closeups.py's DAY_SUN note); 08's and 09's put his head
    about 6 m above a camera 12 m away (his-photo-cameras.json), below the whip's apex (fmx-ramp-physics-whip.md)."""
    p, t = math.radians(phi), math.radians(theta)
    d = (math.cos(p) * math.sin(t), math.sin(p) * math.sin(t), math.cos(t))
    u, b = day_rig.photo_up(d, 78.0)
    assert abs(u[0]) < 1e-12 and abs(math.hypot(*u) - 1.0) < 1e-12
    assert abs(math.degrees(math.asin(sum(x * y for x, y in zip(u, d)))) - 78.0) < 1e-9
    assert abs(b - pitch) < 0.05, (view, b)


def test_e1_interpolates_the_table():
    assert day_rig.e1(70.0) == day_rig.E1[70]
    assert day_rig.e1(10.0) == day_rig.E1[min(day_rig.E1)]
    a, b = day_rig.E1[70], day_rig.E1[80]
    assert all(abs(x - (u + v) / 2) < 1e-12 for x, u, v in zip(day_rig.e1(75.0), a, b))


def _blender(*args):
    if not shutil.which("blender"):
        pytest.skip("needs Blender (tools/setup_blender.sh)")
    r = subprocess.run(["blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python",
                        os.path.join(COMMON, "day_rig.py"), "--", *args], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return r.stdout


def test_blender_turns_the_sky_as_the_module_says():
    """The rig turned for a camera on a tilted head (aim with an elevation) renders as the unturned sky seen by the
    turned camera, pixel for pixel, the sun 78 deg high in the sky's frame."""
    out = _blender("turn")
    line = [x for x in out.splitlines() if x.startswith("TURN")][0].split()
    assert float(line[line.index("elevation") + 1]) == pytest.approx(78.0, abs=1e-3)
    assert float(line[line.index("rel_p95") + 1]) < 1e-3, line
    assert int(line[line.index("ground_px") + 1]) > 100, line          # the ground's edge is in the test


def test_the_e1_table_is_the_skys_light():
    """E1 holds Blender's sky on a level white plane (strength 1, RIG's sky), within 1.5 % (1024 samples)."""
    import json
    out = _blender("e1")
    got = json.loads([x for x in out.splitlines() if x.startswith("E1 ")][0][3:])
    for el, rgb in day_rig.E1.items():
        for a, b in zip(got[str(el)], rgb):
            assert abs(a - b) < 0.015 * b, (el, got[str(el)], rgb)
