"""Architect Agent - Logic extraction, Blueprint from text."""

from __future__ import annotations

from anim.blueprint.schema import Blueprint, Element, FlowEdge, FlowNode, Scene, SceneType


class ArchitectAgent:
    """
    Extracts logical structure from text and produces a Blueprint.
    Template-based (no LLM) for deterministic tests.
    """

    def create_blueprint(self, text: str, title: str | None = None) -> Blueprint:
        """Create a Blueprint from raw text."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        if not lines:
            return Blueprint(title=title or "Untitled", scenes=[])

        scenes: list[Scene] = []
        title_line = lines[0] if lines else "Untitled"

        scenes.append(
            Scene(
                id="s1",
                scene_type=SceneType.TITLE,
                duration_seconds=3,
                elements=[Element(content=title_line)],
                narration=title_line,
            )
        )

        content_lines = lines[1:] if len(lines) > 1 else []
        if content_lines:
            elements = [Element(content=line, duration_seconds=1.5) for line in content_lines[:10]]
            scenes.append(
                Scene(
                    id="s2",
                    scene_type=SceneType.BULLETS,
                    duration_seconds=len(elements) * 1.2,
                    elements=elements,
                )
            )

        return Blueprint(title=title or title_line, scenes=scenes)
