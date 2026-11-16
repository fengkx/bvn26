"""Compare complete targeted captures without granting character admission."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/probes")]
from compare_mode_reference import compare, source_rows
from test_move_cases import target_seen


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(cases, source, native):
    results = []
    for fixture in sorted(cases.glob("*.json")):
        case = json.loads(fixture.read_text())
        original = source / case["id"] / "events.jsonl"
        port = native / (case["id"] + ".json")
        if not original.is_file() or not port.is_file():
            results.append({"id": case["id"], "status": "missing_capture"})
            continue
        comparison = compare(original, port)
        source_states = source_rows(original)
        native_states = json.loads(port.read_text())
        expected = 2 * (case["frames"] + 1)
        complete = len(source_states) == len(native_states) == expected
        source_reached = target_seen(case, source_states)
        native_reached = target_seen(case, native_states)
        negative = case["scenario"] == "super-below"
        reached = not source_reached and not native_reached if negative else source_reached and native_reached
        status = comparison["status"] if complete and reached else "incomplete_or_unexercised"
        row = {"id": case["id"], **comparison, "status": status,
               "expected_states": expected, "source_target_seen": source_reached,
               "native_target_seen": native_reached, "negative_case": negative,
               "paths": {"fixture": str(fixture), "source": str(original), "native": str(port)},
               "hashes": {"fixture": digest(fixture), "source": digest(original), "native": digest(port)}}
        results.append(row)
        print(case["id"], status, len(comparison.get("differences", [])), flush=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "source", "native", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    rows = collect(args.cases, args.source, args.native)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    raise SystemExit(0 if rows and all(row["status"] == "matched" for row in rows) else 1)
