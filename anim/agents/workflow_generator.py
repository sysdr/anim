"""Workflow Generator Agent - Blueprint and workflow_spec from content or concept."""

from __future__ import annotations

from typing import Any

from anim.agents.architect import ArchitectAgent
from anim.agents.base import BaseAgent, StructuredContent
from anim.agents.director import DirectorAgent
from anim.blueprint.schema import Blueprint


class WorkflowGeneratorAgent(BaseAgent[Blueprint]):
    """
    Produces a Blueprint (and optionally workflow_spec) from structured content or raw text.
    Uses Architect + Director for the text→Blueprint path; Studio path uses Gemini in web layer.
    """

    name = "workflow_generator"

    def __init__(self) -> None:
        self._architect = ArchitectAgent()
        self._director = DirectorAgent()

    def run(
        self,
        content: StructuredContent | str,
        *,
        target_duration_seconds: float | None = None,
        refine: bool = True,
    ) -> Blueprint:
        """
        Generate Blueprint from structured content or raw text.

        Args:
            content: StructuredContent from Analyzer or raw text string.
            target_duration_seconds: Optional target total duration.
            refine: Whether to run Director to balance scene durations.

        Returns:
            Blueprint ready for Animator/Exporter.
        """
        if isinstance(content, str):
            text = content.strip()
            title = text.splitlines()[0].strip() if text else "Untitled"
        else:
            text = content.raw_text or "\n".join([content.title] + content.bullets)
            title = content.title or "Untitled"

        blueprint = self._architect.create_blueprint(text, title=title)
        if refine:
            blueprint = self._director.refine_blueprint(
                blueprint, target_duration_seconds=target_duration_seconds
            )
        return blueprint
