"""Recompute the s261 allocation-observability gap; never infer native generations."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read_pinned_inputs():
    pins = json.loads((HERE / 'artifact-sha256.json').read_text())
    for name, expected in pins.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed evidence: ' + name)
    spec = importlib.util.spec_from_file_location('s261_diagnose', HERE.parent / 's261/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.diagnose()


def allocation_requirements(prior):
    # These are missing observations, not a manufactured allocation trace.
    roots = [row for row in prior['observations'] if row['phase'] == 'root']
    target = []
    for row in roots:
        occupant = row['objects']['depth_occupant']
        target.append({'event_sequence': row['sequence'], 'root': row['display'],
                       'clock_ms': row['clock_ms'], 'path': occupant['path'],
                       'depth': occupant['depth'], 'frame': occupant['frame'],
                       'total_frames': occupant['total_frames'],
                       'native_allocation_address': None, 'native_allocation_generation': None,
                       'saved_reference_native_referent': None})
    controls = prior['controls']
    return {
        'target_observer_sites': target,
        'controls': {
            'retained_content_clear': {
                'status': 'missing_native_control',
                'available_as2_control': 'retained_content_deleted',
                'available_signal': controls['retained_content_deleted'],
                'native_allocation_generation_before': None,
                'native_allocation_generation_after': None,
                'limitation': 'Deleting one token property is not a calibrated retained-content-clear allocation control.'},
            'same_name_same_depth_replacement': {
                'status': 'operation_observed_native_generation_missing',
                'available_as2_control': 'replaced',
                'available_signal': controls['replaced'],
                'native_allocation_generation_before': None,
                'native_allocation_generation_after': None,
                'limitation': 'Explicit remove/create is observed, but no native allocation/free or saved-reference resolution is captured.'},
        },
        'indistinguishable_as2_signals': controls['retained_content_deleted'] == controls['replaced'],
        'missing': [
            'native_slot_to_object_resolution_at_both_root_sites',
            'allocation_and_free_history_including_address_reuse',
            'native_saved_reference_resolution_at_both_root_sites',
            'independently_verified_retained_content_clear_control',
            'same_depth_replacement_native_generation_control',
        ],
    }


def diagnose():
    prior = read_pinned_inputs()
    facility = json.loads((HERE / 'facility/audit.json').read_text())
    for check in facility['checks'].values():
        data = (HERE / 'facility' / check['log']).read_bytes()
        if hashlib.sha256(data).hexdigest() != check['sha256']:
            raise ValueError('Changed facility transcript')
    historical_attach = json.loads((ROOT / 'evidence/importer-loud-fail/r244/retry/debugger/feasibility.json').read_text())
    requirements = allocation_requirements(prior)
    return {
        'scope': 'AFTER-s263 rank 4 only', 'baseline': 'ddd23ad9d37333ba51a640d0f87dbd22de221825',
        'production_admitted': False, 'native_parity_proven': False,
        'mapping_fix_proved': False, 'identity_discriminator_valid_for_cleared_content': False,
        'allocation_generation_observations_established': False,
        'status': 'unproved_native_observation_prerequisite',
        'product_obligations_closed': 0,
        'retained_capture': {'path': 'evidence/sampling-upgrade/s261/native-capture.log.gz',
                             'events': prior['event_count'], 'samples': prior['sample_count'],
                             'raw_validation_exit': prior['raw_validation_exit'],
                             'source_gap_count': prior['source_gap_count'],
                             'actor_comparison': prior['actor_comparison']},
        'allocation_observability': requirements,
        'facility': {'binary_sha256': facility['binary_sha256'],
                     'new_player_launches': facility['new_player_launches'],
                     'allocation_events_captured': facility['allocation_events_captured'],
                     'historical_same_binary_attach_succeeded': historical_attach['debugger']['attached'],
                     'historical_attach_is_target_identity_evidence': False,
                     'native_slot_resolver_established': False,
                     'absence_of_possible_facility_proved': False},
        'next_discriminator': [
            'Identify and byte-pin the native AImain depth-slot resolver and its returned object layout on the s261 executable; generic compose addresses are not applicable.',
            'Calibrate a native allocation/free generation ledger against a retained object whose content is cleared and a same-name/depth remove/create control; address equality alone is insufficient under reuse.',
            'At the source-equivalent last-nonzero and first-zero observer sites, join the parent slot and saved AS2 reference to that ledger without minting identity from clip properties, load callbacks, frame values or path strings.',
            'Retain complete event order, run/source/engine hashes and both controls in the same owned capture. Only a calibrated discriminator can support a later thin mapping proposal.'
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-allocation-identity', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_allocation_identity:
        print('ALLOCATION_IDENTITY_UNPROVED: ' + ', '.join(report['allocation_observability']['missing']))
        return 1
    print('DIAGNOSIS_RECOMPUTED: native allocation generations remain unobserved')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
