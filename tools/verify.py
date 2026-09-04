"""Verify retained assets, exact dependency paths, script bundles and SWF structure.
Run: python3 tools/verify.py
This does not execute the game or verify gameplay equivalence.
"""
from pathlib import Path
import hashlib
import json
import sys
sys.dont_write_bytecode = True
from inspect_swf import inspect

root = Path(__file__).resolve().parent.parent
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
errors = []
for rel, expected in manifest['file_sha256'].items():
    p = root / rel
    if not p.is_file():
        errors.append('Missing file: ' + rel)
    elif hashlib.sha256(p.read_bytes()).hexdigest() != expected:
        errors.append('Hash mismatch: ' + rel)
required = set()
for record in manifest['fighter_catalog'].values():
    for key, prefix in [('url', 'game/fighter/'), ('fzurl', 'game/fighter/fz/'), ('music', 'game/music/')]:
        if key in record:
            required.add(prefix + record[key])
for record in manifest['map_catalog'].values():
    required.add('game/music/' + record['music'])
required.update(['game/music/bleach.mp3', 'game/music/naruto.mp3'])
# Compare exact path strings, including on case-insensitive filesystems.
actual = {p.relative_to(root).as_posix() for p in (root / 'game').rglob('*') if p.is_file()}
for missing in sorted(required - actual):
    errors.append('Unresolved exact-case dependency: ' + missing)
for extra in sorted(actual - required - {'game/main.swf'}):
    errors.append('Unexpected game file: ' + extra)
swfs = 0
for p in sorted((root / 'game').rglob('*.swf')):
    try:
        inspect(p)
        swfs += 1
    except Exception as e:
        errors.append(str(p.relative_to(root)) + ': ' + str(e))
script_count = 0
for entry in manifest['script_bundles']:
    p = root / entry['path']
    data = json.loads(p.read_text(encoding='utf-8'))
    source_sha = hashlib.sha256((root / data['game_file']).read_bytes()).hexdigest()
    if source_sha != data['swf_sha256']:
        errors.append('Scripts associated with different SWF: ' + entry['path'])
    if len(data['scripts']) != entry['script_count']:
        errors.append('Script count mismatch: ' + entry['path'])
    if len({s['path'] for s in data['scripts']}) != len(data['scripts']):
        errors.append('Duplicate script path: ' + entry['path'])
    script_count += len(data['scripts'])
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
print(json.dumps({'status': 'passed', 'assets': len(actual), 'dependencies': len(required), 'swfs': swfs, 'script_bundles': len(manifest['script_bundles']), 'script_exports': script_count}, ensure_ascii=False))
