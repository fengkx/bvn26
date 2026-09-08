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


def build(workspace: Path, output: Path, manifest_path: Path, source: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads((workspace / "export-report.json").read_text(encoding="utf-8"))
    if report["source"]["sha256"] != file_sha256(source):
        raise ValueError("Export workspace does not match the source SWF")
    timeline = extract_frames(workspace / "main.xml", 1738)
    root = ET.parse(workspace / "main.xml").getroot()
    stages = []
    music_output = output / "music"
    music_output.mkdir(parents=True, exist_ok=True)
    for key, entry in manifest["map_catalog"].items():
        matches = [f for f in timeline["frames"] if entry["frame"] in f["labels"]]
        if len(matches) != 1:
            raise ValueError(f"Expected one stage label: {entry['frame']}")
        frame = matches[0]
        names = {p.get("name") for p in frame["display_list"]}
        if not {"p1", "p2"} <= names:
            raise ValueError(f"Missing fighter spawn markers: {key}")
        directory = output / f"frame_{frame['frame']}"
        directory.mkdir(parents=True, exist_ok=True)
        sliced = copy.deepcopy(timeline)
        sliced["frames"] = [frame]
        sliced["definitions"] = referenced_definitions(root, [frame])
        sliced["source_swf"] = {
            "path": source.as_posix(),
            "sha256": file_sha256(source),
        }
        # Keep the compiler input outside the materializer's destination file.
        timeline_path = output / f"frame_{frame['frame']}.timeline.json"
        timeline_path.write_text(
            json.dumps(sliced, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        assets = materialize(workspace, timeline_path, directory)
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
                "asset_count": len(assets["assets"]),
                "runtime_verified": False,
            }
        )
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
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("godot/generated/stages/catalog")
    )
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    parser.add_argument("--source", type=Path, default=Path("game/main.swf"))
    args = parser.parse_args()
    print(
        json.dumps(
            build(args.workspace, args.output, args.manifest, args.source),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
