"""Capture original raster output; keep diagnostic rendering separate from parity."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
state = subprocess.check_output(['ioreg', '-n', 'Root', '-d1'], text=True)
if not re.search(r'"IOConsoleLocked"\s*=\s*No\b', state):
    raise SystemExit('DESKTOP_LOCKED_OR_UNKNOWN_STOP')
probe = OUT / 'probe-visual-r01'
output = OUT / 'original-visual-r01'
output.mkdir(exist_ok=False)
subprocess.run([sys.executable, str(ROOT / 'tools/probes/capture_native_player.py'),
                str(probe), str(output / 'original.log'), '--allow-window-activation'], check=True)
subprocess.run([sys.executable, str(ROOT / 'tools/probes/collect_ai_reference.py'),
                '--build', str(probe), '--capture', str(output / 'original.log'),
                '--output', str(output / 'collected'), '--retain-post-done-frames'], check=True)
print('ORIGINAL_BITMAP_CAPTURE_COMPLETE')
