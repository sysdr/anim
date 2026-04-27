"""Pytest fixtures and configuration."""

import json
from pathlib import Path

import pytest

from anim.blueprint.schema import (
    Blueprint,
    Element,
    FlowEdge,
    FlowNode,
    GlobalStyle,
    Scene,
    SceneType,
)


@pytest.fixture
def minimal_blueprint_dict():
    """Minimal valid Blueprint as dict."""
    return {
        "version": "1.0",
        "title": "Test",
        "scenes": [
            {"id": "s1", "scene_type": "title", "elements": [{"content": "Title"}]},
        ],
    }


@pytest.fixture
def full_blueprint_dict():
    """Full Blueprint with all scene types."""
    return {
        "version": "1.0",
        "title": "Full Test",
        "metadata": {"source": "test"},
        "global_style": {"theme": "dark", "background_color": "#000"},
        "scenes": [
            {"id": "s1", "scene_type": "title", "duration_seconds": 2, "elements": [{"content": "Title"}]},
            {"id": "s2", "scene_type": "bullets", "elements": [{"content": "A"}, {"content": "B"}]},
            {"id": "s3", "scene_type": "text", "elements": [{"content": "Text"}]},
            {"id": "s4", "scene_type": "formula", "elements": [{"content": "E=mc^2"}]},
            {"id": "s5", "scene_type": "flow", "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}], "edges": [{"source": "A", "target": "B"}]},
            {"id": "s6", "scene_type": "transition", "duration_seconds": 1},
        ],
    }


@pytest.fixture
def blueprint(minimal_blueprint_dict):
    """Blueprint instance."""
    return Blueprint.model_validate(minimal_blueprint_dict)


@pytest.fixture
def full_blueprint(full_blueprint_dict):
    """Full Blueprint instance."""
    return Blueprint.model_validate(full_blueprint_dict)


@pytest.fixture
def example_blueprint_path(tmp_path, full_blueprint_dict):
    """Path to a temp Blueprint JSON file."""
    path = tmp_path / "test_blueprint.json"
    path.write_text(json.dumps(full_blueprint_dict), encoding="utf-8")
    return path
