"""Fail closed on the unfulfilled AFTER-s335 rank-5 measurement prerequisite."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('invocation-generations', 'activation-erasure', 'coercion-erasure',
         'helper-effects', 'off-on', 'external-callsite')
BOUNDARIES = ('initialization', 'scope-member-access', 'intervening-call',
              'first-overwrite', 'return-before-overwrite', 'body-end',
              'dashing-read', 'coercion-and-branch')


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('locked_s331', HERE.parent / 's331/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay():
    result = load_prior().diagnose()
    if result != json.loads((HERE.parent / 's331/diagnosis.json').read_text()):
        raise ValueError('Complete locked s331 replay changed')
    return result


def expected_attempt():
    # This is a blocked measurement record, not an interface accepting proof claims.
    return dict(
        slice='s340', scope='AFTER-s335 rank #5 only',
        status='blocked-before-live-binding',
        original_run=None, candidate_run=None, same_input_tape=None,
        original_loaded_body=None, candidate_loaded_body=None,
        original_invocation=None, candidate_invocation=None,
        original_activation=None, candidate_activation=None,
        original_this_generation=None, candidate_this_generation=None,
        original_root_generation=None, candidate_root_generation=None,
        original_parent_generation=None, candidate_parent_generation=None,
        original_defining_scope=None, candidate_defining_scope=None,
        original_scope_generation=None, candidate_scope_generation=None,
        suppression_preload_visibility=None, dashing_value_type=None,
        coercion_effects=None, external_callsite=None,
        independent_channel=None, uninterrupted_lifetime=None,
        boundaries=[dict(boundary=b, original_event=None, candidate_event=None,
                         original_slot_state=None, candidate_slot_state=None,
                         erasure_measurement=None) for b in BOUNDARIES],
        helper_installed=False, off_on_controls_executed=False,
        independent_observations=[],
        reason='Locked s331 supplies no independent body/invocation/scope/generation resolver. '
               'No replacement resolver or paired live trace was obtained in s340. '
               'Measurement stops before live binding and helper installation.')


def audit_attempt(record):
    if record != expected_attempt():
        raise ValueError('Unobserved binding/erasure record changed; new proof requires independent review')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    replay()
    attempt = json.loads((HERE / 'binding-attempt.json').read_text())
    audit_attempt(attempt)
    return dict(
        slice='s340', scope='AFTER-s335 rank #5 only',
        production_admitted=False, native_parity_proven=False, m0_02_status='pending',
        locked_s331_reproduced=True, replay_is_new_progress=False,
        repeated_header_dataflow_or_interface_audit_is_new_proof=False,
        attempt=attempt, independent_native_observations=0,
        mechanism_obligations_closed=0, product_obligations_closed=0,
        gates={g: dict(proved=False, code='S340_' + g.upper().replace('-', '_') + '_UNPROVED')
               for g in GATES},
        new_builds=0, new_player_launches=0, new_attaches=0, new_memory_reads=0,
        new_helper_installations=0, new_captures=0, other_ranks_executed=[],
        next_required_evidence='Independently derive and qualify a loaded-body, activation and '
                               'defining-scope channel for one original/candidate invocation pair, binding '
                               'uninterrupted this/root/parent generations and retaining '
                               'uninterrupted lifetime and initialization-to-overwrite/return '
                               'observations through opaque operations. Then measure erasure; '
                               'including actual dashing value/type and coercion effects; '
                               'only afterwards qualify helper effects and natural off/on controls.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    try:
        result = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S340_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    failed = [result['gates'][g]['code'] for g in GATES
              if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failed) if failed else
          'S340_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
