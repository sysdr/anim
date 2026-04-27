"""Tests for RenderOrchestrator."""

from pathlib import Path

import pytest

from anim.blueprint.schema import Blueprint, Element, Scene, SceneType
from anim.renderer.orchestrator import RenderOrchestrator


@pytest.fixture
def minimal_blueprint():
    return Blueprint(
        title="Test",
        scenes=[Scene(id="s1", scene_type=SceneType.TITLE, elements=[Element(content="T")])],
    )


class TestRenderOrchestrator:
    """Tests for RenderOrchestrator."""

    def test_init_defaults(self, minimal_blueprint):
        orch = RenderOrchestrator(minimal_blueprint)
        assert orch.blueprint == minimal_blueprint
        assert orch.output_dir == Path("media")
        assert orch.quality == "standard"
        assert orch.output_filename == "synapseflow_output"

    def test_init_custom(self, minimal_blueprint):
        orch = RenderOrchestrator(
            minimal_blueprint,
            output_dir="/tmp",
            quality="draft",
            output_filename="my_video",
        )
        assert orch.output_dir == Path("/tmp")
        assert orch.quality == "draft"
        assert orch.output_filename == "my_video"

    def test_output_path_before_render(self, minimal_blueprint):
        orch = RenderOrchestrator(minimal_blueprint)
        assert orch.output_path is None

    def test_output_path_after_render(self, minimal_blueprint):
        orch = RenderOrchestrator(minimal_blueprint)
        orch._rendered_path = Path("/tmp/out.mp4")
        assert orch.output_path == Path("/tmp/out.mp4")

    def test_quality_presets(self):
        assert "draft" in RenderOrchestrator.QUALITY_PRESETS
        assert "standard" in RenderOrchestrator.QUALITY_PRESETS
        assert "premium" in RenderOrchestrator.QUALITY_PRESETS
        assert RenderOrchestrator.QUALITY_PRESETS["draft"]["quality"] == "low_quality"
