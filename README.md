# SynapseFlow 2026 — Animation Layer

Blueprint-driven procedural animation using **Manim Community Edition** for technical visualizations. Full agentic pipeline: input extraction → Architect → Director → Manim render.

## Overview

This package implements the **procedural layer** of the SynapseFlow 2026 architecture. It reads a **Unified Logic Blueprint** (JSON) and renders it as video using Manim, ensuring technical accuracy for diagrams, formulas, and process flows.

## Project Structure

```
anim/
├── anim/
│   ├── blueprint/          # Blueprint schema and parser
│   │   ├── schema.py       # Blueprint, Scene, SceneType, Element
│   │   └── parser.py       # load_blueprint(), parse_blueprint()
│   ├── renderer/           # Manim scene builders
│   │   ├── scene_builder.py  # BlueprintScene — maps Blueprint → Manim
│   │   └── orchestrator.py   # RenderOrchestrator — config & render
│   └── cli.py              # Command-line interface
├── examples/
│   └── supply_chain_demo.json
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Installation

```bash
cd /Users/sumedhshende/anim
pip install -r requirements.txt
```

## Dashboard

Start the web dashboard to generate and browse videos from a browser:

```bash
./start.sh
# Or: python -m anim.web.run
```

Open **http://localhost:8000** in your browser.

- **Generate** — Enter a topic, URL, or paste text to create a video
- **Rendered Videos** — List and download completed videos

**Dependencies:** Manim requires FFmpeg and system libraries (Cairo, Pango). On macOS:

```bash
brew install ffmpeg pkg-config cairo pango
pip install -r requirements.txt
```

If `pycairo` fails to install, try: `brew install py3cairo` or use a conda environment with `conda install -c conda-forge manim`.

## Usage

### CLI

```bash
# Render a Blueprint (standard quality)
python -m anim.cli render examples/supply_chain_demo.json

# Generate from topic/text
python -m anim.cli generate "How batteries work" -q draft -o battery_video

# Generate from URL
python -m anim.cli generate "https://example.com/article" -q draft

# Generate from PDF
python -m anim.cli generate path/to/document.pdf -o doc_video

# Save Blueprint for editing
python -m anim.cli generate "Topic" --save-blueprint my_blueprint.json

# Quality: draft | standard | premium
python -m anim.cli render examples/supply_chain_demo.json -q premium -o final
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=anim --cov-fail-under=85
```

### Programmatic

```python
from anim.blueprint.parser import load_blueprint
from anim.renderer.orchestrator import RenderOrchestrator

blueprint = load_blueprint("examples/supply_chain_demo.json")
orchestrator = RenderOrchestrator(
    blueprint,
    output_dir="media",
    quality="standard",
    output_filename="my_video",
)
path = orchestrator.render()
print(f"Rendered to: {path}")
```

## Blueprint Schema

The Blueprint JSON defines:

| Field | Description |
|-------|-------------|
| `scenes` | List of scenes to render in order |
| `scene_type` | `title`, `bullets`, `text`, `formula`, `flow`, `diagram`, `process`, `transition` |
| `elements` | Content (text, LaTeX) with duration |
| `nodes` / `edges` | For `flow` scenes (graph diagrams) |
| `global_style` | Theme, colors, fonts |

Example scene:

```json
{
  "id": "s1",
  "scene_type": "title",
  "duration_seconds": 4,
  "elements": [{ "content": "My Title", "duration_seconds": 4 }]
}
```

## Scene Types

| Type | Manim Mapping |
|------|---------------|
| `title` | Large text, FadeIn |
| `bullets` | BulletedList, Write |
| `text` | Text, FadeIn |
| `formula` | MathTex (LaTeX) |
| `flow` | Graph with nodes/edges |
| `diagram` | Text (placeholder) |
| `process` | BulletedList |
| `transition` | Wait |

## Quality Presets

| Preset | Resolution | FPS | Use Case |
|--------|------------|-----|----------|
| `draft` | 854×480 | 15 | Quick preview |
| `standard` | 1280×720 | 30 | Default |
| `premium` | 1920×1080 | 60 | Final delivery |

## Next Steps (Design Doc)

- **SVD3 polish layer** — AI refinement over procedural frames
- **IndexTTS-2 integration** — Duration-controlled voiceover
- **FFmpeg assembly** — Combine video + audio for final MP4
- **WebGL preview** — Lightweight browser preview before cloud render
# anim
