#!/usr/bin/env python3
"""Derive the r09 inventory from the audited r08 inventory and r09 comparison."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[5]
here = Path(__file__).resolve().parent
prior = json.loads((root / "evidence/characters/lee/callback-exact-r01/pending-inventory-current-r08.json").read_text())
comparison = json.loads((here / "comparison.json").read_text())
by_frame = {}
for case in comparison["cases"]:
    if case["status"] != "exact_0diff":
        continue
    for frame in sorted({int(e["source_frame"]) for e in case["source_events"]}):
        matching = [e for e in case["source_events"] if int(e["source_frame"]) == frame]
        by_frame[frame] = {
            "case_id": case["case_id"], "case": case,
            "count": len(matching), "slot": case["slot"],
        }
for entry in prior["entries"]:
    found = by_frame.get(int(entry["source_frame"]))
    if not found or entry["kind"] != "frame_action":
        continue
    case = found["case"]
    entry["status"] = "native_matched"
    entry["observed_slots"] = [found["slot"]]
    entry["lee_slots_observed"] = [found["slot"]]
    entry.pop("remaining_reason", None)
    entry.pop("provenance_note", None)
    entry["source_raw_captures"] = sorted(set(entry.get("source_raw_captures", []) + [case["provenance"]["source_raw"]]))
    entry["godot_exact_scope"] = {
        "artifact": "evidence/characters/lee/godot/callback-exact-r09/comparison.json",
        "case_id": found["case_id"], "fields": case["compared_fields"], "differences": [],
        "source_event_count_for_frame": found["count"],
    }
    entry["native_provenance"] = {
        "fixture": case["provenance"]["native_fixture"],
        "fixture_sha256": case["provenance"]["native_fixture_sha256"],
        "source_raw": case["provenance"]["source_raw"],
        "source_raw_sha256": case["provenance"]["source_raw_sha256"],
        "source_build": case["provenance"]["source_build_copy"],
        "source_build_sha256": case["provenance"]["source_build_sha256"],
        "native_log": "evidence/characters/lee/godot/callback-exact-r09/engine.log",
        "native_log_sha256": comparison["godot_log_sha256"],
        "runtime_hash": "ddfce1b11f6b211dad81dda22105e5d17ae97d2a9e329d40270cfda719a66510",
    }
    entry["matched_fields"] = case["compared_fields"]
    entry["differences"] = []
prior["schema"] = "lee-callback-inventory-current-r09"
prior["scope"] = "Derived from current r08 inventory plus r09 same-run source/native exact callback comparisons. Matches are only source_frame, entering, action, decoded ql for the bound body frame-action fixture; no full parity claim."
from collections import Counter
counts = Counter(e["status"] for e in prior["entries"])
prior["counts"] = {k: counts[k] for k in ("native_matched", "source_only", "remaining", "normal_input_unreachable")}
out = root / "evidence/characters/lee/callback-exact-r01/pending-inventory-current-r09.json"
out.write_text(json.dumps(prior,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(prior["counts"],ensure_ascii=False))
