"""Extract code-driven evidence for the two base-form vertical slices.

The output is intermediate reverse-engineering data, not production gameplay
data. Every value retains its SWF and decompiled-script source path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from inspect_swf import inspect  # noqa: E402


COMMON_ACTION_GROUPS = {
    "movement": ["站立", "走", "瞬步", "跳", "落", "跳2", "落2", "落地"],
    "ground_combo": ["砍1", "砍2", "砍3"],
    "hurt": ["被打"],
}

FIGHTER_SPECIAL_LABELS = {
    "鸣人": ["必杀", "必杀1", "必杀0"],
    "一护": ["必杀"],
}

FIELD_NAMES = {
    "pw": "damage",
    "zl": "impact_strength",
    "up": "vertical_impulse",
    "x": "horizontal_impulse",
    "tm": "hitstun_ms",
    "dz": "reaction_label",
}

ASSIGNMENT_RE = re.compile(r"gjl1\.([A-Za-z0-9_]+)\s*=\s*([^;]+);")
FRAME_PATH_RE = re.compile(r"^DefineSprite_(\d+)/frame_(\d+)(?:/|$)")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_literal(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    raise ValueError(f"Unsupported AS2 literal in fighter table: {value}")


def extract_hit_parameters(source: str) -> dict[str, dict[str, Any]]:
    attacks: dict[str, dict[str, Any]] = {}
    for match in ASSIGNMENT_RE.finditer(source):
        property_name, literal = match.groups()
        suffix = next(
            (candidate for candidate in FIELD_NAMES if property_name.endswith(candidate)),
            None,
        )
        if suffix is None:
            continue
        attack = property_name[: -len(suffix)]
        attacks.setdefault(attack, {})[FIELD_NAMES[suffix]] = parse_literal(literal)
    return attacks


def _decompress_swf(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw[:3] == b"FWS":
        return raw
    if raw[:3] == b"CWS":
        return raw[:8] + zlib.decompress(raw[8:])
    raise ValueError(f"Unsupported SWF signature: {path}")


def root_placements(path: Path) -> list[dict[str, int]]:
    data = _decompress_swf(path)
    nbits = data[8] >> 3
    offset = 8 + (5 + 4 * nbits + 7) // 8 + 4
    frame = 1
    placements = []
    while offset + 2 <= len(data):
        header = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        tag_code = header >> 6
        size = header & 63
        if size == 63:
            size = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        payload = data[offset : offset + size]
        if tag_code in (26, 70):
            flags = payload[0]
            if tag_code == 26:
                depth = struct.unpack_from("<H", payload, 1)[0]
                cursor = 3
            else:
                extra_flags = payload[1]
                depth = struct.unpack_from("<H", payload, 2)[0]
                cursor = 4
                has_class_name = bool(extra_flags & 0x08)
                has_image = bool(extra_flags & 0x10)
                if has_class_name or (has_image and flags & 0x02):
                    cursor = payload.index(0, cursor) + 1
            character_id = None
            if flags & 0x02:
                character_id = struct.unpack_from("<H", payload, cursor)[0]
            if character_id is not None:
                placements.append(
                    {
                        "frame": frame,
                        "tag": tag_code,
                        "depth": depth,
                        "character_id": character_id,
                    }
                )
        if tag_code == 1:
            frame += 1
        offset += size
        if tag_code == 0:
            break
    return placements


def action_spans(labels: list[dict[str, Any]], frame_count: int) -> dict[str, dict[str, int]]:
    spans = {}
    for index, label in enumerate(labels):
        end = labels[index + 1]["frame"] - 1 if index + 1 < len(labels) else frame_count
        spans[label["label"]] = {"start_frame": label["frame"], "end_frame": end}
    return spans


def script_record(script: dict[str, str]) -> dict[str, Any]:
    source_bytes = script["source"].encode("utf-8")
    return {
        "path": script["path"],
        "sha256": sha256(source_bytes),
        "source": script["source"],
    }


def extract_slice(root: Path, fighter_key: str) -> dict[str, Any]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    fighter = manifest["fighter_catalog"][fighter_key]
    if "WKframe" in fighter:
        raise ValueError(f"{fighter_key} is not a base form")

    swf_path = root / "game/fighter" / fighter["url"]
    script_path = root / "scripts/fighter" / f"{swf_path.stem}.json"
    script_bundle = json.loads(script_path.read_text(encoding="utf-8"))
    scripts = script_bundle["scripts"]

    base_placements = [item for item in root_placements(swf_path) if item["frame"] == 1]
    if len(base_placements) != 1:
        raise ValueError(f"Expected one base-form placement in {swf_path}, got {base_placements}")
    timeline_id = base_placements[0]["character_id"]

    swf = inspect(swf_path)
    timeline = next(
        item for item in swf["timelines"] if item["name"] == f"sprite_{timeline_id}"
    )
    all_spans = action_spans(timeline["labels"], timeline["declared_frames"])
    selected_spans = {}
    selected_ranges = []
    action_groups = {
        **COMMON_ACTION_GROUPS,
        "special": FIGHTER_SPECIAL_LABELS[fighter_key],
    }
    for group, labels in action_groups.items():
        selected_spans[group] = {}
        for label in labels:
            if label not in all_spans:
                raise ValueError(f"Missing {fighter_key} action label: {label}")
            selected_spans[group][label] = all_spans[label]
            selected_ranges.append(all_spans[label])

    timeline_scripts = []
    for script in scripts:
        match = FRAME_PATH_RE.match(script["path"])
        if not match or int(match.group(1)) != timeline_id:
            continue
        frame = int(match.group(2))
        if any(item["start_frame"] <= frame <= item["end_frame"] for item in selected_ranges):
            timeline_scripts.append({"frame": frame, **script_record(script)})
    timeline_scripts.sort(key=lambda item: (item["frame"], item["path"]))

    root_init = next(script for script in scripts if script["path"] == "frame_1/DoAction.as")
    load_pattern = re.compile(
        rf"^frame_1/PlaceObject[23]_{timeline_id}_1/CLIPACTIONRECORD onClipEvent\(load\)\.as$"
    )
    load_script = next(script for script in scripts if load_pattern.match(script["path"]))
    speed_match = re.search(r"\bvar spd\s*=\s*(-?\d+(?:\.\d+)?);", load_script["source"])
    jump_match = re.search(
        r"\bvar jumpPower\s*=\s*(-?\d+(?:\.\d+)?);", load_script["source"]
    )
    if speed_match is None or jump_match is None:
        raise ValueError(f"Missing movement constants in {load_script['path']}")

    all_hit_parameters = extract_hit_parameters(root_init["source"])
    selected_attack_ids = ["k1", "k2", "k3"] + sorted(
        attack for attack in all_hit_parameters if attack.startswith("bs")
    )
    hit_parameters = {
        attack: all_hit_parameters[attack]
        for attack in selected_attack_ids
        if attack in all_hit_parameters
    }

    shared_paths = ["DefineSprite_16/frame_1/DoAction.as", "DefineSprite_2/frame_1/DoAction.as"]
    shared_scripts = [
        script_record(next(script for script in scripts if script["path"] == path))
        for path in shared_paths
    ]

    return {
        "format": "bvn26-fighter-slice-v1",
        "status": "reverse_engineering_intermediate",
        "fighter_id": fighter_key,
        "display_name": fighter["name"],
        "form_frame": 1,
        "source": {
            "swf_path": swf_path.relative_to(root).as_posix(),
            "swf_sha256": swf["sha256"],
            "script_bundle_path": script_path.relative_to(root).as_posix(),
            "script_bundle_sha256": sha256(script_path.read_bytes()),
            "timeline_symbol_id": timeline_id,
        },
        "movement_constants": {
            "speed_per_tick": parse_literal(speed_match.group(1)),
            "jump_power": parse_literal(jump_match.group(1)),
            "source": script_record(load_script),
        },
        "actions": selected_spans,
        "hit_parameters": {
            "source_path": root_init["path"],
            "attacks": hit_parameters,
        },
        "shared_control_scripts": shared_scripts,
        "timeline_scripts": timeline_scripts,
        "validation_notice": (
            "Frame spans come from SWF labels and values come from exact AS2 assignments. "
            "Execution order and collision geometry remain pending M0-03/M1-02 evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fighters", nargs="*", default=["鸣人", "一护"])
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "data/slices")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for fighter_key in args.fighters:
        result = extract_slice(REPO_ROOT, fighter_key)
        output = args.output_dir / f"{Path(result['source']['swf_path']).stem}-base.json"
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summaries.append(
            {
                "fighter": fighter_key,
                "timeline_symbol_id": result["source"]["timeline_symbol_id"],
                "output": output.relative_to(REPO_ROOT).as_posix(),
                "timeline_script_count": len(result["timeline_scripts"]),
            }
        )
    print(json.dumps(summaries, ensure_ascii=False))


if __name__ == "__main__":
    main()
