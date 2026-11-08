"""Retain complete s355 and distinguish packed-name disk facts from live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'c092443fb61dd07954f363ca4f331398312ca269'
GATES = {name: 'S364_' + name.replace('-', '_').upper() + '_UNPROVED'
         for name in ('target-entry', 'outer-lifetime', 'independent-controls',
                      'child-clock', 'fresh-capture')}
ROUTE_SHA256 = 'f65cb3474ce2d84a653995e4d62c7aa8922dd3db9b18499f0516084d045b54a1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('s364_locked_s355', HERE.parent / 's355/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    return prior


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's355/diagnosis.json').read_text()):
        raise ValueError('complete locked s355 diagnosis changed')
    return prior


def audit(record):
    if sha((json.dumps(record, indent=2) + '\n').encode()) != ROUTE_SHA256:
        raise ValueError('independent native record changed')
    container = record['container']
    raw = bytes.fromhex(container['hex'])
    if sha(raw) != container['sha256'] or len(raw) != container['end_exclusive'] - container['file_offset']:
        raise ValueError('container bytes or bounds differ')
    members = raw.decode('ascii').split(',')
    if members != container['members'] or members[17] != 'gotoAndStop' or members[19] != 'removeMovieClip':
        raise ValueError('packed member binding differs')
    return record


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    prior = replay()
    route = audit(json.loads((HERE / 'native-route.json').read_text()))
    return dict(slice='s364', base=BASE, scope='AFTER-s362 rank #2 only',
                authority='evidence/sampling-upgrade/next-fix-priority-after-s362.md',
                production_admitted=False, native_parity_proven=False, m0_02_status='pending',
                retained=prior, locked_s355_reproduced=True,
                retained_validation_not_new_progress=['Complete s355 report and recursive retained tooling',
                                                      'Original static caller and 0x52 continuation',
                                                      'Historical helper/glyph/placement stream'],
                independent_disk_route=route,
                independently_observed_disk_facts=['Two raw ASCII occurrences outside the old exact-NUL-name boundary',
                                                   'One 328-byte printable comma-delimited container in __TEXT,__const',
                                                   'Zero exact-u64 / RIP-LEA candidates to that container start within declared bounds'],
                observations={key: None for key in ('loaded_actual_call', 'loaded_method_resolution',
                                                    'target_frame_entry', 'outer_allocation', 'outer_removal',
                                                    'outer_replacement', 'uninterrupted_generation',
                                                    'following_root_callback_order')},
                qualification_matrix=prior['qualification_matrix'],
                outer_lifetime_assessment=dict(independently_observed=False, channel=None,
                    reason='The removal-name member has no executable association or typed receiver. Text adjacency cannot derive creation/removal/replacement or uninterrupted outer generations; no separate live lifetime experiment was executed.'),
                controls={name: dict(executed=False, qualified=None) for name in
                          ('isolated_repeated_target', 'isolated_changed_target', 'same_depth_replacement', 'observer_off_on')},
                gates={name: dict(proved=False, code=code) for name, code in GATES.items()},
                observer_qualified=False, independent_controls_proved=False,
                independent_child_clock_proved=False, fresh_capture_eligible=False,
                new_mechanism_proof=False, independent_observations_new=[],
                new_builds=0, new_player_launches=0, new_attaches=0,
                new_memory_reads=0, new_captures=0, new_images=0,
                other_ranks_executed=[], re_ranked=False, product_obligations_closed=0,
                blocker='Packed-name route stops before executable registration. Actual ones caller is still not associated with loaded method/frame entry for any of ten targets. Independent outer lifetime is absent; controls/capture remain blocked before execution.',
                next_required_observation='Derive executable method and outer lifetime channels independent of name/opcode identity; bind actual loaded caller, receiver generations and entries 1-10 in one run before isolated controls and fresh capture.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as error:
        print('S364_EVIDENCE_INVALID: ' + str(error))
        return 2
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code for flag, code in GATES.items()
                if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S364_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
