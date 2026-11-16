"""Rebuild only Sage Naruto's offline candidate packages, without admission."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/importer"))

from build_combat_model import build_model
from build_form_profile import compile_programs, voice_spec
from compile_ai_hit_state import compile_transfer
from compile_hurt_voice import build as build_voice
from extract_fighter_slice import extract_slice
from extract_timeline_geometry import extract_frames
from materialize_timeline_assets import materialize
from prepare_form_graph import prepare
from visual_control_guard import validate_nested_controls


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def build(workspace, ffdec, ffmpeg):
    bundle = json.loads((ROOT / "scripts/fighter/minrenx.json").read_text())
    report = json.loads((workspace / "export-report.json").read_text())
    assert report["source"]["sha256"] == bundle["swf_sha256"]
    for item in report["files"]:
        assert hashlib.sha256((workspace / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    base = ROOT / "godot/generated/fighters/minrenx"
    target = ROOT / "godot/generated/forms/minrenx-2"
    rows = []
    for name, directory, stem in (
        ("仙鸣", base, "minrenx-base"),
        ("黄金鸣人", target, "minrenx-form-2"),
    ):
        fighter = extract_slice(ROOT, name, allow_forms=True)
        sprite = fighter["source"]["timeline_symbol_id"]
        timeline = extract_frames(workspace / "minrenx.xml", sprite, wrapper_siblings=True)
        timeline["source_swf"] = {"path": bundle["game_file"], "sha256": bundle["swf_sha256"]}
        validate_nested_controls(timeline, bundle)
        fighter_path = Path("data/slices") / (stem + ".json")
        timeline_path = Path("data/slices") / (stem + ".timeline.json")
        fighter["source"]["timeline_path"] = timeline_path.as_posix()
        write(ROOT / fighter_path, fighter)
        write(ROOT / timeline_path, timeline)
        combat_path = Path("data/actions") / (stem + ".json")
        write(ROOT / combat_path, build_model(fighter_path, timeline_path, Path("scripts/fighter/minrenx.json")))
        materialize(workspace, timeline_path, directory, fighter_path, combat_path)
        compile_programs(directory, bundle, json.loads((directory / "timeline.json").read_text()))
        if directory == base:
            action = next(group["开场"] for group in fighter["actions"].values() if "开场" in group)
            sources = {}
            states = {}
            for record in bundle["scripts"]:
                match = re.fullmatch(rf"DefineSprite_{sprite}/frame_(\d+)/DoAction.as", record["path"])
                if not match or not action["start_frame"] <= int(match[1]) <= action["end_frame"]:
                    continue
                assignment = re.search(r"kcplayed = (\d+);", record["source"])
                if assignment:
                    states[match[1]] = int(assignment[1])
                    sources[match[1]] = {"path": record["path"], "source": record["source"].strip()}
            assert sorted(set(states.values())) == [1, 2, 3]
            write(directory / "intro.json", {
                "format": "bvn26-fighter-opening-v1", "status": "source_compiled_not_runtime_integrated",
                "fighter_id": "minrenx", "source_fighter_id": name, "source_sprite_id": sprite,
                "action": action, "state_frames": states, "state_frame_sources": sources,
                "source": {**fighter["source"], "timeline_sha256": hashlib.sha256((ROOT / timeline_path).read_bytes()).hexdigest()},
            })
        code, metadata = compile_transfer(bundle)
        (directory / "ai_hit_state.gd").write_text(code)
        write(directory / "ai_hit_state.json", metadata)
        if directory == base:
            build_voice(["minrenx"])
        else:
            write(directory / "hurt_voice.json", voice_spec(bundle, sprite, base))
        subprocess.run([
            sys.executable, str(ROOT / "tools/importer/build_sound_segments.py"),
            "--directory", str(directory), "--ffdec", str(ffdec), "--ffmpeg", str(ffmpeg),
        ], check=True)
        rows.append({"fighter": name, "sprite": sprite, "frames": len(timeline["frames"]),
                     "directory": str(directory.relative_to(ROOT))})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    # Activation and shared catalogs require serial integration and fresh parity evidence.
    write(ROOT / "evidence/characters/minrenx/form-graph-dry-run.json", prepare(base, {2: target}))
    write(ROOT / "evidence/characters/minrenx/offline-build.json", {
        "status": "compiled_not_integrated_or_parity_accepted", "packages": rows,
        "source_swf_sha256": bundle["swf_sha256"], "python": sys.version,
        "export_generator": report["generator"],
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("workspace", "ffdec", "ffmpeg"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.ffdec, args.ffmpeg)
