"""Director Agent - Scene blocking, camera moves, timing."""

from __future__ import annotations

from anim.blueprint.schema import Blueprint, Scene, SceneType


class DirectorAgent:
    """
    Adjusts scene timing and camera for visual flow.
    """

    def refine_blueprint(self, blueprint: Blueprint, target_duration_seconds: float | None = None) -> Blueprint:
        """Refine Blueprint with balanced scene durations."""
        scenes = list(blueprint.scenes)
        total = sum(s.duration_seconds for s in scenes)

        if target_duration_seconds and total > 0 and total != target_duration_seconds:
            scale = target_duration_seconds / total
            scenes = [
                Scene(**{**s.model_dump(), "duration_seconds": max(1.0, s.duration_seconds * scale)})
                for s in scenes
            ]

        return Blueprint(
            version=blueprint.version,
            title=blueprint.title,
            metadata=blueprint.metadata,
            global_style=blueprint.global_style,
            scenes=scenes,
        )
