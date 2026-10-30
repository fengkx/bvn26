"""Audit authored-context controls without inferring a VM exit from silence."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_native import sha, validate_capture
from tools.sampling_callsite import collect_calls
from tools.sampling_chad_lifecycle import collect_lifecycle
from tools.sampling_doaction import collect, check_inventory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('s263_diagnose', HERE.parent / 's263/diagnose.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def controls(lines):
    keys = ('mode', 'before', 'receiver_before', 'defining_before', 'occupied_before',
            'empty_at_boundary', 'parent_frame', 'depth', 'boundary', 'post', 'empty_after')
    rows = []
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        if parts[6] != 's266_authored_control':
            continue
        values = parts[7].split(',')
        if len(values) != len(keys):
            raise ValueError('malformed control')
        rows.append(dict(zip(keys, values), sequence=int(parts[2]), tick=int(parts[5]), display=int(parts[4])))
    if [r['mode'] for r in rows] != ['retain', 'remove']:
        raise ValueError('missing, reordered or duplicate authored pair')
    for row in rows:
        removed = row['mode'] == 'remove'
        empty = 'true' if removed else 'false'
        expected = ('1', 'true', 'true', 'true', empty, '3' if removed else '2', '-16383', '1', '0' if removed else '1', empty)
        if tuple(row[k] for k in keys[1:]) != expected:
            raise ValueError('authored pair does not match independent slot and write observations')
    if any(r['tick'] != 10 for r in rows) or rows[0]['display'] != rows[1]['display'] or rows[1]['sequence'] != rows[0]['sequence'] + 1:
        raise ValueError('wrong authored control boundary')
    return rows


def compiled_worker(text):
    text = text.replace('\r\n', '\n')
    needle = ('Push register4\nPush 1\nPush register5\nPush undefined\nCallMethod\nPop\n'
              'Push register4\nPush "post"\nPush 1\nSetMember\n}')
    if text.count(needle) != 1 or 'Push register2\nStoreRegister 4\nPop' not in text:
        raise ValueError('missing register-only post-call write')
    if 'Push "defining"\nPush "this"\nGetVariable\nDefineLocal' not in text:
        raise ValueError('missing defining timeline binding')
    return needle


def diagnose():
    old = previous.diagnose()
    meta = json.loads((HERE / 'native-build.json').read_text())
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(meta['move_case'], meta, trace)
    lines = raw.decode().splitlines()
    old_meta = json.loads((HERE.parent / 's263/native-build.json').read_text())
    old_lines = gzip.decompress((HERE.parent / 's263/native-capture.log.gz').read_bytes()).decode().splitlines()
    assert meta['move_case'] == old_meta['move_case']
    assert previous.previous.states(lines) == previous.previous.states(old_lines)
    rows = controls(lines)
    dynamic = previous.controls(lines)
    witnesses = previous.previous.observations(lines)
    assert all(r['post'] == r['observer_entry'] == '0' for r in witnesses[1:])
    lifecycle = collect_lifecycle(lines)
    calls = collect_calls(lines, meta['callsite_specification'], retain_incomplete=True)
    actions = collect(lines, meta['run_id'], 60, check_inventory(meta))
    assert lifecycle['missing_boundaries'] == old['lifecycle']['missing_boundaries']
    assert len(calls['incomplete_invocations']) == 1
    assert calls['incomplete_invocations'][0]['observer_tick'] == 10
    assert sha(HERE.parent / 's263/build-extension.tar.gz') == meta['s266_control']['base_archive_sha256']
    with tarfile.open(HERE.parent / 's257/native-build.tar.gz') as base, tarfile.open(HERE / 'build-extension.tar.gz') as extension:
        names = set(extension.getnames())
        for path, digest in meta['outputs_sha256'].items():
            archive = extension if path in names else base
            assert hashlib.sha256(archive.extractfile(path).read()).hexdigest() == digest
        assert json.loads(extension.extractfile('build.json').read()) == meta
        assert hashlib.sha256(extension.extractfile('instrumentation.diff').read()).hexdigest() == meta['instrumentation_sha256']
    for path, digest in meta['sources_sha256'].items():
        assert sha(ROOT / path) == digest
    assert meta['outputs_sha256']['game/fighter/chad.swf'] == old_meta['outputs_sha256']['game/fighter/chad.swf']
    provenance = json.loads((HERE / 'pcode-provenance.json').read_text())
    assert provenance['main_sha256'] == meta['outputs_sha256']['game/main.swf']
    for path, digest in provenance['exports_sha256'].items():
        assert sha(HERE / path) == digest
    sequence = compiled_worker(gzip.decompress((HERE / 'worker.pcode.gz').read_bytes()).decode())
    return dict(production_admitted=False, native_parity_proven=False, exit_model_fix_proved=False,
                executed_pc_trace=False, exact_chad_context_invalidation_access_proved=False,
                authored_retained_register_write_observed=True, authored_removed_register_write_observed=False,
                events=len(lines), root_samples=len(actions['samples']), controls=rows, dynamic_controls=dynamic,
                chad_witnesses=witnesses, chad_swf_unchanged=True,
                actor_comparison=dict(rows=len(previous.previous.states(lines)), exact_tick_payload_equal_s263=True),
                compiled_control_sequence=sequence, lifecycle=lifecycle,
                incomplete_invocations=calls['incomplete_invocations'],
                full_as=dict(unvisited=len(actions['unvisited']), uninstrumented=len(actions['uninstrumented'])),
                boundary_window=lines[dynamic[0]['sequence']-1:witnesses[-1]['sequence']],
                limit='Synthetic authored child, not Chad activation. Retained post=1; removed post=0 is an absent write, not a return, unwind or executed-PC record. AS2 defining-reference equality does not expose VM activation identity.',
                next_discriminator='Native executed-PC, operand stack and defining activation records at exact Chad gotoAndPlay CallMethod, following Pop and register5 SetMember, paired with retained same-context execution. No additional absent marker or synthetic return closes this gap.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-exact-continuation', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_exact_continuation and not report['exact_chad_context_invalidation_access_proved']:
        print('S266_EXACT_CONTINUATION_UNPROVED production_admitted=false native_parity_proven=false')
        raise SystemExit(1)
    print('S266_EVIDENCE_OK production_admitted=false native_parity_proven=false')
