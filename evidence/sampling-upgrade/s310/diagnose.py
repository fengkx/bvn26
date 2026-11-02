"""Bound replacement witnesses without promoting helper identity to live entry."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '38f66b5cb46df0fab2010f30ea4f423072c1d7b6'
GATES = {
    'observer': 'S310_ENTRY_INSTANCE_RESOLVER_UNPROVED',
    'independent-controls': 'S310_INDEPENDENT_CONTROLS_UNPROVED',
    'child-clock': 'S310_CHILD_CLOCK_UNPROVED',
    'fresh-capture': 'S310_FRESH_CAPTURE_BLOCKED',
}


def load_prior():
    spec = importlib.util.spec_from_file_location('s310_locked_s301', HERE.parent / 's301/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state(event, label):
    parts = event['value'].split(',')
    if len(parts) != 5 or parts[0] != label:
        raise ValueError('invalid state label or shape')
    return {'path': parts[1], 'depth': int(parts[2]),
            'encoded_generation': int(parts[3]), 'frame': int(parts[4])}


def replacement_audit(audit):
    """Join existing helper events only; retain the unload-depth discrepancy."""
    rows = []
    for group, prefix in (('replacement', 'replace'), ('encoded_replacement', 'encoded_replace')):
        source = audit['groups'][group]
        text = source['source']
        if text.count('duplicateMovieClip("__s274Control", 100001)') != 1 or 'gotoAndStop' in text:
            raise ValueError('replacement source changed')
        before, after = [audit['historical_boundaries'][prefix + '_' + side]
                         for side in ('before', 'after')]
        left, right = state(before, prefix + '_before'), state(after, prefix + '_after')
        if left['path'] != right['path'] or left['depth'] != right['depth']:
            raise ValueError('replacement endpoint slot mismatch')
        if right['encoded_generation'] != left['encoded_generation'] + 1:
            raise ValueError('encoded generation mismatch')
        if before['run'] != after['run'] or before['sequence'] >= after['sequence']:
            raise ValueError('replacement run/order mismatch')
        events = [e for e in audit['historical_lifecycle_events']
                  if before['sequence'] < e['sequence'] < after['sequence']]
        if len(events) != 2 or any(e['run'] != before['run'] for e in events):
            raise ValueError('missing, duplicate or cross-run lifecycle witness')
        unload, load = events
        old, new = state(unload, 'unload'), state(load, 'load')
        if not before['sequence'] < unload['sequence'] < load['sequence'] < after['sequence']:
            raise ValueError('lifecycle order mismatch')
        if any(e['kind'] != 's274_life' for e in events):
            raise ValueError('lifecycle kind mismatch')
        if old['path'] != left['path'] or old['encoded_generation'] != left['encoded_generation']:
            raise ValueError('unload helper identity mismatch')
        if new != right or old['frame'] != left['frame']:
            raise ValueError('load helper identity/frame mismatch')
        rows.append({'control': group, 'source_lines': source['source_lines'],
                     'source': text, 'before': before, 'unload': unload, 'load': load, 'after': after,
                     'endpoint_states': [left, right], 'unload_state': old,
                     'unload_depth_equals_endpoint': old['depth'] == left['depth'],
                     'explicit_target_selection_count': 0,
                     'observed_helper_frames': sorted({left['frame'], right['frame'], old['frame'], new['frame']}),
                     'live_instance_identity': None, 'independent_entry_order': None,
                     'observer_off_on_preservation': None})
    return rows


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + name)
    prior = load_prior()
    historical = prior.diagnose()
    if historical != json.loads((HERE.parent / 's301/diagnosis.json').read_text()):
        raise ValueError('locked s301 diagnosis changed')
    # s301 has already verified this entire predecessor result and its pinned inputs.
    controls = json.loads((HERE.parent / 's292/diagnosis.json').read_text())['control_audit']
    replacements = replacement_audit(controls)
    return {
        'slice': 's310', 'base': BASE,
        'scope': 'AFTER-s308 rank #2 only: Independent ones entry clock',
        'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
        'locked_s301_reproduced': True, 'historical': historical['historical'],
        'replacement_witness_audit': replacements,
        'qualification_matrix': historical['qualification_matrix'],
        'live_entry_resolver': None, 'live_instance_resolver': None,
        'observer_qualified': False, 'independent_controls_proved': False,
        'independent_child_clock_proved': False, 'fresh_capture_eligible': False,
        'candidate_decisions': historical['candidate_decisions'],
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0, 'new_images': 0,
        'other_ranks_executed': [], 'product_obligations_closed': 0,
        'blocker': 'No independent live entry/instance resolver for all ten frames. Replacement witnesses are helper events at frame1 only, with unload depth differing from endpoint depth; they do not qualify native lifetime or isolated entry. Repeated/changed-target and independent observer-off/on controls remain unproved. Fresh capture is blocked before launch.',
        'exclusions': ['static glyph-as-entry', 'synthetic clock',
                       'added empty-frame action treated as neutral', 'scene/intro repair',
                       'HUD reset', 'cross-run tape or images', 's254-s309 edits',
                       'game/scripts/runtime/contracts/shared sampler/threshold/validator changes',
                       'rank 1 or ranks 3-9 execution'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    # Fixed historical evidence has no acceptance path for user-supplied proof flags.
    failures = [code for flag, code in GATES.items()
                if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + result['blocker'])
        return 1
    print('S310_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
