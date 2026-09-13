#!/usr/bin/env python3
"""Capture and summarize an ordered set of Rukia hit-test geometry builds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number  # noqa: E402


RECEIVER_FIELDS = (
    "fight_tick", "parent_name", "parent_frame", "receiver_name", "receiver_frame",
    "attack_key", "attack_name", "attack_frame", "hit_test",
    "receiver_x", "receiver_y", "receiver_xscale", "receiver_yscale",
    "attack_x", "attack_y", "attack_xscale", "attack_yscale",
    "receiver_local_xmin", "receiver_local_ymin", "receiver_local_xmax", "receiver_local_ymax",
    "attack_local_xmin", "attack_local_ymin", "attack_local_xmax", "attack_local_ymax",
    "receiver_game_xmin", "receiver_game_ymin", "receiver_game_xmax", "receiver_game_ymax",
    "attack_game_xmin", "attack_game_ymin", "attack_game_xmax", "attack_game_ymax",
    "receiver_root_xmin", "receiver_root_ymin", "receiver_root_xmax", "receiver_root_ymax",
    "attack_root_xmin", "attack_root_ymin", "attack_root_xmax", "attack_root_ymax",
    "receiver_matrix_a", "receiver_matrix_b", "receiver_matrix_c", "receiver_matrix_d",
    "receiver_matrix_tx", "receiver_matrix_ty",
    "attack_matrix_a", "attack_matrix_b", "attack_matrix_c", "attack_matrix_d",
    "attack_matrix_tx", "attack_matrix_ty",
    "game_matrix_a", "game_matrix_b", "game_matrix_c", "game_matrix_d",
    "game_matrix_tx", "game_matrix_ty",
)


def number(value: str) -> float:
    return decode_number(value)


def summarize(build: Path, capture_file: Path) -> dict:
    metadata = json.loads((build / "build.json").read_text())
    run_id = metadata["run_id"]
    events = []
    for line in capture_file.read_text().splitlines():
        fields = line.split("|", 7)
        if len(fields) != 8 or fields[0] != "AIREF" or fields[1] != run_id:
            continue
        events.append({
            "sequence": int(fields[2]),
            "display_tick": int(fields[4]),
            "fight_tick": int(fields[5]),
            "kind": fields[6],
            "value": fields[7],
        })

    done = any(event["kind"] == "done" for event in events)
    if not done:
        raise ValueError(f"Incomplete capture for {run_id}: no done event")

    receiver_events = []
    for event in events:
        if event["kind"] != "rukia_receiver_test":
            continue
        values = event["value"].split(",")
        if len(values) != len(RECEIVER_FIELDS):
            raise ValueError(
                f"Unexpected receiver event width for {run_id}: "
                f"{len(values)} != {len(RECEIVER_FIELDS)}"
            )
        decoded = {}
        for field, value in zip(RECEIVER_FIELDS, values):
            if field in ("parent_name", "receiver_name", "attack_key", "attack_name", "hit_test"):
                decoded[field] = value
            else:
                decoded[field] = number(value)
        decoded.update(sequence=event["sequence"], display_tick=event["display_tick"])
        decoded["x_gap_game"] = decoded["receiver_game_xmin"] - decoded["attack_game_xmax"]
        decoded["x_gap_root"] = decoded["receiver_root_xmin"] - decoded["attack_root_xmax"]
        decoded["y_overlap_game"] = min(
            decoded["receiver_game_ymax"], decoded["attack_game_ymax"]
        ) - max(decoded["receiver_game_ymin"], decoded["attack_game_ymin"])
        receiver_events.append(decoded)

    clocks = []
    for event in events:
        if event["kind"] == "clock":
            index, site, value = event["value"].split(",", 2)
            clocks.append({"index": int(index), "site": site, "value_ms": int(value)})

    return {
        "run_id": run_id,
        "fixture_id": (metadata.get("move_case") or {}).get("id"),
        "source_rukia_sha256": metadata.get("sources_sha256", {}).get("game/fighter/rukia.swf"),
        "case_setup": metadata.get("geometry_probe", {}).get("case_setup",
                                                              (metadata.get("move_case") or {}).get("setup")),
        "case_inputs": metadata.get("geometry_probe", {}).get("case_inputs",
                                                               (metadata.get("move_case") or {}).get("inputs")),
        "event_count": len(events),
        "completed": done,
        "instrumentation_note": (
            "The source hitTest is evaluated once and its result feeds the original branch. "
            "Diagnostic bounds/matrix logging runs afterward and may affect wall-clock timing; "
            "recorded event timestamps and any source clock tape must be retained."
        ),
        "receiver_test_count": len(receiver_events),
        "receiver_tests": receiver_events,
        "clock_count": len(clocks),
        "clock_tape": clocks,
        "capture": str(capture_file.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--player-app", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("builds", nargs="+", type=Path)
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("Timeout must be positive")

    capture_tool = ROOT / "tools/probes/capture_native_player.py"
    summaries = []
    for build in args.builds:
        build = build.resolve()
        metadata = json.loads((build / "build.json").read_text())
        run_id = metadata["run_id"]
        capture_dir = build.parent / (run_id + "-capture")
        if capture_dir.exists():
            raise FileExistsError(f"Capture already exists: {capture_dir}")
        capture_dir.mkdir(parents=True)
        capture_file = capture_dir / "original.log"
        subprocess.run([
            sys.executable, str(capture_tool),
            "--player-app", str(args.player_app.resolve()),
            "--allow-window-activation", "--timeout", str(args.timeout),
            str(build), str(capture_file),
        ], cwd=ROOT, check=True)
        summary = summarize(build, capture_file)
        summary_path = capture_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        summaries.append(summary)

    print(json.dumps({"runs": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
