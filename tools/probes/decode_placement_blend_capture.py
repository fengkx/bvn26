"""Keep authored blend inputs separate from lossy native straight-alpha readback."""
import argparse
import json
from pathlib import Path


def decode(build: dict, trace: str) -> list:
    rows = [dict(case) for case in build['cases']]
    seen = set()
    done = False
    sequence = 0
    for line in trace.splitlines():
        parts = line.split('|')
        if len(parts) != 8 or parts[:2] != ['AIREF', build['run_id']]:
            continue
        if int(parts[2]) != sequence:
            raise ValueError('Missing or reordered native events')
        sequence += 1
        kind, value = parts[6:]
        if kind == 'done':
            if done or value != 'ok':
                raise ValueError('Invalid completion event')
            done = True
            continue
        if done or kind not in ('back', 'front', 'pixel', 'black'):
            raise ValueError(f'Unexpected native event: {kind}')
        index, packed = map(int, value.split(','))
        if not 0 <= index < len(rows) or (index, kind) in seen:
            raise ValueError('Duplicate or out-of-range native sample')
        seen.add((index, kind))
        rgba = [(packed >> shift) & 255 for shift in (16, 8, 0, 24)]
        rows[index][{'back': 'observed_back', 'front': 'observed_front',
                     'pixel': 'output_pixel', 'black': 'on_black'}[kind]] = rgba
    if not done or len(seen) != len(rows) * 4:
        raise ValueError('Incomplete native capture')
    for row in rows:
        # Drawing onto black measures stored premultiplied bytes directly.
        # Multiplying getPixel32's straight RGB by alpha cannot recover them.
        row['premultiplied'] = row['on_black'][:3] + row['output_pixel'][3:]
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(decode(json.loads(args.build.read_text()),
                                            args.trace.read_text()), indent=2) + '\n')
