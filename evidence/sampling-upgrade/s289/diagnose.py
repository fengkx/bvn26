"""Audit one retained AImain reference window; never mint native identity."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MEMBER = 'patches/main/frame_1/DoAction.as'
ERROR = 'S289_NATIVE_ALLOCATION_UNPROVED'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_pins(root, pins):
    for name, expected in pins.items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError('Changed evidence: ' + name)


def source_binding(source, statement):
    lines = source.splitlines()
    matches = [i for i, line in enumerate(lines, 1) if line.strip() == statement]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous source statement: ' + statement)
    return {'member': MEMBER, 'line': matches[0], 'statement': statement,
            'member_sha256': digest(source.encode()), 'native_address': None}


def reference_window(raw):
    rows = []
    run = None
    for expected, line in enumerate(raw.splitlines(), 1):
        parts = line.split('|', 7)
        if len(parts) != 8 or parts[0] != 'AIREF' or int(parts[2]) != expected:
            raise ValueError('Malformed or noncontiguous event stream')
        if run is None:
            run = parts[1]
        if parts[1] != run:
            raise ValueError('Mixed run')
        rows.append({'sequence': expected, 'clock_ms': int(parts[3]),
                     'root': int(parts[4]), 'tick': int(parts[5]),
                     'kind': parts[6], 'payload': parts[7]})
    boundaries = [r for r in rows if r['kind'] == 'aimain_identity'
                  and r['payload'].startswith('root,')]
    if len(boundaries) != 2:
        raise ValueError('Expected the two locked root observations')
    start, end = [r['sequence'] for r in boundaries]
    # Include all four object reads following the second identity observation.
    window = rows[start - 1:end + 4]
    for boundary in boundaries:
        objects = rows[boundary['sequence']:boundary['sequence'] + 4]
        if [r['payload'].split(',')[:2] for r in objects] != [
                ['root', role] for role in ('parent', 'saved_receiver', 'depth_occupant', 'named_receiver')]:
            raise ValueError('Missing or reordered root object observations')
    controls = [r for r in rows if r['kind'] == 's261_control']
    if [r['payload'] for r in controls] != [
            'retained,true,true', 'replaced,true,false', 'retained_content_deleted,true,false']:
        raise ValueError('Changed locked control observations')
    return {'run_id': run, 'event_count': len(rows), 'events': window,
            'controls': controls, 'raw_sha256': digest(raw.encode()),
            'interpretation': 'AS2 observations only; contiguous log sequence is not complete native lifecycle coverage'}


def diagnose():
    verify_pins(ROOT, json.loads((HERE / 'input-sha256.json').read_text()))
    spec = importlib.util.spec_from_file_location('s279', HERE.parent / 's279/diagnose.py')
    prior_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior_module)
    prior = prior_module.diagnose()
    if prior != json.loads((HERE.parent / 's279/diagnosis.json').read_text()):
        raise ValueError('Locked s279 diagnosis differs')
    with tarfile.open(HERE.parent / 's261/native-build.tar.gz') as archive:
        source = archive.extractfile(MEMBER).read().decode()
    statements = {
        'save_reference': '_global.s261Receiver = receiver;',
        'read_saved_reference': 'var saved = _global.s261Receiver;',
        'read_depth_slot': 'var occupant = parent.getInstanceAtDepth(_global.s261Depth);',
        'read_named_slot': 'var named = parent.AImain;',
        'control_remove': 'saved.removeMovieClip();',
        'control_replace': 'var replacement = host.createEmptyMovieClip("slot", 1);',
        'control_property_delete': 'delete replacement.identity;',
    }
    bindings = {name: source_binding(source, text) for name, text in statements.items()}
    window = reference_window(gzip.decompress((HERE.parent / 's261/native-capture.log.gz').read_bytes()).decode())
    return {
        'scope': 's289 / AFTER-s281 rank #8 only', 'base': '8c54258e',
        'production_admitted': False, 'native_parity_proven': False,
        'allocation_identity_proved': False, 'product_obligations_closed': 0,
        'status': 'honest_unproved', 'requirement_failure_code': ERROR,
        'retained_capture': prior['retained_capture'],
        'source_bindings': bindings, 'reference_window': window,
        'target_sites': prior['allocation_observability']['target_observer_sites'],
        'controls': prior['allocation_observability']['controls'],
        'native_observations': {
            'slot_resolver': None, 'saved_reference_resolver': None,
            'object_layout': None, 'allocation_free_reuse_ledger': None,
            'pool_lifetime_coverage': None, 'retained_content_clear': None,
            'replacement_control_generations': None,
        },
        'missing': prior['allocation_observability']['missing'],
        'next_discriminator': prior['next_discriminator'],
        'new_player_launches': 0, 'new_captures': 0,
        'absence_of_possible_resolver_proved': False,
        'exclusions': ['pointer-only identity', '0->1 alias', 'token-loss identity',
                       'unloaded exemption', 'import inventory as runtime proof',
                       'ranks 1-7 and 9', 'production implementation'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-slot-reference', action='store_true')
    parser.add_argument('--require-allocation-identity', action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as exc:
        print('S289_EVIDENCE_INVALID: ' + str(exc), file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_slot_reference or args.require_allocation_identity:
        print(ERROR + ': native slot/reference resolution and qualified allocation/free/reuse controls absent', file=sys.stderr)
        return 1
    print('S289_DIAGNOSIS_RECOMPUTED: archived AS2 bindings are not native resolvers')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
