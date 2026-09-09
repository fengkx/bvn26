"""Compile the stage BGM pick order and copy only the reachable music files.

Source: scripts/main.json :: DefineSprite_1900/frame_1/DoAction.as loadSound()

    var _loc3_ = _root.getFighterData(_root.p2selt);
    if(_loc3_.music) { if(Math.random() < 0.8) { _loc2_ = _loc3_.music; } }
    if(!_loc2_) {
       if(Math.random() < 0.5) {
          _loc2_ = !_loc3_.isNaruto ? _root.bleachMusic : _root.narutoMusic;
       } else {
          _loc2_ = _root.getMapData(_root.curStage).music;
       }
    }
    _root.stageSound = new Sound();
    _root.stageSound.loadSound(_root.musicDir + _loc2_);

The random draws are part of the source order, so the steps are emitted as data
and the runtime only interprets them. Playback numbers come from
scripts/main.json :: frame_8/DoAction.as startGame(), which calls
stageSound.start(0,999) and then setVolume(80).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


# Source main.json frame_1: var bleachMusic = "bleach.mp3"; narutoMusic = "naruto.mp3";
BLEACH_MUSIC = "bleach.mp3"
NARUTO_MUSIC = "naruto.mp3"
# Source main.json frame_1: var musicDir = "music/";
MUSIC_DIR = "music/"
LOAD_SOUND_SOURCE = "scripts/main.json :: DefineSprite_1900/frame_1/DoAction.as loadSound()"
START_GAME_SOURCE = "scripts/main.json :: frame_8/DoAction.as startGame()"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selection_steps(manifest: dict, p2selt: str, cur_stage: str) -> tuple[list[dict], bool]:
    fighters = manifest["fighter_catalog"]
    maps = manifest["map_catalog"]
    if p2selt not in fighters:
        raise KeyError(f"Unknown fighter_catalog entry: {p2selt}")
    if cur_stage not in maps:
        raise KeyError(f"Unknown map_catalog entry: {cur_stage}")
    # getFighterData is a plain fighterData[id] lookup; addFighterClone already
    # copied every parent key into the clone at registration time, and
    # fighter_catalog keeps that flattened result. No inheritance here.
    fighter_data = fighters[p2selt]
    is_naruto = bool(fighter_data.get("isNaruto", False))
    steps: list[dict] = []
    if fighter_data.get("music"):
        steps.append(
            {
                "random_below": 0.8,
                "random_site": "main#DefineSprite_1900/frame_1/DoAction.as:1",
                "file": fighter_data["music"],
                "source": f"fighter_catalog.{p2selt}.music",
            }
        )
    steps.append(
        {
            "random_below": 0.5,
            "random_site": "main#DefineSprite_1900/frame_1/DoAction.as:2",
            "file": NARUTO_MUSIC if is_naruto else BLEACH_MUSIC,
            "source": "narutoMusic" if is_naruto else "bleachMusic",
        }
    )
    map_music = maps[cur_stage].get("music")
    if not map_music:
        raise KeyError(f"map_catalog.{cur_stage} has no music; loadSound would bail out")
    steps.append(
        {
            "otherwise": True,
            "file": map_music,
            "source": f"map_catalog.{cur_stage}.music",
        }
    )
    return steps, is_naruto


def materialize(
    manifest_path: Path,
    music_dir: Path,
    p2selt: str,
    cur_stage: str,
    output_dir: Path,
) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    steps, is_naruto = selection_steps(manifest, p2selt, cur_stage)
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_manifest = output_dir / "music.json"
    if previous_manifest.is_file():
        previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
        for entry in previous.get("files", []):
            if Path(entry["path"]).name != entry["path"]:
                raise ValueError(f"Unsafe generated music path: {entry['path']}")
            (output_dir / entry["path"]).unlink(missing_ok=True)
    files = []
    for name in sorted({step["file"] for step in steps}):
        source = music_dir / name
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = output_dir / name
        shutil.copyfile(source, destination)
        files.append(
            {
                "file": name,
                "source_path": source.as_posix(),
                "path": destination.name,
                "bytes": destination.stat().st_size,
                "sha256": file_sha256(destination),
            }
        )
    report = {
        "format": "bvn26-stage-music-v1",
        "source": {
            "load_sound": LOAD_SOUND_SOURCE,
            "start_game": START_GAME_SOURCE,
            "music_dir": MUSIC_DIR,
        },
        "selection": {
            "p2selt": p2selt,
            "cur_stage": cur_stage,
            "is_naruto": is_naruto,
            "steps": steps,
        },
        "playback": {
            "start_offset_seconds": 0,
            "loops": 999,
            "volume_percent": 80,
        },
        "files": files,
    }
    previous_manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--music-dir", type=Path, required=True)
    parser.add_argument("--p2selt", required=True, help="Source _root.p2selt")
    parser.add_argument("--cur-stage", required=True, help="Source _root.curStage")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(
        args.manifest,
        args.music_dir,
        args.p2selt,
        args.cur_stage,
        args.output_dir,
    )
    print(json.dumps({"files": len(report["files"]), "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
