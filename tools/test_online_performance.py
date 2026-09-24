"""Run a warmed, serial native screening comparison in baseline/current/current/baseline order."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence/online/performance-30hz"
PROFILE = ROOT / "godot/tests/rollback_performance_profile.gd"
USER_TAPE = ROOT / "godot/tests/rollback_performance_user_log_r01.json"
MARKER = "ROLLBACK_PERFORMANCE "
KNOWN_ENVIRONMENT_ERRORS = (
    'ERROR: Condition "ret != noErr" is true. Returning:',
    "ERROR: 3 RID allocations of type 'P12GodotBody3D' were leaked at exit.",
    "ERROR: 2 resources still in use at exit (run with --verbose for details).",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_identity(source: Path) -> dict:
    resolved = source.resolve()
    for path in EVIDENCE.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("frozen_copy") == str(resolved):
            return {
                "manifest": str(path.relative_to(ROOT)),
                "fingerprint": item.get("tree_sha256"),
                "parent_tree_sha256": item.get("parent_tree_sha256"),
                "battle_checkpoint_sha256": sha256(resolved / "battle_checkpoint.gd"),
            }
    return {
        "manifest": None,
        "fingerprint": None,
        "battle_checkpoint_sha256": sha256(resolved / "battle_checkpoint.gd"),
    }


def load_sample() -> dict:
    return {
        "load_average": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
        "cpu_count": os.cpu_count(),
    }


def prepare(source: Path, destination: Path, scenario: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-cR", str(source.resolve()), str(destination)], check=True)
    shutil.copy2(PROFILE, destination / "tests/rollback_performance_profile.gd")
    if scenario == "user-log-r01":
        shutil.copy2(USER_TAPE, destination / "tests/rollback_performance_user_log_r01.json")


def run_one(godot: str, label: str, source: Path, project: Path, ordinal: int, log_dir: Path, scenario: str) -> dict:
    before = load_sample()
    started = time.perf_counter()
    log_dir.mkdir(parents=True, exist_ok=True)
    engine_log = log_dir / f"{ordinal:02d}-{label}-godot.log"
    result = subprocess.run(
        [godot, "--headless", "--path", str(project), "--log-file", str(engine_log),
         "--script", "res://tests/rollback_performance_profile.gd", "--", f"--scenario={scenario}"],
        text=True,
        capture_output=True,
        timeout=300,
    )
    wall_seconds = time.perf_counter() - started
    after = load_sample()
    console_output = result.stdout + result.stderr
    engine_output = engine_log.read_text(encoding="utf-8", errors="replace") if engine_log.exists() else ""
    output = console_output + "\n--- Godot --log-file ---\n" + engine_output
    log_path = log_dir / f"{ordinal:02d}-{label}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    errors = [
        line for line in output.splitlines()
        if "ERROR:" in line and not any(known in line for known in KNOWN_ENVIRONMENT_ERRORS)
    ]
    hard_errors = [
        line for line in output.splitlines()
        if any(token in line for token in ("SCRIPT ERROR", "Parse Error", "Assertion failed"))
    ]
    marker_lines = list(dict.fromkeys(
        line for line in output.splitlines() if line.startswith(MARKER)
    ))
    measurements = [json.loads(line[len(MARKER):]) for line in marker_lines]
    if result.returncode != 0 or errors or hard_errors or len(measurements) != 2:
        raise RuntimeError(
            f"{label}#{ordinal} failed: exit={result.returncode}, markers={len(measurements)}, "
            f"errors={errors}, script-errors={hard_errors}; see {log_path}\n{output[-6000:]}"
        )
    return {
        "ordinal": ordinal,
        "label": label,
        "source": str(source.resolve()),
        "profile_sha256": sha256(PROFILE),
        "wall_seconds": wall_seconds,
        "host_before": before,
        "host_after": after,
        "known_environment_diagnostics": [
            line for line in output.splitlines()
            if any(known in line for known in KNOWN_ENVIRONMENT_ERRORS)
        ],
        "log": str(log_path),
        "godot_log": str(engine_log),
        "measurements": measurements,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        choices=("default", "user-log-r01", "current-log-roster-r01"),
        default="default",
        help="Deterministic screening input; current-log-roster-r01 uses a fresh complete fixture matching the latest log's roster and stage.",
    )
    parser.add_argument(
        "--order",
        default="baseline,candidate,candidate,baseline",
        help="Comma-separated source order; for example baseline,candidate,candidate.",
    )
    parser.add_argument("--report", type=Path, default=EVIDENCE / "native-warmed-abba-r01.json")
    parser.add_argument("--log-dir", type=Path, default=Path("/private/tmp/bvn26-native-perf-r01"))
    args = parser.parse_args()

    version = subprocess.run([args.godot, "--version"], check=True, text=True, capture_output=True, timeout=15).stdout.strip()
    if not version.startswith("4.7.2"):
        raise RuntimeError(f"Expected Godot 4.7.2, got {version}")
    order = [part.strip() for part in args.order.split(",") if part.strip()]
    if not order or any(label not in {"baseline", "candidate"} for label in order):
        raise RuntimeError("--order must contain baseline and/or candidate labels")
    with tempfile.TemporaryDirectory(prefix="bvn-native-perf-") as temporary:
        root = Path(temporary)
        projects = {
            "baseline": root / "baseline/godot",
            "candidate": root / "candidate/godot",
        }
        prepare(args.baseline, projects["baseline"], args.scenario)
        prepare(args.candidate, projects["candidate"], args.scenario)
        runs = [
            run_one(
                args.godot, label,
                args.baseline if label == "baseline" else args.candidate,
                projects[label], ordinal, args.log_dir, args.scenario,
            )
            for ordinal, label in enumerate(order, start=1)
        ]

    report = {
        "validity": "native screening only; not a Web/browser 30 Hz acceptance result",
        "godot": version,
        "order": order,
        "profile_sha256": sha256(PROFILE),
        "warmup": "Each invocation warms a fresh fixture for 90 frames before measured modes; this warms project resources and the opening input window, not the full combat move set.",
        "fixture": {
            "default": "Naruto/Ichigo deterministic 330-frame input r01; fixed seed 727 and recorded intro schedule.",
            "user-log-r01": "日番谷/佐助, helpers 鼬 (asset you)/我爱罗, stage 现世; source-log inputs replay only on ticks 28-249, with neutral padding outside that partial range; fixed seed 727 and the profiler's deterministic intro schedule.",
            "current-log-roster-r01": "一护/佐助, helpers 我爱罗/松本, stage 流魂街; complete deterministic 330-tick synthetic input from a fresh fixture; fixed seed 727 and recorded intro schedule. This matches the latest log's roster and stage but is not a replay of its partial live observation.",
        }[args.scenario],
        "scenario": args.scenario,
        "input_tape_sha256": (
            sha256(USER_TAPE) if args.scenario == "user-log-r01"
            else runs[0]["measurements"][0]["input_fixture_metadata"].get("input_tape_sha256")
            if args.scenario == "current-log-roster-r01"
            else None
        ),
        "sources": {
            "baseline": {"path": str(args.baseline.resolve()), **source_identity(args.baseline)},
            "candidate": {"path": str(args.candidate.resolve()), **source_identity(args.candidate)},
        },
        "runs": runs,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
