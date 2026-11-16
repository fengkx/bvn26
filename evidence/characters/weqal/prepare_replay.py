"""Bind native external timer delivery to observed original callback boundaries."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path


def prepare(case, events):
    fixture = json.loads(case.read_text())
    retained = events if events.exists() else Path(str(events) + '.gz')
    raw = gzip.decompress(retained.read_bytes()) if retained.suffix == '.gz' else retained.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    assert any(row['kind'] == 'done' for row in rows)
    tape = []
    origins = ['fighter/weqal#DefineSprite_387/frame_1/DoAction.as']
    for index, row in enumerate(rows):
        if row['kind'] != 'form_interval_enter':
            continue
        assert rows[index + 1]['kind'] == 'form_interval_exit'
        origin, receiver, _ = row['value'].split(',')
        assert receiver == '_level0.game.p1.mc' and origin in origins
        assert any(r['kind'] == 'state' and r['fight_tick'] == row['fight_tick']
                   for r in rows[:index])
        tape.append({'before_tick': row['fight_tick'] + 1, 'id': origins.index(origin) + 1,
                     'source_sequence': row['sequence'], 'source_origin': origin})
    for slot, fields in fixture.get('source_state_preconditions', {}).items():
        for field in fields:
            assert any(r['kind'] == 'source_state_precondition' and
                       r['value'].startswith(slot + ',' + field + ',') for r in rows)
    fixture['form_interval_tape'] = tape
    fixture['wrapper_probe'] = any(r['kind'] == 'wrapper_state' for r in rows)
    fixture['form_interval_provenance'] = {
        'events': str(events), 'sha256': hashlib.sha256(raw).hexdigest(),
        'phase': 'After root state N, before next display; delivered before tick N+1.',
        'ids': 'First registration 1; source clearInterval then second registration 2.'}
    return fixture


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['case', 'events', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(prepare(args.case, args.events), ensure_ascii=False, indent=2) + '\n')
