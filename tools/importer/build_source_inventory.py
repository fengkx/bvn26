"""Build a deterministic inventory of locked BVN 2.6 source assets and scripts.

This tool classifies inputs for conversion work. It does not execute
ActionScript and does not claim that any gameplay behavior is implemented.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from inspect_swf import inspect  # noqa: E402


TAG_NAMES = {
    0: "End",
    1: "ShowFrame",
    2: "DefineShape",
    6: "DefineBits",
    8: "JPEGTables",
    9: "SetBackgroundColor",
    11: "DefineText",
    12: "DoAction",
    14: "DefineSound",
    15: "StartSound",
    20: "DefineBitsLossless",
    21: "DefineBitsJPEG2",
    22: "DefineShape2",
    26: "PlaceObject2",
    28: "RemoveObject2",
    32: "DefineShape3",
    34: "DefineButton2",
    35: "DefineBitsJPEG3",
    36: "DefineBitsLossless2",
    37: "DefineEditText",
    39: "DefineSprite",
    43: "FrameLabel",
    45: "SoundStreamHead2",
    46: "DefineMorphShape",
    56: "ExportAssets",
    59: "DoInitAction",
    69: "FileAttributes",
    70: "PlaceObject3",
    73: "DefineFontAlignZones",
    74: "CSMTextSettings",
    75: "DefineFont3",
    77: "Metadata",
    83: "DefineShape4",
    88: "DefineFontName",
}

INVENTORY_PARSED_TAGS = {0, 1, 12, 26, 39, 43, 56, 59, 69, 70}
METADATA_TAGS = {69, 73, 74, 77, 88}
TIMELINE_TAGS = {0, 1, 12, 15, 26, 28, 39, 43, 45, 59, 70}

SCRIPT_RULES = (
    ("platform_adapter", re.compile(r"\b(?:getURL|ExternalInterface|SharedObject|4399)\b", re.I)),
    ("ai", re.compile(r"\b(?:Math\.random|aiMode|cpuLevel|computer)\b", re.I)),
    ("collision_or_damage", re.compile(r"\b(?:hitTest|damage|hurt|beHit|blood|hp)\b", re.I)),
    ("input_or_control", re.compile(r"\b(?:Key\.|keyDown|keyUp|initCtrl|ctrl)\b", re.I)),
    ("audio", re.compile(r"\b(?:Sound|startSound|stopAllSounds)\b", re.I)),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_script(path: str, source: str) -> tuple[str, str]:
    if path.startswith("__Packages/AS2_4399_API/"):
        return "init_action_class", "platform_adapter"
    if path.startswith("__Packages/"):
        return "init_action_class", "library_support"
    if "CLIPACTIONRECORD" in path:
        event_type = "clip_action"
    elif "BUTTONCONDACTION" in path:
        event_type = "button_action"
    elif path.endswith("/DoAction.as") or "/DoAction_" in path:
        event_type = "frame_action"
    else:
        event_type = "unresolved_event_type"

    for category, pattern in SCRIPT_RULES:
        if pattern.search(source):
            return event_type, category
    if event_type == "button_action":
        return event_type, "ui"
    return event_type, "unresolved_semantics"


def tag_record(code: int, count: int) -> dict[str, object]:
    if code in METADATA_TAGS:
        role = "metadata"
    elif code in TIMELINE_TAGS:
        role = "timeline_or_event"
    else:
        role = "visual_or_audio_asset"
    return {
        "code": code,
        "name": TAG_NAMES.get(code, "Unknown"),
        "count": count,
        "role": role,
        "gameplay_relevance": "not_gameplay" if code in METADATA_TAGS else "indirect_or_direct",
        "inventory_status": "parsed" if code in INVENTORY_PARSED_TAGS else "counted_only",
        "conversion_status": "pending",
    }


def build_inventory(root: Path) -> dict[str, object]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assets = []
    aggregate_tags: collections.Counter[int] = collections.Counter()
    clip_action_tag_count = 0

    for source_asset in sorted(manifest["assets"], key=lambda item: item["path"]):
        path = root / source_asset["path"]
        raw = path.read_bytes()
        actual_sha = sha256_bytes(raw)
        if actual_sha != source_asset["sha256"]:
            raise ValueError(f"Locked asset hash mismatch: {source_asset['path']}")
        record: dict[str, object] = {
            "path": source_asset["path"],
            "bytes": len(raw),
            "sha256": actual_sha,
            "source": source_asset["source"],
            "kind": path.suffix.lower().lstrip("."),
        }
        if path.suffix.lower() == ".swf":
            details = inspect(path)
            counts = {int(code): count for code, count in details["tag_counts"].items()}
            aggregate_tags.update(counts)
            clip_action_tag_count += len(details["clip_action_tags"])
            record["swf"] = {
                key: details[key]
                for key in (
                    "uncompressed_bytes",
                    "swf_version",
                    "avm",
                    "file_attributes",
                    "width",
                    "height",
                    "header_fps",
                    "root_frames",
                    "exports",
                    "clip_action_tags",
                    "timelines",
                )
            }
            record["swf"]["tags"] = [
                tag_record(code, count) for code, count in sorted(counts.items())
            ]
        assets.append(record)

    bundles = []
    script_category_counts: collections.Counter[str] = collections.Counter()
    script_event_counts: collections.Counter[str] = collections.Counter()
    clip_action_script_count = 0
    for bundle_ref in sorted(manifest["script_bundles"], key=lambda item: item["path"]):
        bundle = json.loads((root / bundle_ref["path"]).read_text(encoding="utf-8"))
        scripts = []
        for script in sorted(bundle["scripts"], key=lambda item: item["path"]):
            source = script["source"]
            event_type, category = classify_script(script["path"], source)
            script_category_counts[category] += 1
            script_event_counts[event_type] += 1
            if event_type == "clip_action":
                clip_action_script_count += 1
            scripts.append(
                {
                    "path": script["path"],
                    "bytes": len(source.encode("utf-8")),
                    "sha256": sha256_bytes(source.encode("utf-8")),
                    "event_type": event_type,
                    "semantic_category": category,
                    "gameplay_relevance": (
                        "not_gameplay" if category == "platform_adapter" else "unknown_or_relevant"
                    ),
                    "conversion_status": (
                        "excluded_external_platform_adapter"
                        if category == "platform_adapter"
                        else "pending"
                    ),
                }
            )
        bundles.append(
            {
                "path": bundle_ref["path"],
                "game_file": bundle["game_file"],
                "swf_sha256": bundle["swf_sha256"],
                "script_count": len(scripts),
                "scripts": scripts,
            }
        )

    return {
        "format": "bvn26-source-inventory-v1",
        "baseline_sha256": manifest["baseline"]["main_sha256"],
        "classification_notice": (
            "Script semantic categories are conservative static hints. "
            "unresolved_semantics remains pending until manual or runtime analysis."
        ),
        "summary": {
            "asset_count": len(assets),
            "swf_count": sum(asset["kind"] == "swf" for asset in assets),
            "script_bundle_count": len(bundles),
            "script_count": sum(bundle["script_count"] for bundle in bundles),
            "clip_action_tag_count": clip_action_tag_count,
            "clip_action_script_count": clip_action_script_count,
            "clip_action_count_notice": (
                "A placement tag may contain multiple CLIPACTIONRECORD scripts; "
                "tag and script counts are not expected to be equal."
            ),
            "tag_counts": [
                tag_record(code, count) for code, count in sorted(aggregate_tags.items())
            ],
            "script_event_counts": dict(sorted(script_event_counts.items())),
            "script_category_counts": dict(sorted(script_category_counts.items())),
        },
        "assets": assets,
        "script_bundles": bundles,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data/source-inventory.json",
    )
    args = parser.parse_args()
    inventory = build_inventory(REPO_ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(inventory["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
