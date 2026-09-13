#!/usr/bin/env python3
"""Compile Sakura's source-backed opening state markers into role-local data."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    role_dir = ROOT / "godot/generated/fighters/sakura"
    fighter = json.loads((role_dir / "fighter.json").read_text(encoding="utf-8"))
    timeline = json.loads((role_dir / "timeline.json").read_text(encoding="utf-8"))
    bundle_path = ROOT / "scripts/fighter/Sakura.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    sprite_id = int(timeline["sprite_id"])
    opening = next(
        span
        for group in fighter["actions"].values()
        for label, span in group.items()
        if label == "开场"
    )
    state_frames = {}
    sources = {}
    for entry in bundle["scripts"]:
        match = re.fullmatch(rf"DefineSprite_{sprite_id}/frame_(\d+)/DoAction.as", entry["path"])
        if not match:
            continue
        frame = int(match.group(1))
        if not opening["start_frame"] <= frame <= opening["end_frame"]:
            continue
        marker = re.search(r"\bkcplayed\s*=\s*(\d+)\s*;", entry["source"])
        if marker:
            state_frames[str(frame)] = int(marker.group(1))
            sources[str(frame)] = {
                "path": entry["path"],
                "sha256": hashlib.sha256(entry["source"].encode("utf-8")).hexdigest(),
                "source": entry["source"],
            }
    if sorted(state_frames.values()) != [1, 2, 3]:
        raise ValueError(f"Expected source opening stages 1,2,3; got {state_frames}")
    output = {
        "format": "bvn26-fighter-opening-v1",
        "status": "source_compiled_not_runtime_integrated",
        "fighter_id": "sakura",
        "source_fighter_id": fighter["fighter_id"],
        "source_sprite_id": sprite_id,
        "action": opening,
        "state_frames": state_frames,
        "state_frame_sources": sources,
        "shared_intro_assets": {
            "ready": "res://generated/main/intro/ready",
            "qjxg": "res://generated/main/intro/qjxg",
            "source": "game/main.swf; these are shared match-opening clips",
        },
        "source": {
            "swf_path": "game/fighter/Sakura.swf",
            "swf_sha256": fighter["source"]["swf_sha256"],
            "script_bundle_path": "scripts/fighter/Sakura.json",
            "script_bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
            "timeline_path": "data/slices/Sakura-base.timeline.json",
            "timeline_sha256": hashlib.sha256(
                (ROOT / "data/slices/Sakura-base.timeline.json").read_bytes()
            ).hexdigest(),
        },
    }
    (role_dir / "intro.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    evidence_dir = ROOT / "evidence/characters/sakura-ino"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "sakura-opening-source.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"fighter": "sakura", "state_frames": state_frames}))


if __name__ == "__main__":
    main()
