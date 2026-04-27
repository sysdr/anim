# Cinematic Animation & Complex Workflow Design

This document describes the **animated-movie-style** animation design and **complex workflow** model used in SynapseFlow: real-world entities, distinct parts, and ultra-scalable system concepts.

## Design Goals

1. **Animation like animated movies** — Establishing shots, reveals, callouts, narrative rhythm.
2. **Complex workflows** — Break systems into **distinct parts** (e.g. Ingestion → Queue → Workers → Cache → Storage → Delivery).
3. **Real-world entities** — Visualize using metaphors (pipelines, conveyors, warehouses, server racks, organisms), not abstract boxes.
4. **Ultra-scalable systems** — Show replication, sharding, fan-out, and queue-backed tiers in the visuals.

## Key Concepts

### Cinematic structure (Acts)

- **Acts** are narrative chapters: e.g. "Establishing", "Ingestion & Queue", "Processing at Scale", "Storage & Delivery".
- Each act has a **narrative_beat**: `establishing`, `build`, `scale`, `conflict`, `resolution`.
- Scenes are grouped by `act_id`; the Studio and Blueprint schema support this.

### Workflow parts (distinct subsystems)

- **Parts** are the distinct subsystems of a complex workflow (e.g. `part-ingestion`, `part-queue`, `part-workers`).
- Each part has:
  - **responsibility** — what it does
  - **scale_hint** — e.g. `replicated`, `sharded`, `fan-out`, `queue-backed`
  - **scene_ids** — which steps/scenes belong to it

### Entity metaphors (real-world)

- Components are drawn as **real-world things**:
  - **Data flow:** pipelines, conveyor belts, rivers, highways
  - **Processing:** factories, refineries, assembly lines
  - **Storage:** warehouses, silos, reservoirs, vaults
  - **Scale/compute:** server racks, power plants, organisms (cells, organs)

### Scale indicators

- **Scale indicators** describe how scalability is shown in the visualization (e.g. "multiple worker nodes", "replicated pipelines", "sharded queue").

## Where It’s Implemented

| Area | Location |
|------|----------|
| **Blueprint schema** | `anim/blueprint/schema.py` — `Act`, `WorkflowPart`, `entity_metaphor`, `acts`, `workflow_parts` on Blueprint; `act_id`, `entity_metaphor`, `camera_move` on Scene |
| **Studio prompts** | `anim/web/services/gemini_service.py` — `ARCHITECT_SVG_SYSTEM_PROMPT_TEMPLATE`, `STUDIO_ARCHITECT_PROMPT_TEMPLATE` |
| **Studio UI** | `anim/web/templates/studio.html` — workflow breakdown shows acts, parts, entity_metaphors, scale_indicators, steps with part_ref |
| **Example** | `examples/complex_workflow_demo.json` — full Blueprint with 4 acts, 6 workflow parts, 8 scenes |

## Example: Most Complex Workflow

The **Ultra-Scalable Event Pipeline** example (`examples/complex_workflow_demo.json`) showcases:

- **4 acts:** Establishing → Ingestion & Queue → Processing at Scale → Storage & Delivery
- **6 workflow parts:** Ingestion (fan-out), Queue (sharded), Workers (replicated), Cache (replicated), Storage (sharded), Delivery (fan-out)
- **8 scenes** with `act_id`, `entity_metaphor`, and `camera_move` (establishing, reveal)
- **Global entity_metaphor:** `factory_and_warehouse`

Use it as a reference for authoring or for validating the Manim/Studio pipeline with complex workflows.
