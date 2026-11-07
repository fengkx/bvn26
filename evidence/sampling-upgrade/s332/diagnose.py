"""Audit the rank-6 replacement-surviving callback prerequisite; never infer outer return."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('independent-channel', 'logger-replacement', 'callback-completion',
         'off-on', 'terminal-completeness')
FACILITIES = (
    ('tools/probes/probe_owned_debugger.py', 'debugger_script',
     'Host receipt does not use aiEvent, but selected CPU registers have no loaded AVM closure/body resolver, owner generation, activation identity or matched dispatcher continuation.'),
    ('tools/probes/probe_owned_debugger.py', 'probe',
     'Owned PID and disk hashes bind process/build custody only. Run-profile waiting uses AIREF; script_factory and post_debugger are extension hooks, not implemented callback identity or replacement-survival witnesses.'),
    ('evidence/sampling-upgrade/s284/build_probe.py', 'defer_quit',
     'Moves quit past logger replacement in source only. This does not observe execution, distinguish unwind/termination/return, or qualify observer off/on.'))


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('locked_s323', HERE.parent / 's323/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    retained = prior.diagnose()
    if json.loads(json.dumps(retained)) != json.loads((HERE.parent / 's323/diagnosis.json').read_text()):
        raise ValueError('Locked s323 replay changed')
    facilities = []
    for path, function, gap in FACILITIES:
        source = (ROOT / path).read_text()
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == function)
        facilities.append(dict(path=path, function=function, start_line=node.lineno,
                               end_line=node.end_lineno,
                               source='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]),
                               missing=gap, invoked=False))
    return dict(slice='s332', scope='AFTER-s326 rank #6 only',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                locked_s323_reproduced=True, replay_is_new_progress=False,
                facilities=facilities, independent_native_observations=0,
                retained_validation_not_new_progress=retained['retained_validation_not_new_progress'],
                qualification_requirements=retained['qualification_requirements'],
                observations={key: None for key in (
                    'loaded_closure_body', 'owner_generation', 'defining_scope_generation',
                    'closure_generation', 'activation_entry', 'logger_replacement',
                    'matched_dispatcher_continuation', 'outcome', 'replacement_survival',
                    'observer_off', 'observer_on', 'off_on_preservation')},
                independently_observed_live_invocations=[],
                off_on_controls_executed=False, terminal_inventory_executed=False,
                full_as_proven=False, fixed_suffix_threshold=None,
                gates={g: dict(proved=False, code='S332_'+g.upper().replace('-', '_')+'_UNPROVED')
                       for g in GATES},
                first_unmet_prerequisite='independent loaded closure/body, owner generation and activation through dispatcher continuation after logger replacement',
                blocker='Inspected adapters supply no live identity resolver or matched continuation channel. Off/on qualification and terminal inventory remain deferred; no live proof is inferred from a host sink independent of aiEvent.',
                search_scope='Only the three named adapter functions plus locked s323 replay; not an exhaustive facility search.',
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
        parser.exit(1, 'S332_EVIDENCE_INVALID: '+str(exc)+'\n')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    failures = [report['gates'][g]['code'] for g in GATES
                if getattr(args, 'require_'+g.replace('-', '_')) and not report['gates'][g]['proved']]
    print('; '.join(failures) if failures else
          'S332_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
