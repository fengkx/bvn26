#!/usr/bin/env python3
"""Rebuild the bounded source/native callback comparison from locked evidence."""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys_path = ROOT / "tools/probes"
import sys
sys.path.insert(0, str(sys_path))
from collect_ai_reference import decode_number

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def source_events(path: Path, run_id: str, slot: str, targets: set[int]):
    result = []
    for line in path.read_text().splitlines():
        if not line.startswith("AIREF|"):
            continue
        cols = line.split("|", 7)
        if len(cols) != 8 or cols[1] != run_id or cols[6] != "body_boundary":
            continue
        values = cols[7].split(",")
        if len(values) < 7 or values[0] != slot:
            continue
        frame = int(values[1])
        if frame not in targets:
            continue
        result.append({
            "source_frame": frame,
            "entering": values[2] == "true",
            "action": float(decode_number(values[4])),
            "ql": float(decode_number(values[6])),
            "seq": int(cols[2]), "display_tick": int(cols[4]), "fight_tick": int(cols[5]),
        })
    return result

def native_summaries(log: Path):
    found = {}
    for line in log.read_text().splitlines():
        if line.startswith("LEE_EXACT_CALLBACK_SUMMARY "):
            payload = json.loads(line.split(" ", 1)[1])
            found[payload["fixture"]] = payload["events"]
    return found

pre = json.loads((HERE / "preflight.json").read_text())
log_path = HERE / "engine.log"
native = native_summaries(log_path)
current_runtime_files = [
    "godot/fighter_runtime.gd", "godot/main.gd", "godot/helper_runtime.gd",
    "godot/source_callback_registry.gd", "godot/generated/fighters/lee/player_controller/controller.gd",
    "godot/generated/fighters/lee/ai_controller/controller.gd", "godot/tests/lee_callback_exact_probe.gd",
]
report = {
    "schema": "lee-callback-exact-r09",
    "scope": "Same-source-run bounded body frame-action callbacks only; compare source_frame, entering, action and decoded ql. This is not full-state or full-role parity.",
    "batch_exitcode": 0 if "MOVE_CASE_BATCH_OK 2" in log_path.read_text() else None,
    "script_error": "SCRIPT ERROR" in log_path.read_text(),
    "runtime_file_hashes": {p: sha(ROOT / p) for p in current_runtime_files},
    "godot_log_sha256": sha(log_path),
    "cases": [],
}
for spec in pre["cases"]:
    run_id = spec["source_run_id"]
    raw_path = ROOT / spec["source_raw"]
    if raw_path.is_dir():
        raw_path = raw_path / "events.jsonl"
    copy_build = ROOT / spec["source_build_copy"]
    copy_instr = ROOT / spec["source_instrumentation_copy"]
    if not raw_path.is_file() or not copy_build.is_file() or not copy_instr.is_file():
        raise SystemExit(f"missing provenance artifact for {spec['case_id']}")
    build = json.loads(copy_build.read_text())
    if sha(raw_path) != spec["source_raw_sha256"]:
        raise SystemExit(f"source raw hash mismatch for {spec['case_id']}")
    if sha(copy_build) != spec["source_build_sha256"]:
        raise SystemExit(f"source build hash mismatch for {spec['case_id']}")
    if sha(copy_instr) != spec["source_instrumentation_sha256"]:
        raise SystemExit(f"instrumentation hash mismatch for {spec['case_id']}")
    if build.get("run_id") != run_id:
        raise SystemExit(f"build/run id mismatch for {spec['case_id']}")
    if build.get("outputs_sha256", {}).get("game/main.swf") != spec["source_output_main_sha256"]:
        raise SystemExit(f"source main SWF hash mismatch for {spec['case_id']}")
    targets = {int(x["source_frame"]) for x in spec["target_preflight"]}
    slot = spec["target_preflight"][0]["slot"]
    src = source_events(raw_path, run_id, slot, targets)
    nat = native.get(spec["case_id"])
    if nat is None:
        raise SystemExit(f"missing native summary for {spec['case_id']}")
    source_compare = [{k: e[k] for k in ("source_frame", "entering", "action", "ql")} for e in src]
    native_compare = [{k: e[k] for k in ("source_frame", "entering", "action", "ql")} for e in nat]
    diffs = []
    for i in range(max(len(source_compare), len(native_compare))):
        s = source_compare[i] if i < len(source_compare) else None
        n = native_compare[i] if i < len(native_compare) else None
        if s != n:
            diffs.append({"index": i, "source": s, "native": n})
    # Config and exact input tape are included to prevent same-frame cross-fixture matching.
    fixture = json.loads((ROOT / spec["fixture"]).read_text())
    source_move = spec["source_move_case"]
    input_match = (fixture.get("fighters") == {"p1": "lee", "p2": "yihu"}
        and fixture.get("setup") == source_move.get("setup")
        and fixture.get("inputs") == [{"slot": x["slot"], "keys": x["keys"], "start": x["start"], "end": x["end"]} for x in source_move["inputs"]]
        and fixture.get("p1_helper") == source_move.get("p1_helper")
        and fixture.get("p2_helper") == source_move.get("p2_helper")
        and int(fixture.get("frames", -1)) == int(spec["actual_capture_frames"])
        and build.get("configuration") == spec["source_build_config"]
        and build.get("move_case") == source_move
        and build.get("p1_helper") == source_move.get("p1_helper")
        and build.get("p2_helper") == source_move.get("p2_helper"))
    raw_done = any(line.endswith("|done|") for line in raw_path.read_text().splitlines())
    input_match = input_match and raw_done
    case = {
        "case_id": spec["case_id"],
        "status": "exact_0diff" if input_match and source_compare == native_compare else "diverged_or_invalid_input",
        "slot": slot, "callback_kind": "body_boundary/frame_action",
        "provenance": {
            "source_run_id": run_id, "source_raw": str(raw_path.relative_to(ROOT)),
            "source_raw_sha256": sha(raw_path), "source_build_copy": str(copy_build.relative_to(ROOT)),
            "source_build_sha256": sha(copy_build), "source_instrumentation_sha256": sha(copy_instr),
            "source_output_main_sha256": spec["source_output_main_sha256"],
            "source_build_status_field": build.get("status"),
            "source_capture_done_marker": raw_done,
            "source_move_case": source_move, "source_build_config": spec["source_build_config"],
            "native_fixture": spec["fixture"], "native_fixture_sha256": sha(ROOT / spec["fixture"]),
            "input_setup_helpers_exact_match": input_match,
        },
        "source_event_count": len(src), "native_event_count": len(nat),
        "source_events": src, "native_events": nat, "compared_fields": ["source_frame", "entering", "action", "ql"],
        "diffs": diffs,
    }
    report["cases"].append(case)
report["summary"] = {
    "cases": len(report["cases"]),
    "exact_0diff": sum(c["status"] == "exact_0diff" for c in report["cases"]),
    "source_events": sum(c["source_event_count"] for c in report["cases"]),
    "native_events": sum(c["native_event_count"] for c in report["cases"]),
    "diffs": sum(len(c["diffs"]) for c in report["cases"]),
}
(HERE / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report["summary"], ensure_ascii=False))
