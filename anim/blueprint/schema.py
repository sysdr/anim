"""
Blueprint schema for SynapseFlow 2026.

Defines the unified JSON structure that the Architect, Director, and Narrator
agents produce and the rendering engine consumes.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SceneType(str, Enum):
    """Types of scenes the renderer can produce."""

    TITLE = "title"
    BULLETS = "bullets"
    TEXT = "text"
    FORMULA = "formula"
    FLOW = "flow"
    DIAGRAM = "diagram"
    PROCESS = "process"
    TRANSITION = "transition"


class Element(BaseModel):
    """Base element within a scene."""

    content: str
    duration_seconds: float = 1.5
    metadata: dict[str, Any] = Field(default_factory=dict)


class FlowNode(BaseModel):
    """Node in a flow diagram."""

    id: str
    label: str
    position: tuple[float, float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FlowEdge(BaseModel):
    """Edge connecting flow nodes."""

    source: str
    target: str
    label: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Scene(BaseModel):
    """Single scene in the Blueprint."""

    id: str
    scene_type: SceneType
    duration_seconds: float = 5.0
    elements: list[Element] = Field(default_factory=list)
    # Flow/diagram specific
    nodes: list[FlowNode] = Field(default_factory=list)
    edges: list[FlowEdge] = Field(default_factory=list)
    # Narration
    narration: str | None = None
    # Camera/visual (cinematic)
    camera_move: str | None = None  # e.g. "pan_right", "zoom_in", "establishing", "reveal"
    # Real-world entity metaphor for this scene (e.g. "factory", "pipeline", "organism")
    entity_metaphor: str | None = None
    # Optional act/chapter this scene belongs to
    act_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowPart(BaseModel):
    """Distinct subsystem or "part" of a complex workflow (e.g. ingestion, processing, storage)."""

    id: str
    name: str
    description: str = ""
    responsibility: str = ""
    scale_hint: str = ""  # e.g. "replicated", "sharded", "fan-out"
    scene_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Act(BaseModel):
    """Cinematic act/chapter: groups scenes into narrative beats (like animated movies)."""

    id: str
    title: str
    summary: str = ""
    narrative_beat: str = ""  # e.g. "establishing", "conflict", "resolution"
    scene_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GlobalStyle(BaseModel):
    """Global visual style for the video."""

    theme: str = "dark"
    background_color: str = "#1a1a2e"
    accent_color: str = "#2563EB"
    font_family: str = "sans-serif"
    text_color: str = "#ffffff"


class Blueprint(BaseModel):
    """Complete Blueprint for a SynapseFlow video."""

    version: str = "1.0"
    title: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    global_style: GlobalStyle = Field(default_factory=GlobalStyle)
    scenes: list[Scene] = Field(default_factory=list)
    # Cinematic structure: acts (chapters) and distinct workflow parts
    acts: list[Act] = Field(default_factory=list)
    workflow_parts: list[WorkflowPart] = Field(default_factory=list)
    # Global real-world metaphor (e.g. "factory", "data_center", "organism")
    entity_metaphor: str | None = None

    @property
    def total_duration(self) -> float:
        """Total duration of all scenes in seconds."""
        return sum(s.duration_seconds for s in self.scenes)
