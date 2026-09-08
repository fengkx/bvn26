"""Compile a source-label command catalog.

Original BVN fighters share input predicates (`nornalhit`, `bisha`, …) and
dispatch with `gotoAndPlay("砍1")` frame labels. The catalog keeps those
labels as the public move IDs so later characters only supply their own
timeline + control script. Entries that are not yet wired stay listed so
implementation cannot silently drop a sourced move.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


PREDICATE_NAMES = (
    "nornalhit",
    "skill1",
    "skill2",
    "magichit1",
    "magichit2",
    "magichit3",
    "bisha",
    "bishaUP",
    "bishaSuper",
    "bishaAir",
    "airhit",
    "airMagichit",
    "zhaoHuan",
    "wankai",
    "rush",
    "hide",
    "jump",
    "jumpDown",
    "defence",
    "standup",
    "moveLeft",
    "moveRight",
)

DISPATCH_FUNCS = {
    "doAllAction": "stand",
    "doStand": "stand",
    "onJumping": "air",
    "onDefence": "guard",
    "onDashing": "dash",
    "doDropDown": "drop",
}

KEY_TO_BUTTON = {
    "斩": "attack",
    "招": "ranged",
    "必杀": "special",
    "跳": "jump",
    "冲": "dash",
    "换": "summon",
    "上": "up",
    "下": "down",
    "左": "left",
    "右": "right",
}

# Source doAllAction / onDefence / onJumping are sequential if+goto.
# dispatch_order is the 0-based index in that function.
# Stand/air/dash consume the first leaving goto: the 站立 helper is removed.
# Guard later-wins: onDefence pins 防御2 (same clip) then keeps going.

DEFAULT_ENERGY = {
    "bisha": 100,
    "bishaUP": 100,
    "bishaAir": 100,
    "bishaSuper": 300,
    "zhaoHuan": 100,
    "wankai": 300,
}

HANDLERS = {
    "跳": "start_jump",
    "瞬步": "start_dash",
}

# Labels the current Godot slice already starts from input or internal flow.
# Everything else with a timeline is catalog_only so it cannot be forgotten.
WIRED_LABELS = {
    "站立",
    "走",
    "瞬步",
    "跳",
    "跳2",
    "落",
    "落2",
    "落地",
    "砍1",
    "砍2",
    "砍3",
    "砍技1",
    "砍技2",
    "砍技12",
    "招1",
    "招2",
    "招3",
    "必杀",
    "必杀1",
    "必杀0",
    "上必杀",
    "超必杀",
    "超必杀2",
    "招换",
    "万解",
    "跳砍",
    "跳招",
    "跳招3",
    "砍4",
    "防御",
    "防御2",
    "防住",
    "被打",
    "击飞",
    "击落地",
    "起身",
}

# Already consumed by dedicated runtime paths. Generic cancel dispatch
# must not also fire these or it double-jumps / breaks guard pin.
HANDLED_ELSEWHERE_CANCELS = {
    ("防御2", "砍技1"),
    ("防御2", "招2"),
    ("防御2", "超必杀"),
    ("防御2", "防御2"),
    ("防住", "防御2"),
}

KIS_RE = re.compile(
    r"(?P<neg>!)?_parent\.kis\(_parent\.(?P<key>斩|招|必杀|跳|冲|换|上|下|左|右)\)"
)
QL_RE = re.compile(r"_parent\.ql\s*>=\s*(?P<n>\d+)")
QI_DEFAULT_RE = re.compile(r"qi\s*=\s*(?P<n>\d+)")
IF_GOTO_RE = re.compile(
    r"if\s*\(\s*(?P<pred>"
    + "|".join(PREDICATE_NAMES)
    + r")\s*\((?P<args>[^)]*)\)\s*\)\s*\{"
    r"(?:(?!if\s*\()[\s\S]){0,240}?_parent\.gotoAndPlay\(\"(?P<label>[^\"]+)\"\)",
)
FUNCTION_RE = re.compile(r"function (?P<name>[A-Za-z_][A-Za-z0-9_]*)\(")


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def extract_function(source: str, name: str) -> str | None:
    marker = f"function {name}("
    start = source.find(marker)
    if start < 0:
        return None
    next_fn = FUNCTION_RE.search(source, start + len(marker))
    end = next_fn.start() if next_fn is not None else len(source)
    return source[start:end]


def player_return(body: str) -> str:
    marker = "if(!_parent._parent.useAI)"
    index = body.find(marker)
    if index < 0:
        return ""
    chunk = body[index : index + 400]
    ret = re.search(r"return\s+([^;]+);", chunk)
    return ret.group(1) if ret else ""


def parse_predicate(source: str, name: str) -> dict[str, Any]:
    body = extract_function(source, name)
    buttons_all: list[str] = []
    buttons_none: list[str] = []
    energy_min = DEFAULT_ENERGY.get(name, 0)
    expr = ""
    if body:
        expr = player_return(body)
        qi = QI_DEFAULT_RE.search(body)
        if qi is not None:
            energy_min = int(qi["n"])
        ql = QL_RE.search(expr) or QL_RE.search(body)
        if ql is not None:
            energy_min = int(ql["n"])
        for match in KIS_RE.finditer(expr):
            button = KEY_TO_BUTTON[match["key"]]
            if match["neg"]:
                if button not in buttons_none:
                    buttons_none.append(button)
            elif button not in buttons_all:
                buttons_all.append(button)
    return {
        "name": name,
        "buttons_all": buttons_all,
        "buttons_none": buttons_none,
        "energy_min": energy_min,
        "player_expr": expr,
    }


def find_control_script(
    script_bundle: dict[str, Any], fighter: dict[str, Any]
) -> dict[str, Any] | None:
    for item in fighter.get("shared_control_scripts", []):
        if "function doAllAction" in item.get("source", ""):
            return item
    for script in script_bundle.get("scripts", []):
        if "function doAllAction" in script.get("source", ""):
            return script
    return None


def implementation_for(label: str, has_timeline: bool) -> str:
    if not has_timeline:
        return "missing_timeline"
    if label in WIRED_LABELS:
        return "wired"
    return "catalog_only"


def infer_contexts(label: str, group: str, mapped: set[str]) -> list[str]:
    if mapped:
        return sorted(mapped)
    if label in ("跳砍", "跳招", "跳招2", "跳招3", "空中必杀"):
        return ["air"]
    if label in ("防御", "防御2", "防住"):
        return ["guard"]
    if group == "hurt" or label in ("击飞", "击落地", "起身"):
        return ["hurt"]
    if label in ("开场", "胜利", "失败"):
        return ["cinematic"]
    if group == "movement":
        return ["locomotion"]
    if group == "special":
        return ["special"]
    return ["timeline"]


def build_command_catalog(
    fighter: dict[str, Any],
    script_bundle: dict[str, Any],
    timeline_scripts: list[dict[str, Any]],
    motion_windows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    control = find_control_script(script_bundle, fighter)
    if control is None:
        raise ValueError(f"No doAllAction control script for {fighter.get('fighter_id')}")
    source = control["source"]
    control_path = control["path"]

    predicates = {name: parse_predicate(source, name) for name in PREDICATE_NAMES}

    labels: dict[str, dict[str, Any]] = {}
    for group_name, actions in fighter["actions"].items():
        for label, span in actions.items():
            labels[label] = {
                "label": label,
                "group": group_name,
                "start_frame": span["start_frame"],
                "end_frame": span["end_frame"],
                "has_timeline": True,
                "slot": None,
                "contexts": [],
                "handler": HANDLERS.get(label, "start_action"),
                "dispatch_priority": None,
                "dispatch_order": None,
                "dispatch_orders": {},
                "energy_min": 0,
                "source_dispatch": [],
            }

    slot_targets: dict[tuple[str, str], str] = {}
    for func_name, context in DISPATCH_FUNCS.items():
        body = extract_function(source, func_name)
        if not body:
            continue
        for order, match in enumerate(IF_GOTO_RE.finditer(body)):
            pred = match["pred"]
            label = match["label"]
            slot_targets[(context, pred)] = label
            entry = labels.get(label)
            if entry is None:
                entry = {
                    "label": label,
                    "group": "shared_control",
                    "start_frame": None,
                    "end_frame": None,
                    "has_timeline": False,
                    "slot": pred,
                    "contexts": [context],
                    "handler": HANDLERS.get(label, "start_action"),
                    "dispatch_priority": None,
                    "dispatch_order": order,
                    "dispatch_orders": {context: order},
                    "energy_min": predicates[pred]["energy_min"],
                    "source_dispatch": [],
                }
                labels[label] = entry
            if context not in entry["contexts"]:
                entry["contexts"].append(context)
            entry["slot"] = pred
            entry["energy_min"] = predicates[pred]["energy_min"]
            if func_name not in entry["source_dispatch"]:
                entry["source_dispatch"].append(func_name)
            # First function per context keeps the order (doAllAction, not doStand).
            if context in ("stand", "air", "guard"):
                orders = entry.setdefault("dispatch_orders", {})
                if context not in orders:
                    orders[context] = order
                if entry.get("dispatch_order") is None:
                    entry["dispatch_order"] = order
                    entry["dispatch_priority"] = order

    entries = []
    for label, entry in labels.items():
        entry["contexts"] = infer_contexts(
            label, entry["group"], set(entry["contexts"])
        )
        entry["implementation"] = implementation_for(label, entry["has_timeline"])
        entries.append(entry)
    entries.sort(key=lambda item: (item["label"], item["group"]))

    cancel_windows = []
    seen_cancels: set[tuple[str, str, str, int]] = set()
    for script in timeline_scripts:
        if script.get("kind") != "clip_action":
            continue
        clip_matches = list(IF_GOTO_RE.finditer(script["source"]))
        for order, match in enumerate(clip_matches):
            origin = script["action"]
            target = match["label"]
            pred = match["pred"]
            key = (origin, target, pred, script["frame"])
            if key in seen_cancels:
                continue
            seen_cancels.add(key)
            handled = (origin, target) in HANDLED_ELSEWHERE_CANCELS
            cancel_windows.append(
                {
                    "from": origin,
                    "to": target,
                    "predicate": pred,
                    "combo": "true" in match["args"],
                    "start_frame": script["frame"],
                    "kind": "input",
                    "dispatch_order": order,
                    "implementation": (
                        "handled_elsewhere" if handled else "wired"
                    ),
                    "source_path": script["path"],
                    "source_sha256": script["source_sha256"],
                }
            )
    for window in motion_windows or []:
        origin = str(window.get("action", ""))
        for field, kind in (
            ("contact_cancel_to", "contact"),
            ("land_cancel_to", "land"),
        ):
            if field not in window:
                continue
            target = str(window[field])
            handled = (origin, target) in HANDLED_ELSEWHERE_CANCELS
            cancel_windows.append(
                {
                    "from": origin,
                    "to": target,
                    "predicate": kind,
                    "combo": False,
                    "start_frame": window["start_frame"],
                    "end_frame": window.get("end_frame"),
                    "kind": kind,
                    "implementation": (
                        "handled_elsewhere" if handled else "wired"
                    ),
                    "source_path": window.get("source_path"),
                    "source_sha256": window.get("source_sha256"),
                }
            )
    cancel_windows.sort(
        key=lambda item: (item["start_frame"], item["from"], item["to"], item["kind"])
    )

    gaps = []
    for entry in entries:
        if entry["implementation"] != "wired":
            gaps.append(
                {
                    "kind": "command",
                    "label": entry["label"],
                    "slot": entry["slot"],
                    "reason": entry["implementation"],
                    "has_timeline": entry["has_timeline"],
                    "contexts": entry["contexts"],
                }
            )
    for window in cancel_windows:
        if window["implementation"] == "catalog_only":
            gaps.append(
                {
                    "kind": "cancel",
                    "from": window["from"],
                    "to": window["to"],
                    "predicate": window["predicate"],
                    "reason": "cancel_not_wired",
                    "source_path": window.get("source_path"),
                }
            )
    for context, pred in slot_targets:
        label = slot_targets[(context, pred)]
        if not any(item["label"] == label for item in entries):
            gaps.append(
                {
                    "kind": "command",
                    "label": label,
                    "slot": pred,
                    "reason": "missing_timeline",
                    "has_timeline": False,
                    "contexts": [context],
                }
            )
    used_slots = {item.get("slot") for item in entries if item.get("slot")}
    used_slots |= {
        window["predicate"]
        for window in cancel_windows
        if window.get("kind") == "input"
    }
    for name in PREDICATE_NAMES:
        if name in ("moveLeft", "moveRight") or name in used_slots:
            continue
        gaps.append(
            {
                "kind": "predicate",
                "slot": name,
                "reason": "no_dispatch_label",
            }
        )

    return {
        "format": "bvn26-command-catalog-v1",
        "status": "reverse_engineering_intermediate",
        "id_convention": "source_frame_label",
        "control_path": control_path,
        "control_sha256": text_sha256(source),
        "predicates": predicates,
        "entries": entries,
        "cancel_windows": cancel_windows,
        "gaps": gaps,
    }
