"""Replay retained dash combat references with the real native main loop."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from probes.compare_dash_reference import compare

ROOT = Path(__file__).resolve().parent.parent
CASES = [
    ("super-r03", "super-rush", 610),
    ("super-double", "super-rush", 681),
    ("helper-double", "helper-rush", 38),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="bvn-dash-") as directory:
        for name, scenario, trigger in CASES:
            output = Path(directory) / f"{name}.json"
            log = Path(directory) / f"{name}.log"
            with log.open("w") as stream:
                subprocess.run([args.godot, "--headless", "--path", str(ROOT / "godot"),
                                "--quit-after", "900", "-s", "res://tests/dash_reference.gd",
                                "--", scenario, str(output), str(trigger), "36"],
                               stdout=stream, stderr=subprocess.STDOUT, timeout=90, check=True)
            text = log.read_text()
            if "DASH_REFERENCE_OK" not in text or "SCRIPT ERROR" in text:
                raise RuntimeError(text)
            result = compare(ROOT / "evidence/combat/dash-validation" / name / "events.jsonl", output)
            if result["differences"]:
                raise AssertionError(json.dumps(result))
            print(f"DASH_REFERENCE_MATCH {name}: {result['snapshots']} snapshots", flush=True)


if __name__ == "__main__":
    main()
