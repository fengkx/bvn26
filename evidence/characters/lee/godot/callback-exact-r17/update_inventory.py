#!/usr/bin/env python3
"""Derive r17 inventory by applying the verified frame-62 comparison."""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
source_path = ROOT / "evidence/characters/lee/godot/callback-exact-r16/pending-inventory-current-r16.json"
inventory = json.loads(source_path.read_text())
comparison = json.loads((HERE / "comparison.json").read_text())
assert comparison["status"] == "exact_0diff"
assert comparison["case_id"] == "frame62-updash-airattack-r04"
assert comparison["fields"] == ["source_frame", "entering", "decoded_action", "decoded_ql"]
assert len(comparison["source_events"]) == len(comparison["native_events"]) == 4
assert comparison["differences"] == []

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

source_entry = next(row for row in inventory["entries"] if row["source_frame"] == 62 and row["kind"] == "frame_action" and row["slot"] == "p1")
assert source_entry["status"] == "remaining"
source_entry["status"] = "native_matched"
source_entry["source_raw_captures"] = [comparison["source"]["raw"].removesuffix("/events.jsonl")]
source_entry["observed_slots"] = ["p1"]
source_entry["lee_slots_observed"] = ["p1"]
source_entry.pop("remaining_reason", None)
source_entry["notes"] = "Same-source-fixture bounded callback comparison; only the four listed callback fields are accepted."
source_entry["matched_fields"] = ["source_frame", "entering", "action", "ql"]
source_entry["differences"] = []
source_entry["godot_exact_scope"] = {
    "artifact": "evidence/characters/lee/godot/callback-exact-r17/comparison.json",
    "case_id": comparison["case_id"],
    "fields": ["source_frame", "entering", "action", "ql"],
    "source_event_count_for_frame": 2,
    "differences": [],
}
source_entry["native_provenance"] = {
    "fixture": comparison["native"]["fixture"],
    "fixture_sha256": comparison["native"]["fixture_sha256"],
    "source_raw": comparison["source"]["raw"],
    "source_raw_sha256": comparison["source"]["raw_sha256"],
    "source_build": comparison["source"]["build"],
    "source_build_sha256": comparison["source"]["build_sha256"],
    "native_log": comparison["native"]["engine_log"],
    "native_log_sha256": comparison["native"]["engine_log_sha256"],
    "runner_sha256": comparison["native"]["runner_sha256"],
    "runtime_file_hashes": comparison["native"]["runtime_hashes"],
    "input_match": comparison["native"]["fixture_inputs_setup_helpers_match_source"],
    "build_status_field": comparison["source"]["build_status_field"],
    "source_run_id_bound_to_raw": comparison["source"]["run_id_bound_raw"],
}

counts = Counter(row["status"] for row in inventory["entries"])
inventory["schema"] = "lee-callback-inventory-current-r17"
inventory["scope"] = (
    "Current-derived 49-row callback inventory through r17. Native matches are bounded to same-source-fixture "
    "callback comparisons, not full-state or full-role parity. R17 adds P1 frame62 to the accepted set after "
    "an exact four-field comparison against its actual source build/raw/fixture. R16 clip callbacks 1088/1098 "
    "remain source_only because native wrapper-return observations follow source clip removal."
)
inventory["counts"] = {key: counts[key] for key in ("native_matched", "source_only", "remaining", "normal_input_unreachable")}
inventory["native_exact_current"] = (
    str(inventory.get("native_exact_current", ""))
    + "; evidence/characters/lee/godot/callback-exact-r17/comparison.json (P1 frame62 same-fixture four-field exact comparison)"
).strip("; ")
out = HERE / "pending-inventory-current-r17.json"
out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(inventory["counts"], ensure_ascii=False))
