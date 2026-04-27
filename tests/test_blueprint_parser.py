"""Tests for Blueprint parser."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from anim.blueprint.parser import load_blueprint, parse_blueprint
from anim.blueprint.schema import Blueprint, SceneType


class TestParseBlueprint:
    """Tests for parse_blueprint."""

    def test_from_dict(self, minimal_blueprint_dict):
        bp = parse_blueprint(minimal_blueprint_dict)
        assert isinstance(bp, Blueprint)
        assert bp.title == "Test"
        assert len(bp.scenes) == 1
        assert bp.scenes[0].scene_type == SceneType.TITLE

    def test_from_json_string(self, minimal_blueprint_dict):
        s = json.dumps(minimal_blueprint_dict)
        bp = parse_blueprint(s)
        assert isinstance(bp, Blueprint)
        assert bp.title == "Test"

    def test_invalid_json_raises(self):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parse_blueprint("{ invalid }")

    def test_invalid_schema_raises(self):
        with pytest.raises(ValidationError):
            parse_blueprint({"scenes": "not a list"})  # type: ignore


class TestLoadBlueprint:
    """Tests for load_blueprint."""

    def test_load_file(self, example_blueprint_path, full_blueprint_dict):
        bp = load_blueprint(example_blueprint_path)
        assert bp.title == full_blueprint_dict["title"]

    def test_load_str_path(self, example_blueprint_path):
        bp = load_blueprint(str(example_blueprint_path))
        assert isinstance(bp, Blueprint)

    def test_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError) as exc:
            load_blueprint(missing)
        assert "not found" in str(exc.value).lower()
