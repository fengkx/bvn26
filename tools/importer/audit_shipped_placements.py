"""Check every shipped timeline and retain all locked-source placement blockers.

A source error outside shipped closures is still unresolved, not harmless. This
report separates closure acceptance from the complete source inventory.
"""
import argparse
import json
from pathlib import Path

from placement_build_guard import validate_build_placements
from visual_blend_modes import validate_timeline_blends
from visual_control_guard import validate_build_controls

ROOT = Path(__file__).resolve().parents[2]


def retains(timeline: dict, sprite: int, frame: int) -> bool:
    if sprite == timeline['sprite_id']:
        return any(f['frame'] == frame for f in timeline['frames'])
    return any(d['type'] == 'DefineSpriteTag' and d['character_id'] == sprite
               for d in timeline['definitions'])


def audit() -> dict:
    catalog = json.loads(Path(__file__).with_name('placement_requirements.json').read_text())
    xml_sources = json.loads(Path(__file__).with_name('visual_control_requirements.json').read_text())['_xml_sources']
    checks, closures = [], []
    for path in sorted((ROOT / 'godot/generated').rglob('timeline.json')):
        timeline = json.loads(path.read_text())
        relative = str(path.relative_to(ROOT))
        digest = timeline.get('source_swf', {}).get('sha256') or xml_sources.get(timeline.get('source_xml', {}).get('sha256'))
        closures.append((relative, digest, timeline))
        try:
            validate_timeline_blends(timeline, relative)
            validate_build_controls(timeline, relative)
            validate_build_placements(timeline, relative)
            checks.append({'path': relative, 'status': 'passed'})
        except ValueError as error:
            checks.append({'path': relative, 'status': 'failed', 'error': str(error)})
    issues = []
    for digest, entry in catalog.items():
        for record in entry['records']:
            issues.append({**record, 'swf_sha256': digest, 'status': 'unsupported_hard_error',
                           'retained_by': [path for path, source, timeline in closures
                                           if source == digest and retains(timeline, record['sprite'], record['frame'])]})
    return {'timelines': checks, 'locked_source_issues': issues}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    failures = sum(row['status'] != 'passed' for row in result['timelines'])
    print(json.dumps({'shipped_passed': len(result['timelines']) - failures,
                      'shipped_failed': failures, 'source_issues': len(result['locked_source_issues'])}))
    raise SystemExit(1 if failures or result['locked_source_issues'] else 0)
