"""Audit a positive dynamic-removal control without selecting Chad's exit model."""
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
spec = importlib.util.spec_from_file_location('s257_diagnose', HERE.parent / 's257/diagnose.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def controls(lines):
    rows = []
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        if parts[6] != 's263_register_control':
            continue
        values = parts[7].split(',')
        if len(values) != 8:
            raise ValueError('malformed control')
        rows.append(dict(zip(('mode', 'before', 'receiver_before', 'occupied_before',
                              'empty_at_boundary', 'boundary', 'post', 'empty_after'), values),
                         sequence=int(parts[2]), tick=int(parts[5]), display=int(parts[4])))
    if [r['mode'] for r in rows] != ['retain', 'remove']:
        raise ValueError('missing, reordered or duplicate control')
    for row in rows:
        empty = 'true' if row['mode'] == 'remove' else 'false'
        if tuple(row[k] for k in ('before', 'receiver_before', 'occupied_before',
                                 'empty_at_boundary', 'boundary', 'post', 'empty_after')) != (
                                     '1', 'true', 'true', empty, '1', '1', empty):
            raise ValueError('control did not establish observed removal and continuation')
    if rows[0]['tick'] != 10 or rows[1]['tick'] != 10 or rows[0]['display'] != rows[1]['display']:
        raise ValueError('wrong control boundary')
    if rows[1]['sequence'] != rows[0]['sequence'] + 1:
        raise ValueError('interrupted control pair')
    return rows


def compiled_control(text):
    text = text.replace('\r\n', '\n')
    needle = ('Push register4\nPush 1\nPush register5\nPush undefined\nCallMethod\nPop\n'
              'Push register4\nPush "post"\nPush 1\nSetMember\n}')
    if text.count(needle) != 1 or 'Push register2\nStoreRegister 4\nPop' not in text:
        raise ValueError('missing register-bound continuation')
    if 'Push "removeMovieClip"\nCallMethod\nPop' not in text:
        raise ValueError('missing compiled removal')
    return needle


def diagnose():
    old = previous.diagnose()
    metadata = json.loads((HERE / 'native-build.json').read_text())
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes())
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(metadata['move_case'], metadata, trace)
    lines = raw.decode().splitlines()
    old_metadata, old_lines = previous.read_capture('s257')
    assert metadata['move_case'] == old_metadata['move_case']
    assert previous.states(lines) == previous.states(old_lines)
    rows = controls(lines)
    witnesses = previous.observations(lines)
    assert rows[-1]['sequence'] < witnesses[0]['sequence']
    lifecycle = collect_lifecycle(lines)
    calls = collect_calls(lines, metadata['callsite_specification'], retain_incomplete=True)
    actions = collect(lines, metadata['run_id'], 60, check_inventory(metadata))
    assert len(calls['incomplete_invocations']) == 1
    assert calls['incomplete_invocations'][0]['observer_tick'] == 10
    assert lifecycle['missing_boundaries'] == old['lifecycle']['missing_boundaries']
    assert all(r['post'] == r['observer_entry'] == '0' for r in witnesses[1:])
    assert sha(HERE.parent / 's257/native-build.tar.gz') == metadata['s263_control']['base_archive_sha256']
    with tarfile.open(HERE.parent / 's257/native-build.tar.gz') as base, tarfile.open(HERE / 'build-extension.tar.gz') as extension:
        names = set(extension.getnames())
        for path, expected in metadata['outputs_sha256'].items():
            archive = extension if path in names else base
            assert hashlib.sha256(archive.extractfile(path).read()).hexdigest() == expected
        assert hashlib.sha256(extension.extractfile('instrumentation.diff').read()).hexdigest() == metadata['instrumentation_sha256']
        assert json.loads(extension.extractfile('build.json').read()) == metadata
        assert metadata['outputs_sha256']['game/fighter/chad.swf'] == old_metadata['outputs_sha256']['game/fighter/chad.swf']
    for path, expected in metadata['sources_sha256'].items():
        assert sha(ROOT / path) == expected
    provenance = json.loads((HERE / 'pcode-provenance.json').read_text())
    assert provenance['main_sha256'] == metadata['outputs_sha256']['game/main.swf']
    for path, expected in provenance['exports_sha256'].items():
        assert sha(HERE / path) == expected
    bytecode = gzip.decompress((HERE / 'pcode/main/frame_1/DoAction.pcode.gz').read_bytes()).decode()
    sequence = compiled_control(bytecode)
    return {'production_admitted': False, 'native_parity_proven': False,
            'exit_model_fix_proved': False, 'executed_pc_trace': False,
            'exact_chad_context_invalidation_access_proved': False,
            'dynamic_receiver_removal_register_access_observed': True,
            'events': len(lines), 'root_samples': len(actions['samples']),
            'controls': rows, 'chad_witnesses': witnesses,
            'actor_comparison': {'rows': len(previous.states(lines)), 'exact_tick_payload_equal_s257': True},
            'chad_swf_unchanged': True, 'compiled_control_sequence': sequence,
            'chad_compiled_sites': old['compiled_sites'],
            'lifecycle': lifecycle, 'incomplete_invocations': calls['incomplete_invocations'],
            'full_as': {'unvisited': len(actions['unvisited']), 'uninstrumented': len(actions['uninstrumented'])},
            'boundary_window': lines[rows[0]['sequence'] - 1:witnesses[-1]['sequence']],
            'limit': 'Worker is defined at root and invoked with a dynamic clip as this. Slot removal is positively observed; invalidation of Chad Function2 defining timeline/activation is not. No exact executed PC or stack unwind observation.',
            'next_discriminator': 'Define the same register-bound worker in an authored child timeline, pair retained and parent-goto removal controls, and independently bind the defining target/activation to the removed instance. If that context cannot positively continue, obtain native executed-PC and activation/stack observations at Chad CallMethod/Pop/SetMember; do not infer return from absence.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-exact-continuation', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_exact_continuation and not report['exact_chad_context_invalidation_access_proved']:
        print('S263_EXACT_CONTINUATION_UNPROVED production_admitted=false native_parity_proven=false')
        raise SystemExit(1)
    print('S263_EVIDENCE_OK production_admitted=false native_parity_proven=false')
