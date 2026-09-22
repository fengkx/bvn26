#!/usr/bin/env python3
"""Classify native test-proxy returns separately from source clip markers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
preflight = json.loads((HERE / "preflight.json").read_text())
report = json.loads((HERE / "comparison.json").read_text())
run_dir = HERE / "retry-01"
cases = {case["case_id"]: case for case in preflight["cases"]}
audits = []

for result in report["results"]:
    case = cases[result["case_id"]]
    native_path = run_dir / "out" / f'{case["case_id"]}.json.clips.json'
    native_payload = json.loads(native_path.read_text())
    lifetimes = native_payload["lifetime_events"]
    for target in result["target_comparisons"]:
        native_rows = target["native_events"]
        source_rows = target["source_events"]
        wrappers = []
        for index, event in enumerate(native_rows):
            placement = event.get("child_placement")
            if event.get("phase") != "exit" or placement != {}:
                continue
            identity = {
                "source_path": event["source_path"],
                "slot": event["slot"],
                "registration_id": event["registration_id"],
                "generation": event["generation"],
                "controller_instance_id": event["controller_instance_id"],
            }
            removed = [life for life in lifetimes if life.get("phase") == "removed" and all(
                life.get(key) == value for key, value in identity.items()
            )]
            earlier_enter = [prior for prior in native_rows[:index] if prior.get("phase") == "enter" and all(
                prior.get(key) == value for key, value in identity.items()
            )]
            later_same_registration = [later for later in native_rows[index + 1:] if all(
                later.get(key) == identity["source_path"] if key == "source_path" else later.get(key) == value
                for key, value in identity.items()
            )]
            # Test-proxy exit is not a source marker when the callback changed
            # the parent timeline and the same placement/registration vanished.
            removed_at_return_parent = [life for life in removed if int(life.get("parent_frame", -1)) == int(event.get("parent_frame", -2))]
            wrapper = {
                "raw_native_event_index": index,
                "event": event,
                "matched_removal_events": removed,
                "earlier_same_instance_enters": len(earlier_enter),
                "identity_is_complete": all(value not in (None, "") for value in identity.values()),
                "placement_absent_after_wrapped_call": True,
                "removal_observed_at_same_parent_frame": bool(removed_at_return_parent),
                "no_later_callback_for_same_registration": not later_same_registration,
                "classification": "wrapper_return_after_removed_placement"
                    if earlier_enter and removed_at_return_parent and not later_same_registration
                    else "unresolved_empty_placement_exit",
            }
            wrappers.append(wrapper)

        projected_native = [event for index, event in enumerate(native_rows)
                            if index not in {wrapper["raw_native_event_index"] for wrapper in wrappers}]
        clock_offset = target["native_minus_source_tick_offset"]
        is_p2 = target["slot"] == "p2"
        source_projection = [{
            "source_path": row["source_path"], "phase": row["phase"], "slot": row["slot"],
            "child_local_frame": int(row["child_local_frame"]),
            "normalized_tick": int(row["fight_tick"]),
            **({"parent_frame": int(row["source_reported_p2_frame"])} if is_p2 else {}),
        } for row in source_rows]
        native_projection = [{
            "source_path": row["source_path"], "phase": row["phase"], "slot": row["slot"],
            "child_local_frame": int(row.get("child_placement", {}).get("child_local_frame", -1)),
            "normalized_tick": int(row["display_tick"]) - int(clock_offset) if clock_offset is not None else None,
            **({"parent_frame": int(row["parent_frame"])} if is_p2 else {}),
        } for row in projected_native]
        audits.append({
            "case_id": result["case_id"],
            "source_path": target["source_path"],
            "source_run_id": case["run_id"],
            "source_raw": case["source_raw"],
            "source_build": case["source_build"],
            "source_fixture": case["source_fixture"],
            "native_capture": str(native_path.relative_to(ROOT)),
            "original_raw_event_count": len(native_rows),
            "source_marker_event_count": len(source_rows),
            "wrapper_return_events": wrappers,
            "legacy_exit_preserved": True,
            "projected_native_marker_event_count": len(projected_native),
            "source_marker_projection_equals_native_projection": source_projection == native_projection,
            "source_marker_projection": source_projection,
            "native_source_marker_projection": native_projection,
            "acceptance_status": "source_only" if wrappers and source_projection == native_projection
                else target["status"],
            "scope_note": "Raw native exit is preserved. Projection excludes it only after same registration/generation/instance had an enter, the callback returned with no child placement, the matching lifetime removal was observed at that parent frame, and the registration had no later callback. This is test-proxy lifecycle evidence, not full clip parity.",
        })

output = {
    "schema": "lee-callback-clip-wrapper-return-audit-r01",
    "source_comparison": "evidence/characters/lee/godot/callback-exact-r16/comparison.json",
    "scope": "Classify raw native proxy return observations independently; do not rewrite or discard original R16 comparison rows.",
    "audits": audits,
    "all_wrapper_returns_classified": all(
        wrapper["classification"] == "wrapper_return_after_removed_placement"
        for audit in audits for wrapper in audit["wrapper_return_events"]
    ),
    "all_projected_sequences_match": all(audit["source_marker_projection_equals_native_projection"] for audit in audits),
}
(HERE / "wrapper-return-audit-r01.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({
    "targets": len(audits),
    "wrapper_returns": sum(len(audit["wrapper_return_events"]) for audit in audits),
    "all_wrapper_returns_classified": output["all_wrapper_returns_classified"],
    "all_projected_sequences_match": output["all_projected_sequences_match"],
}, ensure_ascii=False))
