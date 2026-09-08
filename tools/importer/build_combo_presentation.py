"""Materialize the original combo board and its root placements."""
import argparse
import json
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

from extract_timeline_geometry import extract_frames, placement_delta, file_sha256
from materialize_timeline_assets import materialize


def build(workspace: Path, output: Path) -> None:
    xml = workspace / 'main.xml'
    timeline = extract_frames(xml, 1833)
    timeline.pop('wrapper', None)
    root = ET.parse(xml).getroot()
    timeline['boards'] = {
        tag.attrib['name']: placement_delta(tag)
        for tag in root.findall('./tags/item')
        if tag.attrib.get('name') in ('p1hits', 'p2hits')
    }
    if len(timeline['boards']) != 2:
        raise ValueError('Missing source combo board placements')
    timeline['source_swf'] = {'path': 'game/main.swf', 'sha256': file_sha256(Path('game/main.swf'))}
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bvn-combo-') as temporary:
        path = Path(temporary) / 'timeline.json'
        path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + '\n')
        materialize(workspace, path, output, None, None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.output)
