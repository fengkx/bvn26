"""Compare root-observed projectile playback and locals against native Flash."""
import argparse
import json
from pathlib import Path

from compare_mode_reference import read_text
from collect_ai_reference import decode_number

FIELDS = ("frame", "x", "y", "played", "movspeed")


def compare(events: Path, native: Path) -> dict:
    expected = []
    for line in read_text(events).splitlines():
        event = json.loads(line)
        if event["kind"] != "projectile_state" or event["fight_tick"] < 0:
            continue
        slot, name, *values = event["value"].split(",")
        if len(values) != len(FIELDS):
            raise ValueError("Unexpected projectile state shape")
        expected.append({"tick": event["fight_tick"], "slot": slot, "name": name,
                         **{key: None if value == "undefined" else decode_number(value)
                            for key, value in zip(FIELDS, values)}})
    actual = json.loads(read_text(native))
    differences = [{"source": source, "native": port}
                   for source, port in zip(expected, actual) if source != port]
    stopped = [row for row in expected if row["played"] == 1 and row["movspeed"] == 0]
    # A damage-only case need not take the child callback's hitTest branch.
    # Require observations after its one-shot guard fires, not just a hit count.
    covered = len(stopped) >= 2 and any(row["movspeed"] and row["played"] == 0 for row in expected)
    complete = bool(expected) and len(expected) == len(actual)
    return {"status": "matched" if complete and covered and not differences else "different",
            "source_states": len(expected), "native_states": len(actual),
            "post_contact_states": len(stopped), "contact_covered": covered,
            "complete": complete, "fields": list(FIELDS), "differences": differences}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = compare(args.source, args.native)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "differences"}))
    return 0 if result["status"] == "matched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
