"""Compare source helper timing with the fixed-input native scene fixture."""
import argparse
import hashlib
import json
from pathlib import Path


def compare(source_path: Path, native_path: Path) -> dict:
    source = []
    for line in source_path.read_text().splitlines():
        event = json.loads(line)
        if event['kind'] != 'helper_state':
            continue
        v = event['value'].split(',')
        source.append(dict(tick=event['fight_tick'], helper_frame=int(v[0]),
                           helper_active=v[1] == 'true', child_frame=None if v[2] == 'undefined' else int(v[2]),
                           defender_frame=int(v[3]), hp=float(v[4]), hits=int(v[5]),
                           pause=v[6] == 'true', energy=float(v[7])))
    native = json.loads(native_path.read_text())
    source_start = next(i for i, row in enumerate(source) if row['helper_active'])
    native_start = next(i for i, row in enumerate(native) if row['helper_active'])
    differences = []
    fields = ['helper_frame', 'helper_active', 'child_frame', 'hp', 'pause', 'energy']
    expected = source[source_start:]
    actual = native[native_start:]
    count = min(len(expected), len(actual))
    for tick, (left, right) in enumerate(zip(expected, actual)):
        for field in fields:
            if left[field] != right[field]:
                differences.append(dict(tick=tick, field=field, expected=left[field], actual=right[field]))
        # Root observations precede deferred standing-frame hits=0. Preserve
        # the native post-step snapshot too; do not change its recorded values.
        for field, key in [('hits', 'hits'), ('defender_frame', 'frame')]:
            if field == 'defender_frame' and left['hp'] == 1000:
                continue
            if left[field] != right['root_state'][key]:
                differences.append(dict(tick=tick, field='root_' + field,
                                        expected=left[field], actual=right['root_state'][key]))
    if count < 120 or expected[count - 1]['helper_active'] or actual[count - 1]['helper_active']:
        raise ValueError('Capture must include the complete summon and recovery')
    settlements = []
    drains = []
    previous_hp = 1000
    previous_energy = expected[0]['energy']
    for row in expected:
        if row['hp'] != previous_hp:
            settlements.append(dict(helper_frame=row['helper_frame'], damage=previous_hp-row['hp']))
            previous_hp = row['hp']
        if row['energy'] < previous_energy:
            drains.append(dict(helper_frame=row['helper_frame'], delta=row['energy']-previous_energy))
        previous_energy = row['energy']
    return dict(status='matched' if not differences else 'first_difference', compared_ticks=count,
                alignment='relative to first visible helper frame 2; actor counters use root observer',
                settlements=settlements, final_hp=previous_hp, energy_drains=drains,
                final_energy=previous_energy, differences=differences,
                source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                native_sha256=hashlib.sha256(native_path.read_bytes()).hexdigest(),
                limits=['Fixed positions and O input only; initial standing phase is not compared.',
                        'Not a full boot, all-character, pixel, audio or browser parity assertion.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.source, args.native)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'matched' else 1)


if __name__ == '__main__':
    main()
