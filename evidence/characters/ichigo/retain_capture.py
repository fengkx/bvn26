"""Retain source-only capture artifacts without scratch game symlinks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def retain(source, destination):
    destination.mkdir(parents=True, exist_ok=False)
    records = []
    for path in sorted(source.rglob('*')):
        if path.is_symlink() or not path.is_file() or 'game' in path.relative_to(source).parts:
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        compressed = len(data) > 20000
        if compressed:
            target = target.with_name(target.name + '.gz')
            target.write_bytes(gzip.compress(data, mtime=0))
        else:
            target.write_bytes(data)
        records.append({'path': target.relative_to(destination).as_posix(),
                        'uncompressed_sha256': hashlib.sha256(data).hexdigest(),
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                        'bytes': len(data), 'gzip': compressed})
    (destination / 'archive-index.json').write_text(json.dumps({
        'source': str(source), 'status': 'source_only_not_native_parity',
        'files': records}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    retain(args.source, args.destination)
