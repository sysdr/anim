"""Tests for CLI."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anim.cli import main


class TestCLI:
    """Tests for CLI main."""

    def test_main_is_callable(self):
        assert callable(main)

    @patch("anim.cli.RenderOrchestrator")
    @patch("anim.cli.load_blueprint")
    def test_main_render_invokes_orchestrator(self, mock_load, mock_orch_cls, tmp_path):
        import sys

        bp_path = tmp_path / "test.json"
        bp_path.write_text(
            json.dumps({"title": "T", "scenes": [{"id": "s1", "scene_type": "title", "elements": [{"content": "T"}]}]})
        )
        mock_bp = MagicMock()
        mock_bp.title = "Test"
        mock_bp.scenes = []
        mock_bp.total_duration = 0.0
        mock_load.return_value = mock_bp
        mock_orch = MagicMock()
        mock_orch.render.return_value = Path("/tmp/out.mp4")
        mock_orch_cls.return_value = mock_orch

        with patch.object(sys, "argv", ["synapseflow", "render", str(bp_path)]):
            main()
        mock_load.assert_called_once()
        mock_orch_cls.assert_called_once()

    @patch("anim.cli.PipelineOrchestrator")
    def test_main_generate_invokes_pipeline(self, mock_orch_cls, tmp_path):
        import sys

        mock_orch = MagicMock()
        mock_orch.generate.return_value = {
            "status": "done",
            "blueprint": MagicMock(title="Topic", scenes=[], total_duration=5.0),
            "workflow": [],
            "path": str(tmp_path / "out.mp4"),
            "url": "/media/out.mp4",
            "output_name": "generated",
            "storage_id": None,
        }
        mock_orch_cls.return_value = mock_orch

        with patch.object(sys, "argv", ["synapseflow", "generate", "How batteries work"]):
            main()
        mock_orch_cls.assert_called_once()
        mock_orch.generate.assert_called_once()
        call_kw = mock_orch.generate.call_args[1]
        assert call_kw.get("output_name") == "generated"
        assert call_kw.get("target_duration_seconds") == 90.0
