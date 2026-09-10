"""Materialize source effects with root position writes and explicit unload."""
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
from compile_hit_receive import SHAKE_RE, SHINE_RE, _clip_events_for_prefix

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
        match = re.fullmatch(re.escape(prefix) + r"frame_(\d+)/DoAction(?:_\d+)?\.as", script["path"])
        remaining = re.sub(r"_root\." + SHINE_RE.pattern + r"\s*;", '',
                           SHAKE_RE.sub('', script['source'])).strip()
        if not match or remaining not in ['', 'this.unloadMovie();']:
            raise ValueError("Unsupported effect script: " + script["path"])
    events = _clip_events_for_prefix(bundle, prefix.rstrip('/'))
    unloads = [event for event in events if event['op'] == 'unload']
    if len(unloads) != 1:
        raise ValueError("Expected one explicit unload event")
    nested_ids = {d["character_id"] for d in timeline["definitions"] if d["type"] == "DefineSpriteTag"}
    nested_scripts = []
    for script in bundle["scripts"]:
        match = re.match(r"DefineSprite_(\d+)(?:_[^/]+)?/", script["path"])
        if not match or int(match[1]) not in nested_ids:
            continue
        terminal = re.fullmatch(r"DefineSprite_\d+(?:_[^/]+)?/frame_(\d+)/DoAction.as", script["path"])
        # The containing effect is removed before this child could play past
        # its stop frame. Earlier stops or other actions need a real scheduler.
        if not terminal or script["source"].strip() != "stop();" or int(terminal[1]) < unloads[0]["frame"]:
            raise ValueError("Unsupported nested effect script: " + script["path"])
        nested_scripts.append(script)

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
        "nested_terminal_scripts": nested_scripts,
        "source_swf": timeline["source_swf"]}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.clip, args.output)
