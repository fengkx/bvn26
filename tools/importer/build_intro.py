"""Compile the source match opening and materialize its authored UI shapes."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

from extract_timeline_geometry import extract_frames, placement_delta
from materialize_timeline_assets import materialize


def scripts(path):
    return {s['path']: s['source'] for s in json.loads(path.read_text())['scripts']}


def compile_hud_timeline(workspace, source):
    hud = extract_frames(workspace / 'main.xml', 1815)
    stops = []
    for frame in hud['frames']:
        path = f'DefineSprite_1815/frame_{frame["frame"]}/DoAction.as'
        text = source.get(path, '').strip()
        if text:
            if text != 'stop();':
                raise ValueError('Unsupported HUD timeline script: ' + path)
            stops.append(frame['frame'])
    labels = {label: frame['frame'] for frame in hud['frames'] for label in frame['labels']}
    return {'hud_frames': {str(f['frame']): next(p for p in f['display_list'] if p['character_id'] == 1814) for f in hud['frames']},
            'hud_in': labels['in'], 'hud_labels': labels, 'hud_stop_frames': stops,
            'hud_frame_count': len(hud['frames'])}


def build(workspace, output, jar):
    source = scripts(Path('scripts/main.json'))
    controller = source['DefineSprite_1991/frame_1/DoAction.as']
    interval = int(re.search(r'setInterval\(kaichang,(\d+)\)', controller)[1])
    root = ET.parse(workspace / 'main.xml').getroot()
    spec = {'poll_ms': interval, 'source': 'scripts/main.json:DefineSprite_1991/frame_1/DoAction.as',
            'clips': {}, 'fighters': {}}
    spec.update(compile_hud_timeline(workspace, source))
    with tempfile.TemporaryDirectory(prefix='bvn-intro-') as tmp:
        tmp = Path(tmp)
        for name in ['ready', 'qjxg']:
            placement = next(t for t in root.findall('./tags/item') if t.get('name') == name)
            sid = int(placement.get('characterId'))
            timeline = extract_frames(workspace / 'main.xml', sid)
            timeline.pop('wrapper', None)
            events = {}
            for frame in timeline['frames']:
                path = f'DefineSprite_{sid}/frame_{frame["frame"]}/DoAction.as'
                text = source.get(path, '').strip()
                supported = {'stop();', 'clearInterval(_root.kcint);', 'clearInterval(_root.nxtfht);',
                             '_root.fadinXuetiao();', '_root.startFight();', '_root.initGameStart();',
                             '_root.焦点 = "all";', '_root.game.p1.mc.gotoAndPlay("站立");',
                             '_root.game.p2.mc.gotoAndPlay("站立");', 'gotoAndStop(1);'}
                if any(line.strip() not in supported for line in text.splitlines()):
                    raise ValueError(f'Unsupported opening script: {path}')
                if text:
                    events[str(frame['frame'])] = {'source_path': path, 'source': text}
            spec['clips'][name] = {'placement': placement_delta(placement), 'events': events,
                'frame_count': len(timeline['frames']),
                'labels': {label: f['frame'] for f in timeline['frames'] for label in f['labels']}}
            # Compile nested gotoAndStop(rounds+5), stop() and five-frame digit
            # transitions. No AS2 is shipped or evaluated by the player.
            for definition in timeline['definitions']:
                did = definition['character_id']
                local = definition.get('display_list_frames', [])
                for f in range(1, len(local) + 1):
                    text = source.get(f'DefineSprite_{did}/frame_{f}/DoAction.as', '').strip()
                    if text == 'stop();':
                        definition['intro_stop_frame'] = f
                    elif text == 'roundshu.gotoAndStop(_root.rounds + 5);':
                        target = next(p['character_id'] for p in local[f - 1] if p.get('name') == 'roundshu')
                        child = next(d for d in timeline['definitions'] if d['character_id'] == target)
                        child['intro_round_offset'] = int(re.search(r'rounds \+ (\d+)', text)[1])
            path = tmp / (name + '.json')
            path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + '\n')
            report = materialize(workspace, path, output / name)
            report['timeline']['path'] = (output / name / 'timeline.json').as_posix()
            (output / name / 'assets.json').write_text(json.dumps(report, indent=2) + '\n')
            shapes = [d for d in timeline['definitions'] if d['type'].startswith('DefineShape') and not d.get('bitmap_fills')]
            ids = ','.join(str(d['character_id']) for d in shapes)
            if ids:
                subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(jar), '-selectid', ids,
                                '-format', 'shape:png', '-export', 'shape', str(tmp / name), 'game/main.swf'], check=True, stdout=subprocess.DEVNULL)
            for d in shapes:
                shutil.copyfile(tmp / name / (str(d['character_id']) + '.png'), output / name / ('shape-%s.png' % d['character_id']))
        # Compile every materialized base form from its own root timeline and
        # kcplayed callbacks.  The directory is the generated artifact index;
        # keeping a hand-maintained roster here silently drops newly imported
        # source forms (for example Byakuya and Lee).
        fighter_root = Path('godot/generated/fighters')
        candidates = sorted(
            folder.name for folder in fighter_root.iterdir()
            if folder.is_dir() and (folder / 'fighter.json').is_file()
        )
        for name in candidates:
            folder = Path('godot/generated/fighters') / name
            fighter = json.loads((folder / 'fighter.json').read_text())
            timeline = json.loads((folder / 'timeline.json').read_text())
            action = next(group['开场'] for group in fighter['actions'].values() if '开场' in group)
            # The selected inner sprite is explicit in the extracted timeline.
            sid = timeline['sprite_id']
            state_frames = {}
            evidence = []
            script_bundle = Path(fighter['source']['script_bundle_path'])
            script_bytes = script_bundle.read_bytes()
            if hashlib.sha256(script_bytes).hexdigest() != fighter['source']['script_bundle_sha256']:
                raise ValueError(f'Fighter script bundle hash mismatch: {script_bundle}')
            for path, text in scripts(script_bundle).items():
                match = re.match(rf'DefineSprite_{sid}/frame_(\d+)/DoAction.as$', path)
                if not match or not action['start_frame'] <= int(match[1]) <= action['end_frame']:
                    continue
                evidence.append({'path': path, 'source': text.strip()})
                assignment = re.search(r'kcplayed = (\d+);', text)
                if assignment:
                    state_frames[match[1]] = int(assignment[1])
            # Some source openings repeat the ready state (Byakuya writes
            # kcplayed=3 twice) before the terminal kcplayed=2 transition.
            # Repetition is authored timing, while the required state domain
            # remains exactly 1/2/3.
            if sorted(set(state_frames.values())) != [1, 2, 3]:
                raise ValueError(f'Incomplete intro state chain: {name}')
            audit_frames = [{'frame': f['frame'], 'changes': f.get('changes', []),
                             'events': f.get('events', []),
                             'scripts': [e for e in evidence if f'/frame_{f["frame"]}/' in e['path']]}
                            for f in timeline['frames'] if action['start_frame'] <= f['frame'] <= action['end_frame']]
            spec['fighters'][name] = {'action': action, 'state_frames': state_frames, 'scripts': evidence, 'frames': audit_frames}
            timeline_path = fighter['source'].get('timeline_path', f'data/slices/{name}-base.timeline.json')
            timeline_file = Path(timeline_path)
            timeline_sha256 = hashlib.sha256(timeline_file.read_bytes()).hexdigest() if timeline_file.is_file() else ''
            intro = {
                'format': 'bvn26-fighter-opening-v1',
                'status': 'source_compiled_not_runtime_integrated',
                'fighter_id': name,
                'source_fighter_id': fighter.get('fighter_id', name),
                'source_sprite_id': sid,
                'action': action,
                'state_frames': state_frames,
                'state_frame_sources': {
                    frame: next(item for item in evidence if f'/frame_{frame}/' in item['path'])
                    for frame in state_frames
                },
                'source': {
                    'swf_path': fighter['source']['swf_path'],
                    'swf_sha256': fighter['source']['swf_sha256'],
                    'script_bundle_path': fighter['source']['script_bundle_path'],
                    'script_bundle_sha256': fighter['source']['script_bundle_sha256'],
                    'timeline_path': timeline_path,
                    'timeline_sha256': fighter['source'].get('timeline_sha256', timeline_sha256),
                },
            }
            (folder / 'intro.json').write_text(json.dumps(intro, ensure_ascii=False, indent=2) + '\n')
        # Keep decompiled evidence outside production data; runtime consumes fields.
        (Path('evidence') / 'intro-source.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
        for clip in spec['clips'].values():
            for event in clip['events'].values():
                text = event.pop('source')
                event['stop'] = 'stop();' in text or 'gotoAndStop(1)' in text
                event['start_fight'] = '_root.startFight()' in text
                event['fade_hud'] = '_root.fadinXuetiao()' in text
                event['reset_fighters'] = '_root.game.p1.mc.gotoAndPlay("站立")' in text
                event['rewind'] = 'gotoAndStop(1)' in text
                event['clear_intervals'] = re.findall(r'clearInterval\(_root\.(\w+)\);', text)
        for fighter in spec['fighters'].values():
            fighter.pop('scripts')
            fighter.pop('frames')
        (output / 'intro.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('godot/generated/main/intro'))
    p.add_argument('--ffdec-jar', type=Path, required=True)
    a = p.parse_args()
    build(a.workspace, a.output, a.ffdec_jar)
