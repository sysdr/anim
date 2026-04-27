"""Tests for scene builder (mocked Manim)."""

from unittest.mock import MagicMock, patch

import pytest

from anim.blueprint.schema import (
    Blueprint,
    Element,
    FlowEdge,
    FlowNode,
    Scene,
    SceneType,
)


def _make_scene_with_mocks():
    """Create BlueprintScene with mocked play/wait."""
    from anim.renderer.scene_builder import BlueprintScene

    bp = Blueprint(scenes=[])
    scene = BlueprintScene(bp)
    scene.play = MagicMock()
    scene.wait = MagicMock()
    return scene


@pytest.fixture
def blueprint_title_only():
    """Blueprint with single title scene."""
    return Blueprint(
        title="Test",
        scenes=[Scene(id="s1", scene_type=SceneType.TITLE, elements=[Element(content="Title")])],
    )


@pytest.fixture
def blueprint_bullets():
    """Blueprint with bullets scene."""
    return Blueprint(
        title="Test",
        scenes=[
            Scene(
                id="s1",
                scene_type=SceneType.BULLETS,
                elements=[Element(content="A"), Element(content="B")],
            )
        ],
    )


@pytest.fixture
def blueprint_flow():
    """Blueprint with flow scene."""
    return Blueprint(
        title="Test",
        scenes=[
            Scene(
                id="s1",
                scene_type=SceneType.FLOW,
                nodes=[FlowNode(id="A", label="A"), FlowNode(id="B", label="B")],
                edges=[FlowEdge(source="A", target="B")],
            )
        ],
    )


@pytest.fixture
def blueprint_flow_empty_nodes():
    """Blueprint with flow but no nodes."""
    return Blueprint(
        title="Test",
        scenes=[Scene(id="s1", scene_type=SceneType.FLOW, nodes=[], edges=[])],
    )


class TestBlueprintScene:
    """Tests for BlueprintScene - uses mocked Manim."""

    @patch("anim.renderer.scene_builder.Scene")
    @patch("anim.renderer.scene_builder.Text")
    @patch("anim.renderer.scene_builder.FadeIn")
    @patch("anim.renderer.scene_builder.FadeOut")
    @patch("anim.renderer.scene_builder.VGroup")
    @patch("anim.renderer.scene_builder.Write")
    def test_construct_title(
        self, mock_write, mock_vgroup, mock_fade_out, mock_fade_in, mock_text, mock_scene
    ):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(
            scenes=[Scene(id="s1", scene_type=SceneType.TITLE, elements=[Element(content="T")])]
        )
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2  # FadeIn + FadeOut

    def test_hex_to_manim_color(self):
        from anim.renderer.scene_builder import _hex_to_manim_color

        with patch("manim.ManimColor") as mock_mc:
            mock_mc.return_value = "mock_color"
            result = _hex_to_manim_color("#ffffff")
            mock_mc.assert_called_once_with("#ffffff")
            assert result == "mock_color"

    def test_hex_to_manim_color_fallback(self):
        from anim.renderer.scene_builder import _hex_to_manim_color

        with patch("manim.ManimColor", side_effect=Exception("err")):
            result = _hex_to_manim_color("#bad")
            from manim import BLUE

            assert result == BLUE

    def test_render_bullets_with_elements(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.BULLETS, elements=[Element(content="A"), Element(content="B")])])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_bullets_narration_only(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.BULLETS, elements=[], narration="Narr")])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_text(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.TEXT, elements=[Element(content="T")])])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_formula(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.FORMULA, elements=[Element(content="E=mc^2")])])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_flow_empty_nodes(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.FLOW, nodes=[], edges=[])])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_flow_with_nodes_graph_success(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(
            scenes=[
                Scene(
                    id="s1",
                    scene_type=SceneType.FLOW,
                    nodes=[FlowNode(id="A", label="A"), FlowNode(id="B", label="B")],
                    edges=[FlowEdge(source="A", target="B")],
                )
            ]
        )
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        with patch("manim.Graph") as mock_graph:
            mock_graph.return_value = MagicMock()
            scene._render_scene(bp.scenes[0])
            mock_graph.assert_called_once()
            assert scene.play.call_count >= 2

    def test_render_flow_with_nodes_graph_fallback(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(
            scenes=[
                Scene(
                    id="s1",
                    scene_type=SceneType.FLOW,
                    nodes=[FlowNode(id="A", label="A"), FlowNode(id="B", label="B")],
                    edges=[FlowEdge(source="A", target="B")],
                )
            ]
        )
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        with patch("manim.Graph", side_effect=Exception("graph err")):
            scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_diagram(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.DIAGRAM, elements=[Element(content="D")])])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_process(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.PROCESS, elements=[Element(content="P")])])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        assert scene.play.call_count >= 2

    def test_render_transition(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(scenes=[Scene(id="s1", scene_type=SceneType.TRANSITION, duration_seconds=0.5)])
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene._render_scene(bp.scenes[0])
        scene.wait.assert_called_once_with(0.5)

    def test_construct_multiple_scenes(self):
        from anim.renderer.scene_builder import BlueprintScene

        bp = Blueprint(
            scenes=[
                Scene(id="s1", scene_type=SceneType.TITLE, elements=[Element(content="T1")]),
                Scene(id="s2", scene_type=SceneType.TITLE, elements=[Element(content="T2")]),
            ]
        )
        scene = BlueprintScene(bp)
        scene.play = MagicMock()
        scene.wait = MagicMock()
        scene.construct()
        assert scene.play.call_count >= 4
        assert scene.wait.call_count >= 2  # inter-scene waits + within-scene waits
