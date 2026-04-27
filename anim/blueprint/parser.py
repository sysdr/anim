"""Blueprint parser - load and validate Blueprint from JSON."""

import json
from pathlib import Path

from .schema import Blueprint


def parse_blueprint(data: dict | str) -> Blueprint:
    """Parse Blueprint from dict or JSON string."""
    if isinstance(data, str):
        data = json.loads(data)
    return Blueprint.model_validate(data)


def load_blueprint(path: str | Path) -> Blueprint:
    """Load Blueprint from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Blueprint file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return parse_blueprint(json.load(f))
