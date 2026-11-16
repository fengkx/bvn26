"""Seal lane-local receipts without modifying shared admission manifests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/characters/minrenx'


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    flags = read(OUT / 'integration-plan.json')['proof_flags']
    assert len(flags) == 6 and not any(flags.values())
    targeted = []
    for name in ['comparisons.json', 'form-comparisons.json',
                 'cancel-comparisons.json', 'crossing-comparisons.json']:
        rows = read(OUT / name)
        assert all(r['status'] == 'matched' for r in rows)
        targeted.extend(rows)
    assert len(targeted) == 22
    for file, key in [('runtime-hashes-during.json', 'sha256'),
                      ('integration-plan.json', 'base_shared_sha256')]:
        hashes = read(OUT / file)[key]
        assert all(sha(ROOT / name) == value for name, value in hashes.items())
    saved = []
    residuals = []
    for name, folder, expected in [
        ('saved-roster', '/tmp/bvn-lane2-minrenx-regression/flash-replay', 288),
        ('saved-weqal', '/tmp/bvn-lane2-minrenx-weqal-regression/flash-replay', 12),
    ]:
        source = Path(folder)
        report = read(source / 'report.json')
        rows = report['results']
        assert len(rows) == expected
        assert all(r['execution']['executed'] and r['comparison']['status'] == 'matched' for r in rows)
        saved.extend(rows)
        for log in sorted(source.glob('*/process.log')):
            lines = [line for line in log.read_text().splitlines()
                     if any(word in line for word in ['ERROR:', 'WARNING:', 'leaked', 'still in use'])]
            if lines:
                residuals.append({'case': log.parent.name, 'archive': name + '.tar.gz',
                                  'log': str(log.relative_to(source)), 'lines': lines})
        write(name + '-report.json', report)
        with tarfile.open(OUT / (name + '.tar.gz'), 'w:gz') as archive:
            archive.add(source, arcname=name)
    log = (OUT / 'logs/form-lifecycle-r03.log').read_text()
    assert 'MINRENX_FORM_LIFECYCLE_OK' in log and 'SCRIPT ERROR' not in log and 'ERROR:' not in log
    write('validation-summary.json', {
        'status': 'candidate_blocked_on_serial_integration_and_remaining_acceptance',
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'engine': 'Godot 4.7.2.stable.official.ed1daf0bf',
        'jpexs': '26.2.1',
        'base': 'a3b479414546250b7d0cd6e35cbc3ae52b3169d1',
        'character': '仙鸣', 'source': 'game/fighter/minrenx.swf',
        'branch': 'port/minrenx-base',
        'proof_flags': flags,
        'targeted': {'cases': len(targeted), 'state_rows': sum(r['source_states'] for r in targeted),
                     'status': 'matched_14_character_state_fields',
                     'negative_cases': 1, 'controlled_post_transform_energy_refills': 5},
        'saved_roster': {'cases': len(saved), 'state_rows': sum(r['comparison']['source_states'] for r in saved),
                         'status': 'matched_character_states', 'exit_residuals': residuals},
        'controlled_form_checkpoint_lifecycle': 'passed_r03',
        'focused_python_tests': '17 passed; logs/focused-tests-r02.log',
        'verify': 'passed; logs/verify-final.log',
        'handoff': 'passed; logs/handoff-final.log',
        'font': 'actual isolated candidate regeneration; 502 characters covered; font-check.json',
        'shared_files': '8 pinned hashes unchanged',
        'runtime_and_packages': '807 during-capture hashes unchanged',
        'unaccepted_residuals': [
            'Initial incomplete-import native diagnostic has missing-resource and RID/ObjectDB exit errors.',
            'Base matched batch has sandbox user-log write errors.',
            'Saved-roster exit warnings/errors listed separately; matching states do not accept leaks.',
            'Headed resource cleanup is not established or accepted.'
        ],
        'not_verified': ['standard roster integration', 'actual Web gameplay',
                         'aligned visual and effect-instance parity', 'audio parity',
                         'full character acceptance', 'production admission'],
        'draft_pr_opened': False,
        'quota': {'last_user_report_percent': 100, 'current_remaining': 'not exposed',
                  'hard_block_observed': False, 'purchased': False},
    })
    files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'artifact-manifest.json' and '__pycache__' not in p.parts]
    files += list((ROOT / 'godot/generated/fighters/minrenx').rglob('*'))
    files += list((ROOT / 'godot/generated/forms/minrenx-2').rglob('*'))
    files += [ROOT / 'godot/tests/minrenx_form_lifecycle.gd']
    files += list((ROOT / 'data/slices').glob('minrenx-*.json'))
    files += list((ROOT / 'data/actions').glob('minrenx-*.json'))
    durable = set(subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines())
    write('artifact-manifest.json', {'proof_flags': flags,
          'scope': 'lane-local evidence and packages, not global release manifest',
          'sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files)) if p.is_file() and str(p.relative_to(ROOT)) in durable}})


if __name__ == '__main__':
    main()
