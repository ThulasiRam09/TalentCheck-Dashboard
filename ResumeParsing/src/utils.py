import json
import re
from pathlib import Path
from typing import Any


def safe_filename(name: str) -> str:
    """Create a filesystem-safe filename."""
    base = Path(name).stem
    base = re.sub(r"[^a-zA-Z0-9_-]+", "_", base)
    return base.strip("_") or "resume"


def save_text(text: str, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_filename(filename)}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def save_json(data: dict[str, Any], output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_filename(filename)}_parsed.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def save_uploaded_file(uploaded_file, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / uploaded_file.name

    with path.open("wb") as file:
        file.write(uploaded_file.getbuffer())

    return path
