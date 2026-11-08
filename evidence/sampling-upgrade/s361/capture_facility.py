"""Read-only host observation; retained diagnosis does not require macOS."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
receipt = json.loads((HERE.parent / 's343/lookup-candidates.json').read_text())
records = []
for command in [
    ['/bin/ps', '-axo', 'pid=,comm='],
    ['/usr/bin/swift', '-module-cache-path', '/tmp/s361-swift-cache',
     'evidence/sampling-upgrade/s361/window_probe.swift'],
]:
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    stdout = result.stdout
    if command[0] == '/bin/ps':
        stdout = '\n'.join(line for line in stdout.splitlines() if 'Flash Player' in line) + '\n'
    records.append(dict(command=command, exit_code=result.returncode, stdout=stdout,
                        stderr=result.stderr, wall_seconds=time.monotonic()-start))
binary = Path(receipt['binary'])
report = dict(player_receipt='evidence/sampling-upgrade/s343/lookup-candidates.json',
              observed_binary_path=str(binary),
              observed_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
              captured_unix=time.time(), records=records,
              retention='Only Flash Player process/window rows; unrelated applications omitted')
(HERE / 'facility-result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
