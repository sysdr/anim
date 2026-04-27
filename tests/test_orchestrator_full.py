"""Full tests for RenderOrchestrator including render path."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anim.blueprint.schema import Blueprint, Element, Scene, SceneType
from anim.renderer.orchestrator import RenderOrchestrator


@pytest.fixture
def minimal_blueprint():
    return Blueprint(
        title="Test",
        scenes=[Scene(id="s1", scene_type=SceneType.TITLE, elements=[Element(content="T")])],
    )


class TestRenderOrchestratorRender:
    """Tests for RenderOrchestrator.render() - mocked Manim."""

    @patch("anim.renderer.orchestrator.tempconfig")
    @patch("anim.renderer.orchestrator.BlueprintScene")
    def test_render_returns_path(self, mock_scene_cls, mock_tempconfig, minimal_blueprint, tmp_path):
        mock_scene = MagicMock()
        out_mp4 = tmp_path / "videos" / "480p15" / "test.mp4"
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        out_mp4.touch()
        mock_fw = MagicMock()
        mock_fw.movie_file_path = str(out_mp4)
        mock_scene.renderer.file_writer = mock_fw
        mock_scene_cls.return_value = mock_scene

        orch = RenderOrchestrator(minimal_blueprint, output_dir=tmp_path, quality="draft", output_filename="test")
        result = orch.render()

        mock_tempconfig.assert_called_once()
        mock_scene_cls.assert_called_once_with(minimal_blueprint)
        mock_scene.render.assert_called_once_with(preview=False)
        assert result == out_mp4
        assert orch.output_path == out_mp4

    @patch("anim.renderer.orchestrator.tempconfig")
    @patch("anim.renderer.orchestrator.BlueprintScene")
    def test_render_config_keys(self, mock_scene_cls, mock_tempconfig, minimal_blueprint, tmp_path):
        class FakeCtx:
            def __enter__(_):
                return None

            def __exit__(_, *a):
                pass

        mock_tempconfig.return_value = FakeCtx()
        mock_scene = MagicMock()
        out_mp4 = tmp_path / "videos" / "480p15" / "test.mp4"
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        out_mp4.touch()
        mock_fw = MagicMock()
        mock_fw.movie_file_path = str(out_mp4)
        mock_scene.renderer.file_writer = mock_fw
        mock_scene_cls.return_value = mock_scene

        orch = RenderOrchestrator(minimal_blueprint, output_dir=tmp_path)
        orch.render()

        call_args = mock_tempconfig.call_args[0][0]
        assert "media_dir" in call_args
        assert "quality" in call_args
        assert "output_file" in call_args

    @patch("anim.renderer.orchestrator.tempconfig")
    @patch("anim.renderer.orchestrator.BlueprintScene")
    def test_render_fallback_when_file_writer_raises(self, mock_scene_cls, mock_tempconfig, minimal_blueprint, tmp_path):
        class FakeCtx:
            def __enter__(_):
                return None

            def __exit__(_, *a):
                pass

        mock_tempconfig.return_value = FakeCtx()
        mock_scene = MagicMock()
        mock_scene.renderer = None  # Accessing .file_writer raises AttributeError
        mock_scene_cls.return_value = mock_scene

        orch = RenderOrchestrator(minimal_blueprint, output_dir=tmp_path, output_filename="test")
        result = orch.render()

        assert orch._rendered_path == tmp_path / "videos" / "test.mp4"
