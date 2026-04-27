"""Analyzer Agent - extract and structure raw input (URL, PDF, text)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anim.agents.base import BaseAgent, StructuredContent
from anim.input.extractor import extract_text


class AnalyzerAgent(BaseAgent[StructuredContent]):
    """Extracts text from URL/PDF/plain text and produces structured content (title, bullets, raw)."""

    name = "analyzer"

    def run(
        self,
        source: str | Path,
        *,
        max_bullets: int = 50,
    ) -> StructuredContent:
        """
        Analyze source (URL, PDF path, or raw text) into StructuredContent.

        Args:
            source: URL string, path to PDF, or plain text.
            max_bullets: Maximum number of bullet lines to keep.

        Returns:
            StructuredContent with title, sections, bullets, raw_text.
        """
        raw = extract_text(source)
        raw_text = raw.strip()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        title = lines[0] if lines else "Untitled"
        bullets = lines[1:max_bullets] if len(lines) > 1 else []

        # Simple sectioning: treat double-newline as section break
        sections: list[dict[str, Any]] = []
        current: list[str] = []
        for line in lines:
            if not line:
                if current:
                    sections.append({"heading": current[0] if current else "", "lines": current[1:]})
                    current = []
            else:
                current.append(line)
        if current:
            sections.append({"heading": current[0] if current else "", "lines": current[1:]})

        return StructuredContent(
            title=title,
            sections=sections,
            bullets=bullets,
            raw_text=raw_text,
            metadata={"source": str(source)[:200], "line_count": len(lines)},
        )
