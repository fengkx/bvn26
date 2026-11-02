"""Audit the complete body-push candidate CFG; fail closed before capture."""
import argparse
import difflib
import hashlib
import gzip
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_prior():
    spec = importlib.util.spec_from_file_location('s283_prior', HERE.parent / 's273/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.diagnose()


def project(source):
    """Keep every opcode, operand and function flag; resolve all branch edges."""
    lines = re.sub(r'(loc[0-9a-f]+):', r'\1:\n', source).splitlines()
    header = lines.pop(0)
    if not header.startswith('DefineFunction2 "on_enterframe",') or lines.pop() != '}':
        raise ValueError('incomplete function envelope')
    instructions, labels = [], {}
    for line in lines:
        if not line:
            continue
        if line.endswith(':'):
            if line[:-1] in labels:
                raise ValueError('duplicate label')
            labels[line[:-1]] = len(instructions)
        elif line.startswith('Push '):
            # CSV parsing keeps operand type separate from its textual value.
            for token in re.findall(r'"(?:[^"\\]|\\.)*"|[^,]+', line[5:]):
                token = token.strip()
                if not token.startswith('"'):
                    token = re.sub(r'^(-?\d+)\.0$', r'\1', token)
                instructions.append('Push ' + token)
        else:
            instructions.append(line)
    nodes = []
    for index, instruction in enumerate(instructions):
        if instruction.startswith(('If ', 'Jump ')):
            label = instruction.split()[1]
            if label not in labels:
                raise ValueError('unresolved branch')
            target = labels[label]
            instruction = instruction.split()[0] + ' ' + str(target)
            successors = [target] + ([index + 1] if instruction.startswith('If ') else [])
        else:
            successors = [] if instruction == 'Return' else [index + 1]
        nodes.append({'index': index, 'instruction': instruction, 'successors': successors})
    return {'header': header, 'nodes': nodes, 'exit_index': len(nodes)}


def source_window(projection):
    ins = [n['instruction'] for n in projection['nodes']]
    hits = [i for i, v in enumerate(ins) if v == 'Push "hitTest"']
    if len(hits) != 1 or ins[hits[0]+1] != 'CallMethod':
        raise ValueError('expected exactly one native hitTest')
    hit = hits[0]
    start = ins.index('Push "airBody"')
    window = ins[start:hit+2]
    if window.count('PushDuplicate') != 2 or 'And' in window:
        raise ValueError('changed short-circuit guards')
    if window[-6:] != ['GetMember', 'Push 1', 'Push "bdmn"', 'GetVariable', 'Push "hitTest"', 'CallMethod']:
        raise ValueError('changed target-before-receiver evaluation')
    return {'start_index':start, 'call_index':hit+1,
            'nodes':projection['nodes'][start:hit+2],
            'short_circuit_guards_proved':True, 'target_before_receiver_proved':True}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input hash mismatch: ' + path)
    spec = importlib.util.spec_from_file_location('s283_builder', HERE / 'build_probe.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    for name in ('original', 'candidate'):
        full = gzip.decompress((HERE / (name + '.frame.pcode.gz')).read_bytes()).decode()
        if builder.function_pcode(full) != (HERE / (name + '.pcode')).read_text():
            raise ValueError('function extraction or terminal label mismatch')
    prior = load_prior()
    if prior != json.loads((HERE.parent / 's273/diagnosis.json').read_text()):
        raise ValueError('historical replay changed')
    original = project((HERE / 'original.pcode').read_text())
    candidate = project((HERE / 'candidate.pcode').read_text())
    window = source_window(original)
    # Do not silently alpha-rename registers: preload flags and all uses need proof.
    header_equal = original['header'] == candidate['header']
    diff = list(difflib.unified_diff(
        [original['header']] + [n['instruction'] for n in original['nodes']],
        [candidate['header']] + [n['instruction'] for n in candidate['nodes']],
        fromfile='original', tofile='candidate', lineterm=''))
    return {'base':'d840168c4c70e170d2a443844e508d0a66b53739', 'rank':2,
            'scope':'AFTER-s281 rank 2 only; P2 base Sprite638 ticks10-12',
            'production_admitted':False, 'native_parity_proven':False,
            'observer_qualified':False, 'external_callsite_execution_proved':False,
            'eligibility_fix_proved':False, 'product_obligations_closed':0,
            'new_player_launches':0, 'new_captures':0,
            'historical_events_revalidated':prior['observed']['events'],
            'historical_samples':prior['observed']['p2_body_samples'],
            'historical_execution_observed':prior['site']['execution_observed'],
            'source_window':window, 'original_projection':original,
            'candidate_projection':candidate, 'function_header_equal':header_equal,
            'complete_projection_diff':diff,
            'blockers':[
                'Candidate changes DefineFunction2 register count/preload flags; register and activation correspondence is not qualified.',
                'All candidate instructions and branch edges are retained, but observer erasure and complete original/candidate equivalence are not proved.',
                'Candidate helper is not installed or executed; logging side effects, once-evaluated live operand lifetime and natural executed/skipped controls are unproved.'
            ],
            'capture_decision':'Do not launch: qualification failed before constructing a capture-ready build.',
            'next_discriminator':'Prove the complete register/preload/observer-erasure correspondence or retain original bytecode with qualified stack-preserving instrumentation; then qualify the bounded helper and one unchanged s64 capture. No extra hitTest or forced branch.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-observer', action='store_true')
    parser.add_argument('--require-external-callsite', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print('S283_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    if args.require_observer or args.require_external_callsite:
        print('UNPROVED: ' + '; '.join(report['blockers']))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
