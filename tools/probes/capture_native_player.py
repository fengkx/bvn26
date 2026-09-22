"""Capture native Flash probes using a windowed LaunchServices launch."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from urllib.parse import unquote, urlparse
import zlib

APP = Path('/Volumes/Flash Player/Flash Player.app')
BINARY = APP / 'Contents/MacOS/Flash Player Debugger'
LOG = Path.home() / 'Library/Preferences/Macromedia/Flash Player/Logs/flashlog.txt'
LOCK_PATH = Path('/tmp/bvn-native-flash-capture.lock')
LOCK_WAIT_SECONDS = 10.0


def player_binary(app):
    return Path(app) / 'Contents/MacOS/Flash Player Debugger'


def matching_players(movie, binary=BINARY):
    result = subprocess.run(['ps', '-axo', 'pid=,command='], capture_output=True, text=True, check=True)
    command = str(binary) + ' ' + str(movie)
    return {int(line.strip().split(None, 1)[0]) for line in result.stdout.splitlines()
            if len(line.strip().split(None, 1)) == 2 and line.strip().split(None, 1)[1] == command}


def preflight(app=APP):
    binary = player_binary(app)
    if not binary.is_file():
        raise FileNotFoundError(f'Native Flash player is unavailable: {binary}')
    # Fail once before a batch, rather than recording the same host error per case.
    matching_players(Path('/tmp/bvn-preflight-no-movie.swf'), binary)


def _swf_body(movie):
    data = movie.read_bytes()
    signature = data[:3]
    if signature == b'FWS':
        return data[8:]
    if signature == b'CWS':
        return zlib.decompress(data[8:])
    raise ValueError(f'Cannot verify runtime fighter path in SWF compression {signature!r}')


def _verify_runtime_fighter(build, metadata):
    """Verify the fighter SWF at the path embedded in the launched main movie."""
    if not metadata.get('dynamic_move_case'):
        return None
    move_case = metadata.get('move_case')
    configuration = metadata.get('configuration')
    if not move_case or not configuration:
        raise ValueError('Dynamic capture lacks case/configuration metadata')
    slot = move_case.get('slot')
    character = configuration.get(slot)
    if not slot or not character:
        raise ValueError('Dynamic capture cannot resolve selected fighter slot')

    catalog_path = Path(__file__).resolve().parents[2] / 'manifest.json'
    catalog = json.loads(catalog_path.read_text()).get('fighter_catalog', {})
    character_record = catalog.get(character)
    if not character_record or not character_record.get('url'):
        raise ValueError(f'No manifest fighter SWF mapping for {character!r}')
    relative = Path('game/fighter') / character_record['url']
    expected = metadata.get('outputs_sha256', {}).get(relative.as_posix())
    if not expected:
        expected = metadata.get('sources_sha256', {}).get(relative.as_posix())
    if not expected:
        raise ValueError(f'Build metadata has no expected hash for {relative.as_posix()}')

    declared = build / relative
    if declared.is_file():
        declared_sha = hashlib.sha256(declared.read_bytes()).hexdigest()
        if declared_sha != expected:
            raise ValueError(
                f'Build artifact hash mismatch for {relative}: expected {expected}, got {declared_sha}'
            )

    body = _swf_body(build / 'game/main.swf')
    roots = set(re.findall(rb'(file:///[\x20-\x7e]{1,2048}?/game/fighter/)', body))
    if len(roots) != 1:
        raise ValueError(f'Main SWF has {len(roots)} resolvable fighterDir paths; expected one')
    url = roots.pop().decode('ascii')
    parsed = urlparse(url)
    if parsed.scheme != 'file' or parsed.netloc:
        raise ValueError(f'Unsupported embedded fighterDir URL: {url!r}')
    actual = Path(unquote(parsed.path)) / character_record['url']
    if not actual.is_file():
        raise FileNotFoundError(f'Embedded fighterDir resolves to missing file: {actual}')
    actual_sha = hashlib.sha256(actual.read_bytes()).hexdigest()
    if actual_sha != expected:
        raise ValueError(
            f'Runtime fighter hash mismatch: main.swf loads {actual} ({actual_sha}), '
            f'but build expects {relative} ({expected})'
        )
    return {'path': str(actual), 'sha256': actual_sha}


def capture(build, destination, timeout, app=APP, lock_timeout=LOCK_WAIT_SECONDS):
    # Native Flash always writes one account-wide log, including with -n.
    # Serialize independent harnesses before launching or reading that log.
    with LOCK_PATH.open('a') as lock:
        deadline = time.monotonic() + lock_timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(
                        f'Native Flash capture lock is busy after {lock_timeout:g}s: {LOCK_PATH}'
                    )
                time.sleep(min(0.1, remaining))
        return _capture_locked(build, destination, timeout, app)


def _capture_locked(build, destination, timeout, app=APP):
    metadata = json.loads((build / 'build.json').read_text())
    runtime_fighter = _verify_runtime_fighter(build, metadata)
    prefix = ('AIREF|' + metadata['run_id'] + '|').encode()
    if LOG.exists() and prefix in LOG.read_bytes():
        raise ValueError('Run ID already exists in the player log; use a fresh probe run ID')
    movie = build / 'game/main.swf'
    binary = player_binary(app)
    before = matching_players(movie, binary)
    # Flash can still activate itself despite -g; callers must explicitly allow it.
    # -n isolates this run; -W keeps the launcher alive until its app exits.
    command = ['/usr/bin/open', '-g', '-n', '-W', '-a', str(app), '--args', str(movie)]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    seen = {}
    deadline = time.monotonic() + timeout
    done = None
    capture_error = None
    capture_traceback = None
    try:
        while time.monotonic() < deadline:
            if LOG.exists():
                for line in LOG.read_bytes().splitlines():
                    if not line.startswith(prefix):
                        continue
                    parts = line.split(b'|', 7)
                    if len(parts) == 8:
                        seen[int(parts[2])] = line
                        if parts[6] == b'done' and done is None:
                            done = time.monotonic()
            if done is not None and (process.poll() is not None or time.monotonic() - done > 2):
                break
            time.sleep(0.1)
    except BaseException as error:
        # Cleanup must run even when log parsing, polling or sleeping fails.
        capture_error = error
        capture_traceback = error.__traceback__

    cleanup_errors = []
    try:
        destination.write_bytes(b'\n'.join(seen[key] for key in sorted(seen)) + b'\n')
    except BaseException as error:
        cleanup_errors.append(error)

    # Never terminate the user's original player or another probe instance.
    try:
        owned_players = matching_players(movie, binary) - before
    except BaseException as error:
        owned_players = ()
        cleanup_errors.append(error)
    for pid in owned_players:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except BaseException as error:
            cleanup_errors.append(error)

    try:
        running = process.poll() is None
    except BaseException as error:
        running = True
        cleanup_errors.append(error)
    if running:
        try:
            process.terminate()
        except BaseException as error:
            cleanup_errors.append(error)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as wait_error:
        try:
            process.kill()
        except BaseException as error:
            cleanup_errors.append(error)
        try:
            process.wait(timeout=5)
        except BaseException as error:
            cleanup_errors.extend((wait_error, error))
    except BaseException as error:
        cleanup_errors.append(error)

    if capture_error is not None:
        for error in cleanup_errors:
            capture_error.add_note(f'Capture cleanup also failed: {error!r}')
        raise capture_error.with_traceback(capture_traceback)
    if cleanup_errors:
        raise cleanup_errors[0]
    result = {'events': len(seen), 'done': done is not None, 'capture': str(destination),
              'launch': 'windowed LaunchServices launch (activation possible)',
              'player_app': str(app), 'command': command,
              'runtime_fighter': runtime_fighter}
    (destination.parent / 'capture-environment.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return done is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--lock-timeout', type=float, default=LOCK_WAIT_SECONDS,
                        help='Maximum seconds to wait for the shared native capture lock')
    parser.add_argument('--player-app', type=Path, default=APP,
                        help='Path to the standalone Flash Player Debugger app bundle')
    parser.add_argument('--allow-window-activation', action='store_true',
                        help='Allow a player that can activate itself despite background launch')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Native Flash may raise its window despite -g; capture is disabled without --allow-window-activation')
    preflight(args.player_app)
    if args.lock_timeout < 0:
        parser.error('--lock-timeout must be non-negative')
    raise SystemExit(0 if capture(args.build, args.capture, args.timeout, args.player_app, args.lock_timeout) else 1)


if __name__ == '__main__':
    main()
