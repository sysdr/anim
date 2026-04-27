"""Studio Display & Controller Agent - UI state and control events for Studio."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StudioDisplayState:
    """Current state for Studio UI: workflow_spec, SVG, timeline, script, aspect ratio."""

    workflow_spec: dict[str, Any] = field(default_factory=dict)
    svg_source: str = ""
    timeline: list[dict[str, Any]] = field(default_factory=list)
    voiceover_script: str = ""
    aspect_ratio: str = "16:9"
    concept: str = ""
    status: str = "idle"  # idle | loading | ready | error
    error_message: str = ""


class StudioDisplayController:
    """
    Holds Studio display state and applies control events (e.g. set concept, set result).
    Used by the web layer to prepare data for the Studio UI.
    """

    def __init__(self) -> None:
        self._state = StudioDisplayState()

    @property
    def state(self) -> StudioDisplayState:
        return self._state

    def set_concept(self, concept: str, aspect_ratio: str = "16:9") -> None:
        """Update concept and aspect ratio (e.g. when user starts generation)."""
        self._state.concept = concept
        self._state.aspect_ratio = aspect_ratio
        self._state.status = "loading"

    def set_result(
        self,
        workflow_spec: dict[str, Any],
        svg_source: str,
        timeline: list[dict[str, Any]],
        voiceover_script: str,
    ) -> None:
        """Update state with generation result (workflow_spec, SVG, timeline, script)."""
        self._state.workflow_spec = workflow_spec or {}
        self._state.svg_source = svg_source or ""
        self._state.timeline = timeline or []
        self._state.voiceover_script = voiceover_script or ""
        self._state.status = "ready"
        self._state.error_message = ""

    def set_error(self, message: str) -> None:
        """Set error state for UI."""
        self._state.status = "error"
        self._state.error_message = message or "Unknown error"

    def to_display_dict(self) -> dict[str, Any]:
        """Export state for API/UI consumption."""
        return {
            "workflow_spec": self._state.workflow_spec,
            "svg_source": self._state.svg_source,
            "timeline": self._state.timeline,
            "voiceover_script": self._state.voiceover_script,
            "aspect_ratio": self._state.aspect_ratio,
            "concept": self._state.concept,
            "status": self._state.status,
            "error_message": self._state.error_message,
        }
