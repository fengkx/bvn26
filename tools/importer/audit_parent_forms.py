"""Attempt real target-body compilation; report guards that block parent switching.

Successful context compilation is not a complete form port or runtime acceptance.
All large exports live in a temporary directory and are removed after the audit.
"""
import argparse
import json
from pathlib import Path
import tempfile

from compile_ai_context import compile_context
from export_swf_xml import export_swf
from extract_timeline_geometry import extract_frames
from visual_control_guard import validate_nested_controls

ROOT = Path(__file__).resolve().parents[2]


def audit(requirements: list[dict], ffdec: Path) -> list[dict]:
    rows = []
    with tempfile.TemporaryDirectory(prefix='bvn-parent-forms-') as temporary:
        for requirement in requirements:
            source = ROOT / requirement['source']
            work = Path(temporary) / source.stem
            row = {'source': requirement['source'], 'target_body_sprite': requirement['target_body_sprite']}
            try:
                export_swf(ffdec, source, work)
                timeline = extract_frames(work / (source.stem + '.xml'), requirement['target_body_sprite'])
                timeline['source_swf'] = {'path': requirement['source'], 'sha256': requirement['source_swf_sha256']}
                bundle = json.loads((ROOT / requirement['source'].replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
                validate_nested_controls(timeline, bundle)
                context = compile_context(bundle, timeline)
                row.update(status='context_compiled', frames=len(timeline['frames']), frame_calls=len(context['frame_calls']))
            except (ValueError, AssertionError) as error:
                row.update(status='failed', error=str(error))
            rows.append(row)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requirements', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = audit(json.loads(args.requirements.read_text()), args.ffdec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'compiled_contexts': sum(r['status'] == 'context_compiled' for r in rows), 'total': len(rows)}))
    raise SystemExit(1 if any(r['status'] != 'context_compiled' for r in rows) else 0)
