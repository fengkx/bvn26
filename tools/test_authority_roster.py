#!/usr/bin/env python3
"""Compare host/presenter state for every currently selectable fighter."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    available = json.loads((ROOT / "godot/generated/main/character_selection/available.json").read_text())
    stages = json.loads((ROOT / "services/matchmaking/src/catalog.json").read_text())["stages"]
    helpers = list(available["helpers"])
    results = []
    for index, (fighter, resource) in enumerate(available["fighters"].items()):
        helper = helpers[index % len(helpers)]
        if available["helpers"][helper] == resource:
            helper = "魂"
        selection = [fighter, "一护", helper, "魂", stages[index % len(stages)]]
        log = args.output / f"{resource}.log"
        command = [args.godot, "--headless", "--path", str(ROOT / "godot"),
                   "--log-file", str(args.output / f"{resource}-engine.log"),
                   "-s", "res://tests/authority_projection_smoke.gd", "--quit-after", "3000",
                   "--", json.dumps(selection, ensure_ascii=False)]
        with log.open("w") as stream:
            try:
                result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = -1
        text = log.read_text()
        passed = code == 0 and "AUTHORITY_PROJECTION_OK" in text and not any(
            marker in text for marker in ["SCRIPT ERROR", "Assertion failed", "resources still in use", "leaked at exit"]
        )
        errors = [line for line in text.splitlines() if "ERROR:" in line]
        # Match the repository checked runner's exact macOS system-CA diagnostic.
        passed = passed and all(line == 'ERROR: Condition "ret != noErr" is true. Returning: ""' for line in errors)
        results.append({"selection": selection, "passed": passed, "exit_code": code})
        (args.output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
        print(resource, "passed" if passed else "failed", flush=True)
        if not passed:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
