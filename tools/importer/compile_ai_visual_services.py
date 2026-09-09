"""Resolve simple AI effect wrappers against the retained SWF linkage tables."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from inspect_swf import inspect


def build() -> dict:
    bundle = json.loads((ROOT / "scripts/main.json").read_text())
    source = next(s["source"] for s in bundle["scripts"] if s["path"] == "frame_8/DoAction.as")
    exports = {}
    inputs = []
    for path in sorted((ROOT / "game").rglob("*.swf")):
        relative = path.relative_to(ROOT).as_posix()
        inputs.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for export in inspect(path)["exports"]:
            exports.setdefault(export["name"], []).append(relative)
    wrappers = {}
    for name in ("jumpxg", "luodixg"):
        match = re.search(r"^function " + name + r"\(player\)\s*\{\s*addChildXG\(player,\"(\w+)\",0,0\);\s*\}", source, re.M)
        if match is None:
            raise ValueError("Unsupported effect wrapper: " + name)
        clip = match[1]
        wrappers[name] = {"clip": clip, "offset_y": 0, "offset_x": 0,
                          "exported_by": exports.get(clip, []),
                          "source_path": "scripts/main.json#frame_8/DoAction.as#" + name,
                          "source_sha256": hashlib.sha256(match[0].encode()).hexdigest()}
    return {"format": "bvn26-ai-visual-services-v1", "wrappers": wrappers, "inputs": inputs}


if __name__ == "__main__":
    output = ROOT / "godot/generated/main/ai_visual_services.json"
    output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
