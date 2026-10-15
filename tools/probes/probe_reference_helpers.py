"""Pure helpers shared by native reference probe builders."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
