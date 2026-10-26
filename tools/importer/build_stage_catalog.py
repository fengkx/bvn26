"""Extract all catalogued stages from the locked main SWF timeline."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

from extract_timeline_geometry import (
    extract_frames,
    file_sha256,
    referenced_definitions,
)
from materialize_timeline_assets import materialize
from materialize_stage_music import materialize as materialize_music


def build(workspace: Path, output: Path, manifest_path: Path, source: Path,
          current_world_output: Path | None = None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads((workspace / "export-report.json").read_text(encoding="utf-8"))
    if report["source"]["sha256"] != file_sha256(source):
        raise ValueError("Export workspace does not match the source SWF")
    timeline = extract_frames(workspace / "main.xml", 1738)
    root = ET.parse(workspace / "main.xml").getroot()
    backgrounds = extract_frames(workspace / "main.xml", 1501)
    scripts = json.loads(Path("scripts/main.json").read_text(encoding="utf-8"))["scripts"]
    hidden_ids = {
        int(match[1])
        for item in scripts
        if (match := re.fullmatch(r"DefineSprite_(\d+)/frame_1/DoAction.as", item["path"]))
        and item["source"].strip() == "_visible = false;"
    }
    previous_catalog = output / "catalog.json"
    previous_stages = (json.loads(previous_catalog.read_text())["stages"]
                       if previous_catalog.is_file() else [])
    stages = []
    music_output = output / "music"
    music_output.mkdir(parents=True, exist_ok=True)
    directory = output / "world"
    directory.mkdir(parents=True, exist_ok=True)
    world_timeline = copy.deepcopy(timeline)
    # GameWorld owns the root game transform (source camera enterFrame).
    # Keeping its authored placement here applies that container twice.
    world_timeline.pop("wrapper", None)
    # Each cache identifies this complete source sprite. Keep every frame
    # and dependency so omitted root obligations cannot hide in a slice.
    # The stage consumer selects its catalog frame with autoplay disabled.
    for definition in world_timeline["definitions"]:
        if definition["character_id"] in hidden_ids:
            definition["initial_visible"] = False
    # Sprite1900 loads fighter/helper movies into these marker clips.
    # Their geometry remains available for spawning; the runtime owns art.
    for source_frame in world_timeline["frames"]:
        for placement in source_frame["display_list"]:
            if placement.get("name") in {"p1", "p2", "p1fz", "p2fz"}:
                placement["replaced_by_external_movie"] = True
    world_timeline["source_swf"] = {
        "path": source.as_posix(),
        "sha256": file_sha256(source),
    }
    # Keep the compiler input outside the materializer's destination file.
    timeline_path = output / "world.timeline.json"
    timeline_path.write_text(
        json.dumps(world_timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    assets = materialize(workspace, timeline_path, directory)
    for key, entry in manifest["map_catalog"].items():
        matches = [f for f in timeline["frames"] if entry["frame"] in f["labels"]]
        if len(matches) != 1:
            raise ValueError(f"Expected one stage label: {entry['frame']}")
        frame = matches[0]
        names = {p.get("name") for p in frame["display_list"]}
        if not {"p1", "p2"} <= names:
            raise ValueError(f"Missing fighter spawn markers: {key}")
        background_frame = next(f for f in backgrounds["frames"] if entry["frame"] in f["labels"])
        background = copy.deepcopy(backgrounds)
        background["frames"] = [background_frame]
        background["definitions"] = referenced_definitions(root, [background_frame])
        background_path = output / f"background_{frame['frame']}.timeline.json"
        background_path.write_text(json.dumps(background, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        materialize(workspace, background_path, output / f"background_{frame['frame']}")
        with tempfile.TemporaryDirectory(prefix="bvn-map-music-") as temporary:
            music = materialize_music(
                manifest_path, source.parent / "music", "一护", key, Path(temporary)
            )
            for asset in music["files"]:
                shutil.copyfile(
                    Path(temporary) / asset["path"], music_output / asset["path"]
                )
        (music_output / f"frame_{frame['frame']}.json").write_text(
            json.dumps(music, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        stages.append(
            {
                "id": key,
                "name": entry["name"],
                "frame": frame["frame"],
                "directory": directory.name,
                "music": entry["music"],
                "background_directory": f"background_{frame['frame']}",
                "background_frame": background_frame["frame"],
                "asset_count": len(assets["assets"]),
                "runtime_verified": False,
            }
        )
    if current_world_output is not None:
        materialize(workspace, timeline_path, current_world_output)
    script_bundle = json.loads(Path("scripts/main.json").read_text(encoding="utf-8"))
    defaults = next(
        item["source"]
        for item in script_bundle["scripts"]
        if item["path"] == "frame_7/DoAction.as"
    )
    floor_y = int(re.search(r"var floorY = (-?\d+);", defaults)[1])
    map_size_x = int(re.search(r"var mapSizeX = (\d+);", defaults)[1])
    catalog = {
        "floor_y": floor_y,
        "map_size_x": map_size_x,
        "source_swf": {"path": source.as_posix(), "sha256": file_sha256(source)},
        "sprite_id": 1738,
        "stages": stages,
    }
    (output / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Retire only directories previously owned by this catalog, after the
    # replacement has materialized successfully. Stale slices fail root guards.
    active_directories = {stage["directory"] for stage in stages}
    for stage in previous_stages:
        old_directory = stage["directory"]
        if old_directory not in active_directories:
            if not re.fullmatch(r"frame_\d+", old_directory):
                raise ValueError(f"Unexpected obsolete stage directory: {old_directory}")
            shutil.rmtree(output / old_directory)
            (output / f"{old_directory}.timeline.json").unlink(missing_ok=True)
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("godot/generated/stages/catalog")
    )
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    parser.add_argument("--source", type=Path, default=Path("game/main.swf"))
    parser.add_argument("--current-world-output", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(args.workspace, args.output, args.manifest, args.source, args.current_world_output),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
