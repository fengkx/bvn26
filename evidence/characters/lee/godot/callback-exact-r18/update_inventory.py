#!/usr/bin/env python3
"""Derive the 49-row callback inventory through the accepted R18 evidence."""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
inventory = json.loads((ROOT / "evidence/characters/lee/godot/callback-exact-r17/pending-inventory-current-r17.json").read_text())
body = json.loads((ROOT / "evidence/characters/lee/godot/callback-exact-body-final-r01/comparison-r01.json").read_text())
rooftop = json.loads((ROOT / "evidence/characters/lee/godot/callback-exact-stage-r01/comparison-r01.json").read_text())
failure = json.loads((ROOT / "evidence/characters/lee/godot/callback-exact-r18/comparison-r01.json").read_text())
clip = json.loads((ROOT / "evidence/characters/lee/godot/callback-exact-r16/wrapper-return-audit-r01.json").read_text())

def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def entry(frame: int, slot: str, kind: str = "frame_action") -> dict:
    matches = [row for row in inventory["entries"] if row.get("source_frame") == frame and row.get("slot") == slot and row.get("kind") == kind]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one inventory entry: frame={frame} slot={slot} kind={kind} got={len(matches)}")
    return matches[0]

def promote_frame(row: dict, comparison_path: str, comparison: dict, raw_capture: str, slot: str) -> None:
    row["status"] = "native_matched"
    row["source_raw_captures"] = [raw_capture]
    row["observed_slots"] = [slot]
    row["lee_slots_observed"] = [slot]
    row.pop("remaining_reason", None)
    row["matched_fields"] = ["source_frame", "entering", "action", "ql"]
    row["differences"] = []
    row["notes"] = "Bounded same-source-build/input callback match on four fields only; this does not establish full-state or role parity."
    row["godot_exact_scope"] = {
        "artifact": comparison_path,
        "fields": ["source_frame", "entering", "action", "ql"],
        "differences": [],
    }
    row["native_provenance"] = comparison

promote_frame(
    entry(738, "p1"), "evidence/characters/lee/godot/callback-exact-stage-r01/comparison-r01.json",
    rooftop["native"], "evidence/characters/lee/original/lee-callback-738-rooftop-walkoff-r04", "p1")
promote_frame(
    entry(1288, "p1"), "evidence/characters/lee/godot/callback-exact-r18/comparison-r01.json",
    failure["native"], "evidence/characters/lee/original/lee-callback-round-loss-failure-r06", "p1")

for frame in (1219, 1260):
    case = next(item for item in body["cases"] if item["case_id"] == "kill700-external-tape")
    result = case["frames"][str(frame)]
    if not result["four_fields_sequence_equal"]:
        raise SystemExit(f"cannot promote frame {frame}: four-field callback sequence differs")
    promote_frame(
        entry(frame, "p1"), "evidence/characters/lee/godot/callback-exact-body-final-r01/comparison-r01.json",
        {"comparison": result, "case_id": case["case_id"], "fields": body["batch"], "source": case["source"], "native": case["native"]},
        "evidence/characters/lee/original/lee-body-boundaries-r02", "p1")

for audit in clip["audits"]:
    if not audit["source_marker_projection_equals_native_projection"]:
        raise SystemExit(f"clip projection did not match: {audit['case_id']}")
    frame = 1088 if "1088" in audit["case_id"] else 1098
    slot = "p1" if frame == 1088 else "p2"
    row = entry(frame, slot, "clip_action")
    row["status"] = "native_matched"
    row.pop("remaining_reason", None)
    row["notes"] = (
        "Bounded source-marker/lifecycle projection match only. Raw native wrapper-return exit remains preserved; "
        "the projection classifies it separately after matching registration/generation/instance removal and no later callback. "
        "This is not full clip parity."
    )
    row["matched_fields"] = ["source_path", "phase", "slot", "child_local_frame", "source-relative-tick", "parent_frame"]
    row["godot_exact_scope"] = {
        "artifact": "evidence/characters/lee/godot/callback-exact-r16/wrapper-return-audit-r01.json",
        "case_id": audit["case_id"],
        "raw_wrapper_returns_preserved": audit["legacy_exit_preserved"],
        "wrapper_return_events": audit["wrapper_return_events"],
        "projected_native_marker_event_count": audit["projected_native_marker_event_count"],
        "source_marker_projection_equals_native_projection": True,
        "scope": "source marker and placement/registration lifecycle projection; not full clip parity",
    }

# Preserve the unmatched/source-only cases and document what the latest probe did.
frame8 = entry(8, "p1")
frame8["notes"] = (
    "Latest same-source-input native attempt is not exact: the source has 248 P1 frame-8 enter/exit rows while native has 92; "
    "do not promote based on selected individual rows."
)
frame8["native_diagnostic"] = {
    "artifact": "evidence/characters/lee/godot/callback-exact-body-final-r01/comparison-r01.json",
    "status": "diverged_or_invalid",
    "source_marker_count": 248,
    "native_marker_count": 92,
    "reason": "full repeated callback sequence count differs",
}
frame1083 = entry(1083, "p1")
frame1083["status"] = "invalid_source_fixture_precondition"
frame1083["notes"] = (
    "Do not count this P1 inventory row as source-only or as a runtime mismatch. The only actual source fixture found for frame1083 "
    "is Lee in P2, but its raw Ready state is P2 HP=1000 while the native fixture was modified to HP=1; the pair is not same-input. "
    "A source capture with the native fixture's actual precondition is required before comparison."
)
frame1083["invalid_provenance"] = {
    "source_capture": "evidence/characters/lee/callback-exact-r01/source-callback-provenance-r01/recovery-p2-hp1/",
    "source_run_id": "lee-callback-observer-hp1-r01",
    "source_slot": "p2",
    "source_ready_state": {"sequence": 7410, "display_tick": 452, "fight_tick": 0, "p2_health": 1000},
    "native_fixture_hp": 1,
    "same_input": False,
    "reason": "native fixture applied HP=1 intervention that is absent from the source event tape",
    "discarded_cross-input_observation": {
        "artifact": "evidence/characters/lee/godot/callback-exact-body-final-r01/engine.log",
        "source_target_p2": {"fight_tick": 29, "hp": 960, "sw": False, "hits": 1},
        "native_p2_before_target": {"fixture_tick": 28, "hp": 0, "sw": True, "hits": 2, "frame": 1096},
    },
}

counts = Counter(row["status"] for row in inventory["entries"])
inventory["schema"] = "lee-callback-inventory-current-r18"
inventory["scope"] = (
    "49-row bounded callback inventory through R18. Same-fixture frame-action matches compare source_frame, entering, decoded action and ql; "
    "clip matches use an explicitly audited source-marker/placement-lifecycle projection with raw wrapper returns preserved. "
    "Neither means full-state, full-clip, full-role, visual/audio or menu parity."
)
inventory["counts"] = {key: counts[key] for key in ("native_matched", "source_only", "remaining", "normal_input_unreachable", "invalid_source_fixture_precondition")}
if inventory["counts"] != {"native_matched": 44, "source_only": 1, "remaining": 0, "normal_input_unreachable": 3, "invalid_source_fixture_precondition": 1}:
    raise SystemExit(f"unexpected derived counts: {inventory['counts']}")
inventory["current_evidence"] = {
    "stage_738": "evidence/characters/lee/godot/callback-exact-stage-r01/comparison-r01.json",
    "natural_1288": "evidence/characters/lee/godot/callback-exact-r18/comparison-r01.json",
    "body_1219_1260": "evidence/characters/lee/godot/callback-exact-body-final-r01/comparison-r01.json",
    "clip_projection": "evidence/characters/lee/godot/callback-exact-r16/wrapper-return-audit-r01.json",
    "remaining_source_only": [
        {"slot": "p1", "frame": 8, "reason": "repeated callback counts differ: 248 source vs 92 native"},
        {"slot": "p1", "frame": 1083, "reason": "invalid source fixture precondition; actual source P2 Ready HP=1000 but native override HP=1"},
    ],
    "unreachable": [325, 332, 1149],
    "timer_phase_pending": "Frame 1288 callback fields match, but source fight_tick 2263 versus native fixture_tick 2228 is not aligned; retain as independent timing gap.",
}
out = HERE / "pending-inventory-current-r18.json"
out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(inventory["counts"], ensure_ascii=False))
