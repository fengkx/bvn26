"""Audit one proposed raster family against locked s262 state, before pixels."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCKED = HERE.parent / 's262'


def load_replay():
    spec = importlib.util.spec_from_file_location('s272_locked_s262', LOCKED / 'diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.diagnose()


def audit_pair(contract, scene):
    """Recompute exact fields and bind native rows to this capture, not its tick alone."""
    if len(scene['rows']) != len(contract['snapshots']) or len(scene['rows']) != 61:
        raise ValueError('incomplete paired rows')
    counts = Counter()
    rows = []
    for tick, (snapshot, row) in enumerate(zip(contract['snapshots'], scene['rows'])):
        before = contract['tape']['snapshots'][tick]['before']
        if (row['tick'], row['native_display'], row['replayed_firings']) != (
                snapshot['tick'], snapshot['display'], snapshot['firing']) or row['tick'] != tick:
            raise ValueError('capture boundary mismatch')
        nodes = snapshot['nodes']
        expected = {'tens': int(before['tens']), 'ones': int(before['ones']),
                    'hud_frame': int(nodes['hud']['frame'])}
        for role in ('camera', 'root'):
            for axis in ('x', 'y'):
                expected[role + '_' + axis] = float(nodes[role][axis])
        expected['camera_scale'] = float(nodes['camera']['xscale'])
        for side in ('p1', 'p2'):
            for suffix, field, value, cast in (
                    ('bar2', 'trail', 'xscale', float), ('win', 'win', 'frame', int)):
                matches = [n for n in nodes.values() if n['role'].endswith('/' + side + 'xt/' + suffix)]
                if len(matches) != 1:
                    raise ValueError('ambiguous HUD owner')
                expected[side + '_' + field] = cast(matches[0][value])
        if row['native'] != expected or set(row['godot']) != set(expected):
            raise ValueError('native state or comparison fields mismatch')
        differences = [{'field': key, 'native': value, 'godot': row['godot'][key]}
                       for key, value in expected.items() if value != row['godot'][key]]
        if sorted(differences, key=lambda d: d['field']) != sorted(row['differences'], key=lambda d: d['field']):
            raise ValueError('recorded differences mismatch')
        counts.update(d['field'] for d in differences)
        rows.append({'tick': tick, 'display': snapshot['display'],
                     'firing': snapshot['firing'], 'differences': differences})
    comparisons_passed = not counts
    if scene['state_comparisons_passed'] != comparisons_passed:
        raise ValueError('state summary mismatch')
    if scene['callback_outputs_verified'] != contract['tape']['firing_count']:
        raise ValueError('callback count mismatch')
    # Matching selected fields cannot establish the missing lifetime and phase contract.
    return {'rows': rows, 'differing_snapshot_counts': dict(sorted(counts.items())),
            'selected_state_comparisons_passed': comparisons_passed,
            'state_admitted': False, 'residual_family_classified': False,
            'thin_raster_cut_proved': False,
            'classification': 'blocked_before_pixels',
            'blockers': contract['unproved'],
            'same_capture_godot_images_written': scene['images_written']}


def diagnose():
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for name, expected in pins.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + name)
    contract = load_replay()
    if contract != json.loads((LOCKED / 'diagnosis.json').read_text()):
        raise ValueError('locked replay differs')
    scene = json.loads((LOCKED / 'paired-scene.json').read_text())
    if any(scene[key] is not False for key in ('imaging_allowed', 'common_visual_phase_proved',
                                              'production_admitted', 'native_parity_proven')):
        raise ValueError('unexpected locked admission')
    if scene['images_written'] != 0:
        raise ValueError('unexpected locked images')
    return {'base': '443d36b6821eff88ca16bb7dba5609fc3b6275bd', 'rank': 9,
            'production_admitted': False, 'native_parity_proven': False,
            'candidate_family': 'countdown digit glyph edges (Sprite1810); candidate only, not an observed raster defect',
            'events_revalidated': contract['events'], 'native_bitmap_frames': contract['bitmap_frames'],
            'callback_outputs_verified_in_locked_scene': scene['callback_outputs_verified'],
            'new_captures': 0, 'new_images': 0, 'product_obligations_closed': 0,
            'pair_audit': audit_pair(contract, scene),
            'next_discriminator': 'In one encoded capture and its own scene, prove timer/digit allocation and registration-to-intro/child-clock joins, then exact selected state and complete visual phase. Only after admission compare unchanged RGBA at identical coordinates for the selected digit edges. Separate wrong digit/frame/transform from edge coverage or color residuals; no offsets, rounding or image replacement.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-thin-raster', action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'pair_audit'}))
    return int(args.require_thin_raster and not result['pair_audit']['thin_raster_cut_proved'])


if __name__ == '__main__':
    raise SystemExit(main())
