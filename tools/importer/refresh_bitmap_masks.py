"""Refresh only bitmap masks from pinned SWF XML, retaining timeline semantics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from export_swf_xml import EXPECTED_GENERATOR, file_sha256
from extract_timeline_geometry import extract_frames

MASK_FIELDS = ('bitmap_clip_polygon', 'bitmap_clip_polygons')


def refresh(timeline_path: Path, workspace: Path) -> dict:
    timeline = json.loads(timeline_path.read_text())
    source = timeline['source_swf']
    if file_sha256(Path(source['path'])) != source['sha256']:
        raise ValueError(f'Locked SWF mismatch: {source["path"]}')
    xml_path = workspace / Path(source['path']).stem / timeline['source_xml']['name']
    if ET.parse(xml_path).getroot().get('_generator') != EXPECTED_GENERATOR:
        raise ValueError(f'Unpinned XML generator: {xml_path}')
    fresh = extract_frames(xml_path, timeline['sprite_id'])
    definitions = {item['character_id']: item for item in fresh['definitions']}
    changed = []
    for old in timeline['definitions']:
        new = definitions[old['character_id']]
        # Older artifacts lack unrelated sound/frame-event fields. Updating
        # masks must not silently migrate scheduling or solid-fill behavior.
        for key in ('type', 'shape_bounds_twips', 'bitmap_fills'):
            if old.get(key) != new.get(key):
                raise ValueError(f'Source geometry mismatch: {timeline_path}:{old["character_id"]}:{key}')
        if all(old.get(key) == new.get(key) for key in MASK_FIELDS):
            continue
        changed.append(old['character_id'])
        for key in MASK_FIELDS:
            old.pop(key, None)
            if key in new:
                old[key] = new[key]
    if changed:
        timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + '\n')
    return {
        'path': timeline_path.as_posix(),
        'source_swf': source,
        'original_source_xml': timeline['source_xml'],
        'mask_source_xml': fresh['source_xml'],
        'changed_shape_ids': changed,
        'sha256': file_sha256(timeline_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('timelines', type=Path, nargs='+')
    args = parser.parse_args()
    reports = [refresh(path, args.workspace) for path in args.timelines]
    args.report.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
    print(f'Refreshed {len(reports)} timelines; changed {sum(len(r["changed_shape_ids"]) for r in reports)} shapes')


if __name__ == '__main__':
    main()
