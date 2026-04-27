"""Judge Agent - quality and sync checks for blueprint, timeline, script."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from anim.agents.base import BaseAgent


@dataclass
class JudgeResult:
    """Result of JudgeAgent.run: pass/fail and optional feedback."""

    passed: bool
    feedback: list[str]
    metadata: dict[str, Any]


class JudgeAgent(BaseAgent[JudgeResult]):
    """Checks quality and synchronization: narration length vs duration, timeline vs script, etc."""

    name = "judge"

    # Approximate words per second for natural narration
    WORDS_PER_SECOND = 2.5
    MIN_DURATION_PER_STEP = 1.0

    def run(
        self,
        *,
        timeline: list[dict[str, Any]] | None = None,
        full_script: str | None = None,
        target_duration_seconds: float | None = None,
    ) -> JudgeResult:
        """
        Run quality/sync checks.

        Args:
            timeline: List of { id, narration, startTime, duration }.
            full_script: Concatenated narration (for word count).
            target_duration_seconds: Expected total duration (e.g. 90).

        Returns:
            JudgeResult with passed, feedback list, metadata.
        """
        feedback: list[str] = []
        meta: dict[str, Any] = {}

        if timeline:
            total_dur = 0.0
            for step in timeline:
                total_dur += float(step.get("duration", 0))
            meta["timeline_total_duration"] = total_dur
            if target_duration_seconds is not None and total_dur < target_duration_seconds:
                feedback.append(
                    f"Timeline total duration {total_dur:.1f}s is below target {target_duration_seconds}s"
                )

        if full_script:
            words = len(full_script.split())
            meta["script_word_count"] = words
            expected_words = (target_duration_seconds or 90) * self.WORDS_PER_SECOND
            if target_duration_seconds and words < expected_words * 0.8:
                feedback.append(
                    f"Script has {words} words; aim for ~{int(expected_words)} for {target_duration_seconds}s at {self.WORDS_PER_SECOND} w/s"
                )

        passed = len(feedback) == 0
        return JudgeResult(passed=passed, feedback=feedback, metadata=meta)
