"""Recompute authored-query observations without relaxing receiver eligibility."""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
from urllib.parse import unquote

from tools.sampling_geometry import collect
from tools.sampling_native import sha, validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIELDS = ('phase', 'path', 'parent_frame', 'getHitObj_type', 'getStgHitObj_type',
          'fs_length', 'fzfs_length', 'stgks_length', 'operand_path', 'suffix',
          'array_length', 'result_type', 'result_value', 'stamp_id', 'stamp_birth')
PHASES = {'beida_entry', 'checkHit_entry', 'getHitObj_entry', 'getStgHitObj_entry',
          'checkHit_result', 'fighter_helper_operand', 'stage_operand'}


def load(directory, name):
    spec = importlib.util.spec_from_file_location(directory + '_' + name, HERE.parent / directory / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def query_rows(raw):
    rows = []
    for line in raw.splitlines():
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        if parts[6] != 's264_query':
            continue
        values = list(map(unquote, parts[7].split(',')))
        if len(values) != len(FIELDS):
            raise ValueError('malformed query observation')
        row = dict(zip(FIELDS, values))
        row.update(sequence=int(parts[2]), display=int(parts[4]), tick=int(parts[5]))
        if row['phase'] not in PHASES or row['path'] != '_level0.game.p1.mc.bdmn' or row['tick'] not in (10, 11, 12):
            raise ValueError('out-of-scope query')
        rows.append(row)
    if any(a['sequence'] >= b['sequence'] for a, b in zip(rows, rows[1:])):
        raise ValueError('duplicate/out-of-order query')
    for tick in (11, 12):
        phases = [r['phase'] for r in rows if r['tick'] == tick]
        required = ['beida_entry', 'checkHit_entry', 'getHitObj_entry', 'getHitObj_entry', 'getStgHitObj_entry', 'checkHit_result']
        if phases != required:
            raise ValueError('missing/changed same-context query control')
    return rows


def diagnose():
    prior = load('s260', 'diagnose')
    prior_report = prior.diagnose()
    builder = load('s264', 'build_probe')
    for name, expected in json.loads((HERE / 'artifact-sha256.json').read_text()).items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed evidence: ' + name)
    metadata = json.loads((HERE / 'native-build.json').read_text())
    old_metadata = json.loads((HERE.parent / 's260/native-build.json').read_text())
    case = json.loads((HERE.parent / 's64/didala__summon__neutral__ground__near.json').read_text())
    if metadata['move_case'] != old_metadata['move_case']:
        raise ValueError('changed input tape')
    for name, expected in metadata['sources_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed source: ' + name)
    with tarfile.open(HERE / 'native-build.tar.gz') as archive, tarfile.open(HERE.parent / 's260/native-build.tar.gz') as old:
        if json.loads(archive.extractfile('build.json').read()) != metadata:
            raise ValueError('changed build metadata')
        for name, expected in {**metadata['outputs_sha256'], 'instrumentation.diff': metadata['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != expected:
                raise ValueError('changed compiled output: ' + name)
        for name, digest in metadata['outputs_sha256'].items():
            if name not in ('game/main.swf', 'game/fighter/didala.swf') and digest != old_metadata['outputs_sha256'][name]:
                raise ValueError('unrelated compiled output changed')
        for name in old.getnames():
            if not name.startswith('patches/') or not old.getmember(name).isfile():
                continue
            before = old.extractfile(name).read().decode()
            before = before.replace('/bvn-s260-r01-build/', '/bvn-s264-r01-build/')
            before = before.replace(old_metadata['run_id'], metadata['run_id'])
            if name == 'patches/main/frame_1/DoAction.as':
                before = (HERE / 'observer.as').read_text() + '\n' + before
            elif name == 'patches/fighter/didala/' + builder.RECEIVER:
                before = builder.patch_receiver(before)
            if archive.extractfile(name).read().decode() != before:
                raise ValueError('unexpected script edit: ' + name)
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_text(raw)
        validate_capture(case, metadata, trace)
    order = prior.observations(raw)
    rows = query_rows(raw)
    begin = next(r for r in order if r['tick'] == 11 and r['phase'] == 'root_before_geometry')
    initialized = next(r for r in order if r['phase'] == 'frame1_exit')
    interval = [r for r in rows if begin['sequence'] <= r['sequence'] < initialized['sequence']]
    old_raw = gzip.decompress((HERE.parent / 's260/native-capture.log.gz').read_bytes()).decode()
    comparisons = {kind: {'rows': len(prior.payloads(raw, kind)), 'exact_tick_payload_equal_s260': prior.payloads(raw, kind) == prior.payloads(old_raw, kind)} for kind in ('state', 'input_next_display', 'key_read', 'random')}
    sources = set()
    for name in metadata['sources_sha256']:
        if name.startswith('scripts/'):
            bundle = json.loads((ROOT / name).read_text())
            sources.update(bundle['game_file'] + '#' + s['path'] for s in bundle['scripts'])
    geometry = collect(raw.splitlines(), metadata['run_id'], case['frames'], sources)
    bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
    references = [{'path': s['path'], 'line': i, 'text': line.strip()}
                  for s in bundle['scripts'] for i, line in enumerate(s['source'].splitlines(), 1)
                  if any(token in line for token in ('getHitObj(', 'getStgHitObj(', 'checkHit(', 'bdmn.hitTest('))]
    return {'production_admitted': False, 'native_parity_proven': False, 'eligibility_fix_proved': False,
            'pre_init_authored_query_proved': False, 'all_collision_paths_observed': False,
            'new_native_captures': 1, 'events': len(raw.splitlines()), 'query_rows': rows,
            'query_phase_counts': dict(Counter(r['phase'] for r in rows)),
            'initialization_order': order, 'unready_interval': {'begin_sequence': begin['sequence'], 'initialized_sequence': initialized['sequence'], 'observed_query_rows': interval},
            'comparison': comparisons, 'geometry_samples': len(geometry['samples']),
            'selected_geometry': [s for s in geometry['samples'] if 10 <= s['tick'] <= 12],
            'source': prior_report['source'], 'didala_query_reference_inventory': references,
            'limit': 'Positive authored query controls after initialization do not prove observation of calls to undefined methods before initialization, external direct hitTests, or absence of every collision path. No eligibility change follows.',
            'next_discriminator': 'Instrument source call sites that can address the newly placed bdmn before frame1, with same-context dispatch/operand controls independent of functions defined by that frame. Separate a failed undefined-method dispatch from no call; do not invoke it artificially.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-pre-init-query', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('AUTHORED_QUERY_DIAGNOSIS_OK; eligibility_fix_proved=false')
    raise SystemExit(1 if args.require_pre_init_query and not report['pre_init_authored_query_proved'] else 0)
