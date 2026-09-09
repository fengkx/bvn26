"""Extract observed kaichang inputs and goStep calls for branch comparison."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    events = [json.loads(line) for line in args.events.read_text().splitlines()]
    rows = []
    for index, event in enumerate(events):
        if event['kind'] != 'intro_poll_state':
            continue
        values = event['value'].split(',')
        if len(values) != 6 or values[1] not in ('true', 'false'):
            raise ValueError('Unexpected recorded poll state')
        called = []
        for following in events[index + 1:]:
            if following['kind'] == 'intro_poll':
                break
            if following['kind'] == 'intro_step':
                called.append(int(following['value']))
        rows.append({'sequence': event['sequence'], 'time_ms': event['time_ms'],
                     'step': int(values[0]), 'loaded': values[1] == 'true',
                     'kcplayed': values[2:4], 'frames': values[4:6], 'called_steps': called})
    if not rows:
        raise ValueError('Capture has no observed poll inputs')
    args.output.write_text(json.dumps({
        'scope': 'Observed function inputs and goStep calls, not full battle replay',
        'cases': rows,
    }, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
