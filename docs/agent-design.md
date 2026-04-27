# SynapseFlow Agent Design

This document describes the **agent-based architecture** for SynapseFlow: orchestrator, analyzer, researcher, workflow generator, animator, validators, judge, studio display/controller, and exporter.

## Overview

All pipeline steps are implemented as **agents** with clear inputs/outputs. The **Orchestrator** drives the pipeline and delegates to specialist agents. Data flows as typed artifacts (text, blueprint, workflow_spec, SVG, timeline, etc.).

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    ORCHESTRATOR                           │
                    │  (drives pipeline, delegates to agents, holds context)   │
                    └─────────────────────────────────────────────────────────┘
                                              │
     ┌────────────────────────────────────────┼────────────────────────────────────────┐
     │                                        │                                        │
     ▼                                        ▼                                        ▼
┌─────────┐  ┌────────────┐  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────┐
│ ANALYZER│  │ RESEARCHER │  │ WORKFLOW_GEN     │  │   ANIMATOR      │  │  VALIDATORS │
│         │  │            │  │ (Blueprint/      │  │ (editor,        │  │ (SVG,       │
│ input → │  │ topic →    │  │  workflow_spec)  │  │  modifier,      │  │  blueprint, │
│ structured│  │ enriched  │  │                 │  │  updater,       │  │  timeline)  │
│ content │  │ context    │  │ text/spec →      │  │  scene builder) │  │             │
└─────────┘  └────────────┘  │ blueprint/spec   │  └────────┬────────┘  └──────┬──────┘
     │              │        └──────────────────┘           │                 │
     └──────────────┴────────────────┬───────────────────────┴─────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
             ┌──────────┐     ┌──────────────┐   ┌───────────┐
             │  JUDGE   │     │ STUDIO       │   │ EXPORTER  │
             │ quality  │     │ DISPLAY &    │   │ video,    │
             │ sync     │     │ CONTROLLER   │   │ blueprint │
             └──────────┘     └──────────────┘   └───────────┘
```

## Agent Roles

| Agent | Responsibility | Inputs | Outputs |
|-------|----------------|--------|----------|
| **Orchestrator** | Run pipeline, delegate to agents, hold job context | source (text/URL/PDF), options | job result (blueprint, paths, status) |
| **Analyzer** | Extract and structure raw input | raw string, URL, or path | structured content (title, bullets, sections) |
| **Researcher** | Enrich topic with context (optional LLM/web) | topic/summary | enriched context, references |
| **WorkflowGenerator** | Produce Blueprint or workflow_spec from content | structured content / topic | Blueprint and/or workflow_spec + steps |
| **Animator** | Edit, modify, update; build scenes (Manim or SVG) | Blueprint / workflow_spec / SVG | Rendered scenes, SVG, or updated Blueprint |
| **Validators** | Validate and fix artifacts | SVG / Blueprint / timeline | Validated/fixed artifact |
| **Judge** | Quality and sync checks | blueprint, timeline, script | pass/fail, feedback |
| **StudioDisplay & Controller** | UI state, display, user controls | user actions, current artifact | display model, control events |
| **Exporter** | Export to video, JSON, etc. | Blueprint, SVG, media | file paths, URLs |

## Data Artifacts

- **StructuredContent**: `{ title, sections, bullets, raw_text }` — from Analyzer
- **WorkflowSpec**: `{ title, summary, acts, parts, steps, actors, entities, ... }` — from WorkflowGenerator (Studio path)
- **Blueprint**: Pydantic schema — from Architect/WorkflowGenerator
- **Timeline**: `[ { id, label, narration, startTime, duration } ]`
- **SVG**: string (valid, safe for iframe)
- **ExportResult**: `{ path, url, format }`

## Pipeline Variants

1. **CLI / Dashboard generate**: Source → Analyzer → WorkflowGenerator (Architect) → Director → Validators → Animator (Manim) → Exporter
2. **Studio generate**: Concept → Researcher (optional) → WorkflowGenerator (Gemini workflow_spec + SVG) → Validators → Judge → StudioDisplay
3. **Studio export-blueprint**: Script → WorkflowGenerator (script→scenes) → Blueprint → Animator → Exporter

## File Layout

```
anim/
  agents/
    __init__.py          # export all agents
    base.py              # BaseAgent protocol/ABC
    orchestrator.py      # PipelineOrchestrator
    analyzer.py          # AnalyzerAgent (uses input/extractor)
    researcher.py        # ResearcherAgent (optional enrichment)
    workflow_generator.py # WorkflowGeneratorAgent (Architect + Director + Gemini path)
    animator.py          # AnimatorAgent (editor, modifier, updater, scene_builder)
    validators.py        # BlueprintValidator, TimelineValidator; re-export SvgValidationAgent
    judge.py             # JudgeAgent (quality, sync)
    studio_controller.py # StudioDisplayController (state for UI)
    exporter.py          # ExporterAgent (video, blueprint JSON)
    # existing: architect.py, director.py, svg_validator.py
```

## Usage

- **Orchestrator** is the single entry point for "generate" and "render" flows; it composes agents and returns a result.
- **Web app** and **CLI** call the Orchestrator instead of calling Architect/Director/Extractor/Orchestrator directly.
- **Studio** uses WorkflowGenerator (Gemini), Validators, Judge, and StudioDisplayController; export uses Exporter.
