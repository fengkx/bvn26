"""Audit the rank-4 observation prerequisite; never promote static bytes."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('consumer-request', 'returned-consumed-ranges', 'pre-advance-target',
         'loader-attestation', 'wrong-resource-control')
FACILITIES = (
    ('tools/probes/probe_owned_debugger.py', 'debugger_script',
     'Selected frame-zero registers do not bind an executed P1 consumer, request generation, read return or callback target.'),
    ('tools/probes/capture_native_player.py', '_verify_runtime_fighter',
     'Disk path and hash preflight do not observe bytes returned to or consumed by a live request.'),
    ('evidence/sampling-upgrade/s321/extract_native.py', 'main',
     'Disk-byte extraction and disassembly identify a static candidate only; no execution or immutable request identity.'))


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('locked_s321', HERE.parent / 's321/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    retained = prior.diagnose()
    if retained != json.loads((HERE.parent / 's321/diagnosis.json').read_text()):
        raise ValueError('Locked s321 replay changed')
    facilities = []
    for path, function, gap in FACILITIES:
        source = (ROOT / path).read_text()
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == function)
        facilities.append(dict(path=path, function=function, start_line=node.lineno,
                               end_line=node.end_lineno,
                               source='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]),
                               missing=gap, invoked=False))
    return dict(slice='s330', scope='AFTER-s326 rank #4 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                locked_s321_reproduced=True, replay_is_new_progress=False,
                facilities=facilities, independent_native_observations=0,
                retained_candidate=retained['static_candidate'],
                observations={key: None for key in (
                    'executed_caller', 'actual_p1_consumer', 'immutable_request_generation',
                    'executed_read_return', 'returned_buffer_ranges', 'consumed_buffer_ranges',
                    'target_before_inline_advance', 'same_request_initialization',
                    'target_use_unload_replacement', 'observer_effects')},
                normal_association_qualified=False, wrong_resource_control_executed=False,
                gates={g: dict(proved=False, code='S330_'+g.upper().replace('-', '_')+'_UNPROVED')
                       for g in GATES},
                first_unmet_prerequisite='executed P1 consumer bound to immutable request generation',
                blocker='Inspected adapters provide no independent request resolver. Normal association remains unqualified; wrong-resource control is deferred.',
                new_builds=0, new_player_launches=0, new_process_attaches=0,
                new_memory_reads=0, new_captures=0, product_obligations_closed=0,
                other_ranks_executed=[])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-'+gate, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S330_EVIDENCE_INVALID: '+str(exc)+'\n')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    failures = [report['gates'][g]['code'] for g in GATES
                if getattr(args, 'require_'+g.replace('-', '_')) and not report['gates'][g]['proved']]
    print('; '.join(failures) if failures else
          'S330_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
