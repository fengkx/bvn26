"""Check helper pause semantics, repeated CPU overlap and the original trace."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent / 'probes'))
from compare_mode_reference import compare

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/combat/helper-super-overlap'


def run_checks(godot: str, project: Path, output: Path) -> None:
    checks = [
        ('helper_pause_semantics', 'HELPER_PAUSE_SEMANTICS_OK', []),
        ('vs_com_helper_overlap', 'VS_COM_HELPER_OVERLAP_OK', []),
        ('move_case_reference', 'MOVE_CASE_REFERENCE_OK overlap-00',
         [str(EVIDENCE / 'case.json'), str(output / 'native.json')]),
    ]
    for name, marker, arguments in checks:
        command = [godot, '--headless', '--path', str(project),
                   '--log-file', str(output / f'{name}.engine.log'),
                   '--quit-after', '1800', '-s', f'res://tests/{name}.gd']
        if arguments:
            command.extend(['--', *arguments])
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        log = result.stdout + result.stderr
        (output / f'{name}.log').write_text(log)
        # Godot can exit zero after an assertion or script error.
        if result.returncode != 0 or 'SCRIPT ERROR' in log or marker not in log:
            raise RuntimeError(f'{name} failed:\n{log}')
        print(marker, flush=True)

    comparison = compare(EVIDENCE / 'events.jsonl.gz', output / 'native.json')
    (output / 'comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')
    if comparison['status'] != 'matched':
        raise AssertionError(json.dumps(comparison))
    print(f'HELPER_SUPER_OVERLAP_MATCH {comparison["source_states"]} actor states', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bvn-helper-super-overlap-') as directory:
        run_checks(args.godot, ROOT / 'godot', Path(directory))


if __name__ == '__main__':
    main()
