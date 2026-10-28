"""Small helpers for readable reports and file fingerprints."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import numpy as np
import pandas as pd


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_default(value):
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating,)): return float(value)
    if isinstance(value, (np.bool_,)): return bool(value)
    if isinstance(value, (pd.Timestamp, Path)): return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               default=json_default, allow_nan=False), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_figure(figure, path):
    """Render fully before writing, so a failed render cannot leave an empty PNG."""
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=160)
    payload = buffer.getvalue()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"Figure did not render correctly: {path}")
    Path(path).write_bytes(payload)
