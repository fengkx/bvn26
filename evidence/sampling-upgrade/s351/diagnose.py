"""Keep rank-7 static address resolution separate from live allocation identity."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('name-executable', 'saved-reference', 'slot-reference',
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
    if record != json.loads((HERE / 'reference-attempt.json').read_text()):
        raise ValueError('Reference attempt differs from pinned record')
    if record['section_relocation_count'] != 0:
        raise ValueError('Unexpected section relocations require review')
    for target in record['targets']:
        if target['absolute_u64_occurrences']:
            raise ValueError('New address references require review')
    for key in ('executable_association', 'saved_reference_dereference', 'live_generations'):
        if record[key] is not None:
            raise ValueError('Static data promoted to proof')
    if record['controls_executed']:
        raise ValueError('Unobserved controls')
    return record


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'route-sha256.json')
    # Replay the portable retained chain, preserving the entire s343 report separately.
    prior = load('s351_s334', HERE.parent / 's334/diagnose.py').diagnose()
    archived = json.loads((HERE.parent / 's343/diagnosis.json').read_text())
    if json.loads(json.dumps(prior)) != archived['locked_s334_diagnosis']:
        raise ValueError('Retained chain changed')
    attempt = audit_attempt(json.loads((HERE / 'reference-attempt.json').read_text()))
    return dict(slice='s351', scope='AFTER-s344 rank #7 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                retained_s343_diagnosis=archived, complete_s334_replayed=True,
                s343_disk_name_search_repeated=False, retained_validation_is_new_progress=False,
                reference_attempt=attempt, lookup_paths=prior['lookup_paths'],
                observations=prior['observations'], independent_native_observations=0,
                actual_native_controls_executed=False,
                saved_reference_attempt=dict(source_route='_global.s261Receiver -> saved',
                    source_is_retained_only=True, value_location=None, representation=None,
                    dereference_instructions=None, result_allocation_generation=None,
                    slot_result_borrowed=False,
                    blocker='No independently resolved saved AS2 value location or representation; no native address target can be selected without assuming the missing layout. No saved-name search repeated.'),
                gates={g: dict(proved=False, code='S351_' + g.upper().replace('-', '_') + '_UNPROVED') for g in GATES},
                first_unmet_prerequisite='byte-bound name-to-executable association and separate saved-value dereference',
                new_builds=0, new_player_launches=0, new_attaches=0, new_memory_reads=0,
                new_captures=0, mechanism_obligations_closed=0, product_obligations_closed=0,
                other_ranks_executed=[], ranks_8_plus='planning only')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S351_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    failures = [report['gates'][g]['code'] for g in GATES if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failures) if failures else 'S351_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
