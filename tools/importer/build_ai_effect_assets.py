"""Materialize source effects whose only script operation is unloadMovie."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

from extract_timeline_geometry import extract_frames
from materialize_timeline_assets import materialize

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(workspace: Path, clip: str, output: Path) -> None:
    report = json.loads((workspace / "export-report.json").read_text())
    xml = workspace / "main.xml"
    bundle = json.loads((ROOT / "scripts/main.json").read_text())
    source_hash = sha(ROOT / "game/main.swf")
    assert report["source"]["sha256"] == bundle["swf_sha256"] == source_hash
    records = {f["path"]: f["sha256"] for f in report["files"]}
    assert sha(xml) == records["main.xml"]
    exports = {}
    for tag in ET.parse(xml).getroot().findall("./tags/item"):
        if tag.get("type") == "ExportAssetsTag":
            exports.update(zip([v.text for v in tag.findall("./names/item")],
                               [int(v.text) for v in tag.findall("./tags/item")]))
    symbol = exports[clip]
    timeline = extract_frames(xml, symbol)
    timeline["source_swf"] = {"path": "game/main.swf", "sha256": source_hash}
    events = []
    prefix = f"DefineSprite_{symbol}_{clip}/"
    for script in bundle["scripts"]:
        if not script["path"].startswith(prefix):
            continue
        match = re.fullmatch(re.escape(prefix) + r"frame_(\d+)/DoAction.as", script["path"])
        if not match or script["source"].strip() != "this.unloadMovie();":
            raise ValueError("Unsupported effect script: " + script["path"])
        events.append({"frame": int(match[1]), "op": "unload", "source_path": script["path"],
                       "source_sha256": hashlib.sha256(script["source"].encode()).hexdigest()})
    if len(events) != 1:
        raise ValueError("Expected one explicit unload event")
    if any(d["type"] == "DefineSpriteTag" for d in timeline["definitions"]):
        raise ValueError("Nested effect timelines need a separate script audit")
    with tempfile.TemporaryDirectory(prefix="bvn-ai-effect-") as directory:
        path = Path(directory) / "timeline.json"
        path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n")
        assets = materialize(workspace, path, output)
    for asset in assets["assets"]:
        assert records[asset["materialized_source"]] == asset["sha256"]
    assets["timeline"]["path"] = "timeline.json"
    (output / "assets.json").write_text(json.dumps(assets, indent=2) + "\n")
    (output / "effect.json").write_text(json.dumps({"format": "bvn26-simple-effect-v1",
        "clip": clip, "sprite_id": symbol, "presentation_events": events,
        "source_swf": timeline["source_swf"]}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.clip, args.output)
