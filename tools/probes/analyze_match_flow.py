"""Summarize observed match transitions without claiming native-port parity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FIELDS = ("root_frame", "rounds", "p1ws", "p2ws", "gametime", "to", "paused",
          "game_paused", "ko_frame", "timeout_frame", "timeout_played", "ready_frame")


def scalar(value: str):
    if value == "undefined":
        return None
    if value in ("true", "false"):
        return value == "true"
    return int(value)


def analyze(directory: Path) -> dict:
    summary = json.loads((directory / "summary.json").read_text())
    assert summary["status"] == "original_capture_completed_not_port_parity"
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    records = []
    for event in events:
        if event["kind"] != "match":
            continue
        values = event["value"].split(",")
        assert len(values) == len(FIELDS) + 1, event
        records.append({"sequence": event["sequence"], "time_ms": event["time_ms"],
                        "display_tick": event["display_tick"], "fight_tick": event["fight_tick"],
                        "site": values[0], **dict(zip(FIELDS, map(scalar, values[1:])))})
    assert records, "Capture has no match-flow instrumentation"
    callbacks = []
    pending = None
    for record in records:
        if record["site"] == "timer_enter":
            assert pending is None, "Nested/unpaired countdown callback"
            pending = record
        elif record["site"] == "timer_exit":
            assert pending is not None, "Countdown exit without entry"
            callbacks.append({"enter": pending, "exit": record})
            pending = None
    assert pending is None, "Capture ends inside countdown callback"
    transitions = []
    previous = None
    for record in records:
        if record["site"] != "root":
            continue
        signature = tuple(record[k] for k in ("root_frame", "rounds", "p1ws", "p2ws", "to"))
        if signature != previous:
            transitions.append(record)
            previous = signature
    return {
        "status": "original_match_observation_not_port_parity",
        "run_id": summary["run_id"],
        "match_records": len(records),
        "timer_loads": [r for r in records if r["site"] == "timer_load"],
        "timer_callbacks": callbacks,
        "root_transitions": transitions,
        "timeline_events": [r for r in records if r["site"].startswith("DefineSprite_")],
        "nextfight_calls": [r for r in records if r["site"] == "nextfight_enter"],
        "limits": ["Snapshots observe authored callbacks; elapsed capture time includes instrumentation overhead.",
                   "A frame cap may cut off a round or match; transitions must be inspected for actual coverage.",
                   "No Godot match-flow comparison or presentation acceptance is performed here."],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.capture)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "timer_callbacks": len(result["timer_callbacks"]),
                      "nextfight_calls": len(result["nextfight_calls"]),
                      "root_transitions": result["root_transitions"]}, ensure_ascii=False))
