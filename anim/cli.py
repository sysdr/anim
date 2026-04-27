#!/usr/bin/env python3
"""
SynapseFlow 2026 - Animation CLI

Usage:
  python -m anim.cli render path/to/blueprint.json
  python -m anim.cli generate "topic or text" --output my_video
"""

import argparse
from pathlib import Path

from anim.agents import PipelineOrchestrator
from anim.blueprint.parser import load_blueprint
from anim.renderer.orchestrator import RenderOrchestrator


def main():
    parser = argparse.ArgumentParser(
        prog="synapseflow",
        description="SynapseFlow 2026 - Blueprint-driven animation",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a Blueprint to video")
    render_parser.add_argument("blueprint", type=Path, help="Path to Blueprint JSON file")
    render_parser.add_argument("-o", "--output", type=str, default=None)
    render_parser.add_argument("-q", "--quality", choices=["draft", "standard", "premium"], default="standard")
    render_parser.add_argument("--media-dir", type=Path, default=Path("media"))

    gen_parser = subparsers.add_parser("generate", help="Generate video from topic/URL/PDF")
    gen_parser.add_argument("source", type=str, help="Topic, URL, or path to PDF")
    gen_parser.add_argument("-o", "--output", type=str, default=None)
    gen_parser.add_argument("-q", "--quality", choices=["draft", "standard", "premium"], default="draft")
    gen_parser.add_argument("--media-dir", type=Path, default=Path("media"))
    gen_parser.add_argument("--duration", type=float, default=90.0, help="Target duration in seconds (default: 90)")
    gen_parser.add_argument("--save-blueprint", type=Path, default=None, help="Save Blueprint JSON to file")

    args = parser.parse_args()

    if args.command == "generate":
        _run_generate(args)
        return

    if args.command != "render":
        parser.print_help()
        return

    blueprint = load_blueprint(args.blueprint)
    output_name = args.output or args.blueprint.stem

    orchestrator = RenderOrchestrator(
        blueprint,
        output_dir=args.media_dir,
        quality=args.quality,
        output_filename=output_name,
    )

    print(f"Rendering Blueprint: {blueprint.title or 'Untitled'}")
    print(f"  Scenes: {len(blueprint.scenes)}, Total duration: {blueprint.total_duration:.1f}s")
    print(f"  Quality: {args.quality}")
    print("  Rendering...")

    path = orchestrator.render()

    print(f"  Done: {path}")


def _run_generate(args):
    """Generate video from source via PipelineOrchestrator (Analyzer → WorkflowGenerator → Animator → Exporter)."""
    orch = PipelineOrchestrator(
        output_dir=args.media_dir,
        quality=args.quality,
    )
    result = orch.generate(
        args.source,
        output_name=args.output or "generated",
        target_duration_seconds=args.duration,
        save_blueprint_path=args.save_blueprint,
    )
    blueprint = result["blueprint"]
    path = result["path"]
    if args.save_blueprint:
        print(f"Blueprint saved to {args.save_blueprint}")
    print(f"Generating: {blueprint.title}")
    print(f"  Scenes: {len(blueprint.scenes)}, Duration: {blueprint.total_duration:.1f}s")
    print(f"  Done: {path}")


if __name__ == "__main__":
    main()
