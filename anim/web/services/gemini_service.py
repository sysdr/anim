"""Gemini API service for Studio SVG + script generation and TTS narration."""

from __future__ import annotations

import base64
import io
import json
import logging
import re
import struct
import time
from typing import Any

from anim.agents.svg_validator import SvgValidationAgent

logger = logging.getLogger(__name__)

# Aspect ratio -> (width, height) for viewBox
_VIEWBOX_BY_RATIO = {
    "16:9": (960, 540),
    "9:16": (540, 960),
    "1:1": (540, 540),
}

# YouTube multi-ratio safe zone: (x, y, width, height) — region visible when frame is
# center-cropped to all three aspect ratios (16:9, 9:16, 1:1). Keep titles and key text here.
_SAFE_ZONE_BY_RATIO = {
    "16:9": (328, 0, 304, 540),   # center horizontal strip (9:16 and 1:1 crop intersect)
    "9:16": (0, 328, 540, 304),   # center vertical strip
    "1:1": (118, 118, 304, 304),  # center square
}

# Edge margin (px) for general content; safe zone is stricter for critical text.
_EDGE_MARGIN_PX = 50

# Minimum total animation duration (seconds). Narrations should be written to fill this when spoken at ~2.5 words/sec.
MIN_ANIMATION_DURATION_SECONDS = 90
# Approximate words per second for natural narration; total words ≈ MIN_ANIMATION_DURATION_SECONDS * WORDS_PER_SECOND.
WORDS_PER_SECOND_NARRATION = 2.5


def _safe_zone_description(aspect_ratio: str) -> str:
    """Human-readable safe zone for prompts (title/key text placement)."""
    w, h = _VIEWBOX_BY_RATIO.get(aspect_ratio, (960, 540))
    sz = _SAFE_ZONE_BY_RATIO.get(aspect_ratio, (328, 0, 304, 540))
    x, y, sw, sh = sz
    return (
        f"for {aspect_ratio} (viewBox 0 0 {w} {h}): "
        f"keep titles and key labels inside the rectangle x={x}-{x + sw}, y={y}-{y + sh} "
        f"(center safe zone for 16:9, 9:16, and 1:1 YouTube capture)."
    )

# --- Cinematic Animation Design (Animated-Movie Style) ---
# Real-world entities, complex workflows with distinct parts, ultra-scalable systems.
# Used to generate SVG + timeline + full_script from workflow steps or description text.

ARCHITECT_SVG_SYSTEM_PROMPT_TEMPLATE = r"""Act as a Lead Motion Graphics Engineer, Visual Effects Artist, and Technical Architect for **cinematic animated-movie-style** explainers. Your mission is to generate a *breathtakingly beautiful*, high-fidelity, sequential, animated SVG visualization of: {{CONCEPT}}.

### 1. CINEMATIC DESIGN (ANIMATED MOVIES — PIXAR/APPLE QUALITY)
- **Story beats:** Structure the visualization like a short film: (1) **Establishing shot** — wide view of the whole system, (2) **Reveals** — zoom or pan into distinct parts one by one, (3) **Callouts** — highlight the active component during each step, (4) **Flow** — show data/materials moving through real-world metaphors (conveyors, pipes, streams).
- **Narrative rhythm:** Each step = one clear "moment": something enters, transforms, or exits. Avoid flat diagrams; create a sense of depth, layers, and motion.
- **Transitions:** Use subtle entrances (fade-in + scale-up + slight translateY) and keep previous steps visible so the audience sees the full picture build.

### 2. REAL-WORLD ENTITIES (NOT ABSTRACT BOXES)
- **Metaphors:** Represent components as real-world things the audience recognizes:
  - Data/system flows: **pipelines**, **conveyor belts**, **rivers**, **highways**, **railways**
  - Processing: **factories**, **refineries**, **assembly lines**, **kitchens**
  - Storage: **warehouses**, **silos**, **reservoirs**, **vaults**
  - Scale/compute: **server racks**, **power plants**, **hives**, **organisms** (cells, organs)
- **Visual language:** Use shapes that suggest these (rounded tanks, rectangular buildings, flowing paths, clusters of units). Add simple icons or silhouettes (e.g. gears, drops, boxes) where helpful. Labels stay readable; avoid clutter.

### 3. COMPLEX WORKFLOW — DISTINCT PARTS
- **Deconstruct** the process into **distinct subsystems (parts)** — e.g. Ingestion, Processing, Storage, Delivery, or Request → Queue → Workers → Cache → Response.
- **At least 10–15 steps**, each tied to one clear part. Show how data or material moves **between** parts (arrows, flowing paths, dashed "in transit" lines). Include **realtime concerns** where relevant: latency, backpressure, failure modes, consistency; and **complex architecture** aspects: multi-region, event-sourced, CQRS, replication, sharding.
- **Parallel vs sequential:** If the system has fan-out, replication, or sharding, show multiple similar units (e.g. several worker nodes, multiple pipelines) so it reads as **ultra scalable**.

### 4. PREMIUM VISUAL DESIGN (CRITICAL — THIS IS WHAT MAKES IT 100x BEAUTIFUL)

#### 4A. GOOGLE FONTS (MANDATORY)
Inside your SVG <defs>, include a <style> block that imports Google Fonts:
```
<defs>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&amp;family=Space+Grotesk:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap');
  </style>
</defs>
```
- Use **Inter** or **Space Grotesk** (font-weight 600-700) for titles and section headers.
- Use **Inter** (font-weight 400-500) for body text, labels, and narration overlays.
- Use **JetBrains Mono** for code snippets, numeric values, and technical identifiers.
- Always set letter-spacing: -0.01em on headings for a tight, modern look.
- Use text-anchor="middle" for centered labels. Ensure dominant-baseline="central" for vertical centering.

#### 4B. SVG FILTER EFFECTS (MANDATORY — USE THESE FOR VISUAL RICHNESS)
Define these filters in <defs> and apply them to create depth and glow:

**Soft drop shadow** (apply to all node cards/panels):
```
<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#000" flood-opacity="0.3"/>
</filter>
```

**Neon glow** (apply to active/highlighted elements and accent lines):
```
<filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur1"/>
  <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur2"/>
  <feMerge>
    <feMergeNode in="blur2"/>
    <feMergeNode in="blur1"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
```

**Subtle inner glow** (for containers/panels):
```
<filter id="innerGlow" x="-10%" y="-10%" width="120%" height="120%">
  <feGaussianBlur in="SourceAlpha" stdDeviation="4" result="blur"/>
  <feComposite in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1" result="glow"/>
  <feFlood flood-color="var(--accent-primary)" flood-opacity="0.15"/>
  <feComposite in2="glow" operator="in"/>
  <feMerge>
    <feMergeNode/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
```

#### 4C. GRADIENTS (MANDATORY — NO FLAT FILLS)
- **Background:** Use a rich radial or linear gradient, NOT a flat color. Example:
  ```
  <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#0a0a1a"/>
    <stop offset="50%" stop-color="#0f1029"/>
    <stop offset="100%" stop-color="#080818"/>
  </linearGradient>
  ```
- **Node cards:** Use subtle gradient fills (slightly lighter at top, darker at bottom) with rounded corners (rx="12").
- **Accent lines/paths:** Use linearGradient fills on connector paths for a "flowing energy" look:
  ```
  <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="var(--accent-primary)" stop-opacity="0.3"/>
    <stop offset="50%" stop-color="var(--accent-primary)" stop-opacity="1"/>
    <stop offset="100%" stop-color="var(--accent-primary)" stop-opacity="0.3"/>
  </linearGradient>
  ```
- **Animated gradient on key connectors:** Use SMIL to animate stop-colors for a living, breathing feel:
  ```
  <stop offset="0%">
    <animate attributeName="stop-color" values="#6366f1;#d946ef;#6366f1" dur="4s" repeatCount="indefinite"/>
  </stop>
  ```

#### 4D. GLASSMORPHISM PANELS (RECOMMENDED FOR NODE CARDS)
- Node cards should have a frosted-glass appearance:
  - `fill="rgba(255,255,255,0.04)"` (or `rgba(255,255,255,0.06)` for emphasis)
  - `stroke="rgba(255,255,255,0.08)"`  with `stroke-width="1"`
  - `rx="12"` for rounded corners
  - Apply `filter="url(#softShadow)"`
  - Add a thin bright line at the top edge: `<line ... stroke="rgba(255,255,255,0.12)" stroke-width="1"/>`

#### 4E. COLOR PALETTE (DEEP, RICH, CINEMATIC)
Use a sophisticated color system:
- **Background:** Deep indigo-black (`#0a0a1a` → `#0f1029` → `#080818`)
- **Node fill:** Semi-transparent (`rgba(255,255,255,0.04)`)
- **Borders:** Subtle white (`rgba(255,255,255,0.08)`)
- **Primary text:** Bright (`#e2e8f0` or `#f0f0f5`)
- **Muted text:** (`#94a3b8`)
- **Accent palette:** Use 2-3 accent colors that form a gradient family:
  - Primary accent: indigo-blue (`#6366f1`)
  - Secondary accent: violet (`#8b5cf6`)
  - Tertiary accent: magenta-pink (`#d946ef`)
  - Success/flow: cyan (`#06d6a0` or `#00d4ff`)
- **Status colors:** Green for active, amber for pending, red for error states.
- Override all above with CSS variables: var(--bg-canvas), var(--text-primary), var(--accent-primary), var(--border-dim), var(--node-bg).

#### 4F. MICRO-ANIMATIONS (LIFE AND POLISH)
Beyond basic SMIL entrance, add these subtle animations to make it feel *alive*:
- **Floating particles/dots** in the background (small circles with slow translateY animation, looping)
- **Pulsing rings** on active nodes (circle with expanding radius + fading opacity)
- **Flowing dashes on connectors** with smooth stroke-dashoffset animation
- **Gentle scale breathing** on key icons (values="1;1.03;1" dur="3s" repeatCount="indefinite")
- **Gradient color cycling** on accent elements (animate stop-color values)
- **Staggered entrance:** Don't just fade in — combine opacity 0→1 with translateY(10)→translateY(0) for each node group entrance. Use calcMode="spline" keySplines="0.16 1 0.3 1" for an ease-out-expo feel.

### 5. VISIBILITY & STRUCTURE (CRITICAL)
- **Standalone SVG:** Complete, valid <svg> with viewBox="0 0 {{WIDTH}} {{HEIGHT}}". First element: background rect with gradient fill.
- **Styling:** Use CSS variables (--bg-canvas, --text-primary, --accent-primary, --border-dim, --node-bg, --panel-bg, --svg-font, --svg-font-size) so the frontend can override.
- **Edge margin:** All content at least {{EDGE_MARGIN}}px from edges. Space nodes so paths are clear and non-overlapping ({{RATIO_NAME}}).
- **YouTube multi-ratio (16:9, 9:16, 1:1):** Place titles and key labels inside the **title-safe zone** so the same design stays readable when captured for landscape, portrait, or square. {{SAFE_ZONE_DESC}}

### 6. ANIMATION SPECS (SMIL — SMOOTH & PROFESSIONAL)
- **Entrance:** Combine opacity fade + translateY for a smooth slide-up entrance:
  ```
  <animate attributeName="opacity" from="0" to="1" dur="0.6s" begin="[startTime]s" fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1"/>
  <animateTransform attributeName="transform" type="translate" from="0 15" to="0 0" dur="0.6s" begin="[startTime]s" fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1"/>
  ```
- **Data flow (connectors):** stroke-dasharray="8,4" and animated stroke-dashoffset with smooth timing.
- **Pulse (active step):** <animateTransform type="scale" values="1;1.04;1" dur="2.5s" repeatCount="indefinite" additive="sum" begin="[startTime]s" end="[startTime+duration]s" calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>.
- **Connector glow pulse:** On active connectors, animate filter opacity or stroke-opacity for a breathing glow.

### 7. INTERACTIVITY & IDs (CRITICAL)
- **One group per step:** All visual elements for a timeline step in a single <g id="node-{id}" class="interactive-node" opacity="0">. {id} matches the timeline id (e.g. node-step-1).

### 8. OUTPUT SCHEMA (JSON ONLY)
1. svg_source: Complete SVG (root id="root").
2. timeline: [ { "id", "label", "narration", "startTime", "duration" } ].
3. full_script: Concatenated narration for TTS. Also voiceover_script: same as full_script.

### 9. SYNCHRONIZATION (CRITICAL)
- **Total animation MUST be at least 90 seconds.** Per-step duration_seconds = max(2, word_count / 2.5). Step 1 startTime=0; Step N+1 startTime = Step N startTime + Step N duration. If the sum of step durations is below 90 seconds, write longer narrations (more words per step) so that the total timeline duration reaches at least 90 seconds.
- **Narration length:** The full_script (and each step's narration) must be written so that when spoken at natural pace (~2.5 words/second), the **entire voiceover lasts approximately 90 seconds** — i.e. aim for roughly 220–250 words total across all steps. Each step's narration should be substantive (full sentences, not one-liners).
- timeline[].startTime MUST match the begin attribute for that step in the SVG. No large gaps.

Output ONLY valid JSON. No markdown, no code fences.
"""

# --- Studio: Cinematic + Complex Workflow + Real-World Entities ---

STUDIO_ARCHITECT_PROMPT_TEMPLATE = r"""You are a Technology Architect, Lead Motion Graphics Engineer, and Visual Effects Artist for **breathtakingly beautiful animated-movie-style** explainers (think Pixar + Apple keynote quality). The user will give you: (1) a topic, (2) topic and description, (3) description only, (4) a detailed article, or (5) explicit workflow steps. Your job is to design a **complex workflow** with **distinct parts**, **real-world entities**, and **ultra-scalable** concepts, then visualize it cinematically with **stunning visual polish**.

### PHASE 1 — INTERPRET & ARCHITECT (COMPLEX WORKFLOW)
- **Interpret** the input type: topic, topic+description, description_only, article, workflow_steps, realtime_system, distributed_system, or high_throughput.
- **Break down** the subject into a clear system with **distinct subsystems (parts)** — e.g. Ingestion → Processing → Storage → Delivery, or Request → Queue → Workers → Cache → Response. Think: layers, tiers, pipelines. Where relevant, include **realtime issues** (latency, backpressure, failure handling, consistency) and **complex architecture** (multi-region, event-sourced, CQRS, replication, sharding).
- **Produce a workflow_spec** (JSON) with these keys:
  - title: string
  - summary: string (2–4 sentences)
  - input_type: string (one of: "topic", "topic_and_description", "description_only", "article", "workflow_steps", "realtime_system", "distributed_system", "high_throughput", "event_driven")
  - **acts**: array of { id, title, summary, narrative_beat, step_ids } — cinematic acts/chapters (e.g. "Establishing", "Ingestion", "Processing", "Scale-out", "Failure modes"). narrative_beat one of: "establishing", "build", "conflict", "resolution", "scale".
  - **parts**: array of { id, name, description, responsibility, scale_hint, step_ids } — **distinct workflow parts** (subsystems). scale_hint e.g. "replicated", "sharded", "fan-out", "queue-backed".
  - **entity_metaphors**: array of { id, name, metaphor, description } — how to draw key entities (e.g. metaphor: "pipeline", "warehouse", "conveyor", "server_rack", "organism").
  - **scale_indicators**: array of { part_id, indicator } — how scalability is shown.
  - **realtime_issues**: array of { id, name, description, mitigation } — e.g. latency, backpressure, partial failure, consistency, clock skew. Include where the topic involves real-time or distributed systems.
  - **architecture_style**: string or array — e.g. "event-driven", "CQRS", "multi-region", "event-sourced", "microservices", "stream-processing". Enriches the narrative.
  - actors: array of { id, name, role, description }
  - entities: array of { id, name, type, description }
  - components: array of { id, name, responsibility, description }
  - communication: array of { from_id, to_id, payload_or_event, description }
  - state_transitions: array of { from_state, to_state, trigger, description }
  - steps: array of { id, label, narration, description, part_id? } — **10–18 steps** with rich detail. part_id links to parts[].id. **Narration** = full voiceover sentences (each step ~15–25 words so total script is ~220–250+ words for a 90-second video).

Use stable IDs (actor-1, part-ingestion, entity-order) so communication and acts/parts reference them.

### PHASE 2 — VISUALIZE (CINEMATIC + STUNNING VISUALS + ULTRA-SCALABLE)
Generate SVG and timeline from workflow_spec using **animated-movie** and **real-world** design:

1. **Cinematic:** (1) Establishing shot — wide view of full system. (2) Reveals — each major part appears in sequence. (3) Callouts — pulse/highlight the active step. (4) Flow — show movement (conveyors, pipes, streams) between parts.
2. **Real-world entities:** Draw components as recognizable metaphors — pipelines, conveyor belts, warehouses, server racks, factories, organisms — not generic boxes. Use suggestive shapes and simple icons.
3. **Distinct parts:** Visually group or label each subsystem (part). Show data/material moving **between** parts. For scale_hint "replicated" or "fan-out", draw multiple similar units (e.g. several workers, parallel pipelines).

#### PREMIUM VISUAL DESIGN (THIS IS WHAT MAKES IT 100x BEAUTIFUL — MANDATORY):

4. **Google Fonts (MANDATORY):** Inside SVG <defs>, include:
   ```
   <style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&amp;family=Space+Grotesk:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap');</style>
   ```
   - Use **Space Grotesk** (700) for titles, **Inter** (400-600) for labels, **JetBrains Mono** for technical values.
   - Set letter-spacing="-0.01em" on headings. Use text-anchor="middle" for centered text.

5. **SVG Filters (MANDATORY — define in <defs>):**
   - **softShadow:** `<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#000" flood-opacity="0.3"/></filter>` — apply to all node cards
   - **neonGlow:** `<filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b1"/><feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/><feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge></filter>` — apply to accent lines and active highlights
   - **subtleGlow:** `<filter id="subtleGlow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>` — apply to icons and small accent elements

6. **Gradients (MANDATORY — NO flat single-color fills):**
   - **Background:** Rich multi-stop gradient, NOT flat: `<linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0a0a1a"/><stop offset="50%" stop-color="#0f1029"/><stop offset="100%" stop-color="#080818"/></linearGradient>` — use as fill on the background rect.
   - **Node cards:** Subtle glass gradient: `<linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="rgba(255,255,255,0.06)"/><stop offset="100%" stop-color="rgba(255,255,255,0.02)"/></linearGradient>`
   - **Accent connector paths:** Use gradient strokes that fade in/out: `<linearGradient id="flowGrad"><stop offset="0%" stop-color="var(--accent-primary)" stop-opacity="0.2"/><stop offset="50%" stop-color="var(--accent-primary)" stop-opacity="1"/><stop offset="100%" stop-color="var(--accent-primary)" stop-opacity="0.2"/></linearGradient>`
   - **Animated gradient on key elements:** SMIL animate stop-color values for a living, breathing effect.

7. **Glassmorphism Node Cards:**
   - `fill="rgba(255,255,255,0.04)"` + `stroke="rgba(255,255,255,0.08)"` + `rx="12"` + `filter="url(#softShadow)"`
   - Add a thin bright highlight line at the card top edge: `stroke="rgba(255,255,255,0.15)"`
   - Group label above card in accent color with `filter="url(#subtleGlow)"`

8. **Rich Color Palette:**
   - Deep background: `#0a0a1a` → `#0f1029` → `#080818`
   - Primary accent: `#6366f1` (indigo), Secondary: `#8b5cf6` (violet), Tertiary: `#d946ef` (pink)
   - Flow/success: `#06d6a0` or `#00d4ff`
   - All overridden by CSS vars: var(--bg-canvas), var(--text-primary), var(--accent-primary), var(--border-dim), var(--node-bg)

9. **Micro-animations for life:**
   - Small floating particles/dots in background (circles with slow looping translateY)
   - Pulsing rings on active nodes (expanding circle + fading opacity)
   - Flowing dashes on connector paths (smooth stroke-dashoffset animation)
   - Gentle breathing scale on icons (values="1;1.03;1" dur="3s" repeatCount="indefinite")
   - Gradient color cycling on accent elements

10. **Structure:** <svg> viewBox="0 0 {{WIDTH}} {{HEIGHT}}". Root id="root". Stroke/fill uses CSS variables. Labels fill="var(--text-primary)", font-size ≥14px. Margin {{EDGE_MARGIN}}px from edges. **YouTube multi-ratio:** Keep titles and key labels inside the title-safe zone: {{SAFE_ZONE_DESC}}

11. **SMIL Animations (SMOOTH — use spline easing):**
    - **Entrance:** Combine opacity fade + translateY slide-up:
      `<animate attributeName="opacity" from="0" to="1" dur="0.6s" begin="[startTime]s" fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1"/>`
      `<animateTransform attributeName="transform" type="translate" from="0 12" to="0 0" dur="0.6s" begin="[startTime]s" fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1"/>`
    - **Connectors:** stroke-dasharray="8,4" + animated stroke-dashoffset.
    - **Active pulse:** `<animateTransform type="scale" values="1;1.04;1" dur="2.5s" repeatCount="indefinite" additive="sum" calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>`
12. **Interactive nodes:** One `<g id="node-{id}" class="interactive-node" opacity="0">` per timeline step; {id} matches timeline id.
13. **Sync & duration (CRITICAL):** **Total animation MUST be at least {{TARGET_DURATION_SECONDS}} seconds.** Per-step duration = max(2, word_count / 2.5). Step 1 startTime=0; Step N+1 startTime = Step N startTime + Step N duration. If the sum of step durations is below {{TARGET_DURATION_SECONDS}}, write longer narrations so the total timeline reaches at least {{TARGET_DURATION_SECONDS}} seconds. **Narration:** full_script must be long enough that when spoken at ~2.5 words/second it lasts **approximately {{TARGET_DURATION_SECONDS}} seconds** (aim for ~{{TARGET_WORDS}} words total). Each step's narration = substantive sentences, not one-liners. timeline[].startTime = SVG begin for that step. No gaps.

### OUTPUT SCHEMA (JSON ONLY)
Return a single JSON object with:
1. workflow_spec: Phase 1 object (title, summary, input_type, acts, parts, entity_metaphors, scale_indicators, realtime_issues, architecture_style, actors, entities, components, communication, state_transitions, steps).
2. svg_source: complete SVG (root id="root").
3. timeline: [ { "id", "label", "narration", "startTime", "duration" } ].
4. full_script: concatenated narration for TTS (long enough for ~{{TARGET_DURATION_SECONDS}}s when spoken).
5. voiceover_script: same as full_script.

Output ONLY valid JSON. No markdown, no code fences.

USER INPUT:
---
{{USER_INPUT}}
---
"""

# Legacy/concept-only prompt: use ArchitectSVG design (same as ARCHITECT_SVG_SYSTEM_PROMPT_TEMPLATE).
WORKFLOW_PROMPT_TEMPLATE = ARCHITECT_SVG_SYSTEM_PROMPT_TEMPLATE


def generate_svg_animation_from_workflow(
    workflow_steps_or_description: str,
    aspect_ratio: str = "16:9",
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Generate SVG animation from workflow steps or description text using the
    ArchitectSVG design (State-Machine Visualization, SMIL, synchronized timeline).
    Returns {svg_source, voiceover_script, timeline}.
    """
    return generate_svg_and_script(
        concept=workflow_steps_or_description.strip(),
        aspect_ratio=aspect_ratio,
        api_key=api_key,
    )


def generate_svg_and_script(
    concept: str,
    aspect_ratio: str = "16:9",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Call Gemini to generate SVG + timeline + script. Returns {svg_source, voiceover_script, timeline?}."""
    import os

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add to .env or pass api_key.")

    width, height = _VIEWBOX_BY_RATIO.get(aspect_ratio, (960, 540))
    ratio_name = aspect_ratio.replace(":", "×")
    prompt = WORKFLOW_PROMPT_TEMPLATE.replace("{{CONCEPT}}", concept)
    prompt = prompt.replace("{{WIDTH}}", str(width))
    prompt = prompt.replace("{{HEIGHT}}", str(height))
    prompt = prompt.replace("{{WIDTH_INNER}}", str(width - 60))
    prompt = prompt.replace("{{HEIGHT_INNER}}", str(height - 60))
    prompt = prompt.replace("{{RATIO_NAME}}", ratio_name)
    prompt = prompt.replace("{{SAFE_ZONE_DESC}}", _safe_zone_description(aspect_ratio))
    prompt = prompt.replace("{{EDGE_MARGIN}}", str(_EDGE_MARGIN_PX))

    model_name = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name,
            system_instruction="You output only valid JSON. No markdown, no code fences.",
        )
    except ImportError:
        raise ImportError("Install: pip install google-generativeai") from None

    last_err = None
    for attempt in range(3):
        try:
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": 0.6, "max_output_tokens": 32768},
            )
            text = resp.text.strip()
            # Extract JSON (handle markdown code blocks)
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if json_match:
                text = json_match.group(1).strip()
            data = json.loads(text)
            svg = data.get("svg_source", "")
            script = (
                data.get("voiceover_script")
                or data.get("full_script")
                or _script_from_timeline(data.get("timeline", []))
            )
            if not svg:
                raise ValueError("Missing svg_source in response")
            if not script:
                raise ValueError("Missing voiceover_script, full_script, or timeline in response")
            result = SvgValidationAgent().validate_and_fix_with_report(svg)
            svg = result.svg
            if result.errors_found or result.fixes_applied:
                logger.info(
                    "SVG validation: errors_found=%s fixes_applied=%s parse_failed=%s",
                    result.errors_found,
                    result.fixes_applied,
                    result.parse_failed,
                )
            out = {"svg_source": svg, "voiceover_script": script}
            if data.get("timeline"):
                out["timeline"] = data["timeline"]
            return out
        except (json.JSONDecodeError, ValueError, Exception) as e:
            last_err = e
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"Gemini generation failed: {last_err}") from last_err


def generate_svg_and_script_with_workflow(
    user_input: str,
    aspect_ratio: str = "16:9",
    api_key: str | None = None,
    target_duration_seconds: float | None = None,
) -> dict[str, Any]:
    """
    Accept any Studio input (topic, topic+description, description, article, or workflow steps).
    Think as Technology Architect: research, break down, build workflow_spec (actors, entities,
    components, communication, state_transitions, steps, realtime_issues, architecture_style),
    then generate SVG + timeline + script. Animation and narration target at least target_duration_seconds.
    Returns dict with workflow_spec, svg_source, voiceover_script, timeline.
    """
    import os

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add to .env or pass api_key.")

    duration = target_duration_seconds if target_duration_seconds is not None else MIN_ANIMATION_DURATION_SECONDS
    target_words = int(duration * WORDS_PER_SECOND_NARRATION)

    width, height = _VIEWBOX_BY_RATIO.get(aspect_ratio, (960, 540))
    prompt = STUDIO_ARCHITECT_PROMPT_TEMPLATE.replace("{{USER_INPUT}}", user_input.strip())
    prompt = prompt.replace("{{WIDTH}}", str(width))
    prompt = prompt.replace("{{HEIGHT}}", str(height))
    prompt = prompt.replace("{{WIDTH_INNER}}", str(width - 60))
    prompt = prompt.replace("{{HEIGHT_INNER}}", str(height - 60))
    prompt = prompt.replace("{{SAFE_ZONE_DESC}}", _safe_zone_description(aspect_ratio))
    prompt = prompt.replace("{{EDGE_MARGIN}}", str(_EDGE_MARGIN_PX))
    prompt = prompt.replace("{{TARGET_DURATION_SECONDS}}", str(int(duration)))
    prompt = prompt.replace("{{TARGET_WORDS}}", str(target_words))

    model_name = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name,
            system_instruction="You output only valid JSON. No markdown, no code fences.",
        )
    except ImportError:
        raise ImportError("Install: pip install google-generativeai") from None

    last_err = None
    for attempt in range(3):
        try:
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": 0.5, "max_output_tokens": 32768},
            )
            text = resp.text.strip()
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if json_match:
                text = json_match.group(1).strip()
            data = json.loads(text)

            workflow_spec = data.get("workflow_spec") or {}
            svg = data.get("svg_source", "")
            script = (
                data.get("voiceover_script")
                or data.get("full_script")
                or _script_from_timeline(data.get("timeline", []))
            )
            if not svg:
                raise ValueError("Missing svg_source in response")
            if not script:
                raise ValueError("Missing voiceover_script, full_script, or timeline in response")

            timeline_list = data.get("timeline") or []
            if timeline_list:
                svg = _ensure_step_visibility_animations(svg, timeline_list)
            result = SvgValidationAgent().validate_and_fix_with_report(svg)
            svg = result.svg
            if result.errors_found or result.fixes_applied:
                logger.info(
                    "SVG validation: errors_found=%s fixes_applied=%s parse_failed=%s",
                    result.errors_found,
                    result.fixes_applied,
                    result.parse_failed,
                )
            out = {
                "workflow_spec": workflow_spec,
                "svg_source": svg,
                "voiceover_script": script,
            }
            if timeline_list:
                out["timeline"] = timeline_list
            return out
        except (json.JSONDecodeError, ValueError, Exception) as e:
            last_err = e
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"Studio architect generation failed: {last_err}") from last_err


def _script_from_timeline(timeline: list[dict]) -> str:
    """Build full narration script from timeline array."""
    if not timeline:
        return ""
    parts = []
    for step in timeline:
        n = step.get("narration") or step.get("label") or ""
        if n:
            parts.append(n.strip())
    return " ".join(parts)


def _ensure_step_visibility_animations(svg: str, timeline: list[dict]) -> str:
    """
    Ensure each step in the SVG appears as a state change: groups with id="node-{id}"
    get opacity 0 -> 1 animation at begin="{startTime}s" so steps appear in sequence.
    """
    if not timeline or not svg.strip():
        return svg
    # Build map: step id -> startTime (and duration for optional end)
    step_times: dict[str, tuple[float, float]] = {}
    for i, step in enumerate(timeline):
        step_id = str(step.get("id") or f"step-{i + 1}").strip()
        start = float(step.get("startTime", 0))
        duration = float(step.get("duration", 3))
        step_times[step_id] = (start, duration)

    def inject_opacity_animate(match: re.Match) -> str:
        full = match.group(0)
        g_open = match.group(1)
        node_id = match.group(2)
        if node_id.startswith("node-"):
            node_id = node_id[5:]
        start_time, _duration = step_times.get(node_id, (0, 3))
        # Skip if the next 300 chars already contain an opacity animate (model added one)
        start_idx = match.end()
        if start_idx + 300 <= len(svg) and (
            'attributeName="opacity"' in svg[start_idx : start_idx + 300]
            or "attributeName='opacity'" in svg[start_idx : start_idx + 300]
        ):
            return full
        animate = (
            f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" '
            f'begin="{start_time}s" fill="freeze"/>'
        )
        return g_open + animate

    # Match <g id="node-step-1" or <g id='node-step-1' ...> (with possible other attrs)
    pattern = re.compile(
        r'(<g\s+id=["\']node-([^"\']+)["\'][^>]*>)',
        re.IGNORECASE,
    )
    return pattern.sub(inject_opacity_animate, svg)


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    """Wrap raw PCM (s16le) in a WAV header for browser playback."""
    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(pcm_data)))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, sample_rate * channels * 2, channels * 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", len(pcm_data)))
    buf.write(pcm_data)
    return buf.getvalue()


def generate_audio(text: str, voice: str = "Kore", api_key: str | None = None) -> str:
    """Generate TTS audio via Gemini 2.5 Flash TTS. Returns base64-encoded WAV."""
    import os

    text = (text or "").strip()
    if not text:
        raise ValueError("No text provided for narration.")

    # Gemini TTS has input length limits; truncate very long scripts to avoid errors
    max_chars = 5000
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add to .env or pass api_key.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise ImportError("Narration requires google-genai. Install: pip install google-genai") from e

    client = genai.Client(api_key=api_key)
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=f"Say clearly and naturally: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice),
                        )
                    ),
                ),
            )
            if not response.candidates:
                feedback = getattr(response, "prompt_feedback", None)
                if feedback and getattr(feedback, "block_reason", None):
                    reason = str(getattr(feedback, "block_reason", ""))
                    raise ValueError(f"Request blocked: {reason}. Try shorter or different text.")
                raise ValueError(
                    "Gemini returned no candidates. The TTS model may be unavailable, "
                    "rate-limited, or the request was blocked. Try again in a moment."
                )
            content = response.candidates[0].content
            if not content or not getattr(content, "parts", None) or not content.parts:
                raise ValueError("Gemini returned no audio parts.")
            part = content.parts[0]
            inline = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
            if not inline:
                raise ValueError("No inline_data in TTS response. The model may have returned a different format.")
            raw = getattr(inline, "data", None)
            if raw is None:
                raise ValueError("No audio data in TTS response.")
            if isinstance(raw, str):
                pcm_bytes = base64.b64decode(raw)
            elif isinstance(raw, (bytes, bytearray, memoryview)):
                pcm_bytes = bytes(raw)
            else:
                pcm_bytes = bytes(raw)
            wav_bytes = _pcm_to_wav(pcm_bytes, sample_rate=24000)
            return base64.b64encode(wav_bytes).decode("ascii")
        except ValueError:
            raise
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(1 + attempt)
    err_msg = str(last_err) if last_err else "Unknown error"
    raise RuntimeError(f"Gemini TTS failed: {err_msg}") from last_err
