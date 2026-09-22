#!/usr/bin/env python3
"""Capture a recursive AS2 freeze before terminating the owned Flash process.

Unlike capture_native_player.py this intentionally waits for visual_freeze_end,
records two 500ms screenshots, and only then cleans up the process.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import traceback

APP = Path('/Volumes/Flash Player/Flash Player.app')
LOG = Path.home() / 'Library/Preferences/Macromedia/Flash Player/Logs/flashlog.txt'
LOCK = Path('/tmp/bvn-native-flash-capture.lock')

def player_binary() -> Path:
    return APP / 'Contents/MacOS/Flash Player Debugger'

def owned_pids(movie: Path) -> set[int]:
    result = subprocess.run(['ps', '-axo', 'pid=,command='], capture_output=True, text=True, check=True)
    binary = str(player_binary())
    movie_text = str(movie)
    owned: set[int] = set()
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2 or binary not in fields[1] or movie_text not in fields[1]:
            continue
        try:
            owned.add(int(fields[0]))
        except ValueError:
            continue
    return owned

def sha(path: Path) -> str | None:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def pixel_sha(path: Path) -> str | None:
    if not path.exists():
        return None
    from PIL import Image
    import hashlib
    # Flash window PNGs include the title/rounded border on this macOS player.
    # The authored stage is 600x400; at Retina 2x the customer area is the
    # explicit 1200x800 rectangle below. Refuse other geometry rather than
    # silently comparing a guessed crop.
    image = Image.open(path).convert('RGB')
    if image.size == (1336, 992):
        image = image.crop((68, 110, 1268, 910))
    return hashlib.sha256(image.tobytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('build', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--lock-timeout', type=float, default=180)
    parser.add_argument('--target-frame', type=int, required=True)
    args = parser.parse_args()
    meta = json.loads((args.build / 'build.json').read_text())
    run_id = str(meta['run_id'])
    prefix = f'AIREF|{run_id}|'.encode()
    args.output.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a') as lock:
        deadline = time.monotonic() + args.lock_timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f'capture lock busy: {LOCK}')
                time.sleep(.1)
        old = LOG.read_bytes() if LOG.exists() else b''
        if prefix in old:
            raise RuntimeError(f'run id already exists: {run_id}')
        movie = args.build / 'game/main.swf'
        launcher = subprocess.Popen(['/usr/bin/open', '-g', '-n', '-W', '-a', str(APP), '--args', str(movie)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        own: set[int] = set()
        lines: list[bytes] = []
        freeze_end = None
        done = None
        try:
            until = time.monotonic() + args.timeout
            while time.monotonic() < until:
                data = LOG.read_bytes() if LOG.exists() else b''
                lines = [line for line in data.splitlines() if line.startswith(prefix)]
                own |= owned_pids(movie)
                if lines:
                    (args.output / 'events.jsonl').write_bytes(b'\n'.join(lines) + b'\n')
                for line in lines:
                    if b'|visual_freeze_end|' in line:
                        freeze_end = line
                    if b'|done|' in line:
                        done = line
                if freeze_end is not None:
                    break
                if done is not None:
                    raise RuntimeError('done arrived before visual_freeze_end')
                time.sleep(.05)
            if freeze_end is None:
                raise TimeoutError('visual_freeze_end not observed')
            begin = next((line for line in lines if b'|visual_freeze_begin|' in line), None)
            begin_payload = begin.split(b'|visual_freeze_begin|', 1)[1].split(b',') if begin else []
            target_reached = bool(begin_payload and int(begin_payload[0]) == args.target_frame)
            clips = [line.decode(errors='replace') for line in lines if b'|visual_clip|' in line]
            def clip_state(line: str) -> tuple[str, str]:
                payload = line.split('|visual_clip|', 1)[1].split(',')
                path = payload[0].replace('root_after', 'root', 1).rstrip('.')
                return path, payload[1]
            before_states = {clip_state(line) for line in clips if '|visual_clip|root,' in line or '|visual_clip|root.' in line}
            after_states = {clip_state(line) for line in clips if '|visual_clip|root_after,' in line or '|visual_clip|root_after.' in line}
            child_lines = [line.decode(errors='replace') for line in lines if b'|visual_freeze_' in line]
            diagnostics = {
                'run_id': run_id, 'visual_freeze': child_lines, 'target_frame': args.target_frame,
                'target_reached': target_reached, 'visual_clip_count': len(clips),
                'before_states': sorted(before_states), 'after_states': sorted(after_states),
                'raw_events_sha256': sha(args.output / 'events.jsonl'), 'owned_pids': sorted(own),
            }
            (args.output / 'freeze-events.json').write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + '\n')
            if not target_reached:
                raise RuntimeError(f'freeze target frame mismatch: expected {args.target_frame}, begin={begin!r}')
            if not before_states or before_states != after_states:
                raise RuntimeError('recursive freeze child path/frame set changed')
            window_tool = Path('/tmp/window-list')
            if not window_tool.is_file() or not os.access(window_tool, os.X_OK):
                raise RuntimeError('window-list helper unavailable; refusing unscoped screenshot')
            window_list = subprocess.run([str(window_tool)], capture_output=True, text=True, check=False).stdout
            owner_lines = [line for line in window_list.splitlines() if 'OWNER=Flash Player Debugger' in line]
            owner = next((line for line in owner_lines if str(movie) in line), '')
            ids = re.findall(r'ID=(\d+)', owner)
            if not ids:
                raise RuntimeError('Flash window was not scoped to this movie/PID; window-list output archived for diagnosis')
            def snapshot_blocks(raw: bytes) -> list[dict]:
                blocks = []
                active = None
                for line in raw.splitlines():
                    if b'|visual_snapshot_begin|' in line:
                        q = line.split(b'|')
                        active = {'seq': int(q[2]), 'time_ms': int(q[3]), 'display_tick': int(q[4]), 'fight_tick': int(q[5]), 'tag': q[7].decode(errors='replace'), 'states': {}}
                    elif active is not None and b'|visual_snapshot_clip|' in line:
                        q = line.split(b'|visual_snapshot_clip|', 1)[1].split(b',')
                        if len(q) >= 3:
                            path = q[1].decode(errors='replace').rstrip('.')
                            active['states'][path] = q[2].decode(errors='replace')
                    elif active is not None and b'|visual_snapshot_end|' in line:
                        q = line.split(b'|')
                        active['end_seq'] = int(q[2]); active['end_time_ms'] = int(q[3]); active['states'] = [[p, active['states'][p]] for p in sorted(active['states'])]
                        blocks.append(active); active = None
                return blocks

            def wait_snapshot(after_seq: int = -1) -> tuple[dict, bytes]:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    data = LOG.read_bytes() if LOG.exists() else b''
                    filtered = b'\n'.join(line for line in data.splitlines() if line.startswith(prefix)) + b'\n'
                    blocks = snapshot_blocks(filtered)
                    fresh = [b for b in blocks if b['end_seq'] > after_seq]
                    if fresh:
                        return fresh[-1], filtered
                    time.sleep(.05)
                raise TimeoutError(f'fresh post-freeze visual snapshot not observed after seq {after_seq}')

            before_sample, before_raw = wait_snapshot()
            subprocess.run(['screencapture', '-x', '-l', ids[0], str(args.output / 'flash-window-before.png')], check=True)
            (args.output / 'post-flash-window-before-events.jsonl').write_bytes(before_raw)
            time.sleep(.5)
            after_sample, after_raw = wait_snapshot(before_sample['end_seq'])
            subprocess.run(['screencapture', '-x', '-l', ids[0], str(args.output / 'flash-window-after.png')], check=True)
            (args.output / 'post-flash-window-after-events.jsonl').write_bytes(after_raw)
            screenshot_states = {
                'after_freeze_end': sorted(after_states),
                'before_screenshot': before_sample,
                'after_screenshot': after_sample,
            }
            (args.output / 'screenshot-states.json').write_text(
                json.dumps(screenshot_states, ensure_ascii=False, indent=2) + '\n'
            )
            if before_sample['end_seq'] <= 0 or after_sample['end_seq'] <= before_sample['end_seq']:
                raise RuntimeError('post-freeze snapshots did not advance monotonically')
            if before_sample['states'] != after_sample['states']:
                raise RuntimeError('root/child state changed during screenshot interval')
            before_sha, after_sha = sha(args.output / 'flash-window-before.png'), sha(args.output / 'flash-window-after.png')
            before_pixels, after_pixels = pixel_sha(args.output / 'flash-window-before.png'), pixel_sha(args.output / 'flash-window-after.png')
            if not before_pixels or not after_pixels or before_pixels != after_pixels:
                raise RuntimeError('recursive freeze screenshots are not stable')
            (args.output / 'capture-state.txt').write_text(freeze_end.decode(errors='replace') + '\n' + owner + '\n' +
                f'file_sha_before={before_sha}\nfile_sha_after={after_sha}\n' +
                f'pixel_sha_before={before_pixels}\npixel_sha_after={after_pixels}\n')
            (args.output / 'build.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
            return 0
        except BaseException as error:
            # Preserve a machine-readable failure even when the window closes,
            # the target is missed, or a screenshot becomes unstable.
            failure = {
                'run_id': run_id,
                'target_frame': args.target_frame,
                'error': str(error),
                'error_type': type(error).__name__,
                'traceback': traceback.format_exc(),
                'owned_pids': sorted(own | owned_pids(movie)),
                'events_sha256': sha(args.output / 'events.jsonl'),
                'freeze_events_sha256': sha(args.output / 'freeze-events.json'),
                'window_list': window_list if 'window_list' in locals() else None,
            }
            (args.output / 'failure.json').write_text(json.dumps(failure, ensure_ascii=False, indent=2) + '\n')
            raise
        finally:
            try:
                launcher.terminate()
                launcher.wait(timeout=5)
            except Exception:
                try:
                    launcher.kill()
                except Exception:
                    pass
            for pid in own | owned_pids(movie):
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass


if __name__ == '__main__':
    raise SystemExit(main())
