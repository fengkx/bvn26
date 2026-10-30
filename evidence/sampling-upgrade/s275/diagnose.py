"""Replay the exclusive s275 operand/owner observations without admitting a fix."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
import tempfile
from urllib.parse import unquote

from tools.sampling_native import validate_capture
from tools.sampling_geometry import collect

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pcode_projection(source, observed=False):
    if observed:
        source = re.sub(r'Push "(?:target[1-5]|receiver[1-5]|result[1-5]|pause|played)"\nPush 2\nPush "_root"\nGetVariable\nPush "s275Value"\nCallMethod\n', '', source)
        source = re.sub(r'Push "this"\nGetVariable\nPush "(?:before_goto|after_goto)"\nPush 2\nPush "_root"\nGetVariable\nPush "s275Boundary"\nCallMethod\nPop\n', '', source)
    source = re.sub(r'(loc[0-9a-f]+):', r'\1:\n', source)
    instructions, labels = [], {}
    for line in source.splitlines():
        if not line or line.startswith('ConstantPool '):
            continue
        if line.endswith(':'):
            labels[line[:-1]] = len(instructions)
        elif line.startswith('Push '):
            for value in next(csv.reader([line[5:]], skipinitialspace=True)):
                instructions.append('Push ' + re.sub(r'^(\d+)\.0$', r'\1', value))
        else:
            instructions.append(line)
    return [re.sub(r'loc[0-9a-f]+', lambda m: str(labels[m[0]]), line) for line in instructions]


def observations(lines):
    rows = []
    for line in lines:
        p = line.split('|', 7)
        if p[6].startswith('s275_'):
            if not 15 <= int(p[5]) <= 22:
                raise ValueError('out of scope observation')
            rows.append({'sequence': int(p[2]), 'tick': int(p[5]), 'kind': p[6],
                         'fields': [unquote(v) for v in p[7].split(',')]})
    values = [r for r in rows if r['kind'] == 's275_value']
    boundaries = [r for r in rows if r['kind'] == 's275_boundary']
    expected = ['pause'] + [s + str(i) for i in range(1, 6) for s in ('target', 'receiver', 'result')]
    for tick in range(16, 21):
        got = [r['fields'][0] for r in values if r['tick'] == tick]
        if got != expected + (['played'] if tick == 18 else []):
            raise ValueError('missing or reordered operand evaluation')
    if [r['tick'] for r in boundaries if r['fields'][0] == 'root_slot'] != list(range(15, 23)):
        raise ValueError('missing parent slot observation')
    by_phase = {r['fields'][0]: r for r in boundaries if r['fields'][0] != 'root_slot'}
    if list(by_phase) != ['before_goto', 'after_goto', 'before_rename', 'after_rename']:
        raise ValueError('missing lifecycle boundary')
    outer = '_level0.game.p1.mc.k1atm'
    before, after = by_phase['before_goto'], by_phase['after_goto']
    if (before['tick'], after['tick'], before['fields'][5:7], after['fields'][5:7], after['fields'][1]) != (18, 18, [outer+'.mian']*2, ['undefined']*2, outer):
        raise ValueError('changed child removal boundary')
    before, after = by_phase['before_rename'], by_phase['after_rename']
    if (before['tick'], after['tick'], before['fields'][1], after['fields'][1], before['fields'][3], after['fields'][3]) != (19,19,outer,'_level0.game.p1.mc.abcd','70','70'):
        raise ValueError('changed rename boundary')
    return {'values': values, 'boundaries': boundaries}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input hash mismatch: ' + path)
    original = (HERE / 'original.pcode').read_text()
    observed = (HERE / 'observed.pcode').read_text()
    if pcode_projection(original) != pcode_projection(observed, True):
        raise ValueError('changed projected opcode/control-flow sequence')
    if original.splitlines().count('Or') != 4:
        raise ValueError('changed eager Or chain')
    meta = json.loads((HERE / 'native-build.json').read_text())
    receipt = json.loads((HERE / 'native-receipt.json').read_text())
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.loads(archive.extractfile('build.json').read()) != meta:
            raise ValueError('archived metadata mismatch')
        for path, expected in meta['outputs_sha256'].items():
            actual = digest(archive.extractfile(path).read())
            if actual != expected or actual != receipt['files'][receipt['build'] + '/' + path]:
                raise ValueError('archived output mismatch')
        if digest(archive.extractfile('instrumentation.diff').read()) != meta['instrumentation_sha256']:
            raise ValueError('archived instrumentation mismatch')
    for path, expected in meta['sources_sha256'].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('changed build source')
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    if digest(raw) != receipt['files'][receipt['trace']]:
        raise ValueError('raw receipt mismatch')
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'; trace.write_bytes(raw)
        validate_capture(meta['move_case'], meta, trace)
    lines = raw.decode().splitlines()
    observed_rows = observations(lines)
    old = gzip.decompress((HERE.parent / 's247/native-capture.log.gz').read_bytes()).decode().splitlines()
    def payloads(rows, kind):
        return [(int(p[5]), p[7]) for line in rows if (p := line.split('|', 7))[6] == kind and int(p[5]) >= 0]
    states = payloads(lines, 'state')
    if len(states) != 122 or states != payloads(old, 'state'):
        raise ValueError('changed actor states on unchanged tape')
    sources = set()
    for path in meta['sources_sha256']:
        if path.startswith('scripts/'):
            bundle = json.loads((ROOT / path).read_text())
            sources.update(bundle['game_file'] + '#' + s['path'] for s in bundle['scripts'])
    try:
        collect(lines, meta['run_id'], meta['move_case']['frames'], sources)
    except ValueError as error:
        geometry_error = str(error)
    else:
        raise ValueError('expected unresolved geometry rejection absent')
    return {'scope':'AFTER-s272 rank 3 only; frame188 ticks15-22', 'base':'af2ddb59',
            'production_admitted':False, 'native_parity_proven':False,
            'runtime_binding_proved':False, 'product_obligations_closed':0,
            'events':len(lines), 'actor_rows_equal_s247':len(states),
            'input_rows':len(payloads(lines,'input_next_display')),
            'input_rows_equal_s247':payloads(lines,'input_next_display') == payloads(old,'input_next_display'),
            'key_read_rows':len(payloads(lines,'key_read')),
            'key_read_rows_equal_s247':payloads(lines,'key_read') == payloads(old,'key_read'),
            'random_rows_equal_s247':payloads(lines,'random') == payloads(old,'random'),
            'opcode_projection_equal':True, 'original_or_is_eager':True,
            'observation':observed_rows, 'geometry_exit_code':1, 'geometry_error':geometry_error,
            'limits':['Pass-through calls preserve projected opcodes and native receiver binding, not wall-clock timing or all VM internals.',
                      'No direct parent-removal hook: depth28 occupied at root21, absent at root22; exact removal PC unobserved.',
                      'No allocation identity or exhaustive nested function invocation/eligibility proof.',
                      'No Godot comparison or production repair; undefined operands retained.'],
            'next_discriminator':'Within the same placement, correlate source-authored depth28 removal dispatch with owner/child operand lifetimes and direct invocation of nested receiver functions; qualify pass-through timing perturbation before deriving any eligibility rule. No extra hitTests, ancestor pn, aliases or other chains.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-runtime-binding', action='store_true')
    parser.add_argument('--require-geometry', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('S275_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    if args.require_runtime_binding or args.require_geometry:
        print('UNPROVED: ' + (report['geometry_error'] if args.require_geometry else '; '.join(report['limits'])))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
