"""Seal only reviewed Sage Naruto changes after targeted native/Web checks."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/characters/minrenx'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    web = read(OUT / 'web/execution.json')
    web_passed = web['status'] == 'passed_targeted_keyboard_and_transformation'
    assert web_passed or web['status'] == 'blocked_on_locked_desktop'
    assert 'MINRENX_PACKED_PROFILES_OK' in (OUT / 'logs/packed-profile.log').read_text()
    comparisons = [row for name in ['comparisons.json', 'form-comparisons.json',
                    'cancel-comparisons.json', 'crossing-comparisons.json', 'receive-comparisons.json']
                   for row in read(OUT / name)]
    assert len(comparisons) == 25 and all(row['status'] == 'matched' for row in comparisons)
    baseline = read(OUT / 'runtime-hashes-during.json')['sha256']
    assert all(digest(ROOT / path) == sha for path, sha in baseline.items())
    summary = read(OUT / 'validation-summary.json')
    assert len(summary['proof_flags']) == 6 and not any(summary['proof_flags'].values())
    summary.update(status='targeted_sop_validation_passed_full_acceptance_pending' if web_passed else 'integrated_native_passed_web_blocked_on_locked_desktop',
                   recorded_at=datetime.now(timezone.utc).isoformat(),
                   web='Local release export: keyboard selection, natural start, movement/attack/super and required transformation; packed form preflight passed.' if web_passed else 'Export and packed-form preflight passed; foreground keyboard flow blocked by confirmed locked desktop. Two failed attempts retained; no Web gameplay pass.',
                   matchmaking='32 tests and typecheck passed under Node 24.18.0; local Wrangler only.',
                   python='24 integrated guard/manifest checks plus 10 source/selection checks passed.',
                   contracts='6 schemas and 6 examples passed; not gameplay admission.',
                   prior_saved_roster_applicability='All 807 previously tested runtime/package hashes unchanged; 300-case saved corpus receipt retained.')
    summary['not_verified'] = ([] if web_passed else ['foreground Web gameplay']) + ['full aligned audiovisual parity', 'exhaustive AI and boundary matrix',
                               'headed exit cleanup', 'live Internet match', 'full character acceptance', 'production admission']
    write(OUT / 'validation-summary.json', summary)
    durable = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines())
    # Exclude our own manifests and logs still being written by final verification.
    lane = [name for name in durable if (name.startswith('evidence/characters/minrenx/')
            or name.startswith('godot/generated/fighters/minrenx/')
            or name.startswith('godot/generated/forms/minrenx-2/')
            or name.startswith('godot/tests/minrenx_')
            or name.startswith('data/slices/minrenx-') or name.startswith('data/actions/minrenx-'))
            and name != 'evidence/characters/minrenx/artifact-manifest.json'
            and '/logs/' not in name]
    write(OUT / 'artifact-manifest.json', {'proof_flags': summary['proof_flags'],
          'scope': 'Integrated lane evidence and packages; raw logs retained separately',
          'sha256': {name: digest(ROOT / name) for name in sorted(lane) if (ROOT / name).is_file()}})
    manifest_path = ROOT / 'manifest.json'
    manifest = read(manifest_path)
    changed = set(subprocess.check_output(['git', 'diff', '--name-only', '82b5ad6d4'], cwd=ROOT, text=True).splitlines())
    assert not any(name.startswith(('game/', 'scripts/')) for name in changed)
    for name in changed & manifest['file_sha256'].keys():
        if name != 'manifest.json':
            manifest['file_sha256'][name] = digest(ROOT / name)
    additions = lane + ['evidence/characters/minrenx/artifact-manifest.json',
                        'tools/tests/test_minrenx_import.py', 'tools/importer/build_menu_font.py']
    additions += [name for name in durable if name.startswith('godot/generated/main/character_selection/minrenx-')]
    for name in additions:
        path = ROOT / name
        if path.is_file() and not path.is_symlink() and not name.endswith('.import'):
            manifest['file_sha256'][name] = digest(path)
    write(manifest_path, manifest)
    print('MINRENX_INTEGRATION_SEALED', len(lane), 'lane files; source inputs unchanged; six flags false')


if __name__ == '__main__':
    main()
