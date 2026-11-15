"""The scene look shared by the bike and the rider (decision 54, scripts/common/scene_look.py): Blender renders it as
the module's numpy reference says, its numbers hold, and the bike's scripts use it (scene_look_checks.py)."""
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
    ("build_bike.py", {"studio": ["scene"], "render": ["scene", "studio"]}),
    ("rake.py", {None: ["scene"]}),
])
def test_the_bike_scripts_take_their_look_from_the_module(script, functions):
    C.check_script(os.path.join(HERE, script), functions)


# ---- Honda's studio light (decision 55, round 2b: research/scene-look.md "Honda's studio") -------------------------

def _build_bike():
    import ast
    tree = ast.parse(open(os.path.join(HERE, "build_bike.py")).read())
    return tree, {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def _default(tree, name):
    """The literal default of a module-level NAME = ... os.environ.get(..., default) ... assignment."""
    import ast
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            for c in ast.walk(n.value):
                if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "get" and len(c.args) == 2:
                    return ast.literal_eval(c.args[1])
            return ast.literal_eval(n.value)
    raise AssertionError(name + " not assigned")


def test_the_studio_reflects_dark_as_hondas_does():
    """Honda's photos show their studio dark in the coat (linear G 7 to 9 per mille below 60 deg of elevation, 20
    overhead): the world shows in reflections well under the strength it lights with, and of the lamps only the top
    one is seen in reflections (on main every lamp and the whole grey world were, G 26 to 137)."""
    tree, _ = _build_bike()
    w, lamps, ev, refl = (float(v) for v in _default(tree, "_S").split(","))
    assert 0.0 < refl <= w / 3, (w, refl)
    seen = {k for k, v in _default(tree, "STUDIO_LAMPS").items() if v[1]}
    assert seen == {"top"}, seen


def test_the_studio_shows_the_world_to_reflections_through_its_dome_in_hondas_views_only():
    """render(): in the honda_* views the world is hidden from reflected rays and the dome (the world's grey at
    STUDIO[3], seen by reflected rays only) takes its place; every other view keeps the world as before."""
    import ast
    _, fn = _build_bike()
    src = ast.unparse(fn["render"])
    assert "sc.world.cycles_visibility.glossy = not honda" in src
    assert "bpy.data.objects['refl_dome'].hide_render = not honda" in src
    st = ast.unparse(fn["studio"])
    for k in ("camera", "diffuse", "transmission", "volume_scatter", "shadow"):
        assert "'%s'" % k in st, k
    assert "em.inputs['Strength'].default_value = STUDIO[3]" in st
    assert "dm.cycles.emission_sampling = 'NONE'" in st


def test_the_studio_turns_with_hondas_camera():
    """Honda's left and right photos light the bike alike (the plain red's linear R 896 and 898): the lamps turn
    about the bike's vertical axis with the honda_* camera (turn_lamps), and go back home for the other views."""
    import ast
    _, fn = _build_bike()
    assert "turn_lamps" in fn
    calls = [ast.unparse(c) for c in ast.walk(fn["render"]) if isinstance(c, ast.Call)
             and getattr(c.func, "id", "") == "turn_lamps"]
    assert calls == ["turn_lamps(co if honda else None)"], calls
    assert "honda_left" in ast.unparse(fn["turn_lamps"])


def test_the_red_gate_leaves_out_the_coats_highlights():
    """look_fit.red_test, the coordinator's gate on his 07 (round 2b): red the largest channel, saturation over 0.5,
    value over 77, G and B under 0.45 R. His plastic's body passes; the coat's pinkish highlights (the surroundings
    in it) and dark or orange-yellow pixels do not (round 2's hue gate kept the highlights)."""
    import numpy as np
    import look_fit
    px = np.asarray([[183, 41, 41], [221, 60, 57], [230, 110, 120], [245, 120, 125], [70, 12, 12], [200, 150, 40]],
                    float) / 255.0
    assert look_fit.red_test(px).tolist() == [True, True, False, False, False, False]
