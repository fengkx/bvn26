"""Recompute one source-bound unload lifetime; no aliases or gate exceptions."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
from urllib.parse import unquote

from tools.sampling_display import collect, enrich, source_timelines
from tools.sampling_native import sha, validate_capture

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ROLES = ('parent', 'saved_receiver', 'depth_occupant', 'named_receiver')
FIELDS = ('path', 'type', 'parent', 'name', 'depth', 'frame', 'total_frames',
          'source_stamp', 'token', 'display_id', 'child_count', 'children')


def parse_lifetime(text):
    observations = []
    controls = {}
    for line in text.splitlines():
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        kind, fields = parts[6], parts[7].split(',')
        if kind == 's261_control':
            if len(fields) != 3 or fields[0] in controls:
                raise ValueError('duplicate/malformed control')
            controls[fields[0]] = fields[1:]
        elif kind == 'aimain_identity':
            if len(fields) != 5:
                raise ValueError('malformed identity')
            observations.append({'phase': fields[0], 'sequence': int(parts[2]),
                'clock_ms': int(parts[3]), 'display': int(parts[4]), 'tick': int(parts[5]),
                'saved_equals_occupant': fields[1], 'named_equals_occupant': fields[2],
                'saved_parent_equals_parent': fields[3], 'saved_depth': int(fields[4]), 'objects': {}})
        elif kind == 'aimain_object':
            if not observations or len(fields) != 14:
                raise ValueError('missing identity/malformed object')
            row = observations[-1]
            if fields[0] != row['phase'] or fields[1] not in ROLES or fields[1] in row['objects']:
                raise ValueError('reordered/duplicate object')
            row['objects'][fields[1]] = dict(zip(FIELDS, map(unquote, fields[2:])))
    if any(tuple(p['objects']) != ROLES for p in observations):
        raise ValueError('incomplete objects')
    if len(observations) < 4 or [p['phase'] for p in observations[:2]] != ['before_unload', 'after_unload'] or observations[-1]['phase'] != 'first_sample':
        raise ValueError('incomplete boundaries')
    roots = observations[2:-1]
    if not roots or any(p['phase'] != 'root' for p in roots):
        raise ValueError('unexpected phase')
    if [p['display'] for p in roots] != list(range(observations[1]['display'] + 1, roots[-1]['display'] + 1)):
        raise ValueError('missing/duplicate root')
    zero = lambda p: all(p['objects'][r]['frame'] == '0' and p['objects'][r]['total_frames'] == '0' for r in ROLES[1:])
    if not zero(roots[-1]) or any(zero(p) for p in roots[:-1]):
        raise ValueError('missing first zero boundary or excess roots')
    if tuple(controls) != ('retained', 'replaced', 'retained_content_deleted'):
        raise ValueError('missing/reordered controls')
    return observations, controls


def actor_rows(text):
    return [(int(p[5]), p[7]) for line in text.splitlines()
            if len(p := line.split('|', 7)) == 8 and p[6] == 'state' and int(p[5]) >= 0]


def diagnose():
    pins = json.loads((HERE / 'artifact-sha256.json').read_text())
    for name, expected in pins.items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed evidence: ' + name)
    metadata = json.loads((HERE / 'native-build.json').read_text())
    case = json.loads((HERE.parent / 's231/yijiao__attack__neutral__ground__near.json').read_text())
    raw = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode()
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        if json.loads(archive.extractfile('build.json').read()) != metadata:
            raise ValueError('build metadata differs')
        diff = archive.extractfile('instrumentation.diff').read()
        if hashlib.sha256(diff).hexdigest() != metadata['instrumentation_sha256']:
            raise ValueError('changed instrumentation')
        for name, expected in metadata['outputs_sha256'].items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != expected:
                raise ValueError('changed compiled output: ' + name)
        patched = archive.extractfile('patches/fighter/yijiao/DefineSprite_455/frame_1/DoAction.as').read().decode()
        sequence = ('_global.s261Observe("before_unload", AImain);\n'
                    '      AImain.unloadMovie();\n'
                    '      _global.s261Observe("after_unload", AImain);')
        if patched.count(sequence) != 1:
            raise ValueError('authored unload not preserved between observations')
    for name, expected in metadata['sources_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('changed source: ' + name)
    observations, controls = parse_lifetime(raw)
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        trace = temp / 'native.log'; trace.write_text(raw)
        validate_capture(case, metadata, trace)
        exports = json.loads((HERE / 'source-exports.json').read_text())
        paths = {}
        for source, entry in exports.items():
            archive_path = (HERE.parent / 's233/yijiao-source-export.tar.gz' if 'yijiao' in source
                            else HERE.parent / 's30/source-exports.tar.gz')
            name = Path(entry['xml']).name
            with tarfile.open(archive_path) as archive:
                member = name if 'yijiao' in source else 'bvn-s30-source/' + name
                data = archive.extractfile(member).read()
            path = temp / name; path.write_bytes(data)
            if sha(path) != entry['xml_sha256'] or sha(ROOT / source) != entry['source_sha256']:
                raise ValueError('changed source export')
            paths[source] = path
        samples = collect(raw.splitlines(), metadata['run_id'], 60)
        gaps = enrich(samples, paths)
        frames, _ = source_timelines(paths['game/fighter/yijiao.swf'])
        placement = frames[455][0][1]
        frame_inventory = [sorted(frame) for frame in frames[3]]
    historical = gzip.decompress((HERE.parent / 's255/native-capture.log.gz').read_bytes()).decode()
    states = actor_rows(raw)
    bundle = json.loads((ROOT / 'scripts/fighter/yijiao.json').read_text())
    script = next(s['source'] for s in bundle['scripts'] if s['path'] == 'DefineSprite_455/frame_1/DoAction.as')
    start = script.index('function initCtrl()'); end = script.index('\n}', start) + 2
    return {'production_admitted': False, 'native_parity_proven': False,
            'mapping_fix_proved': False, 'identity_discriminator_valid_for_cleared_content': False, 'native_receipt_resealed': False,
            'raw_validation_exit': 0, 'event_count': len(raw.splitlines()),
            'observations': observations, 'controls': controls, 'root_count': len(observations) - 3, 'authored_slot': {'source': 'game/fighter/yijiao.swf',
            'parent_symbol': 455, 'placement': placement, 'sprite': 3,
            'parent_frame2_aimain_slot': frames[455][1].get(1), 'frame_child_depths': frame_inventory, 'initCtrl': script[start:end],
            'sprite_scripts': [s for s in bundle['scripts'] if s['path'].startswith('DefineSprite_3/')]},
            'first_sample_node': samples[0]['nodes']['_level0.game.p1.mc.AImain'],
            'sample_count': len(samples), 'source_gap_count': len(gaps), 'source_gaps': gaps,
            'actor_comparison': {'reference': 's255/native-capture.log.gz', 'rows': len(states),
                                 'all_14_fields_equal': states == actor_rows(historical)},
            'identity_limit': 'Independent controls test reference equality and external token equality against deliberate retention, replacement, and retained-property deletion. Loss of token is not allocation identity; target content clearing remains ambiguous.',
            'next_discriminator': 'Acquire native player engine allocation/lifecycle identity at the now-bounded last-nonzero/first-zero root interval, calibrated against retained-content clearing and same-path/depth replacement. AS2 reference/token observations alone cannot distinguish these; no alias or exemption follows.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(diagnose(), indent=2, ensure_ascii=False) + '\n')
