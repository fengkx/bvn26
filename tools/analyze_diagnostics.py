#!/usr/bin/env python3
"""Summarize and compare BVN Web diagnostics exports without claiming replay parity."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from build_web_diagnostics_metadata import sha256_tree


VOLATILE_EVENT_FIELDS = {
    "seq", "monoMs", "receivedAt", "receivedMonoMs", "buildID", "runId", "matchId",
    "origin", "shellSeq",
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


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


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


def _match_started_event(report: dict[str, Any]) -> dict[str, Any] | None:
    return next((event for event in _runtime_events(report) if event.get("type") == "match_started"), None)


def _contiguous_consumption(events: list[dict[str, Any]], event_type: str, state: dict[str, Any] | None) -> dict[str, Any]:
    indices = [
        _as_int(event.get("payload", {}).get("index"), -1)
        for event in events
        if event.get("type") == event_type and isinstance(event.get("payload"), dict)
    ]
    start_index = _as_int(state.get("absoluteIndex"), 0) if state else 0
    final_index = max(indices, default=start_index)
    contiguous = indices == list(range(start_index + 1, final_index + 1))
    return {"startIndex": start_index, "finalIndex": final_index, "observed": len(indices), "contiguous": contiguous}


def _input_coverage(report: dict[str, Any], recipe: dict[str, Any] | None) -> dict[str, Any]:
    runtime = report.get("runtime", {})
    events = runtime.get("inputTape")
    if not isinstance(events, list):
        events = [event for event in _runtime_events(report) if event.get("type") == "input_consumed"]
    events = [event for event in events if isinstance(event, dict)]
    per_tick: dict[int, set[str]] = {}
    for event in events:
        tick = event.get("fightTick")
        payload = event.get("payload", {})
        if isinstance(tick, int) and isinstance(payload, dict) and isinstance(payload.get("slot"), str):
            per_tick.setdefault(tick, set()).add(payload["slot"])
    if not per_tick:
        return {"count": len(events), "complete": False, "firstTick": None, "lastTick": None, "missing": []}

    snapshot = _runtime_snapshot(report)
    final_tick = _as_int(snapshot.get("fightTick"), max(per_tick)) if snapshot else max(per_tick)
    start_match = recipe or {}
    initial_tick = _as_int(start_match.get("fightTick"), 0)
    first_expected = initial_tick + 1
    required_slots = []
    for slot in ("p1", "p2"):
        if start_match.get(f"{slot}cpu") is not True:
            required_slots.append(slot)
    if not required_slots:
        required_slots = sorted({slot for slots in per_tick.values() for slot in slots})
    missing = [
        {"fightTick": tick, "slots": sorted(set(required_slots) - per_tick.get(tick, set()))}
        for tick in range(first_expected, final_tick + 1)
        if set(required_slots) - per_tick.get(tick, set())
    ]
    return {
        "count": len(events),
        "firstTick": min(per_tick),
        "lastTick": max(per_tick),
        "expectedFirstTick": first_expected,
        "expectedLastTick": final_tick,
        "slots": required_slots,
        "missing": missing[:20],
        "missingTickCount": len(missing),
        "complete": bool(required_slots) and min(per_tick) == first_expected and max(per_tick) >= final_tick and not missing,
    }


def _replayability(report: dict[str, Any], snapshot: dict[str, Any] | None) -> dict[str, Any]:
    runtime = report.get("runtime")
    warnings: list[str] = []
    if report.get("schemaVersion", 1) < 2 or not isinstance(runtime, dict):
        warnings.append("Schema v1 contains console entries only; it has no structured input/random tape or checkpoint.")
        return {"exactReplayCandidate": False, "freshStartRecipeAvailable": False,
                "executorEligibility": "unavailable", "warnings": warnings}

    buffer = runtime.get("buffer", {})
    if not isinstance(buffer, dict):
        buffer = {}
    start_event = _match_started_event(report)
    start_match = start_event.get("payload", {}).get("match") if start_event else None
    if not isinstance(start_match, dict):
        start_match = None
    replay = start_match.get("replayability", {}) if start_match else {}
    random_state = start_match.get("random", {}) if start_match else {}
    clock_state = start_match.get("clock", {}) if start_match else {}
    if not isinstance(replay, dict):
        replay = {}
    if not isinstance(random_state, dict):
        random_state = {}
    if not isinstance(clock_state, dict):
        clock_state = {}
    if not snapshot:
        warnings.append("No runtime snapshot was captured.")
    if runtime.get("snapshotStatus") != "acknowledged":
        warnings.append(f"Snapshot status is {runtime.get('snapshotStatus', 'missing')}; export did not receive a current-state acknowledgement.")
    recipe_available = bool(
        start_match
        and replay.get("canonicalInitialization") is True
        and isinstance(start_match.get("initialState"), dict)
    )
    if not recipe_available:
        warnings.append("No canonical match_started fresh-match recipe is present.")
    latest_replay = snapshot.get("replayability", {}) if snapshot else {}
    if snapshot and not recipe_available and isinstance(latest_replay, dict) and latest_replay.get("completeCheckpoint") is not True:
        warnings.append("The latest snapshot is not a complete scene-restoration checkpoint.")
    latest_random = snapshot.get("random", {}) if snapshot else {}
    latest_clock = snapshot.get("clock", {}) if snapshot else {}
    if not isinstance(latest_random, dict):
        latest_random = {}
    if not isinstance(latest_clock, dict):
        latest_clock = {}
    random_coverage = _contiguous_consumption(_runtime_events(report), "random_consumed", random_state)
    clock_coverage = _contiguous_consumption(_runtime_events(report), "clock_consumed", clock_state)
    random_complete = bool(recipe_available and replay.get("randomCapturedFromStart") is True
                           and random_coverage["contiguous"] and random_coverage["finalIndex"] == _as_int(latest_random.get("absoluteIndex"), random_coverage["finalIndex"]))
    clock_complete = bool(recipe_available and replay.get("clockCapturedFromStart") is True
                          and clock_coverage["contiguous"] and clock_coverage["finalIndex"] == _as_int(latest_clock.get("absoluteIndex"), clock_coverage["finalIndex"]))
    if not random_complete:
        warnings.append("Random consumption is not proven contiguous from the fresh-match recipe through the latest snapshot.")
    if not clock_complete:
        warnings.append("Clock/timer consumption is not proven contiguous from the fresh-match recipe through the latest snapshot.")
    input_coverage = _input_coverage(report, start_match)
    if not input_coverage["complete"]:
        warnings.append("Consumed player input does not cover every expected slot/tick from the fresh-match start.")
    if _as_int(buffer.get("retainedEvents", len(_runtime_events(report)))) == 0:
        warnings.append("No structured runtime events were retained.")
    dropped = buffer.get("dropped", {})
    if isinstance(dropped, dict) and any(_as_int(value) for value in dropped.values()):
        warnings.append("The bounded runtime event window dropped older events.")
    if _as_int(buffer.get("rejectedEvents", 0)) > 0:
        warnings.append("At least one runtime event was rejected by size or format limits.")
    dropped = runtime.get("droppedEvents", 0)
    if _as_int(dropped) > 0:
        warnings.append("Runtime event capture reports dropped events.")
    ring_drops = buffer.get("dropped", {})
    if not isinstance(ring_drops, dict):
        ring_drops = {}
    prerequisites = bool(recipe_available and input_coverage["complete"] and random_complete and clock_complete
                         and not any(_as_int(value) for value in ring_drops.values())
                         and _as_int(buffer.get("rejectedEvents", 0)) == 0 and _as_int(dropped) == 0)
    return {
        "exactReplayCandidate": False,
        "freshStartRecipeAvailable": recipe_available,
        "inputCoverage": input_coverage,
        "randomCoverage": random_coverage,
        "clockCoverage": clock_coverage,
        "freshReplayPrerequisitesComplete": prerequisites,
        "executorEligibility": "ready_for_executor" if prerequisites else "incomplete_capture",
        "warnings": warnings,
        "executorVerdict": "not_run",
    }


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
    replay_events = [
        event for event in runtime_events
        if isinstance(event.get("payload"), dict) and event["payload"].get("replay") is True
    ]
    replay_types = Counter(str(event.get("type", "unknown")) for event in replay_events)
    performance_events = [
        event for event in runtime_events
        if event.get("type") == "online_performance" and isinstance(event.get("payload"), dict)
    ]
    hit_events = [event for event in runtime_events if event.get("type") in {"hit_settled", "hit_settlement"}]
    last_hit = None
    if hit_events:
        event = hit_events[-1]
        payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        attack = source.get("attack") if isinstance(source.get("attack"), dict) else {}
        last_hit = {
            "fightTick": event.get("fightTick"),
            "slot": payload.get("slot"),
            "damage": payload.get("damage"),
            "defended": payload.get("defended"),
            "reaction": payload.get("reaction"),
            "source": {key: source.get(key) for key in ("kind", "slot", "action") if key in source},
            "attack": {key: attack.get(key) for key in ("instance_name", "damage") if key in attack},
        }
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
            "replayEvents": {
                "count": len(replay_events),
                "types": dict(sorted(replay_types.items())),
                "last": replay_events[-1] if replay_events else None,
            },
            "onlinePerformance": {
                "count": len(performance_events),
                "latest": performance_events[-1].get("payload") if performance_events else None,
            },
            "randomEventCount": runtime_types.get("random_consumed", 0),
            "clockEventCount": runtime_types.get("clock_consumed", 0),
            "inputCount": len(runtime.get("inputTape", [])) if isinstance(runtime.get("inputTape"), list) else None,
            "lastHit": last_hit,
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
        "notes": _fighter_pause_notes(players) + _legacy_pause_notes(legacy_events),
    }


def _legacy_pause_notes(events: list[dict[str, Any]]) -> list[str]:
    if any("zhanting" in event.get("payload", {}) for event in events):
        return ["Legacy COMBAT_EVENT.zhanting is fighter-local; it does not establish global pause state."]
    return []


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
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        return None if float(left) == float(right) else {"path": path, "left": left, "right": right}
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
        "left": {"path": left_path, "schemaVersion": left.get("schemaVersion", 1), "runId": left.get("runId"), "build": (left.get("build") if isinstance(left.get("build"), dict) else {}).get("status", "unknown")},
        "right": {"path": right_path, "schemaVersion": right.get("schemaVersion", 1), "runId": right.get("runId"), "build": (right.get("build") if isinstance(right.get("build"), dict) else {}).get("status", "unknown")},
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


def replay_preflight(report: dict[str, Any], project_root: Path) -> list[str]:
    problems: list[str] = []
    if report.get("schemaVersion") != 2:
        return ["Only structured schema v2 reports can be replayed."]
    replay = analyze_report(report)["replayability"]
    if replay.get("executorEligibility") != "ready_for_executor":
        problems.append("Capture lacks a complete fresh-start recipe/input/random/clock window.")

    build = report.get("build", {})
    if not isinstance(build, dict) or build.get("status") != "match":
        problems.append("Build identity is unknown or mismatched; a matching sidecar is required.")
    elif build.get("buildID") != build.get("sidecarBuildID"):
        problems.append("Embedded runtime build ID differs from the post-export sidecar.")
    pck_sha = build.get("pckSha256") if isinstance(build, dict) else None
    if not isinstance(build, dict) or build.get("pckHashKind") != "exported_artifact" or not isinstance(pck_sha, str) or not re.fullmatch(r"[a-f0-9]{64}", pck_sha):
        problems.append("The log has no verified exported-PCK SHA-256.")
    runtime_ids = {
        event.get("buildID") for event in _runtime_events(report)
        if event.get("origin", "runtime") == "runtime" and isinstance(event.get("buildID"), str) and event.get("buildID")
    }
    runtime = report.get("runtime", {})
    runtime_snapshot = runtime.get("snapshot", {}) if isinstance(runtime, dict) else {}
    if isinstance(runtime_snapshot, dict) and isinstance(runtime_snapshot.get("buildID"), str) and runtime_snapshot.get("buildID"):
        runtime_ids.add(runtime_snapshot["buildID"])
    if not runtime_ids or (isinstance(build, dict) and runtime_ids != {build.get("buildID")}):
        problems.append("Runtime events/snapshot do not prove the same embedded build ID as the export sidecar.")

    runtime_resource_versions: set[str] = set()
    match_started = _match_started_event(report)
    match_recipe = match_started.get("payload", {}).get("match") if match_started else None
    if isinstance(match_recipe, dict) and isinstance(match_recipe.get("resourceVersion"), str) and match_recipe["resourceVersion"]:
        runtime_resource_versions.add(match_recipe["resourceVersion"])
    snapshot_match = _runtime_snapshot(report)
    if snapshot_match and isinstance(snapshot_match.get("resourceVersion"), str) and snapshot_match["resourceVersion"]:
        runtime_resource_versions.add(snapshot_match["resourceVersion"])
    if not runtime_resource_versions or (isinstance(build, dict) and runtime_resource_versions != {build.get("resourceVersion")}):
        problems.append("Runtime match/snapshot resourceVersion does not prove the same generated resources as the export sidecar.")

    try:
        generated = project_root / "generated"
        current_resource_version = sha256_tree(generated, exclude={Path("build_metadata.json")})
        if build.get("resourceVersion") != current_resource_version:
            problems.append("Current generated resources do not match the log's resourceVersion.")
        metadata_path = generated / "build_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("schemaVersion") != 1:
            problems.append("Selected project has no supported embedded build metadata.")
        if metadata.get("buildID") != build.get("buildID"):
            problems.append("Selected project embedded buildID does not match the log and export sidecar.")
        if metadata.get("resourceVersion") != build.get("resourceVersion"):
            problems.append("Selected project embedded resourceVersion does not match the export sidecar.")
        expected_source_hash = metadata.get("sourceTreeSha256")
        if not isinstance(expected_source_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_source_hash):
            problems.append("Selected project's embedded source-tree hash is missing or invalid.")
        elif sha256_tree(project_root, exclude={Path("generated/build_metadata.json")}) != expected_source_hash:
            problems.append("Selected project files have changed since their embedded build metadata was prepared.")
    except OSError as error:
        problems.append(f"Cannot verify selected Godot project/build metadata: {error}")
    except json.JSONDecodeError as error:
        problems.append(f"Cannot read selected project's embedded build metadata: {error}")

    roster_path = project_root / "generated/main/character_selection/available.json"
    stage_catalog_path = project_root / "generated/stages/catalog/catalog.json"
    try:
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
        stage_catalog = json.loads(stage_catalog_path.read_text(encoding="utf-8"))
        fighter_map = roster.get("fighters", {})
        helper_map = roster.get("helpers", {})
        stages = stage_catalog.get("stages", [])
        maps = {stage.get("id") for stage in stages if isinstance(stage, dict)}
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"Cannot load the selected project's fighter/map catalogs: {error}")
        return problems

    start_event = _match_started_event(report)
    match = start_event.get("payload", {}).get("match") if start_event else None
    if not isinstance(match, dict):
        problems.append("No match_started recipe is available.")
        return problems
    mode = match.get("modeName")
    if mode != "versus" or match.get("mode") != 3:
        problems.append(f"Unsupported replay mode: {mode!r}.")
    for slot in ("p1", "p2"):
        if match.get(f"{slot}cpu") is not False:
            problems.append(f"{slot} must be a human-controlled player; AI input is not captured for replay.")
    if match.get("timerTape") or match.get("timerRecords"):
        problems.append("Timer tape replay is not supported by the fresh Main executor.")

    players = match.get("players", {})
    if isinstance(players, list):
        players = {str(player.get("slot", index)): player for index, player in enumerate(players) if isinstance(player, dict)}
    if not isinstance(players, dict) or set(players) != {"p1", "p2"}:
        problems.append("Replay requires exactly p1 and p2 in the match recipe.")
        return problems

    for slot in ("p1", "p2"):
        player = players.get(slot)
        if not isinstance(player, dict):
            problems.append(f"Missing {slot} player recipe.")
            continue
        fighter = player.get("fighter")
        fighter_aliases = dict(fighter_map)
        fighter_aliases.update({fighter_id: fighter_id for fighter_id in fighter_map.values()})
        for fighter_id_candidate in set(fighter_map.values()):
            fighter_json = project_root / f"generated/fighters/{fighter_id_candidate}/fighter.json"
            try:
                fighter_metadata = json.loads(fighter_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            display_name = fighter_metadata.get("display_name")
            if isinstance(display_name, str):
                fighter_aliases[display_name] = fighter_id_candidate
        fighter_id = fighter_aliases.get(fighter)
        if not fighter_id:
            problems.append(f"{slot} fighter {fighter!r} is not in the current available roster.")
        expected_fighter_path = f"res://generated/fighters/{fighter_id}" if fighter_id else None
        if player.get("resourcePath") != expected_fighter_path:
            problems.append(f"{slot} fighter resource path is not the catalog-resolved path.")
        if player.get("form") not in (None, "", "base"):
            problems.append(f"{slot} form {player.get('form')!r} is outside the supported base-form replay.")
        helper = player.get("helper")
        if isinstance(helper, dict) and helper.get("id"):
            helper_aliases = dict(helper_map)
            helper_aliases.update({helper_id: helper_id for helper_id in helper_map.values()})
            helper_id = helper_aliases.get(helper.get("id"))
            expected_helper_path = f"res://generated/helpers/{helper_id}" if helper_id else None
            if not helper_id or helper.get("resourcePath") != expected_helper_path:
                problems.append(f"{slot} helper is not resolved by the current available roster.")

    if match.get("map") not in maps:
        problems.append(f"Map {match.get('map')!r} is not in the current map catalog.")
    return problems


def run_replay(
    report_path: Path,
    report: dict[str, Any],
    *,
    godot_executable: str | None,
    project_path: Path,
    output_path: Path,
    log_path: Path | None,
    timeout_seconds: int,
) -> tuple[int, dict[str, Any]]:
    project_root = project_path.expanduser().resolve()
    repo_godot = Path(__file__).resolve().parent.parent / "godot"
    executor = repo_godot / "tests/diagnostic_replay_smoke.gd"
    if not (project_root / "project.godot").is_file():
        return 2, {"status": "rejected", "problems": [f"Not a Godot project: {project_root}"]}
    problems = replay_preflight(report, project_root)
    if problems:
        return 2, {"status": "rejected", "problems": problems}
    executable = godot_executable or shutil.which("godot") or shutil.which("godot4")
    if not executable or not Path(executable).is_file():
        return 2, {"status": "rejected", "problems": ["Pass --godot with the Godot 4.7.2 executable; no runnable Godot was found on PATH."]}
    if not executor.is_file():
        return 2, {"status": "rejected", "problems": [f"Replay executor is missing: {executor}"]}

    source_path = report_path.resolve()
    output_path = output_path.resolve()
    if output_path.exists():
        return 2, {"status": "rejected", "problems": [f"Refusing to overwrite replay output: {output_path}"]}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path is None:
        log_path = output_path.with_suffix(output_path.suffix + ".godot.log")
    log_path = log_path.resolve()
    if log_path.exists():
        return 2, {"status": "rejected", "problems": [f"Refusing to overwrite Godot log: {log_path}"]}

    command = [
        str(Path(executable).resolve()), "--headless", "--path", str(project_root),
        "-s", str(executor.resolve()), "--log-file", str(log_path), "--",
        str(source_path), str(output_path),
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as error:
        return 2, {"status": "executor_error", "command": command, "error": str(error), "log": str(log_path)}
    try:
        result = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        if completed.returncode != 0:
            return 2, {
                "status": "executor_error", "returnCode": completed.returncode,
                "stdoutTail": completed.stdout[-3000:], "stderrTail": completed.stderr[-3000:],
                "log": str(log_path), "command": command,
                "error": f"Executor result missing or invalid: {error}",
            }
        return 2, {"status": "executor_error", "error": f"Executor result missing or invalid: {error}", "log": str(log_path), "command": command}
    if not isinstance(result, dict) or not isinstance(result.get("replay"), dict):
        return 2, {"status": "executor_error", "error": "Executor result has an unknown schema", "log": str(log_path)}
    replay_status = result["replay"].get("status", "unknown")
    if completed.returncode != 0 and replay_status == "exact_match":
        return 2, {
            "status": "executor_error", "returnCode": completed.returncode,
            "stdoutTail": completed.stdout[-3000:], "stderrTail": completed.stderr[-3000:],
            "log": str(log_path), "command": command,
            "error": "Executor reported exact_match but exited nonzero.",
            "executorResult": result,
        }
    return (0 if completed.returncode == 0 and replay_status == "exact_match" else 1), {
        "status": replay_status,
        "returnCode": completed.returncode,
        "executorResult": result,
        "source": str(source_path),
        "output": str(output_path),
        "log": str(log_path),
        "command": command,
        "stdoutTail": completed.stdout[-2000:],
        "stderrTail": completed.stderr[-2000:],
    }


def _print_result(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    elif "legacyCombatEvents" in value:
        build = value["build"]
        runtime = value["runtime"]
        print(f"BVN diagnostics schema v{value['schemaVersion']}  run={value.get('runId') or 'unknown'}")
        print(f"Build: {build['status']}  commit={build.get('gitCommit') or 'unknown'}  pck={build.get('pckSha256') or 'unknown'}")
        print(f"Legacy entries: {value['entries']['count']}  combat events: {value['legacyCombatEvents']['count']}  errors: {len(value['entries']['errors'])}")
        for error in value["entries"]["errors"][:5]:
            print(f"Error {error.get('time') or '?'}: {error['message'].replace(chr(10), ' ')[:240]}")
        if value["legacyCombatEvents"]["count"]:
            print(f"Legacy combat event types: {value['legacyCombatEvents']['types']}")
            latest = value["legacyCombatEvents"]["last"]
            payload = latest["payload"]
            print(f"Last legacy event: {latest.get('time')} {latest.get('type')} fighter={payload.get('fighter')} action={payload.get('action')} frame={payload.get('frame')} hp={payload.get('health')} bs={payload.get('bs')} zhanting={payload.get('zhanting')}")
        if runtime["eventCount"] or runtime["snapshotStatus"] is not None:
            match = runtime["match"]
            print(f"Runtime events: {runtime['eventCount']} {runtime['eventTypes']}  inputs: {runtime['inputCount']}  snapshot={runtime['snapshotStatus']}")
            replay_events = runtime.get("replayEvents", {})
            if replay_events.get("count", 0):
                print(f"Replay-tagged diagnostic events: {replay_events['count']} {replay_events.get('types', {})}; the console may still contain the original predicted event.")
            performance = runtime.get("onlinePerformance", {})
            latest_performance = performance.get("latest") if isinstance(performance, dict) else None
            if isinstance(latest_performance, dict):
                work = latest_performance.get("rollbackWork", {})
                work_delta = work.get("windowDelta", {}) if isinstance(work, dict) else {}
                sync = latest_performance.get("sync", {})
                ticks = sync.get("ticks", {}) if isinstance(sync, dict) else {}
                drains = sync.get("transportDrains", {}) if isinstance(sync, dict) else {}
                lead = sync.get("inputArrivalLead", {}) if isinstance(sync, dict) else {}
                advantage = sync.get("frameAdvantage", {}) if isinstance(sync, dict) else {}
                print(f"Online performance v{latest_performance.get('schemaVersion', '?')} windows: {performance.get('count', 0)}; rollbackWork delta={work_delta}")
                print("Sync window: "
                      f"tick messages={ticks.get('remoteMessages', 0)} corrections={ticks.get('corrections', 0)} "
                      f"p95/tick={ticks.get('remoteMessagesPerTick', {}).get('p95')} / {ticks.get('correctionsPerTick', {}).get('p95')}; "
                      f"drains={drains.get('count', 0)} messages={drains.get('messagesDelivered', 0)} corrections={drains.get('corrections', 0)} "
                      f"p95/drain={drains.get('messagesPerDrain', {}).get('p95')} / {drains.get('correctionsPerDrain', {}).get('p95')}; "
                      f"arrivalLead p5/p50/p95={lead.get('p5')}/{lead.get('p50')}/{lead.get('p95')}; "
                      f"frameAdvantage p50/p95/max={advantage.get('p50')}/{advantage.get('p95')}/{advantage.get('max')}")
            if match:
                print(f"Match: mode={match.get('modeName', match.get('mode'))} map={match.get('map')} tick={match.get('fightTick')}")
            for player in runtime["players"]:
                helper = player.get("helper")
                helper_id = helper.get("id") if isinstance(helper, dict) else None
                print(f"{player.get('slot', '?')}: {player.get('fighter', '?')} action={player.get('action')} frame={player.get('sourceFrame')} hp={player.get('hp')} energy={player.get('energy')} x/y=({player.get('x')},{player.get('y')}) helper={helper_id or 'none'}")
            print(f"Random records: {runtime['randomEventCount']}  clock records: {runtime['clockEventCount']}  last hit: {runtime['lastHit']}")
            if runtime["pause"] is not None:
                print(f"Pause: {runtime['pause']}")
            if runtime["buffer"]:
                print(f"Event window: {runtime['buffer'].get('coverageMs', 0)}ms  drops={runtime['buffer'].get('dropped', {})}")
            replay = value["replayability"]
            print(f"Fresh replay prerequisites: {replay.get('executorEligibility')}  input={replay.get('inputCoverage', {}).get('count', 0)} events/{replay.get('inputCoverage', {}).get('missingTickCount', 0)} missing ticks")
            for event in runtime["criticalEvents"][-5:]:
                print(f"Critical: {_event_brief(event)}")
        for note in value["notes"]:
            print(f"Note: {note}")
        for warning in value["replayability"]["warnings"]:
            print(f"Replay limit: {warning}")
    elif "firstEventDifference" in value:
        print(value["mode"])
        print(f"Events ({value['eventSource']}): {value['leftEventCount']} vs {value['rightEventCount']}")
        print(f"First event difference: {json.dumps(value['firstEventDifference'], ensure_ascii=False)}")
        print(f"First snapshot difference: {json.dumps(value['firstSnapshotDifference'], ensure_ascii=False)}")
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="summarize a v1/v2 diagnostics export")
    analyze.add_argument("report", type=Path)
    analyze.add_argument("--json", action="store_true", help="emit full machine-readable JSON")
    compare = commands.add_parser("compare", help="show the first ordered event and snapshot differences")
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)
    compare.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    replay = commands.add_parser("replay", help="run the fixed fresh-Main replay executor for an eligible v2 report")
    replay.add_argument("report", type=Path)
    replay.add_argument("--godot", help="Godot 4.7.2 executable; defaults to godot on PATH")
    replay.add_argument("--project", type=Path, default=Path(__file__).resolve().parent.parent / "godot",
                        help="Godot project copy with matching embedded build metadata (default: repository project)")
    replay.add_argument("--output", type=Path, required=True, help="new executor result JSON path (must not already exist)")
    replay.add_argument("--log-file", type=Path, help="Godot log path; defaults beside --output")
    replay.add_argument("--timeout", type=int, default=120, help="executor timeout in seconds")
    replay.add_argument("--json", action="store_true", help="emit machine-readable JSON")
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
        elif args.command == "replay":
            report = load_report(args.report)
            return_code, result = run_replay(
                args.report, report, godot_executable=args.godot,
                project_path=args.project,
                output_path=args.output, log_path=args.log_file,
                timeout_seconds=args.timeout,
            )
            _print_result(result, args.json)
            return return_code
        else:
            raise AssertionError(f"Unhandled command {args.command}")
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
