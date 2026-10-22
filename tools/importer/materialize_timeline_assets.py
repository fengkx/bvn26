"""Copy only the external assets reachable from an extracted timeline slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from source_instance_key import instance_key
from visual_control_guard import ROOT, validate_nested_controls


def _timeline_start_sound_ids(timeline: dict) -> set[int]:
    sound_ids = {
        int(event["sound_id"])
        for frame in timeline.get("frames", [])
        for event in frame.get("events", [])
        if event.get("type") == "start_sound" and "sound_id" in event
    }
    for definition in timeline.get("definitions", []):
        for frame_events in definition.get("display_list_frame_events", []):
            sound_ids.update(
                int(event["sound_id"])
                for event in frame_events
                if event.get("type") == "start_sound" and "sound_id" in event
            )
    return sound_ids


def _workspace_sound(workspace: Path, sound_id: int) -> Path | None:
    matches = sorted(workspace.glob(f"*_assets/sounds/{sound_id}.mp3"))
    if matches:
        return matches[0]
    fallback = workspace / "sounds" / f"{sound_id}.mp3"
    return fallback if fallback.is_file() else None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize(
    workspace: Path,
    timeline_path: Path,
    output_dir: Path,
    fighter_slice_path: Path | None = None,
    combat_model_path: Path | None = None,
) -> dict[str, object]:
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    if "source_swf" in timeline:
        bundle_path = ROOT / timeline["source_swf"]["path"].replace("game/", "scripts/").replace(".swf", ".json")
        validate_nested_controls(timeline, json.loads(bundle_path.read_text()))
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_manifest = output_dir / "assets.json"
    if previous_manifest.is_file():
        previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
        for asset in previous.get("assets", []):
            previous_name = Path(asset["path"])
            if previous_name.name != asset["path"]:
                raise ValueError(f"Unsafe generated asset path: {asset['path']}")
            (output_dir / previous_name).unlink(missing_ok=True)
    runtime_timeline = json.loads(json.dumps(timeline))
    if combat_model_path is not None:
        combat = json.loads(combat_model_path.read_text())
        handles = {p['instance_name'] for p in combat.get('projectiles', [])}
        for frame in runtime_timeline['frames']:
            for placement in frame['display_list']:
                if not placement.get('name') and instance_key(placement) in handles:
                    placement['name'] = instance_key(placement)
                    placement['runtime_only_name'] = True
    (output_dir / "timeline.json").write_text(json.dumps(runtime_timeline, ensure_ascii=False, indent=2) + "\n")
    if fighter_slice_path is not None:
        shutil.copyfile(fighter_slice_path, output_dir / "fighter.json")
    if combat_model_path is not None:
        shutil.copyfile(combat_model_path, output_dir / "combat.json")
    assets = []
    for definition in timeline["definitions"]:
        external_file = definition.get("external_file")
        if external_file is None:
            continue
        # images-png holds JPEXS PNG exports with the original alpha merged
        # back in; sound ids share the numbering space, so only bitmaps may
        # fall back to it.
        combined_png = workspace / "images-png" / f"{definition['character_id']}.png"
        is_bitmap = Path(external_file).suffix.lower() in (".png", ".jpg", ".jpeg")
        source = (
            combined_png
            if is_bitmap and combined_png.is_file()
            else workspace / external_file
        )
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = output_dir / f"{definition['character_id']}{source.suffix.lower()}"
        shutil.copyfile(source, destination)
        assets.append(
            {
                "character_id": definition["character_id"],
                "source_external_file": external_file,
                "materialized_source": source.relative_to(workspace).as_posix(),
                "path": destination.name,
                "bytes": destination.stat().st_size,
                "sha256": file_sha256(destination),
            }
        )
    copied_ids = {int(item["character_id"]) for item in assets}
    for sound_id in sorted(_timeline_start_sound_ids(timeline)):
        if sound_id in copied_ids:
            continue
        source = _workspace_sound(workspace, sound_id)
        if source is None:
            continue
        destination = output_dir / f"{sound_id}{source.suffix.lower()}"
        shutil.copyfile(source, destination)
        assets.append(
            {
                "character_id": sound_id,
                "source_external_file": source.relative_to(workspace).as_posix(),
                "materialized_source": source.relative_to(workspace).as_posix(),
                "path": destination.name,
                "bytes": destination.stat().st_size,
                "sha256": file_sha256(destination),
            }
        )

    report = {
        "format": "bvn26-materialized-assets-v1",
        "timeline": {
            "path": timeline_path.as_posix(),
            "sha256": file_sha256(timeline_path),
        },
        "fighter_slice": {
            "path": fighter_slice_path.as_posix(),
            "sha256": file_sha256(fighter_slice_path),
        }
        if fighter_slice_path is not None
        else None,
        "combat_model": {
            "path": combat_model_path.as_posix(),
            "sha256": file_sha256(combat_model_path),
        }
        if combat_model_path is not None
        else None,
        "assets": assets,
    }
    report_path = output_dir / "assets.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--fighter-slice", type=Path)
    parser.add_argument("--combat-model", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(
        args.workspace,
        args.timeline,
        args.output_dir,
        args.fighter_slice,
        args.combat_model,
    )
    print(json.dumps({"assets": len(report["assets"]), "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
