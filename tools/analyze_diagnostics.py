#!/usr/bin/env python3
"""Summarize and compare BVN Web diagnostics exports without claiming replay parity."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


VOLATILE_EVENT_FIELDS = {
    "seq", "monoMs", "receivedAt", "receivedMonoMs", "buildID", "runId", "matchId",
}


def load_report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read diagnostics JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Diagnostics report must be an object: {path}")
    version = value.get("schemaVersion", 1)
    if version not in (1, 2):
        raise ValueError(f"Unsupported diagnostics schemaVersion {version!r}: {path}")
    if not isinstance(value.get("entries", []), list):
        raise ValueError(f"entries must be an array: {path}")
    if version == 2 and not isinstance(value.get("runtime", {}), dict):
        raise ValueError(f"runtime must be an object in schemaVersion 2: {path}")
    return value


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration_ms(start: Any, end: Any) -> int | None:
    first, last = _parse_timestamp(start), _parse_timestamp(end)
    if first is None or last is None:
        return None
    return max(0, int((last - first).total_seconds() * 1000))


def legacy_combat_events(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract old console-encoded COMBAT_EVENT records without inventing fight ticks."""
    events: list[dict[str, Any]] = []
    for index, entry in enumerate(report.get("entries", [])):
        if not isinstance(entry, dict):
            continue
        message = entry.get("message")
        prefix = "COMBAT_EVENT "
        if not isinstance(message, str) or not message.startswith(prefix):
            continue
        try:
            payload = json.loads(message[len(prefix):])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append({
                "origin": "legacy_console",
                "entryIndex": index,
                "time": entry.get("time"),
                "type": payload.get("event", "unknown"),
                "payload": payload,
            })
    return events


def _runtime_snapshot(report: dict[str, Any]) -> dict[str, Any] | None:
    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        return None
    snapshot = runtime.get("snapshot")
    if not isinstance(snapshot, dict):
        return None
    match = snapshot.get("match")
    return match if isinstance(match, dict) else snapshot


def _players(snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not snapshot:
        return []
    value = snapshot.get("players", [])
    if isinstance(value, dict):
        return [dict(player, slot=player.get("slot", slot)) for slot, player in value.items() if isinstance(player, dict)]
    if isinstance(value, list):
        return [player for player in value if isinstance(player, dict)]
    return []


def _runtime_events(report: dict[str, Any]) -> list[dict[str, Any]]:
    runtime = report.get("runtime")
    events = runtime.get("events", []) if isinstance(runtime, dict) else []
    return [event for event in events if isinstance(event, dict)]


def _replayability(report: dict[str, Any], snapshot: dict[str, Any] | None) -> dict[str, Any]:
    runtime = report.get("runtime")
    warnings: list[str] = []
    if report.get("schemaVersion", 1) < 2 or not isinstance(runtime, dict):
        warnings.append("Schema v1 contains console entries only; it has no structured input/random tape or checkpoint.")
        return {"exactReplayCandidate": False, "warnings": warnings}

    buffer = runtime.get("buffer", {})
    if not isinstance(buffer, dict):
        buffer = {}
    replay = snapshot.get("replayability", {}) if snapshot else {}
    random_state = snapshot.get("random", {}) if snapshot else {}
    clock_state = snapshot.get("clock", {}) if snapshot else {}
    if not snapshot:
        warnings.append("No runtime snapshot was captured.")
    if runtime.get("snapshotStatus") != "acknowledged":
        warnings.append(f"Snapshot status is {runtime.get('snapshotStatus', 'missing')}; export did not receive a current-state acknowledgement.")
    if replay.get("completeCheckpoint") is not True:
        warnings.append("The snapshot is diagnostic state, not a complete scene-restoration checkpoint.")
    if replay.get("randomCapturedFromStart") is not True or random_state.get("complete") is False:
        warnings.append("Random history is not confirmed complete from match start.")
    if replay.get("clockCapturedFromStart") is not True or clock_state.get("complete") is False:
        warnings.append("Clock/timer history is not confirmed complete from match start.")
    if int(buffer.get("retainedEvents", len(_runtime_events(report))) or 0) == 0:
        warnings.append("No structured runtime events were retained.")
    dropped = buffer.get("dropped", {})
    if isinstance(dropped, dict) and any(int(value or 0) for value in dropped.values()):
        warnings.append("The bounded runtime event window dropped older events.")
    if int(buffer.get("rejectedEvents", 0) or 0) > 0:
        warnings.append("At least one runtime event was rejected by size or format limits.")
    if runtime.get("inputTape") is None:
        warnings.append("No input tape is present; exact input replay is unavailable.")
    elif not runtime.get("inputTape"):
        warnings.append("The retained input tape is empty; confirm that player input was consumed during the capture.")
    return {"exactReplayCandidate": False, "warnings": warnings}


def _fighter_pause_notes(players: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    for player in players:
        state = player.get("state", player)
        if isinstance(state, dict) and "zhanting" in state:
            slot = player.get("slot", "unknown")
            notes.append(f"{slot}.zhanting is a fighter-local field; do not interpret it as global pause.")
    return notes


def analyze_report(report: dict[str, Any], source_path: str | None = None) -> dict[str, Any]:
    version = report.get("schemaVersion", 1)
    entries = [entry for entry in report.get("entries", []) if isinstance(entry, dict)]
    levels = Counter(str(entry.get("level", "unknown")) for entry in entries)
    legacy_events = legacy_combat_events(report)
    legacy_types = Counter(str(event.get("type", "unknown")) for event in legacy_events)
    runtime_events = _runtime_events(report)
    runtime_types = Counter(str(event.get("type", "unknown")) for event in runtime_events)
    runtime = report.get("runtime", {}) if isinstance(report.get("runtime"), dict) else {}
    snapshot = _runtime_snapshot(report)
    players = _players(snapshot)
    build = report.get("build", {}) if isinstance(report.get("build"), dict) else {}
    incidents = runtime.get("criticalIncidents", [])
    if not isinstance(incidents, list):
        incidents = []

    return {
        "source": source_path,
        "schemaVersion": version,
        "runId": report.get("runId"),
        "startedAt": report.get("startedAt"),
        "exportedAt": report.get("exportedAt"),
        "durationMs": _duration_ms(report.get("startedAt"), report.get("exportedAt")),
        "page": report.get("page"),
        "build": {
            "status": build.get("status", "unknown"),
            "buildID": build.get("buildID"),
            "sidecarBuildID": build.get("sidecarBuildID"),
            "gitCommit": build.get("gitCommit"),
            "dirty": build.get("dirty"),
            "resourceVersion": build.get("resourceVersion"),
            "pckSha256": build.get("pckSha256"),
            "pckHashKind": build.get("pckHashKind"),
        },
        "entries": {
            "count": len(entries),
            "dropped": report.get("droppedEntries", 0),
            "levels": dict(sorted(levels.items())),
            "errors": [
                {"time": entry.get("time"), "message": str(entry.get("message", ""))[:500]}
                for entry in entries if entry.get("level") == "error"
            ],
        },
        "legacyCombatEvents": {
            "count": len(legacy_events),
            "types": dict(sorted(legacy_types.items())),
            "first": legacy_events[0] if legacy_events else None,
            "last": legacy_events[-1] if legacy_events else None,
            "fightTickAvailable": False,
        },
        "runtime": {
            "snapshotStatus": runtime.get("snapshotStatus"),
            "eventCount": len(runtime_events),
            "eventTypes": dict(sorted(runtime_types.items())),
            "inputCount": len(runtime.get("inputTape", [])) if isinstance(runtime.get("inputTape"), list) else None,
            "buffer": runtime.get("buffer"),
            "criticalEvents": runtime.get("criticalEvents", []),
            "criticalIncidents": [
                {
                    "status": incident.get("status"),
                    "trigger": _event_brief(incident.get("trigger")),
                    "eventCount": len(incident.get("events", [])) if isinstance(incident.get("events"), list) else 0,
                    "droppedEvents": incident.get("droppedEvents", 0),
                    "windowMs": incident.get("windowMs"),
                }
                for incident in incidents if isinstance(incident, dict)
            ],
            "match": {
                key: snapshot.get(key)
                for key in ("matchId", "mode", "modeName", "map", "fightTick", "physicsHz", "p1cpu", "p2cpu")
                if snapshot and key in snapshot
            },
            "players": [
                {
                    key: player.get(key)
                    for key in ("slot", "fighter", "form", "resourcePath", "action", "sourceFrame", "hp", "energy", "x", "y", "facing", "bs", "hited", "zhanting", "timelinePlaying", "helper", "state")
                    if key in player
                }
                for player in players
            ],
            "pause": snapshot.get("pause") if snapshot else None,
            "random": snapshot.get("random") if snapshot else None,
            "clock": snapshot.get("clock") if snapshot else None,
            "inputTape": runtime.get("inputTape"),
        },
        "replayability": _replayability(report, snapshot),
        "notes": _fighter_pause_notes(players),
    }


def _event_brief(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    return {
        key: event.get(key)
        for key in ("seq", "type", "fightTick", "origin", "shellSeq", "receivedAt", "payload")
        if key in event
    }


def _canonical_event(event: dict[str, Any], legacy: bool = False) -> Any:
    if legacy:
        return {
            "type": event.get("type"),
            "payload": event.get("payload"),
        }
    return {key: value for key, value in event.items() if key not in VOLATILE_EVENT_FIELDS}


def _first_json_difference(left: Any, right: Any, path: str = "$") -> dict[str, Any] | None:
    if type(left) is not type(right):
        return {"path": path, "left": left, "right": right}
    if isinstance(left, dict):
        keys = sorted(set(left) | set(right))
        for key in keys:
            if key not in left or key not in right:
                return {"path": f"{path}.{key}", "left": left.get(key, "<missing>"), "right": right.get(key, "<missing>")}
            difference = _first_json_difference(left[key], right[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(left, list):
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            difference = _first_json_difference(left_item, right_item, f"{path}[{index}]")
            if difference:
                return difference
        if len(left) != len(right):
            return {"path": f"{path}.length", "left": len(left), "right": len(right)}
        return None
    if left != right:
        return {"path": path, "left": left, "right": right}
    return None


def compare_reports(left: dict[str, Any], right: dict[str, Any], left_path: str | None = None, right_path: str | None = None) -> dict[str, Any]:
    left_runtime = _runtime_events(left)
    right_runtime = _runtime_events(right)
    left_legacy = not left_runtime and bool(legacy_combat_events(left))
    right_legacy = not right_runtime and bool(legacy_combat_events(right))
    left_events = left_runtime or legacy_combat_events(left)
    right_events = right_runtime or legacy_combat_events(right)
    first_event_difference = None
    for index in range(min(len(left_events), len(right_events))):
        a = _canonical_event(left_events[index], left_legacy)
        b = _canonical_event(right_events[index], right_legacy)
        if a != b:
            first_event_difference = {
                "index": index,
                "left": _event_brief(left_events[index]) if not left_legacy else left_events[index],
                "right": _event_brief(right_events[index]) if not right_legacy else right_events[index],
            }
            break
    if first_event_difference is None and len(left_events) != len(right_events):
        index = min(len(left_events), len(right_events))
        first_event_difference = {
            "index": index,
            "left": _event_brief(left_events[index]) if index < len(left_events) and not left_legacy else left_events[index] if index < len(left_events) else None,
            "right": _event_brief(right_events[index]) if index < len(right_events) and not right_legacy else right_events[index] if index < len(right_events) else None,
            "reason": "event_stream_length_differs",
        }

    left_snapshot, right_snapshot = _runtime_snapshot(left), _runtime_snapshot(right)
    snapshot_difference = None
    if left_snapshot is not None or right_snapshot is not None:
        snapshot_difference = _first_json_difference(left_snapshot, right_snapshot)
    return {
        "mode": "ordered diagnostic evidence comparison; not a source-parity verdict",
        "left": {"path": left_path, "schemaVersion": left.get("schemaVersion", 1), "runId": left.get("runId"), "build": (left.get("build") or {}).get("status", "unknown")},
        "right": {"path": right_path, "schemaVersion": right.get("schemaVersion", 1), "runId": right.get("runId"), "build": (right.get("build") or {}).get("status", "unknown")},
        "eventSource": "runtime" if left_runtime and right_runtime else "legacy_console" if left_legacy and right_legacy else "mixed_or_unavailable",
        "leftEventCount": len(left_events),
        "rightEventCount": len(right_events),
        "firstEventDifference": first_event_difference,
        "firstSnapshotDifference": snapshot_difference,
        "limitations": [
            "Event comparison ignores run/build IDs and wall/monotonic timestamps.",
            "Legacy COMBAT_EVENT records have no global fightTick; entry order is not an exact simulation clock.",
            "A matching diagnostic stream does not establish source-game parity or replayability.",
        ],
    }


def _print_result(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="summarize a v1/v2 diagnostics export")
    analyze.add_argument("report", type=Path)
    analyze.add_argument("--json", action="store_true", help="emit machine-readable JSON (default output is also JSON)")
    compare = commands.add_parser("compare", help="show the first ordered event and snapshot differences")
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)
    compare.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "analyze":
            report = load_report(args.report)
            _print_result(analyze_report(report, str(args.report)), args.json)
        elif args.command == "compare":
            left, right = load_report(args.left), load_report(args.right)
            _print_result(compare_reports(left, right, str(args.left), str(args.right)), args.json)
        else:
            raise AssertionError(f"Unhandled command {args.command}")
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
