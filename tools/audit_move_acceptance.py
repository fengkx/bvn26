"""Inventory observed evidence and unresolved boundaries without inferring parity."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(cases, native_results, references, deferred_labels=()):
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
        if local and not local['executed']:
            status = 'native_failed'
        rows.append({'id': case['id'], 'fighter': case['fighter'], 'label': case['label'],
                     'scenario': case['scenario'], 'status': status,
                     'native': local, 'original': original})
    windows = []
    labels = []
    fighters = sorted({case['fighter'] for case in cases})
    for fighter in fighters:
        catalog = json.loads((ROOT / f'godot/generated/fighters/{fighter}/combat.json').read_text())['command_catalog']
        for entry in catalog['entries']:
            associated = [row for row in rows if row['fighter'] == fighter and row['label'] == entry['label']]
            labels.append({'fighter': fighter, 'label': entry['label'],
                           'source_frames': [entry['start_frame'], entry['end_frame']],
                           'cases': [row['id'] for row in associated],
                           'status': 'deferred_by_scope' if entry['label'] in deferred_labels else
                           'cases_listed_not_full_acceptance' if associated else 'chain_or_lifecycle_case_required'})
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
    by_id = {row['id']: row for row in rows}
    for boundary in windows:
        row = by_id.get(boundary['id'])
        if row is None:
            continue
        boundary['status'] = 'root_input_phase_matched' if row['status'] == 'matched' else row['status']
        boundary['input_phase'] = 'root observation before next-display key publication'
        if row['original']:
            boundary['observation'] = row['original'].get('cancellation')
    counts = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    matched_statuses = {'matched', 'matched_negative_case', 'matched_source_missing_label'}
    targeted_matched = bool(rows) and all(
        row['status'] in matched_statuses and row['native'] and row['native']['executed']
        for row in rows)
    # Keep the legacy full-acceptance field conservative for existing consumers.
    return {'status': 'not_accepted',
            'targeted_status': 'targeted_cases_matched' if targeted_matched else 'not_accepted',
            'targeted_unmatched_cases': [row['id'] for row in rows
                                       if row['status'] not in matched_statuses
                                       or not row['native'] or not row['native']['executed']],
            'full_acceptance': 'not_accepted', 'scope': '_'.join(fighters) + '_base_forms',
            'deferred_labels': list(deferred_labels),
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
                'Input release and same-tick conflict',
                'OS/canvas focus loss and held-key release',
                'Page visibility changes and browser recovery',
                *([] if '万解' in deferred_labels else
                  ['Form-switch retained state and replacement callback registration'])],
            'acceptance_rule': 'No empty, native-only, unexercised or unrecorded row implies original parity.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--native-results', type=Path, required=True)
    parser.add_argument('--reference-results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--defer-label', action='append', default=[])
    args = parser.parse_args()
    result = audit([json.loads(p.read_text()) for p in sorted(args.cases.glob('*.json'))],
                   json.loads(args.native_results.read_text()), json.loads(args.reference_results.read_text()), args.defer_label)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'targeted_status': result['targeted_status'], 'case_counts': result['case_counts'],
                      'source_window_boundaries': len(result['source_window_boundaries'])}))


if __name__ == '__main__':
    main()
