"""Use the unchanged capture runner with more wall time on a loaded shared host."""
from pathlib import Path
import subprocess
import sys

runner = Path(__file__).resolve().parents[3] / 'tools/probes/capture_native_player.py'
raise SystemExit(subprocess.call([sys.executable, str(runner), *sys.argv[1:], '--timeout', '360']))
