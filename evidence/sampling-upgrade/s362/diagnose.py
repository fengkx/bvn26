"""AFTER-s353 rank 9 only: independent negative digit witnesses; no admission repair."""
import argparse
import hashlib
import sys
sys.dont_write_bytecode = True
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '24282a2205ea7f024980834585c8b7b694bc3fe5'
REQUIREMENTS = {
    'state-admission': 'S362_STATE_ADMISSION_UNPROVED',
    'paired-scene': 'S362_PAIRED_SCENE_UNPROVED',
    'thin-raster': 'S362_STRICT_RASTER_UNPROVED',
}


def locked_module():
    spec = importlib.util.spec_from_file_location('s362_locked_s353', HERE.parent / 's353/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_locked(prior, retained):
    if prior != retained:
        raise ValueError('Locked s353 replay differs')
    # Reuse the retained rejection guards; no new accepting admission policy.
    return locked_module().audit_locked(prior, retained)


def diagnose():
    locked = locked_module()
    for name, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Changed input: ' + name)
    prior = locked.diagnose()
    retained = json.loads((HERE.parent / 's353/diagnosis.json').read_text())
    rows = audit_locked(prior, retained)
    spec = importlib.util.spec_from_file_location('s362_witness', HERE / 'derive_digit_witnesses.py')
    route = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(route)
    independent = route.collect()
    if independent != json.loads((HERE / 'digit-witnesses.json').read_text()):
        raise ValueError('Independent derivation differs')
    return {
        'independent_negative_derivation': independent,
        'slice': 's362', 'base': BASE, 'scope': 'AFTER-s353 rank #9 only',
        'status': 'honest_unproved', 'candidate_family': prior['candidate_family'],
        'production_admitted': False, 'native_parity_proven': False,
        'state_admission_proved': False, 'paired_scene_proved': False,
        'thin_raster_cut_proved': False, 'residual_family_classified': False,
        'locked_s353_reproduced': True,
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
            's254-s361 edits',
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
        parser.exit(1, 'S362_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code + ': ' + report['blocker'] for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + '\n')
    print('S362_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
