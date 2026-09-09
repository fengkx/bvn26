"""Compile the shared hit-receive chain from fighter + main scripts.

Source: docs/HIT_RECEIVE_SOP.md step B. Runtime may only consume these
fields. Do not invent cut-in names, reset frames, or FX timings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HIT_RECEIVE_FUNCS = (
    "beida",
    "fangyu",
    "checkHit",
    "onBeHit",
    "isPoFangAct",
)

HITS_ZERO_RE = re.compile(r"^\s*hits\s*=\s*0;\s*$")
ON_BE_HIT_RE = re.compile(r"^onBeHit\((?P<flying>true)?\);\s*$")
ON_DEFENCE_RE = re.compile(r"^onDefence\((?P<xgtype>\d+)?\);\s*$")
SHOW_FACE_RE = re.compile(r'_root\.showFace\s*\(\s*pn\s*,\s*"(?P<label>[^"]+)"\s*\)')
SUPER_START_RE = re.compile(r"_root\.(?P<op>bsd|cbsd)\s*\(")
SUPER_END_RE = re.compile(r"_root\.(?P<op>bsw|cbsw)\s*\(")
FRAME_PATH_RE = re.compile(
    r"^DefineSprite_(?P<sprite>\d+)(?:_[A-Za-z0-9]+)*/frame_(?P<frame>\d+)/"
)
BDXG_CASE_RE = re.compile(
    r"case\s+(?P<zl>\d+)\s*:\s*[\s\S]*?addChildXG\([^,]+,\s*\"(?P<clip>XG_[^\"]+)\"",
)
P1HITS_PN_RE = re.compile(r"p1hits\.pn\s*=\s*(?P<pn>\d+)")
P2HITS_PN_RE = re.compile(r"p2hits\.pn\s*=\s*(?P<pn>\d+)")
PAUSE_RE = re.compile(r"pauseGame\s*\(")
RESUME_RE = re.compile(r"resumeGame\s*\(")
SHINE_RE = re.compile(r"shine\s*\(\s*(?P<color>\d*)\s*\)")
SHAKE_RE = re.compile(
    r"_root\._(?P<axis>[xy])\s*(?P<op>=|\+=|-=)\s*(?:_root\._[xy]\s*=\s*)?(?P<num>-?\d+(?:\.\d+)?)"
)
UNLOAD_RE = re.compile(r"unloadMovie\s*\(")
RANDOM_OFFSET_RE = re.compile(
    r"_(?P<axis>[XY])\s*=\s*_(?P=axis)\s*\+\s*\(Math\.random\(\)\s*\*\s*"
    r"(?P<positive>\d+)\s*-\s*Math\.random\(\)\s*\*\s*(?P<negative>\d+)\);"
)
FORM_ASSIGN_RE = re.compile(r"gjl(\d+)\.([A-Za-z0-9_]+)\s*=\s*([^;]+);")

FIELD_NAMES = {
    "pw": "damage",
    "zl": "impact_strength",
    "up": "vertical_impulse",
    "x": "horizontal_impulse",
    "tm": "hitstun_ms",
    "dz": "reaction_label",
}

XG_PREFIX_RE = re.compile(r"^(?P<prefix>DefineSprite_\d+_(?P<clip>XG_[A-Za-z0-9]+))/")


def extract_function(source: str, name: str) -> str | None:
    match = re.search(rf"function {name}\s*\([^)]*\)\s*\{{", source)
    if not match:
        return None
    start = match.start()
    brace = source.find("{", match.end() - 1)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    return None


def normalize_source(source: str) -> str:
    return re.sub(r"\s+", " ", source).strip()


def function_hash(source: str, name: str) -> str | None:
    body = extract_function(source, name)
    if body is None:
        return None
    return hashlib.sha256(normalize_source(body).encode("utf-8")).hexdigest()


def bundle_blob(script_bundle: dict[str, Any]) -> str:
    return "\n".join(script["source"] for script in script_bundle.get("scripts", []))


def on_defence_hit_receive(source: str) -> str | None:
    for match in re.finditer(r"function onDefence\s*\(([^)]*)\)\s*\{", source):
        brace = source.find("{", match.end() - 1)
        depth = 0
        for index in range(brace, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    body = source[match.start() : index + 1]
                    if "bdfyxg" in body:
                        return body
                    break
    return None


def parse_literal(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    raise ValueError(f"Unsupported AS2 literal: {value}")


def extract_attacks_by_form(source: str) -> dict[str, Any]:
    by_form: dict[int, dict[str, dict[str, Any]]] = {}
    for match in FORM_ASSIGN_RE.finditer(source):
        form = int(match.group(1))
        property_name = match.group(2)
        suffix = next(
            (candidate for candidate in FIELD_NAMES if property_name.endswith(candidate)),
            None,
        )
        if suffix is None:
            continue
        attack = property_name[: -len(suffix)]
        by_form.setdefault(form, {}).setdefault(attack, {})[FIELD_NAMES[suffix]] = (
            parse_literal(match.group(3))
        )
    forms = {}
    for form, attacks in sorted(by_form.items()):
        forms[str(form)] = {
            "form": form,
            "status": "extracted",
            "attacks": dict(sorted(attacks.items())),
        }
    return forms


def compile_hits_reset_frames(script_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    frames = []
    for script in script_bundle.get("scripts", []):
        if not HITS_ZERO_RE.match(script["source"].replace("\r", "").strip()):
            continue
        match = FRAME_PATH_RE.match(script["path"])
        if match is None:
            continue
        frames.append(
            {
                "sprite_id": int(match["sprite"]),
                "frame": int(match["frame"]),
                "source_path": script["path"],
            }
        )
    frames.sort(key=lambda item: (item["sprite_id"], item["frame"]))
    return frames


def compile_on_be_hit_frames(script_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    frames = []
    for script in script_bundle.get("scripts", []):
        text = script["source"].replace("\r", "").strip()
        match = ON_BE_HIT_RE.match(text)
        if match is None:
            continue
        path_match = FRAME_PATH_RE.match(script["path"])
        if path_match is None:
            continue
        frames.append(
            {
                "sprite_id": int(path_match["sprite"]),
                "frame": int(path_match["frame"]),
                "flying": match.group("flying") == "true",
                "source_path": script["path"],
            }
        )
    frames.sort(key=lambda item: (item["sprite_id"], item["frame"]))
    return frames


def compile_on_defence_frames(script_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    frames = []
    for script in script_bundle.get("scripts", []):
        text = script["source"].replace("\r", "").strip()
        match = ON_DEFENCE_RE.match(text)
        if match is None:
            continue
        path_match = FRAME_PATH_RE.match(script["path"])
        if path_match is None:
            continue
        xgtype = int(match.group("xgtype") or 1)
        frames.append(
            {
                "sprite_id": int(path_match["sprite"]),
                "frame": int(path_match["frame"]),
                "xgtype": xgtype,
                "source_path": script["path"],
            }
        )
    frames.sort(key=lambda item: (item["sprite_id"], item["frame"]))
    return frames


def compile_super_events(scripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    for script in scripts:
        if script.get("kind") != "frame_action":
            continue
        source = script["source"]
        # Shared form init (frame 1) defines helpers that mention _root.bsw.
        # Only compile actual call-site frames.
        if re.search(r"(?m)^function\s+", source):
            continue
        start = SUPER_START_RE.search(source)
        face = SHOW_FACE_RE.search(source)
        end = SUPER_END_RE.search(source)
        if start is None and face is None and end is None:
            continue
        event = {
            "action": script.get("action"),
            "frame": script.get("frame"),
            "source_path": script["path"],
            "source_sha256": script.get("source_sha256"),
        }
        if start is not None:
            event["op"] = "super_start"
            event["kind"] = start.group("op")
            # Source bsd() default xg="XG_bs"; cbsd(pn) is bsd(pn,"XG_cbs").
            event["xg"] = "XG_cbs" if start.group("op") == "cbsd" else "XG_bs"
        if end is not None:
            event["op"] = "super_end"
            event["kind"] = end.group("op")
        if face is not None:
            event["face_label"] = face.group("label")
            if "op" not in event:
                event["op"] = "show_face"
        events.append(event)
    events.sort(key=lambda item: (item.get("frame") or 0, item.get("action") or ""))
    return events


def compile_show_face_labels(script_bundle: dict[str, Any]) -> list[str]:
    labels = []
    for script in script_bundle.get("scripts", []):
        for match in SHOW_FACE_RE.finditer(script["source"]):
            label = match.group("label")
            if label not in labels:
                labels.append(label)
    return labels


def _clip_events_for_prefix(script_bundle: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    events = []
    for script in script_bundle.get("scripts", []):
        if not script["path"].startswith(prefix + "/"):
            continue
        match = FRAME_PATH_RE.match(script["path"])
        if match is None:
            continue
        frame = int(match["frame"])
        source = script["source"]
        if PAUSE_RE.search(source):
            events.append({"frame": frame, "op": "pause_game", "source_path": script["path"]})
        shine = SHINE_RE.search(source)
        if shine:
            color = int(shine.group("color") or 0xFFFFFF)
            events.append(
                {
                    "frame": frame,
                    "op": "shine",
                    "color_rgb24": color,
                    "source_path": script["path"],
                }
            )
        for shake in SHAKE_RE.finditer(source):
            amount = float(shake.group("num"))
            if shake.group("op") == "-=":
                amount = -amount
            events.append(
                {
                    "frame": frame,
                    "op": "shake_root",
                    "axis": shake.group("axis"),
                    "pixels": amount,
                    "source_path": script["path"],
                }
            )
        offsets = list(RANDOM_OFFSET_RE.finditer(source))
        if source.count("Math.random()") != len(offsets) * 2:
            raise ValueError("Unsupported hit-effect random expression: " + script["path"])
        for offset in offsets:
            first = source[:offset.start()].count("Math.random()") + 1
            events.append({
                "frame": frame, "op": "random_offset", "axis": offset["axis"].lower(),
                "positive_factor": int(offset["positive"]),
                "negative_factor": int(offset["negative"]),
                "random_sites": [f'main#{script["path"]}:{first + i}' for i in range(2)],
                "source_path": script["path"],
            })
        if RESUME_RE.search(source):
            events.append({"frame": frame, "op": "resume_game", "source_path": script["path"]})
        if UNLOAD_RE.search(source):
            events.append({"frame": frame, "op": "unload", "source_path": script["path"]})
    events.sort(key=lambda item: item["frame"])
    return events


def _switch_clip_table(func_source: str) -> dict[int, str]:
    table: dict[int, str] = {}
    for match in BDXG_CASE_RE.finditer(func_source):
        table[int(match.group("zl"))] = match.group("clip")
    return table


def compile_hit_fx(main_bundle: dict[str, Any]) -> dict[str, Any]:
    frame8 = next(
        (script for script in main_bundle["scripts"] if script["path"] == "frame_8/DoAction.as"),
        None,
    )
    if frame8 is None:
        raise ValueError("main.json missing frame_8/DoAction.as")
    tables: dict[str, dict[int, str]] = {}
    for name in ("bdxg", "bdfyxg", "bdfyxg2"):
        body = extract_function(frame8["source"], name)
        if body is None:
            raise ValueError(f"{name}() missing from frame_8")
        tables[name] = _switch_clip_table(body)
    body = extract_function(frame8["source"], "bdxg")
    color_effects = {}
    for case in re.finditer(r"case\s+(\d+)\s*:(.*?)(?=case\s+\d+\s*:|default\s*:|$)", body, re.S):
        strength, source = case.groups()
        palette = re.search(r"selfmc\._parent\.setColor\((\[.*?\])\);", source, re.S)
        matrix = re.findall(r"_loc2_ = _loc2_\.concat\((\[[^]]+\])\);", source)
        if palette:
            # AS2 object keys are unquoted identifiers; preserve every numeric
            # value and array order rather than choosing colors by element.
            value = re.sub(r"([A-Za-z_]\w*)\s*:", r'"\1":', palette[1])
            color_effects[int(strength)] = {"op": "set_colors", "colors": json.loads(value)}
        elif matrix:
            values = [value for row in matrix for value in json.loads(row)]
            if len(values) != 20 or "selfmc.filters = [_loc3_];" not in source:
                raise ValueError("Unsupported bdxg color matrix")
            color_effects[int(strength)] = {"op": "set_color_matrix", "matrix": values}
        if int(strength) in color_effects:
            color_effects[int(strength)]["source_path"] = "frame_8/DoAction.as#bdxg"
    prefixes: dict[str, str] = {}
    for script in main_bundle.get("scripts", []):
        match = XG_PREFIX_RE.match(script["path"])
        if match:
            prefixes[match.group("clip")] = match.group("prefix")
    clips = {}
    extra_clips = ("XG_bs", "XG_cbs", "XG_bsq", "XG_fzcc", "XG_fzbs")
    clip_names = []
    for table in tables.values():
        clip_names.extend(table.values())
    clip_names.extend(extra_clips)
    for clip_name in clip_names:
        if clip_name in clips:
            continue
        prefix = prefixes.get(clip_name)
        events = _clip_events_for_prefix(main_bundle, prefix) if prefix else []
        clips[clip_name] = {
            "clip": clip_name,
            "source_prefix": prefix,
            "imported": prefix is not None,
            "presentation_events": events,
        }
    return {
        "source_path": "frame_8/DoAction.as",
        "bdxg": tables["bdxg"],
        "color_effects": color_effects,
        "bdfyxg": tables["bdfyxg"],
        "bdfyxg2": tables["bdfyxg2"],
        "clips": clips,
    }


def compile_combo_hud(
    main_bundle: dict[str, Any], *, play_frame: int | None = None
) -> dict[str, Any]:
    p1_pn = None
    p2_pn = None
    p1_path = None
    p2_path = None
    number_frame = None
    reset_frame = None
    stop_frame = None
    number_path = None
    reset_path = None
    for script in main_bundle["scripts"]:
        if p1_pn is None:
            match = P1HITS_PN_RE.search(script["source"])
            if match:
                p1_pn = int(match.group("pn"))
                p1_path = script["path"]
        if p2_pn is None:
            match = P2HITS_PN_RE.search(script["source"])
            if match:
                p2_pn = int(match.group("pn"))
                p2_path = script["path"]
        if script["path"].startswith("DefineSprite_1833/"):
            frame_match = FRAME_PATH_RE.match(script["path"])
            source = script["source"].replace("\r", "")
            if frame_match and "stop();" in source and stop_frame is None:
                stop_frame = int(frame_match["frame"])
            if "changeNum" in source and frame_match:
                number_frame = int(frame_match["frame"])
                number_path = script["path"]
            if "gotoAndStop(1)" in source and frame_match:
                reset_frame = int(frame_match["frame"])
                reset_path = script["path"]
    if p1_pn is None or p2_pn is None:
        raise ValueError("p1hits.pn / p2hits.pn missing from main.json")
    return {
        "p1hits_pn": p1_pn,
        "p2hits_pn": p2_pn,
        "p1hits_source_path": p1_path,
        "p2hits_source_path": p2_path,
        "play_label": "连击",
        "play_frame": play_frame,
        "stop_frame": stop_frame or 1,
        "show_number_frame": number_frame,
        "reset_frame": reset_frame,
        "show_number_source_path": number_path,
        "reset_source_path": reset_path,
        "bar2_chase_per_tick": "maxhp/500",
    }


def _sprite_timeline(swf: dict[str, Any], sprite_id: int) -> dict[str, Any]:
    name = f"sprite_{sprite_id}"
    for timeline in swf.get("timelines", []):
        if timeline.get("name") == name:
            return timeline
    raise ValueError(f"sprite_{sprite_id} missing from main.swf")


def _label_frame(timeline: dict[str, Any], label: str) -> int | None:
    for item in timeline.get("labels", []):
        if item.get("label") == label:
            return int(item["frame"])
    return None


def _generated_timeline_imported(
    repo_root: Path | None, relative: str, sprite_id: int
) -> bool:
    if repo_root is None:
        return False
    path = repo_root / relative / "timeline.json"
    if not path.is_file():
        return False
    timeline = json.loads(path.read_text(encoding="utf-8"))
    return int(timeline.get("sprite_id", -1)) == sprite_id


def compile_super_presentation(
    main_bundle: dict[str, Any],
    *,
    swf_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Compile shared bsd/showFace/blackStg presentation from main.swf.

    Asset bitmaps are a separate import step. This records sprite ids, idle/in
    frames, and showFace(pn) slot mapping so the runtime only interprets source.
    """
    frame8 = next(
        (script for script in main_bundle["scripts"] if script["path"] == "frame_8/DoAction.as"),
        None,
    )
    if frame8 is None:
        raise ValueError("main.json missing frame_8/DoAction.as")
    black_stg = extract_function(frame8["source"], "blackStg")
    show_face = extract_function(frame8["source"], "showFace")
    if black_stg is None or show_face is None:
        raise ValueError("blackStg/showFace missing from frame_8")
    default_frame = 2
    default_match = re.search(r"frame\s*=\s*(\d+)", black_stg)
    if default_match:
        default_frame = int(default_match.group(1))
    # Root 游戏场景 PlaceObject names: blackMu=1510, ts_face=1678,
    # ts_face.bg=1517, face_p1/p2=1677, face=1676.
    if repo_root is None and swf_path is not None:
        repo_root = swf_path.resolve().parent.parent
    black_mu_dir = "godot/generated/main/blackMu"
    ts_face_dir = "godot/generated/main/ts_face"
    xg_bs_dir = "godot/generated/effects/XG_bs"
    xg_cbs_dir = "godot/generated/effects/XG_cbs"
    black_mu_imported = _generated_timeline_imported(repo_root, black_mu_dir, 1510)
    ts_face_imported = _generated_timeline_imported(repo_root, ts_face_dir, 1678)
    xg_imported = _generated_timeline_imported(
        repo_root, xg_bs_dir, 459
    ) and _generated_timeline_imported(repo_root, xg_cbs_dir, 441)
    black_mu = {
        "instance_name": "blackMu",
        "sprite_id": 1510,
        "idle_frame": 1,
        "super_frame": default_frame,
        "ko_label": "KO",
        "imported": black_mu_imported,
        "directory": "res://generated/main/blackMu",
        "source_path": "frame_8/DoAction.as",
    }
    ts_face = {
        "instance_name": "ts_face",
        "sprite_id": 1678,
        "bg_instance": "bg",
        "bg_sprite_id": 1517,
        "face_p1_instance": "face_p1",
        "face_p2_instance": "face_p2",
        "face_clip_sprite_id": 1677,
        "portrait_sprite_id": 1676,
        "idle_frame": 1,
        "in_label": "in",
        "out_label": "out",
        "in_frame": 5,
        "out_frame": 35,
        "bg_frame_count": 38,
        "face_frame_count": 38,
        "portrait_labels": {},
        # Source: pn != 2 ? face_p2 : face_p1. P1 caster passes pn==2.
        "pn_face_slot": {"1": "face_p2", "2": "face_p1"},
        "imported": ts_face_imported,
        "directory": "res://generated/main/ts_face",
        "source_path": "frame_8/DoAction.as",
    }
    if swf_path is not None:
        tools_dir = Path(__file__).resolve().parents[1]
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from inspect_swf import inspect  # noqa: WPS433

        swf = inspect(swf_path)
        black_timeline = _sprite_timeline(swf, 1510)
        black_mu["frame_count"] = int(black_timeline["declared_frames"])
        ko_frame = _label_frame(black_timeline, "KO")
        if ko_frame is not None:
            black_mu["ko_frame"] = ko_frame
        bg_timeline = _sprite_timeline(swf, 1517)
        face_timeline = _sprite_timeline(swf, 1677)
        portrait_timeline = _sprite_timeline(swf, 1676)
        ts_face["bg_frame_count"] = int(bg_timeline["declared_frames"])
        ts_face["face_frame_count"] = int(face_timeline["declared_frames"])
        ts_face["in_frame"] = _label_frame(bg_timeline, "in") or ts_face["in_frame"]
        ts_face["out_frame"] = _label_frame(bg_timeline, "out") or ts_face["out_frame"]
        ts_face["portrait_labels"] = {
            item["label"]: int(item["frame"])
            for item in portrait_timeline.get("labels", [])
        }
        if "鸣人2" not in ts_face["portrait_labels"]:
            raise ValueError("ts_face portrait sprite missing 鸣人2")
    return {
        "format": "bvn26-super-presentation-v1",
        "source_path": "frame_8/DoAction.as",
        "black_mu": black_mu,
        "ts_face": ts_face,
        "xg": {"bsd": "XG_bs", "cbsd": "XG_cbs"},
        "hide_stage_instances": ["bgmc", "fgmc"],
        "ts_face_imported": ts_face_imported,
        "black_mu_imported": black_mu_imported,
        "xg_imported": xg_imported,
    }


def combo_hud_play_frame(swf_path: Path, sprite_id: int = 1833, label: str = "连击") -> int:
    tools_dir = Path(__file__).resolve().parents[1]
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from inspect_swf import inspect  # noqa: WPS433

    swf = inspect(swf_path)
    for timeline in swf["timelines"]:
        if timeline["name"] != f"sprite_{sprite_id}":
            continue
        for item in timeline.get("labels", []):
            if item["label"] == label:
                return int(item["frame"])
    raise ValueError(f"{label} label missing on sprite_{sprite_id}")


def compile_shared_hit_receive(
    main_bundle: dict[str, Any],
    *,
    play_frame: int | None = None,
    swf_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if play_frame is None and swf_path is not None:
        play_frame = combo_hud_play_frame(swf_path)
    if repo_root is None and swf_path is not None:
        repo_root = swf_path.resolve().parent.parent
    return {
        "format": "bvn26-hit-receive-v1",
        "status": "reverse_engineering_intermediate",
        "hit_fx": compile_hit_fx(main_bundle),
        "combo_hud": compile_combo_hud(main_bundle, play_frame=play_frame),
        "super_presentation": compile_super_presentation(
            main_bundle, swf_path=swf_path, repo_root=repo_root
        ),
    }


def compile_fighter_hit_receive(
    script_bundle: dict[str, Any],
    scripts: list[dict[str, Any]],
    root_init_source: str,
    timeline_symbol_id: int,
) -> dict[str, Any]:
    forms = extract_attacks_by_form(root_init_source)
    missing = [form for form, payload in forms.items() if not payload["attacks"]]
    return {
        "attacks_by_form": forms,
        "hits_reset_frames": compile_hits_reset_frames(script_bundle),
        "on_be_hit_frames": compile_on_be_hit_frames(script_bundle),
        "on_defence_frames": compile_on_defence_frames(script_bundle),
        "super_events": compile_super_events(scripts),
        "face_labels": compile_show_face_labels(script_bundle),
        "timeline_symbol_id": timeline_symbol_id,
        "extracted_partial": bool(missing),
    }


def playable_fighter_paths(root: Path) -> list[Path]:
    return sorted((root / "scripts/fighter").glob("*.json"))


def helper_fighter_paths(root: Path) -> list[Path]:
    return sorted((root / "scripts/fighter/fz").glob("*.json"))


def load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_shared_hit_receive(root: Path) -> dict[str, Any]:
    payload = compile_shared_hit_receive(
        load_bundle(root / "scripts/main.json"),
        swf_path=root / "game/main.swf",
    )
    outputs = [
        root / "data/actions/hit_receive.json",
        root / "godot/generated/main/hit_receive.json",
    ]
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return {"output": [path.as_posix() for path in outputs], "play_frame": payload["combo_hud"]["play_frame"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(json.dumps(write_shared_hit_receive(args.root), ensure_ascii=False))


if __name__ == "__main__":
    main()
