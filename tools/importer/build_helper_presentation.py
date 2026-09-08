"""Compile stage depths and the original MP-bar helper portraits from pinned XML."""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from extract_timeline_geometry import extract_frames, file_sha256
from materialize_timeline_assets import materialize


def polygon(shape: ET.Element) -> list[list[float]]:
    points = []
    x = y = 0
    for record in shape.findall('./shapes/shapeRecords/item'):
        kind = record.get('type')
        if kind == 'StyleChangeRecord' and record.get('stateMoveTo') == 'true':
            x, y = int(record.get('moveDeltaX')), int(record.get('moveDeltaY'))
            points.append([x / 20, y / 20])
        elif kind == 'StraightEdgeRecord':
            x += int(record.get('deltaX', 0))
            y += int(record.get('deltaY', 0))
            points.append([x / 20, y / 20])
        elif kind == 'CurvedEdgeRecord':
            raise ValueError('Curved portrait mask needs a curve compiler')
    return points


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    xml = args.workspace / 'main.xml'
    root = ET.parse(xml).getroot()
    sprites = {int(t.get('spriteId')): t for t in root.iter('item') if t.get('type') == 'DefineSpriteTag'}
    shapes = {int(t.get('shapeId')): t for t in root.iter('item') if t.get('shapeId')}
    # Use the existing extractor/materializer, including JPEG3 alpha, for tx.
    timeline_path = args.workspace / "helper-portrait.timeline.json"
    timeline = extract_frames(xml, 1753)
    timeline["source_swf"] = {
        "path": "game/main.swf",
        "sha256": file_sha256(Path("game/main.swf")),
    }
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n")
    report = materialize(args.workspace, timeline_path, args.output_dir, None, None)
    timeline = json.loads(timeline_path.read_text())
    definitions = {d['character_id']: d for d in timeline['definitions']}
    assets = {a['character_id']: a['path'] for a in report['assets']}
    frame = 1
    labels = {}
    for tag in sprites[1465].find('subTags'):
        if tag.get('type') == 'FrameLabelTag':
            labels[tag.get('name')] = frame
        elif tag.get('type') == 'ShowFrameTag':
            frame += 1
    portraits = {}
    for label, frame in labels.items():
        placement = definitions[1465]['display_list_frames'][frame - 1][0]
        shape = definitions[placement['character_id']]
        fill = next(f for f in shape['bitmap_fills'] if f['bitmap_id'] in assets)
        portraits[label] = {'texture': assets[fill['bitmap_id']], 'matrix': fill['matrix'], 'frame': frame}
    tx = next(p for p in timeline['frames'][0]['display_list'] if p.get('name') == 'namemc')
    border = next(f for f in definitions[1750]['bitmap_fills'] if f['bitmap_id'] in assets)
    line = shapes[1752].find('./shapes/lineStyles/lineStyles2/item')
    depths = {t.get('name'): int(t.get('depth')) for t in sprites[1738].find('subTags') if t.get('name') in ['p1', 'p2', 'p1fz', 'p2fz', 'layer_effect']}
    spec = {
        "source_swf_sha256": file_sha256(Path("game/main.swf")),
        "stage_sprite": 1738,
        "depths": depths,
        "portrait_sprite": 1753,
        "portrait_matrix": tx["matrix"],
        "mask": polygon(shapes[1751]),
        "outline": polygon(shapes[1752]),
        "outline_width": int(line.get("width")) / 20,
        "outline_color": [
            int(line.find("color").get(k)) / 255
            for k in ["red", "green", "blue", "alpha"]
        ],
        "border": {"texture": assets[border["bitmap_id"]], "matrix": border["matrix"]},
        "portraits": portraits,
    }
    (args.output_dir / 'presentation.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
