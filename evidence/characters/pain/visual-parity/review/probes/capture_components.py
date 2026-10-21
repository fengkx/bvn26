import os
from pathlib import Path
import subprocess, json

for folder in sorted(
    Path(
        os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "components")
    ).iterdir()
):
    if not (folder / "build.json").exists():
        continue
    if (folder / "native.log").exists() and "|done|ok" in (
        folder / "native.log"
    ).read_text():
        continue
    command = [
        __import__("sys").executable,
        "tools/probes/capture_native_player.py",
        str(folder),
        str(folder / "native.log"),
        "--allow-window-activation",
        "--timeout",
        "600",
        "--lock-timeout",
        "1800",
        "--player-app",
        os.environ["BVN_FLASH_APP"],
    ]
    p = subprocess.run(command, capture_output=True, text=True)
    (folder / "capture.log").write_text(p.stdout + p.stderr)
    print(folder.name, p.returncode, flush=True)
    if p.returncode:
        raise SystemExit(p.returncode)
