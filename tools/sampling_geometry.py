"""Validate native source-collision candidates at each root observation boundary."""
import argparse
import json
import math
from pathlib import Path

from tools.sampling_native import sha, validate
from tools.probes.collect_ai_reference import decode_number


def collect(lines, run_id, frames, sources):
    samples = []
    current = None
    lifetimes = {}
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8 or parts[:2] != ['AIREF', run_id]:
            raise ValueError('foreign or malformed geometry capture')
        tick, kind, value = int(parts[5]), parts[6], parts[7]
        if kind == 'geometry_error':
            raise ValueError('source geometry error: ' + value)
        if not kind.startswith('geometry_'):
            continue
        if kind == 'geometry_begin':
            if current is not None or tick != len(samples):
                raise ValueError('missing/duplicate/out-of-order geometry sample')
            current = {'tick': tick, 'boxes': []}
        elif current is None or tick != current['tick']:
            raise ValueError('geometry event outside sample')
        elif kind == 'geometry_box':
            fields = value.split(',')
            if len(fields) != 17:
                raise ValueError('incomplete geometry box')
            role, path, instance, source = fields[:4]
            if role not in ('hurt', 'attack', 'helper_attack', 'stage_attack') or source not in sources:
                raise ValueError('unknown geometry role/source')
            birth, depth, frame = map(int, fields[4:7])
            numbers = [decode_number(v) for v in fields[7:]]
            if not all(math.isfinite(n) for n in numbers):
                raise ValueError('nonfinite geometry')
            if any(b['path'] == path or b['instance_id'] == instance for b in current['boxes']):
                raise ValueError('duplicate geometry box')
            if instance in lifetimes:
                old = lifetimes[instance]
                if (old['path'], old['source'], old['birth_display']) != (path, source, birth):
                    raise ValueError('instance identity changed')
            else:
                lifetimes[instance] = {'path': path, 'source': source, 'birth_display': birth,
                                       'first_observed_tick': tick}
            lifetimes[instance]['last_observed_tick'] = tick
            a, b, c, d, tx, ty = numbers[:6]
            xmin, ymin, xmax, ymax = numbers[6:]
            corners = [(a*x+c*y+tx, b*x+d*y+ty) for x in (xmin, xmax) for y in (ymin, ymax)]
            global_bounds = [min(x for x,y in corners), min(y for x,y in corners),
                             max(x for x,y in corners), max(y for x,y in corners)]
            current['boxes'].append({'role': role, 'path': path, 'instance_id': instance,
                                     'source': source, 'birth_display': birth, 'depth': depth,
                                     'frame': frame, 'global_matrix': numbers[:6], 'local_bounds': numbers[6:],
                                     'global_bounds_from_local_rectangle': global_bounds})
        elif kind == 'geometry_end':
            count, receivers = map(int, value.split(','))
            if count != len(current['boxes']) or receivers < 0:
                raise ValueError('missing geometry box or bad sample counts')
            current['receiver_count'] = receivers
            current['by_role'] = {role: [b['instance_id'] for b in current['boxes'] if b['role'] == role]
                                  for role in ('hurt', 'attack', 'helper_attack', 'stage_attack')}
            samples.append(current)
            current = None
        else:
            raise ValueError('unsupported geometry event: ' + kind)
    if current is not None or [s['tick'] for s in samples] != list(range(frames + 1)):
        raise ValueError('missing geometry samples')
    return {'samples': samples, 'observed_lifetimes': lifetimes}


def gate(case_path, receipt_path):
    receipt_hash = validate(case_path, receipt_path)
    receipt = json.loads(receipt_path.read_text())
    build = json.loads((Path(receipt['build']) / 'build.json').read_text())
    if build.get('sampling_geometry') is not True:
        raise ValueError('build lacks sampling geometry observer')
    root = Path(__file__).resolve().parents[1]
    sources = set()
    for name in build['sources_sha256']:
        if name.startswith('scripts/') and name.endswith('.json'):
            bundle = json.loads((root / name).read_text())
            sources.update(bundle['game_file'] + '#' + script['path'] for script in bundle['scripts'])
    result = collect(Path(receipt['trace']).read_text().splitlines(), build['run_id'],
                     build['move_case']['frames'], sources)
    # This cell has two live fighter receivers. A one-sided scan is not evidence.
    for sample in result['samples']:
        for slot in ('p1', 'p2'):
            if not any(b['role'] == 'hurt' and f'.game.{slot}.' in b['path'] for b in sample['boxes']):
                raise ValueError(f"missing {slot} receiver at tick {sample['tick']}")
    result.update(case_id=build['move_case']['id'], receipt_sha256=receipt_hash,
                  capture_sha256=sha(Path(receipt['trace'])), native_parity_proven=False,
                  production_admitted=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = gate(args.case, args.receipt)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print('GEOMETRY_COVERAGE_OK', len(result['samples']))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'geometry error: {error}\n')


if __name__ == '__main__':
    main()
