"""Build the isolated Temari candidate; compilation does not prove parity."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from extract_fighter_slice import extract_slice
from extract_timeline_geometry import extract_frames
from build_combat_model import build_model
from materialize_timeline_assets import materialize
from compile_ai_context import compile_context
from compile_ai_body import compile_body, compile_player_body
from compile_ai_controller import compile_controller
from compile_ai_predicates import compile_source, controller_script
from compile_ai_hit_state import compile_transfer
from compile_hurt_voice import build as build_voice


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(workspace, ffdec, ffmpeg):
    bundle = json.loads((ROOT / 'scripts/fighter/shouju.json').read_text())
    directory = ROOT / 'godot/generated/fighters/shouju'
    fighter = extract_slice(ROOT, '手鞠')
    sprite = fighter['source']['timeline_symbol_id']
    timeline = extract_frames(workspace / 'shouju.xml', sprite, wrapper_siblings=True)
    timeline['source_swf'] = {'path': bundle['game_file'], 'sha256': bundle['swf_sha256']}
    fighter_path = Path('data/slices/shouju-base.json')
    timeline_path = Path('data/slices/shouju-base.timeline.json')
    combat_path = Path('data/actions/shouju-base.json')
    fighter['source']['timeline_path'] = timeline_path.as_posix()
    write(ROOT / fighter_path, fighter)
    write(ROOT / timeline_path, timeline)
    write(ROOT / combat_path, build_model(fighter_path, timeline_path, Path('scripts/fighter/shouju.json')))
    materialize(workspace, timeline_path, directory, fighter_path, combat_path)
    timeline = json.loads((directory / 'timeline.json').read_text())
    write(directory / 'ai.json', compile_context(bundle, timeline))
    for player in (False, True):
        target = directory / ('player_controller' if player else 'ai_controller')
        target.mkdir(exist_ok=True)
        code, meta = compile_player_body(bundle, sprite, timeline) if player else compile_body(bundle, sprite)
        (target / 'body.gd').write_text(code)
        write(target / 'body.json', meta)
        code, meta = compile_controller(bundle, sprite, timeline, player=player)
        meta['input_mode'] = 'player' if player else 'cpu'
        (target / 'controller.gd').write_text(code)
        write(target / 'controller.json', meta)
        (target / 'predicates.gd').write_text(compile_source(controller_script(bundle, sprite)['source'], player=player))
    code, meta = compile_transfer(bundle)
    (directory / 'ai_hit_state.gd').write_text(code)
    write(directory / 'ai_hit_state.json', meta)
    build_voice(['shouju'])
    subprocess.run([sys.executable, str(ROOT / 'tools/importer/build_sound_segments.py'),
                    '--directory', str(directory), '--ffdec', str(ffdec), '--ffmpeg', str(ffmpeg)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('workspace', 'ffdec', 'ffmpeg'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.ffdec, args.ffmpeg)
