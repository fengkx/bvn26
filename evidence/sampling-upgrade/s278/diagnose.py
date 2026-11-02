"""Bind the Chad observation sites and audit the missing native AVM1 resolver."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHAD = 'evidence/sampling-upgrade/s257/pcode/chad/DefineSprite_16/frame_1/DoAction.pcode.gz'
CHAD_SEQUENCE = ('Push "砍1"\nPush 1\nPush register2\nPush "gotoAndPlay"\nCallMethod\nPop\n'
                 'Push register5\nPush "post"\nPush 1\nSetMember')
CONTROL_SEQUENCE = ('Push register4\nPush 1\nPush register5\nPush undefined\nCallMethod\nPop\n'
                    'Push register4\nPush "post"\nPush 1\nSetMember')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def site(text, sequence):
    text = text.replace('\r\n', '\n')
    if text.count(sequence) != 1:
        raise ValueError('missing or ambiguous instruction window')
    start = text[:text.index(sequence)].count('\n') + 1
    return {'coordinate_kind': 'one-based exported text line, NOT executed PC or byte offset',
            'instructions': [{'line': start + index, 'instruction': instruction}
                             for index, instruction in enumerate(sequence.splitlines())]}


def facility():
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    reports = {}
    for directory in ('rejected-query', 'facility', 'entry-sandbox', 'entry-unsandboxed'):
        report = json.loads((HERE / directory / 'audit.json').read_text())
        if report['binary_sha256'] != receipt['files'][report['binary']]:
            raise ValueError('player differs from s266 receipt')
        for check in report['checks'].values():
            raw = (HERE / directory / check['log']).read_bytes()
            if digest(raw) != check['sha256']:
                raise ValueError('changed facility transcript')
        reports[directory] = report
    pending = (HERE / 'facility/instruction-breakpoints.txt').read_text()
    entry = (HERE / 'entry-unsandboxed/native-entry.txt').read_text()
    if 'locations = 0 (pending)' not in pending:
        raise ValueError('unexpected breakpoint qualification; review new evidence')
    if not all(s in entry for s in ('dyld`_dyld_start', 'rip =', 'rsp =', 'rbp =', 'process kill', 'killed')):
        raise ValueError('missing owned entry-stop/register/termination observation')
    return reports


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('changed pinned input: ' + path)
    spec = importlib.util.spec_from_file_location('s278_prior_s266', HERE.parent / 's266/diagnose.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    old = previous.diagnose()
    raw = gzip.decompress((HERE.parent / 's266/native-capture.log.gz').read_bytes())
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    if digest(raw) != receipt['files'][receipt['trace']]:
        raise ValueError('historical complete trace differs from receipt')
    chad = site(gzip.decompress((ROOT / CHAD).read_bytes()).decode(), CHAD_SEQUENCE)
    control = site(gzip.decompress((HERE.parent / 's266/worker.pcode.gz').read_bytes()).decode(), CONTROL_SEQUENCE)
    return {'scope': 'AFTER-s272 rank 6 only', 'base': '783e69d7',
            'production_admitted': False, 'native_parity_proven': False,
            'native_instruction_activation_facility_qualified': False,
            'exact_continuation_proved': False, 'product_obligations_closed': 0,
            'historical': {'events': old['events'], 'root_samples': old['root_samples'],
                           'controls': old['controls'], 'dynamic_controls': old['dynamic_controls'],
                           'chad_witnesses': old['chad_witnesses'],
                           'actor_comparison': old['actor_comparison'], 'full_as': old['full_as'],
                           'missing_boundaries': old['lifecycle']['missing_boundaries']},
            'sites': {'chad': dict(chad, artifact=CHAD, source='DefineSprite_16/frame_1/DoAction.as',
                                   note='Original goto call in archived instrumented Chad; post write is s257 instrumentation.'),
                      'retained_control': dict(control, artifact='evidence/sampling-upgrade/s266/worker.pcode.gz',
                                               note='Synthetic authored context; operation call, not equivalent Chad activation.')},
            'facility': facility(),
            'native_cpu_entry_stop_observed': True,
            'native_avm1_pc': None, 'operand_stack': None, 'defining_activation': None,
            'executed_retained_control': None,
            'new_swf_builds': 0, 'new_movie_captures': 0,
            'debugger_launch_attempts': 2, 'confirmed_entry_stops': 1,
            'missing': ['byte-pinned native dispatch/AVM1 PC resolver',
                        'operand stack and register5 witness mapping',
                        'defining activation identity and observed lifetime',
                        'same resolver qualified on retained authored context'],
            'next_discriminator': 'Resolve native AVM1 dispatch and activation layout on the pinned binary; bind the loaded action buffer to archived Chad bytes, then observe CallMethod, next Pop and register5 SetMember in one activation. First qualify the resolver on s266 retained authored control (register4 post=1), then inspect Chad with unchanged tape. Record an actual unwind/invalidation transition if the next instruction is not reached; silence is not a return.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-native-continuation', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_native_continuation:
        print('S278_NATIVE_CONTINUATION_UNPROVED: ' + '; '.join(report['missing']))
        return 1
    print('S278_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
