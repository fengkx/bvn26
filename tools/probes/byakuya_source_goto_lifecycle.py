#!/usr/bin/env python3
"""Build an analysis-only Byakuya source-goto lifecycle probe.

This deliberately does not patch or execute production Godot/AS2 code.  It
binds a locked source bundle and emits the exact paired-native harness contract
needed for a later capture.  Its synthetic rows verify the expected semantics,
not character parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
SWF = ROOT / "game/fighter/Byakuya.swf"
SCRIPTS = ROOT / "scripts/fighter/Byakuya.json"
FIGHTER = ROOT / "godot/generated/fighters/byakuya/fighter.json"
TIMELINE = ROOT / "data/slices/Byakuya-base.timeline.json"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_scripts() -> dict[str, dict]:
    data = json.loads(SCRIPTS.read_text())
    return {item["path"]: item for item in data["scripts"]}


def require_run_id(run_id: str) -> None:
    if not re.fullmatch(r"byakuya-goto-[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id must match byakuya-goto-<unique-token>")


def build(run_id: str) -> dict:
    require_run_id(run_id)
    scripts = source_scripts()
    fighter = json.loads(FIGHTER.read_text())
    timeline = json.loads(TIMELINE.read_text())
    frames = {int(frame["frame"]): frame for frame in timeline["frames"]}
    source_sha = sha(SWF)
    bundle = json.loads(SCRIPTS.read_text())
    if bundle.get("swf_sha256") != source_sha:
        raise ValueError("locked SWF and Byakuya script bundle hashes disagree")

    def script(frame: int) -> dict:
        path = f"DefineSprite_631/frame_{frame}/DoAction.as"
        item = scripts.get(path)
        if item is None:
            raise ValueError(f"missing locked source script: {path}")
        return {"path": path, "source": item.get("source", ""),
                "source_sha256": hashlib.sha256(item.get("source", "").encode()).hexdigest()}

    def display(frame: int) -> list[dict]:
        return [{"depth": item.get("depth"), "character_id": item.get("character_id"),
                 "name": item.get("name", ""), "placed_frame": item.get("placed_frame"),
                 "clip_actions": item.get("clip_actions", [])}
                for item in frames[frame].get("display_list", [])]

    actions = fighter["actions"]
    a = actions["movement"]["站立"]
    b = actions["extended_actions"]["招换"]
    source = {
        "sprite_id": 631,
        "A": {"label": "站立", "range": a, "entry_frame": 8, "script": script(8),
              "display_list": display(8)},
        "B": {"label": "招换", "range": b, "entry_frame": 819, "script": script(819),
              "display_list": display(819)},
        "A_after_B": {"label": "站立", "exit_frame": 844, "script": script(844),
                       "display_list": display(844)},
    }
    native = {
        "status": "prepared_not_captured",
        "run_id": run_id,
        "capture_tool": "tools/probes/capture_native_player.py",
        "lock": "/tmp/bvn-native-flash-capture.lock",
        "fixture": {"p1": "白哉", "p2": "一护", "p1_helper": "魂", "p2_helper": "魂",
                     "sequence": ["站立", "招换", "站立"], "same_input": True},
        "required_observation": ["source_frame", "display_tick", "fight_tick", "entry_serial",
                                  "frame_script_serial", "pending_frames", "defer_once",
                                  "depth", "character_id", "placed_frame", "generation",
                                  "placed_tick", "child_local_frame", "child_age",
                                  "child_playing", "callback_dispatch_order"],
        "acceptance": ["source events include 819 and 844", "A-B-A has three entry serials",
                        "same-frame reentry has distinct generations", "placement tick callback is absent",
                        "next display callback is present", "missing/empty child rows fail closed"],
        "command_template": "python3 tools/probes/capture_native_player.py --build <build.json> --output <capture-dir> --lock-timeout 180",
    }
    return {
        "format": "bvn26-byakuya-source-goto-probe-v1",
        "status": "analysis_only_not_parity",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "source": {"swf": str(SWF.relative_to(ROOT)), "swf_sha256": source_sha,
                   "scripts": str(SCRIPTS.relative_to(ROOT)), "scripts_sha256": sha(SCRIPTS),
                   "timeline_slice": str(TIMELINE.relative_to(ROOT)), "timeline_sha256": sha(TIMELINE)},
        "sequence": source,
        "static_contract": {
            "required_relation": "A->B->A must preserve three observed entry records; same-frame reentry must be checked from observed generation IDs, not preset values",
            "required_fields": ["entry_serial", "pending_frames", "defer_once", "generation", "placed_tick", "child_local_frame", "child_age", "callback_dispatch_order"],
        },
        "native_paired_harness": native,
        "scope": "The oracle checks source/runtime lifecycle rules only. No row is native evidence and no Godot production file is changed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = build(args.run_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "run_id": args.run_id,
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
