"""Build source-traceable combat metadata for assistance (fz) clips."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from inspect_swf import inspect  # noqa: E402

FIELD_NAMES = {
    "pw": "damage",
    "zl": "impact_strength",
    "up": "vertical_impulse",
    "x": "horizontal_impulse",
    "tm": "hitstun_ms",
    "dz": "reaction_label",
}
GJL_ASSIGN = re.compile(
    r"gjl\.(?P<name>[A-Za-z0-9_]+?)(?P<suffix>pw|zl|up|x|tm|dz)\s*=\s*(?P<value>[^;]+);"
)
ROOT_FRAME = re.compile(r"^frame_(?P<frame>\d+)/")
ENERGY_DRAIN = re.compile(
    r'_root\.game\["p" \+ pn\]\.mc\.ql\s*-=\s*(?P<value>\d+(?:\.\d+)?)'
)


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_literal(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    raise ValueError(f"Unsupported helper literal: {value}")


def extract_attacks(source: str) -> dict[str, dict[str, Any]]:
    attacks: dict[str, dict[str, Any]] = {}
    for match in GJL_ASSIGN.finditer(source):
        attacks.setdefault(match["name"], {})[FIELD_NAMES[match["suffix"]]] = (
            parse_literal(match["value"])
        )
    return attacks


def build_model(scripts_path: Path, swf_path: Path, helper_id: str) -> dict[str, Any]:
    bundle = json.loads(scripts_path.read_text(encoding="utf-8"))
    swf = inspect(swf_path)
    attacks: dict[str, dict[str, Any]] = {}
    hide_frames: list[int] = []
    drain_events: list[dict[str, Any]] = []
    indexed = []
    presentation_events = []
    clip_load_events = []
    for script in bundle["scripts"]:
        record = {
            "path": script["path"],
            "source_sha256": text_sha256(script["source"]),
        }
        indexed.append(record)
        root_match = ROOT_FRAME.match(script["path"])
        if root_match is None:
            continue
        frame = int(root_match["frame"])
        record["frame"] = frame
        if script["path"].endswith("frame_1/DoAction.as"):
            attacks.update(extract_attacks(script["source"]))
        source = script["source"]
        if "_root.fzccXg(this)" in source:
            presentation_events.append({"frame": frame, "op": "effect", "xg": "XG_fzcc", "source_path": script["path"]})
        for call in re.finditer(r'_root\.(bsd|bsw)\(pn(?:,"([^"]+)")?(?:,(true|false))?\)', source):
            presentation_events.append({
                "frame": frame, "op": "super_start" if call[1] == "bsd" else "super_end",
                "kind": call[1], "xg": call[2] or "XG_bs", "helper": call[3] == "true",
                "source_path": script["path"],
            })
        for call in re.finditer(r'_root\.shine\((\d+)\)', source):
            presentation_events.append({"frame": frame, "op": "shine", "color": int(call[1]), "source_path": script["path"]})
        placement = re.search(r'/PlaceObject2_(\d+)_(\d+)/', script["path"])
        if placement and 'onClipEvent(load)' in source:
            if '_root.game["p" + _parent.pn]._x - _parent._x' not in source:
                raise ValueError(f"Unsupported helper load script: {script['path']}")
            clip_load_events.append({
                "frame": frame, "op": "aim_opponent_x", "character_id": int(placement[1]),
                "depth": int(placement[2]), "source_path": script["path"],
            })
        for drain in ENERGY_DRAIN.finditer(script["source"]):
            drain_events.append(
                {
                    "frame": frame,
                    "target": "opponent",
                    "delta": -float(drain["value"]),
                    "source_path": script["path"],
                    "source_sha256": record["source_sha256"],
                }
            )
    return {
        "format": "bvn26-helper-model-v1",
        "status": "reverse_engineering_intermediate",
        "helper_id": helper_id,
        "simulation_hz": 30,
        "source": {
            "swf": swf_path.as_posix(),
            "swf_sha256": swf["sha256"],
            "script_bundle": scripts_path.as_posix(),
            "header_fps": swf["header_fps"],
            "root_frames": swf["root_frames"],
        },
        "start_frame": 2,
        "end_frame": swf["root_frames"],
        "hide_frames": sorted(set(hide_frames)),
        "attacks": attacks,
        "presentation_events": sorted(presentation_events, key=lambda event: event["frame"]),
        "clip_load_events": clip_load_events,
        "drain_events": sorted(drain_events, key=lambda item: item["frame"]),
        "indexed_source_events": indexed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", type=Path, required=True)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--helper-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = build_model(args.scripts, args.swf, args.helper_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"helper_id": model["helper_id"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
