"""Replay immutable e84a and inspect encoded timelines; never infer native lifetime."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from urllib.parse import unquote
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HISTORY = HERE.parent / 'native-fight-r22-live-03'
spec = importlib.util.spec_from_file_location('r23_history', HERE.parent / 'native-fight-r21/analyze.py')
r21 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r21)
FLAGS = r21.r19.r17.FLAGS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tags(data):
    position, frame = 0, 1
    while position < len(data):
        if position + 2 > len(data):
            raise ValueError('Truncated tag header')
        header = struct.unpack_from('<H', data, position)[0]
        position += 2
        kind, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack_from('<I', data, position)[0]
            position += 4
        payload = data[position:position + size]
        position += size
        if len(payload) != size:
            raise ValueError('Truncated tag payload')
        yield frame, kind, payload
        if kind == 1:
            frame += 1


def timeline(raw):
    if raw[:3] not in (b'CWS', b'FWS'):
        raise ValueError('Unsupported SWF')
    body = zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:]
    if len(body) + 8 != struct.unpack_from('<I', raw, 4)[0]:
        raise ValueError('SWF length mismatch')
    offset = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    result = []
    for _, kind, payload in tags(body[offset:]):
        if kind != 39 or struct.unpack_from('<H', payload)[0] != 638:
            continue
        for frame, kind, payload in tags(payload[4:]):
            row = dict(frame=frame, tag=kind, payload_sha256=hashlib.sha256(payload).hexdigest())
            if kind == 43:
                row['label'] = payload.split(b'\0')[0].decode('utf8')
            elif kind == 26:
                row.update(flags=payload[0], depth=struct.unpack_from('<H', payload, 1)[0],
                           move=bool(payload[0] & 1))
                if payload[0] & 2:
                    row['character_id'] = struct.unpack_from('<H', payload, 3)[0]
            elif kind == 28:
                row['depth'] = struct.unpack_from('<H', payload)[0]
            elif kind not in (1, 12):
                continue
            result.append(row)
    if not result:
        raise ValueError('Missing body638')
    return result


def target_observations(raw, tag):
    """Parse observations only. Never join target entries to an earlier invocation."""
    result = []
    for index, line in enumerate(raw.splitlines()):
        if not line.startswith(b'M002TARGET|'):
            continue
        fields = line.decode('ascii').split('|')
        if len(fields) != 5 or fields[1:3] != [tag, 'yihu638-frame174']:
            raise ValueError('Foreign/malformed target marker')
        owner = unquote(fields[3])
        if owner not in ('/game/p1/mc', '/game/p2/mc') or fields[4] != '174':
            raise ValueError('Unexpected body/frame target marker')
        result.append(dict(raw_line=index + 1, owner=owner, frame=174,
                           initiating_call_join_proven=False, helper_lifetime_proven=False))
    return result


def replay():
    for name, digest in json.loads((HERE / 'input-pins.json').read_text()).items():
        if sha(ROOT / name) != digest:
            raise ValueError('Pinned input mismatch: ' + name)
    build = json.loads((HISTORY / 'build.json').read_text())
    raw = (HISTORY / 'run-01/combined.log').read_bytes()
    if raw != (HISTORY / 'run-01/flashlog.after.log').read_bytes():
        raise ValueError('Historical raw log mismatch')
    records, rows = r21.parse(raw, build['run_id'])
    report = dict(**FLAGS, cause='unproved', live_validated=False,
                  literal=r21.classify(records, rows, build['run_id']),
                  candidate=[r for r in rows if 6513 <= r['seq'] <= 6527],
                  helper_installations=[r for r in rows if r['kind'] == 'decision-installed' and 'instance3413' in r['data']],
                  target_observations=target_observations(raw, build['run_id']),
                  timeline=timeline((ROOT / 'game/fighter/yihu.swf').read_bytes()))
    try:
        r21.r19.r17.history.r05.validate_rows((HISTORY / 'run-01/tagged.log').read_bytes(), build)
    except ValueError as exc:
        report['structural_refusal'] = str(exc)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = replay()
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report.get('structural_refusal', 'No independent oracle acceptance'))
    print('Target marker has no live proof; cause/lifetime/call join unproved')
    raise SystemExit(1)
