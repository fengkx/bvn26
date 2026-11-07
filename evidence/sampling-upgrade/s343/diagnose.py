"""Keep candidate disk names separate from two unproved native lookup paths."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('slot-reference', 'content-clearing', 'replacement', 'allocation-identity')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_candidates(record):
    fresh = load('s343_candidates', HERE/'collect_lookup_candidates.py').collect()
    for value in (fresh, record):
        duration = value.pop('wall_seconds')
        if not isinstance(duration, (int, float)) or not 0 < duration < 3600:
            raise ValueError('Invalid collection duration')
    if fresh != record:
        raise ValueError('Disk candidate search changed')
    return record


def diagnose():
    for path, digest in json.loads((HERE/'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: '+path)
    retained = load('s343_locked_s334', HERE.parent/'s334/diagnose.py').diagnose()
    if json.loads(json.dumps(retained)) != json.loads((HERE.parent/'s334/diagnosis.json').read_text()):
        raise ValueError('Locked s334 replay changed')
    candidates = audit_candidates(json.loads((HERE/'lookup-candidates.json').read_text()))
    return dict(slice='s343', scope='AFTER-s335 rank #8 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                locked_s334_reproduced=True, locked_s334_diagnosis=retained,
                replay_is_new_progress=False, disk_candidate_search=candidates,
                lookup_paths=retained['lookup_paths'], observations=retained['observations'],
                independent_native_observations=0, actual_native_controls_executed=False,
                gates={g: dict(proved=False, code='S343_'+g.upper().replace('-', '_')+'_UNPROVED') for g in GATES},
                first_unmet_prerequisite='separate byte-bound parent/depth and saved-reference lookup paths',
                blocker='Parent/depth names occur in disk text lists; saved-global names have no hits in the finite search. Neither result supplies instruction entry, dereference layout or allocation generation. Live binding and clearing/replacement/free/reuse controls remain deferred.',
                absence_of_possible_resolver_proved=False,
                new_builds=0, new_player_launches=0, new_process_attaches=0,
                new_memory_reads=0, new_captures=0, product_obligations_closed=0,
                other_ranks_executed=[], rank_9_status='planning')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-'+gate, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S343_EVIDENCE_INVALID: '+str(exc)+'\n')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    failures = [report['gates'][g]['code'] for g in GATES
                if getattr(args, 'require_'+g.replace('-', '_')) and not report['gates'][g]['proved']]
    print('; '.join(failures) if failures else
          'S343_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
