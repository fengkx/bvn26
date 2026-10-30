"""Audit retained loader evidence without promoting file provenance to live identity."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

from tools.sampling_native import validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOADER = 'DefineSprite_1900/frame_1/DoAction.as'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_bytes(data, expected):
    if digest(data) != expected:
        raise ValueError('wrong resource bytes')


def loader_sites(source):
    source = source.replace('\r\n', '\n')
    request = '_this._loader.loadClip(_root.fighterDir + _loc3_.url,_root.game[pr]);'
    callback = 'LO.onLoadComplete = function(target)\n{\n   loadStep++;\n   loadSteps[loadStep]();\n};'
    if request not in source or callback not in source:
        raise ValueError('changed loader source sites')
    return {'request': request, 'callback': callback,
            'callback_target_recorded': False,
            'callback_consumes_target': False}


def audit_run(name):
    directory = HERE.parent / name
    metadata = json.loads((directory / 'native-build.json').read_text())
    receipt = json.loads((directory / 'native-receipt.json').read_text())
    raw = gzip.decompress((directory / 'native-capture.log.gz').read_bytes())
    check_bytes(raw, receipt['files'][receipt['trace']])
    with tempfile.TemporaryDirectory() as temporary:
        trace = Path(temporary) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(metadata['move_case'], metadata, trace)
    archives = [directory / 'native-build.tar.gz'] if name.startswith('s259') else [
        HERE.parent / 's257/native-build.tar.gz', directory / 'build-extension.tar.gz']
    contents = {}
    wanted = set(metadata['outputs_sha256']) | {'patches/main/' + LOADER, 'build.json'}
    for path in archives:
        with tarfile.open(path) as archive:
            for member in archive.getmembers():
                if member.name in wanted:
                    contents[member.name] = archive.extractfile(member).read()
    if json.loads(contents['build.json']) != metadata:
        raise ValueError('archive metadata mismatch')
    for path, expected in metadata['outputs_sha256'].items():
        check_bytes(contents[path], expected)
        check_bytes(contents[path], receipt['files'][receipt['build'] + '/' + path])
    for path, expected in metadata['sources_sha256'].items():
        check_bytes((ROOT / path).read_bytes(), expected)
    sites = loader_sites(contents['patches/main/' + LOADER].decode())
    loader = contents['patches/main/' + LOADER].decode()
    helper_event = loader.index('_root.aiEvent("helper_load"')
    helper_request = loader.index('_this._loader.loadClip(_root.fzDir')
    if not loader.index('function loadfz(pr)') < helper_event < helper_request:
        raise ValueError('helper event is no longer a request-site proxy')
    sites['helper_load_before_request'] = True
    rows = [line.split('|', 7) for line in raw.decode().splitlines()]
    fighter = metadata['move_case']['fighters']['p1']
    target_path = f'game/fighter/{fighter}.swf'
    return {
        'events': len(rows), 'raw_sha256': digest(raw),
        'capture_structure_exit': 0, 'archived_output_and_receipt_hashes_match': True,
        'configuration_fighter': fighter, 'requested_slot_expression': '_root.game[pr]',
        'expected_source_sha256': metadata['sources_sha256'][target_path],
        'expected_instrumented_sha256': metadata['outputs_sha256'][target_path],
        'loader_sites': sites, 'event_kind_counts': dict(sorted(Counter(r[6] for r in rows).items())),
        'candidate_proxy_events': [r for r in rows if r[6] in ('boot', 'initCtrl', 'helper_load')],
        'actual_load_callback_target': None, 'consumed_bytes_observation': None,
        'callback_to_instance_lifetime': None,
    }


def wrong_resource_control():
    directory = HERE.parent / 's259/normal'
    metadata = json.loads((directory / 'native-build.json').read_text())
    expected = metadata['outputs_sha256']['game/fighter/yijiao.swf']
    with tarfile.open(directory / 'native-build.tar.gz') as archive:
        right = archive.extractfile('game/fighter/yijiao.swf').read()
        wrong = archive.extractfile('game/fighter/yihu.swf').read()
    check_bytes(right, expected)
    try:
        check_bytes(wrong, expected)
    except ValueError as error:
        rejection = str(error)
    else:
        raise ValueError('wrong-resource negative unexpectedly passed')
    return {'kind': 'offline_archived_byte_substitution_only',
            'expected_resource': 'game/fighter/yijiao.swf', 'expected_sha256': expected,
            'substituted_resource': 'game/fighter/yihu.swf', 'substituted_sha256': digest(wrong),
            'correct_bytes_exit': 0, 'wrong_bytes_exit': 1, 'rejection': rejection,
            'actual_wrong_resource_load_performed': False,
            'runtime_wrong_resource_control': None,
            'limitation': 'A file mismatch is detected; no player consumed these substituted bytes. This cannot attest a callback or lifetime.'}


def diagnose():
    for path, expected in json.loads((HERE / 'artifact-sha256.json').read_text()).items():
        check_bytes((ROOT / path).read_bytes(), expected)
    source = next(s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts'] if s['path'] == LOADER)
    environment = json.loads((HERE.parent / 's259/normal/capture-environment.json').read_text())
    chad_environment = json.loads((HERE.parent / 's263/capture.txt').read_text().splitlines()[0])
    if environment['runtime_fighter'] is not None or chad_environment['runtime_fighter'] is not None:
        raise ValueError('historical runtime observation changed')
    return {'scope': 'AFTER-s263 rank 5 only', 'base': 'b0fa64b8',
            'production_admitted': False, 'native_parity_proven': False,
            'loader_attestation_proved': False, 'product_obligations_closed': 0,
            'source_path': 'scripts/main.json#' + LOADER, 'source_sites': loader_sites(source),
            'runtime_fighter': {'s259_normal': None, 's263': None},
            'runs': {name: audit_run(name) for name in ('s259/normal', 's259/held', 's263')},
            'wrong_resource_negative': wrong_resource_control(),
            'missing': ['actual_callback_target_observation', 'independent_consumed_bytes_binding',
                        'callback_to_observed_instance_lifetime', 'actual_wrong_resource_load_control'],
            'new_player_launches': 0,
            'next_discriminator': [
                'Extend only s259 normal P1 loadman and its existing MovieClipLoader listener; record request, callback target and ordering without moving loadStep or invoking extra gameplay methods.',
                'Observe the resource bytes consumed by that load independently of the configured path, build hash and embedded self-declared token; correlate the read with the callback in the same run.',
                'Track the callback target through initialization and bounded use to unload/replacement, distinguishing same-path reuse. Do not infer lifetime from frame1 or path equality.',
                'Repeat with a different locked resource actually supplied to the same requested target while preserving the expected identity. Retain complete success/error callbacks and require rejection of the mismatch.',
                'Until that paired capture exists, keep runtime_fighter null and all historical receipts unchanged.'
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-loader-attestation', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_loader_attestation:
        print('LOADER_ATTESTATION_UNPROVED: ' + ', '.join(report['missing']))
        return 1
    print('S268_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
