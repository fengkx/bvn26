"""Read only the nineteen s345-bounded signed offsets from a receipt-pinned player."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, COUNT = 0xd2540, 19


def extract(binary):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    raw = binary.read_bytes()
    if hashlib.sha256(raw).hexdigest() != locked['binary_sha256']:
        raise ValueError('Binary differs from locked receipt')
    spec = importlib.util.spec_from_file_location('s354_macho', HERE.parent / 's303/audit_native.py')
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    module = decoder.macho(raw)
    if module != locked['module']:
        raise ValueError('Mach-O metadata differs')
    offset = decoder.file_offset(module, locked['image_base'] + START, COUNT * 4)
    data = raw[offset:offset + COUNT * 4]
    return dict(binary_sha256=locked['binary_sha256'], binary_size=len(raw),
                module_uuid=module['uuid'], image_base=locked['image_base'],
                start=START, end_exclusive=START + COUNT * 4, file_offset=offset,
                hex=data.hex(), sha256=decoder.sha(data),
                new_player_launches=0, new_memory_reads=0, destination_bytes_read=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.binary), indent=2) + '\n')


if __name__ == '__main__':
    main()
