"""Rebuild Ulquiorra's source-bound base and replacement packages.

Compilation is not parity acceptance. Run the retained fixtures separately.
"""
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
from build_form_profile import compile_programs, voice_spec
from compile_ai_hit_state import compile_transfer


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(workspace, ffdec, ffmpeg):
    bundle = json.loads((ROOT / 'scripts/fighter/weqal.json').read_text())
    base = ROOT / 'godot/generated/fighters/weqal'
    for frame, directory, stem in (
        (1, base, 'weqal-base'),
        (2, ROOT / 'godot/generated/forms/weqal-2', 'weqal-form2'),
    ):
        fighter = extract_slice(ROOT, '小乌', allow_forms=True, parent_frame=frame)
        sprite = fighter['source']['timeline_symbol_id']
        timeline = extract_frames(workspace / 'weqal.xml', sprite, wrapper_siblings=True)
        timeline['source_swf'] = {'path': bundle['game_file'], 'sha256': bundle['swf_sha256']}
        validate_nested_controls(timeline, bundle)
        fighter_path = Path('data/slices') / (stem + '.json')
        timeline_path = Path('data/slices') / (stem + '.timeline.json')
        fighter['source']['timeline_path'] = timeline_path.as_posix()
        write(ROOT / fighter_path, fighter)
        write(ROOT / timeline_path, timeline)
        combat_path = Path('data/actions') / (stem + '.json')
        write(ROOT / combat_path, build_model(fighter_path, timeline_path, Path('scripts/fighter/weqal.json')))
        materialize(workspace, timeline_path, directory, fighter_path, combat_path)
        runtime_timeline = json.loads((directory / 'timeline.json').read_text())
        compile_programs(directory, bundle, runtime_timeline)
        code, metadata = compile_transfer(bundle)
        (directory / 'ai_hit_state.gd').write_text(code)
        write(directory / 'ai_hit_state.json', metadata)
        if frame == 1:
            voice = json.loads((ROOT / 'godot/generated/fighters/yihu/hurt_voice.json').read_text())
            for key, site in voice['clock_sites'].items():
                voice['clock_sites'][key] = 'fighter/weqal#' + site.split('#', 1)[1]
            voice['probability_site'] = 'fighter/weqal#' + voice['probability_site'].split('#', 1)[1]
            write(base / 'hurt_voice.json', voice)
        write(directory / 'hurt_voice.json', voice_spec(bundle, sprite, base))
        subprocess.run([sys.executable, str(ROOT / 'tools/importer/build_sound_segments.py'),
                        '--directory', str(directory), '--ffdec', str(ffdec),
                        '--ffmpeg', str(ffmpeg)], check=True)
        print(json.dumps({'parent_frame': frame, 'sprite': sprite, 'directory': str(directory)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('workspace', 'ffdec', 'ffmpeg'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.workspace, args.ffdec, args.ffmpeg)
