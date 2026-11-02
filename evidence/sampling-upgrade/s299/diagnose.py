"""Audit only AFTER-s290 rank 9; stop before pixels without same-capture admission."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '9cc27526bf8bcb51effbf75fd9e2b0a624987731'
REQUIREMENTS = {
    'state-admission': 'S299_STATE_ADMISSION_UNPROVED',
    'paired-scene': 'S299_PAIRED_SCENE_UNPROVED',
    'thin-raster': 'S299_STRICT_RASTER_UNPROVED',
}
EXCLUSIONS = [
    'admission repair', 'ranks 1-8 execution', 'tolerance', 'offset search',
    'image substitution', 'camera rounding', 'renderer rewrite',
    'game/scripts/runtime/contracts changes', 'shared sampler/threshold/validator changes',
    's254-s298 edits',
]


def verify_pins(root, pins):
    for name, expected in pins.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed locked evidence: ' + name)


def replay_locked():
    path = HERE.parent / 's290'
    spec = importlib.util.spec_from_file_location('s299_locked_s290', path / 'diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    replay = module.diagnose()
    retained = json.loads((path / 'diagnosis.json').read_text())
    if replay != retained:
        raise ValueError('Locked s290 replay differs')
    return replay


def audit_locked(prior, retained):
    # Full equality preserves every boundary, not just a convenient summary or tick13.
    if prior != retained:
        raise ValueError('Locked s290 evidence differs')
    for key in ('production_admitted', 'native_parity_proven',
                'state_admission_proved', 'thin_raster_cut_proved'):
        if prior[key] is not False:
            raise ValueError('Unexpected proof promotion: ' + key)
    pre = prior['locked_prerequisites']
    if pre['same_capture_state_admitted'] is not False or pre['matched_image_pairs'] != 0:
        raise ValueError('New admission or images require independent analysis')
    if any(pre[key] is not None for key in ('exact_rgba_edge_residual', 'exact_rgba_interior_residual')):
        raise ValueError('Unmeasured residuals must remain null')
    rows = prior['boundary_audit']['rows']
    if [r['tick'] for r in rows] != list(range(61)):
        raise ValueError('Incomplete or reordered boundaries')
    for row in rows:
        if (not row['glyph_mismatch_fields'] or not row['other_selected_state_mismatch_fields']
                or row['full_scene_admitted'] is not False
                or row['same_capture_image_pair_available'] is not False
                or row['pixel_classification'] != 'not_measured'):
            raise ValueError('Changed boundary admission requires independent analysis')
    return [{
        **row,
        'paired_capture_attempted': False,
        'source_bound_edge_membership': None,
        'source_bound_interior_membership': None,
        'exact_rgba_edge_residual': None,
        'exact_rgba_interior_residual': None,
        'differing_channels': None,
    } for row in rows]


def diagnose():
    verify_pins(ROOT, json.loads((HERE / 'input-sha256.json').read_text()))
    prior = replay_locked()
    retained = json.loads((HERE.parent / 's290/diagnosis.json').read_text())
    rows = audit_locked(prior, retained)
    return {
        'slice': 's299', 'base': BASE, 'scope': 'AFTER-s290 rank #9 only',
        'status': 'honest_unproved', 'candidate_family': prior['candidate_family'],
        'production_admitted': False, 'native_parity_proven': False,
        'state_admission_proved': False, 'paired_scene_proved': False,
        'thin_raster_cut_proved': False, 'residual_family_classified': False,
        'locked_s290_reproduced': True,
        'locked_prerequisites': prior['locked_prerequisites'],
        'boundary_audit': rows,
        'ordered_gates': prior['ordered_gates'],
        'matched_image_pairs': 0,
        'exact_rgba_edge_residual': None, 'exact_rgba_interior_residual': None,
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0, 'new_images': 0,
        'product_obligations_closed': 0,
        'exclusions_enforced': EXCLUSIONS,
        'requirement_failure_codes': REQUIREMENTS,
        'blocker': 'Complete same-capture state admission absent: all 61 boundaries differ in glyph and other selected scene state; zero same-capture Godot images. Exact source-bound edge/interior membership and RGBA remain unmeasured.',
        'next_discriminator': 'Outside this cut, establish complete same-capture state admission. Only then capture its paired scene, bind source glyph/frame, PlaceObject/MOVE lifetime, placement, transform, compositing and capture boundary, and classify unchanged exact RGBA at identical coordinates with source-bound edge/interior membership. Edge proximity alone does not prove rasterizer causation.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    for name in REQUIREMENTS:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'S299_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code + ': ' + report['blocker'] for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + '\n')
    print('S299_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
