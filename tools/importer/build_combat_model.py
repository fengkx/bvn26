"""Build source-traceable combat metadata for the first playable slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_PATH = re.compile(
    r"^DefineSprite_(?P<sprite>\d+)/frame_(?P<frame>\d+)/(?P<kind>.+)$"
)
PLACEMENT_PATH = re.compile(r"^PlaceObject[23]_(?P<character>\d+)_(?P<depth>\d+)/")
GOTO = re.compile(r'gotoAnd(?:Play|Stop)\("(?P<label>[^\"]+)"\)')
ENERGY_COST = re.compile(r"ql\s*-=\s*(?P<cost>\d+)")


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def contiguous_windows(frames: list[int]) -> list[dict[str, int]]:
    if not frames:
        return []
    windows = []
    start = previous = frames[0]
    for frame in frames[1:]:
        if frame != previous + 1:
            windows.append({"start_frame": start, "end_frame": previous})
            start = frame
        previous = frame
    windows.append({"start_frame": start, "end_frame": previous})
    return windows


def target_ranges(fighter: dict[str, Any]) -> dict[str, dict[str, int]]:
    result = {}
    for group_name, actions in fighter["actions"].items():
        for label, span in actions.items():
            result[label] = {**span, "group": group_name}
    return result


def action_for_frame(
    frame: int, ranges: dict[str, dict[str, int]]
) -> str | None:
    for label, span in ranges.items():
        if span["start_frame"] <= frame <= span["end_frame"]:
            return label
    return None


def clip_lifetime(
    frames_by_number: dict[int, dict[str, Any]], start_frame: int, depth: int
) -> tuple[int, str]:
    placement = next(
        (
            item
            for item in frames_by_number[start_frame]["display_list"]
            if int(item["depth"]) == depth and item.get("clip_actions")
        ),
        None,
    )
    if placement is None:
        raise ValueError(f"No clip action at frame {start_frame}, depth {depth}")
    action_hash = placement["clip_actions"][0]["action_bytes_sha256"]
    end_frame = start_frame
    for frame_number in sorted(frames_by_number):
        if frame_number < start_frame:
            continue
        current = next(
            (
                item
                for item in frames_by_number[frame_number]["display_list"]
                if int(item["depth"]) == depth
                and any(
                    record["action_bytes_sha256"] == action_hash
                    for record in item.get("clip_actions", [])
                )
            ),
            None,
        )
        if current is None:
            break
        end_frame = frame_number
    return end_frame, action_hash


def build_model(
    fighter_path: Path, timeline_path: Path, scripts_path: Path
) -> dict[str, Any]:
    fighter = json.loads(fighter_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    script_bundle = json.loads(scripts_path.read_text(encoding="utf-8"))
    sprite_id = int(fighter["source"]["timeline_symbol_id"])
    ranges = target_ranges(fighter)
    frames_by_number = {int(frame["frame"]): frame for frame in timeline["frames"]}

    scripts = []
    for script in script_bundle["scripts"]:
        match = SCRIPT_PATH.match(script["path"])
        if match is None or int(match["sprite"]) != sprite_id:
            continue
        frame = int(match["frame"])
        action = action_for_frame(frame, ranges)
        if action is None:
            continue
        scripts.append(
            {
                "action": action,
                "frame": frame,
                "kind": "clip_action" if "CLIPACTIONRECORD" in match["kind"] else "frame_action",
                "path": script["path"],
                "source_sha256": text_sha256(script["source"]),
                "source": script["source"],
            }
        )

    hitbox_windows: dict[str, list[dict[str, int]]] = {}
    for label, span in ranges.items():
        named_frames: dict[str, list[int]] = {}
        for frame_number in range(span["start_frame"], span["end_frame"] + 1):
            frame = frames_by_number.get(frame_number)
            if frame is None:
                continue
            for placement in frame["display_list"]:
                name = str(placement.get("name", ""))
                if name.endswith("atm"):
                    named_frames.setdefault(name, []).append(frame_number)
        if named_frames:
            hitbox_windows[label] = [
                {"instance_name": name, **window}
                for name in sorted(named_frames)
                for window in contiguous_windows(named_frames[name])
            ]

    combo_labels = list(fighter["actions"]["ground_combo"])
    combo_transitions = []
    for index, label in enumerate(combo_labels[:-1]):
        next_label = combo_labels[index + 1]
        candidates = [
            script
            for script in scripts
            if script["action"] == label
            and script["kind"] == "clip_action"
            and "nornalhit(true)" in script["source"]
            and any(match["label"] == next_label for match in GOTO.finditer(script["source"]))
        ]
        if len(candidates) != 1:
            raise ValueError(f"Expected one {label} -> {next_label} transition, got {len(candidates)}")
        candidate = candidates[0]
        path_tail = SCRIPT_PATH.match(candidate["path"])["kind"]
        placement_match = PLACEMENT_PATH.match(path_tail)
        if placement_match is None:
            raise ValueError(f"Cannot locate placement depth for {candidate['path']}")
        end_frame, bytecode_hash = clip_lifetime(
            frames_by_number, candidate["frame"], int(placement_match["depth"])
        )
        combo_transitions.append(
            {
                "from": label,
                "to": next_label,
                "start_frame": candidate["frame"],
                "end_frame": end_frame,
                "condition": "normal_attack_held",
                "source_path": candidate["path"],
                "source_sha256": candidate["source_sha256"],
                "action_bytes_sha256": bytecode_hash,
            }
        )

    exits = {}
    for label in (*combo_labels, *fighter["actions"]["hurt"], *fighter["actions"]["special"]):
        exit_scripts = [
            script
            for script in scripts
            if script["action"] == label
            and script["kind"] == "frame_action"
            and 'gotoAndStop("站立")' in script["source"]
        ]
        if exit_scripts:
            first = min(exit_scripts, key=lambda item: item["frame"])
            exits[label] = {
                "frame": first["frame"],
                "target": "站立",
                "source_path": first["path"],
                "source_sha256": first["source_sha256"],
            }

    hurt_label = next(iter(fighter["actions"]["hurt"]))
    stop_scripts = [
        script
        for script in scripts
        if script["action"] == hurt_label
        and script["kind"] == "frame_action"
        and script["source"].strip() == "stop();"
    ]
    if len(stop_scripts) != 1:
        raise ValueError(f"Expected one hurt stop frame, got {len(stop_scripts)}")

    special_labels = list(fighter["actions"]["special"])
    special_transitions = []
    for label in special_labels:
        for script in scripts:
            if script["action"] != label or script["kind"] != "frame_action":
                continue
            for goto_match in GOTO.finditer(script["source"]):
                target = goto_match["label"]
                if target not in special_labels:
                    continue
                special_transitions.append(
                    {
                        "from": label,
                        "to": target,
                        "frame": script["frame"],
                        "condition": (
                            "source_condition" if "if(" in script["source"] else "always"
                        ),
                        "source_path": script["path"],
                        "source_sha256": script["source_sha256"],
                    }
                )
    for label, next_label in zip(special_labels, special_labels[1:]):
        span = fighter["actions"]["special"][label]
        next_span = fighter["actions"]["special"][next_label]
        if next_span["start_frame"] != span["end_frame"] + 1:
            continue
        if any(
            transition["from"] == label and transition["to"] == next_label
            for transition in special_transitions
        ):
            continue
        special_transitions.append(
            {
                "from": label,
                "to": next_label,
                "frame": next_span["start_frame"],
                "condition": "timeline_fallthrough",
            }
        )
    first_special = special_labels[0]
    cost_matches = [
        (script, match)
        for script in scripts
        if script["action"] == first_special
        for match in ENERGY_COST.finditer(script["source"])
    ]
    if len(cost_matches) != 1:
        raise ValueError(f"Expected one energy cost for {first_special}, got {len(cost_matches)}")
    cost_script, cost_match = cost_matches[0]

    return {
        "format": "bvn26-combat-model-v1",
        "status": "reverse_engineering_intermediate",
        "fighter_id": fighter["fighter_id"],
        "simulation_hz": 30,
        "source": {
            "fighter_slice": fighter_path.as_posix(),
            "timeline": timeline_path.as_posix(),
            "script_bundle": scripts_path.as_posix(),
            "timeline_symbol_id": sprite_id,
        },
        "movement": {
            "speed_per_tick": fighter["movement_constants"]["speed_per_tick"],
            "standing": fighter["actions"]["movement"]["站立"],
            "walking": fighter["actions"]["movement"]["走"],
        },
        "combo": {
            "labels": combo_labels,
            "transitions": combo_transitions,
        },
        "special": {
            "entry_label": first_special,
            "energy_cost": int(cost_match["cost"]),
            "transitions": sorted(
                special_transitions, key=lambda item: (item["frame"], item["to"])
            ),
            "cost_source_path": cost_script["path"],
            "cost_source_sha256": cost_script["source_sha256"],
        },
        "hitbox_windows": hitbox_windows,
        "action_exits": exits,
        "hurt": {
            "label": hurt_label,
            "stop_frame": stop_scripts[0]["frame"],
            "hitstun_ticks_formula": "hitstun_ms / 1000 * 30",
            "source_path": stop_scripts[0]["path"],
            "source_sha256": stop_scripts[0]["source_sha256"],
        },
        "attacks": fighter["hit_parameters"]["attacks"],
        "indexed_source_events": [
            {key: value for key, value in script.items() if key != "source"}
            for script in scripts
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fighter", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--scripts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = build_model(args.fighter, args.timeline, args.scripts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"fighter_id": model["fighter_id"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
