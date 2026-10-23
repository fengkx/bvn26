"""Stage source-bound replacement profiles without publishing incomplete forms.

Every compiler runs under its normal guards. Independent products are attempted
so a failed context does not conceal missing controller or visual dependencies.
A staged profile is never runtime acceptance or permission to enable a form jump.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from build_combat_model import build_model
from compile_ai_body import compile_body
from compile_ai_context import compile_context
from compile_ai_controller import compile_controller
from compile_ai_hit_state import compile_transfer
from compile_ai_predicates import compile_source, controller_script
from export_swf_xml import export_swf
from extract_fighter_slice import extract_slice
from extract_timeline_geometry import extract_frames
from materialize_timeline_assets import materialize
from parent_form_requirements import parent_form_requirement
from visual_control_guard import validate_nested_controls

ROOT = Path(__file__).resolve().parents[2]


def resolve_target(requirement: dict, root: Path = ROOT) -> tuple[str, dict]:
    source = requirement['source']
    path = root / source
    if not path.resolve().is_relative_to((root / 'game/fighter').resolve()):
        raise ValueError(f'Not a fighter source: {source}')
    bundle = json.loads((root / source.replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != bundle['swf_sha256'] or digest != requirement['source_swf_sha256']:
        raise ValueError(f'{source}: replacement source hash mismatch')
    current = parent_form_requirement(bundle, requirement['target_parent_frame'], source)
    for field, value in current.items():
        if json.dumps(requirement.get(field), sort_keys=True) != json.dumps(value, sort_keys=True):
            raise ValueError(f'{source}: stale replacement requirement {field}')
    catalog = json.loads((root / 'manifest.json').read_text())['fighter_catalog']
    keys = [key for key, row in catalog.items()
            if row.get('url') == path.name and row.get('WKframe', 1) == current['target_parent_frame']]
    if not keys:
        keys = [key for key, row in catalog.items()
                if row.get('url') == path.name and row.get('WKframe', 1) == 1]
    if len(keys) != 1:
        raise ValueError(f'{source}: parent frame {current["target_parent_frame"]} needs one catalog form, got {keys}')
    return keys[0], bundle


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def stage(requirements: list[dict], ffdec: Path, output: Path) -> list[dict]:
    # Refuse stale output rather than mixing partial products from different runs.
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for requirement in requirements:
        source = requirement['source']
        directory = output / f'{Path(source).stem}-{requirement["target_parent_frame"]}'
        directory.mkdir()
        row = {'source': source, 'target_body_sprite': requirement['target_body_sprite'],
               'target_parent_frame': requirement['target_parent_frame'], 'stages': {},
               'runtime_integrated': False}
        rows.append(row)

        def attempt(name, operation):
            try:
                result = operation()
            except (ValueError, AssertionError, FileNotFoundError, KeyError, SyntaxError) as error:
                row['stages'][name] = {'status': 'failed', 'error': f'{source}:target body {requirement["target_body_sprite"]}:{name}: {error}'}
                return None
            row['stages'][name] = {'status': 'compiled'}
            return result

        resolved = attempt('source', lambda: resolve_target(requirement))
        if resolved is None:
            row['status'] = 'blocked'
            write_json(output / 'report.json', rows)
            continue
        key, bundle = resolved
        row['fighter_key'] = key
        fighter = attempt('slice', lambda: extract_slice(ROOT, key, allow_forms=True, parent_frame=requirement['target_parent_frame']))
        if fighter is not None:
            if fighter['source']['timeline_symbol_id'] != requirement['target_body_sprite']:
                raise ValueError(f'{source}: target slice body does not match replacement requirement')
            write_json(directory / 'fighter.json', fighter)
        with tempfile.TemporaryDirectory(prefix='bvn-form-export-') as temporary:
            workspace = Path(temporary)
            export_swf(ffdec, ROOT / source, workspace)

            def timeline_product():
                timeline = extract_frames(workspace / (Path(source).stem + '.xml'), requirement['target_body_sprite'])
                timeline['source_swf'] = {'path': source, 'sha256': requirement['source_swf_sha256']}
                validate_nested_controls(timeline, bundle)
                write_json(directory / 'timeline.json', timeline)
                return timeline

            timeline = attempt('timeline', timeline_product)
            if timeline is not None:
                context = attempt('context', lambda: compile_context(bundle, timeline))
                if context is not None:
                    write_json(directory / 'ai.json', context)
                combat = None
                if fighter is not None:
                    combat = attempt('combat', lambda: build_model(
                        directory / 'fighter.json', directory / 'timeline.json',
                        ROOT / source.replace('game/', 'scripts/', 1).replace('.swf', '.json')))
                    if combat is not None:
                        write_json(directory / 'combat.json', combat)
                assets = attempt('assets', lambda: materialize(
                    workspace, directory / 'timeline.json', directory / 'visual',
                    directory / 'fighter.json' if fighter is not None else None,
                    directory / 'combat.json' if combat is not None else None))
                if assets is not None:
                    row['asset_count'] = len(assets['assets'])
                for player in (False, True):
                    mode = 'player' if player else 'cpu'

                    def controller_product():
                        code, metadata = compile_controller(bundle, timeline['sprite_id'], timeline, player=player)
                        predicates = compile_source(controller_script(bundle, timeline['sprite_id'])['source'], player=player)
                        target = directory / (mode + '_controller')
                        target.mkdir()
                        (target / 'controller.gd').write_text(code)
                        (target / 'predicates.gd').write_text(predicates)
                        write_json(target / 'controller.json', metadata)

                    attempt(mode + '_controller', controller_product)
            for player in (False, True):
                mode = 'player' if player else 'cpu'

                def body_product():
                    code, metadata = compile_body(bundle, requirement['target_body_sprite'], player=player)
                    target = directory / (mode + '_body')
                    target.mkdir()
                    (target / 'body.gd').write_text(code)
                    write_json(target / 'body.json', metadata)

                attempt(mode + '_body', body_product)
            hit = attempt('hit_state', lambda: compile_transfer(bundle))
            if hit is not None:
                (directory / 'ai_hit_state.gd').write_text(hit[0])
                write_json(directory / 'ai_hit_state.json', hit[1])
        row['status'] = ('blocked' if any(s['status'] == 'failed' for s in row['stages'].values())
                         else 'staged_not_integrated')
        row['files'] = [{'path': p.relative_to(directory).as_posix(),
                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                        for p in sorted(directory.rglob('*')) if p.is_file()]
        write_json(output / 'report.json', rows)
        print(json.dumps({k: v for k, v in row.items() if k != 'files'}, ensure_ascii=False), flush=True)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requirements', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = stage(json.loads(args.requirements.read_text()), args.ffdec, args.output)
    raise SystemExit(1 if any(r.get('status') != 'staged_not_integrated' for r in results) else 0)
