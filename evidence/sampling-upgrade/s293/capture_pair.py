"""Explicit s293-only capture; archive and check each host log under the capture lock."""
import argparse
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 's284'))
from qualify import qualify
from tools.probes import capture_native_player as player
from tools.sampling_native import seal, validate

CASE = HERE.parent / 's228/ichigo__attack__neutral__ground__near.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--allow-window-activation', action='store_true')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('native player may activate its window')
    player.preflight()
    records = []
    for mode in ('normal', 'held'):
        output = HERE / mode
        output.mkdir(exist_ok=False)
        build = Path('/private/tmp/bvn-s293-' + mode)
        capture = Path('/private/tmp/bvn-s293-' + mode + '-capture')
        capture.mkdir(exist_ok=False)
        record = {'mode': mode, 'started_at': now()}
        records.append(record)
        command = [sys.executable, str(HERE.parent / 's284/build_probe.py'),
                   '--ffdec', str(args.ffdec), '--output', str(build),
                   '--run-id', 's293-' + mode + '-20261102-r01']
        if mode == 'held':
            command.append('--hold-quit')
        record['build_command'] = command
        start = time.monotonic()
        with (output / 'build.txt').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        record['build_exit'] = result.returncode
        record['build_seconds'] = time.monotonic() - start
        write(HERE / 'execution.json', records)
        result.check_returncode()
        write(output / 'qualification.json', qualify(build, mode == 'held'))
        record['qualified_at'] = now()
        # Keep the unchanged capture implementation and the independent host read
        # in one critical section, so another cooperative sampler cannot clear it.
        with player.LOCK_PATH.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            record['launch_started_at'] = now()
            write(HERE / 'execution.json', records)
            start = time.monotonic()
            complete = player._capture_locked(build, capture / 'native.log', 90)
            record['capture_seconds'] = time.monotonic() - start
            host = player.LOG.read_bytes()
            (output / 'host-log.txt.gz').write_bytes(gzip.compress(host, mtime=0))
            record['host_archived_at'] = now()
            if not complete:
                raise ValueError('S293_CAPTURE_INCOMPLETE')
            meta = json.loads((build / 'build.json').read_text())
            prefix = ('AIREF|' + meta['run_id'] + '|').encode()
            lines = [line for line in host.splitlines() if line.startswith(prefix)]
            selected = b'\n'.join(lines) + b'\n'
            trace = (capture / 'native.log').read_bytes()
            equality = {'equal': selected == trace, 'run_id': meta['run_id'],
                        'events': len(lines), 'host_log': str(player.LOG),
                        'host_sha256': hashlib.sha256(host).hexdigest(),
                        'sha256': hashlib.sha256(selected).hexdigest(),
                        'trace_trimmed': False, 'checked_at': now(),
                        'selection': 'all run-prefixed lines in host order; no sorting or deduplication'}
            write(output / 'host-log-equality.json', equality)
            record['host_checked_at'] = equality['checked_at']
            write(HERE / 'execution.json', records)
            if not equality['equal']:
                raise ValueError('S293_HOST_LOG_MISMATCH')
            seal(CASE, build, capture / 'native.log', player.BINARY, capture / 'receipt.json')
            record['receipt_sha256'] = validate(CASE, capture / 'receipt.json')
            record['receipt_validated_at'] = now()
        shutil.copyfile(build / 'build.json', output / 'native-build.json')
        for name in ('receipt.json', 'capture-environment.json'):
            shutil.copyfile(capture / name, output / name)
        (output / 'native-capture.log.gz').write_bytes(gzip.compress(trace, mtime=0))
        with tarfile.open(output / 'native-build.tar.gz', 'w:gz') as archive:
            for path in sorted(build.rglob('*')):
                if path.is_file():
                    archive.add(path, arcname=str(path.relative_to(build)))
        record['archiving_finished_at'] = now()
        write(HERE / 'execution.json', records)
    print('S293_PAIR_CAPTURED production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()
