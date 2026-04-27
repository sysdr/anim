"""Tests for Blueprint schema."""

import pytest

from anim.blueprint.schema import (
    Act,
    Blueprint,
    Element,
    FlowEdge,
    FlowNode,
    GlobalStyle,
    Scene,
    SceneType,
    WorkflowPart,
)


class TestSceneType:
    """Tests for SceneType enum."""

    def test_all_types(self):
        assert SceneType.TITLE == "title"
        assert SceneType.BULLETS == "bullets"
        assert SceneType.TEXT == "text"
        assert SceneType.FORMULA == "formula"
        assert SceneType.FLOW == "flow"
        assert SceneType.DIAGRAM == "diagram"
        assert SceneType.PROCESS == "process"
        assert SceneType.TRANSITION == "transition"


class TestElement:
    """Tests for Element model."""

    def test_minimal(self):
        e = Element(content="test")
        assert e.content == "test"
        assert e.duration_seconds == 1.5
        assert e.metadata == {}

    def test_full(self):
        e = Element(content="x", duration_seconds=2.0, metadata={"k": "v"})
        assert e.content == "x"
        assert e.duration_seconds == 2.0
        assert e.metadata == {"k": "v"}


class TestFlowNode:
    """Tests for FlowNode model."""

    def test_minimal(self):
        n = FlowNode(id="A", label="Label")
        assert n.id == "A"
        assert n.label == "Label"
        assert n.position is None

    def test_with_position(self):
        n = FlowNode(id="A", label="L", position=(1.0, 2.0))
        assert n.position == (1.0, 2.0)


class TestFlowEdge:
    """Tests for FlowEdge model."""

    def test_minimal(self):
        e = FlowEdge(source="A", target="B")
        assert e.source == "A"
        assert e.target == "B"
        assert e.label is None


class TestScene:
    """Tests for Scene model."""

    def test_minimal(self):
        s = Scene(id="s1", scene_type=SceneType.TITLE)
        assert s.id == "s1"
        assert s.scene_type == SceneType.TITLE
        assert s.duration_seconds == 5.0
        assert s.elements == []
        assert s.nodes == []
        assert s.edges == []

    def test_with_elements(self):
        s = Scene(id="s1", scene_type=SceneType.BULLETS, elements=[Element(content="x")])
        assert len(s.elements) == 1
        assert s.elements[0].content == "x"


class TestGlobalStyle:
    """Tests for GlobalStyle model."""

    def test_defaults(self):
        g = GlobalStyle()
        assert g.theme == "dark"
        assert g.background_color == "#1a1a2e"
        assert g.accent_color == "#2563EB"


class TestAct:
    """Tests for Act (cinematic chapter)."""

    def test_minimal(self):
        a = Act(id="act-1", title="Establishing")
        assert a.id == "act-1"
        assert a.title == "Establishing"
        assert a.scene_ids == []
        assert a.narrative_beat == ""

    def test_with_beat_and_scenes(self):
        a = Act(id="a1", title="Build", summary="We build the system", narrative_beat="build", scene_ids=["s1", "s2"])
        assert a.narrative_beat == "build"
        assert a.scene_ids == ["s1", "s2"]


class TestWorkflowPart:
    """Tests for WorkflowPart (distinct subsystem)."""

    def test_minimal(self):
        p = WorkflowPart(id="part-ingestion", name="Ingestion")
        assert p.id == "part-ingestion"
        assert p.name == "Ingestion"
        assert p.scale_hint == ""
        assert p.scene_ids == []

    def test_with_scale(self):
        p = WorkflowPart(id="p1", name="Workers", responsibility="Process", scale_hint="replicated", scene_ids=["s5"])
        assert p.scale_hint == "replicated"
        assert p.scene_ids == ["s5"]


class TestBlueprint:
    """Tests for Blueprint model."""

    def test_empty(self):
        b = Blueprint()
        assert b.version == "1.0"
        assert b.title == ""
        assert b.scenes == []
        assert b.acts == []
        assert b.workflow_parts == []
        assert b.entity_metaphor is None
        assert b.total_duration == 0.0

    def test_total_duration(self, blueprint):
        assert blueprint.total_duration == 5.0  # default scene duration

    def test_full_blueprint_total_duration(self, full_blueprint):
        total = sum(s.duration_seconds for s in full_blueprint.scenes)
        assert full_blueprint.total_duration == total

    def test_blueprint_with_acts_and_parts(self):
        b = Blueprint(
            title="Pipeline",
            acts=[Act(id="a1", title="Establishing", narrative_beat="establishing", scene_ids=["s1"])],
            workflow_parts=[WorkflowPart(id="p1", name="Ingestion", scale_hint="fan-out")],
            entity_metaphor="factory",
        )
        assert len(b.acts) == 1
        assert b.acts[0].title == "Establishing"
        assert len(b.workflow_parts) == 1
        assert b.workflow_parts[0].scale_hint == "fan-out"
        assert b.entity_metaphor == "factory"
