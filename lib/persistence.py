"""JSON persistence helpers — atomic writes via Path.replace()."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "user_data"


def _ensure_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_json(filename: str, default=None):
    """Load a JSON file from user_data/. Returns *default* if missing."""
    path = DATA_DIR / filename
    if not path.exists():
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    """Atomically save *data* as JSON to user_data/."""
    _ensure_dir()
    path = DATA_DIR / filename
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)
