"""Keep rank-7 static address resolution separate from live allocation identity."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('relative-code-association', 'parent-depth-resolver', 'saved-reference', 'slot-reference',
         'content-clearing', 'replacement', 'allocation-identity')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)


def audit_attempt(record):
    if record != json.loads((HERE / 'relative-attempt.json').read_text()):
        raise ValueError('Relative attempt differs from pinned record')
    for key in ('parent_depth_resolver', 'saved_reference_dereference', 'live_generations'):
        if record[key] is not None:
            raise ValueError('Static address promoted to native proof')
    if record['controls_executed']:
        raise ValueError('Unobserved controls')
    edge = record['relative_code_association']
    if edge['next_rip'] + edge['signed_displacement'] != edge['target'] or edge['target'] != 0x10119efe1:
        raise ValueError('Relative target differs')
    if edge['call_target'] != 0x10005d960:
        raise ValueError('Call destination differs')
    return record


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'route-sha256.json')
    prior = load('s360_s351', HERE.parent / 's351/diagnose.py').diagnose()
    archived = json.loads((HERE.parent / 's351/diagnosis.json').read_text())
    if json.loads(json.dumps(prior)) != archived:
        raise ValueError('Complete retained s351 diagnosis changed')
    attempt = audit_attempt(json.loads((HERE / 'relative-attempt.json').read_text()))
    saved = json.loads((HERE / 'saved-reference-attempt.json').read_text())
    for key in ('value_location', 'representation', 'dereference_instructions', 'result_allocation_generation', 'new_native_measurement'):
        if saved[key] is not None:
            raise ValueError('Unobserved saved dereference')
    if saved['slot_result_borrowed'] or saved['parent_text_argument_is_saved_referent']:
        raise ValueError('Saved and slot paths conflated')
    return dict(slice='s360', scope='AFTER-s353 rank #7 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                retained_s351_diagnosis=archived, complete_s351_replayed=True,
                retained_validation_is_new_progress=False,
                reference_attempt=attempt, saved_reference_attempt=saved,
                lookup_paths=prior['lookup_paths'], observations=prior['observations'],
                independent_native_observations=0, actual_native_controls_executed=False,
                gates={g: dict(proved=g == 'relative-code-association',
                    code='S360_' + g.upper().replace('-', '_') + ('_PROVED' if g == 'relative-code-association' else '_UNPROVED')) for g in GATES},
                first_unmet_prerequisite='Native parent/depth resolver semantics and separate saved-value dereference before live generations',
                new_builds=0, new_player_launches=0, new_attaches=0, new_memory_reads=0,
                new_captures=0, mechanism_obligations_closed=0, product_obligations_closed=0,
                other_ranks_executed=[], ranks_1_6='delivered', ranks_8_plus='planning only')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S360_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [report['gates'][g]['code'] for g in GATES if getattr(args, 'require_' + g.replace('-', '_')) and not report['gates'][g]['proved']]
    print('; '.join(failures) if failures else 'S360_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
