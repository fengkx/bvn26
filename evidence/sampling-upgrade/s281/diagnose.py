"""Recheck rank-9 raster prerequisites without joining different captures."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def replay(slice_name):
    path = HERE.parent / slice_name
    spec = importlib.util.spec_from_file_location('s281_' + slice_name, path / 'diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.diagnose()
    if result != json.loads((path / 'diagnosis.json').read_text()):
        raise ValueError('replay differs: ' + slice_name)
    return result


def capture_identity(slice_name):
    path = HERE.parent / slice_name
    build = json.loads((path / 'native-build.json').read_text())
    receipt = json.loads((path / 'native-receipt.json').read_text())
    return {'run_id': build['run_id'], 'raw_sha256': receipt['files'][receipt['trace']]}


def audit_prerequisites(raster, lifetime, identities):
    """Audit the retained evidence only; local lifetime admission is not scene admission."""
    if identities['s262']['run_id'] == identities['s274']['run_id'] or identities['s262']['raw_sha256'] == identities['s274']['raw_sha256']:
        raise ValueError('distinct captures mislabeled as one run')
    pair = raster['pair_audit']
    if pair['state_admitted'] is not False or pair['same_capture_godot_images_written'] != 0:
        raise ValueError('unexpected historical scene admission or images')
    for field in ('thin_state_admission_proved', 'scene_state_admitted', 'common_visual_phase_proved', 'scene_join_attempted'):
        if lifetime[field] is not False:
            raise ValueError('unexpected lifetime scene claim: ' + field)
    if lifetime['images_written'] != 0:
        raise ValueError('unexpected lifetime images')
    for report in (raster, lifetime):
        for flag in ('production_admitted', 'native_parity_proven'):
            if report[flag] is not False:
                raise ValueError('unexpected admission: ' + flag)
    return {
        's262_via_s272': {
            **identities['s262'], 'events_revalidated': raster['events_revalidated'],
            'native_bitmap_frames': raster['native_bitmap_frames'],
            'callback_count': raster['callback_outputs_verified_in_locked_scene'],
            'differing_snapshot_counts': pair['differing_snapshot_counts'],
            'tick13': pair['rows'][13], 'complete_scene_admitted': False,
            'same_capture_godot_images': 0, 'unproved': pair['blockers'],
        },
        's274_read_only_replay': {
            **identities['s274'], 'events_revalidated': lifetime['events'],
            'callback_count': lifetime['callback_count'],
            'encoding_windows': len(lifetime['encoding_windows']),
            'natural_entry_joins': lifetime['complete_entry_joins'],
            'bounded_encoded_lifetime_observed': lifetime['bounded_encoded_lifetime_observed'],
            'local_experiment_state_admitted': lifetime['local_experiment_state_admitted'],
            'complete_scene_admitted': False, 'pixel_payloads': 0,
            'scene_join_attempted': False,
        },
        'cross_capture_join_allowed': False,
        'classification': 'blocked_before_pixels',
        'same_capture_state_admitted': False,
        'matched_image_pairs': 0,
        # Null distinguishes unavailable measurements from measured zero residuals.
        'exact_rgba_edge_residual': None,
        'exact_rgba_interior_residual': None,
        'residual_family_classified': False,
        'thin_raster_cut_proved': False,
    }


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('changed locked input: ' + name)
    raster, lifetime = replay('s272'), replay('s274')
    identities = {name: capture_identity(name) for name in ('s262', 's274')}
    return {
        'slice': 's281', 'base': '7101756b6e5e0ccec00ef2bccfb72c3e6446bb7e',
        'scope': 'AFTER-s272 rank 9 only',
        'candidate_family': 'countdown digit glyph edges (Sprite1810)',
        'production_admitted': False, 'native_parity_proven': False,
        'new_builds': 0, 'new_captures': 0, 'new_images': 0,
        'product_obligations_closed': 0,
        'prerequisites': audit_prerequisites(raster, lifetime, identities),
        'next_discriminator': 'Complete same-capture allocation/child-clock and registration/intro/scene admission, then capture that matched scene. Bind glyph, placement, transform and compositing before exact RGBA edge/interior classification. Upstream work is excluded from s281; no tape or image substitution, tolerance, offsets, camera rounding or renderer rewrite.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-thin-raster', action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('RASTER_UNPROVED: complete same-capture scene admission and matched images absent')
    return int(args.require_thin_raster and not result['prerequisites']['thin_raster_cut_proved'])


if __name__ == '__main__':
    raise SystemExit(main())
