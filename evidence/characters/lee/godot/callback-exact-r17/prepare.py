#!/usr/bin/env python3
"""Prepare a native exact-callback replay from Lee's r04 source fixture."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "evidence/characters/lee/original/lee-callback-frame62-updash-airattack-r04"
OUT = HERE / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


build_path = SOURCE_DIR / "build.json"
source_fixture_path = SOURCE_DIR / "fixture.json"
raw_path = SOURCE_DIR / "events.jsonl"
instrumentation_path = SOURCE_DIR / "instrumentation.diff"
build = json.loads(build_path.read_text())
source_fixture = json.loads(source_fixture_path.read_text())
move = build["move_case"]
run_id = build["run_id"]
assert source_fixture["fighter"] == move["fighter"] and source_fixture["slot"] == move["slot"]
targets = []
for item in source_fixture.get("callback_targets", []):
    targets.append({
        "source_sprite_id": item["source_sprite_id"],
        "source_frame": item["source_frame"],
        "source_path": item["source_path"],
        "action": item["action"],
        "kind": item["kind"],
        "slot": item["slot"],
    })
observed_frames = {}
for line in raw_path.read_text().splitlines():
    if not line.startswith(("AIREF|", "{")):
        continue
    event = parse_event_line(line)
    if event["run_id"] != run_id or event["kind"] != "body_boundary":
        continue
    fields = event["value"].split(",")
    if len(fields) >= 3 and fields[0] == "p1":
        observed_frames.setdefault(int(fields[1]), []).append(fields[2])
for frame in (62, 128):
    assert observed_frames.get(frame) == ["true", "false"], f"raw has no exact P1 enter/exit pair for frame {frame}"

fixture = {
    "id": "frame62-updash-airattack-r04",
    "fighter": move["fighter"],
    "slot": move["slot"],
    "label": move["label"],
    "scenario": move["scenario"],
    "frames": move["frames"],
    "setup": copy.deepcopy(move["setup"]),
    "inputs": copy.deepcopy(move["inputs"]),
    "has_source_timeline": move["has_source_timeline"],
    "source_dispatch": copy.deepcopy(move["source_dispatch"]),
    "fighters": copy.deepcopy(move["fighters"]),
    "p1_helper": move["p1_helper"],
    "p2_helper": move["p2_helper"],
    "capture_callbacks_full_fixture": True,
    "source_callback_targets": targets,
}
fixture_path = OUT / "frame62-updash-airattack-r04.json"
fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n")
preflight = {
    "schema": "lee-callback-exact-r17-preflight",
    "run_id": run_id,
    "case_id": fixture["id"],
    "source_raw": "evidence/characters/lee/original/lee-callback-frame62-updash-airattack-r04/events.jsonl",
    "source_raw_sha256": sha(raw_path),
    "source_build": "evidence/characters/lee/original/lee-callback-frame62-updash-airattack-r04/build.json",
    "source_build_sha256": sha(build_path),
    "source_fixture": "evidence/characters/lee/original/lee-callback-frame62-updash-airattack-r04/fixture.json",
    "source_fixture_sha256": sha(source_fixture_path),
    "source_instrumentation": "evidence/characters/lee/original/lee-callback-frame62-updash-airattack-r04/instrumentation.diff",
    "source_instrumentation_sha256": sha(instrumentation_path),
    "source_output_main_sha256": build["outputs_sha256"]["game/main.swf"],
    "source_output_lee_sha256": build["outputs_sha256"]["game/fighter/lee.swf"],
    "source_build_config": build["configuration"],
    "source_move_case": move,
    "targets": targets,
    "native_fixture": "evidence/characters/lee/godot/callback-exact-r17/fixtures/frame62-updash-airattack-r04.json",
    "native_fixture_sha256": sha(fixture_path),
}
(HERE / "preflight.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n")
(HERE / "paths.json").write_text(json.dumps([str(ROOT / preflight["native_fixture"])], indent=2) + "\n")
print(json.dumps({"run_id": run_id, "targets": [row["source_frame"] for row in targets], "fixture": preflight["native_fixture"]}, ensure_ascii=False))
