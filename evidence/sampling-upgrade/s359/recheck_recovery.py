"""Recheck the pinned Git archive independently of historical temporary absence."""
import json
from recover_candidate import HERE, probe

old = json.loads((HERE / 'recovery-route.json').read_text())
new = probe()
for key in ('base', 'expected_sha256', 'listing_sha256', 'objects', 'examined_blobs', 'matches'):
    if old[key] != new[key]:
        raise SystemExit('S359_ARCHIVE_CHANGED: ' + key)
print('S359_ARCHIVE_RECHECK_OK; temporary-path state is historical, live association unproved')
