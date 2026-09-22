"""Validate contract schemas, examples and source references; not a game compiler.

Run from any directory. Requires requirements-dev.txt.
This checks the delivered format examples. It does not prove gameplay equivalence.
"""
import hashlib
import json
from pathlib import Path
import sys

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("Install development dependencies: python3 -m pip install -r requirements-dev.txt")

ROOT = Path(__file__).resolve().parent.parent


def read_json(path):
    # json.loads otherwise accepts non-finite constants despite the JSON format.
    def reject_constant(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def source_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("Missing or invalid package source: " + relative)
    return path


def check_example(data):
    if "source_swf" in data:
        actual = hashlib.sha256(source_path(data["source_swf"]).read_bytes()).hexdigest()
        if actual != data["source_sha256"]:
            raise ValueError("Source SWF hash does not match")
    if "source_ref" in data:
        reference = data["source_ref"]
        bundle = read_json(source_path(reference["bundle"]))
        if reference["script_path"] not in {s["path"] for s in bundle["scripts"]}:
            raise ValueError("Missing script in source_ref")
        if data["kind"] == "action" and bundle["swf_sha256"] != data["source_sha256"]:
            raise ValueError("Action script and action SWF refer to different sources")
    if data["kind"] == "replay":
        manifest = read_json(ROOT / "manifest.json")
        if data["baseline_sha256"] != manifest["baseline"]["main_sha256"]:
            raise ValueError("Replay references a different baseline")
        if {p["player"] for p in data["initial_state"]["players"]} != {1, 2}:
            raise ValueError("Replay must initialize each player exactly once")
        previous = (-1, -1)
        held_by_player = {1: set(), 2: set()}
        for event in data["inputs"]:
            key = (event["tick"], event["order"])
            if key <= previous:
                raise ValueError("Input records must have increasing (tick, order)")
            previous = key
            held, pressed, released = (set(event[k]) for k in ("held", "pressed", "released"))
            prior = held_by_player[event["player"]]
            if pressed & released or held != (prior | pressed) - released or not released <= prior or pressed & prior:
                raise ValueError("Inconsistent held/pressed/released input sets")
            held_by_player[event["player"]] = held
    if data["kind"] == "action":
        keys = [(e["tick"], e["order"]) for e in data["events"]]
        if keys != sorted(set(keys)):
            raise ValueError("Action events must have unique increasing (tick, order)")
        if data["duration_ticks"] is not None and any(t >= data["duration_ticks"] for t, _ in keys):
            raise ValueError("Event outside action duration")
    if data["kind"] == "trace":
        keys = [(f["tick"], f["phase"]) for f in data["frames"]]
        if len(keys) != len(set(keys)) or [t for t, _ in keys] != sorted(t for t, _ in keys):
            raise ValueError("Trace has repeated phase or decreasing tick")
        for frame in data["frames"]:
            if {p["player"] for p in frame["players"]} != {1, 2}:
                raise ValueError("Trace must describe each player exactly once")
            for player in frame["players"]:
                unknown = {k for k in ("position", "state", "source_frame", "hp", "energy") if player[k] is None}
                if unknown != set(player["unobserved_fields"]):
                    raise ValueError("Null trace values must be declared unobserved")


def main():
    errors = []
    schemas = {}
    for path in sorted((ROOT / "spec/schemas").glob("*.schema.json")):
        try:
            schema = read_json(path)
            Draft202012Validator.check_schema(schema)
            schemas[path.name.removesuffix(".schema.json")] = Draft202012Validator(schema)
        except Exception as error:
            errors.append(f"{path.name}: {error}")
    count = 0
    for path in sorted((ROOT / "spec/examples").glob("*.json")):
        try:
            data = read_json(path)
            schemas[data["kind"]].validate(data)
            check_example(data)
            count += 1
        except Exception as error:
            errors.append(f"{path.name}: {error}")
    expected = {"asset", "fighter", "action", "replay", "trace", "match-input"}
    if set(schemas) != expected or count != len(expected):
        errors.append("Expected one valid example for each of the six schemas")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({"status": "passed", "schemas": len(schemas), "examples": count,
                      "gameplay_tested": False, "production_ready_data": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
