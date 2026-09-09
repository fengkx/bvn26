"""Retain countdown/timeout source and authored placement changes without playback."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from extract_timeline_geometry import extract_frames, placement_delta

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(workspace: Path) -> dict:
    xml = workspace / "main.xml"
    report = json.loads((workspace / "export-report.json").read_text())
    bundle_path = ROOT / "scripts/main.json"
    bundle = json.loads(bundle_path.read_text())
    source_hash = sha(ROOT / "game/main.swf")
    assert report["source"]["sha256"] == bundle["swf_sha256"] == source_hash
    assert sha(xml) == next(r["sha256"] for r in report["files"] if r["path"] == "main.xml")
    sources = {s["path"]: s["source"] for s in bundle["scripts"]}
    timer_paths = [p for p, s in sources.items() if "setInterval(time,1000)" in s]
    assert len(timer_paths) == 1
    timer_id = int(re.match(r"DefineSprite_(\d+)/", timer_paths[0])[1])
    tree = ET.parse(xml).getroot()
    tags = tree.findall("./tags/item")
    timeout_places = [t for t in tags if t.get("name") == "timeover"]
    assert len(timeout_places) == 1
    timeout_id = placement_delta(timeout_places[0])["character_id"]
    timelines = {}
    ids = {timer_id, timeout_id}
    pending = sorted(ids)
    while pending:
        symbol = pending.pop(0)
        timeline = extract_frames(xml, symbol)
        children = {d["character_id"] for d in timeline["definitions"] if d["type"] == "DefineSpriteTag"}
        pending.extend(sorted(children - ids))
        ids.update(children)
        timelines[str(symbol)] = {
            "frame_count": timeline["frame_count"],
            "frames": [{k: f[k] for k in ("frame", "labels", "changes", "events")} for f in timeline["frames"]],
        }
    scripts = []
    for path, source in sources.items():
        match = re.match(r"DefineSprite_(\d+)/", path)
        if match and int(match[1]) in ids:
            scripts.append({"path": path, "source": source, "sha256": hashlib.sha256(source.encode()).hexdigest()})
    placements = []
    frame = 1
    for tag in tags:
        if tag.get("type") == "ShowFrameTag":
            frame += 1
        elif tag.get("characterId") in {str(timer_id), str(timeout_id)}:
            placements.append({"frame": frame, **placement_delta(tag)})
    owners = {"root": tags}
    owners.update({t.get("spriteId"): list(t.find("subTags")) for t in tags if t.get("type") == "DefineSpriteTag"})
    ancestors = {str(timer_id), str(timeout_id)}
    while True:
        found = {owner for owner, owner_tags in owners.items()
                 if owner not in ancestors and any(t.get("characterId") in ancestors for t in owner_tags)}
        if not found:
            break
        ancestors.update(found)
    edges = []
    for owner, owner_tags in owners.items():
        depths = {t.get("depth") for t in owner_tags if t.get("characterId") in ancestors}
        if not depths:
            continue
        frame = 1
        changes = []
        for tag in owner_tags:
            if tag.get("type") == "ShowFrameTag":
                frame += 1
            elif tag.get("depth") in depths:
                changes.append({"frame": frame, "attributes": dict(tag.attrib)})
        edges.append({"owner": owner, "changes": changes})
    ancestor_scripts = [{"path": p, "source": s, "sha256": hashlib.sha256(s.encode()).hexdigest()}
                        for p, s in sources.items()
                        if (m := re.match(r"DefineSprite_(\d+)/", p)) and m[1] in ancestors - {str(i) for i in ids}]
    return {
        "status": "source_inventory_not_runtime_acceptance",
        "source_swf_sha256": source_hash,
        "bundle_sha256": sha(bundle_path),
        "xml_sha256": sha(xml),
        "timer_sprite_id": timer_id,
        "timeout_sprite_id": timeout_id,
        "root_placements": placements,
        "ancestor_depth_changes": edges,
        "ancestor_scripts": ancestor_scripts,
        "timelines": timelines,
        "scripts": scripts,
        "limits": [
            "Ancestor depth changes are linear source evidence; jump/loop preservation still requires comparison.",
            "Timer callback phase requires full match observation; lexical writes are covered by timer-scope probe.",
            "No complete-match input/random/clock comparison is established by this inventory.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = ROOT / "evidence/ai/match-timeout-source.json"
    encoded = json.dumps(build(args.workspace), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert output.read_text() == encoded, "Timeout source inventory is stale"
    else:
        output.write_text(encoded)
