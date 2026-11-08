"""Audit the exclusive diff and index the completed local evidence package."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '3e48153c89da05466213621a2ef05ad8261034df'
PREFIX = HERE.relative_to(ROOT).as_posix() + '/'
TRACKING = ['docs/STATUS.md', 'docs/SAMPLING_UPGRADE.md', 'plan/tasks.json', 'manifest.json']
AUTHORITY = 'evidence/sampling-upgrade/next-fix-priority-after-s362.md'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().splitlines()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')


for report in ('gates.json', 'project-checks.json'):
    records = json.loads((HERE / report).read_text())
    if not records or not all(r['passed'] and r['exit_code'] == r['expected_exit'] for r in records):
        raise SystemExit('Incomplete or failed checks: ' + report)

changed = sorted(set(git('diff', '--name-only', BASE) +
                     git('ls-files', '--others', '--exclude-standard')))
unexpected = [p for p in changed if p not in TRACKING and not p.startswith(PREFIX)]
if unexpected:
    raise SystemExit('Unexpected scope changes: ' + repr(unexpected))
prior = [p for p in git('ls-tree', '-r', '--name-only', BASE, 'evidence/sampling-upgrade')
         if any(p.startswith(f'evidence/sampling-upgrade/s{i}/') for i in range(254, 366))]
write('scope-audit.json', dict(base=BASE, allowed_new_prefix=PREFIX,
      allowed_tracking_paths=TRACKING, unchanged_authority=AUTHORITY, changed_paths=changed, unexpected_paths=unexpected,
      prior_evidence_files_covered_by_empty_diff=len(prior),
      prior_s254_s365_diff_empty=True, historical_authority_diff_empty=True,
      runtime_contracts_shared_tools_game_scripts_diff_empty=True,
      other_ranks_executed=[], after_s353_ranks_1_9='delivered', after_s362_ranks_1_3='delivered', executed_rank=4, ranks_5_plus='planning_only'))
old = json.loads(subprocess.check_output(['git', 'show', BASE + ':manifest.json'], cwd=ROOT))
current = json.loads((ROOT / 'manifest.json').read_text())
changes = {key: dict(before=old['file_sha256'].get(key), after=value)
           for key, value in current['file_sha256'].items() if old['file_sha256'].get(key) != value}
if set(changes) != {'docs/STATUS.md', 'plan/tasks.json'}:
    raise SystemExit('Unexpected manifest hash changes')
for key, record in changes.items():
    if hashlib.sha256((ROOT / key).read_bytes()).hexdigest() != record['after']:
        raise SystemExit('Tracking hash mismatch: ' + key)
restored = json.loads(json.dumps(current))
for key, record in changes.items():
    restored['file_sha256'][key] = record['before']
if restored != old:
    raise SystemExit('Unexpected manifest structure changes')
write('manifest-audit.json', dict(base=BASE, changed_hash_entries=changes,
      only_tracking_hashes_updated=True, all_other_manifest_fields_unchanged=True,
      new_evidence_index=PREFIX + 'artifact-sha256.json'))
start = json.loads((HERE / 'implementation-start.json').read_text())['started_unix']
end = time.time()
write('session-timing.json', dict(started_unix=start, completed_unix=end,
      measured_wall_seconds=end-start, actual_person_days=None,
      includes='Measured implementation interval, independent callback-name operand candidate discovery, packaging and local checks',
      excludes='Initial reading/design/reconnaissance and subsequent commit/push/PR'))
write('artifact-sha256.json', {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
      for p in sorted(HERE.rglob('*')) if p.is_file() and p.name != 'artifact-sha256.json'
      and '__pycache__' not in p.parts})
print('S366_SCOPE_AND_ARTIFACT_INDEX_OK')
