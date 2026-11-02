"""Audit the retained authored worker's unresolved buffer/cursor/activation join."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXCLUSIONS = ['CPU-entry-as-AVM proof', 'silence/removal-as-return',
              'root-worker equivalence', 'broad interpreter', 'other ranks']
GATES = {
    'loaded-buffer': 'S295_LOADED_BUFFER_UNPROVED',
    'cursor-convention': 'S295_CURSOR_CONVENTION_UNPROVED',
    'retained-activation': 'S295_RETAINED_ACTIVATION_UNPROVED',
    'instruction-boundaries': 'S295_INSTRUCTION_BOUNDARIES_UNPROVED',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prior_module():
    spec = importlib.util.spec_from_file_location('s288_locked', HERE.parent / 's288/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cursor_candidates(site):
    """Enumerate file-relative hypotheses, never infer a loaded buffer base."""
    body = site['definition']['body_offset']
    rows = site['instructions']
    if any(a['end'] != b['offset'] for a, b in zip(rows, rows[1:])):
        raise ValueError('noncontiguous instruction window')
    selected = []
    for row in rows:
        if row['instruction'] not in ('CallMethod', 'Pop', 'SetMember'):
            continue
        if row['hex'] != {'CallMethod': '52', 'Pop': '17', 'SetMember': '4f'}[row['instruction']]:
            raise ValueError('unexpected instruction bytes')
        selected.append(dict(instruction=row['instruction'], hex=row['hex'],
            current_opcode_file_offset=row['offset'], next_opcode_file_offset=row['end'],
            current_body_relative=row['offset'] - body, next_body_relative=row['end'] - body))
    if [r['instruction'] for r in selected] != ['CallMethod', 'Pop', 'SetMember']:
        raise ValueError('missing three instruction boundaries')
    return selected


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = prior_module()
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's288/diagnosis.json').read_text()):
        raise ValueError('s288 diagnosis changed')
    site = replay['static_sites']['authored_control']
    with tarfile.open(HERE.parent / site['archive']) as archive:
        raw = archive.extractfile(site['member']).read()
    data, start, end = prior.action_block(raw, site['sprite'])
    definition = site['definition']
    body_start = definition['body_offset']
    body = data[body_start:body_start + definition['body_length']]
    if sha(body) != definition['body_sha256']:
        raise ValueError('worker body differs')
    candidates = cursor_candidates(site)
    facility = json.loads((HERE / 'facility.json').read_text())
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    if facility['binary_sha256'] != receipt['files'][facility['binary']]:
        raise ValueError('facility binary differs from receipt')
    for check in facility['checks']:
        if sha((HERE / check['log']).read_bytes()) != check['sha256']:
            raise ValueError('facility transcript changed')
        if check['exit'] != 1:
            raise ValueError('new lookup result needs review')
    return dict(base='0f6610ab', scope='AFTER-s290 rank #5 only',
        production_admitted=False, native_parity_proven=False, product_obligations_closed=0,
        exact_continuation_proved=False, locked_s288_reproduced=True,
        historical=replay['historical'], facility=facility,
        retained_worker=dict(archive=site['archive'], member=site['member'],
            swf_sha256=site['swf_sha256'], definition=definition,
            body_hex=body.hex(), body_occurrences_in_archived_swf=data.count(body),
            doaction_file_range=[start, end], cursor_candidates=candidates,
            coordinate_kind='Uncompressed archived file/body offsets; NOT loaded buffer addresses',
            ambiguous_file_offset=candidates[0]['next_opcode_file_offset'],
            ambiguity='CallMethod next cursor equals Pop current cursor; static bytes cannot select convention',
            activation_limit='Retain and remove invoke the same authored function; body identity is not invocation identity'),
        observations={key: None for key in ('loaded_action_buffer', 'native_dispatch_pc',
            'cursor_convention', 'retained_activation', 'operand_stack', 'register4_witness',
            'executed_callmethod', 'executed_pop', 'executed_setmember')},
        gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
        new_builds=0, new_player_launches=0, new_captures=0, exclusions=EXCLUSIONS,
        blocker='No byte-derived native buffer/cursor/activation resolver; lookup queries found no matches. '
                'Retained authored activation must be resolved before three executed instruction boundaries.',
        next_observation='Derive module-relative dispatch and activation layout on the receipt-pinned binary; '
            'bind actual loaded bytes and buffer extent to this body, measure current/next cursor, '
            'then identify one retained invocation with scope/register4 witness and operand stack. '
            'Only then observe CallMethod, Pop and SetMember; keep removed and root-defined controls separate.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failed = [code for gate, code in GATES.items() if getattr(args, 'require_' + gate.replace('-', '_'))]
    if failed:
        parser.exit(1, '; '.join(failed) + ': ' + report['blocker'] + '\n')
    print('S295_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
