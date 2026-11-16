"""Run a dedicated headed local browser inside the approved foreground lock."""
import functools
import http.server
import json
from pathlib import Path
import socket
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT.parent / '.cache/ichigo-lane3-web-browser-r02'


def main():
    CACHE.mkdir(exist_ok=False)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT / 'dist/web')
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        debug_port = probe.getsockname()[1]
    command = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
               '--user-data-dir=' + str(CACHE / 'profile'), '--remote-debugging-port=' + str(debug_port),
               '--no-first-run', '--no-default-browser-check', '--window-size=1100,850',
               '--new-window', 'about:blank']
    with (HERE / 'chrome.log').open('w') as log:
        chrome = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(120):
                if chrome.poll() is not None:
                    raise RuntimeError('Dedicated Chrome exited')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{debug_port}/json/list') as response:
                        if json.load(response):
                            break
                except OSError:
                    pass
                time.sleep(0.5)
            else:
                raise TimeoutError('Dedicated Chrome startup')
            subprocess.run(['/Users/fengkx/.local/share/mise/installs/node/24.18.0/bin/node',
                            str(HERE / 'browser_check.mjs'), str(debug_port), str(server.server_port)],
                           check=True, timeout=420)
        finally:
            chrome.terminate()
            chrome.wait(timeout=20)
            server.shutdown()
    print('ICHIGO_BROWSER_SESSION_COMPLETE')


if __name__ == '__main__':
    main()
