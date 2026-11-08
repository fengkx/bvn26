"""Extract the first control-transfer prefix of the selected s360 direct call."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, END = 0x5d960, 0x5d96b
EXPECTED = bytes.fromhex('554889e531c04885ff7449')


def extract(binary):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    raw = binary.read_bytes()
    if hashlib.sha256(raw).hexdigest() != locked['binary_sha256']:
        raise ValueError('Binary differs from locked receipt')
    spec = importlib.util.spec_from_file_location('s365_macho', HERE.parent / 's303/audit_native.py')
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    module = decoder.macho(raw)
    if module != locked['module']:
        raise ValueError('Mach-O metadata differs')
    offset = decoder.file_offset(module, locked['image_base'] + START, END - START)
    relative_spec = importlib.util.spec_from_file_location('s365_boundaries', HERE.parent / 's360/resolve_relative.py')
    relative = importlib.util.module_from_spec(relative_spec)
    relative_spec.loader.exec_module(relative)
    bounds = json.loads((HERE.parent / 's360/relative-attempt.json').read_text())['function_starts']
    stream = raw[bounds['file_offset']:bounds['file_offset'] + bounds['size']]
    if hashlib.sha256(stream).hexdigest() != bounds['sha256']:
        raise ValueError('Function-start custody differs')
    starts = relative.function_starts(stream, bounds['base'])
    entry = locked['image_base'] + START
    index = starts.index(entry)
    if starts[index + 1] < locked['image_base'] + END:
        raise ValueError('Prefix crosses function boundary')
    data = raw[offset:offset + END - START]
    if data != EXPECTED:
        raise ValueError('Selected prefix differs')
    return dict(binary_sha256=locked['binary_sha256'], binary_size=len(raw),
                module_uuid=module['uuid'], image_base=locked['image_base'],
                caller=0xbfcfd, start=START, end_exclusive=END, file_offset=offset,
                function_start=entry, next_function_start=starts[index + 1],
                hex=data.hex(), sha256=decoder.sha(data), successor_bytes_read=0,
                new_player_launches=0, new_memory_reads=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary or Path(json.loads((HERE.parent / 's303/native-audit.json').read_text())['binary'])
    args.output.write_text(json.dumps(extract(binary), indent=2) + '\n')


if __name__ == '__main__':
    main()
