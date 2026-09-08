"""Inventory current move evidence without treating dispatch wiring as acceptance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit():
    result = {'status': 'partial_not_source_parity_accepted', 'fighters': {}}
    for name in ('minren', 'yihu'):
        model = json.loads((ROOT / f'godot/generated/fighters/{name}/combat.json').read_text())
        bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
        scripts = {entry['path']: entry['source'] for entry in bundle['scripts']}
        catalog = model['command_catalog']
        moves = []
        for entry in catalog['entries']:
            events = [event for event in model['indexed_source_events'] if event['action'] == entry['label']]
            moves.append({
                'label': entry['label'], 'slot': entry.get('slot'),
                'source_frames': [entry.get('start_frame'), entry.get('end_frame')],
                'dispatch_status': entry['implementation'],
                'source_event_paths': [event['path'] for event in events],
                'exit': model['action_exits'].get(entry['label']),
                'super_events': [event for event in model['super_events'] if event['action'] == entry['label']],
                'container_gotos': [event['path'] for event in events if '_parent.gotoAndStop(' in scripts.get(event['path'], '')],
                'original_same_input_acceptance': 'not_recorded',
            })
        result['fighters'][name] = {
            'source': model['source'],
            'labels': len(moves),
            'wired_labels': sum(move['dispatch_status'] == 'wired' for move in moves),
            'form_attack_counts': {form: len(data['attacks']) for form, data in model['attacks_by_form'].items()},
            'gaps': catalog['gaps'], 'moves': moves,
        }
    return result


if __name__ == '__main__':
    output = ROOT / 'evidence/combat/current-moves-audit.json'
    output.write_text(json.dumps(audit(), ensure_ascii=False, indent=2) + '\n')
    print(output)
