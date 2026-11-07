"""Search receipt bytes in a bounded, read-only Git archive route."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'f57490ff7fe50bb50b11bc53b2becd0429371cdc'
RECEIPT = 'evidence/sampling-upgrade/s283/build-audit.json'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def probe():
    receipt = json.loads((ROOT / RECEIPT).read_text())
    candidate_path, expected = next((p, h) for p, h in receipt['sha256'].items()
                                    if p.endswith('/candidate.swf'))
    base = git('rev-parse', BASE).decode().strip()
    # Pin a commit rather than --all: branch changes cannot alter search scope.
    listing = git('rev-list', '--objects', base)
    objects = []
    for line in listing.decode().splitlines():
        oid, _, name = line.partition(' ')
        if not name.lower().endswith('.swf'):
            continue
        if git('cat-file', '-t', oid).strip() != b'blob':
            continue
        raw = git('cat-file', 'blob', oid)
        digest = hashlib.sha256(raw).hexdigest()
        objects.append(dict(oid=oid, path=name, bytes=len(raw), sha256=digest,
                            receipt_match=digest == expected))
    objects.sort(key=lambda r: (r['path'], r['oid']))
    exact = dict(path=candidate_path, expected_sha256=expected)
    try:
        raw = Path(candidate_path).read_bytes()
    except FileNotFoundError:
        exact.update(status='absent-at-receipt-path', observed_sha256=None)
    else:
        digest = hashlib.sha256(raw).hexdigest()
        exact.update(status='receipt-match' if digest == expected else 'receipt-mismatch',
                     observed_sha256=digest)
    matches = [r for r in objects if r['receipt_match']]
    return dict(slice='s359', route='receipt-hash-reachable-git-blob-recovery',
                base=base, receipt=RECEIPT, expected_sha256=expected,
                command=['git', 'rev-list', '--objects', base],
                listing_sha256=hashlib.sha256(listing).hexdigest(),
                objects=objects, examined_blobs=len(objects), matches=matches,
                exact_receipt_path=exact,
                recovered=bool(matches or exact['status'] == 'receipt-match'),
                loaded_body=None, defining_scope=None, invocation_pair=None,
                uninterrupted_generations=None, independent_native_observations=0,
                reconstructed=False,
                limitation='Only SWF-named blobs reachable from the pinned base and the exact receipt path. '
                           'No dangling objects, other refs, renamed non-SWF blobs, external archives or process memory. '
                           'No match does not prove global absence or debugger impossibility; disk equality is not live qualification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = probe()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('S359_RECOVERY_ATTEMPT', result['examined_blobs'], 'blobs;',
          len(result['matches']), 'archive matches; recovered=', result['recovered'])


if __name__ == '__main__':
    main()
