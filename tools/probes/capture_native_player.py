"""Capture native Flash probes; LaunchServices background launch is best-effort."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

APP = Path('/Volumes/Flash Player/Flash Player.app')
BINARY = APP / 'Contents/MacOS/Flash Player Debugger'
LOG = Path.home() / 'Library/Preferences/Macromedia/Flash Player/Logs/flashlog.txt'


def matching_players(movie):
    result = subprocess.run(['ps', '-axo', 'pid=,command='], capture_output=True, text=True, check=True)
    command = str(BINARY) + ' ' + str(movie)
    return {int(line.strip().split(None, 1)[0]) for line in result.stdout.splitlines()
            if len(line.strip().split(None, 1)) == 2 and line.strip().split(None, 1)[1] == command}


def preflight():
    if not BINARY.is_file():
        raise FileNotFoundError(f'Native Flash player is unavailable: {BINARY}')
    # Fail once before a batch, rather than recording the same host error per case.
    matching_players(Path('/tmp/bvn-preflight-no-movie.swf'))


def capture(build, destination, timeout):
    metadata = json.loads((build / 'build.json').read_text())
    prefix = ('AIREF|' + metadata['run_id'] + '|').encode()
    if LOG.exists() and prefix in LOG.read_bytes():
        raise ValueError('Run ID already exists in the player log; use a fresh probe run ID')
    movie = build / 'game/main.swf'
    before = matching_players(movie)
    # Flash can still activate itself despite -g; callers must explicitly allow it.
    # -n isolates this run; -W keeps the launcher alive until its app exits.
    command = ['/usr/bin/open', '-g', '-n', '-W', '-a', str(APP), '--args', str(movie)]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    seen = {}
    deadline = time.monotonic() + timeout
    done = None
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
    finally:
        destination.write_bytes(b'\n'.join(seen[key] for key in sorted(seen)) + b'\n')
        # Never terminate the user's original player or another probe instance.
        for pid in matching_players(movie) - before:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)
    result = {'events': len(seen), 'done': done is not None, 'capture': str(destination),
              'launch': 'LaunchServices background window', 'command': command}
    (destination.parent / 'capture-environment.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return done is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--allow-window-activation', action='store_true',
                        help='Allow a player that can activate itself despite background launch')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Native Flash may raise its window despite -g; capture is disabled without --allow-window-activation')
    raise SystemExit(0 if capture(args.build, args.capture, args.timeout) else 1)


if __name__ == '__main__':
    main()
