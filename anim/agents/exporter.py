"""Exporter Agent - export rendered video/blueprint to storage and return URLs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anim.agents.base import BaseAgent, ExportResult


class ExporterAgent(BaseAgent[ExportResult]):
    """Copies rendered output to storage (if available) and returns path/URL."""

    name = "exporter"

    def __init__(self, storage: Any = None) -> None:
        """
        Args:
            storage: Optional anim.storage.Storage instance for persistent save.
                     If None, only path is returned (no storage_id/url from storage).
        """
        self._storage = storage

    def run(
        self,
        source_path: Path | str,
        *,
        output_dir: Path | str = "media",
        title: str = "",
        job_id: str | None = None,
    ) -> ExportResult:
        """
        Export a rendered file (e.g. MP4) to storage and return path/URL.

        Args:
            source_path: Path to the rendered file.
            output_dir: Media root (used if storage not configured).
            title: Display title for storage index.
            job_id: Optional job id that produced this file.

        Returns:
            ExportResult with path, url, storage_id (if storage used).
        """
        source_path = Path(source_path)
        if not source_path.exists() or not source_path.is_file():
            return ExportResult(
                path=str(source_path),
                url="",
                format=source_path.suffix.lstrip(".") or "mp4",
                metadata={"error": "file not found"},
            )

        fmt = source_path.suffix.lstrip(".") or "mp4"
        path_str = str(source_path)
        url = ""
        storage_id = None

        if self._storage is not None:
            try:
                storage_id = self._storage.save_animation(
                    source_path,
                    title=title or source_path.stem,
                    job_id=job_id,
                )
                url = f"/media/animations/{storage_id}.mp4"
                path_str = str(self._storage.get_animation_path(storage_id) or source_path)
            except Exception as e:
                path_str = str(source_path)
                if "media" in path_str:
                    idx = path_str.rfind("media") + len("media") + 1
                    url = f"/media/{path_str[idx:]}"
        else:
            output_dir = Path(output_dir)
            try:
                rel = source_path.relative_to(output_dir)
                url = f"/media/{rel.as_posix()}"
            except ValueError:
                url = f"/media/{source_path.name}"

        return ExportResult(
            path=path_str,
            url=url,
            format=fmt,
            storage_id=storage_id,
            metadata={"title": title, "job_id": job_id},
        )
