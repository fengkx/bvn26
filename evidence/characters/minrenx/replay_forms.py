"""Replay completed original captures with their observed form timer tape."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools/probes"), str(Path(__file__).parent)]
from compare_mode_reference import compare
from prepare_replay import prepare


def run(godot, source, output, skip):
    evidence = Path(__file__).parent
    fixtures = evidence / "form-replay-cases"
    fixtures.mkdir(exist_ok=True)
    output.mkdir(exist_ok=True)
    rows = []
    for original in sorted((evidence / "form-cases").glob("*.json")):
        case = json.loads(original.read_text())
        if case["id"] in skip:
            continue
        capture = source / case["id"]
        deadline = time.monotonic() + 900
        while not (capture / "capture-summary.json").is_file():
            if time.monotonic() >= deadline:
                raise TimeoutError(f"No completed source capture: {capture}")
            time.sleep(2)
        receipt = json.loads((capture / "capture-summary.json").read_text())
        assert receipt["status"] == "captured_source_only"
        fixture = fixtures / original.name
        fixture.write_text(json.dumps(prepare(original, capture / "events.jsonl"), ensure_ascii=False, indent=2) + "\n")
        native = output / (case["id"] + ".json")
        assert not native.exists(), native
        log = output / (case["id"] + ".process.log")
        command = [str(godot), "--headless", "--path", str(ROOT / "godot"),
                   "--log-file", str(output / (case["id"] + ".engine.log")),
                   "-s", "res://tests/move_case_reference.gd", "--quit-after", "1200", "--",
                   str(fixture), str(native)]
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
        text = result.stdout + result.stderr
        log.write_text(text)
        executed = result.returncode == 0 and "MOVE_CASE_REFERENCE_OK" in text and "SCRIPT ERROR" not in text and "ERROR:" not in text
        comparison = compare(capture / "events.jsonl", native) if native.exists() else None
        row = {"id": case["id"], "exit_code": result.returncode, "executed": executed,
               "seconds": time.monotonic() - started, "comparison": comparison,
               "exit_resource_residual": "leaked" in text or "resources still in use" in text}
        rows.append(row)
        (output / "execution.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
        print(case["id"], executed, comparison["status"] if comparison else "missing", flush=True)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("godot", "source", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--skip", action="append", default=[])
    args = parser.parse_args()
    rows = run(args.godot.resolve(), args.source.resolve(), args.output.resolve(), args.skip)
    raise SystemExit(0 if rows and all(r["executed"] and r["comparison"]["status"] == "matched" for r in rows) else 1)
