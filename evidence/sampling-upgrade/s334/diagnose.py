"""Audit separate rank-8 lookup prerequisites; never infer allocation identity."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('slot-reference', 'content-clearing', 'replacement', 'allocation-identity')
FACILITIES = (
    ('evidence/sampling-upgrade/s279/pin_imports.py', 'pin',
     'Maps imported allocator trampolines to indirect slots only. These slots are not parent/depth display slots or saved AS2 references; no internal pool checkout/return ledger.'),
    ('tools/probes/probe_owned_debugger.py', 'debugger_script',
     'Selected CPU registers have no parent/depth occupant lookup or saved-reference dereference, layout or generation resolver; then detach creates an observation boundary.'),
    ('tools/probes/probe_owned_debugger.py', 'probe',
     'Owned PID and build hashes protect custody, not object generations. AIREF profile waiting begins after launch; extension hooks implement neither lookup path nor uninterrupted pool coverage.'))


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('locked_s325', HERE.parent / 's325/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    retained = prior.diagnose()
    if json.loads(json.dumps(retained)) != json.loads((HERE.parent / 's325/diagnosis.json').read_text()):
        raise ValueError('Locked s325 replay changed')
    facilities = []
    for path, function, gap in FACILITIES:
        source = (ROOT / path).read_text()
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == function)
        facilities.append(dict(path=path, function=function, start_line=node.lineno,
                               end_line=node.end_lineno,
                               source='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]),
                               missing=gap, invoked=False))
    paths = {}
    for name, inputs in (
            ('parent_depth', ['parent instance generation', 'depth']),
            ('saved_reference', ['saved AS2 value location', 'reference representation'])):
        paths[name] = dict(required_inputs=inputs, module_relative_address=None,
                           instruction_bytes=None, layout=None, live_binding=None,
                           result_allocation_generation=None, derived=False)
    return dict(slice='s334', scope='AFTER-s326 rank #8 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                locked_s325_reproduced=True, replay_is_new_progress=False,
                locked_s325_diagnosis=retained,
                facilities=facilities, independent_native_observations=0,
                lookup_paths=paths,
                observations={key: None for key in (
                    'loaded_module', 'owner_generation', 'retained_content_clearing',
                    'replacement', 'free', 'reuse', 'uninterrupted_pool_generations',
                    'deferred_free_order')},
                actual_native_controls_executed=False,
                gates={g: dict(proved=False, code='S334_'+g.upper().replace('-', '_')+'_UNPROVED')
                       for g in GATES},
                first_unmet_prerequisite='separate byte-bound parent/depth and saved-reference lookup paths',
                blocker='Inspected adapters implement neither native lookup path. Independent layouts and live binding remain absent; clearing/replacement/free/reuse controls are deferred behind this prerequisite.',
                search_scope='Three named retained adapter functions and complete locked s325 replay; not exhaustive machine-code analysis or proof that no resolver can be built.',
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
        parser.exit(1, 'S334_EVIDENCE_INVALID: '+str(exc)+'\n')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    failures = [report['gates'][g]['code'] for g in GATES
                if getattr(args, 'require_'+g.replace('-', '_')) and not report['gates'][g]['proved']]
    print('; '.join(failures) if failures else
          'S334_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
