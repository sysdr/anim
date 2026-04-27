"""Validators - Blueprint, Timeline, and SVG validation agents."""

from __future__ import annotations

from typing import Any

from anim.agents.base import BaseAgent
from anim.agents.svg_validator import SvgValidationAgent as _SvgValidationAgent
from anim.blueprint.schema import Blueprint


class BlueprintValidatorAgent(BaseAgent[Blueprint]):
    """Validates and optionally fixes a Blueprint (schema, scene ids, durations)."""

    name = "blueprint_validator"

    def run(self, blueprint: Blueprint) -> Blueprint:
        """Validate Blueprint; return as-is or fixed copy. Ensures scene ids unique, durations >= 0."""
        scenes = list(blueprint.scenes)
        seen_ids: set[str] = set()
        fixed = []
        for i, s in enumerate(scenes):
            sid = s.id or f"s{i+1}"
            if sid in seen_ids:
                sid = f"{sid}-{i+1}"
            seen_ids.add(sid)
            dur = max(0.1, s.duration_seconds)
            fixed.append(s.model_copy(update={"id": sid, "duration_seconds": dur}))
        return blueprint.model_copy(update={"scenes": fixed})


class TimelineValidatorAgent(BaseAgent[list[dict[str, Any]]]):
    """Validates timeline list: startTime/duration consistency, ids present."""

    name = "timeline_validator"

    def run(self, timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ensure each step has id, startTime, duration; startTime cumulative."""
        if not timeline:
            return []
        out = []
        t = 0.0
        for i, step in enumerate(timeline):
            step_id = step.get("id") or f"step-{i+1}"
            duration = max(0.5, float(step.get("duration", 3)))
            start_time = float(step.get("startTime", t))
            if start_time < t:
                start_time = t
            t = start_time + duration
            out.append({
                **step,
                "id": step_id,
                "startTime": start_time,
                "duration": duration,
            })
        return out


class SvgValidatorAgent(BaseAgent[str]):
    """Validates and fixes SVG string (security, well-formedness)."""

    name = "svg_validator"

    def __init__(self) -> None:
        self._impl = _SvgValidationAgent()

    def run(self, svg: str) -> str:
        return self._impl.validate_and_fix(svg)
