#!/usr/bin/env python3
"""Ensure AIREF pipe and JSONL encodings normalize identically and fail closed."""
import json
from event_tape import parse_event_line, parse_event_lines

body = {
    "run_id": "fixture", "sequence": 10, "time_ms": 300, "display_tick": 8,
    "fight_tick": 2, "kind": "body_boundary", "value": "p2,1134,true,1134,-1,0,300",
}
clip = {
    "run_id": "fixture", "sequence": 11, "time_ms": 301, "display_tick": 9,
    "fight_tick": 3, "kind": "schedule",
    "value": "fighter/lee#DefineSprite_518/frame_1133/PlaceObject2_18_30/CLIPACTIONRECORD onClipEvent(enterFrame).as,enter,_level0.game.p2.mc.instance572,1,false,1134,undefined",
}
for event in (body, clip):
    pipe = "AIREF|{run_id}|{sequence}|{time_ms}|{display_tick}|{fight_tick}|{kind}|{value}".format(**event)
    assert parse_event_line(pipe) == event
    assert parse_event_line(json.dumps(event, separators=(",", ":"))) == event
for invalid in ("not-an-event", "AIREF|too|few", '{"kind":', '{"kind":"state"}'):
    try:
        parse_event_line(invalid)
    except ValueError:
        continue
    raise AssertionError(f"invalid event was accepted: {invalid}")
assert parse_event_lines("\n" + json.dumps(body) + "\n") == [body]
try:
    parse_event_lines(json.dumps(body) + "\nnot-an-event\n")
except ValueError as exc:
    assert "line 2" in str(exc)
else:
    raise AssertionError("unknown nonempty event line was silently ignored")
assert parse_event_lines("engine banner\n" + json.dumps(body), allowed_log_prefixes=("engine banner",)) == [body]
print("AIREF_EVENT_TAPE_SMOKE_OK")
