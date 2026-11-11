"""Assess retained boundary applicability without inventing native field meaning."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('r28_prior', HERE.parent / 'native-fight-r26/analyze.py')
r26 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r26)
FLAGS = r26.FLAGS


def check_plan(schema, plan):
    if schema.get('schema_verified') is not False or plan.get('qualified') is not False:
        raise ValueError('Unexecuted design cannot be marked verified')
    expected = {'loaded_body', 'owner', 'owner_generation', 'closure_generation',
                'activation', 'transition_edge', 'dispatcher_outcome', 'body_target'}
    if {f['name'] for f in schema['fields']} != expected or len(schema['fields']) != len(expected):
        raise ValueError('Identity requirements missing/duplicated')
    for field in schema['fields']:
        if any(field[k] is not None for k in ['native_location', 'verified_type', 'independent_witness']):
            raise ValueError('No qualified native field mapping in this evidence set')
    if len(plan['stages']) != 5 or any(s['performed'] for s in plan['stages']):
        raise ValueError('Preservation controls not executed in this slice')


def call_interval(code, tag):
    start = 'Push "M002LITERAL|' + tag + '|doAllAction|before"'
    end = 'Push "M002LITERAL|' + tag + '|doAllAction|after"'
    if code.count(start) != 1 or code.count(end) != 1:
        raise ValueError('Nonunique retained call interval')
    result = code[code.index(start):code.index(end) + len(end)]
    if result.count('CallMethod') != 1 or 'Push "砍1"' not in result or 'Push "gotoAndPlay"' not in result:
        raise ValueError('Retained callsite mismatch')
    if any(op in result.split() for op in ['Return', 'Jump']):
        raise ValueError('Unexpected control flow in retained interval')
    return result


def replay():
    for name, digest in json.loads((HERE / 'input-pins.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned input changed: ' + name)
    def read(name):
        return json.loads((ROOT / name).read_text())
    schema = json.loads((HERE / 'identity-requirements.json').read_text())
    plan = json.loads((HERE / 'preservation-plan.json').read_text())
    check_plan(schema, plan)
    build = read('evidence/oracle/native-fight-r25/build.json')
    code_raw = gzip.decompress((HERE.parent / 'native-fight-r26/decision.pcode.gz').read_bytes())
    bytecode = read('evidence/oracle/native-fight-r26/bytecode-receipt.json')
    if hashlib.sha256(code_raw).hexdigest() != bytecode['exports']['decision']['sha256'] or bytecode['swf_sha256'] != build['outputs_sha256']['game/fighter/yihu.swf']:
        raise ValueError('P-code/live build identity mismatch')
    routes = {s: read('evidence/sampling-upgrade/' + s + '/native-route.json') for s in ['s350', 's357', 's366']}
    for route in routes.values():
        if route['binary_sha256'] != read('evidence/importer-loud-fail/r244/retry/debugger/feasibility.json')['binary_sha256']:
            raise ValueError('Player mismatch')
        if route['loaded_closure_body'] is not None or route['native_observations']:
            raise ValueError('Retained candidate assumptions changed; reassessment required')
    prior = r26.replay()
    return dict(**FLAGS, status='native-boundary-and-schema-still-unjustified',
                qualified_native_boundary=None, identity_schema_verified=False,
                preservation_plan_executed=False, native_return_proven=False,
                source_call_interval=call_interval(code_raw.decode(), build['run_id']),
                source_interval_means='Encoded inner CallMethod, not observed native entry or outer clip-event return',
                candidates=[
                    dict(id='s350', file_offset=hex(routes['s350']['target']), meaning='Retained numeric ActionReturn arm',
                         applicable=False, refusal='Generic explicit opcode arm lacks loaded body/activation binding; not the inner goto call or general outer fallthrough/unwind boundary.'),
                    dict(id='s357', file_offset=hex(routes['s357']['target']), meaning='Retained continuation of s350 nonzero branch',
                         applicable=False, refusal='Untyped memory operands, no owner/generation/activation meaning; archived root callback target differs from gameplay clip-event invocation.'),
                    dict(id='s366', unslid_candidate=hex(routes['s366']['local_decode']['start']),
                         reachable_instruction_boundary=routes['s366']['local_decode']['instruction_boundary_from_function_entry_proven'],
                         applicable=False, refusal='onEnterFrame string operand is not clip-event/goto identity; reachability and field semantics unproved.')],
                identity_requirements=schema, preservation_plan=plan,
                structural_refusal=prior['structural_refusal'], r25_join_refusal=prior['targets'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--require-oracle', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    result = replay()
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(result['status'])
    print(result['structural_refusal'])
    raise SystemExit(1)
