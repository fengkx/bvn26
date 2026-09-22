#!/usr/bin/env python3
"""Derive the current callback inventory with r15 clip evidence."""
import json
import hashlib
import sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[5]
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from event_tape import parse_event_line
inventory_path = root / "evidence/characters/lee/callback-exact-r01/pending-inventory-current-r14.json"
inventory = json.loads(inventory_path.read_text())
comparison = json.loads((here / "comparison.json").read_text())
clip_case = comparison["callback_comparison"]
if clip_case["status"] != "exact_0diff":
    raise SystemExit("r15 clip callback comparison is not exact")
if comparison["native_lifecycle_observation"]["status"] != "observed":
    raise SystemExit("r15 native lifecycle observation failed")

matched = 0
for entry in inventory["entries"]:
    if entry["kind"] != "clip_action" or int(entry["source_frame"]) != 1133 or entry.get("slot") != "p2":
        continue
    entry["status"] = "native_matched"
    entry["source_raw_captures"] = sorted(set(entry.get("source_raw_captures", []) + [
        comparison["source_provenance"]["raw"],
    ]))
    entry.pop("remaining_reason", None)
    entry["godot_exact_scope"] = {
        "artifact": "evidence/characters/lee/godot/callback-exact-r15/comparison.json",
        "case_id": comparison["case_id"],
        "kind": "clip_action",
        "fields": clip_case["fields"],
        "differences": [],
        "source_event_count": clip_case["source_count"],
        "native_event_count": clip_case["native_count"],
    }
    entry["native_provenance"] = {
        "fixture": comparison["native_provenance"]["fixture"],
        "fixture_sha256": comparison["native_provenance"]["fixture_sha256"],
        "source_raw": comparison["source_provenance"]["raw"],
        "source_raw_sha256": comparison["source_provenance"]["raw_sha256"],
        "source_build": comparison["source_provenance"]["build"],
        "source_build_sha256": comparison["source_provenance"]["build_sha256"],
        "native_log": "evidence/characters/lee/godot/callback-exact-r15/engine.log",
        "native_log_sha256": comparison["native_provenance"]["engine_log_sha256"],
        "runtime_file_hashes": comparison["runtime_files"],
        "callback_kind": "test-only clip controller proxy, inherited SourceCallbackRegistry.dispatch",
    }
    entry["matched_fields"] = clip_case["fields"]
    entry["differences"] = []
    entry["native_lifecycle_scope"] = comparison["native_lifecycle_observation"]
    matched += 1

if matched != 1:
    raise SystemExit(f"expected exactly one matching P2 frame1133 clip row, found {matched}")

for entry in inventory["entries"]:
    if int(entry["source_frame"]) == 1288 and entry["kind"] == "frame_action":
        raw = root / "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/events.jsonl"
        build_path = root / "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/build.json"
        fixture_path = root / "evidence/characters/lee/original/lee-callback-round-loss-failure-r06/fixture.json"
        build = json.loads(build_path.read_text())
        fixture = json.loads(fixture_path.read_text())
        rows = []
        for line in raw.read_text().splitlines():
            if not line.startswith(("AIREF|", "{")):
                continue
            event = parse_event_line(line)
            if not event or event.get("run_id") != "lee-callback-round-loss-failure-r06" or event.get("kind") != "body_boundary":
                continue
            values = str(event.get("value", "")).split(",")
            if len(values) >= 3 and values[0] == "p1" and values[1] == "1288":
                rows.append({"sequence": int(event["sequence"]), "values": values})
        if len(rows) != 2 or [row["values"][2] for row in rows] != ["true", "false"]:
            raise SystemExit("Lee r06 frame1288 callback marker did not validate")
        if build.get("run_id") != "lee-callback-round-loss-failure-r06" or fixture.get("id") != build.get("move_case", {}).get("id"):
            raise SystemExit("Lee r06 frame1288 build/fixture identity mismatch")
        entry["status"] = "source_only"
        entry["source_raw_captures"] = [str(raw.relative_to(root))]
        entry["observed_slots"] = ["p1"]
        entry["lee_slots_observed"] = ["p1"]
        entry["remaining_reason"] = "source callback observed in latest natural timeout fixture; no current-hash native exact comparison yet"
        entry["source_only_provenance"] = {
            "source_run_id": build["run_id"],
            "source_raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
            "source_build_sha256": hashlib.sha256(build_path.read_bytes()).hexdigest(),
            "source_fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
            "source_main_swf_sha256": build["outputs_sha256"]["game/main.swf"],
            "source_move_case": build["move_case"],
            "source_build_config": build["configuration"],
            "source_rows": rows,
            "scope_note": "Natural timeout failure callback after KO recovery and a later HP-based timeout decision; source-only until same-fixture native comparison.",
        }
    if int(entry["source_frame"]) == 1149 and entry["kind"] == "frame_action":
        entry["status"] = "normal_input_unreachable"
        entry.pop("remaining_reason", None)
        entry["source_reachability_audit"] = "evidence/characters/lee/source-entry-audit-62-738-1149-r01.md"
        entry["notes"] = "Static source control-flow audit: frame1144 unconditionally returns to standing before 1149; no gameplay label or numeric goto targets 1149."

counts = Counter(entry["status"] for entry in inventory["entries"])
inventory["schema"] = "lee-callback-inventory-current-r15"
inventory["scope"] = (
    "Current-derived 49-row inventory through r15. Body matches are same-source-run four-field comparisons "
        "(source_frame, entering, decoded action, decoded ql). The P2 frame1133 clip row is separately matched "
    "on source path, callback phase, slot, parent frame, and child local frame. P1 frame1149 is statically "
    "classified as normal-input-unreachable. Frame1288 remains pending because the current archived r06 raw has "
    "state samples but no body-boundary marker. This is not full-state or full-role parity."
)
inventory["counts"] = {key: counts[key] for key in (
    "native_matched", "source_only", "remaining", "normal_input_unreachable")}
inventory["native_exact_current"] = (
    str(inventory.get("native_exact_current", ""))
    + "; evidence/characters/lee/godot/callback-exact-r15/comparison.json (one clip-action row)"
).strip("; ")
out = root / "evidence/characters/lee/callback-exact-r01/pending-inventory-current-r15.json"
out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(inventory["counts"], ensure_ascii=False))
