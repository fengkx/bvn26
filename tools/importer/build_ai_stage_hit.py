"""Materialize the original burst timeline and its explicit removal event."""
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


def build(workspace: Path, output: Path) -> dict:
    report = json.loads((workspace / 'export-report.json').read_text())
    xml = workspace / 'main.xml'
    bundle = json.loads((ROOT / 'scripts/main.json').read_text())
    source_hash = sha(ROOT / 'game/main.swf')
    if report['source']['sha256'] != source_hash or bundle['swf_sha256'] != source_hash:
        raise ValueError('Stage effect inputs do not share the retained main SWF')
    xml_record = next(f for f in report['files'] if f['path'] == 'main.xml')
    if sha(xml) != xml_record['sha256']:
        raise ValueError('Stage effect XML differs from the export report')
    exports = {}
    for tag in ET.parse(xml).getroot().findall('./tags/item'):
        if tag.get('type') == 'ExportAssetsTag':
            exports.update(zip([v.text for v in tag.findall('./names/item')],
                               [int(v.text) for v in tag.findall('./tags/item')]))
    symbol = exports['XG_baoqi']
    timeline = extract_frames(xml, symbol)
    timeline['source_swf'] = {'path': 'game/main.swf', 'sha256': source_hash}
    root_scripts = [s for s in bundle['scripts'] if s['path'].startswith(f'DefineSprite_{symbol}_XG_baoqi/')]
    removal = []
    for script in root_scripts:
        match = re.fullmatch(rf'DefineSprite_{symbol}_XG_baoqi/frame_(\d+)/DoAction.as', script['path'])
        if not match or script['source'].replace('\r\n', '\n').strip() != 'this.unloadMovie();\nthis.removeMovieClip();':
            raise ValueError('Uncompiled burst script: ' + script['path'])
        removal.append({'frame': int(match[1]), 'path': script['path']})
    if len(removal) != 1:
        raise ValueError('Expected one burst removal event')
    active = [f['frame'] for f in timeline['frames'] if any(p.get('name') == 'mian' for p in f['display_list'])]
    frame8 = next(s['source'] for s in bundle['scripts'] if s['path'] == 'frame_8/DoAction.as').replace('\r\n', '\n')
    spawn = re.search(r'^function addStgHit\([^\n]*\)\n\{.*?^\}', frame8, re.M | re.S)[0]
    counter = re.search(r'^var stgi = (\d+);', frame8, re.M)
    wrap = re.search(r'if\(stgi > (\d+)\)\s*\{\s*stgi = (\d+);', spawn)
    naming = re.search(r'var _loc6_ = "([^"]+)" \+ stgi \+ "([^"]+)" \+ _loc4_;', spawn)
    if not counter or not wrap or not naming or 'stgi++;' not in spawn or spawn.index(wrap[0]) < spawn.index('attachMovie('):
        raise ValueError('Unsupported stage-hit counter or name construction')
    receiver = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
    receiver_source = next(s['source'] for s in receiver['scripts'] if s['path'] == 'DefineSprite_2/frame_1/DoAction.as')
    prefixes = json.loads(re.search(r'var stgks = (\[[^;]+\]);', receiver_source)[1])
    spec = {'format': 'bvn26-stage-hit-v1', 'status': 'source_compiled_partial',
            'clip': 'XG_baoqi', 'hit_instance': 'mian', 'remove': removal[0],
            'active_frames': active, 'source_swf': timeline['source_swf'],
            'source_xml': timeline['source_xml'], 'spawn_path': 'frame_8/DoAction.as#addStgHit',
            'registry': {'initial_counter': int(counter[1]), 'wrap_after': int(wrap[1]),
                         'wrap_to': int(wrap[2]), 'name_prefix': naming[1], 'owner_separator': naming[2],
                         'lookup_prefixes': prefixes, 'lookup_path': 'scripts/fighter/yihu.json#DefineSprite_2/frame_1/DoAction.as#getStgHitObj'},
            'limits': 'Registry naming, candidate ordering and complete battle comparison remain separate.'}
    with tempfile.TemporaryDirectory(prefix='bvn-stage-hit-') as directory:
        path = Path(directory) / 'burst.timeline.json'
        path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + '\n')
        assets = materialize(workspace, path, output)
    source_assets = {f['path']: f['sha256'] for f in report['files']}
    for asset in assets['assets']:
        if source_assets.get(asset['materialized_source']) != asset['sha256']:
            raise ValueError('Stage effect asset differs from the export report: ' + asset['path'])
    # Keep the delivered manifest reproducible; the temporary source has been
    # copied byte-for-byte into the package and is no longer an input path.
    assets['timeline']['path'] = 'timeline.json'
    (output / 'assets.json').write_text(json.dumps(assets, indent=2) + '\n')
    (output / 'stage_hit.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
    return spec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.workspace, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
