"""Compare prior packages under the base and current expression compilers."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/importer'))
import compile_ai_predicates as predicates
import compile_ai_body as body
import compile_ai_controller as controller
import compile_ai_context as context
import build_combat_model as combat


def original(name):
    path = 'tools/importer/' + name + '.py'
    module = types.ModuleType('baseline_' + name)
    module.__file__ = str(ROOT / path)
    exec(compile(subprocess.check_output(['git', 'show', 'e7876e6f:' + path]), str(ROOT / path), 'exec'), module.__dict__)
    return module


def run():
    previous_predicates = original('compile_ai_predicates')
    previous_context = original('compile_ai_context')
    previous_combat = original('build_combat_model')
    current_normalize = predicates.normalize
    current_calls = context.conditional_frame_calls
    results = []
    directories = sorted((ROOT / 'godot/generated/fighters').iterdir()) + sorted((ROOT / 'godot/generated/forms').iterdir())
    for directory in directories:
        if directory.name.startswith('kenshin') or not (directory / 'timeline.json').is_file():
            continue
        timeline = json.loads((directory / 'timeline.json').read_text())
        source = timeline['source_swf']['path']
        bundle = json.loads((ROOT / source.replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
        form = directory.parent.name == 'forms' or (directory / 'form_profiles.json').is_file()
        versions = []
        for baseline in (True, False):
            predicates.normalize = previous_predicates.normalize if baseline else current_normalize
            body.normalize = predicates.normalize
            context.conditional_frame_calls = previous_context.conditional_frame_calls if baseline else current_calls
            previous_context.parse_body_warp = previous_combat.parse_body_warp
            products = {}
            for key, operation in {
                'context': lambda: (previous_context if baseline else context).compile_context(bundle, timeline, form_replacement=form),
                'combat_warps': lambda: [(x['path'], (previous_combat if baseline else combat).parse_body_warp(x['source'])) for x in bundle['scripts'] if '_parent._x' in x['source']],
                'body': lambda: body.compile_player_body(bundle, timeline['sprite_id'], timeline, form_helpers=form),
                'controller': lambda: controller.compile_controller(bundle, timeline['sprite_id'], timeline, player=True, form_replacement=form),
            }.items():
                try:
                    products[key] = {'sha256': hashlib.sha256(json.dumps(operation(), sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
                except (ValueError, SyntaxError, KeyError) as error:
                    products[key] = {'error': str(error)}
            versions.append(products)
        results.append({'directory': str(directory.relative_to(ROOT)), 'unchanged': versions[0] == versions[1],
                        'base': versions[0], 'current': versions[1]})
    output = {'status': 'unchanged' if all(r['unchanged'] for r in results) else 'changed', 'packages': results}
    (Path(__file__).parent / 'compiler-impact.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': output['status'], 'packages': len(results)}))
    return 0 if output['status'] == 'unchanged' else 1


if __name__ == '__main__':
    raise SystemExit(run())
