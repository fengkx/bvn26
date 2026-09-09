"""Verify the retained native ClipAction registration-order probe."""

from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    directory = ROOT / "evidence/probes/schedule/callback-registry"
    build = json.loads((directory / "build.json").read_text())
    sources = ROOT / "tools/probes/as2/callback_registry"
    for name, expected in build["source_sha256"].items():
        assert hashlib.sha256((sources / name).read_bytes()).hexdigest() == expected
    log = directory / "native.log"
    rows = [line.split("|") for line in log.read_text().splitlines()]
    assert rows[-1] == ["REGISTRY", "17", "done"]
    created = [row for row in rows if row[2] == "created"]
    assert [(row[3], row[4]) for row in created] == [
        ("_level0.a.child", "1"), ("_level0.b.child", "2"),
        ("_level0.a.child", "3"), ("_level0.b.child", "4")]
    observed = []
    for tick in range(17):
        callbacks = [row for row in rows if row[1] == str(tick) and row[2] in ("body", "child")]
        names = [row[3].removeprefix("_level0.") for row in callbacks]
        if tick < 4:
            expected = ["b.child", "b", "a.child", "a"]
        elif tick < 6:
            expected = ["b.child", "b", "a"]
        elif tick < 12:
            expected = ["a.child", "b.child", "b", "a"]
        elif tick < 14:
            expected = ["a.child", "b", "a"]
        else:
            expected = ["b.child", "a.child", "b", "a"]
        assert names == expected, (tick, names, expected)
        bodies = {row[3]: int(row[5]) for row in callbacks if row[2] == "body"}
        assert (bodies["_level0.a"] < bodies["_level0.b"]) == (tick < 8)
        observed.append({"root_counter": tick, "callbacks": names})
    print(json.dumps({"status": "original_callback_registry_probe_verified",
                      "native_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                      "observed": observed,
                      "limits": ["Root counter increments in the root observer, after child callbacks.",
                                 "This probe does not establish every game-object loading phase."]}, indent=2))


if __name__ == "__main__":
    main()
