"""Locate original root observations between a goto caller and target script."""
import argparse
import hashlib
import json
from pathlib import Path


def analyze(path: Path) -> dict:
    events = [json.loads(line) for line in path.read_text().splitlines()]
    transitions = []
    for index, caller in enumerate(events):
        if caller['kind'] != 'frame_state_exit' or not caller['value'].startswith('390,1,'):
            continue
        pending = events[index + 1:]
        entry_index = next((i for i, event in enumerate(pending)
                            if event['kind'] == 'frame_state_enter'), None)
        if entry_index is None:
            continue
        entry = pending[entry_index]
        if not entry['value'].startswith('1,1,'):
            continue
        target_exit = next((event for event in pending[entry_index + 1:]
                            if event['kind'] == 'frame_state_exit'), None)
        if target_exit is None or not target_exit['value'].startswith('1,1,'):
            continue
        observations = [event for event in pending[:entry_index]
                        if event['kind'] == 'state' and event['value'].startswith('p2,')]
        transitions.append({'caller_exit': caller, 'root_observations_before_target': observations,
                            'target_entry': entry, 'target_exit': target_exit})
    return {
        'status': 'source_observation_order_only',
        'events_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'transition_count': len(transitions), 'transitions': transitions,
        'native_parity_verified': False,
        'limit': 'Root enterFrame snapshots are not necessarily after queued target DoActions; do not delay runtime writes to match an earlier observation.',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.events)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'transitions': result['transition_count']}))


if __name__ == '__main__':
    main()
