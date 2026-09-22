"""Strict reader for the two retained AIREF event encodings."""
from __future__ import annotations

import json


def parse_event_lines(text: str, allowed_log_prefixes: tuple[str, ...] = ()) -> list[dict]:
    """Parse a pure event stream; only explicit log prefixes may be skipped."""
    events = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if any(line.startswith(prefix) for prefix in allowed_log_prefixes):
            continue
        try:
            events.append(parse_event_line(line))
        except ValueError as exc:
            raise ValueError(f"invalid event at line {line_number}: {exc}") from exc
    return events


def parse_event_line(line: str) -> dict:
    if line.startswith("AIREF|"):
        columns = line.split("|", 7)
        if len(columns) != 8 or not columns[1] or not columns[6]:
            raise ValueError("malformed AIREF row")
        try:
            sequence, time_ms, display_tick, fight_tick = map(int, columns[2:6])
        except ValueError as exc:
            raise ValueError("AIREF row has a nonnumeric clock or sequence") from exc
        return {
            "run_id": columns[1], "sequence": sequence, "time_ms": time_ms,
            "display_tick": display_tick, "fight_tick": fight_tick,
            "kind": columns[6], "value": columns[7],
        }
    if line.startswith("{"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("malformed JSONL event") from exc
        required = ("run_id", "sequence", "time_ms", "display_tick", "fight_tick", "kind", "value")
        if not isinstance(event, dict) or any(key not in event for key in required):
            raise ValueError("JSONL event is missing required fields")
        if not isinstance(event["run_id"], str) or not isinstance(event["kind"], str) or not isinstance(event["value"], str):
            raise ValueError("JSONL event has invalid string fields")
        try:
            for key in ("sequence", "time_ms", "display_tick", "fight_tick"):
                event[key] = int(event[key])
        except (TypeError, ValueError) as exc:
            raise ValueError("JSONL event has a nonnumeric clock or sequence") from exc
        return {key: event[key] for key in required}
    raise ValueError("unrecognized event encoding")
