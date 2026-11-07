"""AFTER-s335 rank 9 only: retain blocked raster prerequisites without repair."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'bad454d9bb7afdf09c5af782bf61aa73993248ab'
REQUIREMENTS = {
    'state-admission': 'S344_STATE_ADMISSION_UNPROVED',
    'paired-scene': 'S344_PAIRED_SCENE_UNPROVED',
    'thin-raster': 'S344_STRICT_RASTER_UNPROVED',
}


def locked_module():
    spec = importlib.util.spec_from_file_location('s344_locked_s335', HERE.parent / 's335/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_locked(prior, retained):
    if prior != retained:
        raise ValueError('Locked s335 replay differs')
    # Reuse the retained rejection guards; no new accepting admission policy.
    return locked_module().audit_locked(prior, retained)


def diagnose():
    locked = locked_module()
    locked.locked_module().locked_module().verify_pins(ROOT, json.loads((HERE / 'input-sha256.json').read_text()))
    prior = locked.diagnose()
    retained = json.loads((HERE.parent / 's335/diagnosis.json').read_text())
    rows = audit_locked(prior, retained)
    return {
        'slice': 's344', 'base': BASE, 'scope': 'AFTER-s335 rank #9 only',
        'status': 'honest_unproved', 'candidate_family': prior['candidate_family'],
        'production_admitted': False, 'native_parity_proven': False,
        'state_admission_proved': False, 'paired_scene_proved': False,
        'thin_raster_cut_proved': False, 'residual_family_classified': False,
        'locked_s335_reproduced': True,
        'evidence_basis': 'Retained historical evidence replay; no new independent runtime observation.',
        'new_independent_runtime_observations': [],
        'locked_prerequisites': prior['locked_prerequisites'],
        'boundary_audit': rows, 'ordered_gates': prior['ordered_gates'],
        'matched_image_pairs': 0, 'eligible_capture_boundaries': 0, 'classified_boundaries': 0,
        'exact_rgba_edge_residual': None, 'exact_rgba_interior_residual': None,
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0, 'new_images': 0,
        'product_obligations_closed': 0, 'm0_02_status': 'pending',
        'exclusions_enforced': [
            'admission repair', 'ranks 1-8 execution', 're-ranking', 'tolerance',
            'offset search', 'image substitution', 'camera rounding', 'renderer rewrite',
            'game/scripts/runtime/contracts changes', 'shared sampler/threshold/validator changes',
            's254-s343 edits',
        ],
        'requirement_failure_codes': REQUIREMENTS,
        'blocker': prior['blocker'], 'next_discriminator': prior['next_discriminator'],
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
        parser.exit(1, 'S344_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code + ': ' + report['blocker'] for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + '\n')
    print('S344_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
