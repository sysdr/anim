"""Base agent protocol and types for SynapseFlow agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

# --- Common artifact types (structured data between agents) ---

T = TypeVar("T")


@dataclass
class StructuredContent:
    """Output of Analyzer: extracted title, sections, bullets, raw text."""

    title: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Output of Exporter: path, URL, format."""

    path: str
    url: str = ""
    format: str = "mp4"
    storage_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC, Generic[T]):
    """Base for all SynapseFlow agents. Subclasses define run() with typed inputs/outputs."""

    name: str = "base"

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> T:
        """Execute the agent; return typed result."""
        ...
