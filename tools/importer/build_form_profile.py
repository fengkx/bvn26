"""Complete an isolated replacement profile from source-checked staging products.

The output is a candidate asset/compiler package, not permission to publish a
form. Runtime integration and source-native replay remain separate acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_ai import functions
from compile_ai_body import compile_body, compile_player_body
from compile_ai_context import compile_context
from compile_ai_controller import compile_controller
from compile_ai_predicates import compile_source, controller_script


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def voice_spec(bundle, sprite, base):
    spec = json.loads((base / 'hurt_voice.json').read_text())
    path = f'DefineSprite_{sprite}/frame_1/DoAction.as'
    source = next(r['source'] for r in bundle['scripts'] if r['path'] == path)
    voice = functions(source)['hurtVoice']
    if hashlib.sha256(voice.encode()).hexdigest() != spec['source_sha256']:
        raise ValueError(f"{bundle['game_file']}:{path}#hurtVoice: uncompiled replacement voice")
    for name, digest in spec['linkages_absent_in'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'{name}: voice linkage inventory changed')
    spec['source_path'] = path
    for key, site in spec['clock_sites'].items():
        spec['clock_sites'][key] = site.split('#')[0] + '#' + path + '#' + site.split('#', 2)[2]
    ordinal = source[:source.index(voice) + voice.index('Math.random()')].count('Math.random()') + 1
    spec['probability_site'] = spec['probability_site'].split('#')[0] + '#' + path + ':' + str(ordinal)
    # onBeHit's threshold/probability are separate from hurtVoice itself.
    base_body = json.loads((base / 'timeline.json').read_text())['sprite_id']
    base_source = next(r['source'] for r in bundle['scripts'] if r['path'] == f'DefineSprite_{base_body}/frame_1/DoAction.as')
    import re
    for pattern in (r'jhp <= (\d+) \? ([\d.]+) : ([\d.]+)', r'var _loc4_ = ([\d.]+);'):
        target = re.search(pattern, functions(source)['onBeHit'])
        original = re.search(pattern, functions(base_source)['onBeHit'])
        if target is None or original is None or target.groups() != original.groups():
            raise ValueError(f"{bundle['game_file']}:{path}#onBeHit: changed voice probability")
    return spec


def compile_programs(directory, bundle, timeline):
    sprite = timeline['sprite_id']
    write(directory / 'ai.json', compile_context(bundle, timeline, form_replacement=True))
    for player in (False, True):
        target = directory / ('player_controller' if player else 'ai_controller')
        target.mkdir(exist_ok=True)
        code, meta = (compile_player_body(bundle, sprite, timeline, form_helpers=True) if player
                      else compile_body(bundle, sprite, form_helpers=True))
        (target / 'body.gd').write_text(code)
        write(target / 'body.json', meta)
        code, meta = compile_controller(bundle, sprite, timeline, player=player, form_replacement=True)
        meta['input_mode'] = 'player' if player else 'cpu'
        (target / 'controller.gd').write_text(code)
        write(target / 'controller.json', meta)
        (target / 'predicates.gd').write_text(compile_source(controller_script(bundle, sprite)['source'], player=player))


def build(staged, base, output, ffdec, ffmpeg):
    output.mkdir(parents=True, exist_ok=False)
    timeline = json.loads((staged / 'timeline.json').read_text())
    source = timeline['source_swf']['path']
    bundle = json.loads((ROOT / source.replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
    if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != timeline['source_swf']['sha256']:
        raise ValueError(f'{source}: stale replacement timeline')
    shutil.copytree(staged / 'visual', output, dirs_exist_ok=True)
    for name in ('ai_hit_state.gd', 'ai_hit_state.json'):
        shutil.copyfile(staged / name, output / name)
    # Materialized timeline keeps source-independent internal anonymous handles.
    runtime_timeline = json.loads((output / 'timeline.json').read_text())
    compile_programs(output, bundle, runtime_timeline)
    write(output / 'hurt_voice.json', voice_spec(bundle, timeline['sprite_id'], base))
    subprocess.run([sys.executable, str(ROOT / 'tools/importer/build_sound_segments.py'),
                    '--directory', str(output), '--ffdec', str(ffdec), '--ffmpeg', str(ffmpeg)], check=True)
    write(output / 'candidate.json', {'status': 'requires_runtime_native_acceptance', 'source_swf': timeline['source_swf']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('staged', 'base', 'output', 'ffdec', 'ffmpeg'):
        parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args()
    build(args.staged, args.base, args.output, args.ffdec, args.ffmpeg)
