"""Parse source projectile motion, collision branches and load-local assignments."""

from __future__ import annotations

import re
from typing import Any
PROJECTILE_X = re.compile(r"_X\s*=\s*_X\s*(?P<op>\+|-)\s*movspeed(?:\s*(?P<scale_op>[*/])\s*(?P<scale>\d+(?:\.\d+)?))?\s*;")
PROJECTILE_Y = re.compile(r"_Y\s*=\s*_Y\s*(?P<op>\+|-)\s*movspeed(?:\s*(?P<scale_op>[*/])\s*(?P<scale>\d+(?:\.\d+)?))?\s*;")
PROJECTILE_LITERAL_DELTA = re.compile(
    r"_(?P<axis>X|Y)\s*=\s*_(?P=axis)\s*(?P<op>\+|-)\s*"
    r"(?P<value>\d+(?:\.\d+)?)"
)
PROJECTILE_HIT_GOTO = re.compile(r"gotoAndPlay\((?P<frame>\d+)\)")
PROJECTILE_LOCAL_WRITE = re.compile(
    r"(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<value>true|false|-?\d+(?:\.\d+)?)\s*;"
)
PROJECTILE_LOCAL_CONDITION = re.compile(
    r"(?P<name>[A-Za-z_]\w*)\s*(?P<operator>==|!=)\s*"
    r"(?P<value>true|false|-?\d+(?:\.\d+)?)"
)
PROJECTILE_PARENT_WRITE = re.compile(
    r"(?<![\w.])_parent\.(?P<field>[A-Za-z_]\w*)\s*=\s*"
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


def parse_projectile_motion(
    source: str, frame_labels: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    if ("_X = _X" not in source and "_Y = _Y" not in source
            and PROJECTILE_PARENT_WRITE.search(source) is None):
        return None
    # Resolve the authored stop/play pair before parsing its guarded goto.
    def resolve_label(match: re.Match[str]) -> str:
        label = match["label"]
        if frame_labels is None or label not in frame_labels:
            raise ValueError("Missing projectile target label: " + label)
        return f"gotoAndPlay({frame_labels[label]})"
    source = re.sub(
        r'gotoAndStop\("(?P<label>[^"\n]+)"\);\s*play\(\)',
        resolve_label, source,
    )
    motion: dict[str, Any] = {}
    x_move = PROJECTILE_X.search(source)
    y_move = PROJECTILE_Y.search(source)
    for axis, move in (("x", x_move), ("y", y_move)):
        if move is None:
            if re.search(rf"_{axis.upper()}\s*=\s*_{axis.upper()}[^;]*movspeed", source):
                raise ValueError("Unsupported projectile movspeed expression")
            continue
        factor = 1.0 if move["op"] == "+" else -1.0
        if move["scale"]:
            scale = float(move["scale"])
            if move["scale_op"] == "/" and scale == 0:
                raise ValueError("Projectile movement divides by zero")
            factor = factor * scale if move["scale_op"] == "*" else factor / scale
        motion[f"local_{axis}_factor"] = factor
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
            {"receiver": "self" if receiver in ("", "this") else receiver, "target": target}
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
    if hit_branch is not None:
        sequential = re.match(
            r"\s*if\s*\((?P<condition>[^{}]*)\)\s*\{", source[hit_end + 1:]
        )
        if sequential is not None:
            condition = PROJECTILE_LOCAL_CONDITION.fullmatch(sequential["condition"].strip())
            if condition is None:
                raise ValueError("Uncompiled sequential projectile movement guard")
            raw = condition["value"]
            value = raw == "true" if raw in ("true", "false") else float(raw)
            motion["motion_after_collision"] = True
            motion["local_motion_conditions"] = [{
                "field": condition["name"], "operator": condition["operator"], "value": value,
            }]
    if hit_branch is None:
        moves = [m for m in (x_move, y_move, *literal_moves) if m is not None]
        guards = []
        for move in moves:
            conditions = []
            for branch in re.finditer(r"if\s*\((?P<condition>[^{}]*)\)\s*\{", source[:move.start()]):
                if _matching_brace(source, branch.end() - 1) < move.start():
                    continue
                if branch["condition"].strip() == "_root.zhanting == false":
                    continue
                condition = PROJECTILE_LOCAL_CONDITION.fullmatch(branch["condition"].strip())
                if condition is None:
                    raise ValueError("Uncompiled movement-only projectile guard")
                raw = condition["value"]
                conditions.append({"field": condition["name"], "operator": condition["operator"],
                                   "value": raw == "true" if raw in ("true", "false") else float(raw)})
            guards.append(conditions)
        if guards and any(g != guards[0] for g in guards):
            raise ValueError("Projectile axes have different motion guards")
        if guards and guards[0]:
            motion["local_motion_conditions"] = guards[0]
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
