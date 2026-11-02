"""Pin two archived action windows; never treat static bytes as executed AVM1."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tarfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s278_locked', HERE.parent / 's278/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def action_block(raw, selected):
    if raw[:3] not in (b'CWS', b'FWS'):
        raise ValueError('unsupported SWF')
    data = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    if len(data) != struct.unpack_from('<I', data, 4)[0]:
        raise ValueError('SWF length mismatch')
    found = []

    def walk(pos, end, sprite=None):
        frame = 1
        while pos < end:
            header = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            code, size = header >> 6, header & 63
            if size == 63:
                size = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            stop = pos + size
            if stop > end:
                raise ValueError('truncated tag')
            if code == 39:
                walk(pos + 4, stop, struct.unpack_from('<H', data, pos)[0])
            if (sprite, frame, code) == (selected, 1, 12):
                found.append((data, pos, stop))
            if code == 1:
                frame += 1
            pos = stop
    rect_size = (5 + 4 * (data[8] >> 3) + 7) // 8
    walk(8 + rect_size + 4, len(data))
    if len(found) != 1:
        raise ValueError('missing or ambiguous DoAction')
    return found[0]


def windows(raw, sprite, sequence):
    """Decode record boundaries and only the operands needed for these two sites."""
    data, start, end = action_block(raw, sprite)
    matches = []

    def string(pos, limit):
        stop = data.index(b'\0', pos, limit)
        return data[pos:stop].decode('utf-8'), stop + 1

    def walk(pos, limit, pool, owner):
        rows = []
        while pos < limit:
            offset = pos
            opcode = data[pos]
            pos += 1
            size = 0
            if opcode >= 128:
                size = struct.unpack_from('<H', data, pos)[0]
                pos += 2
            stop = pos + size
            if stop > limit:
                raise ValueError('truncated action')
            label = {0x52: 'CallMethod', 0x17: 'Pop', 0x4f: 'SetMember'}.get(opcode)
            if opcode == 0x88:
                count = struct.unpack_from('<H', data, pos)[0]
                cursor = pos + 2
                pool = []
                for _ in range(count):
                    value, cursor = string(cursor, stop)
                    pool.append(value)
                if cursor != stop:
                    raise ValueError('invalid constant pool')
            elif opcode == 0x96:
                kind = data[pos]
                cursor = pos + 1
                if kind == 0:
                    value, cursor = string(cursor, stop)
                    label = 'Push ' + json.dumps(value, ensure_ascii=False)
                elif kind == 4:
                    label, cursor = 'Push register' + str(data[cursor]), cursor + 1
                elif kind == 3:
                    label = 'Push undefined'
                elif kind == 7:
                    label, cursor = 'Push ' + str(struct.unpack_from('<i', data, cursor)[0]), cursor + 4
                elif kind in (8, 9):
                    index = data[cursor] if kind == 8 else struct.unpack_from('<H', data, cursor)[0]
                    label, cursor = 'Push ' + json.dumps(pool[index], ensure_ascii=False), cursor + (1 if kind == 8 else 2)
                if cursor != stop:
                    label = None  # Other/multi-value Push records cannot match this window.
            elif opcode in (0x8e, 0x9b):
                name, cursor = string(pos, stop)
                count = struct.unpack_from('<H', data, cursor)[0]
                cursor += 2
                registers = flags = None
                if opcode == 0x8e:
                    registers = data[cursor]
                    flags = struct.unpack_from('<H', data, cursor + 1)[0]
                    cursor += 3
                for _ in range(count):
                    if opcode == 0x8e:
                        cursor += 1
                    _, cursor = string(cursor, stop)
                body_size = struct.unpack_from('<H', data, cursor)[0]
                if cursor + 2 != stop or stop + body_size > limit:
                    raise ValueError('invalid function boundary')
                context = {'definition_offset': offset, 'name': name, 'body_offset': stop,
                           'body_length': body_size, 'body_sha256': sha(data[stop:stop + body_size]),
                           'register_count': registers, 'flags': flags,
                           'definition_hex': data[offset:stop].hex()}
                walk(stop, stop + body_size, pool.copy(), context)
                stop += body_size
            rows.append({'offset': offset, 'end': stop, 'instruction': label,
                         'hex': data[offset:stop].hex() if label else None})
            pos = stop
        wanted = sequence.splitlines()
        for index in range(len(rows) - len(wanted) + 1):
            selected = rows[index:index + len(wanted)]
            if [row['instruction'] for row in selected] == wanted:
                matches.append({'definition': owner, 'instructions': selected,
                                'window_sha256': sha(data[selected[0]['offset']:selected[-1]['end']])})
    walk(start, end, [], None)
    if len(matches) != 1 or matches[0]['definition'] is None:
        raise ValueError('missing or ambiguous function instruction window')
    return dict(matches[0], sprite=sprite, frame=1, doaction_offset=start,
                doaction_sha256=sha(data[start:end]), swf_sha256=sha(raw),
                coordinates='Uncompressed SWF offsets; NOT loaded AVM1 PCs or native addresses')


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = load_prior()
    replay = prior.diagnose()
    sites = {}
    for name, archive, member, sprite, sequence in (
        ('chad', 's257/native-build.tar.gz', 'game/fighter/chad.swf', 16, prior.CHAD_SEQUENCE),
        ('authored_control', 's266/build-extension.tar.gz', 'game/main.swf', 60000, prior.CONTROL_SEQUENCE),
    ):
        with tarfile.open(HERE.parent / archive) as package:
            raw = package.extractfile(member).read()
        sites[name] = dict(windows(raw, sprite, sequence), archive=archive, member=member)
    return {'base': 'c0bb50ee', 'scope': 'AFTER-s281 rank 7 only',
            'production_admitted': False, 'native_parity_proven': False,
            'exact_continuation_proved': False, 'product_obligations_closed': 0,
            'historical': replay['historical'], 'static_sites': sites,
            'historical_cpu_entry_stop': replay['native_cpu_entry_stop_observed'],
            'historical_resolver_locations': 0,
            'observations': {key: None for key in ('loaded_action_buffer', 'executed_callmethod',
                'executed_pop', 'executed_register_write', 'operand_stack', 'defining_activation',
                'retained_control_activation', 'unwind_or_resume_boundary')},
            'new_builds': 0, 'new_captures': 0, 'new_player_launches': 0,
            'missing': ['Native dispatch and activation resolver',
                        'Loaded buffer identity and current/next cursor convention',
                        'Retained authored control call/Pop/register4 write in one activation',
                        'Chad call/Pop/register5 write or observed unwind/resume boundary'],
            'exclusions': ['CPU entry as AVM proof', 'removal as return',
                           'root-worker equivalence', 'broad interpreter']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-native-continuation', action='store_true')
    parser.add_argument('--require-retained-activation', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.require_native_continuation or args.require_retained_activation:
        parser.exit(1, 'S288_NATIVE_CONTINUATION_UNPROVED: ' + '; '.join(report['missing']) + '\n')
    print('S288_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
