"""Replay the saved projectile-contact regression corpus without recapturing Flash."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/probes"))
from compare_mode_reference import compare
from compare_projectile_reference import compare as compare_projectiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", help="restrict to a saved case ID")
    parser.add_argument("--projectile-states", action="store_true",
                        help="replay the Naruto/Hitsugaya child-position and playback captures")
    args = parser.parse_args()
    report = ROOT / "evidence/combat/projectile-contact-fix/regressions.json"
    if args.projectile_states:
        report = report.parent / "projectile-states/references.json"
    cases = json.loads(report.read_text())["comparisons"]
    if args.case:
        missing = set(args.case) - {case["id"] for case in cases}
        if missing:
            parser.error("unknown cases: " + ", ".join(sorted(missing)))
        cases = [case for case in cases if case["id"] in args.case]
    for case in cases:
        for kind in ["fixture", "source"]:
            path = ROOT / case[kind]
            if hashlib.sha256(path.read_bytes()).hexdigest() != case[kind + "_sha256"]:
                raise ValueError(f"saved {kind} changed: {path}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    index = output / "case-paths.json"
    index.write_text(json.dumps([str(ROOT / case["fixture"]) for case in cases]))
    log_path = output / "engine.log"
    with (output / "stdout.log").open("w") as log:
        run = subprocess.run(
            [args.godot, "--headless", "--path", str(ROOT / "godot"),
             "--log-file", str(log_path), "-s", "res://tests/move_case_reference.gd",
             "--", "--batch", str(index), str(output)],
            stdout=log, stderr=subprocess.STDOUT, timeout=max(300, len(cases) * 120),
            cwd=ROOT,
        )
    log = (output / "stdout.log").read_text()
    results = []
    for case in cases:
        native = output / (case["id"] + ".json")
        result = compare(ROOT / case["source"], native)
        result.update(id=case["id"], executed=(run.returncode == 0
                      and "SCRIPT ERROR" not in log
                      and "MOVE_CASE_REFERENCE_OK " + case["id"] in log.splitlines()))
        if args.projectile_states:
            result["projectiles"] = compare_projectiles(
                ROOT / case["source"], Path(str(native) + ".projectiles.json"))
        results.append(result)
    (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    passed = sum(result["status"] == "matched" and result["executed"]
                 and result.get("projectiles", {}).get("status", "matched") == "matched"
                 for result in results)
    print(f"SAVED_PROJECTILE_REFERENCES cases={len(results)} matched={passed} "
          f"states={sum(result['source_states'] for result in results)} "
          f"projectile_states={sum(result.get('projectiles', {}).get('source_states', 0) for result in results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
