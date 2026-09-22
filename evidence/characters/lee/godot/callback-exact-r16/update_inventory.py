#!/usr/bin/env python3
"""Record r16 source evidence and nonmatching native clip attempts."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
report = json.loads((HERE / "comparison.json").read_text())
source_inventory = ROOT / "evidence/characters/lee/callback-exact-r01/pending-inventory-current-r15.json"
inventory = json.loads(source_inventory.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


required_attempts = {
    "DefineSprite_518/frame_1088/PlaceObject2_18_29/CLIPACTIONRECORD onClipEvent(enterFrame).as",
    "DefineSprite_518/frame_1098/PlaceObject2_18_29/CLIPACTIONRECORD onClipEvent(enterFrame).as",
}
attempted = set()
for case in report["results"]:
    pre = next(row for row in json.loads((HERE / "preflight.json").read_text())["cases"] if row["case_id"] == case["case_id"])
    for target in case["target_comparisons"]:
        path = target["source_path"]
        if path not in required_attempts:
            continue
        attempted.add(path)
        entry = next(row for row in inventory["entries"] if row["source_path"] == path and row["kind"] == "clip_action")
        entry["source_raw_captures"] = sorted(set(entry.get("source_raw_captures", []) + [pre["source_raw"]]))
        entry["observed_slots"] = sorted(set(entry.get("observed_slots", []) + [pre["source_slot"]]))
        entry["lee_slots_observed"] = sorted(set(entry.get("lee_slots_observed", []) + [pre["source_slot"]]))
        # Keep exact parity closed until the wrapper-return discrepancy is resolved.
        entry["status"] = "source_only"
        entry["remaining_reason"] = "Same-input native clip proxy observed; exact callback marker comparison differs by one native wrapper-return event at source clip removal. No parity promotion."
        entry["source_only_provenance"] = {
            "source_run_id": pre["run_id"],
            "source_raw": pre["source_raw"],
            "source_raw_sha256": pre["source_raw_sha256"],
            "source_build": pre["source_build"],
            "source_build_sha256": pre["source_build_sha256"],
            "source_fixture": pre["source_fixture"],
            "source_fixture_sha256": pre["source_fixture_sha256"],
            "source_instrumentation": pre["source_instrumentation"],
            "source_instrumentation_sha256": pre["source_instrumentation_sha256"],
            "source_output_main_sha256": pre["source_output_main_sha256"],
            "source_build_config": pre["source_build_config"],
            "source_move_case": pre["source_move_case"],
        }
        entry["native_probe_attempt"] = {
            "artifact": "evidence/characters/lee/godot/callback-exact-r16/comparison.json",
            "case_id": case["case_id"],
            "status": target["status"],
            "fields": target["fields"],
            "source_event_count": len(target["source_events"]),
            "native_event_count": len(target["native_events"]),
            "common_prefix_event_count": target["common_prefix_event_count"],
            "clock_cadence_match": target["clock_cadence_match"],
            "native_minus_source_tick_offset": target["native_minus_source_tick_offset"],
            "differences": target["differences"],
            "observer_note": target["note"],
        }
        entry["notes"] = (
            "Same-source-input native run exists but is not exact: all source observations align in the common prefix; "
            "native test proxy adds one exit/return observation after clip removal. The wrapper return is not treated "
            "as a source callback marker or as proof the target remains alive."
        )
if attempted != required_attempts:
    raise SystemExit(f"r16 did not address exactly the requested source clips: {attempted}")

counts = Counter(entry["status"] for entry in inventory["entries"])
inventory["schema"] = "lee-callback-inventory-current-r16"
inventory["scope"] = (
    "Current-derived 49-row callback inventory through r16. Exact body callback matches remain bounded to their same-source-run "
    "four-field comparisons. R15 P2 frame1133 clip remains exact within its five-field scope. R16 performed same-input "
    "native attempts for P1 frame1088 and P2 frame1098 clip callbacks, but retained both as source_only because native proxy "
    "return observations exceed the source marker tape by one at clip removal. Source P1 frame1088 payload field 6 reports "
    "P2 frame and is not misreported as the P1 parent frame. This is not full-state or full-role parity."
)
inventory["counts"] = {key: counts[key] for key in (
    "native_matched", "source_only", "remaining", "normal_input_unreachable")}
inventory["native_exact_current"] = (
    str(inventory.get("native_exact_current", ""))
    + "; evidence/characters/lee/godot/callback-exact-r16/comparison.json (two same-input clip attempts; both remain source-only due extra native wrapper-return event)"
).strip("; ")
out = HERE / "pending-inventory-current-r16.json"
out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(inventory["counts"], ensure_ascii=False))
