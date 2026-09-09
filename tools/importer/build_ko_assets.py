"""Import the authored KO display list and retain its complete script audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

from extract_timeline_geometry import extract_frames, placement_delta
from materialize_timeline_assets import materialize

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(workspace: Path, output: Path, evidence: Path, instance_name: str = "KO") -> None:
    report = json.loads((workspace / "export-report.json").read_text())
    records = {f["path"]: f["sha256"] for f in report["files"]}
    xml = workspace / "main.xml"
    bundle = json.loads((ROOT / "scripts/main.json").read_text())
    swf_hash = sha(ROOT / "game/main.swf")
    assert report["source"]["sha256"] == bundle["swf_sha256"] == swf_hash
    assert sha(xml) == records["main.xml"]
    placements = [tag for tag in ET.parse(xml).getroot().findall("./tags/item") if tag.get("name") == instance_name]
    assert len(placements) == 1
    placement = placement_delta(placements[0])
    symbol = placement["character_id"]
    timeline = extract_frames(xml, symbol)
    timeline.pop("wrapper", None)
    timeline["source_swf"] = {"path": "game/main.swf", "sha256": swf_hash}
    ids = {symbol} | {d["character_id"] for d in timeline["definitions"] if d["type"] == "DefineSpriteTag"}
    scripts = []
    for script in bundle["scripts"]:
        match = re.match(r"DefineSprite_(\d+)/", script["path"])
        if match and int(match[1]) in ids:
            scripts.append({**script, "sha256": hashlib.sha256(script["source"].encode()).hexdigest()})
    with tempfile.TemporaryDirectory(prefix="bvn-ko-assets-") as directory:
        path = Path(directory) / "timeline.json"
        path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n")
        assets = materialize(workspace, path, output)
    for asset in assets["assets"]:
        assert asset["sha256"] == records[asset["materialized_source"]]
    assets["timeline"]["path"] = "timeline.json"
    (output / "assets.json").write_text(json.dumps(assets, indent=2) + "\n")
    metadata = {"format": "bvn26-ko-assets-v1", "status": "assets_only_not_behavior_compiled",
                "placement": placement, "sprite_ids": sorted(ids),
                "labels": {label: f["frame"] for f in timeline["frames"] for label in f["labels"]},
                "source_swf": timeline["source_swf"]}
    (output / "ko.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    evidence.write_text(json.dumps({**metadata, "source_xml": timeline["source_xml"],
        "scripts": scripts, "assets": assets["assets"]}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.output, args.evidence)
