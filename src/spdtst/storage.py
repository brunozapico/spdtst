from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .models import Result


def default_results_path() -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "spdtst" / "results.jsonl"


def save(result: Result, path: Path | None = None) -> Path:
    destination = path or default_results_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as file:
        file.write(json.dumps(result.as_dict()) + "\n")
    return destination
