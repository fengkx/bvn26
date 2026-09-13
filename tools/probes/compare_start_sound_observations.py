"""Associate authored StartSound tags with observed top-level frame entries.

This is a schedule report, not evidence that the original Flash player emitted
audio. Playback state, same-frame restarts, nested clips, and sound sync flags
require a player-level observation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROBE_DIRECTORY = Path(__file__).resolve().parent
if str(PROBE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(PROBE_DIRECTORY))

try:
    from .compare_mode_reference import compare, source_rows
except ImportError:
    from compare_mode_reference import compare, source_rows


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def start_sounds_by_frame(timeline: dict) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    for frame in timeline.get("frames", []):
        sounds = [event for event in frame.get("events", [])
                  if event.get("type") == "start_sound"]
        if sounds:
            result[int(frame["frame"])] = sounds
    return result


def observed_start_sounds(rows: list[dict], frame_events: dict[int, list[dict]], slot: str) -> list[dict]:
    """Report authored sound tags when an observed fighter playhead enters a tagged frame."""
    previous_frame = None
    output = []
    for row in rows:
        if row["slot"] != slot:
            continue
        frame = int(row["frame"])
        if frame != previous_frame:
            for event in frame_events.get(frame, []):
                output.append({
                    "tick": row["tick"],
                    "slot": slot,
                    "frame": frame,
                    "sound_id": int(event["sound_id"]),
                    "event": event,
                })
        previous_frame = frame
    return output


def compare_start_sounds(events: Path, native: Path, timeline_path: Path, slot: str) -> dict:
    timeline = read_json(timeline_path)
    original_rows = source_rows(events)
    native_rows = read_json(native)
    if not isinstance(native_rows, list):
        raise ValueError("Native fighter observations must be a JSON array")
    fighter = compare(events, native)
    frame_events = start_sounds_by_frame(timeline)
    original = observed_start_sounds(original_rows, frame_events, slot)
    port = observed_start_sounds(native_rows, frame_events, slot)
    return {
        "status": "authored_schedule_report",
        "fighter_state_status": fighter["status"],
        "source_timeline_sha256": timeline.get("source_swf", {}).get("sha256", ""),
        "slot": slot,
        "observation_rule": "Static top-level StartSound tags are listed when a trace enters their authored source frame. This does not observe original or Godot audio playback, same-frame restarts, nested clip playback, syncStop, or syncNoMultiple.",
        "source_frame_schedule_events": original,
        "native_frame_schedule_events": port,
        "source_schedule_event_count": len(original),
        "native_schedule_event_count": len(port),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("timeline", type=Path)
    parser.add_argument("--slot", choices=("p1", "p2"), default="p1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare_start_sounds(args.events, args.native, args.timeline, args.slot)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in
                      ("status", "fighter_state_status", "source_schedule_event_count", "native_schedule_event_count")}))
    raise SystemExit(0 if result["fighter_state_status"] == "matched" else 1)


if __name__ == "__main__":
    main()
