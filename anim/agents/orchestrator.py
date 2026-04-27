"""Pipeline Orchestrator - drives the agent pipeline for generate and render flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anim.agents.analyzer import AnalyzerAgent
from anim.agents.base import StructuredContent
from anim.agents.exporter import ExporterAgent
from anim.agents.workflow_generator import WorkflowGeneratorAgent
from anim.blueprint.schema import Blueprint
from anim.renderer.orchestrator import RenderOrchestrator


class PipelineOrchestrator:
    """
    Orchestrates the full pipeline: Analyzer → WorkflowGenerator → Animator (Manim) → Exporter.
    Single entry point for CLI and web "generate" / "render" flows.
    """

    def __init__(
        self,
        *,
        output_dir: str | Path = "media",
        quality: str = "standard",
        storage: Any = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.quality = quality
        self._analyzer = AnalyzerAgent()
        self._workflow_gen = WorkflowGeneratorAgent()
        self._exporter = ExporterAgent(storage=storage)

    def generate(
        self,
        source: str | Path,
        *,
        output_name: str | None = None,
        target_duration_seconds: float | None = None,
        save_blueprint_path: Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate video from source (URL, PDF path, or text).
        Runs: Analyzer → WorkflowGenerator → RenderOrchestrator → Exporter.

        Returns:
            Dict with blueprint, workflow (scene list), path, output_name, status.
        """
        content = self._analyzer.run(source)
        blueprint = self._workflow_gen.run(
            content,
            target_duration_seconds=target_duration_seconds,
            refine=True,
        )
        if save_blueprint_path:
            save_blueprint_path.write_text(
                blueprint.model_dump_json(indent=2), encoding="utf-8"
            )

        output_name = output_name or "generated"
        orch = RenderOrchestrator(
            blueprint,
            output_dir=self.output_dir,
            quality=self.quality,
            output_filename=output_name,
        )
        rendered_path = orch.render()

        export_result = self._exporter.run(
            rendered_path,
            output_dir=self.output_dir,
            title=blueprint.title or output_name,
        )

        workflow = _workflow_from_blueprint(blueprint)
        return {
            "status": "done",
            "blueprint": blueprint,
            "workflow": workflow,
            "path": str(export_result.path),
            "url": export_result.url or f"/media/{export_result.path}",
            "output_name": output_name,
            "storage_id": export_result.storage_id,
        }

    def render_blueprint(
        self,
        blueprint: Blueprint,
        *,
        output_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Render an existing Blueprint to video (no Analyzer/WorkflowGenerator).
        Runs: Animator (Manim) → Exporter.

        Returns:
            Dict with path, output_name, status.
        """
        output_name = output_name or blueprint.title or "output"
        orch = RenderOrchestrator(
            blueprint,
            output_dir=self.output_dir,
            quality=self.quality,
            output_filename=output_name,
        )
        rendered_path = orch.render()
        export_result = self._exporter.run(
            rendered_path,
            output_dir=self.output_dir,
            title=blueprint.title or output_name,
        )
        return {
            "status": "done",
            "path": str(export_result.path),
            "url": export_result.url or f"/media/{export_result.path}",
            "output_name": output_name,
            "storage_id": export_result.storage_id,
        }


def _workflow_from_blueprint(blueprint: Blueprint) -> list[dict[str, Any]]:
    """Extract workflow (scenes) from Blueprint for UI display."""
    out = []
    for i, s in enumerate(blueprint.scenes, 1):
        scene = {
            "index": i,
            "id": s.id,
            "type": s.scene_type.value,
            "duration": s.duration_seconds,
        }
        if s.elements:
            scene["content"] = [
                e.content[:80] + ("..." if len(e.content) > 80 else "")
                for e in s.elements[:3]
            ]
        elif s.narration:
            scene["content"] = [s.narration[:80] + ("..." if len(s.narration) > 80 else "")]
        elif s.nodes:
            scene["content"] = [f"{n.id}: {n.label}" for n in s.nodes[:5]]
        else:
            scene["content"] = []
        out.append(scene)
    return out
