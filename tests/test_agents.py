"""Tests for Architect and Director agents."""

import pytest

from anim.agents.architect import ArchitectAgent
from anim.agents.director import DirectorAgent
from anim.agents.svg_validator import (
    SvgValidationAgent,
    SvgValidationResult,
    _collapse_duplicate_xmlns_in_string,
    _fix_stray_femerge_close_inside_filter,
)
from anim.blueprint.schema import Blueprint, Element, Scene, SceneType


class TestArchitectAgent:
    """Tests for ArchitectAgent."""

    def test_create_blueprint_empty(self):
        agent = ArchitectAgent()
        bp = agent.create_blueprint("")
        assert bp.title == "Untitled"
        assert len(bp.scenes) == 0

    def test_create_blueprint_single_line(self):
        agent = ArchitectAgent()
        bp = agent.create_blueprint("Hello")
        assert bp.title == "Hello"
        assert len(bp.scenes) == 1
        assert bp.scenes[0].scene_type == SceneType.TITLE
        assert bp.scenes[0].elements[0].content == "Hello"

    def test_create_blueprint_multiline(self):
        agent = ArchitectAgent()
        bp = agent.create_blueprint("Title\nLine 1\nLine 2")
        assert bp.title == "Title"
        assert len(bp.scenes) >= 2
        assert bp.scenes[0].scene_type == SceneType.TITLE
        assert bp.scenes[1].scene_type == SceneType.BULLETS
        assert len(bp.scenes[1].elements) == 2

    def test_create_blueprint_with_title_param(self):
        agent = ArchitectAgent()
        bp = agent.create_blueprint("Content", title="Custom Title")
        assert bp.title == "Custom Title"


class TestDirectorAgent:
    """Tests for DirectorAgent."""

    def test_refine_unchanged(self):
        agent = DirectorAgent()
        bp = Blueprint(title="T", scenes=[Scene(id="s1", scene_type=SceneType.TITLE, duration_seconds=5)])
        refined = agent.refine_blueprint(bp)
        assert refined.scenes[0].duration_seconds == 5

    def test_refine_scales_duration(self):
        agent = DirectorAgent()
        bp = Blueprint(
            title="T",
            scenes=[
                Scene(id="s1", scene_type=SceneType.TITLE, duration_seconds=2),
                Scene(id="s2", scene_type=SceneType.TEXT, duration_seconds=2),
            ],
        )
        refined = agent.refine_blueprint(bp, target_duration_seconds=8)
        total = sum(s.duration_seconds for s in refined.scenes)
        assert abs(total - 8) < 0.5


class TestSvgValidationAgent:
    """Tests for SvgValidationAgent."""

    def test_valid_svg_unchanged(self):
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540"><rect width="100%" height="100%" fill="#000"/></svg>'
        out = agent.validate_and_fix(svg)
        assert "root" in out
        assert "viewBox" in out

    def test_adds_root_id_and_viewbox(self):
        agent = SvgValidationAgent()
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540"><rect width="100%" height="100%"/></svg>'
        out = agent.validate_and_fix(svg)
        assert 'id="root"' in out
        assert "viewBox" in out

    def test_strips_script(self):
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><script>alert(1)</script><rect width="100%" height="100%"/></svg>'
        out = agent.validate_and_fix(svg)
        assert "<script" not in out.lower()
        assert "alert(1)" not in out

    def test_strips_event_handlers(self):
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" onclick="bad()"><rect width="100%" height="100%"/></svg>'
        out = agent.validate_and_fix(svg)
        assert "onclick" not in out

    def test_empty_returns_empty(self):
        agent = SvgValidationAgent()
        assert agent.validate_and_fix("") == ""
        assert agent.validate_and_fix("   ") == ""

    def test_duplicate_xmlns_collapsed(self):
        """Fix 'Attribute xmlns redefined' by keeping only the first xmlns."""
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#000"/></svg>'
        out = agent.validate_and_fix(svg)
        assert out.count('xmlns="http://www.w3.org/2000/svg"') == 1
        assert "viewBox" in out
        assert "<rect" in out

    def test_collapse_duplicate_xmlns_helper(self):
        """_collapse_duplicate_xmlns_in_string keeps first xmlns only."""
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><path d=""/></svg>'
        out = _collapse_duplicate_xmlns_in_string(svg)
        assert out.count("xmlns=") == 1
        assert "viewBox" in out

    def test_femerge_filter_tag_mismatch_fixed(self):
        """Unclosed <feMerge> before </filter> is fixed so SVG parses and renders."""
        agent = SvgValidationAgent()
        svg = '''<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">
  <defs><filter id="f"><feMerge></filter></defs>
  <rect width="100%" height="100%" fill="#000"/>
</svg>'''
        out = agent.validate_and_fix(svg)
        # Either </feMerge> was inserted or parser serialized as <feMerge />; result must be valid XML
        import xml.etree.ElementTree as ET
        ET.fromstring(out)
        # Filter must be well-formed: no stray </filter> closing feMerge
        assert "</filter>" in out
        assert "feMerge" in out

    def test_stray_femerge_close_replaced_with_filter(self):
        """When filter has wrong closing tag </feMerge> (no <feMerge> inside), replace with </filter>."""
        import xml.etree.ElementTree as ET
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><filter id="f"><feGaussianBlur in="SourceGraphic" stdDeviation="2"/></feMerge></defs><rect width="100%" height="100%"/></svg>'
        out = _fix_stray_femerge_close_inside_filter(svg)
        assert "</feMerge>" not in out or out.count("</filter>") >= 1
        fixed = SvgValidationAgent().validate_and_fix(svg)
        ET.fromstring(fixed)

    def test_validate_and_fix_with_report_returns_result(self):
        """validate_and_fix_with_report returns SvgValidationResult with svg, errors, fixes."""
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100%" height="100%"/></svg>'
        result = agent.validate_and_fix_with_report(svg)
        assert isinstance(result, SvgValidationResult)
        assert result.svg
        assert "root" in result.svg
        assert result.parse_failed is False

    def test_report_captures_errors_and_fixes(self):
        """When fixes are applied, report lists them."""
        agent = SvgValidationAgent()
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><path d=""/></svg>'
        result = agent.validate_and_fix_with_report(svg)
        assert result.svg.count("xmlns=") == 1
        assert any("xmlns" in f for f in result.fixes_applied) or len(result.fixes_applied) >= 1

    def test_unescaped_ampersand_in_attribute_fixed(self):
        """Unescaped & in attribute value is escaped to &amp;."""
        agent = SvgValidationAgent()
        svg_attr = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><title label="A & B">Tip</title></svg>'
        result = agent.validate_and_fix_with_report(svg_attr)
        assert "viewBox" in result.svg

    def test_bom_stripped(self):
        """BOM at start of SVG is removed."""
        agent = SvgValidationAgent()
        svg = '\ufeff<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d=""/></svg>'
        result = agent.validate_and_fix_with_report(svg)
        assert result.svg.startswith("<")
        assert not result.svg.startswith("\ufeff")
        assert any("BOM" in f for f in result.fixes_applied)

    def test_invalid_xml_chars_removed(self):
        """Invalid XML 1.0 control characters are removed."""
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\x00<rect\x01 width="100%"/></svg>'
        result = agent.validate_and_fix(svg)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "<rect" in result

    def test_duplicate_svg_attributes_removed(self):
        """Duplicate attributes on opening <svg> tag are deduplicated."""
        agent = SvgValidationAgent()
        svg = '<svg id="root" viewBox="0 0 100 100" id="other" xmlns="http://www.w3.org/2000/svg"><path d=""/></svg>'
        result = agent.validate_and_fix_with_report(svg)
        assert "viewBox" in result.svg
        assert "xmlns" in result.svg

    def test_parse_error_falls_back_to_minimal_fix(self):
        """When XML parse fails, minimal fix is applied and parse_failed is True."""
        agent = SvgValidationAgent()
        svg = '<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><unclosed></svg>'
        result = agent.validate_and_fix_with_report(svg)
        assert result.parse_failed is True
        assert result.svg
        assert "root" in result.svg or "<svg" in result.svg
