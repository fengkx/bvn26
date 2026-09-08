"""Build source-traceable combat metadata for the first playable slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

_IMPORTER_DIR = Path(__file__).resolve().parent
if str(_IMPORTER_DIR) not in sys.path:
    sys.path.insert(0, str(_IMPORTER_DIR))
from command_catalog import build_command_catalog  # noqa: E402


SCRIPT_PATH = re.compile(
    r"^DefineSprite_(?P<sprite>\d+)/frame_(?P<frame>\d+)/(?P<kind>.+)$"
)
PLACEMENT_PATH = re.compile(r"^PlaceObject[23]_(?P<character>\d+)_(?P<depth>\d+)/")
GOTO = re.compile(r'gotoAnd(?:Play|Stop)\("(?P<label>[^\"]+)"\)')
UNCONDITIONAL_GOTO_STOP = re.compile(r'gotoAndStop\("(?P<label>[^\"]+)"\)')
ENERGY_COST = re.compile(r"ql\s*-=\s*(?P<cost>\d+)")
ENERGY_DELTA = re.compile(r"ql\s*(?P<operator>\+=|-=)\s*(?P<value>\d+(?:\.\d+)?)")
SCREEN_FLASH = re.compile(r"_root\.shine\(\s*(?P<color>\d*)\s*\)")
SPEED_EXPR = re.compile(
    r"(?:Math\.round\()?(?P<neg>-\s*)?_parent\.speed"
    r"(?:\s*(?P<op>[*/])\s*(?P<num>\d+(?:\.\d+)?))?(?:\))?"
)
XSCALE_MOVE = re.compile(
    r"if\s*\(\s*_parent\._parent\._xscale\s*(?P<cmp><|>)\s*0\s*\)\s*\{"
    r"\s*_parent\._parent\._x\s*(?P<op>\+=|-=)\s*(?P<expr>[^;]+);",
    re.S,
)
PARENT_X = re.compile(r"_parent\._parent\._x\s*(?P<op>\+=|-=)\s*(?P<expr>[^;]+);")
PARENT_Y = re.compile(r"_parent\._parent\._y\s*(?P<op>\+=|-=)\s*(?P<expr>[^;]+);")
XSCALE_TEST = re.compile(r"_parent\._parent\._xscale\s*(?P<cmp><|>)\s*0")
MOVE_X = re.compile(r"moveX\((?P<value>-?\d+(?:\.\d+)?)\)")
CONTACT_GOTO = re.compile(
    r"hitTest\([^)]+\)[\s\S]{0,240}?gotoAndPlay\(\"(?P<label>[^\"]+)\"\)"
)
CONTACT_INSTANCE = re.compile(
    r"(?:_parent\.)?(?P<name>[A-Za-z0-9_]+atm)\.hitTest"
)
LAND_GOTO = re.compile(
    r"if\s*\(\s*_parent\.(?:touchFloor|touch)(?:\s*==\s*true)?\s*\)[\s\S]{0,80}?"
    r"gotoAndPlay\(\"(?P<label>[^\"]+)\"\)"
)
ON_JUMPING = re.compile(r"onJumping\s*\(\s*(?P<step>\d+)\s*\)")
PROJECTILE_SPEED = re.compile(
    r"movspeed\s*=\s*_parent\.speed\s*\*\s*(?P<factor>\d+(?:\.\d+)?)"
)
PROJECTILE_X = re.compile(r"_X\s*=\s*_X\s*(?P<op>\+|-)\s*movspeed")
PROJECTILE_Y = re.compile(r"_Y\s*=\s*_Y\s*(?P<op>\+|-)\s*movspeed")
PROJECTILE_HIT_GOTO = re.compile(r"gotoAndPlay\((?P<frame>\d+)\)")
NESTED_FRAME_SCRIPT = re.compile(
    r"^DefineSprite_(?P<sprite>\d+)/frame_(?P<frame>\d+)/DoAction"
)
CLIP_RENAME = re.compile(r"(?:this\.)?_name\s*=\s*\"(?P<name>[^\"]+)\"")
CHECK_DEAD = re.compile(
    r"function checkDead\(fly\)\s*\{(?P<body>.*?)\nfunction ",
    re.S,
)
CHECK_DEAD_LAUNCH = re.compile(r'gotoAndStop\("(?P<label>[^\"]+)"\)')
SW_STOP = re.compile(r"if\s*\(\s*sw\s*==\s*true\s*\)\s*\{\s*stop\(\);\s*\}", re.S)
HIT_KEYS = re.compile(r'var hitks\s*=\s*\[(?P<keys>[^\]]+)\]')
QUOTED_VALUE = re.compile(r'"(?P<value>[^"]+)"')
REPO_ROOT = Path(__file__).resolve().parents[2]


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_speed_factor(expr: str) -> tuple[float, bool] | None:
    match = SPEED_EXPR.fullmatch(expr.strip())
    if match is None:
        return None
    factor = 1.0
    if match["op"] == "/":
        factor = 1.0 / float(match["num"])
    elif match["op"] == "*":
        factor = float(match["num"])
    if match["neg"]:
        factor = -factor
    return factor, expr.strip().startswith("Math.round(")


def parse_horizontal_motion(source: str) -> tuple[float, bool] | None:
    xscale = XSCALE_MOVE.search(source)
    cmp_op = None
    assign_op = None
    expr = None
    if xscale is not None:
        cmp_op = xscale["cmp"]
        assign_op = xscale["op"]
        expr = xscale["expr"]
    else:
        scale_test = XSCALE_TEST.search(source)
        parent_x = PARENT_X.search(source)
        if scale_test is not None and parent_x is not None:
            cmp_op = scale_test["cmp"]
            assign_op = parent_x["op"]
            expr = parent_x["expr"]
    if expr is None:
        return None
    parsed = parse_speed_factor(expr)
    if parsed is None:
        return None
    factor, rounded = parsed
    facing_forward = (cmp_op == ">" and assign_op == "+=") or (
        cmp_op == "<" and assign_op == "-="
    )
    return (factor if facing_forward else -factor), rounded


def parse_jumping_step(source: str) -> int | None:
    match = ON_JUMPING.search(source)
    if match is None:
        return None
    return int(match["step"])


def parse_fighter_motion(source: str) -> dict[str, Any] | None:
    if "moveLeft()" in source or "moveRight()" in source:
        return None
    if "_parent._parent.scale_X" in source:
        return None
    motion: dict[str, Any] = {}
    horizontal = parse_horizontal_motion(source)
    if horizontal is not None:
        motion["forward_speed_factor"] = horizontal[0]
        motion["round_forward"] = horizontal[1]
    move = MOVE_X.search(source)
    if move is not None:
        motion["forward_pixels"] = float(move["value"])
    y_move = PARENT_Y.search(source)
    if y_move is not None:
        parsed = parse_speed_factor(y_move["expr"])
        if parsed is None:
            return None
        factor, rounded = parsed
        motion["vertical_speed_factor"] = (
            factor if y_move["op"] == "+=" else -factor
        )
        motion["round_vertical"] = rounded
    contact = CONTACT_GOTO.search(source)
    if contact is not None and "_X =" not in source:
        motion["contact_cancel_to"] = contact["label"]
        instance = CONTACT_INSTANCE.search(source)
        if instance is not None:
            motion["contact_instance"] = instance["name"]
    land = LAND_GOTO.search(source)
    if land is not None:
        motion["land_cancel_to"] = land["label"]
    if not any(
        key in motion
        for key in (
            "forward_speed_factor",
            "forward_pixels",
            "vertical_speed_factor",
        )
    ):
        return None
    return motion


LOCOMOTION_OR_GUARD = {
    "站立",
    "走",
    "瞬步",
    "跳",
    "跳2",
    "落",
    "落2",
    "落地",
    "防御",
    "防御2",
    "防住",
}


def span_has_unconditional_terminal(scripts: list[dict[str, Any]], label: str) -> bool:
    for script in scripts:
        if script["action"] != label or script["kind"] != "frame_action":
            continue
        if parse_unconditional_exit(script["source"]) is not None:
            return True
        if script["source"].strip() == "stop();":
            return True
    return False


def compile_timeline_fallthroughs(
    ranges: dict[str, dict[str, Any]], scripts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Adjacent labels with no stop/goto keep playing into the next label.

    鸣人 砍技1 has no terminal script, so the playhead reaches 砍技12 even
    on a whiff. Contact gotoAndPlay is only an early explode.
    """
    ordered = sorted(
        ranges.items(),
        key=lambda item: (int(item[1]["start_frame"]), item[0]),
    )
    result: list[dict[str, Any]] = []
    for (label, span), (next_label, next_span) in zip(ordered, ordered[1:]):
        if label in LOCOMOTION_OR_GUARD:
            continue
        if int(next_span["start_frame"]) != int(span["end_frame"]) + 1:
            continue
        if span_has_unconditional_terminal(scripts, label):
            continue
        result.append(
            {
                "from": label,
                "to": next_label,
                "frame": int(next_span["start_frame"]),
                "condition": "timeline_fallthrough",
            }
        )
    return result


def parse_unconditional_exit(source: str) -> str | None:
    """Frame scripts that always leave the current clip, e.g. gotoAndStop(\"落\").

    Conditional branches and clip enterFrame cancels stay out of action_exits.
    """
    if "if(" in source.replace(" ", ""):
        return None
    matches = list(UNCONDITIONAL_GOTO_STOP.finditer(source))
    if len(matches) != 1:
        return None
    return matches[0]["label"]


def parse_projectile_motion(source: str) -> dict[str, Any] | None:
    if "_X = _X" not in source and "_Y = _Y" not in source:
        return None
    motion: dict[str, Any] = {}
    x_move = PROJECTILE_X.search(source)
    if x_move is not None:
        motion["local_x_factor"] = 1.0 if x_move["op"] == "+" else -1.0
    y_move = PROJECTILE_Y.search(source)
    if y_move is not None:
        motion["local_y_factor"] = 1.0 if y_move["op"] == "+" else -1.0
    if "movspeed = 0" in source:
        hit_goto = PROJECTILE_HIT_GOTO.search(source)
        if hit_goto is not None:
            motion["on_hit_goto_frame"] = int(hit_goto["frame"])
    return motion or None


def helper_from_catalog(fighter_id: str) -> dict[str, Any]:
    manifest = json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))
    fighter = manifest["fighter_catalog"].get(fighter_id, {})
    helper_id = fighter.get("fz")
    if not helper_id:
        return {}
    helper = manifest["fighter_catalog"].get(helper_id, {})
    return {
        "helper_id": helper_id,
        "helper_swf": helper.get("fzurl") or helper.get("url", ""),
        "behind_pixels": 20,
        "start_frame": 2,
    }


def placement_name(
    frames_by_number: dict[int, dict[str, Any]], frame: int, depth: int
) -> str:
    current = frames_by_number.get(frame)
    if current is None:
        return ""
    for placement in current["display_list"]:
        if int(placement["depth"]) == depth:
            return str(placement.get("name", ""))
    return ""


def placement_character_id(
    frames_by_number: dict[int, dict[str, Any]], frame: int, depth: int
) -> int | None:
    current = frames_by_number.get(frame)
    if current is None:
        return None
    for placement in current["display_list"]:
        if int(placement["depth"]) == depth:
            return int(placement.get("character_id", 0)) or None
    return None


def parse_clip_timeline(
    script_bundle: dict[str, Any], character_id: int
) -> dict[str, Any]:
    stop_frames: list[dict[str, Any]] = []
    rename_frames: list[dict[str, Any]] = []
    for script in script_bundle["scripts"]:
        match = NESTED_FRAME_SCRIPT.match(script["path"])
        if match is None or int(match["sprite"]) != character_id:
            continue
        if "CLIPACTIONRECORD" in script["path"]:
            continue
        frame = int(match["frame"])
        source = script["source"].strip()
        record = {
            "frame": frame,
            "source_path": script["path"],
            "source_sha256": text_sha256(script["source"]),
        }
        if source == "stop();":
            stop_frames.append(record)
        rename = CLIP_RENAME.search(script["source"])
        if rename is not None:
            rename_frames.append({**record, "instance_name": rename["name"]})
    stop_frames.sort(key=lambda item: item["frame"])
    rename_frames.sort(key=lambda item: item["frame"])
    timeline: dict[str, Any] = {"character_id": character_id}
    if stop_frames:
        timeline["stop_frames"] = [item["frame"] for item in stop_frames]
        timeline["stop_sources"] = stop_frames
    if rename_frames:
        timeline["rename_frames"] = rename_frames
    return timeline


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


def extract_death(
    script_bundle: dict[str, Any],
    sprite_id: int,
    scripts: list[dict[str, Any]],
    ranges: dict[str, dict[str, int]],
) -> dict[str, Any] | None:
    check_script = next(
        (
            script
            for script in script_bundle["scripts"]
            if (match := SCRIPT_PATH.match(script["path"])) is not None
            and int(match["sprite"]) == sprite_id
            and match["frame"] == "1"
            and "function checkDead" in script["source"]
        ),
        None,
    )
    if check_script is None:
        return None
    body_match = CHECK_DEAD.search(check_script["source"].replace("\r\n", "\n"))
    if body_match is None:
        raise ValueError(f"Cannot parse checkDead in {check_script['path']}")
    launch_match = CHECK_DEAD_LAUNCH.search(body_match["body"])
    if launch_match is None:
        raise ValueError(f"checkDead has no launch label in {check_script['path']}")
    launch_label = launch_match["label"]
    if launch_label not in ranges:
        raise ValueError(f"checkDead launch label missing from timeline: {launch_label}")
    if "击落地" not in ranges:
        raise ValueError("checkDead requires sourced 击落地 label")
    stop_scripts = [
        script
        for script in scripts
        if script["action"] == "击落地"
        and script["kind"] == "frame_action"
        and SW_STOP.search(script["source"].replace("\r\n", "\n"))
    ]
    if len(stop_scripts) != 1:
        raise ValueError(
            f"Expected one 击落地 sw-stop frame, got {len(stop_scripts)}"
        )
    stop = stop_scripts[0]
    return {
        "flag": "sw",
        "launch_label": launch_label,
        "down_label": "击落地",
        "knockdown_stop_frame": stop["frame"],
        "practice_mode_skips": 4,
        "source_path": check_script["path"],
        "source_sha256": text_sha256(check_script["source"]),
        "stop_source_path": stop["path"],
        "stop_source_sha256": stop["source_sha256"],
    }


def action_for_frame(
    frame: int, ranges: dict[str, dict[str, int]]
) -> str | None:
    for label, span in ranges.items():
        if span["start_frame"] <= frame <= span["end_frame"]:
            return label
    return None


def extract_hit_priority(script_bundle: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    for script in script_bundle["scripts"]:
        match = HIT_KEYS.search(script["source"])
        if match is None or "function getHitObj" not in script["source"]:
            continue
        keys = [item["value"] for item in QUOTED_VALUE.finditer(match["keys"])]
        if keys:
            candidates.append((script, keys))
    if not candidates:
        raise ValueError("Cannot locate source hitks priority table")
    script, keys = candidates[0]
    instances = []
    for key in keys:
        instances.append(f"{key}atm")
        instances.extend(f"{key}{suffix}atm" for suffix in range(1, 6))
    return {
        "instances": instances,
        "source_path": script["path"],
        "source_sha256": text_sha256(script["source"]),
    }


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

    timeline_fallthroughs = compile_timeline_fallthroughs(ranges, scripts)
    stand_exit_actions = {
        *combo_labels,
        *fighter["actions"]["hurt"],
        *fighter["actions"]["special"],
        *(item["to"] for item in timeline_fallthroughs),
    }
    exits = {}
    for script in scripts:
        if script["kind"] != "frame_action":
            continue
        target = parse_unconditional_exit(script["source"])
        if target is None or target == script["action"]:
            continue
        if target == "站立" and script["action"] not in stand_exit_actions:
            continue
        if target != "站立" and target not in ("落", "落2"):
            continue
        current = exits.get(script["action"])
        if current is not None and current["frame"] <= script["frame"]:
            continue
        exits[script["action"]] = {
            "frame": script["frame"],
            "target": target,
            "source_path": script["path"],
            "source_sha256": script["source_sha256"],
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

    energy_events = []
    presentation_events = []
    for script in scripts:
        if script["kind"] != "frame_action" or script["frame"] == 1:
            continue
        for match in ENERGY_DELTA.finditer(script["source"]):
            value = float(match["value"])
            energy_events.append(
                {
                    "action": script["action"],
                    "frame": script["frame"],
                    "delta": value if match["operator"] == "+=" else -value,
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                }
            )
        for match in SCREEN_FLASH.finditer(script["source"]):
            color = int(match["color"]) if match["color"] else 0xFFFFFF
            presentation_events.append(
                {
                    "action": script["action"],
                    "frame": script["frame"],
                    "op": "screen_flash",
                    "color_rgb24": color,
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                }
            )

    helper = helper_from_catalog(fighter["fighter_id"])
    summon_events = []
    for script in scripts:
        if script["kind"] != "frame_action":
            continue
        if "function doZhaoHuan" in script["source"]:
            continue
        if "doZhaoHuan()" not in script["source"]:
            continue
        summon_events.append(
            {
                "action": script["action"],
                "frame": script["frame"],
                "energy_delta": -100,
                **helper,
                "source_path": script["path"],
                "source_sha256": script["source_sha256"],
            }
        )

    motion_windows = []
    jump_windows = []
    projectiles = []
    projectile_speeds: dict[tuple[int, int], float] = {}
    clip_scripts = []
    for script in scripts:
        if script["kind"] != "clip_action":
            continue
        path_tail = SCRIPT_PATH.match(script["path"])["kind"]
        placement_match = PLACEMENT_PATH.match(path_tail)
        if placement_match is None:
            continue
        depth = int(placement_match["depth"])
        clip_scripts.append((script, depth))
        speed_match = PROJECTILE_SPEED.search(script["source"])
        if speed_match is not None:
            projectile_speeds[(script["frame"], depth)] = float(speed_match["factor"])
    for script, depth in clip_scripts:
        projectile = parse_projectile_motion(script["source"])
        if projectile is not None:
            end_frame, bytecode_hash = clip_lifetime(
                frames_by_number, script["frame"], depth
            )
            instance_name = placement_name(
                frames_by_number, script["frame"], depth
            )
            character_id = placement_character_id(
                frames_by_number, script["frame"], depth
            )
            clip_timeline = (
                parse_clip_timeline(script_bundle, character_id)
                if character_id is not None
                else {}
            )
            projectiles.append(
                {
                    "action": script["action"],
                    "instance_name": instance_name,
                    "start_frame": script["frame"],
                    "end_frame": end_frame,
                    "speed_factor": projectile_speeds.get(
                        (script["frame"], depth), 1.0
                    ),
                    **projectile,
                    **clip_timeline,
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                    "action_bytes_sha256": bytecode_hash,
                }
            )
            continue
        jumping_step = parse_jumping_step(script["source"])
        if jumping_step is not None:
            end_frame, bytecode_hash = clip_lifetime(
                frames_by_number, script["frame"], depth
            )
            jump_windows.append(
                {
                    "action": script["action"],
                    "start_frame": script["frame"],
                    "end_frame": end_frame,
                    "step": jumping_step,
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                    "action_bytes_sha256": bytecode_hash,
                }
            )
            continue
        motion = parse_fighter_motion(script["source"])
        if motion is None:
            continue
        end_frame, bytecode_hash = clip_lifetime(
            frames_by_number, script["frame"], depth
        )
        motion_windows.append(
            {
                "action": script["action"],
                "start_frame": script["frame"],
                "end_frame": end_frame,
                **motion,
                "source_path": script["path"],
                "source_sha256": script["source_sha256"],
                "action_bytes_sha256": bytecode_hash,
            }
        )

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
        "timeline_fallthroughs": timeline_fallthroughs,
        "hurt": {
            "label": hurt_label,
            "stop_frame": stop_scripts[0]["frame"],
            "hitstun_ticks_formula": "hitstun_ms / 1000 * 30",
            "source_path": stop_scripts[0]["path"],
            "source_sha256": stop_scripts[0]["source_sha256"],
        },
        "death": extract_death(script_bundle, sprite_id, scripts, ranges),
        "attacks": fighter["hit_parameters"]["attacks"],
        "hit_priority": extract_hit_priority(script_bundle),
        "energy_events": sorted(
            energy_events, key=lambda item: (item["frame"], item["action"])
        ),
        "presentation_events": sorted(
            presentation_events, key=lambda item: (item["frame"], item["action"])
        ),
        "motion_windows": sorted(
            motion_windows,
            key=lambda item: (item["start_frame"], item["action"]),
        ),
        "jump_windows": sorted(
            jump_windows,
            key=lambda item: (item["start_frame"], item["step"]),
        ),
        "projectiles": sorted(
            projectiles,
            key=lambda item: (item["start_frame"], item["instance_name"]),
        ),
        "summon_events": sorted(
            summon_events, key=lambda item: (item["frame"], item["action"])
        ),
        "command_catalog": build_command_catalog(
            fighter, script_bundle, scripts, motion_windows
        ),
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
