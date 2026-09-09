"""Check the controlled original-game recovery callback order pair."""

from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[2]


def inspect(name: str, expected_order: list[str]) -> dict:
    directory = ROOT / "evidence/ai" / name
    build = json.loads((directory / "build.json").read_text())
    assert build["recovery_order_probe"] is True
    path = directory / "events.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert len([event for event in events if event["kind"] == "fixture"]) == 1
    callbacks = [event for event in events if event["kind"] == "recovery_order"]
    first = callbacks[:3]
    values = [event["value"].split(",") for event in first]
    assert [value[0] for value in values] == expected_order
    assert len({event["display_tick"] for event in first}) == 1
    assert all(value[-2:] == ["-16375", "-16377"] for value in values)
    assert sum(event["value"].startswith("recovery-enter,") for event in callbacks) == 3
    return {
        "run_id": name,
        "events_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "first_callbacks": first,
        "p2_x_at_recovery_exit": float(next(value[4] for value in values if value[0] == "recovery-exit")),
    }


def main() -> None:
    later_walk = inspect("recovery-order-r09", ["moveLeft", "recovery-enter", "recovery-exit"])
    earlier_walk = inspect("recovery-order-r10", ["recovery-enter", "recovery-exit", "moveLeft"])
    assert later_walk["p2_x_at_recovery_exit"] == 345
    assert earlier_walk["p2_x_at_recovery_exit"] == 351
    print(json.dumps({
        "status": "original_order_pair_verified_not_native_parity",
        "runs": [later_walk, earlier_walk],
        "conclusion": "Cross-actor callback order changes with goto order at unchanged display depths.",
        "limits": ["Does not establish the full event registry or retained-instance reordering rules."],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
