"""Extract the first control-transfer prefix of s354 table index zero."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, END = 0xd227d, 0xd2288
EXPECTED = bytes.fromhex('89d883e0074883f8077508')


def extract(binary):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    raw = binary.read_bytes()
    if hashlib.sha256(raw).hexdigest() != locked['binary_sha256']:
        raise ValueError('Binary differs from locked receipt')
    spec = importlib.util.spec_from_file_location('s363_macho', HERE.parent / 's303/audit_native.py')
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    module = decoder.macho(raw)
    if module != locked['module']:
        raise ValueError('Mach-O metadata differs')
    offset = decoder.file_offset(module, locked['image_base'] + START, END - START)
    data = raw[offset:offset + END - START]
    if data != EXPECTED:
        raise ValueError('Selected prefix differs')
    return dict(binary_sha256=locked['binary_sha256'], binary_size=len(raw),
                module_uuid=module['uuid'], image_base=locked['image_base'],
                index=0, start=START, end_exclusive=END, file_offset=offset,
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
