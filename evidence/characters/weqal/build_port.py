"""Build the source-bound Ulquiorra base package; acceptance is separate."""
import argparse
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from extract_fighter_slice import extract_slice
from extract_timeline_geometry import extract_frames
from visual_control_guard import validate_nested_controls
from build_combat_model import build_model
from materialize_timeline_assets import materialize
from compile_ai_context import compile_context
from compile_ai_body import compile_body, compile_player_body
from compile_ai_controller import compile_controller
from compile_ai_predicates import compile_source, controller_script
from compile_ai_hit_state import compile_transfer
from build_form_profile import voice_spec


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(workspace, ffdec, ffmpeg):
    bundle = json.loads((ROOT / 'scripts/fighter/weqal.json').read_text())
    fighter = extract_slice(ROOT, '小乌')
    sprite = fighter['source']['timeline_symbol_id']
    timeline = extract_frames(workspace / 'weqal.xml', sprite)
    timeline['source_swf'] = {'path': bundle['game_file'], 'sha256': bundle['swf_sha256']}
    validate_nested_controls(timeline, bundle)
    fp = Path('data/slices/weqal-base.json')
    tp = Path('data/slices/weqal-base.timeline.json')
    cp = Path('data/actions/weqal-base.json')
    fighter['source']['timeline_path'] = tp.as_posix()
    write(ROOT / fp, fighter)
    write(ROOT / tp, timeline)
    write(ROOT / cp, build_model(fp, tp, Path('scripts/fighter/weqal.json')))
    directory = ROOT / 'godot/generated/fighters/weqal'
    materialize(workspace, tp, directory, fp, cp)
    runtime_timeline = json.loads((directory / 'timeline.json').read_text())
    write(directory / 'ai.json', compile_context(bundle, runtime_timeline, form_replacement=True))
    for player in (False, True):
        target = directory / ('player_controller' if player else 'ai_controller')
        target.mkdir(exist_ok=True)
        code, meta = (compile_player_body(bundle, sprite, runtime_timeline, form_helpers=True) if player
                      else compile_body(bundle, sprite, form_helpers=True))
        (target / 'body.gd').write_text(code)
        write(target / 'body.json', meta)
        code, meta = compile_controller(bundle, sprite, runtime_timeline, player=player, form_replacement=True)
        meta['input_mode'] = 'player' if player else 'cpu'
        (target / 'controller.gd').write_text(code)
        write(target / 'controller.json', meta)
        (target / 'predicates.gd').write_text(compile_source(controller_script(bundle, sprite)['source'], player=player))
    code, meta = compile_transfer(bundle)
    (directory / 'ai_hit_state.gd').write_text(code)
    write(directory / 'ai_hit_state.json', meta)
    voice = json.loads((ROOT / 'godot/generated/fighters/yihu/hurt_voice.json').read_text())
    for key, site in voice['clock_sites'].items():
        voice['clock_sites'][key] = 'fighter/weqal#' + site.split('#', 1)[1]
    voice['probability_site'] = 'fighter/weqal#' + voice['probability_site'].split('#', 1)[1]
    write(directory / 'hurt_voice.json', voice)
    write(directory / 'hurt_voice.json', voice_spec(bundle, sprite, directory))
    subprocess.run([sys.executable, str(ROOT / 'tools/importer/build_sound_segments.py'),
                    '--directory', str(directory), '--ffdec', str(ffdec),
                    '--ffmpeg', str(ffmpeg)], check=True)
    write(ROOT / 'evidence/characters/weqal/source-first.json', {
        'source': timeline['source_swf'], 'sprite': sprite, 'wrapper': timeline.get('wrapper'),
        'frames': [{'frame': f['frame'], 'labels': f.get('labels', []),
                    'changes': f.get('changes', []),
                    'scripts': [s for s in bundle['scripts'] if s['path'].startswith(f'DefineSprite_{sprite}/frame_{f["frame"]}/')]}
                   for f in timeline['frames']],
        'native_reference_status': 'pending', 'form_variant': 'deferred'})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--ffdec', type=Path, required=True)
    p.add_argument('--ffmpeg', type=Path, required=True)
    args = p.parse_args()
    build(args.workspace, args.ffdec, args.ffmpeg)
