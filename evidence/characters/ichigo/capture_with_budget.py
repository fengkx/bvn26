"""Allow the same completed source trace more wall time under host contention."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/probes'))
from capture_native_player import main

if __name__ == '__main__':
    sys.argv.extend(['--timeout', '360'])
    main()
