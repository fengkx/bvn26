#!/usr/bin/env python3
"""Build a source-first audit for the Kakashi base fighter.

This deliberately emits source evidence only.  It does not invent timeline
geometry or convert a missing JPEXS export into production assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from inspect_swf import inspect


ROOT = Path(__file__).resolve().parents[1]
SPRITE = 710
SPRITE_PATH = re.compile(r"^DefineSprite_(?P<sprite>\d+)/frame_(?P<frame>\d+)(?:/|$)")
EXIT = re.compile(r"gotoAnd(?P<kind>Play|Stop)\(\"(?P<label>[^\"]+)\"\)|(?P<stop>stop\(\))")
ATTACK = re.compile(
    r"gjl(?P<form>\d+)\.(?P<name>[A-Za-z0-9_]+)(?P<field>pw|zl|up|x|tm|dz)\s*=\s*(?P<value>[^;]+);"
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_record(script: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": script["path"],
        "sha256": sha256_text(script["source"]),
        "source": script["source"],
    }


def action_spans(labels: list[dict[str, Any]], frame_count: int) -> dict[str, dict[str, int]]:
    spans: dict[str, dict[str, int]] = {}
    for index, label in enumerate(labels):
        end = labels[index + 1]["frame"] - 1 if index + 1 < len(labels) else frame_count
        spans[str(label["label"])] = {"start_frame": int(label["frame"]), "end_frame": end}
    return spans


def build_audit(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    fighter = manifest["fighter_catalog"]["卡卡西"]
    swf_path = root / "game/fighter" / fighter["url"]
    script_path = root / "scripts/fighter/Kakashi.json"
    bundle = json.loads(script_path.read_text(encoding="utf-8"))
    scripts = bundle["scripts"]
    swf = inspect(swf_path)
    timeline = next(item for item in swf["timelines"] if item["name"] == f"sprite_{SPRITE}")
    spans = action_spans(timeline["labels"], timeline["declared_frames"])

    frame_scripts: dict[int, dict[str, list[dict[str, Any]]]] = {
        frame: {"do_action": [], "clip_action": []}
        for frame in range(1, int(timeline["declared_frames"]) + 1)
    }
    for script in scripts:
        match = SPRITE_PATH.match(script["path"])
        if match is None or int(match["sprite"]) != SPRITE:
            continue
        frame = int(match["frame"])
        kind = "clip_action" if "CLIPACTIONRECORD" in match[0] else "do_action"
        frame_scripts[frame][kind].append(
            {
                "path": script["path"],
                "sha256": sha256_text(script["source"]),
                "source": script["source"],
            }
        )

    frame_index = []
    for frame in range(1, int(timeline["declared_frames"]) + 1):
        record = frame_scripts[frame]
        exits = []
        for script in record["do_action"]:
            exits.extend(
                {
                    "kind": "stop" if match["stop"] else match["kind"],
                    "target": None if match["stop"] else match["label"],
                    "source_path": script["path"],
                }
                for match in EXIT.finditer(script["source"])
            )
        frame_index.append(
            {
                "frame": frame,
                "labels": [
                    str(label["label"])
                    for label in timeline["labels"]
                    if int(label["frame"]) == frame
                ],
                "do_action": record["do_action"],
                "clip_action": record["clip_action"],
                "exits": exits,
            }
        )

    root_init = next(script for script in scripts if script["path"] == "frame_1/DoAction.as")
    load_script = next(
        script
        for script in scripts
        if script["path"] == "frame_1/PlaceObject2_710_1/CLIPACTIONRECORD onClipEvent(load).as"
    )
    shared = next(
        script for script in scripts if script["path"] == "DefineSprite_2/frame_1/DoAction.as"
    )
    attacks: dict[str, dict[str, Any]] = {}
    for match in ATTACK.finditer(root_init["source"]):
        attacks.setdefault(match["name"], {})[match["field"]] = match["value"].strip()

    face_events = []
    for frame in frame_index:
        for script in frame["do_action"]:
            for match in re.finditer(
                r"_root\.(?P<freeze>bsd|cbsd)\(pn\);\s*_root\.showFace\(pn,\"(?P<label>[^\"]+)\"\)",
                script["source"],
            ):
                face_events.append(
                    {
                        "frame": frame["frame"],
                        "freeze": match["freeze"],
                        "face_label": match["label"],
                        "source_path": script["path"],
                    }
                )

    return {
        "format": "bvn26-kakashi-source-audit-v1",
        "status": "source_audit_only",
        "fighter": {
            "id": "卡卡西",
            "display_name": fighter["name"],
            "source_swf": swf_path.relative_to(root).as_posix(),
            "source_swf_sha256": swf["sha256"],
            "script_bundle": script_path.relative_to(root).as_posix(),
            "script_bundle_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
            "timeline_symbol_id": SPRITE,
            "form_frame": 1,
            "assist": fighter["fz"],
            "versus": fighter["vs"],
            "is_naruto": bool(fighter["isNaruto"]),
        },
        "timeline": {
            "frame_rate": swf["header_fps"],
            "frame_count": timeline["declared_frames"],
            "labels": timeline["labels"],
            "action_spans": spans,
            "frame_index": frame_index,
        },
        "source_questions": {
            "frame_scripts": {
                "answer": "Every frame 1..1385 is indexed; DoAction and enterFrame/load paths are retained verbatim.",
                "paths": ["scripts/fighter/Kakashi.json:DefineSprite_710/frame_*/"],
            },
            "placement_vs_move": {
                "answer": "Root fighter is placed at frame_1; every later placement/clip action is retained by frame/depth path. Exact MOVE/display-list geometry awaits JPEXS XML.",
                "paths": ["scripts/fighter/Kakashi.json:frame_1/PlaceObject2_710_1/", "evidence/probes/schedule/clip_lifecycle.log"],
            },
            "exit_mode": {
                "answer": "All explicit gotoAndPlay/gotoAndStop/stop calls are indexed; labels without a terminal script remain timeline fallthroughs.",
                "paths": ["scripts/fighter/Kakashi.json:DefineSprite_710/frame_*/DoAction.as"],
            },
            "invariants": {
                "answer": "Movement constants, attack table, hits reset, defence, onBeHit and super face labels remain source-owned; no role-specific runtime constants are introduced.",
                "paths": ["scripts/fighter/Kakashi.json:frame_1/DoAction.as", "scripts/fighter/Kakashi.json:DefineSprite_710/frame_2/DoAction.as", "scripts/fighter/Kakashi.json:DefineSprite_710/frame_1105/DoAction.as", "scripts/fighter/Kakashi.json:DefineSprite_710/frame_1117/DoAction.as", "scripts/fighter/Kakashi.json:DefineSprite_710/frame_1130/DoAction.as"],
            },
            "same_input": {
                "answer": "Pending original-player capture; no synthetic Godot trace is promoted to parity evidence.",
                "paths": ["evidence/reference-environment.md", "docs/VALIDATION.md#对战对照方法"],
            },
        },
        "movement_constants": {
            "speed_per_tick": 8,
            "jump_power": 18,
            "source": source_record(load_script),
        },
        "attacks": attacks,
        "hits_reset_frames": [2],
        "defence_frames": [{"frame": 1105, "argument": 2, "path": "DefineSprite_710/frame_1105/DoAction.as"}],
        "be_hit_frames": [
            {"frame": 1117, "flying": False, "path": "DefineSprite_710/frame_1117/DoAction.as"},
            {"frame": 1130, "flying": True, "path": "DefineSprite_710/frame_1130/DoAction.as"},
        ],
        "super_events": face_events,
        "root_control": source_record(root_init),
        "shared_control": source_record(shared),
        "load_control": source_record(load_script),
        "acceptance_gates": {
            "source_static": "ready",
            "timeline_geometry": "ready" if (root / "data/slices/Kakashi-base.timeline.json").is_file() else "blocked_missing_jpexs_xml",
            "materialized_visual_assets": "ready" if (root / "godot/generated/fighters/kakashi/assets.json").is_file() else "blocked_missing_jpexs_xml",
            "native_godot": "pending_godot_binary",
            "web": "blocked_until_native",
            "original_same_input": "pending_shared_player_slot",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = build_audit(ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fighter": audit["fighter"]["id"], "frames": audit["timeline"]["frame_count"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
