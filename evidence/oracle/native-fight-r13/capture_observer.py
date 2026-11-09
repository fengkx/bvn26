"""Drive a hash-pinned observer copy using the retained physical PID menu path."""
import argparse
import fcntl
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
FACILITY = HERE.parent / "native-fight-r02"
spec = importlib.util.spec_from_file_location('original_boot', HERE.parent / 'native-fight-r01/capture_boot.py')
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)


def bound_window(snapshot, pid, binary, movie, windowed):
    apps = [a for a in snapshot['applications'] if a['pid'] == pid and a['executable'] == str(binary)]
    if len(apps) != 1:
        raise ValueError('Exact executable/PID association absent or ambiguous')
    app = apps[0]
    windows = [w for w in app['cg_windows'] if w.get('kCGWindowOwnerPID') == pid
               and w.get('kCGWindowName') == str(movie)
               and w.get('kCGWindowBounds', {}).get('Width', 0) > 0
               and w.get('kCGWindowBounds', {}).get('Height', 0) > 33]
    if len(windows) != 1:
        raise ValueError('Movie window absent or ambiguous')
    if windowed:
        if app['ax_windows_error'] != 0 or app['ax_windows'] != [{'title': str(movie), 'title_error': 0}]:
            raise ValueError('Exact AX movie window association absent or ambiguous')
        if snapshot['frontmost_pid'] != pid or not windows[0].get('kCGWindowIsOnscreen'):
            raise ValueError('Owned movie is not visible and frontmost')
    return windows[0]


def run(output, observer_build):
    output.mkdir(parents=True, exist_ok=False)
    capture = boot.load_capture()
    binary = capture.player_binary(capture.APP)
    receipt = {'kind': 'native-observer-physical-menu-run', 'production_admitted': False,
               'native_parity_proven': False, 'oracle_accepted': False,
               'started_unix': time.time(), 'input_operations': [],
               'instrumentation_diff': 'See observer_build.instrumentation_sha256 and retained instrumentation.diff.gz (decompressed hash)', 'random_tape': None, 'post_menu_state': None,
               'normalized_trace': None, 'native_input_consumption_ticks': None}
    boot.write(output / 'session.json', receipt)
    def command(args):
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        record = {'command': args, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        receipt.setdefault('commands', []).append(record)
        if result.returncode:
            raise RuntimeError(json.dumps(record))
        return result.stdout
    def snapshot(name):
        value = json.loads(command(['swift', str(FACILITY / 'window_probe.swift')]))
        boot.write(output / (name + '.json'), value)
        if not value['accessibility_trusted'] or not value['screen_capture_preflight']:
            raise RuntimeError('Host Accessibility or Screen Recording preflight is false; no grant requested')
        return value
    try:
        if boot.sha(binary.read_bytes()) != boot.PLAYER_SHA:
            raise ValueError('Player hash mismatch')
        assets = {k: v for k, v in json.loads((ROOT / 'manifest.json').read_text())['file_sha256'].items() if k.startswith('game/')}
        boot.verify_assets(ROOT, assets)
        config = (Path.home() / 'mm.cfg').read_bytes()
        if config != (ROOT / 'tools/probes/mm.cfg').read_bytes():
            raise ValueError('Trace config mismatch')
        metadata = json.loads((observer_build / 'build.json').read_text())
        output_hashes = metadata['outputs_sha256']
        boot.verify_assets(observer_build, output_hashes)
        if metadata.get('facility') != 'r12' or any(metadata['source_sha256'].get(name) != assets[name] for name in ['game/main.swf', 'game/fighter/yihu.swf']):
            raise ValueError('Observer build source mismatch')
        receipt['observer_build'] = metadata
        prefix = ('M002|' + metadata['run_id'] + '|').encode()
        tape_raw = (HERE / 'input-tape.json').read_bytes()
        tape = json.loads(tape_raw)
        receipt.update(player={'binary': str(binary), 'sha256': boot.PLAYER_SHA}, source_sha256=assets,
                       tape_sha256=boot.sha(tape_raw), trace_config_sha256=boot.sha(config), trace_config=config.decode(),
                       tool_sha256={p.name: boot.sha(p.read_bytes()) for p in [Path(__file__), FACILITY / 'window_probe.swift', FACILITY / 'input.applescript']})
        for args in [['sw_vers'], ['uname', '-m'], ['arch', '-x86_64', '/usr/bin/uname', '-m'], ['file', str(binary)]]:
            command(args)
        with capture.LOCK_PATH.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            receipt['lock'] = {'path': str(capture.LOCK_PATH), 'acquired': True}
            snapshot('before-launch')
            build = Path(tempfile.mkdtemp(prefix='bvn-native-menu-')).resolve()
            shutil.copytree(observer_build / 'game', build / 'game')
            boot.verify_assets(build, output_hashes)
            movie = build / 'game/main.swf'
            receipt['build'] = {'path': str(build), 'byte_identical_to_observer_build': True, 'outputs_sha256': output_hashes}
            prelaunch = capture.LOG.read_bytes() if capture.LOG.exists() else b''
            (output / 'flashlog.prelaunch.log').write_bytes(prelaunch)
            if prefix in prelaunch:
                raise ValueError('Run tag already present before launch')
            before = prelaunch
            if capture.matching_players(movie, binary):
                raise RuntimeError('Unique movie already has a player')
            launch_args = ['/usr/bin/open', '-g', '-n', '-W', '-a', str(capture.APP), '--args', str(movie)]
            launcher = subprocess.Popen(launch_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            receipt['launch'] = {'command': launch_args, 'launcher_pid': launcher.pid}
            try:
                time.sleep(5)
                before = capture.LOG.read_bytes() if capture.LOG.exists() else b''
                (output / 'flashlog.input-baseline.log').write_bytes(before)
                receipt['launch_log_transition'] = {'prelaunch_size': len(prelaunch), 'input_baseline_size': len(before), 'append_only': before.startswith(prelaunch)}
                pids = capture.matching_players(movie, binary)
                if len(pids) != 1:
                    raise RuntimeError('Expected exactly one owned movie PID')
                pid = next(iter(pids))
                receipt['movie_pid'] = pid
                for index, step in enumerate(tape['steps']):
                    name = f'{index:02d}-{step["name"]}'
                    if capture.matching_players(movie, binary) != {pid}:
                        raise RuntimeError('Owned process identity changed')
                    before_input = snapshot(name + '-before')
                    bound_window(before_input, pid, binary, movie, index > 0)
                    operation = {'step': step, 'pid': pid, 'started_unix': time.time(), 'started_monotonic': time.monotonic()}
                    receipt['input_operations'].append(operation)
                    operation['result'] = command(['/usr/bin/osascript', str(FACILITY / 'input.applescript'), str(pid), str(movie), step['key'], str(step['hold_seconds'])])
                    operation['returned_monotonic'] = time.monotonic()
                    if not operation['result'].startswith(str(pid) + ', true,'):
                        raise RuntimeError('Returned input PID/focus mismatch')
                    time.sleep(step['settle_seconds'])
                    after_input = snapshot(name + '-after')
                    window = bound_window(after_input, pid, binary, movie, True)
                    bounds = window['kCGWindowBounds']
                    rectangle = ','.join(str(int(bounds[k])) for k in ['X', 'Y', 'Width', 'Height'])
                    command(['/usr/sbin/screencapture', '-x', '-t', 'jpg', '-R' + rectangle, str(output / (name + '.jpg'))])
                    operation['screenshot'] = name + '.jpg'
                    boot.write(output / 'session.json', receipt)
                receipt['result'] = 'physical-tape-executed; tagged observer validation required; oracle unproved'
            except Exception as exc:
                receipt['primary_error'] = {'type': type(exc).__name__, 'message': str(exc)}
                raise
            finally:
                after = capture.LOG.read_bytes() if capture.LOG.exists() else b''
                (output / 'flashlog.after.log').write_bytes(after)
                try:
                    delta = boot.appended_bytes(before, after)
                    (output / 'flashlog.delta.log').write_bytes(delta)
                    tagged = [line for line in after.splitlines() if line.startswith(prefix)]
                    (output / 'tagged.log').write_bytes(b'\n'.join(tagged) + (b'\n' if tagged else b''))
                    receipt['tagged_line_count'] = len(tagged)
                    receipt['flashlog'] = {'before_size': len(before), 'after_size': len(after),
                        'before_sha256': boot.sha(before), 'after_sha256': boot.sha(after),
                        'delta_sha256': boot.sha(delta), 'delta_size': len(delta),
                        'attribution': 'account-wide append interval; no unique run tag; not a normalized fight trace'}
                finally:
                    owned = capture.matching_players(movie, binary)
                    receipt['cleanup_pids'] = sorted(owned)
                    for pid in owned:
                        try:
                            os.kill(pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                    if launcher.poll() is None:
                        launcher.terminate()
                    stdout, stderr = launcher.communicate(timeout=5)
                    receipt['launch'].update(exit_after_cleanup=launcher.returncode, stdout=stdout.decode(), stderr=stderr.decode())
                    receipt['remaining_movie_pids'] = sorted(capture.matching_players(movie, binary))
            boot.verify_assets(ROOT, assets)
            boot.verify_assets(build, output_hashes)
            receipt['asset_recheck'] = 'passed'
    except Exception as exc:
        receipt['result'] = 'blocked'
        receipt['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        receipt['completed_unix'] = time.time()
        boot.write(output / 'session.json', receipt)
    print(receipt['result'])
    # Facility success must not silently become M0-02 acceptance.
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--allow-window-activation', action='store_true')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Explicit window/input activation allowance required')
    raise SystemExit(run(args.output.resolve(), args.build.resolve()))
