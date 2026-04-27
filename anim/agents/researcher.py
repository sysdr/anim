"""Researcher Agent - enrich topic with context (optional LLM/web)."""

from __future__ import annotations

from typing import Any

from anim.agents.base import BaseAgent


class ResearcherAgent(BaseAgent[dict[str, Any]]):
    """Enriches a topic or summary with additional context. Optional; can be no-op or LLM-backed."""

    name = "researcher"

    def run(
        self,
        topic_or_summary: str,
        *,
        max_context_chars: int = 2000,
    ) -> dict[str, Any]:
        """
        Research topic/summary and return enriched context.

        Default implementation returns a minimal structure; override or inject
        an LLM client for real research (e.g. Gemini, web search).

        Returns:
            Dict with keys: summary, context_snippets, references (optional).
        """
        return {
            "summary": topic_or_summary[:max_context_chars].strip(),
            "context_snippets": [],
            "references": [],
            "metadata": {"researched": False},
        }
