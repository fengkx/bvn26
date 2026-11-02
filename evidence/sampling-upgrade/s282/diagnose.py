"""Audit retained ones-target observability; never infer a native child clock."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location('s282_locked_lifetime', HERE.parent / 's274/diagnose.py')
locked = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(locked)


def source_frames(contract, scripts, patch):
    symbol = contract['symbols']['1810']
    original = [s for s in scripts['scripts'] if s['path'].startswith('DefineSprite_1810/')]
    if original != symbol['scripts'] or len(original) != 1 or original[0]['source'].strip() != 'stop();':
        raise ValueError('changed authored digit scripts')
    if patch.splitlines() != ['_root.s274Entry(this);', '_root.s262Init(this,1810);', 'stop();']:
        raise ValueError('changed archived entry hook')
    if symbol['frame_count'] != 10 or [c['frame'] for c in symbol['changes']] != list(range(1, 11)):
        raise ValueError('incomplete digit timeline')
    rows = []
    for change in symbol['changes']:
        frame = change['frame']
        tag = ET.fromstring(change['tag'])
        if (tag.get('type'), tag.get('depth'), tag.get('characterId'), tag.get('placeFlagMove')) != (
                'PlaceObject2Tag', '1', str(1799 + frame), 'false' if frame == 1 else 'true'):
            raise ValueError('changed digit placement')
        rows.append({'frame': frame, 'glyph_symbol': int(tag.get('characterId')),
                     'glyph_move': frame != 1, 'authored_script': 'stop();' if frame == 1 else None,
                     'archived_entry_hook': frame == 1})
    return rows


def audit(events, frames):
    # Reuse the full historical validator before deriving any narrower windows.
    lifetime = locked.analyze(events)
    path = lifetime['load']['value'].split(',')[1]
    callbacks = [locked.locked.s262.s258.observed(e) for e in events
                 if e['kind'] == 's258_countdown' and e['value'].startswith('fire_after,')]
    entries = [e for e in events if e['kind'] == 's274_entry' and e['value'].startswith(path + ',')]
    roots = [e for e in events if e['kind'] == 'input_next_display']
    rows = []
    for index, callback in enumerate(callbacks):
        upper = callbacks[index + 1]['sequence'] if index + 1 < len(callbacks) else len(events) + 1
        next_before = next((e for e in events if e['kind'] == 's258_countdown'
                            and e['value'].startswith('fire_before,') and e['sequence'] > callback['sequence']), None)
        if next_before:
            upper = next_before['sequence']
        observed = [e for e in entries if callback['sequence'] < e['sequence'] < upper]
        for entry in observed:
            if entry['value'].split(',')[1:] != ['-16381', '1', str(callback['ones'])]:
                raise ValueError('entry target/generation mismatch')
            if not frames[callback['ones'] - 1]['archived_entry_hook']:
                raise ValueError('entry without archived hook')
        root = next((e for e in roots if e['sequence'] > callback['sequence']), None)
        rows.append({'ordinal': callback['firing'], 'tick': callback['tick'],
                     'callback_after_sequence': callback['sequence'], 'selected_frame': callback['ones'],
                     'next_callback_before_sequence': next_before['sequence'] if next_before else None,
                     'next_root_sequence': root['sequence'] if root else None,
                     'entry_sequences_before_next_callback': [e['sequence'] for e in observed],
                     'independent_target_entry_observed': True if observed else None,
                     'classification': 'entry_observed' if observed else (
                         'hook_present_no_entry_in_window' if frames[callback['ones'] - 1]['archived_entry_hook']
                         else 'target_frame_uninstrumented')})
    for frame in frames:
        selected = [r for r in rows if r['selected_frame'] == frame['frame']]
        frame['callback_selections'] = len(selected)
        frame['windows_with_entry'] = sum(bool(r['entry_sequences_before_next_callback']) for r in selected)
    return {'frames': frames, 'callback_windows': rows, 'events_revalidated': len(events),
            'callback_count': len(callbacks), 'actual_entries_including_initial': len(entries),
            'natural_encoding_entry_joins': lifetime['complete_entry_joins'],
            'uninstrumented_target_windows': sum(r['classification'] == 'target_frame_uninstrumented' for r in rows),
            'initial_entry_sequence': entries[0]['sequence'],
            'bounded_encoded_lifetime_observed': lifetime['bounded_encoded_lifetime_observed'],
            'independent_child_clock_proved': False, 'scene_state_admitted': False,
            'production_admitted': False, 'native_parity_proven': False}


def diagnose():
    for inventory in ('input-sha256.json', 'ranking-basis-sha256.json'):
        for name, expected in json.loads((HERE / inventory).read_text()).items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise ValueError('changed locked input: ' + name)
    historical = locked.diagnose()
    if historical != json.loads((HERE.parent / 's274/diagnosis.json').read_text()):
        raise ValueError('historical replay differs')
    with tarfile.open(HERE.parent / 's274/native-build.tar.gz') as archive:
        names = [n for n in archive.getnames() if n.startswith('s274-patches/DefineSprite_1810/') and n.endswith('.as')]
        if names != ['s274-patches/DefineSprite_1810/frame_1/DoAction.as']:
            raise ValueError('unexpected digit patch inventory')
        patch = archive.extractfile(names[0]).read().decode()
    frames = source_frames(json.loads((HERE.parent / 's262/source-contract.json').read_text()),
                           json.loads((ROOT / 'scripts/main.json').read_text()), patch)
    raw = gzip.decompress((HERE.parent / 's274/native-capture.log.gz').read_bytes())
    result = audit(locked.events_from(raw), frames)
    return dict(result, slice='s282', rank=1, base='f66987b3abf2ff329149f75a76a8911dbf8aae31',
                raw_sha256=hashlib.sha256(raw).hexdigest(), run_id='s274-lifetime-r01',
                new_builds=0, new_captures=0, new_images=0, product_obligations_closed=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-child-clock', action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: result[k] for k in ('events_revalidated', 'callback_count', 'uninstrumented_target_windows', 'independent_child_clock_proved', 'production_admitted', 'native_parity_proven')}))
    return int(args.require_child_clock and not result['independent_child_clock_proved'])


if __name__ == '__main__':
    raise SystemExit(main())
