"""Recompute bounded initialization order without changing receiver eligibility."""
import argparse
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

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FIELDS = ('phase', 'path', 'parent_frame', 'getHitObj_type', 'getStgHitObj_type',
          'fs_type', 'fzfs_type', 'stgks_type', 'fs_length', 'fzfs_length',
          'stgks_length', 'stamp_id', 'stamp_birth')
PHASES = {'root_before_geometry', 'jump_before', 'jump_after', 'frame840_entry',
          'frame1_entry', 'frame1_exit', 'enterFrame_before', 'enterFrame_after'}


def load(directory, name):
    spec = importlib.util.spec_from_file_location(directory + '_' + name,
                                                 HERE.parent / directory / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observations(raw):
    rows = []
    seen = set()
    for line in raw.splitlines():
        p = line.split('|', 7)
        if len(p) != 8:
            raise ValueError('malformed event')
        if not p[6].startswith('s260_'):
            continue
        values = list(map(unquote, p[7].split(',')))
        if p[6] != 's260_order' or len(values) != len(FIELDS):
            raise ValueError('unknown/malformed observation')
        row = dict(zip(FIELDS, values))
        row.update(sequence=int(p[2]), display=int(p[4]), tick=int(p[5]))
        key = (row['tick'], row['phase'])
        if (row['phase'] not in PHASES or row['tick'] not in (10, 11, 12)
                or row['path'] != '_level0.game.p1.mc.bdmn' or key in seen):
            raise ValueError('out-of-scope/duplicate observation')
        seen.add(key)
        rows.append(row)
    required = {(t, 'root_before_geometry') for t in (10, 11, 12)}
    required |= {(10, 'jump_before'), (11, 'frame840_entry'), (11, 'frame1_entry'), (11, 'frame1_exit')}
    required |= {(t, p) for t in (11, 12) for p in ('enterFrame_before', 'enterFrame_after')}
    if not required <= seen:
        raise ValueError('incomplete observation')
    if any(a['sequence'] >= b['sequence'] for a, b in zip(rows, rows[1:])):
        raise ValueError('out-of-order observation')
    return rows


def payloads(raw, kind):
    return [(int(p[5]), p[7]) for line in raw.splitlines()
            if len(p := line.split('|', 7)) == 8 and p[6] == kind and int(p[5]) >= 0]


def diagnose():
    prior_module = load('s256', 'diagnose')
    prior = prior_module.diagnose()
    builder = load('s260', 'build_probe')
    for name, expected in json.loads((HERE / 'artifact-sha256.json').read_text()).items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed evidence: ' + name)
    metadata = json.loads((HERE / 'native-build.json').read_text())
    previous_build = json.loads((HERE.parent / 's256/native-build.json').read_text())
    case = json.loads((HERE.parent / 's64/didala__summon__neutral__ground__near.json').read_text())
    if metadata['move_case'] != previous_build['move_case']:
        raise ValueError('changed tape')
    for name, expected in metadata['sources_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed source: ' + name)
    for name, digest in metadata['outputs_sha256'].items():
        if name not in ('game/main.swf', 'game/fighter/didala.swf') and digest != previous_build['outputs_sha256'][name]:
            raise ValueError('changed unrelated compiled output')
    with tarfile.open(HERE / 'native-build.tar.gz') as archive, tarfile.open(HERE.parent / 's256/native-build.tar.gz') as old:
        if json.loads(archive.extractfile('build.json').read()) != metadata:
            raise ValueError('changed archived metadata')
        for name, expected in {**metadata['outputs_sha256'], 'instrumentation.diff': metadata['instrumentation_sha256']}.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != expected:
                raise ValueError('changed compiled output: ' + name)
        bundle = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/fighter/didala.json').read_text())['scripts']}
        edits = [(builder.CONTROLLER, builder.patch_controller), (builder.RECEIVER, builder.patch_receiver),
                 (builder.ENTER_FRAME, builder.patch_enter_frame),
                 ('DefineSprite_542/frame_840/DoAction.as', builder.patch_destination)]
        for path, transform in edits:
            name = 'patches/fighter/didala/' + path
            before = old.extractfile(name).read().decode().replace('\r\n', '\n') if name in old.getnames() else bundle[path]
            if archive.extractfile(name).read().decode() != transform(before):
                raise ValueError('unexpected authored script edit: ' + path)
        name = 'patches/main/frame_10/DoAction.as'
        root = archive.extractfile(name).read().decode()
        previous_root = old.extractfile(name).read().decode().replace('   _root.s256Observe();\n', '')
        # Absolute loader directories are build-local; the input fixture and sample stay fixed.
        previous_root = previous_root.replace('/bvn-s256-r01-build/', '/bvn-s260-r01-build/')
        if root != builder.patch_root(previous_root):
            raise ValueError('changed root fixture or sampling boundary')
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_text(raw)
        validate_capture(case, metadata, trace)
    sources = set()
    for name in metadata['sources_sha256']:
        if name.startswith('scripts/'):
            b = json.loads((ROOT / name).read_text())
            sources.update(b['game_file'] + '#' + s['path'] for s in b['scripts'])
    geometry = collect(raw.splitlines(), metadata['run_id'], case['frames'], sources)
    old_raw = gzip.decompress((HERE.parent / 's256/native-capture.log.gz').read_bytes()).decode()
    comparisons = {kind: {'rows': len(payloads(raw, kind)), 'exact_tick_payload_equal_s256': payloads(raw, kind) == payloads(old_raw, kind)}
                   for kind in ('state', 'input_next_display', 'key_read', 'random')}
    return {'production_admitted': False, 'native_parity_proven': False, 'eligibility_fix_proved': False,
            'observations': observations(raw), 'source': prior['source'],
            'geometry_boundaries': [dict(sequence=int(p[2]), display=int(p[4]), tick=int(p[5]), kind=p[6])
                                    for line in raw.splitlines() if len(p := line.split('|', 7)) == 8
                                    and p[6] in ('geometry_begin', 'geometry_end') and 10 <= int(p[5]) <= 12],
            'geometry_samples': len(geometry['samples']),
            'selected_geometry': [s for s in geometry['samples'] if 10 <= s['tick'] <= 12],
            'comparison': comparisons, 'events': len(raw.splitlines()), 'new_native_captures': 1,
            'next_discriminator': 'At the unchanged tick11 boundary, separately establish whether an authored collision query executes against this uninitialized bdmn before frame1, with positive controls for query observation and exact operands. This is evidence work, not permission to call the methods, initialize early, move sampling, or exempt the receiver.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(diagnose(), indent=2, ensure_ascii=False) + '\n')
    print('RECEIVER_INIT_ORDER_DIAGNOSIS_OK; eligibility_fix_proved=false')
