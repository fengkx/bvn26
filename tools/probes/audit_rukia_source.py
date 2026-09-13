#!/usr/bin/env python3
"""Build a source-first audit for Rukia's base-form timeline.

This reads locked SWF/script inputs and writes only role-specific evidence.
It does not execute or modify the Flash source.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/importer"))

from extract_fighter_slice import action_spans, root_placements  # noqa: E402
from inspect_swf import inspect  # noqa: E402


def unpack_swf(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw[:3] == b"FWS":
        return raw
    if raw[:3] == b"CWS":
        return raw[:8] + zlib.decompress(raw[8:])
    raise ValueError(f"Unsupported SWF signature: {path}")


def timeline_changes(data: bytes, wanted_id: int) -> dict[int, list[dict]]:
    nbits = data[8] >> 3
    header_offset = 8 + (5 + 4 * nbits + 7) // 8
    _, root_frames = struct.unpack_from("<HH", data, header_offset)
    start = header_offset + 4
    found: dict[int, list[dict]] = {}

    def walk(begin: int, end: int, timeline_id: int | None, frame_count: int) -> None:
        pos = begin
        frame = 1
        while pos + 2 <= end:
            header = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            tag = header >> 6
            size = header & 63
            if size == 63:
                size = struct.unpack_from("<I", data, pos)[0]
                pos += 4
            payload = data[pos : pos + size]
            if tag == 39:
                child_id, child_frames = struct.unpack_from("<HH", payload)
                walk(pos + 4, pos + size, child_id, child_frames)
            elif timeline_id == wanted_id and tag in (4, 5, 26, 28, 70):
                change: dict[str, object] = {"tag": tag}
                if tag == 4:  # PlaceObject (always supplies a character and matrix)
                    character_id, depth = struct.unpack_from("<HH", payload)
                    change.update(type="place", depth=depth, character_id=character_id, move=False)
                elif tag == 5:  # RemoveObject
                    character_id, depth = struct.unpack_from("<HH", payload)
                    change.update(type="remove", depth=depth, character_id=character_id)
                elif tag == 28:  # RemoveObject2
                    depth = struct.unpack_from("<H", payload)[0]
                    change.update(type="remove", depth=depth)
                else:
                    flags = payload[0]
                    if tag == 26:
                        depth = struct.unpack_from("<H", payload, 1)[0]
                        cursor = 3
                    else:
                        extra_flags = payload[1]
                        depth = struct.unpack_from("<H", payload, 2)[0]
                        cursor = 4
                        if extra_flags & 0x08 or ((extra_flags & 0x10) and (flags & 0x02)):
                            cursor = payload.index(0, cursor) + 1
                    has_character = bool(flags & 0x02)
                    move = bool(flags & 0x01)
                    change.update(
                        type="move" if move and not has_character else "place",
                        depth=depth,
                        move=move,
                        has_character=has_character,
                    )
                    if has_character:
                        change["character_id"] = struct.unpack_from("<H", payload, cursor)[0]
                found.setdefault(frame, []).append(change)
            if tag == 1:
                frame += 1
            pos += size
            if tag == 0:
                break
        if frame - 1 != frame_count:
            raise ValueError(f"Timeline {timeline_id} frame count mismatch: {frame - 1} != {frame_count}")

    walk(start, len(data), None, root_frames)
    return found


def compact_ranges(values: list[int]) -> list[str]:
    if not values:
        return []
    values = sorted(values)
    ranges = []
    first = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append(str(first) if first == previous else f"{first}-{previous}")
        first = previous = value
    ranges.append(str(first) if first == previous else f"{first}-{previous}")
    return ranges


def build() -> dict:
    swf_path = ROOT / "game/fighter/rukia.swf"
    bundle_path = ROOT / "scripts/fighter/rukia.json"
    slice_path = ROOT / "data/slices/rukia-base.json"
    if not slice_path.exists():
        raise FileNotFoundError("Run tools/importer/extract_fighter_slice.py 露其雅 first")
    slice_data = json.loads(slice_path.read_text(encoding="utf-8"))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    script_by_path = {entry["path"]: entry for entry in bundle["scripts"]}
    source_timeline_id = slice_data["source"]["timeline_symbol_id"]
    timeline = next(item for item in inspect(swf_path)["timelines"] if item["name"] == f"sprite_{source_timeline_id}")
    spans = action_spans(timeline["labels"], timeline["declared_frames"])
    # The 1144+ "万解" segment belongs to the transformation presentation, outside this task's base-form scope.
    base_spans = {name: span for name, span in spans.items() if name != "万解"}
    frame_changes = timeline_changes(unpack_swf(swf_path), source_timeline_id)
    frame_scripts: dict[int, list[dict]] = {}
    clip_scripts: dict[int, list[dict]] = {}
    path_pattern = re.compile(rf"^DefineSprite_{source_timeline_id}/frame_(\d+)/(.*)$")
    for entry in bundle["scripts"]:
        match = path_pattern.match(entry["path"])
        if not match:
            continue
        frame = int(match.group(1))
        suffix = match.group(2)
        record = {"path": entry["path"], "sha256": hashlib.sha256(entry["source"].encode()).hexdigest()}
        if suffix == "DoAction.as":
            frame_scripts.setdefault(frame, []).append(record)
        elif "onClipEvent(enterFrame)" in suffix or "onClipEvent(load)" in suffix:
            clip_scripts.setdefault(frame, []).append(record)

    action_records = []
    for label, span in base_spans.items():
        start, end = span["start_frame"], span["end_frame"]
        action_frames = [frame for frame in range(start, end + 1) if frame in frame_scripts]
        clips = [frame for frame in range(start, end + 1) if frame in clip_scripts]
        exits = []
        for frame in action_frames:
            for script in frame_scripts[frame]:
                source = script_by_path[script["path"]]["source"]
                for line_no, line in enumerate(source.splitlines(), 1):
                    if re.search(r"\b(?:gotoAndStop|gotoAndPlay|stop|play)\s*\(", line):
                        exits.append({"frame": frame, "path": script["path"], "line": line_no, "source": line.strip()})
        action_records.append({
            "label": label,
            **span,
            "frame_script_frames": action_frames,
            "frame_scripts": {str(frame): frame_scripts[frame] for frame in action_frames},
            "frames_without_DoAction": compact_ranges([f for f in range(start, end + 1) if f not in frame_scripts]),
            "clip_action_frames": clips,
            "clip_event_scripts": {str(frame): clip_scripts[frame] for frame in clips},
            "changes_by_frame": {str(f): frame_changes[f] for f in range(start, end + 1) if frame_changes.get(f)},
            "playback_control_calls": exits,
            "label_exit_classification": "pending source/runtime review",
        })

    init = script_by_path["frame_1/DoAction.as"]["source"]
    root_placement_map = root_placements(swf_path)
    return {
        "format": "bvn26-rukia-base-source-first-audit-v1",
        "status": "source_audit_partial_original_player_capture_pending",
        "scope": {"fighter_id": "露其雅", "form": "base", "excluded_label": "万解 (transformation sequence)"},
        "source": {
            "swf_path": "game/fighter/rukia.swf",
            "swf_sha256": hashlib.sha256(swf_path.read_bytes()).hexdigest(),
            "script_bundle_path": "scripts/fighter/rukia.json",
            "script_bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
            "base_timeline_sprite_id": source_timeline_id,
            "base_root_placement": root_placement_map[0],
            "second_form_root_placement": root_placement_map[1],
        },
        "source_questions": {
            "q1_frame_scripts": "Each base-form label's complete frame span, DoAction frames and empty-frame ranges are listed below. Clip-event script paths are separately listed; audit includes hashes, while full source is retained in scripts/fighter/rukia.json.",
            "q2_placeobject_vs_move": "Raw SWF tag classes and placement depths/character ids are enumerated below per frame. MOVE-only records intentionally carry no new character id; clip-event paths identify event scripts from the frozen script bundle.",
            "q3_label_exit": "Playback-control calls are enumerated below, but each label's control-flow classification remains pending review of all conditional branches and original playback.",
            "q4_source_invariants": [
                {"fact": "Base-form root placement is frame 1, depth 1, character 533; frame 2 replaces root character with 976.", "source": "game/fighter/rukia.swf root PlaceObject2 tags; hash-bound source record above."},
                {"fact": "The base timeline calls stop() on frame 1; frame 2 resets hits = 0.", "source": "scripts/fighter/rukia.json → DefineSprite_533/frame_1/DoAction.as and frame_2/DoAction.as."},
                {"fact": "The root controller/clip state is instance-owned; a new PlaceObject is a fresh clip instance, while a MOVE updates an existing display-list entry. Exact state retention by depth is shown in frame change records; runtime callback ordering still requires player evidence.", "source": "SWF PlaceObject2/RemoveObject tags and corresponding scripts/fighter/rukia.json clip-action paths."},
                {"fact": "The base timeline itself includes a late `万解` label at frames 1144–1178; it is excluded from base-form implementation scope.", "source": "game/fighter/rukia.swf → sprite_533 frame labels."},
            ],
            "q5_original_same_input": "Not yet captured. Requires an exclusive native Flash GUI capture window and fixed input/replay; no parity claim is made.",
        },
        "actions": action_records,
    }


if __name__ == "__main__":
    output = ROOT / "evidence/characters/rukia/base-source-audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    result = build()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.relative_to(ROOT).as_posix(), "actions": len(result["actions"]), "sprite": result["source"]["base_timeline_sprite_id"]}, ensure_ascii=False))
