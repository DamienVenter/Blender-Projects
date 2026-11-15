"""The scene look shared by the bike and the rider (decision 54, scripts/common/scene_look.py): Blender renders it as
the module's numpy reference says, its numbers hold, and the rider's scripts use it (scene_look_checks.py)."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import scene_look_checks as C  # noqa: E402


def test_blender_renders_the_swatch_chart_as_the_module_says():
    C.check_swatches()


def test_the_look_keeps_its_numbers():
    C.check_numbers()


@pytest.mark.parametrize("script,functions", [
    ("build_rider.py", {"studio": ["scene"]}),
    ("head_closeups.py", {"studio": ["scene"], "daylight": ["daylight"]}),
    ("goggle_views.py", {"daylight": ["daylight"]}),
])
def test_the_rider_scripts_take_their_look_from_the_module(script, functions):
    C.check_script(os.path.join(HERE, script), functions)


def test_each_photo_has_its_own_exposure():
    """Decision 55: a view of one of his photos takes that photo's exposure (read off his white shell's lit side,
    research/scene-look.md), every other view the one look."""
    import scene_look as S
    assert set(S.PHOTO_EV) == {"07", "08", "09"}
    assert all(-2.0 < v < 2.0 for v in S.PHOTO_EV.values())
    assert S.photo_ev("p07") == S.photo_ev("cam07") == S.PHOTO_EV["07"]
    assert S.photo_ev("p09") == S.PHOTO_EV["09"] and S.photo_ev("front") == S.photo_ev("isol") == 0.0


def test_head_closeups_puts_each_photo_view_at_its_exposure():
    import ast
    tree = ast.parse(open(os.path.join(HERE, "head_closeups.py")).read())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "day_sun")
    calls = [ast.unparse(n) for n in ast.walk(fn) if isinstance(n, ast.Call) and ast.unparse(n.func) == "scene_look.apply"]
    assert any("scene_look.photo_ev(name)" in c and "'daylight'" in c for c in calls), calls


def test_head_closeups_gives_each_photo_view_its_tint():
    """Decision 59: a view of his 07 (p07, cam07) takes 07's tint of the darks with its exposure, at the same look
    call (scene_look.photo_tint: None for the other views, the lift alone)."""
    import ast
    tree = ast.parse(open(os.path.join(HERE, "head_closeups.py")).read())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "day_sun")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and ast.unparse(n.func) == "scene_look.apply"]
    kw = [{k.arg: ast.unparse(k.value) for k in c.keywords} for c in calls]
    assert any(k.get("tint") == "scene_look.photo_tint(name)" and "scene_look.photo_ev(name)" in k.get("ev", "")
               for k in kw), [ast.unparse(c) for c in calls]
