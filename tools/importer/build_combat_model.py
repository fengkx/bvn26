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
from compile_hit_receive import (  # noqa: E402
    compile_fighter_hit_receive,
    compile_shared_hit_receive,
    extract_function,
)


SCRIPT_PATH = re.compile(
    r"^DefineSprite_(?P<sprite>\d+)/frame_(?P<frame>\d+)/(?P<kind>.+)$"
)
PLACEMENT_PATH = re.compile(r"^PlaceObject[23]_(?P<character>\d+)_(?P<depth>\d+)/")
GOTO = re.compile(r'gotoAnd(?:Play|Stop)\("(?P<label>[^\"]+)"\)')
UNCONDITIONAL_GOTO_STOP = re.compile(r'gotoAndStop\("(?P<label>[^\"]+)"\)')
EXIT_IMPULSE = re.compile(
    r"(?P<name>yup|htx|jhp|zl)\s*=\s*(?P<value>-?\d+(?:\.\d+)?)\s*;"
)
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
SCALE_X_SPEED = re.compile(
    r"_parent\._parent\._x\s*(?P<op>\+=|-=)\s*"
    r"_parent\.speed\s*\*\s*(?P<num>\d+(?:\.\d+)?)\s*\*\s*"
    r"_parent\._parent\.scale_X"
)
PIXEL_X = re.compile(
    r"_parent\._parent\._x\s*(?P<op>\+=|-=)\s*(?P<num>\d+(?:\.\d+)?)\s*;"
)
PIXEL_Y = re.compile(
    r"_parent\._parent\._y\s*(?P<op>\+=|-=)\s*(?P<num>\d+(?:\.\d+)?)\s*;"
)
STEER_LEFT = re.compile(
    r"if\s*\(\s*moveLeft\s*\(\s*\)\s*\)\s*\{[^}]*"
    r"_parent\._parent\._x\s*-=\s*_parent\.speed"
)
STEER_RIGHT = re.compile(
    r"if\s*\(\s*moveRight\s*\(\s*\)\s*\)\s*\{[^}]*"
    r"_parent\._parent\._x\s*\+=\s*_parent\.speed"
)
MOVE_X = re.compile(r"moveX\((?P<value>-?\d+(?:\.\d+)?)\)")
PLACE_AT_OPPONENT_X = re.compile(
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\._x\s*=\s*"
    r"_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._x"
)
PLACE_AT_OPPONENT_Y = re.compile(
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\._y\s*=\s*"
    r"_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._y"
    r"(?:\s*(?P<y_op>[+-])\s*(?P<y_num>\d+(?:\.\d+)?))?"
)
# Player-wrapper flash. Not a named clip.
# Unconditional: `_parent._x/_y = opponent._x/_y` [±pixels] and optional jump.
# Facing: both branches assign `_xscale` then `_x` from opponent._x ± pixels
# or `bdmn._width[*N]`. Y may use `bdmn._height[*N]` after the if/else.
PARENT_WARP_X = re.compile(
    r"_parent\._x\s*=\s*_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._x"
    r"(?:\s*(?P<x_op>[+-])\s*(?:"
    r"(?P<x_num>\d+(?:\.\d+)?)"
    r"|"
    r"_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\.mc\.bdmn\._width"
    r"(?:\s*\*\s*(?P<wfac>\d+(?:\.\d+)?))?"
    r"))?\s*;"
)
PARENT_WARP_Y = re.compile(
    r"_parent\._y\s*=\s*_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._y"
    r"(?:\s*(?P<y_op>[+-])\s*(?:"
    r"(?P<y_num>\d+(?:\.\d+)?)"
    r"|"
    r"_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\.mc\.bdmn\._height"
    r"(?:\s*\*\s*(?P<hfac>\d+(?:\.\d+)?))?"
    r"))?\s*;"
)
PARENT_XSCALE_DELTA = re.compile(
    r"^\s*_parent\._x\s*(?P<operator>\+=|-=)\s*_parent\._xscale\s*;\s*$"
)
FACING_BODY_WARP = re.compile(
    r"if\s*\(\s*_parent\._xscale\s*(?P<cmp>[<>])\s*0\s*\)\s*\{\s*"
    r"_parent\._xscale\s*=\s*(?P<then_scale>-?\d+)\s*;\s*"
    r"(?P<then_x>_parent\._x\s*=\s*_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._x[^;]*;)\s*"
    r"\}\s*else\s*\{\s*"
    r"_parent\._xscale\s*=\s*(?P<else_scale>-?\d+)\s*;\s*"
    r"(?P<else_x>_parent\._x\s*=\s*_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._x[^;]*;)\s*"
    r"\}",
    re.S,
)
# Some source timelines branch on facing only to choose the signed offset;
# they intentionally leave the container's existing _xscale unchanged.
FACING_BODY_WARP_NO_SCALE = re.compile(
    r"if\s*\(\s*_parent\._xscale\s*(?P<cmp>[<>])\s*0\s*\)\s*\{\s*"
    r"(?P<then_x>_parent\._x\s*=\s*_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._x[^;]*;)\s*"
    r"\}\s*else\s*\{\s*"
    r"(?P<else_x>_parent\._x\s*=\s*_root\.game\[\s*\"p\"\s*\+\s*pn\s*\]\._x[^;]*;)\s*"
    r"\}",
    re.S,
)
JUMP_ASSIGN = re.compile(r"\bjump\s*=\s*1\s*;")
# Locomotion/guard loops that DATA_CONTRACTS keep unwired so walk and
# held-guard pin stay intact. 落地/瞬步/防住 early gotos are compiled.
UNWIRED_EXIT_PAIRS = {
    ("走", "站立"),
    ("防御2", "站立"),
    ("落", "落"),
    ("落2", "落2"),
}
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
PROJECTILE_LITERAL_DELTA = re.compile(
    r"_(?P<axis>X|Y)\s*=\s*_(?P=axis)\s*(?P<op>\+|-)\s*"
    r"(?P<value>\d+(?:\.\d+)?)"
)
PROJECTILE_HIT_GOTO = re.compile(r"gotoAndPlay\((?P<frame>\d+)\)")
PROJECTILE_LOAD = re.compile(
    r"onClipEvent\(load\)\{\s*"
    r"(?:(?P<played>played\s*=\s*0;)\s*)?"
    r"movspeed\s*=\s*_parent\.speed(?:\s*\*\s*(?P<factor>\d+(?:\.\d+)?))?;\s*\}\s*"
)
PROJECTILE_LITERAL_DECLARATION = re.compile(
    r"var\s+(?P<name>[A-Za-z_]\w*)\s*=\s*"
    r"(?P<value>true|false|-?\d+(?:\.\d+)?)\s*;"
)
PROJECTILE_LOCAL_WRITE = re.compile(
    r"(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<value>true|false|-?\d+(?:\.\d+)?)\s*;"
)
PROJECTILE_LOCAL_CONDITION = re.compile(
    r"(?P<name>[A-Za-z_]\w*)\s*(?P<operator>==|!=)\s*"
    r"(?P<value>true|false|-?\d+(?:\.\d+)?)"
)
PROJECTILE_PARENT_WRITE = re.compile(
    r"_parent\.(?P<field>[A-Za-z_]\w*)\s*=\s*"
    r"(?P<value>true|false|-?\d+(?:\.\d+)?)\s*;"
)
PROJECTILE_HIT_IF = re.compile(
    r"if\s*\(\s*(?:(?P<receiver>[A-Za-z_]\w*)\s*\.\s*)?hitTest\s*\([^{}]*\)\s*\)\s*\{"
)
PROJECTILE_OPPONENT_GOTO = re.compile(
    r"if\(_root\.game\[\"p\" \+ _parent\.pn\]\.mc\.动作\s*==\s*(?P<action>-?\d+)\)\s*"
    r"\{\s*_root\.game\[\"p\" \+ _parent\.pn\]\.mc\.gotoAnd(?P<mode>Play|Stop)"
    r"\(\"(?P<label>[^\"]+)\"\);\s*\}\s*"
)
SOURCE_HEALTH_LOSS = re.compile(
    r"if\s*\(\s*hp\s*>\s*(?P<threshold>\d+(?:\.\d+)?)\s*\)\s*\{\s*"
    r"loseHp\(\s*(?P<above>\d+(?:\.\d+)?)\s*\)\s*;\s*\}\s*"
    r"else\s*\{\s*loseHp\(\s*hp\s*\*\s*(?P<ratio>\d+(?:\.\d+)?)\s*\)\s*;\s*\}",
    re.S,
)
SOURCE_LOSE_HP = re.compile(
    r"function\s+loseHp\s*\(\s*v\s*\)\s*\{\s*"
    r"if\s*\(\s*wudi\s*\)\s*\{\s*return\s+undefined\s*;\s*\}\s*"
    r"hp\s*-=\s*v\s*;\s*\}",
    re.S,
)
DIRECT_YFGJ_CALL = re.compile(r"_root\.yfgj\(\s*_parent\._name\s*\)\s*;")
NESTED_FRAME_SCRIPT = re.compile(
    r"^DefineSprite_(?P<sprite>\d+)/frame_(?P<frame>\d+)/DoAction"
)
CLIP_RENAME = re.compile(r"(?:this\.)?_name\s*=\s*\"(?P<name>[^\"]+)\"")
# Root timeline actions can rename a placed instance (for example
# `dogs._name = "sbsatm"`) without giving the instance its final authored
# name in the display list.  Keep this separate from CLIP_RENAME: nested clip
# timelines use `this._name`, while root assignments need a depth/lifetime
# lookup against the root display list.
ROOT_CLIP_RENAME = re.compile(
    r"(?P<object>[A-Za-z_]\w*)\._name\s*=\s*\"(?P<name>[^\"]+)\""
)
ROOT_CLIP_RENAME_ASSIGN = re.compile(
    r"(?P<object>[A-Za-z_]\w*)\._name\s*=\s*\"(?P<name>[^\"]+)\"\s*;"
)
# Frame DoAction that overwrites a named clip's local _x so the clip
# registration sits on the opponent container. Facing flip is the
# `_parent._xscale > 0` branch; optional _y uses the same clip name.
PLACE_AT_OPPONENT_X = re.compile(
    r"if\s*\(\s*_parent\._xscale\s*>\s*0\s*\)\s*\{\s*"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\._x\s*=\s*"
    r"_root\.game\[\"p\"\s*\+\s*pn\]\._x\s*-\s*_parent\._x\s*;\s*"
    r"\}\s*else\s*\{\s*"
    r"(?P=name)\._x\s*=\s*_parent\._x\s*-\s*_root\.game\[\"p\"\s*\+\s*pn\]\._x\s*;\s*"
    r"\}",
    re.S,
)
PLACE_AT_OPPONENT_Y = re.compile(
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\._y\s*=\s*"
    r"_root\.game\[\"p\"\s*\+\s*pn\]\._y\s*-\s*_parent\._y"
    r"(?:\s*(?P<y_op>[+-])\s*(?P<y_num>\d+(?:\.\d+)?))?\s*;"
)
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


def parse_place_at_opponent(source: str) -> dict[str, Any] | None:
    match = PLACE_AT_OPPONENT_X.search(source)
    if match is None:
        return None
    name = match["name"]
    if name == "_parent":
        return None
    result: dict[str, Any] = {
        "instance_name": name,
        "op": "place_at_opponent",
        "place_x": True,
        "line": source.count("\n", 0, source.find(f"{name}._x", match.start())) + 1,
    }
    y_match = PLACE_AT_OPPONENT_Y.search(source)
    if y_match is not None and y_match["name"] == name:
        result["place_y"] = True
        extra = 0.0
        if y_match["y_num"]:
            extra = float(y_match["y_num"])
            if y_match["y_op"] == "-":
                extra = -extra
        if extra:
            result["y_pixels"] = extra
    return result


def _signed_pixel(match: re.Match[str], op_key: str, num_key: str) -> float:
    if not match[num_key]:
        return 0.0
    extra = float(match[num_key])
    return -extra if match[op_key] == "-" else extra


def _xscale_facing(scale: str) -> int:
    return 1 if float(scale) > 0 else -1


def _warp_x_fields(source: str) -> dict[str, Any] | None:
    match = PARENT_WARP_X.search(source)
    if match is None:
        return None
    fields: dict[str, Any] = {}
    extra_x = _signed_pixel(match, "x_op", "x_num")
    if extra_x:
        fields["x_pixels"] = extra_x
    elif match["x_op"] and match["x_num"] is None:
        factor = float(match["wfac"]) if match["wfac"] else 1.0
        fields["x_bdmn_width"] = -factor if match["x_op"] == "-" else factor
    return fields


def _apply_warp_y(result: dict[str, Any], source: str) -> None:
    y_match = PARENT_WARP_Y.search(source)
    if y_match is None:
        return
    result["place_y"] = True
    extra_y = _signed_pixel(y_match, "y_op", "y_num")
    if extra_y:
        result["y_pixels"] = extra_y
    elif y_match["y_op"] and y_match["y_num"] is None:
        factor = float(y_match["hfac"]) if y_match["hfac"] else 1.0
        result["y_bdmn_height"] = -factor if y_match["y_op"] == "-" else factor


def parse_body_warp(source: str) -> dict[str, Any] | None:
    xscale_delta = PARENT_XSCALE_DELTA.fullmatch(source)
    if xscale_delta is not None:
        return {
            "op": "offset_parent_x_by_xscale",
            "xscale_factor": 1.0 if xscale_delta["operator"] == "+=" else -1.0,
        }
    facing = FACING_BODY_WARP.search(source)
    if facing is not None:
        then_x = _warp_x_fields(facing["then_x"])
        else_x = _warp_x_fields(facing["else_x"])
        if then_x is None or else_x is None:
            return None
        then_branch = {"set_facing": _xscale_facing(facing["then_scale"]), **then_x}
        else_branch = {"set_facing": _xscale_facing(facing["else_scale"]), **else_x}
        result: dict[str, Any] = {
            "op": "warp_to_opponent",
            "place_x": True,
        }
        if facing["cmp"] == ">":
            result["xscale_gt_0"] = then_branch
            result["xscale_lt_0"] = else_branch
        else:
            result["xscale_lt_0"] = then_branch
            result["xscale_gt_0"] = else_branch
        _apply_warp_y(result, source)
        if JUMP_ASSIGN.search(source):
            result["set_jump"] = True
        return result
    facing_without_scale = FACING_BODY_WARP_NO_SCALE.search(source)
    if facing_without_scale is not None:
        then_x = _warp_x_fields(facing_without_scale["then_x"])
        else_x = _warp_x_fields(facing_without_scale["else_x"])
        if then_x is None or else_x is None:
            return None
        result = {
            "op": "warp_to_opponent",
            "place_x": True,
        }
        if facing_without_scale["cmp"] == ">":
            result["xscale_gt_0"] = then_x
            result["xscale_lt_0"] = else_x
        else:
            result["xscale_lt_0"] = then_x
            result["xscale_gt_0"] = else_x
        _apply_warp_y(result, source)
        if JUMP_ASSIGN.search(source):
            result["set_jump"] = True
        return result
    if re.search(r"_xscale|bdmn", source):
        return None
    x_fields = _warp_x_fields(source)
    if x_fields is None:
        return None
    result = {
        "op": "warp_to_opponent",
        "place_x": True,
        **x_fields,
    }
    _apply_warp_y(result, source)
    if JUMP_ASSIGN.search(source):
        result["set_jump"] = True
    return result


def parse_jumping_step(source: str) -> int | None:
    match = ON_JUMPING.search(source)
    if match is None:
        return None
    return int(match["step"])


def parse_scale_x_motion(source: str) -> float | None:
    match = SCALE_X_SPEED.search(source)
    if match is None:
        return None
    factor = float(match["num"])
    return factor if match["op"] == "+=" else -factor


def parse_pixel_horizontal(source: str) -> float | None:
    scale_test = XSCALE_TEST.search(source)
    pixel = PIXEL_X.search(source)
    if scale_test is None or pixel is None:
        return None
    if SPEED_EXPR.fullmatch(pixel["num"].strip()) is not None:
        return None
    value = float(pixel["num"])
    facing_forward = (scale_test["cmp"] == ">" and pixel["op"] == "+=") or (
        scale_test["cmp"] == "<" and pixel["op"] == "-="
    )
    return value if facing_forward else -value


def parse_fighter_motion(source: str) -> dict[str, Any] | None:
    motion: dict[str, Any] = {}
    scale_x = parse_scale_x_motion(source)
    if scale_x is not None:
        motion["forward_speed_factor"] = scale_x
        motion["round_forward"] = False
    else:
        horizontal = parse_horizontal_motion(source)
        if horizontal is not None:
            motion["forward_speed_factor"] = horizontal[0]
            motion["round_forward"] = horizontal[1]
    if STEER_LEFT.search(source) or STEER_RIGHT.search(source):
        motion["steer_speed_factor"] = 1.0
    move = MOVE_X.search(source)
    if move is not None:
        motion["forward_pixels"] = float(move["value"])
    else:
        pixel_x = parse_pixel_horizontal(source)
        if pixel_x is not None:
            motion["forward_pixels"] = pixel_x
    y_move = PARENT_Y.search(source)
    if y_move is not None:
        parsed = parse_speed_factor(y_move["expr"])
        if parsed is not None:
            factor, rounded = parsed
            motion["vertical_speed_factor"] = (
                factor if y_move["op"] == "+=" else -factor
            )
            motion["round_vertical"] = rounded
        else:
            pixel_y = PIXEL_Y.search(source)
            if pixel_y is not None:
                value = float(pixel_y["num"])
                motion["vertical_pixels"] = (
                    value if pixel_y["op"] == "+=" else -value
                )
            else:
                return None
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
            "vertical_pixels",
            "steer_speed_factor",
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


def _merge_nested_atm_windows(
    hitbox_windows: dict[str, list[dict[str, Any]]],
    ranges: dict[str, dict[str, int]],
    frames_by_number: dict[int, dict[str, Any]],
    script_bundle: dict[str, Any],
    frame_counts: dict[int, int] | None = None,
) -> None:
    """Root PlaceObject names plus nested `_name = "*atm"` DoAction.

    鸣人 上必杀 has no root *atm. DefineSprite_489 is placed as fensheng
    (683–724); frame_11/24 DoAction rename this to sbsatm/sbs2atm.
    Local frame 1 is the PlaceObject root frame.
    """
    seen: set[tuple[str, str, int, int]] = set()
    # A PlaceObject can carry a clip action while referencing a static
    # DefineShape.  Only a DefineSprite has a nested frame timeline whose
    # frame_count is required by parse_clip_timeline; asking the source
    # inventory for a frame count on a shape turns valid legacy fighters into
    # false failures (for example Naruto's character 33).
    scripted_sprite_ids = {
        int(match["sprite"])
        for script in script_bundle["scripts"]
        if (match := NESTED_FRAME_SCRIPT.match(script["path"])) is not None
    }
    for label, span in ranges.items():
        for frame_number in range(span["start_frame"], span["end_frame"] + 1):
            frame = frames_by_number.get(frame_number)
            if frame is None:
                continue
            for placement in frame["display_list"]:
                character_id = int(placement.get("character_id", 0) or 0)
                if not character_id:
                    continue
                placed_name = str(placement.get("name", "") or "")
                placed_frame = int(placement.get("placed_frame", frame_number))
                if character_id not in scripted_sprite_ids:
                    continue
                clip = parse_clip_timeline(script_bundle, character_id, frame_counts)
                for rename in clip.get("rename_frames", []):
                    instance_name = str(rename["instance_name"])
                    if not instance_name.endswith("atm"):
                        continue
                    local = int(rename["frame"])
                    start = placed_frame + local - 1
                    if start < span["start_frame"] or start > span["end_frame"]:
                        continue
                    end = _nested_rename_end(
                        frames_by_number,
                        span,
                        character_id,
                        placed_name,
                        placed_frame,
                        start,
                        clip,
                        local,
                    )
                    key = (label, instance_name, start, end)
                    if key in seen:
                        continue
                    seen.add(key)
                    hitbox_windows.setdefault(label, []).append(
                        {
                            "instance_name": instance_name,
                            "start_frame": start,
                            "end_frame": end,
                            "placed_name": placed_name,
                            "character_id": character_id,
                            "source_path": rename["source_path"],
                            "source_sha256": rename["source_sha256"],
                        }
                    )
        if label in hitbox_windows:
            hitbox_windows[label].sort(
                key=lambda item: (item["start_frame"], item["instance_name"])
            )


def _merge_root_atm_windows(
    hitbox_windows: dict[str, list[dict[str, Any]]],
    ranges: dict[str, dict[str, int]],
    frames_by_number: dict[int, dict[str, Any]],
    scripts: list[dict[str, Any]],
) -> None:
    """Compile root DoAction instance renames into sourced hitbox windows.

    A root timeline can place a clip under a visual name and later rename the
    same display-list instance to ``*atm``.  The window begins at the frame
    containing the assignment and ends immediately before that depth is
    removed, replaced, or reused.  Matching the authored ``placed_frame`` and
    character id keeps a later replacement from inheriting the old attack
    identity.
    """
    events: list[dict[str, Any]] = []
    for script in scripts:
        if script["kind"] != "frame_action":
            continue
        depth = 0
        lines = script["source"].replace("\r\n", "\n").splitlines()
        for line_number, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            match = ROOT_CLIP_RENAME_ASSIGN.fullmatch(line)
            candidate = ROOT_CLIP_RENAME.search(line)
            if match is not None:
                if depth != 0 and match["name"].endswith("atm"):
                    raise ValueError(
                        f"Unsupported controlled root rename: {script['path']}:{line_number}"
                    )
                events.append(
                    {
                        "action": script["action"],
                        "frame": int(script["frame"]),
                        "object": match["object"],
                        "name": match["name"],
                        "script": script,
                    }
                )
            elif candidate is not None and candidate["name"].endswith("atm"):
                raise ValueError(
                    f"Unsupported root rename statement: {script['path']}:{line_number}"
                )
            depth += line.count("{") - line.count("}")
            if depth < 0:
                raise ValueError(f"Unbalanced root rename source: {script['path']}")
        if depth != 0:
            raise ValueError(f"Unbalanced root rename source: {script['path']}")

    # Resolve assignments against the live source identity.  Once an instance
    # is renamed, a later write through the old variable is undefined; only a
    # write through the new name can change that generation again.
    resolved: list[dict] = []
    active: dict[str, list[dict]] = {}
    for event in sorted(events, key=lambda item: (item["action"], int(item["frame"]), item["script"]["path"])):
        label = event["action"]
        frame_number = int(event["frame"])
        frame = frames_by_number.get(frame_number)
        if frame is None:
            raise ValueError(f"Root rename has no source frame: {event['script']['path']}")
        object_name = str(event["object"])
        static = [
            item for item in frame["display_list"]
            if str(item.get("name", "") or "") == object_name
        ]
        candidates: list[dict] = []
        for record in active.get(label, []):
            if record["current_name"] != object_name:
                continue
            placement = next(
                (
                    item for item in frame["display_list"]
                    if int(item.get("depth", -1)) == record["depth"]
                    and int(item.get("character_id", 0) or 0) == record["character_id"]
                    and int(item.get("placed_frame", frame_number)) == record["placed_frame"]
                ),
                None,
            )
            if placement is not None:
                candidates.append(record)
        if not candidates and static:
            # A static authored name is unavailable when this generation has
            # already been renamed away from it.
            for placement in static:
                same_generation = [
                    record for record in active.get(label, [])
                    if record["depth"] == int(placement["depth"])
                    and record["character_id"] == int(placement.get("character_id", 0) or 0)
                    and record["placed_frame"] == int(placement.get("placed_frame", frame_number))
                ]
                if any(record["current_name"] != object_name for record in same_generation):
                    continue
                candidates.append({
                    "depth": int(placement["depth"]),
                    "character_id": int(placement.get("character_id", 0) or 0),
                    "placed_frame": int(placement.get("placed_frame", frame_number)),
                    "authored_name": object_name,
                    "current_name": object_name,
                })
        if len(candidates) != 1:
            # Source writes through an old name are no-ops; other ambiguous or
            # missing identities fail closed so no guessed hitbox is emitted.
            if not candidates and static:
                continue
            raise ValueError(
                f"Root rename target is not uniquely placed: {event['script']['path']}"
            )
        record = candidates[0]
        record["current_name"] = str(event["name"])
        if record not in active.setdefault(label, []):
            active[label].append(record)
        resolved.append({**event, **record})

    seen: set[tuple[str, str, int, int, int, int]] = set()
    for index, event in enumerate(resolved):
        instance_name = str(event["name"])
        if not instance_name.endswith("atm") or event["object"] == "this":
            continue
        label = event["action"]
        span = ranges[label]
        start = int(event["frame"])
        if start < int(span["start_frame"]) or start > int(span["end_frame"]):
            continue
        script = event["script"]
        depth = int(event["depth"])
        character_id = int(event["character_id"])
        placed_frame = int(event["placed_frame"])
        next_rename = min(
            (
                int(other["frame"])
                for other in resolved[index + 1 :]
                if other["action"] == label
                and other["depth"] == depth
                and other["character_id"] == character_id
                and other["placed_frame"] == placed_frame
                and int(other["frame"]) > start
            ),
            default=int(span["end_frame"]) + 1,
        )
        end = min(int(span["end_frame"]), next_rename - 1)
        for frame_number in range(start, end + 1):
            current = frames_by_number.get(frame_number)
            current_placement = next(
                (
                    item
                    for item in current["display_list"]
                    if int(item.get("depth", -1)) == depth
                ),
                None,
            ) if current is not None else None
            if (
                current_placement is None
                or int(current_placement.get("character_id", 0) or 0) != character_id
                or int(current_placement.get("placed_frame", frame_number)) != placed_frame
            ):
                end = frame_number - 1
                break
        if end < start:
            continue
        key = (label, instance_name, start, end, depth, placed_frame)
        if key in seen:
            continue
        seen.add(key)
        hitbox_windows.setdefault(label, []).append(
            {
                "instance_name": instance_name,
                "start_frame": start,
                "end_frame": end,
                "placed_name": str(event["object"]),
                "character_id": character_id,
                "depth": depth,
                "placed_frame": placed_frame,
                "source_path": script["path"],
                "source_sha256": script["source_sha256"],
            }
        )
    for label in hitbox_windows:
        hitbox_windows[label].sort(
            key=lambda item: (item["start_frame"], item["instance_name"])
        )


def _nested_rename_end(
    frames_by_number: dict[int, dict[str, Any]],
    span: dict[str, int],
    character_id: int,
    placed_name: str,
    placed_frame: int,
    start: int,
    clip: dict[str, Any],
    local_start: int,
) -> int:
    next_local = min(
        (
            int(item["frame"])
            for item in clip.get("rename_frames", [])
            if int(item["frame"]) > local_start
        ),
        default=0,
    )
    stop_after = min(
        (int(frame) for frame in clip.get("stop_frames", []) if int(frame) > local_start),
        default=0,
    )
    last = span["end_frame"]
    if next_local:
        last = min(last, placed_frame + next_local - 2)
    if stop_after:
        last = min(last, placed_frame + stop_after - 2)
    for frame_number in range(start, last + 1):
        frame = frames_by_number.get(frame_number)
        if frame is None:
            return max(start, frame_number - 1)
        present = any(
            int(item.get("character_id", 0) or 0) == character_id
            and str(item.get("name", "") or "") == placed_name
            for item in frame["display_list"]
        )
        if not present:
            return max(start, frame_number - 1)
    return last


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


def parse_exit_impulses(source: str) -> dict[str, int | float]:
    """Assignments on the same frame as an unconditional goto, e.g. yup/htx.

    Source: 鸣人 超必杀2 frame 942 sets yup/htx then gotoAndStop(\"击飞\").
    """
    impulses: dict[str, int | float] = {}
    for match in EXIT_IMPULSE.finditer(source):
        raw = match["value"]
        impulses[match["name"]] = float(raw) if "." in raw else int(raw)
    return impulses


def extract_launch_stop(
    scripts: list[dict[str, Any]], launch_label: str
) -> dict[str, Any]:
    """Unconditional stop() on the launch label. 鸣人 击飞@1035, 一护 击飞@759."""
    if not launch_label:
        return {}
    stops = [
        script
        for script in scripts
        if script["action"] == launch_label
        and script["kind"] == "frame_action"
        and script["source"].strip() == "stop();"
    ]
    if not stops:
        return {}
    stop = min(stops, key=lambda item: int(item["frame"]))
    return {
        "launch_stop_frame": stop["frame"],
        "launch_stop_source_path": stop["path"],
        "launch_stop_source_sha256": stop["source_sha256"],
    }


def _matching_brace(source: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unclosed projectile hit branch")


def _brace_depth(source: str, start: int, end: int) -> int:
    depth = 0
    for char in source[start:end]:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
    return depth


def projectile_local_scope(
    source: str, branch_start: int, statement_start: int
) -> tuple[list[dict[str, Any]], tuple[int, ...]]:
    """Return scalar guards and the exact enclosing source block identities."""
    conditions: list[dict[str, Any]] = []
    block_starts: list[int] = []
    for branch in re.finditer(
        r"if\s*\((?P<condition>[^{}]*)\)\s*\{",
        source[branch_start:statement_start],
    ):
        opening = branch_start + branch.end() - 1
        if _matching_brace(source, opening) < statement_start:
            continue
        condition = PROJECTILE_LOCAL_CONDITION.fullmatch(branch["condition"].strip())
        if condition is None:
            raise ValueError("Uncompiled projectile local guard")
        raw = condition["value"]
        value: Any = (
            raw == "true" if raw in ("true", "false")
            else float(raw) if "." in raw else int(raw)
        )
        conditions.append({
            "field": condition["name"],
            "operator": condition["operator"],
            "value": value,
        })
        block_starts.append(opening)
    return conditions, tuple(block_starts)


def parse_projectile_motion(source: str) -> dict[str, Any] | None:
    if ("_X = _X" not in source and "_Y = _Y" not in source
            and PROJECTILE_PARENT_WRITE.search(source) is None):
        return None
    motion: dict[str, Any] = {}
    x_move = PROJECTILE_X.search(source)
    if x_move is not None:
        motion["local_x_factor"] = 1.0 if x_move["op"] == "+" else -1.0
    y_move = PROJECTILE_Y.search(source)
    if y_move is not None:
        motion["local_y_factor"] = 1.0 if y_move["op"] == "+" else -1.0
    literal_moves = list(PROJECTILE_LITERAL_DELTA.finditer(source))
    axes = [match["axis"] for match in literal_moves]
    if len(axes) != len(set(axes)):
        raise ValueError("Projectile has multiple literal deltas for one axis")
    for match in literal_moves:
        if (match["axis"] == "X" and x_move is not None
                or match["axis"] == "Y" and y_move is not None):
            raise ValueError("Projectile mixes literal and movspeed deltas for one axis")
        delta = float(match["value"])
        if match["op"] == "-":
            delta = -delta
        motion[f"local_{match['axis'].lower()}_delta"] = delta
    queries = re.findall(
        r'(?:(\w+)\.)?hitTest\(_root\.game\["p" \+ _parent\.pn\]\.mc\.(\w+)\)',
        source,
    )
    if len(queries) != source.count('hitTest('):
        raise ValueError("Partially recognized projectile collision query")
    if queries or motion:
        # An explicit empty list preserves movement-only ClipActions. Omitting
        # it would enable the runtime's legacy stop-on-body-contact fallback.
        motion["collision_queries"] = [
            {"receiver": "self" if receiver in (None, "this") else receiver, "target": target}
            for receiver, target in queries
        ]
    hit_branch = PROJECTILE_HIT_IF.search(source)
    parent_writes = list(PROJECTILE_PARENT_WRITE.finditer(source))
    if parent_writes and hit_branch is None:
        raise ValueError("Projectile parent write is not guarded by hitTest")
    hit_end = _matching_brace(source, hit_branch.end() - 1) if hit_branch else -1
    hit_start = hit_branch.end() if hit_branch else -1
    if (x_move is not None or y_move is not None or literal_moves) and hit_branch is not None:
        else_branch = re.match(
            r"\s*else\s+if\s*\((?P<condition>[^{}]*)\)\s*\{",
            source[hit_end + 1:],
        )
        if else_branch is not None:
            condition = PROJECTILE_LOCAL_CONDITION.fullmatch(
                else_branch["condition"].strip()
            )
            if condition is None:
                raise ValueError("Uncompiled projectile movement guard")
            raw = condition["value"]
            value: Any = (
                raw == "true" if raw in ("true", "false")
                else float(raw) if "." in raw else int(raw)
            )
            motion["local_motion_conditions"] = [{
                "field": condition["name"],
                "operator": condition["operator"],
                "value": value,
            }]
    hit_gotos = list(PROJECTILE_HIT_GOTO.finditer(source))
    if any(hit_branch is None or not hit_start <= match.start() < hit_end
           for match in hit_gotos):
        raise ValueError("Projectile child goto occurs outside hitTest branch")
    if len(hit_gotos) > 1:
        raise ValueError("Projectile has multiple child gotos in its hitTest branch")
    if hit_gotos:
        hit_goto = hit_gotos[0]
        motion["on_hit_goto_frame"] = int(hit_goto["frame"])
        conditions, scope = projectile_local_scope(source, hit_start, hit_goto.start())
        if conditions:
            motion["on_hit_goto_conditions"] = conditions
            motion["on_hit_goto_scope"] = list(scope)
    if any(not hit_start <= match.start() < hit_end for match in parent_writes):
        raise ValueError("Projectile parent write occurs outside hitTest branch")
    hit_events: list[tuple[int, dict[str, Any]]] = []
    for match in parent_writes:
        if _brace_depth(source, hit_start, match.start()) != 0:
            raise ValueError("Nested projectile parent write has unsupported condition")
        literal = match["value"]
        value: Any = (literal == "true" if literal in ("true", "false")
                      else float(literal) if "." in literal else int(literal))
        event = {"op": "write", "field": match["field"], "operator": "=", "value": value}
        hit_events.append((match.start(), event))
    opponent_gotos = list(PROJECTILE_OPPONENT_GOTO.finditer(source))
    if any(hit_branch is None or not hit_start <= match.start() < hit_end
           for match in opponent_gotos):
        raise ValueError("Projectile opponent goto occurs outside hitTest branch")
    for opponent_goto in opponent_gotos:
        goto = {
            "target": "opponent",
            "action": int(opponent_goto["action"]),
            "label": opponent_goto["label"],
            "play": opponent_goto["mode"] == "Play",
        }
        hit_events.append((opponent_goto.start(), {"op": "goto", **goto}))
    local_writes = list(PROJECTILE_LOCAL_WRITE.finditer(source))
    for write in local_writes:
        if write["name"] not in {"played", "movspeed"}:
            continue
        if hit_branch is None or not hit_start <= write.start() < hit_end:
            continue
        if _brace_depth(source, hit_start, write.start()) == 0:
            raise ValueError("Projectile local hit write has no one-shot guard")
        literal = write["value"]
        value: Any = (literal == "true" if literal in ("true", "false")
                      else float(literal) if "." in literal else int(literal))
        # Preserve scalar one-shot guards around writes. Collision and pause
        # guards are represented by the callback/collision scheduler itself.
        conditions, scope = projectile_local_scope(source, hit_start, write.start())
        if not conditions:
            raise ValueError("Projectile local hit write lacks a scalar source guard")
        event = {
            "field": write["name"], "value": value,
            "conditions": conditions, "source_scope": list(scope),
            "source_position": write.start(),
        }
        hit_events.append((write.start(), {"op": "local_write", **event}))
    if hit_events:
        hit_events.sort(key=lambda item: item[0])
        events: list[dict[str, Any]] = []
        for position, event in hit_events:
            if event["op"] == "local_write":
                if (events and events[-1]["op"] == "local_write_group"
                        and events[-1]["source_scope"] == event["source_scope"]):
                    events[-1]["writes"].append({"field": event["field"], "value": event["value"]})
                    events[-1]["source_position"] = position
                else:
                    events.append({
                        "op": "local_write_group",
                        "conditions": event["conditions"],
                        "source_scope": event["source_scope"],
                        "writes": [{"field": event["field"], "value": event["value"]}],
                        "source_position": position,
                    })
            else:
                events.append(event)
        goto_scope = motion.get("on_hit_goto_scope")
        if goto_scope is not None:
            prior_groups = [
                event for event in events
                if event["op"] == "local_write_group"
                and event["source_scope"] == goto_scope
                and event["source_position"] < hit_gotos[0].start()
            ]
            matching_group = next((
                event for event in reversed(prior_groups)
                if any(write["field"] == "played" for write in event["writes"])
            ), None)
            if prior_groups and matching_group is None:
                raise ValueError(
                    "Projectile local-write/goto guard lacks the supported played pattern"
                )
            if matching_group is not None:
                matching_group["goto_frame"] = motion["on_hit_goto_frame"]
                motion["on_hit_goto_grouped"] = True
                motion.pop("on_hit_goto_conditions", None)
                motion.pop("on_hit_goto_scope", None)
        for event in events:
            event.pop("source_position", None)
        motion["on_hit_events"] = events
    return motion or None


def parse_projectile_initialization(source: str) -> dict[str, Any] | None:
    """Compile every scalar local assigned by a child clip's load callback.

    AS2 does not require locals to be declared with ``var``.  In particular,
    projectile clips commonly initialize ``played`` and ``movspeed`` as plain
    assignments.  Dropping those assignments makes a later source guard read
    an undeclared local, so parse the callback statements themselves and keep
    the source distinction between a literal and the parent's speed field.
    """
    normalized = source.replace("\r\n", "\n")
    callback = re.fullmatch(
        r"onClipEvent\(load\)\{(?P<body>[\s\S]*?)\}\s*", normalized
    )
    if callback is None:
        return None
    body = callback["body"]
    result: dict[str, Any] = {}
    statements = [part.strip() for part in body.split(";") if part.strip()]
    for statement in statements:
        literal = re.fullmatch(
            r"(?:var\s+)?(?P<name>[A-Za-z_]\w*)\s*=\s*"
            r"(?P<value>true|false|-?\d+(?:\.\d+)?)", statement
        )
        if literal is not None:
            name = literal["name"]
            result.setdefault("initial_variables", {})
            if name in result["initial_variables"]:
                raise ValueError("Duplicate projectile local declaration: " + name)
            raw = literal["value"]
            result["initial_variables"][name] = (
                raw == "true" if raw in ("true", "false")
                else float(raw) if "." in raw else int(raw)
            )
            continue
        speed = re.fullmatch(
            r"movspeed\s*=\s*_parent\.speed"
            r"(?:\s*\*\s*(?P<factor>\d+(?:\.\d+)?))?", statement
        )
        if speed is not None:
            if "initial_speed_field" in result:
                raise ValueError("Duplicate projectile speed initialization: " + source)
            result["initial_speed_field"] = "speed"
            result["initial_speed_factor"] = float(speed["factor"] or 1)
            continue
        raise ValueError("Uncompiled projectile load statement: " + statement)
    return result


def enrich_cancel_lifetimes(
    catalog: dict[str, Any],
    frames_by_number: dict[int, dict[str, Any]],
    scripts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Clip enterFrame lasts until that PlaceObject is removed or replaced."""
    by_path = {item["path"]: item for item in scripts}
    for window in catalog.get("cancel_windows", []):
        if window.get("kind") != "input" or window.get("end_frame"):
            continue
        script = by_path.get(window.get("source_path", ""))
        if script is None:
            continue
        match = SCRIPT_PATH.match(script["path"])
        if match is None:
            continue
        path_tail = match["kind"]
        placement_match = PLACEMENT_PATH.match(path_tail)
        if placement_match is None:
            continue
        end_frame, _hash = clip_lifetime(
            frames_by_number, script["frame"], int(placement_match["depth"])
        )
        window["end_frame"] = end_frame
    return catalog


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


def compile_summon_function(source: str) -> dict[str, Any]:
    match = re.fullmatch(
        r"function doZhaoHuan\(\)\s*\{\s*"
        r"if\((?P<guard>\w+)\)\s*\{\s*return undefined;\s*\}\s*"
        r"_root\.yfgj\(_parent\._name\);\s*"
        r"bs\s*=\s*(?P<bs>\d+);\s*ql\s*-=\s*(?P<cost>\d+);\s*\}",
        source,
    )
    if match is None:
        raise ValueError("Unsupported doZhaoHuan body; retain its guards and statement order")
    return {"skip_if_truthy": match["guard"], "set_bs": int(match["bs"]),
            "energy_delta": -int(match["cost"])}


def compile_yfgj_function(main_bundle: dict[str, Any]) -> dict[str, str]:
    script = next(
        (item for item in main_bundle["scripts"] if "function yfgj(" in item["source"]),
        None,
    )
    if script is None:
        raise ValueError("The source yfgj function is missing")
    source = extract_function(script["source"], "yfgj")
    required = (
        r"_loc3_\._x\s*=\s*_loc2_\._x\s*-\s*20\s*\*\s*"
        r"\(_loc2_\._xscale\s*<=\s*0\s*\?\s*-1\s*:\s*1\)\s*;",
        r"_loc3_\._y\s*=\s*_loc2_\._y\s*;",
        r"_loc3_\._xscale\s*=\s*_loc5_\s*\*\s*100\s*;",
        r"_root\.game\[nam\s*\+\s*\"fz\"\]\.gotoAndPlay\(2\)\s*;",
        r"_loc3_\.attacking\s*=\s*true\s*;",
    )
    if any(re.search(pattern, source) is None for pattern in required):
        raise ValueError("Unsupported yfgj placement or lifecycle source")
    return {"source_path": script["path"], "source_sha256": text_sha256(source)}


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
    script_bundle: dict[str, Any], character_id: int,
    frame_counts: dict[int, int] | None = None,
) -> dict[str, Any]:
    if frame_counts is not None and character_id not in frame_counts:
        raise ValueError(f"Missing source frame_count for character {character_id}")
    stop_frames: list[dict[str, Any]] = []
    rename_frames: list[dict[str, Any]] = []
    initial_motion: dict[str, Any] = {}
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
        motion_init = re.fullmatch(
            r"stop\(\);\s*var movspeed = (-?\d+(?:\.\d+)?);\s*var played = 0;", source
        )
        if source == "stop();" or motion_init is not None:
            stop_frames.append(record)
        if motion_init is not None:
            if frame != 1:
                raise ValueError("Projectile initialization outside frame 1: " + script["path"])
            initial_motion = {"initial_speed": float(motion_init[1]), "initial_played": 0,
                              "initial_motion_source": record}
        rename = CLIP_RENAME.search(script["source"])
        if rename is not None:
            rename_frames.append({**record, "instance_name": rename["name"]})
    stop_frames.sort(key=lambda item: item["frame"])
    rename_frames.sort(key=lambda item: item["frame"])
    timeline: dict[str, Any] = {"character_id": character_id, **initial_motion}
    if frame_counts is not None and character_id in frame_counts:
        timeline["frame_count"] = int(frame_counts[character_id])
    if stop_frames:
        timeline["stop_frames"] = [item["frame"] for item in stop_frames]
        timeline["stop_sources"] = stop_frames
    if rename_frames:
        timeline["rename_frames"] = rename_frames
    return timeline


def source_frame_counts(timeline: dict[str, Any]) -> dict[int, int]:
    """Return source sprite frame counts and reject incomplete geometry metadata."""
    counts: dict[int, int] = {}
    for definition in timeline.get("definitions", []):
        if "character_id" not in definition:
            continue
        character_id = int(definition["character_id"])
        if "frame_count" not in definition:
            continue
        count = int(definition["frame_count"])
        if count < 1:
            raise ValueError(
                f"Invalid source frame_count for character {character_id}: {count}"
            )
        counts[character_id] = count
    return counts


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
    ko_prefix = re.search(r"bdzl = (-?\d+);\s*sw = (true|false);\s*_root\.KOplay\(pn\);", body_match["body"])
    pn_assignment = re.search(r'pn = _parent\._name != "(\w+)" \? (\d+) : (\d+);', check_script["source"])
    if ko_prefix is None or pn_assignment is None:
        raise ValueError("Unsupported checkDead KO state/receiver binding")
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
        "ko_writes": [{"field": "bdzl", "value": int(ko_prefix[1])}, {"field": "sw", "value": ko_prefix[2] == "true"}],
        "ko_number_binding": {"name": pn_assignment[1], "equal": int(pn_assignment[3]), "different": int(pn_assignment[2])},
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


def resolve_special_cost(
    fighter: dict[str, Any],
    timeline: dict[str, Any],
    script_bundle: dict[str, Any],
    scripts: list[dict[str, Any]],
    sprite_id: int,
    first_special: str,
) -> tuple[dict[str, Any], re.Match[str]]:
    matches = [
        (script, match)
        for script in scripts
        if script["action"] == first_special
        for match in ENERGY_COST.finditer(script["source"])
    ]
    if not matches:
        span = fighter["actions"]["special"][first_special]
        boundary_frame = int(span["end_frame"]) + 1
        allowed = int(span["start_frame"]) == int(span["end_frame"])
        allowed = allowed and not any(
            re.search(r"\b(?:gotoAnd(?:Stop|Play)|stop)\s*\(", script["source"])
            for script in scripts if script["action"] == first_special
        )
        direct_path = f"DefineSprite_{sprite_id}/frame_{boundary_frame}/DoAction.as"
        if allowed:
            for raw in script_bundle["scripts"]:
                path_match = SCRIPT_PATH.match(raw["path"])
                if path_match is None or int(path_match["sprite"]) != sprite_id:
                    continue
                if int(path_match["frame"]) != boundary_frame or raw["path"] != direct_path:
                    continue
                for match in ENERGY_COST.finditer(raw["source"]):
                    matches.append((
                        {"action": first_special, "frame": boundary_frame,
                         "kind": "fallthrough_frame_action", "path": raw["path"],
                         "source_sha256": text_sha256(raw["source"]), "source": raw["source"]},
                        match,
                    ))
    if len(matches) != 1:
        raise ValueError(f"Expected one energy cost for {first_special}, got {len(matches)}")
    return matches[0]


def build_model(
    fighter_path: Path, timeline_path: Path, scripts_path: Path
) -> dict[str, Any]:
    fighter = json.loads(fighter_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    script_bundle = json.loads(scripts_path.read_text(encoding="utf-8"))
    main_bundle = json.loads(
        (scripts_path.resolve().parent.parent / "main.json").read_text(encoding="utf-8")
    )
    shared_hit_receive = compile_shared_hit_receive(
        main_bundle,
        swf_path=scripts_path.resolve().parent.parent.parent / "game/main.swf",
    )
    sprite_id = int(fighter["source"]["timeline_symbol_id"])
    ranges = target_ranges(fighter)
    frames_by_number = {int(frame["frame"]): frame for frame in timeline["frames"]}
    frame_counts = source_frame_counts(timeline)

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
    _merge_nested_atm_windows(
        hitbox_windows, ranges, frames_by_number, script_bundle, frame_counts
    )
    _merge_root_atm_windows(hitbox_windows, ranges, frames_by_number, scripts)

    combo_labels = list(fighter["actions"]["ground_combo"])
    combo_transitions = []
    for index, label in enumerate(combo_labels[:-1]):
        next_label = combo_labels[index + 1]
        candidates = [
            script
            for script in scripts
            if script["action"] == label
            and script["kind"] == "clip_action"
            and re.search(r"\bnornalhit\((?:true)?\)", script["source"])
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
    exits = {}
    for script in scripts:
        if script["kind"] != "frame_action":
            continue
        target = parse_unconditional_exit(script["source"])
        if target is None:
            continue
        if (script["action"], target) in UNWIRED_EXIT_PAIRS:
            continue
        # Self-goto pins a clip until land/contact cancel. 鸣人 螺旋手里剑1@902
        # loops until touchFloor → 超必杀2. Skipping these used to _finish_action
        # into 落 and drop cbsatm. Locomotion self-pins stay in UNWIRED_EXIT_PAIRS.
        current = exits.get(script["action"])
        if current is not None and current["frame"] <= script["frame"]:
            continue
        record = {
            "frame": script["frame"],
            "target": target,
            "source_path": script["path"],
            "source_sha256": script["source_sha256"],
        }
        record.update(parse_exit_impulses(script["source"]))
        exits[script["action"]] = record

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
    hurt_callbacks = [script for script in scripts
                      if script["action"] == hurt_label and script["kind"] == "clip_action"
                      and re.fullmatch(r"onClipEvent\(enterFrame\)\{\s*_parent\.beidax\(\);\s*\}", script["source"].strip())]
    if len(hurt_callbacks) != 1:
        raise ValueError(f"Expected one hurt timer callback, got {len(hurt_callbacks)}")

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
    cost_script, cost_match = resolve_special_cost(
        fighter, timeline, script_bundle, scripts, sprite_id, first_special
    )

    energy_events = []
    health_events = []
    presentation_events = []
    lose_hp_source = next(
        (item for item in script_bundle["scripts"]
         if extract_function(item["source"], "loseHp")
         and SOURCE_LOSE_HP.fullmatch(extract_function(item["source"], "loseHp") or "")),
        None,
    )
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
            source_line = script["source"][:match.start()].count("\n") + 1
            presentation_events.append(
                {
                    "action": script["action"],
                    "frame": script["frame"],
                    "op": "screen_flash",
                    "color_rgb24": color,
                    "source_path": script["path"],
                    "source_line": source_line,
                    "source_sha256": script["source_sha256"],
                }
            )
        health_match = SOURCE_HEALTH_LOSS.fullmatch(script["source"].strip())
        if health_match is not None:
            if lose_hp_source is None:
                raise ValueError("Health event has no source loseHp guard: " + script["path"])
            health_events.append(
                {
                    "action": script["action"],
                    "frame": script["frame"],
                    "threshold": float(health_match["threshold"]),
                    "above_damage": float(health_match["above"]),
                    "below_ratio": float(health_match["ratio"]),
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                    "lose_hp_source_path": lose_hp_source["path"],
                    "lose_hp_source_sha256": text_sha256(lose_hp_source["source"]),
                }
            )

    clip_placements = []
    body_warps = []
    for script in scripts:
        if script["kind"] != "frame_action":
            continue
        warp = parse_body_warp(script["source"])
        if warp is not None:
            body_warps.append(
                {
                    "action": script["action"],
                    "frame": script["frame"],
                    **warp,
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                }
            )
            continue
        placement = parse_place_at_opponent(script["source"])
        if placement is None:
            continue
        clip_placements.append(
            {
                "action": script["action"],
                "frame": script["frame"],
                **placement,
                "source_path": script["path"],
                "source_sha256": script["source_sha256"],
            }
        )

    helper = helper_from_catalog(fighter["fighter_id"])
    catalog = json.loads((REPO_ROOT / "manifest.json").read_text())["fighter_catalog"]
    is_naruto = bool(catalog[fighter["fighter_id"]].get("isNaruto", False))
    summon_events = []
    yfgj_source: dict[str, str] | None = None
    summon_script = next((s for s in scripts if "function doZhaoHuan" in s["source"]), None)
    summon_function = (compile_summon_function(extract_function(summon_script["source"], "doZhaoHuan"))
                       if summon_script else None)
    for script in scripts:
        if script["kind"] != "frame_action":
            continue
        if "function doZhaoHuan" in script["source"]:
            continue
        if "doZhaoHuan()" not in script["source"]:
            direct_call = DIRECT_YFGJ_CALL.search(script["source"])
            if direct_call is None:
                continue
            if DIRECT_YFGJ_CALL.search(script["source"], direct_call.end()):
                raise ValueError("Multiple direct yfgj calls in one frame are unsupported: " + script["path"])
            if _brace_depth(script["source"], 0, direct_call.start()) != 0:
                raise ValueError("Conditional direct yfgj call is unsupported: " + script["path"])
            if not helper.get("helper_id"):
                raise ValueError("Direct yfgj call has no source-mapped helper: " + script["path"])
            if yfgj_source is None:
                yfgj_source = compile_yfgj_function(main_bundle)
            summon_events.append({
                "action": script["action"],
                "frame": script["frame"],
                "call_kind": "direct_yfgj",
                **helper,
                "function_source_path": yfgj_source["source_path"],
                "function_source_sha256": yfgj_source["source_sha256"],
                "source_path": script["path"],
                "source_sha256": script["source_sha256"],
            })
            continue
        if summon_function is None:
            raise ValueError("doZhaoHuan is missing its source function")
        summon_events.append(
            {
                "action": script["action"],
                "frame": script["frame"],
                "call_kind": "doZhaoHuan",
                **summon_function,
                "function_source_path": summon_script["path"],
                "function_source_sha256": summon_script["source_sha256"],
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
    scripted_sprite_ids = {
        int(match["sprite"])
        for script in script_bundle["scripts"]
        if (match := NESTED_FRAME_SCRIPT.match(script["path"])) is not None
    }
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
                parse_clip_timeline(script_bundle, character_id, frame_counts)
                if character_id is not None and character_id in scripted_sprite_ids
                else {}
            )
            load_path = script["path"].replace(
                "onClipEvent(enterFrame)", "onClipEvent(load)"
            )
            load_script = next(
                (item for item in script_bundle["scripts"] if item["path"] == load_path),
                None,
            )
            initialization = (
                parse_projectile_initialization(load_script["source"])
                if load_script is not None
                else None
            )
            if load_script is not None and initialization is None:
                raise ValueError("Uncompiled projectile initialization: " + load_path)
            initialization_source = (
                {
                    "source_path": load_path,
                    "source_sha256": text_sha256(load_script["source"]),
                }
                if load_script is not None
                else None
            )
            if initialization and "initial_variables" in initialization:
                if (any(key in projectile for key in ("local_x_factor", "local_y_factor"))
                        and "movspeed" not in initialization["initial_variables"]
                        and initialization.get("initial_speed_field") != "speed"):
                    raise ValueError("Projectile movement local is undeclared: " + load_path)
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
                    **(initialization or {}),
                    **(
                        {"initial_motion_source": initialization_source}
                        if initialization_source is not None
                        else {}
                    ),
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

    death = extract_death(script_bundle, sprite_id, scripts, ranges)
    launch_stop = extract_launch_stop(
        scripts, (death or {}).get("launch_label", "击飞")
    )

    return {
        "format": "bvn26-combat-model-v1",
        "status": "reverse_engineering_intermediate",
        "fighter_id": fighter["fighter_id"],
        "is_naruto": is_naruto,
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
            "callback_start_frame": hurt_callbacks[0]["frame"] + 1,
            "callback_source_path": hurt_callbacks[0]["path"],
            "callback_source_sha256": hurt_callbacks[0]["source_sha256"],
            "hitstun_ticks_formula": "hitstun_ms / 1000 * 30",
            "source_path": stop_scripts[0]["path"],
            "source_sha256": stop_scripts[0]["source_sha256"],
            **launch_stop,
        },
        "death": death,
        "attacks": fighter["hit_parameters"]["attacks"],
        **compile_fighter_hit_receive(
            script_bundle,
            scripts,
            next(
                item["source"]
                for item in script_bundle["scripts"]
                if item["path"] == "frame_1/DoAction.as"
            ),
            sprite_id,
        ),
        "hit_fx": shared_hit_receive["hit_fx"],
        "combo_hud": shared_hit_receive["combo_hud"],
        "super_presentation": shared_hit_receive["super_presentation"],
        "hit_priority": extract_hit_priority(script_bundle),
        "energy_events": sorted(
            energy_events, key=lambda item: (item["frame"], item["action"])
        ),
        "health_events": sorted(
            health_events, key=lambda item: (item["frame"], item["action"])
        ),
        "presentation_events": sorted(
            presentation_events, key=lambda item: (item["frame"], item["action"])
        ),
        "clip_placements": sorted(
            clip_placements,
            key=lambda item: (item["frame"], item["instance_name"]),
        ),
        "body_warps": sorted(
            body_warps,
            key=lambda item: (item["frame"], item["action"]),
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
        "command_catalog": enrich_cancel_lifetimes(
            build_command_catalog(
                fighter, script_bundle, scripts, motion_windows
            ),
            frames_by_number,
            scripts,
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
