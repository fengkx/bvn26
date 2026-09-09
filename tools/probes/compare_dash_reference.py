"""Compare native dash observations with retained, validated Flash root events."""
import argparse
import json
from pathlib import Path

FIELDS = {
    "attacker_frame": 0, "defender_frame": 1, "hp": 2, "hits": 3,
    "canhit": 4, "dashing": 5, "dash_frame": 6, "energy": 7,
    "x": 8, "paused": 9, "helper_child": 11, "receiver": 17,
}


def compare(events: Path, native: Path) -> dict:
    source = [row for line in events.read_text().splitlines()
              if (row := json.loads(line))["kind"] == "dash_state"]
    actual = json.loads(native.read_text())
    differences = []
    helper_phase = []
    if not source or len(source) != len(actual):
        raise ValueError(f"Incomplete trace: original={len(source)}, native={len(actual)}")
    for original, port in zip(source, actual):
        tick = original["fight_tick"]
        if tick != port["tick"]:
            raise ValueError("Root observation ticks do not align")
        values = [None if value == "undefined" else json.loads(value)
                  for value in original["value"].split(",")]
        for field, index in FIELDS.items():
            expected = values[index]
            observed = port[field]
            # Missing AS2 instance/frame and unset dashing map to the port's
            # zero frame/false value; never normalize an existing source value.
            if expected is None and observed in (None, 0):
                continue
            if expected != observed:
                differences.append({"tick": tick, "field": field,
                                    "original": expected, "native": observed})
        if values[10] != port["helper_frame"]:
            helper_phase.append({"tick": tick, "original": values[10],
                                 "native": port["helper_frame"]})
    return {"status": "matched_combat_fields" if not differences else "different",
            "snapshots": len(source), "fields": list(FIELDS),
            "differences": differences,
            "helper_root_phase_differences": helper_phase,
            "excluded": ["sand AABB floating point geometry", "renamed child alias lookup",
                         "helper activation root-observer phase (reported separately)"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(args.events, args.native)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(json.dumps({key: result[key] for key in ("status", "snapshots")}
                     | {"differences": len(result["differences"])}))
    raise SystemExit(0 if result["status"] == "matched_combat_fields" else 1)


if __name__ == "__main__":
    main()
