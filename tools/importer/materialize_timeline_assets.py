"""Copy only the external assets reachable from an extracted timeline slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


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
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_manifest = output_dir / "assets.json"
    if previous_manifest.is_file():
        previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
        for asset in previous.get("assets", []):
            previous_name = Path(asset["path"])
            if previous_name.name != asset["path"]:
                raise ValueError(f"Unsafe generated asset path: {asset['path']}")
            (output_dir / previous_name).unlink(missing_ok=True)
    shutil.copyfile(timeline_path, output_dir / "timeline.json")
    if fighter_slice_path is not None:
        shutil.copyfile(fighter_slice_path, output_dir / "fighter.json")
    if combat_model_path is not None:
        shutil.copyfile(combat_model_path, output_dir / "combat.json")
    assets = []
    for definition in timeline["definitions"]:
        external_file = definition.get("external_file")
        if external_file is None:
            continue
        combined_png = workspace / "images-png" / f"{definition['character_id']}.png"
        source = combined_png if combined_png.is_file() else workspace / external_file
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
