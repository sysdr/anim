"""
Render Orchestrator - drives Manim rendering from Blueprint.

Handles:
- Config (quality, output dir, background)
- Programmatic Scene.render()
- Output path collection for downstream assembly
"""

from __future__ import annotations

from pathlib import Path

from manim import config, tempconfig

from anim.blueprint.schema import Blueprint
from anim.renderer.scene_builder import BlueprintScene


class RenderOrchestrator:
    """
    Orchestrates Manim rendering of a Blueprint.

    Uses tempconfig for programmatic control of quality, output path, etc.
    """

    QUALITY_PRESETS = {
        "draft": {"quality": "low_quality", "pixel_height": 480, "pixel_width": 854, "frame_rate": 15},
        "standard": {"quality": "medium_quality", "pixel_height": 720, "pixel_width": 1280, "frame_rate": 30},
        "premium": {"quality": "high_quality", "pixel_height": 1080, "pixel_width": 1920, "frame_rate": 60},
    }

    def __init__(
        self,
        blueprint: Blueprint,
        *,
        output_dir: str | Path = "media",
        quality: str = "standard",
        output_filename: str | None = None,
    ):
        self.blueprint = blueprint
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.output_filename = output_filename or "synapseflow_output"
        self._rendered_path: Path | None = None

    def render(self) -> Path:
        """
        Render the Blueprint to video.

        Returns:
            Path to the rendered MP4 file.
        """
        preset = self.QUALITY_PRESETS.get(
            self.quality,
            self.QUALITY_PRESETS["standard"],
        )

        render_config = {
            "media_dir": str(self.output_dir),
            "output_file": self.output_filename,
            **preset,
        }

        # Apply global style background if supported
        try:
            from manim import ManimColor

            render_config["background_color"] = ManimColor(
                self.blueprint.global_style.background_color
            )
        except Exception:
            pass

        with tempconfig(render_config):
            scene = BlueprintScene(self.blueprint)
            scene.render(preview=False)

            # Manim writes to media_dir/videos/SceneName/quality/SceneName.mp4
            # When using output_file, it uses that as the scene name
            # The actual path is in scene.renderer.file_writer
            try:
                fw = scene.renderer.file_writer
                if hasattr(fw, "movie_file_path") and fw.movie_file_path:
                    self._rendered_path = Path(fw.movie_file_path)
                else:
                    # Fallback: infer from config
                    base = Path(config.media_dir) / "videos" / self.output_filename
                    candidates = list(base.rglob("*.mp4"))
                    self._rendered_path = candidates[0] if candidates else base
            except Exception:
                self._rendered_path = self.output_dir / "videos" / f"{self.output_filename}.mp4"

        return self._rendered_path

    @property
    def output_path(self) -> Path | None:
        """Path to the rendered video file (after render())."""
        return self._rendered_path
