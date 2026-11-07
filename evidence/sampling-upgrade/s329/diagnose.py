"""Report the rank-3 binding prerequisite without installing an observer."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('activation-scope', 'activation-erasure', 'observer')


def diagnose():
    for name, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)
    spec = importlib.util.spec_from_file_location('locked_s318', HERE.parent / 's318/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    if prior.diagnose() != json.loads((HERE.parent / 's318/diagnosis.json').read_text()):
        raise ValueError('Locked s318 replay changed')
    facilities = []
    for path, function, gap in (
        ('tools/probes/probe_owned_debugger.py', 'debugger_script',
         'Selected frame-zero CPU registers do not resolve AVM activation, defining scope, slot lifetime or boundary execution.'),
        ('tools/probes/yulong_k1atm_observer.py', 'instrument_source',
         'Appends aiK1Observe after source stamp; AS receiver/path and parent pn do not independently bind activation or defining scope.'),
        ('tools/probes/yulong_k1atm_observer.py', 'instrument_geometry',
         'Adds aiK1Observe at source-list check, not an independent initialization/opaque-operation/return channel.')):
        source = (ROOT / path).read_text()
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == function)
        excerpt = '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])
        facilities.append(dict(path=path, function=function, start_line=node.lineno,
                               end_line=node.end_lineno, source=excerpt, missing=gap, invoked=False))
    return dict(slice='s329', scope='AFTER-s326 rank #3 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                locked_s318_reproduced=True, replay_is_new_progress=False,
                facilities=facilities, independent_native_observations=0,
                bindings=[dict(boundary=b, original_activation=None, candidate_activation=None,
                               original_defining_scope=None, candidate_defining_scope=None,
                               erasure_measurement=None) for b in
                          ('initialization', 'enumeration', 'member-access', 'coercion', 'overwrite', 'no-overwrite-null-return')],
                gates={g:dict(proved=False, code='S329_'+g.upper().replace('-', '_')+'_UNPROVED') for g in GATES},
                blocker='No independent activation/scope resolver or paired erasure measurement is available in the inspected adapters. Observer controls are deferred before installation.',
                new_builds=0, new_player_launches=0, new_captures=0,
                product_obligations_closed=0, other_ranks_executed=[])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-'+gate, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S329_EVIDENCE_INVALID: '+str(exc)+'\n')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    failures = [report['gates'][g]['code'] for g in GATES if getattr(args, 'require_'+g.replace('-', '_'))]
    print('; '.join(failures) if failures else 'S329_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
