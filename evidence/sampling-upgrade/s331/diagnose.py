"""Audit the rank-5 observation prerequisite; never promote static body-push evidence."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('scope-binding', 'activation-erasure', 'coercion-erasure',
         'helper-effects', 'off-on', 'external-callsite')
FACILITIES = (
    ('tools/probes/probe_owned_debugger.py', 'debugger_script',
     'Selected CPU registers do not resolve a loaded AVM body, defining scope, activation or uninterrupted this/root/parent generations.'),
    ('evidence/sampling-upgrade/s283/build_probe.py', 'instrument',
     'Candidate wrappers pass this as an owner argument to s283Value. This is not an independent scope/generation channel or a measurement of observer erasure.'),
    ('evidence/sampling-upgrade/s283/build_probe.py', 'build',
     'Compilation and pcode export produce disk artifacts only; they do not observe activation slots, live coercion or helper effects.'))


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('locked_s322', HERE.parent / 's322/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    retained = prior.diagnose()
    if json.loads(json.dumps(retained)) != json.loads((HERE.parent / 's322/diagnosis.json').read_text()):
        raise ValueError('Locked s322 replay changed')
    facilities = []
    for path, function, gap in FACILITIES:
        source = (ROOT / path).read_text()
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == function)
        facilities.append(dict(path=path, function=function, start_line=node.lineno,
                               end_line=node.end_lineno,
                               source='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]),
                               missing=gap, invoked=False))
    return dict(slice='s331', scope='AFTER-s326 rank #5 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                locked_s322_reproduced=True, replay_is_new_progress=False,
                facilities=facilities, independent_native_observations=0,
                historical_events_revalidated=retained['historical_events_revalidated'],
                observations={key: None for key in (
                    'loaded_body', 'invocation', 'defining_scope_generation',
                    'this_generation', 'root_generation', 'parent_generation',
                    'suppression_preload_visibility', 'activation_visibility',
                    'dashing_value_type', 'coercion_effects', 'helper_effects',
                    'off_on', 'external_callsite')},
                boundary_measurements=[dict(boundary=b, original=None, candidate=None,
                                            erasure=None) for b in (
                    'initialization', 'scope-member-access', 'intervening-call',
                    'first-overwrite', 'return-before-overwrite', 'body-end',
                    'dashing-read', 'coercion-and-branch')],
                helper_installed=False, off_on_controls_executed=False,
                gates={g: dict(proved=False, code='S331_'+g.upper().replace('-', '_')+'_UNPROVED')
                       for g in GATES},
                first_unmet_prerequisite='independent loaded body/invocation and defining scope with this/root/parent generations',
                blocker='Inspected adapters do not provide an independent live resolver or activation/coercion erasure measurement. Helper and off/on controls remain deferred before installation.',
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
        parser.exit(1, 'S331_EVIDENCE_INVALID: '+str(exc)+'\n')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    failures = [report['gates'][g]['code'] for g in GATES
                if getattr(args, 'require_'+g.replace('-', '_')) and not report['gates'][g]['proved']]
    print('; '.join(failures) if failures else
          'S331_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
