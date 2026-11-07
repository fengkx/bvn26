"""Check an existing SWF debugger entry without modifying or launching either movie."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import tarfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIPT = 'evidence/sampling-upgrade/s275/native-build.json'
ARCHIVE = 'evidence/sampling-upgrade/s275/native-build.tar.gz'
MOVIE = 'game/fighter/yulong.swf'
DEBUG_TAGS = {58: 'EnableDebugger', 63: 'DebugID', 64: 'EnableDebugger2'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(raw, expected):
    if sha(raw) != expected:
        raise ValueError('Movie differs from pinned build receipt')
    if raw[:3] not in (b'CWS', b'FWS') or len(raw) < 9:
        raise ValueError('Unsupported SWF')
    data = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    if len(data) != struct.unpack_from('<I', data, 4)[0]:
        raise ValueError('SWF length mismatch')
    rows = []
    timelines = 0

    def walk(pos, end, ancestry):
        nonlocal timelines
        timelines += 1
        while pos < end:
            if pos + 2 > end:
                raise ValueError('Truncated tag header')
            offset = pos
            header = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            code, size = header >> 6, header & 63
            if size == 63:
                if pos + 4 > end:
                    raise ValueError('Truncated long tag')
                size = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            stop = pos + size
            if stop > end:
                raise ValueError('Truncated tag payload')
            if code in DEBUG_TAGS:
                rows.append(dict(tag=code, name=DEBUG_TAGS[code], offset=offset,
                                 ancestry=ancestry, payload_hex=data[pos:stop].hex()))
            if code == 39:
                if size < 4:
                    raise ValueError('Truncated sprite')
                walk(pos + 4, stop, ancestry + [struct.unpack_from('<H', data, pos)[0]])
            pos = stop
            if code == 0:
                if size or pos != end:
                    raise ValueError('Invalid End tag')
                return
        raise ValueError('Missing End tag')

    rect_size = (5 + 4 * (data[8] >> 3) + 7) // 8
    walk(8 + rect_size + 4, len(data), [])
    return dict(sha256=sha(raw), file_bytes=len(raw), validated_timelines=timelines,
                debug_tags=rows, debug_tag_counts={name: sum(r['tag'] == code for r in rows)
                                                  for code, name in DEBUG_TAGS.items()})


def probe():
    receipt = json.loads((ROOT / RECEIPT).read_text())
    with tarfile.open(ROOT / ARCHIVE) as archive:
        matches = [m for m in archive.getmembers() if m.name == MOVIE]
        if len(matches) != 1 or not matches[0].isfile():
            raise ValueError('Missing or ambiguous archived candidate')
        candidate = archive.extractfile(matches[0]).read()
    return dict(slice='s356', route='existing-source-debugger-entry',
                hypothesis='Existing debugger metadata might identify a loaded definition independently of numeric dispatch and observer slots.',
                receipt=RECEIPT, archive=ARCHIVE, archive_member=MOVIE,
                original=inspect((ROOT / MOVIE).read_bytes(), receipt['sources_sha256'][MOVIE]),
                candidate=inspect(candidate, receipt['outputs_sha256'][MOVIE]),
                loaded_definition_pair=None, same_input_activation_pair=None,
                defining_scope_pair=None, independent_runtime_observations=[],
                conclusion='Disk identity and debug-tag presence/absence only. No source-breakpoint-to-loaded-definition association or defining-scope channel obtained. Absence does not establish that native debugging is impossible.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(probe(), indent=2) + '\n')


if __name__ == '__main__':
    main()
