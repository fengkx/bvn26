#!/usr/bin/env python3
"""Refresh audited frame calls and their parent initial values; preserve other cached fields."""
import argparse
import json
from pathlib import Path

from compile_ai_context import compile_context
from frame_call_guard import validate_cached_frame_calls

ROOT = Path(__file__).resolve().parents[2]


def refresh(write: bool = False) -> list[dict]:
    rows = []
    for timeline_path in sorted((ROOT / 'godot/generated/fighters').glob('*/timeline.json')):
        timeline = json.loads(timeline_path.read_text())
        source = timeline['source_swf']['path']
        bundle = json.loads((ROOT / (source.replace('game/', 'scripts/', 1).removesuffix('.swf') + '.json')).read_text())
        path = timeline_path.with_name('ai.json')
        previous = json.loads(path.read_text())
        row = {'source': source, 'path': str(path.relative_to(ROOT))}
        try:
            compiled = compile_context(bundle, timeline)
            if any(previous.get(k) != compiled[k] for k in ('source_swf', 'sprite_id')):
                raise ValueError(f'{source}: cached context source identity mismatch')
            updated = {**previous, 'frame_calls': compiled['frame_calls']}
            if compiled.get('parent_initial_values'):
                updated['parent_initial_values'] = compiled['parent_initial_values']
            else:
                updated.pop('parent_initial_values', None)
            validate_cached_frame_calls(timeline, updated)
            row.update(status='passed', changed=updated != previous,
                       deferred_fields=[k for k in compiled if k not in ('frame_calls', 'parent_initial_values') and compiled[k] != previous.get(k)])
            if write and updated != previous:
                path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
        except ValueError as error:
            row.update(status='failed', error=str(error))
        rows.append(row)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-successful', action='store_true', help='Explicitly write only contexts whose compile and build guards pass.')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    rows = refresh(args.write_successful)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': sum(r['status'] == 'passed' for r in rows), 'failed': sum(r['status'] == 'failed' for r in rows)}))
    raise SystemExit(1 if any(r['status'] == 'failed' for r in rows) else 0)
