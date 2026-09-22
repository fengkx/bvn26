#!/usr/bin/env python3
"""Build strict same-source-fixture Godot replays for four Lee body callbacks."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
PROV = ROOT / "evidence/characters/lee/callback-exact-r01/source-callback-provenance-r01"
CASES = [
    {
        "name": "rush-p1-8-1219",
        "build": ROOT / "evidence/characters/lee/original/lee-callback-exact-rush-r01-normalized/build.json",
        "raw": ROOT / "evidence/characters/lee/original/lee-callback-exact-rush-r01-normalized/events.jsonl",
        "fixture": None,
        "frames": [8, 1219],
        "slot": "p1",
    },
    {
        "name": "recovery-hp1-p2-1083",
        "build": PROV / "recovery-p2-hp1/build.json",
        "raw": ROOT / "evidence/characters/lee/original/lee-callback-observer-hp1-r01/events.jsonl/events.jsonl",
        "fixture": PROV / "recovery-p2-hp1/fixture-from-build.json",
        "frames": [1083],
        "slot": "p2",
    },
    {
        "name": "kill700-p1-1260",
        "build": PROV / "kill700-external-tape/build.json",
        "raw": ROOT / "evidence/characters/lee/original/lee-body-boundaries-r02/events.jsonl",
        "fixture": PROV / "kill700-external-tape/fixture-from-build.json",
        "frames": [1260],
        "slot": "p1",
    },
]

sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


OUT = HERE / "fixtures/four-body-r01"
OUT.mkdir(parents=True, exist_ok=True)
specs: list[str] = []
manifest_cases = []
for case in CASES:
    build_path: Path = case["build"]
    raw_path: Path = case["raw"]
    build = json.loads(build_path.read_text())
    move = build["move_case"]
    source_fixture = json.loads(case["fixture"].read_text()) if case["fixture"] else move
    targets = []
    found: dict[int, list[str]] = {frame: [] for frame in case["frames"]}
    run_id = str(build["run_id"])
    for line in raw_path.read_text().splitlines():
        if not line.strip():
            continue
        event = parse_event_line(line)
        if event["run_id"] != run_id or event["kind"] != "body_boundary":
            continue
        fields = event["value"].split(",")
        if len(fields) >= 3 and fields[0] == case["slot"] and fields[1].isdigit():
            frame = int(fields[1])
            if frame in found:
                found[frame].append(fields[2])
    for frame, phases in found.items():
        if phases.count("true") == 0 or phases.count("false") == 0:
            raise SystemExit(f"source lacks enter/exit marker: {case['name']} frame={frame} phases={phases}")
        targets.append({
            "source_sprite_id": 518,
            "source_frame": frame,
            "source_path": f"DefineSprite_518/frame_{frame}/DoAction.as",
            "action": move["label"],
            "kind": "frame_action",
            "slot": case["slot"],
        })
    if source_fixture.get("slot") != case["slot"] or source_fixture.get("fighter") != "lee":
        raise SystemExit(f"source fixture role/slot mismatch: {case['name']}")
    fixture = {
        "id": case["name"],
        "fighter": move["fighter"],
        "slot": case["slot"],
        "label": move["label"],
        "scenario": move.get("scenario", ""),
        "frames": move["frames"],
        "setup": copy.deepcopy(move["setup"]),
        "inputs": copy.deepcopy(move["inputs"]),
        "has_source_timeline": move.get("has_source_timeline", True),
        "source_dispatch": copy.deepcopy(move.get("source_dispatch", [])),
        "fighters": copy.deepcopy(move["fighters"]),
        "p1_helper": move["p1_helper"],
        "p2_helper": move["p2_helper"],
        "stage": build["configuration"]["stage"],
        "source_callback_targets": targets,
    }
    fixture_path = OUT / f"{case['name']}.json"
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n")
    specs.append(str(fixture_path))
    manifest_cases.append({
        "id": case["name"], "run_id": run_id,
        "source_build": str(build_path.relative_to(ROOT)), "source_build_sha256": sha(build_path),
        "source_raw": str(raw_path.relative_to(ROOT)), "source_raw_sha256": sha(raw_path),
        "source_fixture": str(case["fixture"].relative_to(ROOT)) if case["fixture"] else "build.move_case",
        "source_slot": case["slot"], "target_frames": case["frames"],
        "fixture": str(fixture_path.relative_to(ROOT)), "fixture_sha256": sha(fixture_path),
        "configuration": build["configuration"], "move_case": move,
        "observed_source_phases": found,
    })
(HERE / "four-body-r01-paths.json").write_text(json.dumps(specs, ensure_ascii=False, indent=2) + "\n")
(HERE / "four-body-r01-preflight.json").write_text(json.dumps({
    "schema": "lee-callback-four-body-r01-preflight",
    "native_hashes": {
        path: sha(ROOT / path) for path in [
            "godot/tests/lee_callback_exact_probe.gd", "godot/fighter_runtime.gd",
            "godot/main.gd", "godot/helper_runtime.gd", "godot/source_callback_registry.gd",
            "godot/generated/main/execution_profile.json",
        ]
    },
    "cases": manifest_cases,
}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"cases": [item["name"] for item in CASES], "preflight": "four-body-r01-preflight.json"}))
