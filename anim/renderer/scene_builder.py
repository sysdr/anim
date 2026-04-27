"""
Manim scene builder - maps Blueprint scenes to Manim animations.

Each SceneType is rendered with appropriate Manim primitives:
- TITLE: Large text with fade-in
- BULLETS: Bullet list with successive Write animations
- TEXT: Paragraph with appropriate formatting
- FORMULA: MathTex/TeX
- FLOW: Graph/network with arrows
- DIAGRAM: Shapes + labels
- PROCESS: Step-by-step with arrows
- TRANSITION: Fade/transition effect
"""

from __future__ import annotations

from manim import (
    BLUE,
    Create,
    DOWN,
    LEFT,
    FadeIn,
    FadeOut,
    MathTex,
    Scene,
    Text,
    UP,
    VGroup,
    Write,
)

from anim.blueprint.schema import Blueprint, SceneType as BlueprintSceneType


def _hex_to_manim_color(hex_color: str):
    """Convert hex string to Manim color. Fallback to BLUE if invalid."""
    try:
        from manim import ManimColor

        return ManimColor(hex_color)
    except Exception:
        return BLUE


class BlueprintScene(Scene):
    """
    Manim Scene that renders a SynapseFlow Blueprint.

    Dynamically builds construct() from the Blueprint's scene list.
    """

    def __init__(self, blueprint: Blueprint, **kwargs):
        self._blueprint = blueprint
        super().__init__(**kwargs)

    def construct(self):
        style = self._blueprint.global_style
        # Apply background if supported
        # Manim uses config.background_color - we'd set it before render

        for i, scene in enumerate(self._blueprint.scenes):
            self._render_scene(scene)
            # Brief pause between scenes
            if i < len(self._blueprint.scenes) - 1:
                self.wait(0.3)

    def _render_scene(self, scene):
        """Render a single Blueprint scene based on its type."""
        handlers = {
            BlueprintSceneType.TITLE: self._render_title,
            BlueprintSceneType.BULLETS: self._render_bullets,
            BlueprintSceneType.TEXT: self._render_text,
            BlueprintSceneType.FORMULA: self._render_formula,
            BlueprintSceneType.FLOW: self._render_flow,
            BlueprintSceneType.DIAGRAM: self._render_diagram,
            BlueprintSceneType.PROCESS: self._render_process,
            BlueprintSceneType.TRANSITION: self._render_transition,
        }
        handler = handlers.get(scene.scene_type, self._render_text)
        handler(scene)

    def _render_title(self, scene):
        content = scene.elements[0].content if scene.elements else scene.narration or "Title"
        text = Text(content, font_size=48).to_edge(UP, buff=1)
        self.play(FadeIn(text), run_time=1.5)
        self.wait(scene.duration_seconds - 1.5)
        self.play(FadeOut(text), run_time=0.5)

    def _render_bullets(self, scene):
        items = [e.content for e in scene.elements] if scene.elements else []
        if not items and scene.narration:
            items = [scene.narration]
        if not items:
            items = ["Placeholder bullet"]
        # Use Text (no LaTeX) - BulletedList requires LaTeX
        bullet_texts = VGroup(
            *[Text(f"•  {item}", font_size=32) for item in items]
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        self.play(FadeIn(bullet_texts), run_time=min(scene.duration_seconds, len(items) * 0.6))
        self.wait(max(0, scene.duration_seconds - len(items) * 0.6))
        self.play(FadeOut(bullet_texts), run_time=0.5)

    def _render_text(self, scene):
        content = scene.elements[0].content if scene.elements else scene.narration or "Content"
        text = Text(content, font_size=32)
        self.play(FadeIn(text), run_time=1.0)
        self.wait(scene.duration_seconds - 1.0)
        self.play(FadeOut(text), run_time=0.5)

    def _render_formula(self, scene):
        content = scene.elements[0].content if scene.elements else scene.narration or "E = mc²"
        # Use Text (no LaTeX) - MathTex requires latex to be installed
        display = content.replace("\\frac{1}{2}", "½").replace("^2", "²").replace("^", "")
        formula = Text(display, font_size=48)
        self.play(Write(formula), run_time=1.5)
        self.wait(scene.duration_seconds - 1.5)
        self.play(FadeOut(formula), run_time=0.5)

    def _render_flow(self, scene):
        nodes = scene.nodes or []
        edges = scene.edges or []
        if not nodes:
            text = Text("Flow diagram (no nodes)", font_size=24)
            self.play(FadeIn(text), run_time=1)
            self.wait(scene.duration_seconds - 1)
            self.play(FadeOut(text), run_time=0.5)
            return
        # Build graph from nodes/edges
        vertices = [n.id for n in nodes]
        edge_list = [(e.source, e.target) for e in edges]
        labels = {n.id: n.label for n in nodes}
        try:
            from manim import Graph

            g = Graph(
                vertices,
                edge_list,
                labels=labels,
                layout="circular",
                layout_scale=2.5,
            )
            self.play(Create(g), run_time=2)
        except Exception:
            g = VGroup(*[Text(f"{n.id}: {n.label}", font_size=20) for n in nodes])
            g.arrange_in_grid(rows=2)
            self.play(FadeIn(g), run_time=1.5)
        self.wait(max(0, scene.duration_seconds - 2))
        self.play(FadeOut(g), run_time=0.5)

    def _render_diagram(self, scene):
        # Simple diagram: render elements as labeled shapes
        self._render_text(scene)

    def _render_process(self, scene):
        # Process = ordered steps, similar to bullets
        self._render_bullets(scene)

    def _render_transition(self, scene):
        self.wait(scene.duration_seconds)
