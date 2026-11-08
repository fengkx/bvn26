"""Record an unmodified native boot attempt, never certify a fight oracle."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAYER_SHA = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def verify_assets(root, hashes):
    for name, digest in hashes.items():
        if sha((root / name).read_bytes()) != digest:
            raise ValueError('Locked asset mismatch: ' + name)


def appended_bytes(before, after):
    if not after.startswith(before):
        raise ValueError('Global flashlog changed non-append-only; no attributable interval')
    return after[len(before):]


def load_capture():
    spec = importlib.util.spec_from_file_location('native_capture', ROOT / 'tools/probes/capture_native_player.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(output, seconds):
    output.mkdir(parents=True, exist_ok=False)
    capture = load_capture()
    binary = capture.player_binary(capture.APP)
    receipt = dict(kind='native-boot-facility-attempt', started_unix=time.time(),
                   production_admitted=False, native_parity_proven=False,
                   oracle_accepted=False, input_events_sent=0,
                   visible_content=None, input_target_binding=None, post_menu_state=None,
                   fixed_input_tape=None, random_seed=None, random_tape=None,
                   normalized_trace=None, instrumentation='none; original bytes copied unchanged')
    write(output / 'session.json', receipt)
    try:
        if sha(binary.read_bytes()) != PLAYER_SHA:
            raise ValueError('Native player hash mismatch')
        receipt['player'] = dict(app=str(capture.APP), binary=str(binary), sha256=PLAYER_SHA)
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        assets = {name: digest for name, digest in manifest['file_sha256'].items() if name.startswith('game/')}
        verify_assets(ROOT, assets)
        receipt['source_sha256'] = assets
        expected_config = (ROOT / 'tools/probes/mm.cfg').read_bytes()
        actual_config = (Path.home() / 'mm.cfg').read_bytes()
        if actual_config != expected_config:
            raise ValueError('Trace config differs; no settings modified')
        receipt['trace_config'] = dict(path=str(Path.home() / 'mm.cfg'), text=actual_config.decode(), sha256=sha(actual_config))
        receipt['environment'] = []
        for command in (['sw_vers'], ['uname', '-m'], ['arch', '-x86_64', '/usr/bin/uname', '-m']):
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            receipt['environment'].append(dict(command=command, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
        with capture.LOCK_PATH.open('a') as lock:
            # Never remove or replace the lock inode, including after a failed attempt.
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            receipt['lock'] = dict(path=str(capture.LOCK_PATH), acquired=True)
            capture.preflight(capture.APP)
            build = Path(tempfile.mkdtemp(prefix='bvn-oracle-boot-')).resolve()
            shutil.copytree(ROOT / 'game', build / 'game')
            verify_assets(build, assets)
            receipt['build'] = dict(path=str(build), outputs_sha256=assets, byte_identical=True, instrumentation_diff=[])
            movie = build / 'game/main.swf'
            before_pids = capture.matching_players(movie, binary)
            before_log = capture.LOG.read_bytes() if capture.LOG.exists() else b''
            command = ['/usr/bin/open', '-g', '-n', '-W', '-a', str(capture.APP), '--args', str(movie)]
            receipt['launch'] = dict(command=command, preexisting_matching_pids=sorted(before_pids))
            launcher = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            receipt['launch']['launcher_pid'] = launcher.pid
            try:
                observed = set()
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    observed |= capture.matching_players(movie, binary) - before_pids
                    time.sleep(0.25)
                receipt['launch']['observed_exact_command_pids'] = sorted(observed)
                receipt['launch']['launcher_exit_before_cleanup'] = launcher.poll()
                after_log = capture.LOG.read_bytes() if capture.LOG.exists() else b''
                delta = appended_bytes(before_log, after_log)
                (output / 'flashlog.delta.log').write_bytes(delta)
                receipt['flashlog'] = dict(path=str(capture.LOG), before_size=len(before_log), after_size=len(after_log),
                    before_sha256=sha(before_log), after_sha256=sha(after_log), delta_size=len(delta), delta_sha256=sha(delta),
                    attribution='Unattributed account-wide append interval, not a fight trace; existing players may also write')
            finally:
                # Match the unique temporary movie immediately before cleanup.
                receipt['cleanup'] = dict(exact_command_pids=[], terminated=[])
                try:
                    owned = capture.matching_players(movie, binary) - before_pids
                    receipt['cleanup']['exact_command_pids'] = sorted(owned)
                except Exception as exc:
                    owned = set()
                    receipt['cleanup']['ownership_scan_error'] = str(exc)
                try:
                    for pid in owned:
                        try:
                            os.kill(pid, signal.SIGTERM)
                            receipt['cleanup']['terminated'].append(pid)
                        except ProcessLookupError:
                            pass
                finally:
                    if launcher.poll() is None:
                        launcher.terminate()
                    try:
                        stdout, stderr = launcher.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        launcher.kill()
                        stdout, stderr = launcher.communicate(timeout=5)
                    receipt['launch'].update(exit_after_cleanup=launcher.returncode, stdout=stdout.decode(), stderr=stderr.decode())
                receipt['cleanup']['remaining_matching_pids'] = sorted(capture.matching_players(movie, binary) - before_pids)
            verify_assets(ROOT, assets)
            verify_assets(build, assets)
        receipt['result'] = 'boot-attempt-only; CUA binding unavailable; no fight oracle'
    except Exception as exc:
        receipt['error'] = dict(type=type(exc).__name__, message=str(exc))
        receipt['result'] = 'blocked'
    finally:
        receipt['completed_unix'] = time.time()
        receipt['wall_seconds'] = receipt['completed_unix'] - receipt['started_unix']
        write(output / 'session.json', receipt)
    print(receipt['result'])
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=15)
    parser.add_argument('--allow-window-activation', action='store_true')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Native Flash may raise its window; explicit allowance required')
    if not 0 < args.seconds <= 30:
        parser.error('Bounded boot window must be within (0, 30] seconds')
    raise SystemExit(run(args.output, args.seconds))
