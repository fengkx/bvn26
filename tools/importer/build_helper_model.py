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
CONTACT_GOTO = re.compile(
    r"onClipEvent\(enterFrame\)\{\s*"
    r"if\(this\.hitTest\(_root\.game\[\"p\" \+ _parent\.pn\]\.mc\.bdmn\)\)\s*"
    r"\{\s*_parent\.gotoAnd(?P<mode>Play|Stop)\(\"(?P<label>[^\"]+)\"\);\s*\}\s*\}\s*"
)
ENERGY_DRAIN = re.compile(
    r'_root\.game\["p" \+ pn\]\.mc\.ql\s*-=\s*(?P<value>\d+(?:\.\d+)?)'
)
ROOT_STOP_ONE = re.compile(r"gotoAndStop\s*\(\s*1\s*\)\s*;")


def find_unconditional_root_stop_line(source: str) -> int | None:
    """Return the source line of a top-level gotoAndStop(1), if present."""
    depth = 0
    statement_start = 0
    quote = ""
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char in ('"', "'"):
            quote = char
            index += 1
            continue
        if char == "/" and index + 1 < len(source) and source[index + 1] == "/":
            newline = source.find("\n", index + 2)
            index = len(source) if newline < 0 else newline + 1
            continue
        if char == "/" and index + 1 < len(source) and source[index + 1] == "*":
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
            if depth == 0:
                statement_start = index + 1
        elif char == ";" and depth == 0:
            statement = re.sub(
                r"//[^\r\n]*|/\*.*?\*/", "", source[statement_start:index + 1], flags=re.S
            ).strip()
            if ROOT_STOP_ONE.fullmatch(statement):
                return source.count("\n", 0, index) + 1
            statement_start = index + 1
        index += 1
    return None


def has_unconditional_root_stop(source: str) -> bool:
    """Return whether a root DoAction contains a top-level gotoAndStop(1)."""
    return find_unconditional_root_stop_line(source) is not None


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


def _source_label_frames(timeline_path: Path, swf_path: Path) -> dict[str, int]:
    """Resolve labels only from an explicitly supplied, hash-bound timeline."""
    if not timeline_path.is_file():
        return {}
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    source_swf = timeline.get("source_swf", {})
    if source_swf.get("path") != swf_path.as_posix():
        raise ValueError(f"Timeline source does not match helper SWF: {timeline_path}")
    if source_swf.get("sha256") != hashlib.sha256(swf_path.read_bytes()).hexdigest():
        raise ValueError(f"Timeline source hash does not match helper SWF: {timeline_path}")
    return {
        label: int(frame["frame"])
        for frame in timeline.get("frames", [])
        for label in frame.get("labels", [])
    }


def build_model(scripts_path: Path, swf_path: Path, helper_id: str,
                timeline_path: Path | None = None) -> dict[str, Any]:
    bundle = json.loads(scripts_path.read_text(encoding="utf-8"))
    swf = inspect(swf_path)
    attacks: dict[str, dict[str, Any]] = {}
    hide_frames: list[int] = []
    hide_frame_events: list[dict[str, Any]] = []
    drain_events: list[dict[str, Any]] = []
    indexed = []
    presentation_events = []
    clip_load_events = []
    action_events = []
    position_events = []
    contact_gotos = []
    nested_stops = []
    label_frames = _source_label_frames(timeline_path, swf_path) if timeline_path else {}
    for script in bundle["scripts"]:
        record = {
            "path": script["path"],
            "source_sha256": text_sha256(script["source"]),
        }
        indexed.append(record)
        nested = re.fullmatch(r"DefineSprite_(\d+)/frame_(\d+)/DoAction.as", script["path"])
        if nested and script["source"].strip() == "stop();":
            nested_stops.append({"sprite_id": int(nested[1]), "frame": int(nested[2]),
                                 "source_path": script["path"], "source_sha256": record["source_sha256"]})
        root_match = ROOT_FRAME.match(script["path"])
        if root_match is None:
            continue
        frame = int(root_match["frame"])
        record["frame"] = frame
        if script["path"] == f"frame_{frame}/DoAction.as":
            root_stop_line = find_unconditional_root_stop_line(script["source"])
            if root_stop_line is not None:
                hide_frames.append(frame)
                hide_frame_events.append({
                    "frame": frame,
                    "op": "root_goto_and_stop",
                    "target_frame": 1,
                    "source_path": script["path"],
                    "source_line": root_stop_line,
                    "source_sha256": record["source_sha256"],
                })
            for assignment in re.finditer(r'^动作 = (-?\d+);\r?$', script["source"], re.M):
                action_events.append({"frame": frame, "value": int(assignment[1]),
                                      "source_path": script["path"], "source_sha256": record["source_sha256"]})
            if script["source"].strip() == '_X = _parent["p" + pn]._x;':
                position_events.append({
                    "frame": frame,
                    "op": "aim_opponent_x",
                    "source_path": script["path"],
                    "source_sha256": record["source_sha256"],
                })
        placement = re.fullmatch(
            r"frame_(\d+)/PlaceObject2_(\d+)_(\d+)/CLIPACTIONRECORD "
            r"onClipEvent\(enterFrame\)\.as", script["path"]
        )
        if placement:
            contact = CONTACT_GOTO.fullmatch(script["source"].strip())
            if contact:
                label = contact["label"]
                if label not in label_frames:
                    raise ValueError(
                        f"Helper contact goto requires an explicit timeline label {label!r}: {script['path']}"
                    )
                contact_gotos.append({
                    "frame": frame,
                    "placed_frame": frame,
                    "character_id": int(placement[2]),
                    "depth": int(placement[3]),
                    "target_frame": label_frames[label],
                    "target_label": label,
                    "play": contact["mode"] == "Play",
                    "source_path": script["path"],
                    "source_sha256": record["source_sha256"],
                })
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
        "hide_frame_events": sorted(hide_frame_events, key=lambda event: event["frame"]),
        "nested_stops": nested_stops,
        "action_events": sorted(action_events, key=lambda event: event["frame"]),
        "position_events": sorted(position_events, key=lambda event: event["frame"]),
        "contact_gotos": sorted(contact_gotos, key=lambda event: event["frame"]),
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
    parser.add_argument("--timeline", type=Path,
                        help="Explicit hash-bound root timeline export for resolving labels")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = build_model(args.scripts, args.swf, args.helper_id, args.timeline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"helper_id": model["helper_id"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
