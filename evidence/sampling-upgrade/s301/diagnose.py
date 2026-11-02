"""Bound the archived glyph-state facility; never infer an entry from a snapshot."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'b344582d479980eb397d2e9484862bc7a1d99065'


def prior_module():
    spec = importlib.util.spec_from_file_location('s301_prior', HERE.parent / 's292/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def placement_inventory(tags):
    """Decode only the locked PlaceObject2 prefix, not live display-list execution."""
    rows = []
    for tag in tags:
        if tag['code'] != 26:
            continue
        raw = bytes.fromhex(tag['payload_hex'])
        if len(raw) < 5 or not raw[0] & 2:
            raise ValueError('missing placement character')
        flags, depth, symbol = struct.unpack_from('<BHH', raw)
        rows.append({'frame': tag['frame'], 'offset': tag['offset'],
                     'payload_sha256': hashlib.sha256(raw).hexdigest(),
                     'flags': flags, 'depth': depth, 'symbol': symbol,
                     'move': bool(flags & 1), 'has_clip_actions': bool(flags & 128)})
    expected = [(f, 6 if f == 1 else 3, 1, 1799 + f) for f in range(1, 11)]
    if [(r['frame'], r['flags'], r['depth'], r['symbol']) for r in rows] != expected:
        raise ValueError('locked glyph placement inventory changed')
    return rows


def control_sequences(audit):
    """Join historical endpoints and entries without inventing intermediate reads."""
    rows = []
    boundaries = audit['historical_boundaries']
    for name in ('retained', 'encoded_retained'):
        group = audit['groups'][name]
        calls = [int(x) for x in re.findall(r'__s274Control\.gotoAndStop\((\d+)\);', group['source'])]
        if calls != [2, 1]:
            raise ValueError('locked control call sequence changed')
        before, after = (boundaries[name + '_' + side] for side in ('before', 'after'))
        entries = [r for r in audit['historical_retained_entries'] if r['tick'] == before['tick']]
        if len(entries) != 1:
            raise ValueError('ambiguous historical entry')
        entry = entries[0]
        events = [before, after, entry]
        if len({r['run'] for r in events}) != 1:
            raise ValueError('cross-run control join')
        if not before['sequence'] < after['sequence'] < entry['sequence']:
            raise ValueError('historical control order changed')
        if before['value'].split(',')[1:] != after['value'].split(',')[1:]:
            raise ValueError('historical endpoint state changed')
        if entry['value'].split(',') != before['value'].split(',')[1:]:
            raise ValueError('historical entry identity changed')
        rows.append({'control': name, 'source_lines': group['source_lines'],
                     'authored_targets_in_one_callback': calls,
                     'before': before, 'after': after, 'later_entry': entry,
                     'intermediate_frame2_entry': None,
                     'isolated_repeated_target_entry': None,
                     'endpoint_state_equal': True,
                     'limitation': 'Equal endpoints surround two target selections and a later frame1 event; neither call has an independent entry witness.'})
    return rows


def diagnose():
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for name, digest in pins.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('locked input changed: ' + name)
    historical = prior_module().diagnose()
    if historical != json.loads((HERE.parent / 's292/diagnosis.json').read_text()):
        raise ValueError('locked s292 diagnosis changed')
    byte_audit = historical['byte_audit']
    original = placement_inventory(byte_audit['original_tags'])
    archived = placement_inventory(byte_audit['archived_tags'])
    if [{k: v for k, v in r.items() if k != 'offset'} for r in original] != [
            {k: v for k, v in r.items() if k != 'offset'} for r in archived]:
        raise ValueError('placement bytes differ')
    return {
        'slice': 's301', 'base': BASE,
        'scope': 'AFTER-s299 rank #2 only: Independent ones entry clock',
        'production_admitted': False, 'native_parity_proven': False,
        'observer_qualified': False, 'independent_child_clock_proved': False,
        'product_obligations_closed': 0,
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0, 'new_images': 0,
        'historical': historical['historical'],
        'unobserved_frame1_windows': historical['unobserved_frame1_windows'],
        'placement_facility_audit': {
            'original': original, 'archived': archived,
            'static_glyph_to_frame_bijection': True,
            'live_placement_dispatch_resolver': None,
            'live_instance_generation_resolver': None,
            'repeated_target_entry_witness': None,
            'limitation': 'A unique glyph identifies authored frame state, not entry multiplicity/order. MOVE/character replacement is not proof of a new outer ones instance. File offsets are not live dispatch addresses.'},
        'control_sequence_audit': control_sequences(historical['control_audit']),
        'qualification_matrix': [
            {'frame': frame, 'original_action_present': frame == 1,
             'archived_action_present': frame == 1,
             'independent_entry': None, 'isolated_repeated_target': None,
             'isolated_changed_target': None, 'same_depth_replacement': None,
             'observer_off_on_order': None}
            for frame in range(1, 11)],
        'candidate_decisions': [
            {'facility': 'archived frame1 action hook', 'qualified': False,
             'reason': 'Nine frames have no action dispatch; helper preservation and independent controls remain unproved.'},
            {'facility': 'glyph state / placement prefix', 'qualified': False,
             'reason': 'Static ten-frame mapping has no independent live entry or instance resolver; equal states cannot count repeated entries.'},
            {'facility': 'add actions to empty frames', 'qualified': False,
             'reason': 'Introduces action dispatch; not a neutral observer. Not built or executed.'}],
        'capture_decision': 'Blocked before fresh ones-only capture; no independently qualified facility.',
        'blocker': 'Missing live all-ten-frame entry/instance resolver and isolated repeated-target, changed-target, replacement and independent observer-off/on controls.',
        'exclusions': ['synthetic clock', 'added empty-frame action treated as neutral',
                       'scene/intro repair', 'HUD reset', 'cross-run tape', 'images',
                       'runtime/contracts/shared sampler/threshold/validator changes',
                       's254-s300 edits', 'rank 1 or ranks 3+ execution'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in ('observer', 'independent-controls', 'child-clock'):
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    for required, code in ((args.require_observer, 'S301_ENTRY_FACILITY_UNPROVED'),
                           (args.require_independent_controls, 'S301_INDEPENDENT_CONTROLS_UNPROVED'),
                           (args.require_child_clock, 'S301_CHILD_CLOCK_UNPROVED')):
        if required:
            print(code + ': ' + result['blocker'])
            return 1
    print('S301_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
