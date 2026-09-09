"""Inventory observed evidence and unresolved boundaries without inferring parity."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(cases, native_results, references):
    native = {row['id']: row for row in native_results}
    originals = {row['id']: row for row in references}
    rows = []
    for case in cases:
        original = originals.get(case['id'])
        local = native.get(case['id'])
        status = 'not_run'
        if local:
            status = 'native_only' if local['executed'] else 'native_failed'
        if original:
            status = original['status']
            if status == 'matched' and not original.get('target_seen'):
                if case['target_frames'][0] is None:
                    status = 'matched_source_missing_label'
                elif case['scenario'] == 'energy_below':
                    status = 'matched_negative_case'
                else:
                    status = 'unexercised'
        rows.append({'id': case['id'], 'fighter': case['fighter'], 'label': case['label'],
                     'scenario': case['scenario'], 'status': status,
                     'native': local, 'original': original})
    windows = []
    labels = []
    for fighter in ['minren', 'yihu']:
        catalog = json.loads((ROOT / f'godot/generated/fighters/{fighter}/combat.json').read_text())['command_catalog']
        for entry in catalog['entries']:
            associated = [row for row in rows if row['fighter'] == fighter and row['label'] == entry['label']]
            labels.append({'fighter': fighter, 'label': entry['label'],
                           'source_frames': [entry['start_frame'], entry['end_frame']],
                           'cases': [row['id'] for row in associated],
                           'status': 'cases_listed_not_full_acceptance' if associated else 'chain_or_lifecycle_case_required'})
        for index, window in enumerate(catalog['cancel_windows']):
            for edge, frame in [('before_start', window['start_frame']-1),
                                ('at_start', window['start_frame']),
                                ('at_end', window['end_frame']),
                                ('after_end', window['end_frame']+1)]:
                windows.append({'id': f'{fighter}-window-{index}-{edge}',
                                'fighter': fighter, 'from': window['from'], 'to': window['to'],
                                'predicate': window['predicate'], 'kind': window['kind'],
                                'source_frame': frame, 'source_path': window['source_path'],
                                'source_sha256': window['source_sha256'], 'status': 'not_run'})
    counts = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    return {'status': 'not_accepted', 'scope': 'minren_yihu_base_forms_and_form_exit',
            'case_counts': counts, 'cases': rows, 'labels': labels,
            'source_window_boundaries': windows,
            'additional_required_boundaries': [
                'Hitbox tangency on all four edges, twip offsets inside/outside, both facings',
                'Each hitbox placement, MOVE, removal and renamed-instance lifetime boundary',
                'Hit strength and guard-break thresholds, receiver creation/removal boundaries',
                'Same-tick mutual hits, helper/fighter/stage candidate ordering',
                'Pause/unpause at callback and deferred-script boundaries',
                'KO/timeover/round reset while attacks, helpers and timers remain active',
                'Jump floor/platform transitions and both stage walls',
                'Ghost/ordinary dash cancellation and repeated-input boundaries',
                'Input release, same-tick conflict, focus loss and browser recovery',
                'Form-switch retained state and replacement callback registration'],
            'acceptance_rule': 'No empty, native-only, unexercised or unrecorded row implies original parity.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--native-results', type=Path, required=True)
    parser.add_argument('--reference-results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit([json.loads(p.read_text()) for p in sorted(args.cases.glob('*.json'))],
                   json.loads(args.native_results.read_text()), json.loads(args.reference_results.read_text()))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'case_counts': result['case_counts'],
                      'source_window_boundaries': len(result['source_window_boundaries'])}))


if __name__ == '__main__':
    main()
