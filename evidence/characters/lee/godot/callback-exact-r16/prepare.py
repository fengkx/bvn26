#!/usr/bin/env python3
"""Prepare same-input native fixtures for source-observed Lee clip callbacks."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = HERE / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = [
    {
        "case_id": "round-loss-r03-p1-clip1088",
        "run_id": "lee-callback-round-loss-failure-r03",
        "source_dir": "evidence/characters/lee/original/lee-callback-round-loss-failure-r03",
        "targets": [
            {
                "source_sprite_id": 518,
                "source_frame": 1088,
                "source_path": "DefineSprite_518/frame_1088/PlaceObject2_18_29/CLIPACTIONRECORD onClipEvent(enterFrame).as",
                "action": "击飞",
                "kind": "clip_action",
                "slot": "p1",
                "placement_id": 18,
                "depth": 29,
            }
        ],
    },
    {
        "case_id": "lifecycle-r01-p2-clip1098-1133",
        "run_id": "lee-callback-lifecycle-recovery-r01",
        "source_dir": "evidence/characters/lee/original/lee-callback-lifecycle-recovery-r01",
        "targets": [
            {
                "source_sprite_id": 518,
                "source_frame": 1098,
                "source_path": "DefineSprite_518/frame_1098/PlaceObject2_18_29/CLIPACTIONRECORD onClipEvent(enterFrame).as",
                "action": "击落地",
                "kind": "clip_action",
                "slot": "p2",
                "placement_id": 18,
                "depth": 29,
            },
            {
                "source_sprite_id": 518,
                "source_frame": 1133,
                "source_path": "DefineSprite_518/frame_1133/PlaceObject2_18_30/CLIPACTIONRECORD onClipEvent(enterFrame).as",
                "action": "起身",
                "kind": "clip_action",
                "slot": "p2",
                "placement_id": 18,
                "depth": 30,
            },
        ],
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


preflight = {"schema": "lee-callback-exact-r16-preflight", "cases": []}
for spec in SOURCES:
    source_dir = ROOT / spec["source_dir"]
    build_path = source_dir / "build.json"
    source_fixture_path = source_dir / "fixture.json"
    raw_path = source_dir / "events.jsonl"
    instrumentation_path = source_dir / "instrumentation.diff"
    build = json.loads(build_path.read_text())
    source_fixture = json.loads(source_fixture_path.read_text())
    assert build.get("run_id") == spec["run_id"], (spec["case_id"], build.get("run_id"))
    move = build["move_case"]
    assert source_fixture["id"] == move["id"]

    fixture = {
        "id": spec["case_id"],
        "fighter": move["fighter"],
        "slot": move["slot"],
        "label": move["label"],
        "scenario": move["scenario"],
        "frames": move["frames"],
        "setup": copy.deepcopy(move["setup"]),
        "inputs": copy.deepcopy(move["inputs"]),
        "has_source_timeline": move.get("has_source_timeline", True),
        "source_dispatch": copy.deepcopy(move.get("source_dispatch", ["doAllAction", "doStand"])),
        "fighters": copy.deepcopy(move["fighters"]),
        "p1_helper": move["p1_helper"],
        "p2_helper": move["p2_helper"],
        "source_state_preconditions": copy.deepcopy(move.get("source_state_preconditions", {})),
        "capture_callbacks_full_fixture": True,
        "source_callback_targets": copy.deepcopy(spec["targets"]),
    }
    fixture_path = OUT / f"{spec['case_id']}.json"
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n")

    preflight["cases"].append({
        **spec,
        "source_raw": f"{spec['source_dir']}/events.jsonl",
        "source_raw_sha256": sha(raw_path),
        "source_build": f"{spec['source_dir']}/build.json",
        "source_build_sha256": sha(build_path),
        "source_instrumentation": f"{spec['source_dir']}/instrumentation.diff",
        "source_instrumentation_sha256": sha(instrumentation_path),
        "source_fixture": f"{spec['source_dir']}/fixture.json",
        "source_fixture_sha256": sha(source_fixture_path),
        "source_output_main_sha256": build["outputs_sha256"]["game/main.swf"],
        "source_build_config": build["configuration"],
        "source_move_case": move,
        "native_fixture": f"evidence/characters/lee/godot/callback-exact-r16/fixtures/{fixture_path.name}",
        "native_fixture_sha256": sha(fixture_path),
        "source_slot": move["slot"],
        "source_rows": [],
    })

preflight["paths"] = [case["native_fixture"] for case in preflight["cases"]]
(HERE / "preflight.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n")
(HERE / "paths.json").write_text(json.dumps([str(ROOT / path) for path in preflight["paths"]], indent=2) + "\n")
smoke_fixture = {
    "id": "callback-probe-output-dir-smoke",
    "frames": 0,
    "fighters": {"p1": "lee", "p2": "byakuya"},
    "setup": {"p1": {"x": 300, "energy": 300}, "p2": {"x": 350, "energy": 300}},
    "inputs": [],
    "p1_helper": "魂",
    "p2_helper": "魂",
    "source_callback_targets": [],
}
(OUT / "output-dir-smoke.json").write_text(json.dumps(smoke_fixture, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"cases": len(preflight["cases"]), "paths": preflight["paths"]}, ensure_ascii=False))
