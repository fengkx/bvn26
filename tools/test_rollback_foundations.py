"""Run native offline battle rollback and its service/source regressions."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CASES = [
    ("battle_checkpoint_smoke", "BATTLE_CHECKPOINT_SMOKE_OK"),
    ("rollback_battle_smoke", "ROLLBACK_BATTLE_SMOKE_OK"),
    ("rollback_roster_smoke", "ROLLBACK_ROSTER_SMOKE_OK"),
    ("rollback_round_smoke", "ROLLBACK_ROUND_SMOKE_OK"),
    ("controller_checkpoint_smoke", "CONTROLLER_CHECKPOINT_SMOKE_OK"),
    ("timeout_checkpoint_smoke", "TIMEOUT_CHECKPOINT_SMOKE_OK"),
    ("ai_projectile_driver_smoke", "AI_PROJECTILE_DRIVER_SMOKE_OK"),
    ("rollback_services_smoke", "ROLLBACK_SERVICES_SMOKE_OK"),
    ("manual_match_step_smoke", "MANUAL_MATCH_STEP_SMOKE_OK"),
    ("source_callback_registry_smoke", "SOURCE_CALLBACK_REGISTRY_SMOKE_OK"),
    ("ai_random_smoke", "AI_RANDOM_SMOKE_OK"),
    ("hit_effect_clock_smoke", "HIT_EFFECT_CLOCK_SMOKE_OK"),
    ("hit_effect_random_smoke", "HIT_EFFECT_RANDOM_SMOKE_OK"),
    ("ai_timeouts_smoke", "AI_TIMEOUTS_SMOKE_OK"),
    ("match_input_scene_smoke", "MATCH_INPUT_SCENE_SMOKE_OK"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    version = subprocess.run(
        [args.godot, "--version"], check=True, text=True, capture_output=True, timeout=15
    ).stdout.strip()
    results = []
    with tempfile.TemporaryDirectory(prefix="bvn-rollback-") as directory:
        for script, marker in CASES:
            result = subprocess.run(
                [args.godot, "--headless", "--verbose", "--path", str(ROOT / "godot"),
                 "--log-file", str(Path(directory) / (script + ".log")),
                 "--quit-after", "5000", "-s", f"res://tests/{script}.gd"],
                text=True, capture_output=True, timeout=180,
            )
            output = result.stdout + result.stderr
            leaks = [line for line in output.splitlines() if line.startswith("Leaked instance:")]
            audio_shutdown = bool(leaks) and all(
                line.startswith(("Leaked instance: AudioStreamMP3:",
                                 "Leaked instance: AudioStreamPlaybackMP3:",
                                 "Leaked instance: AudioStreamWAV:",
                                 "Leaked instance: AudioStreamPlaybackWAV:"))
                for line in leaks
            )
            passed = result.returncode == 0 and marker in output and not any(
                token in output for token in ["SCRIPT ERROR", "Parse Error", "Assertion failed"]
            ) and not any(
                line.startswith("ERROR:") and 'Condition "ret != noErr"' not in line
                and not (audio_shutdown and "resources still in use at exit" in line)
                for line in output.splitlines()
            )
            results.append({"test": script, "passed": passed,
                            "audio_shutdown_warning": audio_shutdown,
                            "markers": [line for line in output.splitlines()
                                        if marker in line or line.startswith(("ROLLBACK_FAULTS", "ROLLBACK_PROFILE", "ROLLBACK_ROSTER_CASE_OK", "ROLLBACK_ROUND_CASE_OK", "ROLLBACK_INDEPENDENT_RUN_OK"))]})
            print(f"{'PASS' if passed else 'FAIL'} {script}", flush=True)
            if not passed:
                print(output)
    report = {"scope": "native offline battle rollback; synthetic external timer envelopes; not Chrome or online acceptance",
              "godot": version, "status": "passed" if all(r["passed"] for r in results) else "failed",
              "checks": results}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
