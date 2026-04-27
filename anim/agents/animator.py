"""Animator Agent - editor, modifier, updater; builds and renders scenes (Manim or SVG)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anim.agents.base import BaseAgent
from anim.blueprint.schema import Blueprint
from anim.renderer.orchestrator import RenderOrchestrator
from anim.renderer.scene_builder import BlueprintScene


class AnimatorAgent(BaseAgent[Path]):
    """
    Edits, modifies, and updates Blueprint-driven animation; renders via Manim.
    Responsibilities: apply edits to Blueprint, run scene builder, trigger render.
    """

    name = "animator"

    def run(
        self,
        blueprint: Blueprint,
        *,
        output_dir: str | Path = "media",
        quality: str = "standard",
        output_filename: str | None = None,
    ) -> Path:
        """
        Render Blueprint to video using Manim (RenderOrchestrator + BlueprintScene).

        Args:
            blueprint: Blueprint to render.
            output_dir: Media output directory.
            quality: draft | standard | premium.
            output_filename: Output base name.

        Returns:
            Path to the rendered MP4 file.
        """
        output_filename = output_filename or blueprint.title or "output"
        orch = RenderOrchestrator(
            blueprint,
            output_dir=output_dir,
            quality=quality,
            output_filename=output_filename,
        )
        return orch.render()

    def modify_duration(self, blueprint: Blueprint, target_seconds: float) -> Blueprint:
        """Return a new Blueprint with total duration scaled to target_seconds."""
        from anim.agents.director import DirectorAgent

        return DirectorAgent().refine_blueprint(blueprint, target_duration_seconds=target_seconds)

    def update_scene_narration(self, blueprint: Blueprint, scene_id: str, narration: str) -> Blueprint:
        """Return a new Blueprint with the given scene's narration updated."""
        scenes = []
        for s in blueprint.scenes:
            if s.id == scene_id:
                scenes.append(s.model_copy(update={"narration": narration}))
            else:
                scenes.append(s)
        return blueprint.model_copy(update={"scenes": scenes})
