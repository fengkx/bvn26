#!/usr/bin/env python3
"""Exercise the shipped filter/cache placements through the raw-tag component harness."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def inventory(*, raster_input_only: bool = False) -> list[dict]:
    sites = json.loads((ROOT / 'evidence/importer-loud-fail/shipped-filters.json').read_text())
    sites.append({'swf': 'game/fighter/fz/jinye.swf', 'sprite': 0, 'frame': 41, 'depth': 1})
    rows = []
    for site in sites:
        stem = Path(site['swf']).stem
        path = (ROOT / ('godot/generated/effects/XG_mfdjx/timeline.json' if stem == 'main' else
                       f'godot/generated/{"helpers" if stem == "jinye" else "fighters"}/{stem}/timeline.json'))
        data = json.loads(path.read_text())
        owner, frame, depth = int(site['sprite']), int(site['frame']), int(site['depth'])
        definitions = {d['character_id']: d for d in data['definitions']}
        placements = (next(f['display_list'] for f in data['frames'] if f['frame'] == frame)
                      if owner == data['sprite_id'] else definitions[owner]['display_list_frames'][frame - 1])
        placement = next(p for p in placements if p['depth'] == depth)
        if not placement.get('filters') and not placement.get('cache_as_bitmap'):
            raise ValueError(f"{site['swf']}/sprite_{owner}/frame_{frame}/depth_{depth}: missing filter/cache")
        digest = hashlib.sha256((ROOT / site['swf']).read_bytes()).hexdigest()
        if digest != data['source_swf']['sha256']:
            raise ValueError('Timeline source hash mismatch: ' + str(path))
        count = definitions[placement['character_id']].get('frame_count', 1)
        rows.append({'id': f'{stem}-{owner}-{frame}-{depth}', 'kind': 'blend',
                     'source': {'path': site['swf'], 'sha256': digest},
                     'timeline': path.relative_to(ROOT).as_posix(), 'symbol': placement['character_id'],
                     'owner': owner, 'source_frame': frame, 'placement': placement,
                     'source_frame_count': count, 'frame_count': min(count, 100)})
        if raster_input_only:
            rows[-1]['raster_input_only'] = True
            rows[-1]['placement'] = {k: v for k, v in placement.items()
                                     if k not in ('filters', 'cache_as_bitmap')}
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--raster-input-only', action='store_true',
                        help='Diagnostic only: remove the tested outer filter/cache in both players')
    args = parser.parse_args()
    output = args.output.resolve()
    for locked in (ROOT / 'game', ROOT / 'scripts'):
        if output == locked or locked in output.parents:
            raise ValueError(f'Component output cannot overwrite locked input: {output}')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'inventory.json').write_text(json.dumps(inventory(raster_input_only=args.raster_input_only), ensure_ascii=False, indent=2) + '\n')
    env = {**os.environ, 'BVN_REVIEW_DIR': str(output), 'BVN_FFDEC': str(args.ffdec.resolve()),
           'JAVA_TOOL_OPTIONS': f'-Duser.home={output}'}
    subprocess.run([sys.executable, str(ROOT / 'evidence/characters/pain/visual-parity/review/probes/build_components.py')],
                   cwd=ROOT, env=env, check=True)
