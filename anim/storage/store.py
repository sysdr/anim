"""
Persistent storage for generated animations (MP4) and audio (WAV).

- Animations: saved under media/animations/<id>.mp4 with metadata.
- Audio: saved under media/audio/<id>.wav with metadata.
- Index: media/storage_index.json for listing and lookup.
"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Storage:
    """Store and retrieve generated animations and audio by id."""

    INDEX_FILENAME = "storage_index.json"

    def __init__(self, media_root: str | Path = "media"):
        self.media_root = Path(media_root)
        self.animations_dir = self.media_root / "animations"
        self.audio_dir = self.media_root / "audio"
        self._index_path = self.media_root / self.INDEX_FILENAME
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.animations_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, list[dict[str, Any]]]:
        if not self._index_path.exists():
            return {"animations": [], "audio": []}
        try:
            with open(self._index_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"animations": [], "audio": []}

    def _save_index(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.media_root.mkdir(parents=True, exist_ok=True)
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def save_animation(
        self,
        source_path: Path,
        *,
        title: str = "",
        job_id: str | None = None,
        storage_id: str | None = None,
    ) -> str:
        """
        Copy a rendered video into storage and register it.

        Args:
            source_path: Path to the rendered MP4 file.
            title: Display title.
            job_id: Optional job id that produced this animation.
            storage_id: Optional id; if not provided, one is generated.

        Returns:
            Storage id (used in paths and API).
        """
        source_path = Path(source_path)
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Animation file not found: {source_path}")

        sid = storage_id or self._new_id()
        dest = self.animations_dir / f"{sid}.mp4"
        shutil.copy2(source_path, dest)

        index = self._load_index()
        entry = {
            "id": sid,
            "path": dest.relative_to(self.media_root).as_posix(),
            "title": title or source_path.stem,
            "job_id": job_id,
            "size_bytes": dest.stat().st_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Avoid duplicates by id
        index["animations"] = [e for e in index["animations"] if e.get("id") != sid]
        index["animations"].append(entry)
        self._save_index(index)
        return sid

    def save_audio(
        self,
        wav_bytes: bytes,
        *,
        title: str = "",
        script_preview: str | None = None,
        voice: str | None = None,
        storage_id: str | None = None,
    ) -> str:
        """
        Save WAV bytes to storage and register.

        Args:
            wav_bytes: Raw WAV file bytes.
            title: Display title.
            script_preview: Optional first N chars of script for display.
            voice: Optional voice name used for TTS.
            storage_id: Optional id; if not provided, one is generated.

        Returns:
            Storage id.
        """
        sid = storage_id or self._new_id()
        dest = self.audio_dir / f"{sid}.wav"
        dest.write_bytes(wav_bytes)

        index = self._load_index()
        entry = {
            "id": sid,
            "path": dest.relative_to(self.media_root).as_posix(),
            "title": title or "Narration",
            "script_preview": (script_preview or "")[:200],
            "voice": voice,
            "size_bytes": len(wav_bytes),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        index["audio"] = [e for e in index["audio"] if e.get("id") != sid]
        index["audio"].append(entry)
        self._save_index(index)
        return sid

    def list_animations(self) -> list[dict[str, Any]]:
        """List all stored animations (newest first)."""
        index = self._load_index()
        entries = list(index.get("animations", []))
        out = []
        for e in entries:
            path = self.media_root / e.get("path", "")
            if not path.exists():
                continue
            if "size_bytes" not in e:
                e = {**e, "size_bytes": path.stat().st_size}
            if "created_at" not in e:
                e = {**e, "created_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()}
            out.append(e)
        out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return out

    def list_audio(self) -> list[dict[str, Any]]:
        """List all stored audio (newest first)."""
        index = self._load_index()
        entries = list(index.get("audio", []))
        out = []
        for e in entries:
            path = self.media_root / e.get("path", "")
            if not path.exists():
                continue
            if "size_bytes" not in e:
                e = {**e, "size_bytes": path.stat().st_size}
            if "created_at" not in e:
                e = {**e, "created_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()}
            out.append(e)
        out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return out

    def get_animation_path(self, storage_id: str) -> Path | None:
        """Return full path to stored animation file, or None if not found."""
        path = self.animations_dir / f"{storage_id}.mp4"
        return path if path.exists() else None

    def get_audio_path(self, storage_id: str) -> Path | None:
        """Return full path to stored audio file, or None if not found."""
        path = self.audio_dir / f"{storage_id}.wav"
        return path if path.exists() else None

    def delete_animation(self, storage_id: str) -> bool:
        """Remove animation from storage and index. Returns True if removed."""
        path = self.animations_dir / f"{storage_id}.mp4"
        if not path.exists():
            index = self._load_index()
            index["animations"] = [e for e in index.get("animations", []) if e.get("id") != storage_id]
            self._save_index(index)
            return False
        path.unlink()
        index = self._load_index()
        index["animations"] = [e for e in index.get("animations", []) if e.get("id") != storage_id]
        self._save_index(index)
        return True

    def delete_audio(self, storage_id: str) -> bool:
        """Remove audio from storage and index. Returns True if removed."""
        path = self.audio_dir / f"{storage_id}.wav"
        if not path.exists():
            index = self._load_index()
            index["audio"] = [e for e in index.get("audio", []) if e.get("id") != storage_id]
            self._save_index(index)
            return False
        path.unlink()
        index = self._load_index()
        index["audio"] = [e for e in index.get("audio", []) if e.get("id") != storage_id]
        self._save_index(index)
        return True
