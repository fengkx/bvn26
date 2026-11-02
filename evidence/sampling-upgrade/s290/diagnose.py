"""Audit AFTER-s281 rank 9 prerequisites; never promote selected state to parity."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '42bc2c690e83dfeff12367fa67bf944bf4f56366'
ERROR = 'S290_STRICT_RASTER_UNPROVED'


def verify_pins(root, pins):
    for name, expected in pins.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed locked evidence: ' + name)


def replay_locked():
    path = HERE.parent / 's281'
    spec = importlib.util.spec_from_file_location('s290_locked_s281', path / 'diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.diagnose()
    if result != json.loads((path / 'diagnosis.json').read_text()):
        raise ValueError('Locked s281 replay differs')
    return result


def audit_rows(pair, prerequisites):
    """Retain every boundary and separate glyph mismatches from whole-scene state."""
    rows = pair['rows']
    if len(rows) != 61 or [row['tick'] for row in rows] != list(range(61)):
        raise ValueError('Incomplete or reordered state rows')
    counts = Counter(d['field'] for row in rows for d in row['differences'])
    if dict(counts) != pair['differing_snapshot_counts']:
        raise ValueError('State difference summary mismatch')
    retained = prerequisites['s262_via_s272']
    if rows[13] != retained['tick13'] or dict(counts) != retained['differing_snapshot_counts']:
        raise ValueError('s281 state binding differs')
    if pair['state_admitted'] is not False or pair['same_capture_godot_images_written'] != 0:
        raise ValueError('Unexpected admission or image substitution')
    for flag in ('same_capture_state_admitted', 'thin_raster_cut_proved', 'residual_family_classified'):
        if prerequisites[flag] is not False:
            raise ValueError('Unexpected proof promotion: ' + flag)
    if prerequisites['matched_image_pairs'] != 0 or any(
            prerequisites[key] is not None for key in ('exact_rgba_edge_residual', 'exact_rgba_interior_residual')):
        raise ValueError('Unmeasured pixels cannot be reported as residuals')
    result = []
    for row in rows:
        fields = [d['field'] for d in row['differences']]
        result.append({
            'tick': row['tick'], 'display': row['display'], 'firing': row['firing'],
            'run_id': retained['run_id'], 'raw_sha256': retained['raw_sha256'],
            'glyph_mismatch_fields': [f for f in fields if f in ('tens', 'ones')],
            'other_selected_state_mismatch_fields': [f for f in fields if f not in ('tens', 'ones')],
            'full_scene_admitted': False, 'same_capture_image_pair_available': False,
            'pixel_classification': 'not_measured',
        })
    return {
        'rows': result,
        'glyph_mismatch_ticks': [r['tick'] for r in result if r['glyph_mismatch_fields']],
        'other_selected_state_mismatch_ticks': [r['tick'] for r in result if r['other_selected_state_mismatch_fields']],
        'selected_fields_equal_ticks': [r['tick'] for r in result if not r['glyph_mismatch_fields'] and not r['other_selected_state_mismatch_fields']],
        'note': 'Selected equality would not prove full visual phase. Camera differences do not establish HUD camera inheritance or rounding defects.',
    }


def diagnose():
    verify_pins(ROOT, json.loads((HERE / 'input-sha256.json').read_text()))
    locked = replay_locked()
    prerequisites = locked['prerequisites']
    pair = json.loads((HERE.parent / 's272/diagnosis.json').read_text())['pair_audit']
    return {
        'slice': 's290', 'base': BASE, 'scope': 'AFTER-s281 rank #9 only',
        'candidate_family': locked['candidate_family'],
        'production_admitted': False, 'native_parity_proven': False,
        'new_builds': 0, 'new_captures': 0, 'new_images': 0, 'product_obligations_closed': 0,
        'locked_prerequisites': prerequisites,
        'boundary_audit': audit_rows(pair, prerequisites),
        'state_admission_proved': False, 'thin_raster_cut_proved': False,
        'blocker_code': ERROR,
        'ordered_gates': [
            {'stage': 'full_same_capture_state', 'status': 'unproved',
             'reason': 'Wrong glyph/scene state and missing independent child-clock, allocation and registration/intro/scene joins.'},
            {'stage': 'matched_scene_images', 'status': 'blocked',
             'reason': 'Zero same-capture Godot images; local s274 lifetime cannot supply s262 scene admission.'},
            {'stage': 'exact_edge_interior_rgba', 'status': 'not_measured',
             'reason': 'No admitted pair or source-bound edge/interior membership; unavailable residuals remain null.'},
        ],
        'exclusions': ['ranks 1–8 execution', 'tolerance', 'offset search', 'image substitution',
                       'assumed camera rounding', 'renderer rewrite', 'runtime or shared validator changes'],
        'next_discriminator': locked['next_discriminator'].replace('s281', 's290'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-state-admission', action='store_true')
    parser.add_argument('--require-thin-raster', action='store_true')
    args = parser.parse_args()
    try:
        result = diagnose()
    except (ValueError, KeyError, OSError) as error:
        print('S290_EVIDENCE_INVALID: ' + str(error), file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(ERROR + ': full same-capture state and matched image pair absent', file=sys.stderr)
    return int(args.require_state_admission or args.require_thin_raster)


if __name__ == '__main__':
    raise SystemExit(main())
