#!/usr/bin/env python3
"""Generate or verify the compatibility fingerprints used by online rooms."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable

from importer.visual_blend_modes import validate_timeline_blends
from importer.import_guards import finite_numbers
from importer.visual_control_guard import validate_build_controls
from importer.placement_build_guard import validate_build_placements
from importer.frame_call_guard import validate_cached_frame_calls


ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "godot"
OUTPUT = GODOT / "generated/online/manifest.json"
INPUTS_OUTPUT = ROOT / "evidence/online/manifest-inputs.json"
ENGINE_VERSION = "4.7.2-stable"
PEER_PROTOCOL_VERSION = 1
MATCHMAKING_PROTOCOL = ROOT / "services/matchmaking/src/protocol.ts"
ROOM_CATALOG = ROOT / "services/matchmaking/src/catalog.json"
SELECTION_CATALOG = GODOT / "generated/main/character_selection/available.json"
STAGE_CATALOG = GODOT / "generated/stages/catalog/catalog.json"


def load_json(path: Path) -> object:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        finite_numbers(value, str(path))
        return value
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc


def relative(path: Path, base: Path = ROOT) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def files_under(path: Path) -> Iterable[Path]:
    if not path.is_dir():
        raise ValueError(f"missing runtime content directory: {relative(path)}")
    ignored_directories = {".git", ".godot", "__pycache__"}
    ignored_names = {".DS_Store", "Thumbs.db"}
    for item in path.rglob("*"):
        if not item.is_file() or item.name in ignored_names or item.name.startswith("._"):
            continue
        if any(part in ignored_directories for part in item.relative_to(path).parts):
            continue
        if item.name.endswith(("~", ".tmp", ".bak")):
            continue
        yield item


def file_record(path: Path, base: Path = ROOT) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": relative(path, base),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
    }


def records(paths: Iterable[Path], base: Path = ROOT) -> list[dict[str, object]]:
    unique = {path.resolve() for path in paths}
    return [file_record(path, base) for path in sorted(unique, key=lambda item: relative(item, base))]


def fingerprint(records_value: list[dict[str, object]], metadata: dict[str, object]) -> str:
    payload = json.dumps(
        {"metadata": metadata, "files": records_value},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_inputs() -> list[Path]:
    paths = [
        GODOT / "project.godot",
        GODOT / "main.tscn",
        GODOT / "render_surface.tscn",
        GODOT / "export_presets.cfg",
        GODOT / "web/shell.html",
        MATCHMAKING_PROTOCOL,
    ]
    paths.extend(GODOT.glob("*.gd"))
    paths.extend(GODOT.glob("*.gdshader"))
    paths.extend(
        path
        for path in (GODOT / "generated").rglob("*.gd")
        if "/tests/" not in path.as_posix()
    )
    return paths


def content_inputs() -> tuple[list[Path], dict[str, list[str]]]:
    room_catalog = load_json(ROOM_CATALOG)
    selection = load_json(SELECTION_CATALOG)
    stages = load_json(STAGE_CATALOG)
    if not isinstance(room_catalog, dict) or not isinstance(selection, dict):
        raise ValueError("online content catalogs must be objects")
    if not isinstance(stages, dict) or not isinstance(stages.get("stages"), list):
        raise ValueError("invalid generated stage catalog")

    expected = {
        "fighters": room_catalog.get("fighters"),
        "helpers": room_catalog.get("helpers"),
    }
    names: dict[str, list[str]] = {}
    paths: list[Path] = [ROOM_CATALOG, SELECTION_CATALOG, STAGE_CATALOG]
    for kind, ids in expected.items():
        available = selection.get(kind)
        if not isinstance(ids, list) or not isinstance(available, dict):
            raise ValueError(f"invalid {kind} catalog")
        available_ids = set(str(value) for value in available.values())
        if set(ids) != available_ids or len(ids) != len(available_ids):
            raise ValueError(f"service and Godot {kind} catalogs differ")
        names[kind] = sorted(str(value) for value in ids)
        for content_id in names[kind]:
            category = "forms" if kind == "fighters" and content_id in selection.get("forms", {}) else kind
            directory = GODOT / "generated" / category / content_id
            paths.extend(files_under(directory))

    stage_ids = room_catalog.get("stages")
    if not isinstance(stage_ids, list):
        raise ValueError("invalid stage catalog")
    stage_entries = {
        str(stage.get("id")): stage
        for stage in stages["stages"]
        if isinstance(stage, dict)
    }
    if set(stage_ids) != set(stage_entries):
        raise ValueError("service and Godot stage catalogs differ")
    names["stages"] = sorted(str(value) for value in stage_ids)
    stage_root = GODOT / "generated/stages/catalog"
    for stage_id in names["stages"]:
        stage = stage_entries[stage_id]
        for field in ("directory", "background_directory"):
            directory_name = stage.get(field)
            if not isinstance(directory_name, str) or not directory_name:
                raise ValueError(f"stage {stage_id} is missing {field}")
            paths.extend(files_under(stage_root / directory_name))
        music = stage.get("music")
        if not isinstance(music, str) or not (stage_root / "music" / music).is_file():
            raise ValueError(f"stage {stage_id} is missing its music asset")
        paths.append(stage_root / "music" / music)

    # These generated tables contain shared move, stage, hit, menu and rendering data.
    ui = GODOT / "ui"
    if ui.is_dir():
        paths.extend(files_under(ui))
    for shared in (GODOT / "generated/main", GODOT / "generated/effects"):
        paths.extend(files_under(shared))
    # Runtime music and the bundled default stage also load outside the selected
    # stage source directories; hash the shipped copies as well.
    for shared in (GODOT / "generated/music", GODOT / "generated/stages/current_world"):
        paths.extend(files_under(shared))
    forms = GODOT / 'generated/forms'
    if forms.is_dir():
        paths.extend(files_under(forms))
    return paths, names


def make_documents() -> tuple[dict[str, object], dict[str, object]]:
    for timeline in (GODOT / "generated").rglob("timeline.json"):
        data = load_json(timeline)
        validate_timeline_blends(data, relative(timeline))
        validate_build_controls(data, relative(timeline))
        validate_build_placements(data, relative(timeline))
        if timeline.parent.parent == GODOT / "generated/fighters":
            validate_cached_frame_calls(data, load_json(timeline.with_name('ai.json')), directory=timeline.parent)
    protocol_text = MATCHMAKING_PROTOCOL.read_text(encoding="utf-8")
    protocol_match = re.search(r"export\s+const\s+VERSION\s*=\s*(\d+)", protocol_text)
    if not protocol_match:
        protocol_match = re.search(r"const\s+VERSION\s*=\s*(\d+)", protocol_text)
    if not protocol_match:
        raise ValueError("cannot determine matchmaking protocol version")
    protocol_version = int(protocol_match.group(1))

    build_records = records(build_inputs())
    content_paths, roster = content_inputs()
    content_records = records(content_paths)
    build_metadata = {
        "engine": ENGINE_VERSION,
        "matchmaking_protocol": protocol_version,
        "peer_protocol": PEER_PROTOCOL_VERSION,
    }
    content_metadata = {
        "matchmaking_protocol": protocol_version,
        "fighters": roster["fighters"],
        "helpers": roster["helpers"],
        "stages": roster["stages"],
    }
    compatibility = {
        "protocol": protocol_version,
        "build": fingerprint(build_records, build_metadata),
        "content": fingerprint(content_records, content_metadata),
    }
    manifest = {
        "schemaVersion": 1,
        "engine": ENGINE_VERSION,
        "compatibility": compatibility,
        "roster": roster,
        "inputSummary": {
            "build": {"count": len(build_records), "sha256": compatibility["build"]},
            "content": {"count": len(content_records), "sha256": compatibility["content"]},
        },
    }
    evidence = {
        "schemaVersion": 1,
        "engine": ENGINE_VERSION,
        "metadata": {"build": build_metadata, "content": content_metadata},
        "compatibility": compatibility,
        "inputs": {"build": build_records, "content": content_records},
    }
    return manifest, evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="fail if the generated manifest is stale")
    action.add_argument("--print", action="store_true", help="print the manifest without writing it")
    args = parser.parse_args()
    try:
        manifest, evidence = make_documents()
    except (OSError, ValueError) as exc:
        print(f"online manifest error: {exc}", file=sys.stderr)
        return 1

    serialized = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    evidence_serialized = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        try:
            existing = OUTPUT.read_text(encoding="utf-8")
            existing_evidence = INPUTS_OUTPUT.read_text(encoding="utf-8")
        except OSError:
            print("missing online compatibility output; regenerate it", file=sys.stderr)
            return 1
        if existing != serialized or existing_evidence != evidence_serialized:
            print("stale online compatibility output; regenerate it", file=sys.stderr)
            return 1
        compatibility = manifest["compatibility"]
        print(
            "ONLINE_MANIFEST_OK "
            f"fighters={len(manifest['roster']['fighters'])} "
            f"helpers={len(manifest['roster']['helpers'])} "
            f"stages={len(manifest['roster']['stages'])} "
            f"build={compatibility['build']} content={compatibility['content']}"
        )
        return 0
    if args.print:
        sys.stdout.write(serialized)
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    INPUTS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized, encoding="utf-8")
    INPUTS_OUTPUT.write_text(evidence_serialized, encoding="utf-8")
    compatibility = manifest["compatibility"]
    print(
        f"WROTE {relative(OUTPUT)} and {relative(INPUTS_OUTPUT)} "
        f"build={compatibility['build']} content={compatibility['content']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
