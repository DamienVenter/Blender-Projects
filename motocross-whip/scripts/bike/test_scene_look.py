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
