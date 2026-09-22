#!/usr/bin/env python3
"""Prepare a real-clock native replay for Lee's natural 1288 callback source run."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "evidence/characters/lee/original/lee-callback-round-loss-failure-r06"
OUT = HERE / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

build_path = SOURCE / "build.json"
fixture_path = SOURCE / "fixture.json"
raw_path = SOURCE / "events.jsonl"
instrumentation_path = SOURCE / "instrumentation.diff"
build = json.loads(build_path.read_text())
source_fixture = json.loads(fixture_path.read_text())
move = build["move_case"]
assert build["run_id"] == "lee-callback-round-loss-failure-r06"
assert move["frames"] == 2400 and move["slot"] == "p1" and move["fighter"] == "lee"
target = next(row for row in source_fixture["source_callback_targets"]
              if row.get("kind") == "frame_action" and int(row["source_frame"]) == 1288)
source_events = []
for line in raw_path.read_text().splitlines():
    if not line.strip():
        continue
    if line.startswith(("AIREF|", "{")):
        event = parse_event_line(line)
    else:
        raise SystemExit(f"unknown nonempty source event line: {line[:120]!r}")
    if event["run_id"] == build["run_id"]:
        source_events.append(event)
ready_anchor = next(event for event in source_events if event["kind"] == "state"
                    and event["fight_tick"] == 1 and event["value"].startswith("p1,"))
target_enter = next(event for event in source_events if event["kind"] == "body_boundary"
                    and event["fight_tick"] == 2263 and event["value"].startswith("p1,1288,true,"))
source_clock_ms_per_display_tick = (
    (target_enter["time_ms"] - ready_anchor["time_ms"])
    / (target_enter["display_tick"] - ready_anchor["display_tick"])
)
profile_path = ROOT / "godot/generated/main/execution_profile.json"
profile = json.loads(profile_path.read_text())
assert profile["host_fps"] == 30
profile_tick_ms = 1000.0 / profile["host_fps"]
native_code_paths = [
    "godot/tests/lee_callback_exact_probe.gd",
    "godot/fighter_runtime.gd",
    "godot/main.gd",
    "godot/helper_runtime.gd",
    "godot/source_callback_registry.gd",
    "godot/generated/fighters/lee/player_controller/controller.gd",
    "godot/generated/fighters/lee/ai_controller/controller.gd",
    "godot/generated/main/execution_profile.json",
]
native_code_hashes = {path: sha(ROOT / path) for path in native_code_paths}
fixture = {
    "id": "round-loss-failure-1288-r06",
    "fighter": move["fighter"],
    "slot": move["slot"],
    "label": move["label"],
    "scenario": move["scenario"],
    "stage": build["configuration"]["stage"],
    "frames": move["frames"],
    "setup": copy.deepcopy(move["setup"]),
    "inputs": copy.deepcopy(move["inputs"]),
    "has_source_timeline": move["has_source_timeline"],
    "source_dispatch": copy.deepcopy(move["source_dispatch"]),
    "fighters": copy.deepcopy(move["fighters"]),
    "p1_helper": move["p1_helper"],
    "p2_helper": move["p2_helper"],
    "source_state_preconditions": copy.deepcopy(move.get("source_state_preconditions", {})),
    "capture_callbacks_full_fixture": True,
    "real_wall_clock_per_fight_tick": True,
    "source_callback_targets": [copy.deepcopy(target)],
}
native_fixture = OUT / f'{fixture["id"]}.json'
native_fixture.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n")
preflight = {
    "schema": "lee-callback-exact-r18-preflight",
    "case_id": fixture["id"],
    "run_id": build["run_id"],
    "source_raw": "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/events.jsonl",
    "source_raw_sha256": sha(raw_path),
    "source_build": "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/build.json",
    "source_build_sha256": sha(build_path),
    "source_fixture": "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/fixture.json",
    "source_fixture_sha256": sha(fixture_path),
    "source_instrumentation": "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/instrumentation.diff",
    "source_instrumentation_sha256": sha(instrumentation_path),
    "source_outputs_sha256": build["outputs_sha256"],
    "source_configuration": build["configuration"],
    "source_move_case": move,
    "source_clock_calibration": {
        "ready_anchor": {key: ready_anchor[key] for key in ("sequence", "time_ms", "display_tick", "fight_tick")},
        "target_enter": {key: target_enter[key] for key in ("sequence", "time_ms", "display_tick", "fight_tick")},
        "source_ms_per_display_tick": source_clock_ms_per_display_tick,
        "profile_host_fps": profile["host_fps"],
        "profile_ms_per_host_tick": profile_tick_ms,
    },
    "execution_profile": "godot/generated/main/execution_profile.json",
    "execution_profile_sha256": sha(profile_path),
    "native_code_hashes": native_code_hashes,
    "source_target": target,
    "native_fixture": str(native_fixture.relative_to(ROOT)),
    "native_fixture_sha256": sha(native_fixture),
    "real_clock_policy": "Await one real SceneTree timer interval per logical fight tick; leave MatchCountdown Timer enabled and record each timeout callback. No manual timeover or frame goto.",
    "source_clock_calibration": {
        "ready_anchor": {key: ready_anchor[key] for key in ("sequence", "time_ms", "display_tick", "fight_tick")},
        "target_enter": {key: target_enter[key] for key in ("sequence", "time_ms", "display_tick", "fight_tick")},
        "source_ms_per_display_tick": source_clock_ms_per_display_tick,
        "profile_host_fps": profile["host_fps"],
        "profile_ms_per_host_tick": profile_tick_ms,
    },
    "execution_profile": "godot/generated/main/execution_profile.json",
    "execution_profile_sha256": sha(profile_path),
    "native_code_hashes": native_code_hashes,
}
(HERE / "preflight.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n")
(HERE / "paths.json").write_text(json.dumps([str(ROOT / preflight["native_fixture"])], indent=2) + "\n")
print(json.dumps({"case_id": fixture["id"], "source_run_id": build["run_id"],
                  "frames": fixture["frames"], "target": target["source_frame"],
                  "native_fixture": preflight["native_fixture"],
                  "real_clock": fixture["real_wall_clock_per_fight_tick"],
                  "source_ms_per_display_tick": source_clock_ms_per_display_tick,
                  "profile_ms_per_host_tick": profile_tick_ms}, ensure_ascii=False))
